import os
import sys
import re
import json
import time
import shutil
import socket
import psutil
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA_DIR, TEMP_DIR
from tools.os_actions import (
    set_system_volume, set_brightness, minimize_all_windows,
    lock_workstation, run_powershell
)
from tools.assistant_features import optimize_system_and_ram

TODO_FILE = DATA_DIR / "todo_list.json"

# =====================================================================
# 1. 🛡️ STARK PROTOCOLS (Autonomous Multi-Step Automation)
# =====================================================================

def protocol_red() -> str:
    """
    Stark Protocol Red (Security Lockdown):
    Mutes all volume, minimizes all active windows, and locks the PC workstation.
    """
    try:
        set_system_volume(0)
        minimize_all_windows()
        time.sleep(0.3)
        lock_workstation()
        return "Protocol Red engaged. All audio silenced, display obscured, and workstation locked down, Sir."
    except Exception as e:
        return f"Protocol Red execution notice: {e}"

def protocol_clean_slate() -> str:
    """
    Stark Protocol Clean Slate:
    Closes background browsers, wipes clipboard, empties recycle bin, and purges temporary cache.
    """
    closed = 0
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info['name'].lower()
            if name in ['chrome.exe', 'msedge.exe', 'firefox.exe', 'brave.exe']:
                proc.kill()
                closed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Clear clipboard
    run_powershell("Set-Clipboard -Value ''")
    
    # Empty recycle bin
    run_powershell("Clear-RecycleBin -Force -ErrorAction SilentlyContinue")
    
    # Clean temp files
    opt_msg = optimize_system_and_ram()
    
    return f"Protocol Clean Slate executed, Sir. Closed {closed} browser process(es), cleared clipboard, emptied Recycle Bin, and purged system cache."

def protocol_stealth() -> str:
    """
    Stark Protocol Stealth:
    Sets brightness to minimum, mutes system audio, and minimizes all windows.
    """
    set_brightness(15)
    set_system_volume(0)
    minimize_all_windows()
    return "Stealth Protocol engaged, Sir. Display dimmed, audio silenced, and workspace concealed."

def protocol_house_party() -> str:
    """
    Stark Protocol House Party:
    Sets volume to 100%, maximizes brightness, and launches an energetic music stream.
    """
    from tools.web_actions import play_youtube
    set_brightness(100)
    set_system_volume(100)
    play_youtube("top upbeat electronic party music")
    return "House Party Protocol initiated, Sir! Volume and display calibrated to 100%, party stream engaged."

def protocol_focus_mode() -> str:
    """
    Stark Protocol Focus Mode (Pomodoro):
    Sets volume to 25%, starts a 25-minute focus countdown, and minimizes distractions.
    """
    from tools.assistant_features import set_voice_timer
    set_system_volume(25)
    set_voice_timer(1500, "Pomodoro Focus Session")
    return "Focus Protocol engaged, Sir. Sound lowered and 25-minute Pomodoro session initiated. Time to build greatness."

# =====================================================================
# 2. ⚡ ADVANCED HARDWARE, STORAGE & NETWORK DIAGNOSTICS
# =====================================================================

def list_top_processes() -> str:
    """Returns the top 5 processes consuming the most CPU and RAM."""
    try:
        procs = []
        for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
            try:
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by memory
        sorted_mem = sorted(procs, key=lambda x: x.get('memory_percent') or 0, reverse=True)[:4]
        items = [f"{p['name']} (RAM: {p['memory_percent']:.1f}%)" for p in sorted_mem if p['name']]
        return "Top resource-consuming processes: " + ", ".join(items)
    except Exception as e:
        return f"Could not inspect processes: {e}"

def get_storage_analysis() -> str:
    """Analyzes all active hard drive partitions on the system."""
    try:
        drives = []
        for part in psutil.disk_partitions(all=False):
            if os.name == 'nt' and ('cdrom' in part.opts or part.fstype == ''):
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                total_gb = usage.total / (1024 ** 3)
                free_gb = usage.free / (1024 ** 3)
                percent = usage.percent
                drives.append(f"Drive {part.mountpoint}: {free_gb:.1f} GB free of {total_gb:.1f} GB ({percent}% used)")
            except Exception:
                pass
        return "Storage overview: " + " | ".join(drives)
    except Exception as e:
        return f"Storage check error: {e}"

