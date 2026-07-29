#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scanner_battery_test.py — prove the scanners with BOTH batteries, end-to-end.

PII battery (every sample MUST be caught) and trap battery (every sample MUST
pass clean), fired at:
  (a) the Python PostToolUse hook (setup/hooks-master/post_write_secret_scan.py)
  (b) the PowerShell PostToolUse hook (.ps1 twin)
  (c) the runner-gate scan (Test-M6SecretScan in scripts-win/_M6RunnerLib.ps1)

Samples are built by CONCATENATION so this source file itself never contains
a raw phone/email/token (the repo scan stays clean).

Writes samples to a temp dir OUTSIDE the pack. Exit 0 all green / 2 failures.
"""
import json, os, subprocess, sys, tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
HOOK_PY = os.path.join(ROOT, "setup", "hooks-master", "post_write_secret_scan.py")
HOOK_PS = os.path.join(ROOT, "setup", "hooks-master", "post_write_secret_scan.ps1")
LIB_PS = os.path.join(ROOT, "scripts-win", "_M6RunnerLib.ps1")

J = "".join
PII = [
    ("meta token",        J(["EAA", "Bwz", "LixnjY", "BAOZ", "Cqx1", "Vlt0", "9abcd"])),
    ("secret assignment", J(["api", "_key = '", "9f8e7d6c5b4a", "3210fedc", "'"])),
    ("user-id assign",    J(["customer", "_id: \"", "98765", "4321", "\""])),
    ("phone contiguous",  J(["lien he ", "09", "12", "345", "678", " nhe"])),
    ("phone +84 contig",  J(["+", "84", "912", "345", "678"])),
    ("phone spaced",      J(["+", "84 ", "91 ", "234 ", "5678"])),
    ("phone dotted",      J(["0", "912", ".", "345", ".", "678"])),
    ("phone dashed",      J(["0", "91", "-", "234", "-", "5678"])),
    ("email",             J(["lan", ".ngu", "yen", "@", "exam", "ple.com"])),
    ("id-in-JSON",        J(['{"customer', '_id": "', "12345", "6789", '"}'])),
]
TRAP = [
    ("ISO date",         "deadline 2026-07-02 and 2025-12-31"),
    ("ISO datetime",     "at 2026-07-02T09:15:30 then 2026-07-02 09:15:30"),
    ("US date",          "07/02/2026 and 12/31/2025"),
    ("ID ranges",        "ADS-P0-001..015 and M6-SMK-001..018 and X-001..026"),
    ("timestamps",       "epoch 1782986475737 build 20260702173057"),
    ("IP addresses",     "hosts 192.168.1.10 and 10.0.84.123 and 172.16.0.1"),
    ("version strings",  "v1.2.3 and 5.1.22631 and 3.14.5"),
    ("dense number run", "counts: 0 100 2000 30000 totals 84 91 234 sum 4000 5000 6000"),
    ("masked email",     "contact u***@example.com and lan***om"),
    ("masked phone",     "so dien thoai 091***78 va +84***678"),
    ("rule id ranges",   "rules M6-RULE-001..020 and M6-FAIL-001..010"),
]

def run_hook_py(path):
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": path}})
    p = subprocess.run([sys.executable, HOOK_PY], input=payload.encode(), capture_output=True)
    return p.returncode

def run_hook_ps(path):
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": path}})
    p = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-File", HOOK_PS], input=payload.encode(), capture_output=True)
    return p.returncode

def run_gate_ps(path):
    cmd = (". '%s'; $f=@(); if (Test-M6SecretScan '%s' ([ref]$f)) { exit 0 } else { exit 2 }"
           % (LIB_PS, path))
    p = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-Command", cmd], capture_output=True)
    return p.returncode

def main():
    tmp = tempfile.mkdtemp(prefix="m6battery_")
    failures = 0
    print("=== PII battery (must ALL be caught: expect exit 2) ===")
    for name, sample in PII:
        f = os.path.join(tmp, "pii.txt")
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(sample + "\n")
        r = (run_hook_py(f), run_hook_ps(f), run_gate_ps(f))
        ok = all(x == 2 for x in r)
        if not ok:
            failures += 1
        print("%s  %-18s py=%d ps=%d gate=%d" % ("PASS" if ok else "FAIL", name, *r))
    print("=== Trap battery (must ALL pass clean: expect exit 0) ===")
    for name, sample in TRAP:
        f = os.path.join(tmp, "trap.txt")
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(sample + "\n")
        r = (run_hook_py(f), run_hook_ps(f), run_gate_ps(f))
        ok = all(x == 0 for x in r)
        if not ok:
            failures += 1
        print("%s  %-18s py=%d ps=%d gate=%d" % ("PASS" if ok else "FAIL", name, *r))
    if failures:
        print("scanner_battery_test: FAIL (%d)" % failures)
        sys.exit(2)
    print("scanner_battery_test: PASS (all PII caught, all traps clean, 3 scanners agree)")

if __name__ == "__main__":
    main()
