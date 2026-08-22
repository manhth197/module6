# M6.2C IMPLEMENTATION NOTES — M6-P1202 (CODER, implement, STAGED)

Realizes [`PLAN.md`](PLAN.md) (M6-P1201) as staged code under `04-artifacts/impl/M6.2C/` against the LOCKED
target manifest (python 3.12, `pytest -q`, `python -m app`). **Nothing shipped**: `global_gateway_state=BLOCKED`,
`production_flag=OFF`, `external_send=OFF`; no migration applied; no external call; no event invented; no flag
flipped; `04-artifacts/state/` not touched; no self-certification (RULE-015).

## 0. Governance & entry

- Ledger: **M6-P1202 = RUNNING** (row 100); dependency **M6-P1201 = PASS** (plan gate). Target `LOCKED`,
  `STAGED_ONLY`, `safety` all false; **M6-OD-011 = DECIDED**.
- Entry gate M6-P1200 = SIGNED: **no M6.2C-scoped fix-first BINDING** (M6.2B F1/F2 already closed). External-send
  controls (M6-OD-003 hash, M6-OD-004 connector) are HARD FORWARD gates before M6.2D real send. The M6.2B
  boundary/security residuals bind at integration; **O-1 (no raw PII in outbox payloads)** is honored here.

## 1. Staging model — cumulative snapshot (as planned §2)

The whole **M6.2B** `app/`+`tests/`+`migrations/`+config tree was **carried forward byte-identical** into
`04-artifacts/impl/M6.2C/` (M6.2C adds a NEW outbox layer; it modifies no M6.2B tracking/measurement code), and
the outbox modules were **added**. The change set below is the **diff vs the carried-forward M6.2B baseline**;
three carried-forward files were **extended additively** (§4 delta 8).

## 2. Change set built (per plan)

| Plan item | File(s) | Contract/Rule | Status |
|---|---|---|---|
| B1 conversion model | `app/measurement/models/conversion_event.py` | CTR-007; RULE-003/002/005 | done |
| B2 measurement outbox model | `app/measurement/models/measurement_outbox.py` | CTR-008; RULE-004/005 | done |
| B3 audience outbox model | `app/measurement/models/audience_outbox.py` | CTR-011; RULE-004/002/012 | done |
| B4 consumed segments | `app/measurement/models/segments.py` | CTR-009/010; RULE-012/018 | done |
| C1 conversion store | `app/measurement/store/conversion_event_store.py` | CTR-007; RULE-005 | done |
| C2+C3 outbox store (consolidated) | `app/measurement/outbox/outbox_store.py` | CTR-008/011; RULE-004/005 | done (delta §4.1) |
| D1 ports +SegmentReader | `app/measurement/ports.py` (extended) | CTR-009/010; RULE-018 | done |
| D2 segment adapter | `app/measurement/adapters/segment_reader.py` | RULE-018 | done |
| E1 transport | `app/measurement/outbox/transport.py` | RULE-004; H01 | done |
| E2 enqueue seam | `app/measurement/outbox/enqueue.py` | CTR-008/011; RULE-004/002/005/012 | done |
| E3 measurement dispatcher | `app/measurement/outbox/measurement_dispatcher.py` | CTR-021; RULE-004/002/005 | done |
| E4 audience dispatcher | `app/measurement/outbox/audience_dispatcher.py` | CTR-022; RULE-002/004/012 | done |
| F1 conversions endpoint | `app/api/conversions.py` | CTR-017; RULE-001/002/003/004/005/H03 | done |
| M1/M2/M3 migrations | `migrations/0003..0005_*.sql` | CTR-007/008/011 | done (staged, not applied) |
| M4/A1 README+config (extended) | `migrations/README.md`, `app/config.py` | RULE-H01 | done |
| T1–T6 tests | `tests/test_*.py` (+conftest fixtures) | — | done (24 tests) |

## 3. Load-bearing invariants (how each is enforced)

