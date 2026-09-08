# TEST_MANIFEST — Slice M6.2O smoke suite (out-of-band backfill: psid_hash B1 + duck-coerce F2-6)

| Field | Value |
|---|---|
| Prompt | M6-P2303 — `M6_2O_TESTER_BUILD` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — the M6.2O official smoke legs are FORMALIZED here (docstrings promoted to the SMK-026/027 register identity + verbatim scenario/expected; assertions unchanged). This attempt ran a **collect-only build-validation** (imports/collects clean, no assertions executed) per "Build (do not yet run)"; the **formal executed-results recording** belongs to M6-P2304. |
| Executed by (formal) | M6-P2304 (`M6_2O_TESTER_RUN`) → `04-artifacts/test-reports/M6.2O/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-026, M6-SMK-027** (2 `proposed — HARDENING, owner review`; per `00-spec/slices/M6.2O.md` "Core smokes" + this prompt's `<smoke_ids>`) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Slice scope | Retroactive ledger/judge certification of two out-of-band, off-ledger changes ALREADY SHIPPED in `04-artifacts/impl/M6.2O/`: **B1** (raw psid → one-way `psid_hash`, per M5 PSID policy) landed in impl/M6.2N; **F2-6** (`_smokes` coerces any smoke object to a canonical `SmokeResult`, never trusting a caller `.recorded`) landed in impl/M6.2O. This slice certifies the existing impl by regression smoke — **no new features, no re-implementation**. |
| Staging root | `04-artifacts/impl/M6.2O/` (STAGED_ONLY; cumulative superset of M6.2M) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (proposed additions rows M6-SMK-026/027) + `00-spec/slices/M6.2O.md` |

> **Governance (immutable — nothing in this suite flips a flag; this slice certifies existing code):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all scale/hash/learning flags `False`,
> `live_migrations=false`. No application code changed by the TESTER (docstring-only formalization of already-shipped
> tests). The B1 fail-closed leg injects `production=True` as a **call argument** — the immutable `PRODUCTION_FLAG`
> is NOT flipped (asserted still `OFF`). No pepper or raw psid anywhere (RULE-014 / FAIL-008). `M6-P1000` / `M6-P1309`
> stay BLOCKED. **HARD FORWARD CONDITION** (per entry judge / coder record): M6-OD-003 (privacy/legal hash policy)
> must be DECIDED before any REAL psid_hash deploy/send/join, and the exit judge M6-P2309 scrutinizes whether the
> internal HMAC/pepper scheme itself needs M6-OD-003 sign-off before B1 is deemed closed. `status` is an honest
> TESTER self-report; the runner EVIDENCE_GATE + slice Judge (M6-P2309) decide closure.

## What this suite is

Two **official smoke legs**, one per new smoke id, each carrying the register scenario/expected **verbatim** and
proving one shipped out-of-band fix through the frozen M6.2O code. These files were first authored out-of-band and
are **recorded by the coder's M6-P2302 record leg as the official SMK-026/027 smokes**; this BUILD leg formalizes
them (register identity + verbatim scenario/expected in the docstring) — no assertion added, removed, or changed.
They **coexist with the coder's regression tests** (`tests/test_b1_psid_hash.py`, `tests/test_duck_smoke_recorded.py`)
and reuse the shared [`tests/conftest.py`](04-artifacts/impl/M6.2O/tests/conftest.py) fixtures. **No production code**
and **no fix to the code under test**. All ids are synthetic + runtime-assembled; no raw secret/PII.

## Smoke → test binding (scenario/expected verbatim from SMOKE_REGISTER)

| Smoke ID | Fix | Test file (`tests/smoke/…`) | Nodes | Primary (scenario verbatim) | Negatives / control | Rule(s) | Fail gate | Exit leg |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-026 | B1 psid_hash | `test_b1_psid_hash_smoke.py` | 4 | `test_b1_no_raw_psid_in_store` | `..._hash_is_one_way_prefixed_deterministic_collision_sensitive`, `..._fail_closed_production_without_pepper_raises`, `..._none_or_blank_psid_is_none` | M6-RULE-014, M6-RULE-009 | M6-FAIL-008 | 1 / 3 |
| M6-SMK-027 | F2-6 duck-coerce | `test_f2_6_duck_recorded_coerced.py` | 3 | `test_f2_6_duck_recorded_is_not_trusted_mandatory_smoke_unrecorded` | `..._duck_alone_flips_readiness_when_all_others_recorded`, `..._control_genuine_smoke_results_still_record` | M6-RULE-015 | M6-FAIL-007 | 2 / 4 |

**New M6.2O official-smoke nodes: 7 (4 + 3).** (These 7 are already present + green in the tree; this leg formalizes
their identity/docstrings — the node count is unchanged.)

## Per-smoke summary (what each leg proves)

- **M6-SMK-026 (B1 psid_hash):** (a) a raw PSID at the resolve seam is one-way hashed — `as_stored()` carries only a
  `psid_hash:` HMAC value and NEVER the raw psid (`_PSID not in str(as_stored())`, no raw-psid key); (b) the hash is
  `psid_hash:`-prefixed, one-way (output ≠ input, raw not in the hash), deterministic per pepper, and
  collision-sensitive (distinct psids → distinct hashes); (c) fail-closed — `production=True` (injected as a call arg)
  + pepper env unset → `PsidHashPolicyError` (immutable `PRODUCTION_FLAG` untouched, asserted `OFF`); (d) non-vacuity —
  None/blank psid → None, and a no-psid-signal context has `psid_hash is None`.
- **M6-SMK-027 (F2-6 duck-coerce):** `EvidencePackAssembler._smokes` coerces every provided smoke object into a
  canonical frozen `SmokeResult` from its FIELDS, so a duck `SimpleNamespace(recorded=True, status/correlation_id/
  evidence_id=None)` for a MANDATORY owner smoke has `recorded` RECOMPUTED False → UNRUN_SMOKE gap → pack NOT_READY
  (the caller's fake `.recorded` is never trusted). Isolation (only the duck) still flips readiness; a genuine set
  still records (OWNER_REVIEW_REQUIRED).

## Fixtures reused (from `tests/conftest.py`) + APIs under test

| Fixture / API | Role |
|---|---|
| `make_measurement_event`, `make_conversion`, `attribution_resolver` | drive the B1 resolve seam (`signals["psid"]` → `ctx.psid_hash`) |
| `app.measurement.identity.psid_hash` (`hash_psid`, `resolve_pepper`, `PsidHashPolicyError`, `HASH_PREFIX`, `PEPPER_ENV`) | the B1 one-way HMAC hash + fail-closed pepper policy |
| `evidence_assembler`, `full_evidence_refs`, `all_smokes_recorded` | assemble the pack for the F2-6 duck-coerce leg |
| `app.measurement.evidence.models` (`SmokeResult`, `GapKind`, `Readiness`) + `pack_assembler._smokes` | the F2-6 canonical-coercion under test |
| `monkeypatch` (pytest builtin) | remove the pepper env for the fail-closed leg — test-only, no persistent env mutation, no app-code/flag change |

## Boundary / safety asserted by the suite

- **No raw PII / secret (RULE-014 / FAIL-008):** the raw PSID reaches no durable/export surface; psid markers are
  synthetic + runtime-assembled; no pepper or raw psid in any test, log, or report.
- **No overstated readiness / no trusted foreign `.recorded` (RULE-015 / FAIL-007):** a lying duck cannot mark a
  mandatory smoke recorded; the pack fails closed to NOT_READY.
- **No flag flip:** `production=True` is a call argument only; `config.PRODUCTION_FLAG` asserted `OFF`; posture
  BLOCKED/OFF/OFF unchanged.
- **No fix to code under test; no application code / migration / external call / flag flip / `04-artifacts/state/`
  write** by the TESTER. M6-P1000 / M6-P1309 stay BLOCKED.

## Build-validation performed in M6-P2303 (attempt 1, collect-only — "do not yet run")

Per the prompt's `<task>` ("Build (do not yet run)"), this attempt ran **collect-only** (imports + collects; **no
assertions executed**). Run with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest 8.4.2**, from
`04-artifacts/impl/M6.2O/`, **no shell redirection** (the role guard blocks a `>`/`2>` co-occurring with the venv
`Scripts` path), cache-free (`-B` / `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```bash
python.exe -B -c "<in-process pytest_collection_finish tally; pytest.main(['--collect-only','-q','-p','no:cacheprovider'])>"
#   -> RC 0 ; the 2 SMK files collect 4 + 3 = 7 nodes ; full-suite collect clean ; 0 collection errors
```

