# TEST_MANIFEST — Slice M6.2A smoke suite

| Field | Value |
|---|---|
| Prompt | M6-P1003 — `M6_2A_TESTER_BUILD` (attempt 4) |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — the smoke tests are AUTHORED/inventoried here. Per the operator's instruction this attempt ALSO ran `pytest -q` from the tester venv as a **build-validation** (green); the **formal executed-results recording** for exit-gate legs L4/L5 still belongs to M6-P1004. |
| Executed by (formal) | M6-P1004 (`M6_2A_TESTER_RUN`) → `04-artifacts/test-reports/M6.2A/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-001, M6-SMK-002** (exactly — per `00-spec/slices/M6.2A.md` "Core smokes" + this prompt's `<smoke_ids>`) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2** (matches the `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin; `test_command = pytest -q`) |
| Round | **Round 4** re-author. M6-P1002 attempt 4 closed the **input type-boundary class** at the seam entry (a required non-`str` scalar → fail-closed REJECT; an optional non-`str` → dropped absent; a reader/caller consent value of the wrong TYPE → fail-closed, id never logged) and added `tests/test_round4_regressions.py` (26 nodes). The two smoke files are **byte-unchanged from Round 3** and re-collected/re-run against the frozen Round-4 code; the `ingest_event()` signature is unchanged, so they bind unchanged. This manifest's only substantive delta vs Round 3 is: (a) inventory + node map for `test_round4_regressions.py`, and (b) the one Round-3 reason code that Round-4 FIX 2 moved earlier (see § Round-4). |
| Staging root | `04-artifacts/impl/M6.2A/` (STAGED_ONLY; convention reference, not a live repo) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (owner P0 matrix, doc §21) |

