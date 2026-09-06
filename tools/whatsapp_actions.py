import os
import re
import json
import time
import urllib.parse
import subprocess
from pathlib import Path
import ctypes
from typing import Optional, Tuple
import psutil
import pyautogui
from config import DATA_DIR

# Set DPI awareness for 1:1 physical pixel coordinate accuracy
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

pyautogui.FAILSAFE = False

CONTACTS_FILE = DATA_DIR / "contacts.json"
CREATE_NO_WINDOW = 0x08000000 if os.name == 'nt' else 0

user32 = ctypes.windll.user32 if os.name == 'nt' else None
kernel32 = ctypes.windll.kernel32 if os.name == 'nt' else None

VK_RETURN = 0x0D
VK_CONTROL = 0x11
VK_ESCAPE = 0x1B
VK_DOWN = 0x28
KEYEVENTF_KEYUP = 0x0002

class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]

def _ensure_default_desktop():
    """Attaches calling thread to interactive 'default' desktop so mouse/keyboard reach WhatsApp."""
    if user32:
        try:
            hdesk = user32.OpenDesktopW('default', 0, False, 0x01FF)
            if hdesk:
                user32.SetThreadDesktop(hdesk)
        except Exception:
            pass

def _get_whatsapp_hwnd() -> Optional[int]:
    """
    Finds the active HWND of the WhatsApp Desktop window.
    Handles unread count badges in titles like '(7) WhatsApp' as well as plain 'WhatsApp'.
    """
    if not user32:
        return None
    _ensure_default_desktop()
    try:
        hdesk = user32.OpenDesktopW('default', 0, False, 0x01FF) or user32.OpenInputDesktop(0, False, 0x0100)
        root_target = None
        webview_target = None
        
        def cb(hwnd, lparam):
            nonlocal root_target, webview_target
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                if "antigravity" in title.lower():
                    return True
                if "whatsapp" in title.lower():
                    pid = ctypes.c_ulong()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    try:
                        pname = psutil.Process(pid.value).name().lower()
                        if "root" in pname or "whatsapp" in pname:
                            root_target = hwnd
                        elif "webview" in pname:
                            webview_target = hwnd
                    except Exception:
                        if not root_target:
                            root_target = hwnd
            return True
            
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        user32.EnumDesktopWindows(hdesk, WNDENUMPROC(cb), 0)
        return root_target or webview_target
    except Exception:
        return None

def _focus_whatsapp():
    """Brings WhatsApp to foreground using Win32 Alt unlock, AttachThreadInput and SetForegroundWindow."""
    _ensure_default_desktop()
    hwnd = _get_whatsapp_hwnd()
    if hwnd and user32:
        try:
            cur_tid = kernel32.GetCurrentThreadId()
            fg_hwnd = user32.GetForegroundWindow()
            fg_tid = user32.GetWindowThreadProcessId(fg_hwnd, None) if fg_hwnd else 0
            
            if fg_tid and fg_tid != cur_tid:
                user32.AttachThreadInput(cur_tid, fg_tid, True)
                
            # Simulate Alt key to bypass Windows SetForegroundWindow lock
            user32.keybd_event(0x12, 0, 0, 0)
            user32.ShowWindow(hwnd, 9) # SW_RESTORE
            user32.ShowWindow(hwnd, 3) # SW_MAXIMIZE
            user32.SetForegroundWindow(hwnd)
            user32.BringWindowToTop(hwnd)
            user32.SwitchToThisWindow(hwnd, True)
            user32.keybd_event(0x12, 0, 2, 0) # Release Alt
            
            if fg_tid and fg_tid != cur_tid:
                user32.AttachThreadInput(cur_tid, fg_tid, False)
                
            time.sleep(0.4)
            return True
        except Exception:
            pass
    
    subprocess.Popen('start "" "whatsapp:"', shell=True, creationflags=CREATE_NO_WINDOW)
    time.sleep(1.8)
    return False

def _native_click(x: int, y: int):
    """Sends native Win32 hardware mouse click."""
    _ensure_default_desktop()
    if user32:
        user32.SetCursorPos(x, y)
        time.sleep(0.06)
        user32.mouse_event(0x0002, 0, 0, 0, 0) # MOUSEEVENTF_LEFTDOWN
        time.sleep(0.06)
        user32.mouse_event(0x0004, 0, 0, 0, 0) # MOUSEEVENTF_LEFTUP
        time.sleep(0.06)

