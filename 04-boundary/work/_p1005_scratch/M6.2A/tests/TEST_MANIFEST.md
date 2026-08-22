# TEST_MANIFEST — Slice M6.2A smoke suite

| Field | Value |
|---|---|
| Prompt | M6-P1003 — `M6_2A_TESTER_BUILD` |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — tests are AUTHORED here; **not executed** ("do not yet run") |
| Executed by | M6-P1004 (`M6_2A_TESTER_RUN`) → `04-artifacts/test-reports/M6.2A/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-001, M6-SMK-002** (exactly — per `00-spec/slices/M6.2A.md` "Core smokes" + this prompt's `<smoke_ids>`) |
| Target manifest | python 3.12 · `pytest -q` (staged; verify env is python 3.11, code is 3.11-compatible) |
| Staging root | `04-artifacts/impl/M6.2A/` (STAGED_ONLY; convention reference, not a live repo) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (owner P0 matrix, doc §21) |

> **Governance (immutable — nothing in this suite flips a flag):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`.
> This slice proves capability with evidence only. The ENTRY-001/ENTRY-003 owner risk-acceptance
> and the MANDATORY M6.2G Scale-Gate re-gate remain in force before any real scale or external send.

## What this suite is

The **official smoke suite** for slice M6.2A: exactly one primary test per bound smoke id, carrying the
register's scenario/expected **verbatim**, driven **end-to-end through the real ingest seam**
(`app.measurement.ingest.IngestService`), plus the negative / fail-closed companions the doc done-gate
requires. It reuses the existing test fixtures in
[`tests/conftest.py`](04-artifacts/impl/M6.2A/tests/conftest.py) (in-memory TEST DOUBLES for the CONSUMED
`event_registry` / `guest_contacts` / `guest_marketing_consent_snapshot`) — no new production code, no fix
to the code under test (TESTER reports, never fixes).

All fixture ids are **synthetic**; no raw secret/PII. `event_code` and `session_id` are channel-origin,
untrusted DATA — treated as data only; identity values are masked by the audit sink at the boundary.

## Smoke → test binding

| Smoke ID | Doc ID | Test file | Primary test (scenario verbatim) | Negative / fail-closed tests | Control | Rule(s) | Fail gate | Exit leg |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-001 | ADS-P0-001 | [`tests/smoke/test_smk_001_event_not_in_registry.py`](04-artifacts/impl/M6.2A/tests/smoke/test_smk_001_event_not_in_registry.py) | `test_smk_001_event_not_in_event_registry_is_rejected_with_audit` | `..._neg_deregistered_event_is_held_not_false_allowed`, `..._neg_registered_but_missing_owner_is_held` | `..._control_known_active_event_is_accepted_and_logged` | M6-RULE-001, M6-RULE-018 | M6-FAIL-003 | L1 |
| M6-SMK-002 | ADS-P0-002 | [`tests/smoke/test_smk_002_valid_event_missing_consent.py`](04-artifacts/impl/M6.2A/tests/smoke/test_smk_002_valid_event_missing_consent.py) | `test_smk_002_valid_event_missing_consent_no_external_measurement_no_audience_sync` | `..._neg_non_valid_consent_blocks_every_egress_scope[cs_missing / cs_expired / cs_optout]`, `..._neg_absent_snapshot_is_fail_closed` | `..._control_valid_inscope_consent_is_egress_eligible_at_gate` | M6-RULE-002 | M6-FAIL-002 | L2 |

---

## M6-SMK-001 — event not in `event_registry`

Verbatim from `SMOKE_REGISTER.md` (extract line 401):

```
Kịch bản:          Event không có trong event_registry
Kết quả phải đạt:  Reject/HOLD, audit rõ
Bound slices:      M6.2A, M6.2B, M6.2K
```

**How it is proven.** An event code absent from the registry is driven through `IngestService.ingest_event`.
Expected end-to-end behaviour (RULE-001 / RULE-018, prevents M6-FAIL-003 event drift):

- decision `REJECT`, reason `UNKNOWN_EVENT_NOT_IN_REGISTRY`;
- **not** written to `web_event_logs` (`res.logged is False`, store empty) — an unknown event never becomes a
  measurement row;
- **not** egress-eligible;
- the rejection is **clearly audited** ("audit rõ") — never silently dropped.

