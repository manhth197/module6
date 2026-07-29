# role_pre_tool_guard.ps1 -- PreToolUse hook (M6 build pack).
# Byte-identical copy shipped to every role folder; canonical master lives in
# setup/hooks-master/. Behavior must stay identical to role_pre_tool_guard.py.
#
# Blocks (exit 2 + reason on stderr):
#   (a) danger patterns anywhere in the raw payload: production-flag flips,
#       gateway-state flips, secret assignments, live token shapes;
#   (b) mutating shell verbs combined with denied roots -- scanned ONLY in
#       command/script fields, never in Write/Edit file content;
#   (c) Write/Edit/MultiEdit paths outside the role allowlist or inside
#       deny roots (absolute paths inside the role project are normalized
#       to relative first; absolute paths outside the project are blocked).
# Fail-closed: unparseable payload or missing policy file => block.

$ErrorActionPreference = 'Stop'

function Block($reason) {
    [Console]::Error.WriteLine("ROLE_PRE_TOOL_GUARD BLOCK: " + $reason)
    exit 2
}

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { Block "empty hook payload (fail-closed)" }

try { $payload = $raw | ConvertFrom-Json } catch { Block "unparseable hook payload (fail-closed)" }

$roleRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$policyPath = Join-Path $roleRoot ".claude\role_policy.json"
if (-not (Test-Path $policyPath)) { Block "role_policy.json missing (fail-closed)" }
try {
    $policy = Get-Content -Raw -Encoding UTF8 $policyPath | ConvertFrom-Json
} catch { Block "role_policy.json unparseable (fail-closed)" }

$toolName = ""
if ($payload.PSObject.Properties['tool_name']) { $toolName = [string]$payload.tool_name }

# ---------------- (a) danger patterns on the whole payload ----------------
$dangerPatterns = @(
    @{ Name = "production flag flip";  Rx = '(?i)production_flag\s*"?\s*[:=]\s*"?\s*(ON|TRUE|1|ENABLED)\b' },
    @{ Name = "gateway state flip";    Rx = '(?i)global_gateway_state\s*"?\s*[:=]\s*"?\s*(OPEN|READY|PASS|UNLOCKED|GO)\b' },
    @{ Name = "meta token shape";      Rx = 'EAA[A-Za-z0-9]{20,}' },
    @{ Name = "openai token shape";    Rx = 'sk-[A-Za-z0-9_\-]{20,}' },
    @{ Name = "github token shape";    Rx = 'gh[pousr]_[A-Za-z0-9]{20,}' },
    @{ Name = "slack token shape";     Rx = 'xox[baprs]-[A-Za-z0-9\-]{10,}' },
    @{ Name = "aws key shape";         Rx = 'AKIA[0-9A-Z]{16}' },
    @{ Name = "google key shape";      Rx = 'AIza[0-9A-Za-z_\-]{30,}' },
    @{ Name = "jwt shape";             Rx = 'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}' }
)
foreach ($p in $dangerPatterns) {
    if ($raw -match $p.Rx) { Block ("danger pattern detected: " + $p.Name) }
}
# secret assignment with a literal value (secret_ref / placeholder values allowed)
$secretRx = '(?i)\b(api[_-]?key|apikey|secret|token|passwd|password|access[_-]?key|verify[_-]?token|private[_-]?key)\b\s*[:=]\s*[''"]([^''"\r\n]{12,})[''"]'
$m = [regex]::Matches($raw, $secretRx)
foreach ($mm in $m) {
    $val = $mm.Groups[2].Value
    if ($val -notmatch '^(secret_ref|vault:|\$\{|\{\{|<|MASKED|REDACTED|PLACEHOLDER|EXAMPLE)') {
        Block "secret assignment with literal value (use secret_ref)"
    }
}

# ---------------- (b) shell verb + denied root, command fields only -------
$denyRoots = @()
if ($policy.PSObject.Properties['deny_write_roots']) { $denyRoots = @($policy.deny_write_roots) }
$cmdText = ""
if ($payload.PSObject.Properties['tool_input'] -and $payload.tool_input) {
    foreach ($f in @('command', 'script')) {
        if ($payload.tool_input.PSObject.Properties[$f]) {
            $cmdText = $cmdText + " " + [string]$payload.tool_input.$f
        }
    }
}
if ($cmdText.Trim().Length -gt 0) {
    # Redirection alt uses (?<![-=]) so display arrows -> and => do NOT trip it,
    # while real redirection > and >> still match (false-positive fix, 2026-07-20).
    $verbRx = '(?i)(\brm\b|\bdel\b|\berase\b|\brmdir\b|\brd\b|Remove-Item|\bri\b|\bmv\b|\bmove\b|Move-Item|\bren\b|Rename-Item|Set-Content|Add-Content|Out-File|Clear-Content|New-Item|\bcp\b|\bcopy\b|Copy-Item|\btee\b|(?<![-=])>{1,2})'
    $hasVerb = $cmdText -match $verbRx
    $normCmd = $cmdText.Replace('\', '/')
    foreach ($root in $denyRoots) {
        $needle = ([string]$root).Replace('\', '/').TrimEnd('/')
        if ($needle.Length -eq 0) { continue }
        if ($normCmd -match [regex]::Escape($needle)) {
            if ($hasVerb) { Block ("mutating shell verb touching denied root: " + $root) }
        }
    }
}

# ---------------- (c) Write/Edit path allowlist ----------------------------
$writeTools = @('Write', 'Edit', 'MultiEdit', 'NotebookEdit')
if ($writeTools -contains $toolName) {
    $filePath = ""
    if ($payload.tool_input -and $payload.tool_input.PSObject.Properties['file_path']) {
        $filePath = [string]$payload.tool_input.file_path
    } elseif ($payload.tool_input -and $payload.tool_input.PSObject.Properties['notebook_path']) {
        $filePath = [string]$payload.tool_input.notebook_path
    }
    if ([string]::IsNullOrWhiteSpace($filePath)) { Block "write tool without file path (fail-closed)" }
    $norm = $filePath.Replace('/', '\')
    $rootNorm = $roleRoot.TrimEnd('\')
    if ($norm -match '^[A-Za-z]:\\' -or $norm.StartsWith('\\')) {
        # absolute: must be inside the role project
        $full = [System.IO.Path]::GetFullPath($norm)
        if (-not ($full.ToLower().StartsWith($rootNorm.ToLower() + '\'))) {
            Block ("absolute write path outside role project: " + $filePath)
        }
        $norm = $full.Substring($rootNorm.Length + 1)
    }
    if ($norm -match '\.\.') { Block "path traversal in write path" }
    $rel = $norm.Replace('\', '/').TrimStart('/')
    foreach ($root in $denyRoots) {
        $needle = ([string]$root).Replace('\', '/').TrimEnd('/')
        if ($needle.Length -eq 0) { continue }
        if ($rel -eq $needle -or $rel.ToLower().StartsWith($needle.ToLower() + '/')) {
            Block ("write into denied root: " + $root)
        }
    }
    $allowRoots = @()
    if ($policy.PSObject.Properties['allowed_write_roots']) { $allowRoots = @($policy.allowed_write_roots) }
    $allowed = $false
    foreach ($root in $allowRoots) {
        $needle = ([string]$root).Replace('\', '/').TrimEnd('/')
        if ($needle.Length -eq 0) { continue }
        if ($rel -eq $needle -or $rel.ToLower().StartsWith($needle.ToLower() + '/')) { $allowed = $true; break }
    }
    if (-not $allowed) { Block ("write path not in role allowlist: " + $rel) }
}

exit 0
