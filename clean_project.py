"""
Helper script to clean up temporary test files and redundant scripts.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

FILES_TO_REMOVE = [
    BASE_DIR / "cleanup_processes.py",
    BASE_DIR / "test_overlay_flow.py",
    BASE_DIR / "test_modules.py",
    BASE_DIR / "test_all_features.py",
    BASE_DIR / "run_jarvis_background.vbs",
    BASE_DIR / "start_jarvis_background.bat",
]

# 1. Remove redundant scripts
for file_path in FILES_TO_REMOVE:
    if file_path.exists():
        try:
            file_path.unlink()
            print(f"[REMOVED] {file_path.name}")
        except Exception as e:
            print(f"[ERROR] Could not remove {file_path.name}: {e}")

# 2. Clean temp directory
temp_dir = BASE_DIR / "temp"
if temp_dir.exists():
    for f in temp_dir.glob("*"):
        if f.is_file():
            try:
                f.unlink()
                print(f"[CLEANED TEMP] {f.name}")
            except Exception:
                pass

print("[DONE] Project cleanup finished!")

# Self-remove this script
try:
    Path(__file__).unlink()
except Exception:
    pass
