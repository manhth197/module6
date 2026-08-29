# M6.2I IMPLEMENTATION NOTES — Phase 2 Golden Hour Funnel measurement (STAGED)

**Prompt**: M6-P1802 (`M6_2I_CODER_IMPLEMENT`) · **Role**: CODER · **Mode**: `implement` · **Gate**: EVIDENCE_GATE
**Follows**: [PLAN.md](PLAN.md) (M6-P1801). Built item-by-item; **one plan-delta** (§4, the dashboard wiring).
**Posture unchanged & immutable**: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
`SCALE_MODEL_RATIFIED=False`, `SCALE_EXECUTION_ENABLED=False`, `HASH_POLICY_RATIFIED=False`,
`LEARNING_AUTOPUBLISH_ENABLED=False`, `LEARNING_CONTENT_FILL_ENABLED=False`, `LEARNING_SAFE_RANGE_RATIFIED=False`,
`live_migrations=false`. No code operates a live session, sends anything, scales/publishes, applies a migration, or
flips a flag.

> **Status: coder self-reported PASS** (the runner gate + JUDGE decide, RULE-015). The module-critical invariants —
> **measure-only** (no live-session controller RULE-013; no new table RULE-018; no send/scale/publish/order-state),
> **revenue only from ORDER_VERIFIED** (RULE-003 / FAIL-001, SMK-004), the **live/comment/messenger trace** (SMK-013),
> **retargeting consent-valid-only**, and **RULE-021 order-capture recorded-not-owned** — held under a 3-dimension
> adversarial review driven against the running code: 2 dimensions CLEAN, **1 CONFIRMED MINOR** (the RULE-003 revenue
> choke was not self-enforcing) **fixed + regressed** (§5).

## 1. Staging model — cumulative carry-forward

The whole **M6.2H** tree was carried forward byte-identical into `04-artifacts/impl/M6.2I/` (caches excluded;
`PLAN.md` kept, this file added). Baseline verified green **BEFORE any patch: 377... — measured 351 passed, rc 0**
(the M6.2H notes recorded 345; the carried tree collects/runs **351** — parity with M6.2H confirmed exactly, both
351). Final suite: **378 passed, rc 0** (351 carried + 27 new: 26 initial + 1 review regression). Subprocess counts.

## 2. Change set (all under `04-artifacts/impl/M6.2I/`)

