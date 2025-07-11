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
from browser_tracker import update_browser_tracking, get_browser_status

LOG_FILE = "data/logs.json"
STATUS_FILE = "data/status.json"
SESSIONS_FILE = "data/sessions.json"
ALERT_CONFIG_FILE = "data/alert_config.json"

# Alert configuration
ALERT_LEVELS = [
    {"minutes": 3, "title": "Idle App Alert", "severity": "info"},
    {"minutes": 10, "title": "Long Idle App", "severity": "warning"},
    {"minutes": 30, "title": "Very Long Idle App", "severity": "critical"},
]

# Break reminder configuration
BREAK_REMINDER_INTERVAL = 180  # 3 minutes in seconds

# Apps to exclude from alerts (system apps, etc.)
EXCLUDED_APPS = {
    "dwm.exe",
    "explorer.exe",
    "winlogon.exe",
    "csrss.exe",
    "wininit.exe",
    "services.exe",
    "lsass.exe",
    "svchost.exe",
    "taskhost.exe",
    "dllhost.exe",
    "conhost.exe",
    "RuntimeBroker.exe",
    "ApplicationFrameHost.exe",
    "ShellExperienceHost.exe",
    "StartMenuExperienceHost.exe",
    "SearchApp.exe",
    "UserOOBEBroker.exe",
    "SettingsApp.exe",
    "SystemSettings.exe",
}

log_buffer = []
keystroke_count = 0
session_start_time = time.time()
current_app = None
current_title = None
start_time = time.time()
open_apps = {}
sessions = []
notifier = None
last_mouse_move_time = time.time()
last_break_reminder_time = time.time()
alert_config = {}

# Initialize notifier with error handling
try:
    notifier = ToastNotifier()
    print("[Tracker] Toast notifications initialized successfully")
except Exception as e:
    print(f"[Tracker] Toast notification initialization failed: {e}")
    notifier = None

# Ensure data directory exists
os.makedirs("data", exist_ok=True)


def load_alert_config():
    """Load alert configuration from file"""
    global alert_config
    try:
        if os.path.exists(ALERT_CONFIG_FILE):
            with open(ALERT_CONFIG_FILE, "r") as f:
                alert_config = json.load(f)
        else:
            alert_config = {
                "enabled": True,
                "whitelist": [],  # Apps to never alert for
                "snooze_until": {},  # App -> timestamp when snooze expires
                "alert_levels_enabled": [True, True, True],  # Which levels are enabled
                "show_resource_usage": True,
                "smart_filtering": True,
                "break_reminders_enabled": True,
                "break_reminder_interval": 180,  # 3 minutes in seconds
            }
            save_alert_config()
    except Exception as e:
        print(f"Error loading alert config: {e}")
        alert_config = {
            "enabled": True,
            "whitelist": [],
            "snooze_until": {},
            "alert_levels_enabled": [True, True, True],
            "show_resource_usage": True,
            "smart_filtering": True,
            "break_reminders_enabled": True,
            "break_reminder_interval": 180,  # 3 minutes in seconds
        }


def save_alert_config():
    """Save alert configuration to file"""
    try:
        with open(ALERT_CONFIG_FILE, "w") as f:
            json.dump(alert_config, f, indent=2)
    except Exception as e:
        print(f"Error saving alert config: {e}")


def get_process_resource_usage(app_name):
    """Get memory and CPU usage for an app"""
    try:
        total_memory = 0
        total_cpu = 0
        process_count = 0

        for proc in psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"]):
            try:
                if proc.info["name"] == app_name:
                    process_count += 1
                    total_memory += proc.info["memory_info"].rss
                    total_cpu += proc.info["cpu_percent"]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {
            "memory_mb": round(total_memory / (1024 * 1024), 1),
            "cpu_percent": round(total_cpu, 1),
            "process_count": process_count,
        }
    except Exception as e:
        print(f"Error getting resource usage for {app_name}: {e}")
        return {"memory_mb": 0, "cpu_percent": 0, "process_count": 0}


