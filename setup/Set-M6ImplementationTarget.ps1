# Set-M6ImplementationTarget.ps1 -- operator-only binding for M6-OD-011.
# Creates or updates 04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json.
# Executors can read this file but role policies deny writing 04-artifacts/state.

param(
    [ValidateSet('Existing', 'Greenfield')]
    [string]$Mode = 'Greenfield',
    [string]$TargetPath = '',
    [string]$CodeRoot = '.',
    [string]$Language = '',
    [string]$LanguageVersion = '',
    [string]$Framework = '',
    [string]$Database = '',
    [string]$Queue = '',
    [string]$TestCommand = '',
    [string]$RunCommand = '',
    [string]$DecisionEvidenceRef = '',
    [switch]$Lock,
    [string]$PackRoot = ''
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($PackRoot)) {
    $PackRoot = Split-Path $PSScriptRoot -Parent
}
$PackRoot = [System.IO.Path]::GetFullPath($PackRoot)
if ([string]::IsNullOrWhiteSpace($TargetPath) -and $Mode -eq 'Greenfield') {
    $TargetPath = Join-Path $PackRoot 'work-root\target-repo'
}
if ([string]::IsNullOrWhiteSpace($TargetPath)) {
    throw 'TargetPath is required for Existing mode.'
}
$TargetPath = [System.IO.Path]::GetFullPath($TargetPath)

if ($Mode -eq 'Greenfield') {
    New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null
} elseif (-not (Test-Path -LiteralPath $TargetPath -PathType Container)) {
    throw "Existing target repository not found: $TargetPath"
}

if ($Lock) {
    $missing = @()
    foreach ($pair in @(@('Language', $Language), @('TestCommand', $TestCommand), @('DecisionEvidenceRef', $DecisionEvidenceRef))) {
        if ([string]::IsNullOrWhiteSpace([string]$pair[1])) { $missing += $pair[0] }
    }
    if ($missing.Count -gt 0) {
        throw ('Cannot LOCK implementation target; missing: ' + ($missing -join ', '))
    }
}

$status = if ($Lock) { 'LOCKED' } else { 'DRAFT' }
$decisionStatus = if ($Lock) { 'DECIDED' } else { 'OPEN' }
$decidedAt = if ($Lock) { (Get-Date).ToUniversalTime().ToString('s') + 'Z' } else { '' }
$obj = [ordered]@{
    schema_version = 'GFD-M6-IMPLEMENTATION-TARGET-001'
    module = 'M6'
    status = $status
    workspace_mode = 'STAGED_ONLY'
    staging_root = '04-artifacts/impl'
    repository = [ordered]@{
        mode = $Mode.ToUpperInvariant()
        absolute_path = $TargetPath
        code_root = $CodeRoot
    }
    stack = [ordered]@{
        language = $Language
        language_version = $LanguageVersion
        framework = $Framework
        database = $Database
        queue = $Queue
        test_command = $TestCommand
        run_command = $RunCommand
    }
    owner_decision = [ordered]@{
        id = 'M6-OD-011'
        status = $decisionStatus
        decided_at = $decidedAt
        evidence_ref = $DecisionEvidenceRef
    }
    safety = [ordered]@{
        production_access = $false
        external_platform_calls = $false
        live_migrations = $false
    }
    note = 'Operator-owned manifest. Executors never edit this file; implementation remains staged until an owner-controlled integration step.'
}
$out = Join-Path $PackRoot '04-artifacts\state\IMPLEMENTATION_TARGET_LOCKED.json'
$json = $obj | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($out, $json + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
Write-Host ("Implementation target " + $status + ': ' + $out)
Write-Host ("Reference repository: " + $TargetPath)
if (-not $Lock) {
    Write-Host 'DRAFT only. Rerun with -Lock after M6-OD-011 is recorded in DECISION_REGISTER with owner evidence.'
}
