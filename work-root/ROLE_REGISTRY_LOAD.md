# ROLE_REGISTRY_LOAD — role/agent table + hook integrity

**Prompt**: M6-P0004 (ROLE_REGISTRY_LOAD) · Role: PM_ORCHESTRATOR · Mode: analysis_only
**Recorded**: 2026-07-20 · Read-only cross-check; nothing modified except this note and the evidence JSON.
**Source of truth**: `registry/ROLE_REGISTRY.json` cross-checked against `04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv`.

## 1. Registry role/agent table (`registry/ROLE_REGISTRY.json`)

| Folder | role_name | agent | allowed_write_roots |
|---|---|---|---|
| `00-analyst` | ANALYST_ARCHITECT | m6-analyst-architect | work, 04-artifacts/evidence/prompts, 04-artifacts/analysis |
| `01-coder` | CODER | m6-coder | work, 04-artifacts/evidence/prompts, 04-artifacts/impl |
| `02-tester` | TESTER | m6-tester | work, 04-artifacts/evidence/prompts, 04-artifacts/impl, 04-artifacts/test-reports |
| `03-runner` | RUNNER | m6-runner | work, 04-artifacts/evidence/prompts |
| `04-boundary` | BOUNDARY_ADVERSARY | m6-boundary-adversary | work, 04-artifacts/evidence/prompts, 04-artifacts/boundary-reports |
| `06-security` | SECURITY_PII | m6-security-pii | work, 04-artifacts/evidence/prompts, 04-artifacts/security-reports |
| `.` (pack root) | PM_ORCHESTRATOR,JUDGE | m6-pm-orchestrator\|m6-judge | work-root, 04-artifacts/evidence/prompts, 04-artifacts/evidence/judge, 05-judge |
| `05-judge` | JUDGE-OUTPUT-ONLY | m6-judge | 05-judge |

**Compound-role note**: the pack-root entry declares a compound `role_name`
(`PM_ORCHESTRATOR,JUDGE`) with a pipe-joined `agent`
(`m6-pm-orchestrator|m6-judge`). Expanded position-wise:
`PM_ORCHESTRATOR => m6-pm-orchestrator`, `JUDGE => m6-judge`. The ledger uses
these two as **separate** role values, so reconciliation expands the compound
before matching.

## 2. Check 1 — every ledger Role maps to exactly one agent id

| Ledger Role | rows | Agent(s) in ledger | exactly one? |
|---|---|---|---|
| ANALYST_ARCHITECT | 65 | m6-analyst-architect | yes |
| BOUNDARY_ADVERSARY | 24 | m6-boundary-adversary | yes |
| CODER | 22 | m6-coder | yes |
| JUDGE | 27 | m6-judge | yes |
| PM_ORCHESTRATOR | 25 | m6-pm-orchestrator | yes |
| SECURITY_PII | 12 | m6-security-pii | yes |
| TESTER | 23 | m6-tester | yes |

- `ROLE_AGENT_MULTIMAP_ISSUES = 0` (no role maps to more than one agent).
- Row total = **198** = `prompts_total` in `CURRENT_STATE_LOCKED.json` (independent cross-check).

### Reconciliation ledger vs registry

Every ledger role matches its registry-declared agent:
`LEDGER_ROLE_MISMATCH = 0`, `LEDGER_ROLE_NOT_IN_REGISTRY = 0`.

### Informational — registry roles with no ledger prompts

- `RUNNER` (m6-runner, folder `03-runner`) — declared, 0 ledger prompts.
- `JUDGE-OUTPUT-ONLY` (m6-judge, folder `05-judge`) — write-scope-only sub-role.

Neither violates Check 1 (which is ledger-role → one-agent, forward direction).
The runner's gate operation is operator-script-driven; `JUDGE-OUTPUT-ONLY` is a
write-scope declaration for the judge output folder. Recorded for completeness.

## 3. Check 2 — hook sha256 match files in each role folder

Verified `Get-FileHash -Algorithm SHA256` of every hook file against
`registry.hook_sha256`, across **8 hook homes**: pack-root `.claude/hooks`, the
6 role-session `.claude/hooks`, and the `setup/hooks-master` source.

- `HOOK_FILES_CHECKED = 48` (8 homes × 6 files)
- `HOOK_HASH_MISMATCH = 0`
- `HOOK_FILE_MISSING = 0`
- **ALL_HOOK_HASHES_MATCH = True** — every deployed hook is byte-identical to the registry-pinned hash.

Registry-pinned SHA256 (for the record):

| Hook file | sha256 |
|---|---|
| role_pre_tool_guard.ps1 | 5699d81f54d7f890f81335df9fe1db514714883fbe5d8b10789675dbff0d4425 |
| role_pre_tool_guard.py | 4508547b225591f070835fa1e3cbb1c6d288def40dfc99733fcc6c3e68a127c2 |
| post_write_secret_scan.ps1 | b9862eac33fb1d44c60aec61b93b7146fe09234400dcef73497da89bf1a51147 |
| post_write_secret_scan.py | c31f93da36dcc63f46b6903eb7e6846b0e4c69a4409eac0d8af645a92b0d7539 |
| stop_role_evidence_guard.ps1 | 7936d91f728e05934aaa283569f26678c5907518bb67d76c459123fba315be3c |
| stop_role_evidence_guard.py | c75e211b188ec50c27860de8381b79ad118db35f8e2d58cfa9bc2bce67859ed4 |

## 4. Verdict

- Check 1 (role/agent pairs consistent): **satisfied** — 7/7 ledger roles map to exactly one agent, all reconciling with the registry.
- Check 2 (hook hashes match registry): **satisfied** — 48/48 hook files match.

Final PASS/FAIL is the runner gate + Judge's call.

## 5. Method note (read-only)

Registry loaded via `Get-Content | ConvertFrom-Json`; ledger via `Import-Csv`;
hashes via `Get-FileHash -Algorithm SHA256`. No file created/modified except
this note and the evidence JSON. (One read-only reconcile command initially trip
ped the `role_pre_tool_guard` false-positive because display arrows contained
`>`; re-run with `::` separators — the command was always a pure read.)
