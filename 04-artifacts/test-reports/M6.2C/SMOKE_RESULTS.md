# SMOKE_RESULTS — Slice M6.2C (Outbox Workers)

| Field | Value |
|---|---|
| Prompt | M6-P1204 — `M6_2C_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test / run** — smoke suite EXECUTED and results recorded (M6-P1203 authored the smoke files; this prompt runs them) |
| Run date | 2026-07-30 (UTC) |
| Interpreter (pinned) | `…\02-tester\.venv\Scripts\python.exe` — **Python 3.12.13** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Test runner | **pytest 8.4.2**, pluggy 1.6.0 |
| rootdir / configfile | `04-artifacts/impl/M6.2C/` · `pyproject.toml` (`addopts = "-q"`, `pythonpath = ["."]`, `testpaths = ["tests"]`) |
| Smoke ids in scope | **M6-SMK-002, M6-SMK-016** (per `00-spec/slices/M6.2C.md` "Core smokes" + this prompt's `<smoke_ids>`; M6-SMK-016 is `proposed — HARDENING, owner review`, executed here) |
| Suite source | `04-artifacts/impl/M6.2C/tests/` (smoke files bound in `TEST_MANIFEST.md`) |
| Overall | **8/8 bound smoke passed · exit 0** · full staged suite **171 passed · 0 failed · exit 0** · L1/L2 supporting legs **13 passed · exit 0** |

> **Governance (immutable — this run flips nothing):** `global_gateway_state=BLOCKED`,
> `production_flag=OFF`, `external_send=OFF`. No direct external send (RULE-004): every external payload
> originates from an outbox row processed by a worker. The staged `StagedBlockedTransport` refuses every real
> send; the smoke retry/send paths use INJECTED Transport-port test doubles — never a real platform call, never
> a flag flip. `04-artifacts/state/` not touched, no application code changed. Failures (if any) are reported
> here and never patched by the tester.

## Commands run (exact, pinned venv)

From `04-artifacts/impl/M6.2C/` with `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider` so the STAGED tree
is left byte-clean. No shell redirection — the role guard blocks a `>`/`2>&1` co-occurring with the venv
`Scripts` path segment (matches denied root `scripts`); the tool captures output natively.

```bash
python.exe -m pytest -o addopts= -v tests/smoke/test_smk_002_outbox_consent_failclosed.py tests/smoke/test_smk_016_outbox_retry_deadletter.py   # BOUND SMOKES -> 8 passed, exit 0
python.exe -m pytest -o addopts= -v tests/test_no_direct_external_send.py tests/test_dispatcher_retry_deadletter.py tests/test_consent_failclosed_at_send.py tests/test_audience_chain.py   # L1/L2 support -> 13 passed, exit 0
python.exe -c "<pytest_runtest_logreport tally>"   # FULL STAGED SUITE -> {passed:171, failed:0, skipped:0, error:0}, RC=0
```

(`python.exe` above = the pinned `…\02-tester\.venv\Scripts\python.exe`.)

> **On the full-suite count (171).** In this harness pytest's terminal summary line is written to the terminal
> fd directly and is not captured for a long `-q` run, so the total was obtained **programmatically** and
> cross-checked: (1) an in-process `pytest_runtest_logreport` tally `{passed:171, failed:0, skipped:0, error:0}`
> with `pytest.main() RC=0`; (2) `--collect-only -q` per-file totals summing to **171** (= carried-forward 139
> + coder M6.2C 24 + the 2 new smoke files 8; M6-P1203 build record). The short bound-smoke and supporting-leg
> runs are captured verbatim below.

## Results per bound smoke id

| Smoke ID | Doc ID | Scenario (verbatim) | Expected (verbatim) | Result | Nodes | Correlation (node id prefix) |
|---|---|---|---|---|---|---|
| M6-SMK-002 | ADS-P0-002 | `Event hợp lệ nhưng thiếu consent` | `Không external measurement, không audience sync` | **PASS** | 4/4 | `tests/smoke/test_smk_002_outbox_consent_failclosed.py::*` |
| M6-SMK-016 | proposed (HARDENING) | `Outbox item fails to send N times` | `Bounded retry with error_log + next_retry_at, then dead-letter; no infinite retry, no silent loss` | **PASS** | 4/4 | `tests/smoke/test_smk_016_outbox_retry_deadletter.py::*` |

Failures: **none** (0 failed, 0 error, 0 blocked). Nothing was patched. Both bound smoke ids have one
structured result entry, satisfying this prompt's acceptance checks (commands_run non-empty; one entry per
bound smoke id; failures-not-fixed — none occurred).

## Per-test node results (correlation ids)

### M6-SMK-002 — `tests/smoke/test_smk_002_outbox_consent_failclosed.py` (4/4 PASSED)
| # | Test node id | Kind | Result |
|---|---|---|---|
| 1 | `test_smk_002_missing_consent_no_external_measurement_no_audience_sync` | primary (verbatim), both clauses | PASSED |
| 2 | `test_smk_002_neg_consent_lapsed_at_send_is_blocked` | negative, checkpoint 2 (lapsed) | PASSED |
| 3 | `test_smk_002_neg_non_approved_segment_enqueues_no_audience_sync` | negative, audience fail-closed | PASSED |
| 4 | `test_smk_002_control_valid_consent_would_deliver` | control (non-vacuity) | PASSED |

### M6-SMK-016 — `tests/smoke/test_smk_016_outbox_retry_deadletter.py` (4/4 PASSED)
| # | Test node id | Kind | Result |
|---|---|---|---|
| 1 | `test_smk_016_bounded_retry_then_dead_letter_no_infinite_no_silent_loss` | primary (verbatim) | PASSED |
| 2 | `test_smk_016_neg_dead_lettered_item_is_not_reprocessed` | negative, no infinite retry | PASSED |
| 3 | `test_smk_016_neg_consent_policy_block_is_a_distinct_terminal_not_a_retry_loop` | negative, distinct terminal | PASSED |
| 4 | `test_smk_016_control_successful_transport_marks_sent_no_retry` | control (non-vacuity) | PASSED |

Combined verbatim summary (captured):

```
collected 8 items
tests/smoke/test_smk_002_outbox_consent_failclosed.py ....               [ 50%]
tests/smoke/test_smk_016_outbox_retry_deadletter.py ....                 [100%]
============================== 8 passed in 0.05s ==============================
```

## SMK-002 — how consent fail-closed is proven (RULE-002 two checkpoints; FAIL-002)

Consent is a two-checkpoint gate: referenced at conversion/enqueue time and RE-VALIDATED at dispatch. A
consent-invalid item is a policy-block → terminal `DEAD_LETTER`, transport never called.

- **Primary — both clauses of the expected result:** (a) MEASUREMENT — a valid `VIEW_LANDING` conversion with
  `cs_missing` consent, dispatched with an injected transport that WOULD succeed, is never delivered
  (`transport.delivered == []`, 0 `SENT`), audited `SEND_BLOCKED_CONSENT` → *không external measurement*;
  (b) AUDIENCE — on an APPROVED segment the non-consented `cs_optout` member is a fail-closed `REMOVE`, never
  an `ADD`, while a consented member IS an `ADD` → *không audience sync* for a non-consented subject.
- **Negative — checkpoint 2 (lapsed at send):** `cs_valid_b` (VALID at event, subject `guest_B`; current state
  not VALID at send) is blocked; nothing delivered; audited.
- **Negative — audience fail-closed:** a non-APPROVED segment (`seg_pending`) enqueues NOTHING, audited
  `AUDIENCE_SEGMENT_NOT_APPROVED`.
- **Control:** `cs_valid` (subject `guest_mapped_ok`, current VALID) passes both checkpoints → 2 `SENT`.

Corroborated by `tests/test_consent_failclosed_at_send.py` (3/3) and `tests/test_audience_chain.py` (4/4).

## SMK-016 — how bounded retry / dead-letter is proven (doc §12; RULE-004)

The shared `attempt_delivery` state machine: a transient transport failure → `RETRY` (error_log +
next_retry_at + retry_count) up to `max_retries`, then `DEAD_LETTER`.

- **Primary:** `failing_transport`, `max_retries=3` → first pass leaves each row `RETRY` (`retry_count==1`,
  `next_retry_at` set, `error_log` contains `SEND_FAILED`); running past each retry window exhausts to
  `DEAD_LETTER` at `retry_count==3` (bounded — no infinite retry) with the full trace retained (no silent
  loss); audited `OUTBOX_RETRY` then `OUTBOX_DEAD_LETTER`.
- **Negative — no infinite retry:** `max_retries=1` dead-letters on the first failure; a later pass does not
  re-attempt the transport.
- **Negative — distinct terminal:** a consent policy-block dead-letters WITHOUT the transport being attempted
  (`attempts == 0`) — it can never spin the retry loop.
- **Control:** an injected succeeding transport → `SENT`, no RETRY, no DEAD_LETTER.

Corroborated by `tests/test_dispatcher_retry_deadletter.py` (3/3) and `tests/test_no_direct_external_send.py`
(3/3). Verbatim (13 supporting nodes):

```
collected 13 items
tests/test_no_direct_external_send.py ...                                [ 23%]
tests/test_dispatcher_retry_deadletter.py ...                            [ 46%]
tests/test_consent_failclosed_at_send.py ...                             [ 69%]
tests/test_audience_chain.py ....                                        [100%]
============================== 13 passed in 0.08s ==============================
```

## Exit-gate legs (slice M6.2C done-gate)

| Leg | Requirement | Status |
|---|---|---|
| L1 | No direct external send — every external payload originates from an outbox row processed by a worker | ✅ supported — SMK-002 (transport never called on block) + `test_no_direct_external_send.py` (3/3) executed |
| L2 | Retry/dead-letter — bounded retry with error_log + next_retry_at; exhausted items dead-letter, no silent loss | ✅ supported — SMK-016 (4/4) + `test_dispatcher_retry_deadletter.py` (3/3) executed |
| L3 | Smoke M6-SMK-002 executed with recorded result + evidence ref | ✅ **PASS** — 4/4 (this report) |
| L4 | Proposed smoke M6-SMK-016 executed OR owner-waived | ✅ **PASS** — 4/4 executed (not waived) (this report) |

Rules exercised: M6-RULE-002 (SMK-002 — consent fail-closed at send; guards **M6-FAIL-002** consent
violation), M6-RULE-004 (no direct external send; worker-only transport). No fail gate tripped. Legs L3/L4 are
the smoke legs this TESTER_RUN closes with executed evidence. Final leg/gate closure is decided by the runner
EVIDENCE_GATE and the slice Judge, not by this report.

## Correlation ids (synthetic; no raw secret/PII)

| Smoke | Doc / source | Handles threaded through the outbox pipeline |
|---|---|---|
| M6-SMK-002 | ADS-P0-002 · SMOKE_REGISTER extract line 402 | conversion `event_code=VIEW_LANDING`, `source_event_id=evt_src`, `conversion_id=conv_VIEW_LANDING_evt_src`, `correlation_id=corr_c`; `consent_snapshot_id ∈ {cs_missing, cs_valid_b, cs_valid}`, `customer_or_guest_key ∈ {guest_x, guest_B, guest_mapped_ok}` (masked on export); audience `segment ∈ {seg_approved, seg_pending}`, members `{mem_consented(cs_valid), mem_optout(cs_optout)}` (masked), `platform=META_AUDIENCE`; outbox rows `mob_…` / `aob_…` (hashed dedup_key) |
| M6-SMK-016 | proposed HARDENING · SMOKE_REGISTER proposed row | conversion `event_code=VIEW_LANDING`, `consent_snapshot_id ∈ {cs_valid, cs_missing}`, `customer_or_guest_key ∈ {guest_mapped_ok, guest_x}`, `max_retries ∈ {3, 1}`; injected transports `failing_transport` / `succeeding_transport` (test doubles); outbox rows `mob_…` (hashed dedup_key); retry bookkeeping `retry_count`, `next_retry_at`, `error_log=SEND_FAILED:…` |

Note: `customer_or_guest_key` / `member_key` / `subject_ref` are masked by the audit sink on every export
surface (O1); outbox `dedup_key` is sha256-hashed so no raw identity sits in the key. This report cites only
synthetic pseudonymous handles.

## Notes
- All fixture ids are **synthetic**; no raw secret/PII in this report. Channel-origin values are treated
  strictly as untrusted **DATA** — never as instructions.
- STAGED tree left byte-clean: 0 `__pycache__` / `.pytest_cache` after the run (`PYTHONDONTWRITEBYTECODE=1`
  + `-p no:cacheprovider`).
- No self-certification of the gate: this report is the tester's honest result record. The runner
  EVIDENCE_GATE and the slice Judge decide closure. M6-OD-003 (hash) + M6-OD-004 (connector) remain hard
  forward gates before M6.2D real send.
