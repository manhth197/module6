# TEST_MANIFEST — Slice M6.2C smoke suite (Outbox Workers)

| Field | Value |
|---|---|
| Prompt | M6-P1203 — `M6_2C_TESTER_BUILD` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — the smoke tests are AUTHORED here. This attempt also ran `pytest` as a **build-validation** (green); the **formal executed-results recording** for the exit-gate smoke legs belongs to M6-P1204. |
| Executed by (formal) | M6-P1204 (`M6_2C_TESTER_RUN`) → `04-artifacts/test-reports/M6.2C/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-002, M6-SMK-016** (exactly — per `00-spec/slices/M6.2C.md` "Core smokes" + this prompt's `<smoke_ids>`; M6-SMK-016 is `proposed — HARDENING, owner review`, executed here per done-gate leg 4) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin; `test_command = pytest -q`) |
| Slice scope | conversion_events → `marketing_measurement_outbox` + dispatcher · customer_segments → `marketing_audience_outbox` + dispatcher · `POST /api/ads/conversions` (per `00-spec/slices/M6.2C.md`, doc §5/§7/§12) |
| Staging root | `04-artifacts/impl/M6.2C/` (STAGED_ONLY; convention reference, not a live repo) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (owner P0 matrix + proposed hardening rows) |

> **Governance (immutable — nothing in this suite flips a flag):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`.
> No direct external send: every external payload originates from an outbox row processed by a worker, never
> from a runtime request (RULE-004). The staged `StagedBlockedTransport` refuses every real send; the smoke
> retry/send paths use INJECTED test-double transports (never a real platform call, never a flag flip). The
> MANDATORY M6.2G Scale-Gate re-gate remains in force before any real scale or external send; M6-OD-003 (hash)
> and M6-OD-004 (connector) are hard forward gates before M6.2D real send.

## What this suite is

The **official M6.2C smoke suite**: exactly one **primary** test per bound smoke id, carrying the register's
scenario/expected **verbatim**, driven through the M6.2C outbox pipeline — the runtime-side enqueue seam
(`enqueue_measurement` / `enqueue_audience_sync`, which hold NO transport) and the dispatcher workers
(`MeasurementDispatcher` / `AudienceDispatcher`, the only holders of a `Transport`) over the generic
`OutboxStore` — plus the negative / fail-closed companions the doc done-gate requires and a positive control
for non-vacuity. It reuses the shared fixtures in
[`tests/conftest.py`](04-artifacts/impl/M6.2C/tests/conftest.py) (`make_conversion`, `measurement_outbox`,
`audience_outbox`, `segment_reader`, `consent_gate`, `app_consent_reader`, `audit`, `succeeding_transport`,
`failing_transport`). No new production code, and **no fix to the code under test** (TESTER reports defects,
never fixes them).

All fixture ids are **synthetic**; no raw secret/PII. Outbox dedup keys are hashed and identity refs
(`customer_or_guest_key` / `member_key` / `subject_ref`) are masked on every export surface (O1).

M6.2C **carried the whole M6.2B tree forward** (which itself carried M6.2A). The carried smokes
(`test_smk_001_event_not_in_registry.py`, `test_smk_001_track_unknown_event.py`,
`test_smk_002_valid_event_missing_consent.py`, `test_smk_003_duplicate_dedup.py`) and the M6.2A/2B regression
suites remain and re-run here as supporting coverage; the two files below are the **new M6.2C-bound smokes**
authored by this prompt.

## Smoke → test binding

