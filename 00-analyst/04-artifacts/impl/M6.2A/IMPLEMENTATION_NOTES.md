# M6.2A IMPLEMENTATION NOTES — M6-P1002 (CODER, implement, STAGED)

Realizes [`PLAN.md`](PLAN.md) (M6-P1001) as staged code under `04-artifacts/impl/M6.2A/` against the LOCKED
target manifest (python 3.12, `pytest -q`, `python -m app`). **Nothing shipped**: `global_gateway_state=BLOCKED`,
`production_flag=OFF`, `external_send=OFF`; no migration applied; no external call; no event invented; no flag flipped.

## 1. Verification (this prompt actually ran)

| Command | Result |
|---|---|
| `python -m app` | prints staged posture, exit 0 (no server, no egress) |
| `python -m pytest` | **28 passed in 0.05s** |
| enabling-flag sweep (grep for production/gateway/external-send set to any enabling value across `app/` + `migrations/`) | **none found** — every occurrence is the locked BLOCKED/OFF value |

Environment: Python 3.11.9 + pytest 8.4.2 (verify env). Code is 3.11-compatible so it runs here and on the 3.12 target.

## 2. Plan item → file → status (built as planned)

| Plan item | File(s) staged | Rule/Contract | Status |
|---|---|---|---|
| A1/A2/A4 baseline+config | `pyproject.toml`, `README.md`, `app/config.py` | RULE-H01/H02 | done |
| A3 packages | `app/__init__.py` (+ 6 subpackage `__init__.py`) | convention | done |
| B1 consumed models | `app/measurement/models/consumed.py` | CTR-003/005/006 | done |
| B2 owned row | `app/measurement/models/web_event_log.py` | CTR-004 | done |
| C1 masking | `app/measurement/masking.py` | RULE-014/H02 | done |
| C2 audit | `app/measurement/audit.py` | RULE-001/006/015 | done |
| C3 ports | `app/measurement/ports.py` | RULE-018 boundary | done |
| D1 validator | `app/measurement/registry/validator.py` | RULE-001 (FAIL-003, SMK-001, L1) | done |
| D2 consent gate | `app/measurement/consent/gate.py` | RULE-002 (FAIL-002, SMK-002, L2) | done |
| D3 identity resolver | `app/measurement/identity/resolver.py` | RULE-006 (L3) | done |
| E1 idempotency | `app/measurement/logs/idempotency.py` | RULE-005 | done |
| E2 append-only store | `app/measurement/logs/web_event_log_store.py` | RULE-007/005 | done |
| F1 ingest seam | `app/measurement/ingest.py` | RULE-001/002/004/007 | done |
| G1 entrypoint | `app/__main__.py` | run_command | done |
| M1/M2 migration | `migrations/0001_create_web_event_logs.sql`, `migrations/README.md` | CTR-004, RULE-007 | done (staged, not applied) |
| conftest + T1..T5 | `tests/conftest.py`, `tests/test_*.py` | L1/L2/L3 + SMK-001/002 | done (28 tests) |

## 3. Plan deltas (documented, per the task's "deviations require a plan-delta note")

All deltas are minor/non-behavioral or fail-closed refinements; none changes scope, egress, or flags.

1. **`tests/__init__.py` omitted.** The plan listed it; instead `pyproject.toml` sets `pythonpath = ["."]` so
   `app` imports without a test package marker (standard pytest convention; avoids import-mode edge cases).
   Non-behavioral.
2. **Python 3.11 compatibility.** Target is 3.12; code stays 3.11-compatible (`from __future__ import
   annotations`, no 3.12-only syntax) so the staged tests run in the verify env. `requires-python = ">=3.11"`.
3. **`permits_external_send()` is fail-closed for ALL tokens.** The plan said "MISSING `external_send_policy` =>
   BLOCKED"; the implementation returns `False` for every value while `M6-OD-003` is OPEN (no token is ratified
   as "allow"). This is a superset of the plan rule — strictly more fail-closed. Egress stays framework-only.
