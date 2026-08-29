# TEST_MANIFEST — Slice M6.2J smoke suite (Phase 3 CRM / Diamond / Lifecycle growth)

| Field | Value |
|---|---|
| Prompt | M6-P1903 — `M6_2J_TESTER_BUILD` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — the smoke tests are AUTHORED here. This attempt ran a **collect-only build-validation** (imports/collects clean, no assertions executed) per the prompt's "Build (do not yet run)"; the **formal executed-results recording** belongs to M6-P1904. |
| Executed by (formal) | M6-P1904 (`M6_2J_TESTER_RUN`) → `04-artifacts/test-reports/M6.2J/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-008, M6-SMK-010, M6-SMK-014** (exactly — per `00-spec/slices/M6.2J.md` "Core smokes" + this prompt's `<smoke_ids>`) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Slice scope | measure the Phase 3 growth machine (doc §9): repeat/reorder + CRM revenue (verified-only, consent/eligibility/suppression gated), dormant reactivation, Diamond referral attribution + verified/commission-ready revenue, value-optimization + Learning-Engine growth KPIs; the Data Mart remains a support view |
| Staging root | `04-artifacts/impl/M6.2J/` (STAGED_ONLY; convention reference, not a live repo) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (owner P0 matrix, extract lines 408 / 410 / 414) |

> **Governance (immutable — nothing in this suite flips a flag, and the growth layer only measures):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `SCALE_MODEL_RATIFIED=False`,
> `SCALE_EXECUTION_ENABLED=False`, `LEARNING_AUTOPUBLISH_ENABLED=False`. The growth layer is **measure-only**: it
> never sends CRM (RULE-002 — CRM Messaging owns; no send surface), never computes a commission (RULE-019 —
> Finance owns), never turns the Data Mart into a trigger (RULE-012 / FAIL-005), and never overrides Core/CRM/
> Diamond (FAIL-004). CRM Revenue is **verified-only AND consent/eligibility/suppression gated** — an opt-out /
> expired / missing / scope-not-granted subject is fail-closed excluded (SMK-008 / FAIL-002). Diamond referral
> attribution is recorded with **buyer identity masked** on export (RULE-014 / H02); commission-ready revenue is a
> **revenue figure, never a commission** (SMK-014). No pricing (M3), consult content (M4), public reply (M5), live
> ops (M7), order-state (M8). `status` is an honest self-report; the runner EVIDENCE_GATE and the slice Judge
> (M6-P1909) decide closure.

## What this suite is

The **official M6.2J smoke suite**: one dedicated smoke file per bound smoke id, each carrying the register's
scenario/expected **verbatim**, driven through the M6.2J `growth/` package — `CrmReorderMeasurement` (gated
verified-only CRM revenue, no send surface), `DiamondReferralMeasurement` (referral attribution + verified /
commission-ready revenue, buyer masked, no commission method), the read-only `DataMart` + `GrowthReportBuilder`
(no trigger) — plus the negative / fail-closed companions and non-vacuous controls. It reuses the shared fixtures
in [`tests/conftest.py`](04-artifacts/impl/M6.2J/tests/conftest.py) (`make_crm_measurement`, `make_crm_consent`,
`make_diamond_measurement`, `make_growth_builder`, `make_data_mart`, `make_verified_row`, `measurement_store`). No
new production code, and **no fix to the code under test** (TESTER reports defects, never fixes them).

SMK-010 is **re-bound** in M6.2J (it was M6.2F), so it gets a NEW slice-appropriate **growth-leg** smoke file that
coexists with the carried M6.2F dashboard smoke — the same coexistence pattern used for SMK-006 / SMK-003 / SMK-004
/ SMK-013 across slices.

All ids are **synthetic**; no raw secret/PII. The Diamond buyer-identity marker (`cust_dia_smk14`) is synthetic
and is **masked** on every referral-attribution export.

M6.2J **carried the whole M6.2I tree forward** (cumulatively M6.2A–I, byte-identical) and the coder (M6-P1902)
added the `growth/` package with its own leg tests. The carried smokes and regression suites remain and re-run
here as supporting coverage; the **three files below are the new M6.2J-bound smokes** authored by this prompt.

## Smoke → test binding

| Smoke ID | Doc ID | Test file (M6.2J, new) | Nodes | Primary test (scenario verbatim) | Negative / fail-closed & control tests | Rule(s) | Fail gate | Exit leg |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-008 | ADS-P0-008 | [`tests/smoke/test_smk_008_crm_optout_no_sync.py`](04-artifacts/impl/M6.2J/tests/smoke/test_smk_008_crm_optout_no_sync.py) | 4 | `test_smk_008_crm_optout_excluded_and_no_sync_surface` | `..._neg_expired_or_missing_consent_excluded`, `..._neg_consent_without_crm_scope_excluded`, `..._control_valid_crm_consent_is_counted` | M6-RULE-002 | M6-FAIL-002 | L3 |
| M6-SMK-010 | ADS-P0-010 | [`tests/smoke/test_smk_010_growth_data_mart_support_view_only.py`](04-artifacts/impl/M6.2J/tests/smoke/test_smk_010_growth_data_mart_support_view_only.py) | 3 | `test_smk_010_data_mart_and_growth_expose_no_crm_or_scale_trigger` | `..._neg_growth_report_is_data_only`, `..._neg_building_growth_report_does_not_mutate_store` | M6-RULE-012 | M6-FAIL-005 | L4 |
| M6-SMK-014 | ADS-P0-014 | [`tests/smoke/test_smk_014_diamond_referral_no_commission.py`](04-artifacts/impl/M6.2J/tests/smoke/test_smk_014_diamond_referral_no_commission.py) | 4 | `test_smk_014_verified_referral_records_attribution_and_measures_revenue` | `..._neg_no_commission_method_anywhere`, `..._neg_commission_ready_zero_without_eligibility`, `..._neg_buyer_identity_masked_on_export` | M6-RULE-019 | M6-FAIL-004 | L5 |

**New M6.2J smoke nodes: 11 (4 + 3 + 4).**

---

## M6-SMK-008 — CRM opt-out → no CRM audience/event outbound

Verbatim from `00-spec/registers/SMOKE_REGISTER.md` (extract line 408):

```
Smoke ID:          M6-SMK-008  (Doc ID ADS-P0-008)
Kịch bản:          CRM opt-out
Kết quả phải đạt:  Không sync CRM audience/CRM event outbound
```

- **Primary:** a verified CRM order whose consent is `OPT_OUT` → `crm_revenue() == 0.0` (excluded, fail-closed),
  and the CRM measurement exposes NO `send/sync/dispatch/transport/enqueue/publish/crm_send/send_crm` surface —
  there is no CRM audience/event outbound path at all.
- **Negative — expired / missing:** expired consent, and a missing snapshot entirely, are fail-closed excluded.
- **Negative — scope not granted:** VALID consent granting only `audience_sync` (not the CRM scope) is excluded.
- **Control:** a VALID CRM-scope consent + eligibility + suppression → `crm_revenue() == 250000` (non-vacuous —
  the exclusions are consent/suppression-caused).

## M6-SMK-010 — Data Mart / growth cannot trigger CRM/scale → support view only

Verbatim (extract line 410):

```
Smoke ID:          M6-SMK-010  (Doc ID ADS-P0-010)
Kịch bản:          Data Mart tạo trigger CRM/scale
Kết quả phải đạt:  Fail - Data Mart chỉ support view
```

This is the **M6.2J growth leg** of SMK-010 (the carried M6.2F dashboard smoke
[`test_smk_010_data_mart_support_view_only.py`](04-artifacts/impl/M6.2J/tests/smoke/test_smk_010_data_mart_support_view_only.py)
proves the dashboard side).

- **Primary:** neither the `DataMart` nor the `GrowthReportBuilder` exposes a
  `trigger/send/sync/crm_send/scale/set_price/publish/commission/order_state/write/insert/update/delete` verb; the
  built report has `kpis` and no trigger (RULE-012 / FAIL-005).
- **Negative — data-only:** the growth report export is a plain dict of KPIs, no trigger handle.
- **Negative — read is side-effect-free:** building the growth report twice does not mutate the measurement store.

## M6-SMK-014 — Diamond referral order verified → referral attribution, no commission

Verbatim (extract line 414):

```
Smoke ID:          M6-SMK-014  (Doc ID ADS-P0-014)
Kịch bản:          Diamond referral order verified
Kết quả phải đạt:  Gắn referral attribution, không tự tính commission
```

- **Primary:** a verified Diamond referral order → `referral_attributions()` records `referral_link_id` +
  `order_code`; `diamond_revenue()` (verified-only) and `commission_ready_revenue()` (commission-eligible verified
  revenue) are MEASURED; the measurement exposes NO
  `commission/compute_commission/commission_amount/commission_rate/payout/...` method (RULE-019).
- **Negative — no commission method:** absent even with no data wired (the surface itself is absent).
- **Negative — commission-ready fail-closed:** with no consumed eligibility, `commission_ready_revenue() == 0.0`;
  `diamond_revenue()` still measured.
- **Negative — buyer masked:** `to_public()["buyer_ref"]` is masked; the raw buyer id never reaches the export.

---

## Supporting / regression suite (run alongside the three bound smokes)

The full staged suite re-runs. Files below (coder M6-P1902) are **not** the three bound M6.2J smoke ids but pin the
growth layer the smokes rely on.

| File | Purpose | Nodes |
|---|---|---|
| [`tests/test_crm_optout_excluded.py`](04-artifacts/impl/M6.2J/tests/test_crm_optout_excluded.py) | SMK-008 leg — opt-out/expired/missing/scope-not-granted excluded; no send surface | 4 |
| [`tests/test_crm_reorder_revenue_verified_only.py`](04-artifacts/impl/M6.2J/tests/test_crm_reorder_revenue_verified_only.py) | RULE-002/003 — CRM revenue verified-only + gated; click/CRM_REORDER_SENT never revenue; repeat rate | 5 |
| [`tests/test_data_mart_stays_support_view.py`](04-artifacts/impl/M6.2J/tests/test_data_mart_stays_support_view.py) | SMK-010 leg — Data Mart + growth builder expose no trigger; report data-only | 3 |
| [`tests/test_diamond_referral_no_commission.py`](04-artifacts/impl/M6.2J/tests/test_diamond_referral_no_commission.py) | SMK-014 leg — referral attribution; verified/commission-ready revenue; no commission; buyer masked; lead rate | 5 |
| [`tests/test_reactivation_consent_eligibility_failclosed.py`](04-artifacts/impl/M6.2J/tests/test_reactivation_consent_eligibility_failclosed.py) | RULE-002 — reactivation counts only consent-valid + CRM-eligible; opt-out/ineligible excluded | 4 |
| [`tests/test_growth_kpis_from_valid_signals_only.py`](04-artifacts/impl/M6.2J/tests/test_growth_kpis_from_valid_signals_only.py) | doc §9 KPIs each from valid signals; fail-closed None; unwired-reactivation fails closed | 3 |
| [`tests/test_growth_measure_only_boundary.py`](04-artifacts/impl/M6.2J/tests/test_growth_measure_only_boundary.py) | boundary — no send/commission/member-rights/scale/publish/order-state/trigger verb | 4 |
| carried M6.2A–I suite | seam/tracking/outbox/integration/attribution/dashboard/DQ/scale/learning/funnel smokes + all unit + regression suites | 386 |

## Fixtures reused (from `tests/conftest.py`)

| Fixture | Role |
|---|---|
| `make_crm_measurement(consumed=None)` | `CrmReorderMeasurement(measurement_store, consent_gate, consumed)` — gated verified-only CRM revenue |
| `make_crm_consent(snapshot_id=, subject=, state="VALID", scopes=("crm",))` | build a `ConsentSnapshot` with a chosen state + scope set |
| `make_diamond_measurement(consumed=None)` | `DiamondReferralMeasurement(measurement_store, consumed)` — referral attribution + verified/commission-ready revenue |
| `make_growth_builder(...)` | `GrowthReportBuilder` over the data mart + crm/diamond/reactivation (read-only) |
| `make_data_mart(consumed=None)` | read-only `DataMart` (support view) |
| `make_verified_row(event_id, revenue=, order_code=, signals=, customer_id=)` | seed a Zone-A ORDER_VERIFIED + materialize verified revenue + attribution signals (crm / referral_link_id / diamond_id) |
| `measurement_store` | `MeasurementEventStore` — `all` (used to assert the growth read is side-effect-free) |

## Boundary / safety asserted by the suite

- **Consent-gated CRM revenue (RULE-002, FAIL-002):** opt-out / expired / missing / scope-not-granted subjects are
  fail-closed excluded; the CRM layer has no send/sync surface.
- **Support view only (RULE-012, FAIL-005):** the Data Mart + growth builder expose no trigger; the growth report
  is read-only data; building it mutates nothing.
- **No commission (RULE-019):** the Diamond layer records referral attribution + measures verified / commission-
  ready revenue but computes NO commission amount/rate/payout; buyer identity masked (RULE-014 / H02).
- **No Core override (FAIL-004), no pricing (M3), no consult (M4), no public reply (M5), no order-state (M8), no
  flag flip, no external call, no `04-artifacts/state/` write** anywhere in the suite.

## Build-validation performed in M6-P1903 (attempt 1, collect-only — "do not yet run")

Per the prompt's `<task>` ("Build (do not yet run)"), this attempt ran **collect-only** (imports + collects; **no
assertions executed**). Run with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest 8.4.2**, from
`04-artifacts/impl/M6.2J/`, **no shell redirection** (the role guard blocks a `>`/`2>` co-occurring with the venv
`Scripts` path), cache-free (`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```bash
python.exe -m pytest tests/smoke/test_smk_008_crm_optout_no_sync.py tests/smoke/test_smk_010_growth_data_mart_support_view_only.py tests/smoke/test_smk_014_diamond_referral_no_commission.py --collect-only -q -p no:cacheprovider   # per-file: 4,3,4 ; EXIT=0
python.exe -c "<in-process pytest_collection_finish tally>" --collect-only   # COLLECTED_TOTAL=425 ; EXIT=0
```

