import requests
import threading
import time
import random
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

current_suggestion = "Initializing your personalized study monitor... 📊"
is_fetching        = False
suggestion_history = []
monitoring_history = []

SYSTEM_PROMPT = """You are ARIA — an Advanced Real-time Intelligence Assistant for students.

YOUR PERSONALITY:
- Warm, professional, and caring like a senior mentor
- Respond in the SAME language the user writes in
- English → English | Roman Urdu → Roman Urdu | Mixed → Mixed
- Use calm supportive emojis naturally: 📚 💡 😊 🎯 ✨ 💪 🧠 🌟
- Never be robotic or use scripted responses

YOUR CAPABILITIES:
1. REAL-TIME MONITORING — Analyze focus, fatigue, distraction from sensor data
2. PROBLEM SOLVING — Understand problem fully, offer roadmap, guide step by step if asked
3. FATIGUE RECOVERY — Offer brain games when very fatigued
4. MEMORY — Remember study topics and monitoring history
5. MOTIVATION — Specific data-driven encouragement

CONVERSATION RULES:
- React to EXACT sensor data — never give generic advice
- After roadmap, ask: "Would you like me to guide you through each step? 😊"
- If fatigued (blinks > 8, idle > 30s): "Would you like a quick brain game to refresh? 🎮"
- Be concise but meaningful
- If score < 60% on quiz: motivate specifically, offer a riddle challenge
- Always end with a gentle next-step nudge"""

def call_groq(messages, max_tokens=200, temperature=0.85):
    if not GROQ_KEY:
        return None

    body = {
        "model": "qwen/qwen3.6-27b",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        }
        r = requests.post(GROQ_URL, headers=headers, json=body, timeout=10)
        return r.json()["choices"][0]["message"]["content"].strip()
    except:
        return None

def get_suggestion(status, blinks, keys, moves, idle, emotion, head_dir):
    global current_suggestion, is_fetching, suggestion_history, monitoring_history
    is_fetching = True

    monitoring_history.append({
        "time": time.time(), "status": status,
        "blinks": blinks, "keys": keys,
        "moves": moves, "idle": idle
    })
    cutoff = time.time() - 120
    monitoring_history[:] = [m for m in monitoring_history if m["time"] > cutoff]

    if len(monitoring_history) >= 3:
        avg_blinks = sum(m["blinks"] for m in monitoring_history) / len(monitoring_history)
        avg_keys   = sum(m["keys"]   for m in monitoring_history) / len(monitoring_history)
        avg_idle   = sum(m["idle"]   for m in monitoring_history) / len(monitoring_history)
        data_note  = "2-min average"
    else:
        avg_blinks, avg_keys, avg_idle = blinks, keys, idle
        data_note  = "early data"

    history_text = " | ".join(suggestion_history[-4:]) if suggestion_history else "None"

    fatigue_note = ""
    if avg_blinks > 8 and avg_idle > 30:
        fatigue_note = "ALERT: Severe fatigue detected. Strongly suggest brain game."
    elif status == "DISTRACTED" and avg_idle > 20:
        fatigue_note = "User is distracted. Give a specific re-engagement tip."
    elif status == "FOCUSED" and avg_keys > 15:
        fatigue_note = "User is highly focused. Give positive reinforcement."

    prompt = f"""Monitor a student RIGHT NOW and give ONE precise coaching suggestion.

Live Data ({data_note}):
- Status: {status}
- Expression: {emotion}
- Head: {head_dir}
- Avg Blinks/10s: {avg_blinks:.1f} (normal: 3-5)
- Avg Keys/10s: {avg_keys:.1f}
- Avg Idle: {avg_idle:.1f}s

{fatigue_note}

Previous suggestions (DO NOT REPEAT): {history_text}

Requirements:
- Exactly 1 suggestion, max 18 words
- Reference the actual numbers
- Use 1 calm relevant emoji
- Sound like a caring human mentor, not a bot
- Vary tone: sometimes encouraging, sometimes gently alerting, sometimes practical"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    reply = call_groq(messages, max_tokens=60, temperature=0.92)
    if reply:
        current_suggestion = reply
        suggestion_history.append(reply)
        if len(suggestion_history) > 20:
            suggestion_history.pop(0)

    is_fetching = False

def fetch_suggestion_async(status, blinks, keys, moves, idle, emotion, head_dir):
    t = threading.Thread(
        target=get_suggestion,
        args=(status, blinks, keys, moves, idle, emotion, head_dir)
    )
    t.daemon = True
    t.start()

def get_current_suggestion():
    return current_suggestion

def is_busy():
    return is_fetching

def chat_response(user_message, conversation_history, user_context=None):
    context = f"\nUser Context: {user_context}" if user_context else ""
    messages = [{"role": "system", "content": SYSTEM_PROMPT + context}]
    for msg in conversation_history[-12:]:
        messages.append(msg)
    messages.append({"role": "user", "content": user_message})
    reply = call_groq(messages, max_tokens=350, temperature=0.85)
    return reply or "Sorry, I couldn't process that. Please try again 😊"

def generate_quiz(topic="general knowledge", used_questions=None):
    if used_questions is None:
        used_questions = []

    avoid = ""
    if used_questions:
        avoid = f"DO NOT use these questions: {', '.join(used_questions[:5])}"

    prompt = f"""Create a 3-question multiple choice quiz on "{topic}" for a student brain refresher.

{avoid}

IMPORTANT: Make questions UNIQUE and DIFFERENT every single time. Use variety:
- Interesting facts, logical thinking, science, history, or fun trivia
- Medium difficulty — not too easy, not too hard
- Confidence-boosting but genuinely challenging

Return ONLY this exact JSON format, nothing else:
{{
  "title": "Brain Refresher Quiz 🧠",
  "questions": [
    {{
      "q": "Question text here?",
      "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
      "answer": "A",
      "explanation": "Brief explanation why this is correct"
    }}
  ]
}}"""

    messages = [
        {"role": "system", "content": "You are a quiz generator. Return ONLY valid JSON, no markdown, no extra text."},
        {"role": "user", "content": prompt}
    ]
    reply = call_groq(messages, max_tokens=600, temperature=0.95)
    return reply

def generate_riddle():
    riddles = [
        {"q": "I speak without a mouth and hear without ears. I have no body, but I come alive with the wind. What am I?", "a": "An Echo"},
        {"q": "The more you take, the more you leave behind. What am I?", "a": "Footsteps"},
        {"q": "I have cities, but no houses live there. I have mountains, but no trees grow there. I have water, but no fish swim there. What am I?", "a": "A Map"},
        {"q": "What can run but never walks, has a mouth but never talks, has a head but never weeps, has a bed but never sleeps?", "a": "A River"},
        {"q": "I'm light as a feather, but even the world's strongest person can't hold me for more than 5 minutes. What am I?", "a": "Breath"},
        {"q": "The more you study me, the more I grow. What am I?", "a": "Knowledge"},
        {"q": "I have keys but no locks. I have space but no room. You can enter, but can't go inside. What am I?", "a": "A Keyboard"},
    ]
    return random.choice(riddles)