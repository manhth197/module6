# M6.2A — ADS Phase 1 Data Foundation (STAGED)

Staged implementation of slice **M6.2A**: the clean measurement foundation — **valid events**, **correct identity**,
**fail-closed consent** — built per [`PLAN.md`](PLAN.md) (prompt M6-P1001) and this slice's spec
`00-spec/slices/M6.2A.md`.

## Posture (immutable to this role)

- `global_gateway_state = BLOCKED`
- `production_flag = OFF`
- `external_send = OFF` (egress framework-only; **nothing is ever sent** in this slice)

This code is **staged** under `04-artifacts/impl/M6.2A/`. It applies no migration to any live DB, calls no external
platform, invents no event code, and flips no flag. Egress/attribution/dashboard/scale are later slices (M6.2C+).

> **Entry gate note:** M6.2A was opened by an **owner override** of the BLOCKED entry gate (M6-P1000), for STAGED work
> only — **not** a judge PASS. The ENTRY-001/ENTRY-003 gaps are risk-accepted and re-gated at **M6.2G**. This code
> encodes those gaps as fail-closed defaults (see `PLAN.md` §9 and `app/measurement/registry/validator.py`).

## Layout

```
app/
  config.py                    # staged-posture constants (BLOCKED/OFF/external_send=OFF)
  __main__.py                  # `python -m app` — prints posture, exits 0 (no server, no egress)
  measurement/
    models/consumed.py         # CTR-003/005/006 CONSUMED read-models
    models/web_event_log.py    # CTR-004 M6-OWNED append-only row
    ports.py                   # read-only ports (M6 cannot mutate consumed tables)
    masking.py                 # RULE-014/H02 PII masking (M6-OD-012 default abc***xy)
    audit.py                   # audit records for reject/hold/mapping
    registry/validator.py      # RULE-001 event validity -> REJECT/HOLD + audit   (SMK-001, FAIL-003)
    consent/gate.py            # RULE-002 consent fail-closed                       (SMK-002, FAIL-002)
    identity/resolver.py       # RULE-006 guest->customer mapping + audit
    logs/idempotency.py        # RULE-005 locked idempotency key
    logs/web_event_log_store.py# RULE-007 append-only store + dedup
    ingest.py                  # orchestrates validate -> log -> consent-eligibility (measure-only)
migrations/0001_create_web_event_logs.sql   # staged DDL (up+down), never applied
tests/                         # pytest -q ; fail-closed behaviours + SMK-001/002 mappings
```

## Run / test

```bash
python -m app          # prints staged posture, exits 0
pytest -q              # runs the fail-closed unit/smoke-backing tests
```

Smoke **execution with recorded evidence** (SMK-001/SMK-002, exit-gate legs L4/L5) is the TESTER role
(M6-P1003 / M6-P1004). This slice makes them runnable; it does not self-run or self-certify (RULE-015).
