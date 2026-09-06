import os
import subprocess
from pathlib import Path
from typing import List

def search_local_files(pattern: str, search_path: str = None, max_results: int = 5) -> str:
    """
    Searches for files matching a pattern (e.g. *.pdf, budget, notes) in user directories.
    """
    if not search_path:
        search_path = os.path.expanduser("~")
        
    base = Path(search_path)
    if not base.exists():
        return f"Directory {search_path} does not exist."

    matches = []
    # Search common folders: Desktop, Documents, Downloads
    target_dirs = [
        base / "Desktop",
        base / "Documents",
        base / "Downloads"
    ]
    
    clean_pattern = pattern.lower().replace("*", "")
    for directory in target_dirs:
        if not directory.exists():
            continue
        try:
            for item in directory.rglob("*"):
                if len(matches) >= max_results:
                    break
                if clean_pattern in item.name.lower():
                    matches.append(str(item))
        except (PermissionError, OSError):
            continue
        if len(matches) >= max_results:
            break
            
    if not matches:
        return f"No files matching '{pattern}' found in Desktop, Documents, or Downloads."
    
    return "Found files:\n" + "\n".join(f"- {m}" for m in matches)

def open_file_or_folder(path: str) -> str:
    """
    Opens a file or folder in Windows Explorer or default system app.
    """
    p = Path(path)
    if not p.exists():
        return f"Path does not exist: {path}"
    try:
        os.startfile(str(p))
        return f"Opened {path}"
    except Exception as e:
        return f"Failed to open {path}: {e}"

def read_text_file(filepath: str, max_chars: int = 2000) -> str:
    """
    Reads the content of a local text or markdown file.
    """
    p = Path(filepath)
    if not p.exists():
        return f"File does not exist: {filepath}"
    try:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(max_chars)
        return f"Content of {p.name}:\n{content}"
    except Exception as e:
        return f"Failed to read file: {e}"
