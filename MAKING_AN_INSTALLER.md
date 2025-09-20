# Making a Windows Installer for ESO Top Builds

This guide explains how to create a Windows installer for the ESO Top Builds Python application, making it easy for Windows users to install and use without requiring Python knowledge.

## 📋 Overview

Your ESO Top Builds project can be packaged into a professional Windows installer that:
- Bundles Python and all dependencies into a single executable
- Creates a proper Windows application with Start Menu shortcuts
- Handles API credentials setup
- Provides an uninstaller
- Works on Windows 10/11 without requiring Python installation

## 🛠️ Prerequisites

Before creating the installer, ensure you have:
- Windows machine (or Windows VM)
- Python 3.9+ installed
- Your ESO Top Builds project working locally
- Administrator privileges

## 📦 Method 1: PyInstaller + NSIS (Recommended)

This method creates a professional Windows installer with proper integration.

### Step 1: Install Required Tools

```bash
# Install PyInstaller
pip install pyinstaller

# Install NSIS (download from https://nsis.sourceforge.io/)
# Or use chocolatey:
choco install nsis
```

### Step 2: Create PyInstaller Spec File

Create `single_report_tool.spec` in your project root:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['single_report_tool.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/eso_builds', 'src/eso_builds'),
        ('README.md', '.'),
        ('USAGE.md', '.'),
    ],
    hiddenimports=[
        'reportlab',
        'httpx',
        'aiofiles',
        'esologs',
        'dotenv',
        'reportlab.pdfgen',
        'reportlab.lib',
        'reportlab.lib.colors',
        'reportlab.platypus',
        'reportlab.lib.styles',
        'reportlab.lib.units',
        'reportlab.lib.enums',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ESO-Log-Build-and-Buff-Summary',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'  # Optional: add an icon file
)
```

### Step 3: Create NSIS Installer Script

Create `installer.nsi`:

```nsis
!define APPNAME "ESO Top Builds"
!define COMPANYNAME "ESO Community"
!define DESCRIPTION "ESO Logs Analysis Tool"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0
!define HELPURL "https://github.com/brainsnorkel/ESO-Log-Build-and-Buff-Summary"
!define UPDATEURL "https://github.com/brainsnorkel/ESO-Log-Build-and-Buff-Summary"
!define ABOUTURL "https://github.com/brainsnorkel/ESO-Log-Build-and-Buff-Summary"
!define INSTALLSIZE 50000

RequestExecutionLevel admin
InstallDir "$PROGRAMFILES\${APPNAME}"
Name "${APPNAME}"
outFile "ESO-Log-Build-and-Buff-Summary-Installer.exe"

!include LogicLib.nsh
!include MUI2.nsh

!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "header.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "welcome.bmp"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${If} $0 != "admin"
    messageBox mb_iconstop "Administrator rights required!"
    setErrorLevel 740
    quit
${EndIf}
!macroend

function .onInit
    setShellVarContext all
    !insertmacro VerifyUserIsAdmin
functionEnd

section "install"
    setOutPath $INSTDIR
    file "dist\ESO-Log-Build-and-Buff-Summary.exe"
    file "README.md"
    file "USAGE.md"
    file "LICENSE.txt"
    
    # Create config directory
    createDirectory "$APPDATA\ESO-Log-Build-and-Buff-Summary"
    
    writeUninstaller "$INSTDIR\uninstall.exe"
    
    # Start Menu shortcuts
    createDirectory "$SMPROGRAMS\${APPNAME}"
    createShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\ESO-Log-Build-and-Buff-Summary.exe" "" "$INSTDIR\ESO-Log-Build-and-Buff-Summary.exe" 0
    createShortCut "$SMPROGRAMS\${APPNAME}\User Guide.lnk" "$INSTDIR\USAGE.md"
    createShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    
    # Desktop shortcut
    createShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\ESO-Log-Build-and-Buff-Summary.exe" "" "$INSTDIR\ESO-Log-Build-and-Buff-Summary.exe" 0
    
    # Registry entries for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$\"$INSTDIR\ESO-Log-Build-and-Buff-Summary.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
    
    # Create .env template
    FileOpen $0 "$APPDATA\ESO-Log-Build-and-Buff-Summary\.env.template" w
    FileWrite $0 "ESOLOGS_ID=your_client_id_here$\r$\n"
    FileWrite $0 "ESOLOGS_SECRET=your_client_secret_here$\r$\n"
    FileClose $0
sectionEnd

section "uninstall"
    delete "$INSTDIR\ESO-Log-Build-and-Buff-Summary.exe"
    delete "$INSTDIR\README.md"
    delete "$INSTDIR\USAGE.md"
    delete "$INSTDIR\LICENSE.txt"
    delete "$INSTDIR\uninstall.exe"
    
    delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
    delete "$SMPROGRAMS\${APPNAME}\User Guide.lnk"
    delete "$SMPROGRAMS\${APPNAME}\Uninstall.lnk"
    delete "$DESKTOP\${APPNAME}.lnk"
    rmdir "$SMPROGRAMS\${APPNAME}"
    
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    
    rmdir $INSTDIR
