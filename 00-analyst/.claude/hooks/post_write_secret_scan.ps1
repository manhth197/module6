# post_write_secret_scan.ps1 -- PostToolUse hook (M6 build pack).
# Byte-identical copy shipped to every role folder; canonical master lives in
# setup/hooks-master/. Behavior must stay identical to post_write_secret_scan.py.
#
# After Write/Edit/MultiEdit, re-reads the written file from disk and scans for:
#   - live token shapes and secret assignments with literal values,
#   - user-id assignments with raw numeric values,
#   - email addresses,
#   - phone numbers via a TWO-PATTERN design (contiguous + separator-grouped).
#     NEVER a single separator-tolerant digit-class with a counted repeat:
#     that form false-positives on ISO dates and ID ranges and bridges
#     across unrelated number runs.
# Findings => exit 2 with the masked finding list on stderr so the agent
# must remediate. Clean => exit 0.

$ErrorActionPreference = 'Stop'

function Fail($lines) {
    [Console]::Error.WriteLine("POST_WRITE_SECRET_SCAN FINDINGS:")
    foreach ($l in $lines) { [Console]::Error.WriteLine(" - " + $l) }
    exit 2
}

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
try { $payload = $raw | ConvertFrom-Json } catch { exit 0 }

$filePath = ""
if ($payload.PSObject.Properties['tool_input'] -and $payload.tool_input) {
    if ($payload.tool_input.PSObject.Properties['file_path']) { $filePath = [string]$payload.tool_input.file_path }
    elseif ($payload.tool_input.PSObject.Properties['notebook_path']) { $filePath = [string]$payload.tool_input.notebook_path }
}
if ([string]::IsNullOrWhiteSpace($filePath)) { exit 0 }
if (-not (Test-Path -LiteralPath $filePath)) { exit 0 }

$binaryExt = @('.png','.jpg','.jpeg','.gif','.pdf','.zip','.docx','.xlsx','.pptx','.exe','.dll','.ico','.woff','.woff2','.ttf')
$ext = [System.IO.Path]::GetExtension($filePath).ToLower()
if ($binaryExt -contains $ext) { exit 0 }

$content = Get-Content -Raw -Encoding UTF8 -LiteralPath $filePath
if ([string]::IsNullOrEmpty($content)) { exit 0 }

$findings = New-Object System.Collections.Generic.List[string]

function Mask($s) {
    if ($s.Length -le 6) { return "***" }
    return $s.Substring(0, 3) + "***" + $s.Substring($s.Length - 2)
}

# --- token shapes -----------------------------------------------------------
$tokenShapes = @(
    @{ Name = "meta token";   Rx = 'EAA[A-Za-z0-9]{20,}' },
    @{ Name = "openai token"; Rx = 'sk-[A-Za-z0-9_\-]{20,}' },
    @{ Name = "github token"; Rx = 'gh[pousr]_[A-Za-z0-9]{20,}' },
    @{ Name = "slack token";  Rx = 'xox[baprs]-[A-Za-z0-9\-]{10,}' },
    @{ Name = "aws key";      Rx = 'AKIA[0-9A-Z]{16}' },
    @{ Name = "google key";   Rx = 'AIza[0-9A-Za-z_\-]{30,}' },
    @{ Name = "jwt";          Rx = 'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}' }
)
foreach ($t in $tokenShapes) {
    foreach ($m in [regex]::Matches($content, $t.Rx)) {
        $findings.Add($t.Name + ": " + (Mask $m.Value))
    }
}

# --- secret assignments (literal values only; secret_ref etc. allowed) ------
$secretRx = '(?i)\b(api[_-]?key|apikey|secret|token|passwd|password|access[_-]?key|verify[_-]?token|private[_-]?key)\b\s*[:=]\s*[''"]([^''"\r\n]{12,})[''"]'
foreach ($m in [regex]::Matches($content, $secretRx)) {
    $val = $m.Groups[2].Value
    if ($val -notmatch '^(secret_ref|vault:|\$\{|\{\{|<|MASKED|REDACTED|PLACEHOLDER|EXAMPLE)') {
        $findings.Add("secret assignment (" + $m.Groups[1].Value + "): " + (Mask $val))
    }
}

# --- raw user-id assignments -------------------------------------------------
$idRx = '(?i)\b(user[_-]?id|customer[_-]?id|guest[_-]?id|psid|buyer[_-]?id|member[_-]?id)\b[''"]?\s*[:=]\s*[''"]?(\d{6,})'
foreach ($m in [regex]::Matches($content, $idRx)) {
    $findings.Add("raw user-id assignment (" + $m.Groups[1].Value + "): " + (Mask $m.Groups[2].Value))
}

# --- emails ------------------------------------------------------------------
$emailRx = '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
foreach ($m in [regex]::Matches($content, $emailRx)) {
    $findings.Add("email: " + (Mask $m.Value))
}

# --- phones: TWO-PATTERN design (contiguous + grouped), VN prefix ------------
$phoneContiguousRx = '(?<![A-Za-z0-9])(?:\+?84|0)\d{8,10}(?![A-Za-z0-9])'
$phoneGroupedRx = '(?<![A-Za-z0-9])(?:\+?84[ .\-]?|0)\d{2,3}[ .\-]\d{3,4}[ .\-]\d{3,4}(?![A-Za-z0-9])(?![ .\-]\d)'
foreach ($m in [regex]::Matches($content, $phoneContiguousRx)) {
    $findings.Add("phone (contiguous): " + (Mask $m.Value))
}
foreach ($m in [regex]::Matches($content, $phoneGroupedRx)) {
    $findings.Add("phone (grouped): " + (Mask $m.Value))
}

if ($findings.Count -gt 0) { Fail $findings }
exit 0