def should_alert_for_app(app_name, current_time):
    """Check if we should alert for this app based on configuration"""
    if not alert_config.get("enabled", True):
        return False

    # Check whitelist (apps to never alert for)
    if app_name in alert_config.get("whitelist", []):
        return False

    # Check system apps exclusion
    if alert_config.get("smart_filtering", True) and app_name in EXCLUDED_APPS:
        return False

    # Check snooze status
    snooze_until = alert_config.get("snooze_until", {}).get(app_name, 0)
    if current_time < snooze_until:
        return False

    return True


def show_notification(title, message, duration=5):
    """Show notification with error handling"""
    global notifier
    try:
        if notifier is not None:
            notifier.show_toast(title, message, duration=duration)
            print(f"[Notification] {title}: {message}")
        else:
            print(f"[Notification] {title}: {message}")
    except Exception as e:
        print(f"[Notification Error] {title}: {message} (Error: {e})")
        # Try to reinitialize notifier
        try:
            notifier = ToastNotifier()
            notifier.show_toast(title, message, duration=duration)
        except:
            print(f"[Notification] Fallback - {title}: {message}")


def snooze_app_alerts(app_name, minutes=30):
    """Snooze alerts for an app for specified minutes"""
    snooze_until = time.time() + (minutes * 60)
    alert_config["snooze_until"][app_name] = snooze_until
    save_alert_config()
    print(f"[Alert] Snoozed alerts for {app_name} for {minutes} minutes")


def check_break_reminder(current_time):
    """Check if it's time to send a break reminder"""
    global last_break_reminder_time

    if not alert_config.get("break_reminders_enabled", True):
        return

    reminder_interval = alert_config.get("break_reminder_interval", 180)
    time_since_last_reminder = current_time - last_break_reminder_time

    if time_since_last_reminder >= reminder_interval:
        # Calculate how many minutes since last reminder
        minutes_elapsed = int(time_since_last_reminder / 60)

        # Send break reminder
        show_notification(
            "💪 Break Time!",
            f"Hey! You've been working for {minutes_elapsed} minutes. "
            f"Time to take a break! 🚶‍♂️\n"
            f"• Stand up and stretch\n"
            f"• Look away from the screen\n"
            f"• Take a deep breath",
            duration=10,
        )

        # Update last reminder time
        last_break_reminder_time = current_time
        print(
            f"[Break Reminder] Sent reminder after {minutes_elapsed} minutes of activity"
        )


# Activity tracking
last_activity_time = time.time()


# Keystroke listener
def on_key_press(key):
    global \
        keystroke_count, \
        last_mouse_move_time, \
        last_break_reminder_time, \
        last_activity_time
    keystroke_count += 1
    current_time = time.time()
    last_mouse_move_time = current_time  # Reset inactivity timer on keyboard input
    last_activity_time = current_time
    # Don't reset break reminder on every keystroke, only on mouse movement


# Mouse movement listener
def on_mouse_move(x, y):
    global last_mouse_move_time, last_break_reminder_time, last_activity_time
    current_time = time.time()
    last_mouse_move_time = current_time
    last_activity_time = current_time
    # Reset break reminder time when user moves mouse (indicates active break)
    if (
        current_time - last_break_reminder_time > 60
    ):  # Only reset if last reminder was more than 1 minute ago
        last_break_reminder_time = current_time


keyboard_listener = keyboard.Listener(on_press=on_key_press)
keyboard_listener.start()

mouse_listener = mouse.Listener(on_move=on_mouse_move)
mouse_listener.start()

# Load alert configuration on startup
load_alert_config()


def load_existing_sessions():
    """Load existing sessions from file on startup"""
    global sessions
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, "r") as f:
                sessions = json.load(f)
            print(f"[Tracker] Loaded {len(sessions)} existing sessions")
        else:
            sessions = []
            print("[Tracker] No existing sessions file found, starting fresh")
    except Exception as e:
        print(f"[Tracker] Error loading sessions: {e}")
        sessions = []


