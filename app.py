from flask import Flask, render_template, jsonify, request
import json
import os
import time
from datetime import datetime
import subprocess
import winreg
from pathlib import Path
from ai_analysis import get_scheduler, init_scheduler, start_scheduler, stop_scheduler

app = Flask(__name__)

# SnapAlert App ID for Windows notifications
SNAPALERT_APP_ID = "SnapAlert.ProductivityMonitor"

# File paths
LOG_FILE = "data/logs.json"
STATUS_FILE = "data/status.json"
SESSIONS_FILE = "data/sessions.json"
ALERT_CONFIG_FILE = "data/alert_config.json"
CUSTOM_ALERTS_FILE = "data/custom_alerts.json"
AI_ANALYSIS_CONFIG_FILE = "data/ai_analysis_config.json"
INSIGHTS_FILE = "data/insights.json"


def ensure_app_id_registered():
    """Automatically register SnapAlert app ID with Windows on startup"""
    try:
        # Check if already registered
        key_path = f"SOFTWARE\\Classes\\AppUserModelId\\{SNAPALERT_APP_ID}"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path):
                print("[App Registration] SnapAlert app ID already registered")
                return True
        except FileNotFoundError:
            pass  # Not registered yet

        print("[App Registration] Registering SnapAlert app ID...")

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
                print(f"[App Registration] Icon registered: {icon_path}")

            winreg.SetValueEx(key, "ShowInSettings", 0, winreg.REG_DWORD, 1)

        print("[App Registration] ✅ SnapAlert app ID registered successfully")
        return True

    except Exception as e:
        print(f"[App Registration] ⚠️ Registration failed: {e}")
        return False


def read_status():
    """Read current status from status.json"""
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r") as f:
                return json.load(f)
        return {
            "session_time": 0,
            "keystrokes": 0,
            "last_updated": datetime.now().isoformat(),
            "open_apps": [],
            "sessions": [],
        }
    except Exception as e:
        print(f"Error reading status: {e}")
        return {
            "session_time": 0,
            "keystrokes": 0,
            "last_updated": datetime.now().isoformat(),
            "open_apps": [],
            "sessions": [],
        }


def read_sessions():
    """Read all sessions from sessions.json"""
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, "r") as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error reading sessions: {e}")
        return []


