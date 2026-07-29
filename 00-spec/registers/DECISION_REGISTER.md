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
| M6-OD-011 | Target repository / stack for implementation slices. The doc instructs "Read the current repository structure first" and "Reuse existing conventions and test patterns" but does not identify the repo in this document. | PHASE0_RESEARCH audits the repo the owner points to; until then, coder prompts run plan/implement against `04-artifacts/impl/` staging with stdlib-only tooling and reuse conventions established in prior staged output; framework selection happens in a gated Phase-0 prompt. | DECIDED 2026-07-23 | slice implement prompts (plan legs may proceed) | extract lines 459, 463–466 |
| M6-OD-012 | Evidence masking policy for pack execution: exact masking format for user ids / phones / emails quoted in evidence (extends M6-OD-003 to the build pack itself). | Use `abc***xy` masking (first 3 + last 2 chars) and `secret_ref` indirection everywhere; enforced by hooks and gate scans. | OPEN (pack proceeds with recommendation) | evidence format | pack hardening; extract line 429 |

## Rules

1. OPEN decisions never block DOCUMENTATION or plan-only prompts; they block
   the specific implement/exit legs listed in "Blocks".
2. A decision is recorded by the operator as a dated row edit plus an
   `04-artifacts/evidence/` note; registers referencing the decision update in
   the same commit (SCHEMA_CHANGELOG row if a schema is affected).
3. Executors must mark BLOCKED (never assume) when they hit an OPEN decision
   inside their scope.
