# M6.2B IMPLEMENTATION NOTES — M6-P1102 (CODER, implement, STAGED)

Realizes [`PLAN.md`](PLAN.md) (M6-P1101) as staged code under `04-artifacts/impl/M6.2B/` against the LOCKED
target manifest (python 3.12, `pytest -q`, `python -m app`). **Nothing shipped**: `global_gateway_state=BLOCKED`,
`production_flag=OFF`, `external_send=OFF`; no migration applied; no external call; no event invented; no flag
flipped; `04-artifacts/state/` not touched; no self-certification (RULE-015).

## 0. Governance & entry (this prompt actually verified)

- Ledger: **M6-P1102 = RUNNING** (row 90); dependency **M6-P1101 = PASS** (plan gate). Target `LOCKED`,
  `STAGED_ONLY`, `safety` all false; **M6-OD-011 = DECIDED** (GREENFIELD python 3.12, `framework=""`).
- The M6.2B entry gate (M6-P1100 = SIGNED) **BOUND four fix-first preconditions** (`M6-DEFER-F1F2-M6.2B.json`):
  **F1, F2** are fix-first (close BEFORE the endpoint/adapter); **MINOR-9, O1** close in this slice. All four are
  done in §2 and proven in `tests/test_m6_2b_fixfirst_regressions.py`.

## 1. Staging model — cumulative snapshot (as planned §2)

The whole M6.2A `app/`+`tests/`+`migrations/`+`pyproject.toml`+`README.md` tree was **carried forward** into
`04-artifacts/impl/M6.2B/`, the four fix-first modules **patched in place**, and the new tracking/endpoint/store
modules **added**. Rationale: the TESTER runs SMK-001/SMK-003 **end-to-end through the endpoint → seam → stores**
against `04-artifacts/impl/M6.2B/`, so the full app must be importable there. The "change set" below is the
**diff vs the carried-forward M6.2A baseline**; every other file is carried forward byte-identical.

## 2. Fix-first BINDING preconditions — DONE FIRST, proven green before the endpoint

| # | File (patched) | What was done | Test (RED pre-fix / GREEN post-fix) |
|---|---|---|---|
| **F1** | `app/measurement/ingest.py` | Completed the forgiving-seam contract: the ts guard now also has `except Exception` (catches `OverflowError` from a year-max ts + negative offset, and any tzinfo-raised error) → audited `TS_NORMALIZE_FAILED`; and `resolve` / `validate` / `subject_matches` / `store.append` are each wrapped so a callee raise becomes an audited DENY (`IDENTITY_RESOLVE_FAILED` / `VALIDATION_FAILED` / `STORE_APPEND_FAILED`; a failed validate yields a synthetic REJECT result). `ingest_event()` now never raises. | `test_f1_*` (overflow ts, tzinfo-raise, validator/store/resolver raise) |
| **F2** | `app/measurement/consent/gate.py` | Hardened the **decision point**: before the membership test, `gate.evaluate` asserts `snapshot.consent_scope` is a real `set/frozenset[ConsentScope]` (coerce-or-DENY, audit `CONSENT_SCOPE_UNTRUSTED_TYPE`). A `ConsentSnapshot` **subclass** that no-ops `__post_init__` (raw-string scope) can no longer substring-match into ALLOW. `is not ConsentState.VALID` unchanged. | `test_f2_*` (subclass at the gate; subclass through the seam → egress ineligible) |
| **MINOR-9** | `app/measurement/audit.py` | Verbatim-retention of `event_code` now ALSO rejects **identifier/PII-shaped** tokens (`\d{6,}` run, or an id prefix `cust_/guest_/psid/ord_/...`), wrapping them as `INVALID_EVENT_CODE[...]`. A genuine code (short, letter-dominant, incl. lowercase) stays diagnostic — SMK-001 "audit rõ" preserved. | `test_minor9_*` (identifier wrapped; genuine codes diagnostic) |
| **O1** | `app/measurement/masking.py` (+ endpoint callers) | `session_id` / `correlation_id` are masked on every **export** surface. The durable rows keep the raw value (dedup/trace); the endpoint masks `correlation_id` in audit detail and never audits `session_id`. `mask()` behaviour unchanged; the fix lives at the export callers with `mask()` as the choke point (see §3 delta). | `test_o1_*` (no raw session_id/correlation_id in the audit sink) |

