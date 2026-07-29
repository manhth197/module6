#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-closed readiness checks for the Claude Code operating flow.

Stages:
  bootstrap         local role environment is ready to start M6-P0000
  slice-a-entry     prerequisites exist to run the M6.2A entry-gate judge
  slice-a-implement prerequisites exist to run the first coder implement prompt

This validator never creates evidence and never converts an OPEN decision into
a decision. Exit 0 = ready for the requested stage; exit 2 = exact blockers.
"""
import argparse
import csv
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
ROLES = [".", "00-analyst", "01-coder", "02-tester", "03-runner", "04-boundary", "06-security"]
TARGET = os.path.join(ROOT, "04-artifacts", "state", "IMPLEMENTATION_TARGET_LOCKED.json")
LEDGER = os.path.join(ROOT, "04-artifacts", "state", "PROMPT_EXECUTION_LEDGER_LOCKED.csv")


def table_rows(path, prefix):
    rows = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("| " + prefix):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if cells:
                    rows[cells[0]] = cells
    return rows


def ledger_statuses():
    with open(LEDGER, encoding="utf-8-sig", newline="") as f:
        return {r["PromptId"]: r["Status"] for r in csv.DictReader(f)}


def validate_entry_file(entry_id, problems):
    path = os.path.join(ROOT, "04-artifacts", "evidence", "entry", entry_id + ".json")
    if not os.path.isfile(path):
        problems.append("missing standardized entry evidence: " + os.path.relpath(path, ROOT))
        return
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        problems.append("entry evidence %s is invalid JSON: %s" % (entry_id, exc))
        return
    if data.get("schema_version") != "GFD-M6-ENTRY-EVIDENCE-001":
        problems.append(entry_id + ": schema_version must be GFD-M6-ENTRY-EVIDENCE-001")
    if data.get("entry_id") != entry_id:
        problems.append(entry_id + ": entry_id mismatch")
    if data.get("status") != "READY_FOR_JUDGE":
        problems.append(entry_id + ": status must be READY_FOR_JUDGE (not self-certified PASS)")
    for field in ("source_module", "supplied_by", "captured_at"):
        if not str(data.get(field, "")).strip():
            problems.append(entry_id + ": missing " + field)
    if not isinstance(data.get("evidence_refs"), list) or not data["evidence_refs"]:
        problems.append(entry_id + ": evidence_refs must be a non-empty list")
    if not isinstance(data.get("assertions"), list) or not data["assertions"]:
        problems.append(entry_id + ": assertions must be a non-empty list")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("bootstrap", "slice-a-entry", "slice-a-implement"),
                        default="bootstrap")
    args = parser.parse_args()
    problems = []

    for role in ROLES:
        py = os.path.join(ROOT, role, ".venv", "Scripts", "python.exe")
        if not os.path.isfile(py):
            problems.append("missing role venv: " + os.path.relpath(py, ROOT))
    if os.path.exists(os.path.join(ROOT, "05-judge", ".venv")):
        problems.append("05-judge must not have a venv")

    state_path = os.path.join(ROOT, "04-artifacts", "state", "CURRENT_STATE_LOCKED.json")
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)
    if state.get("global_gateway_state") != "BLOCKED" or state.get("production_flag") != "OFF":
        problems.append("global safety state must remain BLOCKED/OFF")

    if args.stage != "bootstrap":
        try:
            with open(TARGET, encoding="utf-8") as f:
                target = json.load(f)
        except Exception as exc:
            target = {}
            problems.append("implementation target manifest missing/invalid: %s" % exc)
        if target.get("status") != "LOCKED":
            problems.append("implementation target status is not LOCKED")
        target_path = str(target.get("repository", {}).get("absolute_path", "")).strip()
        if not target_path or not os.path.isdir(target_path):
            problems.append("implementation target repository path is missing or inaccessible")
        stack = target.get("stack") or {}
        for field in ("language", "test_command"):
            if not str(stack.get(field, "")).strip():
                problems.append("implementation target stack missing " + field)
        if target.get("owner_decision", {}).get("id") != "M6-OD-011":
            problems.append("implementation target must bind owner decision M6-OD-011")

        decisions = table_rows(os.path.join(ROOT, "00-spec", "registers", "DECISION_REGISTER.md"), "M6-OD-")
        od = decisions.get("M6-OD-011", [])
        if len(od) < 4 or od[3].upper().startswith("OPEN"):
            problems.append("M6-OD-011 remains OPEN in DECISION_REGISTER")

        contracts = table_rows(os.path.join(ROOT, "00-spec", "registers", "CONTRACT_REGISTER.md"), "M6-CTR-")
        for cid in ("M6-CTR-003", "M6-CTR-004", "M6-CTR-005", "M6-CTR-006"):
            row = contracts.get(cid, [])
            if len(row) < 4 or "MISSING" in row[3].upper():
                problems.append(cid + " is not DRAFT_LOCKED")

        for eid in ("M6-ENTRY-001", "M6-ENTRY-002", "M6-ENTRY-003"):
            validate_entry_file(eid, problems)

        statuses = ledger_statuses()
        if statuses.get("M6-P0715") != "SIGNED":
            problems.append("M6-P0715 harmonization judge is not SIGNED")
        if args.stage == "slice-a-implement":
            if statuses.get("M6-P1000") != "SIGNED":
                problems.append("M6-P1000 slice entry judge is not SIGNED")
            if statuses.get("M6-P1001") != "PASS":
                problems.append("M6-P1001 coder plan is not PASS")

    if problems:
        print("validate_implementation_readiness: BLOCKED stage=%s (%d)" % (args.stage, len(problems)))
        for item in problems:
            print("  - " + item)
        sys.exit(2)
    print("validate_implementation_readiness: PASS stage=%s" % args.stage)


if __name__ == "__main__":
    main()
