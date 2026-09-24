#define AppVersion "0.3.0"
[Setup]
AppId={{48A3FA0A-F8D0-436A-91A2-19C1FD5F3382}
AppName=CREDID GUARDIAN CODEX
AppVersion={#AppVersion}
AppPublisher=Mihai-Bogdan Simion
AppPublisherURL=https://github.com/chatgptopenaiagi/CGCCHILD
DefaultDirName={autopf}\CGCCHILD
DefaultGroupName=CREDID GUARDIAN CODEX
UninstallDisplayIcon={app}\CGC.exe
OutputDir=..\dist
OutputBaseFilename=CGCCHILD-Setup-{#AppVersion}
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
VersionInfoVersion=0.3.0.0
VersionInfoDescription=CGCCHILD Experimental Windows Setup

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; Flags: unchecked

[Files]
Source: "..\dist\CGC\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\CREDID GUARDIAN CODEX"; Filename: "{app}\CGC.exe"
Name: "{autodesktop}\CREDID GUARDIAN CODEX"; Filename: "{app}\CGC.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\CGC.exe"; Description: "Launch CREDID GUARDIAN CODEX"; Flags: nowait postinstall skipifsilent
