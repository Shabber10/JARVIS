import os
import sys
import re
import subprocess
import socket
import psutil
import pyautogui
from pathlib import Path
from datetime import datetime
from config import TEMP_DIR

# Suppress console window popups on Windows
CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

pyautogui.FAILSAFE = False

APP_SHORTCUTS = {
    "whatsapp": "whatsapp:",
    "whatsapp web": "https://web.whatsapp.com",
    "chrome": "chrome",
    "google chrome": "chrome",
    "browser": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "cmd": "cmd",
    "terminal": "wt",
    "powershell": "powershell",
    "spotify": "spotify:",
    "vscode": "code",
    "code": "code",
    "visual studio code": "code",
    "explorer": "explorer",
    "files": "explorer",
    "settings": "ms-settings:",
    "task manager": "taskmgr",
    "paint": "mspaint",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "camera": "microsoft.windows.camera:",
    "store": "ms-windows-store:",
    "clock": "ms-clock:",
    "mail": "mailto:",
    "calendar": "outlookcal:",
    "youtube": "https://www.youtube.com",
    "gmail": "https://mail.google.com"
}

def open_application(app_name: str) -> str:
    """Opens any application on the Windows laptop by name, protocol, or executable."""
    clean_app = app_name.lower().strip()
    
    # Strip conversational suffixes like "and call Subhan"
    app_target = clean_app
    for k in [" and call", " and message", " and send", " and text", " and write"]:
        if k in clean_app:
            app_target = clean_app.split(k)[0].strip()
            
    # Check shortcuts dictionary
    for key, target in APP_SHORTCUTS.items():
        if key in app_target or app_target in key:
            try:
                if target.startswith("http://") or target.startswith("https://"):
                    import webbrowser
                    webbrowser.open(target)
                elif ":" in target or target.startswith("ms-"):
                    subprocess.Popen(f"start {target}", shell=True, creationflags=CREATE_NO_WINDOW)
                else:
                    subprocess.Popen(f"start {target}", shell=True, creationflags=CREATE_NO_WINDOW)
                return f"Successfully opened {key.capitalize()}."
            except Exception:
                pass

    # WhatsApp special handler
    if "whatsapp" in clean_app:
        try:
            subprocess.Popen("start whatsapp:", shell=True, creationflags=CREATE_NO_WINDOW)
            return "Opened WhatsApp for you, Boss."
        except Exception:
            import webbrowser
            webbrowser.open("https://web.whatsapp.com")
            return "Opened WhatsApp Web for you, Boss."

    # General Shell fallback
    try:
        first_word = app_target.split()[0] if app_target else "explorer"
        subprocess.Popen(f"start {first_word}", shell=True, creationflags=CREATE_NO_WINDOW)
        return f"Opened {first_word.capitalize()}."
    except Exception as e:
        return f"Could not launch {app_name}: {e}"

def close_application(app_name: str) -> str:
    """Closes running applications matching the given name."""
    target = app_name.lower().replace(".exe", "").strip()
    killed = 0
    for proc in psutil.process_iter(['name']):
        try:
            proc_name = proc.info['name'].lower()
            if target in proc_name:
                proc.kill()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    if killed > 0:
        return f"Closed {killed} instance(s) of {app_name}."
    return f"No running application found matching '{app_name}'."

