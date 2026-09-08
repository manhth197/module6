-- Migration 0013 — ads_attribution_context.psid -> psid_hash  (B1 / M6-OD-003, M5 PSID hash policy DAP-M5-cho-M6)
-- STAGED per 04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json (live_migrations=false): NEVER applied to any
-- live database by this slice. Engine-neutral DDL; the concrete engine binds at the M6-OD-011 integration step.
-- Applies AFTER 0006. No flag is flipped here; no external send.
--
-- Policy (PSID_HASH_POLICY_M5_TMP): a raw PSID is NEVER stored on any durable row (mask() is REVERSIBLE and
-- insufficient). The column now stores a ONE-WAY salted hash — 'psid_hash:' + base64url(HMAC-SHA256(pepper, psid)).
-- The pepper is a per-environment SECRET resolved from a secret_ref at deploy (env M6_PSID_HASH_PEPPER, an M6-OWN
-- pepper); production fail-closes (refuse boot) if it is unset. The pepper is NEVER stored in the schema or emitted.
-- After this migration there is no raw `psid` column — only the one-way `psid_hash`.

-- ============================================================ UP
ALTER TABLE ads_attribution_context RENAME COLUMN psid TO psid_hash;
-- psid_hash now holds a one-way salted hash ('psid_hash:'-prefixed), never a raw PSID. (0006 created no index on
-- psid, so there is none to rename.) A future engine may re-type/constraint it to a fixed-length token at
-- integration time; the app already writes only the hash.

-- Illustrative Postgres form for the intent (NOT executed here):
--   COMMENT ON COLUMN ads_attribution_context.psid_hash IS 'one-way salted PSID hash (psid_hash:...); never raw PSID';

-- ============================================================ DOWN (rollback)
-- Staged now => documented, not executed. Reverting the rename would REINTRODUCE a raw-PSID column name and is a
-- privacy regression; do NOT run it. A real rollback of B1 is the whole-slice staged-tree revert, not this rename.
--   ALTER TABLE ads_attribution_context RENAME COLUMN psid_hash TO psid;