> **Governance (immutable — nothing in this suite flips a flag):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`.
> This slice proves capability with evidence only. The ENTRY-001/ENTRY-003 owner risk-acceptance
> and the MANDATORY M6.2G Scale-Gate re-gate remain in force before any real scale or external send.

## What this suite is

The **official smoke suite** for slice M6.2A: exactly one **primary** test per bound smoke id, carrying the
register's scenario/expected **verbatim**, driven **end-to-end through the real ingest seam**
(`app.measurement.ingest.IngestService.ingest_event`), plus the negative / fail-closed companions the doc
done-gate requires and a positive control for non-vacuity. It reuses the existing fixtures in
[`tests/conftest.py`](04-artifacts/impl/M6.2A/tests/conftest.py) (in-memory TEST DOUBLES for the CONSUMED
`event_registry` / `guest_contacts` / `guest_marketing_consent_snapshot` / `customers`) — no new production
code, and **no fix to the code under test** (TESTER reports defects, never fixes them).

All fixture ids are **synthetic**; no raw secret/PII. `event_code` and `session_id` are channel-origin,
untrusted DATA — treated as data only; identity values are masked by the audit sink at the boundary.

This manifest also inventories the **regression suite** the `pytest -q` run exercises alongside the two
smokes — `tests/test_round4_regressions.py` (Round 4, 26 nodes), `tests/test_round3_regressions.py`
(Round 3, 20 nodes) and the retained `tests/test_round2_regressions.py` (11 nodes) — see
[§ Regression suites](#regression-suites-in-manifest-per-operator-instruction). Those files are **not** among
the two bound smoke ids, but they are recorded here because the seam contract they pin — *strict callee,
forgiving seam, hard type boundary at entry* — is exactly what makes the two seam-driven smokes meaningful.

## Smoke → test binding

| Smoke ID | Doc ID | Test file | Primary test (scenario verbatim) | Negative / fail-closed tests | Control | Rule(s) | Fail gate | Exit leg |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-001 | ADS-P0-001 | [`tests/smoke/test_smk_001_event_not_in_registry.py`](04-artifacts/impl/M6.2A/tests/smoke/test_smk_001_event_not_in_registry.py) | `test_smk_001_event_not_in_event_registry_is_rejected_with_audit` | `..._neg_deregistered_event_is_held_not_false_allowed`, `..._neg_registered_but_missing_owner_is_held` | `..._control_known_active_event_is_accepted_and_logged` | M6-RULE-001, M6-RULE-018 | M6-FAIL-003 | L1 (support) + L4 |
| M6-SMK-002 | ADS-P0-002 | [`tests/smoke/test_smk_002_valid_event_missing_consent.py`](04-artifacts/impl/M6.2A/tests/smoke/test_smk_002_valid_event_missing_consent.py) | `test_smk_002_valid_event_missing_consent_no_external_measurement_no_audience_sync` (parametrized `[external_measurement]`, `[audience_sync]`) | `..._neg_non_valid_consent_blocks_egress_through_the_seam[cs_missing / cs_expired / cs_optout]`, `..._neg_absent_snapshot_is_fail_closed_through_the_seam` | `..._control_valid_inscope_consent_is_egress_eligible_at_gate` | M6-RULE-002 | M6-FAIL-002 | L2 (support) + L5 |

---

## M6-SMK-001 — event not in `event_registry`

Verbatim from `00-spec/registers/SMOKE_REGISTER.md` (extract line 401):

```
Smoke ID:          M6-SMK-001  (Doc ID ADS-P0-001)
Kịch bản:          Event không có trong event_registry
Kết quả phải đạt:  Reject/HOLD, audit rõ
Bound slices:      M6.2A, M6.2B, M6.2K
```

**How it is proven.** An event code absent from the registry is driven through `IngestService.ingest_event`.
Expected end-to-end behaviour (RULE-001 / RULE-018, prevents M6-FAIL-003 event drift):

- decision `REJECT`, reason `UNKNOWN_EVENT_NOT_IN_REGISTRY`;
- **not** written to `web_event_logs` (`res.logged is False`, `len(store) == 0`) — an unknown event never
  becomes a measurement row;
- **not** egress-eligible (`res.egress_eligible is False`);
- the rejection is **clearly audited** ("audit rõ") — `audit.find("UNKNOWN_EVENT_NOT_IN_REGISTRY")` is
  non-empty — never silently dropped.

**Negative / fail-closed cases (the "HOLD" arm of "Reject/HOLD"):**
- de-registered event (`DEREG_SAMPLE`) → `HOLD` (`REGISTRATION_STATE_NOT_ACTIVE`), audited, not logged;
- registered ACTIVE but missing owner (`NO_OWNER_SAMPLE`) → `HOLD` (`MISSING_OWNER`), audited.

**Positive control (non-vacuity):** a known ACTIVE event (`VIEW_LANDING`) → `ACCEPT` and logged
(`len(store) == 1`) — proving the smoke discriminates rather than rejecting everything.

---

## M6-SMK-002 — valid event but consent missing

Verbatim from `00-spec/registers/SMOKE_REGISTER.md` (extract line 402):

```
Smoke ID:          M6-SMK-002  (Doc ID ADS-P0-002)
Kịch bản:          Event hợp lệ nhưng thiếu consent
Kết quả phải đạt:  Không external measurement, không audience sync
Bound slices:      M6.2A, M6.2C, M6.2K
```

**How it is proven — END-TO-END THROUGH THE SEAM (leg L2).** A VALID registry event (`VIEW_LANDING`) is
driven through `IngestService.ingest_event` with a consent handle (`consent_snapshot_id`) and a matching
`guest_id`. The seam itself resolves the handle through the mandatory `ConsentReader`, subject-binds it
(`cs_missing.subject_ref == "guest_x"` == the event's `guest_id`, so Round-3 subject binding lets the
snapshot through to the gate rather than dropping it as a mismatch), drives the fail-closed
`ConsentGate.evaluate`, and audits the denial. The primary runs for **both** egress kinds named in the
expected result — `external_measurement` **and** `audience_sync` — via `@pytest.mark.parametrize`.

> **What actually closes leg L2 (read this before trusting a green).** The load-bearing assertion is
> **`audit.find("CONSENT_MISSING")` on the seam's own shared audit sink** — it is satisfied ONLY because the
> **seam** called `ConsentGate.evaluate(cs_missing, scope)`, which records `CONSENT_MISSING`
> (`f"CONSENT_{state.value.upper()}"`) onto the function-scoped `audit` fixture. There is **no** pre-loop or
> side-channel `consent_gate.evaluate(...)` call in the primary or negative tests feeding that audit — the
> Round-2 defect (FIX C) where a direct pre-loop gate call pre-seeded `CONSENT_MISSING` and the smoke passed
> for the wrong reason is gone.
>
> `res.egress_eligible is False` is asserted too, but it is **NOT** by itself the consent proof: for
> `VIEW_LANDING`, `external_send_permitted` is always `False` (`permits_external_send()` returns `False`
> while M6-OD-003 is OPEN), so `egress_eligible` would be `False` even with valid consent. The seam-produced
> `CONSENT_MISSING` audit is the non-vacuous evidence that **consent** fail-closed, end-to-end, through the
> seam. The `control` test (below) is the only place a gate is called directly, and it exists precisely to
> prove the gate can return `True`, so the primary denies because consent is *missing*, not because the gate
> blocks everything.

- the valid event **is** durably logged (`res.logged is True`, an internal measurement row) — measurement is
  not lost; only egress is withheld;
- `res.egress_eligible is False` (no external measurement / audience sync without consent);
- the seam audits the denial (`CONSENT_MISSING`).

**Negative / fail-closed cases, ALL through the seam:** `cs_missing` → `CONSENT_MISSING`, `cs_expired` →
`CONSENT_EXPIRED`, `cs_optout` → `CONSENT_OPT_OUT` (each: `egress_eligible is False` + the seam audits the
matching reason); and an **absent** snapshot (no `consent_snapshot_id`, no `guest_id`) → the seam drives the
gate to deny and audits `CONSENT_SNAPSHOT_ABSENT` (consent is never inferred or upgraded).

**Positive control (non-vacuity, gate-level by design):** consent `VALID` and granted for both scopes →
`consent_gate.evaluate(...) is True`. This is the single deliberate direct-gate call in the file; it proves
the deny in the primary is caused by *missing consent*, not a blanket block. Actual send still stays
framework-only at the seam (`external_send=OFF`, M6-OD-003 OPEN).

---

## Regression suites (in-manifest per operator instruction)

Per the M6-P1002→M6-P1003 handoff and the operator instruction (including "đọc `test_round4_regressions.py`
vào manifest"), the regression files are recorded here. They are **not** among the two bound smoke ids
(M6-SMK-001/002), but they pin the exact seam contract that makes the two seam-driven smokes meaningful, so
M6-P1004's `pytest -q` run must exercise them alongside the smokes.

| File | Purpose | Node count (collected) | In smoke scope? |
|---|---|---|---|
| [`tests/test_round4_regressions.py`](04-artifacts/impl/M6.2A/tests/test_round4_regressions.py) | Round-4 regression + **type-boundary invariant** — the whole INPUT wrong-TYPE class at the seam entry is fail-closed: never raises, never junk-accepts a non-`str` into a row, never grants egress on a wrong-typed consent value, always audits a non-logged event | 26 | No (regression) |
| [`tests/test_round3_regressions.py`](04-artifacts/impl/M6.2A/tests/test_round3_regressions.py) | Round-3 regression + **seam invariant** — every hostile wrong-VALUE external input becomes an AUDITED DENY, never an escaped exception | 20 | No (regression) |
| [`tests/test_round2_regressions.py`](04-artifacts/impl/M6.2A/tests/test_round2_regressions.py) | Round-2 regressions (MAJOR-1..5 / SEC-PII-01/02), retained | 11 | No (regression) |

### Round-4 (`test_round4_regressions.py`) — fix → test map (26 nodes)

Round 4 installs **one type boundary at the head of `ingest_event()`** (before identity/consent): a required
channel scalar of a non-`str` type → fail-closed **REJECT** (audited `FIELD_TYPE_INVALID`, early return, no
raise); an optional field of the wrong type → **dropped to absent** (audited); a reader- or caller-supplied
consent value that is not a real `ConsentSnapshot` → fail-closed (audited `CONSENT_SNAPSHOT_UNTRUSTED_TYPE`),
its id **never** written to the append-only log. Nothing is `str()`-coerced (that would ingest garbage).

- **MAJOR-7 — reader-returned duck-type consent** (`test_major7_reader_duck_type_snapshot_is_failclosed_and_id_not_logged`, 1): a reader hands back a `SimpleNamespace` whose `consent_scope` is a RAW STRING (`"no_external_measurement_allowed"`, which the pre-fix gate substring-matched as *allowed*). The seam does not raise, denies egress, audits `CONSENT_SNAPSHOT_UNTRUSTED_TYPE`, and the duck id is **not** in the logged row even though the valid event is still logged.
- **MAJOR-6 — non-`str` required `event_code`** (`test_major6_non_str_event_code_is_rejected_not_raised`, 4 params `[["x"], {"a":1}, 123, None]`): REJECT, `logged is False`, `idempotency_key is None`, `FIELD_TYPE_INVALID` audited, `len(store) == 0` — never a measurement row.
- **MAJOR-6 — non-`str` other required scalars, junk-accept closure** (`test_major6_non_str_required_field_is_rejected_not_junk_accepted`, 12 = `{page_id, session_id, source, raw_event_hash}` × `{["x"], 123, None}`): the four fields that a probe found were silently ACCEPTED as `str(list)` baked into the RULE-005 key are now hard-REJECTed fail-closed, not logged.
- **MAJOR-6 — non-`str` `guest_id` dropped before the resolver** (`test_major6_non_str_guest_id_is_dropped_before_the_resolver`, 3 params): a wrong-type guest is dropped to absent AT THE BOUNDARY so the resolver (`mask()` / `contacts.get()`) never sees it and cannot raise; the valid event is still logged, `identity is None`.
- **MAJOR-6 — non-`str` optional ids dropped absent** (`test_major6_non_str_optional_ids_are_dropped_absent_not_raised`, 3 params): wrong-type `consent_snapshot_id` / `correlation_id` are dropped to absent (audited); a non-`str` consent handle never reaches the reader and a non-`str` `correlation_id` never enters the log row.
- **FIX 2b — caller-supplied consent object** (`test_fix2b_consent_snapshot_object_without_id_attr_is_absent_not_raised`, 1): a stray `object()` passed as `consent_snapshot=` (no `.consent_snapshot_id`) is treated absent + audited `CONSENT_SNAPSHOT_UNTRUSTED_TYPE`, never `AttributeError` out of the seam.
- **FIX 2b — control, do not over-reject** (`test_fix2b_real_consent_snapshot_object_is_still_accepted`, 1): a REAL `ConsentSnapshot` passed as the object param still resolves via its id and binds.
- **§4 — type-boundary invariant, whole-class** (`test_seam_type_boundary_never_raises_no_junk_accept_every_deny_audited`, 1): sweeps **957 combinations** (945 = `event_code` × `guest_id` × consent-source(object+id) × reader, plus 12 = 4 required scalars × 3 bad types) asserting for **every** one that `ingest_event()` never raises, no non-`str` scalar is ever logged, a wrong-typed consent value never grants egress, and every non-logged event carries ≥1 audit record.

### Round-3 (`test_round3_regressions.py`) — fix → test map (20 nodes)

- **FIX A — forgiving seam** (`test_fixa_*`): a naive `event_ts`, a raw-string `event_ts`, and a consent-reader that throws each become an **audited deny** (`TS_NOT_TZ_AWARE`, `CONSENT_READER_FAILED`) — `ingest_event()` returns an `IngestResult`, never raises; an unverifiable consent ref is never written to the append-only log. **NOTE (Round-4 shift):** the fourth case, a malformed (duck-typed, raw-string `consent_state`) reader value, is now refused **earlier** at Round-4's `isinstance` type boundary and audited `CONSENT_SNAPSHOT_UNTRUSTED_TYPE` (was `CONSENT_STATE_MALFORMED` at the gate in Round 3). The `test_fixa_malformed_consent_state_is_audited_deny_not_raised` assertion was updated to the stronger, earlier reason code; the **security invariant is unchanged** (no raise, egress denied, deny audited). The gate's `CONSENT_STATE_MALFORMED` try/except is retained as **defense-in-depth** behind the boundary.
- **FIX B — subject binding, FAIL-002** (`test_fixb_*`): a genuinely reader-issued consent for a *different* subject is denied (`CONSENT_SUBJECT_MISMATCH`) and its id never enters the log; consent keyed by a trusted customer mapping binds (control, no over-deny); no `guest_id` ⇒ dropped; `consent_reader` is mandatory.
- **FIX D — consent vocabulary** (`test_fixd_*`): a raw-string / `None` `consent_state` is rejected at construction; a malformed requested scope is denied (`CONSENT_SCOPE_MALFORMED`) not crashed; a raw valid-value scope on a deny path is coerced and denied via `CONSENT_MISSING` without crashing.
- **FIX E — sanitizer hardening** (`test_fixe_*`): trailing-newline `event_code` neutralized (`\A..\Z`); legitimately lower-cased code kept diagnostic; absent vs literal-`"None"` key components distinct; `subject` control chars stripped in the audit sink; `action`/`reason` length-bounded; whitespace-only owner HELD; raw `data_sensitivity` token defaults to PII.
- **§7 — seam invariant** (`test_seam_never_raises_and_every_denial_is_audited`): sweeps the Cartesian product of hostile `event_ts` × `consent_snapshot_id` × reader × `event_code` and asserts for **every** combination that `ingest_event()` never raises and any non-logged (denied/held) event carries ≥1 audit record.

---

## Negative / fail-closed fixture inventory

Shared conftest doubles reused by the two smokes (`tests/conftest.py`):

| Fixture | State | Drives |
|---|---|---|
| _(code not present in registry)_ | absent | SMK-001 REJECT |
| `registry_rows["DEREG_SAMPLE"]` | registration_state = DEREGISTERED | SMK-001 HOLD (fail-closed) |
| `registry_rows["NO_OWNER_SAMPLE"]` | ACTIVE, owner missing | SMK-001 HOLD (data-quality) |
| `registry_rows["VIEW_LANDING"]` | ACTIVE, INTERNAL | SMK-001 control (accept) + SMK-002 valid event |
| `consent_rows["cs_missing"]` | consent_state = MISSING, subject_ref = `guest_x` | SMK-002 deny (`CONSENT_MISSING`) |
| `consent_rows["cs_expired"]` | consent_state = EXPIRED, subject_ref = `guest_x` | SMK-002 deny (`CONSENT_EXPIRED`) |
| `consent_rows["cs_optout"]` | consent_state = OPT_OUT, subject_ref = `guest_x` | SMK-002 deny (`CONSENT_OPT_OUT`) |
| `None` (no `consent_snapshot_id`) | no snapshot | SMK-002 deny (`CONSENT_SNAPSHOT_ABSENT`; never infer) |
| `consent_rows["cs_valid"]` | VALID, {external_measurement, audience_sync} | SMK-002 control (eligible at gate) |
| `consent_rows["cs_valid_b"]` | VALID for `guest_B` | round3 FIX-B subject-mismatch (not a smoke) |
| `consent_rows["cs_valid_cust"]` | VALID keyed by `cust_0001` | round3 FIX-B trusted-mapping bind (not a smoke) |

Round-4 wrong-TYPE cases use **local** test doubles declared in `test_round4_regressions.py` (not conftest):
`_ThrowingReader` (consent store down), `_DuckReader` / `_MapReader` (return a duck-typed or dict-backed
value), and the `_DUCK_OPEN` `SimpleNamespace` (VALID enum state but a raw-string scope) — the exact MAJOR-7
fail-OPEN shape.

## Boundary / safety asserted by the suite

- **Measure-only:** the ingest seam exposes *eligibility*, never a send/scale/publish — a valid event with
  valid consent is still `egress_eligible is False` while `external_send=OFF` (OD-003 OPEN).
- **Append-only + audit-on-deny:** unknown/held/denied events are never written to `web_event_logs` yet are
  always audited (RULE-007 append-only store is exercised via `store`).
- **No flag flip, no external call, no `04-artifacts/state/` write** anywhere in the suite.

## Build + validation run performed in M6-P1003 (attempt 4, pinned interpreter)

Run with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest 8.4.2** — matching the target
manifest's 3.12 pin. Per the operator's instruction this attempt ran the suite (not collect-only) as a
**build-validation**; the run was **green**. Commands run from `04-artifacts/impl/M6.2A/`, **no shell
redirection** (the role guard blocks a `>`/`2>` that co-occurs with the venv `Scripts` path), cache-free
(`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```bash
"D:\M6\Module6-workspace\02-tester\.venv\Scripts\python.exe" -V                     # Python 3.12.13
"D:\M6\Module6-workspace\02-tester\.venv\Scripts\python.exe" -m pytest --version    # pytest 8.4.2
python -m pytest -q                         # full staged suite: 96 passed, exit 0
python -m pytest -v tests/smoke             # smoke suite: 11 passed, exit 0
python -m pytest --collect-only -q          # per-file collected counts (below)
```

