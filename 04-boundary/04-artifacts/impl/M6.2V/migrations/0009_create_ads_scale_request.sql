-- Migration 0009 — create ads_scale_request (M6-CTR-013, M6-OWNED, INERT scale-request proposal)
-- STAGED per 04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json (live_migrations=false): NEVER applied here.
--
-- RULE-010 / FAIL-006: this table is INERT PROPOSAL DATA. A row records the 8 doc §16 condition statuses, an
-- OWNER-review budget_cap and rollback_condition (both are request FIELDS / requirements, NOT actions), evidence
-- refs, and an approval_state. Module 6 has NO trigger and NO executable path that raises a budget, enables a
-- campaign, opens audience scale, or publishes — those are OWNER actions performed OUTSIDE Module 6, gated by
-- production_flag=OFF. There is deliberately NO trigger/rule on this table that could effect a scale. Applies AFTER 0002.

-- ============================================================ UP
CREATE TABLE ads_scale_request (
    request_id          TEXT NOT NULL PRIMARY KEY,
    campaign_id         TEXT NULL,                    -- scale_target reference (recorded only, never mutated)
    adset_id            TEXT NULL,
    ad_id               TEXT NULL,
    budget_cap          NUMERIC NULL,                 -- request FIELD (a ceiling/requirement), NOT an action
    rollback_condition  TEXT NULL,                    -- request FIELD (a requirement), NOT an action
    evidence_refs       TEXT NULL,                    -- assembled masked evidence refs (owner-review pack)
    -- the 8 doc §16 condition statuses (each PASS|HOLD|FAIL)
    cond_p3_p5_p6       TEXT NOT NULL,
    cond_quote_order    TEXT NOT NULL,
    cond_public_privacy TEXT NOT NULL,
    cond_funnel         TEXT NOT NULL,
    cond_dashboard      TEXT NOT NULL,
    cond_quality        TEXT NOT NULL,
    cond_risk           TEXT NOT NULL,
    cond_approval       TEXT NOT NULL,
    overall_status      TEXT NOT NULL,                -- worst of the 8 (PASS|HOLD|FAIL)
    approval_state      TEXT NOT NULL DEFAULT 'PROPOSED',
    created_at          TIMESTAMP NOT NULL,
    decided_at          TIMESTAMP NULL,
    CONSTRAINT ck_asr_approval_state CHECK (approval_state IN ('COMPUTED','PROPOSED','APPROVED','REJECTED')),
    CONSTRAINT ck_asr_overall        CHECK (overall_status IN ('PASS','HOLD','FAIL')),
    CONSTRAINT ck_asr_cond_p3        CHECK (cond_p3_p5_p6       IN ('PASS','HOLD','FAIL')),
    CONSTRAINT ck_asr_cond_qo        CHECK (cond_quote_order    IN ('PASS','HOLD','FAIL')),
    CONSTRAINT ck_asr_cond_pp        CHECK (cond_public_privacy IN ('PASS','HOLD','FAIL')),
    CONSTRAINT ck_asr_cond_funnel    CHECK (cond_funnel         IN ('PASS','HOLD','FAIL')),
    CONSTRAINT ck_asr_cond_dashboard CHECK (cond_dashboard      IN ('PASS','HOLD','FAIL')),
    CONSTRAINT ck_asr_cond_quality   CHECK (cond_quality        IN ('PASS','HOLD','FAIL')),
    CONSTRAINT ck_asr_cond_risk      CHECK (cond_risk           IN ('PASS','HOLD','FAIL')),
    CONSTRAINT ck_asr_cond_approval  CHECK (cond_approval       IN ('PASS','HOLD','FAIL'))
);

CREATE INDEX ix_asr_approval_state ON ads_scale_request (approval_state);
CREATE INDEX ix_asr_overall        ON ads_scale_request (overall_status);
CREATE INDEX ix_asr_campaign_id    ON ads_scale_request (campaign_id);

-- No trigger, no rule, no procedure is ever attached that could effect a scale from this table (RULE-010). The
-- owner reads it, decides, and performs any budget change outside Module 6 (production_flag=OFF).

-- ============================================================ DOWN (rollback)
-- Staged now => documented, not executed.
-- DROP TABLE ads_scale_request;
