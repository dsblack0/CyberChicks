# SnapAlert - Complete Productivity Monitoring System

A comprehensive Windows productivity monitoring system with real-time session tracking, custom alerts, AI-powered insights, and automated notification management.

## 🚀 Overview

SnapAlert is a complete productivity monitoring solution that provides:
- **Real-time session tracking** with live updates every second
- **Custom alert system** with 4 alert types and flexible conditions
- **AI-powered insights** from local models analyzing your productivity patterns
- **Goal-based notifications** triggered by AI based on your work sessions
- **Automated Windows notifications** with proper SnapAlert branding
- **Manual alert testing** with instant trigger buttons
- **Comprehensive web dashboard** with live indicators

## 🎉 Key Features

### ✅ Live Session Timing
- **Real-time Updates**: Session time updates every second on the client-side
- **Backend Sync**: Syncs with backend every 5 seconds to prevent drift
- **Live Indicator**: Shows a pulsing "🔴 LIVE" indicator when session is active
- **Accurate Timing**: Uses backend session start time for precision
- **Status Updates**: Shows progression from "starting..." → "active now" → "🔴 LIVE"

### ✅ Custom Alerts System
- **Complete Backend API**: Full CRUD operations for custom alerts
- **4 Alert Types**: Session time, app usage time, keystroke count, and idle time
- **Flexible Conditions**: Greater than, less than, equal to
- **App Filtering**: Optional filtering by specific applications
- **Custom Messages**: Personalized alert messages with variable placeholders
- **Easy Management**: Enable/disable, edit, delete alerts from the web interface
- **Automatic Monitoring**: Tracker checks all enabled alerts every 5 seconds

### ✅ SnapAlert Test System & Branding
- **Test Alert Buttons**: Each custom alert has a "🧪 Test" button for instant testing
- **Basic Alert Testing**: Three test buttons for break reminders, idle apps, and session end alerts
- **🔺 SnapAlert Branding**: Consistent red triangle logo and "SnapAlert" naming throughout
- **Notification Branding**: All Windows notifications show "🔺 SnapAlert:" prefix
- **Automatic App Registration**: System automatically registers with Windows for proper notification branding

### 🤖 AI-Powered Insights & Goal-Based Notifications
- **Local AI Model**: Analyzes your productivity data using on-device AI models
- **Smart Insights**: Generates personalized productivity suggestions based on your work patterns
- **Goal Integration**: Set work goals and let AI trigger relevant notifications
- **Contextual Alerts**: AI understands your work context and sends timely reminders
- **Privacy-First**: All AI processing happens locally on your device
- **Adaptive Learning**: AI learns your productivity patterns over time

## 🔥 Custom Alert Examples You Can Create:

- **"Long Work Session"** - Alert after 2 hours of continuous work
- **"Social Media Limit"** - Alert after 30 minutes on social media apps
- **"Typing Goal"** - Alert after reaching 1000 keystrokes
- **"Idle Detection"** - Alert after 15 minutes of inactivity
- **"Chrome Time Limit"** - Alert after 1 hour of Chrome usage

## 📸 System in Action

The SnapAlert notification system provides proper Windows branding and clear messaging:

![Idle App Alert](alerts@1.png)
*Idle App Alert: Notifies when applications have been unused for specified periods*

![Keystroke Alert](alerts@2.png)  
*Keystroke Alert: Tracks typing activity and triggers when thresholds are reached*

![Session Time Alert](3@3.png)
*Session Time Alert: Monitors work session duration and provides timely reminders*

## 📁 File Structure

```
CyberChicks/
├── app.py                   # Main Flask web application
├── tracker.py              # Background productivity tracker
├── insights.py             # AI insights generation
├── alerts/
│   └── launcher.py          # Manual alert launcher script
├── data/
│   ├── custom_alerts.json   # Custom alerts from web interface
│   ├── logs.json           # Activity logs
│   ├── sessions.json       # Session history
│   └── status.json         # Current status
├── icons/
│   └── snapalert.ico        # SnapAlert icon
├── templates/
│   └── index.html          # Web dashboard
└── README_LAUNCHER.md       # This file
```

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Key dependencies include:
- `win10toast_click` - For proper Windows notification branding
- `flask` - Web interface
- `pynput` - Keyboard/mouse monitoring
- `psutil` - System monitoring
- `requests` - For AI model communication