sectionEnd
```

### Step 4: Build Script

Create `build_installer.bat`:

```batch
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
```

### Step 5: Run the Build

```bash
# Run the build script
build_installer.bat
```

## 🎨 Method 2: GUI Wrapper (Optional Enhancement)

For users who prefer a GUI, create a simple launcher:

### Create `gui_launcher.py`:

```python
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import subprocess
import os
import sys
import threading

class ESOTopBuildsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESO Top Builds - Report Analyzer")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="ESO Top Builds", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Report input
        ttk.Label(main_frame, text="ESO Logs Report:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.report_entry = ttk.Entry(main_frame, width=50)
        self.report_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        # Help button
        help_btn = ttk.Button(main_frame, text="?", command=self.show_help, width=3)
        help_btn.grid(row=1, column=2, padx=(5, 0))
        
        # Output format
        format_frame = ttk.LabelFrame(main_frame, text="Output Format", padding="5")
        format_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        format_frame.columnconfigure(0, weight=1)
        
        self.format_var = tk.StringVar(value="console")
        formats = [
            ("Console Only", "console"),
            ("Markdown File", "markdown"),
            ("Discord Format", "discord"),
            ("PDF Report", "pdf"),
            ("All Formats", "all")
        ]
        
        for i, (text, value) in enumerate(formats):
            ttk.Radiobutton(format_frame, text=text, variable=self.format_var, value=value).grid(
                row=i//3, column=i%3, sticky=tk.W, padx=5, pady=2
            )
        
        # Output directory
        ttk.Label(main_frame, text="Output Directory:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar(value="reports")
        output_entry = ttk.Entry(main_frame, textvariable=self.output_var, width=40)
        output_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        ttk.Button(main_frame, text="Browse", command=self.browse_folder).grid(row=3, column=2, padx=(5, 0))
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="5")
        options_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.verbose_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Verbose Output", variable=self.verbose_var).grid(row=0, column=0, sticky=tk.W)
        
        self.anonymize_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Anonymize Report", variable=self.anonymize_var).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="Analyze Report", command=self.analyze_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Open Output Folder", command=self.open_output_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Setup API Credentials", command=self.setup_credentials).pack(side=tk.LEFT, padx=5)
        
        # Output text area
        ttk.Label(main_frame, text="Output:").grid(row=6, column=0, sticky=tk.W, pady=(10, 0))
        
        self.output_text = scrolledtext.ScrolledText(main_frame, height=15, width=70)
        self.output_text.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(7, weight=1)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
    def show_help(self):
        help_text = """
ESO Logs Report Input:

• Report ID: mtFqVzQPNBcCrd1h
• Full URL: https://www.esologs.com/reports/mtFqVzQPNBcCrd1h

You can find the report ID in the URL of any ESO Logs report.
        """
        messagebox.showinfo("Help", help_text.strip())
        
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_var.set(folder)
            
    def open_output_folder(self):
        output_dir = self.output_var.get()
        if os.path.exists(output_dir):
            os.startfile(output_dir)
        else:
            messagebox.showwarning("Warning", f"Output directory '{output_dir}' does not exist.")
            
    def setup_credentials(self):
        cred_text = """
To use this tool, you need ESO Logs API credentials:

1. Go to: https://www.esologs.com/api/clients/
2. Create a new API client
3. Copy your Client ID and Secret
4. Create a .env file in: %APPDATA%\\ESO-Log-Build-and-Buff-Summary\\
5. Add these lines:
   ESOLOGS_ID=your_client_id
   ESOLOGS_SECRET=your_client_secret
        """
        messagebox.showinfo("API Setup", cred_text.strip())
        
    def analyze_report(self):
        report_code = self.report_entry.get().strip()
        if not report_code:
            messagebox.showerror("Error", "Please enter a report code or URL")
            return
            
        # Clear output
        self.output_text.delete(1.0, tk.END)
        
        # Start progress bar
        self.progress.start()
        
        # Run analysis in separate thread
        thread = threading.Thread(target=self.run_analysis, args=(report_code,))
        thread.daemon = True
        thread.start()
        
    def run_analysis(self, report_code):
        try:
            # Build command
            cmd = ["ESO-Log-Build-and-Buff-Summary.exe", report_code, "--output", self.format_var.get()]
            
            if self.output_var.get():
                cmd.extend(["--output-dir", self.output_var.get()])
                
            if self.verbose_var.get():
                cmd.append("--verbose")
                
            if self.anonymize_var.get():
                cmd.append("--anonymize")
            
            # Run command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Stream output to GUI
            for line in process.stdout:
                self.root.after(0, lambda l=line: self.output_text.insert(tk.END, l))
                self.root.after(0, self.output_text.see, tk.END)
                
            process.wait()
            
            # Stop progress bar
            self.root.after(0, self.progress.stop)
            
            if process.returncode == 0:
                self.root.after(0, lambda: messagebox.showinfo("Success", "Analysis complete!"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Analysis failed. Check output for details."))
                
        except Exception as e:
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to run analysis: {e}"))

if __name__ == "__main__":
    root = tk.Tk()
    app = ESOTopBuildsGUI(root)
    root.mainloop()
```

### Build GUI Version:

```batch
@echo off
echo Building GUI version...
pyinstaller --onefile --name "ESO-Log-Build-and-Buff-Summary-GUI" --windowed ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.messagebox ^
    --hidden-import tkinter.filedialog ^
    --hidden-import tkinter.scrolledtext ^
    --hidden-import threading ^
    gui_launcher.py
```

## 🚀 Method 3: Simple Portable Version

For a quick portable version without installer:

```batch
@echo off
echo Creating portable version...
pyinstaller --onefile --name "ESO-Log-Build-and-Buff-Summary-Portable" --console ^
    --add-data "src/eso_builds;src/eso_builds" ^
    --add-data "README.md;." ^
    --add-data "USAGE.md;." ^
    single_report_tool.py

echo.
echo Portable version created: dist\ESO-Log-Build-and-Buff-Summary-Portable.exe
echo Users can run this directly without installation.
```

## 🧪 Testing Your Installer

### Pre-Release Testing Checklist:

- [ ] Test on clean Windows 10 machine
- [ ] Test on clean Windows 11 machine  
- [ ] Verify all dependencies are included
- [ ] Test command-line arguments work
- [ ] Test file output generation (Markdown, Discord, PDF)
- [ ] Test uninstaller removes all files
- [ ] Test Start Menu shortcuts work
- [ ] Test desktop shortcut works
- [ ] Verify API credentials setup works
- [ ] Test with different report codes
- [ ] Test error handling (invalid report codes)
- [ ] Check file size is reasonable (< 100MB)

### Test Commands:

```bash
# Test basic functionality
ESO-Log-Build-and-Buff-Summary.exe --help

# Test with a real report
ESO-Log-Build-and-Buff-Summary.exe mtFqVzQPNBcCrd1h --output all

# Test error handling
ESO-Log-Build-and-Buff-Summary.exe invalidcode
```

## 🎨 Optional Enhancements

### 1. Add Icons and Graphics

- Create `icon.ico` (16x16, 32x32, 48x48, 256x256)
- Create `header.bmp` (150x57) for installer header
- Create `welcome.bmp` (164x314) for welcome page

### 2. Auto-Update Functionality

```python
# Add to your main script
def check_for_updates():
    """Check for application updates."""
    try:
        response = requests.get("https://api.github.com/repos/brainsnorkel/ESO-Log-Build-and-Buff-Summary/releases/latest")
        if response.status_code == 200:
            latest_version = response.json()["tag_name"]
            current_version = "1.0.0"  # Your current version
            if latest_version != current_version:
                print(f"Update available: {latest_version}")
                return True
    except:
        pass
    return False
```

### 3. Configuration File

Create a settings file for user preferences:

```python
# config.json
{
    "default_output_format": "markdown",
    "default_output_dir": "reports",
    "auto_open_output": true,
    "theme": "dark"
}
```

## 📦 Distribution Options

### 1. GitHub Releases
- Upload installer to GitHub Releases
- Include changelog and installation instructions
- Provide portable version alongside installer

### 2. Direct Download
- Host on your website
- Include download statistics
- Provide multiple download mirrors

### 3. Package Managers
- Chocolatey: `choco install eso-log-build-and-buff-summary`
- Scoop: `scoop install eso-log-build-and-buff-summary`

## 🔧 Troubleshooting

### Common Issues:

**"Failed to create executable"**
- Check all dependencies are installed
- Verify Python version compatibility
- Check for antivirus interference

**"Missing modules"**
- Add missing modules to `hiddenimports` in spec file
- Use `--collect-all` flag for problematic packages

**"Large file size"**
- Use `--exclude-module` for unused packages
- Consider using `--onedir` instead of `--onefile`
- Compress with UPX (already enabled in spec)

**"Antivirus false positives"**
- Submit to antivirus vendors for whitelisting
- Consider code signing certificate
- Provide checksums for verification

## 📝 Final Notes

Your ESO Top Builds project is perfect for Windows distribution because:

1. **Self-contained**: CLI tool with clear input/output
2. **No complex dependencies**: Standard Python libraries
3. **Clear use case**: ESO community will benefit from easy installation
4. **Professional output**: PDF reports justify the installer effort

The PyInstaller + NSIS combination provides the most professional result, while the portable version offers simplicity for power users.

Remember to:
- Update version numbers in NSIS script
- Test thoroughly before release
- Provide clear installation instructions
- Include troubleshooting guide
- Monitor user feedback for improvements
