@echo off
cd /d "%~dp0"
echo Cleaning up unwanted temporary files and test scripts...

del /F /Q "cleanup_processes.py" 2>nul
del /F /Q "test_overlay_flow.py" 2>nul
del /F /Q "test_modules.py" 2>nul
del /F /Q "test_all_features.py" 2>nul
del /F /Q "run_jarvis_background.vbs" 2>nul
del /F /Q "start_jarvis_background.bat" 2>nul
del /F /Q "run_clean.vbs" 2>nul
del /F /Q "clean_project.py" 2>nul
del /F /Q "temp\*.mp3" 2>nul
del /F /Q "temp\*.png" 2>nul

echo [SUCCESS] All unwanted and temporary files cleaned up!
(goto) 2>nul & del "%~f0"
