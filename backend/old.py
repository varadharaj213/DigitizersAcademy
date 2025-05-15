import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Default XAMPP password is empty
    'database': 'course_registration'
}

# Helper functions
def get_db_connection():
    return mysql.connector.connect(**db_config)

def send_email(to_email, subject, body):
    # Configure this with your email provider details
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "varadharaj160@gmail.com"  # Replace with your email
    smtp_password = "jlsbkoanclltyfdy"     # Replace with your app password
    
    # Create message
    message = MIMEMultipart()
    message["From"] = smtp_username
    message["To"] = to_email
    message["Subject"] = subject
    
    # Add body to email
    message.attach(MIMEText(body, "html"))
    
    try:
        # Create SMTP session
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        # Send email
        server.send_message(message)
        server.quit()
        return True
    except Exception as e:
        print(f"Email sending error: {e}")
        return False

def generate_otp():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def save_otp(email, otp, purpose):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Delete any existing OTPs for this email and purpose
    cursor.execute(
        "DELETE FROM otp_verification WHERE email = %s AND purpose = %s",
        (email, purpose)
    )
    
    # Set expiration time (10 minutes from now)
    expires_at = datetime.now() + timedelta(minutes=10)
    
    # Save new OTP
    cursor.execute(
        "INSERT INTO otp_verification (email, otp, purpose, expires_at) VALUES (%s, %s, %s, %s)",
        (email, otp, purpose, expires_at)
    )
    
    conn.commit()
    cursor.close()
    conn.close()

