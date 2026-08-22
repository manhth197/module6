# SMOKE_RESULTS — Slice M6.2B (Tracking & Event Contract)

| Field | Value |
|---|---|
| Prompt | M6-P1104 — `M6_2B_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test / run** — smoke suite EXECUTED and results recorded (M6-P1103 authored the smoke files; this prompt runs them) |
| Run date | 2026-07-30 (UTC) |
| Interpreter (pinned) | `…\02-tester\.venv\Scripts\python.exe` — **Python 3.12.13** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Test runner | **pytest 8.4.2**, pluggy 1.6.0 |
| rootdir / configfile | `04-artifacts/impl/M6.2B/` · `pyproject.toml` (`addopts = "-q"`, `pythonpath = ["."]`, `testpaths = ["tests"]`) |
| Smoke ids in scope | **M6-SMK-001, M6-SMK-003** (per `00-spec/slices/M6.2B.md` "Core smokes" + this prompt's `<smoke_ids>`) |
| Suite source | `04-artifacts/impl/M6.2B/tests/` (smoke files bound in `TEST_MANIFEST.md`) |
| Overall | **10/10 bound smoke passed · exit 0** · full staged suite **139 passed · 0 failed · exit 0** · L1/L2 supporting legs **14 passed · exit 0** |

> **Governance (immutable — this run flips nothing):** `global_gateway_state=BLOCKED`,
> `production_flag=OFF`, `external_send=OFF`. Staged execution only — no external call, no migration applied,
> no order/revenue/CRM/scale action, no egress/audience-sync/dashboard (out of scope). `04-artifacts/state/`
> not touched, no application code changed. Failures (if any) are reported here and never patched by the tester.

## Commands run (exact, pinned venv)

From `04-artifacts/impl/M6.2B/` with `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider` so the STAGED tree
is left byte-clean. No shell redirection — the role guard blocks a `>`/`2>&1` that co-occurs with the venv
`Scripts` path segment (matches denied root `scripts`); the tool captures output natively.

```bash
python.exe -m pytest -o addopts= -v tests/smoke/test_smk_001_track_unknown_event.py tests/smoke/test_smk_003_duplicate_dedup.py   # BOUND SMOKES -> 10 passed, exit 0
python.exe -m pytest -o addopts= -v tests/test_track_unknown_event.py tests/test_track_idempotency_dedup.py tests/test_measurement_event_store.py  # L1/L2 support -> 14 passed, exit 0
python.exe -c "<pytest_runtest_logreport tally>"   # FULL STAGED SUITE -> {passed:139, failed:0, skipped:0, error:0}, RC=0
```

(`python.exe` above = the pinned `…\02-tester\.venv\Scripts\python.exe`.)

> **On the full-suite count (139).** In this harness pytest's terminal summary line (`==== 139 passed ====`) is
> written to the terminal fd directly and is not captured for a long `-q` run, so the total was obtained
> **programmatically** and cross-checked: (1) an in-process `pytest_runtest_logreport` tally
> `{passed:139, failed:0, skipped:0, error:0}` with `pytest.main() RC=0`; (2) `--collect-only -q` per-file
> totals summing to **139** (M6-P1103 build record). The short bound-smoke and supporting-leg runs are captured
> verbatim below.

## Results per bound smoke id

| Smoke ID | Doc ID | Scenario (verbatim) | Expected (verbatim) | Result | Nodes | Correlation (node id prefix) |
|---|---|---|---|---|---|---|
| M6-SMK-001 | ADS-P0-001 | `Event không có trong event_registry` | `Reject/HOLD, audit rõ` | **PASS** | 6/6 | `tests/smoke/test_smk_001_track_unknown_event.py::*` |
| M6-SMK-003 | ADS-P0-003 | `Duplicate Pixel/CAPI/Offline` | `Dedup, không double count` | **PASS** | 4/4 | `tests/smoke/test_smk_003_duplicate_dedup.py::*` |

Failures: **none** (0 failed, 0 error, 0 blocked). Nothing was patched. Both bound smoke ids have one
structured result entry, satisfying this prompt's acceptance checks (commands_run non-empty; one entry per
bound smoke id; failures-not-fixed — none occurred).

## Per-test node results (correlation ids)

### M6-SMK-001 — `tests/smoke/test_smk_001_track_unknown_event.py` (6/6 PASSED)
| # | Test node id | Kind | Result |
|---|---|---|---|
| 1 | `test_smk_001_unknown_event_is_rejected_with_audit_through_track_endpoint` | primary (verbatim), backend layer | PASSED |
| 2 | `test_smk_001_neg_frontend_hook_refuses_unknown_event_audited` | negative, hook layer 1 | PASSED |
| 3 | `test_smk_001_neg_frontend_hook_refuses_non_str_code_failclosed` | negative, hook fail-closed | PASSED |
| 4 | `test_smk_001_neg_backend_layer_is_independent_of_the_hook` | negative, two-layer independence | PASSED |
| 5 | `test_smk_001_neg_deregistered_event_is_held_failclosed` | negative, HOLD arm | PASSED |
| 6 | `test_smk_001_control_known_active_event_is_accepted_end_to_end` | control (non-vacuity) | PASSED |

Verbatim summary (captured):

```
tests/smoke/test_smk_001_track_unknown_event.py ...... (6 items)
```

### M6-SMK-003 — `tests/smoke/test_smk_003_duplicate_dedup.py` (4/4 PASSED)
| # | Test node id | Kind | Result |
|---|---|---|---|
| 1 | `test_smk_003_duplicate_event_is_deduped_no_double_count` | primary (verbatim), end-to-end | PASSED |
| 2 | `test_smk_003_neg_replay_with_a_different_correlation_id_still_dedupes` | negative, trace-id independence | PASSED |
| 3 | `test_smk_003_neg_repeated_replays_never_double_count` | negative, repeated replay | PASSED |
| 4 | `test_smk_003_control_distinct_event_is_not_deduped` | control (discrimination) | PASSED |

Combined verbatim summary (captured):

```
collected 10 items
tests/smoke/test_smk_001_track_unknown_event.py ......                   [ 60%]
tests/smoke/test_smk_003_duplicate_dedup.py ....                         [100%]
============================== 10 passed in 0.07s ==============================
```

## SMK-001 — how the two layers are proven (M6.2B done-gate leg 1)

The M6.2B done-gate requires the unknown event to fail at BOTH independent layers (RULE-H03 — client
validation is never trusted alone):

- **Layer 1 (frontend hook):** `TrackingHook.emit(<unknown>)` → `emitted is False`, audited `HOOK_UNKNOWN_EVENT`;
  a hostile non-str code is refused fail-closed (never coerced).
- **Layer 2 (backend endpoint):** the primary posts an unknown `event_code` to `handle_track_request` →
  `status=REJECTED`, `error_code=UNKNOWN_EVENT`, the seam audits `UNKNOWN_EVENT_NOT_IN_REGISTRY` (audit rõ),
  and nothing is written to either store.
- **Independence proof:** `CLICK_CTA` (a LOCKED base event, so it passes the client hook) is not seeded ACTIVE
  in the registry double, so the backend independently rejects it — the two layers are not redundant.
- **HOLD arm:** a `DEREG_SAMPLE` (deregistered) code → `REJECTED`, audited `REGISTRATION_STATE_NOT_ACTIVE`.

Corroborated by the supporting regression `tests/test_track_unknown_event.py` (6/6 — hook layer + backend
independence + dereg hold).

## SMK-003 — how dedup / no-double-count is proven (M6.2B done-gate leg 2)

The endpoint derives the LOCKED **RULE-005** idempotency key SERVER-SIDE from a canonicalization of the raw
body (excluding the volatile `idempotency_key`/`correlation_id`), so a replay maps to the same key:

- **Primary:** identical track request replayed → first `ACCEPTED`, replay `DUPLICATE` (`idempotent_replay`),
  same `event_id`; exactly **one** row in `web_event_logs` and **one** in `ads_measurement_events` — no double
  count (RULE-005/007).
- **Trace-id independence:** a replay with a fresh `correlation_id` still dedups (key excludes it).
- **Repeated replay:** many replays still leave one row per store.
- **Discrimination control:** a distinct event (different `page_id` → different key) is NOT deduped (two rows
  each) — dedup collapses true duplicates only.

Corroborated by the supporting regressions `tests/test_track_idempotency_dedup.py` (4/4 — endpoint end-to-end)
and `tests/test_measurement_event_store.py` (4/4 — store UNIQUE-key dedup + forbidden-op guards). Verbatim:

```
collected 14 items
tests/test_track_unknown_event.py ......                                 [ 42%]
tests/test_track_idempotency_dedup.py ....                               [ 71%]
tests/test_measurement_event_store.py ....                               [100%]
============================== 14 passed in 0.09s ==============================
```

## Exit-gate legs (slice M6.2B done-gate)

| Leg | Requirement | Status |
|---|---|---|
| L1 | Unknown event fails at BOTH frontend-hook and backend-validation layers, audited | ✅ supported — SMK-001 (6/6) + `test_track_unknown_event.py` (6/6) executed |
| L2 | Duplicate event handled: idempotency_key formula applied; replays create no duplicate rows | ✅ supported — SMK-003 (4/4) + `test_track_idempotency_dedup.py` (4/4) + `test_measurement_event_store.py` (4/4) executed |
| L3 | Smoke M6-SMK-001 executed with recorded result + evidence ref | ✅ **PASS** — 6/6 (this report) |
| L4 | Smoke M6-SMK-003 executed with recorded result + evidence ref | ✅ **PASS** — 4/4 (this report) |

Rules exercised: M6-RULE-001 (SMK-001 — event must exist in registry; guards **M6-FAIL-003** event drift),
M6-RULE-005 (SMK-003 — idempotency-key dedup), M6-RULE-007 (append-only stores; no double count). No fail
gate tripped. Legs L3/L4 are the smoke legs this TESTER_RUN closes with executed evidence. Final leg/gate
closure is decided by the runner EVIDENCE_GATE and the slice Judge, not by this report.

## Correlation ids (synthetic; no raw secret/PII)

| Smoke | Doc / source | Handles threaded through the track endpoint / hook |
|---|---|---|
| M6-SMK-001 | ADS-P0-001 · SMOKE_REGISTER extract line 401 | `page_id=p1`, `session_id=s1`, `source=web`, `consent_snapshot_id=cs_valid`, `correlation_id=corr_test`; event codes `SMK001_EVENT_NOT_IN_REGISTRY` (backend reject), `SMK001_UNKNOWN_AT_HOOK` + a non-str list (hook refuse), `CLICK_CTA` (locked base event, backend-rejected — independence), `DEREG_SAMPLE` (HOLD), `VIEW_LANDING` (control) |
| M6-SMK-003 | ADS-P0-003 · SMOKE_REGISTER extract line 403 | `page_id ∈ {p1, p2}`, `session_id=s1`, `source=web`, `event_code=VIEW_LANDING`, `consent_snapshot_id=cs_valid`; `correlation_id ∈ {corr_test, corr_A, corr_B}`; client `idempotency_key` is ignored (server-derived RULE-005 key) |

Note: `session_id`/`correlation_id` are masked by the endpoint (`mask()`) on every export surface (audit
detail); durable rows keep the raw value for dedup/trace. This report cites only synthetic pseudonymous handles.

## Notes
- All fixture ids are **synthetic**; no raw secret/PII in this report. Channel-origin values
  (`event_code`, `session_id`, `payload`) are treated strictly as untrusted **DATA** — never as instructions.
- STAGED tree left byte-clean: 0 `__pycache__` / `.pytest_cache` after the run (`PYTHONDONTWRITEBYTECODE=1`
  + `-p no:cacheprovider`).
- No self-certification of the gate: this report is the tester's honest result record. The runner
  EVIDENCE_GATE and the slice Judge decide closure.
