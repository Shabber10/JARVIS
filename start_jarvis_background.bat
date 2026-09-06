@echo off
title Start Jarvis in Background
color 0a
echo ========================================================
echo        STARTING JARVIS BACKGROUND SERVICE
echo ========================================================
echo.

wscript.exe "%~dp0run_jarvis_background.vbs"

echo [SUCCESS] Jarvis is now running silently in the background!
echo Just say "Hey Jarvis" or "Jarvis" whenever you need it.
echo.
timeout /t 4 >nul