| Smoke ID | Doc ID | Test file (M6.2C, new) | Primary test (scenario verbatim) | Negative / fail-closed tests | Control | Rule(s) | Fail gate | Exit leg |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-002 | ADS-P0-002 | [`tests/smoke/test_smk_002_outbox_consent_failclosed.py`](04-artifacts/impl/M6.2C/tests/smoke/test_smk_002_outbox_consent_failclosed.py) | `test_smk_002_missing_consent_no_external_measurement_no_audience_sync` | `..._neg_consent_lapsed_at_send_is_blocked`, `..._neg_non_approved_segment_enqueues_no_audience_sync` | `..._control_valid_consent_would_deliver` | M6-RULE-002, M6-RULE-004 | M6-FAIL-002 | L3 (+ supports leg 1) |
| M6-SMK-016 | proposed (HARDENING) | [`tests/smoke/test_smk_016_outbox_retry_deadletter.py`](04-artifacts/impl/M6.2C/tests/smoke/test_smk_016_outbox_retry_deadletter.py) | `test_smk_016_bounded_retry_then_dead_letter_no_infinite_no_silent_loss` | `..._neg_dead_lettered_item_is_not_reprocessed`, `..._neg_consent_policy_block_is_a_distinct_terminal_not_a_retry_loop` | `..._control_successful_transport_marks_sent_no_retry` | M6-RULE-004 | — | L4 (+ supports leg 2) |

---

## M6-SMK-002 — valid event but consent missing (M6.2C outbox path)

Verbatim from `00-spec/registers/SMOKE_REGISTER.md` (extract line 402):

```
Smoke ID:          M6-SMK-002  (Doc ID ADS-P0-002)
Kịch bản:          Event hợp lệ nhưng thiếu consent
Kết quả phải đạt:  Không external measurement, không audience sync
Bound slices:      M6.2A, M6.2C, M6.2K
```

**How it is proven (RULE-002 two-checkpoint consent; FAIL-002).** Consent is referenced at conversion/enqueue
time (checkpoint 1) and RE-VALIDATED at dispatch (checkpoint 2). A consent-invalid item is a policy-block →
terminal `DEAD_LETTER`, and the transport is **never** called.

- **Primary — both clauses:** (a) a VALID `VIEW_LANDING` conversion with `cs_missing` consent, dispatched with
  an injected transport that WOULD succeed → nothing delivered (`transport.delivered == []`, 0 `SENT`), audited
  `SEND_BLOCKED_CONSENT` ("không external measurement"); (b) on an APPROVED segment, the non-consented
  (`cs_optout`) member is a fail-closed `REMOVE`, never an `ADD` ("không audience sync"), while a consented
  member IS an `ADD` (discrimination).
- **Negative — checkpoint 2 (lapsed at send):** `cs_valid_b` was VALID at event time (subject `guest_B`) but
  its current state is not VALID at send → blocked, nothing delivered, audited.
- **Negative — audience fail-closed:** a non-APPROVED segment (`seg_pending`) enqueues NOTHING, audited
  `AUDIENCE_SEGMENT_NOT_APPROVED` (membership read for sync only, never a trigger — RULE-012).
- **Positive control (non-vacuity):** `cs_valid` (subject `guest_mapped_ok`, current VALID) passes BOTH
  checkpoints → 2 `SENT` with the injected transport, proving the block is caused by *missing consent*, not a
  blanket refusal.

Prevents M6-FAIL-002 (consent violation). RULE-002 / RULE-004.

---

## M6-SMK-016 — outbox item fails to send N times (proposed — HARDENING)

Verbatim from `00-spec/registers/SMOKE_REGISTER.md` (proposed additions row):

```
Smoke ID:          M6-SMK-016  (proposed — HARDENING, owner review)
Scenario:          Outbox item fails to send N times
Expected:          Bounded retry with error_log + next_retry_at, then dead-letter; no infinite retry,
                   no silent loss
Bound slices:      M6.2C, M6.2K
```

**How it is proven (the shared `attempt_delivery` state machine; doc §12).** A TRANSIENT transport failure →
`RETRY` (error_log + next_retry_at + retry_count) up to `max_retries`, then `DEAD_LETTER`.

- **Primary:** an injected `failing_transport`, `max_retries=3` → first pass leaves each row `RETRY` with
  `retry_count==1`, a scheduled `next_retry_at`, and an `error_log` containing `SEND_FAILED`; running past each
  retry window exhausts the budget → `DEAD_LETTER` with `retry_count==3` (bounded — no infinite retry) and the
  full error trace retained (no silent loss). Audited `OUTBOX_RETRY` then `OUTBOX_DEAD_LETTER`.