def verify_otp(email, otp, purpose):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        "SELECT * FROM otp_verification WHERE email = %s AND otp = %s AND purpose = %s AND expires_at > NOW()",
        (email, otp, purpose)
    )
    
    result = cursor.fetchone()
    
    if result:
        # OTP is valid, delete it to prevent reuse
        cursor.execute("DELETE FROM otp_verification WHERE id = %s", (result['id'],))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    cursor.close()
    conn.close()
    return False

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('user_home'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        location = request.form['location']
        occupation = request.form['occupation']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            flash('Email already registered. Please use a different email or login.', 'danger')
            return render_template('register.html', now=datetime.now())
        
        # Insert user data
        cursor.execute(
            "INSERT INTO users (first_name, last_name, email, phone_number, location, occupation) VALUES (%s, %s, %s, %s, %s, %s)",
            (first_name, last_name, email, phone_number, location, occupation)
        )
        conn.commit()
        
        # Generate and send OTP for email verification
        otp = generate_otp()
        save_otp(email, otp, 'registration')
        
        email_body = f"""
        <html>
        <body>
            <h2>Verify Your Email Address</h2>
            <p>Thank you for registering with our course platform. Please use the following OTP to verify your email address:</p>
            <h3 style="background-color: #f0f0f0; padding: 10px; text-align: center; font-size: 24px;">{otp}</h3>
            <p>This OTP will expire in 10 minutes.</p>
        </body>
        </html>
        """
        
        send_email(email, "Email Verification OTP", email_body)
        
        # Store email in session for verification
        session['verification_email'] = email
        
        cursor.close()
        conn.close()
        
        return redirect(url_for('verify_email'))
    
    return render_template('register.html', now=datetime.now())

@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    if 'verification_email' not in session:
        return redirect(url_for('register'))
    
    email = session['verification_email']
    
    if request.method == 'POST':
        otp = request.form['otp']
        
        if verify_otp(email, otp, 'registration'):
            # Mark email as verified
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET email_verified = TRUE WHERE email = %s", (email,))
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Email verified successfully! You can now login.', 'success')
            session.pop('verification_email', None)
            return redirect(url_for('login'))
        else:
            flash('Invalid or expired OTP. Please try again.', 'danger')
    
    return render_template('verify_email.html', email=email, now=datetime.now())

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    if 'verification_email' not in session:
        return jsonify({'status': 'error', 'message': 'No email found for verification'})
    
    email = session['verification_email']
    otp = generate_otp()
    save_otp(email, otp, 'registration')
    
    email_body = f"""
    <html>
    <body>
        <h2>Verify Your Email Address</h2>
        <p>Here is your new OTP to verify your email address:</p>
        <h3 style="background-color: #f0f0f0; padding: 10px; text-align: center; font-size: 24px;">{otp}</h3>
        <p>This OTP will expire in 10 minutes.</p>
    </body>
    </html>
    """
    
    if send_email(email, "New Email Verification OTP", email_body):
        return jsonify({'status': 'success', 'message': 'New OTP sent to your email'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to send OTP. Please try again.'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user exists and email is verified
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            flash('Email not registered. Please register first.', 'danger')
            return render_template('login.html', now=datetime.now())
        
        if not user['email_verified']:
            session['verification_email'] = email
            cursor.close()
            conn.close()
            flash('Please verify your email before logging in.', 'warning')
            return redirect(url_for('verify_email'))
        
        # Generate and send OTP for login
        otp = generate_otp()
        save_otp(email, otp, 'login')
        
        email_body = f"""
        <html>
        <body>
            <h2>Login OTP</h2>
            <p>Use the following OTP to login to your account:</p>
            <h3 style="background-color: #f0f0f0; padding: 10px; text-align: center; font-size: 24px;">{otp}</h3>
            <p>This OTP will expire in 10 minutes.</p>
        </body>
        </html>
        """
        
        send_email(email, "Login OTP", email_body)
        
        # Store email in session for OTP verification
        session['login_email'] = email
        
        cursor.close()
        conn.close()
        
        return redirect(url_for('verify_login'))
    
    return render_template('login.html', now=datetime.now())

@app.route('/verify-login', methods=['GET', 'POST'])
def verify_login():
    if 'login_email' not in session:
        return redirect(url_for('login'))
    
    email = session['login_email']
    
    if request.method == 'POST':
        otp = request.form['otp']
        
        if verify_otp(email, otp, 'login'):
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, first_name, last_name FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user:
                session['user_id'] = user['id']
                session['user_name'] = f"{user['first_name']} {user['last_name']}"
                session.pop('login_email', None)
                return redirect(url_for('user_home'))
        
        flash('Invalid or expired OTP. Please try again.', 'danger')
    
    return render_template('login.html', verify_mode=True, email=email, now=datetime.now())

@app.route('/user-home')
def user_home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get user profile
    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    
    # Get user's registered courses
    cursor.execute("""
        SELECT c.*, uc.registration_date, uc.payment_status 
        FROM courses c 
        JOIN user_courses uc ON c.id = uc.course_id 
        WHERE uc.user_id = %s AND uc.payment_status = 'completed'
    """, (session['user_id'],))
    registered_courses = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('user_home.html', user=user, registered_courses=registered_courses, now=datetime.now())

@app.route('/all-courses')
def all_courses():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all courses
    cursor.execute("SELECT * FROM courses")
    all_courses = cursor.fetchall()
    
    # Get user's registered courses for exclusion
    cursor.execute(
        "SELECT course_id FROM user_courses WHERE user_id = %s AND payment_status = 'completed'", 
        (session['user_id'],)
    )
    registered_course_ids = [row['course_id'] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return render_template(
        'all_courses.html', 
        courses=all_courses, 
        registered_course_ids=registered_course_ids,
        now=datetime.now()
    )

@app.route('/registered-courses')
def registered_courses():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get user's registered courses
    cursor.execute("""
        SELECT c.*, uc.registration_date, uc.payment_status 
        FROM courses c 
        JOIN user_courses uc ON c.id = uc.course_id 
        WHERE uc.user_id = %s AND uc.payment_status = 'completed'
    """, (session['user_id'],))
    registered_courses = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('registered_courses.html', courses=registered_courses, now=datetime.now())

@app.route('/payment/<int:course_id>')
def payment(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get course details
    cursor.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
    course = cursor.fetchone()
    
    # Check if user already registered for this course
    cursor.execute(
        "SELECT * FROM user_courses WHERE user_id = %s AND course_id = %s AND payment_status = 'completed'",
        (session['user_id'], course_id)
    )
    
    if cursor.fetchone():
        cursor.close()
        conn.close()
        flash('You have already registered for this course.', 'info')
        return redirect(url_for('registered_courses'))
    
    cursor.close()
    conn.close()
    
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('all_courses'))
    
    return render_template('payment.html', course=course, now=datetime.now())

@app.route('/process-payment', methods=['POST'])
def process_payment():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    
    course_id = request.form.get('course_id')
    # In a real application, you would process payment with a payment gateway
    # For demonstration, we'll assume payment is successful
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if already registered
        cursor.execute(
            "SELECT id FROM user_courses WHERE user_id = %s AND course_id = %s",
            (session['user_id'], course_id)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            cursor.execute(
                "UPDATE user_courses SET payment_status = 'completed', payment_id = %s WHERE user_id = %s AND course_id = %s",
                (f"PAY-{secrets.token_hex(6).upper()}", session['user_id'], course_id)
            )
        else:
            # Create new registration
            cursor.execute(
                "INSERT INTO user_courses (user_id, course_id, payment_status, payment_id) VALUES (%s, %s, %s, %s)",
                (session['user_id'], course_id, 'completed', f"PAY-{secrets.token_hex(6).upper()}")
            )
        
        conn.commit()
        
        # Get user email and course details for confirmation email
        cursor.execute("SELECT email FROM users WHERE id = %s", (session['user_id'],))
        user_email = cursor.fetchone()[0]
        
        cursor.execute("SELECT title, price FROM courses WHERE id = %s", (course_id,))
        course = cursor.fetchone()
        course_title = course[0]
        course_price = course[1]
        
        # Send confirmation email
        email_body = f"""
        <html>
        <body>
            <h2>Course Registration Confirmation</h2>
            <p>Congratulations! You have successfully registered for the following course:</p>
            <p><strong>Course:</strong> {course_title}</p>
            <p><strong>Price:</strong> ${course_price}</p>
            <p>You can access your course materials from your dashboard.</p>
            <p>Thank you for choosing our platform!</p>
        </body>
        </html>
        """
        
        send_email(user_email, "Course Registration Confirmation", email_body)
        
        return jsonify({'status': 'success', 'message': 'Payment successful'})
    
    except Exception as e:
        conn.rollback()
        print(f"Payment error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})
    
    finally:
        cursor.close()
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.context_processor
def inject_now():
    """Add the current datetime to all templates."""
    return {'now': datetime.now()}

if __name__ == '__main__':
    app.run(debug=True)