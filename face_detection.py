import cv2
from classifier import get_head_direction, get_expression

# ── Detectors ──
face_cascade  = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade   = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

def process_frame(frame, blink_count, eye_visible_prev):
    gray     = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w     = frame.shape[:2]
    faces    = face_cascade.detectMultiScale(gray, 1.3, 5)

    eye_visible_now = False
    emotion         = "No Face"
    head_dir        = "Unknown"
    eye_count       = 0

    for (x, y, fw, fh) in faces:
        # Face box
        cv2.rectangle(frame, (x, y), (x+fw, y+fh), (0, 255, 0), 2)

        # Head direction
        head_dir = get_head_direction(x, fw, w)
        cv2.putText(frame, head_dir, (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)

        # Eyes — sirf upar wala hissa
        face_gray  = gray[y:y+fh//2, x:x+fw]
        face_color = frame[y:y+fh//2, x:x+fw]
        eyes       = eye_cascade.detectMultiScale(face_gray, 1.1, 5)
        eye_count  = len(eyes)

        if eye_count >= 1:
            eye_visible_now = True
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(face_color, (ex, ey),
                              (ex+ew, ey+eh), (255, 0, 0), 2)

        # Smile — sirf neeche wala hissa
        smile_gray = gray[y+fh//2:y+fh, x:x+fw]
        smiles     = smile_cascade.detectMultiScale(smile_gray, 1.7, 20)

        # Expression
        emotion = get_expression(eye_count, len(smiles))

    # Blink detect
    if eye_visible_prev and not eye_visible_now and len(faces) > 0:
        blink_count += 1

    return frame, blink_count, eye_visible_now, emotion, head_dir