### 2. Start the System

#### Option A: Web Interface + Tracker (Recommended)
```bash
python app.py
```
- Starts web interface at http://localhost:5000
- Includes all features: custom alerts, testing, session management, AI insights

#### Option B: Tracker Only
```bash
python tracker.py
```
- Starts background tracker with GUI
- Monitors productivity and triggers alerts
- Automatically registers SnapAlert with Windows

### 3. Create Custom Alerts

1. Open the web interface: http://localhost:5000
2. Go to **Settings** → **Custom Alerts**
3. Click **"+ Create Alert"** and configure:
   - **Name**: Short descriptive name (e.g., "Drink Water")
   - **Type**: Choose from session_time, app_time, keystroke_count, idle_time
   - **Condition**: greater_than, less_than, or equal_to
   - **Threshold**: Numeric value (minutes for time, count for keystrokes)
   - **Message**: Alert text (can use {threshold} and {app} placeholders)
   - **App Filter**: Optional app name filter
4. Click **"🧪 Test"** to test your alert immediately
5. Enable the alert to have it monitored automatically

### 4. Set Up AI Insights

1. Ensure you have a local AI model running (e.g., Ollama with Mistral)
2. Configure your work goals in the web interface
3. The system will automatically:
   - Analyze your productivity patterns
   - Generate personalized insights
   - Trigger goal-based notifications
   - Provide actionable suggestions

### 5. Use Your System

After setup:
- **Live Dashboard**: Watch real-time session tracking at http://localhost:5000
- **Automatic Alerts**: Custom alerts trigger automatically based on your conditions
- **AI Insights**: Get personalized productivity suggestions
- **Goal Notifications**: Receive AI-triggered reminders based on your goals
- **Manual Testing**: Click "🧪 Test" buttons to test any alert
- **Notifications**: All appear as "🔺 SnapAlert:" in Windows notifications

## 🎯 How It Works

### 1. Automatic Monitoring (tracker.py)
```python
# The tracker continuously monitors:
# - Keystroke count
# - Session duration
# - App usage time
# - Idle time
# - Checks all enabled custom alerts every 5 seconds
# - Triggers Windows notifications when conditions are met
```

### 2. Custom Alert Format (data/custom_alerts.json)
```json
{
  "id": "1703123456789",
  "name": "Drink Water",
  "type": "session_time",
  "condition": "greater_than",
  "threshold": 30,
  "message": "💧 Time to drink water! You've been working for {threshold} minutes.",
  "enabled": true,
  "app_filter": "",
  "created_at": "2024-01-01T12:00:00.000Z",
  "last_triggered": 1703123456.789,
  "trigger_count": 5
}
```

### 3. AI Insights System (insights.py)
```python
# AI system analyzes:
# - Work patterns and productivity cycles
# - App usage and focus times
# - Break patterns and session lengths
# - Generates personalized suggestions
# - Triggers goal-based notifications
# - Provides actionable productivity insights
```

### 4. Notification System
- **Primary Method**: `win10toast_click` (proper app source control)
- **Fallback 1**: PowerShell Toast notifications (with registered app ID)
- **Fallback 2**: `plyer` notifications
- **Fallback 3**: `win10toast` (final fallback)
- **Automatic Registration**: System registers "SnapAlert.ProductivityMonitor" with Windows

### 5. Alert Prevention
- **Anti-Spam**: Same alert won't trigger within 5 minutes
- **Smart Filtering**: Excludes system apps from idle alerts
- **Condition Checking**: Evaluates greater_than, less_than, equal_to conditions
- **Placeholder Replacement**: Replaces {threshold}, {app}, {value} in messages

## 🤖 AI Insights Features

### Productivity Analysis
- **Pattern Recognition**: Identifies your most productive hours and apps
- **Focus Analysis**: Tracks deep work sessions and interruption patterns
- **Break Optimization**: Suggests optimal break timing based on your work style
- **App Usage Insights**: Analyzes which applications boost or hurt productivity

### Goal-Based Notifications
- **Smart Goals**: Set productivity goals and let AI monitor progress
- **Contextual Reminders**: AI triggers notifications based on work context
- **Adaptive Suggestions**: AI learns your preferences and adjusts recommendations
- **Progress Tracking**: Monitor goal achievement with AI-powered insights

