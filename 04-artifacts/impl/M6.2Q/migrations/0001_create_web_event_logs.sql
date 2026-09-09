-- Migration 0001 — create web_event_logs (M6-CTR-004, M6-OWNED, append-only)
-- STAGED per 04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json (live_migrations=false): NEVER applied to any
-- live database by this slice. Engine-neutral DDL; the concrete engine + physical append-only enforcement bind
-- at the owner-controlled M6-OD-011 integration step.
--
-- Rules: RULE-007 (append-only: INSERT only; no UPDATE/DELETE), RULE-005 (idempotency_key UNIQUE = dedup).
-- Module 6 owns ONLY this table; event_registry / guest_contacts / guest_marketing_consent_snapshot are owned
-- and migrated by their own modules and are NOT created here.

-- ============================================================ UP
CREATE TABLE web_event_logs (
    log_id              TEXT        NOT NULL PRIMARY KEY,   -- surrogate key (PACK addition)
    event_code          TEXT        NOT NULL,               -- must resolve in event_registry (RULE-001)
    page_id             TEXT        NOT NULL,               -- doc §7 L117 'page'
    session_id          TEXT        NOT NULL,               -- 'session' (PII-pseudonymous; mask in logs/evidence)
    source              TEXT        NOT NULL,               -- 'source' (channel-origin = untrusted DATA)
    consent_snapshot_id TEXT        NULL,                   -- 'consent snapshot' -> M6-CTR-006 (nullable)
    event_ts            TIMESTAMP   NOT NULL,               -- 'event_ts' (event's own time)
    idempotency_key     TEXT        NOT NULL,               -- locked RULE-005 formula
    ingested_at         TIMESTAMP   NOT NULL,               -- append time (distinct from event_ts)
    correlation_id      TEXT        NULL,                   -- trace to ads_measurement_event (later slice)
    CONSTRAINT uq_web_event_logs_idempotency_key UNIQUE (idempotency_key)  -- dedup: no double log (RULE-005)
);

-- Append-only enforcement (RULE-007) is realized at the chosen engine at integration time. Illustrative
-- Postgres form (NOT executed here):
--   REVOKE UPDATE, DELETE ON web_event_logs FROM PUBLIC;
--   CREATE RULE web_event_logs_no_update AS ON UPDATE TO web_event_logs DO INSTEAD NOTHING;
--   CREATE RULE web_event_logs_no_delete AS ON DELETE TO web_event_logs DO INSTEAD NOTHING;
-- History is never updated or deleted (doc §7 L117 / §13 L264).

-- ============================================================ DOWN (rollback)
-- Because the table is append-only, reverting after a real apply requires dropping the table (not row deletes).
-- Staged now => this is documented, not executed.
-- DROP TABLE web_event_logs;