- **RULE-004 — no direct external send (leg 1).** The conversions endpoint (`ConversionDeps`) and the enqueue
  seam hold **no Transport** — they only write outbox rows. Only the dispatcher workers hold a `Transport`, and
  the staged `StagedBlockedTransport` raises `ExternalSendBlocked` on every attempt, so even the worker makes no
  real call (`external_send=OFF`). Proven by `test_no_direct_external_send.py`.
- **RULE-002 — two-checkpoint consent (SMK-002, FAIL-002).** Consent is referenced at conversion creation
  (checkpoint 1) and **re-validated at dispatch** via `ConsentGate.permits_send` (checkpoint 2, using
  `ConsentReader.current_state`). A consent-invalid item is a **policy-block → DEAD_LETTER(reason)+audit, NEVER
  delivered** (`test_consent_failclosed_at_send.py`). A member opt-out → audience `REMOVE`/not-ADD.
- **Bounded retry → dead-letter (SMK-016, leg 2).** A transient transport failure → `RETRY` (error_log +
  next_retry_at + retry_count) → `DEAD_LETTER` at `max_retries`; a policy-block is a distinct terminal non-send.
  No infinite retry, no silent loss (`test_dispatcher_retry_deadletter.py`). The single transition mechanic is
  `transport.attempt_delivery`.
- **Dedup (RULE-005 / audience).** UNIQUE `dedup_key` on each outbox row (measurement: one per conversion×platform;
  audience: one per segment×member×platform×op). Keys are **hashed** so no raw PII sits in the key. Fan-out +
  dedup proven by `test_measurement_outbox_fanout_dedup.py`.
- **Fail-closed on PII (O-1).** No raw PII in `dedup_key` (hashed) or `payload_ref` (PII-safe reference); the
  hashed payload is built by the dispatcher at send (M6-OD-003/M6.2D). `customer_or_guest_key`/`member_key` are
  masked on every export (audit/error_log). OFFLINE fan-out only for ORDER_VERIFIED.
- **RULE-012 — membership never a trigger.** The audience enqueue reads segment membership ONLY to build sync
  rows; it triggers no CRM/pricing/scale (`test_audience_chain.py`).

## 4. Plan-deltas (deviations require a note)

1. **Consolidated outbox stores (PLAN C2/C3 → one `OutboxStore`).** The measurement and audience outbox row
   mechanics are byte-identical (outbox_id, UNIQUE dedup_key, status, retry bookkeeping); one generic store
   serves both. The domain distinction lives in the ITEM type + dedup_key formula. Less duplication, same behavior.
2. **Conversion idempotency key is server-derived from the conversion's OWN stable inputs** (event_code +
   source_event_id + customer_or_guest_key + occurred_at(UTC, sec) + order_code), NOT the track RULE-005 formula
   (a conversion carries no page_id/session_id). A replayed conversion maps to the SAME key → DUPLICATE (replay-
   safe). The client `idempotency_key` is required (present) but never trusted (RULE-H03). The per-platform
   RULE-005 `dedup_key` (verbatim formula) lives on the OUTBOX row.
3. **CTR-017 `DEDUP_CONFLICT` is not reachable in M6.2C** (documented, not omitted): because the conversion key
   is server-derived from the same stable inputs used for dedup, two conversions with colliding dedup inputs map
   to the SAME key → `DUPLICATE` (replay-safe), never a different-key conflict. No 409 path is needed here.
4. **`data_quality_pass` is a fail-closed hook.** No DQ checker runs until M6.2F (CTR-024), so the dispatcher's
   `dq_status` hook defaults to `HOLD` → not PASS → not sent (fail-closed). SMK-016's transport retry/dead-letter
   is exercised by injecting a PASS hook + a failing/succeeding transport (test doubles; no real send, no flag flip).
