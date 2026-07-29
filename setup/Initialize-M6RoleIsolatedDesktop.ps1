# Initialize-M6RoleIsolatedDesktop.ps1
# One-time setup (and safe to re-run): creates, for every execution role
# folder, Windows junctions to the shared pack directories, a REAL-COPY
# fallback snapshot of 00-spec with a sha256 manifest, and (optionally)
# per-role Python venvs.
#
# Junctions store ABSOLUTE targets and BREAK when the pack is moved or copied:
# run Repair-M6RoleJunctions.ps1 after any move/copy.
#
# Usage:  powershell -NoProfile -ExecutionPolicy Bypass -File setup\Initialize-M6RoleIsolatedDesktop.ps1 [-SkipVenv] [-PythonExe C:\Path\To\python.exe]

param(
    [string]$PackRoot = "",
    [string]$PythonExe = "",
    [switch]$SkipVenv
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($PackRoot)) {
    $PackRoot = Split-Path $PSScriptRoot -Parent
}
$PackRoot = [System.IO.Path]::GetFullPath($PackRoot)

$roleFolders = @('00-analyst', '01-coder', '02-tester', '03-runner', '04-boundary', '06-security')
$sharedDirs = @('00-spec', '04-artifacts', 'registry', 'scripts', 'scripts-win')

function Remove-JunctionSafe([string]$path) {
    $item = Get-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
    if ($null -ne $item) {
        if ($item.LinkType -ne 'Junction') {
            throw "Refusing to remove non-junction path: $path"
        }
        # Directory.Delete on a junction removes only the reparse point, never
        # the target tree. Keep the operation in PowerShell/.NET end-to-end.
        [System.IO.Directory]::Delete($path, $false)
    } else {
        # A broken junction may not resolve through Test-Path/Get-Item. This
        # still targets the literal link path and is non-recursive.
        try { [System.IO.Directory]::Delete($path, $false) } catch { }
    }
}

function New-JunctionChecked([string]$link, [string]$target) {
    Remove-JunctionSafe $link
    if (Test-Path -LiteralPath $link) {
        throw "Cannot create junction: a real directory already exists at $link"
    }
    New-Item -ItemType Junction -Path $link -Target $target | Out-Null
    Write-Host ("  junction {0} -> {1}" -f $link, $target)
}

function Write-Snapshot([string]$roleBase) {
    $snapRoot = Join-Path $roleBase '_source_snapshot'
    $snapSpec = Join-Path $snapRoot '00-spec'
    if (Test-Path -LiteralPath $snapSpec) {
        Remove-Item -Recurse -Force -LiteralPath $snapSpec -Confirm:$false
    }
    New-Item -ItemType Directory -Force $snapSpec | Out-Null
    Copy-Item -Recurse -Force (Join-Path $PackRoot '00-spec\*') $snapSpec
    $manifest = @{}
    $sha = [System.Security.Cryptography.SHA256]::Create()
    Get-ChildItem -Recurse -File $snapSpec | ForEach-Object {
        $rel = $_.FullName.Substring($snapSpec.Length + 1).Replace('\', '/')
        $bytes = [System.IO.File]::ReadAllBytes($_.FullName)
        $hash = ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) -join ''
        $manifest[$rel] = $hash
    }
    $obj = New-Object PSObject
    $obj | Add-Member NoteProperty snapshot_of '00-spec'
    $obj | Add-Member NoteProperty created ((Get-Date).ToString('s'))
    $obj | Add-Member NoteProperty files $manifest
    $json = $obj | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText((Join-Path $snapRoot 'SOURCE_SNAPSHOT_MANIFEST.json'), $json, (New-Object System.Text.UTF8Encoding($false)))
    Write-Host ("  snapshot {0} ({1} files)" -f $snapSpec, $manifest.Count)
}

Write-Host ("Pack root: " + $PackRoot)
foreach ($rf in $roleFolders) {
    $base = Join-Path $PackRoot $rf
    if (-not (Test-Path -LiteralPath $base)) { throw "Role folder missing: $base (run scripts/gen_roles.py first)" }
    Write-Host ("Role: " + $rf)
    foreach ($sd in $sharedDirs) {
        New-JunctionChecked (Join-Path $base $sd) (Join-Path $PackRoot $sd)
    }
    Write-Snapshot $base
}
if (-not $SkipVenv) {
    & (Join-Path $PSScriptRoot 'New-M6RoleVenvs.ps1') -PackRoot $PackRoot -PythonExe $PythonExe
}
Write-Host "NOTE: 05-judge gets NO venv, NO CLAUDE.md, NO hooks by design (output-only)."
Write-Host "Done. If you ever move/copy this pack, run setup\Repair-M6RoleJunctions.ps1."
