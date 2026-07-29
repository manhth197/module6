#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_release_clean.py — is the pack in pristine pre-run state?

PASS means: no evidence files, no handoff files, ledger all TODO / Attempt 0,
CURRENT_STATE_LOCKED.json shows BLOCKED / OFF.

*** EXPECTED TO FAIL WHILE A RUN IS IN FLIGHT — that is by design, not a bug.
Use it before handover/re-zip and after a state reset only. ***
Exit 0 / 2.
"""
import csv, json, os, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))

problems = []
def bad(m):
    problems.append(m)

def main():
    for sub in ["prompts", "judge", "entry"]:
        d = os.path.join(ROOT, "04-artifacts", "evidence", sub)
        if os.path.isdir(d):
            leftover = [f for f in os.listdir(d) if f != ".gitkeep"]
            if leftover:
                bad("evidence/%s not empty (%d files) — in-flight run?" % (sub, len(leftover)))
    handoff = os.path.join(ROOT, "03-runner", "handoff")
    if os.path.isdir(handoff) and os.listdir(handoff):
        bad("03-runner/handoff not empty — in-flight run?")
    for extra in ["_NEXT_PROMPT_LOCKED.md"]:
        if os.path.isfile(os.path.join(ROOT, extra)):
            bad(extra + " present — in-flight run?")

    ledger = os.path.join(ROOT, "04-artifacts", "state", "PROMPT_EXECUTION_LEDGER_LOCKED.csv")
    with open(ledger, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["Status"] != "TODO":
                bad("ledger %s status=%s (not TODO)" % (row["PromptId"], row["Status"]))
            if row["Attempt"] not in ("0", ""):
                bad("ledger %s attempt=%s (not 0)" % (row["PromptId"], row["Attempt"]))

    state = os.path.join(ROOT, "04-artifacts", "state", "CURRENT_STATE_LOCKED.json")
    with open(state, encoding="utf-8") as f:
        st = json.load(f)
    if st.get("global_gateway_state") != "BLOCKED":
        bad("global_gateway_state != BLOCKED")
    if st.get("production_flag") != "OFF":
        bad("production_flag != OFF")

    if problems:
        print("validate_release_clean: FAIL (%d) — EXPECTED while a run is in flight" % len(problems))
        for p in problems[:20]:
            print("  - " + p)
        sys.exit(2)
    print("validate_release_clean: PASS (pristine pre-run state, BLOCKED/OFF)")

if __name__ == "__main__":
    main()
