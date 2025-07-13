import tkinter as tk
from tkinter import ttk
import json
import time
import threading
from datetime import datetime
import os
import sys


class SnapAlertWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_styling()
        self.setup_widget()
        self.load_field_config()
        self.create_widgets()
        self.start_updates()

    def setup_widget(self):
        """Configure the widget window with Apple-style design"""
        self.root.title("SnapAlert Widget")
        self.root.geometry("360x500+100+100")  # Increased height for scrolling

        # Make it stay on top
        self.root.attributes("-topmost", True)

        # Perfect opacity for Apple-style glass effect
        self.root.attributes("-alpha", 0.96)

        # Remove window decorations for clean look
        self.root.overrideredirect(True)

        # Set clean background
        self.root.configure(bg=self.colors["bg"])

        # Add customization options
        self.position_x = 100
        self.position_y = 100
        self.opacity = 0.96
        self.always_on_top = True

    def load_field_config(self):
        """Load field configuration from file or set defaults"""
        self.field_config = {
            "session_time": {
                "enabled": True,
                "name": "Session Time",
                "icon": "⏱",
                "color": "primary",
            },
            "keystrokes": {
                "enabled": True,
                "name": "Keystrokes",
                "icon": "⌨",
                "color": "success",
            },
            "current_app": {
                "enabled": True,
                "name": "Current App",
                "icon": "🖥",
                "color": "accent",
            },
            "open_apps": {
                "enabled": True,
                "name": "Open Apps",
                "icon": "📱",
                "color": "warning",
            },
            "alerts": {
                "enabled": True,
                "name": "Alerts",
                "icon": "🔔",
                "color": "secondary_text",
            },
            "browser_tabs": {
                "enabled": True,
                "name": "Browser Tabs",
                "icon": "🌐",
                "color": "accent",
            },
            "cpu_usage": {
                "enabled": False,
                "name": "CPU Usage",
                "icon": "⚡",
                "color": "warning",
            },
            "memory_usage": {
                "enabled": False,
                "name": "Memory Usage",
                "icon": "💾",
                "color": "error",
            },
        }

        # Try to load from config file
        try:
            config_file = "widget_config.json"
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    saved_config = json.load(f)
                    self.field_config.update(saved_config)
                    print("✅ Loaded field configuration")
        except Exception as e:
            print(f"⚠️  Could not load field config: {e}")

    def save_field_config(self):
        """Save field configuration to file"""
        try:
            with open("widget_config.json", "w") as f:
                json.dump(self.field_config, f, indent=2)
                print("✅ Saved field configuration")
        except Exception as e:
            print(f"❌ Error saving field config: {e}")

    def setup_styling(self):
        """Configure Apple-inspired colors and fonts"""
        self.colors = {
            # Apple-style background hierarchy
            "bg": "#f8f8f8",
            "card_bg": "#ffffff",
            "inner_bg": "#fafafa",
            "secondary_bg": "#f5f5f5",
            "transparent": "#f0f0f0",
            # Apple-style text colors
            "primary_text": "#1d1d1f",
            "secondary_text": "#86868b",
            "accent_text": "#007aff",
            "success_text": "#30d158",
            "warning_text": "#ff9500",
            "error_text": "#ff3b30",
            # Apple-style accent colors
            "primary": "#007aff",
            "primary_dark": "#0056cc",
            "secondary": "#1d1d1f",
            "accent": "#007aff",
            "accent_light": "#4da6ff",
            "success": "#30d158",
            "warning": "#ff9500",
            "error": "#ff3b30",
            # Apple-style borders and shadows
            "border": "#d2d2d7",
            "border_light": "#e5e5e7",
            "shadow": "#e8e8e8",
            "shadow_dark": "#d0d0d0",
            # Apple-style interactive elements
            "button_bg": "#007aff",
            "button_hover": "#0056cc",
            "button_text": "#ffffff",
            "card_hover": "#f0f0f5",
        }

        # Apple-style typography (SF Pro Display inspired)
        self.fonts = {
            "title": ("SF Pro Display", 18, "bold")
            if self._font_exists("SF Pro Display")
            else ("Segoe UI", 18, "bold"),
            "subtitle": ("SF Pro Display", 14, "normal")
            if self._font_exists("SF Pro Display")
            else ("Segoe UI", 14, "normal"),
            "body": ("SF Pro Text", 13, "normal")
            if self._font_exists("SF Pro Text")
            else ("Segoe UI", 13, "normal"),
            "caption": ("SF Pro Text", 11, "normal")
            if self._font_exists("SF Pro Text")
            else ("Segoe UI", 11, "normal"),
            "small": ("SF Pro Text", 10, "normal")
            if self._font_exists("SF Pro Text")
            else ("Segoe UI", 10, "normal"),
            "mono": ("SF Mono", 12, "normal")
            if self._font_exists("SF Mono")
            else ("Consolas", 12, "normal"),
        }

    def _font_exists(self, font_name):
        """Check if a font exists on the system"""
        try:
            import tkinter.font as tkFont

            return font_name in tkFont.families()
        except:
            return False

    def create_widgets(self):
        """Create the widget UI elements with Apple-style design"""
        # Main container with Apple-style shadow effect
        main_container = tk.Frame(
            self.root, bg=self.colors["shadow"], relief="flat", bd=0
        )
        main_container.pack(fill="both", expand=True, padx=4, pady=4)

        # Card container with rounded corners effect
        card_container = tk.Frame(
            main_container, bg=self.colors["card_bg"], relief="flat", bd=0
        )
        card_container.pack(fill="both", expand=True, padx=2, pady=2)

        # Header/title bar (draggable area) - Apple style
        self.header = tk.Frame(
            card_container, bg=self.colors["card_bg"], height=50, relief="flat", bd=0
        )
        self.header.pack(fill="x", padx=20, pady=(20, 0))
        self.header.pack_propagate(False)

        # Title area (draggable)
        title_frame = tk.Frame(self.header, bg=self.colors["card_bg"])
        title_frame.pack(fill="both", expand=True, pady=10)

        self.title = tk.Label(
            title_frame,
            text="SnapAlert",
            font=self.fonts["title"],
            fg=self.colors["primary_text"],
            bg=self.colors["card_bg"],
        )
        self.title.pack(side="left", anchor="w")

        # Control buttons (Apple-style)
        controls_frame = tk.Frame(title_frame, bg=self.colors["card_bg"])
        controls_frame.pack(side="right", anchor="e")

        # Settings button - Apple style
        self.settings_btn = tk.Button(
            controls_frame,
            text="⚙",
            font=("Segoe UI", 14),
            fg=self.colors["secondary_text"],
            bg=self.colors["card_bg"],
            bd=0,
            command=self.show_settings,
            cursor="hand2",
            relief="flat",
            padx=10,
            pady=6,
            activebackground=self.colors["card_hover"],
            activeforeground=self.colors["primary"],
        )
        self.settings_btn.pack(side="left", padx=2)

        # Close button - Apple style
        self.close_btn = tk.Button(
            controls_frame,
            text="×",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors["secondary_text"],
            bg=self.colors["card_bg"],
            bd=0,
            command=self.close_widget,
            cursor="hand2",
            relief="flat",
            padx=10,
            pady=6,
            activebackground=self.colors["card_hover"],
            activeforeground=self.colors["error"],
        )
        self.close_btn.pack(side="left", padx=2)

        # Scrollable metrics container
        canvas = tk.Canvas(
            card_container,
            bg=self.colors["inner_bg"],
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        scrollbar = ttk.Scrollbar(
            card_container, orient="vertical", command=canvas.yview
        )
        scrollable_frame = tk.Frame(canvas, bg=self.colors["inner_bg"])

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y", pady=20)

        # Metrics container
        metrics_container = tk.Frame(
            scrollable_frame, bg=self.colors["inner_bg"], relief="flat", bd=0
        )
        metrics_container.pack(fill="both", expand=True, padx=0, pady=0)

        # Store metric labels for updates
        self.metric_labels = {}

        # Create cards based on configuration
        self.create_dynamic_metrics(metrics_container)

        # Bind mouse wheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Status indicator at bottom - Apple style
        status_container = tk.Frame(
            card_container, bg=self.colors["secondary_bg"], relief="flat", bd=0
        )
        status_container.pack(fill="x", padx=20, pady=(0, 20))

        status_inner = tk.Frame(status_container, bg=self.colors["secondary_bg"])
        status_inner.pack(fill="both", expand=True, padx=15, pady=8)

        self.status_dot = tk.Label(
            status_inner,
            text="●",
            font=("Segoe UI", 12),
            fg=self.colors["success"],
            bg=self.colors["secondary_bg"],
        )
        self.status_dot.pack(side="left", padx=(0, 5))

        self.status_label = tk.Label(
            status_inner,
            text="Live",
            font=self.fonts["caption"],
            fg=self.colors["secondary_text"],
            bg=self.colors["secondary_bg"],
        )
        self.status_label.pack(side="left")

        # Make only the title bar draggable
        self.make_draggable()

    def create_metric_card(self, parent, title, value, accent_color, icon):
        """Create an Apple-style metric card"""
        card = tk.Frame(parent, bg=self.colors["card_bg"], relief="flat", bd=0)

        # Card content frame
        content_frame = tk.Frame(card, bg=self.colors["card_bg"])
        content_frame.pack(fill="both", expand=True, padx=16, pady=12)

        # Icon and title row
        header_frame = tk.Frame(content_frame, bg=self.colors["card_bg"])
        header_frame.pack(fill="x", pady=(0, 4))

        # Icon
        icon_label = tk.Label(
            header_frame,
            text=icon,
            font=("Segoe UI", 16),
            fg=accent_color,
            bg=self.colors["card_bg"],
        )
        icon_label.pack(side="left", padx=(0, 8))

        # Title
        title_label = tk.Label(
            header_frame,
            text=title,
            font=self.fonts["caption"],
            fg=self.colors["secondary_text"],
            bg=self.colors["card_bg"],
        )
        title_label.pack(side="left", anchor="w")

        # Value
        value_label = tk.Label(
            content_frame,
            text=value,
            font=self.fonts["subtitle"],
            fg=self.colors["primary_text"],
            bg=self.colors["card_bg"],
        )
        value_label.pack(anchor="w", pady=(0, 2))

        return card, value_label

    def create_dynamic_metrics(self, parent):
        """Create metric cards based on field configuration"""
        enabled_fields = {k: v for k, v in self.field_config.items() if v["enabled"]}

        for field_key, field_config in enabled_fields.items():
            card, label = self.create_metric_card(
                parent,
                field_config["name"],
                self.get_default_value(field_key),
                self.colors[field_config["color"]],
                field_config["icon"],
            )
            card.pack(fill="x", pady=(0, 12))
            self.metric_labels[field_key] = label

    def get_default_value(self, field_key):
        """Get default display value for a field"""
        defaults = {
            "session_time": "0m 0s",
            "keystrokes": "0",
            "current_app": "None",
            "open_apps": "0",
            "alerts": "Monitoring",
            "browser_tabs": "0",
            "cpu_usage": "0%",
            "memory_usage": "0%",
        }
        return defaults.get(field_key, "N/A")

    def make_draggable(self):
        """Make only the title bar draggable"""

        def start_drag(event):
            self.root.x = event.x
            self.root.y = event.y

        def drag(event):
            x = self.root.winfo_pointerx() - self.root.x
            y = self.root.winfo_pointery() - self.root.y
            self.root.geometry(f"+{x}+{y}")

        # Only bind dragging to the title bar and title label
        self.header.bind("<Button-1>", start_drag)
        self.header.bind("<B1-Motion>", drag)
        self.title.bind("<Button-1>", start_drag)
        self.title.bind("<B1-Motion>", drag)

    def load_status_data(self):
        """Load current status from SnapAlert tracker"""
        try:
            # Check in current directory first, then parent directory
            status_files = [
                "data/status.json",
                "../data/status.json",
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "data", "status.json"
                ),
            ]

            for status_file in status_files:
                if os.path.exists(status_file):
                    with open(status_file, "r") as f:
                        data = json.load(f)
                        print(f"✅ Loaded status from: {status_file}")
                        return data

            print("⚠️  No status.json found in any location")
            return {}
        except Exception as e:
            print(f"❌ Error loading status: {e}")
            return {}

    def update_metrics(self):
        """Update widget with current metrics"""
        try:
            status = self.load_status_data()

            # Session time with better formatting
            session_time = status.get("session_time", 0)
            if session_time > 3600:  # More than 1 hour
                hours = int(session_time // 3600)
                minutes = int((session_time % 3600) // 60)
                time_str = f"{hours}h {minutes}m"
            else:
                minutes = int(session_time // 60)
                seconds = int(session_time % 60)
                time_str = f"{minutes}m {seconds}s"
            # Update each enabled field dynamically
            for field_key, label in self.metric_labels.items():
                if field_key == "session_time":
                    label.config(text=time_str)

                elif field_key == "keystrokes":
                    keystrokes = status.get("keystrokes", 0)
                    if keystrokes > 1000:
                        k_str = f"{keystrokes / 1000:.1f}k"
                    else:
                        k_str = f"{keystrokes:,}"
                    label.config(text=k_str)

                elif field_key == "current_app":
                    current_app = status.get("current_app", "None")
                    if current_app and len(current_app) > 20:
                        current_app = current_app[:20] + "..."
                    label.config(text=current_app)

                elif field_key == "open_apps":
                    open_apps = status.get("open_apps", [])
                    label.config(text=f"{len(open_apps)} active")

                elif field_key == "alerts":
                    custom_alerts = status.get("custom_alerts", [])
                    enabled_alerts = [
                        a for a in custom_alerts if a.get("enabled", True)
                    ]
                    alert_count = len(enabled_alerts)
                    if alert_count > 0:
                        label.config(text=f"{alert_count} active")
                    else:
                        label.config(text="None active")

                elif field_key == "browser_tabs":
                    browser_data = status.get("browser_data", {})
                    stats = browser_data.get("stats", {})
                    tab_count = stats.get("total_tabs", 0)
                    label.config(text=f"{tab_count} tabs")

                elif field_key == "cpu_usage":
                    # Basic CPU usage (would need psutil for real data)
                    import random

                    cpu_usage = random.randint(10, 80)  # Placeholder
                    label.config(text=f"{cpu_usage}%")

                elif field_key == "memory_usage":
                    # Basic memory usage (would need psutil for real data)
                    import random

                    mem_usage = random.randint(30, 90)  # Placeholder
                    label.config(text=f"{mem_usage}%")

            # Animate status dot
            if status:
                # Pulse animation for live status
                current_color = self.status_dot.cget("fg")
                if current_color == self.colors["success"]:
                    self.status_dot.config(fg=self.colors["accent"])
                else:
                    self.status_dot.config(fg=self.colors["success"])

                self.status_label.config(text="Live", fg=self.colors["secondary_text"])
            else:
                self.status_dot.config(fg=self.colors["secondary_text"])
                self.status_label.config(
                    text="Offline", fg=self.colors["secondary_text"]
                )

        except Exception as e:
            print(f"❌ Error updating metrics: {e}")
            self.status_dot.config(fg=self.colors["error"])
            self.status_label.config(text="Error", fg=self.colors["error_text"])

    def start_updates(self):
        """Start the update loop"""

        def update_loop():
            while True:
                try:
                    self.root.after(0, self.update_metrics)
                    time.sleep(2)  # Update every 2 seconds
                except Exception as e:
                    print(f"Update loop error: {e}")
                    time.sleep(5)

        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()

    def show_settings(self):
        """Show widget settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("SnapAlert Settings")
        settings_window.geometry("450x550")
        settings_window.configure(bg=self.colors["bg"])
        settings_window.transient(self.root)
        settings_window.grab_set()

        # Center the settings window
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (
            settings_window.winfo_width() // 2
        )
        y = (settings_window.winfo_screenheight() // 2) - (
            settings_window.winfo_height() // 2
        )
        settings_window.geometry(f"+{x}+{y}")

        # Main container with Apple-style design
        main_container = tk.Frame(
            settings_window, bg=self.colors["card_bg"], relief="flat", bd=0
        )
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header_frame = tk.Frame(main_container, bg=self.colors["card_bg"])
        header_frame.pack(fill="x", pady=(0, 20))

        tk.Label(
            header_frame,
            text="SnapAlert Settings",
            font=self.fonts["title"],
            fg=self.colors["primary_text"],
            bg=self.colors["card_bg"],
        ).pack(pady=10)

        # Settings content
        content_frame = tk.Frame(main_container, bg=self.colors["card_bg"])
        content_frame.pack(fill="both", expand=True, pady=20)

        # Opacity setting
        tk.Label(
            content_frame,
            text="Opacity",
            font=self.fonts["subtitle"],
            fg=self.colors["primary_text"],
            bg=self.colors["card_bg"],
        ).pack(anchor="w", pady=(0, 8))

        opacity_var = tk.DoubleVar(value=self.opacity)
        opacity_scale = tk.Scale(
            content_frame,
            from_=0.3,
            to=1.0,
            orient="horizontal",
            resolution=0.05,
            variable=opacity_var,
            command=lambda v: self.root.attributes("-alpha", float(v)),
            bg=self.colors["card_bg"],
            fg=self.colors["primary_text"],
            highlightbackground=self.colors["primary"],
            activebackground=self.colors["primary"],
            troughcolor=self.colors["secondary_bg"],
            length=300,
            font=self.fonts["body"],
        )
        opacity_scale.pack(fill="x", pady=(0, 20))

        # Always on top toggle
        always_on_top_var = tk.BooleanVar(value=self.always_on_top)
        always_on_top_check = tk.Checkbutton(
            content_frame,
            text="Always stay on top",
            variable=always_on_top_var,
            font=self.fonts["body"],
            fg=self.colors["primary_text"],
            bg=self.colors["card_bg"],
            selectcolor=self.colors["primary"],
            activebackground=self.colors["card_bg"],
            activeforeground=self.colors["primary_text"],
            command=lambda: self.root.attributes("-topmost", always_on_top_var.get()),
        )
        always_on_top_check.pack(anchor="w", pady=(0, 20))

        # Field selection
        tk.Label(
            content_frame,
            text="Display Fields",
            font=self.fonts["subtitle"],
            fg=self.colors["primary_text"],
            bg=self.colors["card_bg"],
        ).pack(anchor="w", pady=(0, 8))

        # Create field checkboxes
        field_vars = {}
        fields_frame = tk.Frame(content_frame, bg=self.colors["card_bg"])
        fields_frame.pack(fill="x", pady=(0, 20))

        for field_key, field_config in self.field_config.items():
            field_vars[field_key] = tk.BooleanVar(value=field_config["enabled"])
            check = tk.Checkbutton(
                fields_frame,
                text=f"{field_config['icon']} {field_config['name']}",
                variable=field_vars[field_key],
                font=self.fonts["caption"],
                fg=self.colors["primary_text"],
                bg=self.colors["card_bg"],
                selectcolor=self.colors["primary"],
                activebackground=self.colors["card_bg"],
                activeforeground=self.colors["primary_text"],
            )
            check.pack(anchor="w", pady=2)

        # Buttons
        button_frame = tk.Frame(main_container, bg=self.colors["card_bg"])
        button_frame.pack(fill="x", pady=20)

        # Save button - Apple style
        save_btn = tk.Button(
            button_frame,
            text="Save Changes",
            font=self.fonts["body"],
            bg=self.colors["primary"],
            fg=self.colors["button_text"],
            padx=25,
            pady=12,
            relief="flat",
            cursor="hand2",
            activebackground=self.colors["primary_dark"],
            activeforeground=self.colors["button_text"],
            command=lambda: self.save_settings(
                opacity_var.get(), always_on_top_var.get(), field_vars, settings_window
            ),
        )
        save_btn.pack(side="left", padx=5)

        # Cancel button - Apple style
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            font=self.fonts["body"],
            bg=self.colors["secondary_bg"],
            fg=self.colors["secondary_text"],
            padx=25,
            pady=12,
            relief="flat",
            cursor="hand2",
            activebackground=self.colors["border"],
            activeforeground=self.colors["secondary_text"],
            command=settings_window.destroy,
        )
        cancel_btn.pack(side="right", padx=5)

    def save_settings(self, opacity, always_on_top, field_vars, settings_window):
        """Save widget settings"""
        self.opacity = opacity
        self.always_on_top = always_on_top
        self.root.attributes("-alpha", opacity)
        self.root.attributes("-topmost", always_on_top)

        # Update field configuration
        fields_changed = False
        for field_key, var in field_vars.items():
            new_enabled = var.get()
            if self.field_config[field_key]["enabled"] != new_enabled:
                self.field_config[field_key]["enabled"] = new_enabled
                fields_changed = True

        if fields_changed:
            self.save_field_config()
            self.recreate_widget()

        settings_window.destroy()
        print(
            f"✅ Settings saved: opacity={opacity}, always_on_top={always_on_top}, fields_changed={fields_changed}"
        )

    def recreate_widget(self):
        """Recreate the widget with new field configuration"""
        # Destroy all children of the main widget
        for widget in self.root.winfo_children():
            widget.destroy()

        # Recreate the widget
        self.create_widgets()
        print("🔄 Widget recreated with new field configuration")

    def close_widget(self):
        """Close the widget"""
        self.root.destroy()

    def run(self):
        """Start the widget"""
        print("SnapAlert Desktop Widget - Apple Design Edition")
        print("• Cutting-edge Apple-style design")
        print("• Scrollable metrics with mouse wheel support")
        print("• Customizable field selection")
        print("• Drag the title bar to move")
        print("• Click ⚙ for settings and field customization")
        print("• Click × to close")
        print("• Professional card-based layout")
        self.root.mainloop()


if __name__ == "__main__":
    widget = SnapAlertWidget()
    widget.run()
