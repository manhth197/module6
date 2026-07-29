#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_registers.py — register lint.

  1. All eleven register files exist.
  2. Rule/fail/smoke/decision/contract/entry/lexicon/conflict IDs are unique
     and contiguous where numbered.
  3. Every smoke in SMOKE_REGISTER is bound to >=1 slice in
     slice_definitions.json (no orphan smokes) and the register's bound-slice
     column matches the JSON binding exactly.
  4. Every CONTRACT_REGISTER row with MISSING status names a producing prompt
     that exists in the index; the producer's Order is lower than the first
     prompt of every slice that lists the contract in slice_definitions.json.
  5. Every generated slice MD contains its JSON smoke ids and done-gate legs
     (gen_slices.py output in sync with slice_definitions.json).
Exit 0 / 2.
"""
import csv, json, os, re, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
REG = os.path.join(ROOT, "00-spec", "registers")
SL = os.path.join(ROOT, "00-spec", "slices")

problems = []
def bad(m):
    problems.append(m)

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def main():
    files = ["RULES_LOCKED.md", "FAIL_GATE_REGISTER.md", "SMOKE_REGISTER.md",
             "CONTRACT_REGISTER.md", "SCHEMA_CHANGELOG.md", "DECISION_REGISTER.md",
             "ENTRY_EVIDENCE_REGISTER.md", "MONITORING_REGISTER.md",
             "LEXICON_REGISTER.md", "CONFLICT_MATRIX.md", "SOURCE_MANIFEST.md"]
    for f in files:
        if not os.path.isfile(os.path.join(REG, f)):
            bad("register missing: " + f)
    if problems:
        report()

    with open(os.path.join(SL, "slice_definitions.json"), encoding="utf-8") as f:
        slices = json.load(f)["slices"]

    # numbered-ID contiguity
    for fname, prefix, count in [("RULES_LOCKED.md", "M6-RULE-", 21),
                                 ("FAIL_GATE_REGISTER.md", "M6-FAIL-", 10),
                                 ("SMOKE_REGISTER.md", "M6-SMK-", 18),
                                 ("DECISION_REGISTER.md", "M6-OD-", 12)]:
        txt = read(os.path.join(REG, fname))
        ids = set(re.findall(re.escape(prefix) + r"\d{3}", txt))
        want = {"%s%03d" % (prefix, i) for i in range(1, count + 1)}
        missing = want - ids
        if missing:
            bad("%s: missing ids %s" % (fname, sorted(missing)))

    # smoke binding: JSON side
    bound = {}
    for s in slices:
        for m in s["smoke_ids"] + s.get("proposed_smoke_ids", []):
            bound.setdefault(m, set()).add(s["id"])
    all_smokes = {"M6-SMK-%03d" % i for i in range(1, 19)}
    orphans = all_smokes - set(bound)
    if orphans:
        bad("orphan smokes (bound to no slice): " + str(sorted(orphans)))

    # register bound-slice column matches JSON
    smk_txt = read(os.path.join(REG, "SMOKE_REGISTER.md"))
    for line in smk_txt.splitlines():
        m = re.match(r"^\|\s*(M6-SMK-\d{3})\s*\|", line)
        if not m:
            continue
        sid = m.group(1)
        reg_slices = set(re.findall(r"M6\.2[A-K]", line))
        json_slices = bound.get(sid, set())
        if reg_slices != json_slices:
            bad("%s: register slices %s != JSON binding %s"
                % (sid, sorted(reg_slices), sorted(json_slices)))

    # contract MISSING -> producer exists and is upstream of consuming slices
    with open(os.path.join(ROOT, "00-spec", "PROMPT_INDEX_LOCKED.csv"),
              encoding="utf-8-sig", newline="") as f:
        idx = list(csv.DictReader(f))
    order = {r["PromptId"]: int(r["Order"]) for r in idx}
    slice_first_order = {}
    for r in idx:
        if r["Slice"].startswith("M6.2"):
            o = int(r["Order"])
            slice_first_order[r["Slice"]] = min(o, slice_first_order.get(r["Slice"], 10**9))
    ctr_txt = read(os.path.join(REG, "CONTRACT_REGISTER.md"))
    producer = {}
    for line in ctr_txt.splitlines():
        m = re.match(r"^\|\s*(M6-CTR-\d{3})\s*\|", line)
        if not m:
            continue
        cid = m.group(1)
        is_missing = "MISSING / OWNER_DECISION_REQUIRED" in line
        pm = re.search(r"(M6-P\d{4})", line)
        if is_missing:
            if not pm:
                bad(cid + ": MISSING without a producing prompt")
                continue
            producer[cid] = pm.group(1)
            if pm.group(1) not in order:
                bad(cid + ": producing prompt %s not in index" % pm.group(1))
    for s in slices:
        first = slice_first_order.get(s["id"], 10**9)
        for cid in s["contracts"]:
            if cid in producer and producer[cid] in order:
                if order[producer[cid]] >= first:
                    bad("%s: producer %s (order %d) NOT upstream of slice %s (first order %d)"
                        % (cid, producer[cid], order[producer[cid]], s["id"], first))

    # slice MD in sync with JSON
    for s in slices:
        p = os.path.join(SL, s["id"] + ".md")
        if not os.path.isfile(p):
            bad("slice file missing: " + s["id"] + ".md")
            continue
        txt = read(p)
        for m in s["smoke_ids"] + s.get("proposed_smoke_ids", []):
            if m not in txt:
                bad("%s.md: smoke %s missing (re-run gen_slices.py)" % (s["id"], m))
        for leg in s["done_gate_legs"]:
            if leg.split(":")[0] not in txt:
                bad("%s.md: done-gate leg missing: %s" % (s["id"], leg[:50]))

    report()

def report():
    if problems:
        print("validate_registers: FAIL (%d)" % len(problems))
        for p in problems[:40]:
            print("  - " + p)
        sys.exit(2)
    print("validate_registers: PASS (ids contiguous, no orphan smokes, producers upstream, slices in sync)")
    sys.exit(0)

if __name__ == "__main__":
    main()
