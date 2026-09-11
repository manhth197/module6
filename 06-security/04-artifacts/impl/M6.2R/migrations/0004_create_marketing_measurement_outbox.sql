-- Migration 0004 — create marketing_measurement_outbox (M6-CTR-008, M6-owned, WORKER-ONLY)
-- STAGED per IMPLEMENTATION_TARGET_LOCKED.json (live_migrations=false): NEVER applied here. Applies AFTER 0003.
--
-- Transactional outbox for Pixel/CAPI/Offline egress. External measurement goes ONLY through this outbox + the
-- dispatcher worker (M6-CTR-021), never direct from a runtime request (RULE-004). One row per (conversion x
-- platform), UNIQUE on the LOCKED RULE-005 dedup_key. Bounded retry -> dead-letter (doc 12 L252; SMK-016).
-- NO raw PII in the row: dedup_key is HASHED, payload_ref is PII-safe (payload built + hashed at dispatch,
-- M6-OD-003/M6.2D). Doc-named fields error_log + next_retry_at verbatim.

-- ============================================================ UP
CREATE TABLE marketing_measurement_outbox (
    outbox_id           TEXT        NOT NULL PRIMARY KEY,
    source_event_id     TEXT        NOT NULL,               -- link to conversion_events (M6-CTR-007)
    platform            TEXT        NOT NULL,               -- PIXEL|CAPI|OFFLINE (connector scope = M6-OD-004)
    dedup_key           TEXT        NOT NULL,               -- LOCKED RULE-005 (hashed, PII-safe)
    idempotency_key     TEXT        NOT NULL,               -- LOCKED RULE-005 (platform-side dedup)
    payload_ref         TEXT        NOT NULL,               -- PII-safe reference; hashed payload at dispatch
    consent_snapshot_id TEXT        NOT NULL,               -- consent RE-VALIDATED at send (RULE-002)
    status              TEXT        NOT NULL DEFAULT 'QUEUED',   -- QUEUED|SENT|RETRY|DEAD_LETTER (SPEC 13)
    retry_count         INTEGER     NOT NULL DEFAULT 0,
    max_retries         INTEGER     NOT NULL,               -- bounded (value=config; the BOUND is doc-mandated)
    error_log           TEXT        NULL,                   -- doc 12 L252 verbatim (no silent loss)
    next_retry_at       TIMESTAMP   NULL,                   -- doc 12 L252 verbatim
    created_at          TIMESTAMP   NULL,
    sent_at             TIMESTAMP   NULL,
    CONSTRAINT uq_mm_outbox_dedup_key UNIQUE (dedup_key),   -- one row per conversion x platform (no double send)
    CONSTRAINT ck_mm_outbox_platform CHECK (platform IN ('PIXEL','CAPI','OFFLINE')),
    CONSTRAINT ck_mm_outbox_status CHECK (status IN ('QUEUED','SENT','RETRY','DEAD_LETTER'))
);

CREATE INDEX ix_mm_outbox_status ON marketing_measurement_outbox (status, next_retry_at);

-- WORKER-ONLY: runtime ENQUEUES QUEUED rows; ONLY the dispatcher (M6-CTR-021) transitions status + sends.
-- Illustrative Postgres guard (NOT executed here): REVOKE UPDATE, DELETE ... FROM the runtime role.

-- ============================================================ DOWN (rollback)
-- DROP TABLE marketing_measurement_outbox;