**New — the `funnel/` measurement package (derived, read-only)**
| File | Purpose |
|---|---|
| `app/measurement/funnel/__init__.py` | package marker (measure-only; no new table RULE-018; no live-op RULE-013). |
| `app/measurement/funnel/golden_hour.py` | `GoldenHourState` (PRE/LIVE/POST/CLOSED/**UNKNOWN**) + `observe_state()` — a pure measurement projection: labels an OBSERVED golden-hour signal; **no** start/close/emit/controller (RULE-013). Absent/unknown/non-string ⇒ **UNKNOWN** (fail-closed, M6-OD-009). `GOLDEN_HOUR_START/REMINDER` constants only (never emitted). |
| `app/measurement/funnel/flow.py` | `FlowStage` (the six doc §8 flows) + the **doc §8/§10 event-code → stage map** (codes referenced from canon, none invented; none added to the Phase-1 client allow-list) + `CHAIN` + `REVENUE_VALID_STAGE/EVENT = ORDER_TO_VERIFIED/"ORDER_VERIFIED"` (RULE-003) + `FUNNEL_RATE_SPECS` (the doc §14 rate definitions, verbatim formulas). |
| `app/measurement/funnel/models.py` | frozen `GoldenHourFunnelView` / `FunnelRate` / `FunnelTrace`. `to_public()` masks `psid` (RULE-014/H02); only verified revenue is present (RULE-003); no write/trigger field (RULE-012). |
| `app/measurement/funnel/funnel.py` | `GoldenHourFunnel` — the read-only assembler: groups the measurement store's events by `live_session_id`, buckets by observed Golden Hour state, per-stage counts (+ per-state breakdown), the doc §14 funnel rates (**reusing kpi_metrics' `_safe_div`** + the §14 definitions at the per-session grain), **verified-only revenue** (self-enforcing: `event_code == ORDER_VERIFIED` AND revenue present — RULE-003/FAIL-001), the **RULE-021** `capture_gate_passed` (CONSUMED Commerce flag; absent ⇒ False), and the **SMK-013** trace from `ads_attribution_context`. No write/send/scale/publish method. |
| `app/measurement/funnel/retargeting.py` | `RetargetingMeasurement` — measure-only eligibility: a recognized engagement signal (doc §8/§10) **AND** `ConsentGate.evaluate(snapshot, ConsentScope.AUDIENCE_SYNC)` (reuse existing scope; no new scope invented, RULE-018). Missing/expired/opt-out/scope-not-granted/unrecognized ⇒ not eligible (fail-closed). **No send/enqueue/transport surface** (`external_send=OFF`). |

**Patched (carried-forward)** — none in the final tree (see the §4 plan-delta). **No new migration** (doc §13 defines
no golden-hour/funnel/session table; adding one breaches RULE-018 — the projection reads mig 0002 + 0006). **No new
config flag** (measure-only).

**Tests (new)** + `tests/conftest.py` fixtures (`make_golden_hour_funnel`, `retargeting_measurement`).

## 3. Tests → smoke/leg mapping (TESTER executes the official smokes)

| Test | Proves | Leg / smoke |
|---|---|---|
| `test_golden_hour_funnel_chain.py` | the full Ads→Live→Comment→Messenger→Quote→Order→Verified chain measured end-to-end across PRE/LIVE/POST/CLOSED; §14 rates; verified-only revenue; trace threads; absent golden-hour ⇒ UNKNOWN but chain still measured | **L1 (Golden Hour conversion smoke)** |
| `test_golden_hour_state_measure_only.py` | `observe_state` coercion; fail-closed to UNKNOWN; **no session-controller verb** (RULE-013); OD-009 | L1 / RULE-013 |
| `test_quote_in_funnel_not_revenue.py` | a quote/order-created is a funnel stage but 0 revenue; **defense-in-depth**: a quote force-carrying a revenue_value is still 0 (self-enforcing RULE-003); cross-check vs the M6.2F dashboard | **L2 / SMK-004 / FAIL-001** |
| `test_live_chain_trace_in_funnel.py` | funnel threads live_session_id + comment_id + messenger_thread_id; **psid masked** on export | **L3 / SMK-013** |
| `test_retargeting_consent_valid_only.py` | retargeting eligible only on VALID AUDIENCE_SYNC consent; missing/expired/opt-out/scope-not-granted/unrecognized ⇒ not eligible; **no send surface** | L1 (retargeting) |
| `test_order_capture_commerce_gate_rule021.py` | `capture_gate_passed` True only with the consumed Commerce flag; absent/False ⇒ False (fail-closed); **no order-ownership verb** (RULE-021) | L1 / RULE-021 |
| `test_funnel_measure_only_boundary.py` | the funnel/view/retargeting expose **no** write/send/scale/publish/order-state/pricing verb; read-only data (RULE-012/013/018) | L1/L2/L3 |

Smoke EXECUTION + official SMK-004/SMK-013 authoring (M6.2I copies) is the TESTER's (M6-P1803/1804) — no self-run
(RULE-015).

## 4. Plan-delta (one)

**Dropped the dashboard wiring (PLAN §5 P1/P2).** The plan proposed surfacing the funnel as an optional read-only
section on the existing GET /api/admin/ads/dashboard (CTR-018) by adding `funnel` to `DashboardDeps` + a
`golden_hour_funnel` field to `DashboardView`. Implementing it broke **two carried-forward tests** that assert
`set(vars(DashboardDeps).keys()) == {"mart"}` — including the **TESTER-owned** smoke
`tests/smoke/test_smk_010_data_mart_support_view_only.py`. Editing a TESTER-owned smoke is **out of CODER role**
(the M6.2E Round-1 lesson; RULE-015 / role boundary). Since the dashboard section is the plan's most optional item
and is **not required by any M6.2I exit-gate leg** (the legs are the funnel chain + SMK-004 + SMK-013 + rollback),
both edits were **reverted to M6.2H byte-identical** and the funnel is delivered as a **standalone measurement
layer**. Wiring it to the dashboard (with a corresponding TESTER smoke update) belongs to the owner integration step
(M6-OD-011). The `funnel` package and all seven tests are unaffected; T7 was trimmed to drop the dashboard-section
assertion.

## 5. Adversarial self-review (ultracode) — 1 CONFIRMED (fixed), 2 dimensions CLEAN

A read-only adversarial review (3 dimensions, each finding re-verified by an independent skeptic RUNNING the code)
found: **boundary/measure-only CLEAN**, **PII/reuse/formula CLEAN**, and **one CONFIRMED MINOR** in fail-closed
correctness: `funnel._verified_revenue` gated on `revenue_value is not None` only, never on the ORDER_VERIFIED event
code — so the RULE-003 revenue choke did not **self-enforce** its own docstring. In the canonical/tested flow revenue
only ever lands on ORDER_VERIFIED rows (numbers were correct), but a store/materializer misuse or a mismatched
event↔conversion pairing could put a revenue_value on a non-verified row and the funnel would count it (and report an
incoherent ORDER_TO_VERIFIED=0). **Fix**: the choke now ANDs `event_code == flow.REVENUE_VALID_EVENT` with revenue
presence (defense-in-depth; `REVENUE_VALID_EVENT` already existed for this purpose; PAYMENT_COMPLETED / non-verified
stages are meant to contribute 0, so nothing legitimate is dropped). **Regression added**
(`test_quote_carrying_revenue_is_still_zero_in_funnel`): a QUOTE_SENT row force-carrying a revenue_value reports 0
funnel revenue. Not a gate sign-off — the runner gate + JUDGE (M6-P1809) decide.

## 6. Rollback

Staged only — baseline rollback = delete the M6.2I tree (M6.2H untouched). Per-item: new `funnel/` files → delete;
patched carried-forward files → **none** (the dashboard patch was reverted, §4). No migration to unwind (none added).
The projection is derived + read-only — it writes nothing to the stores; removing it leaves `ads_measurement_events`
/ `ads_attribution_context` exactly as M6.2H left them.

## 7. Scope & governance (unchanged)

In scope built: the Golden Hour state measurement (PRE/LIVE/POST/CLOSED/UNKNOWN, measure-only), the doc §8
flow-chain funnel assembler (per live-session, bucketed by state, §14 rates, verified-only revenue, RULE-021
capture flag, SMK-013 trace), the consent-valid-only retargeting measurement. OUT (not built): operating live
sessions (Gateway/Live, RULE-013), public final price (LEX-003/004), revenue from live signals (Module 7), AI
consult content (M4), sending/audience-sync/CRM/scale/publish/commission, the dashboard section (§4 plan-delta →
owner integration step). Module boundary intact (no M3 pricing/QuoteSnapshot write, no M5 public reply, no M8
order-state, no CRM send, no commission). No raw secrets/PII (psid masked on export; trace/audit PII-safe).
FAIL-001 not tripped (verified-only revenue, self-enforcing); FAIL-010 not tripped (Phase 1 A..H complete/SIGNED;
this is the first Phase-2 slice). `M6-P1000` + `M6-P1309` verdicts stay BLOCKED (not converted).
