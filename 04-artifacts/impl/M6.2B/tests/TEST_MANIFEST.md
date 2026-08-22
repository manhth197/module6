# TEST_MANIFEST — Slice M6.2B smoke suite (Tracking & Event Contract)

| Field | Value |
|---|---|
| Prompt | M6-P1103 — `M6_2B_TESTER_BUILD` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — the smoke tests are AUTHORED here. This attempt also ran `pytest` as a **build-validation** (green); the **formal executed-results recording** for the exit-gate smoke legs belongs to M6-P1104. |
| Executed by (formal) | M6-P1104 (`M6_2B_TESTER_RUN`) → `04-artifacts/test-reports/M6.2B/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-001, M6-SMK-003** (exactly — per `00-spec/slices/M6.2B.md` "Core smokes" + this prompt's `<smoke_ids>`) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin; `test_command = pytest -q`) |
| Slice scope | frontend tracking hooks · `POST /api/ads/events/track` validation · `ads_measurement_event` contract · idempotency (per `00-spec/slices/M6.2B.md`, doc §7/§10) |
| Staging root | `04-artifacts/impl/M6.2B/` (STAGED_ONLY; convention reference, not a live repo) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (owner P0 matrix, doc §21) |

> **Governance (immutable — nothing in this suite flips a flag):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`.
> This slice proves capability with evidence only. No external send, no audience sync, no dashboard (out of
> scope). The MANDATORY M6.2G Scale-Gate re-gate (ENTRY-001/002/003) remains in force before any real scale
> or external send.

## What this suite is

The **official M6.2B smoke suite**: exactly one **primary** test per bound smoke id, carrying the register's
scenario/expected **verbatim**, driven **end-to-end through the M6.2B tracking pipeline** — the client
tracking hook (`app.measurement.tracking.hooks.TrackingHook`) and the backend endpoint handler
(`app.api.track.handle_track_request`) over its two append-only stores (`web_event_logs` and the normalized
`ads_measurement_events`) — plus the negative / fail-closed companions the doc done-gate requires and a
positive control for non-vacuity. It reuses the shared fixtures in
[`tests/conftest.py`](04-artifacts/impl/M6.2B/tests/conftest.py) (`track_deps`, `make_track_body`, `store`,
`measurement_store`, `audit`; in-memory TEST DOUBLES for the CONSUMED `event_registry` / consent / identity).
No new production code, and **no fix to the code under test** (TESTER reports defects, never fixes them).

All fixture ids are **synthetic**; no raw secret/PII. `event_code` / `session_id` / `payload` are
channel-origin, untrusted DATA — treated as data only; `session_id`/`correlation_id` are masked by the
endpoint (O1) on export.

M6.2B **carried the whole M6.2A tree forward** (so the smoke suite runs end-to-end endpoint→seam→stores). The
carried-forward M6.2A seam-level smokes (`tests/smoke/test_smk_001_event_not_in_registry.py`,
`tests/smoke/test_smk_002_valid_event_missing_consent.py`) and the full M6.2A + Round-2/3/4 regression suites
remain and are re-run here as supporting/regression coverage; the two files below are the **new M6.2B-bound
smokes** authored by this prompt.

## Smoke → test binding

| Smoke ID | Doc ID | Test file (M6.2B, new) | Primary test (scenario verbatim) | Negative / fail-closed tests | Control | Rule(s) | Fail gate | Exit leg |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-001 | ADS-P0-001 | [`tests/smoke/test_smk_001_track_unknown_event.py`](04-artifacts/impl/M6.2B/tests/smoke/test_smk_001_track_unknown_event.py) | `test_smk_001_unknown_event_is_rejected_with_audit_through_track_endpoint` | `..._neg_frontend_hook_refuses_unknown_event_audited`, `..._neg_frontend_hook_refuses_non_str_code_failclosed`, `..._neg_backend_layer_is_independent_of_the_hook`, `..._neg_deregistered_event_is_held_failclosed` | `..._control_known_active_event_is_accepted_end_to_end` | M6-RULE-001 | M6-FAIL-003 | L1 (both layers) + L3 |
| M6-SMK-003 | ADS-P0-003 | [`tests/smoke/test_smk_003_duplicate_dedup.py`](04-artifacts/impl/M6.2B/tests/smoke/test_smk_003_duplicate_dedup.py) | `test_smk_003_duplicate_event_is_deduped_no_double_count` | `..._neg_replay_with_a_different_correlation_id_still_dedupes`, `..._neg_repeated_replays_never_double_count` | `..._control_distinct_event_is_not_deduped` | M6-RULE-005, M6-RULE-007 | — | L2 (dedup) + L4 |

---

## M6-SMK-001 — event not in `event_registry` (M6.2B tracking pipeline)

