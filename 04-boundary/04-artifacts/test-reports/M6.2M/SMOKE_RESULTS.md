# SMOKE_RESULTS — Slice M6.2M (evidence authenticity, M6-OD-013 twin)

| Field | Value |
|---|---|
| Prompt | M6-P2204 — `M6_2M_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test** — the M6.2M smoke suite is EXECUTED here and results recorded. Smoke legs were authored in M6-P2203 (`M6_2M_TESTER_BUILD`). |
| Smoke ids executed | **M6-SMK-024, M6-SMK-025** (2 `proposed — HARDENING, owner review`; executed here, not owner-waived) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Staging root | `04-artifacts/impl/M6.2M/` (STAGED_ONLY; convention reference, not a live repo) |
| Evidence-leg result | **7 passed, 0 failed — exit 0** (3 + 4) |
| Full staged suite | **575 passed, 0 failed, 0 skipped, 0 error — RC 0** |
| Overall | **both bound smoke ids PASS; no failures; nothing patched; the M6-OD-013 authenticity twin proven by regression** |

> **Governance (immutable — nothing in this run flips a flag; this slice only proves the authenticity mechanism):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all scale/hash/learning flags `False`,
> `live_migrations=false`. No application code changed by the TESTER, no migration, no external call, no flag flipped,
> no ROAS Pass / Scale Ready declared. The evidence pack still tops at `OWNER_REVIEW_REQUIRED` and carries the 8
> standing blockers; `M6-P1000` / `M6-P1309` stay BLOCKED. The authenticity mechanism is proven with a **staged**
> `known_refs` allowlist — the real issued-refs registry stays owner-populated (integration step). `status` is an
> honest TESTER self-report; the runner EVIDENCE_GATE and the slice Judge (M6-P2209) decide closure.

## Per-smoke results (scenario / expected verbatim from SMOKE_REGISTER; all PASS)

The `correlation_id` / `evidence_id` per smoke are **synthetic** trace ids for the doc §22 Smoke Report, shown in
their **export-masked** form (`app.measurement.masking.mask`, RULE-014/H02); the raw synthetic value is
`corr_2m_0NN` / `ev_2m_0NN`.

| Smoke ID | Twin side | Test file (`tests/smoke/…`) | Nodes | Result | correlation_id (masked) | evidence_id (masked) | Scenario → Expected (verbatim) |
|---|---|---|---|---|---|---|---|
| M6-SMK-024 | M6-OD-013 ref-side | `test_smk_024_ref_authenticity_allowlist.py` | 3 | **PASS** | `cor***24` | `ev_***24` | "Evidence pack assembled with a known-refs allowlist + a ref that is shape-valid, uniquely used, correctly (category,key)-bound, but NOT in the allowlist (canonical-string reconstruction)" → "that category reads MISSING (authenticity, not just slot-correctness); with no allowlist the M6.2L slot-correctness bar still holds (no regression)" |
| M6-SMK-025 | M6-OD-013 smoke-side | `test_smk_025_smoke_result_authenticity.py` | 4 | **PASS** | `cor***25` | `ev_***25` | "SmokeResult for a mandatory owner smoke carries whitespace / fake-but-nonblank status/correlation_id/evidence_id" → "recorded() is False (stripped-non-blank required, not raw truthiness); the mandatory smoke stays un-recorded → pack NOT_READY" |

**Evidence-leg nodes: 7 (3 + 4), all PASSED.**

### M6-SMK-024 — ref-side authenticity (M6-OD-013) · **PASS (3/3)**

- `test_smk_024_reconstructed_canonical_ref_not_issued_is_missing` (primary) — PASS: with a staged allowlist that
  omits the DEDUP target slot's ref, the correctly-reconstructed canonical ref is REJECTED → DEDUP category MISSING,
  all issued-ref categories COMPLETE, pack NOT_READY (authenticity beyond slot-correctness).
- `test_smk_024_neg_no_allowlist_keeps_slot_correctness_no_regression` — PASS: with no allowlist the honest refs are
  all COMPLETE → OWNER_REVIEW_REQUIRED (the check is opt-in; no regression).
- `test_smk_024_control_fully_issued_allowlist_all_complete` — PASS: a fully-issued allowlist → all COMPLETE
  (discriminating: a category is COMPLETE iff its ref is issued).

### M6-SMK-025 — smoke-side twin (M6-OD-013) · **PASS (4/4)**

- `test_smk_025_whitespace_mandatory_smoke_is_unrecorded_and_not_ready` (primary) — PASS: a whitespace/fake-but-nonblank
  `SmokeResult` for mandatory owner smoke M6-SMK-001 → `recorded()` False, pack NOT_READY, UNRUN_SMOKE gap carries its
  id.
- `test_smk_025_neg_recorded_requires_stripped_non_blank_not_raw_truthiness` — PASS: whitespace fields (each truthy,
  `bool("  ")` True) → recorded False; a genuine trace → recorded True (authenticity, not raw truthiness).
- `test_smk_025_neg_assembler_normalizes_whitespace_fields_to_none` — PASS: `_smokes` normalizes whitespace-only
  fields to None → nothing masquerades on export (`to_public` status None + recorded False).
- `test_smk_025_control_genuine_recorded_smokes_all_record` — PASS: the honest set still records every smoke →
  OWNER_REVIEW_REQUIRED (non-vacuous).

## Supporting / regression coverage (inside the 575 full suite, all green)

The full staged suite re-ran green: the coder's M6.2M regression tests (`tests/test_m6_2m_ref_authenticity.py`,
`tests/test_m6_2m_smoke_authenticity.py`), the carried M6.2A–L tree, and the evidence-pack + 18-P0-smoke suite. Full
total **575 passed, 0 failed** (= carried + coder M6.2M baseline 568 + the 7 new official-smoke nodes).

## Commands run (from `04-artifacts/impl/M6.2M/`, no shell redirection, cache-free)

The role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path, so no redirection is used;
`PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider` keep the run cache-free.

```bash
# 1) full staged suite + per-smoke tally, counted in-process via pytest_runtest_logreport
python.exe -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider']); pytest stdout swallowed>"
#   -> RC 0 ; COUNTS passed=575 failed=0 skipped=0 error=0 ; FAILS [] ; each evidence leg pass=(3,4) fail=0

