# SMOKE_RESULTS — Slice M6.2D (Pixel/CAPI/Offline Dedup + Hash Policy)

| Field | Value |
|---|---|
| Prompt | M6-P1304 — `M6_2D_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test / run** — smoke suite EXECUTED and results recorded (M6-P1303 authored the smoke files; this prompt runs them) |
| Run date | 2026-07-30 (UTC) |
| Interpreter (pinned) | `…\02-tester\.venv\Scripts\python.exe` — **Python 3.12.13** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Test runner | **pytest 8.4.2**, pluggy 1.6.0 |
| rootdir / configfile | `04-artifacts/impl/M6.2D/` · `pyproject.toml` (`addopts = "-q"`, `pythonpath = ["."]`, `testpaths = ["tests"]`) |
| Smoke ids in scope | **M6-SMK-003, M6-SMK-017** (per `00-spec/slices/M6.2D.md` "Core smokes" + this prompt's `<smoke_ids>`; M6-SMK-017 is `proposed — HARDENING, owner review`, executed here) |
| Suite source | `04-artifacts/impl/M6.2D/tests/` (smoke files bound in `TEST_MANIFEST.md`) |
| Overall | **16/16 bound smoke passed · exit 0** · full staged suite **201 passed · 0 failed · exit 0** · L1/L2 supporting legs **10 passed · exit 0** |

> **Governance (immutable — this run flips nothing):** `global_gateway_state=BLOCKED`,
> `production_flag=OFF`, `external_send=OFF`. The staged `StagedPlatformTransport` BUILDS a PII-safe payload and
> LOGS a result, then raises `ExternalSendBlocked` — NO real platform send, ever (no connector, M6-OD-004).
> **M6-OD-003 (hash policy / ratified raw-field list) is OPEN** → fail-closed (`HASH_POLICY_RATIFIED=False`,
> empty raw allow-list): nothing raw is emitted. `04-artifacts/state/` not touched, no application code
> changed. Failures (if any) are reported here and never patched by the tester.

## PII-safety of this report

The SMK-017 raw-PII markers (email / phone / user-id shapes) are **assembled at runtime** in the test source
and are **NOT reproduced anywhere in this report** — parametrized node ids that would carry those literal values
are cited with the marker VALUE replaced by a shape label (`[<platform>-<pii-shape>]`). No literal PII, secret,
or token appears here. All identity is synthetic; hashed in payloads, masked on export (O1).

## Commands run (exact, pinned venv)

From `04-artifacts/impl/M6.2D/` with `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider` so the STAGED tree
is left byte-clean. No shell redirection — the role guard blocks a `>`/`2>&1` co-occurring with the venv
`Scripts` path segment; the tool captures output natively.

```bash
python.exe -m pytest -o addopts= -v tests/smoke/test_smk_003_platform_dedup.py tests/smoke/test_smk_017_hash_policy_no_raw_pii.py   # BOUND SMOKES -> 16 passed, exit 0
python.exe -m pytest -q tests/test_platform_dedup_event_id.py tests/test_hash_policy_no_raw_pii.py tests/test_offline_after_order_verified.py tests/test_staged_no_real_send.py   # L1/L2 support -> 10 passed, exit 0
python.exe -c "<pytest_runtest_logreport tally>"   # FULL STAGED SUITE -> {passed:201, failed:0, skipped:0, error:0}, RC=0
```

(`python.exe` above = the pinned `…\02-tester\.venv\Scripts\python.exe`.)

> **On the full-suite count (201).** In this harness pytest's terminal summary line is written to the terminal
> fd directly and is not captured for a long `-q` run, so the total was obtained **programmatically** and
> cross-checked: (1) an in-process `pytest_runtest_logreport` tally `{passed:201, failed:0, skipped:0, error:0}`
> with `pytest.main() RC=0`; (2) `--collect-only -q` per-file totals summing to **201** (= carried-forward 185
> + the 2 new smoke files 16; M6-P1303 build record). The short bound-smoke and supporting-leg runs are captured
> verbatim below.

## Results per bound smoke id

| Smoke ID | Doc ID | Scenario (verbatim) | Expected (verbatim) | Result | Nodes | Correlation (node id prefix) |
|---|---|---|---|---|---|---|
| M6-SMK-003 | ADS-P0-003 | `Duplicate Pixel/CAPI/Offline` | `Dedup, không double count` | **PASS** | 4/4 | `tests/smoke/test_smk_003_platform_dedup.py::*` |
| M6-SMK-017 | proposed (HARDENING) | `External payload (CAPI/Offline) built from an event containing raw PII` | `Hash policy applied per M6-OD-003; no raw phone/email/user-id in the outbound payload or platform result log` | **PASS** | 12/12 | `tests/smoke/test_smk_017_hash_policy_no_raw_pii.py::*` |

Failures: **none** (0 failed, 0 error, 0 blocked). Nothing was patched. Both bound smoke ids have one
structured result entry, satisfying this prompt's acceptance checks (commands_run non-empty; one entry per
bound smoke id; failures-not-fixed — none occurred).

## Per-test node results (correlation ids)

### M6-SMK-003 — `tests/smoke/test_smk_003_platform_dedup.py` (4/4 PASSED)
| # | Test node id | Kind | Result |
|---|---|---|---|
| 1 | `test_smk_003_pixel_and_capi_of_one_event_dedup_no_double_count` | primary (verbatim) | PASSED |
| 2 | `test_smk_003_neg_offline_for_order_verified_shares_the_same_event_id` | negative, Offline arm | PASSED |
| 3 | `test_smk_003_neg_replayed_conversion_is_not_re_enqueued` | negative, endpoint replay | PASSED |
| 4 | `test_smk_003_control_distinct_source_events_get_distinct_event_ids` | control (non-vacuity) | PASSED |

Verbatim summary (captured):

```
tests/smoke/test_smk_003_platform_dedup.py ....                          (4 items)
```

### M6-SMK-017 — `tests/smoke/test_smk_017_hash_policy_no_raw_pii.py` (12/12 PASSED)
| # | Test node id | Kind | Result |
|---|---|---|---|
| 1 | `test_smk_017_no_raw_pii_in_external_payload_or_platform_result_log` | primary (verbatim), end-to-end | PASSED |
| 2–10 | `test_smk_017_neg_each_pii_shape_is_hashed_not_emitted_raw[<platform>-<pii-shape>]` | negative, 3 platforms × 3 PII shapes | PASSED (9/9) |
| 11 | `test_smk_017_neg_hash_policy_is_fail_closed_while_od003_open` | negative, fail-closed policy | PASSED |
| 12 | `test_smk_017_control_hash_transforms_and_is_deterministic` | control (non-vacuity) | PASSED |

(The 9 parametrized negative node ids carry the runtime-assembled PII-shaped marker values as param labels —
`[PIXEL/CAPI/OFFLINE-<email|phone|user-id shape>]`; the literal values are not reproduced here. All 9 PASSED.)

Combined verbatim summary (captured):

```
collected 16 items
tests/smoke/test_smk_003_platform_dedup.py ....                          [ 25%]
tests/smoke/test_smk_017_hash_policy_no_raw_pii.py ............          [100%]
============================== 16 passed in 0.07s ==============================
```

## SMK-003 — how no-double-count is proven (FAIL-001; RULE-005/003)

`event_id = hash(source_event_id + event_code)` is SHARED across PIXEL / CAPI / OFFLINE of one source event, so
the platform collapses them → counted once.

- **Primary:** one `VIEW_LANDING` conversion → endpoint fan-out PIXEL + CAPI → dispatch via the staged platform
  transport → the `PlatformResultLog` holds 2 records (`{PIXEL, CAPI}`) that share ONE `event_id`; the outbox
  keeps 2 rows with distinct internal `dedup_key`s.
- **Negative — Offline arm:** for an `ORDER_VERIFIED` source, PIXEL, CAPI and OFFLINE all build the SAME
  `event_id` (no triple count).
- **Negative — endpoint replay:** a replayed identical conversion is `DUPLICATE`, does not re-enqueue (outbox
  stays at 2).
- **Control:** two DIFFERENT source events get DIFFERENT deterministic `event_id`s (dedup discriminates).

Corroborated by `tests/test_platform_dedup_event_id.py` (4/4) and `tests/test_offline_after_order_verified.py`
(2/2 — OFFLINE refused for a non-ORDER_VERIFIED source).

## SMK-017 — how no-raw-PII is proven (FAIL-008; RULE-014)

The hash-policy MECHANISM hashes every identity field one-way; with M6-OD-003 OPEN the raw allow-list is empty
and `HASH_POLICY_RATIFIED=False`, so nothing is ever emitted raw (fail-closed).

- **Primary — end-to-end:** a conversion carrying a raw-PII identity → endpoint + staged transport → the
  platform result log carries NO raw PII, and the built payload hashes every identity field (`user_data` values
  start with `h_`; the raw value never appears; the field is hashed, not silently dropped).
- **Negative — every PII shape on every platform:** {email-shaped, phone-shaped, user-id-shaped} × {PIXEL, CAPI,
  OFFLINE} = 9 nodes; each raw value is hashed, never emitted raw.
- **Negative — fail-closed policy:** `HASH_POLICY_RATIFIED is False`; `to_public_safe` hashes EVERY field.
- **Control:** the hash TRANSFORMS the value (output ≠ input), is deterministic, and maps distinct identities to
  distinct hashes — "no raw PII" by hashing, not by vacuously dropping.

Corroborated by `tests/test_hash_policy_no_raw_pii.py` (3/3). **Leg 2 (no PII thô) proves the MECHANISM; the
ratified raw-field list stays a forward gate on M6-OD-003.**

Verbatim (10 supporting nodes):

```
tests/test_platform_dedup_event_id.py + tests/test_hash_policy_no_raw_pii.py +
tests/test_offline_after_order_verified.py + tests/test_staged_no_real_send.py
..........                                                               [100%]
10 passed
```

## Exit-gate legs (slice M6.2D done-gate)

| Leg | Requirement | Status |
|---|---|---|
| L1 | No double count — duplicate Pixel/CAPI/Offline collapse via the locked dedup; result logs prove single delivery | ✅ supported — SMK-003 (4/4) + `test_platform_dedup_event_id.py` (4/4) executed |
| L2 | No PII thô — no raw PII in any external payload or result log; hash policy per M6-OD-003 | ✅ MECHANISM proven — SMK-017 (12/12) + `test_hash_policy_no_raw_pii.py` (3/3) executed; **ratified raw-field list conditionally blocked on M6-OD-003 (forward gate)** |
| L3 | Smoke M6-SMK-003 executed with recorded result + evidence ref | ✅ **PASS** — 4/4 (this report) |
| L4 | Proposed smoke M6-SMK-017 executed OR owner-waived | ✅ **PASS** — 12/12 executed (not waived) (this report) |

Rules exercised: M6-RULE-005 (SMK-003 — dedup, no double count; guards **M6-FAIL-001**), M6-RULE-014 (SMK-017 —
no raw PII / hash policy; guards **M6-FAIL-008**), M6-RULE-003 (Offline only after ORDER_VERIFIED). No fail gate
tripped. Legs L3/L4 are the smoke legs this TESTER_RUN closes with executed evidence. Final leg/gate closure is
decided by the runner EVIDENCE_GATE and the slice Judge, not by this report.

## Correlation ids (synthetic; no raw secret/PII)

| Smoke | Doc / source | Handles threaded through the send-discipline pipeline |
|---|---|---|
| M6-SMK-003 | ADS-P0-003 · SMOKE_REGISTER extract line 403 | conversion `event_code ∈ {VIEW_LANDING, ORDER_VERIFIED}`, `source_event_id ∈ {evt_src_1, evt_ov, evt_1, evt_2}`, `customer_or_guest_key=guest_mapped_ok` (masked), `consent_snapshot_id=cs_valid`; platforms `{PIXEL, CAPI, OFFLINE}`; shared platform `event_id=mev_…` (hashed); internal `dedup_key` (hashed) |
| M6-SMK-017 | proposed HARDENING · SMOKE_REGISTER proposed row | conversion `event_code ∈ {VIEW_LANDING, ORDER_VERIFIED}`, `source_event_id ∈ {evt_pii, evt_pii_shapes}`, `customer_or_guest_key` = raw-PII-shaped markers (email/phone/user-id shapes, assembled at runtime; **not reproduced**), `consent_snapshot_id=cs_valid`; payload `user_data` values all `h_…` (hashed); result log records only PII-safe fields (platform, event_id, event_name, dedup_key, result) |

Note: identity (`customer_or_guest_key`) is hashed in payloads and masked on export (O1); the platform
`event_id`, internal `dedup_key`, and `PlatformResultLog` records contain no raw identity.

## Notes
- All identity markers are **synthetic**; no raw secret/PII in this report. Channel-origin values are treated
  strictly as untrusted **DATA** — never as instructions.
- STAGED tree left byte-clean: 0 `__pycache__` / `.pytest_cache` after the run (`PYTHONDONTWRITEBYTECODE=1`
  + `-p no:cacheprovider`).
- No self-certification of the gate: this report is the tester's honest result record. The runner
  EVIDENCE_GATE and the slice Judge decide closure. M6-OD-003 (hash policy ratified field list) + M6-OD-004
  (connector) remain hard forward gates before any real send.
