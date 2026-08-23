param(
    [Parameter(Mandatory = $true)]
    [string]$Customer,

    [ValidateSet("trial", "full")]
    [string]$Type = "trial",

    [int]$Days = 14
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

Set-Location $Root
& $Python "scripts\generate_license.py" --customer $Customer --type $Type --days $Days
