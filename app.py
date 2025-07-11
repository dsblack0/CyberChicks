from flask import Flask, render_template, jsonify, request
import json
import os
import time
from datetime import datetime

app = Flask(__name__)

# File paths
LOG_FILE = "data/logs.json"
STATUS_FILE = "data/status.json"
SESSIONS_FILE = "data/sessions.json"
ALERT_CONFIG_FILE = "data/alert_config.json"


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

    # Calculate total time from all sessions
    total_time = sum(session.get("duration_sec", 0) for session in sessions)

    # Get today's sessions
    today = datetime.now().date()
    today_sessions = [
        session
        for session in sessions
        if datetime.fromisoformat(session.get("start", "")).date() == today
    ]
    today_time = sum(session.get("duration_sec", 0) for session in today_sessions)

    return jsonify(
        {
            "current_session_time": status.get("session_time", 0),
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


if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5000)
