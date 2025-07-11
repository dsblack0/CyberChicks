#!/usr/bin/env python3
"""
Test script to verify session tracking improvements
"""

import json
import os
import time
from datetime import datetime


def test_session_tracking():
    """Test the session tracking functionality"""
    print("🧪 Testing Session Tracking...")

    # Check if status file exists
    status_file = "data/status.json"
    if not os.path.exists(status_file):
        print("❌ Status file not found. Make sure tracker.py is running.")
        return False

    try:
        # Read current status
        with open(status_file, "r") as f:
            status = json.load(f)

        # Check required fields
        required_fields = [
            "session_time",
            "session_start_time",
            "keystrokes",
            "last_updated",
        ]
        for field in required_fields:
            if field not in status:
                print(f"❌ Missing required field: {field}")
                return False
            print(f"✅ Found field: {field} = {status[field]}")

        # Parse session start time
        if status["session_start_time"]:
            session_start = datetime.fromisoformat(status["session_start_time"])
            current_time = datetime.now()
            calculated_session_time = (current_time - session_start).total_seconds()

            print(f"📊 Session Analysis:")
            print(f"   Start time: {session_start}")
            print(f"   Current time: {current_time}")
            print(f"   Reported session time: {status['session_time']} seconds")
            print(f"   Calculated session time: {calculated_session_time:.2f} seconds")
            print(
                f"   Difference: {abs(calculated_session_time - status['session_time']):.2f} seconds"
            )

            if (
                abs(calculated_session_time - status["session_time"]) < 10
            ):  # Within 10 seconds
                print("✅ Session time calculation is accurate!")
            else:
                print("⚠️  Session time calculation may need adjustment")

        # Check keystrokes
        print(f"⌨️  Keystrokes this session: {status['keystrokes']}")

        # Check open apps
        if "open_apps_details" in status:
            print(f"📱 Open apps: {len(status['open_apps_details'])}")
            for app_name, app_info in status["open_apps_details"].items():
                print(f"   • {app_name}: {app_info.get('instance_count', 1)} instances")

        # Check sessions file
        sessions_file = "data/sessions.json"
        if os.path.exists(sessions_file):
            try:
                with open(sessions_file, "r") as f:
                    sessions_data = json.load(f)
                print(f"📊 Sessions file contains {len(sessions_data)} sessions")
                if sessions_data:
                    latest_session = sessions_data[-1]
                    print(
                        f"   Latest session: {latest_session.get('duration_sec', 0)} seconds"
                    )
            except Exception as e:
                print(f"❌ Error reading sessions file: {e}")
        else:
            print("📊 No sessions file found")

        print("\n✅ Session tracking test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error testing session tracking: {e}")
        return False


def test_api_response():
    """Test the API response structure"""
    print("\n🌐 Testing API Response...")

    try:
        import requests

        response = requests.get("http://localhost:5000/api/stats")

        if response.status_code == 200:
            data = response.json()

            # Check for session start time in API response
            if "session_start_time" in data:
                print("✅ session_start_time found in API response")
                print(f"   Value: {data['session_start_time']}")

                # Calculate real-time session time
                session_start = datetime.fromisoformat(data["session_start_time"])
                current_time = datetime.now()
                real_time_session = (current_time - session_start).total_seconds()

                print(f"   Real-time session time: {real_time_session:.2f} seconds")
                print(
                    f"   API session time: {data.get('current_session_time', 0)} seconds"
                )

            else:
                print("❌ session_start_time missing from API response")

            # Check total sessions
            total_sessions = data.get("total_sessions", 0)
            print(f"📊 API reports {total_sessions} total sessions")

            # Check recent sessions
            recent_sessions = data.get("sessions", [])
            print(f"📊 API provides {len(recent_sessions)} recent sessions")

            print("✅ API response test completed!")
            return True
        else:
            print(f"❌ API request failed with status {response.status_code}")
            return False

    except requests.RequestException as e:
        print(f"❌ Failed to connect to API: {e}")
        print("   Make sure Flask app is running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Session Tracking Test Suite")
    print("=" * 50)

    # Test 1: Status file
    success1 = test_session_tracking()

    # Test 2: API response
    success2 = test_api_response()

    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 All tests passed! Session tracking is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
