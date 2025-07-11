# tracker.py
import win32gui
import win32process
import psutil
import time
import json
import threading
from datetime import datetime
from pynput import keyboard, mouse
import tkinter as tk
import os
from win10toast import ToastNotifier

LOG_FILE = "data/logs.json"
STATUS_FILE = "data/status.json"
SESSIONS_FILE = "data/sessions.json"

log_buffer = []
keystroke_count = 0
session_start_time = time.time()
current_app = None
current_title = None
start_time = time.time()
open_apps = {}
sessions = []
notifier = ToastNotifier()
last_mouse_move_time = time.time()

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Keystroke listener
def on_key_press(key):
    global keystroke_count
    keystroke_count += 1

# Mouse movement listener
def on_mouse_move(x, y):
    global last_mouse_move_time
    last_mouse_move_time = time.time()

keyboard_listener = keyboard.Listener(on_press=on_key_press)
keyboard_listener.start()

mouse_listener = mouse.Listener(on_move=on_mouse_move)
mouse_listener.start()

def get_active_window():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        proc = psutil.Process(pid)
        return proc.name(), win32gui.GetWindowText(hwnd)
    except:
        return None, None

def get_open_windows():
    windows = {}
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                proc = psutil.Process(pid)
                name = proc.name()
                title = win32gui.GetWindowText(hwnd)
                if name:
                    windows[name] = {
                        "title": title,
                        "start_time": windows.get(name, {}).get("start_time", time.time())
                    }
            except:
                pass
    win32gui.EnumWindows(callback, None)
    return windows

def check_idle_apps(current_time):
    for app, info in list(open_apps.items()):
        duration = current_time - info["start_time"]
        if duration > 1800:  # 30 minutes
            notifier.show_toast("Idle App Detected", f"{app} has been open for over 30 minutes without focus.", duration=5)
            del open_apps[app]  # alert only once

def save_log():
    with open(LOG_FILE, "a") as f:
        for entry in log_buffer:
            f.write(json.dumps(entry) + "\n")
    log_buffer.clear()

def save_sessions():
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=2)

def update_status_file(session_time, keystrokes):
    with open(STATUS_FILE, "w") as f:
        json.dump({
            "session_time": session_time,
            "keystrokes": keystrokes,
            "last_updated": datetime.now().isoformat(),
            "open_apps": list(open_apps.keys()),
            "sessions": sessions[-5:]  # most recent 5 sessions
        }, f)

def update_tracker():
    global current_app, current_title, start_time, open_apps, session_start_time
    try:
        while True:
            now = time.time()

            # End session after 5 minutes of no mouse movement
            if now - last_mouse_move_time > 300:
                session_duration = round(now - session_start_time, 2)
                sessions.append({
                    "start": datetime.fromtimestamp(session_start_time).isoformat(),
                    "end": datetime.fromtimestamp(now).isoformat(),
                    "duration_sec": session_duration
                })
                save_sessions()
                notifier.show_toast("Session Ended", f"No activity for 5 minutes. Session recorded ({session_duration} sec).", duration=5)
                save_log()
                session_start_time = time.time()
                start_time = session_start_time
                continue

            open_windows = get_open_windows()
            for app in open_windows:
                if app not in open_apps:
                    open_apps[app] = {
                        "title": open_windows[app]["title"],
                        "start_time": now
                    }
            check_idle_apps(now)

            app, title = get_active_window()
            if app != current_app:
                end_time = now
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
                start_time = now
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
        label_open_apps.config(text=f"Open Apps: {len(open_apps)}")
        label_sessions.config(text=f"Sessions Tracked: {len(sessions)}")
        update_status_file(session_time, keystroke_count)
        root.after(1000, update_ui)

    root = tk.Tk()
    root.title("Productivity Monitor")

    label_keystrokes = tk.Label(root, text="Keystrokes: 0", font=("Arial", 14))
    label_keystrokes.pack(pady=10)

    label_session = tk.Label(root, text="Session Time: 0 sec", font=("Arial", 14))
    label_session.pack(pady=10)

    label_open_apps = tk.Label(root, text="Open Apps: 0", font=("Arial", 14))
    label_open_apps.pack(pady=10)

    label_sessions = tk.Label(root, text="Sessions Tracked: 0", font=("Arial", 14))
    label_sessions.pack(pady=10)

    update_ui()
    root.mainloop()

# Run tracker and dashboard concurrently
if __name__ == "__main__":
    print("[Tracker] Running... Press Ctrl+C to stop.")
    tracker_thread = threading.Thread(target=update_tracker)
    tracker_thread.daemon = True
    tracker_thread.start()
    run_dashboard()


# insights.py
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"
LOG_FILE = "data/logs.json"


def read_recent_logs(n=20):
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
    logs = [json.loads(line) for line in lines[-n:]]
    return logs

def generate_prompt(log_data):
    return f"""You are an AI productivity assistant. The following is the user's recent app usage data:

{json.dumps(log_data, indent=2)}

Based on this, suggest 3 specific and actionable productivity improvements."""

def ask_llm(prompt):
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"]

def main():
    log_data = read_recent_logs()
    prompt = generate_prompt(log_data)
    suggestions = ask_llm(prompt)
    print("\n[Productivity Suggestions]\n")
    print(suggestions)

if __name__ == "__main__":
    main()
