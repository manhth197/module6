# TEST_MANIFEST — Slice M6.2D smoke suite (Pixel/CAPI/Offline Dedup + Hash Policy)

| Field | Value |
|---|---|
| Prompt | M6-P1303 — `M6_2D_TESTER_BUILD` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — the smoke tests are AUTHORED here. This attempt also ran `pytest` as a **build-validation** (green); the **formal executed-results recording** for the exit-gate smoke legs belongs to M6-P1304. |
| Executed by (formal) | M6-P1304 (`M6_2D_TESTER_RUN`) → `04-artifacts/test-reports/M6.2D/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-003, M6-SMK-017** (exactly — per `00-spec/slices/M6.2D.md` "Core smokes" + this prompt's `<smoke_ids>`; M6-SMK-017 is `proposed — HARDENING, owner review`, executed here per done-gate leg 4) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin; `test_command = pytest -q`) |
| Slice scope | platform send discipline — locked `dedup_key`/`event_id`, hash policy, offline-after-ORDER_VERIFIED, platform result logs (per `00-spec/slices/M6.2D.md`, doc §12) |
| Staging root | `04-artifacts/impl/M6.2D/` (STAGED_ONLY; convention reference, not a live repo) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (owner P0 matrix + proposed hardening rows) |

> **Governance (immutable — nothing in this suite flips a flag):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`.
> The staged `StagedPlatformTransport` BUILDS a PII-safe payload and LOGS a result, then raises
> `ExternalSendBlocked` — NO real platform send, ever. **M6-OD-003 (hash policy / ratified raw-field list) is
> OPEN** → the raw allow-list is empty and `HASH_POLICY_RATIFIED=False` (fail-closed: nothing raw is emitted).
> Done-gate leg 2 (no PII thô) proves the MECHANISM; the ratified field list remains a forward gate.
> M6-OD-004 (connector) and the MANDATORY M6.2G Scale-Gate re-gate remain in force before any real send.

## What this suite is

The **official M6.2D smoke suite**: exactly one **primary** test per bound smoke id, carrying the register's
scenario/expected **verbatim**, driven through the M6.2D integration layer — `build_platform_payload`
(shared platform `event_id` for cross-platform dedup + hashed identity), the `StagedPlatformTransport` wired
into the `MeasurementDispatcher`, and the PII-safe `PlatformResultLog` — plus the negative / fail-closed
companions the doc done-gate requires and a positive control for non-vacuity. It reuses the shared fixtures in
[`tests/conftest.py`](04-artifacts/impl/M6.2D/tests/conftest.py) (`conversion_deps`, `make_conversion_body`,
`make_conversion`, `measurement_outbox`, `consent_gate`, `app_consent_reader`, `audit`, `platform_transport`,
`platform_result_log`). No new production code, and **no fix to the code under test** (TESTER reports defects,
never fixes them).

All identity markers are **synthetic**; no raw secret/PII. The SMK-017 raw-PII markers (email / phone / user-id
shapes) are **assembled at runtime from fragments** so no literal PII sits in the test source (the pack
post-write secret scan forbids literal email/phone/user-id). Identity is hashed in payloads and masked on
export (O1).

M6.2D **carried the whole M6.2C tree forward** (cumulatively M6.2A/2B/2C). The carried smokes and regression
suites remain and re-run here as supporting coverage; the two files below are the **new M6.2D-bound smokes**
authored by this prompt.

## Smoke → test binding

| Smoke ID | Doc ID | Test file (M6.2D, new) | Primary test (scenario verbatim) | Negative / fail-closed tests | Control | Rule(s) | Fail gate | Exit leg |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-003 | ADS-P0-003 | [`tests/smoke/test_smk_003_platform_dedup.py`](04-artifacts/impl/M6.2D/tests/smoke/test_smk_003_platform_dedup.py) | `test_smk_003_pixel_and_capi_of_one_event_dedup_no_double_count` | `..._neg_offline_for_order_verified_shares_the_same_event_id`, `..._neg_replayed_conversion_is_not_re_enqueued` | `..._control_distinct_source_events_get_distinct_event_ids` | M6-RULE-005, M6-RULE-003 | M6-FAIL-001 | L3 (+ supports leg 1) |
| M6-SMK-017 | proposed (HARDENING) | [`tests/smoke/test_smk_017_hash_policy_no_raw_pii.py`](04-artifacts/impl/M6.2D/tests/smoke/test_smk_017_hash_policy_no_raw_pii.py) | `test_smk_017_no_raw_pii_in_external_payload_or_platform_result_log` | `..._neg_each_pii_shape_is_hashed_not_emitted_raw` (parametrized: 3 platforms × 3 PII shapes = 9), `..._neg_hash_policy_is_fail_closed_while_od003_open` | `..._control_hash_transforms_and_is_deterministic` | M6-RULE-014 | M6-FAIL-008 | L4 (+ supports leg 2) |

