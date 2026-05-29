@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   AI Driver Monitoring System Setup and Launcher
echo ===================================================

:: Define Python path
set "PYTHON_PATH=C:\Users\samee\AppData\Local\Programs\Python\Python310\python.exe"

if not exist "%PYTHON_PATH%" (
    echo Python 3.10 was not found at %PYTHON_PATH%
    echo Attempting to locate Python using uv...
    set "PYTHON_PATH=3.10"
)

:: Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment with Python 3.10...
    uv venv .venv --python "%PYTHON_PATH%"
    if !errorlevel! neq 0 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

:: Install/Upgrade dependencies
echo Installing dependencies from requirements.txt...
uv pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

:: Run main.py
echo Starting AI Driver Monitoring System...
python main.py
if !errorlevel! neq 0 (
    echo Application exited with error code !errorlevel!
)

pause
