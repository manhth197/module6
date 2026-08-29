# M6.2J IMPLEMENTATION PLAN — Phase 3 growth-machine measurement (STAGED, plan-only)

**Prompt**: M6-P1901 (`M6_2J_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code this prompt)
**Slice**: M6.2J — measure the Phase-3 growth machine (doc §9): repeat/reorder, dormant reactivation, Diamond
referral, value-optimization signals; **Data Mart remains a support view**. Depends on M6.2I. **Done gate**:
*CRM/Diamond revenue verified.*
**Posture (immutable)**: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
`SCALE_MODEL_RATIFIED=False`, `SCALE_EXECUTION_ENABLED=False`, `HASH_POLICY_RATIFIED=False`,
`LEARNING_AUTOPUBLISH_ENABLED=False`, `LEARNING_CONTENT_FILL_ENABLED=False`, `LEARNING_SAFE_RANGE_RATIFIED=False`,
`live_migrations=false`. This plan writes no code, applies no migration, sends nothing (no CRM send), computes no
commission, decides no member right, resolves no owner decision, flips no flag.

> **Top-0.1% design lens (load-bearing — it CHANGED the design, not a label).** Four failure modes a strong
> growth-measurement architect would flag, each of which altered this plan:
> 1. **Computing a commission (RULE-019 breach).** The doc §9 Diamond KPI names "commission-ready revenue" — a
>    tempting place to multiply revenue by a rate. → The Diamond measurement RECORDS referral attribution + sums
>    the verified revenue that is commission-**eligible** (a CONSUMED Core/Finance flag); it exposes **NO** method
>    that computes a commission amount / rate / payout. Finance owns commission (RULE-019, SMK-014).
> 2. **Counting a click/chat as CRM revenue (RULE-002 / FAIL-002).** → CRM revenue is verified-only AND gated on
>    CRM-eligibility + suppression-pass + consent-valid (all CONSUMED, fail-closed); a CRM_REORDER_SENT /
>    engagement signal is never revenue. Opt-out ⇒ excluded (SMK-008).
> 3. **Letting the Data Mart become a trigger (RULE-012 / FAIL-005).** → The growth layer READS the Data Mart
>    (support view) and exposes NO CRM/pricing/Diamond/scale trigger; the Data Mart stays read-only (SMK-010).
> 4. **Inventing a growth table (RULE-018).** Doc §13 defines no repeat/reactivation/Diamond/growth table. →
>    **No new table / migration / CTR / config flag.** M6.2J is a DERIVED read-only projection over the existing
>    `ads_measurement_events` (CTR-001), `ads_attribution_context` (CTR-002), the Data Mart support view, and the
>    CONSUMED `customer_segments` / consent snapshots — REUSING the M6.2F `DataMart` **verified-revenue choke**
>    (`verified_rows()`) + `diamond_revenue()` (Diamond Revenue is verified-only with no consent gate) + AOV/boxes,
>    and the `ConsentGate`, adding only the doc §9 growth-specific KPIs. **CRM Revenue is built GATED in new C4 code
>    (eligibility + suppression + consent), NOT from the ungated `DataMart.crm_revenue()` aggregate.**
> And the M6.2I lesson: **do not wire into the dashboard** (adding to `DashboardDeps` broke a TESTER-owned smoke
> in M6.2I) — the growth layer is delivered STANDALONE.
> Load-bearing invariants: revenue only from ORDER_VERIFIED (RULE-003 carries into CRM/Diamond revenue); consent
> fail-closed (RULE-002/FAIL-002); Data Mart support-view only (RULE-012/FAIL-005); no commission (RULE-019); no
> Core/CRM/Diamond/member-rights override (FAIL-004); measure-only at every edge.

---

## 1. Entry-gate verification

| Precondition | Source | Result |
|---|---|---|
| This prompt RUNNING | ledger (order 167) | **M6-P1901 = RUNNING** ✓ |
| Dependency resolved | ledger | **M6-P1900 = SIGNED** (M6.2J entry judge PASS, opens the slice STAGED) ✓; M6.2I exit **M6-P1809 = SIGNED** ✓ |
| Target LOCKED + M6-OD-011 | `04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json` | `status=LOCKED`, `STAGED_ONLY`, safety all false; **M6-OD-011 DECIDED** 2026-07-23 ✓ |
| Slice contract | slice §Contract-checklist + M6-P1900 | sole contract **CTR-002** (ads_attribution_context) **DRAFT_LOCKED** and already BUILT (M6.2E) — resolved-for-entry ✓ |
| OPEN owner decisions vs scope | DECISION_REGISTER (M6.2J sweep) + M6-P1900 | **ZERO** owner decisions name M6.2J (M6-OD-002 thresholds remain OPEN globally → numeric alert thresholds NOT applied, fail-closed, same as kpi_metrics) ✓ |
| Phase order | ledger A..I chain PASS/SIGNED | Phase 1+2 complete + sequential → **no phase jump** (M6.2J is the Phase-3 slice, opened only after M6.2I SIGNED) ✓ |
| Flags | manifest/brief | BLOCKED/OFF/OFF + all scale/hash/learning flags unchanged; `live_migrations=false` ✓ |
| M6.2I foundation | `04-artifacts/impl/M6.2I/` (378 tests green) | present; carries CTR-001/002, DataMart (`crm_revenue`/`diamond_revenue`, verified-only), kpi_metrics (AOV/boxes), ConsentGate, segments (CTR-009/010) + segment_reader, learning review queue — the reuse surface for §5 ✓ |

**Conclusion**: open for **STAGED, measure-only** M6.2J. Build a derived Phase-3 growth measurement over the
existing stores + consumed facts; no new table, no CRM send, no commission, no trigger, no flag flip.

---

## 2. Working mode, conventions & staging model

Reuse the M6.2A–I baseline verbatim (pytest, frozen dataclasses, read-only ports + in-memory staged adapters,
framework-neutral pure functions, mask-on-export, fail-closed everywhere; PII markers assembled at runtime). The
whole **M6.2I** tree (378 tests) is carried forward **byte-identical** into `04-artifacts/impl/M6.2J/`; M6.2J
**adds** a `growth/` measurement package + tests only. The change set (§5) is the diff. **No new migration; no new
config flag; no new contract; no carried-forward file patched** (the growth layer is standalone — the M6.2I
dashboard-wiring lesson). `production_flag=OFF` immutable.

---

## 3. Scope lock (anchored strictly to `00-spec/slices/M6.2J.md`)

**In scope (the doc §9 growth machine, measure-only):**
1. **CRM repeat/reorder chain** — `CRM_REORDER_SENT` → `CRM_REORDER_ORDER_CREATED` → `ORDER_VERIFIED`; **CRM
   Revenue** verified-only AND gated on CRM-eligibility + suppression-pass + consent-valid (RULE-002); Repeat rate;
   AOV. A click/chat is never revenue (RULE-003).
2. **Dormant / reactivation** — dormant segments with **consent + CRM-eligibility** (reuse segment_reader +
   ConsentGate); Reactivation rate, CPA reactivation. Measure-only (no CRM send). Opt-out/ineligible ⇒ excluded.
3. **Diamond referral attribution** — `DIAMOND_LEAD_CREATED`, `referral_link_id`, `DIAMOND_REFERRAL_ORDER_VERIFIED`;
   Diamond lead rate, **Diamond Revenue** verified-only, **commission-ready revenue** (verified revenue that is
   commission-**eligible**, CONSUMED) — **commission is MEASURED-not-computed** (RULE-019; Finance owns).
4. **Value optimization signals** — AOV, CLV proxy, boxes/order, ads-ratio-reduction (from valid signals);
   **Learning-Engine growth KPIs** (doc §9 valid signals = *verified business signals + data quality pass*):
   **Candidate approval rate** from the M6.2H review queue (review_state), **uplift** from verified business signals
   (verified-revenue outcomes in the measurement store / DataMart), **drift violations** from the Data Quality Gate
   (`quality/`). Measure-only; candidate PUBLISH stays the M6.2H guarded path (owner approval), not built here.
5. **The doc §9 growth KPIs** (MONITORING_REGISTER Phase-3 table, verbatim) — each computed ONLY from its listed
   valid signals; verified-only revenue (RULE-003); fail-closed; no numeric alert threshold (M6-OD-002 OPEN).

**Out of scope (explicit — other-owner / deferred):**
- **Sending CRM** (CRM Messaging owns) — no CRM send / audience enqueue; `external_send=OFF`. The audience outbox
  (M6.2C/D) already owns send; M6.2J measures.
- **Member-rights decisions** (CRM/Member owns) — no eligibility/suppression DECISION; M6 reads the CONSUMED flags.
- **Final commission / payout** (Finance owns, RULE-019) — no commission amount/rate/payout computed.
- **Data Mart as a trigger owner** (RULE-012 / FAIL-005) — the Data Mart stays a read-only support view.
- **Core/CRM/Diamond override** (FAIL-004), pricing (M3), order-state (M8), consult content (M4), public reply
  (M5), live-ops (M7), scale/auto-publish. No new API/table/flag.

---

## 4. Locked doc content (build to the exact spec)

### 4.1 The doc §9 growth KPI table (VERBATIM, MONITORING_REGISTER Phase-3 / extract L173–177)

| # | Nhóm tăng trưởng | Signal hợp lệ (valid signals — the ONLY inputs) | KPI |
|---|---|---|---|
| 1 | **Repeat / Reorder** | CRM_REORDER_SENT, CRM_REORDER_ORDER_CREATED, ORDER_VERIFIED | Repeat rate, CRM Revenue, AOV |
| 2 | **Dormant / Reactivation** | Dormant segment, consent pass, CRM eligibility pass, order verified | Reactivation rate, CPA reactivation |
| 3 | **Diamond** | DIAMOND_LEAD_CREATED, referral_link_id, DIAMOND_REFERRAL_ORDER_VERIFIED | Diamond lead rate, Diamond Revenue, commission-ready revenue |
| 4 | **Value Optimization** | High-value order, boxes/order, tier upgrade, product affinity | AOV, CLV proxy, boxes/order, ads ratio reduction |
| 5 | **Learning Engine** | Verified business signals + data quality pass | Candidate approval rate, uplift, drift violations |

### 4.2 Locked doc §9 principles (extract L161–169)

- *Diamond referral phải gắn link hợp lệ, buyer identity, order verified và commission eligibility từ Core/Finance;
  Module 6 chỉ đo nguồn và hiệu quả.* → referral attribution + verified revenue measured; **commission NOT
  computed** (RULE-019).
- *CRM revenue phải xuất phát từ CRM eligibility, suppression pass và order verified; không dùng click/chat làm
  revenue.* → CRM revenue = verified-only, eligibility + suppression + consent gated (RULE-002).
- *Value optimization được phép tạo recommendation/candidate; việc publish phải qua review queue và owner
  approval.* → value-opt SIGNALS measured here; PUBLISH stays the M6.2H guarded path (not built here).
- *Data Mart chỉ là support view … không được lạm quyền thành trigger owner …* → RULE-012 / FAIL-005 (SMK-010).

Event codes (`CRM_REORDER_SENT`, `CRM_REORDER_ORDER_CREATED`, `DIAMOND_LEAD_CREATED`,
`DIAMOND_REFERRAL_ORDER_VERIFIED`) are doc §10 canon — referenced as measurement-time constants (registry-validated
upstream, RULE-001), **invented none**, added to no client allow-list.

---

## 5. Minimal change set (all target-relative, staged under `04-artifacts/impl/M6.2J/`)

Legend: **Leg** = M6.2J exit-gate leg — **L1** = *CRM revenue verified* (eligibility + suppression + ORDER_VERIFIED;
click/chat never revenue); **L2** = *Diamond revenue verified* (referral attribution + ORDER_VERIFIED; commission
measured-not-computed). Rollback: new files → delete (no carried-forward file is patched).

### 5.1 New — the `growth/` measurement package (derived, read-only, standalone)

| # | Target file (new) | Purpose | Contract/Rule | Leg | Smoke |
|---|---|---|---|---|---|
| C1 | `app/measurement/growth/__init__.py` | package marker (measure-only; no new table RULE-018; no send/commission/trigger). | — | — | — |
| C2 | `app/measurement/growth/signals.py` | `GrowthGroup` enum (Repeat/Reactivation/Diamond/ValueOpt/Learning) + the VERBATIM doc §9 valid-signal set per group + the CRM/Diamond event-code constants (doc §10 canon, none invented). | RULE-001/018 | L1/L2 | — |
| C3 | `app/measurement/growth/models.py` | frozen `GrowthKpi{name, formula, value, numerator, denominator, group}` + `GrowthReport`; `to_public()` masks PII (member_key/subject/psid, RULE-014/H02); only verified revenue present (RULE-003); no write/trigger field (RULE-012). | CTR-001/002 | L1/L2 | — |
| C4 | `app/measurement/growth/crm.py` | `CrmReorderMeasurement`: the repeat/reorder chain + **CRM Revenue verified-only, built GATED here** — iterates `DataMart.verified_rows()` (the verified-revenue choke) and sums revenue over CRM-attributed (entry_channel=CRM) ORDER_VERIFIED rows ONLY where CONSUMED CRM-eligibility + suppression + consent all pass (RULE-002, fail-closed); Repeat rate. **Does NOT reuse the ungated `DataMart.crm_revenue()`** (that aggregate has no consent/eligibility gate). A click/chat / CRM_REORDER_SENT is never revenue (RULE-003). No CRM send surface. | CTR-002; **RULE-002/003** | **L1** | **SMK-008** |
| C5 | `app/measurement/growth/diamond.py` | `DiamondReferralMeasurement`: records referral attribution (`referral_link_id` + buyer identity + `DIAMOND_REFERRAL_ORDER_VERIFIED`); Diamond lead rate; **Diamond Revenue verified-only**; **commission-ready revenue** = verified revenue that is commission-**eligible** (CONSUMED flag). **NO commission amount/rate/payout method** (RULE-019; Finance owns). | CTR-002; **RULE-019** | **L2** | **SMK-014** |
| C6 | `app/measurement/growth/reactivation.py` | `ReactivationMeasurement`: dormant-segment reactivation gated on **consent + CRM-eligibility** (reuse `segment_reader` + `ConsentGate`, fail-closed — opt-out/ineligible excluded); Reactivation rate, CPA reactivation. Measure-only; no CRM send. | CTR-009/010; **RULE-002** | L1 | SMK-008 |
| C7 | `app/measurement/growth/growth.py` | `GrowthReportBuilder`: the top assembler — computes the doc §9 growth KPIs for all 5 groups, each from its listed valid signals. Sources: **CRM Revenue + Repeat rate from `crm` (C4, gated)**, **Diamond Revenue + commission-ready + lead rate from `diamond` (C5)**, **Reactivation rate + CPA from `reactivation` (C6)**; **AOV + boxes** reused from `DataMart` (support view, RULE-012); Diamond Revenue may also reuse the (verified-only, ungated-consent-OK) `DataMart.diamond_revenue()`. Learning-Engine KPIs (doc §9 valid signals = verified business signals + DQ pass): **approval rate** from the M6.2H review queue (review_state), **uplift** from verified business signals (measurement store / DataMart verified outcomes), **drift violations** from the Data Quality Gate (`quality/`). Value-opt KPIs (CLV proxy, ads-ratio-reduction) from valid signals. Read-only; NO trigger/send/commission method. | CTR-001/002; **RULE-012** | **L1/L2** | **SMK-010** |

### 5.2 Migrations & config

**None.** No new table (doc §13 defines no growth/repeat/reactivation/Diamond table — inventing one breaches
RULE-018; the projection reads the existing `ads_measurement_events` mig 0002 + `ads_attribution_context` mig 0006
+ `customer_segments` mig … via the consumed reader). No new config flag (measure-only; posture flags already fence
send/scale/publish). Both omissions are deliberate minimal-change calls.

---

## 6. Test plan → done-gate / smoke mapping (`pytest -q`; TESTER authors + executes the official smokes)

Fixtures extend `conftest.py` with a `GrowthReportBuilder`, `CrmReorderMeasurement`, `DiamondReferralMeasurement`,
`ReactivationMeasurement`, and consumed CRM-eligibility / suppression / commission-eligibility / dormant-segment
builders (reusing the M6.2E `make_verified_row` + segment_reader + consent fixtures). Carried-forward M6.2I tests
stay green. PII markers assembled at runtime.

| # | Target test (new) | Proves | Leg | Smoke | Fail-gate |
|---|---|---|---|---|---|
| T1 | `tests/test_crm_reorder_revenue_verified_only.py` | **L1**: CRM Revenue counts ONLY verified revenue on CRM-attributed ORDER_VERIFIED rows with eligibility + suppression + consent all pass; a CRM_REORDER_SENT / click / chat contributes 0 (RULE-002/003). | **L1** | — | FAIL-001/002 (guard) |
| T2 | `tests/test_crm_optout_excluded.py` | **SMK-008**: a CRM subject with opt-out (or missing/expired) consent, or a failed suppression, is EXCLUDED from CRM revenue + reactivation; no CRM send surface exists (fail-closed, RULE-002). | L1 | **SMK-008** | **FAIL-002** |
| T3 | `tests/test_diamond_referral_no_commission.py` | **L2 / SMK-014**: a Diamond referral ORDER_VERIFIED carries referral attribution (referral_link_id + buyer identity); Diamond Revenue + commission-ready revenue are MEASURED (verified-only); NO commission amount/rate/payout method exists (RULE-019). | **L2** | **SMK-014** | — |
| T4 | `tests/test_reactivation_consent_eligibility_failclosed.py` | dormant reactivation counts only consent-valid + CRM-eligible members; opt-out/ineligible/absent ⇒ excluded (fail-closed, RULE-002). | L1 | SMK-008 | FAIL-002 |
| T5 | `tests/test_growth_kpis_from_valid_signals_only.py` | the doc §9 growth KPIs (Repeat/Reactivation/Diamond/ValueOpt/Learning) each compute ONLY from their listed valid signals; fail-closed (0/None denominator → None); verified-only revenue. | L1/L2 | — | FAIL-001 (guard) |
| T6 | `tests/test_data_mart_stays_support_view.py` | **SMK-010**: the growth layer READS the Data Mart but never turns it into a trigger; the Data Mart + growth layer expose no CRM/pricing/Diamond/scale trigger (RULE-012/FAIL-005). | L1/L2 | **SMK-010** | **FAIL-005** |
| T7 | `tests/test_growth_measure_only_boundary.py` | the growth modules expose NO send / CRM-send / commission / member-rights / scale / publish / order-state / trigger verb; read-only data (RULE-012/019; FAIL-002/004/005; module boundary). | L1/L2 | SMK-008/010/014 | FAIL-002/004/005 |

**Smoke → test binding**: SMK-008 = T2 (+T4); SMK-010 = T6; SMK-014 = T3. **Execution + official smoke authoring is
the TESTER's** (M6-P1903 build / M6-P1904 run → `04-artifacts/test-reports/M6.2J/`). No self-run (RULE-015).

---

## 7. Master traceability matrix

| Item | Files | Contract | Rule(s) | Leg | Smoke | Fail-gate | Rollback |
|---|---|---|---|---|---|---|---|
| Growth signals / groups (doc §9) | C2 | — | RULE-001/018 | L1/L2 | — | — | delete |
| Growth result models | C3 | CTR-001/002 | RULE-003/014 | L1/L2 | — | — | delete |
| CRM reorder revenue (verified-only) | C4 | CTR-002 | **RULE-002/003** | **L1** | SMK-008 | FAIL-001/002 | delete |
| Diamond referral (no commission) | C5 | CTR-002 | **RULE-019** | **L2** | SMK-014 | — | delete |
| Reactivation (consent + eligibility) | C6 | CTR-009/010 | **RULE-002** | L1 | SMK-008 | FAIL-002 | delete |
| Growth KPI assembler (Data Mart support view) | C7 | CTR-001/002 | **RULE-012** | **L1/L2** | SMK-010 | FAIL-005 | delete |
| Tests | T1–T7 | — | — | L1/L2 | SMK-008/010/014 | FAIL-002/004/005 | delete |

**Legs**: L1 (CRM revenue verified — T1/T2/T4) ✓; L2 (Diamond revenue verified, commission measured-not-computed —
T3) ✓; SMK-008 (T2/T4) ✓; SMK-010 (T6) ✓; SMK-014 (T3) ✓; growth-KPI coverage (T5) ✓; measure-only boundary (T7) ✓.
TESTER executes the official smokes (M6-P1903/1904); evidence (M6-P1907), docs (M6-P1908), judge (M6-P1909) are
downstream process legs.

---

## 8. Rollback strategy (global)

1. **Nothing live / nothing sends / no commission / no trigger.** Staged under `04-artifacts/impl/M6.2J/`; no
   migration (none added), no external/CRM call, no flag written. Baseline rollback = delete the M6.2J tree
   (M6.2I untouched).
2. **Per-item** (§5): new `growth/` files → delete; **no carried-forward file is patched** (the growth layer is
   standalone — no dashboard/deps edit, avoiding the M6.2I plan-delta).
3. **The projection is derived + read-only** — it writes nothing to the stores; removing it leaves
   `ads_measurement_events` / `ads_attribution_context` / the consumed segments exactly as M6.2I left them.

---

## 9. Plan-deltas & notes

- **No new table / migration / CTR / config flag (RULE-018)** — the primary architecture call. Doc §13 defines no
  growth object; M6.2J is a derived projection over CTR-001/002 + the Data Mart + consumed segments/consent.
- **CRM revenue verified-only + fail-closed (RULE-002/003, exit-leg 1)** — CRM Revenue reuses the DataMart's
  single verified-revenue choke **via `verified_rows()`** (NOT the ungated `crm_revenue()` aggregate), further gated
  in C4 on CONSUMED CRM-eligibility + suppression + consent (all pass, else
  excluded). A click/chat / CRM_REORDER_SENT is never revenue. Opt-out excluded (SMK-008). T1/T2/T4.
- **Diamond commission MEASURED-not-computed (RULE-019, exit-leg 2)** — the Diamond layer records referral
  attribution + verified revenue + commission-**eligible** revenue (consumed flag); it exposes NO commission
  amount/rate/payout method. Finance owns. SMK-014. T3.
- **Data Mart stays a support view (RULE-012/FAIL-005)** — the growth assembler READS the Data Mart; neither the
  Data Mart nor the growth layer exposes a CRM/pricing/Diamond/scale trigger. SMK-010. T6.
- **Reuse, not duplicate** — the DataMart verified-revenue choke (`verified_rows()`) + `diamond_revenue()` + AOV +
  boxes reuse `DataMart`; consent reuses `ConsentGate`; dormant segments reuse `segment_reader` (CTR-009/010);
  Learning-Engine **approval rate** reads the M6.2H review queue, **uplift** reads verified business signals, **drift
  violations** read the Data Quality Gate (`quality/`). The new contribution is the doc §9 growth-specific KPIs
  (Repeat/Reactivation/Diamond-lead/commission-ready/CLV/uplift/drift/…).
- **Standalone (M6.2I lesson)** — the growth layer is NOT wired into the dashboard (`DashboardDeps`), avoiding the
  TESTER-owned-smoke conflict that forced the M6.2I plan-delta; dashboard surfacing belongs to the M6-OD-011
  integration step.
- **Module boundary intact** — no CRM send (M6.2C/D outbox owns send; CRM Messaging owns CRM), no member-rights
  decision, no commission (Finance), no Core/CRM/Diamond override (FAIL-004), no pricing (M3), no order-state (M8),
  no consult content (M4), no scale/publish.
- **Governance unchanged** — `M6-P1000` + `M6-P1309` verdicts stay BLOCKED (not converted); the
  M6.2G/M6.2H/M6.2I before-real-scale/send/auto-publish/surfacing forward conditions remain in force; no flag
  flipped. Numeric alert thresholds NOT applied (M6-OD-002 OPEN).
- **Ultracode note** — this plan was reviewed by an independent adversarial design red-team (§ below) driving the
  claims against the real M6.2I tree before finalizing.

---

## 10. Acceptance self-map

1. *Every item → leg or smoke* → §5–§7. ✓  2. *Rollback per item* → §5/§8. ✓  3. *No scope beyond the slice* →
§3 (CRM-send/member-rights/commission/Data-Mart-trigger/Core-override deferred or other-owner; measure-only). ✓
4. *Target LOCKED + M6-OD-011 decided* → §1. ✓  5. *Reuse conventions / test patterns from the locked target* →
§2/§4 (M6.2I baseline; DataMart/ConsentGate/segment_reader/review-queue reuse). ✓  Plus the **load-bearing
invariants**: no invented schema (RULE-018), CRM revenue verified-only + consent fail-closed (RULE-002/003/FAIL-002,
SMK-008), Diamond commission measured-not-computed (RULE-019, SMK-014), Data Mart support-view only
(RULE-012/FAIL-005, SMK-010) — each with a test and the M6.2I suite staying green.

*Plan-only: no code, no migration, no CRM send, no commission computed, no trigger, no flag flipped;
`global_gateway_state=BLOCKED`, `production_flag=OFF`.*
