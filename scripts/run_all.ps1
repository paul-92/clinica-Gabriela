$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$ApiScript = Join-Path $PSScriptRoot "run_api.ps1"
$FrontendScript = Join-Path $PSScriptRoot "run_frontend.ps1"

Set-Location $Root

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$ApiScript`""
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$FrontendScript`""

Write-Host "Backend e frontend iniciados em janelas separadas." -ForegroundColor Green
