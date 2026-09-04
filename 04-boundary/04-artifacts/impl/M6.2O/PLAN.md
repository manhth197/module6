# M6.2O PLAN / CHANGE-SET RECORD — B1 (psid_hash) + F2-6 (duck-coerce) (STAGED)

**Kind**: coder-role **record** of an already-staged, operator-directed out-of-band change-set (NOT a re-implement —
this file + IMPLEMENTATION_NOTES.md consolidate the plan/rollback/scope for B1 + F2-6, which are live under
`04-artifacts/impl/M6.2O/`). M6.2O is the cumulative superset **M6.2M → M6.2N (B1) → M6.2O (F2-6)**, so it carries
**both** B1 and F2-6. Governance immutable & verified untouched: `config.py` sha256 **911b3238…** identical to
M6.2M; `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `live_migrations=false`. No
self-cert (RULE-015); the runner gate + JUDGE decide. Source evidence:
[M6-B1-PSID-HASH.json](../../evidence/prompts/M6-B1-PSID-HASH.json),
[M6-F2-6-DUCK-SMOKE.json](../../evidence/prompts/M6-F2-6-DUCK-SMOKE.json).

## B1 — PSID one-way hash (M6-OD-003 / M5 PSID policy PSID_HASH_POLICY_M5_TMP)

| File : anchor | Change | Fix | Rollback (staged; per item) |
|---|---|---|---|
| `app/measurement/identity/psid_hash.py` (**new**) | `resolve_pepper` (:37, env `M6_PSID_HASH_PEPPER` via secret_ref; **fail-closed production** when unset; injectable `production`), `hash_psid` (:53, `psid_hash:`+base64url(HMAC-SHA256(**pepper=key**, psid)); None for None/blank; coerces non-str), `PsidHashPolicyError` (:33), labelled **non-secret dev** `_MOCK_PEPPER` (:30) | B1 | delete the file |
| `app/measurement/models/attribution_context.py` | field `psid` → **`psid_hash`** (:77); `to_public()` emits `psid_hash` as-is (:116, no mask); `as_stored()` = `dict(self.to_public())` (:133, no raw-keep); dropped unused `mask` import; docstrings | B1 | revert to M6.2M bytes (restores raw `psid` field) |
| `app/measurement/attribution/resolver.py` | `import hash_psid` (:26); `LiveContext.psid` → `psid_hash` (:75); **hash at ingest** `psid_hash=hash_psid(signals.get("psid"))` (:104, raw psid stays in RAM only); `resolve()` threads `psid_hash=live.psid_hash` (:151) | B1 | revert to M6.2M bytes |
| `app/measurement/funnel/funnel.py` | `_trace` reads `ctx.get("psid_hash")` (:180), threads `psid_hash` into `FunnelTrace` (:182); docstrings | B1 | revert to M6.2M bytes |
| `app/measurement/funnel/models.py` | `FunnelTrace.psid` → `psid_hash` (:36); `to_public()` emits it as-is (:43, no mask); dropped unused `mask` import | B1 | revert to M6.2M bytes |
| `migrations/0013_psid_to_psid_hash.sql` (**new**) | staged `ALTER TABLE ads_attribution_context RENAME COLUMN psid TO psid_hash` (:13, append-only) | B1 | delete the file (do NOT run its DOWN rename — reintroducing a raw-`psid` column is a privacy regression) |
| `migrations/0006_create_ads_attribution_context.sql` | **comment-only** (2 lines): the raw-`psid` column comment forward-noted to `psid_hash` (mask() insufficient) | B1 | revert the 2 comment lines |

## F2-6 — `_smokes` must not trust a caller-supplied `.recorded` (code-exec-only; not channel-reachable; no prod risk)

| File : anchor | Change | Fix | Rollback (staged; per item) |
|---|---|---|---|
| `app/measurement/evidence/pack_assembler.py` | `_smokes` (:157–170) **coerces** every provided object to a canonical frozen `SmokeResult` rebuilt from its **fields** (`smoke_id`=registry; `status`/`correlation_id`/`evidence_id`/`waived` via `getattr`), so `recorded` is recomputed by `SmokeResult.recorded` (fail-closed) — the caller's `.recorded` is never trusted. Strip-waiver + whitespace-normalize run after, unchanged | F2-6 | revert `_smokes` to M6.2M/M6.2N bytes (restores the duck-trusting behaviour) |
| `tests/test_duck_smoke_recorded.py` (**new**) | duck (`.recorded=True`, blank fields) ⇒ `recorded=False` + `UNRUN` gap + `NOT_READY`; isolating flip; non-vacuity | F2-6 | delete the file |

## C7 — M5 runtime-controls invariant (documentation only, no code)

| File | Change | Rollback |
|---|---|---|
| `INVARIANTS_M5_RUNTIME_CONTROLS.md` (**new, doc**) | records the HARD invariant "no `external_send`/real Graph sink until the 4 M5 controls close + owner signs"; M6's fail-closed enforcement is M6-verified; the 4-control status is M5-reported DATA; canonical home (Scale-Gate/go-live checklist + `_OWNER_RISK_ACCEPTANCE.md`) is owner/analyst-owned | delete the file |

## Baseline rollback

Staged only — delete the whole `04-artifacts/impl/M6.2O/` tree (M6.2N + M6.2M untouched). No live migration to unwind
(`live_migrations=false`). Every change is a privacy tightening (B1), a fail-closed tightening (F2-6), or a comment/
doc — a full revert restores the prior (raw-psid / duck-trusting) behaviour, which is precisely what these fixes
remove, so a rollback is a deliberate regression, not a routine undo.
