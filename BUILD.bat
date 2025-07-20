@echo off
echo ==========================================
echo Bitaxe Monitor - Windows Build Script
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Install required packages
echo Installing required packages...
pip install pyinstaller matplotlib requests

REM Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Build the executable
echo.
echo Building executable...
pyinstaller --clean bitaxe_monitor.spec

REM Check result
if exist "dist\BitaxeMonitor.exe" (
    echo.
    echo ==========================================
    echo ✓ BUILD SUCCESSFUL!
    echo ==========================================
    echo.
    echo Your executable is ready: dist\BitaxeMonitor.exe
    echo File size: ~50-70 MB
    echo.
    echo You can now:
    echo 1. Run dist\BitaxeMonitor.exe directly
    echo 2. Distribute the dist folder
    echo 3. Create an installer with NSIS
    echo.
) else (
    echo.
    echo ==========================================
    echo ✗ BUILD FAILED!
    echo ==========================================
    echo.
    echo Please check the errors above and try again.
    echo Common solutions:
    echo - Run as Administrator
    echo - Install Visual C++ Redistributable
    echo - Check internet connection for pip installs
    echo.
)

pause
