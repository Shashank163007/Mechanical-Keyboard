@echo off
title Mechanical Keyboard Audio Simulator
cd /d "%~dp0"

:: Check if virtual environment exists, create it if not
if not exist ".venv\Scripts\python.exe" (
    echo [*] First-time setup: Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [!] Failed to create virtual environment.
        echo [!] Make sure Python 3.8+ is installed and added to PATH.
        echo     Download from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo [*] Installing dependencies...
    ".venv\Scripts\pip.exe" install -r requirements.txt
    if errorlevel 1 (
        echo [!] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo [*] Setup complete!
    echo.
)

:: Launch the app
start "" ".venv\Scripts\pythonw.exe" main.py
exit
