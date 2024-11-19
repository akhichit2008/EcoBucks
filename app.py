from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from ai import calculate_initial_score, suggest_daily_tasks
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
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

@app.route('/', methods=['GET', 'POST'])
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

@app.route('/cert',methods=['GET','POST'])
def cert():
    if request.method == "POST":
        answers = request.get_json()
        keys = {
        "Which of the following is the most energy-efficient type of light bulb?": "LED",
        "Which gas is most commonly associated with climate change?": "Carbon Dio-oxide",
        "What is the primary benefit of composting organic waste?": "Reduces Landfill Waste",
        "Which of the following is a renewable energy source?": "Solar Power",
        "What is the main purpose of recycling?": "To reduce pollution"
        }
        cert_score = 0
        for i in range(len(answers)):
            if answers[i] == list(keys.values())[i]:
                cert_score += 10
        print(cert_score)
        return redirect(url_for("dashboard"))
    return render_template("cert.html")

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

# Route for logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