def load_current_session_state():
    """Load current session state from status file to resume session"""
    global \
        session_start_time, \
        keystroke_count, \
        last_break_reminder_time, \
        last_activity_time
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r") as f:
                status = json.load(f)

            # Check if there's an active session (recent last_updated)
            if "last_updated" in status:
                last_updated = datetime.fromisoformat(status["last_updated"])
                time_since_update = (datetime.now() - last_updated).total_seconds()

                # If last update was less than 10 minutes ago, resume the session
                if time_since_update < 600:  # 10 minutes
                    if "session_start_time" in status:
                        session_start_from_file = datetime.fromisoformat(
                            status["session_start_time"]
                        )
                        session_start_time = session_start_from_file.timestamp()
                        keystroke_count = status.get("keystrokes", 0)
                        last_break_reminder_time = (
                            session_start_time  # Reset break reminder
                        )
                        last_activity_time = (
                            time.time()
                        )  # Set current time as last activity

                        resumed_duration = time.time() - session_start_time
                        print(
                            f"[Tracker] Resumed existing session (running for {resumed_duration:.0f} seconds)"
                        )
                        return True

            print(
                "[Tracker] Starting new session (previous session too old or invalid)"
            )
        else:
            print("[Tracker] No status file found, starting new session")

    except Exception as e:
        print(f"[Tracker] Error loading session state: {e}")

    # If we couldn't resume, start fresh
    current_time = time.time()
    session_start_time = current_time
    keystroke_count = 0
    last_break_reminder_time = current_time
    last_activity_time = current_time  # Initialize for new session
    return False


# Load existing data on startup
load_existing_sessions()
load_current_session_state()


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
    """Enhanced idle app checking with multiple alert levels"""
    for app, info in list(open_apps.items()):
        if not should_alert_for_app(app, current_time):
            continue

        last_used = info.get("last_used_time", info["start_time"])
        duration_since_used = current_time - last_used
        minutes_unused = duration_since_used / 60

        # Get current alert history
        alert_history = info.get("alert_history", [])

        # Check each alert level
        for level_index, level in enumerate(ALERT_LEVELS):
            if not alert_config.get("alert_levels_enabled", [True, True, True])[
                level_index
            ]:
                continue

            threshold_seconds = level["minutes"] * 60

            # Check if we should alert for this level
            if (
                minutes_unused >= level["minutes"]
                and level["minutes"] not in alert_history
            ):
                # Get resource usage if enabled
                resource_info = ""
                if alert_config.get("show_resource_usage", True):
                    usage = get_process_resource_usage(app)
                    if usage["memory_mb"] > 0:
                        resource_info = f"\n💾 Memory: {usage['memory_mb']}MB, CPU: {usage['cpu_percent']}%"

                # Build notification message
                instance_count = info.get("instance_count", 1)
                instance_text = (
                    f" ({instance_count} instances)" if instance_count > 1 else ""
                )

                severity_emoji = {"info": "💡", "warning": "⚠️", "critical": "🚨"}
                emoji = severity_emoji.get(level["severity"], "💡")

                message = (
                    f"{emoji} {app}{instance_text} has been idle for "
                    f"{int(minutes_unused)} minutes.{resource_info}\n"
                    f"Consider closing it to save resources."
                )

                show_notification(
                    level["title"],
                    message,
                    duration=8
                    + (level_index * 2),  # Longer duration for higher severity
                )

                # Record that we've alerted for this level
                alert_history.append(level["minutes"])
                open_apps[app]["alert_history"] = alert_history

                # Log the alert
                print(
                    f"[Alert] {level['title']} - {app} idle for {int(minutes_unused)} minutes"
                )

                # Auto-snooze very frequent alerts (30min+ idle apps)
                if level["minutes"] >= 30:
                    snooze_app_alerts(app, 60)  # Snooze for 1 hour

                break  # Only show one alert per check cycle


def save_log():
    with open(LOG_FILE, "a") as f:
        for entry in log_buffer:
            f.write(json.dumps(entry) + "\n")
    log_buffer.clear()


