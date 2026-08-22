# M6.2C Runbook — Outbox Workers

| Field | Value |
|---|---|
| Slice | **M6.2C** — separate runtime from external sync: `conversion_events → marketing_measurement_outbox` + `customer_segments → marketing_audience_outbox`, drained by dispatcher workers (doc §5/§7/§12/§13/§19); depends on M6.2B |
| Produced by | **M6-P1208** `M6_2C_DOCS` (ANALYST_ARCHITECT, `analysis_only`) |
| Sources | `00-spec/slices/M6.2C.md`, `M6-P1207.json`, `M6_2C_EVIDENCE_INDEX.md`, `M6.2C/PLAN.md`, `M6.2C/IMPLEMENTATION_NOTES.md` |
| Posture (immutable) | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` |

> **Read first — this is a runbook, not a verdict.** It self-certifies nothing and advances no gate (RULE-015);
> the authoritative slice verdict is the slice-gate Judge's at **M6-P1209**, strictly from the evidence files.
> **This is the FIRST slice with a real egress surface** (an outbox + two dispatcher workers), so the consent gate
> is now the load-bearing **M6-FAIL-002** control. **What holds today (executed, credit it):** entry is a real
> Judge PASS (M6-P1200 `SIGNED`); **RULE-004 "no direct external send" holds** (runtime holds no transport; only
> the two workers do) and **FAIL-002 holds** — no non-consented item reaches a transport — with egress **doubly
> bolted** (`permits_external_send()` hard-False + `StagedBlockedTransport` raises on every deliver). **What is
> still open — and one item is sharp:** exit-gate legs **L1/L2 are "supported (staged), not closed"** (tester
> withheld closure); and **two of the routed residuals (F-B, F-C) are consent fail-OPEN paths** — they would
> *send an un-held scope* / *borrow another subject's consent* the moment a **real transport** is wired. They are
> armed-not-fired **only** because the staged transport blocks every send. **They MUST close before M6.2D wires a
> real transport.** The mandatory M6.2G Scale-Gate re-gate is unchanged.

---

## 1. What this slice built

The **transactional outbox layer that never sends from the runtime.** Runtime writes outbox rows; **only** the two
dispatcher workers hold a `Transport`, and the staged `StagedBlockedTransport` refuses every real send
(`external_send=OFF`). This slice adds three M6-owned tables (`conversion_events`, `marketing_measurement_outbox`,
`marketing_audience_outbox`) and consumes the CRM segment shapes read-only.

| Capability | Rule | Contract | Where (staged under `04-artifacts/impl/M6.2C/`) |
|---|---|---|---|
| `POST /api/ads/conversions` — create conversion + transactionally ENQUEUE the measurement outbox (holds NO transport) | RULE-001/002/003/004/005, H03 | CTR-017 | `app/api/conversions.py` |
| `conversion_events` source (revenue only ORDER_VERIFIED) | RULE-003/005 | CTR-007 | `models/conversion_event.py`, `store/conversion_event_store.py` |
| `marketing_measurement_outbox` + fan-out (one row per conversion×platform, UNIQUE dedup_key) | RULE-004/005 | CTR-008 | `models/measurement_outbox.py`, `outbox/outbox_store.py`, `outbox/enqueue.py` |
| **measurement dispatcher** — the ONLY measurement sender; send_policy + bounded retry→dead-letter | RULE-004/002/005 | CTR-021 | `outbox/measurement_dispatcher.py` |
| `customer_segments` / `customer_segment_members` CONSUMED (membership never a trigger, RULE-012) | RULE-012/018 | CTR-009/010 | `models/segments.py`, `adapters/segment_reader.py`, `ports.py` (+SegmentReader) |
| `marketing_audience_outbox` + **audience dispatcher** — APPROVED-only, consent re-checked at send | RULE-002/004/012 | CTR-011/022 | `models/audience_outbox.py`, `outbox/audience_dispatcher.py` |
| Staged `Transport` port + `StagedBlockedTransport` (refuses to send while `external_send=OFF`) | RULE-004, H01 | — | `outbox/transport.py` |

Everything is **staged** — no live system, no applied migration, no external call, no flag flipped, no web
framework (endpoint + workers are pure callables; queue/scheduler/HTTP binding is the owner integration step,
M6-OD-011). Cumulative snapshot: the M6.2B tree is carried forward **byte-identical** (no M6.2B code modified);
M6.2C **adds** the outbox layer + **extends** 3 files additively (`ports.py`, `config.py`, `migrations/README.md`).

**Scope boundary (carried, not bled):** platform-specific dedup/hash (Pixel event_id, CAPI hashing, Offline
shapes) → **M6.2D**; real connector selection (M6-OD-003/004) → M6.2D + M6.2G re-gate; attribution (Zone B, CTR-023)
→ M6.2E; DQ checker (CTR-024) → M6.2F. Consequence: `data_quality_status` stays at M6.2B initial **HOLD**, so the
dispatcher's `data_quality_pass` component is **fail-closed** (HOLD → not pass → not sent) in real staged flow.

---

## 2. Operate (staged)

No production service (BLOCKED/OFF). The outbox layer is exercised as an in-memory library + end-to-end test suite.

```bash
cd 04-artifacts/impl/M6.2C
python -m app        # prints the staged posture (BLOCKED / OFF / OFF), exit 0 — no server, no egress
```

- **Conversions entry point:** `app/api/conversions.py::handle_conversions_request(body, deps)` — framework-neutral,
  pure over an untrusted mapping. Server re-validates (RULE-H03) → CTR-017 errors (`UNKNOWN_EVENT`,
  `CONSENT_MISSING_OR_INVALID`, `REVENUE_NOT_VERIFIED` [revenue present + event not ORDER_VERIFIED, RULE-003],
  `SCHEMA_INVALID`) → creates a `conversion_events` row + **transactionally enqueues** the measurement outbox (fan-out
  per platform, OFFLINE only for ORDER_VERIFIED) → returns `{status, conversion_id, idempotent_replay, dispatch_state
  CREATED|QUEUED, correlation_id}`. **Holds no transport — never sends** (RULE-004).
- **Dispatcher workers** (`measurement_dispatcher`, `audience_dispatcher`) are plain callables (`run_once()` drains
  due `{QUEUED, RETRY}` rows). Each evaluates **send_policy** (`consent_valid` re-checked at send = RULE-002
  checkpoint 2, `event_in_registry`, `data_quality_pass`, `not_duplicate`) → `Transport.send/sync`. **A policy-block
  → terminal `DEAD_LETTER(reason)` + audit, never sent (SMK-002);** a **transport failure → bounded `RETRY`
  (error_log + next_retry_at + retry_count) → `DEAD_LETTER` at max (SMK-016).** The staged transport refuses every
  real send, so the worker marks the item held (`EXTERNAL_SEND_OFF`), not a retry/dead-letter — the staged reality.
- **Audience path:** `enqueue_audience_sync` reads only **APPROVED** segments + consented members (RULE-004/012);
  opt-out → `REMOVE`/not-`ADD`; membership read triggers no CRM/pricing/scale action.
- **No egress:** endpoint + enqueue hold no transport; workers' transport is staged-blocked; `permits_external_send()`
  hard-returns False (RULE-004). Real platform payloads (hashing, connector) are M6.2D.

---

## 3. Verify

```bash
cd 04-artifacts/impl/M6.2C
python -m pytest -q          # expect: 171 passed / 0 failed (final tester run, M6-P1204)
```

| Check | Expected | Evidence |
|---|---|---|
| Full staged suite (139 carried M6.2B + 24 coder + 8 tester smoke nodes) | **171 passed / 0 failed**, exit 0 | `04-artifacts/test-reports/M6.2C/SMOKE_RESULTS.md`; `M6-P1204.json` |
| **M6-SMK-002** — valid event, missing consent → `Không external measurement, không audience sync` | **PASS 4/4** | `SMOKE_RESULTS.md` (both clauses via the RULE-002 two-checkpoint gate; guards FAIL-002) |
| **M6-SMK-016** (proposed HARDENING) — outbox item fails N times → bounded retry + error_log/next_retry_at → dead-letter; no infinite retry, no silent loss | **PASS 4/4 (EXECUTED, not waived)** | `SMOKE_RESULTS.md` |
| L1/L2 supporting legs (`test_no_direct_external_send`, `test_dispatcher_retry_deadletter`, ...) | 13/13 | `SMOKE_RESULTS.md` |
| RULE-004 — endpoint + enqueue hold no transport; StagedBlockedTransport raises; every egress via a worker off an outbox row | pass | `tests/test_no_direct_external_send.py`; boundary `M6.2C_boundary.md` |
| Fan-out + dedup — one conversion → one row per platform, UNIQUE dedup_key (hashed, no raw PII in key) | pass | `tests/test_measurement_outbox_fanout_dedup.py` |
| Carried-forward M6.2B suite (no regression — M6.2C adds files only) | 139 green | `IMPLEMENTATION_NOTES.md` §6 |
| Entry point `python -m app` | staged posture, exit 0 | `IMPLEMENTATION_NOTES.md` §6 |

> **Verify does NOT assert leg closure.** The suites pass within the 171-test run and the boundary adversary
> executed both RULE-004 (no direct send) and the bounded retry/dead-letter mechanic, but legs **L1/L2** are
> **SUPPORTED (staged), not closed** — the tester withheld closure over the **F-A / F-B / F-C** residuals (§7),
> **two of which (F-B, F-C) are consent fail-OPEN paths**. Whether L1/L2 close is the **M6-P1209 Judge's** call.

---

## 4. Rollback — every change

**Baseline rollback is non-destructive: nothing is live.** All artifacts are staged under `04-artifacts/impl/M6.2C/`;
no migration applied, no external call, no flag written. Cumulative snapshot ⇒ the rule is: **new** files revert by
deletion; the **3 extended** carried-forward files revert to their M6.2B version; deleting the M6.2C tree returns to
M6.2B (untouched, the prior good state). Per-item detail: `PLAN.md` §5/§8, `IMPLEMENTATION_NOTES.md` §7.

| Change group | Files | Rollback |
|---|---|---|
| Conversion source | `models/conversion_event.py`, `store/conversion_event_store.py` | Delete (new) |
| Measurement outbox + fan-out | `models/measurement_outbox.py`, `outbox/outbox_store.py`, `outbox/enqueue.py` | Delete (new) |
| Measurement dispatcher (the only measurement sender) | `outbox/measurement_dispatcher.py` | Delete (new) |
| Audience read-models (consumed) | `models/segments.py`, `adapters/segment_reader.py` | Delete (new); no schema shipped to any CRM table |
| Audience outbox + dispatcher | `models/audience_outbox.py`, `outbox/audience_dispatcher.py` | Delete (new) |
| Staged transport | `outbox/transport.py` (`StagedBlockedTransport`) | Delete (new); no real transport exists |
| Conversions endpoint | `app/api/conversions.py` | Delete (new); holds no transport |
| **Extended carried-forward files** | `app/measurement/ports.py` (+SegmentReader), `app/config.py` (+OUTBOX_MAX_RETRIES), `migrations/README.md` | **Revert each to its M6.2B version** (additive extensions; no flag changed) |
| **Staged migrations (3 new owned tables)** | `migrations/0003_create_conversion_events.sql`, `0004_create_marketing_measurement_outbox.sql`, `0005_create_marketing_audience_outbox.sql` (up + down) | **Never applied.** Delete staged files to revert now. **After a real apply, revert = down-DDL `DROP TABLE`** per file (append-only outbox → drop, not row-delete) |
| Tests | `tests/test_no_direct_external_send.py`, `test_dispatcher_retry_deadletter.py`, `test_consent_failclosed_at_send.py`, `test_audience_chain.py`, `test_measurement_outbox_fanout_dedup.py`, `test_conversions_endpoint.py` (+ smoke + conftest) | Delete; test doubles only, no raw PII in fixtures |

**Consumed tables (`customer_segments`, `customer_segment_members`, `event_registry`, consent, `guest_contacts`)
are never mutated by M6** → nothing to roll back on the CRM / Core / Consent side. (Exit-gate leg **7** = this rollback documentation.)

---

## 5. Decision deltas produced / observed by this slice

*(For the operator to reconcile into `DECISION_REGISTER` out-of-band; the analyst does not write `00-spec/`.)*

| Decision | Movement in this slice | Effect |
|---|---|---|
| **M6-OD-003** (hash policy + permitted external-send fields) | OPEN — **HARD FORWARD gate before M6.2D real send** | Outbox stores a **PII-safe `payload_ref`** only; hashing happens at dispatch in M6.2D; egress fail-closed here |
| **M6-OD-004** (connector: Meta vs Google first) | OPEN — **HARD FORWARD gate before M6.2D real send** | Platform enums are a framework; no connector selected/called in M6.2C. M6.2D platform tokens **must be secret_ref-only** |
| **M6-OD-008** (PAYMENT_COMPLETED as revenue) | OPEN | CTR-017 accepts `revenue_value` **only for ORDER_VERIFIED** (RULE-003, fail-closed); PAYMENT_COMPLETED = non-revenue |
| **M6-OD-012** (masking format) | OPEN (forward) | Pack default `abc***xy` for `member_key` / `customer_or_guest_key` mask-on-export |
| **M6-OD-011** (target repo / stack) | Carried DECIDED (GREENFIELD python) | Queue engine / scheduler / transactional-outbox semantics / DB binding realize at owner integration |
| `OUTBOX_MAX_RETRIES` (config) | Introduced as **operational config value** (default 5), NOT an owner-mandated number — the retry *bound* is doc-mandated (§12), the numeric value is config | Bounds the retry→dead-letter loop |
| **ENTRY-001 / ENTRY-003** (inherited) | Unchanged — **RISK-ACCEPTED** under `M6-OVERRIDE-M6P1000-STAGED` (M6-P1000 verdict stays **BLOCKED**, NOT converted) | Bound to the M6.2A entry + the **mandatory M6.2G re-gate**; **not** checked at M6.2C |

---

## 6. Changelog delta produced by this slice

**Eight-contract deferred operator housekeeping; no in-band schema change.** The slice adds **no schema change
beyond the harmonized contracts** (SCHEMA_CHANGELOG rows 9–33, judged PASS at M6-P0715 SIGNED). It **realizes** the
outbox layer as staged code + staged (un-applied) `0003/0004/0005` DDL.

- **Contract canon-flip (operator, out-of-band):** all **eight** slice contracts —
  `M6-CTR-007/008/009/010/011/017/021/022` — are still `MISSING / OWNER_DECISION_REQUIRED` in canon but
  **satisfied-for-entry** (harmonization producers M6-P0704/0705/0706/0711/0713 PASS; gate M6-P0715 SIGNED; staged
  schemas present). The canon-flip — apply the staged schemas to `00-spec/contracts/` + set `CONTRACT_REGISTER` to
  `DRAFT_LOCKED` + add `SCHEMA_CHANGELOG` rows — is **deferred, non-blocking operator housekeeping**. This is the
  same class as M6.2B's CTR-016 flip, now for the outbox+conversions+workers set.
- New tokens (`ExternalSendBlocked`, outbox status/audit reasons, CTR-017 error codes) are **implementation-internal
  vocabulary**, not owner-facing schema → **no** SCHEMA_CHANGELOG row.

---

## 7. Handoff to M6.2D (and the forward gates)

**M6.2D wires the real platform transport** (Pixel/CAPI/Offline + audience connectors) + platform-specific
dedup/hash. That is exactly the step that **arms** the residuals below. **Close them before wiring a real transport.**

### 7.1 MUST-FIX before M6.2D wires a real transport — CONSENT FAIL-OPEN (highest priority)
> These are NOT robustness nits. FAIL-002 holds **today only because the staged transport blocks every send**. With
> a real transport wired, each of these would put a **non-consented / borrowed-consent payload onto a platform.**
- **F-B [consent fail-OPEN, NEW]:** a `set`-subclass `consent_scope` with a lying `__contains__` (empty backing →
  vacuous element check) **defeats the F2 guard** (which validates container/element *types* but trusts
  `__contains__` for the grant) → `permits_send` returns True → **would SEND an un-held scope** (executed with an
  injected transport). **Fix:** evaluate the grant against a rebuilt `frozenset(snapshot.consent_scope)`, not the
  caller's `__contains__`. Needs a compromised/hostile consent adapter — blocked by the staged transport today.
- **F-C [consent fail-OPEN, NEW]:** `enqueue_audience_sync` **never binds `member.member_key` to `snap.subject_ref`**,
  so a mispointed CONSUMED membership → a member `ADD`ed on **another subject's** VALID consent (**borrowed consent**).
  The measurement path binds subject (the M6.2A MAJOR-2 fix); the audience path never did. **Fix:** bind
  `member_key ↔ subject_ref` before `ADD`.

### 7.2 MUST-FIX before M6.2D — robustness + DQ (M6-P1205 / M6-P1206, routed to CODER)
- **F-A [MINOR, robustness]:** the two dispatchers + the audience enqueue wrap `reader.get` but **not**
  `permits_send` / `evaluate` / `current_state` — a hostile consent adapter escapes `run_once` and **aborts the
  drain batch** (lost audit + drain-DoS; no send). Wrap fail-closed like the M6.2A/B seam.
- **O-2 [security, latent by design]:** the audience outbox row + `conversion_events` each hold **one raw identity
  ref** (`member_key` / `customer_or_guest_key`) — masked on every export, hashed into the dedup key, PII-safe
  `payload_ref`, in-memory/staged, never sinked (no leak today). **Enforce OD-012 masking + pseudonymous-id charset
  validation before durable binding.** (The measurement outbox row carries **no** raw PII.)
- **O-4 [DQ]:** a `NaN`/`Inf` `revenue_value` on ORDER_VERIFIED passes the `isinstance` number check → fix
  `math.isfinite`; DQ gap → **M6.2F**.
- **AuthN/authZ (at the M6-OD-011 binding):** the `POST /api/ads/conversions` endpoint needs request **authN/authZ**
  (it is unauthenticated as a pure staged handler today), and the two dispatchers need **worker service-account
  scoping** (least-privilege, `secret_ref`-scoped tokens, identity distinct from the runtime API — see §7.3). Both
  land at the owner HTTP/durable integration step.
- Full detail: `04-artifacts/boundary-reports/M6.2C_boundary.md`, `04-artifacts/security-reports/M6.2C_security.md`.

### 7.3 Hard forward gates (immovable)
- **M6-OD-003** (hash policy) + **M6-OD-004** (connector) **MUST be decided before M6.2D real send.** M6.2D platform
  access/verify tokens **must be `secret_ref`-only**; the two dispatchers become the **credentialed egress
  principals** (least-privilege service accounts, identity distinct from the runtime API — routed at the binding step).
- **Inherited M6.2B endpoint residuals** (its own F-A deep-JSON RecursionError, F-B over-broad hash, O-1, MINOR-6,
  MINOR-9-res — **DISTINCT** from M6.2C's F-A/F-B/F-C above) bind at the same owner HTTP/durable integration step.
- **M6.2G Scale-Gate re-gate (MANDATORY):** ENTRY-001/002/003 re-checked before **any** scale or external send;
  upstream fixes (`CORE_EVENT_REGISTRY_PATCH`, `M3_SELLABLE_GATE_FAILOPEN_PATCH`) must land. M6-P1000 verdict stays **BLOCKED**.
- **Posture stays `BLOCKED` / `OFF` / `OFF`.** Platform dedup/hash (M6.2D) and attribution (M6.2E) are out of scope for M6.2C.

---

## 8. Pointers for the slice-gate Judge (M6-P1209)

This runbook and `M6_2C_EVIDENCE_INDEX.md` are **descriptive**. The slice verdict is the Judge's, from the evidence.
1. **First real egress surface — what holds (executed):** entry is a genuine Judge PASS (M6-P1200 `SIGNED`);
   **RULE-004 no-direct-send** and the load-bearing **FAIL-002 consent control** both hold — no non-consented item
   reaches a transport; egress doubly bolted; **SMK-016 executed, not waived.**
2. **Legs L1/L2 — "supported (staged), not closed":** closure withheld over **F-A / F-B / F-C**. Read
   `M6.2C_boundary.md` and `SMOKE_RESULTS.md` directly, not this summary.
3. **The sharp point:** **F-B and F-C are consent fail-OPEN paths** — armed-not-fired only by the staged transport,
   they would breach FAIL-002 once M6.2D wires a real transport. They are "close before M6.2D", not optional polish.
   Plus F-A (robustness), O-2 (PII before durable binding), O-4 (DQ).
4. **Forward gates & immovables:** M6-OD-003/004 before M6.2D; secret_ref-only tokens + worker service-account
   scoping; the inherited M6.2B residuals + ENTRY-001/003 risk-acceptances (M6-P1000 BLOCKED, not converted); the
   **mandatory M6.2G re-gate** stands regardless — nothing here authorizes real scale or send.

*Analysis-only: no code, no migration, no flag, no external call, no self-certification. `04-artifacts/state/` untouched.*
