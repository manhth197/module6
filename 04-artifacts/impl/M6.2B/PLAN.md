# M6.2B IMPLEMENTATION PLAN — Tracking & Event Contract (STAGED, plan-only)

**Prompt**: M6-P1101 (`M6_2B_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code this prompt)
**Slice**: M6.2B — wire tracking hooks + the measurement-event contract (`ads_measurement_event`) with validation
and append-only logging; unknown-event fail + duplicate-event handled (doc §7/§10/§19/§20).
**Posture (immutable to this role)**: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`.
This plan writes no code, applies no migration, calls nothing external, scales/publishes nothing, flips no flag.

> **Governance — the M6.2B entry gate is JUDGE-SIGNED (not an override), and it BINDS fix-first preconditions.**
> M6-P1100 (M6.2B entry-gate judge) verdict = **PASS / SIGNED** (ledger row 88). Entry opens **STAGED** with four
> residual defects from M6.2A **bound as fix-first coder preconditions** (owner decision
> `04-artifacts/evidence/decisions/M6-DEFER-F1F2-M6.2B.json`, 2026-07-30): **F1** and **F2** are REAL MAJORs that
> were *armed-not-fired* in M6.2A (egress capped, adapters were test doubles, no HTTP endpoint) and **go LIVE at
> M6.2B** when `POST /api/ads/events/track` + a real `ConsentReader` adapter wire into the seam. Per the decision
> they **MUST be closed at the START of M6.2B, BEFORE the endpoint or any real adapter is wired** (§5.1 below).
> `MINOR-9` + `O1` are carried alongside (close before durable binding). Production stays BLOCKED/OFF; the
> **MANDATORY M6.2G Scale-Gate re-gate** (ENTRY-001/002/003) is unchanged.

---

## 1. Entry-gate verification (what was confirmed before planning)

| Precondition | Source checked | Result |
|---|---|---|
| This prompt is the active one (RUNNING) | `04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv` row 89 | **M6-P1101 = RUNNING** ✓ |
| Dependency resolved | ledger row 88 | **M6-P1100 = SIGNED** (entry-gate judge verdict PASS on disk) ✓ |
| Implementation target LOCKED | `04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json` | `status=LOCKED`, `workspace_mode=STAGED_ONLY`, stack `python 3.12` / `pytest -q` / `python -m app`; `safety` all false ✓ |
| M6-OD-011 decided | same manifest + `04-artifacts/evidence/decisions/M6-OD-011.json` | `M6-OD-011 = DECIDED` (2026-07-23), GREENFIELD, `framework=""` ✓ |
| Slice contracts | M6-P1100 evidence + CONTRACT_REGISTER | **M6-CTR-001** `ads_measurement_event` = **DRAFT_LOCKED** (SPEC §10.1, 20 fields); **M6-CTR-016** `POST /api/ads/events/track` = MISSING-but-**SATISFIED for entry** (producer M6-P0711 PASS, gate M6-P0715 SIGNED; schema staged at `04-artifacts/analysis/contracts/CONTRACT_TRACK_APIS.contract.yaml`; canon-flip is non-blocking deferred housekeeping) ✓ |
| Fix-first preconditions bound | `04-artifacts/evidence/decisions/M6-DEFER-F1F2-M6.2B.json` | **F1, F2 fix-first; MINOR-9, O1 carried** — encoded in §5.1 ✓ |
| Prod/scale flags | brief + manifest `safety` | BLOCKED/OFF, `production_access=false`, `external_platform_calls=false`, `live_migrations=false` ✓ |
| M6.2A foundation available | `04-artifacts/impl/M6.2A/` (Round-4 green, 96 tests) | present; carried forward per §2 ✓ |

**Conclusion**: entry is open for **STAGED** M6.2B work. No flag flips; the fix-first BINDING (F1/F2/MINOR-9/O1)
is a coder precondition, not an entry blocker.

---

## 2. Working mode, conventions & staging model

**Reuse M6.2A conventions (acceptance check 5).** The LOCKED target repo (`work-root/target-repo`) is empty
greenfield, so there is nothing to reuse *there*; the reusable baseline is what **M6.2A established** and this
slice extends it verbatim: Python 3.12, single `app/` package, `python -m app` entrypoint, `pytest -q` co-located
under `tests/`, pure-standard-library (dataclasses / `enum` / `hashlib` / `datetime`), ports for read-only
consumed sources, **in-memory staged adapters** in fixtures, staged migrations (up+down, never applied), and the
Round-4 **"strict callee, forgiving seam"** discipline.

**Staging model — cumulative snapshot (decision, stated so rollback is well-defined).** Each target-relative
path `X` is physically staged at `04-artifacts/impl/M6.2B/X` (target `code_root="."`). M6.2B's staged tree is the
**cumulative target-repo state**: the whole M6.2A `app/`+`tests/`+`migrations/` tree is **carried forward**, the
four fix-first modules are **patched in place**, and the new tracking/endpoint/normalized-store modules are
**added**. This is required because the TESTER runs SMK-001/SMK-003 **end-to-end through the endpoint → seam →
stores** against `04-artifacts/impl/M6.2B/` — the full app must be importable there. The "minimal change set"
(§5) is the **diff vs the carried-forward M6.2A baseline**: 4 patched files + the new files below; every other
M6.2A file is carried forward byte-identical.

**No web framework (decision — M6-OD-011 `framework=""`).** Introducing Flask/FastAPI is a new-dependency
decision that is NOT made; it would also not be exercisable while staged. The endpoint is planned as a
**framework-neutral request handler** `handle_track_request(body) -> TrackResult` (pure function over an untrusted
mapping), fully testable without a server. The actual HTTP routing / WSGI binding + concrete status-code mapping
is an **owner-controlled integration step**, stack-gated by M6-OD-011 — exactly as the DB binding and the JS
tracking-SDK binding are deferred. `python -m app` stays the staged-posture stub.

---

## 3. Scope lock (anchored strictly to `00-spec/slices/M6.2B.md`)

**In scope (4 capabilities):**
1. **Frontend tracking hooks** for the locked base events (`VIEW_LANDING..ORDER_VERIFIED`) — the client-side
   emit guard (layer 1 of the two-layer unknown-event check), staged as a Python module.
2. **`POST /api/ads/events/track` (CTR-016) validation** — server re-validates the untrusted body (RULE-H03),
   fail-closed; layer 2 of the unknown-event check via `event_registry` (RULE-001).
3. **`ads_measurement_event` (CTR-001) contract enforcement** — normalize an accepted event into the 20-field
   DRAFT_LOCKED shape (SPEC §10.1) with `currency=VND`, **UNIQUE `idempotency_key`**, and **Zone-A write-once**
   at insert (append + immutability guards).
4. **Idempotency handling** — the LOCKED RULE-005 key; a replayed request → `DUPLICATE` / `idempotent_replay`,
   **no second row** in either store (RULE-005/007, SMK-003 end-to-end).

**Out of scope (explicit — no scope bleed):**
- **`POST /api/ads/conversions` (CTR-017)** + `conversion_events` (CTR-007) + outbox enqueue (CTR-008) → **M6.2C**
  (Outbox layer; verified against ARCH_BASELINE §1.3 and CONTRACT_TRACK_APIS which places CTR-017 at the outbox).
- **External platform sends / Pixel / CAPI / Offline / audience sync** → M6.2C / M6.2D (`external_send=OFF`).
- **Attribution resolution** (`attribution_context` **Zone B**, worker CTR-023) → M6.2E; **data-quality
  transitions** (`data_quality_status` **Zone C**, worker CTR-024) → M6.2F/G. M6.2B sets Zone A only + the
  **initial** `data_quality_status` at insert; it never runs enrichment.
- **Revenue** (`revenue_value`/`order_code`, Zone B) — never set here (revenue only from ORDER_VERIFIED, RULE-003;
  M6.2E/F). Dashboards → M6.2F. Scale/learning → M6.2G+.
- SMK-002 (consent → no external send) is **M6.2C** binding; M6.2B keeps consent **fail-closed at ingest** (it is
  wired through the seam) but does not own the send-time smoke.

---

## 4. Design overview — the tracking pipeline over the (hardened) M6.2A seam

```
  [locked base-event vocab]                         UNTRUSTED HTTP body (RULE-H03)
          │ layer-1 hook guard (client)                     │
          ▼                                                 ▼
   tracking/hooks.py  ──emit──►            app/api/track.py  handle_track_request(body)
   (unknown code → reject+audit)            │ 1. parse+type-check body (reuses seam type boundary)
                                            │ 2. derive raw_event_hash server-side (never trust client)
                                            │ 3. require idempotency_key present (CTR-016) — but RECOMPUTE
                                            │    the RULE-005 key server-side; client value is never trusted
                                            ▼
                     IngestService.ingest_event(...)   ◄── M6.2A seam (F1/F2-HARDENED)
                     validate(RULE-001) → web_event_logs append (RULE-007/005) → consent eval (RULE-002)
                                            │ ACCEPTED + logged
                                            ▼
                     normalize.py → ads_measurement_event (CTR-001, Zone-A insert, UNIQUE idem key)
                                            │
                                            ▼
             TrackResult → CTR-016 response {status, log_id, event_id, idempotent_replay,
                                             data_quality_status(=HOLD initial), correlation_id}
```

- **Two-layer unknown-event fail (exit-gate leg 1)**: the **hook** rejects a code absent from the locked base
  vocab (client guard, audited); the **endpoint/seam** independently re-rejects a code not ACTIVE in
  `event_registry` (RULE-001, prevents FAIL-003). Client validation is never trusted alone.
- **Dedup end-to-end (leg 2, SMK-003)**: `raw_event_hash` is **server-derived** from a deterministic
  canonicalization of the raw event body; the RULE-005 key is computed by the seam. A replay of the same body →
  same key → `web_event_logs` dedups (M6.2A) **and** `ads_measurement_events` UNIQUE-key dedups → response
  `status=DUPLICATE, idempotent_replay=true`, **no second row anywhere**.
- **Fail-closed everywhere**: unknown event → REJECT+audit; consent `!= VALID` → egress ineligible (still
  `external_send=OFF`); wrong-type/hostile body → audited DENY, never a raise (F1); consent gate cannot fail-open
  on a subclass (F2). `revenue_value`/attribution stay unset (later slices); `data_quality_status` initial = HOLD
  (fail-closed: not yet DQ-checked; only CTR-024 may transition it).

---

## 5. Minimal change set — files (all target-relative, staged under `04-artifacts/impl/M6.2B/`)

Legend: **Leg** = M6.2B exit-gate leg (§ slice file legs 1–7). **Rule/Contract** = anchor. Rollback: staged ⇒
non-destructive. **Patched** files roll back to their M6.2A staged version; **new** files roll back by deletion.

### 5.1 Fix-first BINDING preconditions — DONE FIRST, before any endpoint/adapter wiring (per M6-DEFER-F1F2-M6.2B)

| # | Target file (patched) | Fix | Rule/Contract | Leg | Smoke | Regression constraint | Rollback |
|---|---|---|---|---|---|---|---|
| **F1** | `app/measurement/ingest.py` | Complete the forgiving-seam contract: **widen the ts guard** to also catch `OverflowError` and any **tzinfo-raised** exception (broaden to `except Exception` around `normalize_ts`, or catch `OverflowError` + wrap `astimezone`), and **wrap the remaining external callees** — `validator.validate`, `resolver.resolve`, `resolver.subject_matches`, `store.append` — so each becomes an **AUDITED DENY**, never a raise. Proof to close: a year-max `event_ts` with a negative tz offset, and a tzinfo whose `utcoffset()` raises, both currently escape `ingest_event()` (audit lost). | RULE-001; seam contract | 1,2 | SMK-001 (audit-clarity) | ALL 96 M6.2A tests stay green; the Round-4 seam property test still passes (widening a catch is additive). | revert to M6.2A `ingest.py` |
| **F2** | `app/measurement/consent/gate.py` | Harden the **decision point**: in `gate.evaluate`, before the membership test, **assert/coerce** `snapshot.consent_scope` is a `frozenset[ConsentScope]` (**coerce-or-deny**: a `str`/`bytes` or any non-`ConsentScope` element → audited DENY `CONSENT_SCOPE_UNTRUSTED_TYPE`, `return False`). Closes the gate-level half of MAJOR-7: a `ConsentSnapshot` **subclass** that no-ops `__post_init__` keeps a raw-string scope, passes the seam `isinstance` guard, and today substring-matches into ALLOW. Keep `is not ConsentState.VALID` unchanged. | RULE-002; **prevents FAIL-002** | 1 | (SMK-002 M6.2C) | valid `frozenset[ConsentScope]` consent still ALLOWs; all M6.2A consent tests green. | revert to M6.2A `gate.py` |
| **MINOR-9** | `app/measurement/audit.py` | Tighten verbatim-retention of `event_code` in the audit sink so an **identifier-shaped** token (long digit runs / id-prefix shapes) is **wrapped** (`INVALID_EVENT_CODE[mask#hash]`) even if it matches the base char-shape — a PII-ish identifier must not sit raw. **MUST preserve SMK-001 "audit rõ"**: a genuine (short, known/registry-shaped, incl. lower-case) rejected code stays diagnostic. | RULE-014/H02; SMK-001 | 1 | SMK-001 | `test_fixe_lowercase_event_code_is_kept_diagnostic` + the SEC-PII-01 tests stay green. | revert to M6.2A `audit.py` |
| **O1** | `app/measurement/masking.py` (+ its audit/evidence callers) | **Mask-on-export** `session_id` and `correlation_id`: when they cross an export surface (audit `detail`, evidence, server-side error/response **logs**), mask them (`abc***xy`, M6-OD-012). The durable row keeps the value for join/dedup; only the exported copy is masked. | RULE-014/H02; O1 | 1,2 | — | existing masking tests green; the durable `WebEventLog`/`ads_measurement_event` rows are unchanged. | revert to M6.2A `masking.py` |

> **Why fix-first order matters (top-0.1% check — this is the real bottleneck, not the endpoint):** F1/F2 are the
> two ways the money/PII path can misbehave the moment a real body + real adapter arrive — a 500-with-lost-audit
> (F1) or a consent DENY read as GRANT (F2). Wiring the endpoint first would build on a seam that can still raise
> and a gate that can still fail-open. So §5.1 lands and is proven green **before** §5.2/§5.3.

### 5.2 New — tracking hooks + event-contract model + normalized store

| # | Target file (new) | Purpose | Rule/Contract | Leg | Smoke | Rollback |
|---|---|---|---|---|---|---|
| B1 | `app/measurement/tracking/__init__.py`, `app/measurement/tracking/base_events.py` | The **locked base-event vocabulary** (`VIEW_LANDING..ORDER_VERIFIED`, doc extract L123-134) as a frozen enum/set — the single source both the hook guard and the audit MINOR-9 check consult. | RULE-001; doc §20 | 1 | SMK-001 | delete |
| B2 | `app/measurement/tracking/hooks.py` | **Frontend tracking-hook guard (client layer)**: `build_track_event(event_code, ...)` refuses to emit a code absent from the locked vocab (reject/HOLD + audit) — layer 1 of leg 1. Staged Python representation; the JS/SDK binding is an owner integration step (M6-OD-011). | RULE-001; RULE-H03 | 1 | SMK-001 | delete |
| B3 | `app/measurement/models/measurement_event.py` | The **CTR-001 `ads_measurement_event`** dataclass: all **20 DRAFT_LOCKED fields** (SPEC §10.1) + physical `ingested_at`; `currency` locked constant `VND`; frozen **Zone-A** identity fields; PII fields flagged (`customer_id`/`guest_id`). No field renamed/removed/retyped. | CTR-001; RULE-003/005/008 | 2 | SMK-003 | delete |
| B4 | `app/measurement/store/__init__.py`, `app/measurement/store/measurement_event_store.py` | **`ads_measurement_events` store** (staged in-memory adapter): `insert()` = Zone-A append with **UNIQUE `idempotency_key`** (replay → no second row, returns existing `event_id`); **forbidden ops rejected** — Zone-A `UPDATE`, `DELETE`, and `revenue_value` set without an ORDER_VERIFIED order (RULE-003) all raise `MeasurementStoreViolation` at the store boundary (callers wrap as audited denies). Zone B/C updates are the later workers' (not implemented here). | CTR-001; RULE-005/007/003/008 | 2 | SMK-003 | delete |
| B5 | `app/measurement/normalize.py` | `normalize_to_measurement_event(ingest_result, request_ctx) -> ads_measurement_event`: builds the Zone-A row from an ACCEPTED, logged event — `event_id` generated, `event_code`/`event_ts`/`page_id`/`consent_snapshot_id`/`idempotency_key`/`correlation_id`/`currency=VND`/`ingested_at`; `attribution_context` = **empty initial object** (materialized later, M6.2E); `data_quality_status = HOLD` **initial** (fail-closed; only CTR-024 transitions it); revenue/order left null. | CTR-001; RULE-003/009 | 2 | SMK-003 | delete |

### 5.3 New — the framework-neutral endpoint + staged consent adapter

| # | Target file (new) | Purpose | Rule/Contract | Leg | Smoke | Rollback |
|---|---|---|---|---|---|---|
| E1 | `app/api/__init__.py`, `app/api/track.py` | **`handle_track_request(body: Mapping) -> TrackResult`** (framework-neutral, pure over untrusted input): (a) shape/type-check the body (reuses the seam type boundary discipline) → `SCHEMA_INVALID`; (b) require `idempotency_key` present → else `IDEMPOTENCY_KEY_MISSING`, but **recompute** the RULE-005 key server-side (client value never trusted); (c) derive `raw_event_hash` server-side (§5.4); (d) require `consent_snapshot_id` (RULE-002); (e) scan `payload` for raw PII → `RAW_PII_IN_PAYLOAD`; (f) call `ingest_event` (event_registry gate = layer 2 → `UNKNOWN_EVENT`); (g) on ACCEPT, `normalize` + `insert` into `ads_measurement_events`; (h) build the CTR-016 response `{status: ACCEPTED\|DUPLICATE\|REJECTED, log_id, event_id, idempotent_replay, data_quality_status, correlation_id}` with a **PII-safe** error model `{error_code, message, field?, correlation_id}`. **Never sends externally** (RULE-004; no egress client in the path). | CTR-016; RULE-001/002/005/007/014/H03; **prevents FAIL-003** | 1,2 | SMK-001, SMK-003 | delete |
| E2 | `app/measurement/adapters/__init__.py`, `app/measurement/adapters/consent_reader.py` | A **staged in-memory `ConsentReader` adapter** (reads seeded consent snapshots) wired into the endpoint's `IngestService` — the "real adapter" the entry gate names, kept staged. The DB-backed adapter binds at integration (M6-OD-011). F2 hardens the gate regardless of what any adapter returns. | RULE-002/018 | 1 | — | delete |

### 5.4 Server-derived `raw_event_hash` (design note — load-bearing for RULE-005)

CTR-016 does **not** carry `raw_event_hash`, but the LOCKED key needs it. The endpoint **derives it server-side**:
`raw_event_hash = sha256(canonical(raw_event_body))` over a deterministic, key-sorted canonicalization of the
untrusted event body (excluding server/volatile fields — a client-sent `idempotency_key`, `correlation_id`).
This (a) keeps the RULE-005 formula and its 5 components **unaltered** (only the *value* is computed), (b) honors
RULE-H03 (never trust a client hash), and (c) makes SMK-003 natural: an identical replayed body → identical
`raw_event_hash` → identical key → dedup. The exact canonicalization is an implement detail; the constraint is
deterministic + replay-stable + untrusted-body-safe.

### 5.5 Staged migration (the one new M6-OWNED table)

| # | Target file (new) | Purpose | Rule/Contract | Leg | Rollback |
|---|---|---|---|---|---|
| M1 | `migrations/0002_create_ads_measurement_events.sql` | **Staged DDL (up+down)** for `ads_measurement_events`: the 20 doc fields + `ingested_at`, `PRIMARY KEY event_id`, **`UNIQUE(idempotency_key)`**, indexes (`event_ts, event_code, campaign_id, adset_id, ad_id, page_id, order_code, data_quality_status, correlation_id`), and immutability-zone guard comments (Zone-A write-once / Zone-B set-once / Zone-C audited — engine-level enforcement chosen at the M6-OD-011 stack). **Never applied** (`live_migrations=false`). | CTR-001; RULE-005/007/003/008 | 2 | down-DDL `DROP TABLE ads_measurement_events` in-file; staged ⇒ delete file reverts |
| M2 | `migrations/README.md` (patched) | Append M6.2B migration note: application order `0001` then `0002`; staged, never applied; append + Zone-A-immutability rationale. | RULE-H01 | 7 | revert to M6.2A `migrations/README.md` |

### 5.6 Baseline / config / entrypoint (mostly carried forward)

| # | Target file | Change | Rollback |
|---|---|---|---|
| A1 | `pyproject.toml`, `app/config.py`, `app/__init__.py`, `app/__main__.py`, `README.md` | **Carried forward from M6.2A** (no new dependency; `EXTERNAL_SEND="OFF"` etc. unchanged). Add new package `__init__.py` files (`app/api`, `app/measurement/tracking`, `app/measurement/store`, `app/measurement/adapters`) and, if needed, a `README.md` line noting the M6.2B tracking layer. No flag value changes. | delete new inits / revert README |

---

## 6. Test plan → done-gate / smoke mapping (`pytest -q`; TESTER executes L3/L4)

Fixtures extend `tests/conftest.py` with the staged `ConsentReader` adapter, an `ads_measurement_events` store,
and a track-request builder. All ids synthetic; no raw PII. The **carried-forward M6.2A suite (96 tests) MUST stay
green** — the §5.1 patches are additive/hardening and may not regress R1–R4.

| # | Target test (new) | Proves | Leg | Smoke | Fail-gate | Rollback |
|---|---|---|---|---|---|---|
| T1 | `tests/test_track_unknown_event.py` | unknown `event_code` rejected at **BOTH** the hook layer (B2) **and** the endpoint/registry layer (E1), each **audited** | **L1** | **SMK-001** | FAIL-003 | delete |
| T2 | `tests/test_track_idempotency_dedup.py` | replay the same track body → `status=DUPLICATE`, `idempotent_replay=true`, **no second row** in `web_event_logs` **or** `ads_measurement_events` (end-to-end RULE-005/007) | **L2** | **SMK-003** | — | delete |
| T3 | `tests/test_measurement_event_store.py` | Zone-A insert + UNIQUE-key dedup; forbidden ops (Zone-A UPDATE / DELETE / `revenue_value` without ORDER_VERIFIED) rejected; `currency=VND`; initial `data_quality_status=HOLD` | L2 | SMK-003 | — | delete |
| T4 | `tests/test_track_contract_and_validation.py` | CTR-016 response shape + all `validation_errors` (`UNKNOWN_EVENT`, `CONSENT_MISSING_OR_INVALID`, `IDEMPOTENCY_KEY_MISSING`, `SCHEMA_INVALID`, `RAW_PII_IN_PAYLOAD`); consent fail-closed through the endpoint; **no egress path** reachable (`external_send=OFF`) | L1 | SMK-001 | FAIL-003 | delete |
| T5 | `tests/test_m6_2b_fixfirst_regressions.py` | **F1** (year-max ts + negative offset, tzinfo-raise, and each wrapped callee raising → audited deny, **never a raise**); **F2** (`ConsentSnapshot` subclass with raw-str scope → gate **denies**, audited, not fail-open); **MINOR-9** (identifier-shaped unknown code wrapped in audit; a genuine code stays diagnostic); **O1** (`session_id`/`correlation_id` masked on export) | L1,L2 | SMK-001 | FAIL-002/003 | delete |

**Smoke → test binding**: SMK-001 = T1 (+T4); SMK-003 = T2 (+T3). Smoke **execution with recorded results +
evidence refs** (legs **L3/L4**) is the **TESTER** role's job (M6-P1103 build / M6-P1104 run) — this plan only
wires code+tests to make them runnable. This CODER slice does not self-run or self-certify (RULE-015).

---

## 7. Master traceability matrix (every item → leg + smoke + rule + rollback)

| Item | Files | Contract | Rule(s) | Leg | Smoke | Fail-gate | Rollback |
|---|---|---|---|---|---|---|---|
| F1 seam never-raise | ingest.py | CTR-016 | RULE-001 | L1,L2 | SMK-001 | — | revert to M6.2A |
| F2 gate no fail-open | gate.py | CTR-006 | RULE-002 | L1 | (SMK-002 M6.2C) | FAIL-002 | revert to M6.2A |
| MINOR-9 audit event_code | audit.py | — | RULE-014/H02 | L1 | SMK-001 | — | revert to M6.2A |
| O1 mask-on-export | masking.py | — | RULE-014/H02 | L1,L2 | — | — | revert to M6.2A |
| Hook guard (layer 1) | B1,B2 | CTR-016 | RULE-001/H03 | **L1** | **SMK-001** | FAIL-003 | delete |
| Event-contract model | B3 | CTR-001 | RULE-003/005/008 | L2 | SMK-003 | — | delete |
| Normalized store + dedup | B4,B5 | CTR-001 | RULE-005/007/003 | **L2** | **SMK-003** | — | delete |
| Track endpoint (layer 2) | E1,E2 | CTR-016 | RULE-001/002/004/005/007/014/H03 | **L1,L2** | SMK-001/003 | FAIL-003 | delete |
| Staged migration | M1,M2 | CTR-001 | RULE-005/007 | L2 | — | — | down-DDL; never applied |
| Baseline/config | A1 | stack | RULE-H01 | L7 | — | — | delete inits / revert |
| Tests | T1–T5 | — | — | L1,L2 (+L3/L4 runnable) | SMK-001/003 | FAIL-002/003 | delete |

**Coverage of the slice's exit-gate legs**: L1 ✓ (F1/F2/MINOR-9/B2/E1/T1/T4/T5), L2 ✓ (B3/B4/B5/E1/M1/T2/T3/T5),
L3/L4 ✓ *made runnable* (handed to TESTER M6-P1103/1104), L5 (evidence — process), L6 (judge — process), **L7 ✓
(this doc — rollback per item, §5/§8)**. Every planned item maps to a leg and/or a smoke (acceptance check 1). ✓

---

## 8. Rollback strategy (global)

1. **Nothing is live.** All artifacts staged under `04-artifacts/impl/M6.2B/`; no migration applied
   (`live_migrations=false`), no external call, no flag written. Baseline rollback = delete the M6.2B staged tree
   (M6.2A is untouched and remains the prior good state).
2. **Per-item rollback** is tabulated in §5/§7: **patched** files (F1/F2/MINOR-9/O1, `migrations/README.md`) roll
   back to their **M6.2A** staged version; **new** files roll back by deletion.
3. **Append/immutability caveat for the eventual integration step** (owner-controlled, not this slice): reverting
   `ads_measurement_events` after a real apply uses the **down-DDL `DROP TABLE`** in `M1`, not row deletion.
4. **Consumed tables never mutated** by M6 (event_registry / consent / guest_contacts read-only) — nothing to roll
   back on Core/Customer/Consent sides.

---

## 9. Acceptance self-map (this prompt's acceptance_checks)

1. *Every planned item maps to a done-gate leg or smoke id* → §5–§7 matrices (each row carries a Leg and/or Smoke). ✓
2. *Rollback step per item* → §5 Rollback columns + §8. ✓
3. *No scope beyond the slice file* → §3 scope lock; CTR-017/outbox/attribution/DQ/dashboard/external-send
   explicitly deferred to M6.2C–G, verified against the slice file + ARCH_BASELINE + CONTRACT_TRACK_APIS. ✓
4. *Implementation target LOCKED + M6-OD-011 decided* → §1 verification table. ✓
5. *Reuse conventions/test patterns from the locked target repo* → target empty greenfield; §2 reuses the M6.2A
   baseline (pytest, dataclasses, ports, in-memory adapters, staged migration up+down, forgiving-seam). ✓

Plus the **BINDING** condition from the entry gate: F1/F2 are planned **fix-first** (§5.1) and MINOR-9/O1 are
planned to close in this slice, each with a test (T5) and a regression constraint (M6.2A suite stays green). ✓

---

## 10. Notes / open items (parameters, not blockers for a staged plan)

- **M6-OD-011** (stack) DECIDED greenfield python; the concrete HTTP framework/routing, status-code mapping, DB
  engine, and index/partition implementation are realized at the owner-controlled integration step (E1 stays
  framework-neutral; M1 DDL engine-neutral).
- **M6-OD-012** (masking format) OPEN → pack default `abc***xy` used for MINOR-9/O1 masking as a parameter.
- **M6-OD-008** (PAYMENT_COMPLETED as revenue) OPEN → `revenue_value` stays ORDER_VERIFIED-only; not exercised in
  M6.2B (Zone B is out of scope here anyway).
- **M6-OD-003** (hash policy / egress fields) OPEN → irrelevant to M6.2B (store-only; no egress; hashing is at the
  future dispatcher, M6.2C/D).
- **CTR-016 canon flip** (schema → `00-spec/contracts/` + CONTRACT_REGISTER DRAFT_LOCKED + SCHEMA_CHANGELOG) is a
  **non-blocking operator housekeeping** item (per M6-P1100), not a coder step and not a blocker for this plan.
- Smoke **execution** (L3/L4) and the test manifest/run are the TESTER prompts (M6-P1103/M6-P1104); this plan
  makes them runnable but does not run or self-certify them (RULE-015).

*Plan-only: no code written, no migration applied, nothing sent/scaled/published, no flag flipped;
`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`.*
