# CONTRACT_REGISTER — Module 6

One row per canonical output/consumed contract. HONEST statuses only:

- `DRAFT_LOCKED` — a field-level schema exists in the owner document and is
  reproduced in `00-spec/SPEC.md`.
- `MISSING / OWNER_DECISION_REQUIRED` — the document names the object but gives
  no field-level schema. A CONTRACT_HARMONIZATION prompt (listed in the last
  column) MUST produce the schema before the slice in "Needed before" may pass
  its entry gate. Nothing gates a slice on a contract no prompt produces.

Ownership: `M6` = Module 6 owns and writes; `CONSUMED` = owned elsewhere
(Core/Commerce/CRM/Identity), Module 6 defines only the consumed shape.

| Contract ID | Object / contract | Owner | Status | Fields in doc? | Needed before | Producing prompt | Source |
|---|---|---|---|---|---|---|---|
| M6-CTR-001 | ads_measurement_event (row contract of storage table `ads_measurement_events`) | M6 | DRAFT_LOCKED | YES — 20 fields, doc §10 | M6.2B | locked in SPEC §10.1 (storage binding: M6-P0707) | extract lines 191–211, 273 |
| M6-CTR-002 | ads_attribution_context | M6 | DRAFT_LOCKED | YES — 19 fields, doc §11 | M6.2E | locked in SPEC §10.2 | extract lines 215–234, 272 |
| M6-CTR-003 | event_registry (consumed shape) | CONSUMED (Core Event Governance) | DRAFT_LOCKED | no | M6.2A | M6-P0701 | extract line 263 |
| M6-CTR-004 | web_event_logs | M6 | DRAFT_LOCKED | partial (page, session, source, consent snapshot, event_ts, idempotency — line 117) | M6.2A | M6-P0703 | extract lines 117, 264 |
| M6-CTR-005 | guest_contacts (consumed shape) | CONSUMED (Customer identity) | DRAFT_LOCKED | no | M6.2A | M6-P0702 | extract line 265 |
| M6-CTR-006 | guest_marketing_consent_snapshot (consumed shape) | CONSUMED (Consent) | DRAFT_LOCKED | no | M6.2A | M6-P0702 | extract line 266 |
| M6-CTR-007 | conversion_events | M6/Core | MISSING / OWNER_DECISION_REQUIRED | no | M6.2C | M6-P0704 | extract lines 119, 267 |
| M6-CTR-008 | marketing_measurement_outbox | M6 (worker only) | MISSING / OWNER_DECISION_REQUIRED | partial (error_log, next_retry_at — line 252) | M6.2C | M6-P0705 | extract lines 252, 268 |
| M6-CTR-009 | customer_segments (consumed shape) | CONSUMED (CRM/Ads segmentation) | MISSING / OWNER_DECISION_REQUIRED | no | M6.2C | M6-P0706 | extract line 269 |
| M6-CTR-010 | customer_segment_members (consumed shape; doc note: "Không lạm dụng làm trigger owner") | CONSUMED | MISSING / OWNER_DECISION_REQUIRED | no | M6.2C | M6-P0706 | extract line 270 |
| M6-CTR-011 | marketing_audience_outbox | M6 (worker only) | MISSING / OWNER_DECISION_REQUIRED | no | M6.2C | M6-P0706 | extract line 271 |
| M6-CTR-012 | ads_data_quality_check | M6 | MISSING / OWNER_DECISION_REQUIRED | no (gate items exist, doc §15) | M6.2F | M6-P0708 | extract lines 274, 299–308 |
| M6-CTR-013 | ads_scale_request | M6 | MISSING / OWNER_DECISION_REQUIRED | no (conditions exist, doc §16) | M6.2G | M6-P0709 | extract lines 275, 315–324 |
| M6-CTR-014 | ads_learning_candidate | M6 | MISSING / OWNER_DECISION_REQUIRED | no (lifecycle exists, doc §17) | M6.2H | M6-P0710 | extract lines 276, 347–353 |
| M6-CTR-015 | Dashboard KPI contract | M6 | DRAFT_LOCKED (formulas) — thresholds OPEN via M6-OD-002 | YES — 14 metrics with formula/source, doc §14 | M6.2F | locked verbatim in registers/MONITORING_REGISTER.md (doc §14); thresholds bound by M6-P0714 | extract lines 280–295, 479 |
| M6-CTR-016 | POST /api/ads/events/track | M6 | MISSING / OWNER_DECISION_REQUIRED | no | M6.2B | M6-P0711 | extract line 371 |
| M6-CTR-017 | POST /api/ads/conversions | M6 | MISSING / OWNER_DECISION_REQUIRED | no | M6.2C | M6-P0711 | extract line 372 |
| M6-CTR-018 | GET /api/admin/ads/dashboard | M6 | MISSING / OWNER_DECISION_REQUIRED | no | M6.2F | M6-P0712 | extract line 373 |
| M6-CTR-019 | POST /api/admin/ads/scale-requests | M6 | MISSING / OWNER_DECISION_REQUIRED | no | M6.2G | M6-P0712 | extract line 374 |
| M6-CTR-020 | POST /api/admin/ads/learning-candidates | M6 | MISSING / OWNER_DECISION_REQUIRED | no | M6.2H | M6-P0712 | extract line 375 |
| M6-CTR-021 | worker: marketing_measurement_dispatcher | M6 | MISSING / OWNER_DECISION_REQUIRED | duty only (retry, dedup, error log) | M6.2C | M6-P0713 | extract line 376 |
| M6-CTR-022 | worker: marketing_audience_dispatcher | M6 | MISSING / OWNER_DECISION_REQUIRED | duty only (consent fail-closed) | M6.2C | M6-P0713 | extract line 377 |
| M6-CTR-023 | worker: attribution_materializer | M6 | MISSING / OWNER_DECISION_REQUIRED | duty only (no verified-revenue overwrite) | M6.2E | M6-P0713 | extract line 378 |
| M6-CTR-024 | worker: data_quality_checker | M6 | MISSING / OWNER_DECISION_REQUIRED | duty only (PASS/HOLD/FAIL output) | M6.2F | M6-P0713 | extract line 379 |
| M6-CTR-025 | Evidence package (owner review pack) | M6 | DRAFT_LOCKED (content-level, doc §22) — file format defined by pack (HARDENING) | content list YES | M6.2K | SPEC §19 (doc §22 table verbatim) + M6-P0714 | extract lines 419–430 |
| M6-CTR-026 | Scale Gate approval flow (request -> owner approve/reject -> budget cap -> rollback condition) | M6 + Owner | MISSING / OWNER_DECISION_REQUIRED (thresholds = M6-OD-002) | conditions YES, flow fields no | M6.2G | M6-P0709 | extract lines 312–324 |

## Invariants

1. Every `MISSING` row names a producing CONTRACT_HARMONIZATION prompt; the
   registry validator fails if a slice's entry gate references a contract whose
   producing prompt is not upstream in the DAG.
2. A row may move `MISSING -> DRAFT_LOCKED` only via its producing prompt's
   evidence + judge sign-off, with a `SCHEMA_CHANGELOG.md` row.
3. No row may ever be created directly as `DRAFT_LOCKED` without a field-level
   schema existing (in the doc or in an approved harmonization output).
