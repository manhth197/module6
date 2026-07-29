# stop_role_evidence_guard.ps1 -- Stop hook (M6 build pack).
# Byte-identical copy shipped to every role folder; canonical master lives in
# setup/hooks-master/. Behavior must stay identical to stop_role_evidence_guard.py.
#
# Blocks "done" (exit 2) while a prompt is marked RUNNING in the execution
# ledger for THIS role but its evidence file does not exist yet. Matches both
# normal and critic prompt ids: M6-P(?:C)?\d{4}.
# stop_hook_active=true (already continuing due to a prior block) => allow.

$ErrorActionPreference = 'Stop'

function Block($reason) {
    [Console]::Error.WriteLine("STOP_ROLE_EVIDENCE_GUARD BLOCK: " + $reason)
    exit 2
}

$raw = [Console]::In.ReadToEnd()
$payload = $null
try { $payload = $raw | ConvertFrom-Json } catch { }
if ($payload -and $payload.PSObject.Properties['stop_hook_active'] -and $payload.stop_hook_active) {
    exit 0
}

$roleRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$policyPath = Join-Path $roleRoot ".claude\role_policy.json"
if (-not (Test-Path $policyPath)) { Block "role_policy.json missing (fail-closed)" }
$policy = $null
try { $policy = Get-Content -Raw -Encoding UTF8 $policyPath | ConvertFrom-Json } catch { Block "role_policy.json unparseable (fail-closed)" }
# role_name may be comma-separated when one folder hosts several ledger roles
# (the pack root hosts PM_ORCHESTRATOR and JUDGE sessions).
$roleNameRaw = ""
if ($policy.PSObject.Properties['role_name']) { $roleNameRaw = [string]$policy.role_name }
if ([string]::IsNullOrWhiteSpace($roleNameRaw)) { Block "role_name missing in role_policy.json (fail-closed)" }
$roleNames = @()
foreach ($rn in $roleNameRaw.Split(',')) { if ($rn.Trim().Length -gt 0) { $roleNames += $rn.Trim() } }

$ledgerPath = Join-Path $roleRoot "04-artifacts\state\PROMPT_EXECUTION_LEDGER_LOCKED.csv"
if (-not (Test-Path $ledgerPath)) { Block "execution ledger not found (fail-closed): 04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv" }

$rows = $null
try {
    $rows = Get-Content -Raw -Encoding UTF8 $ledgerPath | ConvertFrom-Csv
} catch { Block "execution ledger unreadable (fail-closed)" }

$promptIdRx = '^M6-P(?:C)?\d{4}$'
$missing = New-Object System.Collections.Generic.List[string]
foreach ($row in $rows) {
    if ([string]$row.Status -ne 'RUNNING') { continue }
    if ($roleNames -notcontains [string]$row.Role) { continue }
    $pid2 = [string]$row.PromptId
    if ($pid2 -notmatch $promptIdRx) { continue }
    $evidence = Join-Path $roleRoot ("04-artifacts\evidence\prompts\" + $pid2 + ".json")
    if (-not (Test-Path -LiteralPath $evidence)) { $missing.Add($pid2) }
}

if ($missing.Count -gt 0) {
    Block ("active prompt(s) without evidence file: " + ($missing -join ", ") + ". Write 04-artifacts/evidence/prompts/<PromptId>.json before finishing. Do not mark your own work PASS; only write evidence.")
}
exit 0
