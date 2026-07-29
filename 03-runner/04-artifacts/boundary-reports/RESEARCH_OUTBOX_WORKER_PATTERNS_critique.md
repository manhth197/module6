# BOUNDARY CRITIQUE — RESEARCH_OUTBOX_WORKER_PATTERNS.md

**Critic prompt**: M6-PC0203 (RESEARCH_OUTBOX_WORKER_PATTERNS_CRITIC) · **Role**: BOUNDARY_ADVERSARY · **Mode**: analysis_only
**Target**: `04-artifacts/analysis/research/RESEARCH_OUTBOX_WORKER_PATTERNS.md` (produced by M6-P0203)
**Author does not respond here.** Findings feed Phase-0 design and the producing prompts M6-P0705/0706/0713 + slice M6.2C.

> `global_gateway_state` stays **BLOCKED**, `production_flag` stays **OFF**. Nothing here flips a gate or a flag. Self-report; the runner gate decides PASS.

---

## 1. Entry gate (verified before review)

| Check | Result | Evidence |
|---|---|---|
| M6-PC0203 is RUNNING in the ledger | ✅ | `PROMPT_EXECUTION_LEDGER_LOCKED.csv` row 35 — `M6-PC0203 … BOUNDARY_ADVERSARY … RUNNING` |
| Dependency M6-P0203 is complete | ✅ | ledger row 34 — `M6-P0203 … PASS`; evidence `M6-P0203.json` status=PASS |
| Required inputs present | ✅ | brief, `RESEARCH_OUTBOX_WORKER_PATTERNS.md`, `M6-P0203.json` all read |

Entry gate holds; review proceeded. *(Aside: the `wpxmh2qy3` "stopped workflow" notice is a dead prior-session artifact from the already-completed M6-PC0200; M6-PC0200.json exists and PC0200 is PASS — no action needed.)*

## 2. Method

Direct citation verification (every `[DOC]`/`[REG]` anchor re-opened) plus an adversarial **find → refute-verify** pass: 5 finder lenses (citation-fidelity, boundary-overreach, **delivery-correctness**, **send-gate**, owner-decisions/executability) surfaced candidates; each was handed to a separate verifier told to **try hard to refute it** and grade severity. **13 candidates verified; 9 confirmed (collapsing to 5 distinct issues), 4 refuted.**

Severity rubric: **BLOCKER** = research unusable / unconditional hard-boundary breach / M6 sends CRM or external-from-runtime / resolves an owner decision / an unconditional lost-event or double-count; **MAJOR** = would cause a lost event, double count, boundary overreach, or dropped owner dependency *if followed*, but mitigated/contradicted elsewhere or hedged as `[EXT]`; **MINOR** = citation precision / completeness / low-impact slip.

## 3. Overall verdict

**No BLOCKER.** Strong artifact. **Every `[DOC]`/`[REG]` citation verified faithful** (L248–252, L254–255, L257 §12; L268 §13; L376–377 §19; dedup/idempotency formulas match RULE-005). Two structural strengths recorded for the judge:
- **The send-time gate is correct.** §5 evaluates the *full* `send_policy` AND-chain **in the worker at send time** — consent re-validated, `event_in_registry` re-checked (not pinned at enqueue) — which **closes the exact MAJOR gap the M6-PC0201 event-registry research was faulted for** (it evaluated send_policy too early). The send-gate attack was refuted.
- **Boundary is essentially clean.** Enqueue-in-transaction vs async-send is correctly distinguished (no RULE-004 direct-send violation); no order-state/pricing/commission side effects; OD-002/003/004 all deferred, none resolved.

The confirmed defects are **1 MAJOR + 4 MINOR**.

