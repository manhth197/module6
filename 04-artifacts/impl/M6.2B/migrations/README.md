# Migrations (STAGED — never applied)

Per `04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json` (`safety.live_migrations = false`), **no migration in
this folder is applied to any live database** by slices M6.2A / M6.2B. They are staged DDL, reviewed as
evidence; the owner-controlled integration step (bound to `M6-OD-011`) chooses the engine and applies them.
**Application order: `0001` then `0002`.**

| # | File | Owns | Rules | Rollback |
|---|---|---|---|---|
| 0001 | `0001_create_web_event_logs.sql` | `web_event_logs` (M6-CTR-004, raw append-only ingress log) | RULE-007 append-only, RULE-005 idempotency UNIQUE | Down = `DROP TABLE web_event_logs` (included, commented). Staged ⇒ never applied ⇒ deleting the file fully reverts. |
| 0002 | `0002_create_ads_measurement_events.sql` | `ads_measurement_events` (M6-CTR-001, normalized store for dashboard/ROAS) | RULE-005 idempotency UNIQUE (dedup, SMK-003), RULE-003 revenue-only-ORDER_VERIFIED, RULE-007/008 immutability zones | Down = `DROP TABLE ads_measurement_events` (included, commented). Zone-A is write-once; revert after a real apply is the down-DDL, not row deletes. Staged ⇒ deleting the file fully reverts. |

**Not migrated here** (owned + migrated by their own modules; Module 6 only reads them):
`event_registry` (Core Event Governance), `guest_contacts` / `customers*` (Customer identity),
`guest_marketing_consent_snapshot` (Consent system).

Append-only note: once a real apply happens, `web_event_logs` history is never updated or deleted; reverting
requires the down-DDL (`DROP TABLE`), not row deletion.