**Negative / fail-closed cases (the "HOLD" arm of "Reject/HOLD"):**
- de-registered event (`DEREG_SAMPLE`) → `HOLD` (`REGISTRATION_STATE_NOT_ACTIVE`), audited, not logged;
- registered ACTIVE but missing owner (`NO_OWNER_SAMPLE`) → `HOLD` (`MISSING_OWNER`), audited.

**Positive control (non-vacuity):** a known ACTIVE event (`VIEW_LANDING`) → `ACCEPT` and logged — proving
the smoke discriminates rather than rejecting everything.

---

## M6-SMK-002 — valid event but consent missing

Verbatim from `SMOKE_REGISTER.md` (extract line 402):

```
Kịch bản:          Event hợp lệ nhưng thiếu consent
Kết quả phải đạt:  Không external measurement, không audience sync
Bound slices:      M6.2A, M6.2C, M6.2K
```

**How it is proven.** A VALID registry event (`VIEW_LANDING`) is driven through the ingest seam with a
consent snapshot that is not usable. The fail-closed consent gate (RULE-002, prevents M6-FAIL-002) denies
**both** egress scopes named in the expected result — `external_measurement` **and** `audience_sync`:

- `consent_gate.evaluate(snapshot, EXTERNAL_MEASUREMENT) is False` **and**
  `consent_gate.evaluate(snapshot, AUDIENCE_SYNC) is False`;
- end-to-end the valid event **is** durably logged (an internal measurement row), but `egress_eligible is
  False` — measurement never leaks without valid consent;
- each denial is audited (`CONSENT_MISSING` / `CONSENT_EXPIRED` / `CONSENT_OPT_OUT` / `CONSENT_SNAPSHOT_ABSENT`).

**Negative / fail-closed cases:** `MISSING`, `EXPIRED`, `OPT_OUT`, and an **absent** snapshot (`None`) — each
denies both egress scopes and is audited. (Consent is never inferred or upgraded.)

**Positive control (non-vacuity):** consent `VALID` and granted for both scopes → eligible **at the gate**,
proving the primary smoke denies because consent is *missing*, not because the gate blocks everything. Actual
send still stays framework-only at the seam (`external_send=OFF`, M6-OD-003 OPEN).

---

## Negative / fail-closed fixture inventory (reused from `tests/conftest.py`)

| Fixture | State | Drives |
|---|---|---|
| `registry_rows["DEREG_SAMPLE"]` | registration_state = DEREGISTERED | SMK-001 HOLD (fail-closed) |
| `registry_rows["NO_OWNER_SAMPLE"]` | ACTIVE, owner missing | SMK-001 HOLD (data-quality) |
| _(code not present in registry)_ | absent | SMK-001 REJECT |
| `consent_rows["cs_missing"]` | consent_state = MISSING | SMK-002 deny |
| `consent_rows["cs_expired"]` | consent_state = EXPIRED | SMK-002 deny |
| `consent_rows["cs_optout"]` | consent_state = OPT_OUT | SMK-002 deny |
| `None` (absent snapshot) | no snapshot | SMK-002 deny (never infer) |
| `registry_rows["VIEW_LANDING"]` | ACTIVE, INTERNAL | SMK-001 control (accept) |
| `consent_rows["cs_valid"]` | VALID, {external_measurement, audience_sync} | SMK-002 control (eligible at gate) |

## Boundary / safety asserted by the suite

- **Measure-only:** the ingest seam exposes eligibility, never a send/scale/publish — a valid event with
  valid consent is still `egress_eligible is False` while `external_send=OFF`.
- **Append-only + audit-on-deny:** unknown/held events are never written to `web_event_logs` yet are always
  audited (RULE-007 append-only store is exercised via `store`).
- **No flag flip, no external call, no `04-artifacts/state/` write** anywhere in the suite.

## Build verification performed in M6-P1003 (build-only, pinned interpreter)

Verified with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest 8.4.2** — matching the target
manifest's 3.12 pin. (An earlier `--collect-only` that used the system python 3.11 was invalid and is
discarded.) **Collection only — no test body is executed**, faithful to this prompt's "do not yet run" mode.
Commands run from `04-artifacts/impl/M6.2A/`:

