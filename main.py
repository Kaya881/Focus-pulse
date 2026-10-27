import cv2
import time
import activity
import chatbot
from face_detection import process_frame
from classifier import classify_status

# ── Start Listeners ──
activity.start_listeners()

# ── Variables ──
blink_count      = 0
eye_visible_prev = False
window_start     = time.time()
last_api_time    = 0
API_INTERVAL     = 6
current_emotion  = "Analyzing..."
current_head     = "Center"

# ── Text Wrap Helper ──
def draw_wrapped(frame, text, x, y, color, scale=0.58, thickness=1, max_chars=52):
    words  = text.split()
    line   = ""
    for word in words:
        if len(line + word) > max_chars:
            cv2.putText(frame, line.strip(), (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)
            y    += 26
            line  = word + " "
        else:
            line += word + " "
    if line:
        cv2.putText(frame, line.strip(), (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)

# ── Camera ──
cap = cv2.VideoCapture(0)
print("Camera chal raha hai - 'q' dabao band karne ke liye")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    h_frame, w_frame = frame.shape[:2]

    # ── Face Detection ──
    frame, blink_count, eye_visible_now, current_emotion, current_head = process_frame(
        frame, blink_count, eye_visible_prev
    )
    eye_visible_prev = eye_visible_now

    # ── Activity Data ──
    keys, moves, idle_seconds = activity.get_activity()

    # ── Classification ──
    status, status_color = classify_status(blink_count, keys, moves, idle_seconds)

    # ── AI Suggestion ──
    now = time.time()
    if not chatbot.is_busy() and (now - last_api_time >= API_INTERVAL):
        last_api_time = now
        chatbot.fetch_suggestion_async(
            status, blink_count, keys, moves,
            idle_seconds, current_emotion, current_head
        )

    # ── UI ──
    # Status bar upar
    cv2.rectangle(frame, (0, 0), (w_frame, 55), (40, 40, 40), -1)
    cv2.putText(frame, f"STATUS: {status}", (15, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, status_color, 2)

    # Face info
    if current_emotion != "No Face":
        eye_txt = "Eyes: Open" if eye_visible_now else "Eyes: BLINK!"
        eye_col = (0, 255, 0) if eye_visible_now else (0, 0, 255)
        cv2.putText(frame, eye_txt, (15, 78),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, eye_col, 2)
        cv2.putText(frame, f"Expression: {current_emotion}", (15, 103),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
        cv2.putText(frame, f"Head: {current_head}", (15, 128),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    else:
        cv2.putText(frame, "No Face Detected", (15, 78),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

    cv2.putText(frame,
                f"Blinks: {blink_count}  Keys: {keys}  Mouse: {moves}  Idle: {idle_seconds}s",
                (15, 153), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 0), 1)

    # AI Suggestion box neeche
    cv2.rectangle(frame, (0, h_frame-95), (w_frame, h_frame), (20, 20, 20), -1)
    cv2.putText(frame, "AI Coach:", (15, h_frame-70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2)
    draw_wrapped(frame, chatbot.get_current_suggestion(),
                 15, h_frame-45, (255, 255, 255))

    # Reset har 10 second
    if time.time() - window_start >= 10:
        activity.reset_activity()
        blink_count  = 0
        window_start = time.time()

    cv2.imshow("AI Study Fatigue Analyzer", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ── Cleanup ──
cap.release()
cv2.destroyAllWindows()
activity.stop_listeners()
print("Program band ho gaya!")