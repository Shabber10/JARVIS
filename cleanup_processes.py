"""
Script to safely locate and terminate all running Jarvis background processes,
and remove any stale startup / scheduler triggers if present.
"""
import os
import sys
import psutil
from pathlib import Path

def cleanup_all_jarvis_processes():
    current_pid = os.getpid()
    jarvis_dir = str(Path(__file__).resolve().parent).lower()
    
    print(f"[CLEANUP] Current PID: {current_pid}")
    print(f"[CLEANUP] Target directory: {jarvis_dir}")
    
    terminated_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.pid == current_pid:
                continue
            
            cmdline = proc.info.get('cmdline') or []
            cmd_str = " ".join(cmdline).lower()
            name = (proc.info.get('name') or '').lower()
            
            if 'python' in name or 'wscript' in name or 'cscript' in name:
                if 'jarvis' in cmd_str or any(f in cmd_str for f in ['background_service', 'main.py', 'test_overlay']):
                    print(f"Terminating Jarvis Process: PID {proc.pid} ({name}) -> {cmd_str[:80]}")
                    proc.kill()
                    terminated_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    print(f"[SUCCESS] Terminated {terminated_count} background process(es).")

if __name__ == "__main__":
    cleanup_all_jarvis_processes()
