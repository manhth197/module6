# SMOKE_RESULTS — Slice M6.2O (out-of-band backfill: psid_hash B1 + duck-coerce F2-6)

| Field | Value |
|---|---|
| Prompt | M6-P2304 — `M6_2O_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test** — the M6.2O smoke suite is EXECUTED here and results recorded. Smoke legs were formalized in M6-P2303 (`M6_2O_TESTER_BUILD`). |
| Smoke ids executed | **M6-SMK-026, M6-SMK-027** (2 `proposed — HARDENING, owner review`; executed here, not owner-waived) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0**, run `-B` (`PYTHONDONTWRITEBYTECODE=1`), `-p no:cacheprovider` |
| Staging root | `04-artifacts/impl/M6.2O/` (STAGED_ONLY; cumulative superset of M6.2M; certifies the existing out-of-band impl) |
| Evidence-leg result | **7 passed, 0 failed — exit 0** (4 + 3) |
| Full staged suite | **593 passed, 0 failed, 0 skipped, 0 error — RC 0** |
| Overall | **both bound smoke ids PASS; no failures; nothing patched; the two out-of-band fixes proven by regression** |

> **Governance (immutable — nothing in this run flips a flag; this slice certifies existing code):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all scale/hash/learning flags `False`,
> `live_migrations=false`. No application code changed by the TESTER, no migration, no external call, no flag flipped,
> no ROAS Pass / Scale Ready declared. The B1 fail-closed leg injects `production=True` as a **call argument** and
> removes the pepper env via `monkeypatch` (test-scoped) — the immutable `PRODUCTION_FLAG` is NOT flipped (asserted
> still `OFF`). No pepper or raw psid anywhere (RULE-014 / FAIL-008). `M6-P1000` / `M6-P1309` stay BLOCKED.
> **HARD FORWARD CONDITION** (disclosed, not resolved here): M6-OD-003 (privacy/legal hash policy) must be DECIDED
> before any REAL psid_hash deploy/send/join; the exit judge M6-P2309 scrutinizes whether the internal HMAC/pepper
> scheme itself needs M6-OD-003 sign-off before B1 is deemed closed. `status` is an honest TESTER self-report; the
> runner EVIDENCE_GATE + slice Judge (M6-P2309) decide closure.

## Per-smoke results (scenario / expected verbatim from SMOKE_REGISTER; all PASS)

The `correlation_id` / `evidence_id` per smoke are **synthetic** doc-§22-style trace ids, shown export-masked
(`app.measurement.masking.mask`, RULE-014/H02); raw synthetic values `corr_2o_0NN` / `ev_2o_0NN`.

| Smoke ID | Fix | Test file (`tests/smoke/…`) | Nodes | Result | correlation_id (masked) | evidence_id (masked) | Scenario → Expected (verbatim) |
|---|---|---|---|---|---|---|---|
| M6-SMK-026 | B1 psid_hash | `test_b1_psid_hash_smoke.py` | 4 | **PASS** | `cor***26` | `ev_***26` | "A raw PSID supplied at the resolve seam is stored/exported (B1 psid_hash)" → "no raw psid on any durable/export surface — as_stored() carries only a one-way `psid_hash:` HMAC value (deterministic per pepper, collision-sensitive); production with the pepper env unset fails closed (PsidHashPolicyError)" |
| M6-SMK-027 | F2-6 duck-coerce | `test_f2_6_duck_recorded_coerced.py` | 3 | **PASS** | `cor***27` | `ev_***27` | "A duck smoke object with a fake .recorded=True + blank status/correlation_id/evidence_id for a mandatory owner smoke (F2-6)" → "_smokes coerces it to a canonical SmokeResult, recomputes recorded=False → UNRUN_SMOKE gap → pack NOT_READY (caller .recorded never trusted)" |

**Evidence-leg nodes: 7 (4 + 3), all PASSED.**

### M6-SMK-026 — B1 psid_hash · **PASS (4/4)**

- `test_b1_no_raw_psid_in_store` (primary) — PASS: a raw PSID at the resolve seam is one-way hashed; `as_stored()`
  carries `psid_hash:…`, no raw-psid key, and `_PSID not in str(as_stored())`.
- `test_b1_hash_is_one_way_prefixed_deterministic_collision_sensitive` — PASS: `psid_hash:` prefix; output ≠ input
  and raw not in the hash (one-way); deterministic (same pepper); distinct psids → distinct hashes.
- `test_b1_fail_closed_production_without_pepper_raises` — PASS: `production=True` injected + pepper env removed
  (`monkeypatch.delenv`) → `resolve_pepper` and `hash_psid` raise `PsidHashPolicyError`; `config.PRODUCTION_FLAG`
  asserted still `OFF` (no flag flipped).
- `test_b1_none_or_blank_psid_is_none` — PASS: `hash_psid(None/""/"   ")` → None; a no-psid-signal context has
  `psid_hash is None`.

### M6-SMK-027 — F2-6 duck-coerce · **PASS (3/3)**

- `test_f2_6_duck_recorded_is_not_trusted_mandatory_smoke_unrecorded` (primary) — PASS: a duck
  `SimpleNamespace(recorded=True, None fields)` for mandatory owner smoke M6-SMK-001 is coerced to a canonical
  `SmokeResult`, `recorded` recomputed False → `UNRUN:M6-SMK-001` gap → readiness `NOT_READY`.
- `test_f2_6_duck_alone_flips_readiness_when_all_others_recorded` — PASS: only the duck among 18 → readiness still
  `NOT_READY` (isolation, non-vacuous).
- `test_f2_6_control_genuine_smoke_results_still_record` — PASS: the honest set still records all → `OWNER_REVIEW_REQUIRED`.

## Supporting / regression coverage (inside the 593 full suite, all green)

The full staged suite re-ran green: the coder's B1/F2-6 regression tests (`tests/test_b1_psid_hash.py`,
`tests/test_duck_smoke_recorded.py`), the SECURITY/OD-011 import-scan gate (`tests/test_no_http_client_import.py`),
the carried M6.2A–M tree, and the evidence-pack + P0-smoke suites. Full total **593 passed, 0 failed**.

## Commands run (from `04-artifacts/impl/M6.2O/`, no shell redirection, cache-free)

The role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path, so no redirection is used; `-B`
(`PYTHONDONTWRITEBYTECODE=1`) + `-p no:cacheprovider` keep the run cache-free.

```bash
# 1) full staged suite + per-smoke tally, counted in-process via pytest_runtest_logreport
python.exe -B -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider']); pytest stdout swallowed>"
#   -> RC 0 ; COUNTS passed=593 failed=0 skipped=0 error=0 ; FAILS [] ; SMK-026 4/4, SMK-027 3/3

