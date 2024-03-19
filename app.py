from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import time
import pandas as pd
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


app = Flask(__name__)

app.secret_key = 'xyzsdfg'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'kn6823'
app.config['MYSQL_DB'] = 'credentials'

mysql = MySQL(app)

@app.route('/student-login')
def student_login():
    return render_template('login-form.html')

@app.route('/admin-login')
def admin_login():
    return render_template('login-form.html')

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
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
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
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            message = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address !'
        elif not userName or not password or not email:
            message = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO user (name, email, password) VALUES (%s, %s, %s)', (userName, email, password))
            mysql.connection.commit()
            message = 'You have successfully registered !'
    elif request.method == 'POST':
        message = 'Please fill out the form !'
    return render_template('register.html', message=message)



import pandas as pd

@app.route('/add_complaint', methods=['POST'])
def add_complaint():
    if request.method == 'POST':
        subject = request.form['subject']
        complaint_type = request.form['complaint_type']
        description = request.form['description']
        
        # Insert the complaint into the database
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO complaints (id, name, subject, type_of_complaint, description) VALUES (NULL, %s, %s, %s, %s)',
                    (session['name'], subject, complaint_type, description))
        mysql.connection.commit()
        cursor.close()
        
        # Get names and emails from the CSV file
        data = pd.read_csv("C:\\Users\\NISHANTH\\Downloads\\Participant_Data.csv")
        names = data["Name"]
        email = data["Email"]
        
        # Call the send_email function to send emails
        send_email('mpb11173846@gmail.com', 'gprb zrcw bhsk xdbi', names, email, subject, complaint_type, description)

        message = 'Thanks for the feedback! Your problem will be solved very soon.'
        return render_template('complaint.html', message=message)
    else:
        return render_template('complaint.html', message=None)


def send_email(sender_address, sender_pass, names, email, subject, complaint_type, description):
    for i in range(len(names)):
        person_name = str(names[i])  # Convert to string explicitly
        receiver_email = str(email[i])  # Convert to string explicitly
        message = MIMEMultipart()
        message['From'] = sender_address
        message['To'] = receiver_email
        message['Subject'] = subject

        # Construct the email content
        msg = f"""
            <html>
                <body>
                    <p style="color: red;">A new complaint has been registered regarding the following issue:</p>
                    <p style="text-align: justify;">{description}</p>
                    <p>This message is to inform you about the issue raised. Please take necessary actions to address this matter.</p>
                    <p style="color: blue;">Regards,<br/>SIESGST Support Team</p>
                    <button style="background-color: green; color: white; padding: 10px 20px; border: none; border-radius: 5px;">Resolved</button>
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
                server.sendmail(sender_address, receiver_email, text)
            print(f'Mail Sent to {person_name}')
        except smtplib.SMTPAuthenticationError:
            print("The username and/or password you entered is incorrect")
        except smtplib.SMTPException as e:
            print(f'Failed to send mail to {person_name}: {e}')


# if __name__ == "__main__":
#     app.run(debug=True)

























# from flask import Flask, render_template, request, redirect, url_for, session
# from flask_mysqldb import MySQL
# import MySQLdb.cursors
# import re

# app = Flask(__name__)

# app.secret_key = 'xyzsdfg'

# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = 'kn6823'
# app.config['MYSQL_DB'] = 'credentials'

# mysql = MySQL(app)

# @app.route('/student-login')
# def student_login():
#     return render_template('login-form.html')

# @app.route('/admin-login')
# def admin_login():
#     return render_template('login-form.html')

# @app.route('/home')
# def home():
#     return render_template('index.html')

# @app.route('/')
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     message = ''
#     if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
#         email = request.form['email']
#         password = request.form['password']
#         cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#         cursor.execute('SELECT * FROM user WHERE email = %s AND password = %s', (email, password))
#         user = cursor.fetchone()
#         if user:
#             session['loggedin'] = True
#             session['userid'] = user['userid']
#             session['name'] = user['name']
#             session['email'] = user['email']
#             message = 'Logged in successfully !'
#             return render_template('complaint.html', message=message)
#         else:
#             message = 'Please enter correct email / password !'
#     return render_template('index.html', message=message)

# @app.route('/logout')
# def logout():
#     session.pop('loggedin', None)
#     session.pop('userid', None)
#     session.pop('email', None)
#     return redirect(url_for('login'))

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     message = ''
#     if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
#         userName = request.form['name']
#         password = request.form['password']
#         email = request.form['email']
#         cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#         cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
#         account = cursor.fetchone()
#         if account:
#             message = 'Account already exists !'
#         elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
#             message = 'Invalid email address !'
#         elif not userName or not password or not email:
#             message = 'Please fill out the form !'
#         else:
#             cursor.execute('INSERT INTO user (name, email, password) VALUES (%s, %s, %s)', (userName, email, password))
#             mysql.connection.commit()
#             message = 'You have successfully registered !'
#     elif request.method == 'POST':
#         message = 'Please fill out the form !'
#     return render_template('register.html', message=message)


# @app.route('/add_complaint', methods=['GET', 'POST'])
# def add_complaint():
#     if request.method == 'POST':
#         subject = request.form['subject']
#         complaint_type = request.form['complaint_type']
#         description = request.form['description']
#         cursor = mysql.connection.cursor()
#         cursor.execute('INSERT INTO complaints (id, name, subject, type_of_complaint, description) VALUES (NULL, %s, %s, %s, %s)',
#                     (session['name'], subject, complaint_type, description))
#         mysql.connection.commit()
#         cursor.close()
#         message = 'Thanks for the feedback! Your problem will be solved very soon.'
#         return render_template('complaint.html', message=message)
#     else:
#         return render_template('complaint.html', message=None)



# if __name__ == "__main__":
#     app.run(debug=True)