5. **`event_in_registry` is enforced upstream at conversion creation**, not re-looked-up at dispatch: the
   conversions endpoint rejects `UNKNOWN_EVENT`, and the outbox row carries no `event_code` (per CTR-008), so the
   dispatcher relies on the upstream gate (consistent with the CTR-001 note "registry gate enforced upstream at
   ingest"). `not_duplicate` is structural (UNIQUE dedup_key store).
6. **`Transport` abstraction + `ExternalSendBlocked`.** The staged transport refuses to send (external_send=OFF)
   → the dispatcher marks the item **held** (QUEUED + `EXTERNAL_SEND_OFF` note), NOT a retry/dead-letter — the
   staged reality. A transient failure (a different exception) is the retry path. This keeps "no real send" and
   "testable retry" cleanly separate.
7. **`event_ts_bucket` = UTC hour truncation** (the RULE-005 dedup window; granularity is operational config, not
   an owner value). Dedup keys are hashed (`sha256`) — the LOCKED component set/order is unchanged; only the
   serialization is hashed for PII-safety.
8. **Three carried-forward files EXTENDED additively** (rollback = revert to M6.2B version): `app/measurement/
   ports.py` (+`SegmentReader`), `app/config.py` (+`OUTBOX_MAX_RETRIES`, no flag changed), `migrations/README.md`
   (+0003/0004/0005). `app/__main__.py` banner still reads "M6.2A measurement foundation" (carried-forward
   verbatim — cosmetic; the entrypoint job + flags are unchanged).

## 5. Fail-closed branches (acceptance check)

- **Consent**: enqueue decides audience ADD/REMOVE by the hardened gate; the dispatchers re-validate at send
  (permits_send) — invalid → policy-block, never sent. Endpoint requires the consent reference field.
- **Registry**: the conversions endpoint gates `event_code` via the validator (unknown/held → UNKNOWN_EVENT,
  nothing enqueued).
- **Dedup**: UNIQUE dedup_key on both outboxes (replay/duplicate → no second row); conversion idempotency dedup.
- **No-send / retry**: staged transport refuses (held); transient failure → bounded retry → dead-letter (no
  silent loss). Runtime holds no transport.

## 6. Verification (this prompt actually ran)

Pinned interpreter, cwd `04-artifacts/impl/M6.2C`, python 3.12; counts captured in-process (authoritative):

| Step | Command | Result |
|---|---|---|
| Baseline (carried-forward M6.2B tree) | `…python.exe -m pytest -q` | green (exit 0) |
| New M6.2C tests only | `…pytest tests/<the 6 new files>` | **24 passed** |
| Green-after (full suite) | `…python.exe -m pytest -q` | **163 passed**, rc 0 (139 carried-forward + 24 new; no regression) |
| Entrypoint | `…python.exe -m app` | prints staged posture BLOCKED/OFF/OFF, exit 0 |
| Handoff hygiene | removed `__pycache__` / `.pytest_cache` | 0 remaining (runs used `PYTHONDONTWRITEBYTECODE=1`) |

> Note: prior M6.2A/M6.2B evidence reported the carried suite as "129" from a terminal dot-count; the in-process
> subprocess capture here shows the carried M6.2B tree is **139** tests (all green). The discrepancy was a
> counting artifact in the earlier prompts, not a test change — all suites passed with exit 0 throughout.

## 7. Rollback

Staged ⇒ non-destructive. **New** files roll back by deletion; the three **extended** carried-forward files
(`ports.py`, `config.py`, `migrations/README.md`) roll back to their M6.2B version; baseline rollback = delete
the M6.2C tree (M6.2B untouched). Post-real-apply, reverting an outbox table uses the down-DDL `DROP TABLE`.

## 8. Governance carried forward (unchanged)

`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` throughout. M6-OD-003 (hash) + M6-OD-004
(connector) remain HARD FORWARD gates before M6.2D real send. The MANDATORY M6.2G Scale-Gate re-gate
(ENTRY-001/002/003) stands before any scale or external send. No self-certification (RULE-015) — the runner
EVIDENCE_GATE and the boundary/security adversaries decide closure.
