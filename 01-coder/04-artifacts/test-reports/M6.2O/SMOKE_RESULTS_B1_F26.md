# SMOKE_RESULTS — Slice M6.2O — B1 (psid_hash) + F2-6 (duck-coerce) official smokes + SMK-013 re-bless

| Field | Value |
|---|---|
| Task | Operator-directed (owner, free-form) — **build + run** 2 official smokes (B1, F2-6) + **re-bless** 2 stale SMK-013 smokes |
| Role / agent | TESTER / m6-tester |
| Mode | **test** (build **and** run in one pass, per the operator instruction) |
| Governance framing | **Out-of-band**: M6.2N/M6.2O have **no ledger row / slice-spec** (last ledger row is M6-P2209, M6.2M judge SIGNED; last RUNNING was M6-P2202). This matches the coder's own M6.2O `IMPLEMENTATION_NOTES.md`. Tests-only under `04-artifacts/impl/M6.2O/tests/`; **no app code changed**, no `00-spec/` or `04-artifacts/state/` touched, no flag flipped. |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0**, run `-B` (`PYTHONDONTWRITEBYTECODE=1`), `-p no:cacheprovider` |
| Baseline (before) | **584 passed, 0 failed, RC 0** (measured before authoring) |
| After (full suite) | **591 passed, 0 failed, 0 skipped, 0 error — RC 0** (delta **+7** = B1 4 + F2-6 3; SMK-013 re-bless kept its node count) |
| Overall | **all target smokes PASS; no regression (591 ≥ 584); nothing patched; no assertion loosened/skipped** |

> **Governance (immutable — nothing here flips a flag):** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
> `external_send=OFF`, all scale/hash/learning flags `False`, `live_migrations=false`. The B1 fail-closed test injects
> `production=True` as a **call argument** (the code supports it) — the immutable `config.PRODUCTION_FLAG` is NOT
> flipped (asserted still `OFF`). No pepper or raw psid appears in any test, log, or this report (RULE-014 / FAIL-008).
> `status` is an honest TESTER self-report; per RULE-015 the runner gate + JUDGE decide.

## Task 1 — official smokes (build + run)

The `correlation_id` / `evidence_id` are **synthetic** doc-§22-style trace ids for this report, shown export-masked
(`abc***xy`); raw synthetic values `corr_2o_*` / `ev_2o_*`.

| Smoke | Audit item | Test file (`tests/smoke/…`) | Nodes | Result | correlation_id (masked) | evidence_id (masked) |
|---|---|---|---|---|---|---|
| B1 psid_hash | B1 / M6-OD-003 (M5 PSID policy) | `test_b1_psid_hash_smoke.py` | 4 | **PASS** | `cor***b1` | `ev_***b1` |
| F2-6 duck-coerce | F2-6 (evidence-pack, code-exec-only) | `test_f2_6_duck_recorded_coerced.py` | 3 | **PASS** | `cor***26` | `ev_***26` |

**B1 nodes (4/4 PASS):**
- `test_b1_no_raw_psid_in_store` (a) — a raw PSID at the resolve seam is one-way hashed; `as_stored()` carries
  `psid_hash:…`, no raw-psid key, and `_PSID not in str(as_stored())`.
- `test_b1_hash_is_one_way_prefixed_deterministic_collision_sensitive` (b) — `psid_hash:`-prefixed; output ≠ input
  and raw not in the hash (one-way); deterministic for the same pepper; distinct psids → distinct hashes.
- `test_b1_fail_closed_production_without_pepper_raises` (c) — with `production=True` injected AND the pepper env
  removed (`monkeypatch.delenv`), `resolve_pepper` and `hash_psid` raise `PsidHashPolicyError`; `config.PRODUCTION_FLAG`
  asserted still `OFF` (no flag flipped).
- `test_b1_none_or_blank_psid_is_none` (d) — `hash_psid(None/""/"   ")` → None; a context with no psid signal has
  `psid_hash is None` (the hash appears only for a real psid).

**F2-6 nodes (3/3 PASS):**
- `test_f2_6_duck_recorded_is_not_trusted_mandatory_smoke_unrecorded` (primary) — a duck
  `SimpleNamespace(recorded=True, status/correlation_id/evidence_id=None)` for mandatory owner smoke M6-SMK-001 is
  coerced to a canonical `SmokeResult`; `recorded` is recomputed False; gap `UNRUN:M6-SMK-001`; readiness `NOT_READY`.
