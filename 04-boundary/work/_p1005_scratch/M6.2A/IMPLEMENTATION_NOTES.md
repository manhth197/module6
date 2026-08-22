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
