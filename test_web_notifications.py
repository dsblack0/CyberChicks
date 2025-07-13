#!/usr/bin/env python3
"""
Test script for web interface notification buttons
This verifies that the test buttons in the web interface work correctly with win10toast_click
"""

import requests
import json
import time
import sys


BASE_URL = "http://localhost:5000"


def test_basic_alerts():
    """Test the basic alert test buttons"""

    print("🧪 Testing Basic Alert Buttons")
    print("=" * 50)

    basic_alerts = [
        {"type": "break_reminder", "name": "Break Reminder"},
        {"type": "idle_app", "name": "Idle App Alert"},
        {"type": "session_end", "name": "Session End"},
    ]

    for alert in basic_alerts:
        print(f"\n📧 Testing {alert['name']}...")

        try:
            response = requests.post(
                f"{BASE_URL}/api/test-basic-alerts",
                json={"type": alert["type"]},
                timeout=10,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ SUCCESS: {alert['name']} notification sent")
                    print(f"Message: {result.get('message', 'No message')}")
                else:
                    print(f"❌ FAILED: {result.get('message', 'Unknown error')}")
            else:
                print(f"❌ HTTP ERROR: {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"⚠️ TIMEOUT: {alert['name']} (this might be normal)")
        except requests.exceptions.ConnectionError:
            print(f"❌ CONNECTION ERROR: Make sure Flask app is running on {BASE_URL}")
            return False
        except Exception as e:
            print(f"❌ ERROR: {e}")

        # Wait between tests
        time.sleep(2)

    return True


def test_custom_alerts():
    """Test custom alert test buttons"""

    print("\n🔔 Testing Custom Alert Buttons")
    print("=" * 50)

    try:
        # Get custom alerts
        response = requests.get(f"{BASE_URL}/api/custom-alerts", timeout=10)

        if response.status_code != 200:
            print(f"❌ Failed to get custom alerts: {response.status_code}")
            return False

        alerts_data = response.json()
        custom_alerts = alerts_data.get("alerts", [])

        if not custom_alerts:
            print("⚠️ No custom alerts found. Create some in the web interface first.")
            return True

        print(f"Found {len(custom_alerts)} custom alerts")

        # Test first 3 custom alerts
        for alert in custom_alerts[:3]:
            alert_id = alert.get("id")
            alert_name = alert.get("name", "Unknown")
            enabled = alert.get("enabled", False)

            print(
                f"\n📧 Testing '{alert_name}' (ID: {alert_id}, Enabled: {enabled})..."
            )

            try:
                response = requests.post(
                    f"{BASE_URL}/api/custom-alerts/{alert_id}/test", timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        print(f"✅ SUCCESS: {alert_name} notification sent")
                        print(f"Message: {result.get('message', 'No message')}")
                        print(
                            f"Test text: {result.get('test_message', 'No test message')}"
                        )
                    else:
                        print(f"❌ FAILED: {result.get('message', 'Unknown error')}")
                else:
                    print(f"❌ HTTP ERROR: {response.status_code}")

            except requests.exceptions.Timeout:
                print(f"⚠️ TIMEOUT: {alert_name} (this might be normal)")
            except Exception as e:
                print(f"❌ ERROR: {e}")

            # Wait between tests
            time.sleep(2)

    except Exception as e:
        print(f"❌ ERROR getting custom alerts: {e}")
        return False

    return True


def check_flask_app():
    """Check if Flask app is running"""

    print("🔍 Checking Flask App Status")
    print("=" * 50)

    try:
        response = requests.get(f"{BASE_URL}/api/stats", timeout=5)

        if response.status_code == 200:
            print("✅ Flask app is running and responding")
            return True
        else:
            print(f"❌ Flask app returned {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"❌ Flask app is not running on {BASE_URL}")
        print("Please start it with: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error checking Flask app: {e}")
        return False


def main():
    """Main test function"""

    print("🔺 SnapAlert Web Interface Test Suite")
    print("=" * 50)

    # Check if Flask app is running
    if not check_flask_app():
        print("\n❌ Cannot proceed without Flask app running")
        sys.exit(1)

    print("\n🎯 Testing Web Interface Notification Buttons")
    print("These should show Windows notifications with '🔺 SnapAlert:' branding")
    print("Check your notification area for the test notifications!")
    print()

    # Test basic alerts
    basic_success = test_basic_alerts()

    # Test custom alerts
    custom_success = test_custom_alerts()

    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    print(f"Basic Alerts: {'✅ Tested' if basic_success else '❌ Failed'}")
    print(f"Custom Alerts: {'✅ Tested' if custom_success else '❌ Failed'}")

    print("\n🎯 What to Check:")
    print("1. Windows notifications should appear in notification area")
    print("2. Notifications should show '🔺 SnapAlert:' in the title")
    print("3. Source should show as 'SnapAlert' (not 'Python' or 'PowerShell')")
    print("4. Test buttons in web interface should work without errors")

    print("\n🔧 If notifications don't appear:")
    print("- Check Windows notification settings")
    print("- Ensure win10toast_click is installed: pip install win10toast_click")
    print("- Check console output for error messages")

    print("\n✅ Test completed!")


if __name__ == "__main__":
    main()
