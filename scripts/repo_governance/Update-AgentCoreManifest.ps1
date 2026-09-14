[CmdletBinding()]
param(
    [switch]$Write,
    [string]$RepositoriesRoot,
    [string]$PublicRegistryPath = (Join-Path (Split-Path -Parent $PSScriptRoot) 'public_registry.json'),
    [string]$ManifestPath = (Join-Path (Split-Path -Parent $PSScriptRoot) 'agent_core_manifest.json')
)

$ErrorActionPreference = 'Stop'
$publicRegistryFile = (Resolve-Path -LiteralPath $PublicRegistryPath).Path
$publicRegistry = Get-Content -LiteralPath $publicRegistryFile -Raw | ConvertFrom-Json
if (-not $RepositoriesRoot) {
    $RepositoriesRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
}
$repositoriesRootPath = (Resolve-Path -LiteralPath $RepositoriesRoot).Path
$digests = [ordered]@{}
$syncDates = [System.Collections.Generic.HashSet[string]]::new()

foreach ($package in $publicRegistry.packages) {
    $agentsPath = Join-Path (Join-Path $repositoriesRootPath $package.local_dir) 'AGENTS.md'
    $source = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $agentsPath).Path)
    $matches = [regex]::Matches(
        $source,
        '<!-- ===== SHARED AGENT CORE .*?<!-- ===== SHARED AGENT CORE — end ===== -->',
        [Text.RegularExpressions.RegexOptions]::Singleline
    )
    if ($matches.Count -ne 1) { throw "$($package.local_dir): expected exactly one shared agent-core block." }
    $stamp = [regex]::Match($matches[0].Value, 'Last synced (\d{4}-\d{2}-\d{2}), agent core v([^ ]+) -->')
    if (-not $stamp.Success) { throw "$($package.local_dir): missing generated block sync stamp." }
    if ($stamp.Groups[2].Value -ne [string]$publicRegistry.agent_core_version) {
        throw "$($package.local_dir): block version $($stamp.Groups[2].Value) differs from registry version $($publicRegistry.agent_core_version)."
    }
    [void]$syncDates.Add($stamp.Groups[1].Value)
    $bytes = [Text.Encoding]::UTF8.GetBytes($matches[0].Value)
    $digests[$package.local_dir] = [Convert]::ToHexString(
        [Security.Cryptography.SHA256]::HashData($bytes)
    ).ToLowerInvariant()
}
if ($syncDates.Count -ne 1) { throw "Public agent blocks do not share one sync date: $($syncDates -join ', ')" }

$generated = [ordered]@{
    version = [string]$publicRegistry.agent_core_version
    date = @($syncDates)[0]
    sha256 = $digests
}
$json = $generated | ConvertTo-Json -Depth 5

if ($Write) {
    [IO.File]::WriteAllText([IO.Path]::GetFullPath($ManifestPath), $json + "`n", [Text.UTF8Encoding]::new($false))
    Write-Output "Updated $ManifestPath"
    exit 0
}

$existing = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$errors = [System.Collections.Generic.List[string]]::new()
if ($existing.version -ne $generated.version) { $errors.Add("version: expected $($generated.version), found $($existing.version)") }
if ($existing.date -ne $generated.date) { $errors.Add("date: expected $($generated.date), found $($existing.date)") }
foreach ($name in $digests.Keys) {
    $actual = $existing.sha256.PSObject.Properties[$name].Value
    if ($actual -ne $digests[$name]) { $errors.Add("${name}: digest differs") }
}
if ($existing.sha256.PSObject.Properties.Name.Count -ne $digests.Count) {
    $errors.Add('manifest repository set differs from the public registry')
}
if ($errors.Count -gt 0) {
    Write-Error ("Agent-core manifest drift:`n - " + ($errors -join "`n - "))
    exit 1
}
Write-Output "PASS: agent-core manifest v$($generated.version) matches $($digests.Count) public repositories."
