[CmdletBinding()]
param([string]$Repo, [switch]$All, [switch]$Uninstall, [switch]$SetupTools)
$ErrorActionPreference = 'Stop'
$registry = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'portfolio_registry.json') -Raw | ConvertFrom-Json
$stackRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $registry.repositories_root))
if ($SetupTools) {
    . (Join-Path $PSScriptRoot 'Enter-AgentRepo.ps1') -RepoPath (Join-Path $stackRoot 'ArturSepp')
    & 'C:\Python\ArturSepp312\Scripts\python.exe' -m pip install -r (Join-Path $PSScriptRoot 'check-requirements.txt')
    if ($LASTEXITCODE) { throw 'Shared check tooling installation failed.' }
    $toolRoot = Join-Path $env:LOCALAPPDATA "AgentWork\$env:COMPUTERNAME\OSSCommitSafety\tools"
    New-Item -ItemType Directory -Force -Path $toolRoot | Out-Null
    $archive = Join-Path $toolRoot 'actionlint-1.7.12-windows.zip'
    Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/rhysd/actionlint/releases/download/v1.7.12/actionlint_1.7.12_windows_amd64.zip' -OutFile $archive
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne '6e7241b51e6817ea6a047693d8e6fed13b31819c9a0dd6c5a726e1592d22f6e9') { throw 'Actionlint checksum mismatch.' }
    Expand-Archive -LiteralPath $archive -DestinationPath (Join-Path $toolRoot 'actionlint-1.7.12') -Force
}
$selected = @($registry.repositories | Where-Object {
    $_.visibility -eq 'public-package' -and ($All -or $_.name -eq $Repo -or $_.directory -eq $Repo)
})
if ($selected.Count -eq 0) { throw 'Select a public package with -Repo or -All.' }
foreach ($entry in $selected) {
    $root = Join-Path $stackRoot $entry.directory
    $current = (& git -C $root config --local --get core.hooksPath)
    if ($Uninstall) {
        if ($current -eq '.githooks') { & git -C $root config --local --unset core.hooksPath }
        Write-Output "$($entry.name): managed hook disabled; tracked hook files retained."
        continue
    }
    $effective = (& git -C $root config --get core.hooksPath)
    if ($effective -and $effective -ne '.githooks') { throw "$($entry.name) has existing hooksPath '$effective'; preserve and integrate it explicitly." }
    $hookDir = & git -C $root rev-parse --git-path hooks
    if (-not [IO.Path]::IsPathRooted($hookDir)) { $hookDir = Join-Path $root $hookDir }
    $existing = @(Get-ChildItem -LiteralPath $hookDir -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike '*.sample' })
    if ($effective -ne ".githooks" -and $existing.Count) { throw "$($entry.name) has existing hooks; preserve and integrate them explicitly." }
    if (-not (Test-Path -LiteralPath (Join-Path $root '.githooks\pre-commit'))) { throw "Merge the reviewed tooling before installing hooks in $root" }
    & git -C $root config --local core.hooksPath .githooks
    if ($LASTEXITCODE) { throw "Hook installation failed: $root" }
    Write-Output "$($entry.name): automatic staged checks installed."
}