4. **Ingest durability semantics clarified (faithful to CTR-004).** The plan said a rejected/HELD event is
   "logged internally, never lost". Implemented precisely: an **unknown/de-registered/missing-owner** event is
   **audited** (durable reject/hold record) but **not** written to `web_event_logs` — because `event_code` must
   resolve in `event_registry` (RULE-001), and the contract states the reject of an unknown event "is itself
   audited". A **valid** event whose consent is missing **is** written to `web_event_logs` (durable), with egress
   blocked. So nothing is silently lost; the durable record is the audit trail for rejects and the event-log for
   valid events.
5. **Consent evaluated on every accepted event.** To honor "consent fail-closed in every path", `ingest` calls
   the consent gate for every accepted event (audited), rather than short-circuiting behind the send-policy flag.
   `egress_eligible = accepted AND policy-permitted AND consent-VALID-in-scope` — still fail-closed; in staged
   mode egress is doubly blocked (policy framework-only + consent).
6. **`__main__.py` prints an ASCII hyphen** (not an em-dash) for Windows console-codepage safety. Cosmetic.

## 4. Fail-closed branches (acceptance check) — where each lives

- **Registry** (`validator.py`): unknown → REJECT+audit; de-registered/stale → HOLD; missing owner → HOLD;
  MISSING `data_sensitivity` → PII; MISSING/unknown `external_send_policy` → egress BLOCKED.
- **Consent** (`gate.py`): absent snapshot → deny; not VALID (MISSING/EXPIRED/OPT_OUT) → deny; scope not granted
  → deny. Never infers/upgrades consent.
- **Dedup** (`web_event_log_store.py` + `idempotency.py`): duplicate `idempotency_key` → no second row; UPDATE /
  DELETE raise `AppendOnlyViolation` (RULE-007); rows are `frozen` (immutable).
- **Identity** (`resolver.py`): unknown guest / mapping-without-audit / mapped-customer-missing → HOLD; unmapped
  → LOW; never overwrites (M6 has no write path; consumed rows are `frozen`).
- **Boundary** (`ports.py`, `config.py`, `ingest.py`): read-only ports (no insert/update/delete) → M6 cannot
  mutate consumed tables; `external_send=OFF`; the ingest seam exposes eligibility only — no send/dispatch/scale.

## 5. Smoke backing (execution is TESTER's job — M6-P1003/M6-P1004)

- **M6-SMK-001** (event not in registry → reject/HOLD + audit): `tests/test_event_registry_validation.py` +
  integrated in `tests/test_ingest_measure_only.py`.
- **M6-SMK-002** (valid event, missing consent → no external measurement / audience sync): the consent mechanism
  is proven definitively in `tests/test_consent_fail_closed.py` (full VALID/MISSING/EXPIRED/OPT_OUT/scope matrix);
  the ingest integration asserts the fail-closed **outcome**. (SMK-003 duplicate-dedup end-to-end is M6.2B/D; the
  store-level dedup invariant is proven here in `tests/test_web_event_logs_append_only.py`.)

This slice does not self-run the smokes as gate evidence and does not self-certify (RULE-015).

## 6. Rollback

All staged ⇒ non-destructive: delete `04-artifacts/impl/M6.2A/` to revert everything (no live system touched, no
migration applied). Per-item rollback is in `PLAN.md` §5–§10. Append-only caveat: after a real (owner-controlled)
apply, reverting `web_event_logs` uses the down-DDL `DROP TABLE` (see `migrations/0001_create_web_event_logs.sql`),
not row deletion.

## 7. Governance carried forward (unchanged)

Entry gate was owner-overridden to STAGED-only (NOT a judge PASS); ENTRY-001/ENTRY-003 remain risk-accepted and
are re-checked at the **MANDATORY M6.2G Scale-Gate re-gate** before any scale or external send. The fail-closed
defaults in `validator.py` (§3.3/§3.4) encode the ENTRY-003 gaps. `global_gateway_state=BLOCKED`,
`production_flag=OFF`, `external_send=OFF` throughout.

---

# Round 2 — fixes for M6-P1005 / M6-P1006 findings