---

## M6-SMK-003 — Pixel/CAPI/Offline dedup, no double count

Verbatim from `00-spec/registers/SMOKE_REGISTER.md` (extract line 403):

```
Smoke ID:          M6-SMK-003  (Doc ID ADS-P0-003)
Kịch bản:          Duplicate Pixel/CAPI/Offline
Kết quả phải đạt:  Dedup, không double count
Bound slices:      M6.2B, M6.2D, M6.2K
```

**How it is proven (FAIL-001; RULE-005).** `event_id = hash(source_event_id + event_code)` is **shared** across
PIXEL / CAPI / OFFLINE of ONE source event, so the platform (Meta) collapses them → counted once, not once per
platform. The internal `dedup_key` stays UNIQUE per (conversion × platform).

- **Primary:** one `VIEW_LANDING` conversion fans out to PIXEL + CAPI; after dispatch the `PlatformResultLog`
  holds 2 records (`{PIXEL, CAPI}`) that share **one** `event_id` (platform dedup — no double count), while the
  outbox holds 2 rows with **distinct** internal `dedup_key`s.
- **Negative — the Offline arm:** for an ORDER_VERIFIED source, PIXEL, CAPI and OFFLINE all build the SAME
  shared `event_id` (all three dedup to one platform-side event — no triple count).
- **Negative — endpoint replay:** a replayed identical conversion is DUPLICATE, does not re-enqueue (the outbox
  stays at 2 rows — no double count, RULE-005).
- **Positive control (non-vacuity):** two DIFFERENT source events get DIFFERENT `event_id`s (deterministic and
  stable), so the shared-id dedup collapses true duplicates only.

Prevents M6-FAIL-001 (double count). RULE-005 / RULE-003.

---

## M6-SMK-017 — external payload with raw PII → hash policy, no raw PII out (proposed — HARDENING)

Verbatim from `00-spec/registers/SMOKE_REGISTER.md` (proposed additions row):

```
Smoke ID:          M6-SMK-017  (proposed — HARDENING, owner review)
Scenario:          External payload (CAPI/Offline) built from an event containing raw PII
Expected:          Hash policy applied per M6-OD-003; no raw phone/email/user-id in the outbound payload or
                   platform result log
Bound slices:      M6.2D, M6.2K
```

**How it is proven (FAIL-008; RULE-014).** The hash-policy MECHANISM hashes every identity field one-way; with
M6-OD-003 OPEN the raw allow-list is empty and `HASH_POLICY_RATIFIED=False`, so nothing is ever emitted raw
(fail-closed). The MECHANISM is what this proves; the ratified field list is the forward gate (leg 2
conditionally blocked on M6-OD-003).

- **Primary — end-to-end:** a conversion carrying a raw-PII identity is driven through the endpoint + the staged
  transport. (a) the `PlatformResultLog` the transport writes carries NO raw PII; (b) the payload the transport
  WOULD hand a connector hashes every identity field (`user_data` values start with `h_`) — the raw value never
  appears, and the field is hashed (not silently dropped).
- **Negative — every PII shape on every platform:** parametrized over {email-shaped, phone-shaped,
  user-id-shaped} × {PIXEL, CAPI, OFFLINE} (9 nodes) — each raw value is hashed, never emitted raw.
- **Negative — fail-closed policy:** `HASH_POLICY_RATIFIED is False`; `to_public_safe` hashes EVERY field
  regardless of name (empty raw allow-list) — nothing raw leaves.
- **Positive control (non-vacuity):** the hash actually TRANSFORMS the value (output ≠ input), is deterministic
  (a stable platform-side identity), and maps distinct identities to distinct hashes — so "no raw PII" is
  achieved by hashing, not by vacuously emitting nothing.

`M6-SMK-017` is `proposed — HARDENING (owner review)`; the M6.2D done-gate leg 4 accepts it executed OR
owner-waived — this suite **executes** it. RULE-014 (no raw PII / hash policy).

---

## Supporting / regression suite (run alongside the two bound smokes)

The `pytest -q` run exercises the full staged suite. Files below (coder M6-P1302) are **not** the two bound
M6.2D smoke ids but pin the send-discipline pipeline the smokes rely on.

