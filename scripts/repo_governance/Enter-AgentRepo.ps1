[CmdletBinding()]
param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$RegistryPath = (Join-Path $PSScriptRoot 'portfolio_registry.json'),
    [string]$RepositoriesRoot,
    [switch]$PassThru
)

$ErrorActionPreference = 'Stop'
$registryFile = (Resolve-Path -LiteralPath $RegistryPath).Path
$registry = Get-Content -LiteralPath $registryFile -Raw | ConvertFrom-Json
$registryDirectory = Split-Path -Parent $registryFile

if (-not $RepositoriesRoot) {
    $RepositoriesRoot = Join-Path $registryDirectory $registry.repositories_root
}
$repositoriesRootPath = (Resolve-Path -LiteralPath $RepositoriesRoot).Path
$candidatePath = (Resolve-Path -LiteralPath $RepoPath).Path.TrimEnd('\')

$matches = @(
    foreach ($repository in $registry.repositories) {
        $root = (Resolve-Path -LiteralPath (Join-Path $repositoriesRootPath $repository.directory)).Path.TrimEnd('\')
        if ($candidatePath -eq $root -or $candidatePath.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) {
            [pscustomobject]@{ Entry = $repository; Root = $root }
        }
    }
)
if ($matches.Count -ne 1) {
    throw "'$candidatePath' does not resolve to exactly one repository in '$registryFile'."
}

$repository = $matches[0].Entry
$repositoryRoot = $matches[0].Root
$pythonRoot = if ($env:PORTFOLIO_PYTHON_ROOT) { $env:PORTFOLIO_PYTHON_ROOT } else { $registry.external_environment_root }
$environmentRoot = [IO.Path]::GetFullPath((Join-Path $pythonRoot $repository.python_environment))
$python = Join-Path $environmentRoot 'Scripts\python.exe'

$oneDriveRoot = [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE 'OneDrive')).TrimEnd('\')
if ($environmentRoot -eq $oneDriveRoot -or $environmentRoot.StartsWith($oneDriveRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing Python environment below OneDrive: $environmentRoot"
}
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "External interpreter is missing: $python"
}

$localEnvironments = @(
    foreach ($name in '.venv', 'venv', '.tox', '.nox') {
        $path = Join-Path $repositoryRoot $name
        if (Test-Path -LiteralPath $path) { $path }
    }
)
if ($localEnvironments.Count -gt 0) {
    throw "Repository-local environments are forbidden: $($localEnvironments -join ', ')"
}

$machine = if ($env:COMPUTERNAME) { $env:COMPUTERNAME } else { 'unknown-machine' }
$agentWorkRoot = Join-Path $env:LOCALAPPDATA "AgentWork\$machine\$($repository.name)"
$paths = [ordered]@{
    Root = $agentWorkRoot
    Temp = Join-Path $agentWorkRoot 'tmp'
    PythonCache = Join-Path $agentWorkRoot 'cache\python'
    NumbaCache = Join-Path $agentWorkRoot 'cache\numba'
    PipCache = Join-Path $agentWorkRoot 'cache\pip'
    UvCache = Join-Path $agentWorkRoot 'cache\uv'
    PytestCache = Join-Path $agentWorkRoot 'cache\pytest'
    PytestDebugTemp = Join-Path $agentWorkRoot 'tmp\pytest'
    RuffCache = Join-Path $agentWorkRoot 'cache\ruff'
    MypyCache = Join-Path $agentWorkRoot 'cache\mypy'
    MatplotlibCache = Join-Path $agentWorkRoot 'cache\matplotlib'
    Coverage = Join-Path $agentWorkRoot 'coverage\.coverage'
    Analyses = Join-Path $agentWorkRoot 'analyses'
    Builds = Join-Path $agentWorkRoot 'builds'
    Outputs = Join-Path $agentWorkRoot 'outputs'
    Runs = Join-Path $agentWorkRoot 'runs'
}
foreach ($path in $paths.Values) {
    $directory = if ($path -eq $paths.Coverage) { Split-Path -Parent $path } else { $path }
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
}

$env:AGENT_LOCAL_ROOT = $paths.Root
$env:UV_PROJECT_ENVIRONMENT = $environmentRoot
$env:PYTHONPYCACHEPREFIX = $paths.PythonCache
$env:NUMBA_CACHE_DIR = $paths.NumbaCache
$env:PIP_CACHE_DIR = $paths.PipCache
$env:UV_CACHE_DIR = $paths.UvCache
$env:RUFF_CACHE_DIR = $paths.RuffCache
$env:MYPY_CACHE_DIR = $paths.MypyCache
$env:MPLCONFIGDIR = $paths.MatplotlibCache
$env:PYTEST_DEBUG_TEMPROOT = $paths.PytestDebugTemp
$env:COVERAGE_FILE = $paths.Coverage
$env:TEMP = $paths.Temp
$env:TMP = $paths.Temp
$env:MPLBACKEND = 'Agg'
$env:PYTHONIOENCODING = 'utf-8'

$context = [pscustomobject]@{
    Name = $repository.name
    Repository = $repository
    RepositoryRoot = $repositoryRoot
    RepositoriesRoot = $repositoriesRootPath
    Python = $python
    EnvironmentRoot = $environmentRoot
    AgentWorkRoot = $paths.Root
    PytestCache = $paths.PytestCache
}

if ($PassThru) {
    $context
} else {
    Write-Output "Configured $($repository.name): Python=$python; generated state=$($paths.Root)"
}
