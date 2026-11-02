-- ====================================================================
-- E-LEARNING COURSE ANALYTICS SYSTEM
-- Database Schema Definition & Demonstration Seed Data
-- Target Database: MySQL 8.0+
-- Storage Engine: InnoDB | Character Set: utf8mb4
-- ====================================================================

-- --------------------------------------------------------------------
-- INSTRUCTIONS FOR RUNNING IN MYSQL WORKBENCH:
-- 1. Open MySQL Workbench and connect to your local MySQL Server instance.
-- 2. Click "File" -> "Open SQL Script..." (or press Ctrl + Shift + O).
-- 3. Navigate to and select this file: 'database.sql'.
-- 4. Click the lightning bolt icon (Execute entire script, or press Ctrl + Shift + Enter).
-- 5. In the left "Schemas" panel, right-click and click "Refresh All".
-- 6. You will see 'elearning_db' with all 4 tables and demonstration data.
-- --------------------------------------------------------------------

-- Step 1: Create Database if not exists
CREATE DATABASE IF NOT EXISTS elearning_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE elearning_db;

-- Step 2: Drop child tables first, then parent tables to avoid FK conflicts
DROP TABLE IF EXISTS activities;
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS learners;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS users;

-- --------------------------------------------------------------------
-- Table 1: users
-- Stores authenticated administrators, analysts, and instructors
-- --------------------------------------------------------------------
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'Admin',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_username (username),
    INDEX idx_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------
-- Table 2: courses
-- Stores available e-learning courses and categories
-- --------------------------------------------------------------------
CREATE TABLE courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT NULL DEFAULT NULL,
    credits INT NULL DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_course_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------