def save_sessions():
    try:
        with open(SESSIONS_FILE, "w") as f:
            json.dump(sessions, f, indent=2)
        print(f"[Tracker] Saved {len(sessions)} sessions to file")
    except Exception as e:
        print(f"[Tracker] Error saving sessions: {e}")


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
            "alert_history": app_info.get("alert_history", []),
            "is_current": app_name == current_app,
            "instance_count": app_info.get("instance_count", 1),
            "instances": app_info.get("instances", []),
            "resource_usage": get_process_resource_usage(app_name)
            if alert_config.get("show_resource_usage", True)
            else None,
        }

    # Get browser data
    browser_data = {}
    try:
        browser_data = get_browser_status()
    except Exception as e:
        print(f"Error getting browser data: {e}")

    with open(STATUS_FILE, "w") as f:
        json.dump(
            {
                "session_time": session_time,
                "session_start_time": datetime.fromtimestamp(
                    session_start_time
                ).isoformat(),
                "keystrokes": keystrokes,
                "last_updated": datetime.now().isoformat(),
                "open_apps": list(open_apps.keys()),
                "open_apps_details": open_apps_details,
                "current_app": current_app,
                "sessions": sessions[-5:],  # most recent 5 sessions
                "browser_data": browser_data,
                "alert_config": alert_config,
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
        keystroke_count, \
        last_activity_time
    try:
        session_ended_recently = False
        while True:
            now = time.time()

            # More robust session management - only end after true inactivity
            time_since_last_activity = now - last_activity_time
            session_duration = now - session_start_time

            # Debug logging every 30 seconds
            if int(now) % 30 == 0:
                print(
                    f"[Debug] Session duration: {session_duration:.1f}s, "
                    f"Time since activity: {time_since_last_activity:.1f}s, "
                    f"Keystrokes: {keystroke_count}"
                )

            # End session after 10 minutes of no activity (increased for stability)
            # Also prevent ending sessions that just started
            if (
                time_since_last_activity > 600  # 10 minutes of inactivity
                and session_duration > 60  # Session must be at least 1 minute
                and not session_ended_recently
            ):  # Prevent rapid session endings
                new_session = {
                    "start": datetime.fromtimestamp(session_start_time).isoformat(),
                    "end": datetime.fromtimestamp(now).isoformat(),
                    "duration_sec": round(session_duration, 2),
                }
                sessions.append(new_session)
                save_sessions()

                print(
                    f"[Tracker] Session ended after {time_since_last_activity / 60:.1f} minutes of inactivity. "
                    f"Session duration: {session_duration / 60:.1f} minutes, total sessions: {len(sessions)}"
                )

                show_notification(
                    "Session Ended",
                    f"No activity for {int(time_since_last_activity / 60)} minutes. "
                    f"Session recorded ({session_duration / 60:.1f} min). Total sessions: {len(sessions)}",
                    duration=5,
                )
                save_log()

                # Start new session
                session_start_time = now
                start_time = now
                keystroke_count = 0
                last_break_reminder_time = now
                last_activity_time = now  # Reset activity time for new session
                session_ended_recently = True

                # Reset the flag after 30 seconds to allow new sessions
                def reset_session_flag():
                    global session_ended_recently
                    time.sleep(30)
                    session_ended_recently = False

                threading.Thread(target=reset_session_flag, daemon=True).start()
                continue

            session_ended_recently = False  # Reset if we get here

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

            # Check for break reminders
            check_break_reminder(now)

            # Update browser tracking
            try:
                update_browser_tracking()
            except Exception as e:
                print(f"Browser tracking error: {e}")

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
                    # Reset alert history when app is used
                    open_apps[app]["alert_history"] = []
                    # Clear any snooze for this app since it's being used
                    if app in alert_config.get("snooze_until", {}):
                        del alert_config["snooze_until"][app]
                        save_alert_config()

                current_app, current_title = app, title
                start_time = now

                # Update activity time when switching apps
                last_activity_time = now

            # Update status file with current session time
            current_session_time = round(now - session_start_time, 2)
            update_status_file(current_session_time, keystroke_count)

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