Re-run of M6-P1002 (ledger row 80, attempt 2, status RUNNING). The adversarial reviews M6-P1005 (boundary)
and M6-P1006 (security/PII) found **5 MAJOR + 2 PII** defects in the Round 1 code, several verified by *running*
the code to a fail-open result. None can fire *today* (egress is bolted shut: `permits_external_send()` hardcodes
`False`, no dispatcher, `external_send=OFF`), but M6.2B wires this exact seam into `POST /api/ads/events/track`,
where they become live consent-bypass and double-count bugs. All Round 2 work stays **STAGED** under
`04-artifacts/impl/M6.2A/`; `production_flag=OFF`, `global_gateway_state=BLOCKED`, `external_send=OFF`; no
migration applied; no external call; no flag flipped; no self-certification.

## R2.1 Finding → fix → regression test

| # | Finding (sev) | File(s) changed | Fix | Regression test (RED pre-fix / GREEN post-fix) |
|---|---|---|---|---|
| MAJOR-1 | consent scope **fail-open** on a raw-string scope (FAIL-002) | `models/consumed.py` | `ConsentSnapshot.__post_init__` coerces `consent_scope` to `frozenset[ConsentScope]`; **raises** on a raw `str`/`bytes` or any non-`ConsentScope` element. Substring matching (`ConsentScope` ⊂ `str`) can no longer grant a scope. | `test_major1_raw_string_consent_scope_is_rejected_not_granted`, `test_major1_raw_string_element_in_scope_is_rejected` |
| MAJOR-3 | mutable scope set **aliased** → retroactive grant | `models/consumed.py` | Same `__post_init__`: `frozenset(...)` takes an immutable copy, so a later `.add()` on the caller's original set cannot change an existing snapshot. Dataclass already `frozen=True`. | `test_major3_mutating_source_set_after_construction_does_not_grant` |
| MAJOR-2 | unissued `consent_snapshot_id` written into the **append-only** log; `ConsentReader` never used | `ingest.py` | Ingest now resolves the consent handle via `ConsentReader` and trusts **only** the reader-issued snapshot. Unresolved handle → fail-closed (note `CONSENT_SNAPSHOT_UNRESOLVED` + audit), and the id is **never** written to `web_event_logs`. | `test_major2_unresolved_snapshot_id_is_failclosed_and_not_logged`, `test_major2_reader_issued_snapshot_id_is_recorded` |
| MAJOR-4 | missing UTC normalization → **revenue double-count** | `logs/idempotency.py` | `normalize_ts` now requires a tz-aware datetime, `.astimezone(timezone.utc)` before `.isoformat()`; a naive datetime is **rejected** (ambiguous). RULE-005 formula (5 components, order) unchanged — only the `normalized_ts` *value* is canonicalized. | `test_major4_same_instant_at_different_offset_yields_same_key`, `test_major4_naive_datetime_is_rejected_failclosed` |
| MAJOR-5 | unescaped `|` delimiter → event **swallowed / mislabelled DEDUP** | `logs/idempotency.py` | Each RULE-005 component is escaped (`\`→`\\`, then `|`→`\|`) before the join, making the canonical serialization injective. Order/count of components unchanged. | `test_major5_delimiter_in_id_does_not_collapse_two_events` |
| SEC-PII-01 | raw attacker `event_code` in the audit trail (MEDIUM-latent) | `audit.py` | `AuditLog.record` sanitizes `event_code` at the single choke point: a registry-shaped code (`^[A-Z0-9_.:-]{1,64}$`) is kept verbatim; anything else is control-char-stripped, length-bounded, masked and hashed (`INVALID_EVENT_CODE[abc***xy#<hash>]`). The reject **reason** is a separate field — SMK-001 "audit rõ" preserved. | `test_secpii01_malformed_event_code_is_not_stored_raw`, `test_secpii01_registry_shaped_event_code_is_preserved` |
| SEC-PII-02 | free-text audit `detail` never bounded (LOW-latent) | `audit.py` | `record` strips control chars and bounds `detail` length (defense-in-depth); docstring states the contract: `detail` carries enum/machine-reason/already-masked text only — never raw PII. Not identity-masked (that would corrupt legitimate enum text). | `test_secpii02_detail_is_control_char_stripped_and_bounded` |

New regression file: `tests/test_round2_regressions.py` (11 tests). Existing 38 tests unchanged.

## R2.2 Traps deliberately heeded (from the Round 2 brief)

- **Did NOT** change `consent/gate.py` line 34 `is not ConsentState.VALID` to `!=`. `ConsentState` subclasses
  `str`; `!=` would let a raw `"VALID"` string through = a real FAIL-002 bypass. The `is` identity check stays
  fail-closed; the fix is at construction (`__post_init__`), not at the comparison. `gate.py` is unchanged.
- **Did NOT** alter the RULE-005 formula (component set/order). Only the *serialization* of components and the
  *value* of `normalized_ts` were hardened.
- **Did NOT** identity-mask audit `detail` (would corrupt the enum text it legitimately carries); bounded +
  control-stripped + explicit contract instead.

## R2.3 Plan-deltas (per the task's "deviations require a plan-delta note")

1. **Ingest seam gains a consent system-of-record dependency (MAJOR-2).** `IngestService.__init__` adds two
   *optional* params — `consent_reader: ConsentReader` and `audit: AuditLog` — appended after `resolver`, so every
   existing constructor call (`IngestService(validator, store, consent_gate, resolver)`) still binds correctly.
   `ingest_event` adds an optional `consent_snapshot_id` handle (the id-based form the M6.2B endpoint will use);
   the legacy `consent_snapshot=` object is still accepted and its id is extracted. **Fail-closed either way:** if a
   consent handle is supplied but no reader is wired, the handle is treated as unresolved (deny + note, id not
   logged) — worst case is over-denial, never fail-open. This resolution is a **read-only** `ConsentReader.get`
   (consume-only, RULE-018); it adds no write path and no egress.
2. **New idempotency-key hash values.** Escaping + UTC normalization change the *bytes* hashed, so keys differ from
   Round 1. No test or artifact pins a literal hash; dedup compares key equality only. Store-level dedup invariant
   (RULE-005/007) is unchanged and still proven by `tests/test_web_event_logs_append_only.py`.
3. **Existing TESTER-authored smoke suite left byte-unchanged.** `tests/smoke/*` and the other Round 1 tests were
   not touched; they construct `IngestService` without a reader and remain green under the backward-compatible
   signature (the R2 seam changes are proven by the new regression file, which wires a reader explicitly).

## R2.4 Verification (this Round 2 actually ran)

Pinned interpreter, cwd = `04-artifacts/impl/M6.2A` (target manifest python 3.12):

| Step | Command | Result |
|---|---|---|
| Baseline (pre-fix) | `…\.venv\Scripts\python.exe -m pytest -q` | **38 passed** |
| Red-before (new tests vs unfixed code) | `… -m pytest -q tests/test_round2_regressions.py` | **10 failed, 1 passed** — each failure maps 1:1 to a finding (the 1 pass is the `event_code`-preserved control) |
| Green-after (full suite) | `…\.venv\Scripts\python.exe -m pytest -q` | **49 passed** (38 + 11) |
| Entrypoint | `…\.venv\Scripts\python.exe -m app` | prints staged posture, `exit=0` |

Environment: Python 3.12.13 · pytest 8.4.2 (`01-coder/.venv`). No raw secret/PII in code, tests, or notes;
`04-artifacts/state/` untouched; no enabling value written for any locked flag. Smoke **execution** as gate
evidence and any test-manifest changes remain the TESTER's job (M6-P1003/M6-P1004); this slice does not
self-certify (RULE-015) — the runner EVIDENCE_GATE and Judge decide.

---

# Round 3 — one decision, not 21 patches: **STRICT CALLEE, FORGIVING SEAM**

Re-run of M6-P1002 (ledger row 80, attempt 3, status RUNNING). Round 2 closed 5 MAJOR by making the sub-
functions `raise`. An independent adversarial pass then found 21 findings — nearly all one root cause: **at a
measurement seam a raised exception is not fail-closed, it is DATA LOSS.** An exception escaping `ingest_event()`
means no `IngestResult`, no log line, and — worst — **no audit record**, silently breaking the seam's own
promise (`ingest.py` docstring) that every rejected/held event is audited, never lost. On the M6.2B path
(`POST /api/ads/events/track`) each was a 500-per-request; a beacon sending `"ts":"2026-07-29T12:00:00"` (no
offset — the most common client bug) would kill every request.

**The fix is one principle:** keep every `raise` in the callees; make the SEAM wrap them and turn each hostile
external input into an **AUDITED DENY**. All Round 3 work stays STAGED under `04-artifacts/impl/M6.2A/`;
`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`; no migration applied, no external
call, no flag flipped, no self-certification.

## R3.1 FIX A — the seam contract (subsumes most of the 21)

Every call in `ingest_event()` that touches external / untrusted data is now wrapped; each failure becomes an
audited reject/hold **plus** an `IngestResult` with `logged=False, egress_eligible=False` and a note.

| Call site (`ingest.py`) | Caught | Audited reason | Note |
|---|---|---|---|
| `normalize_ts(event_ts)` | `ValueError` / `AttributeError` / `TypeError` | `TS_NOT_TZ_AWARE` (REJECT) | naive / `str` / `None` / number ts |
| `self._consent_reader.get(...)` | **any `Exception`** (someone else's system) | `CONSENT_READER_FAILED` (HOLD) | reader/DB unreachable, odd token scope |
| `self._consent.evaluate(...)` | `AttributeError` / `TypeError` | `CONSENT_STATE_MALFORMED` (HOLD) | junk `consent_state` from the reader |

Catching bare `Exception` at the reader is deliberate: the consent store is another team's system; every way it
can fail must become a Module-6 deny, not a Module-6 crash. A **seam-level property test** (§R3.6) proves the
whole class closed rather than these three cases only.

## R3.2 FIX B — bind consent to the correct SUBJECT (FAIL-002, the heaviest)

**A real defect today, not a future risk.** MAJOR-2 (Round 2) proved a `consent_snapshot_id` was *issued* by
the reader; it never proved it *belongs to this subject*. Probe: the reader issues `cs_valid_B` for subject
`guest_B`; `ingest_event(consent_snapshot_id="cs_valid_B", guest_id="guest_A")` gated `consent_ok=True` and wrote
`cs_valid_B` **permanently** into the append-only, un-editable (RULE-007) log — one person's consent authorising
another's event, and now *reader-attested* so it looks legitimate in the audit trail. `permits_send()` did not
help (it re-asks about `guest_B`).

Fix in `ingest.py` (+ a raw-PII-free predicate `IdentityResolver.subject_matches`):
1. Identity resolution moved **before** consent, so the event's subject is known first.
2. A resolved snapshot is trusted only if `subject_ref` matches the event's subject — `guest_id`, or the
   customer it is **trustedly** mapped to (mapping carries audit + the customer exists).
3. Mismatch — or **no `guest_id`** to verify against — is treated as unresolved: deny, audit
   `CONSENT_SUBJECT_MISMATCH`, and the id is **never** written (`consent_snapshot_id` left `NULL`).
4. **`consent_reader` is now MANDATORY** (see plan-delta R3.7).

## R3.3 FIX C — the MAJOR-2 patch had HOLLOWED OUT smoke SMK-002 (green for the wrong reason)

`tests/smoke/test_smk_002_*.py` built `IngestService(...)` **without a reader**, so post-MAJOR-2 the seam turned
`consent_snapshot=` into an `UNRESOLVED` handle — the seam never produced `CONSENT_MISSING`. The test passed only
because a *pre-loop direct* `consent_gate.evaluate(...)` call recorded `CONSENT_MISSING` on the shared audit
fixture **before** the seam ran. So **leg L2 (RULE-002/FAIL-002) had no end-to-end evidence.** Same hollow in
`tests/test_ingest_measure_only.py`.

Fix: both suites now wire the (mandatory) `consent_reader`, drive the seam by `consent_snapshot_id` with a
`guest_id` that matches the snapshot's subject, and assert **the seam's own audit trail** carries
`CONSENT_MISSING` / `CONSENT_EXPIRED` / `CONSENT_OPT_OUT` — end-to-end, both named egress kinds, **not** a
side-channel gate call. `tests/test_consent_fail_closed.py` remains the gate-level unit matrix.

## R3.4 FIX D — the other half of the consent vocabulary

- **`consent_state`**: the Round-2 comment "already fail-closed, do not coerce" was disproved by probe — a raw
  `"MISSING"` / `None` state sailed through construction and then exploded `consent_state.value.upper()` on
  **every DENY branch**. Comment removed; `ConsentSnapshot.__post_init__` now requires a real `ConsentState`
  member, exactly like `consent_scope`.
- **requested `scope`**: `ConsentGate.evaluate` coerces the requested scope to a `ConsentScope` — a raw string
  can no longer hash/substring-match into the ALLOW branch nor crash `scope.value` in a DENY audit; an
  unrecognized scope is denied (`CONSENT_SCOPE_MALFORMED`).

## R3.5 FIX E — sanitizer hardening

- `audit.py` event_code shape: `^…$` → `\A…\Z` (so a trailing `\n` no longer passes) and lower-case allowed
  (a legitimately lower-cased code stays **diagnostic**, not masked away — SMK-001 keeps the code it rejected).
- `idempotency.py` `_escape`: a `None` (absent) component maps to a dedicated sentinel, so an absent component
  and the literal string `"None"` can never collide onto one key.
- `masking.py` `mask()`: strips control / non-printable chars first — closes the one PII field (`subject`) that
  reached `AuditRecord.subject_masked` unstripped, at the single choke point all masking flows through.
- `audit.py`: `action` / `reason` are length-bounded + control-stripped (defense-in-depth; legit codes
  unchanged, so `find(reason)` is unaffected).
- `validator.py`: a raw/unknown `data_sensitivity` token normalizes fail-closed to **PII** (a raw string no
  longer defeats the MISSING⇒PII default); a **whitespace-only** `owner` is now HELD, not ACCEPTed.

## R3.6 The invariant test (closes the class, not the case)

`tests/test_round3_regressions.py::test_seam_never_raises_and_every_denial_is_audited` sweeps the Cartesian
product of hostile inputs — `event_ts ∈ {aware, naive, "…T12:00:00", None, 123}` · `consent_snapshot_id ∈
{right-subject, wrong-subject, unissued, None, "", junk-state, none-state}` · `reader ∈ {normal, throwing}` ·
`event_code ∈ {valid, lower-case, trailing-\n, len-500, control-char}` (350 combinations) — and asserts for
**every** one: `ingest_event()` never raises, and any non-logged (denied/held) event carries ≥1 audit record.
This is precisely the test Round 2 lacked.

## R3.7 Plan-deltas (per "deviations require a plan-delta note")

1. **`IngestService` signature: `consent_reader` and `audit` are now REQUIRED, `resolver` stays optional.**
   `__init__(validator, store, consent_gate, consent_reader, audit, resolver=None)`. This **reverses the R2.3
   decision** to leave `consent_reader` optional — that decision was wrong (finding R3.3 is the proof): optional
   did not "fail-closed anyway", it hollowed out the smoke's L2 leg. A required audit sink is likewise necessary
   for the seam's "audit every deny" promise. All in-tree constructors updated (smoke + unit + regression).
2. **`IdentityResolver.subject_matches(guest_id, subject_ref) -> bool`** added — a raw-PII-free predicate used
   only for consent subject binding (returns a bool, logs nothing; raw ids never leave it).
3. **Idempotency-key bytes change** for events with a `None` component only (new sentinel); no test/artifact
   pins a literal hash and dedup compares key equality. The RULE-005 component set/order is unchanged.

## R3.8 Verification (this Round 3 actually ran)

Pinned interpreter `D:\M6\Module6-workspace\01-coder\.venv\Scripts\python.exe`, cwd `04-artifacts/impl/M6.2A`
(python **3.12.13** · pytest **8.4.2**):

| Step | Command | Result |
|---|---|---|
| Full staged suite | `…\.venv\Scripts\python.exe -m pytest -q` | **70 passed** (exit 0; Round 2 was 49, +21) |
| Independent probe | in-memory reproduction of the BRIEF §1/§3 attacks on the real seam (not via fixtures) | **10/10 PASS** — subject-confusion blocked + id-not-logged + still-audited; naive/str-ts, reader-down, malformed-state each an audited deny (never `audit=[]`); right-subject control honoured |
| Entrypoint | `…\.venv\Scripts\python.exe -m app` | prints staged posture (BLOCKED/OFF/OFF), `exit 0` |
| Handoff hygiene | removed all `__pycache__` / `.pytest_cache` | 0 remaining under the staged tree |

No raw secret/PII in code, tests, or notes; `04-artifacts/state/` untouched; no enabling value for any locked
flag. Smoke **execution** as gate evidence remains the TESTER's job (M6-P1003/M6-P1004); this slice does not
self-certify (RULE-015) — the runner EVIDENCE_GATE and the re-run boundary/security adversaries decide closure.

---

# Round 4 — close ONE class (the input TYPE BOUNDARY), not two more bugs

Re-run of M6-P1002 (ledger row 80, attempt 4, status RUNNING). Rounds 2 and 3 each closed the listed bugs, then
an adversary found the **same class** at a new site. The class: **an untrusted data path enters the seam without a
TYPE check.** Round 3 applied "strict callee, forgiving seam" but only for `normalize_ts` and the `reader.get()`
*exception*. Two sites (plus one probe-confirmed sweep miss) remained — all wrong-TYPE, not wrong-value. Round 4
installs **one type boundary at the head of the seam** and closes the whole class so it stops reappearing at later
slices. This is **hardening added on top** of R1/R2/R3 — none of their verified closures are undone. All work stays
STAGED under `04-artifacts/impl/M6.2A/`; `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`;
no migration applied, no external call, no flag flipped, no self-certification.

## R4.1 Finding → fix → regression (all probe-confirmed on the real seam)

| # | Finding (class: wrong-TYPE input into the seam) | File(s) | Fix | Regression (in `tests/test_round4_regressions.py`) |
|---|---|---|---|---|
| MAJOR-7 | seam never type-checked the **value `consent_reader.get()` returns**; a duck-typed snapshot (never through `__post_init__`) with a RAW-STRING `consent_scope` fails **OPEN** on the gate's substring membership test, and its id was written to the **append-only** log | `ingest.py` (FIX 2) | after `reader.get(...)`, `if not isinstance(resolved_snapshot, ConsentSnapshot)` → fail-closed, audit `CONSENT_SNAPSHOT_UNTRUSTED_TYPE`, id **never** logged. Placed **before** subject binding so a duck-type never reaches the gate. | `test_major7_reader_duck_type_snapshot_is_failclosed_and_id_not_logged` |
| MAJOR-6 | a non-`str` channel scalar (`event_code`/`guest_id`/… as a JSON list/dict/number) made a callee `raise TypeError` **out of the seam** (0 audit); and `page_id`/`session_id`/`source`/`raw_event_hash` as a **list** were silently **junk-accepted** (`str(list)` baked into the RULE-005 key, `logged=True`) | `ingest.py` (FIX 1) | **type boundary at the head of `ingest_event()`**: required non-`str` → fail-closed **REJECT** (audited, early return, no raise); optional non-`str` → dropped to **absent** (audited). Centralized in `_require_str`; never `str()`-coerced. | `test_major6_non_str_event_code_*`, `test_major6_non_str_required_field_is_rejected_not_junk_accepted`, `test_major6_non_str_guest_id_*`, `test_major6_non_str_optional_ids_*` |
| FIX 2b | the caller-supplied **`consent_snapshot` object** was dereferenced (`.consent_snapshot_id`) with no type check → `AttributeError` out of the seam | `ingest.py` (FIX 2b) | `if isinstance(consent_snapshot, ConsentSnapshot)` before dereference; wrong type → absent + audit `CONSENT_SNAPSHOT_UNTRUSTED_TYPE`, no raise | `test_fix2b_consent_snapshot_object_without_id_attr_is_absent_not_raised` (+ `_real_consent_snapshot_object_is_still_accepted` control) |

New regression file `tests/test_round4_regressions.py` (26 tests) includes a seam **type-boundary property test**
sweeping **957** wrong-type combinations (`event_code`×`guest_id`×consent-source(object+id)×reader = 945, plus the
four required scalars × 3 bad types = 12) and asserting for **every** one: `ingest_event()` never raises; every
non-logged event carries ≥1 audit; **no** non-`str` scalar is ever logged (no junk-accept); a wrong-typed consent
value never grants egress. Round 3's property test fuzzed `event_ts` but not non-`str` scalars and its reader always
returned a real `ConsentSnapshot` — that narrow domain is why the class survived; R4 widens it to the type axis.

## R4.2 Why FIX 2 is the right-place fix (not `gate.py`)

A **real** `ConsentSnapshot` has already passed `__post_init__` (raw-string scope refused, `consent_state` coerced
to a real member) at construction. So `isinstance(x, ConsentSnapshot)` at the seam is sufficient: it forces every
reader-returned value to be that already-hardened type; a duck-type is refused, fail-closed, id not logged. Per the
Round-4 brief §6 the gate is left **unchanged** (`is not ConsentState.VALID`, RULE-005 five-component formula, the
mandatory `consent_reader`/`audit`). This is a seam-entry guard, not a gate rewrite.

## R4.3 Plan-delta (per "deviations require a plan-delta note")

1. **One Round-3 test assertion updated (not loosened) — `test_round3_regressions.py::
   test_fixa_malformed_consent_state_is_audited_deny_not_raised`.** That test feeds a reader-returned
   **duck-type** snapshot and asserted the reason `CONSENT_STATE_MALFORMED` (produced by the gate-call
   `try/except`). FIX 2 now catches that duck-type **earlier** — at the `isinstance` boundary, before it can reach
   the gate — so the audited reason is the stronger, earlier `CONSENT_SNAPSHOT_UNTRUSTED_TYPE`. The test's
   **security invariant is unchanged and still asserted**: no raise, `egress_eligible is False`, deny is audited.
   Only the expected reason code moved (a direct, necessary consequence of the mandated FIX 2, not a green-washing
   loosen). The gate-call `try/except` (`CONSENT_STATE_MALFORMED`) is **kept** as defense-in-depth — after FIX 2 it
   is belt-and-suspenders (a real `ConsentSnapshot` cannot make `evaluate` raise), consistent with the forgiving-seam
   philosophy. No other R1/R2/R3 test changed.
2. **New audit reason token `CONSENT_SNAPSHOT_UNTRUSTED_TYPE`** and **`FIELD_TYPE_INVALID`** (with the field name in
   `detail`) are added to the seam's own controlled vocabulary. No new PII surface: `_require_str` records only the
   field **name** (our token), never the offending value (which could be attacker-shaped or unhashable).
3. **Two private helpers on `IngestService`** — `_require_str(name, value, notes, *, optional)` (the single
   type-check choke point) and `_field_type_reject(event_code, notes)` (builds the fail-closed `IngestResult`). No
   public method, no new field on `IngestResult`, no signature change to `ingest_event()` — so every existing caller
   (smoke + unit + regression) binds unchanged.

## R4.4 Verification (this Round 4 actually ran)

Pinned interpreter `D:\M6\Module6-workspace\01-coder\.venv\Scripts\python.exe`, cwd `04-artifacts/impl/M6.2A`
(python **3.12** target; verify env python 3.12 · pytest):

| Step | Command | Result |
|---|---|---|
| Baseline (pre-R4) | `…\.venv\Scripts\python.exe -m pytest -q` | **70 passed** (Round 3 state) |
| Green-after (full suite) | `…\.venv\Scripts\python.exe -m pytest -q` | **96 passed** (70 + 26 Round-4 tests), exit 0 |
| Entrypoint | `…\.venv\Scripts\python.exe -m app` | prints staged posture (BLOCKED/OFF/OFF), exit 0 |
| Enabling-flag sweep | grep production/gateway/external-send set to any enabling value across the staged tree | **none found** |
| Handoff hygiene | removed all `__pycache__` / `.pytest_cache` (10 dirs) | 0 remaining under the staged tree |

The §7 done-list is fully covered: MAJOR-7 (duck-type → `egress_eligible=False`, id not logged, audited) ✓;
MAJOR-6 (non-`str` `event_code`/`guest_id` → no raise, audit REJECT/HOLD) ✓; FIX 2b (stray object → no raise,
absent + audit) ✓; junk-accept (list `page_id`/… → REJECT, not `logged=True`) ✓; extended property test + full
suite green ✓; Round-1 five hits + Round-2/3 invariants still green (no regression) ✓. No raw secret/PII in code,
tests, or notes; `04-artifacts/state/` untouched; no enabling value for any locked flag. This slice does not
self-certify (RULE-015) — the runner EVIDENCE_GATE and the re-run boundary/security adversaries decide closure.
