# Mark-PromptPassLocked.ps1 -- the ONLY way a prompt becomes PASS/SIGNED.
# CALLS Check-PromptGateLocked.ps1 first; throws if the gate fails; then marks
# PASS (or SIGNED for judge rows) in the ledger.
# Usage: scripts-win\Mark-PromptPassLocked.ps1 -PromptId M6-P0000

param(
    [Parameter(Mandatory = $true)][string]$PromptId
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot "_M6RunnerLib.ps1")

# HARD RULE: the gate check is not optional and not skippable.
& (Join-Path $PSScriptRoot "Check-PromptGateLocked.ps1") -PromptId $PromptId
if ($LASTEXITCODE -ne 0) {
    throw ("Gate check FAILED for " + $PromptId + " -- refusing to mark. Fix the evidence and re-run.")
}

$rows = Read-M6Csv $script:LedgerPath
$row = Get-M6Row $rows $PromptId
$target = "PASS"
if ([string]$row.RequiresJudge -eq "true") { $target = "SIGNED" }

foreach ($r in $rows) {
    if ($r.PromptId -eq $PromptId) {
        $r.Status = $target
        $r.UpdatedAt = (Get-Date).ToString('s')
    }
}
Write-M6Ledger $rows
Write-Host ("MARKED " + $PromptId + " => " + $target) -ForegroundColor Green
& (Join-Path $PSScriptRoot "Get-NextPromptLocked.ps1")
exit 0
