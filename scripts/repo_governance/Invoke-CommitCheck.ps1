[CmdletBinding()]
param(
    [string]$RepoPath = (Get-Location).Path,
    [ValidateSet('preflight', 'docs', 'ci', 'doctor')]
    [string]$Task = 'preflight',
    [string]$Revision,
    [string]$Base = 'HEAD'
)
$ErrorActionPreference = 'Stop'
$context = & (Join-Path $PSScriptRoot 'Enter-AgentRepo.ps1') -RepoPath $RepoPath -PassThru
$root = (Resolve-Path -LiteralPath $RepoPath).Path
$checker = Join-Path $root '.github\oss_checks.py'
if (-not (Test-Path -LiteralPath $checker)) {
    throw "The checked-out branch predates OSS commit checks. Update it from main before using the hook: $root"
}
$toolPython = Join-Path (Split-Path -Parent $context.EnvironmentRoot) 'ArturSepp312\Scripts\python.exe'
$env:OSS_ACTIONLINT = Join-Path $env:LOCALAPPDATA "AgentWork\$env:COMPUTERNAME\OSSCommitSafety\tools\actionlint-1.7.12\actionlint.exe"
$arguments = @($checker, $Task, '--repo', $root, '--python', $context.Python, '--base', $Base)
if ($Revision) { $arguments += @('--revision', $Revision) }
$logDirectory = Join-Path $context.AgentWorkRoot 'checks\logs'
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
$logPath = Join-Path $logDirectory ((Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.log')
$ErrorActionPreference = 'Continue'
& $toolPython @arguments 2>&1 | ForEach-Object { $_.ToString() } | Tee-Object -FilePath $logPath
$code = $LASTEXITCODE
Write-Output "Check log: $logPath"
exit $code
