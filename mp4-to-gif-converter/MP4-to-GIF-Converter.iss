; Inno Setup Script for MP4-to-GIF-Converter
; この行はコメントです。セミコロンで始まります。

[Setup]
; アプリの基本情報
AppName=MP4-to-GIF-Converter
AppVersion=1.2
AppPublisher=k3
AppPublisherURL=https://www.vector.co.jp/soft/winnt/art/se527852.html?ds

; インストーラー自体のアイコン（.iss と同じフォルダの app_icon.ico）
SetupIconFile=app_icon.ico

; 管理者権限を要求せず、ユーザーごとにインストールする
PrivilegesRequired=lowest

; 64ビットOSでは64ビットモードでインストールする
ArchitecturesInstallIn64BitMode=x64compatible
DefaultDirName={userpf}\MP4-to-GIF-Converter
DefaultGroupName=MP4-to-GIF-Converter
DisableProgramGroupPage=yes
; 出力されるインストーラーのファイル名
OutputBaseFilename=MP4-to-GIF-Converter_setup
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
; PyInstaller onedir 出力（この .iss と同じフォルダからの相対パス）。
; ビルド後の dist\MP4-to-GIF-Converter\ 一式をインストールします。
Source: "dist\MP4-to-GIF-Converter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; ショートカット／アンインストーラ用アイコン
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion


[Icons]
; スタートメニューとデスクトップにショートカットを作成します。
Name: "{group}\MP4-to-GIF-Converter"; Filename: "{app}\MP4-to-GIF-Converter.exe"; IconFilename: "{app}\app_icon.ico"
Name: "{autodesktop}\MP4-to-GIF-Converter"; Filename: "{app}\MP4-to-GIF-Converter.exe"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon

[Run]
; インストール完了後にアプリを起動するオプション（任意）
Filename: "{app}\MP4-to-GIF-Converter.exe"; Description: "{cm:LaunchProgram,MP4-to-GIF-Converter}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; アンインストール時にAppDataに作成したフォルダを削除する
; 設定・ログ・一時ファイル（uploads/outputs）
Type: filesandordirs; Name: "{localappdata}\MP4-to-GIF-Converter"
; 旧版がホーム直下に保存していたデータ
Type: filesandordirs; Name: "{userprofile}\.mp4togifconverter"
