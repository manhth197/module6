# TEST_MANIFEST — Slice M6.2M smoke suite (evidence authenticity, M6-OD-013 twin)

| Field | Value |
|---|---|
| Prompt | M6-P2203 — `M6_2M_TESTER_BUILD` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — the M6.2M official smoke legs are AUTHORED here. This attempt ran a **collect-only build-validation** (imports/collects clean, no assertions executed) per the prompt's "Build (do not yet run)"; the **formal executed-results recording** belongs to M6-P2204. |
| Executed by (formal) | M6-P2204 (`M6_2M_TESTER_RUN`) → `04-artifacts/test-reports/M6.2M/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-024, M6-SMK-025** (2 `proposed — HARDENING, owner review`; per `00-spec/slices/M6.2M.md` "Core smokes" + this prompt's `<smoke_ids>`) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Slice scope | Close the **M6-OD-013 authenticity residual** left open by M6.2L (B2): the **ref-side** canonical-string reconstruction (SMK-024) + the **smoke-side** SmokeResult truthiness twin (SMK-025), as a cumulative superset of M6.2L under `04-artifacts/impl/M6.2M/`. Authenticity is proven with a staged `known_refs` oracle + fail-closed `SmokeResult` validation; the real known-refs registry stays owner-populated. |
| Staging root | `04-artifacts/impl/M6.2M/` (STAGED_ONLY; convention reference, not a live repo) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (proposed additions rows M6-SMK-024/025) + `00-spec/slices/M6.2M.md` |

> **Governance (immutable — nothing in this suite flips a flag; this slice only proves the authenticity mechanism):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all scale/hash/learning flags `False`,
> `live_migrations=false`. No application code changed by the TESTER, no migration, no external call, no flag flipped,
> no ROAS Pass / Scale Ready declared. The evidence pack still tops at `OWNER_REVIEW_REQUIRED` and carries the 8
> standing blockers; `M6-P1000` / `M6-P1309` stay BLOCKED. `status` is an honest TESTER self-report; the runner
> EVIDENCE_GATE and the slice Judge (M6-P2209) decide closure.

## What this suite is

Two **official smoke legs**, one per new smoke id, each carrying the register scenario/expected **verbatim** and
proving one half of the M6-OD-013 authenticity twin ("vá cả hai một lượt" — patch both sides at once) through the
frozen M6.2M code. They **coexist with the coder's regression tests** (M6-P2202, `tests/test_m6_2m_ref_authenticity.py`
/ `test_m6_2m_smoke_authenticity.py`). They reuse the shared [`tests/conftest.py`](04-artifacts/impl/M6.2M/tests/conftest.py)
fixtures (`evidence_assembler`, `full_evidence_refs`, `all_smokes_recorded`) plus `SmokeResult` / `get_spec`
constructed inline. **No production code** and **no fix to the code under test** (TESTER reports defects, never fixes
them). All ids are synthetic governance refs; no raw secret/PII.

## Smoke → test binding (scenario/expected verbatim from SMOKE_REGISTER)

| Smoke ID | Twin side | New smoke leg (`tests/smoke/…`) | Nodes | Primary (scenario verbatim) | Negatives / control | Rule(s) | Fail gate | Exit leg |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-024 | M6-OD-013 ref-side | `test_smk_024_ref_authenticity_allowlist.py` | 3 | `test_smk_024_reconstructed_canonical_ref_not_issued_is_missing` | `..._neg_no_allowlist_keeps_slot_correctness_no_regression`, `..._control_fully_issued_allowlist_all_complete` | M6-RULE-015 | M6-FAIL-007 | 1 / 3 |
| M6-SMK-025 | M6-OD-013 smoke-side | `test_smk_025_smoke_result_authenticity.py` | 4 | `test_smk_025_whitespace_mandatory_smoke_is_unrecorded_and_not_ready` | `..._neg_recorded_requires_stripped_non_blank_not_raw_truthiness`, `..._neg_assembler_normalizes_whitespace_fields_to_none`, `..._control_genuine_recorded_smokes_all_record` | M6-RULE-015 | M6-FAIL-007 | 2 / 4 |

**New M6.2M official-smoke nodes: 7 (3 + 4).**

## Per-smoke summary (what each leg proves)

- **M6-SMK-024 (ref-side authenticity):** M6.2L closed the shape-only forgeries; a forger reconstructing the exact
  canonical `ev::{category}::{key}` string still passed in the default (no-oracle) path. With a staged `known_refs`
  allowlist supplied, a ref that is shape-valid + correctly (category,key)-bound + unique but was NEVER issued (not in
  the allowlist) is REJECTED → that category MISSING → pack NOT_READY (authenticity beyond slot-correctness). With **no
  allowlist** the M6.2L slot-correctness bar still holds (no regression); with a **fully-issued** allowlist everything
  completes (discriminating — a category is COMPLETE iff its ref is issued).
- **M6-SMK-025 (smoke-side twin):** `SmokeResult.recorded` now requires **stripped-non-blank** status +
  correlation_id + evidence_id — `bool("  ")` is True but a whitespace field is not a real recorded value. A
  whitespace / fake-but-nonblank `SmokeResult` for a MANDATORY owner smoke (M6-SMK-001) stays un-recorded →
  UNRUN_SMOKE gap → pack NOT_READY (FAIL-007); the assembler's `_smokes` normalizes whitespace-only fields to None so
  nothing masquerades on export. A genuine result still records (non-vacuous control).

## Fixtures reused (from `tests/conftest.py`)

| Fixture | Role |
|---|---|
| `evidence_assembler` | `EvidencePackAssembler()` — `.assemble(smoke_results, evidence_refs, known_refs=None)` (the `known_refs` oracle is opt-in) |
| `full_evidence_refs` | the honest, unique, correctly-bound full ref set (`ev::{cat.value}::{key}`) — the staged allowlist is built inline from these |
| `all_smokes_recorded` | all 18 smokes recorded with genuine synthetic correlation_id / evidence_id |

Plus `SmokeResult` + `get_spec` / `SmokeStatus` (constructed inline for the whitespace/mandatory-owner cases) and the
frozen `app/measurement/evidence/` package (`models._nonblank`, `pack_assembler._ref_valid` / `_smokes`,
`gap_blockers`, `smoke_registry`).

## Boundary / safety asserted by the suite

- **Authenticity, not shape alone (M6-OD-013 / RULE-015 / FAIL-007):** a not-issued canonical ref and a
  whitespace SmokeResult both fail closed → NOT_READY; the pack cannot be authenticated by shape/truthiness alone.
- **Opt-in, no regression:** without an allowlist / with genuine results the honest path still completes
  (OWNER_REVIEW_REQUIRED) — the tightening rejects forgeries, not legitimate evidence.
- **PII-safe (RULE-014):** all refs/ids are synthetic governance values; correlation/evidence ids masked on export.
- **No fix to code under test; no application code / migration / external call / flag flip / `04-artifacts/state/`
  write** anywhere in the suite. M6-P1000 / M6-P1309 stay BLOCKED and remain in the assembled pack.

## Build-validation performed in M6-P2203 (attempt 1, collect-only — "do not yet run")

Per the prompt's `<task>` ("Build (do not yet run)"), this attempt ran **collect-only** (imports + collects; **no
assertions executed**). Run with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest 8.4.2**, from
`04-artifacts/impl/M6.2M/`, **no shell redirection** (the role guard blocks a `>`/`2>` co-occurring with the venv
`Scripts` path), cache-free (`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```bash
python.exe -c "<in-process pytest_collection_finish tally; pytest.main(['--collect-only','-q','-p','no:cacheprovider'])>"
#   -> RC 0 ; COLLECTED_TOTAL=575 ; NEW_TOTAL=7 (024:3, 025:4) ; 0 collection errors
```

