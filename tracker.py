# tracker.py - Optimized version
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
import subprocess
import winreg
from pathlib import Path
from win10toast import ToastNotifier
from browser_tracker import update_browser_tracking, get_browser_status

LOG_FILE = "data/logs.json"
STATUS_FILE = "data/status.json"
SESSIONS_FILE = "data/sessions.json"
ALERT_CONFIG_FILE = "data/alert_config.json"
CUSTOM_ALERTS_FILE = "data/custom_alerts.json"

# SnapAlert App ID for Windows notifications
SNAPALERT_APP_ID = "SnapAlert.ProductivityMonitor"

# Alert configuration
ALERT_LEVELS = [
    {"minutes": 3, "title": "Idle App Alert", "severity": "info"},
    {"minutes": 10, "title": "Long Idle App", "severity": "warning"},
    {"minutes": 30, "title": "Very Long Idle App", "severity": "critical"},
]

# Break reminder configuration
BREAK_REMINDER_INTERVAL = 180  # 3 minutes in seconds

# Performance optimization settings
MAIN_LOOP_INTERVAL = 5  # Increased from 3 to 5 seconds for better performance
WINDOW_ENUM_INTERVAL = 10  # Increased to 10 seconds
RESOURCE_CHECK_INTERVAL = 60  # Increased to 60 seconds (1 minute)
BROWSER_UPDATE_INTERVAL = 15  # Increased to 15 seconds

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

# Global variables
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
last_activity_time = time.time()

# Performance tracking
last_window_enum_time = 0
last_resource_check_time = 0
last_browser_update_time = 0
resource_usage_cache = {}
keyboard_listener = None
mouse_listener = None

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Initialize notifier with error handling
try:
    notifier = ToastNotifier()
    print("[Tracker] Toast notifications initialized successfully")
except Exception as e:
    print(f"[Tracker] Toast notification initialization failed: {e}")
    notifier = None


def ensure_app_id_registered():
    """Automatically register SnapAlert app ID with Windows on startup"""
    try:
        # Check if already registered
        key_path = f"SOFTWARE\\Classes\\AppUserModelId\\{SNAPALERT_APP_ID}"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path):
                print("[Tracker] SnapAlert app ID already registered")
                return True
        except FileNotFoundError:
            pass  # Not registered yet

        print("[Tracker] Registering SnapAlert app ID...")

        # Get icon path
        script_dir = Path(__file__).parent.absolute()
        icon_path = script_dir / "icons" / "snapalert.ico"

        # Register the app ID
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "SnapAlert")

            if icon_path.exists():
                winreg.SetValueEx(key, "IconUri", 0, winreg.REG_SZ, str(icon_path))
                winreg.SetValueEx(
                    key, "IconBackgroundColor", 0, winreg.REG_SZ, "#E31E24"
                )
                print(f"[Tracker] Icon registered: {icon_path}")

            winreg.SetValueEx(key, "ShowInSettings", 0, winreg.REG_DWORD, 1)

        print("[Tracker] ✅ SnapAlert app ID registered successfully")
        return True

    except Exception as e:
        print(f"[Tracker] ⚠️ App ID registration failed: {e}")
        return False


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
                "whitelist": [],
                "snooze_until": {},
                "alert_levels_enabled": [True, True, True],
                "show_resource_usage": True,
                "smart_filtering": True,
                "break_reminders_enabled": True,
                "break_reminder_interval": 180,
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
            "break_reminder_interval": 180,
        }


def save_alert_config():
    """Save alert configuration to file"""
    try:
        with open(ALERT_CONFIG_FILE, "w") as f:
            json.dump(alert_config, f, indent=2)
    except Exception as e:
        print(f"Error saving alert config: {e}")


def load_custom_alerts():
    """Load custom alerts from file"""
    try:
        if os.path.exists(CUSTOM_ALERTS_FILE):
            with open(CUSTOM_ALERTS_FILE, "r") as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading custom alerts: {e}")
        return []


