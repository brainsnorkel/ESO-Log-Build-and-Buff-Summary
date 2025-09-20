#!/bin/bash

echo "Building ESO Top Builds for Linux..."
echo

echo "Step 1: Cleaning previous builds..."
rm -rf dist build

echo
echo "Step 2: Installing dependencies..."
pip install -r requirements.txt
pip install pyinstaller

echo
echo "Step 3: Building Linux executable..."
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
    echo "ERROR: Failed to create Linux executable"
    exit 1
fi

echo
echo "Step 4: Creating Linux AppImage..."
# Install appimagetool
wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# Create AppDir structure
mkdir -p ESO-Log-Build-and-Buff-Summary.AppDir/usr/bin
mkdir -p ESO-Log-Build-and-Buff-Summary.AppDir/usr/share/applications
mkdir -p ESO-Log-Build-and-Buff-Summary.AppDir/usr/share/icons

# Copy executable
cp dist/ESO-Log-Build-and-Buff-Summary ESO-Log-Build-and-Buff-Summary.AppDir/usr/bin/

# Create desktop file
cat > ESO-Log-Build-and-Buff-Summary.AppDir/usr/share/applications/eso-log-build-and-buff-summary.desktop << EOF
[Desktop Entry]
Type=Application
Name=ESO Log Build and Buff Summary
Comment=Analyze ESO trial logs and generate build reports
Exec=ESO-Log-Build-and-Buff-Summary
Icon=eso-log-build-and-buff-summary
Terminal=true
Categories=Game;
EOF

# Create AppRun
cat > ESO-Log-Build-and-Buff-Summary.AppDir/AppRun << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
exec ./usr/bin/ESO-Log-Build-and-Buff-Summary "$@"
EOF
chmod +x ESO-Log-Build-and-Buff-Summary.AppDir/AppRun

# Create AppImage
./appimagetool-x86_64.AppImage ESO-Log-Build-and-Buff-Summary.AppDir ESO-Log-Build-and-Buff-Summary-Linux-$(date +%Y%m%d_%H%M).AppImage

if [ -f "ESO-Log-Build-and-Buff-Summary-Linux-$(date +%Y%m%d_%H%M).AppImage" ]; then
    echo "SUCCESS: Linux AppImage created"
else
    echo "WARNING: AppImage creation failed, but portable executable is available"
fi

echo
echo "Build complete!"
echo "Portable executable: dist/ESO-Log-Build-and-Buff-Summary"
