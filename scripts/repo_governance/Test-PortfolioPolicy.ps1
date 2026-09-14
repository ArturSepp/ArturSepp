[CmdletBinding()]
param(
    [string]$RegistryPath = (Join-Path $PSScriptRoot 'portfolio_registry.json'),
    [string]$RepositoriesRoot
)

$ErrorActionPreference = 'Stop'
$registryFile = (Resolve-Path -LiteralPath $RegistryPath).Path
$registry = Get-Content -LiteralPath $registryFile -Raw | ConvertFrom-Json
$registryDirectory = Split-Path -Parent $registryFile
if (-not $RepositoriesRoot) { $RepositoriesRoot = Join-Path $registryDirectory $registry.repositories_root }
$root = (Resolve-Path -LiteralPath $RepositoriesRoot).Path
$violations = [System.Collections.Generic.List[string]]::new()

function Test-RelativePathExcluded {
    param(
        [Parameter(Mandatory)]
        [string]$RelativePath,
        [Parameter(Mandatory)]
        [string[]]$Prefixes
    )

    $normalizedPath = $RelativePath.Replace('\', '/').Trim('/')
    foreach ($prefix in $Prefixes) {
        $normalizedPrefix = $prefix.Replace('\', '/').Trim('/')
        if (
            $normalizedPath -eq $normalizedPrefix -or
            $normalizedPath.StartsWith("$normalizedPrefix/", [StringComparison]::OrdinalIgnoreCase)
        ) {
            return $true
        }
    }
    return $false
}

if ($registry.schema_version -ne 1) { $violations.Add("unsupported registry schema $($registry.schema_version)") }
$names = @($registry.repositories | ForEach-Object { $_.name })
$directories = @($registry.repositories | ForEach-Object { $_.directory })
if (($names | Sort-Object -Unique).Count -ne $names.Count) { $violations.Add('duplicate repository name in portfolio registry') }
if (($directories | Sort-Object -Unique).Count -ne $directories.Count) { $violations.Add('duplicate repository directory in portfolio registry') }

$publicRegistryPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'public_registry.json'
$publicRegistry = Get-Content -LiteralPath $publicRegistryPath -Raw | ConvertFrom-Json
$publicDirectories = @($publicRegistry.packages | ForEach-Object { $_.local_dir })
$registeredPublicDirectories = @(
    $registry.repositories |
        Where-Object { $_.visibility -eq 'public-package' } |
        ForEach-Object { $_.directory }
)
if ((Compare-Object $publicDirectories $registeredPublicDirectories).Count -ne 0) {
    $violations.Add('public-package entries differ from scripts/public_registry.json')
}

foreach ($repository in $registry.repositories) {
    $repositoryRoot = Join-Path $root $repository.directory
    if (-not (Test-Path -LiteralPath $repositoryRoot -PathType Container)) {
        $violations.Add("$($repository.name): repository directory is missing")
        continue
    }
    if (-not (Test-Path -LiteralPath (Join-Path $repositoryRoot '.git'))) {
        $violations.Add("$($repository.name): .git is missing")
    }

    $agentsPath = Join-Path $repositoryRoot 'AGENTS.md'
    $claudePath = Join-Path $repositoryRoot 'CLAUDE.md'
    if (-not (Test-Path -LiteralPath $agentsPath -PathType Leaf)) {
        $violations.Add("$($repository.name): AGENTS.md is missing")
    } else {
        $agents = Get-Content -LiteralPath $agentsPath -Raw
        if ($agents -notmatch [regex]::Escape('agents/ROADMAP_<feature>.md')) {
            $violations.Add("$($repository.name): AGENTS.md lacks the agent-artifact rule")
        }
        if ($agents -notmatch [regex]::Escape('Invoke-Repo.ps1')) {
            $violations.Add("$($repository.name): AGENTS.md lacks the portfolio command entry point")
        }
    }
    if (-not (Test-Path -LiteralPath $claudePath -PathType Leaf)) {
        $violations.Add("$($repository.name): CLAUDE.md is missing")
    } elseif ((Get-Content -LiteralPath $claudePath -Raw) -notmatch 'AGENTS\.md') {
        $violations.Add("$($repository.name): CLAUDE.md does not point to AGENTS.md")
    }

    $artifactExclusions = @('agents', '.git')
    if ($null -ne $repository.artifact_policy) {
        $artifactExclusions += @($repository.artifact_policy.roadmap_exclusions)
    }
    $repositoryItems = @(Get-ChildItem -LiteralPath $repositoryRoot -Recurse -Force -ErrorAction SilentlyContinue)
    $misplacedRoadmaps = @(
        $repositoryItems |
            Where-Object { -not $_.PSIsContainer -and $_.Name -match '(?i)ROADMAP.*\.md$' } |
            Where-Object {
                $relativePath = [IO.Path]::GetRelativePath($repositoryRoot, $_.FullName)
                -not (Test-RelativePathExcluded -RelativePath $relativePath -Prefixes $artifactExclusions)
            }
    )
    foreach ($roadmap in $misplacedRoadmaps) {
        $relativePath = [IO.Path]::GetRelativePath($repositoryRoot, $roadmap.FullName).Replace('\', '/')
        $violations.Add("$($repository.name): roadmap outside repository-root agents/ '$relativePath'")
    }
    $misplacedOutputDirectories = @(
        $repositoryItems |
            Where-Object {
                $_.PSIsContainer -and (
                    $_.Name -match '(?i)^(Claude|Codex|Agent).*outputs?$' -or
                    [IO.Path]::GetRelativePath($repositoryRoot, $_.FullName) -match '(?i)^roadmaps?$'
                )
            } |
            Where-Object {
                $relativePath = [IO.Path]::GetRelativePath($repositoryRoot, $_.FullName)
                -not (Test-RelativePathExcluded -RelativePath $relativePath -Prefixes $artifactExclusions)
            }
    )
    foreach ($directory in $misplacedOutputDirectories) {
        $relativePath = [IO.Path]::GetRelativePath($repositoryRoot, $directory.FullName).Replace('\', '/')
        $violations.Add("$($repository.name): agent-output directory outside repository-root agents/ '$relativePath'")
    }

    $safeDirectory = ([IO.Path]::GetFullPath($repositoryRoot)).Replace('\', '/')
    $ignoreSource = & git -c "safe.directory=$safeDirectory" --no-optional-locks -C $repositoryRoot `
        check-ignore -v -- 'agents/.agent-artifact-probe' 2>$null
    if ($LASTEXITCODE -ne 0 -or $ignoreSource -notmatch '(?i)(^|[/\\])\.gitignore:') {
        $violations.Add("$($repository.name): repository-root agents/ is not ignored by .gitignore")
    }

    foreach ($localName in '.venv', 'venv', '.tox', '.nox') {
        if (Test-Path -LiteralPath (Join-Path $repositoryRoot $localName)) {
            $violations.Add("$($repository.name): forbidden local environment '$localName'")
        }
    }
    $environmentRoot = [IO.Path]::GetFullPath((Join-Path $registry.external_environment_root $repository.python_environment))
    if (-not (Test-Path -LiteralPath (Join-Path $environmentRoot 'Scripts\python.exe') -PathType Leaf)) {
        $violations.Add("$($repository.name): external interpreter is missing at $environmentRoot")
    }

    foreach ($phase in 'check', 'test', 'verify') {
        $definitionProperty = $repository.tasks.PSObject.Properties[$phase]
        if ($null -eq $definitionProperty) { continue }
        $definition = $definitionProperty.Value
        if ($definition.unsupported) { continue }
        foreach ($step in $definition.steps) {
            if ($step.kind -notin 'module', 'script', 'code', 'powershell_script') {
                $violations.Add("$($repository.name)/${phase}: unknown step kind '$($step.kind)'")
            }
            if ($step.kind -eq 'module' -and -not $step.module) { $violations.Add("$($repository.name)/${phase}: module step is incomplete") }
            if (($step.kind -in @('script', 'powershell_script')) -and -not (Test-Path -LiteralPath (Join-Path $repositoryRoot $step.path) -PathType Leaf)) {
                $violations.Add("$($repository.name)/${phase}: script '$($step.path)' is missing")
            }
            if ($step.kind -eq 'code' -and -not $step.code) { $violations.Add("$($repository.name)/${phase}: code step is incomplete") }
        }
    }
}

& (Join-Path $PSScriptRoot 'Update-AgentCoreManifest.ps1') -RepositoriesRoot $root
if ($LASTEXITCODE -ne 0) { $violations.Add('public agent-core manifest differs from repository contents') }

if ($violations.Count -gt 0) {
    Write-Error ("Portfolio policy violations:`n - " + ($violations -join "`n - "))
    exit 1
}
Write-Output "PASS: $($registry.repositories.Count) repositories conform to the shared local workflow and artifact policy."
