# Build the Windows desktop app and verify FFmpeg is bundled for the installer.
# Run from mp4-to-gif-converter/:  .\build_desktop.ps1

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

Write-Host "Installing Python dependencies..."
python -m pip install -r desktop_app/requirements.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Ensuring FFmpeg binaries are present..."
python setup_ffmpeg.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Building with PyInstaller..."
pyinstaller --noconfirm MP4-to-GIF-Converter.spec
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$bundledFfmpeg = Join-Path $PSScriptRoot 'dist\MP4-to-GIF-Converter\_internal\bin\ffmpeg.exe'
$bundledFfprobe = Join-Path $PSScriptRoot 'dist\MP4-to-GIF-Converter\_internal\bin\ffprobe.exe'

foreach ($path in @($bundledFfmpeg, $bundledFfprobe)) {
    if (-not (Test-Path $path)) {
        Write-Error "Build succeeded but required file is missing: $path"
        exit 1
    }
}

Write-Host "Build OK. FFmpeg bundled at dist\MP4-to-GIF-Converter\_internal\bin\"
Write-Host "Next: compile MP4-to-GIF-Converter.iss with Inno Setup."
