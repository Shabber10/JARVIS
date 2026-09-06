@echo off
title J.A.R.V.I.S. AI - Autonomous Voice HUD
color 0b
mode con: cols=100 lines=32

cd /d "%~dp0"

echo =============================================================================
echo                     INITIALIZING STARK J.A.R.V.I.S. CORE
echo =============================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Please install Python.
    pause
    exit /b 1
)

:: Launch Jarvis in Full Hands-Free Mode with Barge-in Interruption
".venv\Scripts\python.exe" main.py

pause
