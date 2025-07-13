import json
import os
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional


class ProductivityAnalyzer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ollama_url = config.get("ollama_url", "http://localhost:11434")
        self.model_name = config.get("model_name", "mistral")
        self.data_dir = Path(config.get("data_dir", "data"))
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load the system prompt from file"""
        prompt_file = Path(__file__).parent / "system_prompt.txt"
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(
                f"[AI Analysis] Warning: System prompt file not found at {prompt_file}"
            )
            return "You are an AI productivity analyst. Analyze the provided data and give insights."

    def load_logs(self, hours_back: int = 24) -> List[Dict]:
        """Load recent logs from logs.json"""
        logs_file = self.data_dir / "logs.json"
        if not logs_file.exists():
            print(f"[AI Analysis] No logs file found at {logs_file}")
            return []

        try:
            all_logs = []
            cutoff_time = datetime.now() - timedelta(hours=hours_back)

            with open(logs_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            log_entry = json.loads(line)
                            # Parse timestamp and filter recent logs
                            if "timestamp" in log_entry:
                                log_time = datetime.fromisoformat(
                                    log_entry["timestamp"].replace("Z", "+00:00")
                                )
                                if log_time.replace(tzinfo=None) >= cutoff_time:
                                    all_logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue

            print(
                f"[AI Analysis] Loaded {len(all_logs)} log entries from last {hours_back} hours"
            )
            return all_logs

        except Exception as e:
            print(f"[AI Analysis] Error loading logs: {e}")
            return []

    def load_status_data(self) -> Dict:
        """Load current status data"""
        status_file = self.data_dir / "status.json"
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[AI Analysis] Error loading status: {e}")
            return {}

    def load_sessions_data(self) -> List[Dict]:
        """Load sessions data"""
        sessions_file = self.data_dir / "sessions.json"
        try:
            with open(sessions_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[AI Analysis] Error loading sessions: {e}")
            return []

    def prepare_analysis_data(self) -> Dict:
        """Prepare structured data for analysis"""
        logs = self.load_logs(hours_back=24)
        status = self.load_status_data()
        sessions = self.load_sessions_data()

        # Analyze app usage patterns
        app_usage = self._analyze_app_usage(logs)

        # Analyze browser activity
        browser_data = self._analyze_browser_activity(logs, status)

        # Analyze session patterns
        session_patterns = self._analyze_session_patterns(sessions)

        # Analyze switching patterns
        switching_patterns = self._analyze_switching_patterns(logs)

        # Current status
        current_status = {
            "session_time": status.get("session_time", 0),
            "keystrokes": status.get("keystrokes", 0),
            "current_app": status.get("current_app", "Unknown"),
            "open_apps": status.get("open_apps", []),
            "last_updated": status.get("last_updated", ""),
        }

        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "time_range": "24 hours",
            "total_logs": len(logs),
            "app_usage": app_usage,
            "browser_data": browser_data,
            "session_patterns": session_patterns,
            "switching_patterns": switching_patterns,
            "current_status": current_status,
        }

    def _analyze_app_usage(self, logs: List[Dict]) -> Dict:
        """Analyze application usage patterns"""
        app_times = {}
        app_idle_times = {}

        for log in logs:
            app = log.get("app", "Unknown")
            duration = log.get("duration_sec", 0)

            if app not in app_times:
                app_times[app] = {"total_time": 0, "sessions": 0}

            app_times[app]["total_time"] += duration
            app_times[app]["sessions"] += 1

            # Check for idle apps (running but not active)
            if duration > 1800:  # 30 minutes
                if app not in app_idle_times:
                    app_idle_times[app] = []
                app_idle_times[app].append(duration)

        # Sort by total time
        sorted_apps = sorted(
            app_times.items(), key=lambda x: x[1]["total_time"], reverse=True
        )

        return {
            "top_apps": sorted_apps[:10],
            "total_apps": len(app_times),
            "potentially_idle": app_idle_times,
        }

    def _analyze_browser_activity(self, logs: List[Dict], status: Dict) -> Dict:
        """Analyze browser activity patterns"""
        browser_data = status.get("browser_data", {})
        active_tabs = browser_data.get("active_tabs", {})

        return {
            "total_tabs": len(active_tabs),
            "active_browsers": browser_data.get("stats", {}).get("active_browsers", []),
            "tab_switching": len(active_tabs) > 5,  # Indicator of potential distraction
            "browser_time": sum(
                tab.get("total_time", 0) for tab in active_tabs.values()
            ),
        }

    def _analyze_session_patterns(self, sessions: List[Dict]) -> Dict:
        """Analyze session patterns"""
        if not sessions:
            return {"total_sessions": 0, "average_length": 0}

        # Get recent sessions (last 7 days)
        recent_sessions = sessions[-50:]  # Last 50 sessions as proxy

        total_duration = sum(
            session.get("duration_sec", 0) for session in recent_sessions
        )
        avg_duration = total_duration / len(recent_sessions) if recent_sessions else 0

        # Categorize sessions
        short_sessions = sum(
            1 for s in recent_sessions if s.get("duration_sec", 0) < 300
        )  # < 5 min
        medium_sessions = sum(
            1 for s in recent_sessions if 300 <= s.get("duration_sec", 0) < 1800
        )  # 5-30 min
        long_sessions = sum(
            1 for s in recent_sessions if s.get("duration_sec", 0) >= 1800
        )  # > 30 min

        return {
            "total_sessions": len(recent_sessions),
            "average_length": avg_duration,
            "short_sessions": short_sessions,
            "medium_sessions": medium_sessions,
            "long_sessions": long_sessions,
        }

    def _analyze_switching_patterns(self, logs: List[Dict]) -> Dict:
        """Analyze app switching patterns"""
        switches = 0
        last_app = None

        for log in logs:
            current_app = log.get("app", "Unknown")
            if last_app and last_app != current_app:
                switches += 1
            last_app = current_app

        hours_analyzed = 24  # Based on log loading
        switches_per_hour = switches / hours_analyzed if hours_analyzed > 0 else 0

        return {
            "total_switches": switches,
            "switches_per_hour": switches_per_hour,
            "high_switching": switches_per_hour > 20,
        }

    def create_analysis_prompt(self, data: Dict) -> str:
        """Create the full prompt for Ollama"""
        prompt = f"""
{self.system_prompt}

