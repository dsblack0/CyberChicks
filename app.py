from flask import Flask, render_template, jsonify
import json
import os
import time
from datetime import datetime

app = Flask(__name__)

# File paths
LOG_FILE = "data/logs.json"
STATUS_FILE = "data/status.json"
SESSIONS_FILE = "data/sessions.json"


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


if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5000)
