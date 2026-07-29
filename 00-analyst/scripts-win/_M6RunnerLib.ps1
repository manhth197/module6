# _M6RunnerLib.ps1 -- shared helpers for the M6 locked runner (dot-source me).
# PowerShell 5.1, ASCII-only literals, UTF-8 (no BOM) file IO.

$script:PackRoot = Split-Path $PSScriptRoot -Parent
$script:LedgerPath = Join-Path $script:PackRoot "04-artifacts\state\PROMPT_EXECUTION_LEDGER_LOCKED.csv"
$script:IndexPath = Join-Path $script:PackRoot "00-spec\PROMPT_INDEX_LOCKED.csv"
$script:StatePath = Join-Path $script:PackRoot "04-artifacts\state\CURRENT_STATE_LOCKED.json"
$script:HandoffDir = Join-Path $script:PackRoot "03-runner\handoff"
$script:LedgerCols = @("PromptId","Order","Role","Agent","Phase","Slice","Title","File",
    "RequiresEvidence","RequiresJudge","GateLevel","DependsOn","ExpectedEvidence",
    "ExpectedJudge","RequiredInputs","RequiredOutputs","Status","Note","UpdatedAt","Attempt")
$script:PassLike = @("PASS","SIGNED","SKIPPED")

function Read-M6Csv([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Missing CSV: $path" }
    $raw = Get-Content -Raw -Encoding UTF8 -LiteralPath $path
    return @($raw | ConvertFrom-Csv)
}

function Write-M6Ledger($rows) {
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine(($script:LedgerCols | ForEach-Object { '"' + $_ + '"' }) -join ",")
    foreach ($r in $rows) {
        $cells = foreach ($c in $script:LedgerCols) {
            $v = [string]$r.$c
            '"' + $v.Replace('"', '""') + '"'
        }
        [void]$sb.AppendLine($cells -join ",")
    }
    [System.IO.File]::WriteAllText($script:LedgerPath, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
}

function Get-M6Row($rows, [string]$promptId) {
    $row = $rows | Where-Object { $_.PromptId -eq $promptId }
    if (-not $row) { throw "PromptId not found in ledger: $promptId" }
    return $row
}

function Get-M6Deps($row) {
    $deps = @()
    foreach ($d in ([string]$row.DependsOn).Split(";")) {
        if ($d.Trim().Length -gt 0) { $deps += $d.Trim() }
    }
    return $deps
}

function Test-M6DepsPassed($rows, $row, [ref]$missing) {
    $byId = @{}
    foreach ($r in $rows) { $byId[$r.PromptId] = $r }
    $bad = @()
    foreach ($d in (Get-M6Deps $row)) {
        if (-not $byId.ContainsKey($d)) { $bad += ($d + " (unknown)"); continue }
        $depStatus = [string]$byId[$d].Status
        if ($script:PassLike -notcontains $depStatus) {
            $bad += ($d + " (status=" + $depStatus + ")")
        }
        # [M5-lesson port | advisor hardening | owner apply-mode A | 2026-07-19]
        # Gate-time SKIPPED bypass fix: a SKIPPED dependency MUST carry an approved
        # SKIP_APPROVED note. The set-time guard (Set-PromptStatusLocked) alone is
        # bypassable via a direct ledger row set to SKIPPED with a blank Note.
        elseif ($depStatus -eq "SKIPPED" -and ([string]$byId[$d].Note) -notmatch '^SKIP_APPROVED:\S+') {
            $bad += ($d + " (SKIPPED_WITHOUT_SKIP_APPROVED_NOTE)")
        }
    }
    $missing.Value = $bad
    return ($bad.Count -eq 0)
}

function Get-M6PromptMode([string]$fileRel) {
    $p = Join-Path $script:PackRoot ($fileRel.Replace("/", "\"))
    if (-not (Test-Path -LiteralPath $p)) { return "" }
    $txt = Get-Content -Raw -Encoding UTF8 -LiteralPath $p
    $m = [regex]::Match($txt, "<mode>([^<]+)</mode>")
    if ($m.Success) { return $m.Groups[1].Value.Trim() }
    return ""
}

function Get-M6RoleAllowlist() {
    # role_name (each comma-separated part) -> allowed_write_roots
    $regPath = Join-Path $script:PackRoot "registry\ROLE_REGISTRY.json"
    $reg = Get-Content -Raw -Encoding UTF8 -LiteralPath $regPath | ConvertFrom-Json
    $map = @{}
    foreach ($role in $reg.roles) {
        foreach ($part in ([string]$role.role_name).Split(",")) {
            $p = $part.Trim()
            if ($p.Length -gt 0) { $map[$p] = @($role.allowed_write_roots) }
        }
    }
    return $map
}

function Test-M6SecretScan([string]$path, [ref]$findings) {
    # Same detection families as the hooks: tokens, secret assignments,
    # user-id assignments, emails, TWO-PATTERN phones (never a bridging form).
    $out = @()
    $content = Get-Content -Raw -Encoding UTF8 -LiteralPath $path -ErrorAction SilentlyContinue
    if ([string]::IsNullOrEmpty($content)) { $findings.Value = @(); return $true }
    $tokenRx = @(
        'EAA[A-Za-z0-9]{20,}', 'sk-[A-Za-z0-9_\-]{20,}', 'gh[pousr]_[A-Za-z0-9]{20,}',
        'xox[baprs]-[A-Za-z0-9\-]{10,}', 'AKIA[0-9A-Z]{16}', 'AIza[0-9A-Za-z_\-]{30,}',
        'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}')
    foreach ($rx in $tokenRx) {
        if ([regex]::IsMatch($content, $rx)) { $out += ("token shape: " + $rx) }
    }
    $secretRx = '(?i)\b(api[_-]?key|apikey|secret|token|passwd|password|access[_-]?key|verify[_-]?token|private[_-]?key)\b\s*[:=]\s*[''"]([^''"\r\n]{12,})[''"]'
    foreach ($m in [regex]::Matches($content, $secretRx)) {
        if ($m.Groups[2].Value -notmatch '^(secret_ref|vault:|\$\{|\{\{|<|MASKED|REDACTED|PLACEHOLDER|EXAMPLE)') {
            $out += ("secret assignment: " + $m.Groups[1].Value)
        }
    }
    $idRx = '(?i)\b(user[_-]?id|customer[_-]?id|guest[_-]?id|psid|buyer[_-]?id|member[_-]?id)\b[''"]?\s*[:=]\s*[''"]?(\d{6,})'
    foreach ($m in [regex]::Matches($content, $idRx)) { $out += ("raw user-id: " + $m.Groups[1].Value) }
    $emailRx = '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
    foreach ($m in [regex]::Matches($content, $emailRx)) { $out += ("email: " + $m.Value.Substring(0, 3) + "***") }
    $phone1 = '(?<![A-Za-z0-9])(?:\+?84|0)\d{8,10}(?![A-Za-z0-9])'
    $phone2 = '(?<![A-Za-z0-9])(?:\+?84[ .\-]?|0)\d{2,3}[ .\-]\d{3,4}[ .\-]\d{3,4}(?![A-Za-z0-9])(?![ .\-]\d)'
    foreach ($m in [regex]::Matches($content, $phone1)) { $out += "phone (contiguous)" }
    foreach ($m in [regex]::Matches($content, $phone2)) { $out += "phone (grouped)" }
    $findings.Value = $out
    return ($out.Count -eq 0)
}
