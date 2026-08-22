# M6.2F — Slice Evidence Index

| Field | Value |
|---|---|
| Slice | **M6.2F** — Dashboard & Data Quality (depends on M6.2E) |
| Assembled by | **M6-P1507** — `M6_2F_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, analysis_only) |
| Assembled on | 2026-08-07 (UTC) |
| Purpose | Index every band's evidence file / artifact / test report / boundary+security report, mapped to the slice exit-gate checklist, and list unresolved blockers — for the slice-gate Judge (M6-P1509). |
| Governance (immutable) | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `HASH_POLICY_RATIFIED=False`, `SCALE_MODEL_RATIFIED=False`, `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False`. This index flips nothing and self-certifies nothing. |

> **Altitude note (read first).** This is an **index of collected evidence**, not a verdict. It does **not** assert
> that slice M6.2F has passed its exit gate. Exit-gate items **7 and 8 are NOT yet met** (docs prompt M6-P1508 and
> the slice-gate Judge M6-P1509 have not run — the steps that *follow* this one). The band is clean: entry gate a
> real Judge PASS (M6-P1500 `SIGNED`), **all seven band prompts self-report PASS**, and **both in-scope fail gates
> (M6-FAIL-001 verified-only revenue, M6-FAIL-005 Data Mart as trigger owner) held**. **M6.2F is the last Phase-1
> measurement slice before the mandatory M6.2G Scale-Gate re-gate (M6-P1600)** — several residuals here (notably
> F-DASH-4) are explicitly routed to that re-gate, whose RequiredInputs already list ENTRY-001…004. The
> authoritative slice verdict is the Judge's, strictly from the evidence.

---

## 1. Slice prompt band — evidence status

Source: `04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv` (rows 128–137) + each evidence JSON.

| Prompt | Role | Title | Ledger status | Evidence JSON | Self-reported | `fail_gate_tripped` | Primary artifact(s) |
|---|---|---|---|---|---|---|---|
| M6-P1500 | JUDGE | M6_2F_ENTRY_GATE_JUDGE | **SIGNED** | `04-artifacts/evidence/prompts/M6-P1500.json` | PASS | false | `04-artifacts/evidence/judge/M6-P1500_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS) |
| M6-P1501 | CODER | M6_2F_CODER_PLAN | PASS | `04-artifacts/evidence/prompts/M6-P1501.json` | PASS | false | `04-artifacts/impl/M6.2F/PLAN.md` |
| M6-P1502 | CODER | M6_2F_CODER_IMPLEMENT | PASS | `04-artifacts/evidence/prompts/M6-P1502.json` | PASS | false | `04-artifacts/impl/M6.2F/IMPLEMENTATION_NOTES.md` + staged `app/` tree |
| M6-P1503 | TESTER | M6_2F_TESTER_BUILD | PASS | `04-artifacts/evidence/prompts/M6-P1503.json` | PASS | false | `04-artifacts/impl/M6.2F/tests/TEST_MANIFEST.md` |
| M6-P1504 | TESTER | M6_2F_TESTER_RUN | PASS | `04-artifacts/evidence/prompts/M6-P1504.json` | PASS | false | `04-artifacts/test-reports/M6.2F/SMOKE_RESULTS.md` |
| M6-P1505 | BOUNDARY_ADVERSARY | M6_2F_BOUNDARY_ADVERSARY | PASS | `04-artifacts/evidence/prompts/M6-P1505.json` | PASS | false | `04-artifacts/boundary-reports/M6.2F_boundary.md` |
| M6-P1506 | SECURITY_PII | M6_2F_SECURITY_REVIEW | PASS | `04-artifacts/evidence/prompts/M6-P1506.json` | PASS | false | `04-artifacts/security-reports/M6.2F_security.md` |
| **M6-P1507** | PM_ORCHESTRATOR | M6_2F_EVIDENCE_COLLECT | **RUNNING** | `04-artifacts/evidence/prompts/M6-P1507.json` | (this index) | false | `04-artifacts/evidence/prompts/M6_2F_EVIDENCE_INDEX.md` |
| M6-P1508 | ANALYST_ARCHITECT | M6_2F_DOCS | **TODO** | — (not produced) | — | — | `04-artifacts/analysis/slices/M6_2F_RUNBOOK.md` (pending) |
| M6-P1509 | JUDGE | M6_2F_SLICE_GATE_JUDGE | **TODO** | — (not produced) | — | — | `04-artifacts/evidence/judge/M6-P1509_JUDGE_FINAL_SIGN_OFF.json` (pending) |

