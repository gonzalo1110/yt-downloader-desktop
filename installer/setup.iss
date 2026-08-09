; Inno Setup script para YT Downloader
; Compilar con Inno Setup 6.x en la máquina Windows de build
; Requiere: build_windows.bat ejecutado primero (genera dist\main.exe)

#define MyAppName "YT Downloader"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "YTDownloader"
#define MyAppURL ""
#define MyAppExeName "main.exe"

[Setup]
AppId={{B8F7A3D1-5E2C-4A9B-8D6F-1C3E5A7B9D0F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=YTDownloader_Setup_v{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=..\resources\icon.ico

; --- Información de versión en el instalador ---
VersionInfoVersion=1.0.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: checked

[Files]
Source: "..\dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSES.txt"; DestDir: "{app}"; Flags: ignoreversion
; ffmpeg, ffprobe y deno van embebidos en el onefile de Nuitka

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{app}\LICENSES.txt"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\YTDownloader\*"

; --- Disclaimer legal breve ---
[Code]
function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
end;

procedure InitializeWizard;
var
  Page: TWizardPage;
  Label1: TNewStaticText;
begin
  Page := CreateCustomPage(wpWelcome, 'Aviso legal', '');
  Label1 := TNewStaticText.Create(Page);
  Label1.WordWrap := True;
  Label1.Width := Page.SurfaceWidth;
  Label1.Height := 180;
  Label1.Caption :=
    'YT Downloader permite descargar videos de YouTube para uso personal.' + #13#10 + #13#10 +
    'Al usar este software aceptas que:' + #13#10 +
    '  - Solo descargaras contenido que tengas derecho a descargar.' + #13#10 +
    '  - No distribuiras el contenido descargado sin autorizacion.' + #13#10 +
    '  - Respetaras los terminos de servicio de YouTube.' + #13#10 + #13#10 +
    'Este software no esta afiliado ni respaldado por YouTube o Google.' + #13#10 + #13#10 +
    'Las licencias de los componentes de terceros (FFmpeg LGPL, yt-dlp' + #13#10 +
    'Unlicense, Deno MIT) se encuentran en LICENSES.txt en la carpeta' + #13#10 +
    'de instalacion.';
  Label1.Parent := Page.Surface;
end;
