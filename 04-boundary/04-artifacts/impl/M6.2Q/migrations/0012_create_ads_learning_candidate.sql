-- Migration 0012 — create ads_learning_candidate (M6-CTR-014, M6-OWNED, INERT learning-candidate)
-- STAGED per 04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json (live_migrations=false): NEVER applied here.
--
-- RULE-011 / LEX-006 / FAIL-006: this table is INERT PROPOSAL DATA for owner/marketing review. A candidate lands
-- in the review queue; there is NO trigger and NO auto-publish path. A candidate NOT WITHIN the owner-ratified
-- safe range (UNKNOWN while M6-OD-006 OPEN) is HELD, never published (SMK-011). review_state transitions only via
-- an explicit owner review decision (see ads_learning_review, recorded app-side). Applies AFTER 0011.

-- ============================================================ UP
CREATE TABLE ads_learning_candidate (
    candidate_id       TEXT NOT NULL PRIMARY KEY,
    kind               TEXT NOT NULL,            -- DELTA | SAFE_RANGE | OPTIMIZATION
    target_dim         TEXT NOT NULL,            -- persona | keyword | hook | landing | cta (the 5 doc §17 Learn dims)
    score              NUMERIC NOT NULL,
    sku_ref            TEXT NOT NULL,            -- anchored to a sellable SKU (LEX-005)
    evidence_refs      TEXT NULL,
    review_state       TEXT NOT NULL DEFAULT 'CANDIDATE',
    safe_range_status  TEXT NOT NULL DEFAULT 'UNKNOWN',   -- fail-closed while M6-OD-006 OPEN
    created_at         TIMESTAMP NOT NULL,
    decided_at         TIMESTAMP NULL,
    CONSTRAINT ck_alc_kind         CHECK (kind IN ('DELTA','SAFE_RANGE','OPTIMIZATION')),
    CONSTRAINT ck_alc_target_dim   CHECK (target_dim IN ('persona','keyword','hook','landing','cta')),
    CONSTRAINT ck_alc_review_state CHECK (review_state IN ('CANDIDATE','IN_REVIEW','APPROVED','REJECTED','HOLD')),
    CONSTRAINT ck_alc_safe_range   CHECK (safe_range_status IN ('WITHIN','OUTSIDE','UNKNOWN'))
);

CREATE INDEX ix_alc_review_state ON ads_learning_candidate (review_state);
CREATE INDEX ix_alc_target_dim   ON ads_learning_candidate (target_dim);

-- No trigger/rule ever attached that publishes a candidate. Publish is owner-approval-only and the guarded
-- safe-range publish is BLOCKED (M6-OD-006 OPEN); the machine never auto-publishes (RULE-011, LEX-006, FAIL-006).

-- ============================================================ DOWN (rollback)
-- Staged now => documented, not executed.
-- DROP TABLE ads_learning_candidate;
