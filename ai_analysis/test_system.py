#!/usr/bin/env python3
"""
Test script for the AI Analysis system

This script tests the main components of the AI analysis system
including data loading, analysis, and Ollama integration.
"""

import json
import os
import sys
import time
from pathlib import Path

# Add the parent directory to the path so we can import from ai_analysis
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_analysis import ProductivityAnalyzer, AIAnalysisScheduler, create_default_config


def test_data_loading():
    """Test data loading functionality"""
    print("=" * 50)
    print("Testing Data Loading")
    print("=" * 50)

    config = create_default_config()
    analyzer = ProductivityAnalyzer(config)

    # Test log loading
    logs = analyzer.load_logs(hours_back=24)
    print(f"✅ Loaded {len(logs)} log entries")

    # Test status loading
    status = analyzer.load_status_data()
    print(f"✅ Loaded status data: {len(status)} fields")

    # Test sessions loading
    sessions = analyzer.load_sessions_data()
    print(f"✅ Loaded {len(sessions)} sessions")

    # Test data preparation
    data = analyzer.prepare_analysis_data()
    print(f"✅ Prepared analysis data with {data['total_logs']} logs")
    print(f"   - Top apps: {len(data['app_usage']['top_apps'])}")
    print(f"   - Browser tabs: {data['browser_data']['total_tabs']}")
    print(f"   - Sessions: {data['session_patterns']['total_sessions']}")

    return True


def test_prompt_generation():
    """Test prompt generation"""
    print("\n" + "=" * 50)
    print("Testing Prompt Generation")
    print("=" * 50)

    config = create_default_config()
    analyzer = ProductivityAnalyzer(config)

    # Prepare data
    data = analyzer.prepare_analysis_data()

    # Generate prompt
    prompt = analyzer.create_analysis_prompt(data)
    print(f"✅ Generated prompt ({len(prompt)} characters)")
    print(f"   Preview: {prompt[:200]}...")

    # Check for key components
    required_sections = [
        "Application Usage",
        "Browser Activity",
        "Session Patterns",
        "App Switching",
        "Current Status",
    ]

    for section in required_sections:
        if section in prompt:
            print(f"   ✅ Contains {section}")
        else:
            print(f"   ❌ Missing {section}")

    return True


def test_ollama_connection():
    """Test Ollama connection"""
    print("\n" + "=" * 50)
    print("Testing Ollama Connection")
    print("=" * 50)

    config = create_default_config()
    scheduler = AIAnalysisScheduler(config)

    # Test connection
    is_connected = scheduler.test_ollama_connection()

    if is_connected:
        print("✅ Ollama connection successful")
        return True
    else:
        print("❌ Ollama connection failed")
        print("   Make sure Ollama is running and Mistral model is available")
        print("   Run: ollama run mistral")
        return False


def test_full_analysis():
    """Test full analysis cycle"""
    print("\n" + "=" * 50)
    print("Testing Full Analysis")
    print("=" * 50)

    config = create_default_config()
    analyzer = ProductivityAnalyzer(config)

    print("🚀 Running full analysis...")
    result = analyzer.run_analysis()

    if result:
        print("✅ Analysis completed successfully")
        print(f"   Summary items: {len(result.get('summary', []))}")
        print(f"   Insights: {len(result.get('insights', {}))}")
        print(f"   Trends: {len(result.get('trends', {}))}")
        print(f"   Timestamp: {result.get('timestamp', 'N/A')}")

        # Print sample output
        print("\n📊 Sample Analysis Output:")
        for i, item in enumerate(result.get("summary", [])[:3]):
            print(f"   {i + 1}. {item}")

        return True
    else:
        print("❌ Analysis failed")
        return False


def test_scheduler():
    """Test scheduler functionality"""
    print("\n" + "=" * 50)
    print("Testing Scheduler")
    print("=" * 50)

    config = create_default_config()
    config["analysis_interval_minutes"] = 1  # Short interval for testing
    config["enabled"] = False  # Don't auto-start

    scheduler = AIAnalysisScheduler(config)

    # Test status
    status = scheduler.get_status()
    print(f"✅ Scheduler status: {status}")

    # Test manual analysis
    print("🧪 Running manual analysis...")
    result = scheduler.run_analysis_now()

    if result:
        print("✅ Manual analysis successful")
        return True
    else:
        print("❌ Manual analysis failed")
        return False


def create_sample_data():
    """Create sample data for testing"""
    print("\n" + "=" * 50)
    print("Creating Sample Data")
    print("=" * 50)

    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Create sample logs
    logs_file = data_dir / "logs.json"
    sample_logs = [
        {
            "timestamp": "2024-01-15T10:30:00",
            "app": "chrome.exe",
            "title": "GitHub - Project",
            "duration_sec": 1800,
        },
        {
            "timestamp": "2024-01-15T11:00:00",
            "app": "code.exe",
            "title": "Visual Studio Code",
            "duration_sec": 3600,
        },
        {
            "timestamp": "2024-01-15T12:00:00",
            "app": "Teams.exe",
            "title": "Microsoft Teams",
            "duration_sec": 600,
        },
    ]

    with open(logs_file, "w") as f:
        for log in sample_logs:
            f.write(json.dumps(log) + "\n")

    # Create sample status
    status_file = data_dir / "status.json"
    sample_status = {
        "session_time": 7200,
        "keystrokes": 1500,
        "current_app": "code.exe",
        "open_apps": ["chrome.exe", "code.exe", "Teams.exe"],
        "browser_data": {
            "active_tabs": {
                "tab1": {
                    "title": "GitHub",
                    "url": "https://github.com",
                    "total_time": 900,
                },
                "tab2": {
                    "title": "Stack Overflow",
                    "url": "https://stackoverflow.com",
                    "total_time": 300,
                },
            }
        },
        "last_updated": "2024-01-15T12:30:00",
    }

    with open(status_file, "w") as f:
        json.dump(sample_status, f, indent=2)

    # Create sample sessions
    sessions_file = data_dir / "sessions.json"
    sample_sessions = [
        {
            "start": "2024-01-15T09:00:00",
            "end": "2024-01-15T12:00:00",
            "duration_sec": 10800,
        },
        {
            "start": "2024-01-14T09:00:00",
            "end": "2024-01-14T17:00:00",
            "duration_sec": 28800,
        },
    ]

    with open(sessions_file, "w") as f:
        json.dump(sample_sessions, f, indent=2)

    print(f"✅ Created sample data in {data_dir}")
    return True


def main():
    """Main test function"""
    print("🔺 SnapAlert AI Analysis System Test")
    print("=" * 50)

    tests = [
        ("Creating Sample Data", create_sample_data),
        ("Data Loading", test_data_loading),
        ("Prompt Generation", test_prompt_generation),
        ("Ollama Connection", test_ollama_connection),
        ("Full Analysis", test_full_analysis),
        ("Scheduler", test_scheduler),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\n📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The AI analysis system is ready.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