- `test_f2_6_duck_alone_flips_readiness_when_all_others_recorded` (isolation, non-vacuous) — every other of the 18
  smokes genuinely recorded, only M6-SMK-001 ducked → readiness still flips to `NOT_READY`.
- `test_f2_6_control_genuine_smoke_results_still_record` (control) — the honest set still records all → `OWNER_REVIEW_REQUIRED`.

## Task 2 — re-bless 2 stale SMK-013 smokes (rename / docstring only; assertions unchanged)

| File | Change | Nodes | Result |
|---|---|---|---|
| `tests/smoke/test_smk_013_live_chain_trace.py` | renamed `…neg_psid_is_masked_on_export_but_kept_durably` → `…neg_psid_hashed_no_raw_on_any_surface`; module docstring + the function note updated from "durable keeps raw / export masks" → "raw PSID never stored; durable + export both one-way `psid_hash`". **All assertions unchanged.** | 4 | **PASS** |
| `tests/smoke/test_smk_013_funnel_live_chain_trace.py` | module docstring "masked on export" → "one-way `psid_hash`"; function note re-blessed. **All chain-trace assertions unchanged** (function name kept, per instruction). | 4 | **PASS** |

Confirmed by isolated run: the renamed node `test_smk_013_neg_psid_hashed_no_raw_on_any_surface` is collected and the
old name is gone; both files still 4/4. These assertions were already correct + strong for the B1 contract (they
assert `psid_hash:` prefix + `_PSID not in str(export)` "no raw psid on any surface") — only the name/doc lagged the
new contract, so this is a pure re-bless (no assertion added, removed, weakened, or skipped).

## Commands run (from `04-artifacts/impl/M6.2O/`, no shell redirection, cache-free)

```bash
# baseline BEFORE authoring
python.exe -B -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider'])>"   # 584 passed, RC 0

# full suite AFTER (2 new smokes + SMK-013 re-bless)
python.exe -B -c "<tally + per-file breakdown; pytest.main(['-p','no:cacheprovider'])>"        # 591 passed, RC 0, delta +7
#   per-file: test_b1_psid_hash_smoke 4/4 ; test_f2_6_duck_recorded_coerced 3/3 ; test_smk_013_live_chain_trace 4/4 ; test_smk_013_funnel_live_chain_trace 4/4

# isolated cross-check of the 4 target files
python.exe -B -c "<tally + node names; pytest.main([the 4 files, '-p','no:cacheprovider'])>"   # 15 passed, RC 0 ; renamed node present, old gone
```

> **Counting note.** pytest's terminal summary is not reliably captured here, so counts come from an in-process
> `pytest_runtest_logreport` tally with pytest stdout swallowed (`redirect_stdout`); `pytest.main() RC=0`.

## Incident + fix (honest record)

The B1 smoke was first written as `tests/smoke/test_b1_psid_hash.py`, which shares a **basename** with the coder's
pre-existing `tests/test_b1_psid_hash.py`. With no `__init__.py` (prepend import mode) pytest raised a **collection
error** on the full tree (RC 2, 0 tests). Fix: renamed the smoke to a unique basename
`tests/smoke/test_b1_psid_hash_smoke.py` and removed the colliding duplicate. Re-run: RC 0, 591 passed. (F2-6's
basename was already unique vs the coder's `tests/test_duck_smoke_recorded.py`.)

## Boundary / safety observed

- **No raw PII / secret:** psid markers are synthetic + runtime-assembled; no pepper or raw psid in any test, log, or
  this report; B1 asserts the raw psid reaches no durable/export surface (RULE-014 / FAIL-008).
- **No flag flip:** `production=True` is a call argument only; `config.PRODUCTION_FLAG` asserted `OFF`; posture
  BLOCKED/OFF/OFF unchanged.
- **Tests-only:** only files under `04-artifacts/impl/M6.2O/tests/smoke/` were created/edited; **no app code**, no
  migration, no `00-spec/` or `04-artifacts/state/` write, no self-cert.
- **No make-green:** no assertion was loosened, skipped, or deleted; every result is a real executed PASS. Had any
  failed, this would be reported BLOCKED (none did).
