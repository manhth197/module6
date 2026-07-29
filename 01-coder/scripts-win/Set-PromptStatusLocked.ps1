# Set-PromptStatusLocked.ps1 -- operator tool for non-success transitions.
# ValidateSet EXCLUDES PASS and SIGNED on purpose: success states exist ONLY
# via Mark-PromptPassLocked.ps1 (which runs the machine gate first).
# SKIPPED requires -Note 'SKIP_APPROVED:<owner-decision-ref>' and is REFUSED
# on JUDGE_GATE rows: SKIPPED counts as passed for dependencies, so an
# ungated judge skip would be a gate bypass.
# Usage: scripts-win\Set-PromptStatusLocked.ps1 -PromptId M6-P0000 -Status BLOCKED -Note "..."

param(
    [Parameter(Mandatory = $true)][string]$PromptId,
    [Parameter(Mandatory = $true)][ValidateSet('TODO','RUNNING','BLOCKED','FAIL','SKIPPED')][string]$Status,
    [string]$Note = ""
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot "_M6RunnerLib.ps1")

$rows = Read-M6Csv $script:LedgerPath
$row = Get-M6Row $rows $PromptId

if ($Status -eq 'SKIPPED') {
    if ($Note -notmatch '^SKIP_APPROVED:\S+') {
        throw "SKIPPED requires -Note 'SKIP_APPROVED:<owner-decision-ref>' (e.g. SKIP_APPROVED:M6-OD-010)."
    }
    if ([string]$row.GateLevel -eq 'JUDGE_GATE') {
        throw ("REFUSED: " + $PromptId + " is a JUDGE_GATE row. Judge gates can never be skipped (gate bypass).")
    }
}

foreach ($r in $rows) {
    if ($r.PromptId -eq $PromptId) {
        $r.Status = $Status
        if ($Note.Length -gt 0) { $r.Note = $Note }
        $r.UpdatedAt = (Get-Date).ToString('s')
    }
}
Write-M6Ledger $rows
Write-Host ("SET " + $PromptId + " => " + $Status + (" (" + $Note + ")"))
exit 0
