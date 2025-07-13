#!/usr/bin/env python3
"""
Test script for the SnapAlert launcher system
This script tests the launcher.py functionality with custom alerts
"""

import os
import json
import sys
import subprocess
from datetime import datetime


def create_test_alerts():
    """Create sample custom alerts for testing"""

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    test_alerts = [
        {
            "id": "test_water_reminder",
            "name": "Drink Water",
            "type": "session_time",
            "condition": "greater_than",
            "threshold": 30,
            "message": "💧 Time to drink water! You've been working for {threshold} minutes.",
            "enabled": True,
            "app_filter": "",
            "created_at": datetime.now().isoformat(),
            "last_triggered": None,
            "trigger_count": 0,
        },
        {
            "id": "test_stretch_reminder",
            "name": "Stretch Break",
            "type": "session_time",
            "condition": "greater_than",
            "threshold": 45,
            "message": "🧘 Time to stretch! Stand up and take a 30-second break.",
            "enabled": True,
            "app_filter": "",
            "created_at": datetime.now().isoformat(),
            "last_triggered": None,
            "trigger_count": 0,
        },
        {
            "id": "test_focus_reminder",
            "name": "Focus Time",
            "type": "keystroke_count",
            "condition": "greater_than",
            "threshold": 1000,
            "message": "🧠 You've typed {threshold} keystrokes! Time to focus deeply.",
            "enabled": True,
            "app_filter": "",
            "created_at": datetime.now().isoformat(),
            "last_triggered": None,
            "trigger_count": 0,
        },
        {
            "id": "test_disabled_alert",
            "name": "Disabled Alert",
            "type": "session_time",
            "condition": "greater_than",
            "threshold": 60,
            "message": "This alert is disabled and should not show up.",
            "enabled": False,
            "app_filter": "",
            "created_at": datetime.now().isoformat(),
            "last_triggered": None,
            "trigger_count": 0,
        },
    ]

    # Write test alerts to file
    with open("data/custom_alerts.json", "w") as f:
        json.dump(test_alerts, f, indent=2)

    print("✅ Created test custom alerts in data/custom_alerts.json")
    return test_alerts


def test_launcher_functionality():
    """Test the launcher with different alert IDs"""

    print("\n🧪 Testing Launcher Functionality")
    print("=" * 50)

    # Test valid alert ID
    print("\n1. Testing valid alert ID (test_water_reminder):")
    try:
        result = subprocess.run(
            [sys.executable, "alerts/launcher.py", "test_water_reminder"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print("✅ SUCCESS: Alert launched successfully")
            print(f"Output: {result.stdout}")
        else:
            print("❌ ERROR: Alert failed to launch")
            print(f"Error: {result.stderr}")

    except subprocess.TimeoutExpired:
        print("⚠️ WARNING: Alert launched but timed out (this is normal)")
    except Exception as e:
        print(f"❌ ERROR: Exception occurred: {e}")

    # Test invalid alert ID
    print("\n2. Testing invalid alert ID (nonexistent):")
    try:
        result = subprocess.run(
            [sys.executable, "alerts/launcher.py", "nonexistent"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            print("✅ SUCCESS: Correctly handled invalid alert ID")
            print(f"Output: {result.stdout}")
        else:
            print("❌ ERROR: Should have failed with invalid alert ID")

    except Exception as e:
        print(f"❌ ERROR: Exception occurred: {e}")

    # Test disabled alert
    print("\n3. Testing disabled alert (test_disabled_alert):")
    try:
        result = subprocess.run(
            [sys.executable, "alerts/launcher.py", "test_disabled_alert"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            print("✅ SUCCESS: Correctly handled disabled alert")
            print(f"Output: {result.stdout}")
        else:
            print("❌ ERROR: Should have failed with disabled alert")

    except Exception as e:
        print(f"❌ ERROR: Exception occurred: {e}")


def test_powershell_script():
    """Test the PowerShell script (if possible)"""

    print("\n🔧 Testing PowerShell Script")
    print("=" * 50)

    try:
        # Test PowerShell script (dry run)
        result = subprocess.run(
            [
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Write-Host 'PowerShell is available and can execute scripts'",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print("✅ SUCCESS: PowerShell is available")
            print("You can run 'register.ps1' to create shortcuts")
        else:
            print("❌ ERROR: PowerShell not available or restricted")
            print(f"Error: {result.stderr}")

    except Exception as e:
        print(f"❌ ERROR: Exception testing PowerShell: {e}")


def main():
    """Main test function"""

    print("🔺 SnapAlert Launcher Test Suite")
    print("=" * 50)

    # Create test alerts
    test_alerts = create_test_alerts()

    # Test launcher functionality
    test_launcher_functionality()

    # Test PowerShell availability
    test_powershell_script()

    print("\n📊 Test Summary")
    print("=" * 50)
    print(f"Created {len(test_alerts)} test alerts")
    print(f"Enabled alerts: {len([a for a in test_alerts if a['enabled']])}")
    print(f"Disabled alerts: {len([a for a in test_alerts if not a['enabled']])}")

    print("\n🎯 Next Steps:")
    print("1. Run your web interface to see the test alerts")
    print("2. Create more custom alerts in the web interface")
    print("3. Run 'register.ps1' to create Windows shortcuts")
    print("4. Test the shortcuts from Start Menu")

    print("\n✅ Test completed!")


if __name__ == "__main__":
    main()
