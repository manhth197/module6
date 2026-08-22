# M6.2B Runbook — Tracking & Event Contract

| Field | Value |
|---|---|
| Slice | **M6.2B** — tracking hooks + `ads_measurement_event` contract with validation + append-only logging (doc §7/§10/§19/§20); depends on M6.2A |
| Produced by | **M6-P1108** `M6_2B_DOCS` (ANALYST_ARCHITECT, `analysis_only`) |
| Sources | `00-spec/slices/M6.2B.md`, `M6-P1107.json`, `M6_2B_EVIDENCE_INDEX.md`, `M6.2B/PLAN.md`, `M6.2B/IMPLEMENTATION_NOTES.md`, `M6-DEFER-F1F2-M6.2B.json` |
| Posture (immutable) | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` |

> **Read first — this is a runbook, not a verdict.** It self-certifies nothing and advances no gate (RULE-015).
> The authoritative slice verdict is the slice-gate Judge's to render at **M6-P1109**, strictly from the evidence
> files. **What is genuinely healthy here (stated accurately, not as a pass):** the M6.2B **entry gate is a real
> Judge PASS** (M6-P1100 `SIGNED`, verdict PASS on disk — *not* an owner override), and the four M6.2A boundary
> residuals **F1 / F2 / MINOR-9 / O1 were closed fix-first** in this slice and executed-verified by both the
> boundary (M6-P1105) and security (M6-P1106) adversaries. **What is still open:** exit-gate legs **L1/L2 are
> "supported at the staged level", not closed** — the tester (M6-P1104) withheld closure over residuals
> MINOR-6 / F-A / F-B; new forward residuals go to CODER before the HTTP/durable binding; the inherited M6.2A
> risk-acceptances (ENTRY-001/003) and the **mandatory M6.2G Scale-Gate re-gate** are unchanged.

---

## 1. What this slice built

The **tracking pipeline over the (now hardened) M6.2A seam** — a framework-neutral track endpoint and the
`ads_measurement_event` contract, both fail-closed, over **two** append-only stores. This slice added a **second
M6-owned table** (`ads_measurement_events`, CTR-001) alongside M6.2A's `web_event_logs` (CTR-004); the consumed
shapes stay read-only.

| Capability | Rule | Contract | Where (staged under `04-artifacts/impl/M6.2B/`) |
|---|---|---|---|
| Frontend hook guard — locked base-event vocab (9 events `VIEW_LANDING..ORDER_VERIFIED`, verbatim) = unknown-event **layer 1** | RULE-001 | CTR-016 | `app/measurement/tracking/base_events.py`, `tracking/hooks.py` |
| `POST /api/ads/events/track` server validation = unknown-event **layer 2** | RULE-001, H03 | CTR-016 | `app/api/track.py` (`handle_track_request`, framework-neutral) |
| `ads_measurement_event` contract — 20 DRAFT_LOCKED fields, `currency=VND`, Zone-A write-once | RULE-003/005/008 | **CTR-001 (M6-owned)** | `app/measurement/models/measurement_event.py`, `normalize.py` |
| Append-only measurement store + **UNIQUE idempotency_key** dedup | RULE-005/007 | CTR-001 | `app/measurement/store/measurement_event_store.py` |
| Idempotency — LOCKED RULE-005 key, **server-derived** `raw_event_hash` (client value never trusted) | RULE-005, H03 | CTR-016 | `app/api/track.py`, `logs/idempotency.py` |
| **Fix-first hardening** of the M6.2A seam (F1/F2/MINOR-9/O1) | RULE-001/002/014 | — | patched `ingest.py`, `consent/gate.py`, `audit.py`, `masking.py` |

Everything is **staged** — no live system, no applied migration, no external call, no flag flipped, no web
framework introduced (M6-OD-011 `framework=""` → the endpoint is a pure `handle_track_request(body)` handler; HTTP
routing binds at the owner-controlled integration step). The staged tree is a **cumulative snapshot**: the whole
M6.2A tree is carried forward byte-identical except the 4 fix-first patches + the new modules.

**Scope boundary (carried, not bled):** `POST /api/ads/conversions` (CTR-017) + `conversion_events` (CTR-007) +
outbox (CTR-008) are **M6.2C**; external send / Pixel / CAPI / audience sync **M6.2C/D**; attribution (Zone B) **M6.2E**;
data-quality transitions (Zone C) **M6.2F/G**. M6.2B sets **Zone A only** + the initial `data_quality_status=HOLD`;
it never sets revenue/attribution and never sends.

---

## 2. Operate (staged)

No production service (BLOCKED/OFF). The staged build is exercised as an in-memory library + end-to-end test suite.

```bash
cd 04-artifacts/impl/M6.2B
python -m app        # prints the staged posture (BLOCKED / OFF / OFF), exit 0 — no server, no egress
```

- **Track entry point (for the eventual HTTP binding):** `app/api/track.py::handle_track_request(body, deps)` is a
  **framework-neutral, pure** handler over an untrusted mapping. It: shape/type-checks the body → requires
  `consent_snapshot_id` (RULE-002) and `idempotency_key` → **recomputes** the RULE-005 key server-side and derives
  `raw_event_hash` server-side (never trusts a client hash, RULE-H03) → drives the hardened M6.2A seam (event_registry
  gate = unknown-event layer 2, RULE-001) → normalizes + inserts the `ads_measurement_event` → returns the CTR-016
  response `{status: ACCEPTED|DUPLICATE|REJECTED, log_id, event_id, idempotent_replay, data_quality_status(=HOLD
  initial), correlation_id}` with a **PII-safe** error model.
- **Two-layer unknown-event fail:** the client **hook** rejects a code absent from the locked base vocab; the
  **endpoint/seam** independently re-rejects a code not ACTIVE in `event_registry`. Client validation is never trusted alone.
- **Dedup end-to-end:** identical replayed body → identical server-derived key → **no second row** in either
  `web_event_logs` (M6.2A) or `ads_measurement_events` (M6.2B) → response `DUPLICATE` / `idempotent_replay=true`.
- **No egress:** `external_send=OFF`, no dispatcher, no egress client in the path (RULE-004). Revenue/attribution unset.

---

## 3. Verify

```bash
cd 04-artifacts/impl/M6.2B
python -m pytest -q          # expect: 139 passed / 0 failed (final tester run, M6-P1104)
```

| Check | Expected | Evidence |
|---|---|---|
| Full staged suite (96 M6.2A carried + M6.2B additions) | **139 passed / 0 failed**, exit 0 | `04-artifacts/test-reports/M6.2B/SMOKE_RESULTS.md`; `M6-P1104.json` |
| **M6-SMK-001** — event not in registry → `Reject/HOLD, audit rõ` (both hook + endpoint layers) | **PASS 6/6** | `SMOKE_RESULTS.md` |
| **M6-SMK-003** — duplicate Pixel/CAPI/Offline → `Dedup, không double count` (end-to-end, both stores) | **PASS 4/4** | `SMOKE_RESULTS.md` |
| L1/L2 supporting legs (`test_track_unknown_event`, `test_track_idempotency_dedup`, `test_measurement_event_store`) | 14/14 | `SMOKE_RESULTS.md` |
| Fix-first regressions F1/F2/MINOR-9/O1 | pass | `tests/test_m6_2b_fixfirst_regressions.py` |
| CTR-001 store — Zone-A insert + UNIQUE dedup; forbidden ops (Zone-A UPDATE/DELETE, revenue without ORDER_VERIFIED) rejected; `currency=VND`; initial `data_quality_status=HOLD` | pass | `tests/test_measurement_event_store.py` |
| Carried-forward M6.2A suite (no regression from the fix-first patches) | 96/96 green | `IMPLEMENTATION_NOTES.md` §6 |
| Entry point `python -m app` | staged posture, exit 0 | `IMPLEMENTATION_NOTES.md` §6 |

> **Verify does NOT assert leg closure.** The suites pass within the 139-test run and the boundary adversary
> executed both the two-layer unknown-event independence and exact-replay dedup, but legs **L1 / L2** are
> **SUPPORTED (staged), not closed** — the tester withheld closure over the MINOR-6 / F-A / F-B residuals (§7).
> Whether L1/L2 close is the **M6-P1109 Judge's** call.

---

## 4. Rollback — every change

**Baseline rollback is non-destructive: nothing is live.** All artifacts are staged under `04-artifacts/impl/M6.2B/`;
no migration applied, no external call, no flag written. M6.2B is a **cumulative snapshot**, so the rollback rule is:
**patched** files revert to their **M6.2A** staged version; **new** files revert by deletion; deleting the whole
M6.2B tree returns to M6.2A (untouched, the prior good state). Per-item detail: `PLAN.md` §5/§8, `IMPLEMENTATION_NOTES.md` §7.

| Change group | Files | Rollback |
|---|---|---|
| **Fix-first patches** (F1 seam never-raise, F2 gate no-fail-open, MINOR-9 audit event_code, O1 mask-on-export) | `ingest.py`, `consent/gate.py`, `audit.py`, `masking.py` (+ endpoint callers) | **Revert each to its M6.2A staged version** (patched-in-place) |
| Tracking hooks (layer 1) | `tracking/base_events.py` (9 locked events), `tracking/hooks.py` | Delete (new) |
| Event-contract model | `models/measurement_event.py` (CTR-001, 20 fields) | Delete (new); no schema shipped to any live table |
| Normalized store + dedup | `store/measurement_event_store.py`, `normalize.py` | Delete (new); no rows persisted |
| Track endpoint + consent adapter (layer 2) | `app/api/track.py`, `adapters/consent_reader.py` | Delete (new); no egress path exists |
| **Staged migration (the new owned table)** | `migrations/0002_create_ads_measurement_events.sql` (up + down) | **Never applied.** Delete staged file to revert now. **After a real (owner-controlled) apply, revert = down-DDL `DROP TABLE ads_measurement_events`** — append-only / Zone-A write-once means no row UPDATE/DELETE, so the table is dropped |
| Migration note | `migrations/README.md` (patched) | Revert to M6.2A version |
| Baseline package inits | new `__init__.py` under `app/api`, `tracking`, `store`, `adapters` | Delete; no flag/behavior change (`config.py`, `__main__.py`, `pyproject.toml` carried forward verbatim) |
| Tests | `tests/test_track_*`, `test_measurement_event_store.py`, `test_m6_2b_fixfirst_regressions.py` (+ conftest additions) | Delete; test doubles only, no raw PII in fixtures |

**Consumed tables (`event_registry`, `guest_contacts`, `guest_marketing_consent_snapshot`, `customers/…`) are never
mutated by M6** → nothing to roll back on the Core / Customer / Consent side. (Exit-gate leg **7** = this rollback documentation.)

---

## 5. Decision deltas produced / observed by this slice

*(For the operator to reconcile into `DECISION_REGISTER` / `04-artifacts/evidence/decisions/` out-of-band; the analyst does not write `00-spec/`.)*

| Decision | Movement in this slice | Effect |
|---|---|---|
| **M6-DEFER-F1F2-M6.2B** | Recorded 2026-07-30 (owner) — the **entry gate bound** F1/F2 as fix-first coder preconditions + MINOR-9/O1 to close in-slice | **All four closed + executed-verified** this slice; this is the mechanism that made the M6.2B entry a real PASS while the M6.2A residuals were retired |
| **M6-OD-011** (target repo / stack) | Carried DECIDED (GREENFIELD python 3.12, `framework=""`) | Endpoint stays framework-neutral; HTTP routing / DB engine bind at owner integration |
| **M6-OD-003** (hash policy / egress fields) | OPEN — **irrelevant to M6.2B** (store-only, no egress); hard forward gate at **M6.2D** external send | Egress framework-only; hashing is the future dispatcher's (M6.2C/D) |
| **M6-OD-012** (masking format) | OPEN (forward) | Pack default `abc***xy` used for MINOR-9 / O1 masking as a parameter |
| **M6-OD-009** (GOLDEN_HOUR_* events) | OPEN | **Excluded from `base_events.py`** (fail-closed); only the 9 locked base events are emitted |
| **ENTRY-001 / ENTRY-003** (inherited) | Unchanged — remain **RISK-ACCEPTED** under `M6-OVERRIDE-M6P1000-STAGED` (M6-P1000 verdict stays **BLOCKED**, NOT converted) | Bound to the M6.2A entry + the **mandatory M6.2G re-gate**; **not** checked at M6.2B |

---

## 6. Changelog delta produced by this slice

**One deferred operator housekeeping item; no in-band schema change.** The slice adds **no schema change beyond the
harmonized contracts** (SCHEMA_CHANGELOG rows 9–33, judged PASS at M6-P0715 SIGNED). It **realizes** the DRAFT_LOCKED
`ads_measurement_event` (CTR-001, 20 fields) as staged code + a staged (un-applied) `0002` DDL.

- **CTR-016 canon-flip (operator, out-of-band):** `M6-CTR-016` (`POST /api/ads/events/track`) is still
  `MISSING / OWNER_DECISION_REQUIRED` in canon, but **satisfied-for-entry** (schema staged at
  `04-artifacts/analysis/contracts/CONTRACT_TRACK_APIS.contract.yaml`; producer M6-P0711 PASS; gate M6-P0715 SIGNED).
  The canon-flip — apply the schema to `00-spec/contracts/` + set `CONTRACT_REGISTER` to `DRAFT_LOCKED` + add a
  `SCHEMA_CHANGELOG` row — is **deferred, non-blocking operator housekeeping** (flagged by the entry-gate Judge
  M6-P1100). **CTR-016 only** — CTR-017 belongs to M6.2C.
- The new tokens introduced by the fix-first patches / endpoint (`TS_NORMALIZE_FAILED`, `VALIDATION_FAILED`,
  `IDENTITY_RESOLVE_FAILED`, `STORE_APPEND_FAILED`, `CONSENT_SCOPE_UNTRUSTED_TYPE`, and the CTR-016 error codes) are
  **implementation-internal vocabulary**, not owner-facing schema → **no** SCHEMA_CHANGELOG row.

---

## 7. Handoff to M6.2C (and the forward gates)

**M6.2C adds the Outbox layer: `POST /api/ads/conversions` (CTR-017) + `conversion_events` (CTR-007) + the
measurement outbox (CTR-008).** External send begins at M6.2C/D. The residuals below must be closed **before the
real HTTP binding / durable store binding** (they are latent while the endpoint is a pure handler + the stores are
in-memory; all armed-not-fired, none trips M6-FAIL-003).

### 7.1 MUST-FIX before the HTTP / durable binding — boundary residuals (M6-P1105, routed to CODER)
- **F-A [MINOR] — DoS / lost-audit:** the endpoint's pre-seam `_contains_raw_pii` + `_raw_event_hash` run **before**
  the hardened seam and are unwrapped — a deeply-nested JSON body (~4000 deep) → `RecursionError` **escapes the
  handler unaudited** (a 500 / DoS + lost-audit gap). Wrap in the audited-deny pattern and **bound payload nesting depth**.
- **F-B [MINOR] — dedup quality:** the server-side `raw_event_hash` is over-broad → cosmetic `event_ts` / field
  variants **over-count**. Hash a **canonical projection** (`normalize_ts`, restricted to the CTR-016 contract fields).
- **MINOR-6:** `validator.validate` does not assert `row.event_code == requested` (needs a hostile / normalizing
  adapter; the shipped strict registry closes it today).
- **MINOR-9-residual:** the audit `event_code` **denylist** (`\d{6,}` + finite id-prefix list) still leaves a
  `<6-digit` / unlisted-prefix identifier-shaped code verbatim in the in-memory audit sink (latent). Replace the
  denylist with an **allowlist** of the real registry base-event grammar.
- Full detail: `04-artifacts/boundary-reports/M6.2B_boundary.md`.

### 7.2 Forward — security/PII residual (M6-P1106, routed to CODER)
- **O-1 [MEDIUM, latent]:** the endpoint PII tripwire scans the **payload only**; a raw email / VN-phone in the
  top-level `session_id` / `page_id` / `source` / `guest_id` bypasses it and is stored **raw** in the durable
  `web_event_logs` + `ads_measurement_events` rows (masked on export/audit). Latent while in-memory/staged; becomes a
  **FAIL-008-class** issue at durable binding. **Extend the guard / add pseudonymous-id charset validation before
  durable binding.**
- At the M6-OD-011 HTTP-binding step, also add request **authN/authZ**, **rate limiting**, and payload **size/depth bounds**.
- Full detail: `04-artifacts/security-reports/M6.2B_security.md`.

### 7.3 Scope carried to M6.2C/D
- **Cross-source dedup-by-content** (Pixel/CAPI/Offline same conversion under different `idempotency_key`) is
  **M6.2D** — M6.2B proves **exact-replay** dedup only (F-B is the seam of this deferral).
- SMK-002 (consent → no external send, send-time) is **M6.2C**-bound; M6.2B keeps consent **fail-closed at ingest**
  but does not own the send-time smoke.

### 7.4 Hard forward gates (immovable — inherited, unchanged)
- **M6-OD-003** MUST be decided before **M6.2D** external send.
- **M6.2G Scale-Gate re-gate (MANDATORY):** ENTRY-001/002/003 re-checked before **any** scale or external send;
  upstream fixes (`CORE_EVENT_REGISTRY_PATCH`, `M3_SELLABLE_GATE_FAILOPEN_PATCH`) must land first. The M6.2A
  risk-acceptances (M6-P1000 verdict **BLOCKED**) were **not** converted by M6.2B's PASS entry.
- **Posture stays `BLOCKED` / `OFF` / `OFF`** — external send / audience sync / dashboard are out of scope for M6.2B.

---

## 8. Pointers for the slice-gate Judge (M6-P1109)

This runbook and `M6_2B_EVIDENCE_INDEX.md` are **descriptive**. The slice verdict is the Judge's, rendered strictly
from the evidence files. When rendering it, weigh:
1. **Healthy posture (real, credit it):** entry is a genuine Judge PASS (M6-P1100 `SIGNED`); the four M6.2A residuals
   **F1/F2/MINOR-9/O1 closed fix-first** and executed-verified by both M6-P1105 and M6-P1106.
2. **Legs L1/L2 — "supported (staged), not closed":** closure withheld by the tester over **MINOR-6 / F-A / F-B**.
   Read `M6.2B_boundary.md` and `SMOKE_RESULTS.md` directly, not this summary.
3. **Forward items:** F-A / F-B / MINOR-6 / MINOR-9-residual (before HTTP binding), **O-1** (before durable binding),
   plus authN/authZ + rate-limit + size/depth bounds; **CTR-016 canon-flip** housekeeping.
4. **Inherited & immovable:** ENTRY-001/003 risk-accepted (M6-P1000 BLOCKED, not converted); the **mandatory M6.2G
   re-gate** stands regardless of this slice's verdict — nothing here authorizes real scale or send.

*Analysis-only: no code, no migration, no flag, no external call, no self-certification. `04-artifacts/state/` untouched.*