def run_powershell(command: str) -> str:
    """Executes any PowerShell command on Windows and returns stdout/stderr."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=CREATE_NO_WINDOW
        )
        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()
        if err and not out:
            return f"Command error: {err}"
        return out if out else "Command executed successfully."
    except Exception as e:
        return f"Failed to execute command: {e}"

def set_brightness(level: int) -> str:
    """Adjusts laptop display brightness (0 to 100)."""
    level = max(0, min(100, level))
    try:
        ps_cmd = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})"
        subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, timeout=5, creationflags=CREATE_NO_WINDOW)
        return f"Adjusted screen brightness to {level}%."
    except Exception as e:
        return f"Could not set brightness: {e}"

def set_system_volume(level: int) -> str:
    """Sets the Windows system volume (0 to 100)."""
    level = max(0, min(100, level))
    try:
        steps = int(level / 2)
        pyautogui.press('volumemute')
        for _ in range(50):
            pyautogui.press('volumedown')
        for _ in range(steps):
            pyautogui.press('volumeup')
        return f"Set system volume to approximately {level}%."
    except Exception as e:
        return f"Failed to adjust volume: {e}"

def mute_system_volume() -> str:
    """Toggles or mutes the system audio."""
    try:
        pyautogui.press('volumemute')
        return "Toggled audio mute state."
    except Exception as e:
        return f"Failed to mute: {e}"

def take_screenshot() -> str:
    """Takes a screenshot of the primary display and saves it."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = TEMP_DIR / f"screenshot_{timestamp}.png"
        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            screenshot.save(str(filepath))
            return f"Screenshot captured and saved to {filepath}."
        except Exception:
            ps_cmd = f"""
            Add-Type -AssemblyName System.Windows.Forms
            Add-Type -AssemblyName System.Drawing
            $Screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
            $Bitmap = New-Object System.Drawing.Bitmap $Screen.Width, $Screen.Height
            $Graphics = [System.Drawing.Graphics]::FromImage($Bitmap)
            $Graphics.CopyFromScreen($Screen.X, $Screen.Y, 0, 0, $Bitmap.Size)
            $Bitmap.Save('{str(filepath).replace(chr(92), '/')}')
            """
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, timeout=5, creationflags=CREATE_NO_WINDOW)
            if filepath.exists():
                return f"Screenshot captured and saved to {filepath}."
            return "Screenshot captured successfully."
    except Exception as e:
        return f"Failed to take screenshot: {e}"

def lock_workstation() -> str:
    """Locks the Windows computer."""
    try:
        subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True, creationflags=CREATE_NO_WINDOW)
        return "Workstation locked."
    except Exception as e:
        return f"Failed to lock workstation: {e}"

def minimize_all_windows() -> str:
    """Minimizes all open windows to show the clean desktop."""
    try:
        pyautogui.hotkey('win', 'd')
        return "Minimized all open windows."
    except Exception as e:
        return f"Failed to minimize windows: {e}"

def press_hotkey(keys: str) -> str:
    """Presses key combinations like 'alt+tab', 'ctrl+c', 'ctrl+v', 'win+e', 'ctrl+w'."""
    try:
        key_list = [k.strip().lower() for k in keys.split('+')]
        pyautogui.hotkey(*key_list)
        return f"Pressed key combination: {keys}"
    except Exception as e:
        return f"Failed to press keys: {e}"

def type_text(text: str) -> str:
    """Types the given text into the active focused window."""
    try:
        pyautogui.write(text, interval=0.02)
        return f"Typed: '{text}'"
    except Exception as e:
        return f"Failed to type text: {e}"

def create_notepad_note(content: str, note_title: str = "quick_note") -> str:
    """Creates a text note on the user's Desktop and opens it in Notepad."""
    try:
        desktop_dir = Path.home() / "Desktop"
        filename = f"{note_title.replace(' ', '_')}.txt"
        file_path = desktop_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"--- Created by Jarvis on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n\n{content}\n")
        subprocess.Popen(f"notepad.exe {file_path}", shell=True, creationflags=CREATE_NO_WINDOW)
        return f"Created note '{filename}' on Desktop and opened it in Notepad."
    except Exception as e:
        return f"Failed to create note: {e}"

def get_battery_status() -> str:
    """Checks the laptop battery percentage and charging status."""
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return "No battery detected. This system might be plugged directly into AC power or running as a desktop."
        percent = battery.percent
        plugged = "plugged in and charging" if battery.power_plugged else "discharging on battery power"
        return f"Your battery is at {percent}% and is currently {plugged}."
    except Exception as e:
        return f"Could not retrieve battery information: {e}"

def get_system_status() -> str:
    """Checks current CPU usage, RAM usage, disk space, and battery status."""
    try:
        cpu = psutil.cpu_percent(interval=0.3)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('C:\\').percent
        battery_info = get_battery_status()
        return f"CPU usage is at {cpu}%, RAM usage is at {ram}%, C: Drive is {disk}% full. {battery_info}"
    except Exception as e:
        return f"Could not retrieve system status: {e}"

def get_network_info() -> str:
    """Checks the active network connection and local IP address."""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return f"Laptop Hostname: {hostname}, Local IP: {local_ip}."
    except Exception as e:
        return f"Could not get network info: {e}"

