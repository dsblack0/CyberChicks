import sys
import json
import os
import subprocess
from win10toast_click import ToastNotifier

# File paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CUSTOM_ALERTS_FILE = os.path.join(PROJECT_ROOT, "data", "custom_alerts.json")
ICON_PATH_CANDIDATE = os.path.join(PROJECT_ROOT, "icons", "snapalert.ico")

# Use icon if it exists, otherwise None
ICON_PATH = ICON_PATH_CANDIDATE if os.path.exists(ICON_PATH_CANDIDATE) else None


def load_custom_alerts():
    """Load custom alerts from JSON file"""
    try:
        if os.path.exists(CUSTOM_ALERTS_FILE):
            with open(CUSTOM_ALERTS_FILE, "r") as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading custom alerts: {e}")
        return []


def show_alert_powershell(title, message):
    """Show Windows notification using PowerShell with proper SnapAlert branding"""
    try:
        # Escape quotes in the message
        escaped_title = title.replace('"', '""').replace("'", "''")
        escaped_message = message.replace('"', '""').replace("'", "''")

        # PowerShell command using Windows Toast notifications with custom app ID
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

# Create toast notification with SnapAlert as the app ID
$toast = New-Object Windows.UI.Notifications.ToastNotification($xml)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("SnapAlert")
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
            print(f"PowerShell notification sent successfully: {title}")
            return True
        else:
            print(f"PowerShell notification failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"PowerShell notification error: {e}")
        return False


def show_alert_fallback(title, message):
    """Fallback notification using win10toast_click"""
    try:
        toaster = ToastNotifier()

        toaster.show_toast(
            title=title,
            msg=message,
            icon_path=ICON_PATH,
            duration=10,
            threaded=True,
            callback_on_click=lambda: print(f"User clicked alert: {title}"),
        )

        print(f"Fallback notification sent: {title}")
        return True

    except Exception as e:
        print(f"Fallback notification error: {e}")
        return False


def show_alert(title, message):
    """Show Windows notification with SnapAlert branding"""
    try:
        # Add SnapAlert branding to title
        branded_title = f"🔺 SnapAlert: {title}"

        # Try PowerShell method first (supports custom app ID)
        if show_alert_powershell(branded_title, message):
            return True

        # Fallback to win10toast_click
        print("PowerShell method failed, trying fallback...")
        if show_alert_fallback(branded_title, message):
            return True

        # Final fallback using plyer
        try:
            from plyer import notification

            notification.notify(
                title=branded_title,
                message=message,
                app_name="SnapAlert",
                timeout=10,
            )
            print(f"Plyer notification sent: {branded_title}")
            return True
        except Exception as e:
            print(f"Plyer notification error: {e}")

        print("All notification methods failed")
        return False

    except Exception as e:
        print(f"Error showing alert: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python launcher.py <alert_id>")
        sys.exit(1)

    alert_id = sys.argv[1]

    # Load custom alerts
    custom_alerts = load_custom_alerts()

    # Find the alert by ID
    alert = None
    for custom_alert in custom_alerts:
        if custom_alert.get("id") == alert_id:
            alert = custom_alert
            break

    if not alert:
        print(f"Alert with ID '{alert_id}' not found")
        sys.exit(1)

    # Check if alert is enabled
    if not alert.get("enabled", True):
        print(f"Alert '{alert.get('name', 'Unknown')}' is disabled")
        sys.exit(1)

    # Get alert details
    alert_name = alert.get("name", "Custom Alert")
    alert_message = alert.get("message", "SnapAlert notification")

    # Replace placeholders in the message
    threshold = alert.get("threshold", 0)
    app_filter = alert.get("app_filter", "")

    # Simple placeholder replacement
    processed_message = alert_message.replace("{threshold}", str(threshold))
    processed_message = processed_message.replace(
        "{app}", app_filter or "your application"
    )

    # Show the alert
    if show_alert(alert_name, processed_message):
        print(f"Successfully triggered alert: {alert_name}")
    else:
        print(f"Failed to show alert: {alert_name}")
        sys.exit(1)


if __name__ == "__main__":
    main()
