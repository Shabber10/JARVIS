import os
from pathlib import Path
from dotenv import load_dotenv

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "documents"
DB_DIR = DATA_DIR / "chroma_db"
TEMP_DIR = BASE_DIR / "temp"

DOCS_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

# LLM & API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.7-flash")

# Multi-Language Settings
# Options: "auto", "en", "hi", "te"
CURRENT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")

# Neural Voices mapping for Edge-TTS (Iconic Iron Man British JARVIS)
VOICE_MAP = {
    "en": "en-GB-RyanNeural",         # Sophisticated British Gentleman (Paul Bettany JARVIS)
    "hi": "hi-IN-MadhurNeural",       # Natural Hindi Male
    "te": "te-IN-MohanNeural"         # Natural Telugu Male
}

# STT Language codes for Google Speech Recognition
STT_LANG_MAP = {
    "en": "en-IN",
    "hi": "hi-IN",
    "te": "te-IN"
}

TTS_VOICE = os.getenv("TTS_VOICE", VOICE_MAP.get(CURRENT_LANGUAGE, "en-GB-RyanNeural"))
TTS_RATE = "-3%"
TTS_PITCH = "-5Hz"

# STT Configuration
STT_ENERGY_THRESHOLD = 800  # Microphone sensitivity (higher = less sensitive to ambient noise)
STT_PAUSE_THRESHOLD = 1.0   # Seconds of silence indicating speech end
