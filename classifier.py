# ── Focus/Fatigue Classification ──

def classify_status(blinks, keys, moves, idle):
    if blinks >= 5 and keys <= 10 and moves <= 50:
        return "FATIGUED", (0, 0, 255)      # Red
    elif idle >= 15 and keys <= 5 and moves <= 30:
        return "DISTRACTED", (0, 165, 255)  # Orange
    elif keys >= 10 or moves >= 50:
        return "FOCUSED", (0, 255, 0)       # Green
    else:
        return "MONITORING", (255, 255, 255) # White

def get_head_direction(face_x, face_w, frame_w):
    face_center = face_x + face_w // 2
    frame_center = frame_w // 2
    offset = face_center - frame_center
    if offset < -60:
        return "Looking Left"
    elif offset > 60:
        return "Looking Right"
    else:
        return "Looking Center"

def get_expression(eye_count, smile_count):
    if smile_count > 0:
        return "Happy"
    elif eye_count == 0:
        return "Sleepy"
    elif eye_count == 1:
        return "Tired"
    else:
        return "Neutral"