-- Migration 0015 — create ads_spend_record (M6.2Q A5, M6-OWNED, MATERIALIZED campaign-level spend)
-- STAGED per 04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json (live_migrations=false): NEVER applied here.
--
-- The set-once destination the materialize worker writes from an APPROVED ads_spend_import (0014, M6-OD-016). One
-- row = one CAMPAIGN-LEVEL spend line (campaign_id + amount + spend_date). adset_id / ad_id are NULL: the phase-1
-- source is campaign-level, so the by-session CPA/ROAS reader (session_roas) attributes spend by the
-- campaign->live_session BINDING (0016), NOT the 3-id AdsSpendRecord.mapped predicate. Materialization is SET-ONCE
-- per import (app-enforced ads_spend_record_store): a correction is a NEW import, never an in-place overwrite.
-- Spend is not PII; measure/record only (RULE-019: no commission). Applies AFTER 0014. No flag is flipped here.

-- ============================================================ UP
CREATE TABLE ads_spend_record (
    import_id       TEXT NOT NULL,                -- FK -> ads_spend_import.import_id (provenance; APPROVED only)
    row_seq         INTEGER NOT NULL,             -- position within the materialized import
    campaign_id     TEXT NOT NULL,                -- CAMPAIGN-LEVEL spend key (M6-OD-016); NOT PII
    adset_id        TEXT NULL,                    -- phase-1 source is campaign-level -> NULL
    ad_id           TEXT NULL,                    -- phase-1 source is campaign-level -> NULL
    amount          NUMERIC NOT NULL,             -- money amount (VND)
    currency        TEXT NOT NULL DEFAULT 'VND',
    spend_date      TIMESTAMP NOT NULL,           -- session-window cut key (leg 3)
    materialized_at TIMESTAMP NULL,
    CONSTRAINT pk_asr_record PRIMARY KEY (import_id, row_seq),
    CONSTRAINT fk_asr_import FOREIGN KEY (import_id) REFERENCES ads_spend_import (import_id),
    CONSTRAINT ck_asr_currency CHECK (currency = 'VND')
);

CREATE INDEX ix_asr_record_campaign_id ON ads_spend_record (campaign_id);
CREATE INDEX ix_asr_record_spend_date  ON ads_spend_record (spend_date);

-- Set-once (app-enforced): only an APPROVED import materializes here; a second/altered materialize is refused.
-- Illustrative Postgres form (NOT executed here):
--   REVOKE UPDATE, DELETE ON ads_spend_record FROM PUBLIC;

-- ============================================================ DOWN (rollback)
-- Staged now => documented, not executed.
-- DROP TABLE ads_spend_record;