def read_recent_logs(n=10):
    """Read recent log entries"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
            logs = [json.loads(line.strip()) for line in lines[-n:] if line.strip()]
            return logs
        return []
    except Exception as e:
        print(f"Error reading logs: {e}")
        return []


@app.route("/")
def dashboard():
    """Main dashboard page"""
    return render_template("index.html")


@app.route("/api/stats")
def get_stats():
    """API endpoint for current stats"""
    status = read_status()
    sessions = read_sessions()
    recent_logs = read_recent_logs(5)

    # Get current session time
    current_session_time = status.get("session_time", 0)

    # Calculate total time from all completed sessions + current session
    completed_sessions_time = sum(
        session.get("duration_sec", 0) for session in sessions
    )
    total_time = completed_sessions_time + current_session_time

    # Get today's sessions
    today = datetime.now().date()
    today_sessions = [
        session
        for session in sessions
        if datetime.fromisoformat(session.get("start", "")).date() == today
    ]
    today_completed_time = sum(
        session.get("duration_sec", 0) for session in today_sessions
    )
    today_time = today_completed_time + current_session_time

    # Debug logging
    print(
        f"[API Debug] Current session: {current_session_time}s, "
        f"Completed sessions: {completed_sessions_time}s, "
        f"Total: {total_time}s, Today: {today_time}s"
    )

    return jsonify(
        {
            "current_session_time": current_session_time,
            "session_start_time": status.get(
                "session_start_time", datetime.now().isoformat()
            ),
            "keystrokes": status.get("keystrokes", 0),
            "open_apps": status.get("open_apps", []),
            "open_apps_details": status.get("open_apps_details", {}),
            "current_app": status.get("current_app", ""),
            "total_sessions": len(sessions),
            "total_time": total_time,
            "today_sessions": len(today_sessions),
            "today_time": today_time,
            "recent_logs": recent_logs,
            "last_updated": status.get("last_updated", ""),
            "sessions": sessions[-10:],  # Last 10 sessions
            "browser_data": status.get("browser_data", {}),
            "alert_config": status.get("alert_config", {}),
            "custom_alerts": read_custom_alerts(),
            "ai_insights": read_insights()[-10:],  # Last 10 insights
            "ai_analysis_config": read_ai_analysis_config(),
        }
    )


@app.route("/api/sessions")
def get_sessions():
    """API endpoint for all sessions"""
    sessions = read_sessions()
    return jsonify(sessions)


@app.route("/api/logs")
def get_logs():
    """API endpoint for recent logs"""
    logs = read_recent_logs(20)
    return jsonify(logs)


def read_alert_config():
    """Read alert configuration"""
    try:
        if os.path.exists(ALERT_CONFIG_FILE):
            with open(ALERT_CONFIG_FILE, "r") as f:
                return json.load(f)
        return {
            "enabled": True,
            "whitelist": [],
            "snooze_until": {},
            "alert_levels_enabled": [True, True, True],
            "show_resource_usage": True,
            "smart_filtering": True,
            "break_reminders_enabled": True,
            "break_reminder_interval": 180,  # 3 minutes in seconds
        }
    except Exception as e:
        print(f"Error reading alert config: {e}")
        return {}


def save_alert_config(config):
    """Save alert configuration"""
    try:
        with open(ALERT_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving alert config: {e}")
        return False


def read_custom_alerts():
    """Read custom alerts from file"""
    try:
        if os.path.exists(CUSTOM_ALERTS_FILE):
            with open(CUSTOM_ALERTS_FILE, "r") as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error reading custom alerts: {e}")
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


def read_ai_analysis_config():
    """Read AI analysis configuration"""
    try:
        if os.path.exists(AI_ANALYSIS_CONFIG_FILE):
            with open(AI_ANALYSIS_CONFIG_FILE, "r") as f:
                return json.load(f)
        return {
            "enabled": True,
            "analysis_interval_minutes": 20,
            "ollama_url": "http://localhost:11434",
            "model_name": "mistral",
            "data_dir": "data",
        }
    except Exception as e:
        print(f"Error reading AI analysis config: {e}")
        return {}


def save_ai_analysis_config(config):
    """Save AI analysis configuration"""
    try:
        with open(AI_ANALYSIS_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving AI analysis config: {e}")
        return False


def read_insights():
    """Read AI insights from file"""
    try:
        if os.path.exists(INSIGHTS_FILE):
            with open(INSIGHTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error reading insights: {e}")
        return []


@app.route("/api/alerts/config")
def get_alert_config():
    """API endpoint for alert configuration"""
    config = read_alert_config()
    return jsonify(config)


@app.route("/api/alerts/config", methods=["POST"])
def update_alert_config():
    """API endpoint to update alert configuration"""
    try:
        config = request.get_json()
        if save_alert_config(config):
            return jsonify({"success": True, "message": "Alert configuration updated"})
        else:
            return jsonify(
                {"success": False, "message": "Failed to save configuration"}
            ), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/api/alerts/snooze", methods=["POST"])
def snooze_app():
    """API endpoint to snooze alerts for a specific app"""
    try:
        data = request.get_json()
        app_name = data.get("app_name")
        minutes = data.get("minutes", 30)

        if not app_name:
            return jsonify({"success": False, "message": "App name is required"}), 400

        config = read_alert_config()
        snooze_until = time.time() + (minutes * 60)
        config["snooze_until"][app_name] = snooze_until

        if save_alert_config(config):
            return jsonify(
                {
                    "success": True,
                    "message": f"Snoozed alerts for {app_name} for {minutes} minutes",
                }
            )
        else:
            return jsonify(
                {"success": False, "message": "Failed to save configuration"}
            ), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/api/alerts/whitelist", methods=["POST"])
def manage_whitelist():
    """API endpoint to add/remove apps from whitelist"""
    try:
        data = request.get_json()
        app_name = data.get("app_name")
        action = data.get("action", "add")  # "add" or "remove"

        if not app_name:
            return jsonify({"success": False, "message": "App name is required"}), 400

        config = read_alert_config()
        whitelist = config.get("whitelist", [])

        if action == "add" and app_name not in whitelist:
            whitelist.append(app_name)
            message = f"Added {app_name} to whitelist"
        elif action == "remove" and app_name in whitelist:
            whitelist.remove(app_name)
            message = f"Removed {app_name} from whitelist"
        else:
            return jsonify({"success": False, "message": "No changes made"}), 400

        config["whitelist"] = whitelist

        if save_alert_config(config):
            return jsonify({"success": True, "message": message})
        else:
            return jsonify(
                {"success": False, "message": "Failed to save configuration"}
            ), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/api/alerts/break-reminder", methods=["POST"])
def update_break_reminder():
    """API endpoint to update break reminder settings"""
    try:
        data = request.get_json()
        enabled = data.get("enabled", True)
        interval = data.get("interval", 180)

        # Validate interval (minimum 1 minute, maximum 60 minutes)
        if interval < 60 or interval > 3600:
            return jsonify(
                {
                    "success": False,
                    "message": "Interval must be between 1 and 60 minutes",
                }
            ), 400

        config = read_alert_config()
        config["break_reminders_enabled"] = enabled
        config["break_reminder_interval"] = interval

        if save_alert_config(config):
            return jsonify(
                {
                    "success": True,
                    "message": f"Break reminders {'enabled' if enabled else 'disabled'} with {interval // 60} minute interval",
                }
            )
        else:
            return jsonify(
                {"success": False, "message": "Failed to save configuration"}
            ), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/api/custom-alerts")
def get_custom_alerts():
    """API endpoint to get all custom alerts"""
    alerts = read_custom_alerts()
    return jsonify({"alerts": alerts})


@app.route("/api/custom-alerts", methods=["POST"])
def create_custom_alert():
    """API endpoint to create a new custom alert"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["name", "type", "condition", "threshold", "message"]
        for field in required_fields:
            if field not in data:
                return jsonify(
                    {"success": False, "message": f"Missing required field: {field}"}
                ), 400

        # Create new alert with ID
        new_alert = {
            "id": str(int(time.time() * 1000)),  # Use timestamp as ID
            "name": data["name"],
            "type": data[
                "type"
            ],  # "session_time", "app_time", "keystroke_count", "break_reminder"
            "condition": data["condition"],  # "greater_than", "less_than", "equal_to"
            "threshold": data["threshold"],  # numeric value
            "message": data["message"],
            "enabled": data.get("enabled", True),
            "app_filter": data.get("app_filter", ""),  # Optional app name filter
            "created_at": datetime.now().isoformat(),
            "last_triggered": None,
            "trigger_count": 0,
        }

        # Load existing alerts and add new one
        alerts = read_custom_alerts()
        alerts.append(new_alert)

        if save_custom_alerts(alerts):
            return jsonify(
                {"success": True, "message": "Custom alert created", "alert": new_alert}
            )
        else:
            return jsonify({"success": False, "message": "Failed to save alert"}), 500

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/api/custom-alerts/<alert_id>", methods=["PUT"])
def update_custom_alert(alert_id):
    """API endpoint to update a custom alert"""
    try:
        data = request.get_json()
        alerts = read_custom_alerts()

        # Find the alert to update
        alert_index = None
        for i, alert in enumerate(alerts):
            if alert["id"] == alert_id:
                alert_index = i
                break

        if alert_index is None:
            return jsonify({"success": False, "message": "Alert not found"}), 404

        # Update the alert
        updatable_fields = [
            "name",
            "type",
            "condition",
            "threshold",
            "message",
            "enabled",
            "app_filter",
        ]
        for field in updatable_fields:
            if field in data:
                alerts[alert_index][field] = data[field]

        if save_custom_alerts(alerts):
            return jsonify(
                {
                    "success": True,
                    "message": "Custom alert updated",
                    "alert": alerts[alert_index],
                }
            )
        else:
            return jsonify({"success": False, "message": "Failed to save alert"}), 500

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/api/custom-alerts/<alert_id>", methods=["DELETE"])
def delete_custom_alert(alert_id):
    """API endpoint to delete a custom alert"""
    try:
        alerts = read_custom_alerts()

        # Find and remove the alert
        original_count = len(alerts)
        alerts = [alert for alert in alerts if alert["id"] != alert_id]

        if len(alerts) == original_count:
            return jsonify({"success": False, "message": "Alert not found"}), 404

        if save_custom_alerts(alerts):
            return jsonify({"success": True, "message": "Custom alert deleted"})
        else:
            return jsonify({"success": False, "message": "Failed to save alerts"}), 500

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/api/custom-alerts/<alert_id>/toggle", methods=["POST"])
def toggle_custom_alert(alert_id):
    """API endpoint to toggle a custom alert on/off"""
    try:
        alerts = read_custom_alerts()

        # Find the alert to toggle
        alert_index = None
        for i, alert in enumerate(alerts):
            if alert["id"] == alert_id:
                alert_index = i
                break

        if alert_index is None:
            return jsonify({"success": False, "message": "Alert not found"}), 404

        # Toggle the alert
        alerts[alert_index]["enabled"] = not alerts[alert_index]["enabled"]

        if save_custom_alerts(alerts):
            status = "enabled" if alerts[alert_index]["enabled"] else "disabled"
            return jsonify(
                {
                    "success": True,
                    "message": f"Alert {status}",
                    "alert": alerts[alert_index],
                }
            )
        else:
            return jsonify({"success": False, "message": "Failed to save alert"}), 500

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


