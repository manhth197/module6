# TEST_MANIFEST — Slice M6.2I smoke suite (Phase 2 Golden Hour Funnel)

| Field | Value |
|---|---|
| Prompt | M6-P1803 — `M6_2I_TESTER_BUILD` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — the smoke tests are AUTHORED here. This attempt ran a **collect-only build-validation** (imports/collects clean, no assertions executed) per the prompt's "Build (do not yet run)"; the **formal executed-results recording** belongs to M6-P1804. |
| Executed by (formal) | M6-P1804 (`M6_2I_TESTER_RUN`) → `04-artifacts/test-reports/M6.2I/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-004, M6-SMK-013** (exactly — per `00-spec/slices/M6.2I.md` "Core smokes" + this prompt's `<smoke_ids>`) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Slice scope | measure the Phase 2 conversion machine (doc §8): Golden Hour funnel (PRE/LIVE/POST/CLOSED), AI-consult handoff, order-capture signals, retargeting on valid events + valid consent only; derived read-only `funnel/` projection over `ads_measurement_events` |
| Staging root | `04-artifacts/impl/M6.2I/` (STAGED_ONLY; convention reference, not a live repo) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (owner P0 matrix, extract lines 404 / 413) |

> **Governance (immutable — nothing in this suite flips a flag, and the funnel only measures):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `SCALE_MODEL_RATIFIED=False`,
> `SCALE_EXECUTION_ENABLED=False`, `HASH_POLICY_RATIFIED=False`, `LEARNING_AUTOPUBLISH_ENABLED=False`. The funnel
> is **measure-only** (RULE-013 — no live-session controller; RULE-018 — no new table; no send/scale/publish/
> order-state): a derived read-only projection over the M6-owned store. Revenue is **verified-only and
> self-enforcing** (RULE-003 / FAIL-001, SMK-004): only an ORDER_VERIFIED set-once `revenue_value` is revenue; a
> quote / order-created is a funnel stage, never revenue — even one force-carrying a `revenue_value` reports 0.
> The live/comment/messenger trace is threaded from `ads_attribution_context` (SMK-013) with **psid masked** on
> export (RULE-014 / H02). Retargeting is eligible only on **valid AUDIENCE_SYNC consent** (fail-closed), with no
> send surface. Order-capture records the CONSUMED Commerce gate; Module 6 never performs/owns it (RULE-021). No
> pricing (M3), consult content (M4), public reply (M5), live ops (M7), order-state (M8), CRM send, or commission
> (RULE-019). `status` is an honest self-report; the runner EVIDENCE_GATE and the slice Judge (M6-P1809) decide
> closure.

## What this suite is

The **official M6.2I smoke suite**: one dedicated smoke file per bound smoke id, each carrying the register's
scenario/expected **verbatim**, driven through the M6.2I `GoldenHourFunnel` projection — per-session stage counts,
the doc §14 funnel rates (reusing kpi_metrics' `_safe_div`), the self-enforcing verified-only revenue, and the
`FunnelTrace` (live/comment/messenger, psid masked) — plus the negative / fail-closed companions and non-vacuous
controls. It reuses the shared fixtures in [`tests/conftest.py`](04-artifacts/impl/M6.2I/tests/conftest.py)
(`make_golden_hour_funnel`, `make_measurement_event`, `make_verified_row`, `make_dashboard_deps`,
`measurement_store`). No new production code, and **no fix to the code under test** (TESTER reports defects, never
fixes them).

Both ids are **re-bound** in M6.2I (SMK-004 was M6.2F, SMK-013 was M6.2E), so each gets a NEW slice-appropriate
**funnel-leg** smoke file that coexists with the carried dashboard/attribution smoke — the same coexistence
pattern used for SMK-006 (M6.2E attribution + M6.2F dashboard) and SMK-003 (M6.2B + M6.2D).

All ids are **synthetic**; no raw secret/PII. The SMK-013 `psid` marker is **assembled at runtime** so no literal
id sits in the test source (the pack secret scan forbids it); psid is masked on every funnel export.

M6.2I **carried the whole M6.2H tree forward** (cumulatively M6.2A–H, byte-identical) and the coder (M6-P1802)
added the `funnel/` package with its own leg tests. The carried smokes and regression suites remain and re-run
here as supporting coverage; the **two files below are the new M6.2I-bound smokes** authored by this prompt.

## Smoke → test binding

| Smoke ID | Doc ID | Test file (M6.2I, new) | Nodes | Primary test (scenario verbatim) | Negative / fail-closed & control tests | Rule(s) | Fail gate | Exit leg |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-004 | ADS-P0-004 | [`tests/smoke/test_smk_004_quote_in_golden_hour_funnel_not_revenue.py`](04-artifacts/impl/M6.2I/tests/smoke/test_smk_004_quote_in_golden_hour_funnel_not_revenue.py) | 4 | `test_smk_004_quote_in_funnel_is_measured_but_not_revenue` | `..._neg_order_created_not_verified_is_not_revenue`, `..._neg_quote_carrying_revenue_is_still_zero`, `..._neg_no_roas_from_quote_same_choke_as_dashboard` | M6-RULE-003 | M6-FAIL-001 | L2 |
| M6-SMK-013 | ADS-P0-013 | [`tests/smoke/test_smk_013_funnel_live_chain_trace.py`](04-artifacts/impl/M6.2I/tests/smoke/test_smk_013_funnel_live_chain_trace.py) | 4 | `test_smk_013_funnel_threads_live_comment_messenger_trace` | `..._neg_psid_masked_on_export`, `..._neg_partial_chain_traces_what_is_present`, `..._control_no_live_chain_traces_none` | M6-RULE-013, M6-RULE-016 | M6-FAIL-010 | L3 |

**New M6.2I smoke nodes: 8 (4 + 4).**

---

## M6-SMK-004 — Quote in the funnel is measured but not revenue

Verbatim from `00-spec/registers/SMOKE_REGISTER.md` (extract line 404):

```
Smoke ID:          M6-SMK-004  (Doc ID ADS-P0-004)
Kịch bản:          Quote được tạo nhưng chưa order
Kết quả phải đạt:  Không revenue, không ROAS
```

This is the **M6.2I funnel leg** of SMK-004 (the carried M6.2F dashboard smoke
[`test_smk_004_quote_not_revenue.py`](04-artifacts/impl/M6.2I/tests/smoke/test_smk_004_quote_not_revenue.py)
proves the dashboard side).

- **Primary:** a `QUOTE_SENT` (+ `MESSENGER_STARTED`) in a live session → counts in the funnel Quote stage
  (`MESSENGER_TO_QUOTE` = 1, Quote Rate numerator = 1) but `verified_revenue == 0.0` (RULE-003 / FAIL-001).
- **Negative — order-created:** an `ORDER_CREATED` (not verified) is a funnel stage (`QUOTE_TO_ORDER`) but 0
  verified revenue.
- **Negative — quote carrying revenue:** a `QUOTE_SENT` row force-materialized with a `revenue_value` still
  reports 0 funnel revenue (self-enforcing RULE-003 choke — ANDs event_code == ORDER_VERIFIED with revenue).
- **Negative — no ROAS:** with only a quote, the funnel reports 0 revenue AND the M6.2F dashboard (same store)
  reports Revenue Verified 0 with ROAS None — no ROAS on either surface (không ROAS).

## M6-SMK-013 — Funnel threads the live/comment/messenger chain

Verbatim (extract line 413):

```
Smoke ID:          M6-SMK-013  (Doc ID ADS-P0-013)
Kịch bản:          Live/Comment/Messenger chain
Kết quả phải đạt:  Trace được live_session_id, comment_id, messenger_thread_id
```

This is the **M6.2I funnel leg** of SMK-013 (the carried M6.2E attribution smoke
[`test_smk_013_live_chain_trace.py`](04-artifacts/impl/M6.2I/tests/smoke/test_smk_013_live_chain_trace.py) proves
the resolver side).

- **Primary:** a verified live-session row with `comment_id` / `messenger_thread_id` / `psid` signals → the funnel
  `trace` threads `live_session_id`, `comment_id`, `messenger_thread_id`.
- **Negative — psid masked:** `to_public()["trace"]["psid"]` is masked (≠ raw, not None); the raw psid never
  appears anywhere in the export.
- **Negative — partial chain:** a comment with no messenger thread traces `comment_id`, leaves
  `messenger_thread_id` None (never fabricated).
- **Control:** a session with no live/comment/messenger source traces none of the two ids; the session key itself
  is still traced (non-vacuity).

---

## Supporting / regression suite (run alongside the two bound smokes)

The full staged suite re-runs. Files below (coder M6-P1802) are **not** the two bound M6.2I smoke ids but pin the
funnel layer the smokes rely on.

| File | Purpose | Nodes |
|---|---|---|
| [`tests/test_golden_hour_funnel_chain.py`](04-artifacts/impl/M6.2I/tests/test_golden_hour_funnel_chain.py) | L1 — full Ads→…→Verified chain measured across PRE/LIVE/POST/CLOSED; §14 rates; verified-only revenue; trace | 3 |
| [`tests/test_golden_hour_state_measure_only.py`](04-artifacts/impl/M6.2I/tests/test_golden_hour_state_measure_only.py) | RULE-013 — `observe_state` fail-closed to UNKNOWN; no session-controller verb | 4 |
| [`tests/test_quote_in_funnel_not_revenue.py`](04-artifacts/impl/M6.2I/tests/test_quote_in_funnel_not_revenue.py) | SMK-004 leg — quote is a funnel stage, 0 revenue; quote-carrying-revenue still 0; dashboard cross-check | 4 |
| [`tests/test_live_chain_trace_in_funnel.py`](04-artifacts/impl/M6.2I/tests/test_live_chain_trace_in_funnel.py) | SMK-013 leg — funnel threads the three ids; psid masked on export | 3 |
| [`tests/test_retargeting_consent_valid_only.py`](04-artifacts/impl/M6.2I/tests/test_retargeting_consent_valid_only.py) | RULE-016 — retargeting eligible only on VALID AUDIENCE_SYNC consent; no send surface | 6 |
| [`tests/test_order_capture_commerce_gate_rule021.py`](04-artifacts/impl/M6.2I/tests/test_order_capture_commerce_gate_rule021.py) | RULE-021 — `capture_gate_passed` from the consumed Commerce flag (absent → False); no order-ownership verb | 4 |
| [`tests/test_funnel_measure_only_boundary.py`](04-artifacts/impl/M6.2I/tests/test_funnel_measure_only_boundary.py) | RULE-012/013/018 — funnel/view/retargeting expose no write/send/scale/publish/order-state/pricing verb | 3 |
| carried M6.2A–H suite | seam/tracking/outbox/integration/attribution/dashboard/DQ/scale/learning smokes + all unit + regression suites | 351 |

## Fixtures reused (from `tests/conftest.py`)

| Fixture | Role |
|---|---|
| `make_golden_hour_funnel(golden_hour_state_by_event=None, capture_gate_passed_by_order=None)` | read-only `GoldenHourFunnel` over the shared measurement store + optional CONSUMED annotations; `.view_for(live_session_id)` |
| `make_measurement_event(event_id, event_code=, live_session_id=, page_id=, order_code=)` | insert one Zone-A `ads_measurement_event` |
| `make_verified_row(event_id, revenue=, order_code=, live_session_id=, page_id=, signals=)` | seed a Zone-A ORDER_VERIFIED + materialize verified revenue + attribution signals (comment_id/messenger_thread_id/psid) |
| `make_dashboard_deps(consumed=None)` | read-only M6.2F `DashboardDeps` over the same store (cross-check the verified-only choke) |
| `measurement_store` | `MeasurementEventStore` — `all`, `materialize` (used to force a bad revenue for the defense-in-depth negative) |

## Boundary / safety asserted by the suite

- **Measure-only (RULE-013/018):** the funnel is a derived read-only projection — no live-session controller, no
  new table, no write/send/scale/publish/order-state/pricing verb.
- **Verified-only revenue, self-enforcing (RULE-003, FAIL-001):** only ORDER_VERIFIED revenue counts; a quote /
  order-created — even one force-carrying a `revenue_value` — is 0.
- **PII masking (RULE-014 / H02):** psid masked on every funnel export; the raw value never reaches an export
  surface; the marker is assembled at runtime (no literal PII in source).
- **Retargeting consent-valid-only (RULE-016)** and **order-capture recorded-not-owned (RULE-021)** exercised by
  the supporting leg tests.
- **No commission (RULE-019), no pricing (M3), no consult (M4), no public reply (M5), no live ops (M7), no
  order-state (M8), no flag flip, no external call, no `04-artifacts/state/` write** anywhere in the suite.

## Build-validation performed in M6-P1803 (attempt 1, collect-only — "do not yet run")

Per the prompt's `<task>` ("Build (do not yet run)"), this attempt ran **collect-only** (imports + collects; **no
assertions executed**). Run with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest 8.4.2**, from
`04-artifacts/impl/M6.2I/`, **no shell redirection** (the role guard blocks a `>`/`2>` co-occurring with the venv
`Scripts` path), cache-free (`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```bash
python.exe -m pytest tests/smoke/test_smk_004_quote_in_golden_hour_funnel_not_revenue.py tests/smoke/test_smk_013_funnel_live_chain_trace.py --collect-only -q -p no:cacheprovider   # per-file: 4,4 ; EXIT=0
python.exe -c "<in-process pytest_collection_finish tally>" --collect-only   # COLLECTED_TOTAL=386 ; EXIT=0
```