**No regression**: the carried-forward **96 M6.2A tests stay green** — F1 widens a catch (additive), F2 accepts
valid `frozenset[ConsentScope]`, MINOR-9 keeps `test_fixe_lowercase_event_code_is_kept_diagnostic`, O1 leaves the
durable stores unchanged.

## 3. New change set — files built (all staged, target-relative)

| # | File(s) | Purpose | Contract/Rule | Leg | Smoke |
|---|---|---|---|---|---|
| B1 | `app/measurement/tracking/base_events.py` | The 9 LOCKED base events `VIEW_LANDING..ORDER_VERIFIED` (SPEC §8.1, **verbatim** — not invented). `GOLDEN_HOUR_*` excluded (M6-OD-009 OPEN, fail-closed). | RULE-001 | L1 | SMK-001 |
| B2 | `app/measurement/tracking/hooks.py` | `TrackingHook.emit()` — client-side guard: emits only for a locked base event, else audited refuse (leg-1 layer 1). Non-str → fail-closed. | RULE-001/H03 | L1 | SMK-001 |
| B3 | `app/measurement/models/measurement_event.py` | `AdsMeasurementEvent` (CTR-001): 20 doc fields + `ingested_at`; `currency=VND`; frozen; PII fields flagged; Zone A/B/C documented. | CTR-001 | L2 | SMK-003 |
| B4 | `app/measurement/store/measurement_event_store.py` | `ads_measurement_events` store: Zone-A `insert()` + UNIQUE `idempotency_key` dedup; `update`/`delete`/revenue-bearing insert → `MeasurementStoreViolation`. | CTR-001; RULE-005/007/003 | L2 | SMK-003 |
| B5 | `app/measurement/normalize.py` | Accepted event → `AdsMeasurementEvent` (deterministic `event_id` from the key; `data_quality_status=HOLD` initial; empty `attribution_context`; Zone B unset). | CTR-001; RULE-003/009 | L2 | SMK-003 |
| E1 | `app/api/track.py` | `handle_track_request(body, deps)` — framework-neutral CTR-016 handler: server re-validate (RULE-H03), server-derive `raw_event_hash`, drive the hardened seam (registry gate = leg-1 layer 2), normalize+insert, CTR-016 response + PII-safe errors. No egress path (RULE-004). | CTR-016; RULE-001/002/005/007/014/H03 | L1,L2 | SMK-001/003 |
| E2 | `app/measurement/adapters/consent_reader.py` | Staged in-memory `ConsentReader` adapter (the "real adapter" the entry gate names), consume-only. | RULE-002/018 | L1 | — |
| M1 | `migrations/0002_create_ads_measurement_events.sql` | Staged DDL (up+down): 20 fields + `ingested_at`, PK `event_id`, UNIQUE `idempotency_key`, indexes, zone/CHECK guards. Never applied. | CTR-001; RULE-005/007/003/008 | L2 | — |
| — | `tests/test_track_unknown_event.py`, `test_track_idempotency_dedup.py`, `test_measurement_event_store.py`, `test_track_contract_and_validation.py`, `test_m6_2b_fixfirst_regressions.py` (+conftest fixtures) | 33 new tests making SMK-001/SMK-003 runnable end-to-end + pinning F1/F2/MINOR-9/O1. | — | L1,L2 (+L3/L4 runnable) | SMK-001/003 |

## 4. Plan-deltas (deviations require a note)

1. **O1's code lives at the export callers, not in `masking.py` behaviour.** The carried-forward code has no
   existing raw-`session_id`/`correlation_id` export leak (they only enter the durable `web_event_logs` row,
   which O1 says to keep). The reachable export surfaces are NEW (the endpoint): so the endpoint masks
   `correlation_id` in audit detail and never audits `session_id`. `masking.py` is unchanged behaviourally
   (docstring documents the choke point). Enforced + tested in `test_o1_*`.
2. **MINOR-9 uses a self-contained identifier-shape heuristic** (`\d{6,}` run OR id-prefix) rather than importing
   the locked base-event vocab into `audit.py` — that would create an `audit → tracking` import cycle. The
   heuristic preserves the SMK-001 diagnostic behaviour (short/known/lowercase codes stay verbatim) and wraps
   PII-ish tokens. Markers in the test are assembled at runtime to keep literal PII out of the source.
