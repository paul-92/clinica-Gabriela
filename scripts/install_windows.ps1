$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Root ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"
$Frontend = Join-Path $Root "frontend"

Write-Host "Instalando dependencias do sistema..." -ForegroundColor Cyan
Set-Location $Root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python nao encontrado. Instale Python 3.11 ou superior e tente novamente."
}

if (-not (Test-Path $Python)) {
    python -m venv $Venv
}

& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $Root "requirements.txt")

if (-not (Test-Path (Join-Path $Root "license.json"))) {
    & $Python "scripts\generate_license.py" --customer "Cliente em teste" --type trial --days 14
}

if (Get-Command npm -ErrorAction SilentlyContinue) {
    Set-Location $Frontend
    npm install
} else {
    Write-Host "npm nao encontrado. O backend e o desktop Python foram instalados; instale Node.js LTS para usar o frontend Electron." -ForegroundColor Yellow
}

Write-Host "Instalacao concluida." -ForegroundColor Green
