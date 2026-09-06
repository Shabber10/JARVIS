import sys
import asyncio
import os
import re
import uuid
import threading
from pathlib import Path

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame
import edge_tts
import speech_recognition as sr
from config import VOICE_MAP, TTS_RATE, TTS_PITCH, TEMP_DIR
from core.ui_overlay import get_overlay_ui, STATE_SPEAKING, STATE_IDLE

# Global interruption control
_is_interrupted = False
_is_speaking = False
_speech_lock = threading.Lock()

# Initialize pygame mixer for audio playback
try:
    pygame.mixer.init()
except Exception as e:
    print(f"Warning: Failed to initialize pygame mixer: {e}")

def stop_speaking():
    """
    Instantly interrupts and stops any ongoing audio playback.
    """
    global _is_interrupted, _is_speaking
    _is_interrupted = True
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
    except Exception:
        pass
    _is_speaking = False
    ui = get_overlay_ui()
    if ui:
        ui.set_state(STATE_IDLE, "Interrupted", "Audio halted")

def is_currently_speaking() -> bool:
    """Returns True if Jarvis is currently outputting audio."""
    global _is_speaking
    return _is_speaking

def detect_language(text: str) -> str:
    """
    Detects if text contains Telugu, Hindi (Devanagari), or English characters.
    """
    if re.search(r'[\u0C00-\u0C7F]', text):
        return "te"
    if re.search(r'[\u0900-\u097F]', text):
        return "hi"
    return "en"

async def _synthesize_edge_tts(text: str, output_path: str, voice: str):
    """Synthesizes text using Edge-TTS into an MP3 file."""
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=TTS_RATE,
        pitch=TTS_PITCH
    )
    await communicate.save(output_path)

def _barge_in_monitor(stop_event: threading.Event):
    """
    Runs in background while audio is playing.
    If user says 'Jarvis', 'Stop', or starts speaking, immediately halts playback.
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 400
    recognizer.dynamic_energy_threshold = False
    
    try:
        with sr.Microphone() as source:
            while not stop_event.is_set() and _is_speaking:
                try:
                    audio = recognizer.listen(source, timeout=0.6, phrase_time_limit=3)
                    # Speech was detected during playback -> Halt immediately!
                    stop_speaking()
                    break
                except sr.WaitTimeoutError:
                    continue
                except Exception:
                    break
    except Exception:
        pass

def speak(text: str, custom_voice: str = None, interruptible: bool = True):
    """
    Speaks the given text using high quality neural voice corresponding
    to the detected language (English / Hindi / Telugu).
    Supports instant live microphone barge-in and wake word interruption.
    """
    global _is_interrupted, _is_speaking

    if not text or not text.strip():
        return

    # Clean text of markdown formatting before speaking
    clean_text = text.replace("*", "").replace("#", "").replace("`", "").replace("[", "").replace("]", "")
    
    try:
        print(f"🔊 Assistant: {clean_text}")
    except Exception:
        print(f"[Assistant]: {clean_text.encode('utf-8', 'ignore').decode('utf-8')}")
    
    # Notify UI overlay of speaking state
    ui = get_overlay_ui()
    if ui:
        ui.set_state(STATE_SPEAKING, "Speaking...", clean_text)
    
    # Detect language and select appropriate voice
    lang = detect_language(clean_text)
    selected_voice = custom_voice or VOICE_MAP.get(lang, "en-GB-RyanNeural")
    
    # Use unique audio filename to avoid file locking collisions
    file_id = uuid.uuid4().hex[:8]
    temp_audio_file = TEMP_DIR / f"tts_{lang}_{file_id}.mp3"
    
    with _speech_lock:
        _is_interrupted = False
        _is_speaking = True
        
        try:
            # Run async synthesis
            asyncio.run(_synthesize_edge_tts(clean_text, str(temp_audio_file), selected_voice))
            
            # Play audio using pygame mixer
            if pygame.mixer.get_init() and temp_audio_file.exists():
                pygame.mixer.music.load(str(temp_audio_file))
                pygame.mixer.music.play()
                
                # Launch live barge-in listener thread
                stop_event = threading.Event()
                if interruptible:
                    monitor_thread = threading.Thread(target=_barge_in_monitor, args=(stop_event,), daemon=True)
                    monitor_thread.start()
                
                # Interruption monitor loop (50ms granularity)
                while pygame.mixer.music.get_busy():
                    if interruptible and _is_interrupted:
                        pygame.mixer.music.stop()
                        break
                    pygame.time.Clock().tick(20)
                    
                stop_event.set()
                pygame.mixer.music.unload()
        except Exception as e:
            pass
        finally:
            _is_speaking = False
            if ui:
                ui.set_state(STATE_IDLE, "Ready", "Listening for 'Hey Jarvis'...")
            try:
                if temp_audio_file.exists():
                    temp_audio_file.unlink()
            except Exception:
                pass

if __name__ == "__main__":
    print("Testing Multilingual Speech with Live Barge-In Interruption...")
    speak("Hello! I am Jarvis, your personal artificial intelligence assistant. You can interrupt me at any time by saying Jarvis or stop.")
