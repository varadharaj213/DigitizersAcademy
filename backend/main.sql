-- Create database
CREATE DATABASE course_registration;
USE course_registration;

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone_number VARCHAR(20) NOT NULL,
    location VARCHAR(100) NOT NULL, 
    occupation VARCHAR(50) NOT NULL,  -- student, job seeker, teacher, or employed
    email_verified BOOLEAN DEFAULT FALSE,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OTP table for verification
CREATE TABLE otp_verification (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL,
    otp VARCHAR(6) NOT NULL,
    purpose VARCHAR(20) NOT NULL,  -- 'registration' or 'login'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (email) REFERENCES users(email)
);

-- Courses table
CREATE TABLE courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    duration VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User course registrations
CREATE TABLE user_courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id INT NOT NULL,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    payment_id VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (course_id) REFERENCES courses(id),
    UNIQUE KEY unique_user_course (user_id, course_id)
);

-- Sample courses data
INSERT INTO courses (title, description, price, duration) VALUES
('Python Programming Basics', 'Learn the fundamentals of Python programming language', 49.99, '4 weeks'),
('Web Development with Flask', 'Build web applications using Flask framework', 69.99, '6 weeks'),
('Database Design and SQL', 'Master database design principles and SQL queries', 59.99, '5 weeks'),
('JavaScript for Beginners', 'Learn JavaScript from scratch', 39.99, '4 weeks'),
('Advanced Python: Data Science', 'Use Python for data analysis and visualization', 79.99, '8 weeks');