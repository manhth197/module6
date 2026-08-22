# M6.2F Runbook — KPI Dashboard & Data Quality Gate

| Field | Value |
|---|---|
| Slice | **M6.2F** — KPI dashboard (14 locked formulas, doc §14) + Data Quality Gate (8 items, doc §15) with metric-level source trace; data mart stays a **support view** (RULE-012); depends on M6.2E |
| Produced by | **M6-P1508** `M6_2F_DOCS` (ANALYST_ARCHITECT, `analysis_only`) |
| Sources | `00-spec/slices/M6.2F.md`, `M6-P1507.json`, `M6_2F_EVIDENCE_INDEX.md`, `M6.2F/PLAN.md`, `M6.2F/IMPLEMENTATION_NOTES.md` |
| Posture (immutable) | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `HASH_POLICY_RATIFIED=False`, `SCALE_MODEL_RATIFIED=False`, `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False` |

> **Read first — this is a runbook, not a verdict.** It self-certifies nothing and advances no gate (RULE-015);
> the authoritative slice verdict is the slice-gate Judge's at **M6-P1509**. **This is the last Phase-1 measurement
> slice before the mandatory M6.2G Scale-Gate re-gate (M6-P1600)** — the next step is the re-gate, not another
> measurement slice. **Clean band, stated accurately (not a pass):** entry is a real Judge PASS (M6-P1500 `SIGNED`),
> all seven band prompts self-report PASS, **both in-scope fail gates held** (FAIL-001 verified-only revenue,
> FAIL-005 Data Mart as trigger owner), the scan is clean over 139 files, and the coder self-found+fixed 2
> fail-closed holes with regressions. **What is still open:** exit-gate leg 1 is **"supported (staged), not
> closed"** — the tester marked it "met" via the bound smokes, but revenue-path residuals **F-DASH-1 / F-DASH-3**
> keep final closure with the Judge; a MEDIUM latent PII surface **F-VIEW-1** (the staged support view exposes raw
> psid) must close before the DB binding; **F-DASH-4** is explicitly routed to and owned by the M6.2G re-gate.

---

## 1. What this slice built

Two layers over the existing measurement store: a **read-only dashboard** and a **Data Quality Gate**. The single
most load-bearing boundary is that the **data mart is a support view** — it exposes only read/aggregate methods,
never a CRM/pricing/Diamond/scale/trigger surface (RULE-012, FAIL-005).

| Capability | Rule | Contract | Where (staged under `04-artifacts/impl/M6.2F/`) |
|---|---|---|---|
| Data Mart **support view** — read/aggregate only; `verified_rows()` = the single revenue choke (set-once Zone-B ORDER_VERIFIED) | RULE-012, FAIL-005 | CTR-018/015 | `dashboard/data_mart.py` |
| 14 KPI metrics, **formulas verbatim** (doc §14); revenue metrics verified-only; fail-closed division | RULE-003, FAIL-001 | **CTR-015 (DRAFT_LOCKED formulas)** | `dashboard/kpi_metrics.py`, `dashboard/models.py` |
| `GET /api/admin/ads/dashboard` — read-only, returns 14 metrics + per-metric trace/evidence + overall DQ; never writes/triggers | RULE-012/003 | **CTR-018** | `app/api/dashboard.py` |
| `ads_data_quality_check` — 8 doc §15 gate items + **worst-status roll-up** (FAIL>HOLD>PASS) | RULE-009 | **CTR-012** | `quality/data_quality_check.py` |
| `data_quality_checker` worker — outputs **ONLY** PASS/HOLD/FAIL; suppression fail-closed (RULE-017) | RULE-003/017/009/015 | **CTR-024** | `quality/data_quality_checker.py` |
| Zone-C audited transition (`set_data_quality_status`) — the ONLY DQ-status writer, append-only history | RULE-007/008/015 | CTR-001/024 | patched `store/measurement_event_store.py` |

Everything is **staged** — no live system, no applied migration, no external call, **no trigger, no threshold, no
scale**. Migrations `0007_create_ads_data_quality_check.sql` + `0008_create_ads_dashboard_support_view.sql` are
staged (never applied). Cumulative snapshot: the M6.2E tree is carried forward byte-identical, the two layers added,
the store patched.