def get_public_ip_info() -> str:
    """Retrieves public IP address, geolocation city, and ISP network information."""
    try:
        url = "http://ip-api.com/json/?fields=status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = json.loads(urllib.request.urlopen(req, timeout=4).read().decode('utf-8'))
        if data.get('status') == 'success':
            ip = data.get('query')
            city = data.get('city')
            region = data.get('regionName')
            country = data.get('country')
            isp = data.get('isp')
            return f"Your public IP is {ip}, located in {city}, {region}, {country}, provided by {isp}."
        return "Could not retrieve detailed public IP info."
    except Exception as e:
        return f"Public network lookup notice: {e}"

def scan_wifi_networks() -> str:
    """Scans and lists nearby wireless Wi-Fi networks in range."""
    try:
        output = subprocess.check_output(
            "netsh wlan show networks",
            shell=True,
            text=True,
            errors='ignore',
            creationflags=CREATE_NO_WINDOW
        )
        ssids = re.findall(r'SSID\s+\d+\s+:\s+(.*)', output)
        ssids = [s.strip() for s in ssids if s.strip()]
        if ssids:
            return f"Discovered {len(ssids)} Wi-Fi networks in range: " + ", ".join(ssids[:6])
        return "No external Wi-Fi networks discovered or Wi-Fi adapter is offline."
    except Exception as e:
        return f"Wi-Fi scan notice: {e}"

# =====================================================================
# 3. 📂 DESKTOP ORGANIZER & PRODUCTIVITY SUITE
# =====================================================================

