@echo off
title Stop Jarvis Background Service
color 0c
echo ========================================================
echo        STOPPING ALL JARVIS PROCESSES
echo ========================================================
echo.

taskkill /F /IM python.exe /IM pythonw.exe /T >nul 2>&1

echo [SUCCESS] All Jarvis background and terminal processes terminated.
echo.
pause
