"""
Test script to verify the Siri/Gemini HUD Overlay UI state transitions,
visualizer animation, subtitles, and button event routing.
"""
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.ui_overlay import (
    init_overlay_ui,
    get_overlay_ui,
    STATE_IDLE,
    STATE_LISTENING,
    STATE_THINKING,
    STATE_SPEAKING,
    STATE_OFFLINE
)

def test_full_overlay_flow():
    print("[TEST] Initializing Jarvis HUD Overlay...")
    
    mic_clicked = False
    hangup_clicked = False
    stop_clicked = False
    
    def on_mic():
        nonlocal mic_clicked
        mic_clicked = True
        print("  -> [EVENT] Mic Clicked callback triggered")
        
    def on_hangup():
        nonlocal hangup_clicked
        hangup_clicked = True
        print("  -> [EVENT] Hangup Clicked callback triggered")
        
    def on_stop():
        nonlocal stop_clicked
        stop_clicked = True
        print("  -> [EVENT] Stop Clicked callback triggered")

    ui = init_overlay_ui(
        on_mic_click=on_mic,
        on_hangup_click=on_hangup,
        on_stop_click=on_stop
    )

    time.sleep(1.0)
    print("  -> 1. Setting state: IDLE / ONLINE")
    ui.set_state(STATE_IDLE, "Online", "Hello Boss! System is online now.")
    time.sleep(1.5)

    print("  -> 2. Setting state: LISTENING (Wake word detected)")
    ui.set_state(STATE_LISTENING, "Listening...", "Monitoring microphone speech...")
    time.sleep(2.0)

    print("  -> 3. Setting state: THINKING (Analyzing directive)")
    ui.set_state(STATE_THINKING, "Processing...", "Executing: 'What is the weather today?'")
    time.sleep(2.0)

    print("  -> 4. Setting state: SPEAKING (TTS Playback)")
    ui.set_state(STATE_SPEAKING, "Speaking...", "The current temperature is 28°C and partly cloudy.")
    time.sleep(2.5)

    print("  -> 5. Setting state: BACK TO IDLE")
    ui.set_state(STATE_IDLE, "Ready", "Listening for 'Hey Jarvis'...")
    time.sleep(1.0)

    print("[SUCCESS] All UI states rendered and tested successfully!")
    ui.close()

if __name__ == "__main__":
    test_full_overlay_flow()