Verbatim from `00-spec/registers/SMOKE_REGISTER.md` (extract line 401):

```
Smoke ID:          M6-SMK-001  (Doc ID ADS-P0-001)
Kịch bản:          Event không có trong event_registry
Kết quả phải đạt:  Reject/HOLD, audit rõ
Bound slices:      M6.2A, M6.2B, M6.2K
```

**How it is proven (M6.2B done-gate leg 1 — BOTH independent layers, RULE-H03).**

- **Primary (backend layer 2):** an event code absent from `event_registry`, posted to
  `handle_track_request`, returns `status=REJECTED`, `error_code=UNKNOWN_EVENT`; the seam audits the registry
  miss (`UNKNOWN_EVENT_NOT_IN_REGISTRY` — "audit rõ"); nothing is written to `web_event_logs`
  (`len(store)==0`) or normalized into `ads_measurement_events` (`len(measurement_store)==0`).
- **Negative — frontend layer 1 (hook):** `TrackingHook.emit("SMK001_UNKNOWN_AT_HOOK")` → `emitted is False`,
  audited `HOOK_UNKNOWN_EVENT`; and a hostile **non-str** code is refused fail-closed (never coerced).
- **Negative — layer independence:** `CLICK_CTA` IS a locked base event (passes the client hook) but is not
  seeded ACTIVE in the registry double, so the backend independently rejects it → the two layers are not
  redundant.
- **Negative — the "HOLD" arm of "Reject/HOLD":** a `DEREG_SAMPLE` (deregistered) code → `REJECTED`, audited
  `REGISTRATION_STATE_NOT_ACTIVE`, never logged.
- **Positive control (non-vacuity):** a known ACTIVE base event (`VIEW_LANDING`) posted to the endpoint →
  `ACCEPTED`, one row in each store — the smoke discriminates rather than rejecting everything.

Prevents M6-FAIL-003 (event drift). RULE-001 / RULE-018.

---

## M6-SMK-003 — duplicate event deduped, no double count

Verbatim from `00-spec/registers/SMOKE_REGISTER.md` (extract line 403):

```
Smoke ID:          M6-SMK-003  (Doc ID ADS-P0-003)
Kịch bản:          Duplicate Pixel/CAPI/Offline
Kết quả phải đạt:  Dedup, không double count
Bound slices:      M6.2B, M6.2D, M6.2K
```

**How it is proven (M6.2B done-gate leg 2).** The endpoint derives the LOCKED **RULE-005** idempotency key
SERVER-SIDE from a canonicalization of the raw body (excluding the volatile `idempotency_key` /
`correlation_id`), so a replay maps to the same key.

- **Primary:** an identical track request replayed → first `ACCEPTED` (`idempotent_replay is False`), replay
  `DUPLICATE` (`idempotent_replay is True`) with the **same** `event_id`; each append-only store holds exactly
  **one** row (`len(store)==1`, `len(measurement_store)==1`) — dedup, không double count, end-to-end across
  both the raw `web_event_logs` (RULE-007) and the normalized `ads_measurement_events` (UNIQUE key, RULE-005).
- **Negative — trace-id independence:** a replay carrying a fresh `correlation_id` still dedups (the key
  excludes `correlation_id`) — dedup keys on the event's identity, not the caller's trace id.
- **Negative — repeated replays:** many replays still leave exactly one row per store (idempotent).
- **Positive control (discrimination / non-vacuity):** a genuinely different event (different `page_id` →
  different key) is NOT deduped → two rows in each store. Dedup collapses true duplicates only.

RULE-005 (idempotency) / RULE-007 (append-only). **Scope note:** the full cross-source Pixel/CAPI/Offline
dedup by content is exercised again where those external channels are wired (**M6.2D**); M6.2B's manifestation
is the exact-replay dedup on the track endpoint via the locked RULE-005 key.

---

## Supporting / regression suite (run alongside the two bound smokes)

The `pytest -q` run exercises the full staged suite. Files below are **not** the two bound M6.2B smoke ids but
pin the pipeline contract the smokes rely on; the coder authored them in M6-P1102.

