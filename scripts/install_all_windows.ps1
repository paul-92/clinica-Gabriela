$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Root ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"
$Frontend = Join-Path $Root "frontend"

function Write-Step($Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Has-Command($Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Install-WithWinget($PackageId, $DisplayName) {
    if (-not (Has-Command "winget")) {
        throw "$DisplayName nao encontrado e winget tambem nao esta disponivel. Instale $DisplayName manualmente e execute novamente."
    }

    Write-Step "Instalando $DisplayName via winget"
    winget install --id $PackageId --silent --accept-package-agreements --accept-source-agreements
}

function Refresh-Path {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}

Set-Location $Root

Write-Step "Verificando Python"
if (-not (Has-Command "python")) {
    Install-WithWinget "Python.Python.3.11" "Python 3.11"
    Refresh-Path
}

if (-not (Has-Command "python")) {
    throw "Python ainda nao foi encontrado apos a instalacao. Feche e abra o terminal, ou instale Python manualmente."
}

Write-Step "Criando ambiente virtual Python"
if (-not (Test-Path $Python)) {
    python -m venv $Venv
}

Write-Step "Instalando dependencias Python"
& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $Root "requirements.txt")

Write-Step "Inicializando banco de dados"
& $Python -c "from backend.database.session import init_db; from backend.database.seed import seed_database; init_db(); seed_database(); print('Banco da API pronto')"
& $Python -c "from app.database.session import init_db; from app.database.seed import seed_database; init_db(); seed_database(); print('Banco desktop pronto')"

if (-not (Test-Path (Join-Path $Root "license.json"))) {
    Write-Step "Criando licenca de teste inicial"
    & $Python "scripts\generate_license.py" --customer "Cliente em teste" --type trial --days 14
}

Write-Step "Verificando Node.js"
if (-not (Has-Command "npm")) {
    Install-WithWinget "OpenJS.NodeJS.LTS" "Node.js LTS"
    Refresh-Path
}

if (Has-Command "npm") {
    Write-Step "Instalando dependencias Electron + React"
    Set-Location $Frontend
    npm install
    Set-Location $Root
} else {
    Write-Host "npm nao encontrado. O desktop Python e a API foram instalados, mas o frontend Electron precisa do Node.js LTS." -ForegroundColor Yellow
}

Write-Step "Validando instalacao"
& $Python -m pytest tests

Write-Host ""
Write-Host "Instalacao finalizada." -ForegroundColor Green
Write-Host "Use run_all.bat para abrir API + Electron, ou run_desktop.bat para abrir o desktop Python." -ForegroundColor Green
