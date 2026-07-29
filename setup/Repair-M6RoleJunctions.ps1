# Repair-M6RoleJunctions.ps1
# Junctions store ABSOLUTE targets and break when the pack is moved/copied.
# This script removes every role junction (broken or not) and rebuilds it
# against the CURRENT pack root, then refreshes each role's _source_snapshot.
#
# Usage:  powershell -NoProfile -ExecutionPolicy Bypass -File setup\Repair-M6RoleJunctions.ps1

param([string]$PackRoot = "")

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($PackRoot)) {
    $PackRoot = Split-Path $PSScriptRoot -Parent
}
$PackRoot = [System.IO.Path]::GetFullPath($PackRoot)

# Re-running Initialize with -SkipVenv is exactly the repair semantics:
# junctions are removed and recreated against the current root and snapshots
# are refreshed; venvs are left untouched.
& (Join-Path $PSScriptRoot 'Initialize-M6RoleIsolatedDesktop.ps1') -PackRoot $PackRoot -SkipVenv
Write-Host "Junction repair complete."
