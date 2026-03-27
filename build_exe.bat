@echo off
title Shanu Fx Downloader - Build EXE
color 0B
echo.
echo  Building Shanu Fx Private Downloader EXE...
echo  ─────────────────────────────────────────────
echo.

:: Install PyInstaller if not present
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

:: Clean old build
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

:: Build
echo Building executable...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "ShanuFxDownloader" ^
    --add-data "assets;assets" ^
    --hidden-import customtkinter ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageTk ^
    --hidden-import yt_dlp ^
    --hidden-import yt_dlp.utils ^
    --hidden-import yt_dlp.extractor ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.filedialog ^
    --exclude-module matplotlib ^
    --exclude-module numpy ^
    --exclude-module scipy ^
    --clean ^
    main.py

if %errorlevel% equ 0 (
    echo.
    echo  ✓ Build successful!
    echo  Output: dist\ShanuFxDownloader.exe
    echo.
    explorer dist
) else (
    echo.
    echo  ✗ Build failed. Check the output above for errors.
)
pause
