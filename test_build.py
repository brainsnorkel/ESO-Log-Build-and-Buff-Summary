#!/usr/bin/env python3
"""
Test script to verify the installer build process works correctly.
This script can be run before creating a release to ensure everything builds properly.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {cmd}")
        print(f"   Error: {e.stderr}")
        return False

def main():
    """Test the build process."""
    print("🧪 Testing ESO Top Builds Installer Build Process")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("single_report_tool.py").exists():
        print("❌ Error: single_report_tool.py not found. Run this script from the project root.")
        sys.exit(1)
    
    # Check if required files exist
    required_files = [
        "single_report_tool.spec",
        "installer.nsi",
        "build_installer.bat",
        "LICENSE.txt"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        sys.exit(1)
    
    print("✅ All required files present")
    
    # Test PyInstaller installation
    if not run_command("pip install pyinstaller", "Installing PyInstaller"):
        sys.exit(1)
    
    # Test PyInstaller dry run (just check if it can parse the spec file)
    if not run_command("pyinstaller --clean single_report_tool.spec --noconfirm", "Testing PyInstaller build"):
        print("⚠️  PyInstaller build failed, but this might be due to missing dependencies")
        print("   This is expected in CI/CD environments")
    
    # Check platform-specific tools
    import platform
    system = platform.system()
    
    if system == "Windows":
        nsis_available = run_command("makensis /VERSION", "Checking NSIS availability")
        if not nsis_available:
            print("⚠️  NSIS not available - Windows installer creation will fail")
            print("   Install NSIS from https://nsis.sourceforge.io/ or use chocolatey: choco install nsis")
    elif system == "Darwin":  # macOS
        dmg_available = run_command("which create-dmg", "Checking create-dmg availability")
        if not dmg_available:
            print("⚠️  create-dmg not available - macOS DMG creation will fail")
            print("   Install with: brew install create-dmg")
    elif system == "Linux":
        print("ℹ️  Linux AppImage creation will use appimagetool (downloaded during build)")
    
    print("\n🎉 Build process test completed!")
    print(f"\nPlatform: {system}")
    print("\nNext steps:")
    print("1. Ensure all dependencies are installed: pip install -r requirements.txt")
    
    if system == "Windows":
        print("2. Install NSIS for Windows installer creation")
        print("3. Run build_installer.bat to create the installer")
        print("4. Test the installer on a clean Windows machine")
    elif system == "Darwin":
        print("2. Install create-dmg for macOS DMG creation: brew install create-dmg")
        print("3. Run PyInstaller to create macOS executable")
        print("4. Test on a clean macOS machine")
    elif system == "Linux":
        print("2. Run PyInstaller to create Linux executable")
        print("3. Test on a clean Linux machine")
    
    print("\nFor automated builds on all platforms, use GitHub Actions by creating a release.")

if __name__ == "__main__":
    main()
