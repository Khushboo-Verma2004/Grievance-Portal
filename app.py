import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
import mysql.connector
from werkzeug.utils import secure_filename
from flask import send_file
import random
import smtplib  # For sending email
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key
bcrypt = Bcrypt(app)

# MySQL database configuration
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="fda24d3252",  # Replace with your MySQL password
    database="signin"    # Replace with your MySQL database name
)
cursor = db.cursor()

# Route for the main page
@app.route('/')
def index():
    return redirect(url_for('signin'))

# Route for the dashboard
@app.route('/dashboard')
def dashboard():
    if 'email' in session:
        cursor.execute("SELECT COUNT(*) FROM grievances WHERE user_email = %s AND status = 'pending'", (session['email'],))
        pending_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM grievances WHERE user_email = %s AND status = 'resolved'", (session['email'],))
        resolved_count = cursor.fetchone()[0]
        cursor.execute("SELECT * FROM grievances WHERE user_email = %s", (session['email'],))
        grievances = cursor.fetchall()
        return render_template('main-page.html', pending_count=pending_count, resolved_count=resolved_count, grievances=grievances)
    return redirect(url_for('signin'))

@app.route('/download_attachment/<filename>')
def download_attachment(filename):
    if 'email' not in session:
        flash('You need to be signed in to download attachments.', 'error')
        return redirect(url_for('signin'))

    filepath = os.path.join(app.root_path, 'uploads', filename)
    return send_file(filepath, as_attachment=True)

# Route for signing in
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if 'email' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Fetch user details from database
        query = "SELECT email, password FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user[1], password):
            session['email'] = email  # Set session for authenticated user
            return redirect(url_for('dashboard'))
        else:
            flash('Incorrect email or password', 'error')

    return render_template('base.html')

# Route for signing out
@app.route('/signout')
def signout():
    session.pop('email', None)  # Clear session
    return redirect(url_for('signin'))

# Route for registering a new user
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user already exists
        query = "SELECT email FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if user:
            flash('Email already registered', 'error')
        else:
            # Hash the password
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            # Insert the new user into the database
            insert_query = "INSERT INTO users (email, password) VALUES (%s, %s)"
            cursor.execute(insert_query, (email, hashed_password))
            db.commit()

            flash('User registered successfully! Your account has been created.', 'success')
            return redirect(url_for('signin'))

    return render_template('sign-up.html')

# Route for registering a grievance
@app.route('/register_grievance', methods=['GET', 'POST'])
def register_grievance():
    if 'email' not in session:
        flash('You need to be signed in to register a grievance.', 'error')
        return redirect(url_for('signin'))

    if request.method == 'POST':
        grievance_type = request.form.get('grievanceType')
        department = request.form.get('department')
        description = request.form.get('description')
        attachment = request.files.get('attachment')

        attachment_name = None
        if attachment:
            attachment_name = secure_filename(attachment.filename)
            attachment.save(os.path.join(app.root_path, 'uploads', attachment_name))

        # Insert the grievance details into the database
        query = """
        INSERT INTO grievances 
        (grievance_type, department, description, attachment_name, user_email, status) 
        VALUES (%s, %s, %s, %s, %s, 'pending')
        """
        cursor.execute(query, (grievance_type, department, description, attachment_name, session['email']))
        db.commit()

        flash('Grievance submitted successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('register_grievance.html')

#new code
def send_otp(email, otp):
    msg = MIMEText(f'Your OTP is: {otp}')
    msg['Subject'] = 'Your OTP Code'
    msg['From'] = 'khushboo.verma2004@gmail.com'  # Replace with your email
    msg['To'] = email

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('khushboo.verma2004@gmail.com', 'ehdw rnjf xaxz xcev')  # Use app password
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")

# Route for forgot password
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user:
            otp = random.randint(100000, 999999)  # Generate a random OTP
            send_otp(email, otp)  # Send the OTP to the entered email
            flash('OTP has been sent to your email.', 'success')
            session['otp'] = otp
            session['email'] = email
            return redirect(url_for('otp_verification'))
        else:
            flash('Email not registered', 'error')
    
    return render_template('forgot-password.html')

@app.route('/otp_verification', methods=['GET', 'POST'])
def otp_verification():
    if request.method == 'POST':
        entered_otp = request.form.get('otpInput')
        print(f"Entered OTP: {entered_otp}")  # Debugging line
        print(f"Session OTP: {session.get('otp')}")  # Debugging line

        if entered_otp == str(session.get('otp')):
            flash('OTP verified successfully!', 'success')
            return redirect(url_for('dashboard'))  # Redirect to dashboard (main-page.html)
        else:
            flash('Invalid OTP', 'error')
            print("Invalid OTP")  # Debugging line

    return render_template('otp.html')



# Route for resetting the password
# @app.route('/reset_password', methods=['GET', 'POST'])
# def reset_password():
#     if request.method == 'POST':
#         new_password = request.form.get('new_password')
#         hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
#         cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, session['email']))
#         db.commit()
#         flash('Password reset successfully!', 'success')
#         return redirect(url_for('signin'))

#     return render_template('reset_password.html')


if __name__ == '__main__':
    app.run(debug=True)