The docstring-only formalization does not change collection; a re-collect confirms 4 + 3 = 7 nodes and the full suite
collects clean (no duplicate-basename collision — the smoke filenames are unique vs the coder's `tests/*` regressions).
A read-only **adversarial static verification** (2 logic verifiers + a verbatim-string auditor + a
completeness/PII/boundary critic) was run alongside — findings recorded in the M6-P2303 evidence.

> **This build does NOT self-certify gate advancement.** Collect-only proves the smoke files import + collect against
> the frozen M6.2O code; it does not execute assertions. The **formal executed-results recording** (with a
> correlation_id + evidence_id per smoke) is produced by **M6-P2304**. The runner EVIDENCE_GATE + slice Judge decide.

## Execution plan for M6-P2304 (`M6_2O_TESTER_RUN`)

Run the full staged suite and the 2 SMK legs, then record per-smoke PASS/FAIL/BLOCKED + detail + correlation_id +
evidence_id:

```bash
python -m pytest -q                                                                   # full staged suite
python -m pytest -q tests/smoke/test_b1_psid_hash_smoke.py tests/smoke/test_f2_6_duck_recorded_coerced.py   # expected 7 passed
```

For SMK-026 (c), the fail-closed leg injects `production=True` as a call argument and removes the pepper env via
`monkeypatch` — the immutable `PRODUCTION_FLAG` is not flipped.

## Exit-gate legs (slice M6.2O done-gate, itemized)

| Leg | Requirement | Covered by |
|---|---|---|
| 1 | psid_hash (B1) — no raw psid on any surface; one-way/deterministic/collision-sensitive; production+no-pepper fail-closed | SMK-026 leg (formalized here) + coder `tests/test_b1_psid_hash.py`; run by M6-P2304 |
| 2 | duck-coerce (F2-6) — `_smokes` coerces to canonical SmokeResult; fake `.recorded` never trusted | SMK-027 leg (formalized here) + coder `tests/test_duck_smoke_recorded.py`; run by M6-P2304 |
| 3–4 | Proposed smoke M6-SMK-026 / 027 executed OR owner-waived | the 2 legs; executed by M6-P2304 |
| 5 | All slice prompts have schema-valid evidence JSON | this evidence + downstream |
| 6 | Slice gate judge sign-off PASS | M6-P2309 (downstream; also scrutinizes M6-OD-003 vs the internal HMAC/pepper scheme) |
| 7 | Rollback steps documented | docstring-only formalization → revert the docstrings (assertions/code untouched); the shipped B1/F2-6 code rollback is per impl PLAN.md |

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-009 / M6-RULE-014 | No raw PII; psid is one-way `psid_hash`, never raw, on any durable/export surface (SMK-026). |
| M6-RULE-015 | No self-certification; a caller-supplied `.recorded` is never trusted (SMK-027). |
| M6-FAIL-007 | No evidence → called PASS — a lying duck stays un-recorded → NOT_READY (SMK-027 guard). |
| M6-FAIL-008 | Raw PII exposure — a raw psid must never reach a durable/export surface; production fail-closes without a pepper (SMK-026 guard). |

## Provenance / notes

- Scenario & expected text quoted **verbatim** from `00-spec/registers/SMOKE_REGISTER.md` (proposed additions rows
  M6-SMK-026/027; derivation: out-of-band B1 / F2-6, chief-auditor 2026-09-07 item B4). Test patterns reused from the
  coder's M6.2N/M6.2O tests + the shared conftest fixtures (doc working mode, extract line 466).
- **Rollback:** this BUILD leg made docstring-only edits to two already-shipped smoke files → revert the docstrings;
  no production code, no migration, no flag flipped. The B1/F2-6 shipped-code rollback is in the impl `PLAN.md`.
- No self-certification of PASS or of gate/leg advancement: the runner EVIDENCE_GATE and the slice Judge decide. This
  manifest and the 2 formalized smoke legs are the *build*; the formal executed results are produced in M6-P2304.
