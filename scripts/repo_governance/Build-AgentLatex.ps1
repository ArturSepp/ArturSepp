[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$MainTex,
    [switch]$Publish,
    [switch]$ForcePublish,
    [string]$RegistryPath = (Join-Path $PSScriptRoot 'portfolio_registry.json')
)

$ErrorActionPreference = 'Stop'
$tex = Get-Item -LiteralPath $MainTex -ErrorAction Stop
if ($tex.Extension -ne '.tex') { throw "MainTex must be a .tex file: $($tex.FullName)" }
$context = & (Join-Path $PSScriptRoot 'Enter-AgentRepo.ps1') -RepoPath $tex.DirectoryName `
    -RegistryPath $RegistryPath -PassThru
$latexmk = Get-Command latexmk -ErrorAction SilentlyContinue
if (-not $latexmk) { throw 'latexmk is not available on PATH.' }

$pathBytes = [Text.Encoding]::UTF8.GetBytes($tex.FullName.ToLowerInvariant())
$pathHash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($pathBytes)).Substring(0, 12).ToLowerInvariant()
$outputDirectory = Join-Path $context.AgentWorkRoot "latex\$pathHash"
New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null

$originalLocation = (Get-Location).Path
try {
    Set-Location -LiteralPath $tex.DirectoryName
    & $latexmk.Source -pdf -interaction=nonstopmode -halt-on-error "-outdir=$outputDirectory" $tex.Name
    if ($LASTEXITCODE -ne 0) { throw "latexmk exited with code $LASTEXITCODE." }
} finally {
    Set-Location -LiteralPath $originalLocation
}

$pdf = Join-Path $outputDirectory ($tex.BaseName + '.pdf')
if (-not (Test-Path -LiteralPath $pdf -PathType Leaf)) { throw "Expected PDF was not produced: $pdf" }
if ($ForcePublish) { $Publish = $true }
if ($Publish) {
    $destination = [IO.Path]::ChangeExtension($tex.FullName, '.pdf')
    if ((Test-Path -LiteralPath $destination) -and -not $ForcePublish) {
        throw "Refusing to overwrite existing PDF without -ForcePublish: $destination"
    }
    Copy-Item -LiteralPath $pdf -Destination $destination -Force:$ForcePublish
    Write-Output $destination
} else {
    Write-Output $pdf
}