```bash
D:\M6\Module6-workspace\02-tester\.venv\Scripts\python.exe -V                                     # Python 3.12.13
D:\M6\Module6-workspace\02-tester\.venv\Scripts\python.exe -m pytest --version                    # pytest 8.4.2
D:\M6\Module6-workspace\02-tester\.venv\Scripts\python.exe -m pytest tests/smoke --collect-only -q  # 10 collected, exit 0
```

`--collect-only` imports the modules and binds the node ids **without running any test body**. This validates
the build; the **formal** smoke RUN report (`04-artifacts/test-reports/M6.2A/SMOKE_RESULTS.md`) and exit-gate
legs L4/L5 are produced by M6-P1004. Collected node ids:

```
tests/smoke/test_smk_001_event_not_in_registry.py::test_smk_001_event_not_in_event_registry_is_rejected_with_audit
tests/smoke/test_smk_001_event_not_in_registry.py::test_smk_001_neg_deregistered_event_is_held_not_false_allowed
tests/smoke/test_smk_001_event_not_in_registry.py::test_smk_001_neg_registered_but_missing_owner_is_held
tests/smoke/test_smk_001_event_not_in_registry.py::test_smk_001_control_known_active_event_is_accepted_and_logged
tests/smoke/test_smk_002_valid_event_missing_consent.py::test_smk_002_valid_event_missing_consent_no_external_measurement_no_audience_sync
tests/smoke/test_smk_002_valid_event_missing_consent.py::test_smk_002_neg_non_valid_consent_blocks_every_egress_scope[cs_missing-CONSENT_MISSING]
tests/smoke/test_smk_002_valid_event_missing_consent.py::test_smk_002_neg_non_valid_consent_blocks_every_egress_scope[cs_expired-CONSENT_EXPIRED]
tests/smoke/test_smk_002_valid_event_missing_consent.py::test_smk_002_neg_non_valid_consent_blocks_every_egress_scope[cs_optout-CONSENT_OPT_OUT]
tests/smoke/test_smk_002_valid_event_missing_consent.py::test_smk_002_neg_absent_snapshot_is_fail_closed
tests/smoke/test_smk_002_valid_event_missing_consent.py::test_smk_002_control_valid_inscope_consent_is_egress_eligible_at_gate
```

## Execution plan for M6-P1004 (`M6_2A_TESTER_RUN`)

Run the full staged suite and the smoke suite, then record structured results + evidence refs for exit-gate
legs **L4** (SMK-001) and **L5** (SMK-002):

```bash
python -m pytest -q            # full staged suite (unit + smoke)
python -m pytest -q tests/smoke
```

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-001 | Every event must exist in `event_registry` before it is logged/sent; unknown → reject/hold + audit; M6 never invents event codes. |
| M6-RULE-002 | Consent fail-closed: without valid consent → no external measurement, no audience sync, no CRM send. |
| M6-RULE-006 | Identity guest→customer mapping carries audit; never overwritten without evidence. *(ingest seam resolves identity only when a `guest_id` is supplied; not exercised by these two smokes — leg L3.)* |
| M6-RULE-007 | `web_event_logs` append-only; never updated/deleted. |
| M6-RULE-018 | Source-of-truth precedence: Core/Runtime owner wins; M6 never invents events/policies. |
| M6-RULE-020 | Entry-evidence gate (ENTRY-001/002/003) precedes implementation; risk-accepted, re-gated at M6.2G. |
| M6-FAIL-002 | Consent violation — external measurement/audience sync without consent (SMK-002 guards). |
| M6-FAIL-003 | Event drift — inventing an event outside `event_registry` (SMK-001 guards). |
| Exit legs | L1 event-registry tests, L2 consent tests, L4 SMK-001 executed, L5 SMK-002 executed (`00-spec/slices/M6.2A.md`). |

## Provenance / notes

- Scenario & expected text quoted verbatim from `00-spec/registers/SMOKE_REGISTER.md` (rows M6-SMK-001,
  M6-SMK-002). Test patterns reused from the existing `tests/conftest.py` and `tests/test_ingest_measure_only.py`.
- No self-certification of PASS: the runner EVIDENCE_GATE and the slice Judge decide. This manifest and the
  smoke files are the *build*; results are produced in M6-P1004.
