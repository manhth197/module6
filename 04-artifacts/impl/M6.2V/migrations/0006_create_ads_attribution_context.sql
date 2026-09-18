-- Migration 0006 — create ads_attribution_context (M6-CTR-002, M6-OWNED attribution snapshot)
-- STAGED per 04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json (live_migrations=false): NEVER applied to any
-- live database by this slice. Engine-neutral DDL; the concrete engine, index implementation, and whether the
-- snapshot is a standalone table (this file) vs. embedded on ads_measurement_events bound at the M6-OD-011
-- integration step (M6-OD-011 = separate snapshot table; ads_measurement_events.attribution_context in 0002 holds
-- the materialized copy for the dashboard/ROAS read path). Applies AFTER 0002. No flag is flipped here.
--
-- The 19 DRAFT_LOCKED doc fields (SPEC 10.2 / doc §11) are reproduced VERBATIM (name/type/optionality). page_id,
-- entry_channel, attribution_window, source_confidence, conflict_status are required; the other 14 are optional.
-- Physical PACK additions (NOT doc fields): attribution_id (surrogate PK), measurement_event_id (the FK to the
-- ads_measurement_events row this snapshot attributes), materialized_at. Rules: RULE-008 (set-once / immutable
-- after verify), RULE-009 (LOW/HOLD or any conflict is never scale evidence), RULE-019 (referral recorded, never
-- a commission — there is deliberately NO commission column). B1/M5 PSID policy: `psid` is renamed to a ONE-WAY
-- salted `psid_hash` by migration 0013 — a raw PSID is NEVER stored (mask() is REVERSIBLE and is NOT sufficient).

-- ============================================================ UP
CREATE TABLE ads_attribution_context (
    attribution_id       TEXT NOT NULL PRIMARY KEY,   -- PACK surrogate id (NOT a doc field)
    measurement_event_id TEXT NOT NULL,               -- PACK FK -> ads_measurement_events.event_id (the attributed row)
    -- ---- 19 DRAFT_LOCKED doc fields (SPEC 10.2), verbatim name/type/optionality ----
    campaign_id          TEXT NULL,
    campaign_name        TEXT NULL,
    adset_id             TEXT NULL,
    adset_name           TEXT NULL,
    ad_id                TEXT NULL,
    ad_name              TEXT NULL,
    page_id              TEXT NOT NULL,               -- doc: string (required)
    live_session_id      TEXT NULL,
    comment_id           TEXT NULL,
    messenger_thread_id  TEXT NULL,
    psid                 TEXT NULL,                   -- B1/0013 renames this -> psid_hash (one-way salted hash); mask() is NOT sufficient for a PSID at rest
    referral_link_id     TEXT NULL,                   -- Diamond referral — RECORDED only, never a commission (RULE-019)
    diamond_id           TEXT NULL,                   -- Diamond referral — RECORDED only, never a commission (RULE-019)
    entry_channel        TEXT NOT NULL,               -- enum FACEBOOK_AD|LIVE_ORGANIC|DIAMOND_LINK|CRM|DIRECT
    attribution_window   TEXT NOT NULL,               -- doc: string (required)
    first_touch_event_id TEXT NULL,                   -- multi-model (M6-OD-005 OPEN): both touches recorded
    last_touch_event_id  TEXT NULL,
    source_confidence    TEXT NOT NULL,               -- enum HIGH|MEDIUM|LOW
    conflict_status      TEXT NOT NULL,               -- enum NONE|MULTI_TOUCH|MISSING_SOURCE|DUPLICATE_RISK
    -- ---- PACK physical addition ----
    materialized_at      TIMESTAMP NOT NULL,          -- when the materializer wrote this snapshot
    CONSTRAINT fk_aac_measurement_event
        FOREIGN KEY (measurement_event_id) REFERENCES ads_measurement_events (event_id),
    CONSTRAINT uq_aac_measurement_event UNIQUE (measurement_event_id),   -- one snapshot per measurement row (set-once)
    CONSTRAINT ck_aac_entry_channel
        CHECK (entry_channel IN ('FACEBOOK_AD', 'LIVE_ORGANIC', 'DIAMOND_LINK', 'CRM', 'DIRECT')),
    CONSTRAINT ck_aac_source_confidence
        CHECK (source_confidence IN ('HIGH', 'MEDIUM', 'LOW')),
    CONSTRAINT ck_aac_conflict_status
        CHECK (conflict_status IN ('NONE', 'MULTI_TOUCH', 'MISSING_SOURCE', 'DUPLICATE_RISK'))
);

-- Dashboard/ROAS + trace-to-source query paths (over doc fields).
CREATE INDEX ix_aac_measurement_event_id ON ads_attribution_context (measurement_event_id);
CREATE INDEX ix_aac_campaign_id          ON ads_attribution_context (campaign_id);
CREATE INDEX ix_aac_adset_id             ON ads_attribution_context (adset_id);
CREATE INDEX ix_aac_ad_id                ON ads_attribution_context (ad_id);
CREATE INDEX ix_aac_page_id              ON ads_attribution_context (page_id);
CREATE INDEX ix_aac_live_session_id      ON ads_attribution_context (live_session_id);
CREATE INDEX ix_aac_entry_channel        ON ads_attribution_context (entry_channel);
CREATE INDEX ix_aac_source_confidence    ON ads_attribution_context (source_confidence);
CREATE INDEX ix_aac_conflict_status      ON ads_attribution_context (conflict_status);

-- Immutability after verify (RULE-008), realized at the chosen engine at integration time (NOT executed here):
--   A snapshot for a VERIFIED measurement row is SET-ONCE: verified revenue/attribution is NEVER overwritten in
--   place. A post-verify correction is an ADJUSTMENT RECORD {actor, reason, audit, evidence} (see the app-side
--   attribution.adjustment log / a future ads_attribution_adjustment table), never a silent UPDATE of this row.
--   RULE-009: a row with source_confidence != HIGH or conflict_status != NONE is NEVER used as scale evidence;
--   scale authority additionally requires an owner-ratified model (M6-OD-005 / SCALE_MODEL_RATIFIED).
-- Illustrative Postgres form (NOT executed here):
--   REVOKE DELETE ON ads_attribution_context FROM PUBLIC;

-- ============================================================ DOWN (rollback)
-- Staged now => documented, not executed. After a real apply, dropping the table is the rollback (the snapshot
-- rows are set-once; a correction is an adjustment record, not a row delete).
-- DROP TABLE ads_attribution_context;
