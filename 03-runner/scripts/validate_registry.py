#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_registry.py — index <-> ledger <-> prompt-files consistency.

Checks:
  1. Index and ledger have identical columns, identical PromptId sets, and
     identical static fields (everything except Status/Note/UpdatedAt/Attempt).
  2. Every index File exists on disk; every prompt file on disk is in the
     index (1:1); filename order prefix equals the Order column.
  3. Every prompt XML parses (fenced block, single root), and its metadata
     matches the index row: prompt_id, order, role, agent (Role<->Agent
     pairing table), gate_level, requires_judge.
  4. HARD: <required_previous_prompts> equals CSV DependsOn for EVERY prompt.
  5. HARD: <required_outputs> equals CSV RequiredOutputs; evidence path equals
     ExpectedEvidence; judge output equals ExpectedJudge on judge rows.
  6. Dependency DAG: all deps exist, no forward references (dep Order strictly
     lower), judges are JUDGE_GATE + role JUDGE and vice versa.
  7. Slice prompts: smoke_ids equal the slice_definitions.json binding.
Exit 0 clean / exit 2 with findings.
"""
import csv, json, os, re, sys
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
INDEX = os.path.join(ROOT, "00-spec", "PROMPT_INDEX_LOCKED.csv")
LEDGER = os.path.join(ROOT, "04-artifacts", "state", "PROMPT_EXECUTION_LEDGER_LOCKED.csv")
PDIR = os.path.join(ROOT, "00-spec", "prompts")
SLICES = os.path.join(ROOT, "00-spec", "slices", "slice_definitions.json")

ROLE_AGENT = {
    "PM_ORCHESTRATOR": "m6-pm-orchestrator", "ANALYST_ARCHITECT": "m6-analyst-architect",
    "CODER": "m6-coder", "TESTER": "m6-tester", "BOUNDARY_ADVERSARY": "m6-boundary-adversary",
    "SECURITY_PII": "m6-security-pii", "JUDGE": "m6-judge",
}
STATIC = ["PromptId", "Order", "Role", "Agent", "Phase", "Slice", "Title", "File",
          "RequiresEvidence", "RequiresJudge", "GateLevel", "DependsOn",
          "ExpectedEvidence", "ExpectedJudge", "RequiredInputs", "RequiredOutputs"]

problems = []
def bad(msg):
    problems.append(msg)

def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        return r.fieldnames, list(r)

def main():
    icols, idx = read_csv(INDEX)
    lcols, led = read_csv(LEDGER)
    if icols != lcols:
        bad("index/ledger column mismatch")
    iby = {r["PromptId"]: r for r in idx}
    lby = {r["PromptId"]: r for r in led}
    if set(iby) != set(lby):
        bad("index/ledger PromptId sets differ: only-index=%s only-ledger=%s"
            % (sorted(set(iby) - set(lby))[:5], sorted(set(lby) - set(iby))[:5]))
    for pid in set(iby) & set(lby):
        for c in STATIC:
            if iby[pid].get(c, "") != lby[pid].get(c, ""):
                bad("%s: static field %s differs index vs ledger" % (pid, c))

    disk = sorted(f for f in os.listdir(PDIR) if f.endswith(".xml.md"))
    index_files = {os.path.basename(r["File"]) for r in idx}
    for f in disk:
        if f not in index_files:
            bad("prompt file on disk not in index: " + f)
    for r in idx:
        fn = os.path.basename(r["File"])
        p = os.path.join(PDIR, fn)
        if not os.path.isfile(p):
            bad("index File missing on disk: " + r["File"])
            continue
        m = re.match(r"^(\d{4})_", fn)
        if not m or int(m.group(1)) != int(r["Order"]):
            bad("%s: filename order prefix != Order %s" % (fn, r["Order"]))

    with open(SLICES, encoding="utf-8") as f:
        sdefs = {s["id"]: s for s in json.load(f)["slices"]}

    order_by_pid = {r["PromptId"]: int(r["Order"]) for r in idx}
    for r in idx:
        pid = r["PromptId"]
        p = os.path.join(ROOT, r["File"].replace("/", os.sep))
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            txt = f.read()
        m = re.search(r"```xml\n(.*?)\n```", txt, re.S)
        if not m:
            bad(pid + ": no fenced xml block")
            continue
        try:
            x = ET.fromstring(m.group(1))
        except ET.ParseError as e:
            bad(pid + ": XML parse error: " + str(e))
            continue
        if x.tag != "m6_claude_code_prompt":
            bad(pid + ": wrong root tag " + x.tag)
        md = x.find("metadata")
        def t(tag, el=md):
            e = el.find(tag)
            return (e.text or "").strip() if e is not None else ""
        if t("prompt_id") != pid:
            bad(pid + ": metadata prompt_id mismatch")
        if t("order") != r["Order"]:
            bad(pid + ": metadata order != index Order")
        if t("role") != r["Role"]:
            bad(pid + ": metadata role != index Role")
        if t("agent") != r["Agent"]:
            bad(pid + ": metadata agent != index Agent")
        if ROLE_AGENT.get(t("role")) != t("agent"):
            bad(pid + ": Role<->Agent pairing violation (%s / %s)" % (t("role"), t("agent")))
        if t("gate_level") != r["GateLevel"]:
            bad(pid + ": gate_level != index GateLevel")
        req_j = t("requires_judge") == "true"
        if req_j != (r["RequiresJudge"] == "true"):
            bad(pid + ": requires_judge != index RequiresJudge")
        if req_j != (r["GateLevel"] == "JUDGE_GATE"):
            bad(pid + ": requires_judge inconsistent with GateLevel")
        if req_j != (r["Role"] == "JUDGE"):
            bad(pid + ": JUDGE role/gate inconsistency")
        # HARD: entry gate == CSV DependsOn
        eg = x.find("entry_gate")
        rpp = (eg.find("required_previous_prompts").text or "").strip() if eg is not None else "?"
        if rpp != r["DependsOn"]:
            bad(pid + ": <required_previous_prompts> '%s' != CSV DependsOn '%s'" % (rpp, r["DependsOn"]))
        # HARD: outputs sync
        ro = x.find("required_outputs")
        outs = ";".join((e.text or "").strip() for e in ro.findall("file")) if ro is not None else ""
        if outs != r["RequiredOutputs"]:
            bad(pid + ": <required_outputs> != CSV RequiredOutputs")
        exp_ev = "04-artifacts/evidence/prompts/%s.json" % pid
        if r["ExpectedEvidence"] != exp_ev:
            bad(pid + ": ExpectedEvidence malformed")
        if exp_ev not in r["RequiredOutputs"].split(";"):
            bad(pid + ": evidence file not among RequiredOutputs")
        if req_j:
            jo = x.find("required_judge_output")
            jf_ = (jo.find("file").text or "").strip() if jo is not None else ""
            if jf_ != r["ExpectedJudge"]:
                bad(pid + ": <required_judge_output> != ExpectedJudge")
        # DAG
        for d in [d for d in r["DependsOn"].split(";") if d]:
            if d not in order_by_pid:
                bad(pid + ": unknown dependency " + d)
            elif order_by_pid[d] >= int(r["Order"]):
                bad(pid + ": forward/self reference to " + d)
        # slice smoke binding
        if r["Slice"] in sdefs:
            sm = x.find("smoke_ids")
            got = (sm.text or "").strip() if sm is not None else ""
            want = ";".join(sdefs[r["Slice"]]["smoke_ids"] + sdefs[r["Slice"]].get("proposed_smoke_ids", []))
            if got != want:
                bad(pid + ": smoke_ids '%s' != slice_definitions binding '%s'" % (got, want))

    if problems:
        print("validate_registry: FAIL (%d)" % len(problems))
        for p_ in problems[:60]:
            print("  - " + p_)
        sys.exit(2)
    print("validate_registry: PASS (%d prompts, index==ledger==disk, DAG ok, entry gates == DependsOn)" % len(idx))

if __name__ == "__main__":
    main()
