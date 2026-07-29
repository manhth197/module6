#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
secret_scan_repo.py — whole-repo secret/PII scan (same families as the hooks).

Scans every text file in the pack for token shapes, secret assignments with
literal values, raw user-id assignments, emails, and phones via the
TWO-PATTERN design: contiguous (?<![A-Za-z0-9])(?:\\+?84|0)\d{8,10}(?![A-Za-z0-9])
plus grouped (?:\\+?84[ .\-]?|0)\d{2,3}[ .\-]\d{3,4}[ .\-]\d{3,4} — never a
separator-tolerant bridging repetition.

Skips: binaries, .venv, .git, _source_snapshot (mirrors of scanned canon),
and the scanner/hook sources themselves ONLY for the "pattern definition"
lines (they contain regex literals, not live data) — implemented by skipping
files whose path is in SCANNER_SOURCES.

Exit 0 clean / exit 2 findings.
"""
import os, re, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))

BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".docx", ".xlsx",
              ".pptx", ".exe", ".dll", ".ico", ".woff", ".woff2", ".ttf", ".pyc"}
SKIP_DIRS = {".git", ".venv", "__pycache__", "_source_snapshot", "node_modules"}
SCANNER_SOURCES = {
    "setup/hooks-master/post_write_secret_scan.ps1",
    "setup/hooks-master/post_write_secret_scan.py",
    "setup/hooks-master/role_pre_tool_guard.ps1",
    "setup/hooks-master/role_pre_tool_guard.py",
    "scripts-win/_M6RunnerLib.ps1",
    "scripts/secret_scan_repo.py",
    "scripts/validate_gate_hardening.py",
    "scripts/scanner_battery_test.py",
}

TOKENS = [r'EAA[A-Za-z0-9]{20,}', r'sk-[A-Za-z0-9_\-]{20,}', r'gh[pousr]_[A-Za-z0-9]{20,}',
          r'xox[baprs]-[A-Za-z0-9\-]{10,}', r'AKIA[0-9A-Z]{16}', r'AIza[0-9A-Za-z_\-]{30,}',
          r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}']
SECRET = (r'(?i)\b(api[_-]?key|apikey|secret|token|passwd|password|access[_-]?key|'
          r'verify[_-]?token|private[_-]?key)\b\s*[:=]\s*[\'"]([^\'"\r\n]{12,})[\'"]')
SAFE = r'^(secret_ref|vault:|\$\{|\{\{|<|MASKED|REDACTED|PLACEHOLDER|EXAMPLE)'
IDRX = (r'(?i)\b(user[_-]?id|customer[_-]?id|guest[_-]?id|psid|buyer[_-]?id|'
        r'member[_-]?id)\b[\'"]?\s*[:=]\s*[\'"]?(\d{6,})')
EMAIL = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
PHONE1 = r'(?<![A-Za-z0-9])(?:\+?84|0)\d{8,10}(?![A-Za-z0-9])'
PHONE2 = r'(?<![A-Za-z0-9])(?:\+?84[ .\-]?|0)\d{2,3}[ .\-]\d{3,4}[ .\-]\d{3,4}(?![A-Za-z0-9])(?![ .\-]\d)'

def is_junction(path):
    try:
        return bool(os.stat(path, follow_symlinks=False).st_file_attributes & 0x400)
    except OSError:
        return False

def main():
    findings = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS
                       and not is_junction(os.path.join(dirpath, d))]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            if os.path.splitext(fn)[1].lower() in BINARY_EXT:
                continue
            if rel in SCANNER_SOURCES:
                continue
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    c = f.read()
            except OSError:
                continue
            for rx in TOKENS:
                if re.search(rx, c):
                    findings.append(rel + ": token shape " + rx[:12])
            for m in re.finditer(SECRET, c):
                if not re.match(SAFE, m.group(2)):
                    findings.append(rel + ": secret assignment " + m.group(1))
            for m in re.finditer(IDRX, c):
                findings.append(rel + ": raw user-id " + m.group(1))
            for m in re.finditer(EMAIL, c):
                findings.append(rel + ": email " + m.group(0)[:3] + "***")
            if re.search(PHONE1, c):
                findings.append(rel + ": phone (contiguous)")
            if re.search(PHONE2, c):
                findings.append(rel + ": phone (grouped)")
    if findings:
        print("secret_scan_repo: FAIL (%d findings)" % len(findings))
        for f_ in findings[:50]:
            print("  - " + f_)
        sys.exit(2)
    print("secret_scan_repo: PASS (repo clean)")

if __name__ == "__main__":
    main()
