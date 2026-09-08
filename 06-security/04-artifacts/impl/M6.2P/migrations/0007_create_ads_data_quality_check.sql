-- Migration 0007 — create ads_data_quality_check (M6-CTR-012, M6-OWNED Data Quality Gate output)
-- STAGED per 04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json (live_migrations=false): NEVER applied to any
-- live database by this slice. Engine-neutral DDL; the concrete engine/index binding is the M6-OD-011 step.
--
-- One row per (measurement_event, check run) recording the 8 doc §15 gate items + the worst-status overall.
-- The 8 gate items are the verbatim doc §15 list (Event Registry / Consent / Dedup / Identity / Attribution /
-- Verified Revenue / Suppression / Dashboard). Every item status and the overall are the PASS/HOLD/FAIL vocabulary
-- (doc §9 must-not-do: the data_quality_checker outputs nothing beyond these three states). HOLD/FAIL rows are
-- never scale evidence (RULE-009). Alert thresholds are M6-OD-002 (OPEN) — NONE are encoded here. Applies AFTER 0002.

-- ============================================================ UP
CREATE TABLE ads_data_quality_check (
    check_id              TEXT NOT NULL PRIMARY KEY,   -- PACK surrogate id
    measurement_event_id  TEXT NOT NULL,               -- FK -> ads_measurement_events.event_id (subject row)
    -- the 8 doc §15 gate-item statuses (each PASS|HOLD|FAIL)
    event_registry        TEXT NOT NULL,
    consent               TEXT NOT NULL,
    dedup                 TEXT NOT NULL,
    identity              TEXT NOT NULL,
    attribution           TEXT NOT NULL,
    verified_revenue      TEXT NOT NULL,
    suppression           TEXT NOT NULL,
    dashboard             TEXT NOT NULL,
    overall               TEXT NOT NULL,               -- worst of the 8 items (FAIL > HOLD > PASS)
    detail                TEXT NULL,                   -- machine reasons (no raw PII)
    evidence_ref          TEXT NULL,                   -- masked ref
    checked_at            TIMESTAMP NOT NULL,
    CONSTRAINT fk_adqc_measurement_event
        FOREIGN KEY (measurement_event_id) REFERENCES ads_measurement_events (event_id),
    CONSTRAINT ck_adqc_event_registry   CHECK (event_registry  IN ('PASS','HOLD','FAIL')),
    CONSTRAINT ck_adqc_consent          CHECK (consent         IN ('PASS','HOLD','FAIL')),
    CONSTRAINT ck_adqc_dedup            CHECK (dedup           IN ('PASS','HOLD','FAIL')),
    CONSTRAINT ck_adqc_identity         CHECK (identity        IN ('PASS','HOLD','FAIL')),
    CONSTRAINT ck_adqc_attribution      CHECK (attribution     IN ('PASS','HOLD','FAIL')),
    CONSTRAINT ck_adqc_verified_revenue CHECK (verified_revenue IN ('PASS','HOLD','FAIL')),
    CONSTRAINT ck_adqc_suppression      CHECK (suppression     IN ('PASS','HOLD','FAIL')),
    CONSTRAINT ck_adqc_dashboard        CHECK (dashboard       IN ('PASS','HOLD','FAIL')),
    CONSTRAINT ck_adqc_overall          CHECK (overall         IN ('PASS','HOLD','FAIL'))
);

CREATE INDEX ix_adqc_measurement_event_id ON ads_data_quality_check (measurement_event_id);
CREATE INDEX ix_adqc_overall              ON ads_data_quality_check (overall);

-- data_quality_status on ads_measurement_events (Zone C) is transitioned ONLY by the data_quality_checker
-- (M6-CTR-024) to this row's `overall`; every transition is audited (RULE-015) — realized app-side by
-- MeasurementEventStore.set_data_quality_status. This table is the check evidence; it is read-only support data
-- (never a trigger owner, RULE-012).

-- ============================================================ DOWN (rollback)
-- Staged now => documented, not executed.
-- DROP TABLE ads_data_quality_check;
