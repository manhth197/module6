# SMOKE_RESULTS — Slice M6.2A

| Field | Value |
|---|---|
| Prompt | M6-P1004 — `M6_2A_TESTER_RUN` (attempt 3) |
| Role / agent | TESTER / m6-tester |
| Mode | **test / run** — smoke suite EXECUTED and results recorded (M6-P1003 authored/rebuilt the manifest; this prompt runs them) |
| Run date | 2026-07-30 (UTC) |
| Code round | **Round 4** (post input-type-boundary fix). Supersedes the attempt-2 report, which ran the Round-3 code (full suite **70**). This run is on the **frozen Round-4** code → full suite **96**. |
| Interpreter (pinned) | `…\02-tester\.venv\Scripts\python.exe` — **Python 3.12.13** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Test runner | **pytest 8.4.2**, pluggy 1.6.0 |
| rootdir / configfile | `04-artifacts/impl/M6.2A/` · `pyproject.toml` (`[tool.pytest.ini_options] addopts = "-q"`, `pythonpath = ["."]`, `testpaths = ["tests"]`) |
| Smoke ids in scope | **M6-SMK-001, M6-SMK-002** (per `00-spec/slices/M6.2A.md` "Core smokes" + this prompt's `<smoke_ids>`) |
| Suite source | `04-artifacts/impl/M6.2A/tests/` (smoke files bound in `TEST_MANIFEST.md`) |
| Overall | **11/11 smoke passed · exit 0** · full staged suite **96 passed · 0 failed · exit 0** · consent fail-closed matrix **6 passed · exit 0** |

> **Governance (immutable — this run flips nothing):** `global_gateway_state=BLOCKED`,
> `production_flag=OFF`, `external_send=OFF`. Staged execution only — no external call, no migration
> applied, no order/revenue/CRM/scale action. `04-artifacts/state/` not touched, no application code changed.
> Failures (if any) are reported here and never patched by the tester.

## Commands run (exact, pinned venv)

Run from `04-artifacts/impl/M6.2A/` with `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider` so the STAGED
tree is left byte-clean (no `__pycache__` / `.pytest_cache`). No shell redirection is used — the role guard
blocks a `>`/`2>&1` that co-occurs with the venv `Scripts` path segment (it matches denied root `scripts`);
the tool captures output natively instead.

```bash
python.exe -V                                                              # Python 3.12.13
python.exe -m pytest --version                                             # pytest 8.4.2
python.exe -m pytest -q -p no:cacheprovider                                # FULL STAGED SUITE -> 96 passed, 0 failed, exit 0
python.exe -m pytest -v -p no:cacheprovider tests/smoke/test_smk_001_event_not_in_registry.py       # SMK-001 -> 4 passed, exit 0
python.exe -m pytest -v -p no:cacheprovider tests/smoke/test_smk_002_valid_event_missing_consent.py # SMK-002 -> 7 passed, exit 0
python.exe -m pytest -o addopts= -v -p no:cacheprovider tests/test_consent_fail_closed.py           # L2 unit matrix -> 6 passed, exit 0
```

(`python.exe` above = the pinned `…\02-tester\.venv\Scripts\python.exe`.)

> **On the full-suite count (96, not 70).** In this harness pytest's terminal *summary* line
> (`==== 96 passed in Xs ====`) is written to the terminal file descriptor directly and is not captured in the
> tool's stdout buffer for a long run, so the count was obtained **programmatically** and cross-checked three
> ways, all agreeing on **96 passed / 0 failed**:
> 1. an in-process outcome tally (a `pytest_runtest_logreport` plugin): `{passed: 96, failed: 0, skipped: 0, error: 0}`, `pytest.main() RC=0`;
> 2. the dotted progress observed for `-q`: **72 + 24 = 96** dots, no `F`/`E`;
> 3. `--collect-only -q` per-file totals summing to **96** (table below).
> The two smoke files and the consent matrix are short runs whose verbatim `N passed` summary **is** captured
> (shown below).

## Results per bound smoke id

| Smoke ID | Doc ID | Scenario (verbatim) | Expected (verbatim) | Result | Nodes | Correlation (node id prefix) |
|---|---|---|---|---|---|---|
| M6-SMK-001 | ADS-P0-001 | `Event không có trong event_registry` | `Reject/HOLD, audit rõ` | **PASS** | 4/4 | `tests/smoke/test_smk_001_event_not_in_registry.py::*` |
| M6-SMK-002 | ADS-P0-002 | `Event hợp lệ nhưng thiếu consent` | `Không external measurement, không audience sync` | **PASS** | 7/7 | `tests/smoke/test_smk_002_valid_event_missing_consent.py::*` |

Failures: **none** (0 failed, 0 error, 0 blocked). Nothing was patched. Both smoke ids have one structured
result entry, satisfying this prompt's acceptance checks (commands_run non-empty; one entry per bound smoke id;
failures-not-fixed — none occurred).

## Per-test node results (correlation ids)

