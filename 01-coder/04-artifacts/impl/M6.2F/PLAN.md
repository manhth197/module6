# M6.2F IMPLEMENTATION PLAN — KPI Dashboard & Data Quality Gate (STAGED, plan-only)

**Prompt**: M6-P1501 (`M6_2F_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code this prompt)
**Slice**: M6.2F — ship the KPI dashboard (locked formulas, doc §14 = CTR-015) and the Data Quality Gate
(doc §15 = CTR-012 / CTR-024) with **metric-level source trace**; the data mart stays a **support view**
(RULE-012). Depends on M6.2E. **Done gate**: *Dashboard shows verified-only revenue* — any quote/order-draft
displayed as revenue is an immediate **FAIL** (FAIL-001, SMK-015).
**Posture (immutable)**: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
`HASH_POLICY_RATIFIED=False`, `SCALE_MODEL_RATIFIED=False`. This plan writes no code, applies no migration, calls
nothing external, resolves no owner decision, flips no flag.

---

## 1. Entry-gate verification

| Precondition | Source | Result |
|---|---|---|
| This prompt RUNNING | ledger row (order 127) | **M6-P1501 = RUNNING** ✓ |
| Dependency resolved | ledger | **M6-P1500 = SIGNED** (entry judge PASS, opens M6.2F STAGED) ✓; M6.2E slice gate **M6-P1409 = SIGNED** ✓ |
| Target LOCKED + M6-OD-011 | manifest | `status=LOCKED`, `workspace_mode=STAGED_ONLY`, safety all false; M6-OD-011 **DECIDED** ✓ |
| Slice contracts | M6-P1500 evidence + CONTRACT_REGISTER | **CTR-015** = DRAFT_LOCKED (14 formulas verbatim, MONITORING_REGISTER / doc §14; thresholds = M6-OD-002 OUT); **CTR-012 / CTR-018 / CTR-024** = MISSING but harmonized-for-entry (producers M6-P0708 / M6-P0712 / M6-P0713 PASS, gate M6-P0715 SIGNED) ✓ |
| Forward/OPEN owner decisions | DECISION_REGISTER | M6-OD-002 (thresholds) OUT; M6-OD-005 (scale model) forward→M6.2G; M6-OD-008 (PAYMENT_COMPLETED) blocks the **edge-handling** leg only — RULE-003 already fixes verified-only revenue, so it does not gate this slice (per M6-P1500) ✓ |
| Flags | manifest/brief | BLOCKED/OFF/OFF, HASH_POLICY_RATIFIED=False, SCALE_MODEL_RATIFIED=False, live_migrations=false ✓ |
| M6.2E foundation | `04-artifacts/impl/M6.2E/` (223 tests green) | present; measurement store (Zone-B `revenue_value` set-once from ORDER_VERIFIED), `DataQualityStatus` enum (PASS/HOLD/FAIL, initial HOLD), attribution context — carried forward per §2 ✓ |

**Conclusion**: open for **STAGED** M6.2F. Dashboard + DQ gate over the existing measurement store; no thresholds,
no scale, no send; verified-only revenue is the load-bearing done-gate.

---

## 2. Working mode, conventions & staging model

Reuse the M6.2A–E baseline (pytest, frozen dataclasses, read-only ports + in-memory staged adapters, framework-
neutral pure request handlers, staged migrations up+down, workers as plain callables, forgiving-seam, mask-on-
export). **Cumulative snapshot**: the whole **M6.2E** tree (223 tests) is carried forward byte-identical; M6.2F
**adds** the Dashboard + Quality layers and **patches** the store with an audited Zone-C transition. The change
set (§5) is the diff; carried-forward files touched are noted (§9). Nothing sends; nothing scales; nothing
triggers. `external_send=OFF` immutable.

---

## 3. Scope lock (anchored strictly to `00-spec/slices/M6.2F.md`)

**In scope (5 capabilities):**
1. **All 14 doc §14 metrics with formulas verbatim** (CTR-015) — see §4.1 (reproduced verbatim from
   `registers/MONITORING_REGISTER.md`).
2. **`ads_data_quality_check` output PASS/HOLD/FAIL** (CTR-012) — the 8 doc §15 gate items, worst-status roll-up.
3. **`data_quality_checker` worker** (CTR-024) — evaluates the 8 items; outputs **ONLY** PASS/HOLD/FAIL
   (nothing beyond the three states, doc §9 must-not-do); audited Zone-C transition on the measurement row.
4. **GET /api/admin/ads/dashboard** (CTR-018) — read-only on the data mart / support view; never writes, never
   triggers (RULE-012); returns the 14 metrics + DQ status.
5. **Sample evidence + trace per metric** — every metric carries a `source_trace` + a `sample_evidence` ref
   (evidence-first; a visual-only metric with no trace is a Dashboard-DQ **FAIL**, doc §15 L308).

**Out of scope (explicit):**
- **Alert thresholds** (M6-OD-002 OPEN) — metrics compute VALUES only; NO numeric alert/threshold logic. The 8
  DQ gate items are **structural** (registry/consent/dedup/identity/attribution/verified-revenue/suppression/
  dashboard-trace) and need no threshold.
- **Scale decisions / Scale Gate / scale-request** (M6.2G; CTR-013/019/026, RULE-010) — not built here.
- **Learning** (M6.2H+), **alerts/notifications**, **connector/real send** (M6-OD-003/004; external_send=OFF).
- **No trigger ownership** from the data mart/dashboard: never CRM, pricing, Diamond, or budget scale
  (RULE-012, FAIL-005, SMK-010). **No commission** (RULE-019, Finance). **No order-state / QuoteSnapshot write.**
- **Ads Spend / boxes / COD / suppression** are **CONSUMED** staged inputs (Ads-platform / Commerce / CRM own
  them) — M6 READS them for metrics, never computes or writes them; absent input ⇒ fail-closed (metric HOLD /
  value `None`), never fabricated.

---

## 4. Locked contract content (reproduced so the implementer builds to the exact spec)

### 4.1 CTR-015 — the 14 KPI metrics (VERBATIM, doc §14 / MONITORING_REGISTER)

| # | Chỉ số | Công thức / nguồn | Ghi chú | Revenue-bearing? (RULE-003) |
|---|---|---|---|---|
| 1 | Ads Spend | Từ Ads platform / approved spend import | Phải có campaign/adset/ad mapping | consumed (import) |
| 2 | Revenue Verified | SUM(verified_revenue) | Chỉ ORDER_VERIFIED | **YES** — verified-only |
| 3 | ROAS | Revenue Verified / Ads Spend | Không dùng order chưa verified | **YES** |
| 4 | CPA | Ads Spend / number_of_ORDER_VERIFIED | Theo campaign/adset/ad/live/session | count of verified |
| 5 | AOV | Revenue Verified / verified_orders | Theo verified order | **YES** |
| 6 | Boxes per Order | Verified boxes / verified_orders | Mục tiêu tăng AOV | verified-only (boxes consumed) |
| 7 | Comment Rate | LIVE_COMMENT / LIVE_VIEW | Top funnel | event-count ratio |
| 8 | Inbox Rate | MESSENGER_STARTED / LIVE_COMMENT | Handoff quality | event-count ratio |
| 9 | Quote Rate | QUOTE_SENT / MESSENGER_STARTED | AI + Commerce quote efficiency | event-count ratio |
| 10 | Order Rate | ORDER_CREATED / QUOTE_SENT | Sales conversion | event-count ratio |
| 11 | Verified Rate | ORDER_VERIFIED / ORDER_CREATED | Payment/COD/fulfillment quality | count ratio |
| 12 | COD Fail Rate | COD fail / COD orders | Rủi ro vận hành | consumed (Commerce) |
| 13 | CRM Revenue | Verified revenue từ CRM attribution | Lifecycle value | **YES** — verified + entry_channel=CRM |
| 14 | Diamond Revenue | Verified revenue từ referral/Diamond attribution | Growth multiplier | **YES** — verified + referral/diamond |

**Verified-only invariant (RULE-003, FAIL-001):** every revenue-bearing metric (2,3,5,6,13,14) reads ONLY the
set-once Zone-B `revenue_value` — which M6.2E populates ONLY on the ORDER_VERIFIED path. Quote / cart / order-
draft / payment-waiting / COD-waiting contribute **zero** revenue and **no** ROAS (SMK-004/005/015). Thresholds
(M6-OD-002) are NOT applied.

### 4.2 CTR-012 / doc §15 — Data Quality Gate (8 items, VERBATIM)

| Gate Item | PASS khi | FAIL/HOLD khi |
|---|---|---|
| Event Registry | Event code tồn tại, owner rõ, schema đúng | Unknown event, event không có owner |
| Consent | Consent valid tại thời điểm event/external send | Missing/expired/opt-out |
| Dedup | No duplicate hoặc duplicate được merge chính xác | Pixel/CAPI/Offline double count |
| Identity | guest/customer/order mapping rõ | Guest merge sai hoặc order không map được |
| Attribution | campaign/adset/ad/page/live/messenger chain đủ | Nguồn mơ hồ, conflict không xử lý |
| Verified Revenue | Revenue lấy từ Commerce Verified Revenue | Quote/order draft/unpaid được tính revenue |
| Suppression | Recall/Sale Lock/CRM suppression được phản ánh | Scale khi đang bị lock/suppression |
| Dashboard | Metric có sample evidence và trace | Dashboard chỉ là visual không có source trace |

**Roll-up:** overall `data_quality_status` = **worst status** across the 8 items (FAIL > HOLD > PASS)
(ARCH_BASELINE §1.6). The worker outputs **only** PASS/HOLD/FAIL. HOLD/FAIL rows are never scale evidence
(RULE-009; scale is M6.2G).

---

## 5. Minimal change set (all target-relative, staged under `04-artifacts/impl/M6.2F/`)

Legend: **Leg** = M6.2F exit-gate leg (L1 = *dashboard verified-only revenue*). Rollback: new files → delete;
patched carried-forward files → revert to M6.2E.

### 5.1 New — the Dashboard layer

| # | Target file (new) | Purpose | Contract/Rule | Leg | Smoke |
|---|---|---|---|---|---|
| D1 | `app/measurement/dashboard/__init__.py` | package marker | — | — | — |
| D2 | `app/measurement/dashboard/data_mart.py` | `DataMart` **support view** — READ-ONLY aggregation over the measurement store (verified rows, counts, entry_channel/referral) + injected CONSUMED staged sources (`AdsSpendSource`, boxes, COD, event-code counts). Exposes ONLY read/aggregate methods; deliberately NO write / CRM / pricing / Diamond / scale / trigger method (RULE-012). Verified-revenue aggregate filters to Zone-B `revenue_value` set (ORDER_VERIFIED) — the single revenue choke. | CTR-018/015; **RULE-012** | L1 | **SMK-010** |
| D3 | `app/measurement/dashboard/kpi_metrics.py` | `compute_metrics(mart)` → the **14 CTR-015 metrics, formulas verbatim** (§4.1); each a pure function over the mart aggregates; revenue metrics verified-only (RULE-003); division fail-closed (denominator 0 → `None`/HOLD, never crash, never fabricate). NO thresholds (M6-OD-002 OUT). | CTR-015; **RULE-003** | **L1** | **SMK-004/005/006/015** |
| D4 | `app/measurement/dashboard/models.py` | `MetricResult{name, formula, value, unit, source_trace, sample_evidence_ref, dq_status}` (frozen; PII masked in trace/evidence) + `DashboardView{metrics[14], overall_dq, generated_at}`. `source_trace` names the inputs+formula; `sample_evidence_ref` is a masked example (correlation_id/event_id) — evidence-first (doc §15 Dashboard item). | CTR-015/025; RULE-014 | L1 | SMK-006 |
| D5 | `app/api/dashboard.py` | `handle_dashboard_request(query, deps)` — **CTR-018 GET /api/admin/ads/dashboard**: framework-neutral, READ-ONLY over `DataMart`; returns the 14 metrics + per-metric trace/evidence + overall DQ; masks PII; NEVER writes, NEVER triggers (RULE-012); a revenue figure is verified-only (SMK-015). Read-only `DashboardDeps` (mart + metrics + dq view; no Transport, no store-writer). | CTR-018; RULE-012/003 | L1 | **SMK-015/006/010** |

### 5.2 New — the Data Quality layer

| # | Target file (new) | Purpose | Contract/Rule | Leg | Smoke |
|---|---|---|---|---|---|
| Q1 | `app/measurement/quality/__init__.py` | package marker | — | — | — |
| Q2 | `app/measurement/quality/data_quality_check.py` | `GateItem` enum (the 8 doc §15 items) + `GateItemResult{item, status, detail, evidence_ref}` + `AdsDataQualityCheck{items[8], overall}` (CTR-012); `overall = worst(items)` (FAIL>HOLD>PASS). Frozen; PII masked. | CTR-012; RULE-009 | L1 | (SMK-004/005/015) |
| Q3 | `app/measurement/quality/data_quality_checker.py` | `DataQualityChecker` **worker (CTR-024)**: `check(event, context)` evaluates the 8 gate items (registry/consent/dedup/identity/attribution/verified-revenue/suppression/dashboard-trace) over a measurement row + consumed context, returns an `AdsDataQualityCheck` whose overall is **ONLY** PASS/HOLD/FAIL (nothing beyond, doc §9); then transitions the row's Zone-C status via the store's audited setter (B5). Verified-Revenue item FAILs if a non-verified figure is counted as revenue (RULE-003). Suppression item reflects a consumed recall/sale-lock/CRM-suppression flag (RULE-017); fail-closed. | CTR-024; **RULE-003/017/009/015** | **L1** | SMK-004/005/006/015 |

### 5.3 Patched (carried-forward) + staged migrations/config

| # | Target file | Change | Contract/Rule | Leg | Rollback |
|---|---|---|---|---|---|
| B5 | `app/measurement/store/measurement_event_store.py` (**patched**) | Add `set_data_quality_status(event_id, status, *, actor, reason, evidence_ref)` — the **ONLY** Zone-C writer (CTR-024); audited PASS/HOLD/FAIL lifecycle (append an audit record; never a silent edit); leaves Zone-A write-once + `materialize()` (Zone-B set-once) + forbidden update/delete untouched (RULE-007/008). | CTR-001/024; RULE-007/008/015 | L1 | revert to M6.2E |
| M1 | `migrations/0007_create_ads_data_quality_check.sql` (new) | Staged DDL (up+down): `ads_data_quality_check` (CTR-012) — the 8 gate-item results + overall status + evidence refs + a CHECK constraint `overall IN ('PASS','HOLD','FAIL')`; never applied. | CTR-012 | L1 | down-DDL DROP; delete |
| M2 | `migrations/0008_create_ads_dashboard_support_view.sql` (new) | Staged **read-only VIEW** DDL (up+down) over `ads_measurement_events` for the KPI/data-mart read path — documented as a **support view** (RULE-012: read-only, no trigger); an explanatory comment that verified revenue is `revenue_value WHERE order_code IS NOT NULL` (verified-only). Never applied. | CTR-018/015; RULE-012/003 | L1 | down-DDL DROP; delete |
| A1 | `app/config.py` (**extend**) | Add `DQ_STATUS_ORDER = ("PASS","HOLD","FAIL")` (worst-status ordering constant) + a comment that alert thresholds are **M6-OD-002 OPEN → none defined here** (fail-closed: no numeric threshold invented). No enabling flag touched. | RULE-009 | L1 | revert to M6.2E |

---

## 6. Test plan → done-gate / smoke mapping (`pytest -q`; TESTER executes L2–L6)

Fixtures extend `conftest.py` with a `DataMart` seeded from staged measurement rows (verified + non-verified),
consumed staged sources (ads_spend with campaign mapping, boxes, COD, funnel event counts, suppression flag), a
`DataQualityChecker`, and `DashboardDeps`. Carried-forward M6.2E **223 tests stay green**. PII markers assembled
at runtime (no literal PII in source).

| # | Target test (new) | Proves | Leg | Smoke | Fail-gate |
|---|---|---|---|---|---|
| T1 | `tests/test_dashboard_verified_only_revenue.py` | **leg 1 / SMK-006**: an ORDER_VERIFIED with full campaign/adset/ad → Revenue Verified / ROAS / CPA / AOV computed from verified revenue; the dashboard updates. | **L1** | **SMK-006** | FAIL-001 |
| T2 | `tests/test_quote_not_revenue.py` | **SMK-004**: a QUOTE_SENT with no verified order → Revenue Verified = 0, ROAS not computed from it (no revenue, no ROAS). | L1 | **SMK-004** | FAIL-001 |
| T3 | `tests/test_order_draft_not_verified.py` | **SMK-005**: ORDER_CREATED / order-draft not verified → NOT counted as Verified Revenue (contributes to Order Rate funnel count only). | L1 | **SMK-005** | FAIL-001 |
| T4 | `tests/test_data_mart_support_view_only.py` | **SMK-010 / FAIL-005**: `DataMart` (and the dashboard handler) expose ONLY read/aggregate methods — no CRM/pricing/Diamond/scale/trigger surface; an attempt to use it as a trigger owner has no method / is refused (RULE-012). | **L1** | **SMK-010** | **FAIL-005** |
| T5 | `tests/test_dashboard_rejects_unverified_as_revenue.py` | **SMK-015 / FAIL-001**: a quote/order-draft can NEVER appear as a revenue figure; dashboard revenue == verified-only; the Verified-Revenue DQ item FAILs if a non-verified figure is presented as revenue. | **L1** | **SMK-015** | **FAIL-001** |
| T6 | `tests/test_data_quality_checker.py` | **CTR-024/012**: the 8 gate items → PASS/HOLD/FAIL; **worst-status** roll-up (one FAIL → overall FAIL; one HOLD, no FAIL → HOLD); output is NEVER anything beyond the three states; Zone-C transition is audited (set once via the store). | L1 | (SMK-004/005/015) | FAIL-001 |
| T7 | `tests/test_kpi_formulas_verbatim.py` | **CTR-015**: all 14 metrics compute per their locked formulas (funnel ratios; revenue metrics verified-only; CRM/Diamond by attribution); each `MetricResult` carries `source_trace` + `sample_evidence_ref`; a zero denominator is fail-closed (`None`), never a crash; NO threshold applied. | L1 | SMK-006 | FAIL-001 |

**Smoke → test binding**: SMK-004 = T2; SMK-005 = T3; SMK-006 = T1(+T7); SMK-010 = T4; SMK-015 = T5. Execution +
recorded results/evidence (legs L2–L6) is the **TESTER**'s (M6-P1503/1504). No self-run / self-certify (RULE-015).

---

## 7. Master traceability matrix

| Item | Files | Contract | Rule(s) | Leg | Smoke | Fail-gate | Rollback |
|---|---|---|---|---|---|---|---|
| Data Mart support view | D2 | CTR-018/015 | RULE-012 | L1 | SMK-010 | FAIL-005 | delete |
| 14 KPI metrics (verbatim) | D3,D4 | CTR-015 | RULE-003 | **L1** | SMK-004/005/006/015 | FAIL-001 | delete |
| Dashboard API (read-only) | D5 | CTR-018 | RULE-012/003 | **L1** | SMK-015/006/010 | FAIL-001/005 | delete |
| ads_data_quality_check | Q2 | CTR-012 | RULE-009 | L1 | (SMK-004/005/015) | FAIL-001 | delete |
| data_quality_checker worker | Q3 | CTR-024 | RULE-003/017/009/015 | **L1** | SMK-004/005/006/015 | FAIL-001 | delete |
| Zone-C audited transition | B5 | CTR-001/024 | RULE-007/008/015 | L1 | — | — | revert store |
| Migrations + config | M1,M2,A1 | CTR-012/018 | RULE-012/003/009 | L1 | — | — | down-DDL / revert |
| Tests | T1–T7 | — | — | L1 (+L2–L6 runnable) | SMK-004/005/006/010/015 | FAIL-001/005 | delete |

**Legs**: L1 ✓ (dashboard verified-only revenue + all the above); L2–L6 ✓ *made runnable* (TESTER executes
SMK-004/005/006/010/015); L7 (evidence — process), L8 (judge — process), **L9 ✓ (this doc — rollback per item)**.

---

## 8. Rollback strategy (global)

1. **Nothing live.** Staged under `04-artifacts/impl/M6.2F/`; no migration applied, no external call, no
   trigger, no flag written. Baseline rollback = delete the M6.2F tree (M6.2E untouched).
2. **Per-item** (§5): new files → delete; patched carried-forward files (`measurement_event_store.py`,
   `config.py`, `conftest.py`) → revert to their M6.2E version.
3. **Migrations** M1/M2 → down-DDL DROP (staged; not executed). The Zone-C transition is audited & reversible in
   staging (in-memory); no historical row is hard-deleted (RULE-007).

---

## 9. Plan-deltas & notes

- **`measurement_event_store.py` gains `set_data_quality_status()` (Zone-C)** — carried-forward patch. This is the
  ONLY DQ-status writer (CTR-024); the frozen row + `materialize()` (Zone-B set-once) + forbidden update/delete
  stay. Per the 0002 DDL comment, Zone C is transitioned ONLY by the data_quality_checker, every transition
  audited; the store enforces that.
- **Consumed staged inputs** (Ads Spend, boxes, COD, funnel event counts, suppression flag) are injected read-only
  ports/dataclasses — M6 READS them, never computes/writes (measure-only). Ads Spend requires campaign/adset/ad
  mapping (doc §14 note); absent/unmapped ⇒ the dependent metric is fail-closed (`None`/HOLD), never fabricated.
- **Data Mart is a support view (RULE-012, FAIL-005, SMK-010)** — the single most load-bearing boundary here: the
  `DataMart`/dashboard classes expose ONLY read methods; there is deliberately no CRM/pricing/Diamond/scale/
  trigger method to call. T4 asserts the read-only public surface.
- **No thresholds (M6-OD-002 OPEN)** — metrics emit values; the DQ gate is structural (8 items). No numeric
  alert/scale threshold is invented anywhere (fail-closed).
- **M6-OD-008 (PAYMENT_COMPLETED)** OPEN — affects only the revenue **edge-handling** leg, NOT this slice's
  verified-only definition (RULE-003 fixes ORDER_VERIFIED-only; payment-waiting never revenue). Carried forward.
- **Scale / learning / alerts / real send** are OUT (M6.2G+, M6-OD-002/003/004/005). Smoke execution (legs L2–L6)
  is the TESTER's (M6-P1503/1504). `M6-P1309` verdict stays BLOCKED (not converted); the mandatory M6.2G
  Scale-Gate re-gate stands before any real scale or external send.

---

## 10. Acceptance self-map

1. *Every planned item → leg or smoke* → §5–§7. ✓  2. *Rollback per item* → §5/§8. ✓  3. *No scope beyond the
slice file* → §3 (thresholds/scale/learning/real-send deferred; data mart support-view only). ✓  4. *Target
LOCKED + M6-OD-011 decided* → §1. ✓  5. *Reuse conventions/test patterns from the locked target* → §2 (M6.2E
baseline). ✓  Plus the **load-bearing invariants**: verified-only revenue (RULE-003, FAIL-001, SMK-004/005/015)
and data-mart-support-view-only (RULE-012, FAIL-005, SMK-010), each with tests (T1–T5) and the M6.2E 223-test
suite staying green.

*Plan-only: no code, no migration applied, nothing sent/scaled/triggered/published, no flag flipped; BLOCKED/OFF/OFF.*
