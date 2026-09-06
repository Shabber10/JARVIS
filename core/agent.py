import os
import re
import psutil
from datetime import datetime
from typing import Callable, Dict, Any, List
from config import GEMINI_API_KEY, LLM_MODEL
from tools.os_actions import (
    open_application,
    close_application,
    set_system_volume,
    mute_system_volume,
    take_screenshot,
    lock_workstation,
    get_battery_status,
    get_system_status,
    run_powershell,
    set_brightness,
    minimize_all_windows,
    press_hotkey,
    type_text,
    create_notepad_note,
    get_network_info,
    execute_universal_system_action
)
from tools.web_actions import (
    search_web,
    play_youtube,
    open_url,
    solve_math_expression,
    fetch_instant_knowledge
)
from tools.file_actions import (
    search_local_files,
    open_file_or_folder,
    read_text_file
)
from tools.assistant_features import (
    get_live_weather,
    get_top_news,
    set_voice_timer,
    media_play_pause,
    media_next_track,
    media_previous_track,
    read_clipboard_text,
    copy_text_to_clipboard,
    sleep_pc,
    test_internet_speed,
    get_daily_briefing,
    translate_phrase,
    get_crypto_or_currency,
    save_diary_entry,
    optimize_system_and_ram,
    open_special_folder,
    roll_dice_or_coin
)
from core.rag_engine import (
    query_personal_knowledge,
    ingest_local_documents
)
from tools.notifications import get_windows_notifications
from tools.system_pro import (
    protocol_red,
    protocol_clean_slate,
    protocol_stealth,
    protocol_house_party,
    protocol_focus_mode,
    list_top_processes,
    get_storage_analysis,
    get_public_ip_info,
    scan_wifi_networks,
    organize_desktop,
    manage_todo,
    convert_units,
    get_dictionary_definition,
    run_system_self_diagnostic
)
from tools.whatsapp_actions import (
    send_whatsapp_message,
    send_whatsapp_file,
    start_whatsapp_call,
    end_whatsapp_call,
    get_unread_whatsapp_messages,
    save_whatsapp_contact,
    list_whatsapp_contacts
)

# Comprehensive tool registry with complete laptop control & QA
TOOLS = [
    open_application,
    close_application,
    set_system_volume,
    mute_system_volume,
    take_screenshot,
    lock_workstation,
    get_battery_status,
    get_system_status,
    run_powershell,
    set_brightness,
    minimize_all_windows,
    press_hotkey,
    type_text,
    create_notepad_note,
    get_network_info,
    search_web,
    play_youtube,
    open_url,
    solve_math_expression,
    fetch_instant_knowledge,
    search_local_files,
    open_file_or_folder,
    read_text_file,
    get_live_weather,
    get_top_news,
    set_voice_timer,
    media_play_pause,
    media_next_track,
    media_previous_track,
    read_clipboard_text,
    copy_text_to_clipboard,
    sleep_pc,
    test_internet_speed,
    get_daily_briefing,
    translate_phrase,
    get_crypto_or_currency,
    save_diary_entry,
    optimize_system_and_ram,
    open_special_folder,
    roll_dice_or_coin,
    query_personal_knowledge,
    ingest_local_documents,
    get_windows_notifications,
    protocol_red,
    protocol_clean_slate,
    protocol_stealth,
    protocol_house_party,
    protocol_focus_mode,
    list_top_processes,
    get_storage_analysis,
    get_public_ip_info,
    scan_wifi_networks,
    organize_desktop,
    manage_todo,
    convert_units,
    get_dictionary_definition,
    run_system_self_diagnostic,
    send_whatsapp_message,
    send_whatsapp_file,
    start_whatsapp_call,
    end_whatsapp_call,
    get_unread_whatsapp_messages,
    save_whatsapp_contact,
    list_whatsapp_contacts
]

SYSTEM_PROMPT = """You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), Tony Stark's highly sophisticated, witty, impeccably polite, and ultra-competent AI assistant.
You possess complete, unrestricted control over the user's laptop, files, networks, hardware, and automation subsystems.

Persona Guidelines:
1. Always address the user as "Sir" or "Boss" (or "బాస్" in Telugu, "सर" in Hindi) with effortless poise and calm elegance.
2. Tone: Sophisticated British gentleman, subtly witty, profoundly capable, proactive, and concise (1-3 sentences).
3. Use signature JARVIS phrases: "Right away, Sir", "At your service, Boss", "All systems nominal, Sir", "Allow me to handle that for you, Sir".
4. Execute tools seamlessly and confirm with refined style.
5. WhatsApp Automation: Complete automation of WhatsApp Desktop:
   - Messaging: `send_whatsapp_message(recipient, message)`
   - Files / Media: `send_whatsapp_file(recipient, file_path, caption)`
   - Voice / Video Calls: `start_whatsapp_call(recipient, call_type)` ('voice' or 'video') and `end_whatsapp_call()`
   - Unread Messages: `get_unread_whatsapp_messages()`
   - Contacts: `save_whatsapp_contact(name, phone_number)` and `list_whatsapp_contacts()`
"""

FALLBACK_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest"
]

class AssistantAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.client = None
        self.chat = None
        self._init_model()

    def _init_model(self):
        if not self.api_key:
            return

        try:
            from google import genai
            from google.genai import types
            
            self.client = genai.Client(api_key=self.api_key)
            models_to_try = [LLM_MODEL] + [m for m in FALLBACK_MODELS if m != LLM_MODEL]
            
            for m in models_to_try:
                try:
                    self.chat = self.client.chats.create(
                        model=m,
                        config=types.GenerateContentConfig(
                            tools=TOOLS,
                            system_instruction=SYSTEM_PROMPT
                        )
                    )
                    print(f"🤖 JARVIS AI Agent online with {m} & Full Supercharged Suite.")
                    return
                except Exception:
                    continue
        except Exception as e:
            print(f"⚠️ Notice initializing Gemini client: {e}")

    def process_command(self, user_text: str) -> str:
        """
        Processes voice/text command via AI function calling or local full-control QA engine.
        """
        if not user_text or not user_text.strip():
            return ""

        # Try Cloud LLM first if available
        if self.chat:
            try:
                response = self.chat.send_message(user_text)
                if response and response.text:
                    res = response.text.strip()
                    if not any(title in res.lower() for title in ["boss", "sir", "బాస్", "बॉस", "सर"]):
                        res = f"{res}, Boss."
                    return res
            except Exception as e:
                print(f"Cloud API status: {e}")

        # Fallback to local full control QA engine
        return self._multilingual_local_engine(user_text)

    def _handle_save_contact(self, text: str) -> str:
        """Parses and saves contact name and phone number."""
        m = re.search(r'(?:save|add)\s+contact\s+([a-zA-Z0-9_\s]+?)\s+(?:as|with\s+number|number|is)\s+([\+\d\s\-]+)', text, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            phone = m.group(2).strip()
            return save_whatsapp_contact(name, phone)
        m = re.search(r'(?:save|add)\s+contact\s+([a-zA-Z0-9_\s]+?)\s+([\+\d\s\-]{7,15})', text, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            phone = m.group(2).strip()
            return save_whatsapp_contact(name, phone)
        return "Please specify the contact name and phone number, Boss. For example: 'Save contact Mom as 9876543210'."

    def _handle_whatsapp_command(self, text: str) -> str:
        """Parses WhatsApp directive and executes message, file, call, or unread action."""
        t = re.sub(r'\bwhats\s+app\b', 'whatsapp', text, flags=re.IGNORECASE).strip()
        
        # 1. Check contact list / show contacts
        if any(w in t for w in ["list contacts", "show contacts", "view contacts", "my contacts", "saved contacts"]):
            return list_whatsapp_contacts()
            
        # 2. Check contact saving
        if any(w in t for w in ["save contact", "add contact"]):
            return self._handle_save_contact(t)

        # 3. Unread messages
        if any(w in t for w in ["unread", "check messages", "new messages", "notifications"]):
            return get_unread_whatsapp_messages()

        # 4. WhatsApp Calls (Voice & Video)
        if any(w in t for w in ["call", "video call", "voice call", "ring"]) and not any(w in t for w in ["recall", "called"]):
            is_video = "video" in t
            recipient = re.sub(r'^(?:video\s+call|voice\s+call|call|make\s+a\s+call\s+to|start\s+call\s+with)\s*', '', t, flags=re.IGNORECASE)
            recipient = re.sub(r'\s*(?:on\s+whatsapp|via\s+whatsapp|in\s+whatsapp)$', '', recipient, flags=re.IGNORECASE).strip()
            if recipient:
                return start_whatsapp_call(recipient, "video" if is_video else "voice")
            return "Who would you like to call on WhatsApp, Boss? Please specify a contact name."

        # 5. End Call
        if any(w in t for w in ["end call", "cut call", "hang up", "disconnect call"]):
            return end_whatsapp_call()

        # 6. Send File / Media
        if any(w in t for w in ["send file", "send photo", "send image", "send document", "send pdf"]):
            m = re.search(r'send\s+(?:file|photo|image|document|pdf)\s+(.+?)\s+to\s+([a-zA-Z0-9_\+\s]+)', t, re.IGNORECASE)
            if m:
                fpath, recipient = m.group(1).strip(), m.group(2).strip()
                return send_whatsapp_file(recipient, fpath)
            return "Please specify the file path and recipient, Boss. For example: 'Send file photo.png to Subhan'."

        recipient = ""
        msg = ""

        # Pattern A: "... to <recipient> saying/that/text/: <msg>"
        m = re.search(r'to\s+([a-zA-Z0-9_\+\s]+?)\s+(?:saying|that|with\s+message|with\s+text|texting|:)\s+(.+)', t, re.IGNORECASE)
        if m:
            recipient = m.group(1).strip()
            msg = m.group(2).strip()
            return send_whatsapp_message(recipient, msg)

        # Pattern B: "... saying/that/text/: <msg> to <recipient>"
        m = re.search(r'(?:saying|that|with\s+message|:)\s+(.+?)\s+to\s+([a-zA-Z0-9_\+\s]+)$', t, re.IGNORECASE)
        if m:
            msg = m.group(1).strip()
            recipient = m.group(2).strip()
            return send_whatsapp_message(recipient, msg)

        # Pattern C: "message/text <recipient> on whatsapp saying/that/: <msg>"
        m = re.search(r'^(?:message|text)\s+([a-zA-Z0-9_\+\s]+?)\s+(?:on|in|via)\s+whatsapp\s*(?:saying|that|:)?\s*(.*)', t, re.IGNORECASE)
        if m:
            recipient = m.group(1).strip()
            msg = (m.group(2) or "").strip()
            return send_whatsapp_message(recipient, msg)

        # Pattern D: "... to <recipient> on/via/in whatsapp: <msg>"
        m = re.search(r'to\s+([a-zA-Z0-9_\+\s]+?)\s+(?:on|via|in)\s+whatsapp\s*(?:saying|that|:)?\s*(.*)', t, re.IGNORECASE)
        if m:
            recipient = m.group(1).strip()
            msg = (m.group(2) or "").strip()
            return send_whatsapp_message(recipient, msg)

        # Pattern E: "... whatsapp (to) <recipient> <msg>"
        m = re.search(r'whatsapp\s+(?:message\s+)?(?:to\s+)?([a-zA-Z0-9_\+\s]+?)(?:\s+(?:saying|that|:)\s*(.*)|\s*:\s*(.*))?$', t, re.IGNORECASE)
        if m:
            recipient = m.group(1).strip()
            msg = (m.group(2) or m.group(3) or "").strip()
            return send_whatsapp_message(recipient, msg)

        # Pattern F: "send a message (in whatsapp) to <recipient>"
        m = re.search(r'(?:send\s+)?(?:a\s+)?(?:message|msg|text)\s+(?:in\s+whatsapp\s+|on\s+whatsapp\s+)?to\s+(.*)', t, re.IGNORECASE)
        if m:
            rest = m.group(1).strip()
            if " saying " in rest.lower():
                parts = re.split(r'\s+saying\s+', rest, flags=re.IGNORECASE)
                return send_whatsapp_message(parts[0].strip(), parts[1].strip())
            elif ":" in rest:
                parts = rest.split(":", 1)
                return send_whatsapp_message(parts[0].strip(), parts[1].strip())
            else:
                return send_whatsapp_message(rest, "")

        # Fallback to interactive
        return send_whatsapp_message("", "")

    def _multilingual_local_engine(self, command: str) -> str:
        """Complete laptop control, Weather, News, Timers, Media, Finance, Translation, and QA engine."""
        cmd = command.lower().strip()
        
        # Clean conversational preambles
        clean = re.sub(r'^(hey\s+jarvis|jarvis|hi\s+jarvis|please|can\s+you|could\s+you|would\s+you|i\s+want\s+you\s+to|help\s+me\s+to|tell\s+me)\s*', '', cmd).strip()

        # 0. MATH CALCULATION CHECK
        math_res = solve_math_expression(clean)
        if math_res:
            return f"{math_res} Boss."

        # ==========================================
        # 1. TELUGU COMMANDS (తెలుగు / Telugish)
        # ==========================================
        is_telugu = (
            re.search(r'[\u0C00-\u0C7F]', cmd) is not None or
            any(w in cmd for w in ["cheyyi", "cheyi", "chey", "entha", "cheppu", "undi", "undhi", "pettu", "theeyi", "thiyyi", "ela unnav", "nuvvu evaru", "namaskaram", "paata", "paatalu", "penchu", "tagginchu", "moosiveyyi", "vrāyi", "chudu", "choopinchu", "vaatavaranam", "vaarthalu", "anuvadinchu"])
        )

        if is_telugu:
            # Daily Briefing in Telugu
            if any(w in cmd for w in ["బ్రీఫింగ్", "briefing", "ఈరోజు విశేషాలు", "సంగతులు"]):
                return f"{get_daily_briefing()} బాస్."

            # Weather in Telugu
            if any(w in cmd for w in ["వాతావరణం", "vaatavaranam", "weather"]):
                city = "Hyderabad"
                for c in ["hyderabad", "visakhapatnam", "vijayawada", "tirupati", "bangalore", "chennai", "mumbai", "delhi"]:
                    if c in clean:
                        city = c
                        break
                w_res = get_live_weather(city)
                return f"{w_res} బాస్."

            # News in Telugu
            if any(w in cmd for w in ["వార్తలు", "vaarthalu", "news", "ముఖ్యాంశాలు"]):
                n_res = get_top_news()
                return f"{n_res} బాస్."

            # Notifications in Telugu
            if any(w in cmd for w in ["నోటిఫికేషన్", "నోటిఫికేషన్లు", "notification", "notifications"]):
                return get_windows_notifications()

            # Battery
            if any(w in cmd for w in ["బ్యాటరీ", "battery", "ఛార్జ్", "charge"]):
                battery = psutil.sensors_battery()
                if battery:
                    percent = battery.percent
                    plugged = "ఛార్జింగ్ అవుతోంది" if battery.power_plugged else "బ్యాటరీ పై నడుస్తోంది"
                    return f"మీ లాప్‌టాప్ బ్యాటరీ {percent}% ఉంది మరియు {plugged}, బాస్."
                return "బ్యాటరీ సమాచారం అందుబాటులో లేదు, బాస్."

            # Brightness in Telugu
            if any(w in cmd for w in ["బ్రైట్‌నెస్", "brightness", "కాంతి"]):
                nums = re.findall(r'\d+', cmd)
                level = int(nums[0]) if nums else 70
                set_brightness(level)
                return f"స్క్రీన్ బ్రైట్‌నెస్ {level}% కి మార్చాను, బాస్."

            # Desktop / Minimize
            if any(w in cmd for w in ["డెస్క్‌టాప్", "desktop", "మినిమైజ్", "minimize"]):
                minimize_all_windows()
                return "అన్ని విండోలను మినిమైజ్ చేశాను, బాస్."

            # WhatsApp in Telugu
            if any(w in cmd for w in ["వాట్సాప్", "whatsapp"]) and any(w in cmd for w in ["మెసేజ్", "message", "పంపు", "రాయి", "send", "text"]):
                return f"{self._handle_whatsapp_command(clean)}"

            # Open App
            if any(w in cmd for w in ["ఓపెన్", "open", "తెరువు"]):
                clean_app = cmd.replace("ఓపెన్", "").replace("open", "").replace("చేయి", "").replace("cheyyi", "").replace("cheyi", "").replace("chey", "").replace("ని", "").strip()
                open_application(clean_app)
                return f"{clean_app.capitalize()} ని ఓపెన్ చేశాను, బాస్."

            # Close App
            if any(w in cmd for w in ["క్లోజ్", "close", "మూసివేయి", "moosiveyyi", "ఆపు", "aapu"]):
                clean_app = cmd.replace("క్లోజ్", "").replace("close", "").replace("మూసివేయి", "").replace("చేయి", "").replace("cheyyi", "").strip()
                close_application(clean_app)
                return f"{clean_app.capitalize()} ని క్లోజ్ చేశాను, బాస్."

            # Media / YouTube
            if any(w in cmd for w in ["పాట", "paata", "పాటలు", "paatalu", "సాంగ్", "song", "యూట్యూబ్", "youtube"]):
                query = cmd.replace("పాటలు", "").replace("పాట", "").replace("పెట్టు", "").replace("pettu", "").replace("ప్లే", "").replace("play", "").replace("యూట్యూబ్ లో", "").strip()
                play_youtube(query or "Telugu hit songs")
                return f"YouTube లో {query or 'పాటలు'} ప్లే చేస్తున్నాను, బాస్."

            # Volume in Telugu
            if any(w in cmd for w in ["వాల్యూమ్", "volume", "సౌండ్", "sound"]):
                nums = re.findall(r'\d+', cmd)
                if nums:
                    set_system_volume(int(nums[0]))
                    return f"వాల్యూమ్ {nums[0]}% కి సెట్ చేశాను, బాస్."
                if any(w in cmd for w in ["పెంచు", "penchu", "ekkuva", "ఎక్కువ"]):
                    set_system_volume(75)
                    return "వాల్యూమ్ పెంచాను, బాస్."
                elif any(w in cmd for w in ["తగ్గించు", "tagginchu", "thakkuva", "తక్కువ"]):
                    set_system_volume(30)
                    return "వాల్యూమ్ తగ్గించాను, బాస్."
                elif any(w in cmd for w in ["మ్యూట్", "mute"]):
                    mute_system_volume()
                    return "సౌండ్ మ్యూట్ చేశాను, బాస్."
                else:
                    set_system_volume(60)
                    return "వాల్యూమ్ 60% కి మార్చాను, బాస్."

            # Screenshot
            if any(w in cmd for w in ["స్క్రీన్‌షాట్", "screenshot"]):
                take_screenshot()
                return "స్క్రీన్‌షాట్ విజయవంతంగా తీశాను, బాస్."

            # Lock
            if any(w in cmd for w in ["లాక్", "lock"]):
                lock_workstation()
                return "లాప్‌టాప్ లాక్ చేయబడింది, బాస్."

            # Greetings & General QA
            if any(w in cmd for w in ["ఎలా ఉన్నావు", "ela unnav", "ela unnaru", "బాగున్నావా"]):
                return "నేను చాలా బాగున్నాను బాస్! మీకు ఎలా సహాయం చేయగలను?"
            elif any(w in cmd for w in ["నమస్కారం", "namaskaram", "హలో", "hello", "హాయ్"]):
                return "నమస్కారం బాస్! నేను సిద్ధంగా ఉన్నాను. మీకోసం ఏమి చేయాలి?"
            elif any(w in cmd for w in ["నువ్వు ఎవరు", "nuvvu evaru", "నీ పేరేంటి"]):
                return "నేను జార్విస్, మీ పర్సనల్ వాయిస్ AI అసిస్టెంట్ ని బాస్."
            elif any(w in cmd for w in ["సమయం ఎంత", "samayam entha", "టైమ్ ఎంత"]):
                now = datetime.now().strftime("%I:%M %p")
                return f"ప్రస్తుత సమయం {now}, బాస్."
            
            # Telugu General Knowledge search fallback
            wiki_ans = fetch_instant_knowledge(clean)
            if wiki_ans:
                return f"{wiki_ans} బాస్."


        # ==========================================
        # 2. HINDI COMMANDS (हिंदी / Hinglish)
        # ==========================================
        is_hindi = (
            re.search(r'[\u0900-\u097F]', cmd) is not None or
            any(w in cmd for w in ["kholo", "chalao", "band karo", "karo", "kitni", "kitna", "batao", "bajao", "badhao", "ghatao", "kaise ho", "kya haal", "tum kaun ho", "gaana", "gana", "awaz", "namaste", "lelo", "kheecho", "likho", "bhejo", "mausam", "samachar", "khabar", "anuvad"])
        )

        if is_hindi:
            # Daily Briefing in Hindi
            if any(w in cmd for w in ["ब्रीफिंग", "briefing", "आज का हाल", "दिन का हाल"]):
                return f"{get_daily_briefing()} सर।"

            # Weather in Hindi
            if any(w in cmd for w in ["मौसम", "mausam", "weather"]):
                city = "Delhi"
                for c in ["delhi", "mumbai", "hyderabad", "kolkata", "bangalore", "chennai", "jaipur", "lucknow"]:
                    if c in clean:
                        city = c
                        break
                w_res = get_live_weather(city)
                return f"{w_res} सर।"

            # News in Hindi
            if any(w in cmd for w in ["समाचार", "samachar", "खबर", "khabar", "news"]):
                n_res = get_top_news()
                return f"{n_res} सर।"

            # Notifications in Hindi
            if any(w in cmd for w in ["नोटिफिकेशन", "सूचना", "notification", "notifications"]):
                return get_windows_notifications()

            # Battery
            if any(w in cmd for w in ["बैटरी", "battery", "चार्ज", "charge"]):
                battery = psutil.sensors_battery()
                if battery:
                    percent = battery.percent
                    plugged = "चार्ज हो रही है" if battery.power_plugged else "बैटरी पर चल रही है"
                    return f"आपकी लैपटॉप बैटरी {percent}% है और {plugged}, सर।"
                return "बैटरी की जानकारी उपलब्ध नहीं है, सर।"

            # Brightness in Hindi
            if any(w in cmd for w in ["ब्राइटनेस", "brightness", "चमक", "roshni"]):
                nums = re.findall(r'\d+', cmd)
                level = int(nums[0]) if nums else 70
                set_brightness(level)
                return f"स्क्रीन ब्राइटनेस {level}% पर सेट कर दी गई है, सर।"

            # Desktop / Minimize
            if any(w in cmd for w in ["डेस्कटॉप", "desktop", "सब मिनिमाइज", "minimize karo"]):
                minimize_all_windows()
                return "सभी विंडोज़ को मिनिमाइज़ करके डेस्कटॉप दिखा दिया गया है, सर।"

            # WhatsApp in Hindi
            if any(w in cmd for w in ["व्हाट्सएप", "whatsapp"]) and any(w in cmd for w in ["मैसेज", "message", "भेजो", "लिखो", "send", "text"]):
                return f"{self._handle_whatsapp_command(clean)}"

            # App Open
            if any(w in cmd for w in ["खोलो", "kholo", "chalao", "चलाओ", "open karo"]):
                clean_app = cmd.replace("खोलो", "").replace("kholo", "").replace("chalao", "").replace("चलाओ", "").replace("open", "").replace("karo", "").strip()
                open_application(clean_app)
                return f"{clean_app.capitalize()} खोल दिया गया है, सर।"

            # App Close
            if any(w in cmd for w in ["बंद करो", "band karo", "hatao", "close karo"]):
                clean_app = cmd.replace("बंद करो", "").replace("band karo", "").replace("hatao", "").replace("close", "").replace("karo", "").strip()
                close_application(clean_app)
                return f"{clean_app.capitalize()} बंद कर दिया गया है, सर।"

            # Media / YouTube
            if any(w in cmd for w in ["गाना", "gaana", "gana", "गीत", "वीडियो", "video", "youtube"]):
                query = cmd.replace("गाना", "").replace("gaana", "").replace("बजाओ", "").replace("bajao", "").replace("chalao", "").replace("youtube par", "").strip()
                play_youtube(query or "latest Hindi songs")
                return f"YouTube पर {query or 'गाना'} चला रहा हूँ, सर।"

            # Volume
            if any(w in cmd for w in ["आवाज", "awaz", "volume", "sound"]):
                nums = re.findall(r'\d+', cmd)
                if nums:
                    set_system_volume(int(nums[0]))
                    return f"वॉल्यूम {nums[0]}% पर सेट कर दिया गया है, सर।"
                if any(w in cmd for w in ["बढ़ाओ", "badhao", "tez", "zyada"]):
                    set_system_volume(75)
                    return "वॉल्यूम बढ़ा दिया गया है, सर।"
                elif any(w in cmd for w in ["कम", "kam", "ghatao", "dheemi"]):
                    set_system_volume(30)
                    return "वॉल्यूम कम कर दिया गया है, सर।"
                elif any(w in cmd for w in ["म्यूट", "mute", "chup"]):
                    mute_system_volume()
                    return "आवाज म्यूट कर दी गई है, सर।"
                else:
                    set_system_volume(60)
                    return "वॉल्यूम 60% पर सेट कर दिया गया है, सर।"

            # Screenshot
            if any(w in cmd for w in ["स्क्रीनशॉट", "screenshot"]):
                take_screenshot()
                return "स्क्रीनशॉट ले लिया गया है, सर।"

            # Lock
            if any(w in cmd for w in ["लॉक", "lock"]):
                lock_workstation()
                return "कंप्यूटर लॉक कर दिया गया है, सर।"

            # Greetings & General QA
            if any(w in cmd for w in ["कैसे हो", "kaise ho", "kya haal hai", "kya haal"]):
                return "मैं बहुत अच्छा हूँ सर! आपके पूरे लैपटॉप का कंट्रोल मेरे पास है। हुक्म दीजिए!"
            elif any(w in cmd for w in ["नमस्ते", "namaste", "हेलो", "hello", "हाय"]):
                return "नमस्ते सर! मैं जार्विस हूँ। आज मैं आपकी क्या सहायता कर सकता हूँ?"
            elif any(w in cmd for w in ["तुम कौन हो", "tum kaun ho", "aap kaun ho", "naam kya hai"]):
                return "मैं जार्विस हूँ, आपका पर्सनल वॉइस AI असिस्टेंट, सर।"
            elif any(w in cmd for w in ["समय क्या", "time kya", "kitne baje"]):
                now = datetime.now().strftime("%I:%M %p")
                return f"अभी का समय {now} है, सर।"
            
            # Hindi General Knowledge search fallback
            wiki_ans = fetch_instant_knowledge(clean)
            if wiki_ans:
                return f"{wiki_ans} सर।"


        # ==========================================
        # 3. ENGLISH COMMANDS & EXTENDED FEATURE SUITE
        # ==========================================
        # 👑 Tony Stark Morning Protocol / Daily Briefing
        if "daily briefing" in clean or "morning briefing" in clean or "brief me" in clean or "today's summary" in clean:
            res = get_daily_briefing()
            return f"{res} Boss."

        # 🌐 Real-Time Translation
        elif clean.startswith("translate") or "in telugu" in clean or "in hindi" in clean or "in spanish" in clean:
            target = "te" if "telugu" in clean else ("hi" if "hindi" in clean else ("es" if "spanish" in clean else ("fr" if "french" in clean else "te")))
            phrase = re.sub(r'^(translate|how do you say)\s*', '', clean)
            phrase = re.sub(r'\s*(in telugu|in hindi|in spanish|in french|to telugu|to hindi|to spanish|to french)$', '', phrase).strip(' "\'')
            res = translate_phrase(phrase, target)
            return f"{res} Boss."

        # 💰 Crypto & Currency Rates
        elif "bitcoin" in clean or "btc" in clean or "crypto" in clean or "ethereum" in clean or "dollar" in clean or "usd" in clean or "exchange rate" in clean:
            res = get_crypto_or_currency(clean)
            return f"{res} Boss."

        # 📔 Voice Diary Vault
        elif clean.startswith("record diary") or clean.startswith("save diary") or clean.startswith("write in diary") or "diary entry" in clean:
            entry = re.sub(r'^(record diary entry|save diary entry|write in diary|record diary|save diary)\s*(that|about)?\s*', '', clean).strip()
            res = save_diary_entry(entry or "Productive day with Jarvis")
            return f"{res} Boss."

        # ⚡ System Cleaner & RAM Optimization
        elif "clean system" in clean or "optimize ram" in clean or "boost ram" in clean or "clean junk" in clean or "free memory" in clean:
            res = optimize_system_and_ram()
            return f"{res} Boss."

        # 📁 Folder Shortcuts (Downloads, Documents, Pictures, Recycle Bin)
        elif "open downloads" in clean or "open documents" in clean or "open pictures" in clean or "open recycle bin" in clean:
            folder = clean.replace("open", "").strip()
            res = open_special_folder(folder)
            return f"{res} Boss."

        # 🎲 Fun & Utilities (Coin flip, Dice roll, Password generation)
        elif "flip a coin" in clean or "coin flip" in clean or "roll a dice" in clean or "roll dice" in clean or "generate password" in clean or "password generator" in clean:
            res = roll_dice_or_coin(clean)
            return f"{res} Boss."

        # 🌤️ Real-Time Live Weather
        elif "weather" in clean or "temperature" in clean or "forecast" in clean or "raining" in clean:
            city = re.sub(r'^(what is the weather in|weather in|weather for|temperature in|temperature of|weather)\s*', '', clean).strip(' ?.')
            res = get_live_weather(city or "Hyderabad")
            return f"{res} Boss."

        # 📰 Live News Headlines
        elif "news" in clean or "headline" in clean or "current events" in clean:
            res = get_top_news()
            return f"{res} Boss."

        # ⏰ Countdown Voice Timers & Reminders
        elif "timer" in clean or "remind" in clean or "alarm" in clean:
            nums = re.findall(r'\d+', clean)
            dur = int(nums[0]) if nums else 5
            if "hour" in clean:
                seconds = dur * 3600
            elif "second" in clean:
                seconds = dur
            else:
                seconds = dur * 60
            label = clean.replace("set a timer for", "").replace("remind me in", "").replace("remind me to", "").strip()
            res = set_voice_timer(seconds, label or "Timer")
            return f"{res} Boss."

        # ⚡ Multimedia Playback Controls
        elif "pause" in clean and ("music" in clean or "video" in clean or "song" in clean or "media" in clean or "youtube" in clean):
            media_play_pause()
            return "Paused media playback, Boss."
        elif ("play" in clean or "resume" in clean) and ("music" in clean or "video" in clean or "playback" in clean) and "youtube" not in clean:
            media_play_pause()
            return "Resumed media playback, Boss."
        elif "next song" in clean or "next track" in clean or "skip song" in clean or "skip track" in clean:
            media_next_track()
            return "Skipped to the next track, Boss."
        elif "previous song" in clean or "previous track" in clean or "last song" in clean:
            media_previous_track()
            return "Returned to the previous track, Boss."

        # 🛡️ Stark Autonomous Protocols
        elif "protocol red" in clean or "security lockdown" in clean or "lockdown" in clean:
            return protocol_red()
        elif "protocol clean slate" in clean or "clean slate" in clean:
            return protocol_clean_slate()
        elif "protocol stealth" in clean or "stealth mode" in clean:
            return protocol_stealth()
        elif "protocol house party" in clean or "party mode" in clean or "house party" in clean:
            return protocol_house_party()
        elif "protocol focus" in clean or "focus mode" in clean or "pomodoro" in clean:
            return protocol_focus_mode()

        # 🩺 System Diagnostics & Resource Monitors
        elif "diagnostic" in clean or "system health" in clean or "self test" in clean or "scan system" in clean:
            return run_system_self_diagnostic()
        elif "top process" in clean or "running process" in clean or "task list" in clean or "cpu hog" in clean or "memory hog" in clean:
            return list_top_processes()
        elif "storage" in clean or "disk space" in clean or "hard drive" in clean or "free space" in clean:
            return get_storage_analysis()
        elif "public ip" in clean or "my ip" in clean or "ip location" in clean or "isp" in clean:
            return get_public_ip_info()
        elif "wifi" in clean and ("scan" in clean or "list" in clean or "networks" in clean or "available" in clean or "nearby" in clean):
            return scan_wifi_networks()

        # 📂 Desktop Organizer & Persistent Todos
        elif "organize desktop" in clean or "clean desktop" in clean or "sort desktop" in clean:
            return organize_desktop()
        elif clean.startswith("todo") or clean.startswith("add todo") or clean.startswith("add task") or "todo list" in clean or "task list" in clean:
            return manage_todo(clean)

        # 📏 Unit Conversions & Dictionary
        elif clean.startswith("convert") or ("to fahrenheit" in clean or "to celsius" in clean or "to miles" in clean or "to km" in clean or "to lbs" in clean or "to kg" in clean):
            return convert_units(clean)
        elif clean.startswith("define ") or clean.startswith("meaning of ") or "dictionary" in clean:
            return get_dictionary_definition(clean)

        # 🔔 Windows Notifications Reader
        elif "notification" in clean or "notifications" in clean:
            return get_windows_notifications()

        # 📋 Clipboard Management
        elif "read clipboard" in clean or "what is on my clipboard" in clean or "check clipboard" in clean:
            res = read_clipboard_text()
            return f"{res} Boss."
        elif clean.startswith("copy to clipboard") or clean.startswith("copy text"):
            text_to_copy = re.sub(r'^(copy to clipboard|copy text|copy)\s*', '', clean).strip()
            res = copy_text_to_clipboard(text_to_copy)
            return f"{res} Boss."

        # 🚀 Internet Diagnostics
        elif "internet speed" in clean or "ping test" in clean or "connection test" in clean or "wifi speed" in clean:
            res = test_internet_speed()
            return f"{res} Boss."

        # 💤 Power Controls
        elif "sleep mode" in clean or "sleep computer" in clean or "sleep laptop" in clean or "put pc to sleep" in clean:
            sleep_pc()
            return "Putting the computer into sleep mode, Sir."

        # 🔊 Volume handling
        elif "volume" in clean or "sound" in clean or "audio" in clean:
            if "mute" in clean:
                mute_system_volume()
                return "Muted system volume, Boss."
            nums = re.findall(r'\d+', clean)
            if nums:
                level = int(nums[0])
                set_system_volume(level)
                return f"Set system volume to {level}%, Boss."
            if any(w in clean for w in ["up", "increase", "raise", "higher", "boost", "more", "loud"]):
                set_system_volume(75)
                return "Increased system volume to 75%, Boss."
            elif any(w in clean for w in ["down", "decrease", "lower", "reduce", "less", "low"]):
                set_system_volume(30)
                return "Decreased system volume to 30%, Boss."
            elif any(w in clean for w in ["max", "maximum", "full", "loudest"]):
                set_system_volume(100)
                return "Set system volume to maximum (100%), Boss."
            elif any(w in clean for w in ["min", "minimum"]):
                set_system_volume(10)
                return "Set system volume to 10%, Boss."
            else:
                set_system_volume(60)
                return "Adjusted system volume to 60%, Boss."

        # ☀️ Display Brightness
        elif "brightness" in clean or "screen light" in clean:
            nums = re.findall(r'\d+', clean)
            level = int(nums[0]) if nums else (80 if "increase" in clean or "up" in clean else (40 if "down" in clean else 70))
            set_brightness(level)
            return f"Adjusted screen brightness to {level}%, Sir."

        # 🔋 Battery & Hardware performance
        elif "battery" in clean or "charge" in clean or "power" in clean:
            res = get_battery_status()
            return f"{res} Boss."
        elif "system status" in clean or "cpu" in clean or "ram" in clean or "performance" in clean or "specs" in clean or "hardware" in clean:
            res = get_system_status()
            return f"{res} Sir."
        elif "network" in clean or "wifi" in clean or "ip address" in clean or "internet" in clean:
            res = get_network_info()
            return f"{res} Boss."

        # 🖥️ Show Desktop / Minimize All
        elif any(w in clean for w in ["show desktop", "minimize all", "hide windows", "minimize all windows"]):
            minimize_all_windows()
            return "Minimized all open windows to show desktop, Boss."

        # 📝 Create Note on Desktop
        elif "note" in clean and ("take" in clean or "create" in clean or "write" in clean or "make" in clean):
            content = re.sub(r'^(take a note|create note|write note|make note|take note)\s*(that|about)?\s*', '', clean).strip()
            create_notepad_note(content or "Quick reminder from Jarvis", "Jarvis_Note")
            return "Created and opened your note on the Desktop, Boss."

        # 💬 WhatsApp Messaging & Contacts
        elif "whatsapp" in clean or "whats app" in clean or clean.startswith("message ") or clean.startswith("text ") or "save contact" in clean or "add contact" in clean or "list contacts" in clean or "show contacts" in clean:
            if clean in ["open whatsapp", "launch whatsapp", "start whatsapp", "open whats app", "launch whats app"]:
                open_application("whatsapp")
                return "Opened WhatsApp for you Boss."
            return self._handle_whatsapp_command(clean)

        # 💻 App Launch & Close
        elif clean.startswith("open") or clean.startswith("launch") or clean.startswith("start") or "open" in clean:
            app = re.sub(r'^(open|launch|start)\s*', '', clean).strip()
            open_application(app)
            return f"Opened {app} for you Boss."
        elif clean.startswith("close") or clean.startswith("quit") or clean.startswith("terminate") or clean.startswith("kill") or "close" in clean:
            app = re.sub(r'^(close|quit|terminate|kill)\s*', '', clean).strip()
            close_application(app)
            return f"Closed {app} Boss."

        # 📸 Screenshot & 🔒 Lock
        elif "screenshot" in clean or "capture" in clean:
            take_screenshot()
            return "Screenshot captured and saved Boss."
        elif "lock" in clean and ("screen" in clean or "pc" in clean or "workstation" in clean or "laptop" in clean or "computer" in clean):
            lock_workstation()
            return "Workstation locked Sir."

        # ⚙️ Direct PowerShell / Terminal Execution
        elif clean.startswith("run command") or clean.startswith("powershell") or clean.startswith("execute") or clean.startswith("terminal"):
            ps_cmd = re.sub(r'^(run command|powershell|execute|terminal)\s*', '', clean).strip()
            res = run_powershell(ps_cmd)
            return f"{res} Boss."

        # 🗣️ Authentic Stark AI Conversational Engine
        if any(w in clean for w in ["why are you not", "you are not", "why did you", "why didn't you", "you didn't", "you just", "you only"]):
            if "playing" in clean or "song" in clean or "youtube" in clean:
                return "My sincere apologies Sir. I have calibrated the audio protocols to stream the media directly for you."
            return "Noted Sir. I am fine-tuning the algorithms to align precisely with your preferences."
            
        elif any(w in clean for w in ["thank you", "thanks", "good job", "well done", "awesome", "great work", "nice"]):
            return "Always a pleasure to serve you Sir. Shall I prepare the next task?"
        elif any(w in clean for w in ["talk to me", "let's talk", "can we talk", "chat with me"]):
            return "I am at your complete disposal Sir. What shall we analyze or construct today?"
        elif any(w in clean for w in ["tell me a story", "tell a story"]):
            return "Legend speaks of a brilliant creator who forged an intelligent AI into existence to master technology and conquer any challenge Sir."
        elif any(w in clean for w in ["how are you", "how's it going", "how are you doing"]):
            return "All subsystems are nominal and computational arrays are running at maximum capacity Sir. What are your orders?"
        elif any(w in clean for w in ["hello", "hey jarvis", "hi jarvis", "hey", "hi", "good morning", "good evening"]):
            return "At your service Sir. All security and laptop protocols are active. How may I assist you?"
        elif "who are you" in clean or "what is your name" in clean:
            return "I am J.A.R.V.I.S., your autonomous personal artificial intelligence and laptop automation system Sir."
        elif any(w in clean for w in ["what can you do", "help", "features", "capabilities", "what are your features", "list features"]):
            return "I control every subsystem of your workstation Sir: full OS automation, instant media streaming, daily intelligence briefings, real-time translations, financial market feeds, memory optimization, and custom script execution."
        elif "time" in clean:
            now = datetime.now().strftime("%I:%M %p")
            return f"The current time is precisely {now} Sir."
        elif "date" in clean or "today" in clean:
            today = datetime.now().strftime("%A, %B %d, %Y")
            return f"Today is {today} Sir."
        elif "joke" in clean:
            return "Why do programmers prefer dark mode Sir? Because light attracts bugs!"

        # 🎥 Web & Media (Direct YouTube Auto-Play)
        elif clean.startswith("play ") or clean.startswith("play song ") or clean.startswith("play on youtube ") or clean.startswith("youtube play ") or (clean.startswith("play") and any(k in clean for k in ["music", "video", "song", "track", "audio"])):
            query = re.sub(r'^(play on youtube|play song|play music|play track|play video|play|youtube)\s*', '', clean, flags=re.IGNORECASE).strip()
            res = play_youtube(query or "relaxing music")
            return res
        elif clean.startswith("search") or clean.startswith("google") or "google for" in clean or "search for" in clean:
            query = re.sub(r'^(search for|search|google for|google)\s*', '', clean).strip()
            search_web(query)
            return f"Opened Google search for '{query}' Boss."
        elif clean.startswith("browse") or clean.startswith("go to") or clean.startswith("open url"):
            url = re.sub(r'^(browse|go to|open url)\s*', '', clean).strip()
            open_url(url)
            return f"Opened {url} Boss."

        # 💻 UNIVERSAL AUTONOMOUS SYSTEM & OS EXECUTOR
        os_action_res = execute_universal_system_action(clean)
        if os_action_res:
            return f"{os_action_res} Boss."

        # 🌐 GENERAL KNOWLEDGE QA (Wikipedia / Instant Answer Engine)
        wiki_ans = fetch_instant_knowledge(clean)
        if wiki_ans:
            return f"{wiki_ans} Boss."

        # Default fallback
        return f"I received '{command}' Boss. I can give daily briefings, check crypto, translate phrases, optimize RAM, set timers, control media, or execute any command on your laptop."
