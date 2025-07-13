import win32gui
import win32con
import win32api
import tkinter as tk
import json
import time
import threading
from datetime import datetime
import os


class AdvancedSnapAlertWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_advanced_widget()
        self.setup_styling()
        self.create_widgets()
        self.start_updates()

    def setup_advanced_widget(self):
        """Configure advanced widget with Win32 API"""
        self.root.title("SnapAlert Advanced Widget")
        self.root.geometry("300x180+100+100")

        # Remove window decorations
        self.root.overrideredirect(True)

        # Set background
        self.root.configure(bg="#2d2d2d")

        # Get window handle after it's created
        self.root.update_idletasks()
        hwnd = int(self.root.wm_frame(), 16)

        # Advanced Win32 styling
        self.setup_win32_properties(hwnd)

    def setup_win32_properties(self, hwnd):
        """Apply advanced Win32 properties"""
        try:
            # Make it a tool window (doesn't appear in taskbar)
            extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            extended_style |= win32con.WS_EX_TOOLWINDOW
            extended_style |= win32con.WS_EX_LAYERED  # Enable layered window
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extended_style)

            # Set transparency
            win32gui.SetLayeredWindowAttributes(hwnd, 0, 230, win32con.LWA_ALPHA)

            # Keep on top but below other topmost windows
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0,
                0,
                0,
                0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
            )

        except Exception as e:
            print(f"Win32 setup error: {e}")

    def setup_styling(self):
        """Configure modern styling"""
        self.colors = {
            "bg": "#2d2d2d",
            "card": "#3d3d3d",
            "primary": "#00ff88",
            "secondary": "#ffffff",
            "accent": "#ff6b6b",
            "warning": "#ffd93d",
            "info": "#6bb6ff",
        }

        self.fonts = {
            "title": ("Segoe UI", 11, "bold"),
            "metric": ("Segoe UI", 9),
            "small": ("Segoe UI", 8),
            "tiny": ("Segoe UI", 7),
        }

    def create_widgets(self):
        """Create modern UI elements"""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # Header with gradient effect
        header_frame = tk.Frame(main_frame, bg=self.colors["card"], height=30)
        header_frame.pack(fill="x", pady=(0, 8))
        header_frame.pack_propagate(False)

        title = tk.Label(
            header_frame,
            text="🔺 SnapAlert Pro",
            font=self.fonts["title"],
            fg=self.colors["primary"],
            bg=self.colors["card"],
        )
        title.pack(side="left", padx=8, pady=6)

        # Status indicator
        self.status_indicator = tk.Label(
            header_frame,
            text="●",
            font=("Segoe UI", 12),
            fg=self.colors["primary"],
            bg=self.colors["card"],
        )
        self.status_indicator.pack(side="right", padx=8, pady=6)

        # Metrics grid
        metrics_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        metrics_frame.pack(fill="both", expand=True)

        # Row 1: Session and Keystrokes
        row1 = tk.Frame(metrics_frame, bg=self.colors["bg"])
        row1.pack(fill="x", pady=2)

        self.session_card = self.create_metric_card(row1, "Session", "0m", "left")
        self.keystrokes_card = self.create_metric_card(row1, "Keys", "0", "right")

        # Row 2: Current App
        row2 = tk.Frame(metrics_frame, bg=self.colors["bg"])
        row2.pack(fill="x", pady=2)

        self.current_app_card = self.create_wide_card(row2, "Current", "None")

        # Row 3: Apps and Alerts
        row3 = tk.Frame(metrics_frame, bg=self.colors["bg"])
        row3.pack(fill="x", pady=2)

        self.apps_card = self.create_metric_card(row3, "Apps", "0", "left")
        self.alerts_card = self.create_metric_card(row3, "Alerts", "0", "right")

        # Footer
        footer_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        footer_frame.pack(fill="x", pady=(8, 0))

        self.last_update_label = tk.Label(
            footer_frame,
            text="Last update: Never",
            font=self.fonts["tiny"],
            fg=self.colors["secondary"],
            bg=self.colors["bg"],
        )
        self.last_update_label.pack(side="left")

        # Close button
        close_btn = tk.Button(
            footer_frame,
            text="×",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["bg"],
            bd=0,
            command=self.close_widget,
            relief="flat",
        )
        close_btn.pack(side="right")

        # Make draggable
        self.make_draggable()

    def create_metric_card(self, parent, title, value, side):
        """Create a metric card"""
        card = tk.Frame(parent, bg=self.colors["card"], relief="flat", bd=1)
        card.pack(side=side, fill="both", expand=True, padx=2)

        title_label = tk.Label(
            card,
            text=title,
            font=self.fonts["small"],
            fg=self.colors["secondary"],
            bg=self.colors["card"],
        )
        title_label.pack(pady=(4, 0))

        value_label = tk.Label(
            card,
            text=value,
            font=self.fonts["metric"],
            fg=self.colors["primary"],
            bg=self.colors["card"],
        )
        value_label.pack(pady=(0, 4))

        return {"title": title_label, "value": value_label}

    def create_wide_card(self, parent, title, value):
        """Create a wide card"""
        card = tk.Frame(parent, bg=self.colors["card"], relief="flat", bd=1)
        card.pack(fill="x", padx=2, pady=1)

        title_label = tk.Label(
            card,
            text=title,
            font=self.fonts["small"],
            fg=self.colors["secondary"],
            bg=self.colors["card"],
        )
        title_label.pack(side="left", padx=8, pady=4)

        value_label = tk.Label(
            card,
            text=value,
            font=self.fonts["metric"],
            fg=self.colors["primary"],
            bg=self.colors["card"],
        )
        value_label.pack(side="right", padx=8, pady=4)

        return {"title": title_label, "value": value_label}

    def make_draggable(self):
        """Make the widget draggable"""

        def start_drag(event):
            self.root.x = event.x
            self.root.y = event.y

        def drag(event):
            x = self.root.winfo_pointerx() - self.root.x
            y = self.root.winfo_pointery() - self.root.y
            self.root.geometry(f"+{x}+{y}")

        self.root.bind("<Button-1>", start_drag)
        self.root.bind("<B1-Motion>", drag)

    def load_status_data(self):
        """Load current status from SnapAlert tracker"""
        try:
            if os.path.exists("data/status.json"):
                with open("data/status.json", "r") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading status: {e}")
            return {}

    def update_metrics(self):
        """Update widget with current metrics"""
        try:
            status = self.load_status_data()

            # Session time
            session_time = status.get("session_time", 0)
            if session_time > 3600:  # More than 1 hour
                hours = int(session_time // 3600)
                minutes = int((session_time % 3600) // 60)
                time_str = f"{hours}h {minutes}m"
            else:
                minutes = int(session_time // 60)
                seconds = int(session_time % 60)
                time_str = f"{minutes}m {seconds}s"
            self.session_card["value"].config(text=time_str)

            # Keystrokes
            keystrokes = status.get("keystrokes", 0)
            if keystrokes > 1000:
                k_str = f"{keystrokes / 1000:.1f}k"
            else:
                k_str = str(keystrokes)
            self.keystrokes_card["value"].config(text=k_str)

            # Current app
            current_app = status.get("current_app", "None")
            if current_app and len(current_app) > 15:
                current_app = current_app[:15] + "..."
            self.current_app_card["value"].config(text=current_app)

            # Open apps
            open_apps = status.get("open_apps", [])
            self.apps_card["value"].config(text=str(len(open_apps)))

            # Custom alerts
            custom_alerts = status.get("custom_alerts", [])
            enabled_alerts = [a for a in custom_alerts if a.get("enabled", True)]
            self.alerts_card["value"].config(text=str(len(enabled_alerts)))

            # Status indicator
            if status:
                self.status_indicator.config(fg=self.colors["primary"])
            else:
                self.status_indicator.config(fg=self.colors["accent"])

            # Last update
            self.last_update_label.config(
                text=f"Updated: {datetime.now().strftime('%H:%M:%S')}"
            )

        except Exception as e:
            print(f"Error updating metrics: {e}")
            self.status_indicator.config(fg=self.colors["accent"])

    def start_updates(self):
        """Start the update loop"""

        def update_loop():
            while True:
                try:
                    self.root.after(0, self.update_metrics)
                    time.sleep(1)  # Update every second
                except Exception as e:
                    print(f"Update loop error: {e}")
                    time.sleep(5)

        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()

    def close_widget(self):
        """Close the widget"""
        self.root.destroy()

    def run(self):
        """Start the widget"""
        print("🔺 SnapAlert Advanced Desktop Widget started")
        print("• Advanced Win32 integration")
        print("• Doesn't appear in taskbar")
        print("• Semi-transparent with modern styling")
        print("• Click and drag to move")
        self.root.mainloop()


if __name__ == "__main__":
    widget = AdvancedSnapAlertWidget()
    widget.run()
