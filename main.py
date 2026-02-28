import threading
import time
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor

import interception
import mss
import numpy as np

COLUMNS = {"Q": 418.5, "S": 634.5, "D": 851.5, "J": 1067.5, "K": 1284.5, "L": 1500.5}
HIT_LINE_Y = 920
TOP_Y = 60
DETECT_Y = 850

YELLOW = np.array([253, 176, 85])
PURPLE = np.array([165, 138, 255])
TOLERANCE = 30
COOLDOWN = 0.12

COL_LEFT = int(min(COLUMNS.values())) - 10
HOLD_TIMEOUT = 5.0
CONFIRM_FRAMES = 6
WATCH_INTERVAL = 0.016
CAPTURE_INTERVAL = 0.016
HOLD_INTERVAL = 0.016

last_hit = {key: 0.0 for key in COLUMNS}
# Indique si une colonne est en cours de hold (bloque les redéclenchements)
holding = {key: False for key in COLUMNS}
executor = ThreadPoolExecutor(max_workers=len(COLUMNS) * 4)
stop_event = threading.Event()

shared_frame = None
frame_lock = threading.Lock()


# ── Capture ───────────────────────────────────────────────────────────────────


def capture_loop():
    global shared_frame
    zone = {
        "left": COL_LEFT,
        "top": TOP_Y,
        "width": int(max(COLUMNS.values())) - COL_LEFT + 10,
        "height": HIT_LINE_Y - TOP_Y,
    }
    with mss.mss() as sct:
        while not stop_event.is_set():
            frame = np.array(sct.grab(zone))[:, :, :3][:, :, ::-1]
            with frame_lock:
                shared_frame = frame
            time.sleep(CAPTURE_INTERVAL)


# ── Détection ────────────────────────────────────────────────────────────────


def _get_frame():
    with frame_lock:
        return shared_frame


def get_note(col_x, target_y):
    frame = _get_frame()
    if frame is None:
        return None
    ox = int(col_x) - COL_LEFT
    oy = target_y - TOP_Y
    x1, x2 = max(0, ox - 2), min(frame.shape[1], ox + 3)
    y1, y2 = max(0, oy - 2), min(frame.shape[0], oy + 3)
    patch = frame[y1:y2, x1:x2]
    if patch.size == 0:
        return None
    diff_y = np.abs(patch.astype(int) - YELLOW).mean(axis=2).min()
    diff_p = np.abs(patch.astype(int) - PURPLE).mean(axis=2).min()
    if diff_y < TOLERANCE and diff_y < diff_p:
        return "yellow"
    if diff_p < TOLERANCE:
        return "purple"
    return None


def note_still_present(col_x):
    frame = _get_frame()
    if frame is None:
        return False
    ox = int(col_x) - COL_LEFT
    oy = HIT_LINE_Y - TOP_Y
    x1, x2 = max(0, ox - 2), min(frame.shape[1], ox + 2)
    y1, y2 = max(0, oy - 60), min(frame.shape[0], oy + 10)
    patch = frame[y1:y2, x1:x2]
    return np.abs(patch.astype(int) - PURPLE).mean(axis=2).min() < 60


# ── Frappe ────────────────────────────────────────────────────────────────────


def wait_release(col_x):
    consecutive = 0
    deadline = time.time() + HOLD_TIMEOUT
    while consecutive < CONFIRM_FRAMES:
        if stop_event.is_set() or time.time() > deadline:
            break
        if note_still_present(col_x):
            consecutive = 0
        else:
            consecutive += 1
        time.sleep(HOLD_INTERVAL)


def hit_key(key, kind, col_x):
    try:
        if kind == "yellow":
            print(f"[YELLOW] {key}")
            interception.press(key.lower())
        elif kind == "purple":
            print(f"[PURPLE START] {key}")
            holding[key] = True
            interception.key_down(key.lower())
            wait_release(col_x)
            interception.key_up(key.lower())
            holding[key] = False
            print(f"[PURPLE END] {key}")
    except Exception as e:
        holding[key] = False
        print(f"[ERR] hit_key {key}: {e}")


# ── Surveillance par colonne ──────────────────────────────────────────────────


def watch_column(key, col_x):
    while not stop_event.is_set():
        note = get_note(col_x, DETECT_Y)
        now = time.time()

        if note and not holding[key] and (now - last_hit[key]) > COOLDOWN:
            last_hit[key] = now
            print(f"[HIT] {key} → {note}  delta={now - last_hit[key]:.3f}")
            executor.submit(hit_key, key, note, col_x)

        time.sleep(WATCH_INTERVAL)


# ── Overlay ───────────────────────────────────────────────────────────────────


def quit_app():
    stop_event.set()
    executor.shutdown(wait=False)
    root.destroy()


root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-transparentcolor", "black")
root.attributes("-alpha", 0.8)
root.geometry("1920x1080+0+0")

canvas = tk.Canvas(root, width=1920, height=1080, bg="black", highlightthickness=0)
canvas.pack()

# Bouton quitter (échappe aussi au clavier)
btn_quit = tk.Button(
    root,
    text="✕ Quitter",
    command=quit_app,
    bg="#ff4444",
    fg="white",
    font=("Arial", 11, "bold"),
    relief="flat",
    padx=8,
    pady=4,
)
btn_quit.place(x=20, y=20)
root.bind("<Escape>", lambda e: quit_app())

threading.Thread(target=capture_loop, daemon=True).start()
for key, col_x in COLUMNS.items():
    threading.Thread(target=watch_column, args=(key, col_x), daemon=True).start()


def draw_overlay():
    if stop_event.is_set():
        return
    canvas.delete("all")
    for key, x in COLUMNS.items():
        canvas.create_line(x, TOP_Y, x, HIT_LINE_Y, fill="lime", width=2)
        canvas.create_text(
            x, TOP_Y - 15, text=key, fill="lime", font=("Arial", 14, "bold")
        )
    canvas.create_line(0, HIT_LINE_Y, 1920, HIT_LINE_Y, fill="red", width=2)
    canvas.create_line(0, DETECT_Y, 1920, DETECT_Y, fill="cyan", width=1)
    root.after(16, draw_overlay)


draw_overlay()
root.mainloop()
