# Helper compartilhado. Nao importa backend nem abre banco.
function Resolve-DevEnvironment {
    param([Parameter(Mandatory)][string]$DevRoot, [switch]$RequireMarker)
    $repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\', '/')
    $root = [IO.Path]::GetFullPath($DevRoot).TrimEnd('\', '/')
    if (-not [IO.Path]::IsPathRooted($DevRoot)) { throw 'DevRoot deve ser um caminho absoluto.' }
    $comparison = [StringComparison]::OrdinalIgnoreCase
    function Overlaps([string]$a, [string]$b) {
        return $a.Equals($b, $comparison) -or
            $a.StartsWith($b + [IO.Path]::DirectorySeparatorChar, $comparison) -or
            $b.StartsWith($a + [IO.Path]::DirectorySeparatorChar, $comparison)
    }
    if (Overlaps $root $repo) { throw 'DevRoot nao pode conter o repositorio nem estar dentro dele.' }
    $local = [Environment]::GetEnvironmentVariable('LOCALAPPDATA')
    if (-not $local) { throw 'LOCALAPPDATA ausente; nao e possivel proteger o runtime operacional.' }
    $operational = [IO.Path]::GetFullPath((Join-Path $local 'ClinicaGabriela\runtime')).TrimEnd('\', '/')
    if (Overlaps $root $operational) { throw 'DevRoot coincide ou se sobrepoe ao runtime operacional.' }
    foreach ($name in @('CLINICA_RUNTIME_ROOT', 'CLINICA_OPERATIONAL_POINTER', 'CLINICA_RUNTIME_MANIFEST_DIR', 'CLINICA_RUNTIME_CODE_ROOT', 'CLINICA_MAINTENANCE_LOCK', 'BACKEND_DATABASE_PATH', 'BACKEND_DATA_DIR')) {
        $value = [Environment]::GetEnvironmentVariable($name)
        if ($value) { throw "Variavel $name ja definida; remova-a antes de usar os scripts DEV." }
    }
    $cursor = $root
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Caminho com junction/symlink nao permitido: $cursor"
            }
        }
        $parent = Split-Path -Parent $cursor
        if (-not $parent -or $parent -eq $cursor) { break }
        $cursor = $parent
    }
    $marker = Join-Path $root '.clinica-dev-root'
    if (Test-Path -LiteralPath $marker) {
        $markerItem = Get-Item -LiteralPath $marker -Force
        if (($markerItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Marcador DEV nao pode ser symlink.' }
        if ($markerItem.PSIsContainer) { throw 'Marcador DEV deve ser arquivo.' }
        if (-not $markerItem.PSIsContainer -and (Get-Content -LiteralPath $marker -Raw).Trim() -ne 'CLINICA_GABRIELA_SYNTHETIC_DEV_V1') {
            throw 'Marcador DEV invalido.'
        }
    }
    if ($RequireMarker -and -not (Test-Path -LiteralPath $marker -PathType Leaf)) {
        throw 'Marcador DEV ausente. Execute bootstrap-dev.ps1 primeiro.'
    }
    if (Test-Path -LiteralPath $root -PathType Container) {
        $entries = @(Get-ChildItem -LiteralPath $root -Force)
        if ($entries.Count -gt 0 -and -not (Test-Path -LiteralPath $marker -PathType Leaf)) {
            throw 'DevRoot nao esta vazio e nao possui marcador DEV.'
        }
    }
    $database = Join-Path $root 'backend\clinica_dev.db'
    $workspace = Join-Path $root 'workspace'
    foreach ($candidate in @((Split-Path $database), $database, $workspace)) {
        if (Test-Path -LiteralPath $candidate) {
            $item = Get-Item -LiteralPath $candidate -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Diretorio ou banco DEV nao pode ser symlink.' }
        }
    }
    $pointer = Join-Path $root 'operational-pointer.json'
    if (Test-Path -LiteralPath $pointer) { throw 'Pointer presente em DevRoot; recusando ambiente ambiguo.' }
    return [pscustomobject]@{ Repo=$repo; Root=$root; Workspace=$workspace; Marker=$marker; Database=$database; DataDir=(Split-Path $database); Pointer=$pointer }
}

function Set-DevProcessEnvironment {
    param([Parameter(Mandatory)]$Dev)
    $env:BACKEND_DATABASE_PATH = $Dev.Database
    $env:BACKEND_DATA_DIR = $Dev.DataDir
    $env:CLINICA_RUNTIME_ROOT = $Dev.Root
    $env:CLINICA_OPERATIONAL_POINTER = $Dev.Pointer
    $env:CLINICA_MAINTENANCE_LOCK = Join-Path $Dev.Root 'maintenance.lock'
    $env:BACKEND_HOST = '127.0.0.1'
    $env:BACKEND_PORT = '8000'
    $env:BACKEND_RELOAD = 'false'
    $env:BACKEND_VERIFY_READ_ONLY = 'false'
    $env:TEMP = Join-Path $Dev.Root 'temp'
    $env:TMP = $env:TEMP
}
