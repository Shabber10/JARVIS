import re
import time
import speech_recognition as sr
from config import STT_ENERGY_THRESHOLD, STT_PAUSE_THRESHOLD, STT_LANG_MAP, CURRENT_LANGUAGE
from core.voice_out import stop_speaking, is_currently_speaking
from core.ui_overlay import get_overlay_ui, STATE_LISTENING, STATE_THINKING, STATE_IDLE

WAKE_WORDS = [
    "hey jarvis", "hi jarvis", "hello jarvis", "ok jarvis", "okay jarvis", "jarvis",
    "हे जार్విస్", "नमस्ते जार्विस", "जार्विस",
    "హే జార్విస్", "నమస్కారం జార్విస్", "జార్విస్"
]

# Words that mean immediate silence/interruption
INTERRUPT_KEYWORDS = [
    "stop", "quiet", "shut up", "be quiet", "silence", "pause", "enough", "cancel",
    "ఆగు", "వద్దు", "ఆపు", "శాంతించు", "రుకో", "चुप", "रुको", "बस"
]

DIRECT_INTENTS = [
    "open", "close", "play", "pause", "resume", "weather", "news", "battery", "volume",
    "brightness", "screenshot", "lock", "timer", "remind", "translate", "calculate", "what is",
    "who is", "how are you", "briefing", "bitcoin", "crypto", "time", "date", "scroll", "type",
    "press", "empty recycle bin", "clean", "optimize", "desktop", "todo", "diagnostic", "storage",
    "wifi", "ip", "convert", "define", "protocol", "whatsapp", "message", "send", "contacts", "text",
    "వాతావరణం", "వార్తలు", "బ్యాటరీ", "పాట", "వాల్యూమ్", "లాక్", "వాట్సాప్", "మెసేజ్",
    "मौसम", "समाचार", "बैटरी", "गाना", "आवाज", "व्हाट्सएप", "मैसेज"
]

class VoiceInput:
    def __init__(self, default_lang: str = "en"):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = STT_ENERGY_THRESHOLD
        self.recognizer.pause_threshold = STT_PAUSE_THRESHOLD
        self.recognizer.dynamic_energy_threshold = True
        self.active_language = default_lang

    def set_language(self, lang_code: str):
        """Sets active language: 'en', 'hi', 'te'."""
        if lang_code in STT_LANG_MAP:
            self.active_language = lang_code
            ui = get_overlay_ui()
            if ui:
                ui.set_language_badge(lang_code.upper())

    def listen_and_transcribe(self, lang: str = None, timeout: int = 10, phrase_time_limit: int = 15, prompt_msg: str = None) -> str:
        """
        Listens to the microphone and converts speech to text.
        Automatically interrupts any ongoing TTS playback when speech starts.
        """
        target_lang_code = STT_LANG_MAP.get(lang or self.active_language, "en-IN")
        ui = get_overlay_ui()
        if ui:
            ui.set_state(STATE_LISTENING, "Listening...", prompt_msg or "Speak your command now...")
        
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                
                # Stop ongoing audio as soon as audio packet is captured
                stop_speaking()
                
                if ui:
                    ui.set_state(STATE_THINKING, "Transcribing...", "Analyzing speech...")
                
                text = self.recognizer.recognize_google(audio, language=target_lang_code)
                clean_text = text.strip()
                if ui and clean_text:
                    ui.set_subtitle(f"\"{clean_text}\"")
                return clean_text
        except Exception:
            if ui:
                ui.set_state(STATE_IDLE, "Ready", "Listening for 'Hey Jarvis'...")
            return ""

    def listen_for_wake_word(self) -> tuple[bool, str]:
        """
        Continuously listens in background for wake word ('Hey Jarvis') or direct command.
        Instant voice barge-in: instantly silences ongoing speech.
        """
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=8)
                
                # Instant interruption if speaking
                if is_currently_speaking():
                    stop_speaking()
                
                target_lang_code = STT_LANG_MAP.get(self.active_language, "en-IN")
                text = self.recognizer.recognize_google(audio, language=target_lang_code).strip()
                lower_text = text.lower()
                
                # Check immediate interrupt keywords
                if any(w == lower_text or lower_text.startswith(w) for w in INTERRUPT_KEYWORDS):
                    stop_speaking()
                    return True, "stop"
                
                # Check explicit wake words
                for wake in WAKE_WORDS:
                    if wake in lower_text:
                        stop_speaking()
                        idx = lower_text.find(wake)
                        remaining = text[idx + len(wake):].strip()
                        remaining = re.sub(r'^[,\.\s\-]+', '', remaining)
                        return True, remaining
                
                # Check direct intent keywords
                if any(k in lower_text for k in DIRECT_INTENTS):
                    stop_speaking()
                    return True, text
                    
                return False, ""
        except sr.WaitTimeoutError:
            return False, ""
        except sr.UnknownValueError:
            return False, ""
        except Exception:
            return False, ""

_voice_in_instance = None

def get_voice_input() -> VoiceInput:
    global _voice_in_instance
    if _voice_in_instance is None:
        _voice_in_instance = VoiceInput(default_lang=CURRENT_LANGUAGE)
    return _voice_in_instance

def listen(lang: str = None, timeout: int = 10) -> str:
    """Helper function to record speech and return transcribed text."""
    return get_voice_input().listen_and_transcribe(lang=lang, timeout=timeout)

def listen_for_wake_word() -> tuple[bool, str]:
    """Helper function to detect wake word or direct speech continuously with barge-in."""
    return get_voice_input().listen_for_wake_word()

def set_active_language(lang: str):
    """Sets active speech recognition language ('en', 'hi', 'te')."""
    get_voice_input().set_language(lang)
