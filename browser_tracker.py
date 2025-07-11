import time
import json
import os
import re
import sqlite3
import shutil
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import win32gui
import win32process
import psutil
import tempfile
from pathlib import Path

BROWSER_LOG_FILE = "data/browser_logs.json"
BROWSER_STATUS_FILE = "data/browser_status.json"

# Browser process names to track
BROWSER_PROCESSES = {
    "chrome.exe": "Chrome",
    "firefox.exe": "Firefox",
    "msedge.exe": "Edge",
    "opera.exe": "Opera",
    "brave.exe": "Brave",
}

# Search engines for query extraction
SEARCH_ENGINES = {
    "google.com": "q",
    "bing.com": "q",
    "duckduckgo.com": "q",
    "yahoo.com": "p",
    "yandex.com": "text",
}


class BrowserTracker:
    def __init__(self):
        self.active_tabs = {}
        self.browser_sessions = {}
        self.current_browser = None
        self.current_tab_start = time.time()
        self.browser_logs = []
        self.last_history_check = 0
        self.recent_urls = {}

        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)

        # Run startup diagnostics
        self.run_startup_diagnostics()

    def run_startup_diagnostics(self):
        """Run diagnostics to check browser accessibility"""
        print("[Browser Tracker] Running startup diagnostics...")

        # Check Chrome
        chrome_path = os.path.expanduser(
            "~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History"
        )
        chrome_available = os.path.exists(chrome_path)
        print(f"[Browser Tracker] Chrome history available: {chrome_available}")

        # Check Firefox
        firefox_dir = os.path.expanduser(
            "~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles"
        )
        firefox_available = os.path.exists(firefox_dir)
        if firefox_available:
            profiles = [
                d
                for d in os.listdir(firefox_dir)
                if d.endswith(".default") or d.endswith(".default-release")
            ]
            firefox_available = len(profiles) > 0
        print(f"[Browser Tracker] Firefox history available: {firefox_available}")

        # Check Edge
        edge_path = os.path.expanduser(
            "~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\History"
        )
        edge_available = os.path.exists(edge_path)
        print(f"[Browser Tracker] Edge history available: {edge_available}")

        if not any([chrome_available, firefox_available, edge_available]):
            print(
                "[Browser Tracker] WARNING: No browser history files found. Browser tracking may be limited."
            )
        else:
            print("[Browser Tracker] Browser tracking initialized successfully.")

    def get_chrome_history_urls(self, limit=20):
        """Get recent URLs from Chrome history"""
        try:
            # Chrome history location
            chrome_path = os.path.expanduser(
                "~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History"
            )

            if not os.path.exists(chrome_path):
                return []

            # Copy to temp file since Chrome locks the database
            temp_path = tempfile.mktemp()
            try:
                shutil.copy2(chrome_path, temp_path)

                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()

                # Get recent URLs with visit time
                query = """
                SELECT url, title, visit_time, visit_count
                FROM urls 
                WHERE visit_time > ? 
                ORDER BY visit_time DESC 
                LIMIT ?
                """

                # Chrome stores time as microseconds since Windows epoch (1601)
                # Convert to Unix timestamp
                hours_ago = int((time.time() - 3600) * 1000000) + 11644473600000000

                cursor.execute(query, (hours_ago, limit))
                results = cursor.fetchall()

                urls = []
                for url, title, visit_time, visit_count in results:
                    # Convert Chrome time to Unix timestamp
                    unix_time = (visit_time - 11644473600000000) / 1000000
                    urls.append(
                        {
                            "url": url,
                            "title": title or url,
                            "timestamp": unix_time,
                            "visit_count": visit_count,
                        }
                    )

                conn.close()
                return urls

            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            print(f"Error reading Chrome history: {e}")
            return []

    def get_firefox_history_urls(self, limit=20):
        """Get recent URLs from Firefox history"""
        try:
            # Firefox profile directory
            firefox_dir = os.path.expanduser(
                "~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles"
            )

            if not os.path.exists(firefox_dir):
                return []

            # Find the default profile
            profiles = [
                d
                for d in os.listdir(firefox_dir)
                if d.endswith(".default") or d.endswith(".default-release")
            ]
            if not profiles:
                return []

            history_path = os.path.join(firefox_dir, profiles[0], "places.sqlite")

            if not os.path.exists(history_path):
                return []

            # Copy to temp file
            temp_path = tempfile.mktemp()
            try:
                shutil.copy2(history_path, temp_path)

                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()

                query = """
                SELECT p.url, p.title, h.visit_date, p.visit_count
                FROM moz_places p
                JOIN moz_historyvisits h ON p.id = h.place_id
                WHERE h.visit_date > ?
                ORDER BY h.visit_date DESC
                LIMIT ?
                """

                # Firefox stores time as microseconds since Unix epoch
                hours_ago = int((time.time() - 3600) * 1000000)

                cursor.execute(query, (hours_ago, limit))
                results = cursor.fetchall()

                urls = []
                for url, title, visit_date, visit_count in results:
                    unix_time = visit_date / 1000000  # Convert to seconds
                    urls.append(
                        {
                            "url": url,
                            "title": title or url,
                            "timestamp": unix_time,
                            "visit_count": visit_count,
                        }
                    )

                conn.close()
                return urls

            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            print(f"Error reading Firefox history: {e}")
            return []

    def get_edge_history_urls(self, limit=20):
        """Get recent URLs from Edge history"""
        try:
            edge_path = os.path.expanduser(
                "~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\History"
            )

            if not os.path.exists(edge_path):
                return []

            # Copy to temp file since Edge locks the database
            temp_path = tempfile.mktemp()
            try:
                shutil.copy2(edge_path, temp_path)

                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()

                query = """
                SELECT url, title, visit_time, visit_count
                FROM urls 
                WHERE visit_time > ? 
                ORDER BY visit_time DESC 
                LIMIT ?
                """

                hours_ago = int((time.time() - 3600) * 1000000) + 11644473600000000

                cursor.execute(query, (hours_ago, limit))
                results = cursor.fetchall()

                urls = []
                for url, title, visit_time, visit_count in results:
                    unix_time = (visit_time - 11644473600000000) / 1000000
                    urls.append(
                        {
                            "url": url,
                            "title": title or url,
                            "timestamp": unix_time,
                            "visit_count": visit_count,
                        }
                    )

                conn.close()
                return urls

            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            print(f"Error reading Edge history: {e}")
            return []

    def extract_search_query(self, url):
        """Extract search query from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            for search_domain, param in SEARCH_ENGINES.items():
                if search_domain in domain:
                    query_params = parse_qs(parsed.query)
                    if param in query_params:
                        return query_params[param][0]
            return None
        except:
            return None

    def categorize_website(self, url):
        """Categorize website by URL"""
        if not url:
            return "unknown"

        url_lower = url.lower()

        # Productivity sites
        if any(
            site in url_lower
            for site in ["github.com", "stackoverflow.com", "docs.", "documentation"]
        ):
            return "productive"

        # Social media
        if any(
            site in url_lower
            for site in [
                "facebook.com",
                "twitter.com",
                "instagram.com",
                "linkedin.com",
                "reddit.com",
            ]
        ):
            return "social"

        # Entertainment
        if any(
            site in url_lower
            for site in ["youtube.com", "netflix.com", "twitch.tv", "spotify.com"]
        ):
            return "entertainment"

        # News
        if any(
            site in url_lower for site in ["news.", "cnn.com", "bbc.com", "reuters.com"]
        ):
            return "news"

        # Shopping
        if any(
            site in url_lower for site in ["amazon.com", "ebay.com", "shop", "store"]
        ):
            return "shopping"

        return "general"

    def get_chrome_current_tab(self):
        """Get current Chrome tab URL and title (simplified approach)"""
        try:
            # This is a simplified approach - in a real implementation,
            # we'd need to use browser automation or extensions
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)

            if "Chrome" in title:
                # Extract URL from title if possible (Chrome shows URL in title)
                # This is a basic approach - real implementation would need browser API
                return {
                    "title": title,
                    "url": self.extract_url_from_title(title),
                    "timestamp": time.time(),
                }
        except:
            pass
        return None

    def extract_url_from_title(self, title):
        """Extract URL from browser window title (basic approach)"""
        # This is a simplified approach - real implementation would access browser APIs
        if " - " in title:
            # Many browsers show "Page Title - Browser Name"
            parts = title.split(" - ")
            if len(parts) >= 2:
                return parts[0]  # Use page title as URL placeholder
        return title

    def get_browser_windows(self):
        """Get all browser windows"""
        browser_windows = []

        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc = psutil.Process(pid)
                    process_name = proc.name()

                    if process_name in BROWSER_PROCESSES:
                        title = win32gui.GetWindowText(hwnd)
                        if title:  # Only include windows with titles
                            browser_windows.append(
                                {
                                    "process": process_name,
                                    "browser": BROWSER_PROCESSES[process_name],
                                    "title": title,
                                    "hwnd": hwnd,
                                    "pid": pid,
                                }
                            )
                except:
                    pass

        win32gui.EnumWindows(callback, None)
        return browser_windows

    def update_browser_history_data(self):
        """Update browser data from history files"""
        current_time = time.time()

        # Only check history every 30 seconds to avoid performance issues
        if current_time - self.last_history_check < 30:
            return

        self.last_history_check = current_time

        # Get recent URLs from all browsers
        all_recent_urls = []

        # Chrome
        chrome_urls = self.get_chrome_history_urls(50)
        for url_data in chrome_urls:
            url_data["browser"] = "Chrome"
            all_recent_urls.append(url_data)

        # Firefox
        firefox_urls = self.get_firefox_history_urls(50)
        for url_data in firefox_urls:
            url_data["browser"] = "Firefox"
            all_recent_urls.append(url_data)

        # Edge
        edge_urls = self.get_edge_history_urls(50)
        for url_data in edge_urls:
            url_data["browser"] = "Edge"
            all_recent_urls.append(url_data)

        # Sort by timestamp (most recent first)
        all_recent_urls.sort(key=lambda x: x["timestamp"], reverse=True)

        # Update recent URLs cache
        self.recent_urls = {}
        for url_data in all_recent_urls[:30]:  # Keep top 30 most recent
            url_key = f"{url_data['browser']}_{url_data['url']}"
            self.recent_urls[url_key] = url_data

    def track_browser_activity(self):
        """Main browser tracking function"""
        browser_windows = self.get_browser_windows()
        current_time = time.time()

        # Update browser history data periodically
        self.update_browser_history_data()

        # Get currently active browser
        active_browser = None
        hwnd = win32gui.GetForegroundWindow()

        for browser in browser_windows:
            if browser["hwnd"] == hwnd:
                active_browser = browser
                break

        # Process all browser windows to create comprehensive tab list
        for browser in browser_windows:
            browser_name = browser["browser"]
            title = browser["title"]

            # Try to find matching URL from recent history
            matching_url_data = None
            for url_key, url_data in self.recent_urls.items():
                if url_data["browser"] == browser_name and (
                    url_data["title"] in title or title in url_data["title"]
                ):
                    matching_url_data = url_data
                    break

            if matching_url_data:
                url = matching_url_data["url"]
                page_title = matching_url_data["title"]
            else:
                # Fallback to title extraction
                url = self.extract_url_from_title(title)
                page_title = title

            search_query = self.extract_search_query(url)
            category = self.categorize_website(url)

            # Track tab activity
            tab_key = f"{browser_name}_{title}"
            is_active = browser["hwnd"] == hwnd

            if tab_key not in self.active_tabs:
                self.active_tabs[tab_key] = {
                    "browser": browser_name,
                    "title": page_title,
                    "window_title": title,
                    "url": url,
                    "category": category,
                    "start_time": current_time,
                    "last_active": current_time if is_active else current_time - 60,
                    "total_time": 0,
                    "search_query": search_query,
                    "is_active": is_active,
                    "visit_count": matching_url_data.get("visit_count", 1)
                    if matching_url_data
                    else 1,
                }
            else:
                # Update existing tab
                if is_active:
                    self.active_tabs[tab_key]["last_active"] = current_time
                self.active_tabs[tab_key]["total_time"] = (
                    current_time - self.active_tabs[tab_key]["start_time"]
                )
                self.active_tabs[tab_key]["is_active"] = is_active

                # Update URL if we found a better match
                if matching_url_data and url != self.active_tabs[tab_key]["url"]:
                    self.active_tabs[tab_key]["url"] = url
                    self.active_tabs[tab_key]["title"] = page_title
                    self.active_tabs[tab_key]["category"] = category
                    self.active_tabs[tab_key]["search_query"] = search_query

            # Update current browser if this is the active window
            if is_active:
                self.current_browser = tab_key
                self.current_tab_start = current_time

        # Clean up inactive tabs (remove tabs not seen for 5 minutes)
        inactive_tabs = []
        for tab_key, tab_data in self.active_tabs.items():
            if current_time - tab_data["last_active"] > 300:  # 5 minutes
                inactive_tabs.append(tab_key)

        for tab_key in inactive_tabs:
            # Log the closed tab
            self.browser_logs.append(
                {
                    "action": "tab_closed",
                    "timestamp": datetime.now().isoformat(),
                    "tab_data": self.active_tabs[tab_key],
                }
            )
            del self.active_tabs[tab_key]

        return {
            "active_tabs": self.active_tabs,
            "browser_windows": browser_windows,
            "current_browser": self.current_browser,
            "total_tabs": len(self.active_tabs),
            "recent_urls_count": len(self.recent_urls),
        }

    def get_browser_stats(self):
        """Get browser statistics"""
        stats = {
            "total_tabs": len(self.active_tabs),
            "active_browsers": list(
                set([tab["browser"] for tab in self.active_tabs.values()])
            ),
            "categories": {},
            "search_queries": [],
            "most_active_tab": None,
            "browser_distribution": {},
        }

        if self.active_tabs:
            # Category distribution
            for tab in self.active_tabs.values():
                category = tab["category"]
                if category not in stats["categories"]:
                    stats["categories"][category] = 0
                stats["categories"][category] += 1

            # Search queries
            for tab in self.active_tabs.values():
                if tab["search_query"]:
                    stats["search_queries"].append(
                        {"query": tab["search_query"], "timestamp": tab["start_time"]}
                    )

            # Most active tab
            most_active = max(self.active_tabs.values(), key=lambda x: x["total_time"])
            stats["most_active_tab"] = most_active

            # Browser distribution
            for tab in self.active_tabs.values():
                browser = tab["browser"]
                if browser not in stats["browser_distribution"]:
                    stats["browser_distribution"][browser] = 0
                stats["browser_distribution"][browser] += 1

        return stats

    def save_browser_status(self):
        """Save current browser status to file"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "active_tabs": self.active_tabs,
            "current_browser": self.current_browser,
            "stats": self.get_browser_stats(),
        }

        with open(BROWSER_STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)

    def save_browser_logs(self):
        """Save browser logs to file"""
        if self.browser_logs:
            with open(BROWSER_LOG_FILE, "a") as f:
                for log in self.browser_logs:
                    f.write(json.dumps(log) + "\n")
            self.browser_logs.clear()


# Global browser tracker instance
browser_tracker = BrowserTracker()


def get_browser_status():
    """Get current browser status"""
    try:
        if os.path.exists(BROWSER_STATUS_FILE):
            with open(BROWSER_STATUS_FILE, "r") as f:
                return json.load(f)
        return {}
    except:
        return {}


def update_browser_tracking():
    """Update browser tracking data"""
    global browser_tracker
    activity = browser_tracker.track_browser_activity()
    browser_tracker.save_browser_status()
    browser_tracker.save_browser_logs()
    return activity
