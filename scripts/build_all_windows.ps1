$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

Set-Location $Root
& (Join-Path $PSScriptRoot "install_windows.ps1")
& (Join-Path $PSScriptRoot "build_desktop_windows.ps1")

if (Get-Command npm -ErrorAction SilentlyContinue) {
    & (Join-Path $PSScriptRoot "build_frontend_windows.ps1")
} else {
    Write-Host "Build Electron ignorado porque npm nao foi encontrado." -ForegroundColor Yellow
}

Write-Host "Build Windows concluido." -ForegroundColor Green
