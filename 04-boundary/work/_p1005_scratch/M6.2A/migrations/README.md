# Migrations (STAGED — never applied)

Per `04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json` (`safety.live_migrations = false`), **no migration in
this folder is applied to any live database** by slice M6.2A. They are staged DDL, reviewed as evidence; the
owner-controlled integration step (bound to `M6-OD-011`) chooses the engine and applies them.

| # | File | Owns | Rules | Rollback |
|---|---|---|---|---|
| 0001 | `0001_create_web_event_logs.sql` | `web_event_logs` (M6-CTR-004, the ONLY M6-owned table this slice) | RULE-007 append-only, RULE-005 idempotency UNIQUE | Down = `DROP TABLE web_event_logs` (included, commented). Staged ⇒ never applied ⇒ deleting the file fully reverts. |

**Not migrated here** (owned + migrated by their own modules; Module 6 only reads them):
`event_registry` (Core Event Governance), `guest_contacts` / `customers*` (Customer identity),
`guest_marketing_consent_snapshot` (Consent system).

Append-only note: once a real apply happens, `web_event_logs` history is never updated or deleted; reverting
requires the down-DDL (`DROP TABLE`), not row deletion.