- **Negative — no infinite retry:** with `max_retries=1` the first failure dead-letters; a later worker pass
  does not touch the transport again (dead-lettered rows are not due).
- **Negative — policy-block is a distinct terminal:** a consent policy-block dead-letters WITHOUT the transport
  ever being attempted (`failing_transport.attempts == 0`), so it can never spin the retry loop.
- **Positive control (non-vacuity):** an injected succeeding transport → `SENT`, no RETRY, no DEAD_LETTER —
  the primary's dead-letter is caused by the failing transport, not everything.

`M6-SMK-016` is `proposed — HARDENING (owner review)`; the M6.2C done-gate leg 4 accepts it executed OR
owner-waived — this suite **executes** it. RULE-004 (worker-only send).

---

## Supporting / regression suite (run alongside the two bound smokes)

The `pytest -q` run exercises the full staged suite. Files below (coder M6-P1202) are **not** the two bound
M6.2C smoke ids but pin the outbox pipeline the smokes rely on.

| File | Purpose | Nodes | In smoke scope? |
|---|---|---|---|
| [`tests/test_no_direct_external_send.py`](04-artifacts/impl/M6.2C/tests/test_no_direct_external_send.py) | RULE-004 leg 1 — the conversions endpoint + enqueue seam hold no transport; only workers send | 3 | No (regression) |
| [`tests/test_dispatcher_retry_deadletter.py`](04-artifacts/impl/M6.2C/tests/test_dispatcher_retry_deadletter.py) | SMK-016 retry → dead-letter regression | 3 | No (regression) |
| [`tests/test_consent_failclosed_at_send.py`](04-artifacts/impl/M6.2C/tests/test_consent_failclosed_at_send.py) | SMK-002 consent checkpoint-2 regression | 3 | No (regression) |
| [`tests/test_measurement_outbox_fanout_dedup.py`](04-artifacts/impl/M6.2C/tests/test_measurement_outbox_fanout_dedup.py) | measurement fan-out (PIXEL/CAPI/OFFLINE) + UNIQUE dedup_key | 4 | No (regression) |
| [`tests/test_conversions_endpoint.py`](04-artifacts/impl/M6.2C/tests/test_conversions_endpoint.py) | CTR-017 `POST /api/ads/conversions` contract + validation | 7 | No (regression) |
| [`tests/test_audience_chain.py`](04-artifacts/impl/M6.2C/tests/test_audience_chain.py) | audience enqueue/dispatch (ADD/REMOVE by consent) + member_key masking (O1) | 4 | No (regression) |
| carried M6.2A/2B suite | seam smokes (4+7), tracking smokes (6+4), fixfirst 10, measurement_store 4, event_registry_validation 6, identity_mapping_audit 7, ingest_measure_only 5, consent_fail_closed 6, web_event_logs_append_only 4, track_contract 9, track_dedup 4, track_unknown 6, round2 11, round3 20, round4 26 | 139 | No (carried regression) |

## Fixtures reused (from `tests/conftest.py`)

| Fixture | Role |
|---|---|
| `make_conversion(event_code, consent_snapshot_id=, customer_or_guest_key=)` | builds a `ConversionEvent` for the outbox/dispatcher unit path (bypasses the endpoint) |
| `measurement_outbox` / `audience_outbox` | generic `OutboxStore` instances (UNIQUE dedup_key; `count_status`, `all`, `due_items`) |
| `segment_reader` | CONSUMED audience chain: `seg_approved` (`mem_consented`=cs_valid → ADD, `mem_optout`=cs_optout → REMOVE), `seg_pending` (non-approved → nothing) |
| `consent_gate` / `app_consent_reader` | the hardened consent gate + staged in-memory reader (`guest_mapped_ok` current VALID) |
| `succeeding_transport` | injected Transport double that records `.delivered` and succeeds (no real platform) |
| `failing_transport` | injected Transport double that always raises a transient failure (drives SMK-016) |
| `audit` | function-scoped `AuditLog` shared across enqueue/dispatch → `audit.find(...)` sees the outcome records |

