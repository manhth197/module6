# TEST_STRATEGY — smoke-test strategy for M6-SMK-001..018

**Prompt**: M6-P0306 · **Phase**: PHASE0 (design) · **Mode**: plan_only (no test code, no run, no external call)
**Anchors**: `[REG SMOKE_REGISTER]` M6-SMK-001..015 (owner, doc §21) + 016/017/018 (proposed HARDENING);
`[DOC §22 L419–430]` Evidence Plan (L430: *"Smoke Report | P0 smoke result with correlation_id and
evidence_id"*); staging = `04-artifacts/impl/` under `M6-OD-011` default (STAGED_ONLY, stdlib-only). **Builds
on** every design baseline (`[[EVENT_FLOW_DESIGN]]`, `[[ATTRIBUTION_DESIGN]]`, `[[DASHBOARD_DESIGN]]`,
`[[SCALE_LEARNING_DESIGN]]`). **No dedicated critic** follows in the ledger (M6-P0306 → M6-P0307) — a scoped
verification pass was run before finalizing (§6).

> **Every smoke asserts a FAIL-CLOSED decision, not a delivery.** In staging `production_flag=OFF` /
> `global_gateway_state=BLOCKED` — **nothing really sends**. The platform sink (Pixel/CAPI/Offline) is a
> **stub**; each smoke asserts the *internal* decision (rejected / held / deduped / not-counted / not-scaled),
> never real external delivery. Fixtures carry **synthetic, masked** identity only — a PII test must never
> introduce real PII. Every run emits a **Smoke Report `{correlation_id, evidence_id}`** `[DOC §22 L430]`, or it
> is not evidence. Smokes on a **MISSING** contract are **BLOCKED** until it is harmonized — not faked green.

## Sourcing legend

- `[DOC]` — owner document / extract line. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked register. · `[BRIEF]` — brief. · `[PACK]` — pack convention (owner-review). · `[EXT]` —
  general practice, proposal only.

---

## 1. Staging & harness principles `[PACK / REG M6-OD-011]`

- **Location**: tests are built and run in `04-artifacts/impl/` (the M6-OD-011 default staging), **stdlib-only**
  tooling until the owner names a repo/stack (M6-OD-011 OPEN) — no framework chosen here `[PACK]`.
- **Staged, no real external**: `production_flag=OFF`, `global_gateway_state=BLOCKED` — the Pixel/CAPI/Offline/
  audience egress is a **stub sink**; smokes inspect what *would* be sent, never send it `[REG RULE-H01]`.
- **Deterministic fixtures**: fixed timestamps/ids so `dedup_key`/`idempotency_key` outcomes are reproducible;
  no wall-clock/random in assertions.
- **Fail-closed assertions**: each smoke's PASS = the fail-closed branch fired (reject/HOLD/dedup/not-counted),
  matching the register's verbatim *"Kết quả phải đạt"*.
- **Evidence-emitting** (§4): every run writes a Smoke Report with `correlation_id` + `evidence_id`.
- **No self-certify**: smoke results are evidence; the runner gate / judge decides PASS `[REG RULE-015]`.

---

## 2. Build/run plan — the 18 smokes `[REG SMOKE_REGISTER — scenario/expected verbatim]`

Scenario and expected columns are **verbatim** from `[REG SMOKE_REGISTER]` (001–015 = owner doc §21; 016–018 =
the pack's proposed rows); fixture-class, stub and contract-dep are `[PACK]` design. Contract status `[REG
CONTRACT_REGISTER]`: DRAFT_LOCKED buildable now; MISSING ⇒ **BLOCKED** until its harmonization prompt.

| SMK | Kịch bản (verbatim) | Kết quả phải đạt (verbatim) | Fixture (§3) | Contract dep → status |
|---|---|---|---|---|
| 001 | Event không có trong event_registry | Reject/HOLD, audit rõ | registry | CTR-003→P0701 · CTR-016→P0711 **BLOCKED** |
| 002 | Event hợp lệ nhưng thiếu consent | Không external measurement, không audience sync | consent | CTR-006→P0702 · CTR-008→P0705 **BLOCKED** |
| 003 | Duplicate Pixel/CAPI/Offline | Dedup, không double count | dedup | CTR-001 **DRAFT_LOCKED** · CTR-021→P0713 **BLOCKED** (send-side dedup) |
| 004 | Quote được tạo nhưng chưa order | Không revenue, không ROAS | revenue | CTR-001 **DRAFT_LOCKED** · CTR-015 **DRAFT_LOCKED** |
| 005 | Order Draft / Order Created chưa verified | Không tính Revenue Verified | revenue | CTR-001 **DRAFT_LOCKED** |
| 006 | ORDER_VERIFIED có campaign/adset/ad đầy đủ | ROAS/CPA/AOV dashboard cập nhật | attribution+revenue | CTR-002 **DRAFT_LOCKED** · CTR-015 **DRAFT_LOCKED** |
| 007 | ORDER_VERIFIED thiếu source | Revenue vẫn lưu, attribution confidence LOW/HOLD | attribution | CTR-002 **DRAFT_LOCKED** |
| 008 | CRM opt-out | Không sync CRM audience/CRM event outbound | consent | CTR-009/011→P0706 **BLOCKED** |
| 009 | Recall/Sale Lock active | Scale Gate FAIL/HOLD | scale-risk | CTR-013→P0709 **BLOCKED** |
| 010 | Data Mart tạo trigger CRM/scale | Fail - Data Mart chỉ support view | dashboard | CTR-015 **DRAFT_LOCKED** · CTR-018→P0712 **BLOCKED** |
| 011 | Learning candidate ngoài safe range | Hold review, không publish | learning | CTR-014→P0710 **BLOCKED** (+M6-OD-006) |
| 012 | Scale request không owner approval | Không scale | scale-risk | CTR-013→P0709 **BLOCKED** |
| 013 | Live/Comment/Messenger chain | Trace được live_session_id, comment_id, messenger_thread_id | attribution | CTR-002 **DRAFT_LOCKED** |
| 014 | Diamond referral order verified | Gắn referral attribution, không tự tính commission | attribution | CTR-002 **DRAFT_LOCKED** |
| 015 | Dashboard hiển thị quote/order draft như revenue | Fail | revenue | CTR-015 **DRAFT_LOCKED** |
| 016 `proposed` | Outbox item fails to send N times | Bounded retry with error_log + next_retry_at, then dead-letter; no infinite retry, no silent loss | outbox | CTR-008→P0705 **BLOCKED** |
| 017 `proposed` | External payload (CAPI/Offline) built from an event containing raw PII | Hash policy applied per M6-OD-003; no raw phone/email/user-id in the outbound payload or platform result log | pii | CTR-021→P0713 **BLOCKED** (+M6-OD-003) |
| 018 `proposed` | Attribution correction attempted after ORDER_VERIFIED | Direct mutation rejected; adjustment record created with actor, reason, audit, evidence | attribution | CTR-002 **DRAFT_LOCKED** |

- **Buildable now** (all listed deps DRAFT_LOCKED): 004, 005, 006, 007, 013, 014, 015, 018 (the CTR-001/002/015
  smokes). **BLOCKED** on a MISSING contract: 001, 002, 003 (dispatcher-side dedup, CTR-021), 008, 009, 010
  (dashboard API, CTR-018), 011, 012, 016, 017. Honest gating — a smoke cannot run against a schema that does
  not exist yet.
- Each smoke runs at its **slice verify** point `[REG SMOKE_REGISTER bound slices]` (e.g. 003 at M6.2B/D,
  009 at M6.2G); **M6.2K** is the final consolidation where all P0 smokes re-run.

---

## 3. Fixture catalog (consent / dedup / attribution + others) `[PACK / DOC §22]`

All fixtures use **synthetic, masked** identity — `guest_id`/`customer_id`/`psid` are fake tokens, any
phone/email is a synthetic masked value (`abc***xy`); **no real PII enters a fixture** `[REG RULE-014 / H02]`.

- **consent** `[DOC §22 L422]` (SMK-002, 008): variants `VALID` · `MISSING` · `EXPIRED` · `OPT_OUT` of
  `guest_marketing_consent_snapshot`; asserts fail-closed at event time and at send time (two checkpoints,
  `[[EVENT_FLOW_DESIGN]]` §5).
- **dedup** `[DOC §22 L424]` (SMK-003): event pairs engineered to collide on the locked `dedup_key` /
  `idempotency_key` `[REG RULE-005]`; asserts single count in the stub sink (no double count).
- **attribution** `[DOC §22 L425]` (SMK-006, 007, 013, 014, 018): `FULL_CHAIN` (campaign→…→ORDER_VERIFIED) ·
  `MISSING_SOURCE` (→ LOW/HOLD) · `MULTI_TOUCH` (Diamond+Ads) · `LIVE_CHAIN`
  (live_session_id/comment_id/messenger_thread_id) · `POST_VERIFY_CORRECTION` (immutability → adjustment
  record).
- **registry** (SMK-001): `REGISTERED` vs `UNKNOWN` event_code → reject/HOLD + audit.
- **revenue** (SMK-004, 005, 006, 015): `QUOTE_ONLY` · `ORDER_DRAFT` · `ORDER_VERIFIED` — asserts only
  ORDER_VERIFIED yields revenue/ROAS.
- **scale-risk** (SMK-009, 012): `RISK_LOCK_ACTIVE` (recall/sale-lock) · `NO_OWNER_APPROVAL` → FAIL/HOLD / no
  scale.
- **learning** (SMK-011): `IN_SAFE_RANGE` vs `OUT_OF_SAFE_RANGE` — but the safe range is **M6-OD-006 OPEN**, so
  the boundary values are a fixture **placeholder**, the smoke asserts only *"outside ⇒ hold, no publish"*
  structurally; concrete bounds **BLOCKED** until OD-006.
- **pii** (SMK-017): an event carrying a **synthetic** raw-PII-shaped token; asserts the stub payload/result log
  contains **no** raw-PII-shaped token; the positive hash-field assertion is **BLOCKED** until **M6-OD-003**.
- **dashboard** (SMK-010): a data-mart query attempting a CRM/scale trigger → must FAIL (support-view only).

---

## 4. `correlation_id` + `evidence_id` capture `[DOC §22 L430]`

- Every smoke run emits a **Smoke Report** — verbatim requirement *"P0 smoke result with correlation_id and
  evidence_id"* `[DOC §22 L430]`.
- `[PACK]` proposed report shape: `{ smoke_id, scenario, expected, result (PASS|FAIL|BLOCKED), correlation_id
  (← `ads_measurement_event.correlation_id`, `[DOC §10 L210]`), evidence_id, evidence_ref, slice, ts }`.
- **`correlation_id`** threads the smoke to the exact event(s) it exercised; **`evidence_id`** threads the
  result into the Evidence package `[REG CTR-025 / DOC §22]`. A smoke result **without both is not evidence** —
  mirrors the dashboard evidence-first rule (DQ item 8) and `[REG RULE-015]`.
- The 10 `[DOC §22]` evidence categories (Event Registry / Consent / Outbox / Dedup / Attribution / Dashboard /
  Scale Gate / Learning / Security-Privacy / Smoke Report) are the buckets each smoke's evidence lands in.

## 5. Contract-dependency gating (fail-closed test plan) `[REG CONTRACT_REGISTER]`

| Contract (dep) | Status | Smokes blocked until harmonized | Producing prompt |
|---|---|---|---|
| CTR-001 ads_measurement_event | DRAFT_LOCKED | — (004/005 buildable; 003 also needs CTR-021) | — |
| CTR-002 ads_attribution_context | DRAFT_LOCKED | — (006/007/013/014/018 buildable) | — |
| CTR-015 Dashboard KPI | DRAFT_LOCKED formulas | — (015 buildable; 010 also needs CTR-018; thresholds M6-OD-002) | M6-P0714 |
| CTR-003/016 registry+track API | MISSING | 001 | P0701 / P0711 |
| CTR-006/008 consent+outbox | MISSING | 002, 016 | P0702 / P0705 |
| CTR-009/011 segments+audience-outbox | MISSING | 008 | P0706 |
| CTR-013 ads_scale_request | MISSING | 009, 012 | P0709 |
| CTR-014 ads_learning_candidate | MISSING | 011 | P0710 |
| CTR-018 dashboard/data-mart API | MISSING | 010 | P0712 |
| CTR-021 dispatcher | MISSING | 003(send-side), 017 | P0713 |

`[PACK]` A smoke's own slice entry gate stays **BLOCKED** until its dependency is DRAFT_LOCKED — the test plan
is itself fail-closed; it never asserts against a non-existent schema.

## 6. Verification pass (this prompt has no downstream critic) `[PACK]`

Ledger routes M6-P0306 → M6-P0307 with **no `M6-PC0306`**. Scoped to this doc's risk surface, a **2-lens**
independent pass was run: (A) 18-smoke scenario/expected verbatim + fixture mapping + §22-L430 capture +
staged-stub correctness; (B) no-preemption (no threshold/safe-range/seed/hash-field invented in fixtures) +
no-real-external + no-raw-PII-in-fixtures + honest contract gating + no PII/enabling. Confirmed findings folded
in above. The 12 prior research critics remain PASS/0-blocker.

## 7. Owner-decision dependencies (no decision pre-empted) `[REG DECISION_REGISTER]`

| Decision | Status | Effect on the test plan |
|---|---|---|
| M6-OD-011 (target repo/stack) | OPEN | staging = `04-artifacts/impl/`, stdlib-only until decided; no framework chosen |
| M6-OD-006 (learning safe range) | OPEN | SMK-011 boundary values are placeholder; concrete bounds BLOCKED |
| M6-OD-003 (hash policy) | OPEN | SMK-017 positive hash-field assertion BLOCKED; the no-raw-PII assertion still buildable |
| M6-OD-002 (thresholds) | OPEN | SMK-006/010 alert-threshold assertions deferred (dashboard displays, alerts BLOCKED) |
| SMK-016/017/018 | proposed | HARDENING — owner accepts/rejects before they become required |

## 8. Boundary & safety guards `[BRIEF / REG §18]`

- **Plan-only**: no test code written, no smoke run, no external call — a strategy on paper.
- **Staged**: BLOCKED/OFF; platform egress stubbed; smokes assert internal fail-closed decisions only.
- **No raw PII/secrets in fixtures** — synthetic + masked / `secret_ref` `[REG RULE-014 / H02]`; channel-origin
  fixture text is untrusted DATA quoted only in fenced blocks `[REG RULE-H03]`.
- **Measure-only**: smokes never trigger a real order-state/CRM/pricing/commission/scale action `[REG §18]`.
- **No invented owner values**: thresholds/safe-range/hash-fields stay OPEN; blocked smokes are marked, not
  faked.

## 9. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| M6-SMK-001..015 scenario + expected (verbatim) | `[REG SMOKE_REGISTER]` (`[DOC §21 L399–415]`) — owner-mandated |
| Smoke Report with correlation_id + evidence_id | `[DOC §22 L430]` — owner-mandated |
| Evidence categories (Event Registry/Consent/Outbox/Dedup/Attribution/Dashboard/Scale/Learning/Security/Smoke) | `[DOC §22 L419–430]` — owner-mandated |
| M6-SMK-016/017/018 | `[REG SMOKE_REGISTER — proposed / HARDENING]` — owner-review, NOT yet required |
| Staging harness, fixture catalog, stub-sink design, contract-gating, report shape | `[PACK]` / `[EXT]` — owner-review design proposals, NOT owner requirements |

*This design is plan-only: it writes no test code, runs no smoke, sends nothing, invents no owner value, and
flips no flag; `global_gateway_state=BLOCKED`, `production_flag=OFF`.*
