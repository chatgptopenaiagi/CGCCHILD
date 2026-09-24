param([string]$InnoCompiler = "$env:LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe")
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$python = Join-Path $root '.venv/Scripts/python.exe'
function Check-Exit { if ($LASTEXITCODE -ne 0) { throw "Build command failed: $LASTEXITCODE" } }
& $python -m build --wheel --no-isolation
Check-Exit
$env:PYTHONPATH = Join-Path $root 'src'
& $python -m PyInstaller --noconfirm packaging/CGC.spec
Check-Exit
& $python packaging/stage.py
Check-Exit
if (!(Test-Path -LiteralPath $InnoCompiler)) { throw 'Inno Setup compiler unavailable; onedir build remains available' }
& $InnoCompiler packaging/installer.iss
Check-Exit
