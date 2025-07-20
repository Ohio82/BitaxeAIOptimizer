# Bitaxe Monitor - Windows Distribution Package

## What's Included

### Source Code
- Complete Python source code for the Bitaxe Monitor application
- All GUI modules and business logic
- Database, API, and optimization components

### Build System
- PyInstaller configuration optimized for Windows
- Automated build script (`build_windows.bat`)
- NSIS installer script for professional distribution
- Version information and licensing

### Files Included:
✓ main.py - Source code - main entry point
✓ bitaxe_api.py - Source code - API module
✓ database.py - Source code - database module
✓ config.py - Source code - configuration
✓ notifications.py - Source code - notifications
✓ optimizer.py - Source code - optimizer
✓ utils.py - Source code - utilities
✓ bitaxe_monitor.spec - PyInstaller configuration
✓ build_windows.bat - Windows build script
✓ version_info.txt - Version information
✓ installer.nsi - NSIS installer script
✓ config.json - Default configuration
✓ generated-icon.png - Application icon
✓ LICENSE.txt - Software license
✓ README_WINDOWS.txt - User guide
✓ WINDOWS_BUILD_GUIDE.md - Build instructions

## Creating Your Windows Executable

### Method 1: Automated Build (Recommended)
1. **Install Python 3.8+** on your Windows 11 machine
2. **Install dependencies**:
   ```cmd
   pip install pyinstaller matplotlib requests
   ```
3. **Run the build script**:
   ```cmd
   build_windows.bat
   ```
4. **Find your executable**: `dist\BitaxeMonitor.exe`

### Method 2: Manual Build
```cmd
pyinstaller --clean bitaxe_monitor.spec
```

## System Requirements
- **Windows 11** (recommended) or Windows 10
- **Python 3.8+** for building (not needed for end users)
- **4GB RAM** minimum, 8GB recommended
- **Network access** to your Bitaxe device

## Distribution
- **Portable**: Just distribute the `BitaxeMonitor.exe` file (~50-70MB)
- **Installer**: Use NSIS to compile `installer.nsi` for professional installation

## First Run Setup
1. Run `BitaxeMonitor.exe`
2. Navigate to Settings tab
3. Enter your Bitaxe device IP address (e.g., 192.168.1.50)
4. Configure mining pool settings
5. Set up email notifications (optional)

## Features
- Real-time mining performance monitoring
- Historical data charts and analytics
- Automated performance optimization
- Email alerts for temperature and hashrate issues
- SQLite database for data persistence
- Professional Windows GUI with multiple tabs

## Troubleshooting

### Build Issues
- Ensure Python and pip are in your PATH
- Install Visual C++ Redistributable if needed
- Try running Command Prompt as Administrator

### Runtime Issues
- Windows Defender may flag the executable initially (add exception)
- Ensure your Bitaxe device is accessible on the network
- Check firewall settings for network access

## Support
- Check application logs for technical issues
- Verify Bitaxe device connectivity via web browser
- Ensure mining pool settings are correct

---
**Version**: 1.0.0  
**Build Date**: July 20, 2025  
**Compatible**: Windows 10/11  
**License**: MIT License