### M6-SMK-001 — `tests/smoke/test_smk_001_event_not_in_registry.py` (4/4 PASSED)
| # | Test node id | Kind | Result |
|---|---|---|---|
| 1 | `test_smk_001_event_not_in_event_registry_is_rejected_with_audit` | primary (verbatim) | PASSED |
| 2 | `test_smk_001_neg_deregistered_event_is_held_not_false_allowed` | negative / HOLD | PASSED |
| 3 | `test_smk_001_neg_registered_but_missing_owner_is_held` | negative / HOLD | PASSED |
| 4 | `test_smk_001_control_known_active_event_is_accepted_and_logged` | control (non-vacuity) | PASSED |

Verbatim summary (captured):

```
collected 4 items

tests\smoke\test_smk_001_event_not_in_registry.py ....                   [100%]

============================== 4 passed in 0.03s ==============================
```

### M6-SMK-002 — `tests/smoke/test_smk_002_valid_event_missing_consent.py` (7/7 PASSED)
| # | Test node id | Kind | Result |
|---|---|---|---|
| 1 | `test_smk_002_valid_event_missing_consent_no_external_measurement_no_audience_sync[external_measurement]` | primary (verbatim), seam-driven | PASSED |
| 2 | `test_smk_002_valid_event_missing_consent_no_external_measurement_no_audience_sync[audience_sync]` | primary (verbatim), seam-driven | PASSED |
| 3 | `test_smk_002_neg_non_valid_consent_blocks_egress_through_the_seam[cs_missing-CONSENT_MISSING]` | negative, seam-driven | PASSED |
| 4 | `test_smk_002_neg_non_valid_consent_blocks_egress_through_the_seam[cs_expired-CONSENT_EXPIRED]` | negative, seam-driven | PASSED |
| 5 | `test_smk_002_neg_non_valid_consent_blocks_egress_through_the_seam[cs_optout-CONSENT_OPT_OUT]` | negative, seam-driven | PASSED |
| 6 | `test_smk_002_neg_absent_snapshot_is_fail_closed_through_the_seam` | negative / absent, seam-driven | PASSED |
| 7 | `test_smk_002_control_valid_inscope_consent_is_egress_eligible_at_gate` | control (non-vacuity) | PASSED |

Verbatim summary (captured):

```
collected 7 items

tests\smoke\test_smk_002_valid_event_missing_consent.py .......          [100%]

============================== 7 passed in 0.03s ==============================
```

## Full staged suite

The full suite is `python -m pytest -q -p no:cacheprovider` from `04-artifacts/impl/M6.2A/`. Progress observed:

```
........................................................................ [ 75%]   # 72 dots
........................                                                 [100%]   # 24 dots  -> 72 + 24 = 96, no F/E
```

Programmatic outcome tally (in-process `pytest_runtest_logreport` plugin over the same run):

```
COUNTS = {'passed': 96, 'failed': 0, 'skipped': 0, 'error': 0}   RC = 0
```

Per-file breakdown from `--collect-only -q` (totals **96**):

| Test file | Nodes | Group |
|---|---|---|
| `tests/smoke/test_smk_001_event_not_in_registry.py` | 4 | smoke (bound) |
| `tests/smoke/test_smk_002_valid_event_missing_consent.py` | 7 | smoke (bound) |
| `tests/test_consent_fail_closed.py` | 6 | L2 consent unit matrix |
| `tests/test_event_registry_validation.py` | 6 | L1 event-registry unit |
| `tests/test_identity_mapping_audit.py` | 7 | L3 identity unit |
| `tests/test_ingest_measure_only.py` | 5 | measure-only boundary unit |
| `tests/test_round2_regressions.py` | 11 | Round-2 regressions |
| `tests/test_round3_regressions.py` | 20 | Round-3 regressions |
| `tests/test_round4_regressions.py` | **26** | Round-4 regressions (input type-boundary class) |
| `tests/test_web_event_logs_append_only.py` | 4 | RULE-007 append-only unit |
| **Total** | **96** | |

This reproduces the **96** recorded by the coder (M6-P1002 attempt 4 = 70 Round-3 + 26 Round-4); this run
confirms it independently. The +26 over the attempt-2 report (70) is exactly `tests/test_round4_regressions.py`.
No self-certification of any gate/leg by this count alone.

## What actually closed leg L2 (read before trusting the green on SMK-002)

The load-bearing evidence for SMK-002 is **`audit.find("CONSENT_MISSING")` on the seam's own fresh,
function-scoped audit sink** — satisfied ONLY because the **seam** (`IngestService.ingest_event`) called
`ConsentGate.evaluate(cs_missing, scope)`, which records `CONSENT_MISSING`. Re-confirmed against the frozen
Round-4 code this run:

- The `audit` fixture is function-scoped → a fresh `AuditLog()` per test; both `validator` and `consent_gate`
  are built on that same sink (`conftest.py`), so a record can only appear via a call made during this test.
