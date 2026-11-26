@echo off
echo ============================================
echo   Building AutoSort (Portable EXE)
echo ============================================
echo.

:: Check Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Install Python 3.9+ from https://www.python.org or run:
    echo         winget install Python.Python.3.12 --scope currentuser
    echo         Then restart your terminal.
    pause
    exit /b 1
)

echo [1/4] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [2/4] Installing PyInstaller...
pip install "pyinstaller>=6.0.0"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)

echo.
echo [3/4] Generating icon if needed...
if not exist "assets" mkdir assets
if not exist "assets\icon.ico" (
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGBA', (256, 256), (0,0,0,0)); d = ImageDraw.Draw(img); d.rectangle([32,48,112,80], fill=(76,175,80,255)); d.rectangle([32,80,224,208], fill=(76,175,80,255)); d.rectangle([56,112,200,144], fill=(255,255,255,180)); d.rectangle([56,156,160,176], fill=(255,255,255,180)); img.save('assets/icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
    if %errorlevel% neq 0 (
        echo [WARNING] Could not generate icon. Building without custom icon.
        set ICON_FLAG=
    ) else (
        echo    Icon generated: assets\icon.ico
        set ICON_FLAG=--icon=assets/icon.ico
    )
) else (
    echo    Icon already exists: assets\icon.ico
    set ICON_FLAG=--icon=assets/icon.ico
)

echo.
echo [4/4] Building portable EXE with PyInstaller...

:: Clean previous build artifacts
if exist "dist\AutoSort.exe" del /f /q "dist\AutoSort.exe"
if exist "build"             rmdir /s /q "build"
if exist "AutoSort.spec"     del /f /q "AutoSort.spec"

:: Use "python -m PyInstaller" instead of bare "pyinstaller" command —
:: avoids PATH issues when the Python Scripts folder is not on PATH
:: (common with Windows Store Python installs).
if defined ICON_FLAG (
    python -m PyInstaller ^
        --onefile ^
        --windowed ^
        --name AutoSort ^
        %ICON_FLAG% ^
        --add-data "assets/icon.ico;assets" ^
        --hidden-import "pystray._win32" ^
        --hidden-import "watchdog.observers.winapi" ^
        --collect-all "pystray" ^
        autosort/main.py
) else (
    python -m PyInstaller ^
        --onefile ^
        --windowed ^
        --name AutoSort ^
        --add-data "assets/icon.ico;assets" ^
        --hidden-import "pystray._win32" ^
        --hidden-import "watchdog.observers.winapi" ^
        --collect-all "pystray" ^
        autosort/main.py
)

if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

if not exist "dist\AutoSort.exe" (
    echo [ERROR] Build completed but dist\AutoSort.exe was not created.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Build successful!
echo   Portable EXE: dist\AutoSort.exe
echo   Copy dist\AutoSort.exe anywhere and run it.
echo   No Python installation required on target.
echo ============================================
pause

