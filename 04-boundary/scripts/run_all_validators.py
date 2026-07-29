#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_all_validators.py — run the whole validator suite, print a result table.

--report-only: identical behavior (validators never modify anything anyway);
the flag exists so bootstrap prompts can state their intent explicitly.

NOTE: validate_release_clean is EXPECTED TO FAIL while a run is in flight;
it is reported separately and does not fail the suite unless --strict-clean.
Exit 0 if all core validators pass, else 2.
"""
import os, subprocess, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = ["validate_registry.py", "validate_roles.py", "validate_gate_hardening.py",
        "validate_registers.py", "validate_implementation_readiness.py",
        "validate_input_consumption.py", "validate_four_eyes.py",
        "secret_scan_repo.py", "scanner_battery_test.py"]
SOFT = ["validate_release_clean.py"]

def run(name):
    p = subprocess.run([sys.executable, os.path.join(HERE, name)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")

def main():
    strict = "--strict-clean" in sys.argv
    failed = []
    print("%-32s %s" % ("VALIDATOR", "RESULT"))
    print("-" * 44)
    outputs = {}
    for v in CORE + SOFT:
        code, out = run(v)
        outputs[v] = out
        soft = v in SOFT and not strict
        status = "PASS" if code == 0 else ("FAIL (in-flight OK)" if soft else "FAIL")
        if code != 0 and not soft:
            failed.append(v)
        print("%-32s %s" % (v, status))
    print("-" * 44)
    if failed:
        print("SUITE: FAIL — details:")
        for v in failed:
            print("\n### " + v)
            print(outputs[v])
        sys.exit(2)
    print("SUITE: PASS (release-clean reported informationally)")

if __name__ == "__main__":
    main()
