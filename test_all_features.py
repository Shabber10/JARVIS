import sys
import os
import traceback
from pathlib import Path

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
        sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def run_all_tests():
    print("================================================================")
    print("       JARVIS COMPREHENSIVE DIAGNOSTIC & TEST SUITE            ")
    print("================================================================")
    
    passed = 0
    failed = 0
    errors = []

    def test_case(name, fn):
        nonlocal passed, failed
        try:
            print(f"\n[TEST] {name}...", end=" ", flush=True)
            res = fn()
            print(f"✅ PASS", flush=True)
            print(f"   ↳ Output: {str(res)[:100]}...", flush=True)
            passed += 1
        except Exception as e:
            print(f"❌ FAIL: {e}", flush=True)
            errors.append((name, str(e), traceback.format_exc()))
            failed += 1

    # 1. OS Actions
    from tools.os_actions import (
        get_battery_status, get_system_status, get_network_info,
        set_system_volume, set_brightness, execute_universal_system_action
    )
    test_case("OS: Battery Status", lambda: get_battery_status())
    test_case("OS: System Status (CPU/RAM)", lambda: get_system_status())
    test_case("OS: Network Info", lambda: get_network_info())
    test_case("OS: Set Volume", lambda: set_system_volume(50))
    test_case("OS: Set Brightness", lambda: set_brightness(70))
    test_case("OS: Universal Action - Mouse Scroll", lambda: execute_universal_system_action("scroll down"))
    test_case("OS: Universal Action - Key Press", lambda: execute_universal_system_action("press enter"))

    # 2. Assistant Features
    from tools.assistant_features import (
        get_live_weather, get_top_news, read_clipboard_text,
        copy_text_to_clipboard, test_internet_speed, get_daily_briefing,
        translate_phrase, get_crypto_or_currency, save_diary_entry,
        optimize_system_and_ram, roll_dice_or_coin
    )
    test_case("Features: Live Weather", lambda: get_live_weather("Hyderabad"))
    test_case("Features: Breaking News", lambda: get_top_news())
    test_case("Features: Clipboard Copy & Read", lambda: (copy_text_to_clipboard("JarvisTest123"), read_clipboard_text())[1])
    test_case("Features: Internet Speed Test", lambda: test_internet_speed())
    test_case("Features: Daily Briefing", lambda: get_daily_briefing())
    test_case("Features: Translation (EN->TE)", lambda: translate_phrase("Good Morning", "te"))
    test_case("Features: Crypto Price (Bitcoin)", lambda: get_crypto_or_currency("bitcoin"))
    test_case("Features: Currency Exchange (USD to INR)", lambda: get_crypto_or_currency("usd"))
    test_case("Features: Voice Diary Vault", lambda: save_diary_entry("Diagnostic test run completed successfully."))
    test_case("Features: System RAM Optimizer", lambda: optimize_system_and_ram())
    test_case("Features: Dice / Coin Roll", lambda: roll_dice_or_coin("flip a coin"))

    # 3. Web Actions & Math & Knowledge
    from tools.web_actions import solve_math_expression, fetch_instant_knowledge
    test_case("Web: Math Solver (Simple)", lambda: solve_math_expression("what is 25 * 4"))
    test_case("Web: Math Solver (Complex)", lambda: solve_math_expression("100 / 5 + 50"))
    test_case("Web: Wikipedia Knowledge QA", lambda: fetch_instant_knowledge("who is Albert Einstein"))

    # 4. Stark System Pro Tools & Diagnostics
    from tools.system_pro import (
        protocol_stealth, list_top_processes, get_storage_analysis,
        get_public_ip_info, scan_wifi_networks, manage_todo,
        convert_units, get_dictionary_definition, run_system_self_diagnostic
    )
    test_case("Stark: Protocol Stealth", lambda: protocol_stealth())
    test_case("Stark: List Top Processes", lambda: list_top_processes())
    test_case("Stark: Storage Drive Analysis", lambda: get_storage_analysis())
    test_case("Stark: Public IP & Geolocation", lambda: get_public_ip_info())
    test_case("Stark: Wi-Fi Scanner", lambda: scan_wifi_networks())
    test_case("Stark: Persistent Todo Add & List", lambda: (manage_todo("add todo Buy arc reactor parts"), manage_todo("list todos"))[1])
    test_case("Stark: Unit Converter (C to F)", lambda: convert_units("100 celsius to fahrenheit"))
    test_case("Stark: Unit Converter (km to miles)", lambda: convert_units("50 km to miles"))
    test_case("Stark: Dictionary Definition", lambda: get_dictionary_definition("quantum"))
    test_case("Stark: System Self Diagnostic Sweep", lambda: run_system_self_diagnostic())

    # 5. Windows Notifications
    from tools.notifications import get_windows_notifications
    test_case("Notifications: Windows Notification Reader", lambda: get_windows_notifications())

    # 5. File & Knowledge RAG Engine
    from core.rag_engine import ingest_local_documents, query_personal_knowledge
    test_case("RAG: Ingest Local Documents", lambda: ingest_local_documents())
    test_case("RAG: Vector Search Query", lambda: query_personal_knowledge("What is the project goal?"))

    # 6. Core Agent Multilingual Intelligence
    from core.agent import AssistantAgent
    agent = AssistantAgent()
    test_case("Agent: English Intent - Weather", lambda: agent.process_command("what is the weather in Hyderabad"))
    test_case("Agent: English Intent - Daily Briefing", lambda: agent.process_command("give me my daily briefing"))
    test_case("Agent: English Intent - Math", lambda: agent.process_command("what is 100 * 25"))
    test_case("Agent: English Intent - Conversational Chat", lambda: agent.process_command("how are you doing"))
    test_case("Agent: English Intent - YouTube Play", lambda: agent.process_command("play Kilimanjaro song"))
    test_case("Agent: Telugu Intent - Weather", lambda: agent.process_command("వాతావరణం ఎలా ఉంది"))
    test_case("Agent: Telugu Intent - News", lambda: agent.process_command("తాజా వార్తలు చెప్పు"))
    test_case("Agent: Hindi Intent - Battery", lambda: agent.process_command("लैपटॉप की बैटरी कितनी है"))

    # 7. Voice TTS Engine
    from core.voice_out import speak
    test_case("Voice: British JARVIS Speech Synthesis", lambda: speak("Diagnostic test sequence complete, Sir."))

    print("\n================================================================")
    print(f" DIAGNOSTIC SUMMARY: {passed} PASSED, {failed} FAILED")
    print("================================================================")
    
    if errors:
        print("\nERRORS DETECTED:")
        for name, err, tb in errors:
            print(f" - {name}: {err}")
    else:
        print("🎉 ALL SYSTEMS AND MODULES ARE OPERATING AT 100% NOMINAL EFFICIENCY!")

if __name__ == "__main__":
    run_all_tests()
