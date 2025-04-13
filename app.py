from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
import mysql.connector
from flask import session 
from flask_cors import CORS
import MySQLdb
import MySQLdb.cursors
import pymysql
import re
import time
import smtplib
import ssl
import schedule
import time
import datetime
import threading
from threading import Thread
from threading import Lock
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Your Flask app setup and routes go here


app = Flask(__name__)
CORS(app) 

app.secret_key = 'xyzsdfg'
pymysql.install_as_MySQLdb()



app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'kn6823'
app.config['MYSQL_DB'] = 'credentials'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/student-login')
def student_login():
    return render_template('login-form.html', user_type="student")

@app.route('/admin-login')
def admin_login():
    return render_template('login-form.html', user_type="admin")


@app.route('/thankyou', methods=['GET'])
def thankyou():
    # Get the complaint ID from the query parameters
    complaint_id = request.args.get('complaint_id')

    # Call the stop_timer function
    stop_timer(complaint_id)

    # Render the 'thankyou.html' template with the complaint ID
    return render_template('thankyou.html', complaint_id=complaint_id)



@app.route('/admin')
def admin():
    if 'admin_logged_in' in session and session['admin_logged_in']:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM complaints')
        complaints = cursor.fetchall()
        cursor.close()
        return render_template('admin.html', complaints=complaints)
    else:
        return redirect(url_for('admin_login'))



@app.route('/home')
def home():
    return render_template('index.html')


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']

        # Check if the user is an admin
        if email == 'Adminsies@gst.sies.edu.in' and password == 'adminsies':
            # Set session variables for admin login
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        
        # Normal user login
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['prn'] = user['prn']
            session['email'] = user['email']
            message = 'Logged in successfully !'
            return render_template('complaint.html', message=message)
        else:
            message = 'Please enter correct email / password !'

    return render_template('index.html', message=message)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form and 'prn' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        prn = request.form['prn']  # Get PRN from the form
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            message = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not userName or not password or not email:
            message = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO user (name, email, password, prn) VALUES (%s, %s, %s, %s)', (userName, email, password, prn))
            mysql.connection.commit()
            message = 'You have successfully registered!'
    elif request.method == 'POST':
        message = 'Please fill out the form!'
    return render_template('register.html', message=message)


@app.route('/add_complaint', methods=['POST'])
def add_complaint():
    if request.method == 'POST':
        # Get the complaint type selected by the user
        complaint_type = request.form['complaint_type']
        
        # Determine the email recipient based on the complaint type
        recipient_email = get_recipient_email(complaint_type, 0)  # Start with count=0

        # Get the subject from the form data
        subject = request.form['subject']

        # Get the description from the form data
        description = request.form['description']
        
        # Get the PRN from the session data
        prn = session['prn']

        try:
            # Insert the complaint into the database using Flask-MySQLdb cursor
            cursor = mysql.connection.cursor()
            current_date = datetime.datetime.now().date()
            default_status = 'Unresolved'  # Default value for status column
            cursor.execute('INSERT INTO complaints (id, name, email, subject, type_of_complaint, description, prn, issued_date, status) VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s)',
                           (session['name'], session['email'], subject, complaint_type, description, prn, current_date, default_status))
            mysql.connection.commit()

            # Get the last inserted complaint ID
            complaint_id = cursor.lastrowid

            # Close the cursor
            cursor.close()

            # Call the send_email function to send the email
            send_email('mpb11173846@gmail.com', 'gprb zrcw bhsk xdbi', recipient_email, subject, complaint_type, description, complaint_id)
            print("Email sent.")

            # Start the timer function in a separate thread after sending the email
            user_name = session.get('name')  # Get user name from session
            print("Starting timer function...")
            timer_thread = Thread(target=schedule_timer, args=(subject, complaint_type, description, complaint_id, user_name))
            timer_thread.start()

            message = 'Thanks for the feedback! Your problem will be solved very soon.'
            return render_template('complaint.html', message=message)
            
        except MySQLdb.Error as e:
            error_message = f"Error inserting complaint: {e}"
            return render_template('complaint.html', message=error_message)
    else:
        return render_template('complaint.html', message=None)


