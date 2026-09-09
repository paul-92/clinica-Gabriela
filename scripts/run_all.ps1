$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$FrontendScript = Join-Path $PSScriptRoot "run_frontend.ps1"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

Set-Location $Root

& $Python -m backend.supervisor run-with -- powershell -ExecutionPolicy Bypass -File $FrontendScript
if ($LASTEXITCODE -ne 0) {
    throw "O fluxo backend/frontend encerrou com falha."
}

Write-Host "Backend e frontend encerrados normalmente." -ForegroundColor Green
