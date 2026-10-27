from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import threading
import time
import json
import requests

load_dotenv()

import activity
import chatbot
import deepface_analyzer
from classifier import classify_status

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY must be configured in the environment or .env file.")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

db = SQLAlchemy(app)

# ── Database Model ──
class User(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password      = db.Column(db.String(200), nullable=False)
    last_activity = db.Column(db.String(500), default="")
    last_topic    = db.Column(db.String(200), default="")

with app.app_context():
    db.create_all()

# ── State ──
last_api_time     = 0
last_fatigue_time = 0
API_INTERVAL      = 45

current_frame_data = {
    "status":          "MONITORING",
    "status_color":    "#ffffff",
    "emotion":         "Analyzing...",
    "head":            "Center",
    "blinks":          0,
    "keys":            0,
    "moves":           0,
    "idle":            0,
    "suggestion":      "Collecting data for accurate analysis... 📊",
    "eye_status":      "Open",
    "show_game_popup": False
}

user_conversations  = {}
user_quiz_questions = {}

def color_to_hex(color_tuple):
    if isinstance(color_tuple, str):
        return color_tuple
    if color_tuple == (0, 255, 0):   return "#00ff00"
    if color_tuple == (0, 0, 255):   return "#ff4444"
    if color_tuple == (0, 165, 255): return "#ffa500"
    return "#ffffff"

# ── Routes ──
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    success = request.args.get('success')
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user'] = user.username
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Invalid username or password!")
    return render_template('login.html',
        success="Account created successfully! Please login. ✅" if success else None)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')

        if not username or not email or not password:
            return render_template('signup.html', error="Please fill all fields!")
        if password != confirm:
            return render_template('signup.html', error="Passwords do not match!")
        if len(password) < 6:
            return render_template('signup.html', error="Password must be at least 6 characters!")
        if User.query.filter_by(username=username).first():
            return render_template('signup.html', error="Username already exists!")
        if User.query.filter_by(email=email).first():
            return render_template('signup.html', error="Email already registered!")

        hashed   = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login') + '?success=1')

    return render_template('signup.html')

@app.route('/logout')
def logout():
    activity.stop_listeners()
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['user']).first()
    last_topic = user.last_topic if user and user.last_topic else ""
    return render_template('dashboard.html', user=session['user'], last_topic=last_topic)

@app.route('/chatbot_page')
def chatbot_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['user']).first()
    last_topic = user.last_topic if user and user.last_topic else ""
    return render_template('chatbot.html', user=session['user'], last_topic=last_topic)

@app.route('/admin')
def admin():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('login'))
    users = User.query.all()
    return render_template('admin.html', users=users)

# ── Camera Routes ──
@app.route('/start_camera', methods=['POST'])
def start_camera():
    activity.start_listeners()
    return jsonify({"status": "started"})

@app.route('/stop_camera', methods=['POST'])
def stop_camera():
    activity.stop_listeners()
    activity.reset_activity()
    return jsonify({"status": "stopped"})

@app.route('/update_face_data', methods=['POST'])
def update_face_data():
    global current_frame_data, last_fatigue_time, last_api_time
    data = request.json
    now  = time.time()

    blinks     = data.get('blinks', 0)
    head_dir   = data.get('head', 'Center')
    eye_status = data.get('eye_status', 'Open')
    ear        = float(data.get('ear', 0.3))
    frame_b64  = data.get('frame_b64', '')

    # DeepFace emotion analyze karo async
    if frame_b64:
        deepface_analyzer.analyze_async(frame_b64)

    # DeepFace se current emotion lo
    emotion = deepface_analyzer.get_emotion()

    keys, moves, idle_seconds = activity.get_activity()

    # ── Fast blink detection — 6+ blinks = instant FATIGUED ──
    if blinks >= 6:
        status       = "FATIGUED"
        status_color = "#ff4444"
    else:
        raw_status, raw_color = classify_status(blinks, keys, moves, idle_seconds)
        status       = raw_status
        status_color = color_to_hex(raw_color)

    # AI suggestion
    if not chatbot.is_busy() and (now - last_api_time >= API_INTERVAL):
        last_api_time = now
        chatbot.fetch_suggestion_async(
            status, blinks, keys, moves,
            idle_seconds, emotion, head_dir
        )

    # Fatigue popup — har 3 min mein ek baar
    show_popup = False
    if status == "FATIGUED" and (now - last_fatigue_time) > 180:
        show_popup        = True
        last_fatigue_time = now

    current_frame_data.update({
        "status":          status,
        "status_color":    status_color,
        "emotion":         emotion,
        "head":            head_dir,
        "blinks":          blinks,
        "keys":            keys,
        "moves":           moves,
        "idle":            idle_seconds,
        "suggestion":      chatbot.get_current_suggestion(),
        "eye_status":      eye_status,
        "show_game_popup": show_popup
    })

    return jsonify({
        "status":          status,
        "status_color":    status_color,
        "suggestion":      chatbot.get_current_suggestion(),
        "keys":            keys,
        "moves":           moves,
        "idle":            idle_seconds,
        "show_game_popup": show_popup,
        "emotion":         emotion
    })

