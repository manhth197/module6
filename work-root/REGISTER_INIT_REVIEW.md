# REGISTER_INIT_REVIEW — Module 6 register snapshot (seeds later gates)

**Prompt**: M6-P0009 (REGISTER_INIT_REVIEW) · Role: PM_ORCHESTRATOR · Mode: analysis_only
**Recorded**: 2026-07-20 · Read-only. All 11 files in `00-spec/registers/` read.
Row counts grep-verified where an `M6-XXX-` row ID exists.

## 1. Row counts per register

| Register | Rows | Composition |
|---|---:|---|
| SOURCE_MANIFEST.md | 12 | 12 field rows (+ 4-item read policy) |
| RULES_LOCKED.md | 24 | 21 owner `M6-RULE-001..021` + 3 hardening `H01..H03` (all LOCKED) |
| FAIL_GATE_REGISTER.md | 10 | 7 owner `M6-FAIL-001..007` + 3 hardening `008..010` |
| SMOKE_REGISTER.md | 18 | 15 owner `M6-SMK-001..015` + 3 proposed `016..018` |
| CONTRACT_REGISTER.md | 26 | `M6-CTR-001..026` |
| DECISION_REGISTER.md | 12 | 7 owner `M6-OD-001..007` + 5 discovered `008..012` |
| CONFLICT_MATRIX.md | 7 | `M6-CONF-001..007` |
| ENTRY_EVIDENCE_REGISTER.md | 4 | `M6-ENTRY-001..004` (+ 7 consumed-boundary reference rows) |
| LEXICON_REGISTER.md | 6 | `M6-LEX-001..006` (+ 1 MISSING banned-word row) |
| MONITORING_REGISTER.md | 27 | 14 KPI (doc §14) + 5 growth KPI (doc §9) + 8 data-quality-gate items (doc §15) |
| SCHEMA_CHANGELOG.md | 8 | entries #1..#8 |

## 2. OPEN decisions — `M6-OD-*` (12 of 12 OPEN)

| ID | Decision (short) | Blocks |
|---|---|---|
| M6-OD-001 | Official Phase-1 Hero SKU list | M6.2A pilot config; PR/PILOT |
| M6-OD-002 | Official CPA/ROAS/AOV/Verified-Rate thresholds per stage | M6-CTR-015 thresholds, M6-CTR-026, M6.2G exit |
| M6-OD-003 | Hash policy + fields allowed to Pixel/CAPI/Offline (privacy/legal) | M6.2D exit, M6-SMK-017 |
| M6-OD-004 | Google/Meta connector used first in pilot | M6.2D scope, PR/PILOT |
| M6-OD-005 | Official attribution model (first/last/weighted/cohort) | M6.2E design, M6.2G scale evidence |
| M6-OD-006 | Safe range for guarded auto-publish | M6.2H publish leg, M6-SMK-011 |
| M6-OD-007 | Persona/keyword/hook from Content Block 20-SKU locked? | M6.2H seed content (framework may proceed) |
| M6-OD-008 | PAYMENT_COMPLETED as revenue-adjacent signal? | M6.2E/F edge handling |
| M6-OD-009 | GOLDEN_HOUR_START/REMINDER enabled for pilot + config owner | M6.2I event set |
| M6-OD-010 | Slice execution model (sequential vs parallel) | prompt DAG shape — pack proceeds SEQUENTIAL default |
| M6-OD-011 | Target repository / stack for implementation slices | slice implement legs — pack proceeds `04-artifacts/impl/` staging |
| M6-OD-012 | Evidence masking format for the pack | evidence format — pack proceeds `abc***xy` + `secret_ref` |

Note: OD-010/011/012 are annotated "pack proceeds with recommendation/default" but their **Status is still OPEN** (owner ratification pending).

## 3. OPEN conflicts — `M6-CONF-*` (5 OPEN of 7)

| ID | Tension (short) | Status |
|---|---|---|
| M6-CONF-001 | `ads_measurement_event` (singular) vs `ads_measurement_events` (plural) | OPEN (low risk; pack proceeds) |
| M6-CONF-002 | PAYMENT_COMPLETED conditional revenue, Core policy absent | OPEN → M6-OD-008 |
| M6-CONF-003 | "Retargeting Engine cơ bản" (Phase 1) vs retargeting measurement scoped to M6.2I | OPEN (pack proceeds) |
| M6-CONF-004 | GOLDEN_HOUR events "Tùy cấu hình", no config owner | OPEN → M6-OD-009 |
| M6-CONF-007 | Scale-condition "P6 evidence" self-references Module 6 | OPEN (pack proceeds) |

Resolved (not OPEN): M6-CONF-005 (doc-nature vs slices) and M6-CONF-006 ("24/7" vs "24-7" spelling) = **RESOLVED-BY-READING**.

