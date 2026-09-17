-- Migration 0002 — create ads_measurement_events (M6-CTR-001, M6-OWNED, normalized measurement store)
-- STAGED per 04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json (live_migrations=false): NEVER applied to any
-- live database by this slice. Engine-neutral DDL; the concrete engine, partition strategy, index
-- implementation, and embedded-object-vs-FK for attribution_context bind at the M6-OD-011 integration step.
--
-- The 20 DRAFT_LOCKED doc fields (SPEC 10.1) are reproduced verbatim (name/type/optionality); the single
-- physical addition is ingested_at (changelog row 18). currency is the locked constant VND; data_quality_status
-- is the verbatim enum PASS|HOLD|FAIL. Rules: RULE-005 (idempotency_key UNIQUE = dedup, SMK-003), RULE-003
-- (revenue only from ORDER_VERIFIED), RULE-007/008 (immutability zones). Applies AFTER 0001.

-- ============================================================ UP
CREATE TABLE ads_measurement_events (
    -- Zone A: event identity / consent / trace / locked constant — WRITE-ONCE after INSERT
    event_id            TEXT        NOT NULL PRIMARY KEY,   -- stable event identity (doc field)
    event_code          TEXT        NOT NULL,               -- ACTIVE in event_registry (RULE-001, gated upstream)
    event_ts            TIMESTAMP   NOT NULL,               -- business event time (source-supplied)
    customer_id         TEXT        NULL,                   -- PII (masked in logs/evidence, RULE-014)
    guest_id            TEXT        NULL,                   -- PII
    page_id             TEXT        NULL,
    live_session_id     TEXT        NULL,
    campaign_id         TEXT        NULL,
    adset_id            TEXT        NULL,
    ad_id               TEXT        NULL,
    sales_session_id    TEXT        NULL,
    quote_snapshot_id   TEXT        NULL,                   -- REFERENCE to M3 QuoteSnapshot (M6 never writes it)
    currency            TEXT        NOT NULL DEFAULT 'VND',  -- locked constant VND (fixed at INSERT)
    consent_snapshot_id TEXT        NULL,                   -- REFERENCE to M6-CTR-006 (consent fail-closed)
    idempotency_key     TEXT        NOT NULL,               -- locked RULE-005 formula
    correlation_id      TEXT        NOT NULL,               -- trace id for evidence linkage (M6-CTR-025)
    ingested_at         TIMESTAMP   NOT NULL,               -- PACK addition (changelog row 18); != event_ts
    -- Zone B: verified-enrichment — SET-ONCE on the ORDER_VERIFIED path (LATER slices; NULL at M6.2B)
    order_code          TEXT        NULL,                   -- REFERENCE to Commerce/M8 (never order-state write)
    revenue_value       NUMERIC     NULL,                   -- ONLY from ORDER_VERIFIED (RULE-003); NULL in M6.2B
    attribution_context TEXT        NULL,                   -- materialized by attribution_materializer (M6.2E)
    -- Zone C: data quality — audited lifecycle, transitioned ONLY by data_quality_checker (M6.2F)
    data_quality_status TEXT        NOT NULL DEFAULT 'HOLD', -- enum PASS|HOLD|FAIL (initial HOLD, fail-closed)
    CONSTRAINT uq_ads_measurement_events_idempotency_key UNIQUE (idempotency_key), -- dedup, no double count (RULE-005)
    CONSTRAINT ck_ads_measurement_events_currency CHECK (currency = 'VND'),
    CONSTRAINT ck_ads_measurement_events_dq CHECK (data_quality_status IN ('PASS', 'HOLD', 'FAIL')),
    -- RULE-003: revenue only alongside an order_code (verification is Commerce-owned; enforced in app + worker)
    CONSTRAINT ck_ads_measurement_events_revenue CHECK (revenue_value IS NULL OR order_code IS NOT NULL)
);

-- Dashboard/ROAS + audit query paths (over doc fields).
CREATE INDEX ix_ame_event_ts            ON ads_measurement_events (event_ts);
CREATE INDEX ix_ame_event_code          ON ads_measurement_events (event_code);
CREATE INDEX ix_ame_campaign_id         ON ads_measurement_events (campaign_id);
CREATE INDEX ix_ame_adset_id            ON ads_measurement_events (adset_id);
CREATE INDEX ix_ame_ad_id               ON ads_measurement_events (ad_id);
CREATE INDEX ix_ame_page_id             ON ads_measurement_events (page_id);
CREATE INDEX ix_ame_order_code          ON ads_measurement_events (order_code);
CREATE INDEX ix_ame_data_quality_status ON ads_measurement_events (data_quality_status);
CREATE INDEX ix_ame_correlation_id      ON ads_measurement_events (correlation_id);

-- Immutability zones (RULE-007/008), realized at the chosen engine at integration time (NOT executed here):
--   Zone A (event_id..ingested_at): write-once — reject UPDATE of any Zone-A column; no hard DELETE / history
--     rewrite. Identity stitching (guest->customer) is recorded in the identity layer with audit (RULE-006),
--     NEVER by mutating this historical row.
--   Zone B (order_code, revenue_value, attribution_context): set-once by named workers on the ORDER_VERIFIED
--     path; verified revenue is NEVER overwritten; any post-verify correction needs an adjustment record
--     {actor, reason, audit, evidence} (RULE-008) — never a silent in-place edit.
--   Zone C (data_quality_status): PASS|HOLD|FAIL lifecycle set/transitioned ONLY by data_quality_checker
--     (M6-CTR-024); every transition audited; HOLD/FAIL rows are never scale evidence (RULE-009).
-- Illustrative Postgres form for Zone A (NOT executed here):
--   REVOKE DELETE ON ads_measurement_events FROM PUBLIC;
--   CREATE RULE ame_no_delete AS ON DELETE TO ads_measurement_events DO INSTEAD NOTHING;

-- ============================================================ DOWN (rollback)
-- Zone-A rows are write-once; reverting after a real apply requires dropping the table (not row deletes).
-- Staged now => this is documented, not executed.
-- DROP TABLE ads_measurement_events;