def save_custom_alerts(alerts):
    """Save custom alerts to file"""
    try:
        with open(CUSTOM_ALERTS_FILE, "w") as f:
            json.dump(alerts, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving custom alerts: {e}")
        return False


def get_process_resource_usage_cached(app_name):
    """Disabled resource usage checking to prevent system crashes"""
    # Return static data to prevent psutil crashes
    return {"memory_mb": 0, "cpu_percent": 0, "process_count": 1}


def should_alert_for_app(app_name, current_time):
    """Check if we should alert for this app based on configuration"""
    if not alert_config.get("enabled", True):
        return False

    if app_name in alert_config.get("whitelist", []):
        return False

    if alert_config.get("smart_filtering", True) and app_name in EXCLUDED_APPS:
        return False

    snooze_until = alert_config.get("snooze_until", {}).get(app_name, 0)
    if current_time < snooze_until:
        return False

    return True


def show_notification_powershell(title, message, duration=8):
    """Show Windows notification using PowerShell with proper SnapAlert branding"""
    try:
        # Escape quotes in the message
        escaped_title = title.replace('"', '""').replace("'", "''")
        escaped_message = message.replace('"', '""').replace("'", "''")

        # PowerShell command using Windows Toast notifications with registered app ID
        powershell_cmd = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

# Create toast XML template
$template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>{escaped_title}</text>
            <text>{escaped_message}</text>
        </binding>
    </visual>
</toast>
"@

# Create XML document and toast notification
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)

