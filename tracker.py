import win32gui
import win32process
import psutil
import time
import json
import threading
from datetime import datetime
from pynput import keyboard
import tkinter as tk
import os
 
LOG_FILE = "data/logs.json"
STATUS_FILE = "data/status.json"
 
log_buffer = []
keystroke_count = 0
session_start_time = time.time()
current_app = None
current_title = None
start_time = time.time()
 
# Ensure data directory exists
os.makedirs("data", exist_ok=True)
 
# Keystroke listener
def on_key_press(key):
    global keystroke_count
    keystroke_count += 1
 
listener = keyboard.Listener(on_press=on_key_press)
listener.start()
 
def get_active_window():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        proc = psutil.Process(pid)
        return proc.name(), win32gui.GetWindowText(hwnd)
    except:
        return None, None
 
def save_log():
    with open(LOG_FILE, "a") as f:
        for entry in log_buffer:
            f.write(json.dumps(entry) + "\n")
    log_buffer.clear()
 
def update_status_file(session_time, keystrokes):
    with open(STATUS_FILE, "w") as f:
        json.dump({
            "session_time": session_time,
            "keystrokes": keystrokes,
            "last_updated": datetime.now().isoformat()
        }, f)
 
def update_tracker():
    global current_app, current_title, start_time
    try:
        while True:
            app, title = get_active_window()
            if app != current_app:
                end_time = time.time()
                if current_app:
                    duration = round(end_time - start_time, 2)
                    log_buffer.append({
                        "app": current_app,
                        "title": current_title,
                        "start": datetime.fromtimestamp(start_time).isoformat(),
                        "end": datetime.fromtimestamp(end_time).isoformat(),
                        "duration_sec": duration
                    })
                    if len(log_buffer) >= 10:
                        save_log()
                current_app, current_title = app, title
                start_time = time.time()
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[Tracker] Stopping and saving log...")
        save_log()
 
# Frontend GUI
def run_dashboard():
    def update_ui():
        now = time.time()
        session_time = round(now - session_start_time, 2)
        label_keystrokes.config(text=f"Keystrokes: {keystroke_count}")
        label_session.config(text=f"Session Time: {session_time} sec")
        update_status_file(session_time, keystroke_count)
        root.after(1000, update_ui)
 
    root = tk.Tk()
    root.title("Productivity Monitor")
 
    label_keystrokes = tk.Label(root, text="Keystrokes: 0", font=("Arial", 14))
    label_keystrokes.pack(pady=10)
 
    label_session = tk.Label(root, text="Session Time: 0 sec", font=("Arial", 14))
    label_session.pack(pady=10)
 
    update_ui()
    root.mainloop()
 
# Run tracker and dashboard concurrently
if __name__ == "__main__":
    print("[Tracker] Running... Press Ctrl+C to stop.")
    tracker_thread = threading.Thread(target=update_tracker)
    tracker_thread.daemon = True
    tracker_thread.start()
    run_dashboard()