## Current Analysis Data

**Analysis Timestamp:** {data["analysis_timestamp"]}
**Time Range:** {data["time_range"]} ({data["total_logs"]} log entries)

### Application Usage
**Top Applications:**
"""

        # Add top apps
        for app, stats in data["app_usage"]["top_apps"][:5]:
            hours = stats["total_time"] / 3600
            prompt += f"- {app}: {hours:.1f}h ({stats['sessions']} sessions)\n"

        prompt += f"\n**Total Apps Used:** {data['app_usage']['total_apps']}\n"

        # Add potentially idle apps
        if data["app_usage"]["potentially_idle"]:
            prompt += "\n**Potentially Idle Apps (>30min sessions):**\n"
            for app, durations in data["app_usage"]["potentially_idle"].items():
                avg_idle = sum(durations) / len(durations) / 60  # Convert to minutes
                prompt += f"- {app}: {avg_idle:.1f}min average idle time\n"

        # Add browser data
        prompt += f"""
### Browser Activity
**Active Tabs:** {data["browser_data"]["total_tabs"]}
**Active Browsers:** {len(data["browser_data"]["active_browsers"])}
**Browser Time:** {data["browser_data"]["browser_time"] / 3600:.1f}h
**High Tab Count:** {"Yes" if data["browser_data"]["tab_switching"] else "No"}

### Session Patterns
**Total Sessions:** {data["session_patterns"]["total_sessions"]}
**Average Session Length:** {data["session_patterns"]["average_length"] / 60:.1f} minutes
**Short Sessions (<5min):** {data["session_patterns"]["short_sessions"]}
**Medium Sessions (5-30min):** {data["session_patterns"]["medium_sessions"]}
**Long Sessions (>30min):** {data["session_patterns"]["long_sessions"]}

### App Switching
**Total Switches:** {data["switching_patterns"]["total_switches"]}
**Switches per Hour:** {data["switching_patterns"]["switches_per_hour"]:.1f}
**High Switching Activity:** {"Yes" if data["switching_patterns"]["high_switching"] else "No"}

### Current Status
**Current Session Time:** {data["current_status"]["session_time"] / 60:.1f} minutes
**Session Keystrokes:** {data["current_status"]["keystrokes"]}
**Current App:** {data["current_status"]["current_app"]}
**Open Apps:** {len(data["current_status"]["open_apps"])}

