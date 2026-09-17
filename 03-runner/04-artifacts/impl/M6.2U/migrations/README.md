# Migrations (STAGED — never applied)

Per `04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json` (`safety.live_migrations = false`), **no migration in
this folder is applied to any live database** by slices M6.2A–M6.2Q. They are staged DDL, reviewed as evidence; the
owner-controlled integration step (bound to `M6-OD-011`) chooses the engine and applies them.
**Application order: `0001` → `0002` → `0003` → `0004` → `0005` → `0006` → `0007` → `0008` → `0009` → `0010` → `0011`
→ `0012` → `0013` → `0014` → `0015` → `0016`.**

| # | File | Owns | Rules | Rollback |
|---|---|---|---|---|
| 0001 | `0001_create_web_event_logs.sql` | `web_event_logs` (M6-CTR-004, raw append-only ingress log) | RULE-007 append-only, RULE-005 idempotency UNIQUE | Down = `DROP TABLE web_event_logs` (included, commented). Staged ⇒ never applied ⇒ deleting the file fully reverts. |
| 0002 | `0002_create_ads_measurement_events.sql` | `ads_measurement_events` (M6-CTR-001, normalized store for dashboard/ROAS) | RULE-005 idempotency UNIQUE (dedup, SMK-003), RULE-003 revenue-only-ORDER_VERIFIED, RULE-007/008 immutability zones | Down = `DROP TABLE ads_measurement_events` (included, commented). Zone-A is write-once; revert after a real apply is the down-DDL, not row deletes. Staged ⇒ deleting the file fully reverts. |
| 0003 | `0003_create_conversion_events.sql` | `conversion_events` (M6-CTR-007, internal outbox source) | RULE-004 (source→outbox, never direct send), RULE-003 revenue-only-ORDER_VERIFIED, RULE-005 idempotency UNIQUE | Down = `DROP TABLE conversion_events` (commented). Staged ⇒ delete the file fully reverts. |
| 0004 | `0004_create_marketing_measurement_outbox.sql` | `marketing_measurement_outbox` (M6-CTR-008, worker-only queue) | RULE-004 outbox+worker only, RULE-005 dedup_key UNIQUE (one per conversion×platform), bounded retry→dead-letter (doc 12 L252, SMK-016) | Down = `DROP TABLE marketing_measurement_outbox` (commented). Staged ⇒ delete the file fully reverts. |
| 0005 | `0005_create_marketing_audience_outbox.sql` | `marketing_audience_outbox` (M6-CTR-011, worker-only queue) | RULE-004 approved-segments+outbox only, RULE-002 consent fail-closed, RULE-012 not-a-trigger, audience dedup_key UNIQUE | Down = `DROP TABLE marketing_audience_outbox` (commented). Staged ⇒ delete the file fully reverts. |
| 0006 | `0006_create_ads_attribution_context.sql` | `ads_attribution_context` (M6-CTR-002, M6-owned attribution snapshot) | Applies AFTER 0002; standalone snapshot table vs. the materialized copy on `ads_measurement_events.attribution_context` (0002) bound at the M6-OD-011 step | Down = `DROP TABLE ads_attribution_context` (commented). Staged ⇒ delete the file fully reverts. |
| 0007 | `0007_create_ads_data_quality_check.sql` | `ads_data_quality_check` (M6-CTR-012, Data Quality Gate output) | one row per (measurement_event, check run) = the 8 doc §15 gate items + worst-status overall | Down = `DROP TABLE ads_data_quality_check` (commented). Staged ⇒ delete the file fully reverts. |
| 0008 | `0008_create_ads_dashboard_support_view.sql` | `ads_dashboard_kpi_source` (M6-CTR-018/015) as a READ-ONLY SUPPORT VIEW | RULE-012 / FAIL-005 (SMK-010) view-only — never a trigger owner for CRM/pricing/Diamond/scale; RULE-003 / FAIL-001 (SMK-004/005/015) verified-only revenue | Down = `DROP VIEW ads_dashboard_kpi_source` (commented). A view owns no data. Staged ⇒ delete the file fully reverts. |
| 0009 | `0009_create_ads_scale_request.sql` | `ads_scale_request` (M6-CTR-013, INERT scale-request proposal) | RULE-010 / FAIL-006 inert proposal data — 8 doc §16 condition statuses; `budget_cap` / `rollback_condition` are request FIELDS, never actions; no executable scale path | Down = `DROP TABLE ads_scale_request` (commented). Staged ⇒ delete the file fully reverts. |
| 0010 | `0010_create_ads_scale_approval.sql` | `ads_scale_approval` (M6-CTR-026, owner-decision records, append-only) | RULE-015 no synthesized approval (actor + reason + audit_ref + evidence_ref required); RULE-010 / FAIL-006 recording an APPROVE never triggers a scale | Down = `DROP TABLE ads_scale_approval` (commented). Append-only ⇒ revert after a real apply is the down-DDL. Staged ⇒ delete the file fully reverts. |
| 0011 | `0011_create_ads_strategy_libraries.sql` | the six ADS Strategy Libraries + the strategy mapping (M6.2H, doc §17) | RULE-011 / LEX-006 `seed_source NOT NULL` (no fabricated origin strategy); `content` NULL while M6-OD-007 OPEN (framework-only); mapping anchored to a sellable SKU (LEX-005) | Down = `DROP TABLE` the libraries + mapping (commented). Staged ⇒ delete the file fully reverts. |
| 0012 | `0012_create_ads_learning_candidate.sql` | `ads_learning_candidate` (M6-CTR-014, INERT learning-candidate) | RULE-011 / LEX-006 / FAIL-006 inert proposal — no trigger, no auto-publish; a candidate outside the owner-ratified safe range (UNKNOWN while M6-OD-006 OPEN) is HELD (SMK-011) | Down = `DROP TABLE ads_learning_candidate` (commented). Staged ⇒ delete the file fully reverts. |
| 0013 | `0013_psid_to_psid_hash.sql` | ALTERS `ads_attribution_context.psid` → `psid_hash` (B1 / M6-OD-003, M5 PSID-hash policy) | Applies AFTER 0006; a raw PSID is NEVER stored on a durable row — `psid_hash` is a one-way salted hash (mask() is reversible, so it is not used for storage) | Down = reverse the column rename (commented). Staged ⇒ delete the file fully reverts. |
| 0014 | `0014_create_ads_spend_import.sql` | `ads_spend_import` (+ `ads_spend_import_row`) (M6.2Q A5, INERT maker-checker import) | M6-OD-016 phase-1 CSV export from Meta Ads Manager + maker-checker approve; campaign-level rows, a time window, a MAKER, a maker-checker state; NO Marketing API, NO new secret, NO network | Down = `DROP TABLE ads_spend_import_row, ads_spend_import` (commented). Staged ⇒ delete the file fully reverts. |
| 0015 | `0015_create_ads_spend_record.sql` | `ads_spend_record` (M6.2Q A5, MATERIALIZED campaign-level spend) | the set-once destination the materialize worker writes from an APPROVED `ads_spend_import` (0014); campaign-level (adset_id / ad_id NULL — phase-1 source is campaign-level) | Down = `DROP TABLE ads_spend_record` (commented). Staged ⇒ delete the file fully reverts. |
| 0016 | `0016_create_live_session_ads_binding.sql` | `live_session_ads_binding` (M6.2Q A5, live-session-ads-binding.v1) | M6-OD-011 binding: `live_session_id` + `primary_campaign_id` (the join hook the by-session CPA/ROAS reader uses to attribute campaign-level spend 0015 to a live_session); `bound_by` is a governance ref (masked on export) | Down = `DROP TABLE live_session_ads_binding` (commented). Staged ⇒ delete the file fully reverts. |

**Enforcement migration `0017` (renumbered — no SQL file here yet):** the runtime-enforcement migration is **`0017`**,
renumbered from the originally-planned `0014` after `0014`–`0016` were taken by the M6.2Q ads-spend tables above. It
is **authored at server-bind (the M6-OD-011 integration step) — no SQL file is written in this staged folder**. The
registry (`04-artifacts/state/…/M6-OD-011.json`, `DECISION_REGISTER`, `SCHEMA_CHANGELOG` under `00-spec`, all
operator-owned) already reflect the `0017` number; this README is the staged-migrations view of the same fact.

**Not migrated here** (owned + migrated by their own modules; Module 6 only reads them):
`event_registry` (Core Event Governance), `guest_contacts` / `customers*` (Customer identity),
`guest_marketing_consent_snapshot` (Consent system), `customer_segments` / `customer_segment_members`
(CRM/Ads segmentation — M6-CTR-009/010, CONSUMED).

Append-only note: once a real apply happens, `web_event_logs` history is never updated or deleted; reverting
requires the down-DDL (`DROP TABLE`), not row deletion.