def send_resolution_email(sender_address, sender_pass, complaint_id, subject, complaint_type, description):
    try:
        # Create a cursor within the application context to execute SQL queries
        with app.app_context():
            # Create a cursor to execute SQL queries
            cursor = mysql.connection.cursor()

            # Get the user's email and complaint data from the complaints table using the complaint ID
            cursor.execute("SELECT email, subject FROM complaints WHERE id = %s", (complaint_id,))
            complaint_data = cursor.fetchone()

            # Check if complaint data exists
            if complaint_data:
                recipient_email = complaint_data['email']
                email_subject = complaint_data['subject']

                # Create the email message
                message = MIMEMultipart()
                message['From'] = sender_address
                message['To'] = recipient_email
                message['Subject'] = email_subject  # Use the subject from the database

                # Construct the email body
                msg = f"""
                <html>
                    <body>
                        <p style="color: red;">Complaint ID: {complaint_id}</p>
                        <p style="color: green;">{email_subject} has been resolved.</p>
                        <p>Thank you for your patience and cooperation.</p>
                        <p style="color: blue;">Regards,<br/>SIESGST Support Team</p>
                    </body>
                </html>
                """

                # Attach the HTML content to the email message
                message.attach(MIMEText(msg, 'html'))

                # Convert the message to a string
                text = message.as_string()

                # Log in to server using secure context and send email
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                    server.login(sender_address, sender_pass)
                    server.sendmail(sender_address, recipient_email, text)

                print(f"Resolution email sent to {recipient_email}")
            else:
                print(f"Email not found for complaint ID {complaint_id}")

            # Close the cursor
            cursor.close()
    except Exception as e:
        print(f"Error sending resolution email: {str(e)}")

stop_timer_flag = False
complaint_id_to_stop = None

@app.route('/stop_timer', methods=['GET'])
def stop_timer():
    global stop_timer_flag, complaint_id_to_stop
    complaint_id_to_stop = request.args.get('complaint_id')  # Get the complaint ID to stop
    stop_timer_flag = True  # Set the flag to stop the timer
    
    print(f"Timer stopped for Complaint ID {complaint_id_to_stop}")
    # Get the complaint ID, subject, complaint type, and description from the query parameters
    complaint_id = request.args.get('complaint_id')
    subject = request.args.get('subject')
    complaint_type = request.args.get('complaint_type')
    description = request.args.get('description')

    # Call the send_resolution_email function with the retrieved parameters
    send_resolution_email('mpb11173846@gmail.com', 'gprb zrcw bhsk xdbi', complaint_id, subject, complaint_type, description)
    update_status_in_database(complaint_id, 'Resolved')
    print("Time stopped")
    return 'Timer stopped successfully', 200



    
    
message_count = {}
    
def timer_function(subject, complaint_type, description, complaint_id, user_name):
    global stop_timer_flag, complaint_id_to_stop, message_count

    # Check if the stop signal is received for the specific complaint ID
    if stop_timer_flag and complaint_id == complaint_id_to_stop:
        print(f"Timer stopped for Complaint ID {complaint_id}")
        return schedule.CancelJob  # Stop scheduling the timer

    # Check if the stop signal is received for any complaint ID and stop processing further
    if stop_timer_flag:
        print("Timer stopped. Skipping mail sending.")
        return schedule.CancelJob  # Stop scheduling the timer for any other IDs

    # Get the recipient email based on the complaint type and message count
    recipient_email = get_recipient_email(complaint_type, message_count.get(complaint_id, 0))

    # Get the current date and time
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Log the start of timer function execution
    print(f"Timer function started: {current_time} {user_name} Complaint ID: {complaint_id}")

    # Print the current message count
    print(f"Current message count for complaint ID {complaint_id}: {message_count.get(complaint_id, 0)}")

    # Send the email based on the message count
    if message_count.get(complaint_id, 0) == 0:
        print(f"First time mail is sent: {current_time} {user_name}")
        send_email('mpb11173846@gmail.com', 'gprb zrcw bhsk xdbi', recipient_email, subject, complaint_type, description, complaint_id)
        # Increment the message count for the next iteration
        message_count[complaint_id] = 1
    elif message_count.get(complaint_id, 0) == 1:
        print(f"Second time mail is sent: {current_time} {user_name}")
        send_email('mpb11173846@gmail.com', 'gprb zrcw bhsk xdbi', recipient_email, subject, complaint_type, description, complaint_id)
        # Increment the message count for the next iteration
        message_count[complaint_id] = 2
    elif message_count.get(complaint_id, 0) == 2:
        print(f"Third time mail is sent: {current_time} {user_name}")
        send_email('mpb11173846@gmail.com', 'gprb zrcw bhsk xdbi', recipient_email, subject, complaint_type, description, complaint_id)
        print("Message printed 3 times. Stopping timer.")
        return schedule.CancelJob  # Stop scheduling the timer
    else:
        print(f"Unexpected message count: {message_count.get(complaint_id, 0)}")