## 4. MISSING contracts — `M6-CTR-*` (22 MISSING of 26)

All 22 are `MISSING / OWNER_DECISION_REQUIRED`; each names a producing CONTRACT_HARMONIZATION prompt and the slice it gates:

| ID | Object | Producing prompt | Needed before |
|---|---|---|---|
| M6-CTR-003 | event_registry (consumed) | M6-P0701 | M6.2A |
| M6-CTR-004 | web_event_logs | M6-P0703 | M6.2A |
| M6-CTR-005 | guest_contacts (consumed) | M6-P0702 | M6.2A |
| M6-CTR-006 | guest_marketing_consent_snapshot (consumed) | M6-P0702 | M6.2A |
| M6-CTR-007 | conversion_events | M6-P0704 | M6.2C |
| M6-CTR-008 | marketing_measurement_outbox | M6-P0705 | M6.2C |
| M6-CTR-009 | customer_segments (consumed) | M6-P0706 | M6.2C |
| M6-CTR-010 | customer_segment_members (consumed) | M6-P0706 | M6.2C |
| M6-CTR-011 | marketing_audience_outbox | M6-P0706 | M6.2C |
| M6-CTR-012 | ads_data_quality_check | M6-P0708 | M6.2F |
| M6-CTR-013 | ads_scale_request | M6-P0709 | M6.2G |
| M6-CTR-014 | ads_learning_candidate | M6-P0710 | M6.2H |
| M6-CTR-016 | POST /api/ads/events/track | M6-P0711 | M6.2B |
| M6-CTR-017 | POST /api/ads/conversions | M6-P0711 | M6.2C |
| M6-CTR-018 | GET /api/admin/ads/dashboard | M6-P0712 | M6.2F |
| M6-CTR-019 | POST /api/admin/ads/scale-requests | M6-P0712 | M6.2G |
| M6-CTR-020 | POST /api/admin/ads/learning-candidates | M6-P0712 | M6.2H |
| M6-CTR-021 | worker: marketing_measurement_dispatcher | M6-P0713 | M6.2C |
| M6-CTR-022 | worker: marketing_audience_dispatcher | M6-P0713 | M6.2C |
| M6-CTR-023 | worker: attribution_materializer | M6-P0713 | M6.2E |
| M6-CTR-024 | worker: data_quality_checker | M6-P0713 | M6.2F |
| M6-CTR-026 | Scale Gate approval flow (thresholds = M6-OD-002) | M6-P0709 | M6.2G |

DRAFT_LOCKED (not MISSING): M6-CTR-001, M6-CTR-002, M6-CTR-015 (formulas locked; thresholds OPEN via M6-OD-002), M6-CTR-025 (content-level).

## 5. OPEN entry evidence — `M6-ENTRY-*` (4 of 4 OPEN)

| ID | Required evidence | Supplied by | Checked at |
|---|---|---|---|
| M6-ENTRY-001 | P3 Verified Revenue boundary (ORDER_VERIFIED, Payment/COD/Order Verified, QuoteSnapshot correctness) | Module 3 / Commerce | BOOTSTRAP readiness + M6.2A entry + Scale Gate |
| M6-ENTRY-002 | P5 channel identity (page/live/comment/messenger + handoff/delivery logs) | Module 5 / Gateway | BOOTSTRAP readiness + M6.2A entry + M6.2I entry + Scale Gate |
| M6-ENTRY-003 | P6 event identity (Core event_registry with owner/channel/sensitivity/send policy) | Core Event Governance | M6.2A entry + Scale Gate |
| M6-ENTRY-004 | Public/privacy conduct (no final price public, no PII leak, no spam) | Module 4 + Module 5 | Scale Gate + PR/PILOT |

## 6. Cross-referenced MISSING/OPEN outside the 4 target registers

- **MONITORING_REGISTER**: all numeric alert thresholds = `MISSING / OWNER_DECISION_REQUIRED` → delegates to **M6-OD-002** (no new ID).
- **LEXICON_REGISTER**: "Banned words / claim blacklist per SKU" = `MISSING / OWNER_DECISION_REQUIRED` → linked to **M6-OD-007**.

Both resolve to decisions already listed in §2; recorded for completeness so later gates see the full downstream of OD-002 and OD-007.

## 7. Method

Read all 11 registers. Row counts for ID-bearing registers grep-verified
(`^\| M6-XXX-`): OD=12, CONF=7, CTR=26, CTR-MISSING=22, ENTRY=4, RULE=24,
FAIL=10, SMK=18, LEX=6 — all match the hand counts. MONITORING/SCHEMA_CHANGELOG/
SOURCE_MANIFEST counted by reading (no uniform row ID). No state touched.
