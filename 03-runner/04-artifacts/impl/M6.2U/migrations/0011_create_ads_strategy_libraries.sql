-- Migration 0011 — create the six ADS Strategy Libraries + the strategy mapping (M6.2H, doc §17)
-- STAGED per 04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json (live_migrations=false): NEVER applied here.
--
-- RULE-011 / LEX-006: the machine NEVER fabricates origin strategy. Every library entry REQUIRES a canonical
-- seed_source (seed_source NOT NULL); `content` is the machine-generated origin strategy and stays NULL while
-- content fill is BLOCKED (M6-OD-007 OPEN, framework-only). The mapping is anchored to a sellable SKU (LEX-005).
-- The layer READS canonical sources only — it never writes pricing/program/policy (RULE-013/018). Applies AFTER 0002.

-- ============================================================ UP
CREATE TABLE ads_strategy_library_entry (
    entry_id      TEXT NOT NULL PRIMARY KEY,
    kind          TEXT NOT NULL,                 -- Persona | Behavior | Keyword | Negative Keyword | Creative Hook | Landing / CTA
    seed_source   TEXT NOT NULL,                 -- REQUIRED canonical source (RULE-011); non-canonical rejected app-side
    purpose       TEXT NOT NULL,                 -- doc §17 purpose (locked per kind)
    content       TEXT NULL,                     -- machine-generated origin strategy; NULL while M6-OD-007 OPEN (framework-only)
    created_at    TIMESTAMP NOT NULL,
    CONSTRAINT ck_asle_kind CHECK (kind IN (
        'Persona Library','Behavior Library','Keyword Library',
        'Negative Keyword Library','Creative Hook Library','Landing / CTA Library'))
);

CREATE INDEX ix_asle_kind ON ads_strategy_library_entry (kind);

CREATE TABLE ads_strategy_mapping (
    mapping_id           TEXT NOT NULL PRIMARY KEY,
    sku_ref              TEXT NOT NULL,           -- sellable SKU / product line (REQUIRED, LEX-005)
    persona              TEXT NULL,
    behavior             TEXT NULL,
    keyword              TEXT NULL,
    creative_hook        TEXT NULL,
    landing              TEXT NULL,
    cta                  TEXT NULL,
    event_ref            TEXT NULL,               -- ref to ads_measurement_events.event_id
    verified_revenue_ref TEXT NULL,               -- ref to the ORDER_VERIFIED revenue row (M6.2E); never a value
    created_at           TIMESTAMP NOT NULL
);

CREATE INDEX ix_asm_sku_ref ON ads_strategy_mapping (sku_ref);

-- No trigger/rule ever attached that generates content or acts on these rows. seed_source is mandatory and the
-- app rejects a non-canonical source; content stays NULL until M6-OD-007 ratifies content fill (RULE-011, LEX-006).

-- ============================================================ DOWN (rollback)
-- Staged now => documented, not executed.
-- DROP TABLE ads_strategy_mapping;
-- DROP TABLE ads_strategy_library_entry;
