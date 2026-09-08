# M6.2O IMPLEMENTATION NOTES — Out-of-band Backfill RECORD (B1 psid_hash + F2-6 duck-coerce) (STAGED)

**Prompt**: M6-P2302 (`M6_2O_CODER_IMPLEMENT`) · **Role**: CODER · **Mode**: `implement` (**RECORD leg — NO
re-implementation**) · **Gate**: EVIDENCE_GATE. **Follows**: [PLAN.md](PLAN.md) (M6-P2301). This leg **records** the
already-shipped, verified-clean B1 + F2-6 code under `04-artifacts/impl/M6.2O/`; it writes **no application code**.

> **Posture (immutable, verified untouched):** `config.py` sha256 **911b3238…** byte-identical to M6.2M;
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `live_migrations=false`. No self-cert
> (RULE-015); the runner gate + JUDGE (M6-P2309) decide.

Ledger verified: **M6-P2302 = RUNNING** (row 222), dependency **M6-P2301 = PASS**. Target **LOCKED**, **M6-OD-011
DECIDED**.

## 1. This is a RECORD leg (the shipped code is unchanged)

The B1 + F2-6 change-set (the §2 tables of [PLAN.md](PLAN.md)) is already staged and green. This leg **verified** it
and wrote these notes; **it changed no code**. App-tree byte-diff M6.2N → M6.2O = **only**
`app/measurement/evidence/pack_assembler.py` (the F2-6 `_smokes` change); every B1 file (`identity/psid_hash.py`,
`models/attribution_context.py`, `attribution/resolver.py`, `funnel/funnel.py`, `funnel/models.py`,
`migrations/0013`, `migrations/0006`-comment) is carried from M6.2N unchanged. The B2/B3/B4 fix-logic files and the
A3/A4/B2/B3 fix logic inside the touched files are byte-identical / unchanged (per PLAN §3).

## 2. Verification (real code, this leg)

- **Full suite: 593 passed** (`PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider`), no skips, no
  regress.
- **B1 leg 1 / SMK-026**: `grep app/` for a raw `.psid` field / `["psid"]` key (excl `psid_hash`) ⇒ **NONE**;
  `as_stored()` / `to_public()` carry only `psid_hash`; the hash is one-way (pepper as HMAC key) + deterministic +
  collision-sensitive; `resolve_pepper(production=True)` with the env unset **raises** `PsidHashPolicyError`; the
  only pepper literal is the labelled non-secret dev mock (RULE-014 / FAIL-008 satisfied; **no raw PSID/pepper**).
- **F2-6 leg 2 / SMK-027**: `pack_assembler._smokes` coerces every provided object to a canonical `SmokeResult`
  (`getattr(provided,…)` present at :167); only `_smokes` changed (no `_ref_valid`/`_ref_binding`/`_categories`/
  `standing_floor_ok` touched — B2/B3 intact); `models.py` unchanged.
- **Posture**: `config.py` sha256 identical to M6.2M; migrations `0001–0013` (0013 the only add; 0006 comment-only).

## 3. Delta vs PLAN.md (documented, honest)

PLAN.md (M6-P2301) cited the suite at **584 passed**; the current tree reports **593** (+9). The delta is **three
official verification artifacts that landed in the tree from the downstream/verify roles** (NOT coder code — the app
code is unchanged, §1) and are all green:

| Added test file | Owner leg | What it verifies | Tests |
|---|---|---|---|
| `tests/smoke/test_b1_psid_hash_smoke.py` | TESTER (SMK-026) | no-raw-in-store · one-way+prefix+deterministic+collision-sensitive · fail-closed production · non-vacuity | 4 |
| `tests/smoke/test_f2_6_duck_recorded_coerced.py` | TESTER (SMK-027) | lying-duck `.recorded` ignored → NOT_READY; isolating flip; non-vacuity control | 3 |
| `tests/test_no_http_client_import.py` | SECURITY_PII / OD-011 sign-off (d) | AST import-scan gate: `app/` imports no HTTP/egress client (RULE-004; keeps egress outbox-worker-only after the OD-011 bind) | 2 |

These are the **TESTER (M6-P2303/2304)** official smokes for SMK-026/027 and the **security/OD-011** import gate —
this coder RECORD leg neither authored nor owns them; it reports their presence + green status accurately. They use
synthetic, runtime-assembled ids (no literal PII), and add no raw psid/pepper. The coder's own regressions
(`tests/test_b1_psid_hash.py`, `tests/test_duck_smoke_recorded.py`) remain and pass.

## 4. Acceptance checklist (all confirmed)

- [x] implementation matches the plan (RECORD leg — no re-implementation); the **delta** (+9 tests = the 3 official
  TESTER/security artifacts) is documented (§3).
- [x] fail-closed branches present: B1 (pepper unset in production → `PsidHashPolicyError`; None/blank psid → None);
  F2-6 (`_smokes` recomputes `recorded` → NOT_READY on a lying duck); consent/registry/dedup fail-closed branches are
  carried from M6.2K..M6.2M **unchanged** (no B1/F2-6 change touches them).
- [x] implementation target manifest is **LOCKED** (M6-OD-011 DECIDED).
- [x] `files_changed` all under `04-artifacts/impl/M6.2O/` (this record leg wrote only `IMPLEMENTATION_NOTES.md`).
- [x] existing conventions/test patterns reused (the shipped B1/F2-6 code; no new pattern introduced by this leg).

## 5. Hard forward condition (carried from PLAN §0 / the entry judge)

**M6-OD-003** (privacy/legal hash-policy review) must be **DECIDED before any REAL psid_hash deploy/send/join** (real
pepper provisioning, the cross-module `psid_hash` join C7, or external send of hashed data). The in-scope B1 is
internal PII-minimization only (`external_send` immutably OFF); the exit judge **M6-P2309** must scrutinize whether
the internal HMAC/pepper scheme itself needs M6-OD-003 sign-off before B1 is deemed closed. C7 invariant recorded in
[INVARIANTS_M5_RUNTIME_CONTROLS.md](INVARIANTS_M5_RUNTIME_CONTROLS.md).

## 6. Rollback

Staged only — baseline rollback = delete the `04-artifacts/impl/M6.2O/` tree (M6.2N + M6.2M untouched). Per item:
the [PLAN.md](PLAN.md) §2 tables (B1 files → revert/delete; F2-6 `_smokes` → revert; the coder test → delete). This
record leg's own rollback = revert `IMPLEMENTATION_NOTES.md`. No live migration to unwind (`live_migrations=false`).
Every code change is a privacy tightening (B1) or a fail-closed tightening (F2-6); a revert is a deliberate
regression, not a routine undo.
