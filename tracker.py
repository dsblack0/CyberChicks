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
    global keystroke_count, last_mouse_move_time
    keystroke_count += 1
    last_mouse_move_time = time.time()  # Reset inactivity timer on keyboard input


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
                if name and title:  # Only count windows with titles
                    if name not in windows:
                        windows[name] = {
                            "instances": [],
                            "count": 0,
                            "start_time": time.time(),
                        }

                    # Check if this specific window is already tracked
                    window_exists = any(
                        instance["title"] == title and instance["hwnd"] == hwnd
                        for instance in windows[name]["instances"]
                    )

                    if not window_exists:
                        windows[name]["instances"].append(
                            {"hwnd": hwnd, "title": title, "pid": pid}
                        )
                        windows[name]["count"] = len(windows[name]["instances"])

                        # Keep the earliest start time
                        if name in open_apps:
                            windows[name]["start_time"] = open_apps[name].get(
                                "start_time", time.time()
                            )
            except:
                pass

    win32gui.EnumWindows(callback, None)
    return windows


def check_idle_apps(current_time):
    for app, info in list(open_apps.items()):
        last_used = info.get("last_used_time", info["start_time"])
        duration_since_used = current_time - last_used

        already_alerted = info.get("alerted", False)

        if (
            duration_since_used > 180 and not already_alerted
        ):  # 3 minutes and not already alerted
            minutes_unused = max(1, int(duration_since_used / 60))
            instance_count = info.get("instance_count", 1)
            instance_text = (
                f" ({instance_count} instances)" if instance_count > 1 else ""
            )
            notifier.show_toast(
                "Unused App Alert",
                f"You haven't used {app}{instance_text} for {minutes_unused} minutes. Consider closing it to save resources.",
                duration=8,
            )
            # Mark as alerted to avoid repeated notifications
            open_apps[app]["alerted"] = True


def save_log():
    with open(LOG_FILE, "a") as f:
        for entry in log_buffer:
            f.write(json.dumps(entry) + "\n")
    log_buffer.clear()


def save_sessions():
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=2)


def update_status_file(session_time, keystrokes):
    # Create detailed info about open apps with timing
    open_apps_details = {}
    current_time = time.time()

    for app_name, app_info in open_apps.items():
        start_time = app_info.get("start_time", current_time)
        last_used = app_info.get("last_used_time", start_time)
        duration_open = current_time - start_time
        duration_since_used = current_time - last_used

        open_apps_details[app_name] = {
            "title": app_info.get("title", ""),
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "duration_open_sec": round(duration_open, 2),
            "last_used_time": datetime.fromtimestamp(last_used).isoformat(),
            "duration_since_used_sec": round(duration_since_used, 2),
            "alerted": app_info.get("alerted", False),
            "is_current": app_name == current_app,
            "instance_count": app_info.get("instance_count", 1),
            "instances": app_info.get("instances", []),
        }

    with open(STATUS_FILE, "w") as f:
        json.dump(
            {
                "session_time": session_time,
                "keystrokes": keystrokes,
                "last_updated": datetime.now().isoformat(),
                "open_apps": list(open_apps.keys()),
                "open_apps_details": open_apps_details,
                "current_app": current_app,
                "sessions": sessions[-5:],  # most recent 5 sessions
            },
            f,
        )


def update_tracker():
    global \
        current_app, \
        current_title, \
        start_time, \
        open_apps, \
        session_start_time, \
        keystroke_count
    try:
        while True:
            now = time.time()

            # End session after 5 minutes of no mouse movement
            if now - last_mouse_move_time > 300:
                session_duration = round(now - session_start_time, 2)
                sessions.append(
                    {
                        "start": datetime.fromtimestamp(session_start_time).isoformat(),
                        "end": datetime.fromtimestamp(now).isoformat(),
                        "duration_sec": session_duration,
                    }
                )
                save_sessions()
                notifier.show_toast(
                    "Session Ended",
                    f"No activity for 5 minutes. Session recorded ({session_duration} sec).",
                    duration=5,
                )
                save_log()
                session_start_time = time.time()
                start_time = session_start_time
                keystroke_count = 0  # Reset keystroke counter for new session
                continue

            open_windows = get_open_windows()
            for app in open_windows:
                if app not in open_apps:
                    # Get the most recent or first instance title for display
                    main_title = (
                        open_windows[app]["instances"][0]["title"]
                        if open_windows[app]["instances"]
                        else "No title"
                    )
                    open_apps[app] = {
                        "title": main_title,
                        "start_time": now,
                        "last_used_time": now,
                        "alerted": False,
                        "instance_count": open_windows[app]["count"],
                        "instances": open_windows[app]["instances"],
                    }
                else:
                    # Update instance count for existing apps
                    open_apps[app]["instance_count"] = open_windows[app]["count"]
                    open_apps[app]["instances"] = open_windows[app]["instances"]
            check_idle_apps(now)

            app, title = get_active_window()
            if app != current_app:
                end_time = now
                if current_app:
                    duration = round(end_time - start_time, 2)
                    log_buffer.append(
                        {
                            "app": current_app,
                            "title": current_title,
                            "start": datetime.fromtimestamp(start_time).isoformat(),
                            "end": datetime.fromtimestamp(end_time).isoformat(),
                            "duration_sec": duration,
                        }
                    )
                    if len(log_buffer) >= 10:
                        save_log()

                # Update the last_used_time for the newly focused app
                if app and app in open_apps:
                    open_apps[app]["last_used_time"] = now
                    open_apps[app]["alerted"] = (
                        False  # Reset alert status when app is used
                    )

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
    response = requests.post(
        OLLAMA_URL, json={"model": MODEL, "prompt": prompt, "stream": False}
    )
    return response.json()["response"]


def main():
    log_data = read_recent_logs()
    prompt = generate_prompt(log_data)
    suggestions = ask_llm(prompt)
    print("\n[Productivity Suggestions]\n")
    print(suggestions)


if __name__ == "__main__":
    main()