Per-file collected counts (total **96**):

```
tests/smoke/test_smk_001_event_not_in_registry.py: 4
tests/smoke/test_smk_002_valid_event_missing_consent.py: 7
tests/test_consent_fail_closed.py: 6
tests/test_event_registry_validation.py: 6
tests/test_identity_mapping_audit.py: 7
tests/test_ingest_measure_only.py: 5
tests/test_round2_regressions.py: 11
tests/test_round3_regressions.py: 20
tests/test_round4_regressions.py: 26
tests/test_web_event_logs_append_only.py: 4
```

Smoke node ids (11), all PASSED:

```
tests/smoke/test_smk_001_event_not_in_registry.py::test_smk_001_event_not_in_event_registry_is_rejected_with_audit
tests/smoke/test_smk_001_event_not_in_registry.py::test_smk_001_neg_deregistered_event_is_held_not_false_allowed
tests/smoke/test_smk_001_event_not_in_registry.py::test_smk_001_neg_registered_but_missing_owner_is_held
tests/smoke/test_smk_001_event_not_in_registry.py::test_smk_001_control_known_active_event_is_accepted_and_logged
tests/smoke/test_smk_002_valid_event_missing_consent.py::test_smk_002_valid_event_missing_consent_no_external_measurement_no_audience_sync[external_measurement]
tests/smoke/test_smk_002_valid_event_missing_consent.py::test_smk_002_valid_event_missing_consent_no_external_measurement_no_audience_sync[audience_sync]
tests/smoke/test_smk_002_valid_event_missing_consent.py::test_smk_002_neg_non_valid_consent_blocks_egress_through_the_seam[cs_missing-CONSENT_MISSING]
tests/smoke/test_smk_002_valid_event_missing_consent.py::test_smk_002_neg_non_valid_consent_blocks_egress_through_the_seam[cs_expired-CONSENT_EXPIRED]
tests/smoke/test_smk_002_valid_event_missing_consent.py::test_smk_002_neg_non_valid_consent_blocks_egress_through_the_seam[cs_optout-CONSENT_OPT_OUT]
tests/smoke/test_smk_002_valid_event_missing_consent.py::test_smk_002_neg_absent_snapshot_is_fail_closed_through_the_seam
tests/smoke/test_smk_002_valid_event_missing_consent.py::test_smk_002_control_valid_inscope_consent_is_egress_eligible_at_gate
```