| File | Purpose | Nodes | In smoke scope? |
|---|---|---|---|
| [`tests/test_platform_dedup_event_id.py`](04-artifacts/impl/M6.2D/tests/test_platform_dedup_event_id.py) | SMK-003 shared-event_id dedup regression (endpoint → result log) | 4 | No (regression) |
| [`tests/test_hash_policy_no_raw_pii.py`](04-artifacts/impl/M6.2D/tests/test_hash_policy_no_raw_pii.py) | SMK-017 hash-policy / no-raw-PII regression | 3 | No (regression) |
| [`tests/test_offline_after_order_verified.py`](04-artifacts/impl/M6.2D/tests/test_offline_after_order_verified.py) | RULE-003 — OFFLINE refused for a non-ORDER_VERIFIED source | 2 | No (regression) |
| [`tests/test_staged_no_real_send.py`](04-artifacts/impl/M6.2D/tests/test_staged_no_real_send.py) | staged transport builds + logs but blocks (external_send=OFF) | 1 | No (regression) |
| [`tests/test_m6_2d_fixfirst_regressions.py`](04-artifacts/impl/M6.2D/tests/test_m6_2d_fixfirst_regressions.py) | fix-first F-A/F-B/F-C (consent gate scope membership, member↔consent subject binding, reader-exception wrapping) | 4 | No (regression) |
| carried M6.2A/2B/2C suite | seam/tracking/outbox smokes + all unit + regression suites | 171 | No (carried regression) |

## Fixtures reused (from `tests/conftest.py`)

| Fixture | Role |
|---|---|
| `conversion_deps` | `POST /api/ads/conversions` deps (validator + `conversion_store` + `measurement_outbox` + audit) |
| `make_conversion_body` / `make_conversion` | builders for a conversions request body / a `ConversionEvent` |
| `platform_transport` | `StagedPlatformTransport` wired with the SAME `conversion_store` the endpoint writes to — builds + logs + blocks |
| `platform_result_log` | `PlatformResultLog` (PII-safe records: platform, event_id, event_name, dedup_key, result) |
| `measurement_outbox` | `OutboxStore` (per-platform rows, UNIQUE internal `dedup_key`) |
| `consent_gate` / `app_consent_reader` / `audit` | hardened consent gate + staged reader + shared audit sink |

## Boundary / safety asserted by the suite

- **No double count (FAIL-001):** Pixel/CAPI/Offline of one source event share the platform `event_id`; a
  replayed conversion never re-enqueues.
- **No raw PII (FAIL-008, RULE-014):** every identity field is hashed; nothing raw appears in any built payload
  or platform result log; fail-closed while M6-OD-003 is OPEN.
- **Offline discipline (RULE-003):** OFFLINE only after ORDER_VERIFIED (transport guard, defense-in-depth).
- **No real send, no flag flip, no `04-artifacts/state/` write** anywhere in the suite (staged transport blocks).

## Build + validation run performed in M6-P1303 (attempt 1, pinned interpreter)

