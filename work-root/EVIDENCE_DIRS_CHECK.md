# EVIDENCE_DIRS_CHECK — marker note

**Prompt**: M6-P0006 (EVIDENCE_DIRS_CHECK) · Role: PM_ORCHESTRATOR · Mode: analysis_only
**Recorded**: 2026-07-20 · Read-only existence check; writability determined from
`role_policy.json` (NOT by attempting writes). This marker lives in `work-root/`,
not in any evidence dir, per task.

## Evidence directories

| Directory | Exists | Items | Writable by this role (PM_ORCHESTRATOR,JUDGE)? |
|---|---|---|---|
| `04-artifacts/evidence/prompts/` | yes | 7 (6 evidence JSONs P0000–P0005 + `.gitkeep`) | **YES** — in `allowed_write_roots` |
| `04-artifacts/evidence/judge/` | yes | 1 (`.gitkeep`) | **YES** — in `allowed_write_roots` |
| `04-artifacts/evidence/entry/` | yes | 1 (`.gitkeep`) | **NO** — not in this role's allowlist |

Parent `04-artifacts/evidence/` exists.

## Writability per policy

`.claude/role_policy.json` `allowed_write_roots` for this role:
`work-root`, `04-artifacts/evidence/prompts`, `04-artifacts/evidence/judge`,
`05-judge`. Rule (pack CLAUDE.md): "everything not in the allowed list is denied
for Write/Edit."

- `evidence/prompts/` and `evidence/judge/` are in the allowlist → writable by
  this role. (prompts/ writability is demonstrated live: this prompt's evidence
  JSON is written there.)
- `evidence/entry/` is **not** in this role's allowlist. Per
  `registry/ROLE_REGISTRY.json`, it is not in **any** executor role's
  `allowed_write_roots` either → it is operator-managed (entry evidence
  `M6-ENTRY-00X.json` is produced/placed under an operator-controlled process,
  analogous to `04-artifacts/state`). Not writable by an executor session.
  This is a policy fact, not a defect: the acceptance check is directory
  existence, and all three exist.

## Verdict

- Acceptance check "all three evidence dirs exist": **satisfied** (prompts, judge, entry all exist).
- Writability reported honestly per policy: prompts=writable, judge=writable, entry=not-writable-by-this-role (operator-managed).

Final PASS/FAIL is the runner gate + Judge's call.

## Method (read-only)

`Test-Path -PathType Container` for each dir + `Get-ChildItem` item counts;
writability read from `role_policy.json` `allowed_write_roots` cross-checked
against `registry/ROLE_REGISTRY.json`. No write attempted against any evidence
dir; no state touched.
