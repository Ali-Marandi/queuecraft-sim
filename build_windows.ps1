# QueueCraft Enterprise AI v3.2 — reproducible 64-bit Windows build
# Run in an x64 Windows PowerShell session:
#   .\build_windows.ps1 -Version "3.2.0"

[CmdletBinding()]
param(
    [string]$Version = "3.2.0",
    [switch]$SkipInstaller,
    [switch]$SkipTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot
$Python = "py"
$AppName = "QueueCraftEnterpriseAI"
$DistPath = Join-Path $ProjectRoot "dist\$AppName"
$ReleasePath = Join-Path $ProjectRoot "release"
$InnoCompiler = Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"
$InstallerPath = Join-Path $ReleasePath "QueueCraftEnterpriseAI-v$Version-Setup-x64.exe"

function Invoke-CodeSigning([string]$FilePath) {
    if (-not (Test-Path $FilePath)) { throw "File to sign does not exist: $FilePath" }
    if ($env:SIGN_CERTIFICATE_PATH -and $env:SIGN_CERTIFICATE_PASSWORD) {
        Write-Host "Signing $([System.IO.Path]::GetFileName($FilePath))..." -ForegroundColor Cyan
        & signtool.exe sign /fd SHA256 /f $env:SIGN_CERTIFICATE_PATH /p $env:SIGN_CERTIFICATE_PASSWORD /tr http://timestamp.digicert.com /td SHA256 $FilePath
        if ($LASTEXITCODE -ne 0) { throw "Authenticode signing failed for $FilePath." }
    } else {
        Write-Host "Code signing skipped; secure certificate environment variables were not supplied." -ForegroundColor Yellow
    }
}

Write-Host "[1/7] Installing reproducible Python runtime dependencies..." -ForegroundColor Cyan
& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt

Write-Host "[2/7] Installing local UI build dependencies..." -ForegroundColor Cyan
npm install

if (-not $SkipTests) {
    Write-Host "[3/7] Running release-gate regression tests..." -ForegroundColor Cyan
    npm test
    & $Python -m unittest -v test_ai_monte_carlo.py test_priority_queue.py test_scenario_manager.py test_data_import.py test_decision_analytics.py test_cloud_cluster_scaling.py test_multi_region_failover.py test_distributed_load_testing.py test_live_slo_monitoring.py test_distributed_stress_scenarios.py test_generative_queue_optimizer.py test_app_v4_bridge.py
} else {
    Write-Host "[3/7] Regression tests skipped by explicit switch." -ForegroundColor Yellow
}

Write-Host "[4/7] Building offline UI assets..." -ForegroundColor Cyan
npm run build:assets
if (-not (Test-Path "assets\vendor\tailwind.css") -or -not (Test-Path "assets\vendor\chart.umd.js")) {
    throw "Offline UI assets were not generated."
}

Write-Host "[5/7] Cleaning previous output and bundling native application..." -ForegroundColor Cyan
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist, release
New-Item -ItemType Directory -Force -Path $ReleasePath | Out-Null
& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --onedir `
  --name $AppName `
  --add-data "index.html;." `
  --add-data "queuecraft.js;." `
  --add-data "assets;assets" `
  --add-data "locales;locales" `
  --add-data "examples;examples" `
  --collect-all webview `
  --collect-all numpy `
  --collect-all matplotlib `
  --collect-all pandas `
  --collect-all openpyxl `
  --collect-all xlrd `
  --hidden-import multi_region_failover `
  --hidden-import distributed_load_testing `
  --hidden-import live_slo_monitoring `
  --hidden-import generative_queue_optimizer `
  --collect-all openai `
  --hidden-import webview.platforms.edgechromium `
  app.py

$AppExecutable = Join-Path $DistPath "$AppName.exe"
if (-not (Test-Path $AppExecutable)) { throw "PyInstaller did not create the application executable." }

Write-Host "[6/7] Signing application bundle when a secure certificate is available..." -ForegroundColor Cyan
Invoke-CodeSigning $AppExecutable

if (-not $SkipInstaller) {
    Write-Host "[7/7] Creating and signing Windows installer..." -ForegroundColor Cyan
    if (-not (Test-Path $InnoCompiler)) {
        throw "Inno Setup 6 was not found. Install it or rerun with -SkipInstaller to retain the application folder."
    }
    & $InnoCompiler "/DMyAppVersion=$Version" "installer\QueueCraftEnterpriseAI.iss"
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup compilation failed." }
    Invoke-CodeSigning $InstallerPath
    Get-FileHash $InstallerPath -Algorithm SHA256 | Format-List | Out-Host
} else {
    Write-Host "[7/7] Installer skipped. Portable bundle available at: $DistPath" -ForegroundColor Yellow
}

Write-Host "QueueCraft Enterprise AI v$Version build completed successfully." -ForegroundColor Green
