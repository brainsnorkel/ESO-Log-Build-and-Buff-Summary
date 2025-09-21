!define APPNAME "ESO Top Builds"
!define COMPANYNAME "ESO Community"
!define DESCRIPTION "ESO Logs Analysis Tool"
!define VERSIONMAJOR 0
!define VERSIONMINOR 1
!define VERSIONBUILD 0
!define VERSIONSUFFIX "-beta"
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
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME} ${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}${VERSIONSUFFIX}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$\"$INSTDIR\ESO-Log-Build-and-Buff-Summary.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}${VERSIONSUFFIX}"
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
