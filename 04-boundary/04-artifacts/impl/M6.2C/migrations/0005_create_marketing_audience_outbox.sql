-- Migration 0005 — create marketing_audience_outbox (M6-CTR-011, M6-owned, WORKER-ONLY)
-- STAGED per IMPLEMENTATION_TARGET_LOCKED.json (live_migrations=false): NEVER applied here. Applies AFTER 0004.
--
-- Transactional outbox for audience sync. Audience sync goes ONLY from APPROVED customer_segments + this outbox
-- + consent pass (doc 12 L251); NEVER ad-hoc/data-mart (RULE-012), NEVER direct from runtime (RULE-004). Consent
-- fail-closed: opt-out => REMOVE / not-ADD (RULE-002). Bounded retry -> dead-letter (mirrors 0004). member_key is
-- PII (masked on export; payload hashed at dispatch, M6-OD-003). The audience dedup_key is DISTINCT from RULE-005.
-- customer_segments / customer_segment_members are CONSUMED (CRM owns) and are NOT created here.

-- ============================================================ UP
CREATE TABLE marketing_audience_outbox (
    outbox_id           TEXT        NOT NULL PRIMARY KEY,
    segment_id          TEXT        NOT NULL,               -- FK to an APPROVED customer_segments (M6-CTR-009)
    member_key          TEXT        NOT NULL,               -- PII (masked on export; payload hashed at dispatch)
    platform            TEXT        NOT NULL,               -- META_AUDIENCE|GOOGLE_AUDIENCE (M6-OD-004)
    operation           TEXT        NOT NULL,               -- ADD|REMOVE (opt-out => REMOVE, fail-closed)
    dedup_key           TEXT        NOT NULL,               -- audience dedup (hashed): segment+member+platform+op
    payload_ref         TEXT        NOT NULL,               -- PII-safe reference
    consent_snapshot_id TEXT        NOT NULL,               -- consent RE-VALIDATED at send (RULE-002)
    status              TEXT        NOT NULL DEFAULT 'QUEUED',
    retry_count         INTEGER     NOT NULL DEFAULT 0,
    max_retries         INTEGER     NOT NULL,
    error_log           TEXT        NULL,
    next_retry_at       TIMESTAMP   NULL,
    created_at          TIMESTAMP   NULL,
    sent_at             TIMESTAMP   NULL,
    CONSTRAINT uq_ma_outbox_dedup_key UNIQUE (dedup_key),   -- no double add/remove per member/platform/op
    CONSTRAINT ck_ma_outbox_platform CHECK (platform IN ('META_AUDIENCE','GOOGLE_AUDIENCE')),
    CONSTRAINT ck_ma_outbox_operation CHECK (operation IN ('ADD','REMOVE')),
    CONSTRAINT ck_ma_outbox_status CHECK (status IN ('QUEUED','SENT','RETRY','DEAD_LETTER'))
);

CREATE INDEX ix_ma_outbox_status ON marketing_audience_outbox (status, next_retry_at);

-- WORKER-ONLY: runtime ENQUEUES; ONLY the audience dispatcher (M6-CTR-022) re-validates consent + syncs.

-- ============================================================ DOWN (rollback)
-- DROP TABLE marketing_audience_outbox;