def schedule_timer(subject, complaint_type, description, complaint_id, user_name):
    global message_count
    # Initialize message count for this complaint ID if not already set
    if complaint_id not in message_count:
        message_count[complaint_id] = 0

    # Log the start of scheduling timer function
    print(f"Scheduling timer started: Complaint ID: {complaint_id}")

    # Print the current message count
    print(f"Current message count for complaint ID {complaint_id}: {message_count.get(complaint_id, 0)}")

    # Schedule the timer function to run after 1 minute only if message count is less than 3
    if message_count[complaint_id] < 3:
        schedule.every(1).minutes.do(timer_function, subject, complaint_type, description, complaint_id, user_name)

    while True:
        schedule.run_pending()
        time.sleep(1)



def update_status_in_database(complaint_id, new_status):
    try:
        # Create a cursor within the application context to execute SQL queries
        with app.app_context():
            # Create a cursor to execute SQL queries
            cursor = mysql.connection.cursor()

            # Update the status in the database
            cursor.execute("UPDATE complaints SET status = %s WHERE id = %s", (new_status, complaint_id))

            # Commit the transaction
            mysql.connection.commit()

            # Close the cursor
            cursor.close()

            print(f"Updating status of complaint ID {complaint_id} to {new_status} in the database successful")
    except Exception as e:
        print(f"Error updating status in the database: {str(e)}")



def get_recipient_email(complaint_type, message_count):
    # Initialize lists or dictionaries for each category of complaints
    infrastructure_emails = 'nishanthkata68@gmail.com'
    facilities_emails = 'kata.nishanth06@gmail.com'
    academic_emails = 'nishanthkata06@gmail.com'
    admin_financial_emails = 'katanishanth@gmail.com'
    social_community_emails = 'nishanthnkce121@siesgst.ac.in'
    environmental_emails = 'nishanthkata@gmail.com'
    other_emails = 'nishanthnkce121@gst.sies.edu.in'
    
    # Principal and HOD email addresses
    principal_email = 'nishanthkata68@gmail.com'
    hod_email = 'hod@example.com'

    # Check the complaint type and return the corresponding email
    if complaint_type == 'Infrastructure Issues':
        if message_count < 2:
            return infrastructure_emails
        else:
            return principal_email
    elif complaint_type == 'Facilities Management Issues':
        if message_count < 2:
            return facilities_emails
        else:
            return principal_email
    elif complaint_type == 'Academic Issues':
        if message_count < 2:
            return academic_emails
        else:
            return principal_email
    elif complaint_type == 'Administrative and Financial Issues':
        if message_count < 2:
            return admin_financial_emails
        else:
            return principal_email
    elif complaint_type == 'Social and Community Issues':
        if message_count < 2:
            return social_community_emails
        else:
            return principal_email
    elif complaint_type == 'Environmental Sustainability':
        if message_count < 2:
            return environmental_emails
        else:
            return principal_email
    else:
        if message_count < 2:
            return other_emails
        else:
            return principal_email





def send_email(sender_address, sender_pass, recipient_email, subject, complaint_type, description, complaint_id=None):
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = recipient_email
    message['Subject'] = subject

    msg = f"""
    <html>
        <body>
            <p style="color: red;">A new Complaint ID: {complaint_id} has been registered regarding the following issue:</p>
            <p style="text-align: justify;">{description}</p>
            <p>This message is to inform you about the issue raised. Please take necessary actions to address this matter.</p>
            <p style="color: blue;">Regards,<br/>SIESGST Support Team</p>
           <a href="http://127.0.0.1:5501/templates/thankyou.html?complaint_id={ complaint_id }">
                <button id="resolveButton" style="background-color: green; color: white; padding: 10px 20px; margin: 6px; border: none; border-radius: 5px;">Resolve Complaint</button>
            </a>
        </body>
    </html>
    """

    # Attach the HTML content to the email message
    message.attach(MIMEText(msg, 'html'))

    # Convert the message to a string
    text = message.as_string()

    # Log in to server using secure context and send email
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_address, sender_pass)
            server.sendmail(sender_address, recipient_email, text)
        print(f'Mail Sent to {recipient_email}')
        
    except smtplib.SMTPAuthenticationError:
        print("The username and/or password you entered is incorrect")
    except smtplib.SMTPException as e:
        print(f'Failed to send mail to {recipient_email}: {e}')


        
@app.route('/delete_complaint', methods=['POST'])
def delete_complaint():
    try:
        # Get the complaint ID from the request
        complaint_id = request.json.get('complaint_id')

        # Delete the complaint from the database
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM complaints WHERE id = %s", (complaint_id,))
        mysql.connection.commit()
        cursor.close()

        return 'Complaint deleted successfully', 200
    except Exception as e:
        print(f"Error deleting complaint: {str(e)}")
        return 'Failed to delete complaint', 500


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=3000, debug=True)

