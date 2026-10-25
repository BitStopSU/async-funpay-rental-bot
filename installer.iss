#define AppName "Async FunPay Rental Bot"
#define AppId "{{B615A7EA-1E18-4F85-9DE7-70B3A5B145F6}"
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=BitStopSU
DefaultDirName={localappdata}\Programs\AsyncFunPayRentalBot
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=AsyncFunPayRentalBot-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "*.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion
Source: "start.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{cmd}"; Parameters: "/c ""{app}\start.bat"""; WorkingDir: "{app}"
Name: "{autodesktop}\{#AppName}"; Filename: "{cmd}"; Parameters: "/c ""{app}\start.bat"""; WorkingDir: "{app}"; Tasks: desktopicon