def show_notification_powershell(title, message, duration=8):
    """Show Windows notification using PowerShell with proper SnapAlert branding"""
    try:
        import subprocess

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
            print(f"[Notification] PowerShell notification sent successfully: {title}")
            return True
        else:
            print(f"[Notification] PowerShell failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"[Notification] PowerShell notification error: {e}")
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

        print(f"[Notification] win10toast_click notification sent: {title}")
        return True

    except Exception as e:
        print(f"[Notification] win10toast_click error: {e}")
        return False


def show_windows_notification(title, message, duration=8):
    """Improved Windows notification function with multiple fallback methods"""
    try:
        print(f"[Notification] Attempting to show: {title}")

        # Add SnapAlert branding to title if not already present
        if not title.startswith("🔺 SnapAlert"):
            branded_title = f"🔺 SnapAlert: {title}"
        else:
            branded_title = title

        # Method 1: Try win10toast_click first (we know this works for you)
        if show_notification_fallback(branded_title, message, duration):
            return True

        # Method 2: Try PowerShell method as backup (currently failing for you)
        print("[Notification] win10toast_click failed, trying PowerShell...")
        if show_notification_powershell(branded_title, message, duration):
            return True

        # Method 3: Try plyer as fallback
        print("[Notification] win10toast_click failed, trying plyer...")
        try:
            from plyer import notification

            notification.notify(
                title=branded_title,
                message=message,
                app_name="SnapAlert",
                timeout=duration,
            )
            print(f"[Notification] Plyer notification sent successfully")
            return True
        except Exception as e:
            print(f"[Notification] Plyer notification failed: {e}")

        # Method 4: Try original win10toast as final fallback
        print("[Notification] Trying original win10toast as final fallback...")
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
            print(f"[Notification] win10toast notification sent successfully")
            return True
        except Exception as e:
            print(f"[Notification] win10toast failed: {e}")

        # If all methods fail, at least log it
        print(
            f"[Notification] All notification methods failed. Title: {branded_title}, Message: {message}"
        )
        return False

    except Exception as e:
        print(f"[Notification] System error: {e}")
        return False


@app.route("/api/custom-alerts/<alert_id>/test", methods=["POST"])
def test_custom_alert(alert_id):
    """API endpoint to test a custom alert by triggering it immediately"""
    try:
        alerts = read_custom_alerts()

        # Find the alert to test
        alert = None
        for a in alerts:
            if a["id"] == alert_id:
                alert = a
                break

        if alert is None:
            return jsonify({"success": False, "message": "Alert not found"}), 404

        # Format the test message
        test_message = alert["message"]

        # Replace placeholders with test values
        test_values = {
            "threshold": str(alert["threshold"]),
            "app": alert.get("app_filter", "TestApp.exe") or "TestApp.exe",
        }

        for placeholder, value in test_values.items():
            test_message = test_message.replace(f"{{{placeholder}}}", value)

        # Show the notification with SnapAlert branding
        success = show_windows_notification(
            title=f"Test: {alert['name']}",
            message=test_message,
            duration=8,
        )

        if success:
            return jsonify(
                {
                    "success": True,
                    "message": f"Test notification sent for '{alert['name']}'",
                    "test_message": test_message,
                }
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "message": "Failed to send notification. Check console for details.",
                }
            ), 500

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/api/test-basic-alerts", methods=["POST"])
def test_basic_alerts():
    """API endpoint to test basic alert system"""
    try:
        alert_type = request.get_json().get("type", "break_reminder")

        success = False

        if alert_type == "break_reminder":
            success = show_windows_notification(
                title="Break Reminder",
                message="💪 Break Time!\nHey! This is a test break reminder.\n• Stand up and stretch\n• Look away from the screen\n• Take a deep breath",
                duration=10,
            )
        elif alert_type == "idle_app":
            success = show_windows_notification(
                title="Idle App Alert",
                message="💡 TestApp.exe has been idle for 5 minutes.\nConsider closing it to save resources.",
                duration=8,
            )
        elif alert_type == "session_end":
            success = show_windows_notification(
                title="Session End",
                message="Session ended after 10 minutes of inactivity.\nSession recorded (25.5 min). Total sessions: 5",
                duration=5,
            )

        if success:
            return jsonify(
                {"success": True, "message": f"Test {alert_type} notification sent"}
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "message": "Failed to send notification. Check console for details.",
                }
            ), 500

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