# 2) the 2 evidence legs isolated (cross-check)
python.exe -c "<tally; pytest.main([the 2 tests/smoke/test_smk_024..025 files, '-p','no:cacheprovider'])>"
#   -> RC 0 ; SUBSET passed=7 failed=0 skipped=0 error=0 ; FAILS []
```

> **On counting.** pytest's terminal summary is not reliably captured in this harness, so the full-suite total
> (**575**) and the per-smoke breakdown came from an in-process `pytest_runtest_logreport` tally
> (`passed=575, failed=0, skipped=0, error=0`) with `pytest.main() RC=0`; the isolated 2-leg run independently
> confirms `7 passed`. pytest's own per-item output was swallowed (`redirect_stdout`) so the tally prints cleanly.

Cache hygiene: `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

## Boundary / safety observed during this run

- **Authenticity, not shape/truthiness alone (M6-OD-013 / RULE-015 / FAIL-007):** a not-issued canonical ref (024)
  and a whitespace SmokeResult (025) both fail closed → NOT_READY; the pack cannot be authenticated by shape alone.
- **Opt-in, no regression:** without an allowlist / with genuine results the honest path still completes
  (OWNER_REVIEW_REQUIRED).
- **PII-safe (RULE-014):** all refs/ids are synthetic governance values; correlation/evidence ids masked on export.
- **No fix to code under test:** all 575 passed, so nothing needed reporting as a failure, and nothing was patched.
  No application code / migration / external call / flag flip / `04-artifacts/state/` write occurred.

## Exit-gate legs closed by this run (slice M6.2M done-gate)

| Leg | Requirement | Status |
|---|---|---|
| 1 | Ref authenticity (M6-OD-013 ref-side) | met — SMK-024 + coder `test_m6_2m_ref_authenticity` green |
| 2 | Smoke authenticity (M6-OD-013 smoke-side twin) | met — SMK-025 + coder `test_m6_2m_smoke_authenticity` green |
| 3 | Proposed smoke M6-SMK-024 executed | **PASS** (3/3) — executed |
| 4 | Proposed smoke M6-SMK-025 executed | **PASS** (4/4) — executed |

> This run does NOT self-certify gate advancement (M6-RULE-015). It is the honest executed-results record of the
> TESTER. The runner EVIDENCE_GATE and the slice Judge (M6-P2209) decide closure; M6-P2205 (boundary adversary),
> M6-P2206 (security/PII), and the PM evidence-collect M6-P2207 come next. Posture stays BLOCKED/OFF/OFF.