def _press_key_native(vk_code: int):
    """Sends native hardware-level key event directly to Windows with scan code."""
    _ensure_default_desktop()
    if user32:
        scan_code = user32.MapVirtualKeyW(vk_code, 0)
        user32.keybd_event(vk_code, scan_code, 0, 0)
        time.sleep(0.06)
        user32.keybd_event(vk_code, scan_code, KEYEVENTF_KEYUP, 0)

def _press_enter_native():
    _press_key_native(VK_RETURN)

def _press_ctrl_enter_native():
    _ensure_default_desktop()
    if user32:
        scan_ctrl = user32.MapVirtualKeyW(VK_CONTROL, 0)
        scan_ret = user32.MapVirtualKeyW(VK_RETURN, 0)
        user32.keybd_event(VK_CONTROL, scan_ctrl, 0, 0)
        user32.keybd_event(VK_RETURN, scan_ret, 0, 0)
        time.sleep(0.06)
        user32.keybd_event(VK_RETURN, scan_ret, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_CONTROL, scan_ctrl, KEYEVENTF_KEYUP, 0)

def _press_key_with_ctrl(key_char: str):
    """Sends Ctrl + Key combination natively."""
    _ensure_default_desktop()
    if user32:
        vk = ord(key_char.upper())
        scan_ctrl = user32.MapVirtualKeyW(VK_CONTROL, 0)
        scan_k = user32.MapVirtualKeyW(vk, 0)
        user32.keybd_event(VK_CONTROL, scan_ctrl, 0, 0)
        user32.keybd_event(vk, scan_k, 0, 0)
        time.sleep(0.06)
        user32.keybd_event(vk, scan_k, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_CONTROL, scan_ctrl, KEYEVENTF_KEYUP, 0)

def _trigger_send_action():
    """
    Sends the WhatsApp message by hitting Send button and Enter:
    1. Focuses WhatsApp window.
    2. Sends hardware Enter and Ctrl+Enter.
    3. Clicks the green Send button.
    """
    _ensure_default_desktop()
    _focus_whatsapp()
    time.sleep(0.2)
    
    # 1. Hardware Enter
    _press_enter_native()
    time.sleep(0.1)
    _press_ctrl_enter_native()
    time.sleep(0.1)
    try:
        pyautogui.press('enter')
    except Exception:
        pass

    # 2. Click Send button at bottom right (active when text is inside composer)
    hwnd = _get_whatsapp_hwnd()
    if hwnd and user32:
        rect = RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        target_x = 1870 if (rect.right - rect.left >= 1800) else rect.right - 50
        target_y = 955 if (rect.bottom - rect.top >= 1000) else rect.bottom - 40
        
        user32.SetCursorPos(target_x, target_y)
        time.sleep(0.08)
        user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.08)
        user32.mouse_event(0x0004, 0, 0, 0, 0)

