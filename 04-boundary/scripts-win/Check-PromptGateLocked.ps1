# Check-PromptGateLocked.ps1 -- the machine gate. Exit 0 = pass, exit 2 = fail
# with reasons. NEVER changes state; Mark-PromptPassLocked.ps1 calls this.
# Validates: dependencies passed; required inputs/outputs exist; evidence JSON
# parses; prompt_id matches; status pass-like; fail_gate_tripped=false;
# open_blockers empty; every evidence_refs path exists; files_changed within
# the role's allowlist; smoke-run prompts have non-empty commands_run +
# structured test_results; judge rows additionally validate the sign-off file
# (verdict pass-like, prompt_id match, non-empty evidence_reviewed with
# existing paths). Secret-scans every checked file.
# Usage: scripts-win\Check-PromptGateLocked.ps1 -PromptId M6-P0000

param(
    [Parameter(Mandatory = $true)][string]$PromptId
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot "_M6RunnerLib.ps1")

$reasons = New-Object System.Collections.Generic.List[string]
function Add-Fail([string]$r) { $reasons.Add($r) }

# Safe existence check. NEVER throws -- executor-written fields (evidence_refs,
# judge evidence_reviewed) may contain prose or illegal path chars; with
# $ErrorActionPreference='Stop' a raw Test-Path on such a value aborts the whole
# gate ("Illegal characters in path"). This returns $false for invalid/missing
# instead, so the gate FAILS the row with a clear reason rather than crashing.
function Test-M6PathExists([string]$p) {
    if ([string]::IsNullOrWhiteSpace($p)) { return $false }
    try {
        foreach ($ch in [System.IO.Path]::GetInvalidPathChars()) {
            if ($p.IndexOf($ch) -ge 0) { return $false }
        }
        return ([System.IO.File]::Exists($p) -or [System.IO.Directory]::Exists($p))
    } catch { return $false }
}

$rows = Read-M6Csv $script:LedgerPath
$row = Get-M6Row $rows $PromptId

# 1. dependencies
$missing = @()
if (-not (Test-M6DepsPassed $rows $row ([ref]$missing))) {
    Add-Fail ("dependencies not passed: " + ($missing -join ", "))
}