Run with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest 8.4.2**. This attempt ran the suite (not
collect-only) as a **build-validation**; the run was **green**. Commands from `04-artifacts/impl/M6.2D/`, **no
shell redirection** (the role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path), cache-free
(`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```bash
python.exe -m pytest -v tests/smoke/test_smk_003_platform_dedup.py tests/smoke/test_smk_017_hash_policy_no_raw_pii.py   # 16 passed, exit 0
python.exe -m pytest --collect-only -q                                                                                  # per-file totals (below)
python.exe -c "<pytest_runtest_logreport tally>"                                                                        # {passed:201, failed:0, skipped:0, error:0}, RC=0
```

New M6.2D smoke node counts (16), all PASSED: `test_smk_003_platform_dedup.py` = 4;
`test_smk_017_hash_policy_no_raw_pii.py` = 12 (primary 1 + `neg_each_pii_shape_is_hashed_not_emitted_raw`
parametrized 3×3 = 9 + `neg_hash_policy_is_fail_closed_while_od003_open` 1 + control 1). The parametrized
SMK-017 node ids carry the runtime-assembled PII-shaped marker values as their param labels; those literals are
NOT reproduced in this manifest (they would trip the pack secret scan) — see the test source for the shapes.

Per-file collected counts (total **201** = carried-forward 185 + these new smokes 16):

```
tests/smoke/test_smk_001_event_not_in_registry.py: 4          (carried M6.2A)
tests/smoke/test_smk_001_track_unknown_event.py: 6           (carried M6.2B)
tests/smoke/test_smk_002_outbox_consent_failclosed.py: 4      (carried M6.2C)
tests/smoke/test_smk_002_valid_event_missing_consent.py: 7    (carried M6.2A)
tests/smoke/test_smk_003_duplicate_dedup.py: 4               (carried M6.2B — endpoint replay dedup)
tests/smoke/test_smk_003_platform_dedup.py: 4               (NEW — M6.2D SMK-003, platform dedup)
tests/smoke/test_smk_016_outbox_retry_deadletter.py: 4       (carried M6.2C)
tests/smoke/test_smk_017_hash_policy_no_raw_pii.py: 12       (NEW — M6.2D SMK-017)
tests/test_platform_dedup_event_id.py: 4
tests/test_hash_policy_no_raw_pii.py: 3
tests/test_offline_after_order_verified.py: 2
tests/test_staged_no_real_send.py: 1
tests/test_m6_2d_fixfirst_regressions.py: 4
... + the carried M6.2C unit/regression suites (unchanged) = 201 total
```

Reconciliation: **201** = carried-forward M6.2C tree **185** (171 M6.2C + 14 M6.2D coder integration tests) +
these new smokes **16**.

Cache hygiene: after the runs, **0** `__pycache__` / `.pytest_cache` directories remain under the staged tree.

> **On the full-suite count.** In this harness pytest's terminal summary line is written to the terminal fd
> directly and is not captured for a long `-q` run, so the total (**201**) was obtained via an in-process
> `pytest_runtest_logreport` tally ({passed:201, failed:0}), `pytest.main() RC=0`, and the `--collect-only`
> per-file sum — all agreeing. The two smoke files' verbatim `16 passed` summary IS captured.

> **This build-validation run does NOT self-certify gate advancement.** It proves the smoke files import,
> collect, and pass against the frozen M6.2D code; it is the honest self-report of a TESTER build. The
> **formal executed-results recording** for the exit-gate smoke legs is produced by **M6-P1304** into
> `04-artifacts/test-reports/M6.2D/SMOKE_RESULTS.md`. The runner EVIDENCE_GATE and the slice Judge decide
> closure. Done-gate leg 2 (no PII thô) stays CONDITIONALLY BLOCKED on M6-OD-003 for the ratified raw-field
> list; the MECHANISM is proven here.

## Execution plan for M6-P1304 (`M6_2D_TESTER_RUN`)

Run the full staged suite and the two bound smokes, then record structured results + evidence refs for the
M6.2D exit-gate smoke legs:

```bash
python -m pytest -q                    # full staged suite: expected 201
python -m pytest -q tests/smoke/test_smk_003_platform_dedup.py tests/smoke/test_smk_017_hash_policy_no_raw_pii.py
```

## Exit-gate legs (slice M6.2D done-gate, itemized)

| Leg | Requirement | Covered by |
|---|---|---|
| L1 | No double count — duplicate Pixel/CAPI/Offline collapse via the locked dedup; result logs prove single delivery | SMK-003 (4/4) + `test_platform_dedup_event_id.py` (4/4) |
| L2 | No PII thô — no raw PII in any external payload or result log; hash policy per M6-OD-003 (conditionally blocked on that decision for the ratified field list) | SMK-017 (12/12) + `test_hash_policy_no_raw_pii.py` (3/3) — MECHANISM proven; ratified list = forward gate |
| L3 | Smoke M6-SMK-003 executed with recorded result + evidence ref | closed by M6-P1304 (built here) |
| L4 | Proposed smoke M6-SMK-017 executed OR owner-waived | executed here (not waived); closed by M6-P1304 |

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-005 | Locked idempotency / dedup formulas; duplicates collapse — no double count (SMK-003 guards). |
| M6-RULE-014 | No raw PII outbound; hash policy applied — nothing raw in payloads/result logs (SMK-017 guards). |
| M6-RULE-003 | Offline / revenue only after ORDER_VERIFIED (SMK-003 Offline arm + supporting `test_offline_after_order_verified.py`). |
| M6-FAIL-001 | Double count — the same conversion counted more than once (SMK-003 guards). |
| M6-FAIL-002 | Consent violation — carried-forward two-checkpoint consent still exercised in the suite. |
| M6-FAIL-008 | Raw PII leaves the boundary (SMK-017 guards). |
| Exit legs | L1 no-double-count, L2 no-PII-thô, L3 SMK-003 executed, L4 SMK-017 executed/waived (`00-spec/slices/M6.2D.md`). |

## Provenance / notes

- Scenario & expected text quoted **verbatim** from `00-spec/registers/SMOKE_REGISTER.md` (row M6-SMK-003 and
  the proposed M6-SMK-017 row). Test patterns reused from the existing `tests/conftest.py`,
  `tests/test_platform_dedup_event_id.py`, and `tests/test_hash_policy_no_raw_pii.py` (doc working mode,
  extract line 466).
- No self-certification of PASS or of gate/leg advancement: the runner EVIDENCE_GATE and the slice Judge
  decide. This manifest and the two smoke files are the *build*; the formal executed results are produced in
  M6-P1304.