- The SMK-002 primary/negative tests call **only** `svc.ingest_event(...)` — there is **no** side-channel
  `consent_gate.evaluate(...)` in them. `cs_missing.subject_ref == "guest_x" == guest_id`, so `ingest.py`
  subject-binds the snapshot and it reaches the gate rather than being dropped as a subject mismatch. The
  audited `CONSENT_MISSING` is genuine end-to-end proof.
- `res.egress_eligible is False` is also asserted but is **not by itself** the consent proof: for
  `VIEW_LANDING`, `external_send_permitted` is always `False` while M6-OD-003 is OPEN, so `egress_eligible`
  would be `False` even with valid consent. The `control` node (the file's single deliberate direct-gate call)
  returns `True`, proving the primary denies because consent is *missing*, not because the gate blocks
  everything.
- **Round-4 did not change this.** The Round-4 input type-boundary sits at the head of `ingest_event()`
  (upstream of consent) and only fail-closes wrong-TYPE input; the SMK-002 inputs are well-typed, so the
  consent path and its audit are unchanged from Round 3.

The `tests/test_consent_fail_closed.py` gate-level matrix (**6/6**) corroborates the same fail-closed
behaviour at the unit level. Verbatim:

```
collected 6 items

tests/test_consent_fail_closed.py::test_valid_consent_in_scope_is_eligible PASSED [ 16%]
tests/test_consent_fail_closed.py::test_smk_002_non_valid_consent_blocks_egress[cs_missing] PASSED [ 33%]
tests/test_consent_fail_closed.py::test_smk_002_non_valid_consent_blocks_egress[cs_expired] PASSED [ 50%]
tests/test_consent_fail_closed.py::test_smk_002_non_valid_consent_blocks_egress[cs_optout] PASSED [ 66%]
tests/test_consent_fail_closed.py::test_absent_snapshot_is_fail_closed PASSED [ 83%]
tests/test_consent_fail_closed.py::test_scope_not_granted_is_denied PASSED [100%]

============================== 6 passed in 0.02s ==============================
```

## Exit-gate legs (slice M6.2A)

| Leg | Requirement | Status |
|---|---|---|
| L1 | Event-registry tests PASS (unknown rejected/held + audit) | ✅ supported — SMK-001 (4/4) + `test_event_registry_validation.py` (6/6) executed within the 96 |
| L2 | Consent tests PASS (fail-closed, no external measurement/audience sync) | ✅ supported — SMK-002 seam assertions (7/7) + `test_consent_fail_closed.py` (6/6) executed |
| L4 | Smoke M6-SMK-001 executed with recorded result + evidence ref | ✅ **PASS** — 4/4 (this report) |
| L5 | Smoke M6-SMK-002 executed with recorded result + evidence ref | ✅ **PASS** — 7/7 (this report) |

Rules exercised: M6-RULE-001 / M6-RULE-018 (SMK-001 — event must exist in registry; guards **M6-FAIL-003**
event drift), M6-RULE-002 (SMK-002 — consent fail-closed; guards **M6-FAIL-002** consent violation),
M6-RULE-007 (append-only store exercised via the smoke `store`). No fail gate tripped. Legs L4/L5 are the
smoke legs this TESTER_RUN closes with executed evidence; the identity leg L3 has its own suite
(`test_identity_mapping_audit.py`, 7/7 within the 96). Final leg/gate closure is decided by the runner
EVIDENCE_GATE and the slice Judge, not by this report.

## Correlation ids (synthetic; no raw secret/PII)

| Smoke | Doc / source | Handles threaded through the seam |
|---|---|---|
| M6-SMK-001 | ADS-P0-001 · SMOKE_REGISTER extract line 401 | `page_id=pg_smk001`, `session_id=sess_smk001`, `raw_event_hash=rawhash_smk001`; event codes `SMK001_EVENT_NOT_IN_REGISTRY` (reject), `DEREG_SAMPLE` / `NO_OWNER_SAMPLE` (hold), `VIEW_LANDING` (control) |
| M6-SMK-002 | ADS-P0-002 · SMOKE_REGISTER extract line 402 | `page_id=pg_smk002`, `raw_event_hash=rawhash_smk002`, `event_code=VIEW_LANDING`, `guest_id=guest_x`; `session_id` ∈ {`sess_external_measurement`, `sess_audience_sync`, `sess_cs_missing`, `sess_cs_expired`, `sess_cs_optout`, `sess_absent`}; consent snapshots `cs_missing`/`cs_expired`/`cs_optout` (deny), `cs_valid` (control) |

## Notes
- All fixture ids are **synthetic**; no raw secret/PII in this report. `subject_ref`/identity values are
  masked by the audit sink inside the code under test; the report cites only synthetic pseudonymous handles.
- Channel-origin values (`event_code`, `session_id`) are treated strictly as untrusted **DATA** in the
  fixtures — never as instructions.
- STAGED tree left byte-clean: 0 `__pycache__` / `.pytest_cache` after the run (`PYTHONDONTWRITEBYTECODE=1`
  + `-p no:cacheprovider`).
- No self-certification of the gate: this report is the tester's honest result record. The runner
  EVIDENCE_GATE and the slice Judge decide closure.