-- Table 2: learners
-- Stores student learner profiles with unique college roll numbers
-- --------------------------------------------------------------------
CREATE TABLE learners (
    learner_id INT AUTO_INCREMENT PRIMARY KEY,
    roll_no VARCHAR(30) NOT NULL,
    name VARCHAR(100) NULL DEFAULT NULL,
    email VARCHAR(100) NULL DEFAULT NULL,
    department VARCHAR(50) NULL DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_learner_roll UNIQUE (roll_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------
-- Table 3: enrollments
-- Tracks student registration in courses with current status
-- Constraint: Learner cannot enroll in the same course more than once
-- --------------------------------------------------------------------
CREATE TABLE enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    learner_id INT NOT NULL,
    course_id INT NOT NULL,
    enrolled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Enrolled', 'In Progress', 'Completed') NOT NULL DEFAULT 'Enrolled',
    CONSTRAINT fk_enrollment_learner FOREIGN KEY (learner_id)
        REFERENCES learners(learner_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_enrollment_course FOREIGN KEY (course_id)
        REFERENCES courses(course_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT uq_learner_course UNIQUE (learner_id, course_id),
    INDEX idx_enrollment_status (status),
    INDEX idx_enrollment_enrolled_at (enrolled_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------
-- Table 4: activities
-- Records learner learning interactions and submissions per enrollment
-- --------------------------------------------------------------------
CREATE TABLE activities (
    activity_id INT AUTO_INCREMENT PRIMARY KEY,
    enrollment_id INT NOT NULL,
    activity_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    activity_type VARCHAR(50) NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    score DECIMAL(5,2) NULL DEFAULT NULL,
    time_spent_minutes INT NULL DEFAULT NULL,
    CONSTRAINT fk_activity_enrollment FOREIGN KEY (enrollment_id)
        REFERENCES enrollments(enrollment_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    INDEX idx_activity_date (activity_date),
    INDEX idx_activity_type (activity_type),
    INDEX idx_activity_completed (completed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================================
-- DEMONSTRATION / SAMPLE DATA (OPTIONAL SEED DATA)
-- The records below populate realistic e-learning courses, college roll
-- numbers, active & completed enrollments, and recent & past activities.
--
-- Note: Dates are relative to recent days (or using NOW() - INTERVAL)
-- to allow immediate testing of inactive detection (> 14 days) and
-- weekly analytics.
-- ====================================================================

-- 0. Insert Default Administrator User (Password: admin123)
INSERT INTO users (user_id, username, email, password_hash, full_name, role) VALUES
(1, 'admin', 'admin@elearning.edu', 'scrypt:32768:8:1$Cc2sVtliv6OGzCKf$baa745c24f760e1a0f651181410e7e1c690c9a9faf0e672740cd872ba6706e0ea22f4322238841a37d74d6ae5748ed346273a0d48cf531d27649c8a7cbfb3d6d', 'Academic Administrator', 'Admin');

-- 1. Insert Sample Courses
INSERT INTO courses (course_id, course_name, category) VALUES
(1, 'Full-Stack Web Development with Python', 'Web Development'),
(2, 'Data Structures & Algorithms in Java', 'Computer Science'),
(3, 'Applied Machine Learning & Data Science', 'Data Science'),
(4, 'Database Systems & SQL Mastery', 'Databases'),
(5, 'Cloud Computing Fundamentals with AWS', 'Cloud & DevOps'),
(6, 'Mobile App Engineering with Flutter', 'Mobile Development');

-- 2. Insert Sample Learners
INSERT INTO learners (learner_id, roll_no) VALUES
(1, '2024CS001'),
(2, '2024CS002'),
(3, '2024CS003'),
(4, '2024IT015'),
(5, '2024IT022'),
(6, '2024AI008'),
(7, '2024AI019'),
(8, '2024EC041');

-- 3. Insert Sample Enrollments
-- Course 1: 4 enrollments (2 Completed, 1 In Progress, 1 Enrolled)
INSERT INTO enrollments (enrollment_id, learner_id, course_id, enrolled_at, status) VALUES
(1, 1, 1, DATE_SUB(NOW(), INTERVAL 35 DAY), 'Completed'),
(2, 2, 1, DATE_SUB(NOW(), INTERVAL 28 DAY), 'Completed'),
(3, 3, 1, DATE_SUB(NOW(), INTERVAL 20 DAY), 'In Progress'),
(4, 4, 1, DATE_SUB(NOW(), INTERVAL 10 DAY), 'Enrolled');

-- Course 2: 3 enrollments (1 Completed, 2 In Progress)
INSERT INTO enrollments (enrollment_id, learner_id, course_id, enrolled_at, status) VALUES
(5, 1, 2, DATE_SUB(NOW(), INTERVAL 40 DAY), 'Completed'),
(6, 5, 2, DATE_SUB(NOW(), INTERVAL 25 DAY), 'In Progress'),
(7, 6, 2, DATE_SUB(NOW(), INTERVAL 30 DAY), 'In Progress');

-- Course 3: 3 enrollments (1 Completed, 1 In Progress, 1 Enrolled)
INSERT INTO enrollments (enrollment_id, learner_id, course_id, enrolled_at, status) VALUES
(8, 2, 3, DATE_SUB(NOW(), INTERVAL 22 DAY), 'Completed'),
(9, 7, 3, DATE_SUB(NOW(), INTERVAL 18 DAY), 'In Progress'),
(10, 8, 3, DATE_SUB(NOW(), INTERVAL 25 DAY), 'Enrolled');

-- Course 4: 2 enrollments (0 Completed, 1 In Progress, 1 Enrolled)
INSERT INTO enrollments (enrollment_id, learner_id, course_id, enrolled_at, status) VALUES
(11, 3, 4, DATE_SUB(NOW(), INTERVAL 25 DAY), 'In Progress'),
(12, 6, 4, DATE_SUB(NOW(), INTERVAL 20 DAY), 'Enrolled');

-- Course 5: 1 enrollment (1 In Progress)
INSERT INTO enrollments (enrollment_id, learner_id, course_id, enrolled_at, status) VALUES
(13, 4, 5, DATE_SUB(NOW(), INTERVAL 15 DAY), 'In Progress');

-- Course 6: 0 enrollments (Test case for empty enrollments / 0% handling)

-- 4. Insert Sample Activities
-- Active activities within last 14 days
INSERT INTO activities (enrollment_id, activity_date, activity_type, completed) VALUES
-- Enrollment 1 (Completed, active history)
(1, DATE_SUB(NOW(), INTERVAL 34 DAY), 'Lesson', TRUE),
(1, DATE_SUB(NOW(), INTERVAL 30 DAY), 'Quiz', TRUE),
(1, DATE_SUB(NOW(), INTERVAL 28 DAY), 'Assignment', TRUE),
(1, DATE_SUB(NOW(), INTERVAL 25 DAY), 'Project', TRUE),

-- Enrollment 2 (Completed)
(2, DATE_SUB(NOW(), INTERVAL 27 DAY), 'Lesson', TRUE),
(2, DATE_SUB(NOW(), INTERVAL 20 DAY), 'Quiz', TRUE),
(2, DATE_SUB(NOW(), INTERVAL 15 DAY), 'Project', TRUE),

-- Enrollment 3 (In Progress, Active recently: 2 days ago)
(3, DATE_SUB(NOW(), INTERVAL 18 DAY), 'Lesson', TRUE),
(3, DATE_SUB(NOW(), INTERVAL 9 DAY), 'Quiz', TRUE),
(3, DATE_SUB(NOW(), INTERVAL 2 DAY), 'Assignment', FALSE),

-- Enrollment 4 (Enrolled, Active 4 days ago)
(4, DATE_SUB(NOW(), INTERVAL 8 DAY), 'Lesson', TRUE),
(4, DATE_SUB(NOW(), INTERVAL 4 DAY), 'Practice', FALSE),

-- Enrollment 5 (Completed)
(5, DATE_SUB(NOW(), INTERVAL 38 DAY), 'Lesson', TRUE),
(5, DATE_SUB(NOW(), INTERVAL 35 DAY), 'Quiz', TRUE),
(5, DATE_SUB(NOW(), INTERVAL 31 DAY), 'Project', TRUE),

-- Enrollment 6 (In Progress, Active 5 days ago)
(6, DATE_SUB(NOW(), INTERVAL 20 DAY), 'Lesson', TRUE),
(6, DATE_SUB(NOW(), INTERVAL 5 DAY), 'Quiz', TRUE),

-- Enrollment 7 (In Progress, INACTIVE - last activity was 21 days ago!)
(7, DATE_SUB(NOW(), INTERVAL 25 DAY), 'Lesson', TRUE),
(7, DATE_SUB(NOW(), INTERVAL 21 DAY), 'Practice', FALSE),

-- Enrollment 8 (Completed)
(8, DATE_SUB(NOW(), INTERVAL 20 DAY), 'Lesson', TRUE),
(8, DATE_SUB(NOW(), INTERVAL 16 DAY), 'Quiz', TRUE),
(8, DATE_SUB(NOW(), INTERVAL 12 DAY), 'Project', TRUE),

-- Enrollment 9 (In Progress, Active 1 day ago)
(9, DATE_SUB(NOW(), INTERVAL 14 DAY), 'Lesson', TRUE),
(9, DATE_SUB(NOW(), INTERVAL 7 DAY), 'Quiz', FALSE),
(9, DATE_SUB(NOW(), INTERVAL 1 DAY), 'Practice', TRUE),

-- Enrollment 10 (Enrolled, INACTIVE - NO activities at all!)
-- (Intentionally left with zero rows in activities table to test no-activity inactive rule)

-- Enrollment 11 (In Progress, INACTIVE - last activity was 19 days ago!)
(11, DATE_SUB(NOW(), INTERVAL 22 DAY), 'Lesson', TRUE),
(11, DATE_SUB(NOW(), INTERVAL 19 DAY), 'Quiz', FALSE),

-- Enrollment 12 (Enrolled, INACTIVE - NO activities recorded!)
-- (Intentionally zero activities)

-- Enrollment 13 (In Progress, Active 3 days ago)
(13, DATE_SUB(NOW(), INTERVAL 12 DAY), 'Lesson', TRUE),
(13, DATE_SUB(NOW(), INTERVAL 3 DAY), 'Assignment', FALSE);
