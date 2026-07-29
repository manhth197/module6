#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_gate_hardening.py — the gate cannot be softened silently.

  1. Set-PromptStatusLocked.ps1: ValidateSet EXCLUDES PASS and SIGNED;
     SKIP_APPROVED note guard present; JUDGE_GATE skip refusal present.
  2. Mark-PromptPassLocked.ps1: CALLS Check-PromptGateLocked.ps1 and throws on
     non-zero exit.
  3. Check-PromptGateLocked.ps1 contains all hardening tokens: dependency
     check, prompt_id match, fail_gate_tripped, open_blockers, evidence_refs
     existence, files_changed allowlist, test_results/commands_run for test
     mode, judge sign-off validation (verdict, evidence_reviewed), secret scan.
  4. ALL hook copies hash-identical across roles and to master.
  5. Every scanner (hooks .ps1/.py + runner lib) contains the TWO-PATTERN
     phone design and does NOT contain the old bridging separator-tolerant
     form like [0-9 .\\-]{7,12}.
Exit 0 / 2.
"""
import hashlib, os, re, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
SW = os.path.join(ROOT, "scripts-win")
MASTER = os.path.join(ROOT, "setup", "hooks-master")

problems = []
def bad(m):
    problems.append(m)

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def main():
    # 1. Set-PromptStatusLocked
    sps = read(os.path.join(SW, "Set-PromptStatusLocked.ps1"))
    m = re.search(r"ValidateSet\(([^)]*)\)", sps)
    if not m:
        bad("Set-PromptStatusLocked: no ValidateSet")
    else:
        vals = m.group(1)
        if "'PASS'" in vals or "'SIGNED'" in vals:
            bad("Set-PromptStatusLocked: ValidateSet must EXCLUDE PASS/SIGNED")
        for need in ["'TODO'", "'RUNNING'", "'BLOCKED'", "'FAIL'", "'SKIPPED'"]:
            if need not in vals:
                bad("Set-PromptStatusLocked: ValidateSet missing " + need)
    if "SKIP_APPROVED:" not in sps:
        bad("Set-PromptStatusLocked: SKIP_APPROVED note guard missing")
    if "JUDGE_GATE" not in sps:
        bad("Set-PromptStatusLocked: JUDGE_GATE skip refusal missing")

    # 2. Mark calls Check
    mark = read(os.path.join(SW, "Mark-PromptPassLocked.ps1"))
    if "Check-PromptGateLocked.ps1" not in mark:
        bad("Mark-PromptPassLocked: does not call Check-PromptGateLocked")
    if "LASTEXITCODE" not in mark or "throw" not in mark:
        bad("Mark-PromptPassLocked: does not throw on gate failure")

    # 3. Check hardening tokens
    check = read(os.path.join(SW, "Check-PromptGateLocked.ps1"))
    for token in ["Test-M6DepsPassed", "prompt_id mismatch", "fail_gate_tripped",
                  "open_blockers", "evidence_refs", "files_changed",
                  "test_results", "commands_run", "evidence_reviewed",
                  "verdict", "Test-M6SecretScan", "RequiredInputs", "RequiredOutputs"]:
        if token not in check:
            bad("Check-PromptGateLocked: hardening token missing: " + token)

    # 4. hook hash identity
    hooks = ["role_pre_tool_guard.ps1", "role_pre_tool_guard.py",
             "post_write_secret_scan.ps1", "post_write_secret_scan.py",
             "stop_role_evidence_guard.ps1", "stop_role_evidence_guard.py"]
    roles = ["00-analyst", "01-coder", "02-tester", "03-runner", "04-boundary",
             "06-security", "."]
    for h in hooks:
        with open(os.path.join(MASTER, h), "rb") as f:
            want = hashlib.sha256(f.read()).hexdigest()
        for r in roles:
            p = os.path.normpath(os.path.join(ROOT, r, ".claude", "hooks", h))
            if not os.path.isfile(p):
                bad("hook copy missing: %s in %s" % (h, r))
                continue
            with open(p, "rb") as f:
                got = hashlib.sha256(f.read()).hexdigest()
            if got != want:
                bad("hook copy differs from master: %s in %s" % (h, r))

    # 5. scanners: two-pattern phone present, bridging form absent
    scanners = [os.path.join(MASTER, "post_write_secret_scan.ps1"),
                os.path.join(MASTER, "post_write_secret_scan.py"),
                os.path.join(SW, "_M6RunnerLib.ps1"),
                os.path.join(HERE, "secret_scan_repo.py")]
    contiguous = r"(?<![A-Za-z0-9])(?:\+?84|0)\d{8,10}(?![A-Za-z0-9])"
    # the grouped pattern may be split across source lines (python string
    # concatenation), so check its two halves independently
    grouped_head = r"\d{2,3}[ .\-]\d{3,4}"
    grouped_tail = r"[ .\-]\d{3,4}(?![A-Za-z0-9])(?![ .\-]\d)"
    bridging = re.compile(r"\[0-9[^\]]*\]\s*\{\s*\d+\s*,\s*\d+\s*\}")
    for sp in scanners:
        if not os.path.isfile(sp):
            bad("scanner file missing: " + sp)
            continue
        txt = read(sp)
        if contiguous not in txt:
            bad(os.path.basename(sp) + ": contiguous phone pattern missing")
        if grouped_head not in txt or grouped_tail not in txt:
            bad(os.path.basename(sp) + ": grouped phone pattern missing")
        if bridging.search(txt):
            bad(os.path.basename(sp) + ": FORBIDDEN bridging phone form present")

    if problems:
        print("validate_gate_hardening: FAIL (%d)" % len(problems))
        for p in problems[:40]:
            print("  - " + p)
        sys.exit(2)
    print("validate_gate_hardening: PASS (gate unsoftened, hooks identical, two-pattern scanners)")

if __name__ == "__main__":
    main()
