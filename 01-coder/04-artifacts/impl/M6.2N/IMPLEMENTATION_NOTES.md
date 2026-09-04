# M6.2N IMPLEMENTATION NOTES — B1 PSID one-way hash (M6-OD-003 / M5 PSID policy) (STAGED)

**Trigger**: operator-directed, out-of-band. **Role**: CODER (m6-coder). **Mode**: implement (staged). Applies the
M5-issued PSID hash policy (`DAP-M5-cho-M6.md` @ M5 `1f3a4a7`, PSID_HASH_POLICY_M5_TMP) to Module 6.

> **Governance framing (read first — this is NOT a ledger-sequenced slice):** B1 (psid_hash) was explicitly OUT OF
> SCOPE of M6.2L/M6.2M ("waits on M5 hash policy / M6-OD-003"); M5 has now issued it, unblocking B1. This patch was
> directed by the operator in chat, not paste from `Get-NextPromptDetail.ps1`; the last ledger-RUNNING prompt is
> **M6-P2202** (M6.2M implement, its gate + the M6.2M slice-completion M6-P2203..2209 still pending). B1 is stacked
> as a **new superset `04-artifacts/impl/M6.2N/` of the latest impl M6.2M** (already-SIGNED impls untouched). There
> is no M6.2N slice-spec / SMOKE_REGISTER entry / ledger row yet — **operator/analyst should register the B1 slice +
> its smokes** so the governance trail is complete. **Posture immutable & untouched**: `config.py` byte-identical to
> M6.2M; `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `live_migrations=false`. No
> self-cert (RULE-015); the runner gate + JUDGE decide.

## 1. Policy applied (M5 CANONICAL, transcribed by the operator)

A raw PSID is stored **NOWHERE** — not even on a durable Zone-B row; `mask()` (abc***xy) hides but is **reversible**
and is **NOT sufficient**. A PSID is hashed to **`psid_hash:` + base64url(HMAC-SHA256(pepper, psid))** — one-way +
salted. The **pepper is a SECRET** (per-environment, an **M6-own** pepper — no shared pepper with M5; cross-module
joins are a separate owner+chief decision, OUT OF SCOPE): resolved from env `M6_PSID_HASH_PEPPER` via secret_ref at
deploy; **fail-closed in production** (unset ⇒ refuse); a fixed **mock pepper** is used ONLY in dev/staged tests.
The pepper and the raw psid are **never committed / logged / emitted / put in evidence**.

## 2. Staging & change set (all under `04-artifacts/impl/M6.2N/`)

Carried **M6.2M** byte-identical (caches + M6.2M PLAN/NOTES excluded); baseline verified green **before any patch:
575 passed** (parity with M6.2M). Final suite: **581 passed** (575 carried, of which **5 realigned** to the new psid
contract, + **6 new B1 tests**). Subprocess `pytest` with `PYTHONDONTWRITEBYTECODE=1 python -B`; no skips.

| File | Change | Kind |
|---|---|---|
| **new** `app/measurement/identity/psid_hash.py` | `hash_psid(psid)` (one-way salted, `psid_hash:` prefix, None for None/blank, coerces a non-str id); `resolve_pepper` (env secret_ref, fail-closed production, injectable `production` flag so the branch is testable without flipping the immutable flag); `PsidHashPolicyError`; a labelled non-secret dev mock pepper | code |
| `app/measurement/models/attribution_context.py` | field `psid` → **`psid_hash`**; `to_public()` emits `psid_hash` as-is (one-way → no mask); `as_stored()` returns the export mapping (no raw-psid keep); dropped the now-unused `mask` import; docstrings | code |
| `app/measurement/attribution/resolver.py` | `LiveContext.psid` → `psid_hash`; **hash at ingest** in `resolve_live_session` (`psid_hash=hash_psid(signals.get("psid"))`) so the raw psid lives only in that one call (RAM); `resolve()` threads `psid_hash` | code |
| `app/measurement/funnel/funnel.py` | `_trace` reads `ctx["psid_hash"]`, threads `psid_hash`; docstrings | code |
| `app/measurement/funnel/models.py` | `FunnelTrace.psid` → `psid_hash`; `to_public()` emits it as-is (no mask); dropped unused `mask` import; docstrings | code |
| **new** `migrations/0013_psid_to_psid_hash.sql` | staged `ALTER TABLE ads_attribution_context RENAME COLUMN psid TO psid_hash` (append-only; 0006 kept as historical DDL, comments forward-noted to psid_hash) | migration |
| `tests/test_live_session_chain_trace.py`, `tests/smoke/test_smk_013_live_chain_trace.py`, `tests/test_golden_hour_funnel_chain.py`, `tests/test_live_chain_trace_in_funnel.py`, `tests/smoke/test_smk_013_funnel_live_chain_trace.py` | **realigned** the psid companion assertions to the new contract (durable+export = one-way hash, no raw); live-chain-trace assertions unchanged | test |
| **new** `tests/test_b1_psid_hash.py` | (a) no raw in store, (b) one-way+prefix+deterministic, (c) fail-closed production, (d) None/blank→None, + non-str coercion + env-pepper-salts | test |

**Scope guard**: no change to the M6.2L/M6.2M fixes (B2/B3/B4/A3/A4), no governance-flag/config change, no
00-spec/state write. Migrations `0001–0013` (0013 is the only new one — explicitly authorized). `audit.py`'s raw-id
tripwire (which lists a `psid` prefix) is a GUARD and is left intact.

> **TESTER-boundary note (flag for re-bless):** removing the raw PSID necessarily invalidated the psid companion
> assertions in two **TESTER-authored SMK-013 smokes** (`test_smk_013_neg_psid_is_masked_on_export_but_kept_durably`,
> `test_smk_013_neg_psid_masked_on_export`) and three coder tests — they asserted the OLD contract (raw kept
> durably, masked-but-reversible on export). I **realigned** them to the new one-way-hash contract (NOT weakened —
> they still prove no raw psid on any surface + the live-chain trace) and left the (now slightly stale) function
> names for the **TESTER to re-bless / rename**. This was unavoidable under the operator's "quét mọi .psid →
> .psid_hash + full suite no regress" directive.

## 3. Security verification (raw psid / pepper leak)

- **Durable + export are hash-only**: `as_stored()` and `to_public()` carry `psid_hash` and **no `psid` key**; the
  model no longer has a raw-psid field. Edge-probe (running code): resolving a context with a raw psid signal →
  the raw value appears in **neither** `str(as_stored())`, `str(to_public())`, the funnel view `to_public()`, nor any
  audit record. `grep` of `app/` for a raw `.psid` field/`["psid"]` key ⇒ **NONE** (only `psid_hash`); the sole
  raw-psid touch is the single hash-on-ingest point in `resolve_live_session`.
- **One-way + deterministic**: HMAC-SHA256 with the **pepper as the key** (not the message) + base64url; a given
  pepper yields a stable join key; the raw psid is not recoverable/embedded.
- **Fail-closed**: `resolve_pepper(production=True)` with the env unset **raises** `PsidHashPolicyError`; the mock
  pepper is reachable **only** in a non-production posture. The pepper is never logged/returned/committed (only a
  labelled non-secret dev mock string is in source; the real pepper is env-only).
- **No PII/pepper literals** in the changed files (scanned). `config.py` byte-identical to M6.2M.

## 4. Adversarial self-review (ultracode) — leak axis CLEAN, 2 NIT fixed

A 2-dimension red-team (leak-hunt + regression/scope), each finding re-verified by an independent skeptic **running
the M6.2N code**, confirmed the **load-bearing axis CLEAN** (no raw-PSID / pepper leak; fail-closed + mock-pepper
reachability correct; no regression; scope intact) and surfaced **2 NIT** (both fixed here) + 2 stale-doc items (1
fixed):
- **(NIT, fixed) `hash_psid` silently dropped a non-str psid** (privacy-safe but lost a legit join key) → now
  coerces `str(psid)` before hashing (+ regression). 
- **(NIT, fixed) migration 0006 comments still called the column reversibly-"masked" PII** — the exact control B1
  rejects — misleading to the M6-OD-011 integration engineer → forward-noted to `psid_hash` + "mask() not
  sufficient".
- **(stale-doc, fixed) `funnel.py` module docstring "psid masked on export"** → one-way hash.

## 5. Rollback

Staged only — baseline rollback = delete the `04-artifacts/impl/M6.2N/` tree (M6.2M untouched). Per item: revert the
named files to their M6.2M bytes and delete `psid_hash.py`, `0013_psid_to_psid_hash.sql`, `test_b1_psid_hash.py`.
**Do NOT** run 0013's DOWN rename (it would reintroduce a raw-PSID column name — a privacy regression). No live
migration to unwind (staged; `live_migrations=false`). Every change is a privacy tightening or a mechanical rename;
a revert restores the prior (raw-psid) behaviour, which is the thing B1 removes — so a rollback is a privacy
regression, to be done only deliberately.
