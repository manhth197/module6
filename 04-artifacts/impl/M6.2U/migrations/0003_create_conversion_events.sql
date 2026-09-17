-- Migration 0003 — create conversion_events (M6-CTR-007, M6/Core-owned; internal outbox source)
-- STAGED per 04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json (live_migrations=false): NEVER applied here.
-- Engine-neutral DDL; the concrete engine binds at the M6-OD-011 integration step. Applies AFTER 0002.
--
-- Rules: RULE-004 (source for the measurement outbox; conversion_events NEVER sends externally), RULE-003
-- (revenue only from ORDER_VERIFIED), RULE-005 (idempotency dedup). customer_or_guest_key is PII (masked on
-- export; never raw in logs/evidence, RULE-014/H02).

-- ============================================================ UP
CREATE TABLE conversion_events (
    conversion_id           TEXT        NOT NULL PRIMARY KEY,
    event_code              TEXT        NOT NULL,               -- ACTIVE in event_registry (RULE-001)
    source_event_id         TEXT        NOT NULL,               -- the ads_measurement_event/web_event_log it derives from
    correlation_id          TEXT        NOT NULL,               -- trace linkage (evidence)
    customer_or_guest_key   TEXT        NOT NULL,               -- PII (masked on export; dedup component)
    consent_snapshot_id     TEXT        NOT NULL,               -- consent gate ref (RULE-002)
    occurred_at             TIMESTAMP   NOT NULL,               -- conversion event time (event_ts_bucket component)
    idempotency_key         TEXT        NOT NULL,               -- conversion-level replay dedup (server-derived)
    attribution_context_ref TEXT        NULL,                   -- link to CTR-002 (materialized later, M6.2E)
    revenue_value           NUMERIC     NULL,                   -- ONLY from ORDER_VERIFIED (RULE-003)
    currency                TEXT        NULL,                   -- VND whenever revenue_value present (locked)
    order_code              TEXT        NULL,                   -- REFERENCE to Commerce/M8 (never an order-state write)
    dispatch_state          TEXT        NOT NULL DEFAULT 'CREATED',  -- CREATED|QUEUED|DISPATCHED|FAILED
    created_at              TIMESTAMP   NULL,
    CONSTRAINT uq_conversion_events_idempotency_key UNIQUE (idempotency_key),
    CONSTRAINT ck_conversion_events_dispatch CHECK (dispatch_state IN ('CREATED','QUEUED','DISPATCHED','FAILED')),
    -- RULE-003: a revenue-bearing conversion must be ORDER_VERIFIED (verification is Commerce-owned)
    CONSTRAINT ck_conversion_events_revenue CHECK (revenue_value IS NULL OR event_code = 'ORDER_VERIFIED')
);

-- conversion_events is the SOURCE for marketing_measurement_outbox; it NEVER sends externally (RULE-004).

-- ============================================================ DOWN (rollback)
-- Staged now => documented, not executed.
-- DROP TABLE conversion_events;
