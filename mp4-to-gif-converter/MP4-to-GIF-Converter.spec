# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the desktop app (run from mp4-to-gif-converter/).
# Prerequisites: python setup_ffmpeg.py  (places ffmpeg.exe/ffprobe.exe in desktop_app/bin/)

from pathlib import Path

block_cipher = None
project_root = Path(SPECPATH)
desktop_app = project_root / 'desktop_app'
ffmpeg_bin = desktop_app / 'bin'

for required in (ffmpeg_bin / 'ffmpeg.exe', ffmpeg_bin / 'ffprobe.exe'):
    if not required.is_file():
        raise SystemExit(
            f"Missing {required.name}. Run 'python setup_ffmpeg.py' before building."
        )

a = Analysis(
    [str(desktop_app / 'main.py')],
    pathex=[str(desktop_app)],
    binaries=[],
    datas=[
        (str(desktop_app / 'templates'), 'templates'),
        (str(ffmpeg_bin / 'ffmpeg.exe'), 'bin'),
        (str(ffmpeg_bin / 'ffprobe.exe'), 'bin'),
        (str(project_root / 'app_icon.ico'), '.'),
    ],
    hiddenimports=[
        'webview',
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
        'flask',
        'waitress',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MP4-to-GIF-Converter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'app_icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MP4-to-GIF-Converter',
)