| File | Purpose | Nodes | In smoke scope? |
|---|---|---|---|
| [`tests/test_track_unknown_event.py`](04-artifacts/impl/M6.2B/tests/test_track_unknown_event.py) | SMK-001 both-layer regression (hook + backend independence) | 6 | No (regression) |
| [`tests/test_track_idempotency_dedup.py`](04-artifacts/impl/M6.2B/tests/test_track_idempotency_dedup.py) | SMK-003 dedup regression (endpoint end-to-end) | 4 | No (regression) |
| [`tests/test_measurement_event_store.py`](04-artifacts/impl/M6.2B/tests/test_measurement_event_store.py) | `ads_measurement_events` store: UNIQUE dedup + forbidden-op guards (RULE-005/007/008) | 4 | No (regression) |
| [`tests/test_track_contract_and_validation.py`](04-artifacts/impl/M6.2B/tests/test_track_contract_and_validation.py) | CTR-016 endpoint contract + server re-validation error model (incl. RAW_PII tripwire, RULE-014) | 9 | No (regression) |
| [`tests/test_m6_2b_fixfirst_regressions.py`](04-artifacts/impl/M6.2B/tests/test_m6_2b_fixfirst_regressions.py) | fix-first hardening (F1 forgiving seam · F2 consent decision-point · MINOR-9 audit retention · O1 masking) | 10 | No (regression) |
| carried-forward M6.2A suite | seam smokes (`test_smk_001_event_not_in_registry` 4, `test_smk_002_valid_event_missing_consent` 7), consent_fail_closed 6, event_registry_validation 6, identity_mapping_audit 7, ingest_measure_only 5, web_event_logs_append_only 4, round2 11, round3 20, round4 26 | 96 | No (carried regression) |

## Fixtures reused (from `tests/conftest.py`)

| Fixture | Role |
|---|---|
| `track_deps` | wired `TrackDeps` (hardened ingest seam + `web_store` + `measurement_store` + shared `audit`) — the endpoint's collaborators |
| `make_track_body(**over)` | CTR-016 request-body builder; default = valid `VIEW_LANDING` with `cs_valid` + `corr_test` |
| `store` | `WebEventLogStore` (raw append-only `web_event_logs`) — same instance inside the seam |
| `measurement_store` | `MeasurementEventStore` (normalized `ads_measurement_events`, UNIQUE idempotency_key) |
| `audit` | function-scoped `AuditLog` shared by validator/gate/seam/endpoint → `audit.find(...)` sees seam + endpoint records |
| registry double | `VIEW_LANDING` (ACTIVE), `DEREG_SAMPLE` (deregistered → HOLD), `NO_OWNER_SAMPLE` (ACTIVE, no owner → HOLD) |

`CLICK_CTA` is a LOCKED base event (`app.measurement.tracking.base_events`) that is deliberately **absent**
from the registry double, used to prove the backend layer is independent of the client hook.

## Boundary / safety asserted by the suite

- **No egress:** the track endpoint exposes ingest + dedup only; there is no send/audience-sync/dashboard in
  this path (out of scope for M6.2B; `external_send=OFF`).
- **Append-only + dedup:** duplicates never create a second row in either store; unknown/held events are never
  logged yet are always audited (RULE-005/007, "audit rõ").
- **No flag flip, no external call, no `04-artifacts/state/` write** anywhere in the suite.

## Build + validation run performed in M6-P1103 (attempt 1, pinned interpreter)

