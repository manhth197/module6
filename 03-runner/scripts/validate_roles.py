#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_roles.py — role-isolation layer checks.

  1. Every role folder has CLAUDE.md, .claude/role_policy.json,
     .claude/settings.json wiring the three hook events to the .ps1 hooks,
     and all six hook files.
  2. ALL hook copies are byte-identical to setup/hooks-master AND across roles.
  3. Every policy denies 04-artifacts/state (the ledger is operator-only) and
     00-spec; no policy allows writing 00-spec or state.
  4. CLAUDE.md agrees with role_policy.json exactly (allowed + denied lists).
  5. 05-judge is output-only: no CLAUDE.md, no .claude, no venv.
  6. No .docx anywhere inside the pack.
  7. Snapshot sync: each role's _source_snapshot/SOURCE_SNAPSHOT_MANIFEST.json
     matches the CURRENT canonical 00-spec (sha256 per file) — stale snapshots
     mean Repair-M6RoleJunctions.ps1 must be re-run.
Exit 0 / 2.
"""
import hashlib, json, os, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
MASTER = os.path.join(ROOT, "setup", "hooks-master")
HOOKS = ["role_pre_tool_guard.ps1", "role_pre_tool_guard.py",
         "post_write_secret_scan.ps1", "post_write_secret_scan.py",
         "stop_role_evidence_guard.ps1", "stop_role_evidence_guard.py"]
ROLES = ["00-analyst", "01-coder", "02-tester", "03-runner", "04-boundary", "06-security", "."]

problems = []
def bad(m):
    problems.append(m)

def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def main():
    master_hash = {h: sha(os.path.join(MASTER, h)) for h in HOOKS}

    for role in ROLES:
        base = os.path.normpath(os.path.join(ROOT, role))
        tag = role if role != "." else "(root)"
        if not os.path.isfile(os.path.join(base, "CLAUDE.md")):
            bad(tag + ": CLAUDE.md missing"); continue
        pol_p = os.path.join(base, ".claude", "role_policy.json")
        set_p = os.path.join(base, ".claude", "settings.json")
        if not os.path.isfile(pol_p):
            bad(tag + ": role_policy.json missing"); continue
        if not os.path.isfile(set_p):
            bad(tag + ": settings.json missing"); continue
        with open(pol_p, encoding="utf-8") as f:
            pol = json.load(f)
        with open(set_p, encoding="utf-8") as f:
            st = json.load(f)
        hooks_cfg = st.get("hooks", {})
        for ev, hookname in [("PreToolUse", "role_pre_tool_guard.ps1"),
                             ("PostToolUse", "post_write_secret_scan.ps1"),
                             ("Stop", "stop_role_evidence_guard.ps1")]:
            entries = hooks_cfg.get(ev) or []
            cmds = [h.get("command", "") for e in entries for h in e.get("hooks", [])]
            if not any(hookname in c for c in cmds):
                bad(tag + ": settings.json does not wire %s -> %s" % (ev, hookname))
        for h in HOOKS:
            hp = os.path.join(base, ".claude", "hooks", h)
            if not os.path.isfile(hp):
                bad(tag + ": hook missing " + h)
            elif sha(hp) != master_hash[h]:
                bad(tag + ": hook %s NOT byte-identical to master" % h)
        deny = [d.replace("\\", "/") for d in pol.get("deny_write_roots", [])]
        allow = [a.replace("\\", "/") for a in pol.get("allowed_write_roots", [])]
        if "04-artifacts/state" not in deny:
            bad(tag + ": policy does not deny 04-artifacts/state")
        if "00-spec" not in deny:
            bad(tag + ": policy does not deny 00-spec")
        for a in allow:
            if a == "00-spec" or a.startswith("00-spec/") or a.startswith("04-artifacts/state"):
                bad(tag + ": policy ALLOWS forbidden root " + a)
        # CLAUDE.md == policy
        with open(os.path.join(base, "CLAUDE.md"), encoding="utf-8") as f:
            cm = f.read()
        for a in allow:
            if ("- `%s/`" % a) not in cm:
                bad(tag + ": CLAUDE.md missing allowed root `%s/`" % a)
        for d in deny:
            if ("- `%s`" % d) not in cm:
                bad(tag + ": CLAUDE.md missing denied root `%s`" % d)

    # 05-judge output-only
    judge = os.path.join(ROOT, "05-judge")
    if not os.path.isdir(judge):
        bad("05-judge folder missing")
    else:
        for forbidden in ["CLAUDE.md", ".claude", ".venv"]:
            if os.path.exists(os.path.join(judge, forbidden)):
                bad("05-judge must be output-only; found " + forbidden)

    # no .docx inside the pack (skip junction-linked duplicates via role dirs;
    # walk real paths only)
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if not os.path.islink(os.path.join(dirpath, d))
                       and not _is_junction(os.path.join(dirpath, d))
                       and d != ".venv"]
        for fn in filenames:
            if fn.lower().endswith(".docx"):
                bad("forbidden .docx inside pack: " + os.path.join(dirpath, fn))

    # snapshot sync
    canon = {}
    spec = os.path.join(ROOT, "00-spec")
    for dirpath, dirnames, filenames in os.walk(spec):
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, spec).replace("\\", "/")
            canon[rel] = sha(p)
    for role in [r for r in ROLES if r != "."]:
        mf = os.path.join(ROOT, role, "_source_snapshot", "SOURCE_SNAPSHOT_MANIFEST.json")
        if not os.path.isfile(mf):
            bad(role + ": SOURCE_SNAPSHOT_MANIFEST.json missing (run Initialize/Repair)")
            continue
        with open(mf, encoding="utf-8") as f:
            man = json.load(f).get("files", {})
        if man != canon:
            missing = set(canon) - set(man)
            extra = set(man) - set(canon)
            changed = {k for k in set(man) & set(canon) if man[k] != canon[k]}
            bad("%s: snapshot STALE vs canonical 00-spec (missing=%d extra=%d changed=%d) -> run Repair-M6RoleJunctions.ps1"
                % (role, len(missing), len(extra), len(changed)))

    if problems:
        print("validate_roles: FAIL (%d)" % len(problems))
        for p in problems[:40]:
            print("  - " + p)
        sys.exit(2)
    print("validate_roles: PASS (7 role trees, hooks byte-identical, policies fail-closed, snapshots in sync, no .docx)")

def _is_junction(path):
    try:
        return bool(os.stat(path, follow_symlinks=False).st_file_attributes & 0x400)
    except OSError:
        return False

if __name__ == "__main__":
    main()