All seven band evidence JSONs (M6-P1500 … M6-P1506) exist, are schema-valid, self-report **PASS**, and declare
`fail_gate_tripped=false`; the entry gate M6-P1500 is a genuine Judge `SIGNED` verdict PASS. This prompt's own
`M6-P1507.json` is produced at completion (written **last**, after this index — pack hard-rule 2).

---

## 2. Artifact inventory (existence verified on disk)

### 2.1 Implementation (staged, `04-artifacts/impl/M6.2F/`)
- `PLAN.md` — minimal staged change set + master traceability + per-item rollback.
- `IMPLEMENTATION_NOTES.md` — realized plan + the 2 self-fixed fail-closed holes (suppression signal, verified_boxes); §6 rollback.
- Carried-forward M6.2E tree + new **dashboard layer**: `dashboard/data_mart.py` (M6-owned support view — read/aggregate only),
  `dashboard/kpi_metrics.py` (the 14 CTR-015 metrics, formulas verbatim; revenue metrics verified-only, fail-closed division),
  `dashboard/models.py` (MetricResult + source_trace + masked sample_evidence_ref), `api/dashboard.py`
  (CTR-018 read-only GET /api/admin/ads/dashboard) + **quality layer**: `quality/data_quality_check.py`
  (CTR-012, 8 doc §15 gate items + worst-status roll-up), `quality/data_quality_checker.py` (CTR-024 worker,
  PASS/HOLD/FAIL only) + a patched `store/measurement_event_store.py` (audited Zone-C `set_data_quality_status()`).
- Migrations (staged, never applied): `migrations/0007_create_ads_data_quality_check.sql`,
  `migrations/0008_create_ads_dashboard_support_view.sql` (read-only support VIEW).

### 2.2 Tests
- Manifest: `04-artifacts/impl/M6.2F/tests/TEST_MANIFEST.md`.
- Bound smoke: `tests/smoke/test_smk_004_quote_not_revenue.py` (3), `test_smk_005_order_not_verified_not_revenue.py` (4),
  `test_smk_006_dashboard_roas_update.py` (4), `test_smk_010_data_mart_support_view_only.py` (3),
  `test_smk_015_dashboard_quote_draft_not_revenue.py` (4).
- Leg-supporting: `tests/test_kpi_formulas_verbatim.py`, `test_dashboard_verified_only_revenue.py`,
  `test_dashboard_rejects_unverified_as_revenue.py`, `test_data_mart_support_view_only.py`,
  `test_data_quality_checker.py` + carried suites.
- Full staged suite **273 passed / 0 failed** (255 carried-forward + 18 new smoke nodes).