# Create toast notification with registered SnapAlert app ID
$toast = New-Object Windows.UI.Notifications.ToastNotification($xml)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("{SNAPALERT_APP_ID}")
$notifier.Show($toast)
"""

        result = subprocess.run(
            ["powershell.exe", "-Command", powershell_cmd],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,  # Hide PowerShell window
        )

        if result.returncode == 0:
            print(f"[Tracker] PowerShell notification sent successfully: {title}")
            return True
        else:
            print(f"[Tracker] PowerShell failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"[Tracker] PowerShell notification error: {e}")
        return False


def show_notification_fallback(title, message, duration=8):
    """Fallback notification using win10toast_click"""
    try:
        from win10toast_click import ToastNotifier

        notifier = ToastNotifier()

        notifier.show_toast(
            title=title,
            msg=message,
            duration=duration,
            icon_path=None,
            threaded=True,
        )

        print(f"[Tracker] win10toast_click notification sent: {title}")
        return True

    except Exception as e:
        print(f"[Tracker] win10toast_click error: {e}")
        return False


def show_notification(title, message, duration=8):
    """Improved Windows notification function with multiple fallback methods"""
    try:
        print(f"[Tracker] Attempting to show: {title}")

        # Add SnapAlert branding to title if not already present
        if not title.startswith("🔺 SnapAlert"):
            branded_title = f"🔺 SnapAlert: {title}"
        else:
            branded_title = title

        # Method 1: Try win10toast_click first (we know this works for you)
        if show_notification_fallback(branded_title, message, duration):
            return True

        # Method 2: Try PowerShell method as backup (with registered app ID)
        print("[Tracker] win10toast_click failed, trying PowerShell...")
        if show_notification_powershell(branded_title, message, duration):
            return True

        # Method 3: Try plyer as fallback
        print("[Tracker] PowerShell failed, trying plyer...")
        try:
            from plyer import notification

            notification.notify(
                title=branded_title,
                message=message,
                app_name="SnapAlert",
                timeout=duration,
            )
            print(f"[Tracker] Plyer notification sent successfully")
            return True
        except Exception as e:
            print(f"[Tracker] Plyer notification failed: {e}")

        # Method 4: Try original win10toast as final fallback
        print("[Tracker] Trying original win10toast as final fallback...")
        try:
            from win10toast import ToastNotifier

            notifier = ToastNotifier()
            notifier.show_toast(
                title=branded_title,
                msg=message,
                duration=duration,
                icon_path=None,
                threaded=True,
            )
            print(f"[Tracker] win10toast notification sent successfully")
            return True
        except Exception as e:
            print(f"[Tracker] win10toast failed: {e}")

        # If all methods fail, at least log it
        print(
            f"[Tracker] All notification methods failed. Title: {branded_title}, Message: {message}"
        )
        return False

    except Exception as e:
        print(f"[Tracker] System error: {e}")
        return False


def snooze_app_alerts(app_name, minutes=30):
    """Snooze alerts for an app for specified minutes"""
    snooze_until = time.time() + (minutes * 60)
    alert_config["snooze_until"][app_name] = snooze_until
    save_alert_config()
    print(f"[Alert] Snoozed alerts for {app_name} for {minutes} minutes")


def check_custom_alerts(current_time):
    """Check custom alerts and trigger them when conditions are met"""
    global session_start_time, keystroke_count, current_app, open_apps

    try:
        # Load custom alerts
        custom_alerts = load_custom_alerts()
        alerts_modified = False

        for alert in custom_alerts:
            # Skip disabled alerts
            if not alert.get("enabled", True):
                continue

            alert_type = alert.get("type", "")
            condition = alert.get("condition", "greater_than")
            threshold = alert.get("threshold", 0)
            app_filter = alert.get("app_filter", "")

            # Check if alert should be triggered
            should_trigger = False
            current_value = 0

            if alert_type == "keystroke_count":
                current_value = keystroke_count
                should_trigger = evaluate_condition(current_value, condition, threshold)

            elif alert_type == "session_time":
                current_value = int((current_time - session_start_time) / 60)  # minutes
                should_trigger = evaluate_condition(current_value, condition, threshold)

            elif alert_type == "app_time":
                if (
                    app_filter
                    and app_filter == current_app
                    and current_app in open_apps
                ):
                    app_start_time = open_apps[current_app].get(
                        "start_time", current_time
                    )
                    current_value = int((current_time - app_start_time) / 60)  # minutes
                    should_trigger = evaluate_condition(
                        current_value, condition, threshold
                    )

            elif alert_type == "idle_time":
                if current_app and current_app in open_apps:
                    last_used = open_apps[current_app].get(
                        "last_used_time", current_time
                    )
                    current_value = int((current_time - last_used) / 60)  # minutes
                    should_trigger = evaluate_condition(
                        current_value, condition, threshold
                    )

            # Trigger alert if conditions are met
            if should_trigger:
                # Check if alert was recently triggered (prevent spam)
                last_triggered = alert.get("last_triggered")
                if last_triggered:
                    time_since_last = current_time - last_triggered
                    # Don't trigger same alert within 5 minutes
                    if time_since_last < 300:
                        continue

                # Format message with placeholders
                message = alert.get("message", "Custom alert triggered")
                message = message.replace("{threshold}", str(threshold))
                message = message.replace(
                    "{app}", app_filter or current_app or "application"
                )
                message = message.replace("{value}", str(current_value))

                # Show notification
                alert_name = alert.get("name", "Custom Alert")
                success = show_notification(alert_name, message, duration=8)

                if success:
                    # Update alert statistics
                    alert["last_triggered"] = current_time
                    alert["trigger_count"] = alert.get("trigger_count", 0) + 1
                    alerts_modified = True

                    print(
                        f"[Custom Alert] Triggered '{alert_name}' - {alert_type}: {current_value} {condition} {threshold}"
                    )

        # Save updated alerts if any were modified
        if alerts_modified:
            save_custom_alerts(custom_alerts)

    except Exception as e:
        print(f"[Custom Alert Error] {e}")


def evaluate_condition(current_value, condition, threshold):
    """Evaluate if current value meets the condition against threshold"""
    if condition == "greater_than":
        return current_value > threshold
    elif condition == "less_than":
        return current_value < threshold
    elif condition == "equal_to":
        return current_value == threshold
    return False


def check_break_reminder(current_time):
    """Check if it's time to send a break reminder"""
    global last_break_reminder_time

    if not alert_config.get("break_reminders_enabled", True):
        return

    reminder_interval = alert_config.get("break_reminder_interval", 180)
    time_since_last_reminder = current_time - last_break_reminder_time

    if time_since_last_reminder >= reminder_interval:
        minutes_elapsed = int(time_since_last_reminder / 60)

        show_notification(
            "💪 Break Time!",
            f"Hey! You've been working for {minutes_elapsed} minutes. "
            f"Time to take a break! 🚶‍♂️\n"
            f"• Stand up and stretch\n"
            f"• Look away from the screen\n"
            f"• Take a deep breath",
            duration=10,
        )

        last_break_reminder_time = current_time
        print(
            f"[Break Reminder] Sent reminder after {minutes_elapsed} minutes of activity"
        )


