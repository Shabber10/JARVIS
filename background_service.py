import sys
import os
import time
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import GEMINI_API_KEY, DOCS_DIR, CURRENT_LANGUAGE
from core.agent import AssistantAgent
from core.voice_in import listen_for_wake_word, listen, set_active_language, get_voice_input
from core.voice_out import speak, stop_speaking
from core.rag_engine import ingest_local_documents
from core.ui_overlay import init_overlay_ui, get_overlay_ui, STATE_IDLE, STATE_LISTENING, STATE_THINKING, STATE_SPEAKING, STATE_OFFLINE

_shutdown_requested = False

def on_mic_click():
    stop_speaking()
    ui = get_overlay_ui()
    if ui:
        ui.set_state(STATE_LISTENING, "Listening...", "Push-to-talk activated...")

def on_hangup_click():
    global _shutdown_requested
    _shutdown_requested = True
    print("\n🛑 [HANGUP TRIGGERED]: Permanent shutdown requested.")
    ui = get_overlay_ui()
    if ui:
        ui.set_state(STATE_OFFLINE, "Shutting Down...", "Permanent offline command initiated.")
    stop_speaking()
    try:
        speak("Goodbye Boss. System is going offline permanently.")
    except Exception:
        pass
    time.sleep(1.2)
    if ui:
        ui.close()
    os._exit(0)

def on_stop_click():
    stop_speaking()
    ui = get_overlay_ui()
    if ui:
        ui.set_state(STATE_IDLE, "Paused", "Audio playback paused.")

def start_background_daemon():
    global _shutdown_requested
    print("=" * 60)
    print("  JARVIS AUTONOMOUS BACKGROUND SERVICE IS ONLINE")
    print("  Modes: Always Listening for 'Hey Jarvis' / 'Jarvis'")
    print("  Languages: English 🇬🇧 | Hindi 🇮🇳 | Telugu 🇮🇳")
    print("  HUD Overlay: Siri/Gemini Floating Widget Active")
    print("=" * 60)

    # Initialize HUD overlay
    ui = init_overlay_ui(
        on_mic_click=on_mic_click,
        on_hangup_click=on_hangup_click,
        on_stop_click=on_stop_click
    )

    agent = AssistantAgent()
    current_lang = CURRENT_LANGUAGE or "en"
    set_active_language(current_lang)
    if ui:
        ui.set_language_badge(current_lang.upper())

    # Initial startup announcement
    print("[STATUS] Hello Boss! System is online now.")
    if ui:
        ui.set_state(STATE_IDLE, "Online", "Hello Boss! System is online now.")
    speak("Hello Boss! System is online now.")

    while not _shutdown_requested:
        try:
            # 1. Listen silently for wake word
            wake_detected, inline_command = listen_for_wake_word()
            
            if _shutdown_requested:
                break
                
            if wake_detected:
                if ui:
                    ui.set_state(STATE_LISTENING, "Listening...", "Wake word detected...")
                command_to_run = inline_command.strip()
                
                # Check immediate silence / stop command
                if command_to_run.lower() in ["stop", "quiet", "shut up", "be quiet", "silence", "pause", "ఆగు", "రుకో"]:
                    stop_speaking()
                    if ui:
                        ui.set_state(STATE_IDLE, "Interrupted", "Halted by voice command")
                    time.sleep(0.3)
                    continue

                # Check permanent shutdown voice triggers
                if command_to_run.lower() in ["hangup", "hang up", "turn off", "shutdown", "shut down", "exit", "quit", "power off", "ఆపు చేయి", "బంద్ చేయి", "बंद करो"]:
                    on_hangup_click()
                    break
                
                # If no command followed the wake word immediately, acknowledge and listen
                if not command_to_run:
                    active_lang = get_voice_input().active_language
                    if active_lang == "te":
                        speak("చెప్పండి బాస్, వింటున్నాను.")
                    elif active_lang == "hi":
                        speak("हाँ बॉस, बताइए।")
                    else:
                        speak("Yes Boss? I am listening.")
                    
                    # Listen for command
                    if ui:
                        ui.set_state(STATE_LISTENING, "Listening...", "I am listening, speak your command...")
                    command_to_run = listen(timeout=8)
                
                if command_to_run:
                    print(f"\n⚡ [EXECUTING COMMAND]: {command_to_run}")
                    if ui:
                        ui.set_state(STATE_THINKING, "Processing...", f"Executing: \"{command_to_run}\"")
                    response = agent.process_command(command_to_run)
                    print(f"🔊 [RESPONSE]: {response}")
                    speak(response)
                else:
                    print("[INFO] No follow-up command heard. Going back to sleep.")
                    if ui:
                        ui.set_state(STATE_IDLE, "Ready", "Listening for 'Hey Jarvis'...")
                    
            # Brief sleep to avoid CPU spinning
            time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n[STOP] Shutting down background service...")
            on_hangup_click()
            break
        except Exception as e:
            print(f"[RECOVER] Error in background loop: {e}")
            time.sleep(1)

if __name__ == "__main__":
    start_background_daemon()
