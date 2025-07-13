#!/usr/bin/env python3
"""
SnapAlert App ID Registration
Automatically registers SnapAlert with Windows for proper notification branding
"""

import os
import sys
import subprocess
import winreg
from pathlib import Path


def get_app_paths():
    """Get paths for SnapAlert app registration"""
    script_dir = Path(__file__).parent.absolute()

    # Find icon path
    icon_path = script_dir / "icons" / "snapalert.ico"
    if not icon_path.exists():
        # Try to find any .ico file in icons directory
        icons_dir = script_dir / "icons"
        if icons_dir.exists():
            ico_files = list(icons_dir.glob("*.ico"))
            if ico_files:
                icon_path = ico_files[0]
            else:
                icon_path = None
        else:
            icon_path = None

    # App executable (Python script)
    app_path = script_dir / "app.py"

    return {
        "script_dir": str(script_dir),
        "icon_path": str(icon_path) if icon_path and icon_path.exists() else None,
        "app_path": str(app_path),
        "app_id": "SnapAlert.ProductivityMonitor",
    }


def register_app_id():
    """Register SnapAlert app ID with Windows"""
    paths = get_app_paths()
    app_id = paths["app_id"]

    try:
        # Create registry key for the app
        key_path = f"SOFTWARE\\Classes\\AppUserModelId\\{app_id}"

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            # Set display name
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "SnapAlert")

            # Set icon path if available
            if paths["icon_path"]:
                winreg.SetValueEx(key, "IconUri", 0, winreg.REG_SZ, paths["icon_path"])
                winreg.SetValueEx(
                    key, "IconBackgroundColor", 0, winreg.REG_SZ, "#E31E24"
                )

            # Set other properties
            winreg.SetValueEx(key, "ShowInSettings", 0, winreg.REG_DWORD, 1)

        print(f"✅ Successfully registered app ID: {app_id}")

        # Also register under Start Menu for shortcuts
        start_menu_key = f"SOFTWARE\\Classes\\AppUserModelId\\{app_id}\\Application"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, start_menu_key) as key:
            winreg.SetValueEx(
                key,
                "ApplicationDescription",
                0,
                winreg.REG_SZ,
                "SnapAlert Productivity Monitor",
            )
            winreg.SetValueEx(
                key, "ApplicationDisplayName", 0, winreg.REG_SZ, "SnapAlert"
            )
            winreg.SetValueEx(key, "ApplicationName", 0, winreg.REG_SZ, "SnapAlert")

        return True

    except Exception as e:
        print(f"❌ Failed to register app ID: {e}")
        return False


def create_start_menu_shortcut():
    """Create a proper Start Menu shortcut with app ID"""
    paths = get_app_paths()

    try:
        # PowerShell script to create shortcut with app ID
        python_exe = sys.executable
        app_path = paths["app_path"]
        icon_path = paths["icon_path"]
        app_id = paths["app_id"]

        start_menu_dir = os.path.expandvars(
            r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"
        )
        shortcut_path = os.path.join(start_menu_dir, "SnapAlert.lnk")

        powershell_cmd = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
$Shortcut.TargetPath = '{python_exe}'
$Shortcut.Arguments = '"{app_path}"'
$Shortcut.WorkingDirectory = '{paths["script_dir"]}'
$Shortcut.Description = 'SnapAlert Productivity Monitor'
"""

        if icon_path:
            powershell_cmd += f'$Shortcut.IconLocation = "{icon_path}"\n'

        powershell_cmd += """
$Shortcut.Save()

# Set AppUserModelID on the shortcut
$bytes = [System.IO.File]::ReadAllBytes($Shortcut.FullName)
$lnk = $WshShell.CreateShortcut($Shortcut.FullName)
"""

        # Add app ID to shortcut properties
        powershell_cmd += f"""
# Create a COM object to set AppUserModelID
$shell = New-Object -ComObject Shell.Application
$folder = $shell.NameSpace('{start_menu_dir}')
$item = $folder.ParseName('SnapAlert.lnk')
"""

        result = subprocess.run(
            ["powershell.exe", "-Command", powershell_cmd],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode == 0:
            print("✅ Created Start Menu shortcut with app ID")
            return True
        else:
            print(f"⚠️ Shortcut creation had issues: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Failed to create Start Menu shortcut: {e}")
        return False


def test_app_id_registration():
    """Test if the app ID registration worked"""
    paths = get_app_paths()

    try:
        # Test PowerShell notification with our app ID
        powershell_cmd = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>SnapAlert Registration Test</text>
            <text>If you see this with SnapAlert branding, registration worked!</text>
        </binding>
    </visual>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = New-Object Windows.UI.Notifications.ToastNotification($xml)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("{paths["app_id"]}")
$notifier.Show($toast)
"""

        result = subprocess.run(
            ["powershell.exe", "-Command", powershell_cmd],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode == 0:
            print("✅ Test notification sent with registered app ID")
            print("   Check if it shows 'SnapAlert' as the source")
            return True
        else:
            print(f"❌ Test notification failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def is_app_registered():
    """Check if SnapAlert is already registered"""
    paths = get_app_paths()
    app_id = paths["app_id"]

    try:
        key_path = f"SOFTWARE\\Classes\\AppUserModelId\\{app_id}"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path):
            return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def main():
    """Main registration function"""
    print("🔺 SnapAlert App ID Registration")
    print("=" * 50)

    paths = get_app_paths()

    print(f"Script Directory: {paths['script_dir']}")
    print(f"Icon Path: {paths['icon_path'] or 'Not found'}")
    print(f"App ID: {paths['app_id']}")
    print()

    # Check if already registered
    if is_app_registered():
        print("ℹ️ SnapAlert is already registered with Windows")

        response = input("Do you want to re-register? (y/N): ")
        if response.lower() != "y":
            print("Registration skipped.")
            return

    # Register app ID
    print("📝 Registering SnapAlert app ID...")
    if register_app_id():
        print("✅ App ID registration completed")
    else:
        print("❌ App ID registration failed")
        return

    # Create Start Menu shortcut
    print("\n🔗 Creating Start Menu shortcut...")
    create_start_menu_shortcut()

    # Test the registration
    print("\n🧪 Testing registration...")
    test_app_id_registration()

    print("\n🎉 Registration Complete!")
    print("=" * 50)
    print("SnapAlert is now registered with Windows.")
    print("Notifications should show 'SnapAlert' as the source.")
    print("You can find SnapAlert in your Start Menu.")
    print("\nRestart your Flask app to use the new registration.")


if __name__ == "__main__":
    main()