# Keystroke listener with better error handling
def on_key_press(key):
    global \
        keystroke_count, \
        last_mouse_move_time, \
        last_break_reminder_time, \
        last_activity_time
    try:
        keystroke_count += 1
        current_time = time.time()
        last_mouse_move_time = current_time
        last_activity_time = current_time

        # Debug logging for keystroke issues
        if keystroke_count % 100 == 0:  # Every 100 keystrokes
            print(f"[Keystroke Debug] Count: {keystroke_count}")
    except Exception as e:
        print(f"[Keystroke Error] {e}")


def on_mouse_move(x, y):
    global last_mouse_move_time, last_break_reminder_time, last_activity_time
    try:
        current_time = time.time()
        last_mouse_move_time = current_time
        last_activity_time = current_time

        if current_time - last_break_reminder_time > 60:
            last_break_reminder_time = current_time
    except Exception as e:
        print(f"[Mouse Error] {e}")


def start_input_listeners():
    """Start keyboard and mouse listeners with error handling"""
    global keyboard_listener, mouse_listener

    try:
        # Stop existing listeners if they exist
        if keyboard_listener:
            keyboard_listener.stop()
        if mouse_listener:
            mouse_listener.stop()

        # Start new listeners
        keyboard_listener = keyboard.Listener(on_press=on_key_press)
        keyboard_listener.start()
        print("[Tracker] Keyboard listener started successfully")

        mouse_listener = mouse.Listener(on_move=on_mouse_move)
        mouse_listener.start()
        print("[Tracker] Mouse listener started successfully")

        return True
    except Exception as e:
        print(f"[Input Listener Error] Failed to start listeners: {e}")
        return False


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

            if "last_updated" in status:
                last_updated = datetime.fromisoformat(status["last_updated"])
                time_since_update = (datetime.now() - last_updated).total_seconds()

                if time_since_update < 600:  # 10 minutes
                    if "session_start_time" in status:
                        session_start_from_file = datetime.fromisoformat(
                            status["session_start_time"]
                        )
                        session_start_time = session_start_from_file.timestamp()
                        keystroke_count = status.get("keystrokes", 0)
                        last_break_reminder_time = session_start_time
                        last_activity_time = time.time()

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

    # Start fresh session
    current_time = time.time()
    session_start_time = current_time
    keystroke_count = 0
    last_break_reminder_time = current_time
    last_activity_time = current_time
    return False


def get_active_window():
    """Get currently active window with better error handling"""
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None, None

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid)
            return proc.name(), win32gui.GetWindowText(hwnd)
        except:
            # If we can't get process info, just return the window title
            try:
                return "Unknown", win32gui.GetWindowText(hwnd)
            except:
                return None, None
    except Exception as e:
        return None, None