## Analysis Request
Based on this data, provide your analysis in the specified JSON format. Focus on actionable insights and patterns that can help improve productivity.
"""

        return prompt

    def call_ollama(self, prompt: str) -> Optional[Dict]:
        """Call Ollama API to generate analysis"""
        try:
            print(
                f"[AI Analysis] Calling Ollama at {self.ollama_url} with model {self.model_name}"
            )
            print(f"[AI Analysis] Prompt length: {len(prompt)} characters")
            print(f"[AI Analysis] Starting analysis request (timeout: 180s)...")

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "top_p": 0.9, "num_predict": 400},
                },
                timeout=180,  # Increased timeout to 3 minutes for complex analysis
            )

            if response.status_code == 200:
                print(f"[AI Analysis] ✅ Ollama responded successfully")
                result = response.json()
                analysis_text = result.get("response", "")
                print(f"[AI Analysis] Response length: {len(analysis_text)} characters")

                # Try to extract JSON from the response
                try:
                    # Find JSON content between ```json and ``` or { and }
                    import re

                    json_match = re.search(
                        r"```json\s*({.*?})\s*```", analysis_text, re.DOTALL
                    )
                    if json_match:
                        analysis_json = json.loads(json_match.group(1))
                    else:
                        # Try to find any JSON object
                        json_match = re.search(r"({.*})", analysis_text, re.DOTALL)
                        if json_match:
                            analysis_json = json.loads(json_match.group(1))
                        else:
                            # Fallback: create basic structure
                            analysis_json = {
                                "summary": [
                                    analysis_text[:200] + "..."
                                    if len(analysis_text) > 200
                                    else analysis_text
                                ],
                                "insights": {
                                    "productivity_score": "Analysis generated",
                                    "focus_quality": "See summary",
                                    "top_distraction": "Multiple factors",
                                    "recommended_action": "Review summary",
                                },
                                "anomalies": [],
                                "trends": {
                                    "improving": "Analysis in progress",
                                    "concerning": "None detected",
                                    "stable": "System functioning",
                                },
                                "timestamp": datetime.now().isoformat(),
                            }

                    print(f"[AI Analysis] Successfully generated analysis")
                    return analysis_json

                except json.JSONDecodeError as e:
                    print(f"[AI Analysis] Failed to parse JSON response: {e}")
                    print(f"[AI Analysis] Raw response: {analysis_text[:500]}...")
                    return None

            else:
                print(
                    f"[AI Analysis] Ollama API error: {response.status_code} - {response.text}"
                )
                return None

        except requests.exceptions.RequestException as e:
            print(f"[AI Analysis] Network error calling Ollama: {e}")
            return None
        except Exception as e:
            print(f"[AI Analysis] Unexpected error: {e}")
            return None

    def save_insights(self, insights: Dict) -> bool:
        """Save insights to insights.json"""
        try:
            insights_file = self.data_dir / "insights.json"

            # Load existing insights
            existing_insights = []
            if insights_file.exists():
                try:
                    with open(insights_file, "r", encoding="utf-8") as f:
                        existing_insights = json.load(f)
                except:
                    existing_insights = []

            # Add new insight
            existing_insights.append(insights)

            # Keep only last 100 insights
            if len(existing_insights) > 100:
                existing_insights = existing_insights[-100:]

            # Save back to file
            with open(insights_file, "w", encoding="utf-8") as f:
                json.dump(existing_insights, f, indent=2, ensure_ascii=False)

            print(f"[AI Analysis] Insights saved to {insights_file}")
            return True

        except Exception as e:
            print(f"[AI Analysis] Error saving insights: {e}")
            return False

    def run_analysis(self) -> Optional[Dict]:
        """Run complete analysis cycle"""
        print(f"[AI Analysis] Starting analysis at {datetime.now()}")

        # Prepare data
        data = self.prepare_analysis_data()

        # Create prompt
        prompt = self.create_analysis_prompt(data)

        # Call Ollama
        insights = self.call_ollama(prompt)

        if insights:
            # Save insights
            if self.save_insights(insights):
                print(f"[AI Analysis] Analysis completed successfully")
                return insights
            else:
                print(f"[AI Analysis] Failed to save insights")
                return None
        else:
            print(f"[AI Analysis] Failed to generate insights")
            return None


def create_default_config() -> Dict:
    """Create default configuration"""
    return {
        "ollama_url": "http://localhost:11434",
        "model_name": "mistral",
        "data_dir": "data",
        "analysis_interval_minutes": 20,
        "enabled": True,
    }


if __name__ == "__main__":
    # Test the analyzer
    config = create_default_config()
    analyzer = ProductivityAnalyzer(config)

    result = analyzer.run_analysis()
    if result:
        print("Analysis completed successfully!")
        print(json.dumps(result, indent=2))
    else:
        print("Analysis failed!")
