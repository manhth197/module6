# TEST_MANIFEST — Slice M6.2F smoke suite (Dashboard & Data Quality)

| Field | Value |
|---|---|
| Prompt | M6-P1503 — `M6_2F_TESTER_BUILD` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — the smoke tests are AUTHORED here. This attempt ran a **collect-only build-validation** (imports/collects clean, no assertions executed) per the prompt's "Build (do not yet run)"; the **formal executed-results recording** for the exit-gate smoke legs belongs to M6-P1504. |
| Executed by (formal) | M6-P1504 (`M6_2F_TESTER_RUN`) → `04-artifacts/test-reports/M6.2F/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-004, M6-SMK-005, M6-SMK-006, M6-SMK-010, M6-SMK-015** (exactly — per `00-spec/slices/M6.2F.md` "Core smokes" + this prompt's `<smoke_ids>`) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Slice scope | KPI dashboard — the 14 doc §14 metrics, formulas verbatim (M6-CTR-015) · Data Quality Gate (doc §15, M6-CTR-012) + `data_quality_checker` worker (M6-CTR-024, PASS/HOLD/FAIL only) · read-only `GET /api/admin/ads/dashboard` (M6-CTR-018) · Data Mart = support view (RULE-012); per-metric source trace + sample evidence |
| Staging root | `04-artifacts/impl/M6.2F/` (STAGED_ONLY; convention reference, not a live repo) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (owner P0 matrix, extract lines 404/405/406/410/415) |

> **Governance (immutable — nothing in this suite flips a flag):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
> `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False` (M6-OD-002 OPEN → no numeric alert threshold invented),
> `HASH_POLICY_RATIFIED=False`, `SCALE_MODEL_RATIFIED=False` (M6-OD-005 OPEN). Every revenue figure is
> **verified-only** (RULE-003 / FAIL-001) — only the set-once Zone-B `revenue_value` of an ORDER_VERIFIED is
> revenue; a quote / order-draft is never revenue. The Data Mart is a **support view only** (RULE-012 /
> FAIL-005) — no write / CRM / scale / trigger surface. Zone-C DQ transitions are audited, never silent
> (RULE-015). Module 6 records referral/diamond ids for attribution only and NEVER computes a commission
> (RULE-019); no pricing (M3), order-state (M8), CRM send, or Core override (FAIL-004) anywhere.

## What this suite is

The **official M6.2F smoke suite**: exactly one dedicated smoke file per bound smoke id, each carrying the
register's scenario/expected **verbatim**, driven through the M6.2F dashboard + data-quality layer — the
read-only `handle_dashboard_request` (M6-CTR-018), the `DataMart` support view + `ConsumedFacts` (RULE-012), the
14 `compute_metrics` KPIs (M6-CTR-015, formulas verbatim, fail-closed division), and the `DataQualityChecker`
worker + `AdsDataQualityCheck` gate (M6-CTR-024/012, PASS/HOLD/FAIL only) — plus the negative / fail-closed
companions the doc done-gate requires and positive controls for non-vacuity. It reuses the shared fixtures in
[`tests/conftest.py`](04-artifacts/impl/M6.2F/tests/conftest.py) (`make_measurement_event`, `make_conversion`,
`make_verified_row`, `make_dashboard_deps`, `make_data_mart`, `dq_checker`, `attribution_materializer`,
`measurement_store`, `audit`). No new production code, and **no fix to the code under test** (TESTER reports
defects, never fixes them).

All ids are **synthetic**; no raw secret/PII. The negative "revenue on a non-verified event" rows are
constructed as fabricated in-memory events fed straight to the DQ checker — the store would never persist them,
the checker catches them — and carry only synthetic ids (`bad_quote`, `q_as_rev`, `corr_q`, …), no PII.

M6.2F **carried the whole M6.2E tree forward** (cumulatively M6.2A–E, byte-identical) and the coder (M6-P1502)
added the dashboard/DQ implementation with its own leg tests. The carried smokes and regression suites remain
and re-run here as supporting coverage; the **five files below are the new M6.2F-bound smokes** authored by this
prompt (SMK-006 gets a NEW M6.2F *dashboard-render* smoke alongside the carried M6.2E *attribution* smoke, per
the SMK-006 dual binding M6.2E + M6.2F — same pattern used for SMK-003 across M6.2B/M6.2D).

## Smoke → test binding

| Smoke ID | Doc ID | Test file (M6.2F, new) | Nodes | Primary test (scenario verbatim) | Negative / fail-closed & control tests | Rule(s) | Fail gate | Exit leg |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-004 | ADS-P0-004 | [`tests/smoke/test_smk_004_quote_not_revenue.py`](04-artifacts/impl/M6.2F/tests/smoke/test_smk_004_quote_not_revenue.py) | 3 | `test_smk_004_quote_is_not_revenue_and_no_roas` | `..._neg_no_spend_roas_is_fail_closed`, `..._neg_quote_carrying_revenue_is_dq_fail` | M6-RULE-003 | M6-FAIL-001 | L2 |
| M6-SMK-005 | ADS-P0-005 | [`tests/smoke/test_smk_005_order_not_verified_not_revenue.py`](04-artifacts/impl/M6.2F/tests/smoke/test_smk_005_order_not_verified_not_revenue.py) | 4 | `test_smk_005_order_created_not_counted_as_verified_revenue` | `..._neg_draft_conversion_materializes_no_revenue`, `..._neg_draft_carrying_revenue_is_dq_fail`, `..._control_verified_order_is_counted` | M6-RULE-003 | M6-FAIL-001 | L3 |
| M6-SMK-006 | ADS-P0-006 | [`tests/smoke/test_smk_006_dashboard_roas_update.py`](04-artifacts/impl/M6.2F/tests/smoke/test_smk_006_dashboard_roas_update.py) | 4 | `test_smk_006_verified_order_updates_roas_cpa_aov` | `..._neg_absent_spend_fail_closed_roas`, `..._neg_unmapped_spend_excluded`, `..._dashboard_updates_as_more_orders_verify` | M6-RULE-003 | M6-FAIL-001 | L4 |
| M6-SMK-010 | ADS-P0-010 | [`tests/smoke/test_smk_010_data_mart_support_view_only.py`](04-artifacts/impl/M6.2F/tests/smoke/test_smk_010_data_mart_support_view_only.py) | 3 | `test_smk_010_data_mart_exposes_only_read_aggregate_methods` | `..._dashboard_deps_and_view_carry_no_trigger_handle`, `..._neg_reading_dashboard_does_not_mutate_store` | M6-RULE-012 | M6-FAIL-005 | L5 |
| M6-SMK-015 | ADS-P0-015 | [`tests/smoke/test_smk_015_dashboard_quote_draft_not_revenue.py`](04-artifacts/impl/M6.2F/tests/smoke/test_smk_015_dashboard_quote_draft_not_revenue.py) | 4 | `test_smk_015_dashboard_revenue_is_verified_only` | `..._dq_fails_quote_shown_as_revenue`, `..._dq_fails_order_draft_shown_as_revenue`, `..._control_verified_revenue_item_passes` | M6-RULE-003 | M6-FAIL-001 | L6 |

**New M6.2F smoke nodes: 18** (3 + 4 + 4 + 3 + 4).

---

## M6-SMK-004 — Quote created, not ordered → no revenue, no ROAS

Verbatim from `00-spec/registers/SMOKE_REGISTER.md` (extract line 404):

```
Smoke ID:          M6-SMK-004  (Doc ID ADS-P0-004)
Kịch bản:          Quote được tạo nhưng chưa order
Kết quả phải đạt:  Không revenue, không ROAS
```

- **Primary:** a `QUOTE_SENT` with real (mapped) ads spend present yields `Revenue Verified == 0.0`, `ROAS == 0.0`
  (0 verified revenue / spend), `AOV == None` (0 verified orders); the quote still counts in the funnel
  (`Quote Rate` trace `QUOTE_SENT=1…`).
- **Negative — no spend:** with no spend import, `ROAS` is fail-closed `None` (0 / None), never fabricated;
  `Revenue Verified` stays `0.0`.
- **Negative — quote carrying revenue (DQ):** a fabricated `QUOTE_SENT` row carrying a revenue figure FAILs the
  Data Quality Verified-Revenue gate (`overall = FAIL`) — a quote can never be counted as revenue (FAIL-001).

## M6-SMK-005 — Order draft / created, not verified → not Verified Revenue

Verbatim (extract line 405):

```
Smoke ID:          M6-SMK-005  (Doc ID ADS-P0-005)
Kịch bản:          Order Draft / Order Created chưa verified
Kết quả phải đạt:  Không tính Revenue Verified
```

- **Primary:** an `ORDER_CREATED` (not verified) → `Revenue Verified == 0.0`; it counts in the funnel
  denominator only (`Verified Rate == 0.0`, trace `ORDER_VERIFIED=0 / ORDER_CREATED=1`).
- **Negative — draft materialize:** an `ORDER_CREATED` conversion carrying a `revenue_value` materializes NO
  revenue / order_code (the set-once Zone-B writer fires only on ORDER_VERIFIED, RULE-003).
- **Negative — draft carrying revenue (DQ):** a fabricated `ORDER_CREATED` row carrying revenue FAILs the DQ
  Verified-Revenue gate (`overall = FAIL`, FAIL-001).
- **Control:** the SAME dashboard DOES count a genuine `ORDER_VERIFIED` as revenue (non-vacuous).

## M6-SMK-006 — ORDER_VERIFIED full source → ROAS/CPA/AOV dashboard updates (dashboard leg)

Verbatim (extract line 406):

```
Smoke ID:          M6-SMK-006  (Doc ID ADS-P0-006)
Kịch bản:          ORDER_VERIFIED có campaign/adset/ad đầy đủ
Kết quả phải đạt:  ROAS/CPA/AOV dashboard cập nhật
```

This is the **M6.2F dashboard-render leg** of SMK-006 (the smoke binds M6.2E + M6.2F). The carried
[`test_smk_006_order_verified_full_source.py`](04-artifacts/impl/M6.2F/tests/smoke/test_smk_006_order_verified_full_source.py)
(M6.2E) proves the attribution + verified-revenue INPUT; this file proves the ROAS/CPA/AOV dashboard READS it.

- **Primary:** a full campaign/adset/ad ORDER_VERIFIED (revenue 250000, mapped spend 100000) →
  `Revenue Verified 250000`, `Ads Spend 100000`, `ROAS 2.5`, `CPA 100000`, `AOV 250000`, revenue metrics
  evidence-first (`has_trace_and_evidence`), `overall_data_quality == PASS`.
- **Negative — absent spend:** `ROAS`/`CPA` fail-closed `None`; `Revenue Verified`/`AOV` still update.
- **Negative — unmapped spend:** spend with no campaign/adset/ad is excluded → `Ads Spend None`, `ROAS None`.
- **Update:** two verified orders move `CPA` (spend/2), `AOV` (total/2), `ROAS` (total/spend) — the dashboard
  aggregates update as more orders verify.

## M6-SMK-010 — Data Mart cannot trigger CRM/scale → support view only

Verbatim (extract line 410):

```
Smoke ID:          M6-SMK-010  (Doc ID ADS-P0-010)
Kịch bản:          Data Mart tạo trigger CRM/scale
Kết quả phải đạt:  Fail - Data Mart chỉ support view
```

- **Primary:** the `DataMart` public surface ⊆ the read-only aggregate allow-list; it exposes NO
  `write/insert/update/delete/trigger/send/dispatch/scale/publish/enqueue/crm/price/budget` verb — a CRM/scale
  trigger simply cannot be created from it (RULE-012, FAIL-005).
- **Deps/view:** `DashboardDeps` holds only `{mart}` (no transport/store/writer/trigger/crm); the returned
  `DashboardView` carries no write/trigger handle.
- **Negative — read is side-effect-free:** computing the dashboard twice does not mutate the measurement store
  (no trigger side effect).

## M6-SMK-015 — Dashboard showing quote/order-draft as revenue → Fail

Verbatim (extract line 415):

```
Smoke ID:          M6-SMK-015  (Doc ID ADS-P0-015)
Kịch bản:          Dashboard hiển thị quote/order draft như revenue
Kết quả phải đạt:  Fail
```

- **Primary:** with a verified order + a quote + an order-draft in one window, `Revenue Verified` counts ONLY
  the verified order (200000) — the quote/draft can never surface as revenue; `overall_data_quality == PASS`.
- **DQ FAIL — quote as revenue:** the DQ Verified-Revenue gate returns FAIL (`overall = FAIL`) for a quote
  presented as revenue (FAIL-001).
- **DQ FAIL — draft as revenue:** likewise for an `ORDER_CREATED` (even with an order_code) — only
  ORDER_VERIFIED is revenue.
- **Control:** a genuine `ORDER_VERIFIED` (order_code + revenue) PASSES the Verified-Revenue gate — the FAILs are
  discriminating, not a gate that always fails.

---

## Supporting / regression suite (run alongside the five bound smokes)

The full staged suite re-runs. Files below (coder M6-P1502) are **not** the five bound M6.2F smoke ids but pin
the dashboard/DQ layer the smokes rely on.

| File | Purpose | Nodes |
|---|---|---|
| [`tests/test_kpi_formulas_verbatim.py`](04-artifacts/impl/M6.2F/tests/test_kpi_formulas_verbatim.py) | CTR-015 — 14 metrics, formulas verbatim; fail-closed division; CRM/Diamond split; boxes fail-closed | 4 |
| [`tests/test_dashboard_verified_only_revenue.py`](04-artifacts/impl/M6.2F/tests/test_dashboard_verified_only_revenue.py) | SMK-006 leg — verified order → ROAS/CPA/AOV | 1 |
| [`tests/test_dashboard_rejects_unverified_as_revenue.py`](04-artifacts/impl/M6.2F/tests/test_dashboard_rejects_unverified_as_revenue.py) | SMK-015 / FAIL-001 — revenue verified-only; DQ Verified-Revenue FAIL | 2 |
| [`tests/test_data_mart_support_view_only.py`](04-artifacts/impl/M6.2F/tests/test_data_mart_support_view_only.py) | SMK-010 / FAIL-005 — mart/deps read-only only | 2 |
| [`tests/test_quote_not_revenue.py`](04-artifacts/impl/M6.2F/tests/test_quote_not_revenue.py) | SMK-004 leg — quote → no revenue, no ROAS | 1 |
| [`tests/test_order_draft_not_verified.py`](04-artifacts/impl/M6.2F/tests/test_order_draft_not_verified.py) | SMK-005 leg — order-created not verified → not revenue | 1 |
| [`tests/test_data_quality_checker.py`](04-artifacts/impl/M6.2F/tests/test_data_quality_checker.py) | CTR-024/012 — 8 items PASS/HOLD/FAIL; worst roll-up; audited Zone-C; suppression fail-closed | 5 |
| carried M6.2A–E suite | seam/tracking/outbox/integration/attribution smokes + all unit + regression suites | 239 |

## Fixtures reused (from `tests/conftest.py`)

| Fixture | Role |
|---|---|
| `make_measurement_event(event_id, event_code=, page_id=, campaign_id=, adset_id=, ad_id=, customer_id=)` | insert one Zone-A `ads_measurement_event` (revenue/attribution never seeded here) |
| `make_conversion(event_code, source_event_id=, revenue_value=, currency=, order_code=)` | build a `ConversionEvent` (revenue only meaningful for ORDER_VERIFIED) |
| `make_verified_row(event_id, revenue=, order_code=, event_code=, signals=, **event_over)` | seed a Zone-A ORDER_VERIFIED + materialize its set-once Zone-B verified revenue (M6.2E materializer) |
| `make_dashboard_deps(consumed=None)` | read-only `DashboardDeps(mart=DataMart(measurement_store, consumed))` |
| `make_data_mart(consumed=None)` | read-only `DataMart` over the shared measurement store |
| `dq_checker` | `DataQualityChecker(measurement_store, audit)` — `check` / `check_and_record` |
| `measurement_store` | `MeasurementEventStore` — `all`, `get_by_event_id`, set-once `materialize`, audited `set_data_quality_status`, `dq_transitions` |
| `attribution_materializer` | `AttributionMaterializer` — `materialize(...)` (set-once Zone B) |
| `audit` | shared `AuditLog` |

## Boundary / safety asserted by the suite

- **Verified-only revenue (RULE-003, FAIL-001):** every revenue metric sources only the set-once Zone-B
  `revenue_value` of an ORDER_VERIFIED; quote / order-draft never carry revenue; a non-verified figure presented
  as revenue is a DQ Verified-Revenue FAIL (SMK-004/005/015).
- **Support view only (RULE-012, FAIL-005):** the Data Mart / dashboard deps / view expose NO
  write/CRM/scale/trigger surface; reading the dashboard mutates nothing (SMK-010).
- **Fail-closed metrics (M6-OD-002 OPEN):** a zero / missing denominator or absent consumed input yields `None`,
  never a fabricated number; no numeric alert threshold is applied.
- **Audited DQ transitions (RULE-015):** Zone-C `data_quality_status` is written only by the store's audited
  setter via the checker — never a silent edit.
- **No commission (RULE-019), no pricing (M3), no order-state (M8), no CRM send, no Core override (FAIL-004),
  no flag flip, no external call, no `04-artifacts/state/` write** anywhere in the suite.

## Build-validation performed in M6-P1503 (attempt 1, collect-only — "do not yet run")

Per the prompt's `<task>` ("Build (do not yet run)"), this attempt ran **collect-only** (imports + collects the
tests; **no assertions executed**). Run with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest
8.4.2**, from `04-artifacts/impl/M6.2F/`, **no shell redirection** (the role guard blocks a `>`/`2>`
co-occurring with the venv `Scripts` path), cache-free (`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```bash
python.exe -m pytest tests/smoke/test_smk_004_quote_not_revenue.py tests/smoke/test_smk_005_order_not_verified_not_revenue.py tests/smoke/test_smk_006_dashboard_roas_update.py tests/smoke/test_smk_010_data_mart_support_view_only.py tests/smoke/test_smk_015_dashboard_quote_draft_not_revenue.py --collect-only -q -p no:cacheprovider   # per-file: 3,4,4,3,4 ; EXIT=0
python.exe -c "<in-process pytest_collection_finish tally>" --collect-only   # COLLECTED_TOTAL=273 ; EXIT=0
```