def get_open_windows_cached():
    """Cached version of window enumeration - only updates every 5 seconds"""
    global last_window_enum_time
    current_time = time.time()

    # Only enumerate windows every 5 seconds
    if current_time - last_window_enum_time < WINDOW_ENUM_INTERVAL:
        return {}

    last_window_enum_time = current_time
    windows = {}

    def callback(hwnd, extra):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return

            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc = psutil.Process(pid)
                    name = proc.name()
                except:
                    # If we can't get process info, skip this window entirely
                    return
            except Exception:
                return

            try:
                title = win32gui.GetWindowText(hwnd)
            except:
                title = "Unknown"

            if name and title:
                if name not in windows:
                    windows[name] = {
                        "instances": [],
                        "count": 0,
                        "start_time": time.time(),
                    }

                window_exists = any(
                    instance["title"] == title and instance["hwnd"] == hwnd
                    for instance in windows[name]["instances"]
                )

                if not window_exists:
                    windows[name]["instances"].append(
                        {"hwnd": hwnd, "title": title, "pid": pid}
                    )
                    windows[name]["count"] = len(windows[name]["instances"])

                    if name in open_apps:
                        windows[name]["start_time"] = open_apps[name].get(
                            "start_time", time.time()
                        )
        except Exception:
            # Silent failure for window enumeration errors
            pass

    try:
        win32gui.EnumWindows(callback, None)
    except Exception as e:
        print(f"[Window Enum Error] {e}")

    return windows


def check_idle_apps(current_time):
    """Enhanced idle app checking with performance optimization"""
    global last_resource_check_time

    for app, info in list(open_apps.items()):
        if not should_alert_for_app(app, current_time):
            continue

        last_used = info.get("last_used_time", info["start_time"])
        duration_since_used = current_time - last_used
        minutes_unused = duration_since_used / 60

        alert_history = info.get("alert_history", [])

        for level_index, level in enumerate(ALERT_LEVELS):
            if not alert_config.get("alert_levels_enabled", [True, True, True])[
                level_index
            ]:
                continue

            if (
                minutes_unused >= level["minutes"]
                and level["minutes"] not in alert_history
            ):
                # Resource usage disabled to prevent system crashes
                resource_info = ""

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
                    duration=8 + (level_index * 2),
                )

                alert_history.append(level["minutes"])
                open_apps[app]["alert_history"] = alert_history

                print(
                    f"[Alert] {level['title']} - {app} idle for {int(minutes_unused)} minutes"
                )

                if level["minutes"] >= 30:
                    snooze_app_alerts(app, 60)

                break

    # Update resource check time
    if current_time - last_resource_check_time >= RESOURCE_CHECK_INTERVAL:
        last_resource_check_time = current_time


def save_log():
    """Save log buffer to file"""
    try:
        with open(LOG_FILE, "a") as f:
            for entry in log_buffer:
                f.write(json.dumps(entry) + "\n")
        log_buffer.clear()
    except Exception as e:
        print(f"[Log Save Error] {e}")


def save_sessions():
    """Save sessions to file"""
    try:
        with open(SESSIONS_FILE, "w") as f:
            json.dump(sessions, f, indent=2)
        print(f"[Tracker] Saved {len(sessions)} sessions to file")
    except Exception as e:
        print(f"[Tracker] Error saving sessions: {e}")


def update_status_file(session_time, keystrokes):
    """Update status file with current data"""
    try:
        open_apps_details = {}
        current_time = time.time()

        for app_name, app_info in open_apps.items():
            start_time = app_info.get("start_time", current_time)
            last_used = app_info.get("last_used_time", start_time)
            duration_open = current_time - start_time
            duration_since_used = current_time - last_used

            # Resource usage disabled to prevent system crashes
            resource_usage = None

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
                "resource_usage": resource_usage,
            }

        # Get browser data with error handling
        browser_data = {}
        try:
            browser_data = get_browser_status()
        except Exception as e:
            print(f"Error getting browser data: {e}")
            browser_data = {}

        status_data = {
            "session_time": session_time,
            "session_start_time": datetime.fromtimestamp(
                session_start_time
            ).isoformat(),
            "keystrokes": keystrokes,
            "last_updated": datetime.now().isoformat(),
            "open_apps": list(open_apps.keys()),
            "open_apps_details": open_apps_details,
            "current_app": current_app,
            "sessions": sessions[-5:],
            "browser_data": browser_data,
            "alert_config": alert_config,
            "custom_alerts": load_custom_alerts(),
        }

        with open(STATUS_FILE, "w") as f:
            json.dump(status_data, f, indent=2)

        print(f"[Status Debug] Session time: {session_time}s, Keystrokes: {keystrokes}")

    except Exception as e:
        print(f"[Status Update Error] {e}")


