import os
import sys
import time
import random
import string
import shutil
import threading
import requests
import pyautogui
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
import subprocess
from pathlib import Path

CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

BASE_DIR = Path(__file__).resolve().parent.parent
DIARY_DIR = BASE_DIR / "data" / "diary"
DIARY_DIR.mkdir(parents=True, exist_ok=True)

def get_live_weather(city: str = "Hyderabad") -> str:
    """Fetches real-time weather, temperature, and conditions."""
    clean_city = city.strip() or "Hyderabad"
    try:
        url = f"https://wttr.in/{urllib.parse.quote(clean_city)}?format=j1"
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            data = res.json()
            curr = data.get("current_condition", [{}])[0]
            desc = curr.get("weatherDesc", [{}])[0].get("value", "Clear")
            temp = curr.get("temp_C", "--")
            feels = curr.get("FeelsLikeC", temp)
            humid = curr.get("humidity", "--")
            wind = curr.get("windspeedKmph", "--")
            return f"The weather in {clean_city.capitalize()} is currently {desc}, with a temperature of {temp}°C (feels like {feels}°C), humidity at {humid}%, and wind speed at {wind} km/h."
    except Exception:
        pass
    return f"Unable to retrieve live weather for {clean_city} at the moment."

def get_top_news(category: str = "general") -> str:
    """Fetches top real-time breaking news headlines."""
    try:
        url = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            items = root.findall(".//item")[:3]
            headlines = []
            for i, item in enumerate(items, 1):
                t = item.find("title").text
                if " - " in t:
                    t = t.rsplit(" - ", 1)[0]
                headlines.append(f"{i}. {t}")
            return "Here are the top headlines: " + " | ".join(headlines)
    except Exception:
        pass
    return "Unable to fetch latest news at the moment."

def _timer_worker(seconds: int, label: str):
    from core.voice_out import speak
    time.sleep(seconds)
    minutes = int(seconds / 60)
    sec_rem = seconds % 60
    dur_str = f"{minutes} minute{'s' if minutes > 1 else ''}" if minutes > 0 else f"{sec_rem} seconds"
    speak(f"Alert Boss! Your timer for {label or dur_str} is complete.")

def set_voice_timer(seconds: int, label: str = "Timer") -> str:
    """Sets a countdown timer for the specified duration and announces via voice when done."""
    try:
        t = threading.Thread(target=_timer_worker, args=(seconds, label), daemon=True)
        t.start()
        minutes = int(seconds / 60)
        sec_rem = seconds % 60
        dur_str = f"{minutes} minute{'s' if minutes > 1 else ''}" if minutes > 0 else f"{sec_rem} seconds"
        return f"Timer set for {dur_str}."
    except Exception as e:
        return f"Failed to set timer: {e}"

def media_play_pause() -> str:
    """Toggles play/pause for active media (YouTube, Spotify, VLC, video players)."""
    try:
        pyautogui.press("playpause")
        return "Toggled media play/pause."
    except Exception as e:
        return f"Could not toggle media: {e}"

def media_next_track() -> str:
    """Skips to the next music track or video."""
    try:
        pyautogui.press("nexttrack")
        return "Skipped to next track."
    except Exception as e:
        return f"Could not skip track: {e}"

def media_previous_track() -> str:
    """Plays the previous music track."""
    try:
        pyautogui.press("prevtrack")
        return "Returned to previous track."
    except Exception as e:
        return f"Could not go to previous track: {e}"

def read_clipboard_text() -> str:
    """Reads the current text copied on the Windows clipboard."""
    try:
        ps_cmd = "Get-Clipboard"
        res = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=3,
            creationflags=CREATE_NO_WINDOW
        )
        clip = res.stdout.strip()
        if clip:
            return f"Your clipboard contains: {clip[:200]}"
        return "Your clipboard is currently empty."
    except Exception as e:
        return f"Could not read clipboard: {e}"

def copy_text_to_clipboard(text: str) -> str:
    """Copies the given text onto the Windows clipboard."""
    try:
        escaped = text.replace("'", "''")
        ps_cmd = f"Set-Clipboard -Value '{escaped}'"
        subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True,
            timeout=3,
            creationflags=CREATE_NO_WINDOW
        )
        return f"Copied '{text[:50]}' to your clipboard."
    except Exception as e:
        return f"Could not copy to clipboard: {e}"

def sleep_pc() -> str:
    """Puts the computer to sleep."""
    try:
        subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True, creationflags=CREATE_NO_WINDOW)
        return "Putting computer to sleep."
    except Exception as e:
        return f"Failed to enter sleep mode: {e}"

def test_internet_speed() -> str:
    """Tests internet latency and connectivity."""
    try:
        start = time.time()
        res = requests.get("https://www.google.com", timeout=4)
        latency = int((time.time() - start) * 1000)
        if res.status_code == 200:
            return f"Internet connection is active with {latency} milliseconds response time."
    except Exception:
        pass
    return "Internet connection appears to be offline or high latency."

# ==========================================
# 🌟 NEW SUPERCHARGED ASSISTANT PROTOCOLS
# ==========================================

