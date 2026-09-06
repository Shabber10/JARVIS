import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    except Exception:
        pass

from config import GEMINI_API_KEY, DOCS_DIR, CURRENT_LANGUAGE
from core.agent import AssistantAgent
from core.voice_in import listen_for_wake_word, listen, set_active_language, get_voice_input
from core.voice_out import speak, stop_speaking
from core.rag_engine import ingest_local_documents
from core.ui_overlay import init_overlay_ui, get_overlay_ui, STATE_IDLE, STATE_LISTENING, STATE_THINKING, STATE_SPEAKING, STATE_OFFLINE

# Global runtime shutdown flag
_shutdown_requested = False

HUD_BANNER = r"""
=============================================================================
      ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗   ██╗  ██╗██╗   ██╗██████╗ 
      ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝   ██║  ██║██║   ██║██╔══██╗
      ██║███████║██████╔╝██║   ██║██║███████╗   ███████║██║   ██║██║  ██║
 ██╗  ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║   ██╔══██║██║   ██║██║  ██║
 ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║   ██║  ██║╚██████╔╝██████╔╝
  ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ 
                 J.A.R.V.I.S. AUTONOMOUS VOICE AI HUD
=============================================================================
  🎙️ PROTOCOL: FULL HANDS-FREE (VOICE BARGE-IN & REAL-TIME INTERRUPT)
  🌐 LANGUAGES: English (Stark British) | Telugu (తెలుగు) | Hindi (हिंदी)
  🖥️ OVERLAY: Siri/Gemini Floating HUD with Mic & Permanent Hangup
  ⚡ PROTOCOLS: OS Control, Stark Automations, Math, YouTube & Diagnostics
=============================================================================
"""

def print_hud_status(status_text: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] 🟢 {status_text}")

def on_mic_button_pressed():
    """Triggered when user clicks the microphone button on the floating HUD."""
    stop_speaking()
    ui = get_overlay_ui()
    if ui:
        ui.set_state(STATE_LISTENING, "Listening...", "Push-to-talk activated...")

def on_hangup_button_pressed():
    """Triggered when user clicks the red hangup button on the floating HUD."""
    global _shutdown_requested
    _shutdown_requested = True
    print("\n\n🛑 [HANGUP TRIGGERED]: Permanent shutdown requested by user.")
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

def on_stop_button_pressed():
    """Triggered when user clicks the pause/stop button on the floating HUD."""
    stop_speaking()
    ui = get_overlay_ui()
    if ui:
        ui.set_state(STATE_IDLE, "Paused", "Audio playback paused.")

def main():
    global _shutdown_requested
    print("\033[H\033[J", end="")
    print(HUD_BANNER)
    
    # Initialize the Siri/Gemini Floating HUD Overlay
    ui = init_overlay_ui(
        on_mic_click=on_mic_button_pressed,
        on_hangup_click=on_hangup_button_pressed,
        on_stop_click=on_stop_button_pressed
    )
    
    agent = AssistantAgent()
    current_lang = CURRENT_LANGUAGE or "en"
    set_active_language(current_lang)
    if ui:
        ui.set_language_badge(current_lang.upper())
    
    # Auto-index knowledge docs on first launch
    sample_doc = DOCS_DIR / "my_project_notes.txt"
    if not sample_doc.exists():
        with open(sample_doc, "w", encoding="utf-8") as f:
            f.write("""Project Antigravity Voice Assistant
Author: Shabber Hussain
Goal: Create an intelligent voice-controlled desktop agent with RAG and Multi-language support (English, Hindi, Telugu).
Status: Active and fully functional.
""")
        ingest_local_documents()

    print_hud_status("SYSTEM INITIALIZED & OPERATING AT 100% CAPACITY.")
    print_hud_status("ALWAYS-LISTENING PROTOCOL ACTIVE. Speak or interrupt anytime!\n")
    if ui:
        ui.set_state(STATE_IDLE, "Online", "Hello Boss! System is online now.")
    speak("Hello Boss! System is online now.")

    while not _shutdown_requested:
        try:
            print("\r🎙️ [LISTENING] Monitoring for speech / wake word...", end="", flush=True)
            wake_detected, inline_cmd = listen_for_wake_word()
            
            if _shutdown_requested:
                break
                
            if wake_detected:
                if ui:
                    ui.set_state(STATE_LISTENING, "Listening...", "Wake word detected...")
                cmd = inline_cmd.strip()
                
                # Check immediate silence / stop command
                if cmd.lower() in ["stop", "quiet", "shut up", "be quiet", "silence", "pause", "ఆగు", "రుకో"]:
                    stop_speaking()
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"\n[{timestamp}] 🛑 [INTERRUPT]: Playback halted by user.")
                    if ui:
                        ui.set_state(STATE_IDLE, "Interrupted", "Halted by voice command")
                    time.sleep(0.3)
                    continue

                # Check permanent shutdown voice triggers
                if cmd.lower() in ["hangup", "hang up", "turn off", "shutdown", "shut down", "exit", "quit", "power off", "ఆపు చేయి", "బంద్ చేయి", "बंद करो"]:
                    on_hangup_button_pressed()
                    break
                
                # If user only said "Hey Jarvis", acknowledge and listen for command
                if not cmd:
                    active_lang = get_voice_input().active_language
                    if active_lang == "te":
                        speak("చెప్పండి బాస్, వింటున్నాను.")
                    elif active_lang == "hi":
                        speak("हाँ सर, बताइए।")
                    else:
                        speak("At your service, Sir.")
                    
                    print("\n🎤 [ACTIVE] Listening for follow-up command...")
                    if ui:
                        ui.set_state(STATE_LISTENING, "Listening...", "I am listening, speak your directive...")
                    cmd = listen(timeout=8)

                if cmd:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"\n\n========================================================")
                    print(f"[{timestamp}] 🗣️ USER: \"{cmd}\"")
                    print(f"[{timestamp}] ⚡ EXECUTING DIRECTIVE...")
                    
                    if ui:
                        ui.set_state(STATE_THINKING, "Processing...", f"Executing: \"{cmd}\"")
                    
                    response = agent.process_command(cmd)
                    
                    print(f"[{timestamp}] 🔊 JARVIS: {response}")
                    print(f"========================================================\n")
                    speak(response)
                else:
                    print("\n[INFO] No follow-up directive detected. Resuming background sweep.\n")
                    if ui:
                        ui.set_state(STATE_IDLE, "Ready", "Listening for 'Hey Jarvis'...")
                    
            time.sleep(0.05)
            
        except KeyboardInterrupt:
            print("\n\n[SHUTDOWN] Exiting Jarvis...")
            on_hangup_button_pressed()
            break
        except Exception as e:
            time.sleep(1)

if __name__ == "__main__":
    main()