# 2. required inputs exist
# ("path#section" notation scopes a read to a section for humans; only the
#  file part is testable on disk)
foreach ($f in ([string]$row.RequiredInputs).Split(";")) {
    $f = $f.Trim(); if ($f.Length -eq 0) { continue }
    $fPath = $f.Split("#")[0]
    $p = Join-Path $script:PackRoot ($fPath.Replace("/", "\"))
    if (-not (Test-M6PathExists $p)) { Add-Fail ("required input missing: " + $f) }
}

# 3. required outputs exist
$checkedFiles = New-Object System.Collections.Generic.List[string]
foreach ($f in ([string]$row.RequiredOutputs).Split(";")) {
    $f = $f.Trim(); if ($f.Length -eq 0) { continue }
    $p = Join-Path $script:PackRoot ($f.Replace("/", "\"))
    if (-not (Test-M6PathExists $p)) { Add-Fail ("required output missing: " + $f) }
    else { $checkedFiles.Add($p) }
}

# 4. evidence JSON
$evPath = Join-Path $script:PackRoot (([string]$row.ExpectedEvidence).Replace("/", "\"))
$evidence = $null
if (-not (Test-M6PathExists $evPath)) {
    Add-Fail ("evidence file missing: " + $row.ExpectedEvidence)
} else {
    try { $evidence = Get-Content -Raw -Encoding UTF8 -LiteralPath $evPath | ConvertFrom-Json }
    catch { Add-Fail "evidence JSON does not parse" }
}
if ($evidence) {
    foreach ($k in @("prompt_id","status","summary","files_read","files_changed",
                     "commands_run","evidence_refs","open_blockers","fail_gate_tripped",
                     "fail_gate_lines","next_recommended_action")) {
        if (-not $evidence.PSObject.Properties[$k]) { Add-Fail ("evidence schema: missing key '" + $k + "'") }
    }
    if ([string]$evidence.prompt_id -ne $PromptId) {
        Add-Fail ("evidence prompt_id mismatch: '" + $evidence.prompt_id + "' vs '" + $PromptId + "'")
    }
    if (@("PASS") -notcontains [string]$evidence.status) {
        Add-Fail ("evidence status not pass-like: '" + $evidence.status + "'")
    }
    if ($evidence.fail_gate_tripped -ne $false) { Add-Fail "fail_gate_tripped is not false" }
    if (@($evidence.open_blockers).Count -gt 0) {
        Add-Fail ("open_blockers not empty: " + ((@($evidence.open_blockers) | Select-Object -First 3) -join " | "))
    }
    foreach ($ref in @($evidence.evidence_refs)) {
        $refStr = [string]$ref
        $rp = Join-Path $script:PackRoot ($refStr.Replace("/", "\"))
        if (-not (Test-M6PathExists $rp)) {
            Add-Fail ("evidence_refs entry must be an EXISTING FILE PATH relative to the pack root (put descriptions in 'summary', not here): '" + $refStr + "'")
        }
    }
    # files_changed within the role allowlist
    $allowMap = Get-M6RoleAllowlist
    $allow = @()
    if ($allowMap.ContainsKey([string]$row.Role)) { $allow = @($allowMap[[string]$row.Role]) }
    foreach ($fc in @($evidence.files_changed)) {
        $rel = ([string]$fc).Replace("\", "/").TrimStart("/")
        $ok = $false
        foreach ($root in $allow) {
            $needle = ([string]$root).Replace("\", "/").TrimEnd("/")
            if ($rel -eq $needle -or $rel.ToLower().StartsWith($needle.ToLower() + "/")) { $ok = $true; break }
        }
        if (-not $ok) { Add-Fail ("files_changed outside role allowlist (" + $row.Role + "): " + $fc) }
    }
    # smoke-run prompts: commands_run + structured test_results
    $mode = Get-M6PromptMode ([string]$row.File)
    if ($mode -eq "test") {
        if (@($evidence.commands_run).Count -eq 0) { Add-Fail "test prompt: commands_run is empty" }
        if (-not $evidence.PSObject.Properties["test_results"]) {
            Add-Fail "test prompt: test_results missing"
        } elseif (@($evidence.test_results).Count -eq 0) {
            Add-Fail "test prompt: test_results is empty"
        } else {
            foreach ($tr in @($evidence.test_results)) {
                foreach ($k in @("smoke_id","result","detail")) {
                    if (-not $tr.PSObject.Properties[$k]) { Add-Fail ("test_results entry missing '" + $k + "'") }
                }
                # [M5-lesson port | advisor hardening | owner apply-mode A | 2026-07-19]
                # A recorded smoke must actually be pass-like AND carry a non-empty detail;
                # key-presence alone let result:"" (or any value) gate-pass a green smoke.
                if ($tr.PSObject.Properties["result"] -and (@("PASS") -notcontains [string]$tr.result)) {
                    Add-Fail ("test_results '" + [string]$tr.smoke_id + "' result not pass-like: '" + [string]$tr.result + "'")
                }
                if ($tr.PSObject.Properties["detail"] -and [string]::IsNullOrWhiteSpace([string]$tr.detail)) {
                    Add-Fail ("test_results '" + [string]$tr.smoke_id + "' detail is empty")
                }
            }
        }
    }
}

# 5. judge rows: sign-off validation
if ([string]$row.RequiresJudge -eq "true") {
    $joPath = Join-Path $script:PackRoot (([string]$row.ExpectedJudge).Replace("/", "\"))
    if (-not (Test-M6PathExists $joPath)) {
        Add-Fail ("judge sign-off missing: " + $row.ExpectedJudge)
    } else {
        $signoff = $null
        try { $signoff = Get-Content -Raw -Encoding UTF8 -LiteralPath $joPath | ConvertFrom-Json }
        catch { Add-Fail "judge sign-off JSON does not parse" }
        if ($signoff) {
            if ([string]$signoff.prompt_id -ne $PromptId) { Add-Fail "judge sign-off prompt_id mismatch" }
            if (@("PASS") -notcontains [string]$signoff.verdict) {
                Add-Fail ("judge verdict not pass-like: '" + $signoff.verdict + "'")
            }
            if ($signoff.fail_gate_tripped -ne $false) { Add-Fail "judge sign-off fail_gate_tripped not false" }
            if (@($signoff.open_blockers).Count -gt 0) { Add-Fail "judge sign-off open_blockers not empty" }
            if (@($signoff.evidence_reviewed).Count -eq 0) {
                Add-Fail "judge sign-off evidence_reviewed is empty"
            } else {
                foreach ($er in @($signoff.evidence_reviewed)) {
                    $erStr = [string]$er
                    $ep = Join-Path $script:PackRoot ($erStr.Replace("/", "\"))
                    if (-not (Test-M6PathExists $ep)) {
                        Add-Fail ("judge evidence_reviewed must be an EXISTING FILE PATH (not prose): '" + $erStr + "'")
                    }
                }
            }
        }
        $checkedFiles.Add($joPath)
    }
}

# 6. secret-scan every checked file
foreach ($cf in $checkedFiles) {
    $found = @()
    if (-not (Test-M6SecretScan $cf ([ref]$found))) {
        Add-Fail ("secret/PII scan hit in " + $cf.Substring($script:PackRoot.Length + 1) + ": " + (($found | Select-Object -First 3) -join "; "))
    }
}

# 7. substance verifier (M6-SGV-1.0): recompute the fail-gate verdict from the
# evidence's own severity/blocker signals. Author-declared status/
# fail_gate_tripped/open_blockers are ADVISORY; the computed verdict is
# AUTHORITATIVE, and a claimed-vs-computed mismatch is an integrity FAIL. Runs
# AFTER the shape checks above and FAILS CLOSED (python or script missing =>
# SUBSTANCE_VERIFIER_UNAVAILABLE). On the pristine pack (no evidence yet) the
# verifier vacuously passes; presence/parse is already enforced in step 4.
$svScript = Join-Path $script:PackRoot "scripts\m6_substance_verifier.py"
$svPy = $null
$venvPy = Join-Path $script:PackRoot ".venv\Scripts\python.exe"
if (Test-Path -LiteralPath $venvPy) { $svPy = $venvPy }
elseif (Get-Command python -ErrorAction SilentlyContinue) { $svPy = "python" }
if (-not $svPy) {
    Add-Fail "SUBSTANCE_VERIFIER_UNAVAILABLE: python not found (fail-closed)"
} elseif (-not (Test-Path -LiteralPath $svScript)) {
    Add-Fail "SUBSTANCE_VERIFIER_UNAVAILABLE: scripts\m6_substance_verifier.py missing (fail-closed)"
} else {
    # With $ErrorActionPreference='Stop' (top of file), a native command that
    # writes to stderr can become a terminating NativeCommandError when the
    # whole invocation is captured with 2>&1. Set Continue locally around the
    # native call so a stray stderr write cannot terminate the gate, then
    # restore. --caller gate makes the verifier emit ONLY the JSON object.
    $svPrevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $svOut = & $svPy $svScript --mode gate --prompt $PromptId --root $script:PackRoot --write-computed --caller gate
    $svExit = $LASTEXITCODE
    $ErrorActionPreference = $svPrevEAP
    $svJson = $null
    if ($svOut) { try { $svJson = ($svOut -join "`n") | ConvertFrom-Json } catch { $svJson = $null } }
    if ($svExit -eq 0) {
        # substance verified (computed record under 04-artifacts\gate-hardening\computed\)
    } elseif ($svExit -eq 2 -and $svJson) {
        foreach ($sf in @($svJson.failures)) { Add-Fail ("SUBSTANCE: " + $sf) }
        foreach ($iv in @($svJson.integrity_violations)) { Add-Fail ("SUBSTANCE_INTEGRITY: " + $iv) }
        if (@($svJson.failures).Count -eq 0 -and @($svJson.integrity_violations).Count -eq 0) {
            Add-Fail "SUBSTANCE: verifier exit 2 without detail (fail-closed)"
        }
    } else {
        Add-Fail ("SUBSTANCE_VERIFIER_ERROR: exit " + $svExit + " (fail-closed)")
    }
}

if ($reasons.Count -gt 0) {
    Write-Host ("GATE FAIL for " + $PromptId + " (" + $reasons.Count + " reason(s)):") -ForegroundColor Red
    foreach ($r in $reasons) { Write-Host ("  - " + $r) }
    exit 2
}
Write-Host ("GATE PASS for " + $PromptId) -ForegroundColor Green
exit 0