@app.route('/get_frame')
def get_frame():
    return jsonify(current_frame_data)

# ── Chat Route ──
@app.route('/chat', methods=['POST'])
def chat():
    if 'user' not in session:
        return jsonify({"reply": "Please login first."})

    data         = request.json
    user_message = data.get('message', '')
    username     = session['user']

    if username not in user_conversations:
        user_conversations[username] = []

    user = User.query.filter_by(username=username).first()

    user_context = f"User's name: {username}."
    if user and user.last_topic:
        user_context += f" Last study topic: {user.last_topic}."
    if user and user.last_activity:
        user_context += f" Last activity: {user.last_activity}."

    mon = current_frame_data
    user_context += f" Current monitoring — Status: {mon.get('status','N/A')}, Blinks: {mon.get('blinks',0)}, Idle: {mon.get('idle',0)}s, Expression: {mon.get('emotion','N/A')}."

    topic_keywords = ['studying', 'reading', 'learning', 'working on',
                      'reading', 'parh rahi', 'kar raha', 'kar rahi',
                      'chapter', 'subject', 'topic', 'assignment']
    for kw in topic_keywords:
        if kw in user_message.lower():
            if user:
                user.last_topic    = user_message[:200]
                user.last_activity = f"Chat at {time.strftime('%H:%M')}"
                db.session.commit()
            break

    reply = chatbot.chat_response(
        user_message,
        user_conversations[username],
        user_context
    )

    user_conversations[username].append({"role": "user",     "content": user_message})
    user_conversations[username].append({"role": "assistant", "content": reply})

    if len(user_conversations[username]) > 24:
        user_conversations[username] = user_conversations[username][-24:]

    offer_quiz = any(w in reply.lower() for w in ['quiz', 'brain game', 'refresher', 'game'])

    return jsonify({"reply": reply, "offer_quiz": offer_quiz})

# ── Quiz Routes ──
@app.route('/generate_quiz', methods=['POST'])
def generate_quiz():
    username  = session.get('user', 'guest')
    data      = request.json
    topic     = data.get('topic', 'general knowledge')
    used      = user_quiz_questions.get(username, [])
    quiz_json = chatbot.generate_quiz(topic, used)

    try:
        clean = quiz_json.strip()
        if '```' in clean:
            clean = clean.split('```')[1]
            if clean.startswith('json'):
                clean = clean[4:]
        quiz = json.loads(clean.strip())
        for q in quiz.get('questions', []):
            used.append(q['q'][:50])
        user_quiz_questions[username] = used[-15:]
        return jsonify({"success": True, "quiz": quiz})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/get_riddle', methods=['GET'])
def get_riddle():
    riddle = chatbot.generate_riddle()
    return jsonify(riddle)

@app.route('/save_topic', methods=['POST'])
def save_topic():
    if 'user' not in session:
        return jsonify({"status": "error"})
    data  = request.json
    topic = data.get('topic', '')
    user  = User.query.filter_by(username=session['user']).first()
    if user:
        user.last_topic = topic
        db.session.commit()
    return jsonify({"status": "saved"})

@app.route('/save_monitoring_summary', methods=['POST'])
def save_monitoring_summary():
    if 'user' not in session:
        return jsonify({"status": "error"})
    data    = request.json
    summary = data.get('summary', '')
    user    = User.query.filter_by(username=session['user']).first()
    if user:
        user.last_activity = summary
        db.session.commit()
    return jsonify({"status": "saved"})

if __name__ == '__main__':
    app.run(debug=False, port=5000)