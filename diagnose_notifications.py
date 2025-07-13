#!/usr/bin/env python3
"""
SnapAlert Notification Diagnostic Tool
This script tests all notification methods and helps diagnose why notifications aren't appearing
"""

import subprocess
import sys
import time
import os


def test_powershell_basic():
    """Test basic PowerShell notification"""
    print("1. Testing Basic PowerShell Notification...")

    try:
        powershell_cmd = """
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show("Basic PowerShell test message", "SnapAlert Test")
        """

        result = subprocess.run(
            ["powershell.exe", "-Command", powershell_cmd],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode == 0:
            print("✅ Basic PowerShell works")
            return True
        else:
            print(f"❌ Basic PowerShell failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ PowerShell error: {e}")
        return False


def test_powershell_toast():
    """Test PowerShell toast notification"""
    print("\n2. Testing PowerShell Toast Notification...")

    try:
        # Simple toast notification
        powershell_cmd = """
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

        $template = @"
        <toast>
            <visual>
                <binding template="ToastGeneric">
                    <text>SnapAlert Diagnostic Test</text>
                    <text>If you see this, PowerShell toasts work!</text>
                </binding>
            </visual>
        </toast>
        "@

        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml($template)
        $toast = New-Object Windows.UI.Notifications.ToastNotification($xml)
        $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("SnapAlert.Diagnostic")
        $notifier.Show($toast)
        Write-Host "Toast notification sent"
        """

        result = subprocess.run(
            ["powershell.exe", "-Command", powershell_cmd],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode == 0:
            print("✅ PowerShell toast command executed")
            print("   Look for notification in bottom-right corner of screen")
            time.sleep(3)  # Give time for notification to appear
            return True
        else:
            print(f"❌ PowerShell toast failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ PowerShell toast error: {e}")
        return False


def test_win10toast_click():
    """Test win10toast_click"""
    print("\n3. Testing win10toast_click...")

    try:
        from win10toast_click import ToastNotifier

        notifier = ToastNotifier()
        notifier.show_toast(
            title="SnapAlert Diagnostic",
            msg="If you see this, win10toast_click works!",
            duration=5,
            threaded=True,
        )

        print("✅ win10toast_click notification sent")
        time.sleep(2)
        return True

    except ImportError:
        print("❌ win10toast_click not installed")
        return False
    except Exception as e:
        print(f"❌ win10toast_click error: {e}")
        return False


def test_plyer():
    """Test plyer notification"""
    print("\n4. Testing plyer...")

    try:
        from plyer import notification

        notification.notify(
            title="SnapAlert Diagnostic",
            message="If you see this, plyer works!",
            app_name="SnapAlert",
            timeout=5,
        )

        print("✅ plyer notification sent")
        time.sleep(2)
        return True

    except ImportError:
        print("❌ plyer not installed")
        return False
    except Exception as e:
        print(f"❌ plyer error: {e}")
        return False


def test_win10toast():
    """Test original win10toast"""
    print("\n5. Testing original win10toast...")

    try:
        from win10toast import ToastNotifier

        notifier = ToastNotifier()
        notifier.show_toast(
            title="SnapAlert Diagnostic",
            msg="If you see this, win10toast works!",
            duration=5,
            threaded=True,
        )

        print("✅ win10toast notification sent")
        time.sleep(2)
        return True

    except ImportError:
        print("❌ win10toast not installed")
        return False
    except Exception as e:
        print(f"❌ win10toast error: {e}")
        return False


def check_windows_settings():
    """Check Windows notification settings"""
    print("\n6. Checking Windows Notification Settings...")

    try:
        # Check if notifications are enabled
        powershell_cmd = """
        Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\PushNotifications" -Name "ToastEnabled" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ToastEnabled
        """

        result = subprocess.run(
            ["powershell.exe", "-Command", powershell_cmd],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0 and result.stdout.strip():
            toast_enabled = result.stdout.strip()
            if toast_enabled == "1":
                print("✅ Windows notifications are enabled")
            else:
                print("❌ Windows notifications are disabled in registry")
        else:
            print("⚠️ Could not check notification settings")

    except Exception as e:
        print(f"⚠️ Error checking settings: {e}")

    # Check Focus Assist
    try:
        powershell_cmd = """
        Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\CloudStore\Store\Cache\DefaultAccount" -ErrorAction SilentlyContinue
        """

        result = subprocess.run(
            ["powershell.exe", "-Command", powershell_cmd],
            capture_output=True,
            text=True,
            timeout=5,
        )

        print("ℹ️ Focus Assist might be blocking notifications")

    except Exception:
        pass


def show_manual_instructions():
    """Show manual troubleshooting instructions"""
    print("\n🔧 Manual Troubleshooting Steps:")
    print("=" * 50)

    print("\n1. Windows Notification Settings:")
    print("   • Press Win + I → System → Notifications & actions")
    print("   • Make sure 'Get notifications from apps and other senders' is ON")
    print("   • Scroll down and make sure notifications are allowed")

    print("\n2. Focus Assist Settings:")
    print("   • Press Win + I → System → Focus assist")
    print("   • Set to 'Off' or 'Priority only'")
    print("   • Check if you're in 'Do not disturb' mode")

    print("\n3. Action Center:")
    print("   • Click notification icon in system tray (bottom-right)")
    print("   • Check if notifications are appearing there")

    print("\n4. App-specific Settings:")
    print(
        "   • In Notifications & actions → scroll to 'Get notifications from these senders'"
    )
    print("   • Look for 'SnapAlert' or 'Python' and make sure it's enabled")

    print("\n5. Windows Version Check:")
    print("   • Toast notifications require Windows 10 version 1607 or later")
    print("   • Press Win + R → 'winver' to check your version")


def main():
    """Main diagnostic function"""

    print("🔺 SnapAlert Notification Diagnostic Tool")
    print("=" * 50)
    print("This tool will test different notification methods to find what works")
    print("Watch your screen for any notifications that appear!")
    print()

    input("Press Enter to start testing... ")

    # Test each method
    results = []

    results.append(("PowerShell Basic", test_powershell_basic()))
    results.append(("PowerShell Toast", test_powershell_toast()))
    results.append(("win10toast_click", test_win10toast_click()))
    results.append(("plyer", test_plyer()))
    results.append(("win10toast", test_win10toast()))

    # Check Windows settings
    check_windows_settings()

    # Show results
    print("\n📊 Test Results Summary:")
    print("=" * 50)

    working_methods = []
    for method, success in results:
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"{method:20} {status}")
        if success:
            working_methods.append(method)

    print(f"\nWorking methods: {len(working_methods)}")

    if not working_methods:
        print("\n❌ No notification methods are working!")
        print("This suggests a Windows configuration issue.")
        show_manual_instructions()
    elif "PowerShell Toast" in working_methods:
        print("\n✅ PowerShell Toast works - SnapAlert should work!")
        print("If you still don't see SnapAlert notifications, try:")
        print("1. Restart the Flask app")
        print("2. Clear browser cache")
        print("3. Check Windows notification permissions")
    else:
        print(f"\n⚠️ Alternative methods work: {', '.join(working_methods)}")
        print("SnapAlert will use these as fallbacks.")

    print("\n🎯 Next Steps:")
    if working_methods:
        print("1. Try the test buttons in your web interface again")
        print("2. If still no notifications, check Windows settings manually")
        print("3. Try running: python test_web_notifications.py")
    else:
        print("1. Follow the manual troubleshooting steps above")
        print("2. Restart Windows if necessary")
        print("3. Re-run this diagnostic after making changes")


if __name__ == "__main__":
    main()
