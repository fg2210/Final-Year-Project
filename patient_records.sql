-- phpMyAdmin SQL Dump
-- version 4.8.3
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Mar 06, 2019 at 04:49 PM
-- Server version: 10.1.36-MariaDB
-- PHP Version: 5.6.38

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `patient_records`
--

-- --------------------------------------------------------

--
-- Table structure for table `admins`
--

CREATE TABLE `admins` (
  `admin_id` int(11) NOT NULL COMMENT 'ID of the admin',
  `admin_first_name` varchar(50) NOT NULL COMMENT 'First name of the doctor',
  `admin_last_name` varchar(50) NOT NULL COMMENT 'Last name of the doctor',
  `admin_address` varchar(100) NOT NULL COMMENT 'The house number and street where the admin lives',
  `admin_town_name` varchar(50) NOT NULL COMMENT 'The name of the town where the admin lives',
  `admin_county_name` varchar(50) NOT NULL COMMENT 'The name of the county where the admin lives',
  `admin_postcode` varchar(15) NOT NULL COMMENT 'The postcode of the admins address',
  `admin_telephone_number` varchar(11) NOT NULL COMMENT 'The admins telephone number',
  `admin_email_address` varchar(100) NOT NULL COMMENT 'The admins email address',
  `admin_username` varchar(50) NOT NULL COMMENT 'The username of the admin',
  `admin_password` varchar(100) NOT NULL COMMENT 'The password of the admin'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `appointments`
--

CREATE TABLE `appointments` (
  `appointment_id` int(11) NOT NULL COMMENT 'ID of the appointment',
  `appointment_date` date NOT NULL COMMENT 'Date the appointment is on',
  `appointment_time` time(6) NOT NULL COMMENT 'Time of the appointment',
  `patient_id` int(11) NOT NULL COMMENT 'Which patient the appointment is for',
  `doctor_id` int(11) NOT NULL COMMENT 'Which doctor the appointment is for',
  `centre_id` int(11) NOT NULL COMMENT 'Where the appointment is available'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `centres`
--

CREATE TABLE `centres` (
  `centre_id` int(11) NOT NULL COMMENT 'ID of the health centre',
  `centre_name` varchar(100) NOT NULL COMMENT 'Name of the health centre',
  `address` varchar(100) NOT NULL COMMENT 'The address where the health centre is',
  `town_name` varchar(50) NOT NULL COMMENT 'The name of the town where the health centre is',
  `county_name` varchar(50) NOT NULL COMMENT 'The name of the county where the health centre is',
  `postcode` varchar(15) NOT NULL COMMENT 'The postcode of the centres address',
  `telephone_number` varchar(11) NOT NULL COMMENT 'The health centres telephone number'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `doctors`
--

CREATE TABLE `doctors` (
  `doctor_id` int(11) NOT NULL COMMENT 'Unique ID of the Doctor',
  `doctor_first_name` varchar(50) NOT NULL COMMENT 'First name of the doctor',
  `doctor_last_name` varchar(50) NOT NULL COMMENT 'Last name of the doctor',
  `centre_id` int(11) NOT NULL COMMENT 'The centre that the doctor is registered to',
  `doctor_address` varchar(100) NOT NULL COMMENT 'The house number and street where the doctor lives',
  `doctor_town_name` varchar(50) NOT NULL COMMENT 'The name of the town where the doctor lives',
  `doctor_county_name` varchar(50) NOT NULL COMMENT 'The name of the county where the doctor lives',
  `doctor_postcode` varchar(15) NOT NULL COMMENT 'The postcode of the doctors address',
  `doctor_telephone_number` varchar(11) NOT NULL COMMENT 'The doctors telephone number',
  `doctor_email_address` varchar(100) NOT NULL COMMENT 'The doctors email address',
  `doctor_username` varchar(50) NOT NULL COMMENT 'The username of the doctor',
  `doctor_password` varchar(100) NOT NULL COMMENT 'The password of the doctor'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `patients`
--

CREATE TABLE `patients` (
  `patient_id` int(11) NOT NULL COMMENT 'Unique ID of the patient',
  `first_name` varchar(50) NOT NULL COMMENT 'First name of the patient',
  `last_name` varchar(50) NOT NULL COMMENT 'Last name of the patient',
  `centre_id` int(11) NOT NULL COMMENT 'The centre that the patient is registered to',
  `doctor_id` int(11) NOT NULL COMMENT 'The ID of the doctor assigned to the patient',
  `address` varchar(100) NOT NULL COMMENT 'The house number and street where the patient lives',
  `town_name` varchar(50) NOT NULL COMMENT 'The name of the town where the patient lives',
  `county_name` varchar(50) NOT NULL COMMENT 'The name of the county where the patient lives',
  `postcode` varchar(15) NOT NULL COMMENT 'The postcode of the patients address',
  `telephone_number` varchar(11) NOT NULL COMMENT 'The patients telephone number',
  `email_address` varchar(100) NOT NULL COMMENT 'The patients email address',
  `patient_username` varchar(50) NOT NULL COMMENT 'The username of the patient',
  `patient_password` varchar(100) NOT NULL COMMENT 'The password of the patient'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Indexes for table `admins`
--
ALTER TABLE `admins`
  ADD PRIMARY KEY (`admin_id`),
  ADD UNIQUE KEY `admin_id` (`admin_id`);

--
-- Indexes for table `appointments`
--
ALTER TABLE `appointments`
  ADD PRIMARY KEY (`appointment_id`),
  ADD UNIQUE KEY `appointment_id` (`appointment_id`);

--
-- Indexes for table `centres`
--
ALTER TABLE `centres`
  ADD PRIMARY KEY (`centre_id`),
  ADD UNIQUE KEY `centre_id` (`centre_id`);

--
-- Indexes for table `doctors`
--
ALTER TABLE `doctors`
  ADD PRIMARY KEY (`doctor_id`),
  ADD UNIQUE KEY `doctor_id` (`doctor_id`);

--
-- Indexes for table `patients`
--
ALTER TABLE `patients`
  ADD PRIMARY KEY (`patient_id`),
  ADD UNIQUE KEY `patient_id` (`patient_id`);
  
--
-- AUTO_INCREMENT for table `appointments`
--
ALTER TABLE `admins`
  MODIFY `admin_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;
  
--
-- AUTO_INCREMENT for table `appointments`
--
ALTER TABLE `appointments`
  MODIFY `appointment_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1000;
  
--
-- AUTO_INCREMENT for table `centres`
--
ALTER TABLE `centres`
  MODIFY `centre_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2000;

--
-- AUTO_INCREMENT for table `doctors`
--
ALTER TABLE `doctors`
  MODIFY `doctor_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3000;

--
-- AUTO_INCREMENT for table `patients`
--
ALTER TABLE `patients`
  MODIFY `patient_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4000;

--
-- Constraints for tables
--
  
ALTER TABLE `doctors`
  ADD CONSTRAINT `doctors_ibfk_1` FOREIGN KEY (`centre_id`) REFERENCES `centres` (`centre_id`);
  
ALTER TABLE `patients`
  ADD CONSTRAINT `patients_ibfk_1` FOREIGN KEY (`centre_id`) REFERENCES `centres` (`centre_id`),
  ADD CONSTRAINT `patients_ibfk_2` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`doctor_id`);
  


/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
