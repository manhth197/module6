# Get-NextPromptDetail.ps1 -- the operator's main command.
# Finds the next ready prompt, marks it RUNNING in the ledger, writes a
# paste-ready handoff file NEXT_<id>_<Role>_<ts>.md (prompt text ONLY, no header),
# pre-generates the downstream same-band judge handoff JUDGE_AFTER_RUNNER_<id>_<ts>.md,
# optionally copies the FULL prompt to the clipboard and opens the file.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File scripts-win\Get-NextPromptDetail.ps1 [-CopyToClipboard] [-Open]

param(
    [switch]$CopyToClipboard,
    [switch]$Open
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot "_M6RunnerLib.ps1")

$rows = Read-M6Csv $script:LedgerPath
$running = @($rows | Where-Object { $_.Status -eq 'RUNNING' })
if ($running.Count -gt 0) {
    throw ("A prompt is already RUNNING: " + (($running | ForEach-Object { $_.PromptId }) -join ", ") + ". Finish or reset it first.")
}

$next = $null
foreach ($r in ($rows | Sort-Object { [int]$_.Order })) {
    if ($r.Status -ne 'TODO') { continue }
    $missing = @()
    if (Test-M6DepsPassed $rows $r ([ref]$missing)) { $next = $r; break }
}
if (-not $next) { throw "No ready prompt (all done or blocked). Run Get-NextPromptLocked.ps1 for details." }

$promptFile = Join-Path $script:PackRoot ($next.File.Replace("/", "\"))
if (-not (Test-Path -LiteralPath $promptFile)) { throw "Prompt file missing: $promptFile" }
$promptText = Get-Content -Raw -Encoding UTF8 -LiteralPath $promptFile

New-Item -ItemType Directory -Force $script:HandoffDir | Out-Null
$ts = Get-Date -Format "yyyyMMdd_HHmmss"

# Handoff = the prompt text ONLY (no comment header lines).
$handoffPath = Join-Path $script:HandoffDir ("NEXT_" + $next.PromptId + "_" + $next.Role + "_" + $ts + ".md")
[System.IO.File]::WriteAllText($handoffPath, $promptText, (New-Object System.Text.UTF8Encoding($false)))

# Pre-generate the downstream judge handoff: the next JUDGE_GATE row at a
# higher Order within the same Slice (band).
$judgeRow = $rows |
    Where-Object { $_.Slice -eq $next.Slice -and $_.GateLevel -eq 'JUDGE_GATE' -and [int]$_.Order -ge [int]$next.Order } |
    Sort-Object { [int]$_.Order } | Select-Object -First 1
$judgePath = ""
if ($judgeRow) {
    $jFile = Join-Path $script:PackRoot ($judgeRow.File.Replace("/", "\"))
    if (Test-Path -LiteralPath $jFile) {
        $jText = Get-Content -Raw -Encoding UTF8 -LiteralPath $jFile
        $judgePath = Join-Path $script:HandoffDir ("JUDGE_AFTER_RUNNER_" + $next.PromptId + "_" + $ts + ".md")
        [System.IO.File]::WriteAllText($judgePath, $jText, (New-Object System.Text.UTF8Encoding($false)))
    }
}

# Mark RUNNING (operator action -- this script IS the operator's tool).
foreach ($r in $rows) {
    if ($r.PromptId -eq $next.PromptId) {
        $r.Status = 'RUNNING'
        $r.UpdatedAt = (Get-Date).ToString('s')
        $r.Attempt = [string]([int]$r.Attempt + 1)
    }
}
Write-M6Ledger $rows

if ($CopyToClipboard) { Set-Clipboard -Value $promptText }
if ($Open) { Start-Process notepad.exe $handoffPath }

Write-Host ("RUNNING: " + $next.PromptId + "  [" + $next.Role + "]  " + $next.Title)
Write-Host ("  handoff: " + $handoffPath)
if ($judgePath) { Write-Host ("  judge pre-gen: " + $judgePath) }
if ($CopyToClipboard) { Write-Host "  full prompt copied to clipboard." }
Write-Host ("  after the executor finishes: scripts-win\Check-PromptGateLocked.ps1 -PromptId " + $next.PromptId)
exit 0
