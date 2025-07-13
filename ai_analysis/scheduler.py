import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
import atexit

from .analyzer import ProductivityAnalyzer, create_default_config


class AIAnalysisScheduler:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or create_default_config()
        self.analyzer = ProductivityAnalyzer(self.config)
        self.scheduler = None
        self.is_running = False
        self.last_analysis_time = None
        self.analysis_count = 0
        self.config_file = (
            Path(self.config.get("data_dir", "data")) / "ai_analysis_config.json"
        )

        # Load configuration from file if it exists
        self.load_config()

        # Set up scheduler
        self.setup_scheduler()

    def load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
                    print(
                        f"[AI Scheduler] Loaded configuration from {self.config_file}"
                    )
        except Exception as e:
            print(f"[AI Scheduler] Error loading config: {e}")

    def save_config(self):
        """Save configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"[AI Scheduler] Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            print(f"[AI Scheduler] Error saving config: {e}")
            return False

    def setup_scheduler(self):
        """Set up the APScheduler"""
        try:
            # Configure scheduler with thread pool executor
            executors = {"default": ThreadPoolExecutor(max_workers=1)}

            job_defaults = {
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 300,  # 5 minutes
            }

            self.scheduler = BackgroundScheduler(
                executors=executors, job_defaults=job_defaults, timezone="UTC"
            )

            # Register shutdown handler
            atexit.register(self.shutdown)

            print(f"[AI Scheduler] Scheduler configured successfully")

        except Exception as e:
            print(f"[AI Scheduler] Error setting up scheduler: {e}")
            self.scheduler = None

    def schedule_analysis(self):
        """Schedule the periodic analysis job"""
        if not self.scheduler:
            print(f"[AI Scheduler] Scheduler not available")
            return False

        try:
            interval_minutes = self.config.get("analysis_interval_minutes", 20)

            # Remove existing job if it exists
            if self.scheduler.get_job("ai_analysis"):
                self.scheduler.remove_job("ai_analysis")

            # Add new job
            self.scheduler.add_job(
                func=self.run_analysis_job,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id="ai_analysis",
                name="AI Productivity Analysis",
                replace_existing=True,
            )

            print(f"[AI Scheduler] Analysis scheduled every {interval_minutes} minutes")
            return True

        except Exception as e:
            print(f"[AI Scheduler] Error scheduling analysis: {e}")
            return False

    def run_analysis_job(self):
        """Job function that runs the analysis"""
        try:
            if not self.config.get("enabled", True):
                print(f"[AI Scheduler] Analysis disabled in config")
                return

            print(
                f"[AI Scheduler] Running scheduled analysis #{self.analysis_count + 1}"
            )

            # Run the analysis
            result = self.analyzer.run_analysis()

            if result:
                self.last_analysis_time = datetime.now()
                self.analysis_count += 1

                print(f"[AI Scheduler] Analysis completed successfully")
                print(
                    f"[AI Scheduler] Summary: {result.get('summary', ['No summary'])}"
                )

                # Log the analysis for debugging
                self.log_analysis_result(result)

            else:
                print(f"[AI Scheduler] Analysis failed")

        except Exception as e:
            print(f"[AI Scheduler] Error in analysis job: {e}")

    def log_analysis_result(self, result: Dict):
        """Log analysis result for debugging"""
        try:
            log_file = (
                Path(self.config.get("data_dir", "data")) / "ai_analysis_log.json"
            )

            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "analysis_count": self.analysis_count,
                "success": True,
                "summary": result.get("summary", []),
                "productivity_score": result.get("insights", {}).get(
                    "productivity_score", "N/A"
                ),
            }

            # Append to log file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            print(f"[AI Scheduler] Error logging analysis result: {e}")

    def start(self):
        """Start the scheduler"""
        if not self.scheduler:
            print(f"[AI Scheduler] Cannot start - scheduler not configured")
            return False

        try:
            if not self.is_running:
                self.scheduler.start()
                self.schedule_analysis()
                self.is_running = True
                print(f"[AI Scheduler] Scheduler started successfully")
                return True
            else:
                print(f"[AI Scheduler] Scheduler already running")
                return True

        except Exception as e:
            print(f"[AI Scheduler] Error starting scheduler: {e}")
            return False

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler and self.is_running:
            try:
                self.scheduler.shutdown(wait=False)
                self.is_running = False
                print(f"[AI Scheduler] Scheduler stopped")
                return True
            except Exception as e:
                print(f"[AI Scheduler] Error stopping scheduler: {e}")
                return False
        return True

    def shutdown(self):
        """Shutdown handler"""
        if self.is_running:
            self.stop()

    def get_status(self) -> Dict:
        """Get current scheduler status"""
        return {
            "is_running": self.is_running,
            "enabled": self.config.get("enabled", True),
            "interval_minutes": self.config.get("analysis_interval_minutes", 20),
            "last_analysis_time": self.last_analysis_time.isoformat()
            if self.last_analysis_time
            else None,
            "analysis_count": self.analysis_count,
            "next_run_time": self.get_next_run_time(),
            "ollama_url": self.config.get("ollama_url", "http://localhost:11434"),
            "model_name": self.config.get("model_name", "mistral"),
        }

    def get_next_run_time(self) -> Optional[str]:
        """Get the next scheduled run time"""
        if self.scheduler and self.is_running:
            try:
                job = self.scheduler.get_job("ai_analysis")
                if job and job.next_run_time:
                    return job.next_run_time.isoformat()
            except Exception as e:
                print(f"[AI Scheduler] Error getting next run time: {e}")
        return None

    def update_config(self, new_config: Dict) -> bool:
        """Update configuration and restart scheduler if needed"""
        try:
            old_interval = self.config.get("analysis_interval_minutes", 20)
            old_enabled = self.config.get("enabled", True)

            # Update config
            self.config.update(new_config)

            # Save to file
            self.save_config()

            # Recreate analyzer with new config
            self.analyzer = ProductivityAnalyzer(self.config)

            # Check if we need to restart scheduler
            new_interval = self.config.get("analysis_interval_minutes", 20)
            new_enabled = self.config.get("enabled", True)

            if self.is_running and (
                old_interval != new_interval or old_enabled != new_enabled
            ):
                print(f"[AI Scheduler] Restarting scheduler due to config change")
                self.schedule_analysis()  # Reschedule with new interval

            print(f"[AI Scheduler] Configuration updated successfully")
            return True

        except Exception as e:
            print(f"[AI Scheduler] Error updating config: {e}")
            return False

    def run_analysis_now(self) -> Optional[Dict]:
        """Run analysis immediately (manual trigger)"""
        try:
            print(f"[AI Scheduler] Running manual analysis")
            return self.analyzer.run_analysis()
        except Exception as e:
            print(f"[AI Scheduler] Error in manual analysis: {e}")
            return None

    def test_ollama_connection(self) -> bool:
        """Test if Ollama is accessible"""
        try:
            import requests

            response = requests.get(
                f"{self.config.get('ollama_url', 'http://localhost:11434')}/api/tags",
                timeout=5,
            )
            return response.status_code == 200
        except Exception as e:
            print(f"[AI Scheduler] Ollama connection test failed: {e}")
            return False


# Global scheduler instance
_global_scheduler = None


def get_scheduler() -> AIAnalysisScheduler:
    """Get the global scheduler instance"""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = AIAnalysisScheduler()
    return _global_scheduler


def init_scheduler(config: Optional[Dict] = None) -> AIAnalysisScheduler:
    """Initialize the global scheduler"""
    global _global_scheduler
    _global_scheduler = AIAnalysisScheduler(config)
    return _global_scheduler


def start_scheduler() -> bool:
    """Start the global scheduler"""
    scheduler = get_scheduler()
    return scheduler.start()


def stop_scheduler() -> bool:
    """Stop the global scheduler"""
    scheduler = get_scheduler()
    return scheduler.stop()


if __name__ == "__main__":
    # Test the scheduler
    print("Testing AI Analysis Scheduler...")

    # Create scheduler
    scheduler = AIAnalysisScheduler()

    # Test Ollama connection
    print(f"Ollama connection: {'✅' if scheduler.test_ollama_connection() else '❌'}")

    # Show status
    status = scheduler.get_status()
    print(f"Status: {json.dumps(status, indent=2)}")

    # Run a single analysis
    print("\nRunning single analysis...")
    result = scheduler.run_analysis_now()
    if result:
        print("✅ Analysis successful")
    else:
        print("❌ Analysis failed")

    # Don't start scheduler in test mode
    print("\nTest completed (scheduler not started)")
