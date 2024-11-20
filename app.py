from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from ai import calculate_initial_score, suggest_daily_tasks, check_submission
from sqlalchemy.orm import relationship
import os
import io
import json
import PIL
from PIL import Image

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png','jpg','jpeg'}
db = SQLAlchemy(app)    
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
 	 	
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/manifest.json')
def serve_manifest():
    return send_file('manifest.json', mimetype='application/manifest+json')

@app.route('/sw.js')
def serve_sw():
    return send_file('sw.js', mimetype='application/javascript')

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    score = db.Column(db.Integer,unique=False)
    tasks = db.relationship("Task",backref="user",lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    info = db.Column(db.String(200),nullable=False)
    user_id = db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    # Check if the user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))  # Redirect to the dashboard or another page if already logged in

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Your account has been created!', 'success')
        return redirect(url_for('questions'))

    return render_template('signup.html')

import cv2
@app.route('/cert',methods=['GET','POST'])  
@login_required
def cert():
    if request.method == "GET":
        # Load the certificate template
        cert_image = cv2.imread("static/cert-template.png")
        
        # Get the username from the form (or current_user)
        text = current_user.username.upper()  # Replace with current_user.username for logged-in user

        # Font settings
        font = cv2.FONT_HERSHEY_DUPLEX
        font_size = 3
        thickness = 2
        
        # Get text size to center the name on the certificate
        text_size = cv2.getTextSize(text, font, font_size, thickness)[0]
        text_width, text_height = text_size
        
        # Calculate position to center the text
        x = (cert_image.shape[1] - text_width) // 2
        y = (cert_image.shape[0] + text_height) // 2
        
        # Add text to image
        cv2.putText(cert_image, text, (x, y), font, font_size, (0, 0, 0), thickness)

        # Convert the OpenCV image (BGR) to RGB
        cert_image_rgb = cv2.cvtColor(cert_image, cv2.COLOR_BGR2RGB)

        # Save the image to a byte buffer
        img_byte_arr = io.BytesIO()
        img_pil = Image.fromarray(cert_image_rgb)  # Convert NumPy array to PIL Image
        img_pil.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        # Send the image as a downloadable file
        return send_file(
            img_byte_arr,
            mimetype="image/png",
            as_attachment=True,
            download_name=f"eco_certificate_{current_user.username}.png"
        )



# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
    return render_template('login.html')


@app.route('/questions', methods=['GET', 'POST'])
def questions():
    return render_template('questions.html')

@app.route('/leaderboard',methods=['GET'])
def leaderboard():
    return render_template('leaderboard.html')

@app.route('/upd',methods=['GET'])
def upd():
    user = current_user
    user.score += 2
    db.session.commit()
    return {"Status":"Success"}

@app.route('/rec',methods=['POST'])
def rec():
    if request.method == "POST":
        answers = request.get_json()
        print(answers)
        questions = ["How often do you recycle?","How often do you use public transportation","What type of vehicle do you drive?","What is your approach to reducing plastic usage?","How do you handle food waste?","What is your typical approach to reducing energy consumption at home?",""]
        responses = {q: a for q, a in zip(questions, answers)}
        score = calculate_initial_score(responses)
        tasks_recv = suggest_daily_tasks(score)
        tasks_recv = tasks_recv.split('\n')
        score = int(''.join(filter(str.isdigit, score)))
        tasks = []
        for task in tasks_recv:
            tasks.append(task)
            task = Task(info=task, user_id=current_user.id)
            db.session.add(task)
        if not tasks:
            tasks = ["Not Working!!!!"]
            task = Task(info="Not Working",user_id=current_user.id)
            db.session.add(task)
        print(tasks)
        user = current_user
        user.score = score
        db.session.commit()
        print("DB Updated Successfully!!!!!")
        return redirect(url_for("dashboard"))

@app.route('/dashboard')
@login_required
def dashboard():
    score = current_user.score
    tasks_recv = current_user.tasks
    tasks = []
    for task in tasks_recv:
        tasks.append(task.info)
    streak = 3
    leaderboard = User.query.order_by(User.score.desc()).limit(6).all()
    leaderboard_data = [{'username': user.username, 'score': user.score} for user in leaderboard]
    return render_template("dashboard.html",score=score,tasks=tasks,streak=streak,leaderboard=leaderboard_data,user=current_user)

@app.route('/submission/<task>',methods=['GET','POST'])
@login_required
def submission(task:str):
    print(task)
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            file = PIL.Image.open(filename)
            res = check_submission(file,task)
            if res:
                user = current_user
                user.score += 2
                db.session.commit()
    return render_template("submission.html",task=task)


# Route for logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