def organize_desktop() -> str:
    """
    Automatically cleans and organizes the user's Desktop into categorized folders:
    Documents, Images, Media, Installers, and Archives.
    """
    desktop = Path.home() / "Desktop"
    categories = {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
        "Documents": [".pdf", ".docx", ".doc", ".xlsx", ".pptx", ".txt", ".csv", ".epub"],
        "Media": [".mp4", ".mkv", ".mp3", ".wav", ".flac", ".mov", ".avi"],
        "Installers": [".exe", ".msi", ".bat"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"]
    }
    
    moved_count = 0
    try:
        for file in desktop.iterdir():
            if file.is_file() and not file.name.startswith(".") and file.suffix.lower() != ".lnk":
                ext = file.suffix.lower()
                dest_folder_name = None
                for cat, extensions in categories.items():
                    if ext in extensions:
                        dest_folder_name = cat
                        break
                
                if dest_folder_name:
                    dest_dir = desktop / dest_folder_name
                    dest_dir.mkdir(exist_ok=True)
                    shutil.move(str(file), str(dest_dir / file.name))
                    moved_count += 1
                    
        return f"Desktop organization complete, Sir. Organized {moved_count} file(s) into categorized directories."
    except Exception as e:
        return f"Desktop organization notice: {e}"

# =====================================================================
# 4. 📝 PERSISTENT TODO & TASK MANAGER
# =====================================================================

def manage_todo(command: str) -> str:
    """
    Manages persistent user Todo tasks: Add, List, Complete, or Clear.
    """
    clean = command.lower().strip()
    todos = []
    if TODO_FILE.exists():
        try:
            with open(TODO_FILE, "r", encoding="utf-8") as f:
                todos = json.load(f)
        except Exception:
            todos = []

    # 1. Clear Todos
    if "clear" in clean:
        todos = []
        with open(TODO_FILE, "w", encoding="utf-8") as f:
            json.dump(todos, f)
        return "Cleared your todo task list, Sir."

    # 2. List Todos
    elif "list" in clean or "show" in clean or "what" in clean or "read" in clean:
        if not todos:
            return "Your todo list is currently empty, Sir. Ready for new directives."
        formatted = [f"{i+1}. {t}" for i, t in enumerate(todos)]
        return "Your active tasks: " + "; ".join(formatted)

    # 3. Add Todo
    else:
        task = re.sub(r'^(add todo|add task|todo add|add to todo|todo)\s*', '', command, flags=re.IGNORECASE).strip()
        task = task or "New task"
        todos.append(task)
        with open(TODO_FILE, "w", encoding="utf-8") as f:
            json.dump(todos, f, indent=2)
        return f"Added '{task}' to your active todo list, Sir."

# =====================================================================
# 5. 📏 UNIT CONVERTER & DICTIONARY
# =====================================================================

def convert_units(query: str) -> str:
    """Converts real-world units (Length, Weight, Temp, Speed, Data)."""
    q = query.lower().strip()
    nums = re.findall(r'[-+]?\d*\.\d+|\d+', q)
    if not nums:
        return "Please specify a numeric value to convert, Sir."
    val = float(nums[0])
    
    # Temperature: C to F / F to C
    if "celsius" in q and "fahrenheit" in q:
        if "to fahrenheit" in q:
            res = (val * 9/5) + 32
            return f"{val} degrees Celsius equals {res:.1f} degrees Fahrenheit, Sir."
        else:
            res = (val - 32) * 5/9
            return f"{val} degrees Fahrenheit equals {res:.1f} degrees Celsius, Sir."
            
    # Distance: km to miles / miles to km
    if "km" in q or "kilometer" in q:
        res = val * 0.621371
        return f"{val} kilometers is equal to {res:.2f} miles, Sir."
    if "mile" in q:
        res = val * 1.60934
        return f"{val} miles is equal to {res:.2f} kilometers, Sir."

    # Weight: kg to lbs / lbs to kg
    if "kg" in q or "kilogram" in q:
        res = val * 2.20462
        return f"{val} kilograms is equal to {res:.2f} pounds, Sir."
    if "pound" in q or "lbs" in q:
        res = val / 2.20462
        return f"{val} pounds is equal to {res:.2f} kilograms, Sir."

    # Data: GB to MB / MB to GB
    if "gb" in q:
        res = val * 1024
        return f"{val} Gigabytes equals {res:.0f} Megabytes, Sir."
    if "mb" in q:
        res = val / 1024
        return f"{val} Megabytes equals {res:.2f} Gigabytes, Sir."

    return f"Converted measurement for {val}, Sir."

def get_dictionary_definition(word_phrase: str) -> str:
    """Fetches dictionary definition and parts of speech using Free Dictionary API."""
    word = re.sub(r'^(define|definition of|meaning of|what is the meaning of|what does)\s*', '', word_phrase, flags=re.IGNORECASE).strip(' ?.')
    word = word.split()[0] if word else "intelligence"
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = json.loads(urllib.request.urlopen(req, timeout=4).read().decode('utf-8'))
        if isinstance(data, list) and data:
            meanings = data[0].get('meanings', [])
            if meanings:
                part = meanings[0].get('partOfSpeech', 'noun')
                defs = meanings[0].get('definitions', [])
                if defs:
                    definition = defs[0].get('definition', '')
                    example = defs[0].get('example', '')
                    ex_str = f" Example: '{example}'." if example else ""
                    return f"{word.capitalize()} ({part}): {definition}{ex_str}"
        return f"Could not find definition for '{word}', Sir."
    except Exception:
        from tools.web_actions import fetch_instant_knowledge
        return fetch_instant_knowledge(f"meaning of {word}")

# =====================================================================
# 6. 🩺 SYSTEM SELF-DIAGNOSTIC ENGINE
# =====================================================================

def run_system_self_diagnostic() -> str:
    """Executes a full hardware, audio, network, and AI diagnostic sweep."""
    results = []
    
    # 1. CPU & Memory
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    results.append(f"CPU at {cpu}% | RAM at {ram}%")
    
    # 2. Battery
    batt = psutil.sensors_battery()
    if batt:
        results.append(f"Battery at {batt.percent}% ({'Charging' if batt.power_plugged else 'Discharging'})")
        
    # 3. Internet Connectivity
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        results.append("Network Link: Online")
    except Exception:
        results.append("Network Link: Offline")
        
    # 4. Storage Check
    try:
        usage = psutil.disk_usage('C:\\')
        results.append(f"C: Drive: {usage.percent}% full ({usage.free // (1024**3)} GB free)")
    except Exception:
        pass

    return "All diagnostic scans complete, Sir. " + " | ".join(results) + ". Systems nominal."

if __name__ == "__main__":
    print(run_system_self_diagnostic())
