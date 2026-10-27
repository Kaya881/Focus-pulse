import time
import threading
import ctypes
from ctypes import wintypes

# ── Shared Variables ──
key_count          = 0
mouse_moves        = 0
last_activity_time = time.time()
lock               = threading.Lock()
_running           = False
_thread            = None

# Windows API
user32 = ctypes.windll.user32

# Virtual key states
_prev_key_states = {}
_prev_mouse_pos  = (0, 0)

def _activity_worker():
    global key_count, mouse_moves, last_activity_time, _running, _prev_mouse_pos

    # Keys to monitor
    keys_to_check = list(range(0x08, 0x90))  # All common keys

    while _running:
        try:
            # ── Keyboard check ──
            for vk in keys_to_check:
                state = user32.GetAsyncKeyState(vk)
                if state & 0x0001:  # Key was pressed since last call
                    with lock:
                        key_count += 1
                        last_activity_time = time.time()
                    break

            # ── Mouse check ──
            pt = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            curr_pos = (pt.x, pt.y)

            if curr_pos != _prev_mouse_pos:
                dx = abs(curr_pos[0] - _prev_mouse_pos[0])
                dy = abs(curr_pos[1] - _prev_mouse_pos[1])
                if dx > 3 or dy > 3:  # Ignore tiny movements
                    with lock:
                        mouse_moves += 1
                        last_activity_time = time.time()
                _prev_mouse_pos = curr_pos

        except Exception:
            pass

        time.sleep(0.05)  # Check every 50ms

def start_listeners():
    global _running, _thread, key_count, mouse_moves, last_activity_time, _prev_mouse_pos

    if _running:
        return

    # Reset
    key_count          = 0
    mouse_moves        = 0
    last_activity_time = time.time()

    # Get initial mouse position
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    _prev_mouse_pos = (pt.x, pt.y)

    _running = True
    _thread  = threading.Thread(target=_activity_worker, daemon=True)
    _thread.start()

def stop_listeners():
    global _running
    _running = False

def get_activity():
    with lock:
        keys  = key_count
        moves = mouse_moves
    idle = int(time.time() - last_activity_time)
    return keys, moves, idle

def reset_activity():
    global key_count, mouse_moves
    with lock:
        key_count   = 0
        mouse_moves = 0