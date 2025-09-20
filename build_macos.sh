#!/bin/bash

echo "Building ESO Top Builds for macOS..."
echo

echo "Step 1: Cleaning previous builds..."
rm -rf dist build

echo
echo "Step 2: Installing dependencies..."
pip install -r requirements.txt
pip install pyinstaller

echo
echo "Step 3: Building macOS executable..."
pyinstaller --onefile --name "ESO-Log-Build-and-Buff-Summary" --console \
  --hidden-import reportlab \
  --hidden-import httpx \
  --hidden-import aiofiles \
  --hidden-import esologs \
  --hidden-import dotenv \
  --hidden-import reportlab.pdfgen \
  --hidden-import reportlab.lib \
  --hidden-import reportlab.lib.colors \
  --hidden-import reportlab.platypus \
  --hidden-import reportlab.lib.styles \
  --hidden-import reportlab.lib.units \
  --hidden-import reportlab.lib.enums \
  --add-data "src/eso_builds:src/eso_builds" \
  --add-data "README.md:." \
  --add-data "USAGE.md:." \
  single_report_tool.py

if [ ! -f "dist/ESO-Log-Build-and-Buff-Summary" ]; then
    echo "ERROR: Failed to create macOS executable"
    exit 1
fi

echo
echo "Step 4: Creating macOS DMG..."
if command -v create-dmg &> /dev/null; then
    # Create DMG
    create-dmg \
      --volname "ESO Log Build and Buff Summary" \
      --window-pos 200 120 \
      --window-size 600 300 \
      --icon-size 100 \
      --hide-extension "ESO-Log-Build-and-Buff-Summary" \
      "ESO-Log-Build-and-Buff-Summary-macOS-$(date +%Y%m%d_%H%M).dmg" \
      "dist/"
    
    echo "SUCCESS: macOS DMG created"
else
    echo "WARNING: create-dmg not available - install with: brew install create-dmg"
    echo "Portable executable created: dist/ESO-Log-Build-and-Buff-Summary"
fi

echo
echo "Build complete!"
