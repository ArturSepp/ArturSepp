[CmdletBinding()]
param(
    [ValidateSet('check', 'test', 'verify')]
    [string]$Task = 'verify',
    [string]$Repo,
    [switch]$All,
    [switch]$DryRun,
    [string]$RegistryPath = (Join-Path $PSScriptRoot 'portfolio_registry.json'),
    [string]$RepositoriesRoot
)

$ErrorActionPreference = 'Stop'
if ($All -and $Repo) {
    throw 'Use either -All or -Repo, not both.'
}

$registryFile = (Resolve-Path -LiteralPath $RegistryPath).Path
$registry = Get-Content -LiteralPath $registryFile -Raw | ConvertFrom-Json
$registryDirectory = Split-Path -Parent $registryFile
if (-not $RepositoriesRoot) {
    $RepositoriesRoot = Join-Path $registryDirectory $registry.repositories_root
}
$repositoriesRootPath = (Resolve-Path -LiteralPath $RepositoriesRoot).Path

if ($All) {
    $selected = @($registry.repositories)
} elseif ($Repo) {
    $selected = @($registry.repositories | Where-Object { $_.name -ieq $Repo -or $_.directory -ieq $Repo })
    if ($selected.Count -ne 1) { throw "Unknown or ambiguous repository '$Repo'." }
} else {
    $current = (Resolve-Path -LiteralPath (Get-Location).Path).Path.TrimEnd('\')
    $selected = @(
        foreach ($repository in $registry.repositories) {
            $root = (Resolve-Path -LiteralPath (Join-Path $repositoriesRootPath $repository.directory)).Path.TrimEnd('\')
            if ($current -eq $root -or $current.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) {
                $repository
            }
        }
    )
    if ($selected.Count -ne 1) { throw 'Run inside a registered repository or pass -Repo/-All.' }
}

$failures = [System.Collections.Generic.List[string]]::new()
$skips = [System.Collections.Generic.List[string]]::new()
$originalLocation = (Get-Location).Path

foreach ($repository in $selected) {
    $root = (Resolve-Path -LiteralPath (Join-Path $repositoriesRootPath $repository.directory)).Path
    Write-Output "=== $($repository.name): $Task ==="
    try {
        $context = & (Join-Path $PSScriptRoot 'Enter-AgentRepo.ps1') -RepoPath $root `
            -RegistryPath $registryFile -RepositoriesRoot $repositoriesRootPath -PassThru
        Set-Location -LiteralPath $root
        $phases = if ($Task -eq 'verify') { @('check', 'test', 'verify') } else { @($Task) }

        foreach ($phase in $phases) {
            $definitionProperty = $repository.tasks.PSObject.Properties[$phase]
            if ($null -eq $definitionProperty) { continue }
            $definition = $definitionProperty.Value
            if ($definition.unsupported) {
                $message = "$($repository.name)/${phase}: $($definition.unsupported)"
                $skips.Add($message)
                Write-Warning "SKIP: $message"
                continue
            }

            foreach ($step in $definition.steps) {
                $arguments = [System.Collections.Generic.List[string]]::new()
                $program = $context.Python
                switch ($step.kind) {
                    'module' {
                        $arguments.Add('-m')
                        $arguments.Add([string]$step.module)
                    }
                    'script' { $arguments.Add([string]$step.path) }
                    'code' {
                        $arguments.Add('-c')
                        $arguments.Add([string]$step.code)
                    }
                    'powershell_script' { $program = Join-Path $root $step.path }
                    default { throw "Unsupported step kind '$($step.kind)' in $($repository.name)/$phase." }
                }
                foreach ($argument in @($step.arguments)) { $arguments.Add([string]$argument) }
                if ($step.kind -eq 'module' -and $step.module -eq 'pytest') {
                    $arguments.Add('-o')
                    $arguments.Add("cache_dir=$($context.PytestCache)")
                }

                $display = @($program) + @($arguments) | ForEach-Object {
                    if ($_ -match '\s') { "'$_'" } else { $_ }
                }
                Write-Output "[$phase] $($step.name): $($display -join ' ')"
                if (-not $DryRun) {
                    & $program @arguments
                    if ($LASTEXITCODE -ne 0) {
                        throw "$($step.name) exited with code $LASTEXITCODE."
                    }
                }
            }
        }
    } catch {
        $failures.Add("$($repository.name): $($_.Exception.Message)")
        Write-Error -ErrorAction Continue $failures[$failures.Count - 1]
    } finally {
        Set-Location -LiteralPath $originalLocation
    }
}

Write-Output "Portfolio task summary: $($selected.Count) repository/repositories; $($failures.Count) failures; $($skips.Count) unsupported phases."
if ($skips.Count -gt 0) {
    $skips | ForEach-Object { Write-Output "  SKIP $_" }
}
if ($failures.Count -gt 0) {
    exit 1
}