Reconciliation: **386** collected = carried M6.2I baseline **378** (351 carried M6.2H tree + 27 coder M6.2I funnel
leg tests) + these new smokes **8**. Both files import + collect clean (funnel fixtures wired). A read-only
adversarial static verification (one verifier per smoke file tracing every assertion through the implementation,
+ a completeness critic) was run alongside — findings are recorded in the M6-P1803 evidence.

> **On counting.** In this harness pytest's terminal summary line is not captured for a long run, so the total
> (**386**) was obtained via an in-process `pytest_collection_finish` tally (`len(session.items)`) with pytest
> RC=0 and the `--collect-only` per-file sum agreeing.

Cache hygiene: `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

> **This build does NOT self-certify gate advancement.** Collect-only proves the smoke files import + collect
> against the frozen M6.2I code; it does not execute assertions. The **formal executed-results recording** is
> produced by **M6-P1804** into `04-artifacts/test-reports/M6.2I/SMOKE_RESULTS.md`. The runner EVIDENCE_GATE and
> the slice Judge decide closure.

## Execution plan for M6-P1804 (`M6_2I_TESTER_RUN`)

Run the full staged suite and the two bound smokes, then record structured results + evidence refs for the M6.2I
exit-gate smoke legs L2 (SMK-004) and L3 (SMK-013):

```bash
python -m pytest -q                    # full staged suite: expected 386 passed
python -m pytest -q tests/smoke/test_smk_004_quote_in_golden_hour_funnel_not_revenue.py tests/smoke/test_smk_013_funnel_live_chain_trace.py   # expected 8 passed
```

## Exit-gate legs (slice M6.2I done-gate, itemized)

| Leg | Requirement | Covered by |
|---|---|---|
| L1 | Golden Hour conversion smoke pass (Ads→…→Verified chain measured PRE→LIVE→POST→CLOSED, live/comment/messenger trace passing) | supporting `test_golden_hour_funnel_chain.py` / `test_golden_hour_state_measure_only.py` + SMK-013 |
| L2 | Smoke M6-SMK-004 executed with recorded result | closed by M6-P1804 (built here) |
| L3 | Smoke M6-SMK-013 executed with recorded result | closed by M6-P1804 (built here) |

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-003 | Only ORDER_VERIFIED / Verified Revenue is revenue; a quote/order-created is a funnel stage, never revenue (SMK-004). |
| M6-RULE-013 | Module 6 measures; it never operates a live session / owns Gateway-Live control (funnel is measure-only). |
| M6-RULE-016 | Retargeting measurement is limited to valid-consent engagement signals (see the register for the full text; supporting `test_retargeting_consent_valid_only.py`). |
| M6-RULE-021 | Order-capture signals are recorded from the consumed Commerce gate; Module 6 never performs/owns that validation. |
| M6-FAIL-001 | Double count / revenue misuse — revenue only from ORDER_VERIFIED, self-enforcing (SMK-004 guard). |
| M6-FAIL-010 | Phase-2 entry without Phase-1 complete — Phase 1 A..H is complete/SIGNED before this first Phase-2 slice. |

## Provenance / notes

- Scenario & expected text quoted **verbatim** from `00-spec/registers/SMOKE_REGISTER.md` (rows M6-SMK-004,
  M6-SMK-013; extract lines 404 / 413). Test patterns reused from the existing `tests/conftest.py` funnel
  fixtures and the coder's `tests/test_quote_in_funnel_not_revenue.py`, `tests/test_live_chain_trace_in_funnel.py`
  (doc working mode, extract line 466).
- No self-certification of PASS or of gate/leg advancement: the runner EVIDENCE_GATE and the slice Judge decide.
  This manifest and the two smoke files are the *build*; the formal executed results are produced in M6-P1804.
