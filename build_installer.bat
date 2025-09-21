@echo off
echo Building ESO Top Builds Windows Installer...
echo.

echo Step 1: Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del "*.spec"

echo.
echo Step 2: Installing PyInstaller...
pip install pyinstaller

echo.
echo Step 3: Building executable...
pyinstaller --onefile --name "ESO-Log-Build-and-Buff-Summary" --console ^
    --hidden-import reportlab ^
    --hidden-import httpx ^
    --hidden-import aiofiles ^
    --hidden-import esologs ^
    --hidden-import dotenv ^
    --hidden-import reportlab.pdfgen ^
    --hidden-import reportlab.lib ^
    --hidden-import reportlab.lib.colors ^
    --hidden-import reportlab.platypus ^
    --hidden-import reportlab.lib.styles ^
    --hidden-import reportlab.lib.units ^
    --hidden-import reportlab.lib.enums ^
    --add-data "src/eso_builds;src/eso_builds" ^
    --add-data "README.md;." ^
    --add-data "USAGE.md;." ^
    single_report_tool.py

if not exist "dist\ESO-Log-Build-and-Buff-Summary.exe" (
    echo ERROR: Failed to create executable
    pause
    exit /b 1
)

echo.
echo Step 4: Creating installer...
if exist "installer.nsi" (
    makensis installer.nsi
    if exist "ESO-Log-Build-and-Buff-Summary-Installer.exe" (
        echo.
        echo SUCCESS: Installer created: ESO-Log-Build-and-Buff-Summary-Installer.exe
    ) else (
        echo ERROR: Failed to create installer
    )
) else (
    echo ERROR: installer.nsi not found
)

echo.
echo Build complete!
pause
