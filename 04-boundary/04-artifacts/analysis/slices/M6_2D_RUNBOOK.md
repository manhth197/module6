# M6.2D Runbook — Pixel/CAPI/Offline Dedup & Send Discipline

| Field | Value |
|---|---|
| Slice | **M6.2D** — platform send discipline: locked dedup keys, the hash-policy **mechanism** (no raw PII), offline-only-after-ORDER_VERIFIED, platform result logs (doc §12); depends on M6.2C |
| Produced by | **M6-P1308** `M6_2D_DOCS` (ANALYST_ARCHITECT, `analysis_only`) |
| Sources | `00-spec/slices/M6.2D.md`, `M6-P1307.json`, `M6_2D_EVIDENCE_INDEX.md`, `M6.2D/PLAN.md`, `M6.2D/IMPLEMENTATION_NOTES.md` |
| Posture (immutable) | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `HASH_POLICY_RATIFIED=False` |

> **Read first — this is a runbook, not a verdict.** It self-certifies nothing and advances no gate (RULE-015);
> the authoritative slice verdict is the slice-gate Judge's at **M6-P1309**. Four things make M6.2D distinctive and
> must reach the Judge and owner:
> 1. **Exit-gate leg 2 (no PII thô) is PARTIAL by design** — the no-raw-PII *mechanism* is proven (SMK-017 12/12,
>    fail-closed, FAIL-008 not tripped), but hash-policy *conformance* is **BLOCKED on the OPEN owner decision
>    M6-OD-003** (the ratified permitted-send-field list + salt/normalization). The slice spec itself says leg 2 is
>    "BLOCKED on that decision where unresolved". The security review **M6-P1306 honestly returned BLOCKED** on
>    exactly this — **not a leak, no fail gate tripped**; the ledger then **SKIPPED** M6-P1306 via an owner deferral.
> 2. **The M6.2C consent fail-OPEN residuals F-A/F-B/F-C were CLOSED fix-first** here (executed-verified by both
>    M6-P1305 and M6-P1306) — a real positive.
> 3. **BUT a NEW symmetric consent fail-OPEN, F-D, was discovered on the measurement path** — reachable from the
>    untrusted conversions body — and is **still OPEN**, committed to fix fix-first at M6.2E.
> 4. **Two governance decision files are MISSING** (operator/owner TODO, §5.1) — they gate how M6.2G binds these.
>
> Legs L1/L2 are **"supported/partial (staged), not closed"**; the mandatory M6.2G re-gate is unchanged.

---

## 1. What this slice built

The **staged send discipline over the M6.2C dispatcher** — the mechanism that would build a platform payload,
dedup it cross-platform, hash all PII, and log the result — while `external_send=OFF` keeps it from ever sending.
Two parts: **(a) fix-first closure** of the M6.2C consent fail-opens, and **(b) a new integration layer.**

