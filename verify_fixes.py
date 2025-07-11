#!/usr/bin/env python3
"""
Verification script for session tracking fixes
Run this to verify that the session tracking improvements are working.
"""

import json
import os
import time
import requests
from datetime import datetime


def check_files():
    """Check if required files exist"""
    print("🔍 Checking required files...")

    files_to_check = ["data/status.json", "data/sessions.json", "tracker.py", "app.py"]

    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            return False

    return True


def check_session_persistence():
    """Check if session data persists correctly"""
    print("\n📊 Checking session persistence...")

    status_file = "data/status.json"
    sessions_file = "data/sessions.json"

    # Read current status
    try:
        with open(status_file, "r") as f:
            status = json.load(f)

        print("✅ Status file loaded successfully")

        # Check for session_start_time
        if "session_start_time" in status:
            session_start = datetime.fromisoformat(status["session_start_time"])
            current_time = datetime.now()
            session_duration = (current_time - session_start).total_seconds()

            print(f"   Current session started: {session_start}")
            print(f"   Session duration: {session_duration:.0f} seconds")
            print(f"   Reported session time: {status.get('session_time', 0)} seconds")

            # Check if times are close (within 10 seconds)
            diff = abs(session_duration - status.get("session_time", 0))
            if diff < 10:
                print("✅ Session time calculation is accurate")
            else:
                print(f"⚠️  Session time difference: {diff:.1f} seconds")
        else:
            print("❌ No session_start_time in status file")

    except Exception as e:
        print(f"❌ Error reading status file: {e}")
        return False

    # Read sessions file
    try:
        with open(sessions_file, "r") as f:
            sessions = json.load(f)

        print(f"✅ Sessions file contains {len(sessions)} sessions")

        if sessions:
            latest = sessions[-1]
            print(f"   Latest session: {latest.get('duration_sec', 0)} seconds")
        else:
            print("   No completed sessions yet")

    except Exception as e:
        print(f"❌ Error reading sessions file: {e}")
        return False

    return True


def check_api_response():
    """Check if API returns correct session data"""
    print("\n🌐 Checking API response...")

    try:
        response = requests.get("http://localhost:5000/api/stats", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print("✅ API is responding")

            # Check required fields
            required_fields = [
                "session_start_time",
                "total_sessions",
                "current_session_time",
            ]
            for field in required_fields:
                if field in data:
                    print(f"✅ {field}: {data[field]}")
                else:
                    print(f"❌ Missing {field}")

            # Calculate real-time session
            if "session_start_time" in data:
                session_start = datetime.fromisoformat(data["session_start_time"])
                current_time = datetime.now()
                real_time_duration = (current_time - session_start).total_seconds()
                api_duration = data.get("current_session_time", 0)

                print(f"   Real-time calculation: {real_time_duration:.0f} seconds")
                print(f"   API reported time: {api_duration} seconds")

                diff = abs(real_time_duration - api_duration)
                if diff < 10:
                    print("✅ API session time is accurate")
                else:
                    print(f"⚠️  API time difference: {diff:.1f} seconds")

            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False

    except requests.RequestException as e:
        print(f"❌ Failed to connect to API: {e}")
        print("   Make sure the Flask app is running on localhost:5000")
        return False


def test_browser_refresh_simulation():
    """Simulate what happens when browser refreshes"""
    print("\n🔄 Testing browser refresh behavior...")

    try:
        # Make multiple API calls to simulate browser refreshes
        session_times = []
        session_starts = []

        for i in range(3):
            response = requests.get("http://localhost:5000/api/stats", timeout=5)
            if response.status_code == 200:
                data = response.json()
                session_times.append(data.get("current_session_time", 0))
                session_starts.append(data.get("session_start_time", ""))

                print(f"   Call {i + 1}: Session time = {session_times[-1]} seconds")
                time.sleep(2)  # Wait 2 seconds between calls
            else:
                print(f"❌ API call {i + 1} failed")
                return False

        # Check if session start time is consistent
        if len(set(session_starts)) == 1:
            print("✅ Session start time is consistent across API calls")
        else:
            print("❌ Session start time is changing between API calls")
            return False

        # Check if session time is increasing
        if session_times[2] > session_times[0]:
            print("✅ Session time is increasing correctly")
        else:
            print("❌ Session time is not increasing")
            return False

        return True

    except Exception as e:
        print(f"❌ Error testing refresh behavior: {e}")
        return False


def main():
    print("🚀 Session Tracking Fix Verification")
    print("=" * 50)

    # Run all tests
    tests = [
        ("File Check", check_files),
        ("Session Persistence", check_session_persistence),
        ("API Response", check_api_response),
        ("Browser Refresh Test", test_browser_refresh_simulation),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"   {test_name}: {status}")

    if all(results):
        print("\n🎉 All tests passed! Session tracking fixes are working correctly.")
        print("\n💡 The fixes should resolve:")
        print("   • Session time resetting on browser refresh")
        print("   • Total sessions not showing up")
        print("   • Session state persistence across tracker restarts")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        print("\n🔧 Make sure:")
        print("   • tracker.py is running")
        print("   • Flask app is running on localhost:5000")
        print("   • You have recent activity (mouse/keyboard) in the last 10 minutes")


if __name__ == "__main__":
    main()
