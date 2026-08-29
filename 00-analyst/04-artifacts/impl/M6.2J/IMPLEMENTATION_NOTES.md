# M6.2J IMPLEMENTATION NOTES — Phase 3 growth-machine measurement (STAGED)

**Prompt**: M6-P1902 (`M6_2J_CODER_IMPLEMENT`) · **Role**: CODER · **Mode**: `implement` · **Gate**: EVIDENCE_GATE
**Follows**: [PLAN.md](PLAN.md) (M6-P1901). Built item-by-item; **no plan-deltas**. **Posture unchanged & immutable**:
`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `SCALE_MODEL_RATIFIED=False`,
`SCALE_EXECUTION_ENABLED=False`, `HASH_POLICY_RATIFIED=False`, `LEARNING_AUTOPUBLISH_ENABLED=False`,
`LEARNING_CONTENT_FILL_ENABLED=False`, `LEARNING_SAFE_RANGE_RATIFIED=False`, `live_migrations=false`. No code sends
CRM, computes a commission, decides a member right, turns the Data Mart into a trigger, applies a migration, or
flips a flag.

> **Status: coder self-reported PASS** (the runner gate + JUDGE decide, RULE-015). The module-critical invariants —
> **measure-only** (no CRM send RULE-002; no commission RULE-019; no Data-Mart-trigger RULE-012/FAIL-005; no new
> table RULE-018), **CRM revenue verified-only + consent/eligibility/suppression gated** (SMK-008/FAIL-002), and
> **Diamond commission MEASURED-not-computed** (SMK-014) — held under a 3-dimension adversarial review driven against
> the running code: the boundary/commission/schema dimension CLEAN, and **2 CONFIRMED** growth-builder robustness
> issues (MINOR + NIT) **fixed + regressed** (§5).

## 1. Staging model — cumulative carry-forward

The whole **M6.2I** tree (final slice state, post-TESTER) was carried forward byte-identical into
`04-artifacts/impl/M6.2J/` (caches excluded; `PLAN.md` kept, this file added). Baseline verified green **BEFORE any
patch: 386 passed, rc 0** (parity with M6.2I confirmed exactly, both 386). Final suite: **414 passed, rc 0** (386
carried + 28 new: 27 initial + 1 review regression). Subprocess counts; no skips.

## 2. Change set (all under `04-artifacts/impl/M6.2J/`)

**New — the `growth/` measurement package (derived, read-only, standalone)**
| File | Purpose |
|---|---|
| `app/measurement/growth/signals.py` | `GrowthGroup` (5 doc §9 groups) + the VERBATIM doc §9 valid-signal set per group + CRM/Diamond event-code constants (doc §10 canon, none invented). |
| `app/measurement/growth/reads.py` | shared read helpers over the M6-owned store (verified_rows, event_count, entry_channel/referral reads) — reuses kpi_metrics' `_safe_div`. |
| `app/measurement/growth/models.py` | frozen `GrowthKpi` / `GrowthReport` (fail-closed None values; data-only `to_public`; no trigger field, RULE-012). |
| `app/measurement/growth/crm.py` | `CrmReorderMeasurement` — **CRM Revenue verified-only, built GATED** over `verified_rows()`: a CRM-attributed ORDER_VERIFIED row counts ONLY where CONSUMED CRM-eligibility + suppression + consent all pass (RULE-002, fail-closed; opt-out excluded, SMK-008). Repeat rate. Does NOT use the ungated `DataMart.crm_revenue()`. No CRM send surface. |
| `app/measurement/growth/diamond.py` | `DiamondReferralMeasurement` — records referral attribution (referral_link_id + buyer identity **masked**); Diamond Revenue verified-only; **commission-ready revenue** = verified commission-ELIGIBLE revenue (CONSUMED flag); **NO commission amount/rate/payout method** (RULE-019). Diamond lead rate. |
| `app/measurement/growth/reactivation.py` | `ReactivationMeasurement` — dormant-segment reactivation gated on consent (reuse `ConsentGate`, CRM scope) + CONSUMED CRM-eligibility (fail-closed — opt-out/ineligible excluded). Reactivation rate, CPA. Measure-only. |
| `app/measurement/growth/growth.py` | `GrowthReportBuilder` — the doc §9 5-group KPI assembler, each KPI from its listed valid signals: CRM/Repeat from `crm`, Diamond from `diamond`, Reactivation from `reactivation`, AOV/boxes reused from `DataMart`, Learning-Engine **approval rate** from the review queue + **uplift** from consumed verified cohorts + **drift** from the Data Quality Gate (rows whose `data_quality_status` is FAIL). Read-only; NO trigger/send/commission method. |

**Patched (carried-forward)** — none (the growth layer is standalone; the M6.2I dashboard-wiring lesson).
**No new migration** (doc §13 defines no growth table — RULE-018). **No new config flag** (measure-only).

**Tests (new)** + `tests/conftest.py` fixtures (`make_crm_consent`, `make_crm_measurement`, `make_diamond_measurement`,
`make_reactivation`, `make_growth_builder`).

## 3. Tests → smoke/leg mapping (TESTER executes the official smokes)

| Test | Proves | Leg / smoke |
|---|---|---|
| `test_crm_reorder_revenue_verified_only.py` | CRM Revenue verified-only + gated (eligibility+suppression+consent); click/CRM_REORDER_SENT never revenue; repeat rate | **L1** (RULE-002/003) |
| `test_crm_optout_excluded.py` | opt-out/expired/missing/scope-not-granted consent ⇒ excluded; no CRM send surface | **SMK-008 / FAIL-002** |
| `test_diamond_referral_no_commission.py` | referral attribution recorded; Diamond Revenue + commission-ready measured; **NO commission method**; buyer identity masked; lead rate | **L2 / SMK-014 / RULE-019** |
| `test_reactivation_consent_eligibility_failclosed.py` | reactivation counts only consent-valid + CRM-eligible members; opt-out/ineligible excluded; fail-closed None | RULE-002 |
| `test_growth_kpis_from_valid_signals_only.py` | the 5-group doc §9 KPIs each from valid signals; fail-closed None; **named-segment-but-unwired-reactivation fails closed** (regression); uplift/ads-ratio from consumed cohorts | doc §9 growth KPIs |
| `test_data_mart_stays_support_view.py` | the Data Mart + growth builder expose no trigger; growth report is data-only | **SMK-010 / RULE-012 / FAIL-005** |
| `test_growth_measure_only_boundary.py` | crm/diamond/reactivation/builder expose no send/commission/member-rights/scale/publish/order-state/trigger verb | boundary (FAIL-002/004/005) |

Smoke EXECUTION + official SMK-008/010/014 authoring is the TESTER's (M6-P1903/1904) — no self-run (RULE-015).

## 4. (No plan-deltas)

Everything matches PLAN §5. CRM Revenue is built gated in `crm.py` over `verified_rows()` (not the ungated
`crm_revenue()`), per the M6-P1901 review fix; Learning-Engine KPIs are sourced approval-rate←review-queue,
uplift←verified cohorts, drift←DQ gate, per the plan §4.1/§9.

## 5. Adversarial self-review (ultracode) — 2 CONFIRMED (fixed), boundary dimension CLEAN

A read-only adversarial review (3 dimensions, each finding re-verified by an independent skeptic RUNNING the code)
found: **boundary/measure-only/commission/invented-schema CLEAN** (no commission computed, no CRM send, no
Data-Mart-trigger, no new table); and **two growth-builder robustness issues**, both fixed:
- **(MINOR) `build()` crashed** with AttributeError when a dormant segment was named but the reactivation
  measurement was unwired (`reactivation=None`) — the guard keyed only on the segment id, unlike the sibling
  queue/store guards. **Fix**: guard on the dependency too (`have_react = bool(seg) and self._reactivation is not
  None`) → fail-closed None. **Regression added** (`test_named_dormant_segment_without_reactivation_is_failclosed_not_crash`).
- **(NIT) fail-closed note omitted** for uplift / ads-ratio-reduction when the missing operand was the numerator (or
  baseline == 0) — the value was correctly None but carried no note. **Fix**: base the note on the computed value.

No PII/masking, reuse, or formula-fidelity findings (buyer identity masked, `_safe_div` reused, the doc §9 formulas
matched). Not a gate sign-off — the runner gate + JUDGE (M6-P1909) decide.

## 6. Rollback

Staged only — baseline rollback = delete the M6.2J tree (M6.2I untouched). Per-item: new `growth/` files → delete;
**no carried-forward file is patched** (nothing to revert). No migration to unwind (none added). The projection is
derived + read-only — removing it leaves `ads_measurement_events` / `ads_attribution_context` / the consumed
segments exactly as M6.2I left them.

## 7. Scope & governance (unchanged)

In scope built: the CRM repeat/reorder gated-revenue measurement, the dormant/reactivation measurement, the Diamond
referral attribution + verified/commission-ready revenue (no commission), the value-optimization + Learning-Engine
growth KPIs, the doc §9 growth-report assembler. OUT (not built): sending CRM (CRM Messaging owns), member-rights
decisions, final commission/payout (Finance, RULE-019), Data Mart as a trigger (RULE-012/FAIL-005), Core/CRM/Diamond
override (FAIL-004), pricing (M3), order-state (M8), consult content (M4), public reply (M5), live-ops (M7),
scale/publish. No raw secrets/PII (buyer identity masked; aggregate KPIs only). FAIL-002 not tripped (consent
fail-closed); FAIL-004 not tripped (no override); FAIL-005 not tripped (Data Mart support-view only). `M6-P1000` +
`M6-P1309` verdicts stay BLOCKED (not converted).