| ID | Severity | Category | One-line |
|---|---|---|---|
| F1 | **MAJOR** | delivery-correctness | Worker crash mid-`IN_FLIGHT` orphans the row → silent loss; no reclaim/lease timeout; defeats §4's at-least-once claim and doc L252 "no silent loss" |
| F2 | MINOR | unsupported-claim | `[REG FAIL-001]` mis-cited for a duplicate-send double-count (FAIL-001 is non-revenue-as-revenue; RULE-005 is the right, co-cited authority) |
| F3 | MINOR | internal-inconsistency | `M6-SMK-016` tagged `[REG]` (locked) but it is a **proposed** smoke (register + the file's own header L8) |
| F4 | MINOR | boundary-violation | §2 names "**CRM**" among the outbox dispatch targets, contradicting M6's hard "never sends CRM" boundary |
| F5 | MINOR | missing-owner-decision | §7 omits `CTR-009/010` (`customer_segments`/members) — the audience-dispatcher source — from its "acceptance requirement" list |

---

## 4. Confirmed findings

### F1 — MAJOR — Crashed `IN_FLIGHT` outbox rows are silently lost (no reclaim/lease)
**Category**: delivery-correctness · **Verdict**: CONFIRMED MAJOR (two independent verifiers; refutations attempted and defeated)

**Exact claim (research):**
- §3 L67: "`status: PENDING → IN_FLIGHT → SENT` | on failure `→ PENDING` (reschedule) | on exhaustion `→ DEAD_LETTER`"
- §3 L69: "Worker selects rows where `status=PENDING AND next_retry_at <= now`"
- §4 L90–92: "a crash **between** the external send and the `status=SENT` write causes an at-least-once re-send. This is **safe and intended**…"

**Evidence:** `M6_FULL_DETAIL_EXTRACT` L252 (§12): "Retry / Dead Letter … **Không retry vô hạn, không mất event không dấu vết**" (no event lost without a trace).

**Defect:** Under verbatim consumption a coder builds: `select status=PENDING` → `UPDATE→IN_FLIGHT` (claim the row against concurrent pickup — the reason the status exists) → send → `UPDATE→SENT`, with the `→PENDING` revert living **only inside the on-failure handler** (L67/L70). If the **worker process crashes** between the `IN_FLIGHT` write and the `SENT` write, no handler runs: the row is orphaned in `IN_FLIGHT` — **never re-selected** (the selector is PENDING-only), **never dead-lettered** (that path is exhaustion-driven, L72), **never surfaced for ops** (only `DEAD_LETTER` rows surface, L73). That is a **silent loss**, which simultaneously (a) violates doc L252 "no event lost without a trace", (b) falsifies §4's own "at-least-once re-send" guarantee (nothing returns the row to the PENDING pool the selector reads), and (c) makes §3 L77's "no silent loss" claim for `M6-SMK-016` unearned — SMK-016 as scoped exercises only the *caught-failure* path, not a process crash.

**Missing mechanism:** a stale-`IN_FLIGHT` **visibility/lease/reclaim timeout** that returns rows stuck in `IN_FLIGHT` beyond a bound to `PENDING` (or a `SELECT … FOR UPDATE SKIP LOCKED` claim that never persists an unrecoverable `IN_FLIGHT` status). This belongs in the CTR-021/022 dispatcher contract (M6-P0713) and the M6.2C done-gate.

**Why MAJOR not BLOCKER:** the loss is conditional (crash within the `IN_FLIGHT` window) and the whole lifecycle is explicitly hedged `[EXT]` (L65 "Proposed row lifecycle", L151 "NOT owner requirements") — an architect would likely repair it before build. It is not MINOR: a dropped external measurement/conversion event at the heart of M6.2C's "retry/dead-letter" done-gate is a real delivery-safety defect against a doc-mandated guarantee.

---

### F2 — MINOR — `[REG FAIL-001]` mis-cited for the duplicate-send double-count
**Category**: unsupported-claim / citation-precision · **Verdict**: CONFIRMED MINOR (three verifiers; finder proposed MAJOR, downgraded)

**Exact claim (research §4 L93–94):** "do **not** drop the idempotency_key (that would double-count and trip `[REG FAIL-001]` revenue-misuse / RULE-005)."

**Evidence:** `FAIL_GATE_REGISTER` L13 — **FAIL-001** trips only when "Quote/cart/order draft/payment waiting/COD waiting **bị tính revenue**" (a non-verified *state* counted as revenue). A dropped `idempotency_key` double-**sends** an event that already passed the §5 gate — a **dedup** failure governed by **RULE-005** ("No double count") and the Data-Quality dedup gate (extract L303 "Pixel/CAPI/Offline double count"), *not* the introduction of a non-verified state into revenue.

**Defect:** FAIL-001 is out of scope for a duplicate-count; RULE-005 (co-cited, correct) is the authority. Behavioral impact is low — the actionable directive ("keep the idempotency_key") is right — but the mis-scoped gate id can propagate as a wrong `fail_gate_tripped` tag into downstream contract-prompt evidence (M6-P0705/0706/0713). **Fix:** drop the `[REG FAIL-001]` attribution; cite RULE-005 (and, if a gate is wanted, the Data-Quality dedup gate) for the double-count.

---

### F3 — MINOR — `M6-SMK-016` tagged `[REG]` (locked) but it is a *proposed* smoke
**Category**: internal-inconsistency · **Verdict**: CONFIRMED MINOR (two verifiers)

**Exact claim (research §3 L76):** "**M6-SMK-016** `[REG]` exercises exactly this: fail N times → bounded retry … no silent loss."

**Evidence:** the file's own legend (L19) defines `[REG]` = "locked pack register", but `SMOKE_REGISTER` places SMK-016 under **"Proposed additions (HARDENING — OWNER REVIEW)"** (locked set is SMK-001..015), and the research's **own header L8** calls it a "**proposed** smoke".

**Defect:** L76 overstates an owner-review-pending smoke as locked — contradicting both the register and the file's own header, in an artifact whose stated discipline (§8, the `[REG]`/`[EXT]`/`[PACK]` split) is separating owner-mandated from proposal. Low impact (the retry/dead-letter behavior is doc-mandated at L252 regardless). **Fix:** retag SMK-016 as `[PACK]`/proposed (matching header L8).

---

### F4 — MINOR — §2 names "CRM" among the outbox's external dispatch targets
**Category**: boundary-violation (framing) · **Verdict**: CONFIRMED MINOR (finder proposed MAJOR, downgraded)

**Exact claim (research §2 L55):** "The request path does **zero** external I/O `[DOC L249]` — latency and failures of Meta/Google/**CRM** never touch the user request."

**Evidence:** brief L10 and DOC L364 — M6 **never sends CRM** (CRM-owned); its citation `[DOC L249]` is the CAPI row and contains no CRM. Every buildable directive in the same file excludes CRM (CTR-021 = Pixel/CAPI/Offline L43; CTR-022 = audience L44; §6 "No CRM send").

**Defect:** naming "CRM" as one of the systems M6's outbox worker dispatches to is exactly the "any hint M6 sends CRM" drift a boundary review should surface. MINOR not MAJOR — the token sits only in a rationale clause, not a buildable directive, so no coder ships a CRM send. **Fix:** delete "CRM" from that clause (e.g. "Meta/Google" or "the external platform").

---

### F5 — MINOR — §7 omits `customer_segments`/members (CTR-009/010) as the audience-source dependency
**Category**: missing-owner-decision / completeness · **Verdict**: CONFIRMED MINOR

**Exact claim:** §5.5 L110 "**Audience** only from approved `customer_segments` … never ad-hoc/data-mart"; §7 row 1 (L131) lists `CTR-007/008/011` only.

**Evidence:** `CONTRACT_REGISTER` — CTR-009 `customer_segments` and CTR-010 `customer_segment_members` are `MISSING/OWNER_DECISION_REQUIRED`, **needed before M6.2C**, producing prompt **M6-P0706**; CTR-010 carries the boundary note "Không lạm dụng làm trigger owner" — directly relevant to §5.5's "never ad-hoc/data-mart" guard.

**Defect:** §7, billed as the "explicit list — acceptance requirement", omits the CONSUMED audience source the audience dispatcher (CTR-022) reads. MINOR — fully mitigated: §7 already lists producing prompt **M6-P0706**, which produces CTR-009/010/011 together, so following the listed prompts resolves them, and CONTRACT_REGISTER is authoritative. **Fix:** add CTR-009/010 (→ M6-P0706) to the §7 dependency row and surface the CTR-010 trigger-owner caveat.

---

## 5. Attacked and dismissed (did not survive adversarial verification)

1. **§5 send-time gate fails open.** DISMISSED — the worker/send-time frame correctly evaluates all four `send_policy` AND-terms (consent re-read, `event_in_registry` re-checked, DQ, dedup) with no fail-open window; this is the gate PC0201's research got wrong and this research gets right.
2. **§7 omits M6-OD-008 (PAYMENT_COMPLETED as owner-approved offline trigger).** DISMISSED (two candidates) — "owner-approved event" (L250) is fail-closed by construction (empty approved-set ⇒ ORDER_VERIFIED-only default); OD-008's Blocks column is M6.2E/M6.2F, not the M6.2C outbox slice; §4/§6/§8 reinforce ORDER_VERIFIED-only. No coder wires PAYMENT_COMPLETED without acting against the plain text.
3. **§7 omits M6-ENTRY-001 (Commerce Verified Revenue).** DISMISSED — §7 is scoped to owner *decisions*, not entry-evidence; ORDER_VERIFIED is a consumed Commerce boundary the coder imports; a missing boundary → fail-closed no-send (never a lost event); ENTRY-001 is enforced independently at BOOTSTRAP/M6.2A.

## 6. Acceptance-check trace

- [x] Every finding cites the exact claim and its evidence (research section/line + source file line/row).
- [x] Verdict per finding: BLOCKER/MAJOR/MINOR — 0 BLOCKER, 1 MAJOR (F1), 4 MINOR (F2–F5).
- [x] No raw secret or unmasked PII (only register/extract/research text quoted; no channel-origin data present).
- [x] Nothing self-certified PASS; `04-artifacts/state/` untouched; gateway BLOCKED / production OFF unchanged.
