; Inno Setup Script for MP4 to GIF Converter 2
; この行はコメントです。セミコロンで始まります。

[Setup]
; アプリの基本情報（旧版と別ソフトとして扱えるよう名前を分ける）
AppName=MP4 to GIF Converter 2
AppVersion=2.0
AppPublisher=k3
AppPublisherURL=https://www.vector.co.jp/soft/winnt/art/se527852.html?ds

; インストーラー自体のアイコン（.iss と同じフォルダの app_icon.ico）
SetupIconFile=app_icon.ico

; 管理者権限を要求せず、ユーザーごとにインストールする
PrivilegesRequired=lowest

; 64ビットアプリのみ対応（32ビット Windows ではインストーラーを起動不可）
ArchitecturesAllowed=x64compatible
; 64ビットOSでは64ビットモードでインストールする
ArchitecturesInstallIn64BitMode=x64compatible
DefaultDirName={userpf}\MP4-to-GIF-Converter2
DefaultGroupName=MP4 to GIF Converter 2
DisableProgramGroupPage=yes
; 出力されるインストーラーのファイル名
OutputBaseFilename=MP4-to-GIF-Converter2_setup
; 圧縮設定（必須）
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; アンインストーラーにアプリアイコンを表示
UninstallDisplayIcon={app}\app_icon.ico

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; PyInstaller onedir 出力（build_desktop.ps1 / MP4-to-GIF-Converter.spec でビルド）。
; FFmpeg は spec で desktop_app\bin\ を _internal\bin\ に同梱する。未ビルドだと起動時に失敗します。
Source: "dist\MP4-to-GIF-Converter2\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; ショートカット／アンインストーラ用アイコン
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion


[Icons]
; スタートメニューとデスクトップにショートカットを作成します。
Name: "{group}\MP4 to GIF Converter 2"; Filename: "{app}\MP4-to-GIF-Converter2.exe"; IconFilename: "{app}\app_icon.ico"
Name: "{autodesktop}\MP4 to GIF Converter 2"; Filename: "{app}\MP4-to-GIF-Converter2.exe"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon

[Run]
; インストール完了後にアプリを起動するオプション（任意）
Filename: "{app}\MP4-to-GIF-Converter2.exe"; Description: "{cm:LaunchProgram,MP4 to GIF Converter 2}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; アンインストール時に本ソフトの AppData だけを削除する（旧版のデータは消さない）
; 設定・ログ・一時ファイル（uploads/outputs）
Type: filesandordirs; Name: "{localappdata}\MP4-to-GIF-Converter2"
