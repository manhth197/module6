# M6.2C IMPLEMENTATION PLAN — Outbox Workers (STAGED, plan-only)

**Prompt**: M6-P1201 (`M6_2C_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code this prompt)
**Slice**: M6.2C — separate runtime requests from external sync: `conversion_events → marketing_measurement_outbox`
and `customer_segments → marketing_audience_outbox`, drained by dispatcher workers with bounded retry/dead-letter
and consent re-checked at send (doc §5/§7/§12/§13/§19).
**Posture (immutable to this role)**: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`.
This plan writes no code, applies no migration, calls nothing external, scales/publishes nothing, flips no flag.

> **Governance — the M6.2C entry gate is JUDGE-SIGNED; the external-send controls are FORWARD gates, not entry
> blockers, and there is NO M6.2C-scoped fix-first BINDING.** M6-P1200 (entry-gate judge) = **PASS / SIGNED**
> (ledger row 98). Entry opens **STAGED**: `external_send=OFF`, `production_flag=OFF`, `global_gateway_state=
> BLOCKED`, `safety.external_platform_calls=false` — the staged dispatchers can make **no real send**. M6-OD-003
> (hash policy / permitted send fields) and M6-OD-004 (which connector first) are **HARD FORWARD gates before
> M6.2D real send** — M6.2C proves the outbox+worker *capability* only. The **M6.2B boundary/security residuals**
> (F-A/F-B/O-1/MINOR-6/MINOR-9-res) are **carried forward, deferred to the owner integration step**; of these,
> **O-1 is design-relevant here**: outbox rows/payloads must be **fail-closed on PII** (no raw PII stored; PII
> masked on export). The **MANDATORY M6.2G Scale-Gate re-gate** (ENTRY-001/002/003) stands before any scale/send.

---

## 1. Entry-gate verification (what was confirmed before planning)

| Precondition | Source checked | Result |
|---|---|---|
| This prompt is the active one (RUNNING) | `04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv` row 99 | **M6-P1201 = RUNNING** ✓ |
| Dependency resolved | ledger row 98 | **M6-P1200 = SIGNED** (entry-gate judge verdict PASS on disk) ✓ |
| Implementation target LOCKED | `04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json` | `status=LOCKED`, `STAGED_ONLY`, `safety` all false (`external_platform_calls=false` blocks real sends) ✓ |
| M6-OD-011 decided | manifest + `04-artifacts/evidence/decisions/M6-OD-011.json` | `DECIDED` (GREENFIELD python 3.12, `framework=""`) ✓ |
| Slice contracts | M6-P1200 evidence + CONTRACT_REGISTER | **CTR-007/008/009/010/011/017/021/022** all harmonized + **satisfied-for-entry** (producers M6-P0704/0705/0706/0711/0713 PASS, gate M6-P0715 SIGNED; staged schemas present); canon-flip non-blocking ✓ |
| No M6.2C fix-first BINDING | M6-P1200 evidence + `04-artifacts/evidence/decisions/` | none (only M6-OD-011 / M6-OVERRIDE-M6P1000-STAGED / M6-DEFER-F1F2-M6.2B exist; F1/F2 already closed in M6.2B) ✓ |
| Prod/scale flags | brief + manifest `safety` | BLOCKED/OFF/OFF, `external_platform_calls=false`, `live_migrations=false` ✓ |
| M6.2B foundation available | `04-artifacts/impl/M6.2B/` (129 tests green) | present; carried forward per §2 ✓ |

**Conclusion**: entry is open for **STAGED** M6.2C work. No flag flips; the external-send controls are forward
gates (M6-OD-003/004 → M6.2D; M6.2G re-gate), not entry blockers.

---

## 2. Working mode, conventions & staging model

**Reuse M6.2B/M6.2A conventions (acceptance check 5)**: python 3.12, single `app/` package, `pytest -q`,
pure-standard-library, read-only ports for CONSUMED sources with in-memory staged adapters, staged migrations
(up+down, never applied), the **"strict callee, forgiving seam"** discipline, framework-neutral request handlers,
and the M6.2B **O1 mask-on-export** discipline for PII (`app.measurement.masking.mask`).

**Staging model — cumulative snapshot (as in M6.2B).** The whole **M6.2B** `app/`+`tests/`+`migrations/`+config
tree is **carried forward** into `04-artifacts/impl/M6.2C/` **byte-identical** (M6.2C adds a NEW layer; it does
not modify the M6.2B tracking/measurement code), and the new outbox modules are **added**. The TESTER runs
SMK-002/SMK-016 end-to-end against `04-artifacts/impl/M6.2C/`, so the full app must be importable there. The
"change set" (§5) is the **diff vs the carried-forward M6.2B baseline** — all new files; the carried-forward
files are unchanged.

**No web framework (M6-OD-011 `framework=""`)**: `POST /api/ads/conversions` (CTR-017) is a framework-neutral
handler `handle_conversions_request(body, deps)`, like the M6.2B track handler; HTTP routing binds at the owner
integration step. The **dispatcher workers** are plain callables driven by a test/operator runner (no scheduler
dependency added); the real queue/scheduler binding is stack-gated (M6-OD-011).

---

## 3. Scope lock (anchored strictly to `00-spec/slices/M6.2C.md`)

**In scope (5 capabilities):**
1. **`conversion_events`** (CTR-007) — the internal conversion source (M6/Core-owned; revenue only from
   ORDER_VERIFIED, RULE-003; consent-referenced).
2. **`marketing_measurement_outbox`** (CTR-008) + **`marketing_measurement_dispatcher`** worker (CTR-021).
3. **`customer_segments` / `customer_segment_members`** (CTR-009/010) **CONSUMED** (read-only; membership is
   NEVER a trigger owner, RULE-012).
4. **`marketing_audience_outbox`** (CTR-011) + **`marketing_audience_dispatcher`** worker (CTR-022).
5. **`POST /api/ads/conversions`** (CTR-017) — creates a conversion + transactionally ENQUEUES the measurement
   outbox (fan-out per platform); NEVER sends externally.

**Out of scope (explicit — no scope bleed):**
- **Platform-specific dedup/hash** (Pixel `event_id`, CAPI hashing, Offline payload shapes) → **M6.2D**. The
  M6.2C dispatchers apply the send **discipline** (send_policy, bounded retry, dead-letter, consent-at-send) but
  perform **no real platform send** (`external_send=OFF`) and build **no platform-specific payload** (the row
  carries a **PII-safe `payload_ref`** only; hashing at dispatch is M6-OD-003/M6.2D).
- **Attribution** (`attribution_materializer` CTR-023, `ads_attribution_context` CTR-002) → **M6.2E**.
- **Data-quality checker** (CTR-024, PASS/HOLD/FAIL transitions) → **M6.2F**. Consequence: `data_quality_status`
  stays at the M6.2B **initial HOLD**; the dispatcher's `data_quality_pass` component is therefore **fail-closed
  (HOLD → not pass → no send)** in real staged flow (§4). Dashboards → M6.2F; scale/learning → M6.2G+.
- **Real external send / connector selection** (M6-OD-003/004) → M6.2D and the M6.2G re-gate.

---

## 4. Design overview — a transactional outbox that never sends from the runtime

```
 POST /api/ads/conversions (CTR-017)                 customer_segments(APPROVED) + members (CTR-009/010, CONSUMED)
   handle_conversions_request(body)                    enqueue_audience_sync(segment_id, op)
   │ validate untrusted body (RULE-H03)                │ read APPROVED segment + consented members (RULE-004/012)
   │ RULE-003 revenue only ORDER_VERIFIED              │ opt-out/expired member -> not ADD / REMOVE (RULE-002)
   ▼                                                    ▼
 conversion_events (CTR-007) ──TRANSACTIONAL──► marketing_measurement_outbox (CTR-008)    marketing_audience_outbox (CTR-011)
   (INSERT + enqueue in one unit;                 one QUEUED row per (conversion×platform),   one QUEUED row per
    RULE-004: runtime NEVER sends)                UNIQUE dedup_key (RULE-005)                (segment,member,platform,op) UNIQUE
                                                        │                                          │
                          ┌─────────────────────────────┘                                          │
                          ▼                                                                          ▼
   marketing_measurement_dispatcher (CTR-021)  ◄── the ONLY measurement sender (RULE-004)   marketing_audience_dispatcher (CTR-022)
     drain {QUEUED,RETRY} due → send_policy → Transport.send → status                         drain → re-check consent → Transport.sync → status
     send_policy = consent_valid(send-time) AND event_in_registry AND data_quality_pass AND not_duplicate  [doc §12 L257]
     policy-block  -> DEAD_LETTER(reason), AUDITED, NOT sent           (SMK-002 consent fail-closed at send)
     transport-fail-> RETRY(error_log,next_retry_at,retry_count++) -> DEAD_LETTER at max   (SMK-016 bounded, no silent loss)
     Transport (staged) = StagedBlockedTransport: REFUSES to send while external_send=OFF   (leg 1: no real send)
```

**Load-bearing invariants (the top-0.1% core of this slice):**
- **RULE-004 — no direct external send (exit-gate leg 1).** The runtime (the conversions endpoint, the audience
  enqueue) ONLY writes outbox rows; it holds **no transport**. Only the dispatcher workers hold a `Transport`.
  The staged `Transport` (`StagedBlockedTransport`) **refuses to send while `external_send=OFF`**, so even the
  worker makes no real call. There is structurally no runtime→platform path.
- **RULE-002 — two-checkpoint consent (SMK-002, prevents FAIL-002).** Consent is referenced at conversion/enqueue
  time (checkpoint 1) **and re-validated at dispatch** (checkpoint 2, via `ConsentReader.current_state` — reuse
  `ConsentGate.permits_send`). A member opt-out → audience `REMOVE`/not-ADD. A consent-invalid item is **never
  sent**, audited.
- **Bounded retry → dead-letter, no silent loss (SMK-016).** A **transport** failure appends `error_log`, sets
  `next_retry_at`, increments `retry_count`; at `retry_count >= max_retries` → `DEAD_LETTER`. A **send_policy**
  failure (consent/registry/dq/dedup) is a **terminal non-send** (→ `DEAD_LETTER` with a policy reason in
  `error_log`), not an infinite loop. Every terminal state carries a full trace — nothing is silently dropped.
- **Dedup (RULE-005).** Measurement `dedup_key = platform + event_code + customer_or_guest_key + event_ts_bucket +
  source_event_id` is **UNIQUE on the outbox row** (one per conversion×platform, computed at fan-out); audience
  `dedup_key = segment_id + member_key + platform + operation` UNIQUE. A duplicate → no second row, no double send.
- **Fail-closed on PII / staged (O-1 carried, RULE-014/H02).** No raw PII in any outbox row or `payload_ref`
  (PII-safe reference only; hashing at dispatch is M6-OD-003/M6.2D); `customer_or_guest_key`/`member_key` are
  masked on every export (audit, `error_log`, evidence). OFFLINE fan-out only for ORDER_VERIFIED (§12 L250).

---

## 5. Minimal change set — files (all target-relative, staged under `04-artifacts/impl/M6.2C/`)

Legend: **Leg** = M6.2C exit-gate leg (slice legs 1–7). Rollback: staged ⇒ non-destructive; every item is a
**new** file → rollback by deletion (the carried-forward M6.2B tree is untouched). No M6.2B file is modified.

### 5.1 Models (consumed read-models + M6-owned rows)

| # | Target file (new) | Purpose | Contract/Rule | Leg | Smoke |
|---|---|---|---|---|---|
| B1 | `app/measurement/models/conversion_event.py` | `ConversionEvent` (CTR-007): conversion_id, event_code, source_event_id, correlation_id, customer_or_guest_key (PII), consent_snapshot_id, attribution_context_ref?, revenue_value? (ORDER_VERIFIED only), currency=VND, occurred_at, dedup_inputs, dispatch_state[CREATED\|QUEUED\|DISPATCHED\|FAILED], created_at. Frozen. | CTR-007; RULE-003/002/005 | 1 | — |
| B2 | `app/measurement/models/measurement_outbox.py` | `MeasurementOutboxItem` (CTR-008) + `OutboxStatus[QUEUED\|SENT\|RETRY\|DEAD_LETTER]` + `MeasurementPlatform[PIXEL\|CAPI\|OFFLINE]`; doc-named `error_log`/`next_retry_at` verbatim; `dedup_key` (RULE-005), `idempotency_key`, `payload_ref` (PII-safe), consent ref, retry_count/max_retries. | CTR-008; RULE-004/005/002 | 1,2 | SMK-016 |
| B3 | `app/measurement/models/audience_outbox.py` | `AudienceOutboxItem` (CTR-011) + `AudiencePlatform[META_AUDIENCE\|GOOGLE_AUDIENCE]` + `AudienceOperation[ADD\|REMOVE]`; `dedup_key` (audience formula, distinct from RULE-005), retry fields mirror CTR-008. | CTR-011; RULE-004/002/012 | 1,2 | SMK-002/016 |
| B4 | `app/measurement/models/segments.py` | CONSUMED read-models `CustomerSegment` (CTR-009: segment_id, name, approval_state[APPROVED\|PENDING\|REJECTED], criteria_ref) + `SegmentMember` (CTR-010: segment_id, member_key (PII), consent_snapshot_id). Read-only; M6 never writes; membership never a trigger (RULE-012). | CTR-009/010; RULE-004/012/018 | 1 | SMK-002 |

### 5.2 Stores (M6-owned; append/enqueue + status transitions)

| # | Target file (new) | Purpose | Contract/Rule | Leg | Smoke |
|---|---|---|---|---|---|
| C1 | `app/measurement/store/conversion_event_store.py` | `ConversionEventStore`: append + idempotent on `idempotency_key` (replay → existing, no double). No external send. | CTR-007; RULE-005 | 1 | — |
| C2 | `app/measurement/outbox/measurement_outbox_store.py` | `MeasurementOutboxStore`: `enqueue()` (INSERT QUEUED, UNIQUE `dedup_key` dedup), `due_items()` selection ({QUEUED,RETRY} with `next_retry_at` due), status transitions `mark_sent`/`mark_retry`/`mark_dead_letter` (worker-only). Forbidden: a direct "send" method — there is none. | CTR-008; RULE-004/005 | 1,2 | SMK-016 |
| C3 | `app/measurement/outbox/audience_outbox_store.py` | `AudienceOutboxStore`: same shape, audience `dedup_key` UNIQUE (segment+member+platform+op). | CTR-011; RULE-004 | 1,2 | SMK-002/016 |

### 5.3 Ports + adapters (CONSUMED segments)

| # | Target file (new) | Purpose | Contract/Rule | Leg | Smoke |
|---|---|---|---|---|---|
| D1 | `app/measurement/ports.py` (**extend, carried-forward file** — see delta §9.1) | add read-only `SegmentReader` (get_segment(id)→CustomerSegment?, members(segment_id)→Iterable[SegmentMember]). No write methods. | CTR-009/010; RULE-018 | 1 | — |
| D2 | `app/measurement/adapters/segment_reader.py` | Staged in-memory `InMemorySegmentReader` (seeded APPROVED/PENDING segments + members). Consume-only. | RULE-018 | 1 | — |

### 5.4 Outbox seams + dispatcher workers (the load-bearing core)

| # | Target file (new) | Purpose | Contract/Rule | Leg | Smoke |
|---|---|---|---|---|---|
| E1 | `app/measurement/outbox/transport.py` | `Transport` port (`send(item)` / `sync(item)`) + **`StagedBlockedTransport`** — the staged default that **refuses to send while `external_send=OFF`** (raises `ExternalSendBlocked` / returns a blocked result), so the worker makes NO real call. Injectable so SMK-016 can drive a failing/succeeding transport WITHOUT any platform. | RULE-004; H01 | **1** | SMK-016 |
| E2 | `app/measurement/outbox/enqueue.py` | `enqueue_measurement(conversion, platforms)` — fan-out one conversion → one outbox row per platform (OFFLINE only if ORDER_VERIFIED), UNIQUE `dedup_key`; `enqueue_audience_sync(segment_id, operation, deps)` — read APPROVED segment + consented members (RULE-004/012), enqueue audience rows (opt-out → REMOVE/skip). Runtime-side; **holds no Transport** (RULE-004). | CTR-008/011; RULE-004/002/005/012 | 1 | SMK-002 |
| E3 | `app/measurement/outbox/measurement_dispatcher.py` | `MeasurementDispatcher` (CTR-021): `run_once()` drains `due_items()`, evaluates **send_policy** (consent re-check via `ConsentGate.permits_send` + `event_in_registry` via the validator + `data_quality_pass` from the linked event's `data_quality_status==PASS` (fail-closed HOLD) + `not_duplicate`), calls `Transport.send`, transitions status; **policy-block → DEAD_LETTER(reason)+audit (SMK-002)**, **transport-fail → bounded RETRY → DEAD_LETTER (SMK-016)**. The ONLY measurement sender. | CTR-021; RULE-004/002/005; **prevents FAIL-002** | **1,2** | **SMK-002, SMK-016** |
| E4 | `app/measurement/outbox/audience_dispatcher.py` | `AudienceDispatcher` (CTR-022): drain, re-validate consent at send (opt-out → REMOVE/not-sync, SMK-008-shaped/SMK-002), APPROVED-segment-only, bounded retry → dead-letter. The ONLY audience sender. | CTR-022; RULE-002/004/012; **prevents FAIL-002** | **1,2** | **SMK-002, SMK-016** |

### 5.5 Endpoint (framework-neutral)

| # | Target file (new) | Purpose | Contract/Rule | Leg | Smoke |
|---|---|---|---|---|---|
| F1 | `app/api/conversions.py` (+ export in `app/api/__init__` scope) | `handle_conversions_request(body, deps) -> ConversionResult`: server re-validate untrusted body (RULE-H03) → CTR-017 errors (`UNKNOWN_EVENT`, `CONSENT_MISSING_OR_INVALID`, `REVENUE_NOT_VERIFIED` [revenue present + event_code≠ORDER_VERIFIED, RULE-003], `DEDUP_CONFLICT`, `SCHEMA_INVALID`); create `conversion_events` row + **transactionally ENQUEUE** the measurement outbox (fan-out); response `{status CREATED\|DUPLICATE\|REJECTED, conversion_id, idempotent_replay, dispatch_state CREATED\|QUEUED, correlation_id}`; PII-safe errors, correlation masked on export (O1). **Never sends** (holds no Transport, RULE-004). | CTR-017; RULE-001/002/003/004/005/014/H03 | **1** | — |

### 5.6 Staged migrations (M6-owned tables only)

| # | Target file (new) | Purpose | Contract/Rule | Leg | Rollback |
|---|---|---|---|---|---|
| M1 | `migrations/0003_create_conversion_events.sql` | Staged DDL (up+down): CTR-007 fields, PK conversion_id, UNIQUE idempotency_key, dispatch_state, revenue-only-with-ORDER_VERIFIED CHECK. Never applied. | CTR-007; RULE-003/005 | 1 | down-DDL DROP; delete file |
| M2 | `migrations/0004_create_marketing_measurement_outbox.sql` | Staged DDL: CTR-008 fields, PK outbox_id, **UNIQUE dedup_key**, status/retry columns, worker-only guard comment. Never applied. | CTR-008; RULE-004/005 | 2 | down-DDL DROP; delete file |
| M3 | `migrations/0005_create_marketing_audience_outbox.sql` | Staged DDL: CTR-011 fields, PK outbox_id, UNIQUE audience dedup_key, status/retry columns. `customer_segments`/`members` NOT migrated (CONSUMED, CRM owns). Never applied. | CTR-011; RULE-004 | 2 | down-DDL DROP; delete file |
| M4 | `migrations/README.md` (**extend, carried-forward** — delta §9.1) | Append 0003/0004/0005 rows; application order 0001→0005; outbox worker-only + retry/dead-letter rationale. | RULE-H01 | 7 | revert to M6.2B version |

### 5.7 Config

| # | Target file | Change | Rollback |
|---|---|---|---|
| A1 | `app/config.py` (**extend, carried-forward** — delta §9.1) | add outbox constants: `OUTBOX_MAX_RETRIES` (operational config default, e.g. 5 — a VALUE, not an owner-mandated number; the *bound* is doc-mandated), `MEASUREMENT_PLATFORMS` framework list. **No enabling flag changed** (`EXTERNAL_SEND="OFF"` untouched). | revert to M6.2B `config.py` |

---

## 6. Test plan → done-gate / smoke mapping (`pytest -q`; TESTER executes L3/L4)

Fixtures extend `tests/conftest.py` with the segment reader, both outbox stores, the conversions deps, and
injectable transports (succeeding / failing / staged-blocked). All ids synthetic; PII masked; no literal PII in
source (assemble at runtime — the pack secret-scan forbids literals). The carried-forward M6.2B **129 tests stay
green** (M6.2C only adds files).

| # | Target test (new) | Proves | Leg | Smoke | Fail-gate |
|---|---|---|---|---|---|
| T1 | `tests/test_no_direct_external_send.py` | RULE-004: the endpoint + enqueue hold **no Transport**; `StagedBlockedTransport` refuses to send while `external_send=OFF`; every egress originates from an outbox row via a worker, never a runtime request. | **L1** | — | — |
| T2 | `tests/test_conversions_endpoint.py` | CTR-017 validate + create conversion + **transactional enqueue** (fan-out per platform, OFFLINE only for ORDER_VERIFIED); `REVENUE_NOT_VERIFIED`/`UNKNOWN_EVENT`/`CONSENT_MISSING_OR_INVALID`/`SCHEMA_INVALID`; replay → `DUPLICATE`/`idempotent_replay`. | L1 | — | — |
| T3 | `tests/test_measurement_outbox_fanout_dedup.py` | one conversion → one QUEUED row per platform, **UNIQUE dedup_key** (RULE-005); duplicate → no second row / no double send. | L1,L2 | (dedup) | — |
| T4 | `tests/test_dispatcher_retry_deadletter.py` | **SMK-016**: an item whose transport fails N times → bounded `RETRY` (error_log + next_retry_at + retry_count) → `DEAD_LETTER` at `max_retries`; **no infinite retry, no silent loss**; full trace on the dead-lettered row. | **L2** | **SMK-016** | — |
| T5 | `tests/test_consent_failclosed_at_send.py` | **SMK-002 / FAIL-002**: a consent-invalid item is **never sent** (policy-block → DEAD_LETTER(reason)+audit, no `Transport.send` call); a member opt-out → audience `REMOVE`/not-ADD; consent re-validated at **send** time (checkpoint 2). | **L1** | **SMK-002** | **FAIL-002** |
| T6 | `tests/test_audience_chain.py` | RULE-004/012: audience enqueue only from **APPROVED** segments + consented members; non-APPROVED / opt-out → not enqueued (or REMOVE); membership read **never triggers** any CRM/pricing/scale action; member_key masked on export. | L1 | SMK-002 | — |

**Smoke → test binding**: SMK-002 = T5 (+T6); SMK-016 = T4 (+T3 dedup). Smoke **execution with recorded results +
evidence refs** (legs **L3/L4**) is the **TESTER** role's job (M6-P1203 build / M6-P1204 run) — this plan only
wires code+tests to make them runnable. SMK-016 is a **proposed** smoke; leg 4 is satisfied by executing it (no
owner waiver needed). This CODER slice does not self-run or self-certify (RULE-015).

---

## 7. Master traceability matrix

| Item | Files | Contract | Rule(s) | Leg | Smoke | Fail-gate | Rollback |
|---|---|---|---|---|---|---|---|
| Conversion source | B1,C1 | CTR-007 | RULE-003/002/005 | L1 | — | — | delete |
| Measurement outbox + fan-out | B2,C2,E2 | CTR-008 | RULE-004/005 | L1,L2 | SMK-016 | — | delete |
| Measurement dispatcher | E3,E1 | CTR-021 | RULE-004/002/005 | **L1,L2** | **SMK-002/016** | FAIL-002 | delete |
| Audience chain (consumed) | B4,D1,D2 | CTR-009/010 | RULE-004/012/018 | L1 | SMK-002 | — | delete / revert ports |
| Audience outbox + dispatcher | B3,C3,E4 | CTR-011/022 | RULE-002/004/012 | L1,L2 | SMK-002/016 | FAIL-002 | delete |
| Conversions endpoint | F1 | CTR-017 | RULE-001/002/003/004/005/H03 | **L1** | — | — | delete |
| No-direct-send guarantee | E1,E2,F1 | — | **RULE-004** | **L1** | — | — | delete |
| Staged migrations | M1,M2,M3 | CTR-007/008/011 | RULE-004/005/003 | L1,L2 | — | — | down-DDL; delete |
| Config/baseline | A1,M4 | stack | RULE-H01 | L7 | — | — | revert |
| Tests | T1–T6 | — | — | L1,L2 (+L3/L4 runnable) | SMK-002/016 | FAIL-002 | delete |

**Coverage of exit-gate legs**: L1 ✓ (no-direct-send: E1/E2/F1/T1 + endpoint/fan-out), L2 ✓ (retry/dead-letter:
E3/E4/C2/C3/T4), L3/L4 ✓ *made runnable* (TESTER M6-P1203/1204 execute SMK-002/SMK-016), L5 (evidence — process),
L6 (judge — process), **L7 ✓ (this doc — rollback per item)**. Every item maps to a leg and/or smoke (check 1). ✓

---

## 8. Rollback strategy (global)

1. **Nothing is live.** All artifacts staged under `04-artifacts/impl/M6.2C/`; no migration applied, no external
   call, no flag written. Baseline rollback = delete the M6.2C staged tree (M6.2B untouched, prior good state).
2. **Per-item rollback** (§5): every M6.2C item is a **new** file → deletion; the three carried-forward files
   *extended* (`ports.py`, `config.py`, `migrations/README.md`) roll back to their M6.2B version.
3. **Append/immutability caveat** (owner integration step, not this slice): reverting an outbox table after a real
   apply uses the down-DDL `DROP TABLE` (M1/M2/M3), not row deletes.
4. **Consumed tables never mutated** (customer_segments/members read-only) — nothing to roll back on CRM's side.

---

## 9. Plan-deltas & notes

### 9.1 Deltas (deviations require a note)
- **Three carried-forward files are EXTENDED (additively), not rewritten**: `app/measurement/ports.py` (+`SegmentReader`
  protocol), `app/config.py` (+outbox constants; no flag changed), `migrations/README.md` (+0003/0004/0005 rows).
  Each keeps its M6.2B content; rollback = revert to the M6.2B version. All other M6.2B files are byte-identical.
- **`Transport` abstraction (E1)** is introduced so RULE-004 (no runtime send) + `external_send=OFF` (no real
  send) + SMK-016 (testable retry/dead-letter) hold simultaneously: the runtime holds no transport; the worker's
  staged transport refuses to send; tests inject failing/succeeding transports to drive the state machine — none
  ever contacts a platform.
- **send_policy `data_quality_pass` is fail-closed** at M6.2C (no DQ checker until M6.2F/CTR-024): real items sit
  at `data_quality_status=HOLD` → not pass → not sent. SMK-016 exercises the retry/dead-letter machine with
  test-seeded pass-policy items + an injected transport (the mechanism, not a real send).
- **policy-block vs transport-fail** are distinct terminal behaviors: a consent/registry/dq/dedup failure →
  terminal `DEAD_LETTER(reason)` + audit (no retry loop; SMK-002); a transient transport failure → bounded
  `RETRY` → `DEAD_LETTER` (SMK-016). Both are audited with full trace (no silent loss).

### 9.2 Open items (parameters, not blockers for a staged plan)
- **M6-OD-003** (hash policy / permitted send fields) OPEN → payloads are **framework-only**; the outbox stores a
  PII-safe `payload_ref`, hashing happens at dispatch in **M6.2D**; egress stays fail-closed here.
- **M6-OD-004** (connector first: Meta vs Google) OPEN → the platform enums are a framework; no connector is
  selected/called in M6.2C.
- **M6-OD-008** (PAYMENT_COMPLETED as revenue) OPEN → `revenue_value` accepted only for ORDER_VERIFIED (RULE-003);
  PAYMENT_COMPLETED is non-revenue.
- **M6-OD-012** (masking format) OPEN → pack default `abc***xy` for member_key/customer_or_guest_key on export.
- **M6-OD-011** (stack) DECIDED greenfield python; the queue engine, scheduler, transactional-outbox semantics and
  DB binding realize at the owner integration step.
- **M6.2B forward residuals** (F-A/F-B/O-1/MINOR-6/MINOR-9-res) are carried forward and bind at integration; O-1
  (no raw PII in payloads) is honored by the PII-safe `payload_ref` + mask-on-export.
- Smoke **execution** (L3/L4) and the test manifest/run are the TESTER prompts (M6-P1203/M6-P1204).

---

## 10. Acceptance self-map (this prompt's acceptance_checks)

1. *Every planned item maps to a done-gate leg or smoke id* → §5–§7 matrices (each row carries a Leg and/or Smoke). ✓
2. *Rollback step per item* → §5 Rollback columns + §8. ✓
3. *No scope beyond the slice file* → §3 scope lock; platform hash/dedup (M6.2D), attribution (M6.2E), DQ checker
   (M6.2F), real send/connector (M6-OD-003/004) all explicitly deferred; verified against M6.2C.md + ARCH_BASELINE
   + the CTR-007/008/009/010/011/017/021/022 contracts. ✓
4. *Implementation target LOCKED + M6-OD-011 decided* → §1 verification table. ✓
5. *Reuse conventions/test patterns from the locked target repo* → §2 reuses the M6.2B/M6.2A baseline (pytest,
   dataclasses, ports, in-memory adapters, staged migrations up+down, framework-neutral handlers, O1 mask-on-export). ✓

*Plan-only: no code written, no migration applied, nothing sent/scaled/published, no flag flipped;
`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`.*
