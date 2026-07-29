# AGENT_OPERATING_MODEL — Module 6 build pack

## Roles

| Role (ledger value) | Agent id | Folder | Mandate | Writes |
|---|---|---|---|---|
| PM_ORCHESTRATOR | m6-pm-orchestrator | pack root session | Bootstrap/registry/readiness prompts; mechanical coordination | evidence, work-pm/ |
| ANALYST_ARCHITECT | m6-analyst-architect | 00-analyst | DOC_LOCK, research, design, contract harmonization | evidence, analysis artifacts, work/ |
| CODER | m6-coder | 01-coder | Plan + implement slices (staged in 04-artifacts/impl) | evidence, impl/, work/ |
| TESTER | m6-tester | 02-tester | Smoke build + run; structured test_results | evidence, impl/ (tests), test-reports/, work/ |
| RUNNER (operator) | — human | 03-runner | Runs scripts-win/ from a TERMINAL, not a Claude session; the role folder exists for isolation-parity and holds no execution mandate | nothing via agents |
| BOUNDARY_ADVERSARY | m6-boundary-adversary | 04-boundary | Attacks slice outputs: revenue misuse, consent bypass, event drift, gate bypass | evidence, boundary-reports/, work/ |
| SECURITY_PII | m6-security-pii | 06-security | PII/secret review, hash policy conformance, untrusted-input handling | evidence, security-reports/, work/ |
| JUDGE | m6-judge | 05-judge (output-only; session opens PACK ROOT, fresh each time) | Reviews evidence for JUDGE_GATE rows; writes sign-off | evidence/judge/ |

## Hard rules (all roles)

1. Never mark your own work PASS; the ledger is operator-only.
2. Evidence JSON per prompt, fixed schema, masked PII, `secret_ref` only.
3. BLOCKED over assumption; enumerate `open_blockers`.
4. Only the files your prompt's `required_outputs` names; only inside your
   role's `allowed_write_roots`.
5. Active-prompt protocol: one prompt at a time; the Stop hook blocks "done"
   without evidence.
6. Source access: junction `00-spec/` first; if broken, `_source_snapshot/00-spec/`
   (read-only copy, sha256-manifested), then tell the operator to run
   `Repair-M6RoleJunctions.ps1`.

## Model guidance (operator-facing)

Strongest available model: JUDGE, BOUNDARY_ADVERSARY, SECURITY_PII, and
CONTRACT_HARMONIZATION analyst prompts. Fast models acceptable: PM bootstrap
mechanics, evidence-collect, docs prompts. Never use a fast model to judge.
