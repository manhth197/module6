# M6.2F IMPLEMENTATION NOTES — KPI Dashboard & Data Quality Gate (STAGED)

**Prompt**: M6-P1502 (`M6_2F_CODER_IMPLEMENT`) · **Role**: CODER · **Mode**: `implement` · **Gate**: EVIDENCE_GATE
**Follows**: [PLAN.md](PLAN.md) (M6-P1501). Built item-by-item; one small plan-delta (§4). **Posture unchanged &
immutable**: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `HASH_POLICY_RATIFIED=False`,
`SCALE_MODEL_RATIFIED=False`. No code applies a migration, calls anything external, triggers anything, or flips a flag.

> **Status: coder self-reported PASS** (the runner gate + JUDGE decide, RULE-015). Attribution/verified-only-revenue
> and support-view-only invariants hold; an adversarial self-review (§5) found 2 fail-closed holes in my new code —
> both **FIXED and locked with regressions** before this evidence.

## 1. Staging model — cumulative carry-forward

The whole **M6.2E** tree (239 tests as the slice finally stood after M6-P1403–1409) was carried forward
byte-identical into `04-artifacts/impl/M6.2F/` (caches excluded; `PLAN.md` kept, this file added). Baseline verified
green (239, rc 0) BEFORE any patch. Final suite: **255 passed, rc 0** (239 carried + 16 new). Counts via subprocess.

## 2. Change set (all under `04-artifacts/impl/M6.2F/`)

**New — Dashboard layer**
| File | Purpose |
|---|---|
| `app/measurement/dashboard/data_mart.py` | `DataMart` **support view** — read-only aggregation over the measurement store + injected CONSUMED `ConsumedFacts` (ads_spend w/ campaign mapping, boxes, COD). Exposes ONLY read/aggregate methods — no write/CRM/pricing/Diamond/scale/trigger surface (RULE-012). `verified_rows()` = the single revenue choke: only rows whose set-once Zone-B `revenue_value` is populated (ORDER_VERIFIED path). |
| `app/measurement/dashboard/kpi_metrics.py` | `compute_metrics(mart)` → the **14 CTR-015 metrics, formulas verbatim** (doc §14); revenue metrics verified-only (RULE-003); every division fail-closed (`_safe_div` → None on 0/None denominator). No thresholds (M6-OD-002 OUT). |
| `app/measurement/dashboard/models.py` | `MetricResult` (value + `source_trace` + `sample_evidence_ref`, `has_trace_and_evidence`) + `DashboardView` (14 metrics + overall DQ). Evidence-first (doc §15 Dashboard item). |
| `app/api/dashboard.py` | `handle_dashboard_request(query, deps)` — **CTR-018** read-only handler; `DashboardDeps` holds ONLY the mart (no writer/transport/trigger); untrusted `query` treated as DATA (RULE-H03); overall DQ = FAIL if any displayed value lacks trace+evidence (else PASS). |

**New — Data Quality layer**
| File | Purpose |
|---|---|
| `app/measurement/quality/data_quality_check.py` | `GateItem` (8 doc §15 items) + `GateItemResult` + `AdsDataQualityCheck` (CTR-012); `overall = worst_status(items)` (FAIL>HOLD>PASS via `config.DQ_STATUS_ORDER`). |
| `app/measurement/quality/data_quality_checker.py` | `DataQualityChecker` **worker (CTR-024)** — evaluates the 8 items over a row + `DQContext`; outputs ONLY PASS/HOLD/FAIL; fail-closed (missing signal→HOLD; real violation→FAIL); `check_and_record` transitions Zone-C via the store's audited setter + audits. |

**Patched (carried-forward) + staged migrations/config**
| File | Change |
|---|---|
| `app/measurement/store/measurement_event_store.py` | Add `set_data_quality_status(event_id, status, *, actor, reason, evidence_ref, at)` — the ONLY Zone-C writer (CTR-024); append-only `DataQualityTransition` history (RULE-015); rejects a non-`DataQualityStatus`; Zone A (write-once) + Zone B (`materialize` set-once) + forbidden update/delete untouched. |
| `app/config.py` | `DQ_STATUS_ORDER=("PASS","HOLD","FAIL")` + `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False` (M6-OD-002 OPEN → no threshold invented). |
| `migrations/0007_create_ads_data_quality_check.sql` | Staged DDL (up+down): CTR-012, 8 gate items + overall, CHECK ∈ {PASS,HOLD,FAIL}; never applied. |
| `migrations/0008_create_ads_dashboard_support_view.sql` | Staged read-only **VIEW** DDL (up+down): verified-only revenue (`revenue_value` non-NULL only alongside `order_code`); documented SELECT-only support view (RULE-012). |

