# Get-M6LockedStatus.ps1 -- one-screen status of the locked M6 runner.
# Shows the global lock banner, status counts, progress, the RUNNING prompt,
# and the next ready prompt (each with its role window). Read-only; changes nothing.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File scripts-win\Get-M6LockedStatus.ps1

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
$total = $rows.Count

# ---- global lock banner (read defensively from CURRENT_STATE_LOCKED.json) ----
$gw = 'BLOCKED'; $pf = 'OFF'
if (Test-Path -LiteralPath $script:StatePath) {
    try {
        $state = Get-Content -Raw -Encoding UTF8 -LiteralPath $script:StatePath | ConvertFrom-Json
        if ($state.global_gateway_state) { $gw = [string]$state.global_gateway_state }
        if ($state.production_flag)      { $pf = [string]$state.production_flag }
    } catch { }
}
Write-Host ""
Write-Host ("=" * 64) -ForegroundColor Cyan
Write-Host "  M6 LOCKED STATUS" -ForegroundColor Cyan
Write-Host ("=" * 64) -ForegroundColor Cyan
$gwColor = if ($gw -eq 'BLOCKED') { 'Green' } else { 'Red' }
Write-Host ("  GLOBAL_GATEWAY : " + $gw) -ForegroundColor $gwColor
Write-Host ("  production_flag: " + $pf) -ForegroundColor $gwColor

# ---- status counts ----
Write-Host ""
Write-Host "  Status counts:" -ForegroundColor White
$rows | Group-Object Status | Sort-Object Name | ForEach-Object {
    Write-Host ("     {0,-10} {1,4}" -f $_.Name, $_.Count)
}
$done = @($rows | Where-Object { $script:PassLike -contains $_.Status }).Count
$pct  = if ($total -gt 0) { [math]::Round(100.0 * $done / $total, 1) } else { 0 }
Write-Host ("  Progress: " + $done + " / " + $total + " done (" + $pct + "%)") -ForegroundColor White

$judgeLeft = @($rows | Where-Object { $_.GateLevel -eq 'JUDGE_GATE' -and ($script:PassLike -notcontains $_.Status) }).Count
Write-Host ("  Judge gates remaining: " + $judgeLeft)

# ---- running ----
Write-Host ""
$running = @($rows | Where-Object { $_.Status -eq 'RUNNING' })
if ($running.Count -gt 0) {
    foreach ($r in $running) {
        Write-Host ("  RUNNING : " + $r.PromptId + "  [" + $r.Role + "]  " + $r.Title) -ForegroundColor Yellow
        Write-Host ("            window: " + (Get-M6Window $r.Role)) -ForegroundColor Yellow
    }
} else {
    Write-Host "  RUNNING : (none)"
}

# ---- next ready ----
$next = $null
foreach ($r in ($rows | Sort-Object { [int]$_.Order })) {
    if ($r.Status -ne 'TODO') { continue }
    $missing = @()
    if (Test-M6DepsPassed $rows $r ([ref]$missing)) { $next = $r; break }
}
if ($next) {
    Write-Host ("  NEXT    : " + $next.PromptId + "  [" + $next.Role + "]  " + $next.Title) -ForegroundColor Green
    Write-Host ("            window: " + (Get-M6Window $next.Role)) -ForegroundColor Green
} else {
    Write-Host "  NEXT    : (none ready -- all done or deps blocked)"
}
Write-Host ("=" * 64) -ForegroundColor Cyan
Write-Host ""
exit 0