Reconciliation: **575** collected = M6.2M carried+coder baseline **568** (M6.2L 561 + 7 coder M6.2M regressions) +
these **7** new official-smoke nodes. Every new file imports + collects clean. A read-only **adversarial static
verification** (2 logic verifiers — one per twin — + 1 verbatim-string auditor + 1 completeness/PII/boundary critic)
was run alongside — findings recorded in the M6-P2203 evidence.

> **On counting.** pytest's terminal summary is not reliably captured in this harness, so the total (**575**) came
> from an in-process `pytest_collection_finish` tally (`len(session.items)`) with pytest `RC=0`; pytest's own
> per-item output was swallowed (`redirect_stdout`).

Cache hygiene: `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

> **This build does NOT self-certify gate advancement.** Collect-only proves the smoke files import + collect against
> the frozen M6.2M code; it does not execute assertions. The **formal executed-results recording** (with a
> correlation_id + evidence_id per smoke) is produced by **M6-P2204** into
> `04-artifacts/test-reports/M6.2M/SMOKE_RESULTS.md`. The runner EVIDENCE_GATE and the slice Judge decide closure.

## Execution plan for M6-P2204 (`M6_2M_TESTER_RUN`)

Run the full staged suite and the 2 new smoke legs, then record structured results + a correlation_id + evidence_id
per smoke:

```bash
python -m pytest -q                                  # full staged suite: expected 575 passed
python -m pytest -q tests/smoke/test_smk_024_ref_authenticity_allowlist.py tests/smoke/test_smk_025_smoke_result_authenticity.py   # expected 7 passed
```

Record per smoke id PASS/FAIL/BLOCKED + detail + correlation_id + evidence_id (synthetic, masked). SMK-024 uses a
staged `known_refs` allowlist (allowlist = genuine refs minus the target slot to model the reconstructed-but-not-issued
vector); SMK-025 asserts a whitespace SmokeResult for a mandatory owner smoke is `recorded()==False` → NOT_READY.

## Exit-gate legs (slice M6.2M done-gate, itemized)

| Leg | Requirement | Covered by |
|---|---|---|
| 1 | Ref authenticity (M6-OD-013 ref-side) | SMK-024 leg + coder `test_m6_2m_ref_authenticity`; run by M6-P2204 |
| 2 | Smoke authenticity (M6-OD-013 smoke-side twin) | SMK-025 leg + coder `test_m6_2m_smoke_authenticity`; run by M6-P2204 |
| 3–4 | Proposed smoke M6-SMK-024 / 025 executed OR owner-waived | the 2 legs (built here); executed by M6-P2204 |
| 5 | All slice prompts have schema-valid evidence JSON | this evidence + downstream |
| 6 | Slice gate judge sign-off PASS | M6-P2209 (downstream) |
| 7 | Rollback steps documented | new smoke files → delete (no carried-forward file patched) |

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-015 | No self-certification; the pack declares no Pass/Ready — authenticity keeps a forged/blank pack from reaching OWNER_REVIEW_REQUIRED. |
| M6-FAIL-007 | No evidence → called PASS — a not-issued ref (024) or a whitespace SmokeResult (025) fails closed to NOT_READY. |
| M6-OD-013 | Evidence authenticity residual (M6.2L re-judge) — the ref-side + smoke-side twin closed here with a staged oracle. |

## Provenance / notes

- Scenario & expected text quoted **verbatim** from `00-spec/registers/SMOKE_REGISTER.md` (proposed additions rows
  M6-SMK-024/025; derivation: M6-OD-013 authenticity residual, M6.2L re-judge 2026-09-03). Test patterns reused from
  the coder's M6.2M regression tests (`tests/test_m6_2m_*.py`) and the shared conftest fixtures (doc working mode,
  extract line 466).
- **Rollback:** the 2 new `tests/smoke/test_smk_024..025_*.py` files → delete; **no carried-forward file is patched**,
  no production code added, no migration, no flag flipped.
- No self-certification of PASS or of gate/leg advancement: the runner EVIDENCE_GATE and the slice Judge decide. This
  manifest and the 2 smoke legs are the *build*; the formal executed results are produced in M6-P2204.