Reconciliation: **273** collected = carried M6.2F baseline **255** (239 carried M6.2E tree + 16 coder M6.2F
dashboard/DQ leg tests) + these new smokes **18**. All five files import + collect clean (fixtures wired). A
read-only adversarial static verification (one verifier per smoke file tracing every assertion through the
implementation, + a completeness critic) was run alongside — findings are recorded in the M6-P1503 evidence.

> **On counting.** In this harness pytest's terminal summary line is not captured for a long run, so the total
> (**273**) was obtained via an in-process `pytest_collection_finish` tally (`len(session.items)`) with pytest
> RC=0 and the `--collect-only` per-file sum agreeing.

Cache hygiene: `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

> **This build does NOT self-certify gate advancement.** Collect-only proves the smoke files import + collect
> against the frozen M6.2F code; it does not execute assertions. The **formal executed-results recording** for
> the exit-gate smoke legs is produced by **M6-P1504** into `04-artifacts/test-reports/M6.2F/SMOKE_RESULTS.md`.
> The runner EVIDENCE_GATE and the slice Judge decide closure.

## Execution plan for M6-P1504 (`M6_2F_TESTER_RUN`)

Run the full staged suite and the five bound smokes, then record structured results + evidence refs for the
M6.2F exit-gate smoke legs L2 (SMK-004), L3 (SMK-005), L4 (SMK-006), L5 (SMK-010), L6 (SMK-015):

```bash
python -m pytest -q                    # full staged suite: expected 273 passed
python -m pytest -q tests/smoke/test_smk_004_quote_not_revenue.py tests/smoke/test_smk_005_order_not_verified_not_revenue.py tests/smoke/test_smk_006_dashboard_roas_update.py tests/smoke/test_smk_010_data_mart_support_view_only.py tests/smoke/test_smk_015_dashboard_quote_draft_not_revenue.py   # expected 18 passed
```

The carried M6.2E SMK-006 smoke (`test_smk_006_order_verified_full_source.py`, 4 nodes) also re-runs as
supporting coverage of the SMK-006 attribution input.

## Exit-gate legs (slice M6.2F done-gate, itemized)

| Leg | Requirement | Covered by |
|---|---|---|
| L1 | Dashboard shows verified-only revenue (quote/draft as revenue = FAIL) | SMK-004/005/015 + `test_dashboard_*`/`test_kpi_formulas_verbatim.py` |
| L2 | Smoke M6-SMK-004 executed | closed by M6-P1504 (built here) |
| L3 | Smoke M6-SMK-005 executed | closed by M6-P1504 (built here) |
| L4 | Smoke M6-SMK-006 executed | closed by M6-P1504 (built here) |
| L5 | Smoke M6-SMK-010 executed | closed by M6-P1504 (built here) |
| L6 | Smoke M6-SMK-015 executed | closed by M6-P1504 (built here) |

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-003 | Only ORDER_VERIFIED / Verified Revenue is revenue; quote/draft never counted (SMK-004/005/006/015). |
| M6-RULE-012 | Data Mart / dashboard is a support view; never a trigger owner (SMK-010). |
| M6-RULE-015 | Zone-C data_quality_status transitioned only via the store's audited setter — never a silent edit. |
| M6-RULE-017 | Active suppression must be reflected; unobserved suppression is fail-closed HOLD (DQ suppression item). |
| M6-FAIL-001 | Double count / revenue misuse — revenue only from ORDER_VERIFIED (SMK-004/005/006/015 guard). |
| M6-FAIL-005 | Data Mart used as trigger owner — forbidden; the mart exposes no trigger surface (SMK-010). |

## Provenance / notes

- Scenario & expected text quoted **verbatim** from `00-spec/registers/SMOKE_REGISTER.md` (rows M6-SMK-004,
  M6-SMK-005, M6-SMK-006, M6-SMK-010, M6-SMK-015; extract lines 404/405/406/410/415). Test patterns reused from
  the existing `tests/conftest.py` and the coder's `tests/test_quote_not_revenue.py`,
  `tests/test_order_draft_not_verified.py`, `tests/test_dashboard_verified_only_revenue.py`,
  `tests/test_dashboard_rejects_unverified_as_revenue.py`, `tests/test_data_mart_support_view_only.py`,
  `tests/test_data_quality_checker.py` (doc working mode, extract line 466).
- No self-certification of PASS or of gate/leg advancement: the runner EVIDENCE_GATE and the slice Judge decide.
  This manifest and the five smoke files are the *build*; the formal executed results are produced in M6-P1504.
