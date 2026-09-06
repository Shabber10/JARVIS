import sys
import io
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def test_tools():
    print("\n--- Testing OS Tools & Web Tools ---")
    from tools.os_actions import open_application, close_application, take_screenshot
    from tools.web_actions import search_web, play_youtube
    from tools.file_actions import search_local_files
    
    print("Testing file search...")
    res = search_local_files("test")
    print(f"File search result: {res}")
    print("[PASS] All tool imports and structures verified successfully!")

def test_rag():
    print("\n--- Testing RAG Engine ---")
    from core.rag_engine import get_rag_engine
    from config import DOCS_DIR
    
    # Create a test document
    test_file = DOCS_DIR / "sample_guide.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("The secret passkey for project Alpha is 998877. The lead architect is Shabber.")
        
    engine = get_rag_engine()
    ingest_msg = engine.ingest_documents()
    print(f"Ingest Result: {ingest_msg}")
    
    query_res = engine.query("What is the secret passkey for project Alpha?")
    print(f"Query Result:\n{query_res}")
    assert "998877" in query_res, "RAG failed to retrieve relevant passkey!"
    print("[PASS] RAG Retrieval Test PASSED!")

def test_tts():
    print("\n--- Testing Edge TTS ---")
    from core.voice_out import speak
    print("Synthesizing test speech...")
    speak("Testing the speech output engine. All systems operational.")
    print("[PASS] TTS Test PASSED!")

if __name__ == "__main__":
    print("Running Voice Assistant Module Tests...")
    test_tools()
    test_rag()
    test_tts()
    print("\n[SUCCESS] ALL TESTS COMPLETED SUCCESSFULLY!")