3. **Consent reconciliation at the endpoint.** An **absent** `consent_snapshot_id` FIELD → `422
   CONSENT_MISSING_OR_INVALID` (a track event must reference consent, CTR-016 `required:true`). A **present but
   invalid** consent STATE (missing/expired/opt-out) → the valid event is still **logged internally** with
   **egress ineligible** (RULE-002 gates EGRESS, not ingestion — consistent with M6.2A). SMK-002 (send-time) is
   not M6.2B-bound; egress is OFF regardless. "Consent fail-closed in every path" holds: nothing egresses.
4. **`raw_event_hash` is server-derived** (deterministic canonical JSON of the body minus `idempotency_key` /
   `correlation_id`), never a client hash (RULE-H03) — keeps the LOCKED RULE-005 5-component formula unaltered
   and replay-stable (SMK-003).
5. **No web framework** (M6-OD-011 `framework=""`): `handle_track_request` is a pure handler; HTTP routing /
   status-code mapping binds at the owner integration step. No new dependency added.
6. **`app/config.py`, `app/__main__.py`, `pyproject.toml` carried forward verbatim.** `python -m app` still prints
   the staged posture (its banner text still reads "M6.2A measurement foundation" — cosmetic; the entrypoint's
   job and the flags are unchanged).
7. **The Round-3 `CONSENT_STATE_MALFORMED` try/except around `gate.evaluate` is kept** (defense-in-depth); after
   F2 it is belt-and-suspenders.
8. **`MeasurementEventStore.insert` rejects a revenue-bearing row** in M6.2B (Zone-A only; revenue is set later on
   the ORDER_VERIFIED path, RULE-003) — a fail-closed scope guard, not a doc field change.

## 5. Fail-closed branches (acceptance check) — where each lives

- **Consent**: `gate.py` (absent/not-VALID/scope-not-granted/**untrusted-type** all DENY, F2); the seam binds a
  reader-issued snapshot to the subject and never writes an unbound id; the endpoint requires the consent field.
- **Registry**: `validator.py` (unknown → REJECT, deregistered/missing-owner → HOLD) driven by the endpoint as
  the second unknown-event layer; the client hook is the first.
- **Dedup**: `idempotency.py` (locked key) + both stores (UNIQUE key → no second row); the endpoint returns
  `DUPLICATE`/`idempotent_replay` on replay.
- **Seam integrity (F1)**: every external callee is wrapped → audited DENY, never a raise.
- **Boundary**: read-only ports; `external_send=OFF`; the endpoint exposes eligibility only — no send/dispatch/
  scale/publish; revenue/attribution (Zone B) and DQ transitions (Zone C) are out of scope (later slices).

## 6. Verification (this prompt actually ran)

Pinned interpreter `D:\M6\Module6-workspace\01-coder\.venv\Scripts\python.exe`, cwd `04-artifacts/impl/M6.2B`
(python 3.12):

| Step | Command | Result |
|---|---|---|
| Baseline (carried-forward, pre-patch) | `…python.exe -m pytest -q` | **96 passed** (M6.2A suite green in the M6.2B tree) |
| After fix-first patches (pre-new-modules) | `…python.exe -m pytest -q` | **96 passed** (F1/F2/MINOR-9/O1 = no regression) |
| Green-after (full suite) | `…python.exe -m pytest -q` | **129 passed**, exit 0 (96 + 33 new) |
| Entrypoint | `…python.exe -m app` | prints staged posture BLOCKED/OFF/OFF, exit 0 |
| Handoff hygiene | removed `__pycache__` / `.pytest_cache` | 0 remaining (runs used `PYTHONDONTWRITEBYTECODE=1`) |

## 7. Rollback

Staged ⇒ non-destructive. **Patched** files (F1/F2/MINOR-9/O1, `migrations/README.md`) roll back to their M6.2A
staged version; **new** files roll back by deletion; baseline rollback = delete the M6.2B tree (M6.2A untouched).
Post-real-apply, reverting `ads_measurement_events` uses the down-DDL `DROP TABLE` (M1), not row deletes.

## 8. Governance carried forward (unchanged)

`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` throughout. The CTR-016 canon-flip is
non-blocking operator housekeeping (per M6-P1100). The **MANDATORY M6.2G Scale-Gate re-gate** (ENTRY-001/002/003,
`CORE_EVENT_REGISTRY_PATCH` + `M3_SELLABLE_GATE_FAILOPEN_PATCH`) remains in force before any scale or external
send. This slice does not self-certify (RULE-015) — the runner EVIDENCE_GATE and the boundary/security
adversaries decide closure.
