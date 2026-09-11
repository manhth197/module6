import json, os
root = r"D:\M6\Module6-workspace"
signoff = os.path.join(root, "04-artifacts", "evidence", "judge", "M6-P2709_JUDGE_FINAL_SIGN_OFF.json")
ev = os.path.join(root, "04-artifacts", "evidence", "prompts", "M6-P2709.json")

def check(path, label, required_keys):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    print(f"[{label}] JSON parse OK")
    missing = [k for k in required_keys if k not in d]
    print(f"[{label}] missing required keys: {missing}")
    print(f"[{label}] prompt_id={d.get('prompt_id')}")
    print(f"[{label}] verdict/status={d.get('verdict', d.get('status'))}")
    print(f"[{label}] fail_gate_tripped={d.get('fail_gate_tripped')}")
    print(f"[{label}] open_blockers={d.get('open_blockers')}")
    return d

so = check(signoff, "SIGNOFF", ["prompt_id","verdict","fail_gate_tripped","open_blockers","evidence_reviewed","required_inputs_reviewed","required_outputs_reviewed","judge_notes"])
ed = check(ev, "EVIDENCE", ["prompt_id","status","summary","files_read","files_changed","commands_run","evidence_refs","open_blockers","fail_gate_tripped","fail_gate_lines","next_recommended_action"])

def paths_exist(d, key, label):
    bad = []
    for p in d.get(key, []):
        full = os.path.join(root, p.replace("/", os.sep))
        if not os.path.exists(full):
            bad.append(p)
    print(f"[{label}] {key}: {len(d.get(key,[]))} paths, MISSING={bad}")
    return bad

b1 = paths_exist(so, "evidence_reviewed", "SIGNOFF")
b2 = paths_exist(so, "required_inputs_reviewed", "SIGNOFF")
b3 = paths_exist(so, "required_outputs_reviewed", "SIGNOFF")
b4 = paths_exist(ed, "evidence_refs", "EVIDENCE")
b5 = paths_exist(ed, "files_read", "EVIDENCE")

allbad = b1+b2+b3+b4+b5
print("=== ALL PATHS EXIST ===" if not allbad else f"=== MISSING PATHS: {allbad} ===")
ok = (so["verdict"]=="PASS" and ed["status"]=="PASS" and so["fail_gate_tripped"] is False and ed["fail_gate_tripped"] is False and not so["open_blockers"] and not ed["open_blockers"])
print("=== verdict PASS, status PASS, fail_gate false, blockers empty ===" if ok else "=== CHECK FAILED ===")