| Capability | Rule | Contract | Where (staged under `04-artifacts/impl/M6.2D/`) |
|---|---|---|---|
| **Fix-first** F-B (gate scope tested on a materialized `frozenset` — subclass `__contains__` can't fool it) | RULE-002, FAIL-002 | CTR-006 | patched `consent/gate.py` |
| **Fix-first** F-C (audience `member_key ↔ subject_ref` bound at enqueue + dispatch — no borrowed consent) | RULE-002, FAIL-002 | CTR-011 | patched `outbox/enqueue.py`, `outbox/audience_dispatcher.py` |
| **Fix-first** F-A (send-time consent check wrapped fail-closed in both dispatchers) | RULE-002, FAIL-002 | CTR-021/022 | patched `outbox/measurement_dispatcher.py`, `audience_dispatcher.py` |
| Hash-policy **mechanism** (every identity field hashed; raw allow-list EMPTY while M6-OD-003 OPEN → fail-closed) | RULE-014, FAIL-008 | — (M6-OD-003) | `integration/hash_policy.py` |
| Platform payload + **shared `event_id = hash(source_event_id + event_code)`** (cross-platform dedup) | RULE-005/014, FAIL-001 | CTR-008 | `integration/payload.py` |
| PII-safe `PlatformResultLog` (staged in-memory; proves single delivery) | RULE-014 | — | `integration/result_log.py` |
| `StagedPlatformTransport` — builds + logs + OFFLINE-after-ORDER_VERIFIED guard, then **raises `ExternalSendBlocked`** (never sends) | RULE-004/003, H01 | CTR-021 | `integration/platform_transport.py` |
| Config fail-closed markers `HASH_POLICY_RATIFIED=False`, `MEASUREMENT_HASH_ALGO=sha256` | RULE-014, H01 | — | `config.py` (extended) |

**No new table / no migration** — M6.2D is a send-discipline layer over the M6.2C outbox (CTR-008); the result log
is a **staged in-memory** store (physical binding is the M6-OD-011 integration step). Cumulative snapshot: the
M6.2C tree is carried forward byte-identical except the 5 fix-first patches; the integration layer is added.

**Scope boundary (carried, not bled):** **inventing hash fields is M6-OD-003** (the mechanism only, no ratified
list); connector choice / real send is **M6-OD-004** + the M6.2G re-gate; attribution → M6.2E; DQ checker → M6.2F.

---

## 2. Operate (staged)

No production service (BLOCKED/OFF); no real platform call anywhere (`external_send=OFF`, no connector).

```bash
cd 04-artifacts/impl/M6.2D
python -m app        # prints the staged posture (BLOCKED / OFF / OFF), exit 0 — no server, no egress
```

- **The send path (staged):** the M6.2C `measurement_dispatcher.run_once()` drains due outbox rows → `send_policy`
  (consent re-checked at send, now F-A/F-B hardened) → `StagedPlatformTransport.deliver(item)`, which: resolves the
  source conversion (read-only) → builds a **PII-safe payload** (all identity fields hashed; shared `event_id`
  across Pixel/CAPI/Offline of one source event for platform dedup) → **refuses OFFLINE unless the source is
  ORDER_VERIFIED** (RULE-003) → records a `PlatformResultLog` entry (no raw PII) → **`external_send=OFF` ⇒ raises
  `ExternalSendBlocked` ⇒ the dispatcher HOLDS the item (never SENT).**
- **Hash policy is fail-closed:** `HASH_POLICY_RATIFIED=False` + an **empty raw allow-list** mean **nothing raw is
  ever formed or emitted** while M6-OD-003 is OPEN. The ratified permitted-send-field list is a forward gate.
- **No real send, ever, in this slice:** the transport builds + logs then blocks; tokens would be `secret_ref`-only.

---

## 3. Verify

```bash
cd 04-artifacts/impl/M6.2D
python -m pytest -q          # expect: 201 passed / 0 failed (final tester run, M6-P1304)
```

| Check | Expected | Evidence |
|---|---|---|
| Full staged suite (185 carried M6.2C+coder + 16 tester smoke nodes) | **201 passed / 0 failed**, exit 0 | `04-artifacts/test-reports/M6.2D/SMOKE_RESULTS.md`; `M6-P1304.json` |
| **M6-SMK-003** — duplicate Pixel/CAPI/Offline → `Dedup, không double count` (single shared platform `event_id`) | **PASS 4/4** | `SMOKE_RESULTS.md` |
| **M6-SMK-017** (proposed HARDENING) — external payload built from raw-PII event → hashed, **no raw phone/email/user-id** in payload or result log | **PASS 12/12 (EXECUTED, not waived)** | `SMOKE_RESULTS.md` |
| L1/L2 supporting legs (`test_platform_dedup_event_id`, `test_hash_policy_no_raw_pii`, `test_offline_after_order_verified`, `test_staged_no_real_send`) | 10/10 | `SMOKE_RESULTS.md` |
| Fix-first regressions F-B/F-C/F-A | pass | `tests/test_m6_2d_fixfirst_regressions.py` |
| No raw PII anywhere (scan) | **CLEAN over 101 files**; FAIL-008 NOT tripped | `04-artifacts/security-reports/M6.2D_security.md` |
| Carried-forward M6.2C suite (no regression from the fix-first patches) | 171 green | `IMPLEMENTATION_NOTES.md` §6 |

> **Verify does NOT assert leg closure, and leg 2 is only PARTIAL.** Leg 1 (no double count) is **SUPPORTED
> (staged)** — tester withheld closure. Leg 2 (no PII) — the **mechanism is met** (no raw PII, FAIL-008 not tripped)
> but **hash-policy conformance is BLOCKED/DEFERRED on M6-OD-003** (§5) and **cannot be certified** here. Whether
> the slice may exit with conformance deferred is the **M6-P1309 Judge's** call.

---

## 4. Rollback — every change

**Baseline rollback is non-destructive: nothing is live.** All artifacts are staged under `04-artifacts/impl/M6.2D/`;
no migration, no external call, no flag written. Cumulative snapshot ⇒ **new** files revert by deletion; the
**patched** carried-forward files revert to their M6.2C version; deleting the M6.2D tree returns to M6.2C (untouched).
**No new table ⇒ no down-DDL for M6.2D.** Per-item detail: `PLAN.md` §5/§8, `IMPLEMENTATION_NOTES.md` §7.

| Change group | Files | Rollback |
|---|---|---|
| **Fix-first patches** (F-B gate, F-C enqueue + audience dispatcher, F-A both dispatchers) | `consent/gate.py`, `outbox/enqueue.py`, `outbox/measurement_dispatcher.py`, `outbox/audience_dispatcher.py` | **Revert each to its M6.2C version** (additive hardening) |
| Hash-policy mechanism | `integration/hash_policy.py` | Delete (new) |
| Platform payload + shared event_id | `integration/payload.py` | Delete (new) |
| Platform result log | `integration/result_log.py` | Delete (new); staged in-memory only |
| Staged platform transport | `integration/platform_transport.py` (`StagedPlatformTransport`) | Delete (new); no real transport exists |
| Integration package init | `integration/__init__.py` | Delete (new) |
| Config markers | `app/config.py` (+`HASH_POLICY_RATIFIED=False`, +`MEASUREMENT_HASH_ALGO=sha256`) | **Revert to M6.2C** (extended; no flag changed) |
| F-C-mandated fixture/test updates | carried M6.2C audience fixtures + tests (2 correctly-bound consent snapshots added, additive) | **Revert to M6.2C** (no test loosened) |
| Tests | `tests/test_platform_dedup_event_id.py`, `test_hash_policy_no_raw_pii.py`, `test_offline_after_order_verified.py`, `test_staged_no_real_send.py`, `test_m6_2d_fixfirst_regressions.py` (+ smoke) | Delete; test doubles only, no raw PII in fixtures |

**No new M6-owned table** (the result log is staged in-memory); **consumed/owned tables unchanged** — M6.2D adds
send discipline only. (Exit-gate leg **7** = this rollback documentation.)

---

## 5. Decision deltas + the governance gaps

### 5.1 GOVERNANCE / TRACEABILITY GAPS — operator/owner TODO (these gate M6.2G)
> Two decision files that the process references but that **do not exist on disk** (`04-artifacts/evidence/decisions/`
> holds only `M6-OD-011.json`, `M6-OVERRIDE-M6P1000-STAGED.json`, `M6-DEFER-F1F2-M6.2B.json`). Surfaced so they are
> not lost — the analyst cannot write to `evidence/decisions/`.
- **`M6-DEFER-OD003-M6.2D.json` is MISSING.** The ledger SKIP of the security review M6-P1306 cites
  `SKIP_APPROVED:M6-DEFER-OD003-M6.2D`, but the backing decision artifact was never created — the deferral exists
  **only in the ledger Note.** *Operator/owner:* create it to back the M6-P1306 SKIP (OD-003 → forward gate at M6.2G).
- **`M6-DEFER-FBC-M6.2D.json` is MISSING.** Recommended by **both** M6-P1209 and M6-P1300 to bind F-B/F-C/F-A **(and
  now F-D)** into the **M6.2G gate (M6-P1600) `RequiredInputs`**, so a real send can never be enabled while a consent
  fail-open is open. F-A/B/C were closed anyway (via the sign-offs), but the decision file **and** the M6-P1600
  `RequiredInputs` wiring remain a TODO — **and F-D is still open**, so this binding matters.

### 5.2 Owner decisions (parameters, for DECISION_REGISTER reconciliation)
| Decision | State | Effect |
|---|---|---|
| **M6-OD-003** (hash policy: permitted send-fields + hashing incl. salt/pepper (O-1) + normalization) | **OPEN — the live leg-2 blocker** | Hash *mechanism* fail-closed (no raw PII); *conformance* uncertifiable until privacy/legal ratify. Must resolve before the M6.2D exit can certify leg 2 and before any real send |
| **M6-OD-004** (connector: Meta vs Google) | OPEN — HARD FORWARD gate before real send | Discipline is platform-agnostic; **no connector exists/called**; M6.2D real send is out of scope |
| **M6-OD-008** (PAYMENT_COMPLETED as revenue) | OPEN | Offline only after ORDER_VERIFIED is the **fail-closed default** (RULE-003) |
| **M6-OD-012** (masking format) | OPEN | `abc***xy` for any identity in logs/evidence |
| **M6-OD-011** (stack) | Carried DECIDED | Result-log physical binding + real transport wiring at owner integration |
| **ENTRY-001 / ENTRY-003** (inherited) | RISK-ACCEPTED under `M6-OVERRIDE-M6P1000-STAGED` (M6-P1000 verdict **BLOCKED**, NOT converted) | Bound to M6.2A entry + the **mandatory M6.2G re-gate**; not checked at M6.2D |

---

## 6. Changelog delta produced by this slice

**One deferred housekeeping item; no in-band schema change.** The slice adds **no schema change beyond the
harmonized contracts** (SCHEMA_CHANGELOG rows 9–33, judged PASS at M6-P0715 SIGNED). It adds **no new table/migration**.

- **CTR-008 canon-flip (operator, out-of-band):** `M6-CTR-008` (`marketing_measurement_outbox`) is still
  `MISSING / OWNER_DECISION_REQUIRED` in canon but **satisfied-for-entry** (producer M6-P0705 PASS; gate M6-P0715
  SIGNED). Canon-flip is **deferred, non-blocking operator housekeeping** (same class as prior slices).
- New tokens (`ExternalSendBlocked`, `HASH_POLICY_RATIFIED`, `MEASUREMENT_HASH_ALGO`, result-log result codes,
  `SYNC_BLOCKED_CONSENT_SUBJECT_MISMATCH`) are **implementation-internal vocabulary**, not owner-facing schema → **no**
  SCHEMA_CHANGELOG row. **Note:** if the owner ratifies M6-OD-003, the resulting permitted-send-field list / hashing
  approach IS an owner decision + likely a schema/CHANGELOG delta **at that time** — recorded then, not here.

---

## 7. Handoff to M6.2E (and the forward gates)

**M6.2E adds attribution materialization** (`attribution_materializer` CTR-023, `ads_attribution_context` CTR-002).
The coder committed to close **F-D fix-first at M6.2E** — that must happen there.

### 7.1 MUST-FIX fix-first at M6.2E — the NEW consent fail-OPEN (highest priority)
> F-A/F-B/F-C are closed. **F-D is the new one and it is OPEN.** Like M6.2C's F-C, it is a consent-bypass on the
> money/PII egress path — and it is **reachable from the untrusted conversions body.** It is armed-not-fired **only**
> because `StagedPlatformTransport` blocks the real send.
- **F-D [consent fail-OPEN — measurement-path twin of F-C, REACHABLE from the untrusted body]:** the M6.2C
  conversions endpoint (`app/api/conversions.py`) requires a `consent_snapshot_id` but **never binds the snapshot's
  `subject_ref` to the conversion's `customer_or_guest_key`**; the measurement dispatcher's send-time `permits_send`
  checks the snapshot's own subject but not that it belongs to the conversion's subject. So a conversion for subject
  X citing subject Y's VALID consent builds a payload on **borrowed consent**. The audience F-C fix was **not**
  applied to the symmetric measurement path (coder flagged it, `IMPLEMENTATION_NOTES §4.3`; NOT self-fixed — closing
  it changes the endpoint signature + ripples into carried tests, an unplanned scope change). Both M6-P1305 and
  M6-P1306 confirmed OPEN. **Fix:** bind `customer_or_guest_key ↔ subject_ref` in the measurement path (enqueue +
  send), mirroring the F-C audience fix. **Must close before `external_send` can ever flip.**

### 7.2 MUST-FIX before real send — hash conformance + robustness/DQ (routed to CODER / owner)
- **M6-OD-003 (privacy/legal) — the leg-2 conformance blocker:** ratify the permitted-send-field list + hashing
  approach incl. **salt/pepper (O-1: the code uses unsalted `sha256`)** + normalization. Until then leg 2 conformance
  is uncertifiable and no real send may occur.
- **F-E [latent]:** `payload.py` joins `source_event_id`+`event_code` for the platform `event_id` **unescaped**
  (non-injective, the M6.2A MAJOR-5 class); not endpoint-reachable, a collision is an under-count (not FAIL-001).
  Escape/canonicalize like the outbox `_hash_key`.
- **F-F [latent]:** `getattr(snap,'subject_ref',None)` at `measurement_dispatcher.py:82` runs **before** the F-A
  try/except and only swallows `AttributeError` — a `subject_ref` property that *raises* crashes `run_once`. Wrap it.
- **O-2/O-4 [DQ → M6.2F]:** the shared `event_id` excludes the customer → under-count; staged held items re-drain
  each run, appending **unbounded** BLOCKED result-log records (PII-safe, but grows).
- Full detail: `04-artifacts/boundary-reports/M6.2D_boundary.md`, `04-artifacts/security-reports/M6.2D_security.md`.

### 7.3 Hard forward gates (immovable)
- **M6-OD-003 + M6-OD-004 MUST be decided before any real external send;** real connector tokens **`secret_ref`-only**;
  the endpoints need request **authN/authZ** and the dispatchers **worker service-account scoping** at the M6-OD-011/004 binding.
- **M6.2G Scale-Gate re-gate (MANDATORY):** ENTRY-001/002/003 re-checked before any scale/send (M6-P1000 stays
  **BLOCKED**). The **F-B/F-C/F-A/F-D binding** (`M6-DEFER-FBC-M6.2D.json`, §5.1) should be wired into the M6.2G gate
  (M6-P1600) `RequiredInputs` so a real send cannot be enabled with an open consent fail-open.
- **Posture stays `BLOCKED` / `OFF` / `OFF` / `HASH_POLICY_RATIFIED=False`.**

---

## 8. Pointers for the slice-gate Judge (M6-P1309)

This runbook and `M6_2D_EVIDENCE_INDEX.md` are **descriptive**. The slice verdict is the Judge's, from the evidence.
1. **What holds (executed):** entry is a genuine Judge PASS (M6-P1300 `SIGNED`); dedup (SMK-003) + the no-raw-PII
   **mechanism** (SMK-017 12/12, FAIL-008 not tripped, scan clean) hold; **F-A/F-B/F-C closed** fix-first, executed-verified.
2. **Leg 2 is the crux:** decide whether the slice may exit with the hash **mechanism** proven while **conformance**
   is deferred on **M6-OD-003** — the security review **M6-P1306 returned BLOCKED** (honest, no leak, no fail gate),
   ledger-SKIPPED via an owner deferral whose **decision file is missing** (§5.1). Per the slice spec, leg 2 is
   explicitly "BLOCKED on that decision where unresolved". Read `M6-P1306.json` + `M6.2D_security.md` directly.
3. **The sharp point — F-D:** a NEW consent fail-OPEN on the measurement path, **reachable from the untrusted body**,
   still OPEN, committed fix-first to M6.2E. It (with F-A/B/C) should be bound into the M6.2G gate via the missing
   **`M6-DEFER-FBC-M6.2D.json`**.
4. **Immovables:** ENTRY-001/003 risk-accepted (M6-P1000 BLOCKED, not converted); the **mandatory M6.2G re-gate**
   stands regardless — nothing here authorizes real scale or send; `external_send=OFF`, `HASH_POLICY_RATIFIED=False`.

*Analysis-only: no code, no migration, no flag, no external call, no self-certification. `04-artifacts/state/` untouched.*