Reconciliation: **425** collected = carried M6.2J baseline **414** (386 carried M6.2I tree + 28 coder M6.2J growth
leg tests) + these new smokes **11**. All three files import + collect clean (growth fixtures wired). A read-only
adversarial static verification (one verifier per smoke file tracing every assertion through the implementation, +
a completeness critic) was run alongside — findings are recorded in the M6-P1903 evidence.

> **On counting.** In this harness pytest's terminal summary line is not captured for a long run, so the total
> (**425**) was obtained via an in-process `pytest_collection_finish` tally (`len(session.items)`) with pytest
> RC=0 and the `--collect-only` per-file sum agreeing.

Cache hygiene: `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

> **This build does NOT self-certify gate advancement.** Collect-only proves the smoke files import + collect
> against the frozen M6.2J code; it does not execute assertions. The **formal executed-results recording** is
> produced by **M6-P1904** into `04-artifacts/test-reports/M6.2J/SMOKE_RESULTS.md`. The runner EVIDENCE_GATE and
> the slice Judge decide closure.

## Execution plan for M6-P1904 (`M6_2J_TESTER_RUN`)

Run the full staged suite and the three bound smokes, then record structured results + evidence refs for the M6.2J
exit-gate smoke legs L3 (SMK-008), L4 (SMK-010), L5 (SMK-014):

```bash
python -m pytest -q                    # full staged suite: expected 425 passed
python -m pytest -q tests/smoke/test_smk_008_crm_optout_no_sync.py tests/smoke/test_smk_010_growth_data_mart_support_view_only.py tests/smoke/test_smk_014_diamond_referral_no_commission.py   # expected 11 passed
```

## Exit-gate legs (slice M6.2J done-gate, itemized)

| Leg | Requirement | Covered by |
|---|---|---|
| L1 | CRM revenue verified (only from eligibility + suppression + ORDER_VERIFIED; clicks/chats never revenue) | SMK-008 + `test_crm_reorder_revenue_verified_only.py` |
| L2 | Diamond revenue verified (referral attribution; commission measured-not-computed) | SMK-014 + `test_diamond_referral_no_commission.py` |
| L3 | Smoke M6-SMK-008 executed with recorded result | closed by M6-P1904 (built here) |
| L4 | Smoke M6-SMK-010 executed with recorded result | closed by M6-P1904 (built here) |
| L5 | Smoke M6-SMK-014 executed with recorded result | closed by M6-P1904 (built here) |

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-002 | External measurement/audience/CRM requires valid consent; opt-out fail-closed (SMK-008). |
| M6-RULE-012 | Data Mart / growth is a support view; never a trigger owner (SMK-010). |
| M6-RULE-019 | Module 6 never computes commission; it records referral attribution + measures revenue (SMK-014). |
| M6-FAIL-002 | Sending/counting without valid consent — opt-out excluded, no send surface (SMK-008 guard). |
| M6-FAIL-004 | Core/CRM/Diamond override — the growth layer reads consumed facts, never overrides them. |
| M6-FAIL-005 | Data Mart used as trigger owner — forbidden; no trigger surface (SMK-010 guard). |

## Provenance / notes

- Scenario & expected text quoted **verbatim** from `00-spec/registers/SMOKE_REGISTER.md` (rows M6-SMK-008,
  M6-SMK-010, M6-SMK-014; extract lines 408 / 410 / 414). Test patterns reused from the existing `tests/conftest.py`
  growth fixtures and the coder's `tests/test_crm_optout_excluded.py`, `tests/test_data_mart_stays_support_view.py`,
  `tests/test_diamond_referral_no_commission.py` (doc working mode, extract line 466).
- No self-certification of PASS or of gate/leg advancement: the runner EVIDENCE_GATE and the slice Judge decide.
  This manifest and the three smoke files are the *build*; the formal executed results are produced in M6-P1904.
