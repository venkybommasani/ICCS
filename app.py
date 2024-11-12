import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import atexit
from twilio.rest import Client
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Twilio credentials (replace with your actual credentials)
TWILIO_ACCOUNT_SID = 'venkyboma@gmail.com'
TWILIO_AUTH_TOKEN = '!ICCSMeghanaV80*'
TWILIO_PHONE_NUMBER = 'whatsapp:+your_twilio_number'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'

mail = Mail(app)

# Initialize Firebase Admin with the service account
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class
class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

# User loader function
@login_manager.user_loader
def load_user(user_id):
    user_ref = db.collection('users').document(user_id)
    user = user_ref.get()
    if user.exists:
        user_data = user.to_dict()
        return User(id=user_id, email=user_data['email'])
    return None
    
#Funtion to send Whatsapp remainder
def send_whatsapp_remainder(phone, task):
    try:
        message = client.messages.create(
            body=f"Remainder: {task}",
            from_=TWILIO_PHONE_NUMBER,
            to=f'whatsapp:{phone}'
        )
        print(f"Whatsapp message sent to {phone} with task: {task}")
    except Exception as e:
        print(f"Failed to send whatsapp message: {e}")

""" Function to send reminder email with error handling
def send_reminder(email, task):
    try:
        msg = Message('Task Reminder', sender='your_email@gmail.com', recipients=[email])
        msg.body = f'Reminder: {task}'
        mail.send(msg)
        print(f"Email sent to {email} with task: {task}")
    except Exception as e:
        print(f"Failed to send email: {e}")
"""

# Schedule reminders
scheduler = BackgroundScheduler()
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

@app.route('/index')
@login_required
def index():
    # Retrieve tasks from Firestore
    tasks_ref = db.collection('tasks')
    tasks = [doc.to_dict() for doc in tasks_ref.stream()]
    return render_template('index.html', tasks=tasks)
    
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    else:
        return render_template('landing.html')

"""
@app.route('/')
def index():
    # Retrieve tasks from Firestore
    tasks_ref = db.collection('tasks')
    tasks = [doc.to_dict() for doc in tasks_ref.stream()]
    return render_template('index.html', tasks=tasks)
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']  # You should hash and verify passwords in production
        user_ref = db.collection('users').where('email', '==', email).get()
        if user_ref:
            user = user_ref[0]
            user_data = user.to_dict()
            # Perform password check here
            if password == user_data['password']:  # This is a placeholder check
                user_obj = User(id=user.id, email=user_data['email'])
                login_user(user_obj)
                return redirect(url_for('index'))
            else:
                flash('Invalid login credentials')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']  # Hash the password for security
        phone = request.form['phone']
        
        user_ref = db.collection('users').where('email', '==', email).get()
        if user_ref:
            flash('Email already exists')
        else:
            user_data = {'email': email, 'password': password, 'phone': phone}
            db.collection('users').add(user_data)
            flash('User registered successfully')
            return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add', methods=['POST'])
@login_required
def add_task():
    date = request.form.get('date')
    time = request.form.get('time')
    task = request.form.get('task')
    email = current_user.email
    
    if not date or not time or not task or not email:
        return "Error: All fields are required."
    
    datetime_str = f"{date} {time}"
    task_date = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
    
    user_ref = db.collection('users').where('email', '==', email).get()[0]
    user_data = user_ref.to_dict()
    phone = user_date['phone']
    
    task_data = {'date': task_date, 'task': task, 'email': email}
    
    # Store task in Firestore
    db.collection('tasks').add(task_data)
    
    # Schedule Whatsapp reminder with error handling
    scheduler.add_job(send_reminder_via_whatsapp, 'date', run_date=task_date, args=[phone, task])
    
    return redirect(url_for('index'))
    
@app.route('/landing')
def landing():
    return render_template('landing.html')


if __name__ == '__main__':
    app.run(debug=True)