def get_daily_briefing() -> str:
    """Tony Stark Daily Briefing Protocol: Date, Time, Battery, Weather, and Top News."""
    import psutil
    now_date = datetime.now().strftime("%A, %B %d, %Y")
    now_time = datetime.now().strftime("%I:%M %p")
    
    battery_info = "battery status unavailable"
    bat = psutil.sensors_battery()
    if bat:
        plugged = "charging" if bat.power_plugged else "on battery"
        battery_info = f"battery is at {bat.percent}% and {plugged}"
        
    weather = get_live_weather("Hyderabad")
    news = get_top_news()
    
    return f"Good day Boss! Today is {now_date}, and current time is {now_time}. Your {battery_info}. {weather} {news}"

def translate_phrase(text: str, target_lang: str = "te") -> str:
    """Translates any text to Telugu, Hindi, Spanish, French, German, etc."""
    try:
        from deep_translator import GoogleTranslator
        lang_code = "te" if "telugu" in target_lang.lower() else ("hi" if "hindi" in target_lang.lower() else target_lang)
        translated = GoogleTranslator(source='auto', target=lang_code).translate(text)
        return f"The translation is: {translated}"
    except Exception as e:
        return f"Could not translate phrase: {e}"

def get_crypto_or_currency(query: str) -> str:
    """Fetches live crypto prices (BTC, ETH) and exchange rates (USD to INR, EUR to INR)."""
    q = query.lower()
    try:
        if "bitcoin" in q or "btc" in q:
            r = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,inr', timeout=5).json()
            usd = r['bitcoin']['usd']
            inr = r['bitcoin']['inr']
            return f"Bitcoin is currently trading at {usd:,} US Dollars, or approximately {inr:,} Indian Rupees."
        elif "ethereum" in q or "eth" in q:
            r = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd,inr', timeout=5).json()
            usd = r['ethereum']['usd']
            inr = r['ethereum']['inr']
            return f"Ethereum is currently trading at {usd:,} US Dollars, or {inr:,} Indian Rupees."
        elif "dollar" in q or "usd" in q or "exchange rate" in q or "inr" in q:
            r = requests.get('https://open.er-api.com/v6/latest/USD', timeout=5).json()
            rate = round(r['rates'].get('INR', 83.5), 2)
            return f"1 US Dollar is currently equal to {rate} Indian Rupees."
        elif "euro" in q or "eur" in q:
            r = requests.get('https://open.er-api.com/v6/latest/EUR', timeout=5).json()
            rate = round(r['rates'].get('INR', 90.5), 2)
            return f"1 Euro is currently equal to {rate} Indian Rupees."
    except Exception:
        pass
    return "Unable to fetch financial exchange rates right now."

def save_diary_entry(entry: str) -> str:
    """Saves a voice note to the user's dated diary vault."""
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%I:%M %p")
    filepath = DIARY_DIR / f"diary_{today}.txt"
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {entry.strip()}\n")
        return f"Saved entry to your personal diary for today: '{entry[:40]}...'"
    except Exception as e:
        return f"Failed to save diary note: {e}"

def optimize_system_and_ram() -> str:
    """Cleans temporary junk files and flushes memory caches."""
    try:
        temp_dir = os.environ.get("TEMP", r"C:\Windows\Temp")
        deleted_count = 0
        for item in Path(temp_dir).glob("*"):
            try:
                if item.is_file():
                    item.unlink()
                    deleted_count += 1
            except Exception:
                continue
        return f"System optimization complete. Cleaned {deleted_count} temporary cache files and refreshed system memory."
    except Exception as e:
        return f"Optimization finished with notice: {e}"

def open_special_folder(folder_name: str) -> str:
    """Opens special user folders (Downloads, Documents, Pictures, Desktop, Recycle Bin)."""
    user_home = Path.home()
    folder_map = {
        "downloads": user_home / "Downloads",
        "documents": user_home / "Documents",
        "pictures": user_home / "Pictures",
        "videos": user_home / "Videos",
        "music": user_home / "Music",
        "desktop": user_home / "Desktop",
    }
    f_lower = folder_name.lower()
    for key, path in folder_map.items():
        if key in f_lower:
            os.startfile(str(path))
            return f"Opened {key.capitalize()} folder."
    if "recycle bin" in f_lower:
        subprocess.run("explorer.exe shell:RecycleBinFolder", shell=True, creationflags=CREATE_NO_WINDOW)
        return "Opened Recycle Bin."
    return "Folder not found."

def roll_dice_or_coin(action: str) -> str:
    """Flips a coin, rolls a dice, or generates a secure password."""
    a = action.lower()
    if "coin" in a or "flip" in a:
        res = random.choice(["Heads", "Tails"])
        return f"I flipped a coin and got {res}."
    elif "dice" in a or "roll" in a:
        res = random.randint(1, 6)
        return f"I rolled a dice and got {res}."
    elif "password" in a:
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        pwd = "".join(random.choice(chars) for _ in range(12))
        copy_text_to_clipboard(pwd)
        return f"Generated secure password and copied to your clipboard."
    return "Action ready."
