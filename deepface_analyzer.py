import cv2
import numpy as np
import base64
import threading
import time
from deepface import DeepFace

# ── State ──
current_emotion   = "Neutral"
current_age       = 0
is_analyzing      = False
last_analyze_time = 0
ANALYZE_INTERVAL  = 2.0  # Har 2 second mein analyze

def analyze_frame(frame_b64):
    global current_emotion, is_analyzing, last_analyze_time

    is_analyzing = True
    try:
        # Base64 decode karo
        img_data = base64.b64decode(frame_b64)
        nparr    = np.frombuffer(img_data, np.uint8)
        frame    = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return

        # DeepFace analyze
        result = DeepFace.analyze(
            frame,
            actions          = ['emotion'],
            enforce_detection = False,
            detector_backend  = 'opencv',
            silent            = True
        )

        emotion = result[0]['dominant_emotion']
        emotions = result[0]['emotion']

        # Professional emotion mapping
        emotion_map = {
            'angry':    'Stressed 😤',
            'disgust':  'Uncomfortable 😒',
            'fear':     'Anxious 😰',
            'happy':    'Happy 😊',
            'sad':      'Sad 😢',
            'surprise': 'Alert 😮',
            'neutral':  'Neutral 😐'
        }

        current_emotion   = emotion_map.get(emotion, 'Neutral 😐')
        last_analyze_time = time.time()

    except Exception as e:
        pass
    finally:
        is_analyzing = False

def analyze_async(frame_b64):
    now = time.time()
    if is_analyzing or (now - last_analyze_time) < ANALYZE_INTERVAL:
        return
    t = threading.Thread(target=analyze_frame, args=(frame_b64,), daemon=True)
    t.start()

def get_emotion():
    return current_emotion