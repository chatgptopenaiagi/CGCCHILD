#ifndef AppVersion
  #define AppVersion "0.4.0"
#endif
#ifndef AppId
  #define AppId "{{48A3FA0A-F8D0-436A-91A2-19C1FD5F3382}"
#endif
#ifndef SourceDir
  #define SourceDir "..\dist\CGC"
#endif
#ifndef OutputDir
  #define OutputDir "..\dist"
#endif
#ifndef OutputBaseFilename
  #define OutputBaseFilename "CGCCHILD-Setup-" + AppVersion
#endif
#ifndef VersionInfoVersion
  #define VersionInfoVersion "0.4.0.0"
#endif
[Setup]
AppId={#AppId}
AppName=CREDID GUARDIAN CODEX
AppVersion={#AppVersion}
AppPublisher=Mihai-Bogdan Simion
AppPublisherURL=https://github.com/chatgptopenaiagi/CGCCHILD
DefaultDirName={autopf}\CGCCHILD
DefaultGroupName=CREDID GUARDIAN CODEX
UninstallDisplayIcon={app}\CGC.exe
OutputDir={#OutputDir}
OutputBaseFilename={#OutputBaseFilename}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog commandline
LicenseFile=..\LICENSE
DisableProgramGroupPage=yes
VersionInfoVersion={#VersionInfoVersion}
VersionInfoDescription=CGCCHILD Experimental Windows Setup

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\CREDID GUARDIAN CODEX"; Filename: "{app}\CGC.exe"
Name: "{autodesktop}\CREDID GUARDIAN CODEX"; Filename: "{app}\CGC.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\CGC.exe"; Description: "Launch CREDID GUARDIAN CODEX"; Flags: nowait postinstall skipifsilent
