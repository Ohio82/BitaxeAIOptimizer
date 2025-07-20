# Windows Executable Build Guide for Bitaxe Monitor

## Overview

This guide explains how to create a Windows executable (.exe) file from the Bitaxe Monitor Python application. The build process uses PyInstaller to package all dependencies into a single executable file.

## Prerequisites

### Software Requirements
- **Windows 10 or 11** (for building Windows executable)
- **Python 3.8 or later** installed from [python.org](https://python.org)
- **Git** (optional, for version control)

### Python Dependencies
The build script will automatically install PyInstaller, but ensure you have these core dependencies:
```bash
pip install pyinstaller matplotlib requests
```

## Quick Start (Automated Build)

### Method 1: Using the Build Script (Recommended)
1. **Download/Clone** the Bitaxe Monitor project to your Windows machine
2. **Open Command Prompt** as Administrator in the project directory
3. **Run the build script**:
   ```cmd
   build_windows.bat
   ```
4. **Wait for completion** - the build process takes 2-5 minutes
5. **Find your executable** in the `dist` folder: `dist\BitaxeMonitor.exe`

### Method 2: Using Python Script
```cmd
python build_windows.py
```

## Manual Build Process

If you prefer to build manually or customize the process:

### Step 1: Install PyInstaller
```cmd
pip install pyinstaller
```

### Step 2: Build with Spec File
```cmd
pyinstaller --clean bitaxe_monitor.spec
```

### Step 3: Test the Executable
```cmd
cd dist
BitaxeMonitor.exe
```

## Build Configuration Files

The project includes several configuration files for the build process:

### `bitaxe_monitor.spec`
- PyInstaller configuration file
- Specifies included files, dependencies, and build options
- Configured for Windows GUI application (no console window)

### `version_info.txt`
- Windows version information displayed in file properties
- Contains application name, version, company info

### `build_windows.bat`
- Automated build script for Windows
- Cleans previous builds and creates new executable
- Provides build status and error reporting

## Creating an Installer (Optional)

### Using NSIS (Nullsoft Scriptable Install System)

1. **Download NSIS** from [nsis.sourceforge.io](https://nsis.sourceforge.io/)
2. **Install NSIS** on your Windows machine
3. **Build the executable first** using steps above
4. **Right-click** on `installer.nsi` and select "Compile NSIS Script"
5. **Find the installer**: `BitaxeMonitorInstaller.exe`

The installer will:
- Install the application to Program Files
- Create Start Menu shortcuts
- Create Desktop shortcut
- Add uninstall entry to Windows Programs list

## Distribution

### Portable Version
- Simply distribute the `dist` folder or just `BitaxeMonitor.exe`
- Users can run it from any location without installation
- First run will create configuration files in the same directory

### Installer Version
- Distribute `BitaxeMonitorInstaller.exe`
- Users run the installer for proper Windows integration
- Automatic uninstall support

## Troubleshooting

### Build Issues

**"PyInstaller not found"**
```cmd
pip install pyinstaller
```

**"Module not found during build"**
- Check that all dependencies are installed
- Add missing modules to `hiddenimports` in `bitaxe_monitor.spec`

**"Build fails with import errors"**
- Ensure you're using the same Python environment for build and testing
- Try building with `--clean` flag to clear caches

### Runtime Issues

**"Application won't start"**
- Run from Command Prompt to see error messages
- Check Windows Defender/Antivirus isn't blocking the executable
- Ensure target Windows version is supported (Windows 10+)

**"Missing DLL errors"**
- Try redistributing with the entire `dist` folder
- Install Visual C++ Redistributable on target machine

**"Connection timeouts"**
- These are normal - the app tries to connect to Bitaxe device
- Configure device IP in Settings tab after first launch

## Advanced Customization

### Custom Icon
Replace `generated-icon.png` with your own icon file and rebuild.

### Additional Files
Edit `bitaxe_monitor.spec` to include additional data files:
```python
datas=[
    ('your-file.txt', '.'),
    ('config-templates/*', 'templates'),
],
```

### Build Options
Modify `bitaxe_monitor.spec` for different configurations:
- `console=True` - Show console window for debugging
- `debug=True` - Include debug information
- `upx=False` - Disable UPX compression for compatibility

## File Sizes and Performance

### Expected Sizes
- **Executable**: ~50-70 MB (includes Python runtime and all dependencies)
- **Installer**: ~50-70 MB (same size, different packaging)

### Performance Notes
- First startup may be slower (2-3 seconds) as temporary files are extracted
- Subsequent launches are faster
- Memory usage: ~50-100 MB depending on chart data

## Security and Signing

### Code Signing (Professional)
For commercial distribution, consider code signing:
1. Obtain a code signing certificate
2. Use `signtool.exe` to sign the executable
3. This prevents Windows security warnings

### Antivirus False Positives
- Some antivirus software may flag the executable as suspicious
- This is common with PyInstaller executables
- Code signing helps reduce false positives
- Submit to antivirus vendors for whitelisting if needed

## Support and Maintenance

### Updating the Application
To release a new version:
1. Update version numbers in `version_info.txt`
2. Update changelog/release notes
3. Rebuild using the same process
4. Test on clean Windows installation

### User Support
- Provide `README_WINDOWS.txt` with the executable
- Include troubleshooting steps for common issues
- Direct users to check application logs for technical issues

---

**Build Status**: ✅ Build system configured and tested
**Last Updated**: July 20, 2025
**Tested On**: Windows 10/11 with Python 3.8+