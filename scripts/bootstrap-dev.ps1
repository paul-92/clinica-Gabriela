param(
    [Parameter(Mandatory)][string]$DevRoot,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'dev-environment.ps1')
$dev = Resolve-DevEnvironment -DevRoot $DevRoot
if (-not (Get-Command py -ErrorAction SilentlyContinue) -and -not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'Python ausente.' }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'Node.js ausente.' }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'npm ausente.' }
$pythonCommand = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'py' }
$pythonArgs = @()
$pythonVersionArgs = @()
if ($pythonCommand -eq 'py') { $pythonVersionArgs = @('-3.12') }
$version = (& $pythonCommand @pythonVersionArgs --version) -join ''
if ($LASTEXITCODE -ne 0) { throw 'Python indisponivel.' }
if ($version -match '^Python (\d+)\.(\d+)\.') {
    if ([int]$Matches[1] -lt 3 -or ([int]$Matches[1] -eq 3 -and [int]$Matches[2] -lt 10)) { throw 'Codigo Python requer sintaxe 3.10 ou superior.' }
} else { throw 'Versao Python nao reconhecida.' }
if ($version -ne 'Python 3.12.10') { Write-Warning "Python $version difere da baseline validada 3.12.10; suporte nao comprovado." }
$pythonArgs = $pythonVersionArgs
$nodeVersion = (& node --version).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Node indisponivel.' }
if ($nodeVersion -notmatch '^v(\d+)\.' -or [int]$Matches[1] -lt 18) { throw 'Vite 5 requer Node 18 ou superior.' }
if ($nodeVersion -ne 'v24.19.0') { Write-Warning "Node $nodeVersion difere da baseline validada v24.19.0; suporte nao comprovado." }
$lock = Join-Path $dev.Repo 'requirements-dev.lock'
if (-not (Test-Path -LiteralPath $lock -PathType Leaf)) { throw 'Lock Python ausente.' }
if ($DryRun) { Write-Host "GUARDS_PASS; DEV_ROOT=$($dev.Root); DATABASE=$($dev.Database); nenhuma alteracao feita"; exit 0 }
if (Test-Path -LiteralPath $dev.Workspace) { throw 'Workspace DEV ja existe; use DevRoot novo.' }
if (-not (Test-Path -LiteralPath $dev.Root)) { New-Item -ItemType Directory -Path $dev.Root -Force | Out-Null }
if (-not (Test-Path -LiteralPath $dev.Marker)) { Set-Content -LiteralPath $dev.Marker -Value 'CLINICA_GABRIELA_SYNTHETIC_DEV_V1' -Encoding ascii }
New-Item -ItemType Directory -Path $dev.DataDir, (Join-Path $dev.Root 'temp') -Force | Out-Null
Set-DevProcessEnvironment -Dev $dev
& $pythonCommand @pythonArgs (Join-Path $dev.Repo 'scripts\copy_dev_workspace.py') $dev.Workspace
if ($LASTEXITCODE -ne 0) { throw 'Copia DEV falhou.' }
$venvPython = Join-Path $dev.Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) { & $pythonCommand @pythonArgs -m venv (Join-Path $dev.Root '.venv'); if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar venv.' } }
& $venvPython -m pip install -r (Join-Path $dev.Workspace 'requirements.txt') -c (Join-Path $dev.Workspace 'requirements-dev.lock')
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependencias Python.' }
& $venvPython -m pip check
if ($LASTEXITCODE -ne 0) { throw 'pip check falhou.' }
Push-Location (Join-Path $dev.Workspace 'frontend')
try { & npm ci; if ($LASTEXITCODE -ne 0) { throw 'npm ci falhou.' } } finally { Pop-Location }
Push-Location $dev.Workspace
try {
    & $venvPython -m scripts.bootstrap_dev_database
    if ($LASTEXITCODE -ne 0) { throw 'Bootstrap do banco DEV falhou.' }
} finally { Pop-Location }
Write-Host "BOOTSTRAP_DEV_READY: $($dev.Database)"
