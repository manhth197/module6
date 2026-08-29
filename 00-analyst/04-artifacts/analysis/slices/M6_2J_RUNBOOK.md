# M6.2J — Slice Runbook — Phase 3 CRM / Diamond / Lifecycle growth (measure-only)

| Field | Value |
|---|---|
| Slice | **M6.2J — Phase 3 CRM/Diamond/Lifecycle** (growth-machine measurement; a **derived, read-only, standalone projection**) |
| Written by | **M6-P1908** — `M6_2J_DOCS` (ANALYST_ARCHITECT, `analysis_only`) |
| ADS phase | **Phase 3** (per the slice spec) |
| Depends on | M6.2I (slice gate M6-P1809 SIGNED) |
| Doc source | doc §9 growth machine (repeat/CRM/Diamond/value attribution) + the MONITORING_REGISTER growth-KPI table |
| Done gate (slice spec) | **CRM revenue verified · Diamond revenue verified** |
| Objective | Measure the Phase-3 growth machine: repeat/reorder, dormant reactivation, Diamond referral + value-optimization signals; the Data Mart stays a support view. The slice proves capability with evidence; it flips no flag, sends no CRM, computes no commission, triggers nothing. |

> **Read this first — the band is clean, but two findings are the real story.** Entry gate a real Judge PASS
> (M6-P1900 `SIGNED`), all seven band prompts self-report PASS, and **all three** in-scope fail gates held —
> **M6-FAIL-002** (consent), **M6-FAIL-004** (core override / commission), **M6-FAIL-005** (Data Mart abuse). The
> slice adds **no new table / migration / CTR / config flag** — a standalone read-only growth projection (RULE-018),
> and it sends no CRM (RULE-002), computes no commission (RULE-019, commission is **measured-not-computed**), and
> keeps the Data Mart a support view (RULE-012). But "clean" is not "closed": exit legs 1 & 2 are **SUPPORTED at the
> staged level** (green smokes + leg tests, both gates hold), not independently closed, and they carry **two sharp
> armed-not-fired findings, both of which are known-controls-not-applied on this surface** (§5.2):
> **(1) F-SEC-2J-1 / F-GROWTH-1 — borrowed consent:** the CRM gate validates consent by `order_code` but **never
> binds it to the row's buyer**, so a *different* subject's valid CRM consent keyed to the order authorizes the
> buyer's CRM Revenue KPI — the exact subject-bind the M6.2E seam already enforces (F-D fix) and the Diamond path
> here already does, simply **omitted** on the CRM path. **(2) F-GROWTH-3 — revenue-choke regression:** the growth
> reads key off `revenue_value is not None`, **not** `event_code == 'ORDER_VERIFIED'` — the self-enforcing choke
> M6.2I just adopted to close F-DASH-1 was **not carried forward** here, and it feeds a **Finance-facing
> commission-ready figure**. Posture is immutable: `global_gateway_state=BLOCKED`, `production_flag=OFF`,
> `external_send=OFF`, all M6.2A–I flags False, `live_migrations=false`; `M6-P1000` and `M6-P1309` verdicts **remain
> BLOCKED (not converted)**. This runbook advances no gate and self-certifies nothing; the runner EVIDENCE_GATE and
> the slice-gate Judge (M6-P1909) decide.

---

## 1. What this slice built (staged under `04-artifacts/impl/M6.2J/`)

Everything is **staged**. The whole M6.2I tree is carried forward byte-identical; M6.2J **adds** a `growth/`
measurement package — and **nothing else** (no migration, no config flag, no patched carried file). **Nothing acts**
— no code sends CRM, computes a commission, decides a member right, turns the Data Mart into a trigger, applies a
migration, or flips a flag.

### 1.1 The growth layer (new `app/measurement/growth/`) — a derived read-only projection