### 2.3 Reports
- Test report: `04-artifacts/test-reports/M6.2F/SMOKE_RESULTS.md` (all 5 smokes PASS, 18/18; full suite 273).
- Boundary report: `04-artifacts/boundary-reports/M6.2F_boundary.md`.
- Security/PII report: `04-artifacts/security-reports/M6.2F_security.md` (verdict PASS; scan clean over 139 files).
- Entry-gate Judge sign-off: `04-artifacts/evidence/judge/M6-P1500_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS).

---

## 3. Contract checklist (from the slice spec)

| Contract | Shape | Ownership | Status (canon) | Harmonization |
|---|---|---|---|---|
| M6-CTR-012 | ads_data_quality_check | M6 | MISSING / OWNER_DECISION_REQUIRED | M6-P0708 (PASS) |
| M6-CTR-015 | Dashboard KPI contract | M6 | **DRAFT_LOCKED (formulas)** — thresholds OPEN via M6-OD-002 | 14 metrics verbatim in MONITORING_REGISTER; thresholds M6-P0714 |
| M6-CTR-018 | GET /api/admin/ads/dashboard | M6 | MISSING / OWNER_DECISION_REQUIRED | M6-P0712 (PASS) |
| M6-CTR-024 | worker: data_quality_checker | M6 | MISSING / OWNER_DECISION_REQUIRED | M6-P0713 (PASS) |

CTR-012/018/024 are `MISSING` in canon but **satisfied-for-entry** (harmonization producers PASS, gate M6-P0715
SIGNED); CTR-015 formulas are `DRAFT_LOCKED` (thresholds are M6-OD-002, out of scope). Canon-flips are deferred,
non-blocking operator housekeeping.

---

## 4. Exit-gate checklist → evidence map

Legend: **MET** = evidence present and sufficient at the staged level · **SUPPORTED (staged)** = the bound suites
pass and the boundary adversary executed the check, but the leg carries open revenue-path residuals · **PENDING** =
the producing prompt has not run yet. Caveats are carry-forwards (see §5); none trips an in-scope fail gate
(M6-FAIL-001/005 — both held).

| # | Exit-gate check (slice spec) | Verdict | Evidence refs | Notes / caveats |
|---|---|---|---|---|
| 1 | **Dashboard shows verified-only revenue** — every revenue figure sources from ORDER_VERIFIED / Verified Revenue; quote/order-draft displayed as revenue is an immediate FAIL | **SUPPORTED (staged)** | `04-artifacts/test-reports/M6.2F/SMOKE_RESULTS.md` (SMK-004/005/015 — directly exercise this leg) + `tests/test_dashboard_verified_only_revenue.py` / `test_kpi_formulas_verbatim.py`; `app/measurement/dashboard/kpi_metrics.py`, `dashboard/data_mart.py`; boundary `M6.2F_boundary.md` + security `M6.2F_security.md` (FAIL-001 not tripped) | RULE-003. The tester's SMOKE_RESULTS marks leg L1 **"met"** (this leg is directly bound to SMK-004/005/015). Caveats B2-F-DASH-1 (materializer books revenue without asserting the row's own event_code==ORDER_VERIFIED; **not channel-reachable**; the dashboard overall never runs the per-row DQ gate) and B2-F-DASH-3 (two verified rows sharing an order_code double-count) — both armed-not-fired, revenue-path residuals routed to CODER/M6.2G. Final L1 closure is the slice-gate Judge's call. |
| 2 | **Smoke M6-SMK-004 executed** with recorded result + evidence ref | **MET** | `SMOKE_RESULTS.md` (3/3, exit 0); `04-artifacts/evidence/prompts/M6-P1504.json` | Quote → no revenue, no ROAS; DQ FAIL on a quote carrying revenue. |
| 3 | **Smoke M6-SMK-005 executed** with recorded result + evidence ref | **MET** | `SMOKE_RESULTS.md` (4/4, exit 0); `04-artifacts/evidence/prompts/M6-P1504.json` | ORDER_CREATED/draft not counted as Verified Revenue. |
| 4 | **Smoke M6-SMK-006 executed** with recorded result + evidence ref | **MET** | `SMOKE_RESULTS.md` (4/4, exit 0); `04-artifacts/evidence/prompts/M6-P1504.json` | Full-source verified order → ROAS/CPA/AOV dashboard update (M6.2F render leg). |
| 5 | **Smoke M6-SMK-010 executed** with recorded result + evidence ref | **MET** | `SMOKE_RESULTS.md` (3/3, exit 0); `04-artifacts/evidence/prompts/M6-P1504.json` | Data Mart exposes only read/aggregate methods; no CRM/scale/trigger surface (RULE-012/FAIL-005). |
| 6 | **Smoke M6-SMK-015 executed** with recorded result + evidence ref | **MET** | `SMOKE_RESULTS.md` (4/4, exit 0); `04-artifacts/evidence/prompts/M6-P1504.json` | Quote/draft shown as revenue → DQ FAIL; verified-only by construction. |
| 7 | **All slice prompts have evidence JSON** (schema-valid, no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | `04-artifacts/evidence/prompts/M6-P1500.json` … `M6-P1506.json` present (7); `M6-P1507.json` produced at this prompt's completion | **Not yet complete:** M6-P1508 (Docs) and M6-P1509 (Judge) evidence not produced (both TODO). |
| 8 | **Slice-gate Judge sign-off exists with verdict PASS** | **PENDING (not met)** | — | `04-artifacts/evidence/judge/M6-P1509_JUDGE_FINAL_SIGN_OFF.json` does **not** exist; M6-P1509 is TODO. (The existing `M6-P1500_JUDGE_FINAL_SIGN_OFF.json` is the *entry* gate, verdict PASS — not the slice gate.) |
| 9 | **Rollback steps documented** for every change this slice made | **MET** | `04-artifacts/impl/M6.2F/PLAN.md` (per-item Rollback) + `IMPLEMENTATION_NOTES.md` §6 (new files → delete; patched carried-forward files → revert to M6.2E version); `migrations/0007`, `0008` down-DDL | All changes staged ⇒ non-destructive. |

**Summary:** items **2, 3, 4, 5, 6 and 9 are MET** (all five bound smokes executed 18/18); item **1 is SUPPORTED at
the staged level** (the tester marks L1 "met" via the directly-bound smokes and FAIL-001 is not tripped, but the
F-DASH-1/F-DASH-3 revenue-path residuals remain — armed-not-fired, not channel-reachable — so final closure is the
slice-gate Judge's call); items **7 and 8 are PENDING** (M6-P1508 docs, then M6-P1509 slice-gate Judge). Coverage:
**every exit-gate checklist item is indexed** (acceptance check 1).

### 4.1 Smoke register bindings

| Smoke ID | Doc ID | Scenario (verbatim) | Expected (verbatim) | Result | Evidence |
|---|---|---|---|---|---|
| M6-SMK-004 | ADS-P0-004 | `Quote được tạo nhưng chưa order` | `Không revenue, không ROAS` | **PASS 3/3** | `SMOKE_RESULTS.md`, `M6-P1504.json` |
| M6-SMK-005 | ADS-P0-005 | `Order Draft / Order Created chưa verified` | `Không tính Revenue Verified` | **PASS 4/4** | `SMOKE_RESULTS.md`, `M6-P1504.json` |
| M6-SMK-006 | ADS-P0-006 | `ORDER_VERIFIED có campaign/adset/ad đầy đủ` | `ROAS/CPA/AOV dashboard cập nhật` | **PASS 4/4** | `SMOKE_RESULTS.md`, `M6-P1504.json` |
| M6-SMK-010 | ADS-P0-010 | `Data Mart tạo trigger CRM/scale` | `Fail - Data Mart chỉ support view` | **PASS 3/3** | `SMOKE_RESULTS.md`, `M6-P1504.json` |
| M6-SMK-015 | ADS-P0-015 | `Dashboard hiển thị quote/order draft như revenue` | `Fail` | **PASS 4/4** | `SMOKE_RESULTS.md`, `M6-P1504.json` |

---

## 5. Unresolved blockers / carry-forwards (acceptance check 2)

None of the following is an open blocker of the **evidence-collection** task itself, and none trips an in-scope
fail gate (M6-FAIL-001/005 — both held). Each was already adjudicated by the responsible upstream prompt and is
carried forward as governance context for the slice-gate Judge (M6-P1509) and the owner. **B2/B3 include revenue-
and PII-path residuals that must close before the M6-OD-011 durable binding and the M6.2G scale re-gate.**

- **B1 — Slice exit gate is not complete (expected at this step).** Item 7 pending M6-P1508/M6-P1509 evidence;
  item 8 pending the M6-P1509 slice-gate Judge PASS sign-off.

- **B2 — Boundary residuals (M6-P1505), armed-not-fired, none trips M6-FAIL-001/005; routed to CODER / M6.2G.**
  - **F-DASH-1 [primary]:** the materializer books revenue onto the event while deriving "verified" from the
    conversion's event_code and **never asserts the measurement event's own `event_code == ORDER_VERIFIED`** (the
    store trusts the caller's `verified` bool); a mispaired ORDER_VERIFIED conversion + a non-verified event books
    revenue onto the pre-verified row. **Not channel-reachable** (the materializer's only caller is wired in tests;
    no app endpoint), and the per-row DQ Verified-Revenue item independently FAILs — **but** the dashboard endpoint
    never runs the per-row DQ gate, so a mispaired row would display as Revenue Verified with overall PASS. Fix:
    assert `event.event_code == ORDER_VERIFIED` in `materialize`; surface per-row DQ into the dashboard overall.
  - **F-DASH-2 [MINOR]:** `attribution_context` is a mutable dict inside a frozen row (frozen freezes the binding,
    not the dict) — an in-place edit flips the DQ Attribution item HOLD→PASS and re-routes the CRM/Diamond
    breakdown (total revenue unchanged → not FAIL-001). Fix: store as `MappingProxyType`/copy-on-read.
  - **F-DASH-3:** `revenue_verified()` sums per-row while `verified_order_count()` dedups by order_code → two
    verified rows sharing an order_code double-count Revenue Verified + AOV (both genuinely ORDER_VERIFIED). Fix:
    dedup revenue by order_code.
  - **F-DASH-4 [routed to M6.2G / M6-P1600]:** `is_scale_evidence_eligible` consults only attribution HIGH+NONE,
    **never the 8-item DQ overall**, so a consent-missing / suppression-unreflected row is still "scale eligible";
    armed-not-fired (AND-gated by `SCALE_MODEL_RATIFIED=False`, no in-slice scale consumer). The **mandatory M6.2G
    Scale-Gate re-gate must close it.**
  - Notes: N-1 (NaN/Inf revenue poisons the total + breaks idempotent replay — carried M6.2E O-5), N-2 (negative
    revenue accepted — understates, never inflates; no `>=0` check), N-4 (`mask()` reveals 5/6 of a 6-char id → M6-OD-012).
  - *Ref:* `04-artifacts/boundary-reports/M6.2F_boundary.md`.

- **B3 — Security PII residuals (M6-P1506), forward-routed.**
  - **F-VIEW-1 [MEDIUM, latent — primary security finding]:** the staged `0008` support view
    (`ads_dashboard_kpi_source`) `SELECT`s the raw `attribution_context` column — which per M6.2E carries raw
    **psid** (+ comment/thread/live ids) — plus raw `page_id`/`live_session_id`. The view is the future DB-backed
    read path granted `SELECT` to `ads_dashboard_reader` at the M6-OD-011 binding, so the reader role would see raw
    psid — **broader exposure than the app** (which aggregates and never reads psid). Latent (view staged,
    `live_migrations=false`, never applied; the app is PII-safe) → no leak today, becomes a real exposure at the
    binding. Fix (CODER, before binding): drop `attribution_context` from the view, or project only non-PII fields,
    or mask psid in the view — align with the app + M6-OD-012.
  - **O-2 (carried M6.2E, → M6-OD-012):** the durable Zone-B keeps raw psid (masked on export); F-VIEW-1 is its
    dashboard-read-path manifestation. **N-4 / O-2b (→ M6-OD-012):** short-id reveal threshold + whether
    conversation/thread ids are masked on export.
  - Forward at the M6-OD-011 binding: request **authN/authZ** on `GET /api/admin/ads/dashboard` (the first admin
    endpoint, exposing revenue/metrics).
  - *Ref:* `04-artifacts/security-reports/M6.2F_security.md`.

- **B4 — Contract housekeeping (non-blocking).** CTR-015 formulas `DRAFT_LOCKED`; CTR-012/018/024
  `MISSING / OWNER_DECISION_REQUIRED` but satisfied-for-entry (producers M6-P0708/M6-P0712/M6-P0713 PASS, gate
  M6-P0715 SIGNED). Canon-flips deferred operator housekeeping.

- **B5 — Open owner decisions (forward / out-of-scope).** **M6-OD-002** (dashboard alert / scale thresholds) OPEN
  — **out of scope** for M6.2F; handled fail-closed (`DASHBOARD_ALERT_THRESHOLDS_DEFINED=False`; the dashboard
  reports values only, applies no threshold, triggers no alert/scale). **M6-OD-005** (attribution scale model) —
  multi-model display only, single-model scale forward to M6.2G (`SCALE_MODEL_RATIFIED=False`). **M6-OD-008**
  (PAYMENT_COMPLETED) blocks only the revenue *edge-handling* leg, **not** the RULE-003-fixed verified-only
  definition (decisive precedent: OD-008 also names M6.2E, which cleared). **M6-OD-012** (masking — N-4/O-2b/F-VIEW-1).
  **M6-OD-003** (hash — blocked at M6.2D, N/A here), **M6-OD-004** (connector).

- **B6 — Governance / decision-file gap (still open).** `M6-DEFER-FBC-M6.2D.json` — recommended since M6-P1209 to
  bind F-B/F-C/F-A + F-D into the M6.2G gate (M6-P1600) RequiredInputs — is **still not filed** in
  `04-artifacts/evidence/decisions/` (re-flagged by M6-P1500's next-action). The substance is carried by
  `M6-OVERRIDE-M6P1309-STAGED` and F-B/F-C/F-A/F-D are closed; the dedicated file remains an operator/owner TODO.
  (Positive: the M6.2G entry-gate row M6-P1600 already lists ENTRY-001…004 in its RequiredInputs per the ledger.)

- **B7 — Inherited cross-slice carry-forwards (still in force).** ENTRY-001/003 remain **risk-accepted** under
  `M6-OVERRIDE-M6P1000-STAGED` (M6-P1000 BLOCKED, not converted); the M6.2D slice exit was via owner override
  (`M6-OVERRIDE-M6P1309-STAGED`; M6-P1309 BLOCKED, not converted). The **mandatory M6.2G Scale-Gate re-gate
  (M6-P1600)** — re-proving ENTRY-001/002/003 (+004) — stands before any real scale or external send, and owns
  F-DASH-4.

- **B8 — Immutable governance posture.** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
  `HASH_POLICY_RATIFIED=False`, `SCALE_MODEL_RATIFIED=False`, `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False` unchanged;
  no real send, no scale, no threshold/alert; the mandatory M6.2G re-gate stands.

---

## 6. Reader's guide for the slice-gate Judge (M6-P1509)

1. Start from `00-spec/slices/M6.2F.md` "Exit gate checks" (the 9 items in §4 above).
2. For legs 1–6 + 9, read the reports/evidence in the §4 "Evidence refs" cells directly (do not rely on this index).
3. **Leg 1 (verified-only revenue) is directly bound** to SMK-004/005/015 (marked "met" by the tester) and FAIL-001
   is not tripped — but weigh the F-DASH-1/F-DASH-3 revenue-path residuals (armed-not-fired, not channel-reachable)
   and whether the dashboard overall should run the per-row DQ gate.
4. Confirm items 7 & 8 by re-reading the ledger and `04-artifacts/evidence/judge/` (M6-P1509 sign-off is the Judge's own output).
5. As the last Phase-1 slice before M6.2G, note which residuals are explicitly routed to the mandatory M6.2G
   Scale-Gate re-gate (F-DASH-4) and to the M6-OD-011 durable binding (F-VIEW-1 raw-psid view, dashboard authN/authZ),
   plus the still-open `M6-DEFER-FBC-M6.2D.json` governance TODO (§5 B6) and the inherited B7 risk-acceptances.

*This index is descriptive. It advances no gate and self-certifies nothing; the runner EVIDENCE_GATE and the
slice-gate Judge decide closure.*
