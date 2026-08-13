; QueueCraft Enterprise AI v3.2 — Inno Setup installer definition
; Compile through build_windows.ps1 after PyInstaller creates dist\QueueCraftEnterpriseAI.

#ifndef MyAppVersion
  #define MyAppVersion "3.2.0"
#endif

#define MyAppName "QueueCraft Enterprise AI"
#define MyAppPublisher "QueueCraft"
#define MyAppExeName "QueueCraftEnterpriseAI.exe"
#define MyAppURL "https://github.com/Ali-Marandi/queuecraft-sim"

[Setup]
AppId={{D0EE550E-47B9-4AF3-B948-55E3343B716A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\QueueCraft Enterprise AI
DefaultGroupName=QueueCraft Enterprise AI
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
OutputDir=..\release
OutputBaseFilename=QueueCraftEnterpriseAI-v{#MyAppVersion}-Setup-x64
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\QueueCraftEnterpriseAI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; To include WebView2 as an offline prerequisite, place its redistributable installer
; at third_party\MicrosoftEdgeWebView2RuntimeInstallerX64.exe and uncomment the next line.
; Source: "..\third_party\MicrosoftEdgeWebView2RuntimeInstallerX64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
; Optional offline WebView2 runtime installation when the file line above is enabled:
; Filename: "{tmp}\MicrosoftEdgeWebView2RuntimeInstallerX64.exe"; Parameters: "/silent /install"; Flags: waituntilterminated skipifdoesntexist