| File | What it is | Contract / Rule |
|---|---|---|
| `growth/signals.py` | `GrowthGroup` (the 5 doc §9 groups) + the verbatim doc §9 valid-signal set per group + CRM/Diamond event-code constants (doc §10 canon, **none invented**). | RULE-018 |
| `growth/reads.py` | Shared read helpers over the M6-owned store (`verified_rows`, `event_count`, entry-channel/referral reads) — reuses `kpi_metrics._safe_div`. | — |
| `growth/models.py` | Frozen `GrowthKpi` / `GrowthReport` (fail-closed None values; data-only `to_public`; **no trigger field**, RULE-012). | RULE-012 |
| `growth/crm.py` | `CrmReorderMeasurement` — **CRM Revenue verified-only, built GATED** over `verified_rows()`: a CRM-attributed ORDER_VERIFIED row counts **only** where the consumed CRM-eligibility + suppression + consent all pass (RULE-002, fail-closed; opt-out excluded, SMK-008). Repeat rate. Does **not** use the ungated `DataMart.crm_revenue()`. **No CRM send surface.** | RULE-002/003 |
| `growth/diamond.py` | `DiamondReferralMeasurement` — records referral attribution (`referral_link_id` + buyer identity **masked** on export); Diamond Revenue verified-only; **commission-ready revenue = verified commission-ELIGIBLE revenue** (a consumed Finance flag); **NO commission amount/rate/payout method** (RULE-019). Diamond lead rate. | RULE-019 |
| `growth/reactivation.py` | `ReactivationMeasurement` — dormant-segment reactivation gated on consent (reuse `ConsentGate`, CRM scope) + the consumed CRM-eligibility flag (fail-closed — opt-out/ineligible excluded); `member_key` never emitted. Reactivation rate, CPA. Measure-only. | RULE-002 |
| `growth/growth.py` | `GrowthReportBuilder` — the doc §9 5-group KPI assembler; each KPI from its listed valid signals (CRM/Repeat ← `crm`, Diamond ← `diamond`, Reactivation ← `reactivation`, AOV/boxes ← `DataMart`, Learning-Engine approval-rate ← the review queue, uplift ← consumed verified cohorts, drift ← the Data Quality Gate). Read-only; **no trigger/send/commission method**. | RULE-012 |

### 1.2 The doc §9 growth KPIs (5 groups; each computed only from its listed valid signals)

| Group | KPIs |
|---|---|
| **CRM / Repeat** | Repeat rate · CRM Revenue · AOV |
| **Reactivation** | Reactivation rate · CPA reactivation |
| **Diamond** | Diamond lead rate · Diamond Revenue · commission-ready revenue |
| **Value optimization** | CLV proxy · boxes/order · ads-ratio reduction |
| **Learning-Engine** | Candidate approval rate · uplift · drift violations |

Every rate is fail-closed (0/None denominator → None, never fabricated). CRM/Diamond revenue is **verified-only**;
click / chat / `CRM_REORDER_SENT` are **never** revenue. Commission is **measured-not-computed** — `commission-ready
revenue` is the subset of verified referral revenue whose consumed Finance eligibility flag is True, fail-closed to 0
without it; Finance owns the actual commission.

### 1.3 No new migration, no new config flag, no patched carried file (deliberate)

Doc §13 defines no growth table; inventing one would breach RULE-018. The projection reads the existing stores;
measure-only ⇒ no new posture flag; and the growth layer is standalone (no carried file patched — the M6.2I
dashboard-wiring lesson applied up front).

---

## 2. Operate

M6.2J is a **measure-only, read-only projection**. There is no "send CRM / compute commission / trigger" step — by
design.

1. **Build the growth report** — `GrowthReportBuilder.build()` reads the M6-owned store + consumed segments and
   returns the doc §9 5-group KPIs as a plain `{kpis: […]}` dict. It writes nothing; building it twice mutates nothing.
2. **Measure CRM revenue** — counts a verified CRM-attributed row **only** on all-pass consent + eligibility +
   suppression (opt-out fail-closed excluded, SMK-008). No CRM send surface.
3. **Measure Diamond referral** — records referral attribution (buyer masked on export) + verified / commission-ready
   revenue; **no commission is computed** (SMK-014).
4. **What is structurally impossible here** — sending CRM, computing a commission, overriding Core/CRM/Diamond,
   turning the Data Mart into a trigger, deciding a member right.