# 2) the 2 evidence legs isolated (cross-check)
python.exe -B -c "<tally; pytest.main([the 2 tests/smoke files, '-p','no:cacheprovider'])>"
#   -> RC 0 ; SUBSET passed=7 failed=0 skipped=0 error=0 ; FAILS []
```

> **On counting.** pytest's terminal summary is not reliably captured in this harness, so the full-suite total
> (**593**) and the per-smoke breakdown came from an in-process `pytest_runtest_logreport` tally
> (`passed=593, failed=0, skipped=0, error=0`) with `pytest.main() RC=0`; the isolated 2-leg run independently
> confirms `7 passed`. pytest's own per-item output was swallowed (`redirect_stdout`).

Cache hygiene: `-B` / `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

## Boundary / safety observed during this run

- **No raw PII / secret (RULE-014 / FAIL-008):** the raw PSID reaches no durable/export surface (`as_stored()` carries
  only `psid_hash:`); psid markers synthetic + runtime-assembled; no pepper or raw psid in any test, log, or report.
- **No trusted foreign `.recorded` / no overstated readiness (RULE-015 / FAIL-007):** a lying duck cannot mark a
  mandatory smoke recorded; the pack fails closed to `NOT_READY`.
- **No flag flip:** `production=True` is a call argument only; `config.PRODUCTION_FLAG` asserted `OFF`; posture
  BLOCKED/OFF/OFF unchanged.
- **No fix to code under test:** all 593 passed, so nothing needed reporting as a failure, and nothing was patched.
  No application code / migration / external call / flag flip / `04-artifacts/state/` write occurred.

## Exit-gate legs closed by this run (slice M6.2O done-gate)

| Leg | Requirement | Status |
|---|---|---|
| 1 | psid_hash (B1) — no raw psid on any surface; one-way/deterministic/collision-sensitive; production+no-pepper fail-closed | met — SMK-026 + coder `tests/test_b1_psid_hash.py` green |
| 2 | duck-coerce (F2-6) — `_smokes` coerces to canonical SmokeResult; fake `.recorded` never trusted | met — SMK-027 + coder `tests/test_duck_smoke_recorded.py` green |
| 3 | Proposed smoke M6-SMK-026 executed | **PASS** (4/4) — executed |
| 4 | Proposed smoke M6-SMK-027 executed | **PASS** (3/3) — executed |

> This run does NOT self-certify gate advancement (RULE-015). It is the honest executed-results record of the TESTER.
> The runner EVIDENCE_GATE and the slice Judge (M6-P2309) decide closure; M6-P2305 (boundary), M6-P2306 (security/PII —
> owns the import gate + scrutinizes the psid_hash/pepper surface + M6-OD-003), and the PM evidence-collect M6-P2307
> come next. Posture stays BLOCKED/OFF/OFF; the M6-OD-003 hard forward condition remains open for the exit judge.
