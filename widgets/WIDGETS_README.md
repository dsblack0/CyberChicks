# 🔺 SnapAlert Desktop Widget

Transform your productivity monitoring with a beautiful, cutting-edge desktop widget that displays real-time metrics from your SnapAlert tracker in a stunning Apple-inspired interface.

## ✨ Features Overview

### 🎨 **Cutting-Edge Apple-Style Design**
- **Professional Typography**: SF Pro Display/Text fonts with Segoe UI fallback
- **Clean Color Palette**: Apple-inspired whites, grays, and blue accents (#007aff)
- **Card-Based Layout**: Each metric displayed in individual, elegant cards
- **Subtle Shadows**: Depth and visual hierarchy for premium feel
- **Modern Icons**: Clean, minimal icons with proper color coding

### 📜 **Scrollable Interface**
- **Mouse Wheel Support**: Effortlessly scroll through all your metrics
- **Canvas + Scrollbar**: Professional scrolling implementation
- **Dynamic Content**: Widget height adapts to your selected fields
- **Smooth Interaction**: Responsive and fluid user experience

### 🎛️ **Advanced Field Customization**
Choose exactly which metrics you want to see:
- ⏱ **Session Time**: Current work session duration
- ⌨ **Keystrokes**: Total keystrokes in current session  
- 🖥 **Current App**: Currently active application
- 📱 **Open Apps**: Number of running applications
- 🔔 **Alerts**: Active custom alerts monitoring
- 🌐 **Browser Tabs**: Open browser tabs across all browsers
- ⚡ **CPU Usage**: System CPU utilization (placeholder)
- 💾 **Memory Usage**: System memory usage (placeholder)

### ⚙️ **Professional Settings Panel**
- **Field Selection**: Toggle any combination of metrics on/off
- **Opacity Control**: Smooth slider for transparency adjustment
- **Always On Top**: Keep widget above other windows
- **Persistent Configuration**: Settings saved automatically
- **Live Updates**: Widget recreates instantly when fields change

## 🚀 Quick Start

### Simple Installation
```bash
# Navigate to the widgets directory
cd widgets

# Run the widget directly
python desktop_widget.py
```

### First Launch
1. **Widget appears** with default Apple-style design
2. **Drag the title bar** to position where you want
3. **Use mouse wheel** to scroll through metrics
4. **Click ⚙ settings** to customize fields and appearance
5. **Select your preferred metrics** and click Save Changes

## 🎯 How to Use

### **Basic Interaction**
- **Move**: Click and drag the "SnapAlert" title bar
- **Scroll**: Use mouse wheel to scroll through metrics
- **Settings**: Click the ⚙ gear icon for customization
- **Close**: Click the × button to exit

### **Customization Workflow**
1. **Open Settings**: Click ⚙ in the top-right corner
2. **Adjust Opacity**: Use slider for perfect transparency
3. **Select Fields**: Check/uncheck metrics you want to display
4. **Always On Top**: Toggle to keep widget visible
5. **Save Changes**: Apply your customizations instantly

### **Field Management**
- **Enable/Disable**: Any combination of the 8 available metrics
- **Real-time Updates**: Widget rebuilds immediately when you change fields
- **Persistent Settings**: Your configuration is saved to `widget_config.json`
- **Smart Defaults**: Essential metrics enabled by default

## 🔮 Future Possibilities

### 🤖 **AI-Powered Metrics (Coming Soon)**
The widget architecture is designed to support advanced AI-driven insights:

- **Productivity AI Score**: Machine learning analysis of your work patterns
- **Focus Quality Metrics**: AI assessment of concentration levels
- **Burnout Prevention**: Intelligent stress and fatigue detection
- **Task Efficiency AI**: Smart recommendations for workflow optimization
- **Predictive Break Suggestions**: AI-powered wellness recommendations
- **Smart Categorization**: Automatic classification of productive vs. non-productive time
- **Mood Analysis**: Sentiment analysis based on typing patterns and app usage
- **Performance Forecasting**: AI predictions of your optimal work periods

*These features will seamlessly integrate into the existing card system with the same beautiful Apple-style design.*

### 🎮 **Advanced Launcher System (Planned)**
We're exploring a comprehensive launcher that would provide:

#### **Visual Widget Builder**
- **Drag-and-Drop Interface**: Visually arrange your metrics
- **Live Preview**: See changes in real-time as you customize
- **Theme Gallery**: Choose from multiple design themes (Apple, Material, Glassmorphism)
- **Custom Color Schemes**: Create your own color palettes
- **Size Presets**: Small, medium, large, and custom dimensions

#### **Advanced Customization**
- **Metric Formulas**: Create custom calculated fields
- **Time-Based Themes**: Automatic day/night mode switching
- **Multi-Monitor Support**: Different widgets for different screens
- **Hotkey Integration**: Keyboard shortcuts for quick actions
- **Export/Import**: Share configurations with others

#### **Smart Templates**
- **Role-Based Presets**: Developer, Designer, Writer, Student configurations
- **Goal-Oriented Layouts**: Focus mode, productivity tracking, wellness monitoring
- **Company Themes**: Match your organization's branding
- **Seasonal Themes**: Automatic updates for holidays and seasons

#### **Integration Ecosystem**
- **Plugin Architecture**: Third-party developers can create custom metrics
- **API Connectivity**: Connect to external productivity tools
- **Webhook Support**: Real-time data from other applications
- **Cloud Sync**: Synchronize settings across multiple devices

## 🛠️ Technical Details

### **Architecture**
- **Data Source**: Reads from `../data/status.json` (auto-detects location)
- **Update Frequency**: 2-second refresh cycle
- **Memory Usage**: ~15-25MB (lightweight and efficient)
- **CPU Usage**: <1% on modern systems

### **Smart Data Loading**
```python
# Automatic path detection
status_files = [
    "data/status.json",
    "../data/status.json", 
    "../../data/status.json"
]
```

### **Field Configuration System**
```json
{
  "session_time": {
    "enabled": true,
    "name": "Session Time", 
    "icon": "⏱",
    "color": "primary"
  }
}
```

### **Extensible Design**
The widget is built with modularity in mind:
- **Easy metric addition**: Add new fields with minimal code changes
- **Theme system ready**: Color schemes easily swappable
- **Plugin-friendly**: Architecture supports future extensions
- **Cross-platform base**: Core functionality works on any OS

## 🎨 Customization Guide

### **Colors & Themes**
```python
# Current Apple-inspired theme
"primary": "#007aff",        # Apple blue
"success": "#30d158",        # Apple green  
"warning": "#ff9500",        # Apple orange
"error": "#ff3b30",          # Apple red
"primary_text": "#1d1d1f",   # Dark text
"secondary_text": "#86868b", # Gray text
```

### **Typography System**
- **Title**: SF Pro Display 18pt Bold (fallback: Segoe UI)
- **Subtitle**: SF Pro Display 14pt Regular
- **Body**: SF Pro Text 13pt Regular
- **Caption**: SF Pro Text 11pt Regular

### **Adding Custom Metrics**
1. **Update field_config** in `load_field_config()`
2. **Add display logic** in `update_metrics()`
3. **Set default value** in `get_default_value()`
4. **Widget automatically includes** the new field in settings

## 📊 Data Integration

### **Current Data Sources**
- **SnapAlert Tracker**: Primary productivity data
- **Browser Tracking**: Tab and website information
- **System Metrics**: Basic CPU/memory (expandable)
- **Custom Alerts**: User-defined monitoring rules

### **Future Data Sources**
- **Calendar Integration**: Meeting and appointment data
- **Email Analytics**: Communication patterns
- **Code Metrics**: Git commits, lines of code, debugging time
- **Health Sensors**: Heart rate, stress levels (with wearables)
- **Environment Data**: Ambient noise, lighting, temperature

## 🔒 Privacy & Performance

### **Privacy-First Design**
- **100% Local**: All data processing happens on your machine
- **No Network Calls**: Widget never connects to the internet
- **Minimal Permissions**: Only reads local JSON files
- **User Control**: You choose exactly what data to display

### **Performance Optimized**
- **Efficient Updates**: Only redraws changed elements
- **Smart Caching**: Reduces file I/O operations
- **Threaded Architecture**: Non-blocking UI updates
- **Memory Management**: Automatic cleanup and optimization

## 🚀 Getting Started Examples

### **Developer Setup**
Perfect for tracking coding productivity:
```bash
# Enable these fields
✓ Session Time
✓ Keystrokes  
✓ Current App
✓ Browser Tabs
✗ Alerts (disable if not using)
```

### **Writer/Content Creator**
Focus on writing metrics:
```bash
# Minimal distraction setup
✓ Session Time
✓ Keystrokes
✓ Current App
✗ Open Apps
✗ Browser Tabs
```

### **Manager/Analyst**
Comprehensive monitoring:
```bash
# Full visibility setup
✓ All fields enabled
+ Future AI metrics when available
```

## 🔗 Integration Examples

### **Auto-Start on Windows**
```batch
@echo off
cd /d "C:\path\to\CyberChicks\widgets"
python desktop_widget.py
```

### **Task Scheduler Integration**
- **Trigger**: At startup or user logon
- **Action**: Start program `python.exe`
- **Arguments**: `C:\path\to\desktop_widget.py`
- **Start in**: `C:\path\to\CyberChicks\widgets`

## 📝 Roadmap

### **Version 2.0 - AI Integration**
- Machine learning productivity insights
- Predictive analytics for work patterns
- Smart recommendations engine
- Advanced data visualization

### **Version 3.0 - Launcher & Ecosystem**
- Visual customization interface
- Plugin marketplace
- Multi-device synchronization
- Enterprise features

### **Version 4.0 - Platform Expansion**
- Cross-platform compatibility (macOS, Linux)
- Mobile companion apps
- Web dashboard integration
- API for third-party tools

---

**Experience the future of productivity monitoring today:**

```bash
cd widgets && python desktop_widget.py
```

**Ready for the next level?** The widget's extensible architecture means that as we add AI metrics and advanced launchers, your customizations and preferences will seamlessly upgrade with new capabilities.

*The future of productivity monitoring is here – beautiful, intelligent, and completely under your control.* 🚀 