> **Owner-facing caveat (do not skip).** The growth report is a **standalone library wired to no endpoint today**
> (no access-control regression). Before it is surfaced through the admin dashboard, the M6-OD-011 binding must
> (a) **authenticate/authorize the admin caller** (doc §22 line 429; the carried `handle_dashboard_request` does not
> itself authenticate), (b) apply the **`buyer_ref` masking** discipline at that export boundary, and (c) close the
> two consent/revenue-integrity findings in §5.2 before any CRM Revenue / commission-ready figure is trusted for a
> decision.

---

## 3. Verify

**Verify env:** `02-tester/.venv` — python **3.12.13**, pytest **8.4.2**, pluggy 1.6.0 (matches the
`IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin). Run from `04-artifacts/impl/M6.2J/` (STAGED_ONLY), cache-free.

### 3.1 Bound smoke

| Smoke ID | Doc ID | Scenario → Expected (verbatim, SMOKE_REGISTER) | Test file | Result |
|---|---|---|---|---|
| **M6-SMK-008** | ADS-P0-008 | `CRM opt-out` → `Không sync CRM audience/CRM event outbound` | `tests/smoke/test_smk_008_crm_optout_no_sync.py` | **PASS 4/4** |
| **M6-SMK-010** | ADS-P0-010 | `Data Mart tạo trigger CRM/scale` → `Fail - Data Mart chỉ support view` | `tests/smoke/test_smk_010_growth_data_mart_support_view_only.py` | **PASS 3/3** |
| **M6-SMK-014** | ADS-P0-014 | `Diamond referral order verified` → `Gắn referral attribution, không tự tính commission` | `tests/smoke/test_smk_014_diamond_referral_no_commission.py` | **PASS 4/4** |

Bound-smoke total: **11 passed, 0 failed — exit 0**. SMK-008: opt-out/expired/missing/wrong-scope consent
fail-closed excluded, valid CRM consent counted, no send surface. SMK-010: neither the DataMart nor the
GrowthReportBuilder exposes a trigger verb; the report is data-only; building it mutates nothing. SMK-014: a verified
referral records attribution + measured Diamond/commission-ready revenue, **no commission method exists**, buyer
identity masked on export, commission-ready fail-closed to 0 without the consumed eligibility flag.

```bash
# from 04-artifacts/impl/M6.2J/  (venv: 02-tester/.venv, python 3.12.13)
python -m pytest -v tests/smoke/test_smk_008_crm_optout_no_sync.py tests/smoke/test_smk_010_growth_data_mart_support_view_only.py tests/smoke/test_smk_014_diamond_referral_no_commission.py -p no:cacheprovider
# -> 11 passed ; exit 0
```

### 3.2 Full staged suite

**425 passed, 0 failed, 0 skipped, 0 error — RC 0.**
Breakdown: **386 carried-forward** (M6.2A–I) **+ 39 new M6.2J nodes** (28 growth-leg + 11 bound smoke).

> **Test-count reconciliation (be precise).** The **tester-run final is 425** (M6-P1904 / SMOKE_RESULTS.md). The
> coder note (M6-P1902) records **414** = 386 carried + the **28 growth-leg tests it authored** (27 initial + 1
> review regression); the **11 bound smoke** nodes (SMK-008 4 + SMK-010 3 + SMK-014 4) were authored by the
> **TESTER** in M6-P1903 and run in M6-P1904, so the tester-run final adds them (414 + 11 = 425). Per test-count
> discipline this runbook cites the **tester-run final 425**. (Continuity: the 386 carried matches the M6.2I
> tester-run final 386 exactly.)

The 28 growth-leg tests (supporting coverage, all green inside the 425): `test_crm_optout_excluded.py` (4),
`test_crm_reorder_revenue_verified_only.py` (5), `test_data_mart_stays_support_view.py` (3),
`test_diamond_referral_no_commission.py` (5), `test_reactivation_consent_eligibility_failclosed.py` (4),
`test_growth_kpis_from_valid_signals_only.py` (3), `test_growth_measure_only_boundary.py` (4).

### 3.3 All three in-scope fail gates — NOT tripped

- **M6-FAIL-002 (consent) — held.** CRM revenue and reactivation are consent + eligibility + suppression gated
  (opt-out / expired / missing / wrong-scope / truthy-not-True all fail-closed excluded; strict `is True`). The
  borrowed-consent gap (F-SEC-2J-1, §5.2) does **not** flip the gate — `consent_by_order` is a consumed Consent/CRM
  map, not channel input — but it is the sharpest consent finding.
- **M6-FAIL-004 (core override / commission) — held.** No commission amount/rate/payout method anywhere; a token
  sweep finds 0 override defs. `commission-ready revenue` is a revenue subset gated by a consumed Finance flag
  (fail-closed to 0); the report carries no override field (RULE-019).
- **M6-FAIL-005 (Data Mart abuse) — held.** The DataMart and GrowthReportBuilder expose no trigger/send/write verb
  (SMK-010); the report is data-only; building it mutates nothing. The only Data-Mart concern is the naming risk
  F-SEC-2J-3, not a trigger path.

Security scan: **0 raw PII, 0 secrets over 204 files** (the 3 `sk-` hits are `risk-*` prose in carried files).

---

## 4. Rollback (every change this slice made) — *acceptance check 1*

Everything is **staged** ⇒ rollback is non-destructive. The projection writes nothing to the stores.

| Change | Rollback |
|---|---|
| **Baseline (all M6.2J)** | Delete the `04-artifacts/impl/M6.2J/` tree. M6.2I is untouched (carried forward byte-identical). |
| `growth/signals.py`, `reads.py`, `models.py`, `crm.py`, `diamond.py`, `reactivation.py`, `growth.py` (new) | Delete the files. |
| New tests (7 growth-leg files + 3 bound smoke files) + `conftest.py` fixtures | Delete the files / revert the fixture additions. |
| **Patched carried-forward files** | **None** (the growth layer is standalone; nothing to revert). |
| **Migrations** | **None added.** No new table (RULE-018); nothing to unwind. |

The projection is derived + read-only: removing it leaves `ads_measurement_events` / `ads_attribution_context` /
the consumed segments exactly as M6.2I left them. There is **no** production/state/flag change to reverse.

---

## 5. Decision deltas & governance

### 5.1 Coder self-fixes (M6-P1902 §5) — 2 confirmed, both fixed + regressed; boundary dimension CLEAN

The coder's own 3-dimension adversarial self-review found the boundary/commission/schema dimension CLEAN and fixed
two growth-builder robustness issues: (MINOR) `build()` crashed with `AttributeError` when a dormant segment was
named but the reactivation measurement was unwired (`reactivation=None`) — the guard keyed only on the segment id;
fixed to guard on the dependency too (fail-closed None), with a regression; and (NIT) a fail-closed note was omitted
for uplift / ads-ratio-reduction when the missing operand was the numerator — fixed to base the note on the computed
value. **This did not surface the §5.2 findings** — those came from the independent boundary (M6-P1905) and security
(M6-P1906) passes.

### 5.2 The two sharp findings — known controls not applied on this surface (armed-not-fired; neither trips a gate)

Both are the same failure shape: a discipline **already enforced elsewhere in the codebase** was **not applied** on
a M6.2J growth path. Neither is channel-reachable, so neither trips an in-scope gate — but both must close before any
CRM Revenue / commission-ready figure is trusted or the report is surfaced.

- **F-SEC-2J-1 / F-GROWTH-1 [PRIMARY — consent integrity, RULE-002/FAIL-002].** `CrmReorderMeasurement._crm_gate_passes`
  evaluates the consent snapshot fetched by **`order_code`** but **never asserts `snapshot.subject_ref` equals the
  verified row's buyer** (`customer_id`/`guest_id`). Executed: a *different* subject's VALID CRM consent, keyed to
  the order, authorized the buyer's CRM Revenue straight into the doc §9 KPI (`crm_revenue() == 650000`). **Not
  channel-reachable** (`consent_by_order` is a consumed Consent/CRM-owned map; it fires only on an upstream mis-key
  or an in-process adversarial `CrmConsumed`). **Why it matters:** the M6.2E conversion seam already enforces this
  exact bind (the F-D fix, `safe_subject_ref(snap) == customer_or_guest_key`) and the **Diamond path here already
  reads the row's `customer_id`/`guest_id`** — the CRM growth gate simply **omits** it. **Fix (CODER):** in
  `_crm_gate_passes`, require `snapshot.subject_ref == the row's customer_id/guest_id` before counting, mirroring the
  M6.2E F-D discipline (and consider the same explicit bind on the reactivation path).
- **F-GROWTH-3 [revenue integrity, RULE-003 — cross-slice regression].** `reads.verified_rows` keys off
  `revenue_value is not None`, **not** `event_code == 'ORDER_VERIFIED'`. Combined with the materializer deriving
  `verified` from `conversion.event_code`, a mispaired (ORDER_VERIFIED conversion, QUOTE_SENT event) call stamps
  revenue onto a quote-content row, which the growth layer then counts as CRM / Diamond / **commission-ready**
  revenue. **Not channel-reachable** (the materializer is test-only) and FAIL-001 is out-of-scope for this slice —
  **but it reaches a Finance-facing commission-ready figure and is a RULE-003 cross-slice consistency regression vs
  M6.2I**: the self-enforcing choke M6.2I just adopted to close F-DASH-1 was **not carried forward** into the growth
  reads. **Fix (CODER):** `verified_rows` should AND `event_code == 'ORDER_VERIFIED'` with revenue presence (adopt
  the M6.2I lesson) — this also aligns the "+ ORDER_VERIFIED" clause of exit legs 1 & 2.

### 5.3 Other residuals (armed-not-fired; none trips a gate) — routed to CODER / M6-OD-012

| ID | Sev | What | Route / fix |
|---|---|---|---|
| **F-SEC-2J-2** (= boundary N-1) | PII / masking | `ReferralAttribution.buyer_ref` holds a **raw** customer/guest id on the public dataclass attribute; masking is applied **only** in `to_public()`, and `referral_attributions()` hands out raw-bearing objects. Not in the shipped aggregate report (latent), but `buyer_ref` is a **direct first-party id — higher sensitivity than a psid**. | CODER + owner (M6-OD-012): make masking non-optional at the identity boundary (store the masked form / gate raw access); ratify the export masking scope. Same M6-OD-012 decision as the M6.2I F-SEC-2I-2 trace-id finding. |
| **F-SEC-2J-3 / F-GROWTH-2** | naming / labeling | A consent-blind `DataMart.crm_revenue` twin (a carried M6.2F channel-breakdown aggregate, `=800000`) is reachable via `builder._mart`; the shipped §9 KPI correctly uses the **gated** `crm.crm_revenue` (`=0` without consent). Only naming keeps the ungated number out of "CRM Revenue". | CODER + owner: rename/mark the ungated aggregate (e.g. `crm_channel_revenue`) or gate it. |
| **F-SEC-2J-4 / F-GROWTH-4** | measurement integrity | The Learning-Engine "Candidate approval rate" KPI counts `review_state.value == 'APPROVED'` only, **not** `is_publish_authorized` / the audited `OwnerReviewDecision` — a construction-marked candidate inflates the rate (it publishes nothing; the M6.2H `is_publish_authorized` still gates real publish). | CODER: count only candidates with a bound audited decision (and/or `is_publish_authorized`). |
| **F-GROWTH-5** | untrusted collaborator | `GrowthReportBuilder.build()` duck-types every injected collaborator (`queue.all()`, `store.all()`, the mart reads) with **no** `isinstance`/Protocol guard, so a mis-wired side-effecting collaborator would run during `build()`. In-process only (shipped `.all()` are pure reads). | CODER: add a Protocol / `isinstance` assertion so `build()` cannot be pointed at an action-bearing queue/store. |

### 5.4 Positive: the standing FBC deferral is now FILED (a cross-slice TODO closed)

`M6-DEFER-FBC-M6.2D.json` — the cross-slice consent-binding record flagged **absent** across the M6.2D–M6.2I
indexes (and called out as an operator TODO in the earlier runbooks) — is now **FILED** in
`04-artifacts/evidence/decisions/` (owner-confirmed 2026-08-07). It records the consent fail-open class (F-A..F-F)
as **CLOSED** (code-verified + adversary-confirmed) and wires the binding as a **M6-P1600 Scale-Gate RequiredInput**.
One residual canon step remains — adding its path to `M6-P1600` `inputs_expected` in `00-spec` (an operator/generator
edit) — but the on-disk filing is what the gate checks (the M6-P1600 judge already globs the decisions dir).

### 5.5 Forward gates + immutable posture

- **ACCESS forward (M6-OD-011):** authenticate/authorize the admin caller (doc §22 line 429) + mask `buyer_ref` when
  the growth report is bound to the dashboard. Mirrors ACCESS-1 at M6.2G/H/I. **M6-OD-012** (masking scope — now with
  F-SEC-2J-2). **M6-OD-003** (external-send hash policy) is **N/A** to this measure-only slice (no external payload,
  sends nothing) — honest N/A, not BLOCKED.
- **Inherited (M6.2G–M6.2I, still in force):** the four attestation true-ups; ENTRY-001/003/004 conditions;
  M6-OD-002/003/004/005; the M6.2G F-SCALE-* + M6.2H F-LEARN-* + M6.2I F-FUNNEL-*/F-SEC-2I-* residuals; the
  M6-OD-006/007 learning gates; ACCESS-1/authN + store/queue-laundering fixes at M6-OD-011. The mandatory M6.2G
  Scale-Gate re-gate stands before any real scale/publish/send.
- **Immutable posture (intact across M6.2A–J):** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
  `external_send=OFF`, all scale/hash/learning flags **False**, `live_migrations=false`. `M6-P1000` + `M6-P1309`
  verdicts remain **BLOCKED (not converted)**. FAIL-002/004/005 not tripped; the growth layer measures only.

---

## 6. Changelog delta — *acceptance check 2*

- **No new `SCHEMA_CHANGELOG` row is appended by this slice.** This is an `analysis_only` docs prompt (the analyst
  is denied write to `00-spec/registers/`), and the slice introduces **no canon schema change**.
- **No canon-flip is pending for this slice.** The sole contract it uses — **CTR-002** (`ads_attribution_context`,
  19 fields, doc §11) — is already **`DRAFT_LOCKED`** in the canon `CONTRACT_REGISTER` (built at M6.2E). The growth
  layer **reads** it; it does not re-define it, and it introduces no new contract.
- **This slice deliberately adds no schema at all** (RULE-018): **no new table, no new migration, no new config
  flag, no new CTR** — the concrete artifact added is only the staged `app/measurement/growth/` package (a derived
  read-only projection), and **no carried file was patched**.
- **Governance-record delta (not a schema change):** `M6-DEFER-FBC-M6.2D.json` is now **FILED** in
  `04-artifacts/evidence/decisions/` (§5.4) — the one residual canon step (its path into `M6-P1600` `inputs_expected`)
  is an operator/generator edit, outside this analyst docs prompt's scope.

---

## 7. Handoff

- **What this slice is.** A measure-only Phase-3 growth projection (CRM/Diamond/reactivation/value-optimization/
  Learning-Engine KPIs, doc §9) over the existing stores. Standalone; wired to no endpoint.
- **Exit-gate state at this docs step** (from the evidence index — M6.2J has **8** exit-gate items):
  - Items **3, 4, 5, 8 = MET** (SMK-008 4/4; SMK-010 3/3; SMK-014 4/4; rollback documented per item).
  - Items **1, 2 = SUPPORTED (staged)** — green smokes + leg tests and all three fail gates hold, but the
    F-SEC-2J-1 (borrowed consent) + F-GROWTH-3 (revenue-choke regression, feeds the commission-ready figure) +
    F-SEC-2J-2/3/4 residuals remain (armed-not-fired), so **final closure is the slice-gate Judge's call**.
  - Item **6** (all slice prompts have evidence JSON) closes when **M6-P1908** (this docs prompt) and **M6-P1909**
    (Judge) produce their evidence — after this prompt, only **M6-P1909.json** is outstanding.
  - Item **7** (slice-gate Judge PASS sign-off) closes only at **M6-P1909**.
- **Next slice.** After the M6.2J slice-gate Judge (M6-P1909), the next prompt is the **M6.2K entry-gate Judge
  (M6-P2000)** (ledger row 178).
- **CODER TODO (before any real send / before the report is surfaced):** **F-SEC-2J-1 / F-GROWTH-1** (bind
  `subject_ref` to the row's buyer in the CRM gate — the top item), **F-GROWTH-3** (AND `event_code ==
  'ORDER_VERIFIED'` in `verified_rows`), **F-SEC-2J-3** (rename/gate the ungated `crm_revenue` twin), **F-SEC-2J-4**
  (count approvals by the audited decision), **F-GROWTH-5** (guard the builder's collaborators).
- **Owner / M6-OD-011 binding:** **F-SEC-2J-2** + **M6-OD-012** (make `buyer_ref` masking non-optional; ratify the
  masking scope); **ACCESS** (authenticate the admin caller + mask `buyer_ref`) when the report is wired to the
  dashboard; plus the inherited M6.2G–M6.2I forward chain. **Operator:** the residual FBC canon step (§5.4) — add
  `M6-DEFER-FBC-M6.2D.json` to `M6-P1600` `inputs_expected` in `00-spec`.

---

## 8. Pointers for the slice-gate Judge (M6-P1909)

The Judge renders the slice verdict **strictly from the evidence files** (this runbook is descriptive, not a
verdict). Suggested reading order:

1. `00-spec/slices/M6.2J.md` "Exit gate checks" — the 8 items.
2. For legs 1–5 + 8, read the primary evidence directly (do **not** rely on this runbook or the index):
   `04-artifacts/test-reports/M6.2J/SMOKE_RESULTS.md`, `04-artifacts/boundary-reports/M6.2J_boundary.md`,
   `04-artifacts/security-reports/M6.2J_security.md`, `04-artifacts/impl/M6.2J/PLAN.md` +
   `IMPLEMENTATION_NOTES.md` §6 (rollback).
3. **Confirm the measure-only posture** (no new table/migration/CTR/flag; no CRM send; commission measured-not-computed;
   Data Mart support-view-only) and that **all three in-scope fail gates (FAIL-002/004/005) are not tripped**.
4. **Weigh the two sharp findings (§5.2) as the load-bearing items:** F-SEC-2J-1 (borrowed consent — the CRM gate
   omits the subject-bind the M6.2E seam and the Diamond path here already enforce) and F-GROWTH-3 (the revenue-choke
   regression vs M6.2I that reaches a Finance-facing figure). Both are armed-not-fired (not channel-reachable) but
   are known-controls-not-applied and must close before any CRM Revenue / commission-ready figure is trusted.
   F-SEC-2J-2/3/4 + F-GROWTH-5 are the supporting masking/naming/integrity items; the ACCESS requirement closes at
   the M6-OD-011 binding.
5. **Confirm items 6 & 7** by re-reading the ledger and `04-artifacts/evidence/judge/` (the M6-P1909 sign-off is the
   Judge's own output).
6. Treat the inherited **§5.5 forward-gate chain** and the standing **BLOCKED `M6-P1000` / `M6-P1309`** verdicts as
   the conditions before any real scale, publish, send, or admin surface — none of which this measure-only slice
   satisfies or claims to. (Governance-positive to note: `M6-DEFER-FBC-M6.2D.json` is now FILED — §5.4.)

*This runbook advances no gate and self-certifies nothing. The runner EVIDENCE_GATE and the slice-gate Judge
(M6-P1909) decide closure. `global_gateway_state=BLOCKED`, `production_flag=OFF`; the growth layer only measures.*