Cache hygiene: after the runs, **0** `__pycache__` / `.pytest_cache` directories remain under the staged tree
(the `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider` combination prevents both).

> **This build-validation run does NOT self-certify gate advancement.** It proves the smoke + regression files
> import, collect, and pass against the frozen Round-4 code; it is the honest self-report of a TESTER build.
> The **formal executed-results recording** for exit-gate legs **L4** (SMK-001 executed) and **L5** (SMK-002
> executed), plus the L2 consent contribution, is produced by **M6-P1004** into
> `04-artifacts/test-reports/M6.2A/SMOKE_RESULTS.md`. The runner EVIDENCE_GATE and the slice Judge decide
> closure — this manifest and its run do not.

## Execution plan for M6-P1004 (`M6_2A_TESTER_RUN`)

Run the full staged suite and the smoke suite, then record structured results + evidence refs for exit-gate
legs **L4** (SMK-001 executed) and **L5** (SMK-002 executed), and contribute to **L2** (consent fail-closed):

```bash
python -m pytest -q            # full staged suite: unit + smoke + round2 + round3 + round4 regressions
python -m pytest -q tests/smoke
```

- **L2 (consent)** is closed by the *executed* SMK-002 primary/negative seam assertions
  (`CONSENT_MISSING`/`EXPIRED`/`OPT_OUT`/`SNAPSHOT_ABSENT` audited **by the seam**, `egress_eligible is
  False`) together with the `tests/test_consent_fail_closed.py` gate-level unit matrix — **not** by any
  direct gate call and **not** by collection.
