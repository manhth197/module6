#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_slices.py — render 00-spec/slices/M6.2X.md from slice_definitions.json.

slice_definitions.json is the SINGLE SOURCE for slice bindings (smokes, rules,
fail gates, contracts, dependencies). The markdown files are generated views;
never hand-edit them — edit the JSON and re-run. Validators cross-check the
two stay in sync.
"""
import json, io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SLICES_DIR = os.path.normpath(os.path.join(HERE, "..", "00-spec", "slices"))

def main():
    with open(os.path.join(SLICES_DIR, "slice_definitions.json"), encoding="utf-8") as f:
        data = json.load(f)
    for s in data["slices"]:
        lines = []
        a = lines.append
        a("<!-- GENERATED from slice_definitions.json by scripts/gen_slices.py — do not hand-edit -->")
        a("# Slice %s — %s" % (s["id"], s["name"]))
        a("")
        a("| Field | Value |")
        a("|---|---|")
        a("| ADS phase | %s |" % s["ads_phase"])
        a("| Depends on | %s |" % (s["depends_on"] or "— (first slice)"))
        a("| Doc scope | %s |" % s["scope_doc"])
        a("| Doc done gate | %s |" % s["done_gate_doc"])
        a("| Source | doc §20, %s |" % s["source_ref"])
        a("")
        a("## Objective")
        a("")
        a(s["objective"])
        a("")
        a("Production/scale state: `global_gateway_state=BLOCKED`, `production_flag=OFF`. "
          "This slice proves capability with evidence; it never flips any flag.")
        a("")
        a("Implementation target gate (pack hardening): `04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json` "
          "must be `LOCKED`, M6-OD-011 must be decided, and the target repository is a read-only convention "
          "reference. All implementation remains staged under `04-artifacts/impl/<slice>/` until an "
          "owner-controlled integration step.")
        a("")
        a("## In scope")
        a("")
        for x in s["in_scope"]:
            a("- " + x)
        a("")
        a("## Out of scope")
        a("")
        for x in s["out_of_scope"]:
            a("- " + x)
        a("")
        a("## Contract checklist (CONTRACT_REGISTER)")
        a("")
        for c in s["contracts"]:
            a("- [ ] %s — status per `00-spec/registers/CONTRACT_REGISTER.md`; if MISSING, its harmonization prompt must be PASS before this slice's entry gate" % c)
        a("")
        a("## Core smokes (SMOKE_REGISTER)")
        a("")
        for m in s["smoke_ids"]:
            a("- %s" % m)
        for m in s.get("proposed_smoke_ids", []):
            a("- %s (proposed — HARDENING, owner review)" % m)
        a("")
        if s.get("entry_evidence"):
            a("## Entry evidence required (ENTRY_EVIDENCE_REGISTER)")
            a("")
            for e in s["entry_evidence"]:
                a("- %s" % e)
            a("")
        a("## Rules / fail gates in scope")
        a("")
        a("- Rules: " + ", ".join(s["rules_in_scope"]))
        a("- Fail gates: " + ", ".join(s["fail_gates_in_scope"]))
        a("")
        a("## Exit gate checks (every leg of the doc done-gate column, itemized)")
        a("")
        n = 0
        for leg in s["done_gate_legs"]:
            n += 1
            a("%d. [ ] %s" % (n, leg))
        for m in s["smoke_ids"]:
            n += 1
            a("%d. [ ] Smoke %s executed with recorded result and evidence ref" % (n, m))
        for m in s.get("proposed_smoke_ids", []):
            n += 1
            a("%d. [ ] Proposed smoke %s executed OR explicitly waived by owner decision note" % (n, m))
        n += 1
        a("%d. [ ] All slice prompts have evidence JSON (schema-valid, no raw secret/PII, fail_gate_tripped=false)" % n)
        n += 1
        a("%d. [ ] Slice gate judge sign-off exists with verdict PASS" % n)
        n += 1
        a("%d. [ ] Rollback steps documented for every change this slice made" % n)
        a("")
        a("## Evidence paths")
        a("")
        a("- Prompt evidence: `04-artifacts/evidence/prompts/<PromptId>.json`")
        a("- Judge sign-off: `04-artifacts/evidence/judge/<JudgePromptId>_JUDGE_FINAL_SIGN_OFF.json`")
        a("- Slice artifacts: `04-artifacts/impl/%s/`, test reports under `04-artifacts/test-reports/%s/`" % (s["id"], s["id"]))
        a("")
        out = os.path.join(SLICES_DIR, s["id"] + ".md")
        with io.open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines))
        print("wrote", out)

if __name__ == "__main__":
    main()