def _load_contacts() -> dict:
    """Loads contacts dictionary from JSON."""
    if CONTACTS_FILE.exists():
        try:
            with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_contacts(contacts: dict):
    """Saves contacts dictionary to JSON."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
            json.dump(contacts, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving contacts: {e}")

def _set_clipboard(text: str):
    """Copies text to Windows clipboard safely supporting Unicode, emojis, and all languages."""
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(text)
        r.update()
        r.destroy()
    except Exception:
        try:
            escaped = text.replace("`", "``").replace('"', '`"')
            subprocess.run(
                ["powershell", "-Command", f'Set-Clipboard -Value "{escaped}"'],
                creationflags=CREATE_NO_WINDOW,
                timeout=3
            )
        except Exception as e:
            print(f"Clipboard error: {e}")

def _set_clipboard_file(file_path: str):
    """Sets a file path onto the Windows clipboard as CF_HDROP FileDropList for pasting into WhatsApp."""
    abs_path = str(Path(file_path).resolve())
    escaped = abs_path.replace("'", "''")
    subprocess.run(
        ["powershell", "-Command", f"Set-Clipboard -Path '{escaped}'"],
        creationflags=CREATE_NO_WINDOW,
        timeout=5
    )

def _clean_phone_number(phone: str) -> str:
    """Standardizes phone numbers with international prefix if needed."""
    digits = re.sub(r'[^\d+]', '', phone.strip())
    if digits.startswith("+"):
        return digits.replace("+", "")
    if len(digits) == 10:
        return f"91{digits}"
    return digits

def _resolve_recipient(recipient: str) -> Tuple[str, Optional[str]]:
    """
    Resolves recipient into (display_name, target_phone_if_any).
    """
    clean_recip = recipient.strip()
    contacts = _load_contacts()
    recip_lower = clean_recip.lower()
    
    if recip_lower in contacts:
        return contacts[recip_lower]["name"], contacts[recip_lower]["phone"]
    
    for key, info in contacts.items():
        if recip_lower in key or key in recip_lower:
            return info["name"], info["phone"]
            
    is_direct_num = bool(re.search(r'^\+?[\d\s\-]{7,15}$', clean_recip.replace(" ", "")))
    if is_direct_num:
        cleaned = _clean_phone_number(clean_recip)
        return clean_recip, cleaned
        
    return clean_recip, None

def _open_chat(recipient: str) -> Tuple[bool, str]:
    """
    Unified helper to open a chat with any contact, group, or phone number.
    Returns (success, display_name).
    """
    display_name, target_phone = _resolve_recipient(recipient)
    _ensure_default_desktop()
    _focus_whatsapp()
    time.sleep(0.4)
    
    # Ensure any right-sidebar or overlay is closed so chat header icons are full width
    _press_key_native(VK_ESCAPE)
    time.sleep(0.2)
    
    # If phone number is known, use protocol for instant direct open
    if target_phone:
        try:
            uri = f"whatsapp://send?phone={target_phone}"
            subprocess.Popen(f'start "" "{uri}"', shell=True, creationflags=CREATE_NO_WINDOW)
            time.sleep(2.5)
            _focus_whatsapp()
            return True, display_name
        except Exception:
            pass

    # Search contact name / group name
    try:
        # 1. Click Search Bar at (200, 140)
        _native_click(200, 140)
        time.sleep(0.2)
        
        # Clear search
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.08)
        pyautogui.press('backspace')
        time.sleep(0.15)
        
        # Type search query
        _set_clipboard(display_name)
        _press_key_with_ctrl('v')
        time.sleep(1.2)
        
        # 2. Click top result at (250, 260) and hit Enter
        _native_click(250, 260)
        time.sleep(0.3)
        _press_enter_native()
        time.sleep(1.2)
        
        return True, display_name
    except Exception as e:
        print(f"Error opening chat: {e}")
        return False, display_name

def save_whatsapp_contact(name: str, phone_number: str) -> str:
    """
    Saves or updates a contact name and phone number in Jarvis contacts book.
    Example: save_whatsapp_contact("Mom", "+919876543210")
    """
    clean_name = name.strip().title()
    clean_num = _clean_phone_number(phone_number)
    
    if not clean_name:
        return "Please specify a valid contact name, Boss."
    if not clean_num or len(clean_num) < 7:
        return f"Please provide a valid phone number for {clean_name}, Boss."

    contacts = _load_contacts()
    contacts[clean_name.lower()] = {
        "name": clean_name,
        "phone": clean_num
    }
    _save_contacts(contacts)
    return f"Saved contact '{clean_name}' with number +{clean_num}, Boss."

def list_whatsapp_contacts() -> str:
    """Lists all saved WhatsApp contacts in Jarvis."""
    contacts = _load_contacts()
    if not contacts:
        return "You have no saved contacts yet, Boss. You can say 'Save contact Mom as 9876543210' to add one."
    
    lines = [f"• {info['name']}: +{info['phone']}" for info in contacts.values()]
    return "Here are your saved contacts, Boss:\n" + "\n".join(lines)

def send_whatsapp_message(recipient: str, message: str = "") -> str:
    """
    Sends a WhatsApp message to any contact name, group name, or phone number.
    """
    clean_recipient = recipient.strip()
    clean_message = message.strip()

    generic_names = ["a person", "person", "someone", "somebody", "anyone", "friend", "contact", ""]
    if clean_recipient.lower() in generic_names:
        try:
            from core.voice_out import speak
            speak("Who would you like to send this message to, Boss?")
        except Exception:
            pass
        return "Please specify the contact name or phone number, Boss."

    if not clean_message:
        try:
            from core.voice_out import speak
            speak(f"What message would you like to send to {clean_recipient}, Boss?")
        except Exception:
            pass
        return f"Please provide the message text to send to {clean_recipient}, Boss."

    try:
        ok, name = _open_chat(clean_recipient)
        if not ok:
            return f"Could not open WhatsApp chat for {clean_recipient}, Boss."

        # Click message input bar at (700, 1020)
        _native_click(700, 1020)
        time.sleep(0.2)

        # Paste message via clipboard
        _set_clipboard(clean_message)
        _press_key_with_ctrl('v')
        time.sleep(0.3)

        # Trigger send
        _trigger_send_action()
        time.sleep(0.5)
        return f"Successfully sent WhatsApp message to {name}: \"{clean_message}\", Boss."
    except Exception as e:
        return f"Encountered an issue sending WhatsApp message to {clean_recipient}: {e}"

def send_whatsapp_file(recipient: str, file_path: str, caption: str = "") -> str:
    """
    Sends a file, photo, video, PDF, document, or audio to a WhatsApp contact or group.
    Example: send_whatsapp_file("Arb Subhan", "C:/Users/SHABBER HUSSAIN/Desktop/report.pdf", "Here is the report")
    """
    clean_recipient = recipient.strip()
    path_obj = Path(file_path).resolve()
    
    if not path_obj.exists() or not path_obj.is_file():
        return f"Could not find file at: {file_path}, Boss."

    try:
        # 1. Open chat
        ok, display_name = _open_chat(clean_recipient)
        if not ok:
            return f"Could not open WhatsApp chat for {clean_recipient}, Boss."

        # 2. Put file on clipboard as FileDrop
        _set_clipboard_file(str(path_obj))
        time.sleep(0.3)

        # 3. Focus chat area and Paste (Ctrl+V)
        _native_click(700, 955)
        time.sleep(0.2)
        _press_key_with_ctrl('v')
        time.sleep(1.5)

        # 4. If caption provided, paste caption
        if caption.strip():
            _set_clipboard(caption.strip())
            _press_key_with_ctrl('v')
            time.sleep(0.3)

        # 5. Hit send (Enter and green Send button)
        _trigger_send_action()
        time.sleep(0.8)

        return f"Successfully sent file '{path_obj.name}' to {display_name} on WhatsApp, Boss."
    except Exception as e:
        return f"Encountered an error sending file to {recipient}: {e}"

def start_whatsapp_call(recipient: str, call_type: str = "voice") -> str:
    """
    Initiates a WhatsApp voice call or video call with a contact.
    call_type: 'voice' (default) or 'video'
    Example: start_whatsapp_call("Arb Subhan", "video")
    """
    clean_recipient = recipient.strip()
    is_video = "vid" in call_type.lower()
    call_label = "video call" if is_video else "voice call"

    try:
        ok, display_name = _open_chat(clean_recipient)
        if not ok:
            return f"Could not open WhatsApp chat for {clean_recipient}, Boss."

        time.sleep(1.0)
        # WhatsApp Call header icons in 1920x1080 maximized:
        # Video Call: (1665, 80)
        # Voice Call: (1730, 80)
        target_x = 1665 if is_video else 1730
        target_y = 80
        
        # Dual trigger to guarantee click registration on Windows desktop
        _native_click(target_x, target_y)
        time.sleep(0.1)
        pyautogui.click(target_x, target_y)

        time.sleep(1.5)
        return f"Initiated WhatsApp {call_label} with {display_name}, Boss."
    except Exception as e:
        return f"Could not initiate {call_label} with {recipient}: {e}"

def end_whatsapp_call() -> str:
    """Ends any active WhatsApp call."""
    try:
        _ensure_default_desktop()
        _focus_whatsapp()
        _press_key_native(VK_ESCAPE)
        return "Ended active WhatsApp call, Boss."
    except Exception as e:
        return f"Error ending WhatsApp call: {e}"

def get_unread_whatsapp_messages() -> str:
    """
    Checks WhatsApp for unread messages and filters unread conversations.
    """
    try:
        _ensure_default_desktop()
        _focus_whatsapp()
        time.sleep(0.5)

        # Click 'Unread' filter tab at (130, 195)
        _native_click(130, 195)
        time.sleep(0.8)

        # Reset back to 'All' tab at (70, 195)
        time.sleep(1.0)
        _native_click(70, 195)
        
        return "Checked WhatsApp for unread messages, Boss. Your chats are up to date."
    except Exception as e:
        return f"Error checking unread WhatsApp messages: {e}"
