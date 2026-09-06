@echo off
title Disable Jarvis Windows Startup
color 0c
echo ========================================================
echo       DISABLING JARVIS WINDOWS AUTO-STARTUP
echo ========================================================
echo.

set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "TARGET_VBS=%STARTUP_DIR%\Jarvis_AutoStart.vbs"

if exist "%TARGET_VBS%" (
    del /F /Q "%TARGET_VBS%"
    echo [SUCCESS] Jarvis auto-startup has been removed.
) else (
    echo [INFO] Jarvis auto-startup was not installed.
)

echo.
pause
