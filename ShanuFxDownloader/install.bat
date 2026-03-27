@echo off
title Shanu Fx Private Downloader - Setup
color 0B

echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║         Shanu Fx Private Downloader - Setup           ║
echo  ║              by Shanudha Tirosh                       ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.

:: Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  ERROR: Python not found!
    echo  Please install Python 3.11+ from https://python.org
    echo  Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)
python --version
echo  ✓ Python found

:: Upgrade pip
echo.
echo [2/5] Upgrading pip...
python -m pip install --upgrade pip -q
echo  ✓ pip upgraded

:: Install requirements
echo.
echo [3/5] Installing Python dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo  ERROR: Failed to install some dependencies
    echo  Try running: pip install customtkinter Pillow yt-dlp requests
    pause
    exit /b 1
)
echo  ✓ Dependencies installed

:: Check FFmpeg
echo.
echo [4/5] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo  ⚠  FFmpeg not found on PATH
    echo  The app will auto-download FFmpeg on first launch.
    echo  OR install manually from https://ffmpeg.org/download.html
) else (
    echo  ✓ FFmpeg found
)

:: Done
echo.
echo [5/5] Setup complete!
echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║  Launch the app by running:                           ║
echo  ║     python main.py                                    ║
echo  ║                                                       ║
echo  ║  Or double-click: run.bat                             ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.

:: Create run.bat
echo @echo off > run.bat
echo pythonw main.py >> run.bat

echo  Created run.bat - double-click it to launch!
echo.
pause
