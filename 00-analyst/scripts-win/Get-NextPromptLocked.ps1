# Get-NextPromptLocked.ps1 -- show the next ready prompt (by Order, deps gated).
# Writes _NEXT_PROMPT_LOCKED.md at the pack root and prints a role-banner summary.
# M5-style upgrade: colored Role/Window banner, field list, and -ShowContent.
# Backward compatible: no-arg behavior unchanged (shows next, writes the .md).
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts-win\Get-NextPromptLocked.ps1 [-ShowContent] [-PromptId M6-Pxxxx]

param(
    [switch]$ShowContent,
    [string]$PromptId
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot "_M6RunnerLib.ps1")

function Get-M6Window([string]$role) {
    switch ($role) {
        'PM_ORCHESTRATOR'    { 'pack root  (PM window)' ; break }
        'JUDGE'              { 'pack root  (FRESH Judge session per judgment)' ; break }
        'ANALYST_ARCHITECT'  { '00-analyst' ; break }
        'CODER'              { '01-coder' ; break }
        'TESTER'             { '02-tester' ; break }
        'BOUNDARY_ADVERSARY' { '04-boundary' ; break }
        'SECURITY_PII'       { '06-security' ; break }
        default              { '(see setup/OPERATING_LOOP.md)' }
    }
}
function Write-Rule([string]$color) { Write-Host ("=" * 64) -ForegroundColor $color }

$rows = Read-M6Csv $script:LedgerPath

# If a prompt is already RUNNING, surface it (with its window) unless a specific
# PromptId was requested.
$running = @($rows | Where-Object { $_.Status -eq 'RUNNING' })
if ($running.Count -gt 0 -and -not $PromptId) {
    Write-Host ""
    Write-Rule 'Yellow'
    Write-Host "  A prompt is already RUNNING" -ForegroundColor Yellow
    Write-Rule 'Yellow'
    foreach ($r in $running) {
        Write-Host ("  " + $r.PromptId + "  [" + $r.Role + "]  " + $r.Title)
        Write-Host ("  window : " + (Get-M6Window $r.Role)) -ForegroundColor Cyan
    }
    Write-Host "  Finish it (Check + Mark) or reset it (Set-PromptStatusLocked -Status TODO/BLOCKED)."
    Write-Host ""
    exit 1
}

# Resolve target: explicit PromptId, else the first deps-clear TODO by Order.
if ($PromptId) {
    $next = $rows | Where-Object { $_.PromptId -eq $PromptId } | Select-Object -First 1
    if (-not $next) { throw "Unknown PromptId: $PromptId" }
} else {
    $next = $null
    foreach ($r in ($rows | Sort-Object { [int]$_.Order })) {
        if ($r.Status -ne 'TODO') { continue }
        $missing = @()
        if (Test-M6DepsPassed $rows $r ([ref]$missing)) { $next = $r; break }
    }
}

if (-not $next) {
    Write-Host "No ready prompt. Either everything is done or dependencies are blocked." -ForegroundColor Yellow
    $blocked = @($rows | Where-Object { $_.Status -eq 'TODO' } | Sort-Object { [int]$_.Order } | Select-Object -First 5)
    foreach ($b in $blocked) {
        $miss = @(); [void](Test-M6DepsPassed $rows $b ([ref]$miss))
        Write-Host ("  waiting: " + $b.PromptId + " <- " + ($miss -join ", "))
    }
    exit 1
}

$win = Get-M6Window $next.Role

# ---- pretty console banner (M5 style) ----
Write-Host ""
Write-Rule 'Cyan'
Write-Host "  NEXT PROMPT  (locked runner)" -ForegroundColor Cyan
Write-Rule 'Cyan'
Write-Host ("  PromptId : " + $next.PromptId + "    Order: " + $next.Order + "    Gate: " + $next.GateLevel)
Write-Host ("  Role     : " + $next.Role) -ForegroundColor White
Write-Host ("  Window   : " + $win + "   <-- paste the prompt HERE") -ForegroundColor Yellow
Write-Host ("  Phase    : " + $next.Phase + " / " + $next.Slice)
Write-Host ("  Title    : " + $next.Title)
Write-Host ("  File     : " + $next.File)
Write-Host ("  Evidence : " + $next.ExpectedEvidence)
Write-Host ("-" * 64) -ForegroundColor DarkGray
Write-Host "  Stage it (mark RUNNING + clipboard + open handoff):" -ForegroundColor Green
Write-Host "     scripts-win\Get-NextPromptDetail.ps1 -CopyToClipboard -Open" -ForegroundColor Green
Write-Rule 'Cyan'

# ---- write _NEXT_PROMPT_LOCKED.md (kept as a stable artifact) ----
$md = @()
$md += "# NEXT PROMPT (locked runner)"
$md += ""
$md += "| Field | Value |"
$md += "|---|---|"
$md += ("| PromptId | " + $next.PromptId + " |")
$md += ("| Order | " + $next.Order + " |")
$md += ("| Role | " + $next.Role + " |")
$md += ("| Window | " + $win + " |")
$md += ("| Phase / Slice | " + $next.Phase + " / " + $next.Slice + " |")
$md += ("| Title | " + $next.Title + " |")
$md += ("| Gate | " + $next.GateLevel + " |")
$md += ("| Prompt file | " + $next.File + " |")
$md += ("| Expected evidence | " + $next.ExpectedEvidence + " |")
$md += ""
$md += "Run: scripts-win\Get-NextPromptDetail.ps1 -CopyToClipboard -Open"
$outPath = Join-Path $script:PackRoot "_NEXT_PROMPT_LOCKED.md"
[System.IO.File]::WriteAllText($outPath, ($md -join [Environment]::NewLine), (New-Object System.Text.UTF8Encoding($false)))
Write-Host ("  wrote " + $outPath) -ForegroundColor DarkGray

# ---- optional: print the full prompt body ----
if ($ShowContent) {
    $promptFile = Join-Path $script:PackRoot ($next.File.Replace("/", "\"))
    if (Test-Path -LiteralPath $promptFile) {
        $body = Get-Content -Raw -Encoding UTF8 -LiteralPath $promptFile
        Write-Host ""
        Write-Host "===== PROMPT START =====" -ForegroundColor Cyan
        Write-Host $body
        Write-Host "===== PROMPT END =====" -ForegroundColor Cyan
    } else {
        Write-Host ("  (prompt file missing: " + $promptFile + ")") -ForegroundColor Red
    }
}
exit 0
