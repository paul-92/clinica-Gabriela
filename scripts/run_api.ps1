$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

Set-Location $Root
& $Python -m backend.supervisor run
if ($LASTEXITCODE -ne 0) {
    throw "O backend encerrou com falha."
}
