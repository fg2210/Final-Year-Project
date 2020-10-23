from flask import Flask, render_template, flash, redirect, url_for, session, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, PasswordField, validators, SelectField
from wtforms.fields.html5 import EmailField, TelField, DateField
from wtforms.validators import DataRequired, ValidationError, EqualTo
from wtforms_components import DateRange
from passlib.hash import sha256_crypt
from functools import wraps
from ukpostcodeutils import validation
from datetime import date, datetime
from datetime import timedelta

app = Flask(__name__)

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'patient_records'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# initiate MYSQL
mysql = MySQL(app)


# Postcode validator
class PostcodeValidator(object):
    def __init__(self, message=None):
        if not message:
            message = u'Must be a valid UK Postcode in the format AA000AA'
        self.message = message

    def __call__(self, form, field):
        if not validation.is_valid_postcode(field.data):
            raise ValidationError('Must be a valid UK Postcode in the format AA000AA')


# Give PostcodeValidator a name
postcode_validator = PostcodeValidator


# Homepage directory
@app.route('/')
def index():
    session.clear()
    return render_template('home.html')


# ---------------------------------------- PATIENT FUNCTIONALITY ----------------------------------------


# Register Patient Form Class
class RegisterForm(Form):
    first_name = StringField('First Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                             render_kw={"placeholder": "Enter First Name"})
    last_name = StringField('Last Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                            render_kw={"placeholder": "Enter Last Name"})
    centre_name = StringField('Centre Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                              render_kw={"placeholder": "Enter Centre Name that you wish to be registered to"})
    doctor_name = StringField('Doctor Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                              render_kw={"placeholder": "Enter Doctor Name"})
    address = StringField('Address', validators=[DataRequired(), validators.Length(min=1, max=100)],
                          render_kw={"placeholder": "Enter Address"})
    town_name = StringField('Town Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                            render_kw={"placeholder": "Enter Town"})
    county_name = SelectField('County Name', choices=[('Antrim', 'Antrim'), ('Armagh', 'Armagh'), ('Down', 'Down'),
                                                      ('Derry/Londonderry', 'Derry/Londonderry'),
                                                      ('Fermanagh', 'Fermanagh'), ('Tyrone', 'Tyrone')],
                              validators=[DataRequired()])
    postcode = StringField('Postcode', validators=[DataRequired(), postcode_validator()],
                           render_kw={"placeholder": "Enter Postcode (In caps without spaces)"})
    telephone_number = TelField('Telephone Number', validators=[DataRequired(), validators.Length(min=11, max=11)],
                                render_kw={"placeholder": "Enter Telephone Number"})
    email_address = EmailField('Email Address', validators=[DataRequired()],
                               render_kw={"placeholder": "Enter Valid Email address"})
    patient_username = StringField('Username', render_kw={"placeholder": "Enter Username"}, validators=[DataRequired(),
                                                                                                        EqualTo(
                                                                                                            'confirm_patient_username',
                                                                                                            message='Usernames Do Not Match')])
    confirm_patient_username = StringField('Confirm Username', render_kw={"placeholder": "Re Enter Username"})
    patient_password = PasswordField('Password', render_kw={"placeholder": "Enter Password"},
                                     validators=[DataRequired(),
                                                 EqualTo('confirm_patient_password', message='Passwords Do Not Match')])
    confirm_patient_password = PasswordField('Confirm Password', render_kw={"placeholder": "Re Enter Password"})


# Patient Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Get the register form
    form = RegisterForm(request.form)

    if request.method == 'POST' and form.validate():
        first_name = form.first_name.data
        last_name = form.last_name.data
        address = form.address.data
        town_name = form.town_name.data
        county_name = form.county_name.data
        postcode = form.postcode.data
        telephone_number = form.telephone_number.data
        email_address = form.email_address.data
        patient_username = form.patient_username.data
        patient_password = sha256_crypt.encrypt(str(form.patient_password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Get the relevant IDs from their respective tables
        result = cur.execute("SELECT * FROM patients WHERE patient_username =%s", [form.patient_username.data])
        result_email = cur.execute("SELECT * FROM patients WHERE email_address =%s", [form.email_address.data])

        # Get the centre ID of the entered centre
        centre_result = cur.execute("SELECT centre_id FROM centres WHERE centre_name =%s", [form.centre_name.data])
        centre_id_result = cur.fetchone()

        # Get the doctor ID of the entered doctor
        doctor_result = cur.execute(
            "SELECT doctor_id FROM doctors WHERE concat(doctor_first_name, ' ', doctor_last_name) =%s",
            [form.doctor_name.data])
        doctor_id_result = cur.fetchone()

        # Execute queries depending on database values
        if doctor_result == 1:
            if centre_result == 1:
                if result == 0 and result_email == 0:
                    cur.execute(
                        "INSERT INTO patients(first_name, last_name, centre_id, doctor_id, address, town_name, county_name, postcode, telephone_number, email_address, patient_username, patient_password) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (first_name, last_name, centre_id_result.get('centre_id'), doctor_id_result.get('doctor_id'),
                         address, town_name, county_name, postcode,
                         telephone_number, email_address, patient_username, patient_password))

                    # Commit to DB
                    mysql.connection.commit()

                    # Close connection
                    cur.close()

                    flash('You are now registered and can now log in!', 'success')
                    return redirect(url_for('login'))

                else:
                    flash('Username/Email already exists!', 'danger')
                    return redirect(url_for('register'))

            else:
                flash('Centre name not found!', 'danger')
                return redirect(url_for('register'))

        else:
            flash('Doctor name not found!', 'danger')
            return redirect(url_for('register'))

    return render_template('/patient/register.html', form=form)


# Patient Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM patients WHERE patient_username =%s", [username])

        # Execute queries depending on results above
        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            patient_password = data['patient_password']

            # Compare passwords
            if sha256_crypt.verify(password_candidate, patient_password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are logged in!', 'success')
                return redirect(url_for('dashboard'))

            else:
                flash('Invalid password!', 'danger')
                return render_template('/patient/login.html')
        else:
            flash('Username not found!', 'danger')
            return render_template('/patient/login.html')

    return render_template('/patient/login.html')


# Checked if patient is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        # If there is a session in progress
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorised, Please login!', 'danger')
            return redirect(url_for('login'))

    return wrap


# Patient Logout
@app.route('/logout')
def logout():
    # Clear any session that is active
    session.clear()
    flash('You are now logged out!', 'success')
    return redirect(url_for('login'))


# Patient Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Retrieve username from the session
    patient_username = session.get('username', None)

    # Create cursor
    cur = mysql.connection.cursor()

    # Get patients with the same username as the session and retrieve their data
    result = cur.execute("SELECT * FROM patients WHERE patient_username =%s", [patient_username])

    patient_data = cur.fetchall()

    # Execute query depending on results
    if result > 0:
        return render_template('/patient/dashboard.html', patient_data=patient_data)
    else:
        flash('No patient found!', 'danger')
        return render_template('/patient/dashboard.html')


# Book appointment form class
class BookAppointment(Form):
    today_date = date.today()
    tomorrow_date = today_date + timedelta(days=1)

    appointment_date = DateField('Appointment Date', format='%Y-%m-%d', default=tomorrow_date,
                                 validators=[DateRange(min=tomorrow_date, message="Please select a date after today"),
                                             DataRequired()])
    appointment_time = SelectField('Appointment Time',
                                   choices=[('09:00', '09:00'), ('09:30', '09:30'), ('10:00', '10:00'),
                                            ('10:30', '10:30'), ('11:00', '11:00'), ('11:30', '11:30'),
                                            ('12:00', '12:00'), ('12:30', '12:30'), ('13:00', '13:00'),
                                            ('13:30', '13:30'), ('14:00', '14:00'), ('14:30', '14:30'),
                                            ('15:00', '15:00'), ('15:30', '15:30'), ('16:00', '16:00'),
                                            ('16:30', '16:30')], validators=[DataRequired()])


# Book an appointment
@app.route('/bookappointment', methods=['GET', 'POST'])
@is_logged_in
def book():
    form = BookAppointment(request.form)
    if request.method == 'POST' and form.validate():
        appointment_date = form.appointment_date.data
        appointment_time = form.appointment_time.data
        patient_username = session.get('username', None)

        # Create cursor
        cur = mysql.connection.cursor()

        # Get patient_id, doctor_id and centre_id from patients table
        appointment_patient_id = cur.execute("SELECT patient_id FROM patients WHERE patient_username =%s",
                                             [patient_username])
        actual_patient_id = cur.fetchone()
        appointment_doctor_id = cur.execute("SELECT doctor_id FROM patients WHERE patient_username =%s",
                                            [patient_username])
        actual_doctor_id = cur.fetchone()
        appointment_centre_id = cur.execute("SELECT centre_id FROM patients WHERE patient_username =%s",
                                            [patient_username])
        actual_centre_id = cur.fetchone()

        # Check if there is already an appointment with the patients doctor at the same time and date
        confirmed_booking = cur.execute(
            "SELECT appointment_id FROM appointments WHERE appointment_time = %s AND appointment_date = %s AND doctor_id = %s",
            (appointment_time, appointment_date, actual_doctor_id.get('doctor_id')))

        # If the selected slot is available
        if confirmed_booking == 0:
            # Execute query
            cur.execute(
                "INSERT INTO appointments(appointment_date, appointment_time, patient_id, doctor_id, centre_id) VALUES(%s, %s, %s, %s, %s)",
                (appointment_date, appointment_time, actual_patient_id.get('patient_id'),
                 actual_doctor_id.get('doctor_id'), actual_centre_id.get('centre_id')))

            # Making sure the appointment is made for a weekday
            if appointment_date.weekday() == 0 or appointment_date.weekday() == 1 or appointment_date.weekday() == 2 or appointment_date.weekday() == 3 or appointment_date.weekday() == 4:

                # Commit to DB
                mysql.connection.commit()

                # Close connection
                cur.close()

                flash('Appointment made successfully!', 'success')
                return redirect(url_for('book'))

            else:
                flash('Sorry, appointments cannot be made for a Saturday/Sunday!', 'danger')
                return render_template('/patient/bookappointment.html', form=form)

        else:
            flash('Sorry, appointment unavailable!', 'danger')
            return render_template('/patient/bookappointment.html', form=form)

    return render_template('/patient/bookappointment.html', form=form)


# View todays appointments
@app.route('/todaysappointments')
@is_logged_in
def todaysappointments():
    # Get the patients username and todays date
    patient_username = session.get('username', None)
    today_date = date.today()

    # Create Cursor
    cur = mysql.connection.cursor()

    # Get the patient ID of the logged in patient
    cur.execute("SELECT patient_id FROM patients WHERE patient_username =%s", [patient_username])
    actual_patient_id = cur.fetchone()

    # Get appointment data
    result = cur.execute(
        "SELECT * FROM appointments WHERE patient_id =%s AND appointment_date =%s ORDER BY appointment_time ASC",
        ([actual_patient_id.get('patient_id')], today_date))
    appointment_data = cur.fetchall()

    # Get doctor_id and centre_id from patients table
    cur.execute("SELECT doctor_id FROM patients WHERE patient_id =%s", [actual_patient_id.get('patient_id')])
    actual_doctor_id = cur.fetchone()
    cur.execute("SELECT centre_id FROM patients WHERE patient_id =%s", [actual_patient_id.get('patient_id')])
    actual_centre_id = cur.fetchone()

    # Get all data from the doctors and centres given the ID
    doctor_result = cur.execute("SELECT * FROM doctors WHERE doctor_id =%s", [actual_doctor_id.get('doctor_id')])
    doctor_data = cur.fetchall()
    centre_result = cur.execute("SELECT * FROM centres WHERE centre_id =%s", [actual_centre_id.get('centre_id')])
    centre_data = cur.fetchall()

    # If there are any appointments for today, show them
    if result > 0 and doctor_result > 0 and centre_result > 0:
        return render_template('/patient/todaysappointments.html', appointment_data=appointment_data,
                               doctor_data=doctor_data, centre_data=centre_data)
    else:
        flash('No appointments found!', 'danger')
        return render_template('/patient/todaysappointments.html')


# View upcoming appointments
@app.route('/upcomingappointments')
@is_logged_in
def upcomingappointments():
    # Get the patients username and todays date
    patient_username = session.get('username', None)
    today_date = date.today()

    # Create Cursor
    cur = mysql.connection.cursor()

    # Get the patient ID of the logged in patient
    cur.execute("SELECT patient_id FROM patients WHERE patient_username =%s", [patient_username])
    actual_patient_id = cur.fetchone()

    # Get patient data
    result = cur.execute(
        "SELECT * FROM appointments WHERE patient_id =%s AND appointment_date >%s ORDER BY appointment_date ASC",
        ([actual_patient_id.get('patient_id')], today_date))
    appointment_data = cur.fetchall()

    # Get doctor_id and centre_id from patients table
    cur.execute("SELECT doctor_id FROM patients WHERE patient_id =%s", [actual_patient_id.get('patient_id')])
    actual_doctor_id = cur.fetchone()
    cur.execute("SELECT centre_id FROM patients WHERE patient_id =%s", [actual_patient_id.get('patient_id')])
    actual_centre_id = cur.fetchone()

    # Get all data from the doctors and centres given the ID
    doctor_result = cur.execute("SELECT * FROM doctors WHERE doctor_id =%s", [actual_doctor_id.get('doctor_id')])
    doctor_data = cur.fetchall()
    centre_result = cur.execute("SELECT * FROM centres WHERE centre_id =%s", [actual_centre_id.get('centre_id')])
    centre_data = cur.fetchall()

    # If there are any upcoming appointments, show them
    if result > 0 and doctor_result > 0 and centre_result > 0:
        return render_template('/patient/upcomingappointments.html', appointment_data=appointment_data,
                               doctor_data=doctor_data, centre_data=centre_data)
    else:
        flash('No appointments found!', 'danger')
        return render_template('/patient/upcomingappointments.html')


# Delete Upcoming Appointment
@app.route('/delete_appointment/<int:appointment_id>', methods=['POST'])
@is_logged_in
def delete_appointment(appointment_id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute, commit and close the delete query given the selected appointment
    cur.execute("DELETE FROM appointments WHERE appointment_id =%s", [appointment_id])
    mysql.connection.commit()
    cur.close()

    # Display a message to show the appointment has been deleted
    flash('Appointment Deleted!', 'success')

    # Reload the upcoming appointments with the new data
    return redirect(url_for('upcomingappointments'))


# Check previous appointments
@app.route('/previousappointments')
@is_logged_in
def previousappointments():
    # Get the patients username and todays date
    patient_username = session.get('username', None)
    today_date = date.today()

    # Create cursor
    cur = mysql.connection.cursor()

    # Get the patient ID of the logged in patient
    cur.execute("SELECT patient_id FROM patients WHERE patient_username =%s", [patient_username])
    actual_patient_id = cur.fetchone()

    # Get patient data
    result = cur.execute(
        "SELECT * FROM appointments WHERE patient_id =%s AND appointment_date <%s ORDER BY appointment_date ASC",
        ([actual_patient_id.get('patient_id')], today_date))
    appointment_data = cur.fetchall()

    # Get doctor_id and centre_id from patients table
    cur.execute("SELECT doctor_id FROM patients WHERE patient_id =%s", [actual_patient_id.get('patient_id')])
    actual_doctor_id = cur.fetchone()
    cur.execute("SELECT centre_id FROM patients WHERE patient_id =%s", [actual_patient_id.get('patient_id')])
    actual_centre_id = cur.fetchone()

    # Get all data from the doctors and centres given the ID
    doctor_result = cur.execute("SELECT * FROM doctors WHERE doctor_id =%s", [actual_doctor_id.get('doctor_id')])
    doctor_data = cur.fetchall()
    centre_result = cur.execute("SELECT * FROM centres WHERE centre_id =%s", [actual_centre_id.get('centre_id')])
    centre_data = cur.fetchall()

    # If there are any previous appointments, show them
    if result > 0 and doctor_result > 0 and centre_result > 0:
        return render_template('/patient/previousappointments.html', appointment_data=appointment_data,
                               doctor_data=doctor_data, centre_data=centre_data)
    else:
        flash('No appointments found!', 'danger')
        return render_template('/patient/previousappointments.html')


# Personal Details
@app.route('/personaldetails')
@is_logged_in
def personaldetails():
    # Get the patients username
    patient_username = session.get('username', None)

    # Create Cursor
    cur = mysql.connection.cursor()

    # Get doctor_id and centre_id from patients table
    cur.execute("SELECT doctor_id FROM patients WHERE patient_username =%s", [patient_username])
    actual_doctor_id = cur.fetchone()
    cur.execute("SELECT centre_id FROM patients WHERE patient_username =%s", [patient_username])
    actual_centre_id = cur.fetchone()

    # Get patient data
    result = cur.execute("SELECT * FROM patients WHERE patient_username =%s", [patient_username])
    patient_data = cur.fetchall()

    # Get doctor and centre records given the IDs
    doctor_result = cur.execute("SELECT * FROM doctors WHERE doctor_id =%s", [actual_doctor_id.get('doctor_id')])
    doctor_data = cur.fetchall()
    centre_result = cur.execute("SELECT * FROM centres WHERE centre_id =%s", [actual_centre_id.get('centre_id')])
    centre_data = cur.fetchall()

    # Show the patients details
    if result > 0 and doctor_result > 0 and centre_result > 0:
        return render_template('/patient/personaldetails.html', patient_data=patient_data, doctor_data=doctor_data,
                               centre_data=centre_data)
    else:
        flash('No patient details found!', 'danger')
        return render_template('/patient/personaldetails.html')


# ---------------------------------------- DOCTOR FUNCTIONALITY ----------------------------------------


# Register Doctor Form Class
class RegisterDoctorForm(Form):
    doctor_first_name = StringField('First Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                                    render_kw={"placeholder": "Enter your First Name"})
    doctor_last_name = StringField('Last Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                                   render_kw={"placeholder": "Enter your Last Name"})
    centre_name = StringField('Centre Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                              render_kw={"placeholder": "Enter the Centre Name that you wish to be registered to"})
    doctor_address = StringField('Address', validators=[DataRequired(), validators.Length(min=1, max=100)],
                                 render_kw={"placeholder": "Enter your Address"})
    doctor_town_name = StringField('Town Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                                   render_kw={"placeholder": "Enter your Town"})
    doctor_county_name = SelectField('County Name',
                                     choices=[('Antrim', 'Antrim'), ('Armagh', 'Armagh'), ('Down', 'Down'),
                                              ('Derry/Londonderry', 'Derry/Londonderry'), ('Fermanagh', 'Fermanagh'),
                                              ('Tyrone', 'Tyrone')], validators=[DataRequired()])
    doctor_postcode = StringField('Postcode', validators=[DataRequired(), postcode_validator()],
                                  render_kw={"placeholder": "Enter your Postcode (In caps without spaces)"})
    doctor_telephone_number = TelField('Telephone Number',
                                       validators=[DataRequired(), validators.Length(min=11, max=11)],
                                       render_kw={"placeholder": "Enter your Telephone Number"})
    doctor_email_address = EmailField('Email Address', validators=[DataRequired()],
                                      render_kw={"placeholder": "Enter a valid Email address"})
    doctor_username = StringField('Username', render_kw={"placeholder": "Enter your Username"},
                                  validators=[DataRequired(),
                                              EqualTo('confirm_doctor_username', message='Usernames do not match')])
    confirm_doctor_username = StringField('Confirm Username', render_kw={"placeholder": "Re-enter Username"})
    doctor_password = PasswordField('Password', render_kw={"placeholder": "Enter your Password"},
                                    validators=[DataRequired(),
                                                EqualTo('confirm_doctor_password', message='Passwords do not match')])
    confirm_doctor_password = PasswordField('Confirm Password', render_kw={"placeholder": "Re enter Password"})


# Doctor Registration
@app.route('/registerdoctor', methods=['GET', 'POST'])
def registerdoctor():
    # Get the register form
    form = RegisterDoctorForm(request.form)

    if request.method == 'POST' and form.validate():
        doctor_first_name = form.doctor_first_name.data
        doctor_last_name = form.doctor_last_name.data
        doctor_address = form.doctor_address.data
        doctor_town_name = form.doctor_town_name.data
        doctor_county_name = form.doctor_county_name.data
        doctor_postcode = form.doctor_postcode.data
        doctor_telephone_number = form.doctor_telephone_number.data
        doctor_email_address = form.doctor_email_address.data
        doctor_username = form.doctor_username.data
        doctor_password = sha256_crypt.encrypt(str(form.doctor_password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Get the relevant IDs from their respective tables
        result = cur.execute("SELECT * FROM doctors WHERE doctor_username =%s", [form.doctor_username.data])
        result_email = cur.execute("SELECT * FROM doctors WHERE doctor_email_address =%s",
                                   [form.doctor_email_address.data])

        # Get the centre ID of the entered centre
        centre_result = cur.execute("SELECT centre_id FROM centres WHERE centre_name =%s", [form.centre_name.data])
        centre_id_result = cur.fetchone()

        # Execute queries depending on database values
        if centre_result == 1:
            if result == 0 and result_email == 0:
                cur.execute(
                    "INSERT INTO doctors(doctor_first_name, doctor_last_name, centre_id, doctor_address, doctor_town_name, doctor_county_name, doctor_postcode, doctor_telephone_number, doctor_email_address, doctor_username, doctor_password) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (doctor_first_name, doctor_last_name, centre_id_result.get('centre_id'), doctor_address,
                     doctor_town_name, doctor_county_name, doctor_postcode, doctor_telephone_number,
                     doctor_email_address, doctor_username, doctor_password))

                # Commiadt to DB
                mysql.connection.commit()

                # Close connection
                cur.close()

                flash('You are now registered and can now log in!', 'success')
                return redirect(url_for('doctorlogin'))

            else:
                flash('Username/Email already exists!', 'danger')
                return redirect(url_for('registerdoctor'))
        else:
            flash('Centre name not found!', 'danger')
            return redirect(url_for('registerdoctor'))

    return render_template('doctor/registerdoctor.html', form=form)


# Doctor Login
@app.route('/doctorlogin', methods=['GET', 'POST'])
def doctorlogin():
    if request.method == 'POST':
        # Get form fields
        doctor_username = request.form['doctor_username']
        password_candidate = request.form['doctor_password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM doctors WHERE doctor_username =%s", [doctor_username])

        # Execute queries depending on results above
        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            doctor_password = data['doctor_password']

            # Compare passwords
            if sha256_crypt.verify(password_candidate, doctor_password):
                session['doctor_logged_in'] = True
                session['username'] = doctor_username

                flash('You are logged in!', 'success')
                return redirect(url_for('doctordashboard'))

            else:
                flash('Invalid password!', 'danger')
                return render_template('doctor/doctorlogin.html')

        else:
            flash('Username not found!', 'danger')
            return render_template('doctor/doctorlogin.html')

    return render_template('doctor/doctorlogin.html')


# Checked if doctor logged in
def doctor_is_logged_in(g):
    @wraps(g)
    def wrap(*args, **kwargs):
        if 'doctor_logged_in' in session:
            return g(*args, **kwargs)
        else:
            flash('Unauthorised, Please login!', 'danger')
            return redirect(url_for('doctorlogin'))

    return wrap


# Doctor Logout
@app.route('/doctorlogout')
def doctorlogout():
    # Clear any session that is active
    session.clear()
    flash('You are now logged out!', 'success')
    return redirect(url_for('doctorlogin'))


# Doctor Dashboard
@app.route('/doctordashboard')
@doctor_is_logged_in
def doctordashboard():
    # Retrieve username from the session
    doctor_username = session.get('username', None)

    # Create cursor
    cur = mysql.connection.cursor()

    # Get doctors with the same username as the session and retrieve their data
    result = cur.execute("SELECT * FROM doctors WHERE doctor_username =%s", [doctor_username])

    doctor_data = cur.fetchall()

    # Execute query depending on results
    if result > 0:
        return render_template('/doctor/doctordashboard.html', doctor_data=doctor_data)
    else:
        flash('No doctor found!', 'danger')
        return render_template('/doctor/doctordashboard.html')


# Add a Patient Form Class
class AddPatientForm(Form):
    first_name = StringField('First Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                             render_kw={"placeholder": "Enter First Name"})
    last_name = StringField('Last Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                            render_kw={"placeholder": "Enter Last Name"})
    address = StringField('Address', validators=[DataRequired(), validators.Length(min=1, max=100)],
                          render_kw={"placeholder": "Enter Address"})
    town_name = StringField('Town Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                            render_kw={"placeholder": "Enter Town"})
    county_name = SelectField('County Name', choices=[('Antrim', 'Antrim'), ('Armagh', 'Armagh'), ('Down', 'Down'),
                                                      ('Derry/Londonderry', 'Derry/Londonderry'),
                                                      ('Fermanagh', 'Fermanagh'), ('Tyrone', 'Tyrone')],
                              validators=[DataRequired()])
    postcode = StringField('Postcode', validators=[DataRequired(), postcode_validator()],
                           render_kw={"placeholder": "Enter Postcode (In caps without spaces)"})
    telephone_number = TelField('Telephone Number', validators=[DataRequired(), validators.Length(min=11, max=11)],
                                render_kw={"placeholder": "Enter Telephone Number"})
    email_address = EmailField('Email Address', validators=[DataRequired()],
                               render_kw={"placeholder": "Enter Valid Email address"})
    patient_username = StringField('Username', render_kw={"placeholder": "Enter Username"}, validators=[DataRequired(),
                                                                                                        EqualTo(
                                                                                                            'confirm_patient_username',
                                                                                                            message='Usernames Do Not Match')])
    confirm_patient_username = StringField('Confirm Username', render_kw={"placeholder": "Re Enter Username"})
    patient_password = PasswordField('Password', render_kw={"placeholder": "Enter Password"},
                                     validators=[DataRequired(),
                                                 EqualTo('confirm_patient_password', message='Passwords Do Not Match')])
    confirm_patient_password = PasswordField('Confirm Password', render_kw={"placeholder": "Re Enter Password"})


# Add a patient
@app.route('/addpatient', methods=['GET', 'POST'])
@doctor_is_logged_in
def addpatient():
    # Get the patient register form
    form = AddPatientForm(request.form)

    if request.method == 'POST' and form.validate():
        first_name = form.first_name.data
        last_name = form.last_name.data
        address = form.address.data
        town_name = form.town_name.data
        county_name = form.county_name.data
        postcode = form.postcode.data
        telephone_number = form.telephone_number.data
        email_address = form.email_address.data
        patient_username = form.patient_username.data
        patient_password = sha256_crypt.encrypt(str(form.patient_password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Get the relevant IDs from their respective tables
        result = cur.execute("SELECT * FROM patients WHERE patient_username =%s", [form.patient_username.data])
        result_email = cur.execute("SELECT * FROM patients WHERE email_address =%s", [form.email_address.data])

        # Get the doctors username
        username = session.get('username', None)

        # Get the current doctors ID
        doctor_result = cur.execute("SELECT doctor_id FROM doctors WHERE doctor_username =%s", [username])
        doctor_id_result = cur.fetchone()

        # Get the current doctors centre
        centre_result = cur.execute("SELECT centre_id FROM doctors WHERE doctor_username =%s", [username])
        centre_id_result = cur.fetchone()

        # Execute queries depending on database values
        if result == 0 and result_email == 0:
            cur.execute(
                "INSERT INTO patients(first_name, last_name, centre_id, doctor_id, address, town_name, county_name, postcode, telephone_number, email_address, patient_username, patient_password) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (first_name, last_name, centre_id_result.get('centre_id'), doctor_id_result.get('doctor_id'), address,
                 town_name, county_name, postcode, telephone_number, email_address, patient_username, patient_password))

            # Commit to DB
            mysql.connection.commit()

            # Close connection
            cur.close()

            flash('The patient has been registered and can now log in!', 'success')
            return redirect(url_for('addpatient'))

        else:
            flash('Username/Email already exists!', 'danger')
            return redirect(url_for('addpatient'))

    return render_template('/doctor/addpatient.html', form=form)


# Search Patient Form
class SearchPatientForm(Form):
    search_criteria = StringField(validators=[DataRequired(), validators.Length(min=1, max=50)],
                                  render_kw={"placeholder": "Enter ID or Patient Name to Search"})


# Search patients
@app.route('/patientsearch', methods=['GET', 'POST'])
@doctor_is_logged_in
def patientsearch():
    if request.method == 'POST':
        # Get the form field
        search_criteria = request.form['search_criteria']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get results depending on search criteria
        result = cur.execute("SELECT * FROM patients WHERE concat(first_name, ' ', last_name) =%s", [search_criteria])

        # Execute queries depending on results
        if result > 0:
            session['search_executed'] = True
            session['results'] = search_criteria
            flash('Here are the results!', 'success')
            return redirect(url_for('patientsearchresult'))

        else:
            flash('No details match, please try again!', 'danger')
            return render_template('doctor/patientsearch.html')

    return render_template('doctor/patientsearch.html')


# Check if there has been a search
def search_executed(z):
    @wraps(z)
    def wrap(*args, **kwargs):
        if 'search_executed' in session:
            return z(*args, **kwargs)
        else:
            flash('Please enter a search criteria!', 'danger')
            return redirect(url_for('patientsearch'))

    return wrap


# Search results
@app.route('/patientsearchresult')
@search_executed
def patientsearchresult():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get the search result
    get_search_result = session.get('results', None)

    # Get patients
    patient_result = cur.execute("SELECT patient_id FROM patients WHERE concat(first_name, ' ', last_name) =%s",
                                 [get_search_result])
    patient_id_result = cur.fetchone()

    # Get details
    result = cur.execute("SELECT * FROM patients WHERE patient_id =%s", [patient_id_result.get('patient_id')])
    patient_data = cur.fetchall()

    if result > 0:
        return render_template('doctor/patientsearchresult.html', patient_data=patient_data)
    else:
        flash("No patients found!", 'danger')
        return render_template('doctor/patientsearchresult.html')


# View patients
@app.route('/viewpatients')
@doctor_is_logged_in
def viewpatients():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get the doctors username
    doctor_username = session.get('username', None)

    # Get the current doctors ID
    doctor_result = cur.execute("SELECT doctor_id FROM doctors WHERE doctor_username =%s", [doctor_username])
    doctor_id_result = cur.fetchone()

    # Get patients
    result = cur.execute("SELECT * FROM patients WHERE doctor_id =%s", [doctor_id_result.get('doctor_id')])
    patients = cur.fetchall()

    if result > 0:
        return render_template('doctor/viewpatients.html', patients=patients)
    else:
        flash("No patients found!", 'danger')
        return render_template('doctor/viewpatients.html')


# Add appointment form class
class AddAppointment(Form):
    today_date = date.today()
    tomorrow_date = today_date + timedelta(days=1)

    appointment_patient_name = StringField('Patient Name',
                                           validators=[DataRequired(), validators.Length(min=1, max=50)],
                                           render_kw={"placeholder": "Enter Patient Name"})
    appointment_date = DateField('Appointment Date', format='%Y-%m-%d', default=tomorrow_date,
                                 validators=[DateRange(min=tomorrow_date, message="Please select a date after today"),
                                             DataRequired()])
    appointment_time = SelectField('Appointment Time',
                                   choices=[('09:00', '09:00'), ('09:30', '09:30'), ('10:00', '10:00'),
                                            ('10:30', '10:30'), ('11:00', '11:00'), ('11:30', '11:30'),
                                            ('12:00', '12:00'), ('12:30', '12:30'), ('13:00', '13:00'),
                                            ('13:30', '13:30'), ('14:00', '14:00'), ('14:30', '14:30'),
                                            ('15:00', '15:00'), ('15:30', '15:30'), ('16:00', '16:00'),
                                            ('16:30', '16:30')], validators=[DataRequired()])


# Add an appointment
@app.route('/addappointment', methods=['GET', 'POST'])
@doctor_is_logged_in
def doctorbook():
    form = AddAppointment(request.form)

    if request.method == 'POST' and form.validate():
        appointment_patient_name = form.appointment_patient_name.data
        appointment_date = form.appointment_date.data
        appointment_time = form.appointment_time.data
        doctor_username = session.get('username', None)

        # Create cursor
        cur = mysql.connection.cursor()

        # Get the patient ID, doctor ID and centre ID of patient
        appointment_patient_id = cur.execute(
            "SELECT patient_id FROM patients WHERE concat(first_name, ' ', last_name) =%s", [appointment_patient_name])
        actual_patient_id = cur.fetchone()
        appointment_doctor_id = cur.execute("SELECT doctor_id FROM doctors WHERE doctor_username =%s",
                                            [doctor_username])
        actual_doctor_id = cur.fetchone()
        appointment_centre_id = cur.execute("SELECT centre_id FROM doctors WHERE doctor_username =%s",
                                            [doctor_username])
        actual_centre_id = cur.fetchone()

        # Get the patients doctor ID
        patient_doctor_id = cur.execute("SELECT doctor_id FROM patients WHERE concat(first_name, ' ', last_name) =%s",
                                        [appointment_patient_name])
        actual_patient_doctor_id = cur.fetchone()

        # Check if there is already an appointment with the patients doctor at the same time and date
        confirmed_booking = cur.execute(
            "SELECT appointment_id FROM appointments WHERE appointment_time = %s AND appointment_date = %s AND doctor_id = %s",
            (appointment_time, appointment_date, actual_doctor_id.get('doctor_id')))

        # Make sure the patient is registered to the doctor
        if actual_doctor_id == actual_patient_doctor_id:

            # If the selected appointment is available
            if confirmed_booking == 0:
                # Execute query
                cur.execute(
                    "INSERT INTO appointments(appointment_date, appointment_time, patient_id, doctor_id, centre_id) VALUES(%s, %s, %s, %s, %s)",
                    (appointment_date, appointment_time, actual_patient_id.get('patient_id'),
                     actual_doctor_id.get('doctor_id'), actual_centre_id.get('centre_id')))

                # Making sure the appointment is made for a weekday
                if appointment_date.weekday() == 0 or appointment_date.weekday() == 1 or appointment_date.weekday() == 2 or appointment_date.weekday() == 3 or appointment_date.weekday() == 4:

                    # Commit to DB
                    mysql.connection.commit()

                    # Close connection
                    cur.close()

                    flash('Appointment made successfully!', 'success')
                    return redirect(url_for('doctorbook'))

                else:
                    flash('Sorry, appointments cannot be made for a Saturday/Sunday!', 'danger')
                    return render_template('/doctor/addappointment.html', form=form)

            else:
                flash('Sorry, appointment unavailable!', 'danger')
                render_template('/doctor/addappointment.html', form=form)
        else:
            flash('Patient is not registered to this doctor!', 'danger')
            return render_template('/doctor/addappointment.html', form=form)

    return render_template('/doctor/addappointment.html', form=form)


# View Todays Appointments
@app.route('/todaysdoctorsappointments')
@doctor_is_logged_in
def todaysdoctorsappointments():
    # Get the doctors username and todays date
    doctor_username = session.get('username', None)
    today_date = date.today()

    # Create Cursor
    cur = mysql.connection.cursor()

    # Get the doctor ID of the logged in doctor
    cur.execute("SELECT doctor_id FROM doctors WHERE doctor_username =%s", [doctor_username])
    actual_doctor_id = cur.fetchone()

    # Get appointment data
    result = cur.execute(
        "SELECT * FROM appointments WHERE doctor_id =%s AND appointment_date =%s ORDER BY appointment_time ASC",
        ([actual_doctor_id.get('doctor_id')], today_date))
    appointment_data = cur.fetchall()

    # Get patient info from patients table
    cur.execute("SELECT patient_id FROM patients WHERE doctor_id =%s", [actual_doctor_id.get('doctor_id')])
    actual_patient_id = cur.fetchone()

    # Get all patient data
    patient_result = cur.execute("SELECT * FROM patients WHERE patient_id =%s", [actual_patient_id.get('patient_id')])
    patient_data = cur.fetchall()

    # If there are any appointments for today, show them
    if result > 0 and patient_result > 0:
        return render_template('/doctor/todaysdoctorsappointments.html', appointment_data=appointment_data,
                               patient_data=patient_data)
    else:
        flash('No appointments found', 'danger')
        return render_template('/doctor/todaysdoctorsappointments.html')


# View Upcoming Appointments
@app.route('/upcomingdoctorsappointments')
@doctor_is_logged_in
def upcomingdoctorsappointments():
    # Get the doctors username and todays date
    doctor_username = session.get('username', None)
    today_date = date.today()

    # Create Cursor
    cur = mysql.connection.cursor()

    # Get the doctor ID of the logged in doctor
    cur.execute("SELECT doctor_id FROM doctors WHERE doctor_username =%s", [doctor_username])
    actual_doctor_id = cur.fetchone()

    # Get appointment data
    result = cur.execute(
        "SELECT * FROM appointments WHERE doctor_id =%s AND appointment_date >%s ORDER BY appointment_date ASC",
        ([actual_doctor_id.get('doctor_id')], today_date))
    appointment_data = cur.fetchall()

    # If there are any appointments for today, show them
    if result > 0:
        return render_template('/doctor/upcomingdoctorsappointments.html', appointment_data=appointment_data)
    else:
        flash('No appointments found!', 'danger')
        return render_template('/doctor/upcomingdoctorsappointments.html')


# Delete Upcoming Appointment
@app.route('/delete_doctor_appointment/<int:appointment_id>', methods=['POST'])
@doctor_is_logged_in
def delete_doctor_appointment(appointment_id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute, commit and close the delete query given the selected appointment
    cur.execute("DELETE FROM appointments WHERE appointment_id =%s", [appointment_id])
    mysql.connection.commit()
    cur.close()

    # Display a message to show the appointment has been deleted
    flash('Appointment deleted!', 'success')

    # Reload the upcoming appointments with the new data
    return redirect(url_for('upcomingdoctorsappointments'))


# View Previous Appointments
@app.route('/previousdoctorsappointments')
@doctor_is_logged_in
def previousdoctorsappointments():
    # Get the doctors username and todays date
    doctor_username = session.get('username', None)
    today_date = date.today()

    # Create Cursor
    cur = mysql.connection.cursor()

    # Get the doctor ID of the logged in doctor
    cur.execute("SELECT doctor_id FROM doctors WHERE doctor_username =%s", [doctor_username])
    actual_doctor_id = cur.fetchone()

    # Get appointment data
    result = cur.execute(
        "SELECT * FROM appointments WHERE doctor_id =%s AND appointment_date <%s ORDER BY appointment_date ASC",
        ([actual_doctor_id.get('doctor_id')], today_date))
    appointment_data = cur.fetchall()

    # Get patient info from patients table
    cur.execute("SELECT patient_id FROM patients WHERE doctor_id =%s", [actual_doctor_id.get('doctor_id')])
    actual_patient_id = cur.fetchone()

    # Get all patient data
    patient_result = cur.execute("SELECT * FROM patients WHERE patient_id =%s", [actual_patient_id.get('patient_id')])
    patient_data = cur.fetchall()

    # If there are any appointments for today, show them
    if result > 0 and patient_result > 0:
        return render_template('/doctor/previousdoctorsappointments.html', appointment_data=appointment_data,
                               patient_data=patient_data)
    else:
        flash('No appointments found', 'danger')
        return render_template('/doctor/previousdoctorsappointments.html')


# Doctor Details
@app.route('/doctordetails')
@doctor_is_logged_in
def doctordetails():
    # Get the doctors username
    doctor_username = session.get('username', None)

    # Create cursor
    cur = mysql.connection.cursor()

    # Get centre ID from doctors table
    cur.execute("SELECT centre_id FROM doctors WHERE doctor_username =%s", [doctor_username])
    actual_centre_id = cur.fetchone()

    # Get doctor data
    result = cur.execute("SELECT * FROM doctors WHERE doctor_username =%s", [doctor_username])
    doctor_data = cur.fetchall()

    # Get centre records
    centre_result = cur.execute("SELECT * FROM centres WHERE centre_id =%s", [actual_centre_id.get('centre_id')])
    centre_data = cur.fetchall()

    # Show the doctors details
    if result > 0 and centre_result > 0:
        return render_template('/doctor/doctordetails.html', doctor_data=doctor_data, centre_data=centre_data)
    else:
        flash('No details found', 'danger')
        return render_template('/doctor/doctordetails.html')


# --------------------------------------- ADMIN FUNCTIONALITY ---------------------------------------

# Register Admin Form Class
class RegisterAdminForm(Form):
    admin_first_name = StringField('First Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                                   render_kw={"placeholder": "Enter First Name"})
    admin_last_name = StringField('Last Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                                  render_kw={"placeholder": "Enter Last Name"})
    admin_address = StringField('Address', validators=[DataRequired(), validators.Length(min=1, max=100)],
                                render_kw={"placeholder": "Enter Address"})
    admin_town_name = StringField('Town Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                                  render_kw={"placeholder": "Enter Town"})
    admin_county_name = SelectField('County Name',
                                    choices=[('Antrim', 'Antrim'), ('Armagh', 'Armagh'), ('Down', 'Down'),
                                             ('Derry/Londonderry', 'Derry/Londonderry'), ('Fermanagh', 'Fermanagh'),
                                             ('Tyrone', 'Tyrone')], validators=[DataRequired()])
    admin_postcode = StringField('Postcode', validators=[DataRequired(), postcode_validator()],
                                 render_kw={"placeholder": "Enter Postcode (In caps without spaces)"})
    admin_telephone_number = TelField('Telephone Number',
                                      validators=[DataRequired(), validators.Length(min=11, max=11)],
                                      render_kw={"placeholder": "Enter Telephone Number"})
    admin_email_address = EmailField('Email Address', validators=[DataRequired()],
                                     render_kw={"placeholder": "Enter Valid Email address"})
    admin_username = StringField('Username', render_kw={"placeholder": "Enter Username"}, validators=[DataRequired(),
                                                                                                      EqualTo(
                                                                                                          'confirm_admin_username',
                                                                                                          message='Usernames Do Not Match')])
    confirm_admin_username = StringField('Confirm Username', render_kw={"placeholder": "Re Enter Username"})
    admin_password = PasswordField('Password', render_kw={"placeholder": "Enter Password"}, validators=[DataRequired(),
                                                                                                        EqualTo(
                                                                                                            'confirm_admin_password',
                                                                                                            message='Passwords Do Not Match')])
    confirm_admin_password = PasswordField('Confirm Password', render_kw={"placeholder": "Re Enter Password"})


# Admin Register
@app.route('/adminregister', methods=['GET', 'POST'])
def adminregister():
    # Get the register form
    form = RegisterAdminForm(request.form)

    if request.method == 'POST' and form.validate():
        admin_first_name = form.admin_first_name.data
        admin_last_name = form.admin_last_name.data
        admin_address = form.admin_address.data
        admin_town_name = form.admin_town_name.data
        admin_county_name = form.admin_county_name.data
        admin_postcode = form.admin_postcode.data
        admin_telephone_number = form.admin_telephone_number.data
        admin_email_address = form.admin_email_address.data
        admin_username = form.admin_username.data
        admin_password = sha256_crypt.encrypt(str(form.admin_password.data))

        # Create Cursor
        cur = mysql.connection.cursor()

        # Get the relevant IDs from their respective tables
        result = cur.execute("SELECT * FROM admins WHERE admin_username =%s", [form.admin_username.data])
        result_email = cur.execute("SELECT * FROM admins WHERE admin_email_address =%s",
                                   [form.admin_email_address.data])

        # Execute queries depending on database values
        if result == 0 and result_email == 0:
            cur.execute(
                "INSERT INTO admins(admin_first_name, admin_last_name, admin_address, admin_town_name, admin_county_name, admin_postcode, admin_telephone_number, admin_email_address, admin_username, admin_password) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (admin_first_name, admin_last_name, admin_address, admin_town_name, admin_county_name, admin_postcode,
                 admin_telephone_number, admin_email_address, admin_username, admin_password))

            # Commit to DB
            mysql.connection.commit()

            # Close connection
            cur.close()

            flash('You are now registered and can now log in!', 'success')
            return redirect(url_for('adminlogin'))

        else:
            flash('Username/Email already exists!', 'danger')
            return redirect(url_for('adminregister'))

    return render_template('admin/register.html', form=form)


# Admin Login
@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        # Get form fields
        username = request.form['admin_username']
        password_candidate = request.form['admin_password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get admin by username
        result = cur.execute("SELECT * FROM admins WHERE admin_username =%s", [username])

        # Execute queries depending on results above
        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            admin_password = data['admin_password']

            # Compare passwords
            if sha256_crypt.verify(password_candidate, admin_password):
                session['admin_logged_in'] = True
                session['username'] = username

                flash('You are logged in!', 'success')
                return redirect(url_for('admindashboard'))

            else:
                flash('Invalid password!', 'danger')
                return render_template('/admin/login.html')
        else:
            flash('Username not found!', 'danger')
            return render_template('/admin/login.html')

    return render_template('/admin/login.html')


# Check if admin is logged in
def admin_is_logged_in(h):
    @wraps(h)
    def wrap(*args, **kwargs):
        # If there is a session in progress
        if 'admin_logged_in' in session:
            return h(*args, **kwargs)
        else:
            flash('Unauthorised, Please login!', 'danger')
            return redirect(url_for('adminlogin'))

    return wrap


# Admin Logout
@app.route('/adminlogout')
def adminlogout():
    # Clear any session that is active
    session.clear()
    flash('You are now logged out!', 'success')
    return redirect(url_for('adminlogin'))


# Admin Dashboard
@app.route('/admindashboard')
@admin_is_logged_in
def admindashboard():
    # Retrieve username from session
    admin_username = session.get('username', None)

    # Create cursor
    cur = mysql.connection.cursor()

    # Get admins with the same username and retrieve their data
    result = cur.execute("SELECT * FROM admins WHERE admin_username =%s", [admin_username])

    admin_data = cur.fetchall()

    # Execute query depending on results
    if result > 0:
        return render_template('/admin/dashboard.html', admin_data=admin_data)
    else:
        flash('No admin found!', 'danger')
        return render_template('/admin/dashboard.html')


# Add a patient form class
class AdminAddPatientForm(Form):
    first_name = StringField('First Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                             render_kw={"placeholder": "Enter First Name"})
    last_name = StringField('Last Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                            render_kw={"placeholder": "Enter Last Name"})
    centre_name = StringField('Centre Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                              render_kw={"placeholder": "Enter Centre Name that you wish to be registered to"})
    doctor_name = StringField('Doctor Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                              render_kw={"placeholder": "Enter Doctor Name"})
    address = StringField('Address', validators=[DataRequired(), validators.Length(min=1, max=100)],
                          render_kw={"placeholder": "Enter Address"})
    town_name = StringField('Town Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                            render_kw={"placeholder": "Enter Town"})
    county_name = SelectField('County Name', choices=[('Antrim', 'Antrim'), ('Armagh', 'Armagh'), ('Down', 'Down'),
                                                      ('Derry/Londonderry', 'Derry/Londonderry'),
                                                      ('Fermanagh', 'Fermanagh'), ('Tyrone', 'Tyrone')],
                              validators=[DataRequired()])
    postcode = StringField('Postcode', validators=[DataRequired(), postcode_validator()],
                           render_kw={"placeholder": "Enter Postcode (In caps without spaces)"})
    telephone_number = TelField('Telephone Number', validators=[DataRequired(), validators.Length(min=11, max=11)],
                                render_kw={"placeholder": "Enter Telephone Number"})
    email_address = EmailField('Email Address', validators=[DataRequired()],
                               render_kw={"placeholder": "Enter Valid Email address"})
    patient_username = StringField('Username', render_kw={"placeholder": "Enter Username"}, validators=[DataRequired(),
                                                                                                        EqualTo(
                                                                                                            'confirm_patient_username',
                                                                                                            message='Usernames Do Not Match')])
    confirm_patient_username = StringField('Confirm Username', render_kw={"placeholder": "Re Enter Username"})
    patient_password = PasswordField('Password', render_kw={"placeholder": "Enter Password"},
                                     validators=[DataRequired(),
                                                 EqualTo('confirm_patient_password', message='Passwords Do Not Match')])
    confirm_patient_password = PasswordField('Confirm Password', render_kw={"placeholder": "Re Enter Password"})


# Add patient
@app.route('/adminaddpatient', methods=['GET', 'POST'])
@admin_is_logged_in
def adminaddpatient():
    # Get the add patient form
    form = AdminAddPatientForm(request.form)

    if request.method == 'POST' and form.validate():
        first_name = form.first_name.data
        last_name = form.last_name.data
        address = form.address.data
        town_name = form.town_name.data
        county_name = form.county_name.data
        postcode = form.postcode.data
        telephone_number = form.telephone_number.data
        email_address = form.email_address.data
        patient_username = form.patient_username.data
        patient_password = sha256_crypt.encrypt(str(form.patient_password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Get the relevant IDs from their respective tables
        result = cur.execute("SELECT * FROM patients WHERE patient_username =%s", [form.patient_username.data])
        result_email = cur.execute("SELECT * FROM patients WHERE email_address =%s", [form.email_address.data])

        # Get the centre ID of the entered centre
        centre_result = cur.execute("SELECT centre_id FROM centres WHERE centre_name =%s", [form.centre_name.data])
        centre_id_result = cur.fetchone()

        # Get the doctor ID of the entered doctor
        doctor_result = cur.execute(
            "SELECT doctor_id FROM doctors WHERE concat(doctor_first_name, ' ', doctor_last_name) =%s",
            [form.doctor_name.data])
        doctor_id_result = cur.fetchone()

        # Execute queries depending on database values
        if doctor_result == 1:
            if centre_result == 1:
                if result == 0 and result_email == 0:
                    cur.execute(
                        "INSERT INTO patients(first_name, last_name, centre_id, doctor_id, address, town_name, county_name, postcode, telephone_number, email_address, patient_username, patient_password) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (first_name, last_name, centre_id_result.get('centre_id'), doctor_id_result.get('doctor_id'),
                         address, town_name, county_name, postcode, telephone_number, email_address, patient_username,
                         patient_password))

                    # Commit to DB
                    mysql.connection.commit()

                    # Close connection
                    cur.close()

                    flash('Patient has been added!', 'success')
                    return redirect(url_for('adminviewpatients'))

                else:
                    flash('Username/Email already exists!', 'danger')
                    return redirect(url_for('adminaddpatient'))

            else:
                flash('Centre name not found!', 'danger')
                return redirect(url_for('adminaddpatient'))

        else:
            flash('Doctor name not found!', 'danger')
            return redirect(url_for('adminaddpatient'))

    return render_template('/admin/addpatient.html', form=form)


# View all patients
@app.route('/adminviewpatients')
@admin_is_logged_in
def adminviewpatients():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get patients
    result = cur.execute("SELECT * FROM patients")
    patients = cur.fetchall()

    if result > 0:
        return render_template('admin/viewpatients.html', patients=patients)
    else:
        flash('No patients found!', 'danger')
        return render_template('admin/viewpatients.html')


# Add Doctor Form Class
class AdminAddDoctorForm(Form):
    doctor_first_name = StringField('First Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                                    render_kw={"placeholder": "Enter your First Name"})
    doctor_last_name = StringField('Last Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                                   render_kw={"placeholder": "Enter your Last Name"})
    centre_name = StringField('Centre Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                              render_kw={"placeholder": "Enter the Centre Name that you wish to be registered to"})
    doctor_address = StringField('Address', validators=[DataRequired(), validators.Length(min=1, max=100)],
                                 render_kw={"placeholder": "Enter your Address"})
    doctor_town_name = StringField('Town Name', validators=[DataRequired(), validators.Length(min=1, max=50)],
                                   render_kw={"placeholder": "Enter your Town"})
    doctor_county_name = SelectField('County Name',
                                     choices=[('Antrim', 'Antrim'), ('Armagh', 'Armagh'), ('Down', 'Down'),
                                              ('Derry/Londonderry', 'Derry/Londonderry'), ('Fermanagh', 'Fermanagh'),
                                              ('Tyrone', 'Tyrone')], validators=[DataRequired()])
    doctor_postcode = StringField('Postcode', validators=[DataRequired(), postcode_validator()],
                                  render_kw={"placeholder": "Enter your Postcode (In caps without spaces)"})
    doctor_telephone_number = TelField('Telephone Number',
                                       validators=[DataRequired(), validators.Length(min=11, max=11)],
                                       render_kw={"placeholder": "Enter your Telephone Number"})
    doctor_email_address = EmailField('Email Address', validators=[DataRequired()],
                                      render_kw={"placeholder": "Enter a valid Email address"})
    doctor_username = StringField('Username', render_kw={"placeholder": "Enter your Username"},
                                  validators=[DataRequired(),
                                              EqualTo('confirm_doctor_username', message='Usernames do not match')])
    confirm_doctor_username = StringField('Confirm Username', render_kw={"placeholder": "Re-enter Username"})
    doctor_password = PasswordField('Password', render_kw={"placeholder": "Enter your Password"},
                                    validators=[DataRequired(),
                                                EqualTo('confirm_doctor_password', message='Passwords do not match')])
    confirm_doctor_password = PasswordField('Confirm Password', render_kw={"placeholder": "Re enter Password"})


# Add Doctor
@app.route('/adminadddoctor', methods=['GET', 'POST'])
@admin_is_logged_in
def adminadddoctor():
    # Get the add doctor form
    form = AdminAddDoctorForm(request.form)

    if request.method == 'POST' and form.validate():
        doctor_first_name = form.doctor_first_name.data
        doctor_last_name = form.doctor_last_name.data
        doctor_address = form.doctor_address.data
        doctor_town_name = form.doctor_town_name.data
        doctor_county_name = form.doctor_county_name.data
        doctor_postcode = form.doctor_postcode.data
        doctor_telephone_number = form.doctor_telephone_number.data
        doctor_email_address = form.doctor_email_address.data
        doctor_username = form.doctor_username.data
        doctor_password = sha256_crypt.encrypt(str(form.doctor_password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Get the relevant IDs from their respective tables
        result = cur.execute("SELECT * FROM doctors WHERE doctor_username =%s", [form.doctor_username.data])
        result_email = cur.execute("SELECT * FROM doctors WHERE doctor_email_address =%s",
                                   [form.doctor_email_address.data])

        # Get the centre ID of the entered centre
        centre_result = cur.execute("SELECT centre_id FROM centres WHERE centre_name =%s", [form.centre_name.data])
        centre_id_result = cur.fetchone()

        # Execute queries depending on database values
        if centre_result == 1:
            if result == 0 and result_email == 0:
                cur.execute(
                    "INSERT INTO doctors(doctor_first_name, doctor_last_name, centre_id, doctor_address, doctor_town_name, doctor_county_name, doctor_postcode, doctor_telephone_number, doctor_email_address, doctor_username, doctor_password) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (doctor_first_name, doctor_last_name, centre_id_result.get('centre_id'), doctor_address,
                     doctor_town_name, doctor_county_name, doctor_postcode, doctor_telephone_number,
                     doctor_email_address, doctor_username, doctor_password))

                # Commit to DB
                mysql.connection.commit()

                # Close connection
                cur.close()

                flash('Patient has been added', 'success')
                return redirect(url_for('adminviewdoctors'))

            else:
                flash('Username/Email already exists!', 'danger')
                return redirect(url_for('adminadddoctor'))
        else:
            flash('Centre name not found!', 'danger')
            return redirect(url_for('adminadddoctor'))

    return render_template('/admin/adddoctor.html', form=form)


# View all doctors
@app.route('/adminviewdoctors')
@admin_is_logged_in
def adminviewdoctors():
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get doctors
    result = cur.execute("SELECT * FROM doctors")
    doctors = cur.fetchall()

    if result > 0:
        return render_template('admin/viewdoctors.html', doctors=doctors)
    else:
        flash('No doctors found!', 'danger')
        return render_template('admin/viewdoctors.html')


# Add Appointment Form Class
class AdminAddAppointmentForm(Form):
    today_date = date.today()
    tomorrow_date = today_date + timedelta(days=1)

    appointment_patient_name = StringField('Patient Name',
                                           validators=[DataRequired(), validators.Length(min=1, max=50)],
                                           render_kw={"placeholder": "Enter Patient Name"})
    appointment_date = DateField('Appointment Date', format='%Y-%m-%d', default=tomorrow_date,
                                 validators=[DateRange(min=tomorrow_date, message="Please select a date after today"),
                                             DataRequired()])
    appointment_time = SelectField('Appointment Time',
                                   choices=[('09:00', '09:00'), ('09:30', '09:30'), ('10:00', '10:00'),
                                            ('10:30', '10:30'), ('11:00', '11:00'), ('11:30', '11:30'),
                                            ('12:00', '12:00'), ('12:30', '12:30'), ('13:00', '13:00'),
                                            ('13:30', '13:30'), ('14:00', '14:00'), ('14:30', '14:30'),
                                            ('15:00', '15:00'), ('15:30', '15:30'), ('16:00', '16:00'),
                                            ('16:30', '16:30')], validators=[DataRequired()])


# Add an appointment
@app.route('/adminaddappointment', methods=['GET', 'POST'])
@admin_is_logged_in
def adminaddappointment():
    form = AdminAddAppointmentForm(request.form)

    if request.method == 'POST' and form.validate():
        appointment_patient_name = form.appointment_patient_name.data
        appointment_date = form.appointment_date.data
        appointment_time = form.appointment_time.data
        doctor_username = session.get('username', None)

        # Create cursor
        cur = mysql.connection.cursor()

        # Get the patient ID, doctor ID and centre ID of patient
        appointment_patient_id = cur.execute(
            "SELECT patient_id FROM patients WHERE concat(first_name, ' ', last_name) =%s", [appointment_patient_name])
        actual_patient_id = cur.fetchone()
        appointment_doctor_id = cur.execute(
            "SELECT doctor_id FROM patients WHERE concat(first_name, ' ', last_name) =%s", [appointment_patient_name])
        actual_doctor_id = cur.fetchone()
        appointment_centre_id = cur.execute(
            "SELECT centre_id FROM patients WHERE concat(first_name, ' ', last_name) =%s", [appointment_patient_name])
        actual_centre_id = cur.fetchone()

        # Check if there is already an appointment with the patients doctor at the same time and date
        confirmed_booking = cur.execute(
            "SELECT appointment_id FROM appointments WHERE appointment_time = %s AND appointment_date = %s AND doctor_id = %s",
            (appointment_time, appointment_date, actual_doctor_id.get('doctor_id')))

        # If the selected appointment is available
        if confirmed_booking == 0:
            # Execute query
            cur.execute(
                "INSERT INTO appointments(appointment_date, appointment_time, patient_id, doctor_id, centre_id) VALUES(%s, %s, %s, %s, %s)",
                (appointment_date, appointment_time, actual_patient_id.get('patient_id'),
                 actual_doctor_id.get('doctor_id'), actual_centre_id.get('centre_id')))

            # Making sure the appointment is made for a weekday
            if appointment_date.weekday() == 0 or appointment_date.weekday() == 1 or appointment_date.weekday() == 2 or appointment_date.weekday() == 3 or appointment_date.weekday() == 4:

                # Commit to DB
                mysql.connection.commit()

                # Close connection
                cur.close()

                flash('Appointment made successfully!', 'success')
                return redirect(url_for('adminaddappointment'))

            else:
                flash('Sorry, appointments cannot be made for a Saturday/Sunday', 'danger')
                return render_template('/admin/addappointment.html', form=form)

        else:
            flash('Sorry, appointment unavailable', 'danger')
            render_template('/admin/addappointment.html', form=form)

    return render_template('/admin/addappointment.html', form=form)


# View Todays Appointments
@app.route('/admintodaysappointments')
@admin_is_logged_in
def admintodaysappointments():
    # Get todays date
    today_date = date.today()

    # Create cursor
    cur = mysql.connection.cursor()

    # Get all appointment data
    result = cur.execute("SELECT * FROM appointments WHERE appointment_date =%s ORDER BY appointment_time ASC",
                         [today_date])
    appointment_data = cur.fetchall()

    # If there are any appointments for today, show them
    if result > 0:
        return render_template('/admin/todayappointments.html', appointment_data=appointment_data)
    else:
        flash('No appointments found!', 'danger')
        return render_template('/admin/todayappointments.html')


# View Previous Appointments
@app.route('/adminpreviousappointments')
@admin_is_logged_in
def adminpreviousappointments():
    # Get todays date
    today_date = date.today()

    # Create cursor
    cur = mysql.connection.cursor()

    # Get all appointment data
    result = cur.execute("SELECT * FROM appointments WHERE appointment_date <%s ORDER BY appointment_time ASC",
                         [today_date])
    appointment_data = cur.fetchall()

    # If there are any appointments for today, show them
    if result > 0:
        return render_template('/admin/previousappointments.html', appointment_data=appointment_data)
    else:
        flash('No appointments found', 'danger')
        return render_template('/admin/previousappointments.html')


# View Upcoming Appointments
@app.route('/adminupcomingappointments')
@admin_is_logged_in
def adminupcomingappointments():
    # Get todays date
    today_date = date.today()

    # Create cursor
    cur = mysql.connection.cursor()

    # Get all appointment data
    result = cur.execute("SELECT * FROM appointments WHERE appointment_date >%s ORDER BY appointment_time ASC",
                         [today_date])
    appointment_data = cur.fetchall()

    # If there are any appointments for today, show them
    if result > 0:
        return render_template('/admin/upcomingappointments.html', appointment_data=appointment_data)
    else:
        flash('No appointments found', 'danger')
        return render_template('/admin/upcomingappointments.html')


# Delete Upcoming Appointment
@app.route('/admin_delete_appointment/<int:appointment_id>', methods=['POST'])
@admin_is_logged_in
def admin_delete_appointment(appointment_id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute, commit and close the delete query given the selected appointment
    cur.execute("DELETE FROM appointments WHERE appointment_id =%s", [appointment_id])
    mysql.connection.commit()
    cur.close()

    # Display a message to show the appointment has been deleted
    flash('Appointment deleted!', 'success')

    # Reload the upcoming appointments with the new data
    return redirect(url_for('adminupcomingappointments'))


# View Admin Details
@app.route('/adminviewdetails')
@admin_is_logged_in
def adminviewdetails():
    # Get the admins username
    admin_username = session.get('username', None)

    # Create cursor
    cur = mysql.connection.cursor()

    # Get admin data
    result = cur.execute("SELECT * FROM admins WHERE admin_username =%s", [admin_username])
    admin_data = cur.fetchall()

    # Show admin details
    if result > 0:
        return render_template('/admin/viewdetails.html', admin_data=admin_data)
    else:
        flash('No details found!', 'danger')
        return render_template('/admin/viewdetails.html')


# ---------------------------------------- MAIN FUNCTIONALITY ----------------------------------------

if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
