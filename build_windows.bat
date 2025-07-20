@echo off
echo Building Bitaxe Monitor for Windows...
echo.

REM Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "gui\__pycache__" rmdir /s /q "gui\__pycache__"

REM Install PyInstaller if not already installed
echo Installing PyInstaller...
pip install pyinstaller

REM Build the executable
echo Building executable...
pyinstaller --clean bitaxe_monitor.spec

REM Check if build was successful
if exist "dist\BitaxeMonitor.exe" (
    echo.
    echo ✓ Build successful!
    echo ✓ Executable created: dist\BitaxeMonitor.exe
    echo.
    echo You can now distribute the 'dist' folder or just the BitaxeMonitor.exe file.
) else (
    echo.
    echo ✗ Build failed!
    echo Please check the output above for errors.
)

pause