## 3. Tests → smoke/leg mapping (TESTER executes L2–L6)

| Test | Proves | Smoke |
|---|---|---|
| `test_dashboard_verified_only_revenue.py` | verified order → ROAS/CPA/AOV update from verified revenue | **SMK-006** (leg 1) |
| `test_quote_not_revenue.py` | quote → no revenue, no ROAS | **SMK-004** |
| `test_order_draft_not_verified.py` | order-created not verified → not revenue | **SMK-005** |
| `test_data_mart_support_view_only.py` | mart/deps expose ONLY read methods (no trigger/write) | **SMK-010** / FAIL-005 |
| `test_dashboard_rejects_unverified_as_revenue.py` | dashboard revenue is verified-only; DQ Verified-Revenue item FAILs on unverified-as-revenue | **SMK-015** / FAIL-001 |
| `test_data_quality_checker.py` | 8 items → PASS/HOLD/FAIL; worst roll-up; audited Zone-C; +suppression fail-closed regression | CTR-024/012 |
| `test_kpi_formulas_verbatim.py` | 14 formulas verbatim; fail-closed division; CRM/Diamond split; +boxes fail-closed regression | CTR-015 |

Smoke EXECUTION (legs L2–L6) is the TESTER's (M6-P1503/1504) — no self-run (RULE-015).

## 4. Plan-delta

- **Per-metric `dq_status` moved to the view level.** The PLAN's `MetricResult` sketch listed a `dq_status`; the
  Data Quality Gate is per measurement-row (registry/consent/…), so the dashboard carries ONE `overall_data_quality`
  (worst of the Dashboard + Verified-Revenue view checks) rather than a per-metric status. More faithful to doc §15;
  everything else matches PLAN §5.

## 5. Adversarial self-review (ultracode) — 2 CONFIRMED, both FIXED

A read-only adversarial review (4 dimensions, each finding re-verified by running the code; 6 agents):
**verified-only-revenue CLEAN, support-view-only CLEAN** (the two fail-gate invariants hold); **2 CONFIRMED**
fail-closed holes in my new code — both fixed and locked:

| # | Dim | Finding (confirmed) | Fix |
|---|---|---|---|
| 1 | dq-states (MEDIUM, RULE-017) | `DQContext.suppression_active` defaulted `False` (not `None`), so an UNOBSERVED suppression signal read as PASS instead of fail-closed HOLD → a row could roll up to overall PASS with suppression never verified. | Made `suppression_active: Optional[bool] = None`; `_suppression` now: None→HOLD, False→PASS, True+reflected→PASS, True+unknown→HOLD, True+not-reflected→FAIL. Regression `test_unobserved_suppression_is_hold_not_pass`. |
| 2 | formulas (LOW) | `verified_boxes()` used `any(...)` — partial `boxes_by_order` coverage fabricated `0` for unreported verified orders (understated Boxes/Order) instead of None, violating the "never fabricated" contract. | Changed to `all(...)`: partial/absent coverage → None (fail-closed). Regression `test_boxes_per_order_fail_closed_on_partial_coverage`. |

Not a gate sign-off — the runner gate + JUDGE (M6-P1509) decide.

## 6. Rollback

Staged only — baseline rollback = delete the M6.2F tree (M6.2E untouched). Per-item: new files → delete; patched
carried-forward files (`measurement_event_store.py`, `config.py`, `tests/conftest.py`) → revert to M6.2E; migrations
0007/0008 → down-DDL DROP (staged; not applied). Zone-C transitions are in-memory + append-only (no hard delete).

## 7. Scope & governance (unchanged)

In scope built: 14 KPI metrics (verbatim), CTR-012 DQ check + CTR-024 worker (PASS/HOLD/FAIL only), CTR-018 read-only
dashboard, per-metric source trace + sample evidence. OUT (not built): alert thresholds (M6-OD-002), scale/Scale-Gate
(M6.2G), learning, real send. Consumed inputs (spend/boxes/COD) read-only, fail-closed. `M6-P1309` verdict stays
BLOCKED (not converted); the mandatory M6.2G re-gate stands before any real scale or external send. Module boundary
intact (no pricing/order-state/commission/CRM). No raw secrets/PII (traces/evidence masked).