Run with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest 8.4.2**. This attempt ran the suite (not
collect-only) as a **build-validation**; the run was **green**. Commands from `04-artifacts/impl/M6.2B/`, **no
shell redirection** (the role guard blocks a `>`/`2>` that co-occurs with the venv `Scripts` path), cache-free
(`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```bash
python.exe -m pytest -v tests/smoke/test_smk_001_track_unknown_event.py tests/smoke/test_smk_003_duplicate_dedup.py   # 10 passed, exit 0
python.exe -m pytest --collect-only -q                                                                               # per-file totals (below)
python.exe -c "<pytest_runtest_logreport tally>"                                                                     # {passed:139, failed:0, skipped:0, error:0}, RC=0
```

New M6.2B smoke node ids (10), all PASSED:

```
tests/smoke/test_smk_001_track_unknown_event.py::test_smk_001_unknown_event_is_rejected_with_audit_through_track_endpoint
tests/smoke/test_smk_001_track_unknown_event.py::test_smk_001_neg_frontend_hook_refuses_unknown_event_audited
tests/smoke/test_smk_001_track_unknown_event.py::test_smk_001_neg_frontend_hook_refuses_non_str_code_failclosed
tests/smoke/test_smk_001_track_unknown_event.py::test_smk_001_neg_backend_layer_is_independent_of_the_hook
tests/smoke/test_smk_001_track_unknown_event.py::test_smk_001_neg_deregistered_event_is_held_failclosed
tests/smoke/test_smk_001_track_unknown_event.py::test_smk_001_control_known_active_event_is_accepted_end_to_end
tests/smoke/test_smk_003_duplicate_dedup.py::test_smk_003_duplicate_event_is_deduped_no_double_count
tests/smoke/test_smk_003_duplicate_dedup.py::test_smk_003_neg_replay_with_a_different_correlation_id_still_dedupes
tests/smoke/test_smk_003_duplicate_dedup.py::test_smk_003_neg_repeated_replays_never_double_count
tests/smoke/test_smk_003_duplicate_dedup.py::test_smk_003_control_distinct_event_is_not_deduped
```

Per-file collected counts (total **139** = carried-forward 96 + coder M6.2B 33 + these new smokes 10):

```
tests/smoke/test_smk_001_event_not_in_registry.py: 4          (carried M6.2A seam smoke)
tests/smoke/test_smk_001_track_unknown_event.py: 6           (NEW — M6.2B SMK-001)
tests/smoke/test_smk_002_valid_event_missing_consent.py: 7    (carried M6.2A seam smoke)
tests/smoke/test_smk_003_duplicate_dedup.py: 4               (NEW — M6.2B SMK-003)
tests/test_consent_fail_closed.py: 6
tests/test_event_registry_validation.py: 6
tests/test_identity_mapping_audit.py: 7
tests/test_ingest_measure_only.py: 5
tests/test_m6_2b_fixfirst_regressions.py: 10
tests/test_measurement_event_store.py: 4
tests/test_round2_regressions.py: 11
tests/test_round3_regressions.py: 20
tests/test_round4_regressions.py: 26
tests/test_track_contract_and_validation.py: 9
tests/test_track_idempotency_dedup.py: 4
tests/test_track_unknown_event.py: 6
tests/test_web_event_logs_append_only.py: 4
```

Cache hygiene: after the runs, **0** `__pycache__` / `.pytest_cache` directories remain under the staged tree.

> **On the full-suite count.** In this harness pytest's terminal summary line (`==== 139 passed ====`) is
> written to the terminal fd directly and is not captured for a long `-q` run, so the total was obtained via
> an in-process `pytest_runtest_logreport` tally ({passed:139, failed:0}), `pytest.main() RC=0`, and the
> `--collect-only` per-file sum (139) — all agreeing. The two smoke files' verbatim `10 passed` summary IS
> captured.

> **This build-validation run does NOT self-certify gate advancement.** It proves the smoke files import,
> collect, and pass against the frozen M6.2B code; it is the honest self-report of a TESTER build. The
> **formal executed-results recording** for exit-gate legs is produced by **M6-P1104** into
> `04-artifacts/test-reports/M6.2B/SMOKE_RESULTS.md`. The runner EVIDENCE_GATE and the slice Judge decide
> closure.

## Execution plan for M6-P1104 (`M6_2B_TESTER_RUN`)

Run the full staged suite and the two bound smokes, then record structured results + evidence refs for the
M6.2B exit-gate smoke legs:

```bash
python -m pytest -q                    # full staged suite: expected 139
python -m pytest -q tests/smoke/test_smk_001_track_unknown_event.py tests/smoke/test_smk_003_duplicate_dedup.py
```

## Exit-gate legs (slice M6.2B done-gate, itemized)

| Leg | Requirement | Covered by |
|---|---|---|
| L1 | Unknown event fails at BOTH frontend-hook and backend-validation layers, audited | SMK-001 primary (backend) + hook/independence negatives (6/6) · `test_track_unknown_event.py` (6/6) |
| L2 | Duplicate event handled: idempotency_key formula applied; replays create no duplicate rows | SMK-003 primary + dedup negatives (4/4) · `test_track_idempotency_dedup.py` (4/4) · `test_measurement_event_store.py` (4/4) |
| L3 | Smoke M6-SMK-001 executed with recorded result + evidence ref | closed by M6-P1104 (this suite built here) |
| L4 | Smoke M6-SMK-003 executed with recorded result + evidence ref | closed by M6-P1104 (this suite built here) |

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-001 | Every event must exist in `event_registry` before it is logged/sent; unknown → reject/hold + audit; M6 never invents event codes (SMK-001 guards). |
| M6-RULE-005 | Idempotency key locked 5-component formula; replayed events dedup, no double count (SMK-003 guards). |
| M6-RULE-007 | `web_event_logs` / `ads_measurement_events` append-only; never updated/deleted. |
| M6-FAIL-003 | Event drift — inventing an event outside `event_registry` (SMK-001 guards). |
| Exit legs | L1 unknown-event two-layer, L2 duplicate handled, L3 SMK-001 executed, L4 SMK-003 executed (`00-spec/slices/M6.2B.md`). |

## Provenance / notes

- Scenario & expected text quoted **verbatim** from `00-spec/registers/SMOKE_REGISTER.md` (rows M6-SMK-001,
  M6-SMK-003). Test patterns reused from the existing `tests/conftest.py`, `tests/test_track_unknown_event.py`
  and `tests/test_track_idempotency_dedup.py` (doc working mode, extract line 466).
- No self-certification of PASS or of gate/leg advancement: the runner EVIDENCE_GATE and the slice Judge
  decide. This manifest and the two smoke files are the *build*; the formal executed results are produced in
  M6-P1104.