# AI Analysis API Endpoints
@app.route("/api/ai-analysis/config")
def get_ai_analysis_config():
    """Get AI analysis configuration"""
    try:
        config = read_ai_analysis_config()
        scheduler = get_scheduler()
        status = scheduler.get_status()

        return jsonify({"success": True, "config": config, "status": status})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/api/ai-analysis/config", methods=["POST"])
def update_ai_analysis_config():
    """Update AI analysis configuration"""
    try:
        data = request.get_json()

        # Validate required fields
        if "analysis_interval_minutes" in data:
            if (
                not isinstance(data["analysis_interval_minutes"], int)
                or data["analysis_interval_minutes"] < 1
            ):
                return jsonify({"success": False, "message": "Invalid interval"}), 400

        # Save configuration
        if save_ai_analysis_config(data):
            # Update scheduler with new config
            scheduler = get_scheduler()
            scheduler.update_config(data)

            return jsonify(
                {"success": True, "message": "AI analysis configuration updated"}
            )
        else:
            return jsonify(
                {"success": False, "message": "Failed to save configuration"}
            ), 500

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/api/ai-analysis/start", methods=["POST"])
def start_ai_analysis():
    """Start AI analysis scheduler"""
    try:
        scheduler = get_scheduler()
        if scheduler.start():
            return jsonify(
                {"success": True, "message": "AI analysis scheduler started"}
            )
        else:
            return jsonify(
                {"success": False, "message": "Failed to start scheduler"}
            ), 500

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/api/ai-analysis/stop", methods=["POST"])
def stop_ai_analysis():
    """Stop AI analysis scheduler"""
    try:
        scheduler = get_scheduler()
        if scheduler.stop():
            return jsonify(
                {"success": True, "message": "AI analysis scheduler stopped"}
            )
        else:
            return jsonify(
                {"success": False, "message": "Failed to stop scheduler"}
            ), 500

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/api/ai-analysis/run-now", methods=["POST"])
def run_ai_analysis_now():
    """Run AI analysis immediately"""
    try:
        scheduler = get_scheduler()
        result = scheduler.run_analysis_now()

        if result:
            return jsonify(
                {
                    "success": True,
                    "message": "Analysis completed successfully",
                    "result": result,
                }
            )
        else:
            return jsonify({"success": False, "message": "Analysis failed"}), 500

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/api/ai-analysis/test-ollama", methods=["POST"])
def test_ollama_connection():
    """Test Ollama connection"""
    try:
        scheduler = get_scheduler()
        is_connected = scheduler.test_ollama_connection()

        return jsonify(
            {
                "success": True,
                "connected": is_connected,
                "message": "Ollama is accessible"
                if is_connected
                else "Ollama is not accessible",
            }
        )

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/api/ai-analysis/insights")
def get_ai_insights():
    """Get AI insights"""
    try:
        insights = read_insights()

        return jsonify(
            {"success": True, "insights": insights, "total_count": len(insights)}
        )

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@app.route("/api/ai-analysis/insights/<int:limit>")
def get_ai_insights_limited(limit):
    """Get limited number of recent AI insights"""
    try:
        insights = read_insights()
        limited_insights = insights[-limit:] if limit > 0 else insights

        return jsonify(
            {
                "success": True,
                "insights": limited_insights,
                "total_count": len(insights),
                "returned_count": len(limited_insights),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Register SnapAlert app ID with Windows automatically
    print("🔺 Starting SnapAlert...")
    ensure_app_id_registered()

    # Initialize AI analysis scheduler
    try:
        print("🤖 Initializing AI analysis scheduler...")
        config = read_ai_analysis_config()
        scheduler = init_scheduler(config)

        if config.get("enabled", True):
            if scheduler.start():
                print("✅ AI analysis scheduler started successfully")
            else:
                print("⚠️ Failed to start AI analysis scheduler")
        else:
            print("⏸️ AI analysis scheduler is disabled")

    except Exception as e:
        print(f"❌ Error initializing AI analysis: {e}")

    app.run(debug=True, host="0.0.0.0", port=5000)
