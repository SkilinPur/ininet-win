# Build ininet-win.exe (single-file) with PyInstaller.
# Usage:  powershell -ExecutionPolicy Bypass -File build.ps1
[CmdletBinding()]
param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root

$Venv = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Venv)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
}

Write-Host "Installing build dependencies..." -ForegroundColor Cyan
& $Venv -m pip install --quiet --upgrade pip
& $Venv -m pip install --quiet -e ".[tui,dev]" pyinstaller

Write-Host "Generating icon and version metadata..." -ForegroundColor Cyan
& $Venv (Join-Path $Root "tools\make_icon.py")
& $Venv (Join-Path $Root "tools\make_version_info.py")

if ($Clean) {
    Write-Host "Cleaning previous build output..." -ForegroundColor Cyan
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist
}

Write-Host "Running tests..." -ForegroundColor Cyan
& $Venv -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed; aborting build." }

Write-Host "Building ininet-win.exe..." -ForegroundColor Cyan
& $Venv -m PyInstaller "ininet-win.spec" --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed." }

$Exe = Join-Path $Root "dist\ininet-win.exe"
if (-not (Test-Path -LiteralPath $Exe)) { throw "Executable not found at $Exe" }

$SizeMb = [math]::Round((Get-Item -LiteralPath $Exe).Length / 1MB, 1)
Write-Host "OK: $Exe ($SizeMb MB)" -ForegroundColor Green
Write-Host "Smoke test:  & '$Exe' version" -ForegroundColor Green