### Local AI Processing
- **Privacy-First**: All AI processing happens on your device
- **No Data Sharing**: Your productivity data never leaves your computer
- **Offline Capable**: Works without internet connection
- **Customizable Models**: Use your preferred local AI model (Ollama, etc.)

## 🧪 Testing Features

### Instant Alert Testing
```bash
# Test any custom alert by ID
python alerts/launcher.py "your_alert_id"

# Test from web interface
# Click "🧪 Test" button next to any custom alert
```

### Web Interface Testing
- **Custom Alert Test**: Click "🧪 Test" on any custom alert
- **Break Reminder Test**: Click "💪 Test Break Reminder" 
- **Idle App Test**: Click "💡 Test Idle App Alert"
- **Session End Test**: Click "📊 Test Session End"

## 🚀 API Endpoints

### Custom Alerts Management
- `GET /api/custom-alerts` - Get all custom alerts
- `POST /api/custom-alerts` - Create new custom alert
- `PUT /api/custom-alerts/{id}` - Update custom alert
- `DELETE /api/custom-alerts/{id}` - Delete custom alert
- `POST /api/custom-alerts/{id}/toggle` - Enable/disable alert
- `POST /api/custom-alerts/{id}/test` - Test alert immediately

### AI Insights
- `GET /api/insights` - Get AI-generated productivity insights
- `POST /api/goals` - Set productivity goals
- `GET /api/analytics` - Get productivity analytics data

### Testing Endpoints
- `POST /api/test-basic-alerts` - Test basic alert types
- `GET /api/stats` - Get current session statistics

## 🔧 Troubleshooting

### Common Issues

1. **Notifications not showing**
   - Check if `win10toast_click` is installed: `pip install win10toast_click`
   - Verify Windows notifications are enabled in system settings
   - Check console output for error messages

2. **Custom alerts not triggering**
   - Ensure alerts are enabled in the web interface
   - Check that the tracker is running: `python tracker.py`
   - Verify alert conditions are realistic (e.g., threshold not too high)

3. **AI insights not generating**
   - Ensure local AI model is running (e.g., Ollama)
   - Check that you have sufficient activity data
   - Verify network connectivity to local AI service

4. **Session time not updating**
   - Ensure JavaScript is enabled in your browser
   - Check that the Flask app is running
   - Refresh the page to restart the live updates

5. **Goal notifications not working**
   - Set clear, measurable goals in the web interface
   - Allow time for AI to learn your patterns
   - Check that AI model is responding properly

## 🎉 Benefits

1. **Complete Solution**: Web interface + background monitoring + Windows integration + AI insights
2. **Real-time Monitoring**: Live session updates with 1-second precision
3. **Proper Branding**: All notifications show as "SnapAlert" instead of "Python"
4. **Flexible Alerts**: 4 types with custom conditions and messages
5. **AI-Powered**: Local AI provides personalized insights and goal-based notifications
6. **Easy Testing**: Instant alert testing without waiting for conditions
7. **Privacy-First**: All AI processing happens locally on your device
8. **Automatic Management**: No manual setup required - everything just works
9. **Scalable**: Add unlimited custom alerts and goals through the web interface

## 📋 Workflow Summary

1. **Setup** → Install dependencies and start `python app.py`
2. **Create** → Design custom alerts in web interface
3. **Set Goals** → Configure productivity goals for AI monitoring
4. **Test** → Click "🧪 Test" buttons to verify alerts work
5. **Monitor** → System automatically checks and triggers alerts
6. **AI Insights** → Receive personalized productivity suggestions
7. **Optimize** → Adjust alerts and goals based on AI recommendations

## 🔗 Related Files

- `app.py` - Main web interface with custom alert management and testing
- `tracker.py` - Background tracker with live monitoring and notification system
- `insights.py` - AI insights generation and goal-based notifications
- `requirements.txt` - Python dependencies including win10toast_click
- `data/custom_alerts.json` - Your custom alert configurations
- `icons/snapalert.ico` - SnapAlert branding icon

---

**🔺 SnapAlert - Your Complete AI-Powered Productivity Monitoring Solution** 

*Made with ❤️ by the SnapAlert Team* 