# DECISION_REGISTER — Module 6 owner decisions

Owner decisions from the document come first (verbatim, doc §25, extract lines
478–484). Discovered decisions (found while building this pack) follow, each
with the pack's recommendation for the owner to ratify or overrule. Status:
OPEN until the owner records a decision; a decision unlocks the rows/prompts
listed in "Blocks".

## From the owner document (doc §25)

| ID | Câu hỏi Owner cần chốt (verbatim) | Ghi chú (verbatim) | Status | Blocks | Source |
|---|---|---|---|---|---|
| M6-OD-001 | Danh sách Hero SKU Phase 1 chính thức là gì? | Không chạy 13/20 SKU song song nếu chưa có Hero SKU lock | OPEN | M6.2A pilot config; PR/PILOT band | extract line 478 |
| M6-OD-002 | Ngưỡng CPA/ROAS/AOV/Verified Rate chính thức cho từng giai đoạn? | Dùng cho Scale Gate và dashboard alert | OPEN | M6-CTR-015 thresholds, M6-CTR-026, M6.2G exit | extract line 479 |
| M6-OD-003 | Hash policy và trường dữ liệu được phép gửi Pixel/CAPI/Offline? | Cần privacy/legal review | OPEN | M6.2D exit, M6-SMK-017 | extract line 480 |
| M6-OD-004 | Google/Meta connector nào dùng trước trong pilot? | Meta trước hay Google song song | OPEN | M6.2D scope, PR/PILOT | extract line 481 |
| M6-OD-005 | Attribution model chính thức: first touch, last touch, weighted hay cohort? | Dashboard có thể hiển thị nhiều model nhưng scale gate cần một model chính | OPEN | M6.2E design, M6.2G scale evidence | extract line 482 |
| M6-OD-006 | Safe range cho guarded auto-publish là gì? | Cần trước khi bật learning engine publish | OPEN | M6.2H publish leg, M6-SMK-011 boundary values | extract line 483 |
| M6-OD-007 | Danh sách persona/keyword/hook fill từ Content Block 20 SKU đã khóa chưa? | Nếu chưa khóa, chỉ dừng ở framework | OPEN | M6.2H seed content (framework may proceed) | extract line 484 |

## Discovered while building the pack (recommendation included)

| ID | Question | Pack recommendation | Status | Blocks | Derivation |
|---|---|---|---|---|---|
| M6-OD-008 | Does Core policy allow PAYMENT_COMPLETED as a revenue-adjacent signal, and in which cases? The doc says "PAYMENT_COMPLETED nếu Core policy cho phép" without the policy. | Treat PAYMENT_COMPLETED as non-revenue telemetry until Core policy evidence is supplied; ORDER_VERIFIED stays the only revenue source (consistent with M6-RULE-003). | OPEN | M6.2E/M6.2F edge handling | extract lines 157, 187 |
| M6-OD-009 | GOLDEN_HOUR_START / REMINDER is "Tùy cấu hình" — is it enabled for pilot, and who owns the config? | Include both codes in event_registry as optional, disabled by default; Gateway/Live owns emission config. | OPEN | M6.2I event set | extract line 134 |
| M6-OD-010 | Slice execution model: the doc gives roadmap order M6.2A..K but no parallelism statement. | Strictly sequential A -> B -> C -> D -> E -> F -> G -> H -> I -> J -> K (safest; honors "Không được nhảy phase"). The pack's DAG encodes sequential; owner may later approve parallel D/E-class bands. | OPEN (pack proceeds with sequential default) | prompt DAG shape | extract lines 100, 384–395 |
| M6-OD-011 | Target repository / stack for implementation slices. The doc instructs "Read the current repository structure first" and "Reuse existing conventions and test patterns" but does not identify the repo in this document. | DECIDED 2026-07-23 by the owner (evidence `04-artifacts/evidence/decisions/M6-OD-011.json`, manifest `04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json` status=LOCKED): mode **GREENFIELD**, target repo `work-root/target-repo` (empty — nothing to reuse, so M6.2A *establishes* the conventions), `workspace_mode=STAGED_ONLY` under `04-artifacts/impl/`, stack **python 3.12** / `pytest -q` / `python -m app`, safety `production_access=false, external_platform_calls=false, live_migrations=false`. Tooling stays stdlib-only at Layer 1 (pack scripts/hooks); the ONLY dependency this decision authorizes is the pinned test runner `pytest==8.4.2` in the 01-coder / 02-tester Layer-2 venvs (SCHEMA_CHANGELOG row 14, applied 2026-07-29). Runtime framework / DB / queue are still unresolved (`""` in the manifest) and need their own gated decision before any slice depends on them. | DECIDED 2026-07-23 | slice implement prompts (plan legs may proceed) | extract lines 459, 463–466 |
| M6-OD-012 | Evidence masking policy for pack execution: exact masking format for user ids / phones / emails quoted in evidence (extends M6-OD-003 to the build pack itself). | Use `abc***xy` masking (first 3 + last 2 chars) and `secret_ref` indirection everywhere; enforced by hooks and gate scans. | OPEN (pack proceeds with recommendation) | evidence format | pack hardening; extract line 429 |
| M6-OVERRIDE-M6P1000-STAGED | Owner break-glass: open slice M6.2A for STAGED implementation while the M6-P1000 entry-gate judge verdict stays BLOCKED (ENTRY-001 all PARTIAL; ENTRY-003 2 PARTIAL + 3 GAP; ENTRY-002 clean). | OWNER_OVERRIDE 2026-07-29: ledger M6-P1000=SKIPPED (never PASS/SIGNED); judge sign-off left UNCHANGED = BLOCKED; `production_flag=OFF` + `global_gateway_state=BLOCKED` enforced; mandatory re-gate at M6.2G; reversible by a real M6-P1000 re-run when evidence is PROVEN. Evidence: `04-artifacts/evidence/decisions/M6-OVERRIDE-M6P1000-STAGED.json`. Upstream fixes bound to M6.2B: `04-artifacts/evidence/decisions/M6-DEFER-F1F2-M6.2B.json`. | DECIDED 2026-07-29 (OWNER OVERRIDE) | M6.2A entry (overridden, staged-only); M6.2G re-gate binding | SCHEMA_CHANGELOG rows 13/15; RULES_LOCKED M6-RULE-020 exception |

## Rules

1. OPEN decisions never block DOCUMENTATION or plan-only prompts; they block
   the specific implement/exit legs listed in "Blocks".
2. A decision is recorded by the operator as a dated row edit plus an
   `04-artifacts/evidence/` note; registers referencing the decision update in
   the same commit (SCHEMA_CHANGELOG row if a schema is affected).
3. Executors must mark BLOCKED (never assume) when they hit an OPEN decision
   inside their scope.
