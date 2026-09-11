-- Migration 0014 — create ads_spend_import (+ ads_spend_import_row) (M6.2Q A5, M6-OWNED, INERT maker-checker import)
-- STAGED per 04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json (live_migrations=false): NEVER applied here.
--
-- M6-OD-016: the ads-spend source is a phase-1 CSV export from Meta Ads Manager + maker-checker approve. This table
-- records an INERT import PROPOSAL: a set of CAMPAIGN-LEVEL spend rows (ads_spend_import_row), a time window, the
-- MAKER (uploaded_by), and a maker-checker state. NO Marketing API, NO new secret, NO network is involved. Spend is
-- campaign-level (campaign_id) — NOT user PII; uploaded_by/decided_by are actor/governance refs (masked on export).
-- The maker != checker (four-eyes) control is APP-ENFORCED (app/measurement/ads_spend/import_gate.py): only a
-- DISTINCT checker may APPROVE, and only an APPROVED import is materialized (0015) — it is deliberately NOT a single
-- CHECK constraint here (a cross-column identity test at approval time belongs in the app gate + audit trail).
-- Applies AFTER 0002. No flag is flipped here.

-- ============================================================ UP
CREATE TABLE ads_spend_import (
    import_id       TEXT NOT NULL PRIMARY KEY,
    window_start    TIMESTAMP NOT NULL,           -- import time window (spend is cut to a live_session window later)
    window_end      TIMESTAMP NOT NULL,
    uploaded_by     TEXT NOT NULL,                -- MAKER (actor/governance ref; masked on export, never PII)
    state           TEXT NOT NULL DEFAULT 'PROPOSED',
    decided_by      TEXT NULL,                    -- CHECKER (actor); app-enforced to DIFFER from uploaded_by on APPROVE
    decision_reason TEXT NULL,                    -- owner-review free-text (never echoed to the audit sink)
    audit_ref       TEXT NULL,
    evidence_ref    TEXT NULL,
    created_at      TIMESTAMP NULL,
    decided_at      TIMESTAMP NULL,
    CONSTRAINT ck_asi_state CHECK (state IN ('PROPOSED','APPROVED','REJECTED'))
);

CREATE TABLE ads_spend_import_row (
    import_id       TEXT NOT NULL,                -- FK -> ads_spend_import.import_id
    row_seq         INTEGER NOT NULL,             -- position within the CSV import
    campaign_id     TEXT NOT NULL,                -- CAMPAIGN-LEVEL spend key (M6-OD-016); NOT PII
    spend_value     NUMERIC NOT NULL,             -- money amount (VND)
    currency        TEXT NOT NULL DEFAULT 'VND',
    spend_date      TIMESTAMP NOT NULL,           -- reported spend day — the session-window cut key (leg 3)
    CONSTRAINT pk_asir PRIMARY KEY (import_id, row_seq),
    CONSTRAINT fk_asir_import FOREIGN KEY (import_id) REFERENCES ads_spend_import (import_id),
    CONSTRAINT ck_asir_currency CHECK (currency = 'VND')
);

CREATE INDEX ix_asi_state        ON ads_spend_import (state);
CREATE INDEX ix_asir_campaign_id ON ads_spend_import_row (campaign_id);
CREATE INDEX ix_asir_spend_date  ON ads_spend_import_row (spend_date);

-- Four-eyes (maker != checker) + "only APPROVED materializes" are APP-ENFORCED (import_gate + materializer), audited.
-- No trigger/rule effects a real spend or a send from this table (measure/record only, RULE-019: no commission).

-- ============================================================ DOWN (rollback)
-- Staged now => documented, not executed.
-- DROP TABLE ads_spend_import_row;
-- DROP TABLE ads_spend_import;
