; Tsufutube Downloader - Inno Setup Script
; Version 1.0
; Build the installer by right-clicking this file and selecting "Compile"

#define MyAppName "Tsufutube Downloader"
#define MyAppVersion "1.0"
#define MyAppPublisher "Tsufutube"
#define MyAppURL "https://github.com/tsufuwu/tsufutube_downloader"
#define MyAppExeName "Tsufutube-Downloader.exe"
#define MyAppAssocName "Video Link"
#define MyAppAssocExt ".tsufutube"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; Unique Application ID (DO NOT CHANGE after first release)
AppId={{B5F8C3D1-9A2E-4F6B-8D7C-1E3A5B2C4D0F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; Allow user to choose install location
AllowNoIcons=yes
; Output installer settings
OutputDir=installer_output
OutputBaseFilename=Tsufutube-Downloader-Setup-v{#MyAppVersion}
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; Installer appearance
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardStyle=modern
WizardResizable=no
; Privileges (don't require admin if installing to user folder)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Supported Windows versions
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
; Note: To add Vietnamese, download Vietnamese.isl from:
; https://github.com/jrsoftware/issrc/tree/main/Files/Languages/Unofficial
; and place it in: C:\Program Files (x86)\Inno Setup 6\Languages\

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main executable
Source: "dist\Tsufutube-Downloader\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; _internal folder (Python runtime and dependencies)
Source: "dist\Tsufutube-Downloader\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; Assets folder
Source: "dist\Tsufutube-Downloader\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; FFmpeg folder (if bundled)
Source: "dist\Tsufutube-Downloader\ffmpeg\*"; DestDir: "{app}\ffmpeg"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

; Python scripts that need to be in root
Source: "dist\Tsufutube-Downloader\*.py"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up settings and cache on uninstall (optional - user can keep them)
Type: filesandordirs; Name: "{localappdata}\Tsufutube"     
Type: filesandordirs; Name: "{app}\*.log"
Type: filesandordirs; Name: "{app}\temp"

[Code]
// Custom uninstall confirmation
function InitializeUninstall: Boolean;
begin
  Result := MsgBox('Are you sure you want to uninstall {#MyAppName}?' + #13#10 + #13#10 + 
                   'Your settings and download history will also be removed.', 
                   mbConfirmation, MB_YESNO) = IDYES;
end;

// Check if app is running before install/uninstall
function IsAppRunning: Boolean;
var
  ResultCode: Integer;
begin
  Exec('tasklist', '/FI "IMAGENAME eq {#MyAppExeName}" /NH', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := ResultCode = 0;
end;

function InitializeSetup: Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  
  // Check if app is running
  if IsAppRunning then
  begin
    if MsgBox('{#MyAppName} is currently running.' + #13#10 + 
              'It will be closed before installation. Continue?', 
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      // Kill the running application
      Exec('taskkill', '/F /IM "{#MyAppExeName}"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      Sleep(1000);
    end
    else
      Result := False;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    // Kill the app if running
    Exec('taskkill', '/F /IM "{#MyAppExeName}"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Sleep(500);
  end;
end;
