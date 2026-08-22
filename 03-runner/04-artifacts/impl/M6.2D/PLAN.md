# M6.2D IMPLEMENTATION PLAN — Pixel/CAPI/Offline Dedup & Send Discipline (STAGED, plan-only)

**Prompt**: M6-P1301 (`M6_2D_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code this prompt)
**Slice**: M6.2D — platform send discipline: locked dedup_key/idempotency_key formulas, the hash-policy MECHANISM
(no raw PII in any external payload / result log), offline conversions only after ORDER_VERIFIED, platform
result logs — per doc §12. Depends on M6.2C.
**Posture (immutable to this role)**: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`.
This plan writes no code, applies no migration, calls nothing external, scales/publishes nothing, flips no flag.

> **Governance — the M6.2D entry gate is JUDGE-SIGNED and BINDS fix-first preconditions; the send owner-gates
> are FORWARD gates.** M6-P1300 (entry judge) = **PASS / SIGNED** (ledger row 108). Entry opens **STAGED**
> (`external_send=OFF`, `external_platform_calls=false` — NO real platform call in this slice). Two **BINDING
> fix-first** consent fail-OPEN residuals from the M6.2C security review (M6-P1209, carried into this gate) MUST
> be closed FIRST (§5.1): **F-B** (the consent gate's scope membership trusts a `set`-subclass `__contains__`),
> **F-C** (the audience path never binds `member_key` to the consent snapshot's `subject_ref` → borrowed
> consent), plus **F-A** robustness (wrap `permits_send`/`current_state` fail-closed). **Forward gates** (not
> entry blockers): **M6-OD-003** (hash policy + permitted send fields — privacy/legal) resolves at *M6.2D exit /
> SMK-017*; **M6-OD-004** (connector) is scoped OUT; both, plus the **MANDATORY M6.2G re-gate**, stand before any
> real send. **Governance gap (judge-escalated):** `M6-DEFER-FBC-M6.2D.json` was recommended but NOT created;
> the F-B/F-C/F-A binding is nonetheless **in force via the M6-P1300 sign-off** — this plan closes them fix-first
> regardless. (Creating that decision file + wiring it into RequiredInputs is an operator/owner action; the coder
> role cannot write to `04-artifacts/evidence/decisions/`.)

---

## 1. Entry-gate verification (what was confirmed before planning)

| Precondition | Source checked | Result |
|---|---|---|
| This prompt is the active one (RUNNING) | ledger row 109 | **M6-P1301 = RUNNING** ✓ |
| Dependency resolved | ledger row 108 | **M6-P1300 = SIGNED** (entry judge verdict PASS on disk) ✓ |
| Implementation target LOCKED | `04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json` | `LOCKED`, `STAGED_ONLY`, `safety` all false (`external_platform_calls=false` + `external_send=OFF` = no real send) ✓ |
| M6-OD-011 decided | manifest + decision file | `DECIDED` (GREENFIELD python 3.12) ✓ |
| Slice contract | M6-P1300 evidence + CONTRACT_REGISTER | **CTR-008** (marketing_measurement_outbox) harmonized + satisfied-for-entry (producer M6-P0705 PASS, gate M6-P0715 SIGNED) ✓ |
| Fix-first BINDING (F-B/F-C/F-A) | M6-P1300 evidence (from M6-P1209 sign-off) | in force — encoded §5.1 ✓ |
| Owner gates OPEN but forward | DECISION_REGISTER | M6-OD-003 (hash, → M6.2D exit / SMK-017), M6-OD-004 (connector, OUT) ✓ |
| Prod/scale flags | brief + manifest `safety` | BLOCKED/OFF/OFF, `external_platform_calls=false`, `live_migrations=false` ✓ |
| M6.2C foundation available | `04-artifacts/impl/M6.2C/` (163 tests green) | present; carried forward per §2 ✓ |

**Conclusion**: entry is open for **STAGED** M6.2D work; F-B/F-C/F-A are fix-first coder preconditions; the
real-send owner gates (M6-OD-003/004) and the M6.2G re-gate are forward, not entry blockers.

---

## 2. Working mode, conventions & staging model

**Reuse the M6.2C/B/A baseline (acceptance check 5)**: python 3.12, `pytest -q`, pure-standard-library,
read-only ports + in-memory staged adapters, staged migrations (up+down, never applied), framework-neutral
handlers, the "strict callee, forgiving seam" discipline, the `Transport` port (M6.2C), and O1/O-1 **mask-on-export**
for PII. **Cumulative snapshot**: the whole **M6.2C** tree is carried forward byte-identical; M6.2D **patches**
the three fix-first modules and **adds** the integration (send-discipline) layer. The change set (§5) is the diff
vs the carried-forward M6.2C baseline (163 tests). No M6.2C behavior is changed except the fix-first hardening.

**No real send, no connector, no invented hash fields (staged)**: `external_send=OFF` is immutable, so the
platform transports are **staged** — they build the PII-safe payload + record a result-log entry, then refuse
(no network call). M6-OD-004 (which connector) is OUT — the discipline is platform-agnostic. M6-OD-003 (which
fields, hashed how) is OPEN — the hash **mechanism** is built **fail-closed** (every identity field hashed/dropped;
NO raw PII ever leaves), and the *ratified field list* is a forward gate (exit-gate leg 2). Platform auth tokens
appear only as `secret_ref` (never raw).

---

## 3. Scope lock (anchored strictly to `00-spec/slices/M6.2D.md`)

**In scope (4 capabilities):**
1. **Dedup across Pixel / CAPI / Offline** — the locked keys: internal `dedup_key`/`idempotency_key` (RULE-005,
   unaltered) + the **platform-facing shared `event_id` + `event_name`** so Pixel + CAPI + Offline of ONE source
   event collapse on the platform side (no double count, FAIL-001, SMK-003).
2. **`send_policy` = consent_valid AND event_in_registry AND data_quality_pass AND not_duplicate** (doc §12 L257)
   — evaluated by the dispatcher at send (built in M6.2C; hardened here by F-A/F-B/F-C).
3. **Platform result logs** — a PII-safe record of each (staged) send attempt/outcome per platform.
4. **Offline conversion only after ORDER_VERIFIED** or an owner-approved event (RULE-003; FAIL-001).

**Out of scope (explicit — no scope bleed):**
- **Inventing hash fields** (M6-OD-003) — build the hash **mechanism** only (fail-closed no-raw-PII); the
  permitted-field list awaits M6-OD-003 (exit-gate leg 2 conditionally blocked where unresolved).
- **Connector choice / real send** (M6-OD-004; `external_send=OFF`) → M6.2G re-gate + owner-controlled integration.
- **Attribution** (M6.2E), **dashboards/DQ checker** (M6.2F), **scale/learning** (M6.2G+).
- **New tables**: none — M6.2D is the send-discipline layer over the M6.2C outbox (CTR-008); the platform result
  log is a staged in-memory store (its physical binding is the M6-OD-011 integration step).

---

## 4. Design overview — the staged send discipline over the M6.2C dispatcher

```
 marketing_measurement_dispatcher (M6.2C, CTR-021)  ── the ONLY sender (RULE-004)
   run_once(): due outbox rows -> send_policy -> Transport.deliver -> status
      send_policy = consent_valid(SEND-TIME, F-A/F-B hardened) AND event_in_registry AND data_quality_pass AND not_duplicate
                         │ policy pass
                         ▼
        StagedPlatformTransport.deliver(item)          ◄── M6.2D Integration layer
          1. resolve source conversion (read-only)
          2. build_platform_payload(): PII-safe, ALL identity fields HASHED (hash-policy mechanism, M6-OD-003
             fail-closed) + platform event_id = f(source_event_id, event_code) [SHARED across PIXEL/CAPI/OFFLINE]
          3. OFFLINE guard: refuse unless the source event is ORDER_VERIFIED (RULE-003; FAIL-001)
          4. record a PlatformResultLog entry (platform, event_id, event_name, dedup_key, result) — NO raw PII
          5. external_send=OFF -> raise ExternalSendBlocked -> the dispatcher HOLDS the item (never SENT)
```

**Load-bearing invariants (the top-0.1% core of this slice):**
- **No raw PII in any external payload or result log (RULE-014, FAIL-008, SMK-017).** The payload builder hashes
  every identity field (`customer_or_guest_key`, phone/email-shaped values) with `sha256`; nothing not on the
  ratified allow-list (M6-OD-003, still OPEN) is emitted → **fail-closed**: no raw PII ever. The result log
  records only hashed/PII-safe fields. This is the doc done-gate "no PII thô".
- **No double count (RULE-005, FAIL-001, SMK-003).** Internal `dedup_key` is UNIQUE per (conversion×platform)
  (M6.2C — no double outbox row / send). The **platform `event_id` is SHARED** across Pixel/CAPI/Offline of one
  source event (`event_id = hash(source_event_id + event_code)`), so the platform (Meta) collapses them — a
  *different* event_id per platform would double-count. Proven from the result log: one event_id across platforms.
- **Consent fail-closed at send (RULE-002, FAIL-002) — F-A/F-B/F-C hardened.** The gate membership can no longer
  be fooled by a `set`-subclass (F-B); audience consent is bound to the member's subject (F-C); a reader failure
  at send is a deny, not a crash/fail-open (F-A).
- **Offline only after ORDER_VERIFIED (RULE-003, FAIL-001).** Enforced at fan-out (M6.2C) AND re-asserted by the
  offline transport (defense-in-depth).
- **Staged, no real send.** `external_send=OFF` → the transport builds + logs but never calls a platform; the
  item is held (QUEUED + note), never SENT. Tokens are `secret_ref`-only.

---

## 5. Minimal change set — files (all target-relative, staged under `04-artifacts/impl/M6.2D/`)

Legend: **Leg** = M6.2D exit-gate leg (slice legs 1–7). Rollback: staged ⇒ non-destructive; **new** files → delete;
**patched** carried-forward files → revert to their M6.2C version.

### 5.1 Fix-first BINDING — consent fail-OPEN residuals, DONE FIRST (per M6-P1300 / M6-P1209)

| # | Target file (patched) | Fix | Rule/Contract | Leg | Smoke | Regression constraint |
|---|---|---|---|---|---|---|
| **F-B** | `app/measurement/consent/gate.py` | The scope membership `if scope not in snapshot.consent_scope` trusts the object's `__contains__`, which a `set`-**subclass** can override to always return True (fail-OPEN — bypasses the Round-4/F2 type check). Fix: test membership against a **materialized real** `frozenset(snapshot.consent_scope)` whose `__contains__` cannot be overridden. | RULE-002; **FAIL-002** | 1 | (SMK-002) | all M6.2C consent tests green; a genuine `frozenset[ConsentScope]` still grants |
| **F-C** | `app/measurement/outbox/enqueue.py` + `app/measurement/outbox/audience_dispatcher.py` | The audience path resolves a member's consent snapshot by id but never checks the snapshot's `subject_ref` matches the member → **borrowed consent** (member A synced under member B's valid consent). Fix: bind `member_key ↔ snapshot.subject_ref` (fail-closed on mismatch) at BOTH enqueue (checkpoint 1) and dispatch (checkpoint 2) — mirroring the measurement seam's subject binding. | RULE-002; **FAIL-002** | 1 | SMK-002-shaped | audience ADD proceeds only when the member's own consent is VALID |
| **F-A** | `app/measurement/outbox/measurement_dispatcher.py` + `audience_dispatcher.py` | `_policy_block` calls `permits_send` (→ `consent_reader.current_state`) unwrapped — a reader exception at send would escape (not fail-closed). Fix: wrap the send-time consent check so any exception → **deny** (audited), never a crash or fail-open. | RULE-002; **FAIL-002** | 1 | SMK-002 | a raising reader → deny; normal path unchanged |

> **Fix-first order (top-0.1% check):** F-B/F-C are **armed** consent fail-OPENs — inert only because
> `external_send=OFF`. They go live the instant a real send is enabled (M6.2G). Building the send discipline on
> top of a gate that can fail open would be exactly the wrong order — so §5.1 lands and is proven green **before**
> §5.2/§5.3, and the M6.2D exit gate (M6-P1309, FAIL-002 in scope) verifies closure.

### 5.2 New — the Integration (send-discipline) layer

| # | Target file (new) | Purpose | Rule/Contract | Leg | Smoke |
|---|---|---|---|---|---|
| B1 | `app/measurement/integration/__init__.py` | Integration-layer package (staged send discipline). | — | — | — |
| B2 | `app/measurement/integration/hash_policy.py` | The **hash-policy mechanism** (M6-OD-003-parameterized, **fail-closed**): `hash_identity(value) -> sha256 token`; `to_public_safe(user_data) ` hashes every identity field and emits NOTHING not explicitly allowed. Until M6-OD-003 ratifies the allow-list, NO raw PII is ever emitted. | RULE-014; **FAIL-008**; M6-OD-003 | 2 | SMK-017 |
| B3 | `app/measurement/integration/payload.py` | `build_platform_payload(conversion, platform) -> PlatformPayload` — a PII-safe payload with `event_name` (= event_code), the **shared** `event_id = hash(source_event_id + event_code)` (same across PIXEL/CAPI/OFFLINE of one source event, for platform dedup), and hashed user_data (via B2). No raw PII. | RULE-005/014; **FAIL-001/008** | 1,2 | SMK-003/017 |
| B4 | `app/measurement/integration/result_log.py` | `PlatformResultLog` (staged in-memory): append a PII-safe record per (staged) send attempt `{platform, event_id, event_name, dedup_key, result, at}`; result ∈ {BLOCKED_EXTERNAL_SEND_OFF, WOULD_SEND, DUPLICATE, FAILED}. No raw PII (SMK-017). Proves single delivery per event (SMK-003). | RULE-014; FAIL-001/008 | 1,2 | SMK-003/017 |
| B5 | `app/measurement/integration/platform_transport.py` | `StagedPlatformTransport` (implements the M6.2C `Transport` port): `deliver(item)` → resolve the source conversion (read-only), build the payload (B3), enforce the OFFLINE-after-ORDER_VERIFIED guard (RULE-003), record a result-log entry (B4), then (`external_send=OFF`) raise `ExternalSendBlocked` → the dispatcher HOLDS the item. NEVER a real send. Tokens `secret_ref`-only. | RULE-004/005/014/003; H01; **FAIL-001/008** | 1,2 | SMK-003/017 |

### 5.3 Config

| # | Target file | Change | Rollback |
|---|---|---|---|
| A1 | `app/config.py` (**extend, carried-forward** — delta §9.1) | add the M6-OD-003-pending marker `HASH_POLICY_RATIFIED = False` (fail-closed: the payload builder emits only hashed identity fields while False) and `MEASUREMENT_HASH_ALGO = "sha256"`. **No enabling flag changed** (`EXTERNAL_SEND="OFF"` untouched); no owner value invented (the field allow-list stays empty until M6-OD-003). | revert to M6.2C `config.py` |

*(No new migration: M6.2D adds no M6-owned table — the result log is a staged in-memory store whose physical
binding is the M6-OD-011 integration step. The CTR-008 outbox DDL already exists from M6.2C.)*

---

## 6. Test plan → done-gate / smoke mapping (`pytest -q`; TESTER executes L3/L4)

Fixtures extend `tests/conftest.py` with the platform result log, the staged platform transport (wired with the
conversion store), and a conversion carrying a PII-shaped identity (assembled at runtime — no literal PII in
source). The carried-forward M6.2C **163 tests stay green** (the §5.1 fixes are additive hardening).

| # | Target test (new) | Proves | Leg | Smoke | Fail-gate |
|---|---|---|---|---|---|
| T1 | `tests/test_platform_dedup_event_id.py` | Pixel + CAPI (+Offline for ORDER_VERIFIED) of ONE source event build the **same `event_id`** → platform-side dedup; distinct source events → distinct event_id; internal `dedup_key` UNIQUE per platform (no second row). | **L1** | **SMK-003** | FAIL-001 |
| T2 | `tests/test_hash_policy_no_raw_pii.py` | A conversion whose identity is a phone/email-shaped value → the built payload AND the result-log entry contain **NO raw PII** (all identity hashed); nothing outside the (empty until M6-OD-003) allow-list is emitted — fail-closed. | **L2** | **SMK-017** | **FAIL-008** |
| T3 | `tests/test_offline_after_order_verified.py` | OFFLINE payload built ONLY for an ORDER_VERIFIED source (the transport refuses OFFLINE otherwise); revenue only from ORDER_VERIFIED (RULE-003). | L1,L2 | SMK-003 | FAIL-001 |
| T4 | `tests/test_staged_no_real_send.py` | The staged platform transport builds + logs but NEVER sends (`external_send=OFF`): the item is held, result-log result=BLOCKED_EXTERNAL_SEND_OFF, no `SENT`. | L1 | — | — |
| T5 | `tests/test_m6_2d_fixfirst_regressions.py` | **F-B** (a `set`-subclass whose `__contains__` returns True → the gate DENIES, not fail-open); **F-C** (a member referencing another subject's consent snapshot → not eligible / not synced — borrowed consent refused); **F-A** (a `current_state`/reader exception at send → deny, no crash). | **L1** | **SMK-002** | **FAIL-002** |

**Smoke → test binding**: SMK-003 = T1 (+T3); SMK-017 = T2 (+T4 result-log). Smoke **execution with recorded
results + evidence refs** (legs **L3/L4**) is the **TESTER** role's job (M6-P1303 build / M6-P1304 run). SMK-017 is
a **proposed** smoke; leg 4 is satisfied by executing it. This CODER slice does not self-run or self-certify
(RULE-015). Exit-gate **leg 2** stays **conditionally blocked on M6-OD-003** where the ratified field list is
unresolved — M6.2D proves the *mechanism* (no raw PII); the *policy* resolves at the owner decision.

---

## 7. Master traceability matrix

| Item | Files | Contract | Rule(s) | Leg | Smoke | Fail-gate | Rollback |
|---|---|---|---|---|---|---|---|
| F-B gate membership | gate.py | CTR-006 | RULE-002 | L1 | SMK-002 | FAIL-002 | revert to M6.2C |
| F-C audience subject binding | enqueue.py, audience_dispatcher.py | CTR-011 | RULE-002/012 | L1 | SMK-002 | FAIL-002 | revert to M6.2C |
| F-A fail-closed send check | both dispatchers | CTR-021/022 | RULE-002 | L1 | SMK-002 | FAIL-002 | revert to M6.2C |
| Hash policy mechanism | B2 | — | RULE-014 | **L2** | **SMK-017** | **FAIL-008** | delete |
| Platform payload + shared event_id | B3 | CTR-008 | RULE-005/014 | **L1,L2** | SMK-003/017 | FAIL-001/008 | delete |
| Platform result log | B4 | — | RULE-014 | L1,L2 | SMK-003/017 | FAIL-001/008 | delete |
| Staged platform transport | B5 | CTR-021 | RULE-004/005/014/003 | **L1,L2** | SMK-003/017 | FAIL-001/008 | delete |
| Config (fail-closed hash marker) | A1 | — | RULE-014/H01 | L2 | — | — | revert |
| Tests | T1–T5 | — | — | L1,L2 (+L3/L4 runnable) | SMK-003/017/002 | FAIL-001/002/008 | delete |

**Coverage of exit-gate legs**: L1 ✓ (dedup/event_id: B3/B4/B5/T1/T3 + no-direct-send held T4 + consent F-*/T5),
L2 ✓ (no-raw-PII: B2/B3/B4/T2 — *conditionally blocked on M6-OD-003 field list*), L3/L4 ✓ *made runnable*
(TESTER M6-P1303/1304 execute SMK-003/SMK-017), L5 (evidence — process), L6 (judge — process), **L7 ✓ (this doc —
rollback per item)**. Every item maps to a leg and/or smoke (acceptance check 1). ✓

---

## 8. Rollback strategy (global)

1. **Nothing is live.** All artifacts staged under `04-artifacts/impl/M6.2D/`; no migration, no external call, no
   flag written. Baseline rollback = delete the M6.2D tree (M6.2C untouched, prior good state).
2. **Per-item** (§5): new files → delete; the patched carried-forward files (`gate.py`, `enqueue.py`, both
   dispatchers, `config.py`) → revert to their M6.2C version.
3. **No new table** → no down-DDL needed for M6.2D (the result log is staged in-memory).
4. **Consumed/owned tables unchanged** — M6.2D adds send discipline only.

---

## 9. Plan-deltas & notes

### 9.1 Deltas (deviations require a note)
- **Five carried-forward files EXTENDED/patched (additively/hardening)**: `gate.py` (F-B), `enqueue.py` +
  `audience_dispatcher.py` (F-C), `measurement_dispatcher.py` + `audience_dispatcher.py` (F-A), `config.py`
  (A1 fail-closed hash marker). Each keeps its M6.2C content; rollback = revert to the M6.2C version.
- **Staged platform transport replaces the bare `StagedBlockedTransport` at the M6.2D wiring** for the send-
  discipline tests: it does the payload/hash/dedup/offline/result-log work THEN blocks (external_send=OFF). The
  M6.2C `StagedBlockedTransport` remains available; M6.2D's `StagedPlatformTransport` is the richer staged
  transport that proves the discipline without a real send.
- **`event_id` is derived from the SOURCE event identity** (`hash(source_event_id + event_code)`), NOT per
  platform, so Pixel/CAPI/Offline of one event share it (platform dedup, FAIL-001) — while the internal
  `dedup_key` stays per-platform (one outbox row per conversion×platform, M6.2C). Two different dedup layers.
- **Hash policy is fail-closed with M6-OD-003 OPEN**: the mechanism hashes every identity field and emits an
  empty allow-list of raw fields; SMK-017 proves no raw PII; the ratified field list is a forward gate (leg 2).

### 9.2 Open items / governance
- **Governance gap (judge-escalated, M6-P1300)**: `04-artifacts/evidence/decisions/M6-DEFER-FBC-M6.2D.json` was
  recommended but not created, and not wired into RequiredInputs. The F-B/F-C/F-A binding is **in force via the
  M6-P1300 sign-off**; this plan closes them fix-first regardless. Formalizing the decision file + wiring it into
  M6-P1302 / the M6.2G gate (M6-P1600) RequiredInputs is an **operator/owner action** (the coder cannot write to
  `decisions/`). Flagged here so it is not lost.
- **M6-OD-003** (hash policy / permitted fields) OPEN → hash mechanism fail-closed; ratified list is the leg-2
  forward gate before real send. **M6-OD-004** (connector) OPEN → platform-agnostic; no connector called.
  **M6-OD-008** (PAYMENT_COMPLETED revenue) OPEN → offline only after ORDER_VERIFIED (fail-closed default).
  **M6-OD-012** masking `abc***xy` for any identity in logs/evidence.
- **M6.2G re-gate** (ENTRY-001/002/003; M6-P1000 verdict BLOCKED, not converted) + `external_send=OFF` remain in
  force before ANY real scale or external send. Smoke execution (L3/L4) is the TESTER's (M6-P1303/1304).

---

## 10. Acceptance self-map (this prompt's acceptance_checks)

1. *Every planned item maps to a done-gate leg or smoke id* → §5–§7 matrices. ✓
2. *Rollback step per item* → §5 Rollback + §8. ✓
3. *No scope beyond the slice file* → §3 scope lock; hash-field invention (M6-OD-003), connector/real send
   (M6-OD-004), attribution (M6.2E), DQ/dashboard (M6.2F) all deferred; verified against M6.2D.md + ARCH_BASELINE
   + CTR-008/021. ✓
4. *Implementation target LOCKED + M6-OD-011 decided* → §1. ✓
5. *Reuse conventions/test patterns from the locked target repo* → §2 reuses the M6.2C baseline. ✓

Plus the **BINDING**: F-B/F-C/F-A planned **fix-first** (§5.1) with tests (T5) and a regression constraint
(M6.2C 163-test suite stays green). ✓

*Plan-only: no code written, no migration applied, nothing sent/scaled/published, no flag flipped;
`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`.*
