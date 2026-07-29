#!/usr/bin/env python3
# stop_role_evidence_guard.py -- Stop hook (M6 build pack), Python fallback.
# Byte-identical copy shipped to every role folder; canonical master lives in
# setup/hooks-master/. Behavior must stay identical to stop_role_evidence_guard.ps1.
#
# Blocks "done" (exit 2) while a prompt is marked RUNNING in the execution
# ledger for THIS role but its evidence file does not exist yet. Matches both
# normal and critic prompt ids: M6-P(?:C)?\d{4}.
# stop_hook_active=true (already continuing due to a prior block) => allow.
import sys, os, json, re, csv, io

def block(reason):
    sys.stderr.write("STOP_ROLE_EVIDENCE_GUARD BLOCK: " + reason + "\n")
    sys.exit(2)

def main():
    raw = sys.stdin.read()
    payload = None
    try:
        payload = json.loads(raw)
    except Exception:
        payload = None
    if isinstance(payload, dict) and payload.get("stop_hook_active"):
        sys.exit(0)

    hook_dir = os.path.dirname(os.path.abspath(__file__))
    role_root = os.path.dirname(os.path.dirname(hook_dir))
    policy_path = os.path.join(role_root, ".claude", "role_policy.json")
    if not os.path.isfile(policy_path):
        block("role_policy.json missing (fail-closed)")
    try:
        with open(policy_path, encoding="utf-8") as f:
            policy = json.load(f)
    except Exception:
        block("role_policy.json unparseable (fail-closed)")
    # role_name may be comma-separated when one folder hosts several ledger
    # roles (the pack root hosts PM_ORCHESTRATOR and JUDGE sessions).
    role_name_raw = str(policy.get("role_name") or "")
    if not role_name_raw.strip():
        block("role_name missing in role_policy.json (fail-closed)")
    role_names = [r.strip() for r in role_name_raw.split(",") if r.strip()]

    ledger_path = os.path.join(role_root, "04-artifacts", "state",
                               "PROMPT_EXECUTION_LEDGER_LOCKED.csv")
    if not os.path.isfile(ledger_path):
        block("execution ledger not found (fail-closed): "
              "04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv")
    try:
        with open(ledger_path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except Exception:
        block("execution ledger unreadable (fail-closed)")

    prompt_id_rx = re.compile(r"^M6-P(?:C)?\d{4}$")
    missing = []
    for row in rows:
        if (row.get("Status") or "") != "RUNNING":
            continue
        if (row.get("Role") or "") not in role_names:
            continue
        pid = row.get("PromptId") or ""
        if not prompt_id_rx.match(pid):
            continue
        evidence = os.path.join(role_root, "04-artifacts", "evidence",
                                "prompts", pid + ".json")
        if not os.path.isfile(evidence):
            missing.append(pid)

    if missing:
        block("active prompt(s) without evidence file: " + ", ".join(missing) +
              ". Write 04-artifacts/evidence/prompts/<PromptId>.json before "
              "finishing. Do not mark your own work PASS; only write evidence.")
    sys.exit(0)

if __name__ == "__main__":
    main()
