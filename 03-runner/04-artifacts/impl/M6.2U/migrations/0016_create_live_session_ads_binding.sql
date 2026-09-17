-- Migration 0016 — create live_session_ads_binding (M6.2Q A5, M6-OWNED, live-session-ads-binding.v1)
-- STAGED per 04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json (live_migrations=false): NEVER applied here.
--
-- M6-OD-011 binding direction: reuse live_session_id + primary_campaign_id to bind a live_session to its primary
-- campaign (v1). This is the join hook the by-session CPA/ROAS reader uses (session_for_campaign) to attribute
-- campaign-level spend (0015) to a live_session. `bound_by` is an actor/governance ref (masked on export), never
-- PII. UNIQUE(live_session_id, primary_campaign_id) makes a binding set-once per pair; a campaign is app-enforced
-- to bind to at most one live_session (so session_for_campaign is unambiguous). No commission (RULE-019); measure/
-- record only. Applies AFTER 0002. No flag is flipped here.

-- ============================================================ UP
CREATE TABLE live_session_ads_binding (
    live_session_id     TEXT NOT NULL PRIMARY KEY,    -- set-once per live_session
    primary_campaign_id TEXT NOT NULL,                -- first-class campaign ref (NOT PII)
    adset_id            TEXT NULL,
    ad_id               TEXT NULL,
    bound_at            TIMESTAMP NULL,
    bound_by            TEXT NULL,                     -- actor/governance ref (masked on export, never PII)
    CONSTRAINT uq_lsab_session_campaign UNIQUE (live_session_id, primary_campaign_id)
);

CREATE INDEX ix_lsab_primary_campaign_id ON live_session_ads_binding (primary_campaign_id);

-- A campaign binds to at most one live_session (app-enforced in live_session_ads_binding_store) so the reverse
-- lookup session_for_campaign(campaign_id) is deterministic. Illustrative Postgres form (NOT executed here):
--   CREATE UNIQUE INDEX uq_lsab_campaign ON live_session_ads_binding (primary_campaign_id);

-- ============================================================ DOWN (rollback)
-- Staged now => documented, not executed.
-- DROP TABLE live_session_ads_binding;