- Expected full-suite total is **96** (Round-4 frozen code): smoke 11 + consent_fail_closed 6 +
  event_registry_validation 6 + identity_mapping_audit 7 + ingest_measure_only 5 + round2 11 + round3 20 +
  round4 26 + web_event_logs_append_only 4. M6-P1002 attempt 4 recorded the same 96; M6-P1004 must reproduce
  and record it independently — this manifest does not self-certify a run.

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-001 | Every event must exist in `event_registry` before it is logged/sent; unknown → reject/hold + audit; M6 never invents event codes. |
| M6-RULE-002 | Consent fail-closed: without valid consent → no external measurement, no audience sync, no CRM send. |
| M6-RULE-006 | Identity guest→customer mapping carries audit; never overwritten without evidence. *(the seam resolves identity when a `guest_id` is supplied; the smokes exercise the subject-binding path but the dedicated identity leg L3 is `tests/test_identity_mapping_audit.py`.)* |
| M6-RULE-007 | `web_event_logs` append-only; never updated/deleted. |
| M6-RULE-018 | Source-of-truth precedence: Core/Runtime owner wins; M6 never invents events/policies. |
| M6-RULE-020 | Entry-evidence gate (ENTRY-001/002/003) precedes implementation; risk-accepted, re-gated at M6.2G. |
| M6-FAIL-002 | Consent violation — external measurement/audience sync without consent (SMK-002 guards). |
| M6-FAIL-003 | Event drift — inventing an event outside `event_registry` (SMK-001 guards). |
| Exit legs | L1 event-registry tests, L2 consent tests, L4 SMK-001 executed, L5 SMK-002 executed (`00-spec/slices/M6.2A.md`). |

## Provenance / notes

- Scenario & expected text quoted **verbatim** from `00-spec/registers/SMOKE_REGISTER.md` (rows M6-SMK-001,
  M6-SMK-002). Test patterns reused from the existing `tests/conftest.py` and
  `tests/test_ingest_measure_only.py` (doc working mode, extract line 466).
- No self-certification of PASS or of gate/leg advancement: the runner EVIDENCE_GATE and the slice Judge
  decide. This manifest and the smoke files are the *build*; the formal executed results are produced in
  M6-P1004.
