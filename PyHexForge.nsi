; PyHexForge Installer Script
!include "MUI2.nsh"

Name "PyHexForge"
OutFile "PyHexForge_Setup.exe"
InstallDir "$PROGRAMFILES\PyHexForge"
InstallDirRegKey HKCU "Software\PyHexForge" ""

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  
  ; Copy the executable from PyInstaller's dist folder
  File "dist\PyHexForge.exe"
  
  ; Create Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\PyHexForge"
  CreateShortCut "$SMPROGRAMS\PyHexForge\PyHexForge.lnk" "$INSTDIR\PyHexForge.exe"
  CreateShortCut "$SMPROGRAMS\PyHexForge\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  CreateShortCut "$DESKTOP\PyHexForge.lnk" "$INSTDIR\PyHexForge.exe"
  
  ; Write uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; Write registry keys for uninstall
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PyHexForge" "DisplayName" "PyHexForge"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PyHexForge" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PyHexForge" "DisplayIcon" "$\"$INSTDIR\PyHexForge.exe$\""
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PyHexForge" "Publisher" "Your Name"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PyHexForge" "DisplayVersion" "1.0"
  
  ; Remember installation folder
  WriteRegStr HKCU "Software\PyHexForge" "" $INSTDIR
SectionEnd

Section "Uninstall"
  ; Remove files
  Delete "$INSTDIR\PyHexForge.exe"
  Delete "$INSTDIR\Uninstall.exe"
  
  ; Remove shortcuts
  Delete "$DESKTOP\PyHexForge.lnk"
  Delete "$SMPROGRAMS\PyHexForge\PyHexForge.lnk"
  Delete "$SMPROGRAMS\PyHexForge\Uninstall.lnk"
  RMDir "$SMPROGRAMS\PyHexForge"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PyHexForge"
  DeleteRegKey HKCU "Software\PyHexForge"
  
  ; Remove installation directory
  RMDir "$INSTDIR"
SectionEnd