def execute_universal_system_action(cmd: str) -> str:
    """
    Executes ANY arbitrary Windows OS command, automation, GUI control, or PowerShell action.
    """
    c = cmd.lower().strip()
    
    # 1. Typing & Keyboard simulation
    if c.startswith("type ") or c.startswith("write "):
        text_to_type = re.sub(r'^(type|write)\s*', '', cmd, flags=re.IGNORECASE).strip(' "\'')
        return type_text(text_to_type)
    elif "press enter" in c:
        pyautogui.press('enter')
        return "Pressed Enter key."
    elif "press tab" in c:
        pyautogui.press('tab')
        return "Pressed Tab key."
    elif "press space" in c:
        pyautogui.press('space')
        return "Pressed Spacebar."
    elif "press escape" in c or "press esc" in c:
        pyautogui.press('esc')
        return "Pressed Escape key."
    elif "press backspace" in c:
        pyautogui.press('backspace')
        return "Pressed Backspace."
    elif "press windows" in c or "press win key" in c or "open start menu" in c:
        pyautogui.press('win')
        return "Opened Windows Start Menu."
    elif "press alt f4" in c or "close window" in c or "close current window" in c:
        pyautogui.hotkey('alt', 'f4')
        return "Closed current window."
    elif "close tab" in c:
        pyautogui.hotkey('ctrl', 'w')
        return "Closed tab."
    elif "new tab" in c:
        pyautogui.hotkey('ctrl', 't')
        return "Opened new tab."
    elif "switch window" in c or "switch app" in c or "alt tab" in c:
        pyautogui.hotkey('alt', 'tab')
        return "Switched window."
    elif "maximize window" in c or "maximize" in c:
        pyautogui.hotkey('win', 'up')
        return "Maximized current window."
    elif "minimize window" in c:
        pyautogui.hotkey('win', 'down')
        return "Minimized window."

    # 2. Mouse Controls
    elif "scroll down" in c or "scroll below" in c:
        pyautogui.scroll(-600)
        return "Scrolled down."
    elif "scroll up" in c or "scroll above" in c:
        pyautogui.scroll(600)
        return "Scrolled up."
    elif "double click" in c:
        pyautogui.doubleClick()
        return "Double clicked."
    elif "right click" in c:
        pyautogui.rightClick()
        return "Right clicked."
    elif "click" in c:
        pyautogui.click()
        return "Clicked mouse."

    # 3. File & Folder Operations
    elif "folder" in c and ("create" in c or "make" in c or "new" in c):
        name = re.sub(r'^(create a folder|create folder|make a folder|make folder|new folder)\s*(on desktop|in desktop)?\s*(named|called)?\s*', '', cmd, flags=re.IGNORECASE)
        name = re.sub(r'\s*(on desktop|in desktop)$', '', name, flags=re.IGNORECASE).strip(' "\'')
        name = name or "New_Folder"
        target_path = Path.home() / "Desktop" / name.replace(" ", "_")
        target_path.mkdir(parents=True, exist_ok=True)
        return f"Created folder '{name}' on your Desktop."
    elif "empty recycle bin" in c or "clear recycle bin" in c:
        run_powershell("Clear-RecycleBin -Force -ErrorAction SilentlyContinue")
        return "Emptied the Recycle Bin."
    elif "list files on desktop" in c or "show desktop files" in c:
        desktop = Path.home() / "Desktop"
        files = [f.name for f in desktop.glob("*") if not f.name.startswith(".")][:10]
        return "Desktop files: " + ", ".join(files)

    # 4. Power & System Controls
    elif "restart laptop" in c or "restart pc" in c or "restart computer" in c:
        subprocess.run("shutdown /r /t 10", shell=True, creationflags=CREATE_NO_WINDOW)
        return "Restarting your laptop in 10 seconds. Say 'cancel restart' to abort."
    elif "shutdown laptop" in c or "shutdown pc" in c or "shutdown computer" in c or "turn off laptop" in c:
        subprocess.run("shutdown /s /t 10", shell=True, creationflags=CREATE_NO_WINDOW)
        return "Shutting down your laptop in 10 seconds. Say 'cancel shutdown' to abort."
    elif "cancel shutdown" in c or "cancel restart" in c or "abort shutdown" in c:
        subprocess.run("shutdown /a", shell=True, creationflags=CREATE_NO_WINDOW)
        return "Cancelled scheduled shutdown."

    # 5. Dynamic PowerShell Execution
    ps_result = run_powershell(cmd)
    if ps_result and "Command error" not in ps_result and len(ps_result) > 0:
        lines = ps_result.splitlines()[:5]
        return "\n".join(lines)
    
    return None
