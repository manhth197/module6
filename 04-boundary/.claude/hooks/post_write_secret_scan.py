#!/usr/bin/env python3
# post_write_secret_scan.py -- PostToolUse hook (M6 build pack), Python fallback.
# Byte-identical copy shipped to every role folder; canonical master lives in
# setup/hooks-master/. Behavior must stay identical to post_write_secret_scan.ps1.
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
import sys, os, json, re

BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".docx", ".xlsx",
              ".pptx", ".exe", ".dll", ".ico", ".woff", ".woff2", ".ttf"}

TOKEN_SHAPES = [
    ("meta token",   r'EAA[A-Za-z0-9]{20,}'),
    ("openai token", r'sk-[A-Za-z0-9_\-]{20,}'),
    ("github token", r'gh[pousr]_[A-Za-z0-9]{20,}'),
    ("slack token",  r'xox[baprs]-[A-Za-z0-9\-]{10,}'),
    ("aws key",      r'AKIA[0-9A-Z]{16}'),
    ("google key",   r'AIza[0-9A-Za-z_\-]{30,}'),
    ("jwt",          r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}'),
]
SECRET_RX = (r'(?i)\b(api[_-]?key|apikey|secret|token|passwd|password|'
             r'access[_-]?key|verify[_-]?token|private[_-]?key)\b'
             r'\s*[:=]\s*[\'"]([^\'"\r\n]{12,})[\'"]')
SAFE_VALUE_RX = r'^(secret_ref|vault:|\$\{|\{\{|<|MASKED|REDACTED|PLACEHOLDER|EXAMPLE)'
ID_RX = (r'(?i)\b(user[_-]?id|customer[_-]?id|guest[_-]?id|psid|buyer[_-]?id|'
         r'member[_-]?id)\b[\'"]?\s*[:=]\s*[\'"]?(\d{6,})')
EMAIL_RX = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
PHONE_CONTIGUOUS_RX = r'(?<![A-Za-z0-9])(?:\+?84|0)\d{8,10}(?![A-Za-z0-9])'
PHONE_GROUPED_RX = (r'(?<![A-Za-z0-9])(?:\+?84[ .\-]?|0)\d{2,3}[ .\-]\d{3,4}'
                    r'[ .\-]\d{3,4}(?![A-Za-z0-9])(?![ .\-]\d)')

def mask(s):
    if len(s) <= 6:
        return "***"
    return s[:3] + "***" + s[-2:]

def main():
    raw = sys.stdin.read()
    if not raw or not raw.strip():
        sys.exit(0)
    try:
        payload = json.loads(raw)
    except Exception:
        sys.exit(0)
    tool_input = payload.get("tool_input") or {}
    file_path = ""
    if isinstance(tool_input, dict):
        file_path = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    if not file_path.strip() or not os.path.isfile(file_path):
        sys.exit(0)
    if os.path.splitext(file_path)[1].lower() in BINARY_EXT:
        sys.exit(0)
    try:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        sys.exit(0)
    if not content:
        sys.exit(0)

    findings = []
    for name, rx in TOKEN_SHAPES:
        for m in re.finditer(rx, content):
            findings.append(name + ": " + mask(m.group(0)))
    for m in re.finditer(SECRET_RX, content):
        if not re.match(SAFE_VALUE_RX, m.group(2)):
            findings.append("secret assignment (" + m.group(1) + "): " + mask(m.group(2)))
    for m in re.finditer(ID_RX, content):
        findings.append("raw user-id assignment (" + m.group(1) + "): " + mask(m.group(2)))
    for m in re.finditer(EMAIL_RX, content):
        findings.append("email: " + mask(m.group(0)))
    for m in re.finditer(PHONE_CONTIGUOUS_RX, content):
        findings.append("phone (contiguous): " + mask(m.group(0)))
    for m in re.finditer(PHONE_GROUPED_RX, content):
        findings.append("phone (grouped): " + mask(m.group(0)))

    if findings:
        sys.stderr.write("POST_WRITE_SECRET_SCAN FINDINGS:\n")
        for f in findings:
            sys.stderr.write(" - " + f + "\n")
        sys.exit(2)
    sys.exit(0)

if __name__ == "__main__":
    main()
