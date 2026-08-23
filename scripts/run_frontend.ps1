$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Frontend = Join-Path $Root "frontend"

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm nao encontrado. Instale Node.js LTS e tente novamente."
}

Set-Location $Frontend
if (-not (Test-Path "node_modules")) {
    npm install
}
npm run dev