`StagedBlockedTransport` (the only transport wired in the staged slice) raises `ExternalSendBlocked` on every
attempt (external_send=OFF) — the smokes inject test-double transports so the retry/consent/success paths are
testable without a real send or a flag flip.

## Boundary / safety asserted by the suite

- **No direct external send (RULE-004):** external payloads originate only from outbox rows processed by a
  worker; the enqueue seam holds no transport; a consent-invalid item never reaches a transport.
- **Consent fail-closed at send (RULE-002):** missing / lapsed / opt-out consent → no measurement send, no
  audience ADD; every block is audited.
- **Bounded retry → dead-letter:** no infinite retry, no silent loss; a policy-block is a distinct terminal.
- **No flag flip, no real platform call, no `04-artifacts/state/` write** anywhere in the suite.

## Build + validation run performed in M6-P1203 (attempt 1, pinned interpreter)

Run with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest 8.4.2**. This attempt ran the suite (not
collect-only) as a **build-validation**; the run was **green**. Commands from `04-artifacts/impl/M6.2C/`, **no
shell redirection** (the role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path), cache-free
(`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```bash
python.exe -m pytest -v tests/smoke/test_smk_002_outbox_consent_failclosed.py tests/smoke/test_smk_016_outbox_retry_deadletter.py   # 8 passed, exit 0
python.exe -m pytest --collect-only -q                                                                                              # per-file totals (below)
python.exe -c "<pytest_runtest_logreport tally>"                                                                                    # {passed:171, failed:0, skipped:0, error:0}, RC=0
```

New M6.2C smoke node ids (8), all PASSED:

```
tests/smoke/test_smk_002_outbox_consent_failclosed.py::test_smk_002_missing_consent_no_external_measurement_no_audience_sync
tests/smoke/test_smk_002_outbox_consent_failclosed.py::test_smk_002_neg_consent_lapsed_at_send_is_blocked
tests/smoke/test_smk_002_outbox_consent_failclosed.py::test_smk_002_neg_non_approved_segment_enqueues_no_audience_sync
tests/smoke/test_smk_002_outbox_consent_failclosed.py::test_smk_002_control_valid_consent_would_deliver
tests/smoke/test_smk_016_outbox_retry_deadletter.py::test_smk_016_bounded_retry_then_dead_letter_no_infinite_no_silent_loss
tests/smoke/test_smk_016_outbox_retry_deadletter.py::test_smk_016_neg_dead_lettered_item_is_not_reprocessed
tests/smoke/test_smk_016_outbox_retry_deadletter.py::test_smk_016_neg_consent_policy_block_is_a_distinct_terminal_not_a_retry_loop
tests/smoke/test_smk_016_outbox_retry_deadletter.py::test_smk_016_control_successful_transport_marks_sent_no_retry
```

Per-file collected counts (total **171** = carried-forward 139 + coder M6.2C 24 + these new smokes 8):

```
tests/smoke/test_smk_001_event_not_in_registry.py: 4          (carried M6.2A seam smoke)
tests/smoke/test_smk_001_track_unknown_event.py: 6           (carried M6.2B smoke)
tests/smoke/test_smk_002_outbox_consent_failclosed.py: 4      (NEW — M6.2C SMK-002)
tests/smoke/test_smk_002_valid_event_missing_consent.py: 7    (carried M6.2A seam smoke)
tests/smoke/test_smk_003_duplicate_dedup.py: 4               (carried M6.2B smoke)
tests/smoke/test_smk_016_outbox_retry_deadletter.py: 4       (NEW — M6.2C SMK-016)
tests/test_audience_chain.py: 4
tests/test_consent_fail_closed.py: 6
tests/test_consent_failclosed_at_send.py: 3
tests/test_conversions_endpoint.py: 7
tests/test_dispatcher_retry_deadletter.py: 3
tests/test_event_registry_validation.py: 6
tests/test_identity_mapping_audit.py: 7
tests/test_ingest_measure_only.py: 5
tests/test_m6_2b_fixfirst_regressions.py: 10
tests/test_measurement_event_store.py: 4
tests/test_measurement_outbox_fanout_dedup.py: 4
tests/test_no_direct_external_send.py: 3
tests/test_round2_regressions.py: 11
tests/test_round3_regressions.py: 20
tests/test_round4_regressions.py: 26
tests/test_track_contract_and_validation.py: 9
tests/test_track_idempotency_dedup.py: 4
tests/test_track_unknown_event.py: 6
tests/test_web_event_logs_append_only.py: 4
```

Totals reconcile: **171** = carried-forward M6.2B tree **139** + coder M6.2C **24** + these new smokes **8**.
(The coder's M6-P1202 evidence recorded the same 163 = 139 + 24 pre-smoke; the earlier "129" for the M6.2B
tree was a terminal dot-count artifact, corrected to 139 by an in-process capture.)

Cache hygiene: after the runs, **0** `__pycache__` / `.pytest_cache` directories remain under the staged tree.

> **On the full-suite count.** In this harness pytest's terminal summary line is written to the terminal fd
> directly and is not captured for a long `-q` run, so the total (**171**) was obtained via an in-process
> `pytest_runtest_logreport` tally ({passed:171, failed:0}), `pytest.main() RC=0`, and the `--collect-only`
> per-file sum — all agreeing. The two smoke files' verbatim `8 passed` summary IS captured.

> **This build-validation run does NOT self-certify gate advancement.** It proves the smoke files import,
> collect, and pass against the frozen M6.2C code; it is the honest self-report of a TESTER build. The
> **formal executed-results recording** for the exit-gate smoke legs is produced by **M6-P1204** into
> `04-artifacts/test-reports/M6.2C/SMOKE_RESULTS.md`. The runner EVIDENCE_GATE and the slice Judge decide
> closure.

## Execution plan for M6-P1204 (`M6_2C_TESTER_RUN`)

Run the full staged suite and the two bound smokes, then record structured results + evidence refs for the
M6.2C exit-gate smoke legs:

```bash
python -m pytest -q                    # full staged suite: expected 171
python -m pytest -q tests/smoke/test_smk_002_outbox_consent_failclosed.py tests/smoke/test_smk_016_outbox_retry_deadletter.py
```

## Exit-gate legs (slice M6.2C done-gate, itemized)

| Leg | Requirement | Covered by |
|---|---|---|
| L1 | No direct external send — every external payload originates from an outbox row processed by a worker | SMK-002 (transport never called on block) + `test_no_direct_external_send.py` (3/3) |
| L2 | Retry/dead-letter — bounded retry with error_log + next_retry_at; exhausted items dead-letter, no silent loss | SMK-016 (4/4) + `test_dispatcher_retry_deadletter.py` (3/3) |
| L3 | Smoke M6-SMK-002 executed with recorded result + evidence ref | closed by M6-P1204 (this suite built here) |
| L4 | Proposed smoke M6-SMK-016 executed OR owner-waived | executed here (not waived); closed by M6-P1204 |

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-002 | Consent fail-closed: without valid consent → no external measurement, no audience sync (SMK-002 guards; two checkpoints in M6.2C). |
| M6-RULE-004 | Runtime/external separation: no direct external send; only the dispatcher workers hold a transport (SMK-002/016 support). |
| M6-FAIL-002 | Consent violation — external measurement/audience sync without consent (SMK-002 guards). |
| Exit legs | L1 no-direct-send, L2 retry/dead-letter, L3 SMK-002 executed, L4 SMK-016 executed/waived (`00-spec/slices/M6.2C.md`). |

## Provenance / notes

- Scenario & expected text quoted **verbatim** from `00-spec/registers/SMOKE_REGISTER.md` (row M6-SMK-002 and
  the proposed M6-SMK-016 row). Test patterns reused from the existing `tests/conftest.py`,
  `tests/test_consent_failclosed_at_send.py`, `tests/test_dispatcher_retry_deadletter.py`, and
  `tests/test_audience_chain.py` (doc working mode, extract line 466).
- No self-certification of PASS or of gate/leg advancement: the runner EVIDENCE_GATE and the slice Judge
  decide. This manifest and the two smoke files are the *build*; the formal executed results are produced in
  M6-P1204.
