# Get-ReadyPromptsLocked.ps1 -- list every TODO prompt whose dependencies are
# already PASS/SIGNED/SKIPPED (runnable now), sorted by Order, with the role
# window to paste each into. Read-only. Because M6 slices run sequentially,
# usually only the immediate next prompt is ready.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File scripts-win\Get-ReadyPromptsLocked.ps1

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot "_M6RunnerLib.ps1")

function Get-M6Window([string]$role) {
    switch ($role) {
        'PM_ORCHESTRATOR'    { 'pack root (PM)' ; break }
        'JUDGE'              { 'pack root (fresh Judge)' ; break }
        'ANALYST_ARCHITECT'  { '00-analyst' ; break }
        'CODER'              { '01-coder' ; break }
        'TESTER'             { '02-tester' ; break }
        'BOUNDARY_ADVERSARY' { '04-boundary' ; break }
        'SECURITY_PII'       { '06-security' ; break }
        default              { '(see OPERATING_LOOP.md)' }
    }
}

$rows  = Read-M6Csv $script:LedgerPath
$ready = @()
foreach ($r in ($rows | Sort-Object { [int]$_.Order })) {
    if ($r.Status -ne 'TODO') { continue }
    $missing = @()
    if (Test-M6DepsPassed $rows $r ([ref]$missing)) {
        $ready += [pscustomobject]@{
            PromptId = $r.PromptId
            Order    = $r.Order
            Role     = $r.Role
            Window   = (Get-M6Window $r.Role)
            Gate     = $r.GateLevel
            Slice    = $r.Slice
            Title    = $r.Title
        }
    }
}
if ($ready.Count -eq 0) {
    Write-Host "NO_READY_PROMPTS (all done or dependencies blocked)." -ForegroundColor Yellow
    exit 0
}
Write-Host ("READY PROMPTS (" + $ready.Count + "):") -ForegroundColor Green
$ready | Format-Table -AutoSize
exit 0
