# Set-PromptStatusLocked.ps1 -- operator tool for non-success transitions.
# ValidateSet EXCLUDES PASS and SIGNED on purpose: success states exist ONLY
# via Mark-PromptPassLocked.ps1 (which runs the machine gate first).
# SKIPPED requires -Note 'SKIP_APPROVED:<owner-decision-ref>'. SKIPPED counts
# as passed for dependencies, so an ungated skip would be a gate bypass.
#
# JUDGE_GATE rows: skipping one is an OWNER BREAK-GLASS, not a normal move
# (SCHEMA_CHANGELOG rows 13 + 15). It is refused unless ALL of these hold:
#   -Note 'SKIP_APPROVED:OWNER_OVERRIDE:<decision-ref>'
#   04-artifacts/evidence/decisions/<decision-ref>.json exists, parses,
#     has type=OWNER_OVERRIDE, and NAMES THIS PromptId in target_gate
#     (an override is scoped to ONE gate -- never to every judge gate)
#   global_gateway_state=BLOCKED and production_flag=OFF (staged builds only)
# The judge verdict / sign-off file is NEVER modified and the ledger records
# SKIPPED, never PASS/SIGNED: an owner-accepted gap, honestly recorded.
# The same check re-runs at GATE time (Test-M6DepsPassed), so hand-editing the
# ledger does not inherit an override the owner never granted.
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
        # OWNER break-glass -- delegated to the shared helper so the set-time and
        # gate-time checks can never drift apart. Transparent, reversible, audited:
        # judge verdict untouched, ledger shows SKIPPED (never PASS/SIGNED), and the
        # override is bound to the ONE gate its decision file names.
        $ovReason = ""
        if (-not (Test-M6OwnerOverride $PromptId $Note ([ref]$ovReason))) {
            throw ("REFUSED: " + $PromptId + " is a JUDGE_GATE and this is an owner break-glass, not a normal skip. " + $ovReason + ". Required: -Note 'SKIP_APPROVED:OWNER_OVERRIDE:<decision-ref>' where 04-artifacts/evidence/decisions/<decision-ref>.json exists, has type=OWNER_OVERRIDE and names " + $PromptId + " in target_gate, while production stays BLOCKED/OFF. The judge verdict stays as-is; this records an owner-accepted gap, never a PASS.")
        }
    } else {
        # EVIDENCE_GATE rows keep the lighter rule (a ref is required, but it need
        # not resolve to a decision file): a skipped evidence row still fails closed
        # downstream, because the next judge gate lists its evidence JSON in
        # RequiredInputs and Check-PromptGateLocked hard-fails on a missing input.
        # Warn rather than block, so the operator is told when a ref points nowhere.
        $refM = [regex]::Match($Note, '^SKIP_APPROVED:([^;\s]+)')
        if ($refM.Success) {
            $refFile = Join-Path $script:PackRoot ("04-artifacts\evidence\decisions\" + $refM.Groups[1].Value + ".json")
            if (-not (Test-Path -LiteralPath $refFile)) {
                Write-Host ("WARNING: skip ref '" + $refM.Groups[1].Value + "' has no decision file at 04-artifacts/evidence/decisions/. The skip is recorded, but the audit trail points nowhere.") -ForegroundColor Yellow
            }
        }
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