**Coder self-review (credit):** an adversarial self-review found **2 fail-closed holes in the new code**, both
FIXED + locked with regressions before evidence — (1) an unobserved suppression signal defaulted to PASS instead of
**HOLD** (RULE-017); (2) `verified_boxes()` fabricated `0` on partial coverage instead of **None** ("never
fabricated"). The two fail-gate invariants (verified-only revenue, support-view-only) were CLEAN.

**Scope boundary (carried, not bled):** **alert/scale thresholds are M6-OD-002** (OUT — `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False`,
metrics report values only, no threshold/alert); scale decisions → M6.2G; learning → M6.2H; connector/real send → M6-OD-003/004.

---

## 2. Operate (staged)

No production service (BLOCKED/OFF); the dashboard is a read-only handler, nothing triggers or scales.

```bash
cd 04-artifacts/impl/M6.2F
python -m app        # prints the staged posture (BLOCKED / OFF / OFF), exit 0 — no server, no egress
```

- **Dashboard read path:** `app/api/dashboard.py::handle_dashboard_request(query, deps)` — framework-neutral,
  **read-only** over `DataMart` (deps hold no writer/transport/trigger). It computes the 14 CTR-015 metrics,
  attaches a `source_trace` + masked `sample_evidence_ref` per metric, and an overall DQ status. The untrusted
  `query` is DATA (RULE-H03). A revenue figure is **verified-only** by construction; a quote/order-draft shown as
  revenue is an immediate **DQ FAIL** (SMK-015).
- **Verified-only revenue:** every revenue-bearing metric (Revenue Verified, ROAS, AOV, Boxes/Order, CRM Revenue,
  Diamond Revenue) reads **only** the set-once Zone-B `revenue_value` (populated by M6.2E on the ORDER_VERIFIED path);
  quote/cart/draft/waiting contribute **0.0** revenue and **no** ROAS. Division is fail-closed (`0`/`None` → `None`, never a crash/fabrication).
- **DQ gate:** the `data_quality_checker` evaluates the 8 doc §15 items over a measurement row + consumed context,
  rolls up to the worst status, and outputs **only** PASS/HOLD/FAIL — a missing signal → HOLD, a real violation →
  FAIL (suppression fail-closed, RULE-017). The Zone-C transition is **audited** (append-only, never a silent edit).
- **Data mart = support view (RULE-012):** exposes only read/aggregate methods — there is deliberately **no**
  CRM/pricing/Diamond/scale/trigger method to call. No threshold, no alert, no scale in this slice.

---

## 3. Verify

```bash
cd 04-artifacts/impl/M6.2F
python -m pytest -q          # expect: 273 passed / 0 failed (final tester run, M6-P1504)
```

| Check | Expected | Evidence |
|---|---|---|
| Full staged suite (255 carried M6.2E+coder + 18 tester smoke nodes) | **273 passed / 0 failed**, exit 0 | `04-artifacts/test-reports/M6.2F/SMOKE_RESULTS.md`; `M6-P1504.json` |
| **M6-SMK-004** — quote created, not ordered → `Không revenue, không ROAS` | **PASS 3/3** | `SMOKE_RESULTS.md` |
| **M6-SMK-005** — order draft/created not verified → `Không tính Revenue Verified` | **PASS 4/4** | `SMOKE_RESULTS.md` |
| **M6-SMK-006** — ORDER_VERIFIED full campaign/adset/ad → `ROAS/CPA/AOV dashboard cập nhật` | **PASS 4/4** | `SMOKE_RESULTS.md` |
| **M6-SMK-010** — Data Mart used as CRM/scale trigger → `Fail - Data Mart chỉ support view` | **PASS 3/3** | `SMOKE_RESULTS.md` |
| **M6-SMK-015** — dashboard shows quote/order-draft as revenue → `Fail` | **PASS 4/4** | `SMOKE_RESULTS.md` |
| 14 KPI formulas verbatim + fail-closed division + per-metric trace/evidence | pass | `tests/test_kpi_formulas_verbatim.py` |
| DQ checker — 8 items → PASS/HOLD/FAIL, worst roll-up, audited Zone-C, suppression fail-closed | pass | `tests/test_data_quality_checker.py` |
| No raw PII (scan) | **CLEAN over 139 files** (incl. psid-literal probe) | `04-artifacts/security-reports/M6.2F_security.md` |
| Carried-forward M6.2E suite (no regression) | 239 green | `IMPLEMENTATION_NOTES.md` §1 |

> **Verify does NOT assert leg closure.** All five bound smokes pass (18/18) and the tester marked **leg 1 "met"**,
> but the evidence-collect softened leg 1 to **SUPPORTED (staged)** because of the revenue-path residuals **F-DASH-1
> / F-DASH-3** (armed-not-fired, not channel-reachable, §7). Whether leg 1 closes — and whether the dashboard
> overall should run the per-row DQ gate — is the **M6-P1509 Judge's** call.

---

## 4. Rollback — every change

**Baseline rollback is non-destructive: nothing is live.** All artifacts are staged under `04-artifacts/impl/M6.2F/`;
no migration, no external call, no trigger, no flag written. Cumulative snapshot ⇒ **new** files revert by deletion;
**patched** carried-forward files revert to their M6.2E version; deleting the M6.2F tree returns to M6.2E (untouched).
Per-item detail: `PLAN.md` §5/§8, `IMPLEMENTATION_NOTES.md` §6.

| Change group | Files | Rollback |
|---|---|---|
| Dashboard layer | `dashboard/data_mart.py`, `dashboard/kpi_metrics.py`, `dashboard/models.py`, `dashboard/__init__.py` | Delete (new) |
| Dashboard API (read-only) | `app/api/dashboard.py` | Delete (new); no writer/transport/trigger in deps |
| Data Quality layer | `quality/data_quality_check.py`, `quality/data_quality_checker.py`, `quality/__init__.py` | Delete (new) |
| Zone-C audited transition | `store/measurement_event_store.py` (+`set_data_quality_status()`) | **Revert to M6.2E** (Zone-A write-once + Zone-B set-once + forbidden update/delete unchanged) |
| Config markers | `app/config.py` (+`DQ_STATUS_ORDER`, +`DASHBOARD_ALERT_THRESHOLDS_DEFINED=False`) | **Revert to M6.2E** (no flag changed) |
| **Staged migrations** | `migrations/0007_create_ads_data_quality_check.sql` (up+down), `migrations/0008_create_ads_dashboard_support_view.sql` (up+down) | **Never applied.** Delete staged files to revert now. **After a real apply, revert = down-DDL `DROP` per file** (0008 is a `VIEW` → `DROP VIEW`; 0007 → `DROP TABLE ads_data_quality_check`) |
| Tests / fixtures | `tests/test_dashboard_*`, `test_quote_not_revenue.py`, `test_order_draft_not_verified.py`, `test_data_mart_support_view_only.py`, `test_kpi_formulas_verbatim.py`, `test_data_quality_checker.py` (+ `conftest.py` → revert) | Delete (new) / revert (conftest); test doubles only, no raw PII in fixtures |

**Consumed inputs (Ads Spend, boxes, COD, funnel counts, suppression) are read-only staged sources — never written
by M6**; no measurement row is hard-deleted (RULE-007; Zone-C transitions are append-only). (Exit-gate leg **9** = this rollback documentation.)

---

## 5. Decision deltas + governance status

*(For the operator to reconcile into `DECISION_REGISTER` out-of-band; the analyst does not write `00-spec/`.)*

| Decision | State | Effect |
|---|---|---|
| **M6-OD-002** (dashboard alert / scale thresholds) | **OPEN — OUT OF SCOPE for M6.2F** (`DASHBOARD_ALERT_THRESHOLDS_DEFINED=False`) | The dashboard reports **values only** — applies no threshold, triggers no alert/scale. No numeric threshold invented anywhere (fail-closed) |
| **M6-OD-005** (attribution scale model) | OPEN | Multi-model display only; single-model **scale** forward to M6.2G (`SCALE_MODEL_RATIFIED=False`) |
| **M6-OD-008** (PAYMENT_COMPLETED as revenue) | OPEN | Blocks only the revenue **edge-handling** leg — NOT the RULE-003-fixed verified-only definition (ORDER_VERIFIED-only) |
| **M6-OD-012** (masking format) | OPEN — now includes **N-4** (short-id reveal), **O-2b** (conversation/thread ids), **F-VIEW-1** (view psid) | §7 |
| **M6-OD-003** (hash) / **M6-OD-004** (connector) | OPEN | N/A here (no external-send data path); before real send |
| **ENTRY-001 / ENTRY-003** (inherited) | RISK-ACCEPTED under `M6-OVERRIDE-M6P1000-STAGED` (M6-P1000 **BLOCKED**, not converted) | Re-proven at the mandatory M6.2G re-gate |

**Governance decision-file gap (still open):** **`M6-DEFER-FBC-M6.2D.json`** — recommended since M6-P1209 to bind
F-B/F-C/F-A + F-D into the M6.2G gate (M6-P1600) `RequiredInputs` — is **still not filed** in
`04-artifacts/evidence/decisions/`. Substance is carried by `M6-OVERRIDE-M6P1309-STAGED` and F-B/F-C/F-A/F-D are
closed; the dedicated file remains an operator/owner TODO. **Positive:** the M6.2G entry-gate row **M6-P1600 already
lists ENTRY-001…004 in its `RequiredInputs`** per the ledger.

---

## 6. Changelog delta produced by this slice

**Deferred housekeeping; no in-band schema change.** The slice adds **no schema change beyond the harmonized
contracts** (SCHEMA_CHANGELOG rows 9–33, judged PASS at M6-P0715 SIGNED). It **realizes** CTR-015 (14 DRAFT_LOCKED
formulas, reproduced verbatim), CTR-012, CTR-018, CTR-024 as staged code + staged (un-applied) `0007`/`0008` DDL.

- **Canon-flip (operator, out-of-band):** `M6-CTR-012`/`018`/`024` are still `MISSING / OWNER_DECISION_REQUIRED` in
  canon but **satisfied-for-entry** (producers M6-P0708/M6-P0712/M6-P0713 PASS; gate M6-P0715 SIGNED). `M6-CTR-015`
  formulas are already `DRAFT_LOCKED` (thresholds are M6-OD-002, not implemented). Canon-flips are **deferred,
  non-blocking operator housekeeping**.
- New tokens (`GateItem`/`GateItemResult`, `DQ_STATUS_ORDER`, `DASHBOARD_ALERT_THRESHOLDS_DEFINED`, `MetricResult`
  fields, `DataQualityTransition`) are **implementation-internal vocabulary**, not owner-facing schema → **no**
  SCHEMA_CHANGELOG row. (If the owner later ratifies M6-OD-002 thresholds, that is a DECISION + likely a CHANGELOG delta at that time.)

---

## 7. Handoff to M6.2G (the Scale-Gate re-gate) + the forward gates

**Next is the mandatory M6.2G Scale-Gate re-gate (M6-P1600)** — not another measurement slice. It re-proves
ENTRY-001/002/003 (+004) before any real scale or external send, and **owns F-DASH-4.** The dashboard/DQ residuals
below must close before the M6-OD-011 durable binding and/or the M6.2G scale re-gate.

### 7.1 MUST-FIX before the M6-OD-011 durable binding — revenue accuracy + PII (routed to CODER)
> None trips an in-scope fail gate (armed-not-fired, not channel-reachable today), but they are revenue-accuracy /
> PII-exposure gaps that become real at the durable DB binding.
- **F-VIEW-1 [MEDIUM, latent — the primary security finding]:** the staged `0008` support view
  (`ads_dashboard_kpi_source`) `SELECT`s the raw `attribution_context` column — which carries raw **psid** (+
  comment/thread/live ids, raw `page_id`/`live_session_id`). The view is the future DB-backed read path granted
  `SELECT` to `ads_dashboard_reader` at the M6-OD-011 binding, so the **reader role would see raw psid — broader
  exposure than the PII-safe app** (which aggregates and never reads psid). Latent (view staged, never applied) → no
  leak today. **Fix (before binding): drop `attribution_context` from the view, or project only non-PII fields, or
  mask psid — align with the app + M6-OD-012.**
- **F-DASH-1 [primary, revenue integrity]:** the materializer books revenue while deriving "verified" from the
  **conversion's** event_code and **never asserts the measurement event's own `event_code == ORDER_VERIFIED`** (the
  store trusts the caller's `verified` bool) — a mispaired ORDER_VERIFIED conversion + non-verified event books
  revenue onto the pre-verified row. **Not channel-reachable** (materializer wired only in tests), and the per-row DQ
  Verified-Revenue item independently FAILs — **but the dashboard overall never runs the per-row DQ gate**, so a
  mispaired row would display as Revenue Verified / overall PASS. **Fix:** assert `event.event_code == ORDER_VERIFIED`
  in `materialize`; surface per-row DQ into the dashboard overall.
- **F-DASH-3:** `revenue_verified()` sums per-row while `verified_order_count()` dedups by `order_code` → two
  verified rows sharing an `order_code` **double-count** Revenue Verified + AOV. Fix: dedup revenue by `order_code`.
- **F-DASH-2 [MINOR]:** `attribution_context` is a mutable dict inside a frozen row — an in-place edit flips the DQ
  Attribution item HOLD→PASS and re-routes the CRM/Diamond breakdown (total revenue unchanged → not FAIL-001). Fix:
  `MappingProxyType`/copy-on-read.
- **N-1/N-2/N-4:** N-1 a `NaN`/`Inf` revenue poisons the total + breaks idempotent replay (carried M6.2E O-5, → `math.isfinite`);
  N-2 negative revenue accepted (understates, never inflates; add `>=0`); N-4 `mask()` reveals 5/6 of a 6-char id (→ M6-OD-012).
- Forward at the M6-OD-011 binding: request **authN/authZ** on `GET /api/admin/ads/dashboard` (the **first admin
  endpoint**, exposing revenue/metrics).
- Full detail: `04-artifacts/boundary-reports/M6.2F_boundary.md`, `04-artifacts/security-reports/M6.2F_security.md`.

### 7.2 Owned by the M6.2G re-gate (M6-P1600)
- **F-DASH-4:** `is_scale_evidence_eligible` consults only attribution HIGH+NONE, **never the 8-item DQ overall** — a
  consent-missing / suppression-unreflected row is still "scale eligible". Armed-not-fired (AND-gated by
  `SCALE_MODEL_RATIFIED=False`, no in-slice scale consumer). **The mandatory M6.2G scale re-gate must close it** so a
  row cannot become scale evidence without passing the full DQ gate.

### 7.3 Hard forward gates (immovable)
- **M6-OD-002** (thresholds) before any dashboard alert/scale; **M6-OD-005** before any row is scale evidence;
  **M6-OD-003/004** before any real send; **`M6-DEFER-FBC-M6.2D.json`** filed + wired into M6-P1600 `RequiredInputs`.
- **M6.2G Scale-Gate re-gate (MANDATORY):** ENTRY-001/002/003(+004) re-proven; **both M6-P1000 and M6-P1309 verdicts
  stay BLOCKED, not converted.** Posture stays `BLOCKED`/`OFF`/`OFF` + all three `*_RATIFIED/DEFINED=False` markers.

---

## 8. Pointers for the slice-gate Judge (M6-P1509)

This runbook and `M6_2F_EVIDENCE_INDEX.md` are **descriptive**. The slice verdict is the Judge's, from the evidence.
1. **What holds (executed):** genuine entry Judge PASS (M6-P1500 `SIGNED`); **both fail gates held** (FAIL-001
   verified-only revenue, FAIL-005 data-mart-support-view); all five bound smokes 18/18; scan clean over 139 files;
   the coder self-fixed 2 fail-closed holes.
2. **Leg 1** is tester-marked "met" but **SUPPORTED (staged), not closed** — weigh **F-DASH-1 / F-DASH-3** and
   whether the dashboard overall should run the per-row DQ gate. Read `M6.2F_boundary.md` + `SMOKE_RESULTS.md` directly.
3. **Forward items:** F-VIEW-1 (raw-psid view — before the DB binding), F-DASH-1/2/3 + N-1/2/4 (revenue accuracy),
   dashboard authN/authZ; **F-DASH-4 is owned by the M6.2G re-gate**; the still-open `M6-DEFER-FBC-M6.2D.json`.
4. **This is the last Phase-1 measurement slice** — the immovables (M6-P1000 + M6-P1309 both BLOCKED-not-converted;
   the mandatory M6.2G re-gate) stand; nothing here authorizes real scale or send.

*Analysis-only: no code, no migration, no flag, no external call, no self-certification. `04-artifacts/state/` untouched.*