def update_tracker():
    """Optimized main tracking loop with reduced system load"""
    global \
        current_app, \
        current_title, \
        start_time, \
        open_apps, \
        session_start_time, \
        keystroke_count, \
        last_activity_time, \
        last_browser_update_time

    try:
        session_ended_recently = False
        loop_count = 0

        print("[Tracker] Starting main tracking loop...")

        while True:
            loop_start_time = time.time()
            now = time.time()

            # Performance monitoring every 20 loops (now ~100 seconds)
            if loop_count % 20 == 0:
                print(
                    f"[Performance] Loop {loop_count}, Session: {(now - session_start_time) / 60:.1f}min, "
                    f"Keys: {keystroke_count}, Apps: {len(open_apps)}"
                )

            # Session management
            time_since_last_activity = now - last_activity_time
            session_duration = now - session_start_time

            # End session after 10 minutes of inactivity
            if (
                time_since_last_activity > 600
                and session_duration > 60
                and not session_ended_recently
            ):
                new_session = {
                    "start": datetime.fromtimestamp(session_start_time).isoformat(),
                    "end": datetime.fromtimestamp(now).isoformat(),
                    "duration_sec": round(session_duration, 2),
                }
                sessions.append(new_session)
                save_sessions()

                print(
                    f"[Tracker] Session ended after {time_since_last_activity / 60:.1f} minutes of inactivity"
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
                last_activity_time = now
                session_ended_recently = True

                def reset_session_flag():
                    global session_ended_recently
                    time.sleep(30)
                    session_ended_recently = False

                threading.Thread(target=reset_session_flag, daemon=True).start()
                continue

            session_ended_recently = False

            # Update open windows (cached - only every 10 seconds now)
            try:
                open_windows = get_open_windows_cached()
                for app in open_windows:
                    if app not in open_apps:
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
                        open_apps[app]["instance_count"] = open_windows[app]["count"]
                        open_apps[app]["instances"] = open_windows[app]["instances"]
            except Exception as e:
                print(f"[Window Update Error] {e}")

            # Check idle apps (less frequently)
            try:
                if loop_count % 3 == 0:  # Every 3rd loop (~15 seconds)
                    check_idle_apps(now)
            except Exception as e:
                print(f"[Idle Check Error] {e}")

            # Check break reminders (less frequently)
            try:
                if loop_count % 2 == 0:  # Every 2nd loop (~10 seconds)
                    check_break_reminder(now)
            except Exception as e:
                print(f"[Break Reminder Error] {e}")

            # Check custom alerts (every loop to ensure responsiveness)
            try:
                check_custom_alerts(now)
            except Exception as e:
                print(f"[Custom Alert Error] {e}")

            # Update browser tracking (even less frequently)
            if now - last_browser_update_time >= BROWSER_UPDATE_INTERVAL:
                try:
                    update_browser_tracking()
                    last_browser_update_time = now
                except Exception as e:
                    print(f"Browser tracking error: {e}")
                    # Continue without browser tracking if it fails

            # Track active window
            try:
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

                    # Update app usage
                    if app and app in open_apps:
                        open_apps[app]["last_used_time"] = now
                        open_apps[app]["alert_history"] = []
                        if app in alert_config.get("snooze_until", {}):
                            del alert_config["snooze_until"][app]
                            save_alert_config()

                    current_app, current_title = app, title
                    start_time = now
                    last_activity_time = now
            except Exception as e:
                print(f"[Active Window Error] {e}")

            # Performance control - ensure we don't exceed our target interval
            loop_duration = time.time() - loop_start_time
            sleep_time = max(
                1.0, MAIN_LOOP_INTERVAL - loop_duration
            )  # Minimum 1 second sleep

            if loop_duration > MAIN_LOOP_INTERVAL:
                print(
                    f"[Performance Warning] Loop took {loop_duration:.2f}s (target: {MAIN_LOOP_INTERVAL}s)"
                )

            time.sleep(sleep_time)
            loop_count += 1

    except KeyboardInterrupt:
        print("\n[Tracker] Stopping and saving log...")
        save_log()
    except Exception as e:
        print(f"[Tracker Error] {e}")
        import traceback

        traceback.print_exc()
        # Try to restart after error with longer delay
        print("[Tracker] Restarting in 15 seconds...")
        time.sleep(15)
        try:
            update_tracker()
        except Exception as restart_error:
            print(f"[Tracker] Failed to restart: {restart_error}")
            print("[Tracker] System may be unstable. Please restart manually.")


def run_dashboard():
    """Frontend GUI with improved session time display"""

    def update_ui():
        try:
            now = time.time()
            session_time = round(now - session_start_time, 2)

            # Update labels
            label_keystrokes.config(text=f"Keystrokes: {keystroke_count}")
            label_session.config(text=f"Session Time: {session_time:.0f} sec")
            label_open_apps.config(text=f"Open Apps: {len(open_apps)}")
            label_sessions.config(text=f"Sessions Tracked: {len(sessions)}")

            # Update status file much less frequently to reduce load
            if int(now) % 30 == 0:  # Only every 30 seconds
                update_status_file(session_time, keystroke_count)

            # Schedule next update (reduced frequency to prevent system overload)
            root.after(3000, update_ui)
        except Exception as e:
            print(f"[GUI Update Error] {e}")
            # Keep trying with reduced frequency to prevent system overload
            root.after(5000, update_ui)

    root = tk.Tk()
    root.title("Productivity Monitor - Optimized")
    root.geometry("400x300")

    # Add debug info
    debug_label = tk.Label(root, text="Debug Info", font=("Arial", 12, "bold"))
    debug_label.pack(pady=5)

    label_keystrokes = tk.Label(root, text="Keystrokes: 0", font=("Arial", 14))
    label_keystrokes.pack(pady=10)

    label_session = tk.Label(root, text="Session Time: 0 sec", font=("Arial", 14))
    label_session.pack(pady=10)

    label_open_apps = tk.Label(root, text="Open Apps: 0", font=("Arial", 14))
    label_open_apps.pack(pady=10)

    label_sessions = tk.Label(root, text="Sessions Tracked: 0", font=("Arial", 14))
    label_sessions.pack(pady=10)

    # Performance info
    perf_label = tk.Label(
        root, text=f"Updates every {MAIN_LOOP_INTERVAL}s", font=("Arial", 10)
    )
    perf_label.pack(pady=5)

    # Start UI updates
    update_ui()
    root.mainloop()


# Initialize everything
load_alert_config()
load_existing_sessions()
load_current_session_state()

# Run tracker and dashboard concurrently
if __name__ == "__main__":
    print("🔺 Starting SnapAlert Tracker...")

    # Register SnapAlert app ID with Windows automatically
    ensure_app_id_registered()

    print("[Tracker] Starting optimized productivity monitor...")
    print("[Tracker] Performance settings:")
    print(f"  - Main loop interval: {MAIN_LOOP_INTERVAL}s")
    print(f"  - Window enumeration: every {WINDOW_ENUM_INTERVAL}s")
    print(f"  - Resource checking: every {RESOURCE_CHECK_INTERVAL}s")
    print(f"  - Browser updates: every {BROWSER_UPDATE_INTERVAL}s")

    # Start input listeners
    if not start_input_listeners():
        print(
            "[Tracker] Warning: Input listeners failed to start. Keystroke tracking may not work."
        )

    # Start tracker thread
    tracker_thread = threading.Thread(target=update_tracker)
    tracker_thread.daemon = True
    tracker_thread.start()

    # Run GUI
    print("[Tracker] Running... Press Ctrl+C to stop.")
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
