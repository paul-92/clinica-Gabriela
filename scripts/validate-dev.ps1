param(
    [Parameter(Mandatory)][string]$DevRoot,
    [switch]$GuardsOnly
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'dev-environment.ps1')
$dev = Resolve-DevEnvironment -DevRoot $DevRoot -RequireMarker
if ((Get-Content -LiteralPath $dev.Marker -Raw).Trim() -ne 'CLINICA_GABRIELA_SYNTHETIC_DEV_V1') { throw 'Marcador DEV invalido.' }
if (-not (Test-Path -LiteralPath $dev.Database -PathType Leaf)) { throw 'Banco DEV ausente.' }
$venvPython = Join-Path $dev.Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) { throw 'Venv ausente.' }
if (-not (Test-Path -LiteralPath (Join-Path $dev.Workspace 'frontend\node_modules') -PathType Container)) { throw 'node_modules ausente; execute bootstrap.' }
Set-DevProcessEnvironment -Dev $dev
Push-Location $dev.Workspace
try {
    & $venvPython -c 'from scripts.bootstrap_dev_database import verify_dev_path; verify_dev_path()'
    if ($LASTEXITCODE -ne 0) { throw 'Resolucao do banco DEV invalida.' }
    if ($GuardsOnly) { Write-Host 'GUARDS_PASS'; exit 0 }
    & $venvPython -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'pip check falhou.' }
    & $venvPython -m compileall -q app backend scripts
    if ($LASTEXITCODE -ne 0) { throw 'compileall falhou.' }
    $env:CLINICA_RUNTIME_ROOT = Join-Path $dev.Root 'test-runtime'
    $env:CLINICA_OPERATIONAL_POINTER = Join-Path $env:CLINICA_RUNTIME_ROOT 'operational-pointer.json'
    & $venvPython -m pytest tests -o "cache_dir=$($dev.Root)\pytest-cache" --basetemp (Join-Path $dev.Root 'pytest-temp')
    if ($LASTEXITCODE -ne 0) { throw 'pytest falhou.' }
    Push-Location (Join-Path $dev.Workspace 'frontend')
    try {
        & npm test; if ($LASTEXITCODE -ne 0) { throw 'npm test falhou.' }
        & npm run build; if ($LASTEXITCODE -ne 0) { throw 'npm run build falhou.' }
    } finally { Pop-Location }
} finally { Pop-Location }
Write-Host 'VALIDATE_DEV_PASS'
