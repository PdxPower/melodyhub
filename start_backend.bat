@echo off
chcp 65001 >nul
set PYTHONUTF8=1
title MelodyHub Backend

:: Switch to the script's directory, so relative paths work even when run from a shortcut
cd /d "%~dp0"

set "PYTHON=C:\Users\86136\.workbuddy\binaries\python\envs\melodyhub\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo [ERROR] Python virtual environment not found.
    echo   %PYTHON%
    echo Please create the venv and install dependencies:
    echo   C:\Users\86136\.workbuddy\binaries\python\versions\3.13.12\python.exe -m venv C:\Users\86136\.workbuddy\binaries\python\envs\melodyhub
    echo   %PYTHON% -m pip install fastapi uvicorn httpx mutagen
    pause
    exit /b 1
)

if not exist "backend\launcher.py" (
    echo [ERROR] backend\launcher.py not found.
    pause
    exit /b 1
)

"%PYTHON%" "backend\launcher.py"
