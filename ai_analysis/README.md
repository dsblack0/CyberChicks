# SnapAlert AI Analysis System

This folder contains the AI-powered productivity analysis system for SnapAlert. It uses Ollama's Mistral model to analyze user behavior patterns and provide actionable insights.

## 🚀 Features

- **Automated Analysis**: Runs every 20 minutes (configurable) to analyze productivity patterns
- **Real-time Insights**: Generates actionable insights based on app usage, browser activity, and session patterns
- **Anomaly Detection**: Identifies unusual behavior patterns and potential productivity issues
- **Customizable Scheduling**: Adjustable analysis intervals and configuration
- **Web Interface**: Full integration with SnapAlert's web dashboard

## 📁 File Structure

```
ai_analysis/
├── __init__.py           # Package initialization
├── analyzer.py           # Core analysis engine
├── scheduler.py          # Scheduling and orchestration
├── system_prompt.txt     # System prompt for Mistral model
├── test_system.py        # Comprehensive test suite
└── README.md            # This file
```

## 🛠️ Prerequisites

### 1. Install Ollama
```bash
# Download and install Ollama from https://ollama.ai/
# Then pull the Mistral model
ollama pull mistral
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

The system requires:
- `requests` for API calls
- `APScheduler` for scheduling
- `Flask` for web integration

## 🔧 Configuration

### Default Configuration
```json
{
    "enabled": true,
    "analysis_interval_minutes": 20,
    "ollama_url": "http://localhost:11434",
    "model_name": "mistral",
    "data_dir": "data"
}
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `enabled` | Enable/disable AI analysis | `true` |
| `analysis_interval_minutes` | How often to run analysis | `20` |
| `ollama_url` | Ollama API endpoint | `http://localhost:11434` |
| `model_name` | Model to use for analysis | `mistral` |
| `data_dir` | Directory for data files | `data` |

## 🚦 Usage

### Starting the System

The AI analysis system starts automatically when you run the SnapAlert Flask app:

```bash
python app.py
```

### Manual Controls

From the web interface (Settings → AI Analysis Configuration):
- **Start/Stop Scheduler**: Control the automatic analysis
- **Run Analysis Now**: Trigger immediate analysis
- **Test Ollama Connection**: Verify Ollama is accessible
- **Configure Settings**: Adjust interval and model settings

### API Endpoints

- `GET /api/ai-analysis/config` - Get current configuration
- `POST /api/ai-analysis/config` - Update configuration
- `POST /api/ai-analysis/start` - Start scheduler
- `POST /api/ai-analysis/stop` - Stop scheduler
- `POST /api/ai-analysis/run-now` - Run analysis immediately
- `POST /api/ai-analysis/test-ollama` - Test Ollama connection
- `GET /api/ai-analysis/insights` - Get all insights
- `GET /api/ai-analysis/insights/<limit>` - Get recent insights

## 🧪 Testing

Run the comprehensive test suite:

```bash
python ai_analysis/test_system.py
```

This will test:
- Data loading and preparation
- Prompt generation
- Ollama connection
- Full analysis cycle
- Scheduler functionality

## 📊 Analysis Output

The system generates insights in the following format:

```json
{
  "summary": [
    "Key finding 1 (brief, actionable)",
    "Key finding 2 (brief, actionable)",
    "Key finding 3 (brief, actionable)"
  ],
  "insights": {
    "productivity_score": "Score from 1-100 with explanation",
    "focus_quality": "Assessment of attention patterns",
    "top_distraction": "Primary distraction identified",
    "recommended_action": "Specific actionable recommendation"
  },
  "anomalies": [
    "Any unusual patterns or behaviors detected"
  ],
  "trends": {
    "improving": "What's getting better",
    "concerning": "What needs attention",
    "stable": "What's consistent"
  },
  "timestamp": "ISO timestamp of analysis"
}
```

## 🎯 Analysis Focus Areas

### 1. Productivity Patterns
- Peak productivity hours and applications
- Focus sessions vs. distraction periods
- Time spent in productive vs. non-productive applications

### 2. Attention & Focus Analysis
- App switching frequency and patterns
- Multitasking behaviors
- Idle periods and break patterns

### 3. Anomaly Detection
- Unusual application usage patterns
- Apps running idle for extended periods (>30 minutes)
- Deviation from normal usage patterns

### 4. Browser Behavior
- Tab management patterns
- Website categories and productivity impact
- Distraction patterns in web browsing

### 5. System Performance
- Application responsiveness indicators
- Resource usage patterns
- Performance bottlenecks

## 🔍 Data Sources

The system analyzes:
- **Application Logs** (`data/logs.json`): App usage, switching patterns, duration
- **Status Data** (`data/status.json`): Current session, browser tabs, keystroke counts
- **Session Data** (`data/sessions.json`): Historical session patterns
- **Browser Data**: Active tabs, URLs, time spent on different sites

## 🛡️ Privacy & Security

- **Local Processing**: All analysis happens locally using Ollama
- **No Data Transmission**: No user data is sent to external services
- **Configurable**: Can be disabled entirely if desired
- **Transparent**: Open source system prompt and analysis logic

## 🐛 Troubleshooting

### Common Issues

1. **Ollama Connection Failed**
   ```bash
   # Make sure Ollama is running
   ollama serve
   
   # Verify Mistral model is available
   ollama list
   ```

2. **Analysis Not Running**
   - Check if scheduler is enabled in settings
   - Verify Ollama is accessible
   - Check console logs for error messages

3. **No Insights Generated**
   - Ensure there's sufficient data in `data/logs.json`
   - Check that the analysis interval isn't too frequent
   - Verify the system prompt is loaded correctly

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export SNAPALERT_DEBUG=true
```

## 🔄 Data Flow

1. **Data Collection**: SnapAlert tracker collects usage data
2. **Data Preparation**: Analyzer processes logs, status, and session data
3. **Prompt Generation**: System creates structured prompt for Mistral
4. **AI Analysis**: Ollama/Mistral generates insights
5. **Storage**: Results saved to `data/insights.json`
6. **Visualization**: Web interface displays insights

## 🎛️ Customization

### Modifying the System Prompt
Edit `system_prompt.txt` to customize the analysis focus or output format.

### Adding New Analysis Types
Extend the `ProductivityAnalyzer` class to add new analysis methods.

### Custom Scheduling
Modify the `AIAnalysisScheduler` to add custom triggers or conditions.

## 📈 Performance

- **Analysis Time**: Typically 5-15 seconds per analysis
- **Memory Usage**: ~50MB during analysis
- **Storage**: Insights are automatically pruned to last 100 entries
- **Scheduling**: Uses APScheduler for efficient background processing

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Add tests for new functionality**
4. **Run the test suite**
5. **Submit a pull request**

## 📋 TODO

- [ ] Add more analysis models (Qgenie, etc.)
- [ ] Implement insight confidence scoring
- [ ] Add trend analysis over longer periods
- [ ] Export insights to different formats
- [ ] Add email/notification alerts for insights

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Run the test suite to identify problems
3. Check the console logs for error messages
4. Review the system prompt and configuration

---

**Built with ❤️ for CyberChicks Productivity Monitor** 
