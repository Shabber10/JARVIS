@echo off
title Enable Jarvis Windows Startup
color 0a
echo ========================================================
echo       ENABLING JARVIS WINDOWS AUTO-STARTUP
echo ========================================================
echo.

set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SOURCE_VBS=%~dp0Launch_Jarvis.vbs"
set "TARGET_VBS=%STARTUP_DIR%\Jarvis_AutoStart.vbs"

echo Copying startup script to:
echo %TARGET_VBS%
echo.

copy /Y "%SOURCE_VBS%" "%TARGET_VBS%" >nul

if exist "%TARGET_VBS%" (
    echo [SUCCESS] Jarvis will now start automatically whenever your laptop turns on!
) else (
    echo [ERROR] Failed to install startup script.
)

echo.
pause
