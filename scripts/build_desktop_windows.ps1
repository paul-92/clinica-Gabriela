$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Dist = Join-Path $Root "dist\windows\desktop"
$Work = Join-Path $Root "build\pyinstaller"

if (-not (Test-Path $Python)) {
    throw "Ambiente virtual nao encontrado. Execute scripts\install_windows.ps1 primeiro."
}

Set-Location $Root
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --name "ClinicaPsicologiaDesktop" `
    --distpath $Dist `
    --workpath $Work `
    --noconsole `
    "main.py"

Write-Host "Build desktop Python gerado em dist\windows\desktop." -ForegroundColor Green
