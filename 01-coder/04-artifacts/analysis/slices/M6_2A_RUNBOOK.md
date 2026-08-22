# M6.2A Runbook — ADS Phase 1 Data Foundation

| Field | Value |
|---|---|
| Slice | **M6.2A** — clean measurement foundation (valid events · correct identity · fail-closed consent), doc §7 |
| Produced by | **M6-P1008** `M6_2A_DOCS` (ANALYST_ARCHITECT, `analysis_only`) |
| Sources | `00-spec/slices/M6.2A.md`, `04-artifacts/evidence/prompts/M6-P1007.json`, `M6_2A_EVIDENCE_INDEX.md`, `PLAN.md`, `IMPLEMENTATION_NOTES.md` (R1–R4) |
| Posture (immutable) | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` |

> **Read first — this is a runbook, not a verdict.** This document self-certifies nothing and advances no gate
> (RULE-015). It documents how to operate / verify / roll back the **staged** M6.2A build and hands off the open
> items. The authoritative slice verdict is the slice-gate Judge's to render at **M6-P1009**, strictly from the
> evidence files. Entry to this slice was opened by a documented **owner override**
> (`M6-OVERRIDE-M6P1000-STAGED`, 2026-07-29) — **not** a Judge PASS; the entry-gate Judge verdict (M6-P1000) is
> **BLOCKED** and unmodified. Exit-gate legs **L1/L2/L3 are "supported at the staged level", not closed** — the
> tester (M6-P1004) deliberately withheld leg-closure; final closure is the M6-P1009 Judge's call. A **mandatory
> M6.2G Scale-Gate re-gate** stands before any real scale or external send.

---

## 1. What this slice built

A **fail-closed, measure-only substrate** — three independent decision paths over one append-only record. Module 6
**owns and writes exactly one table**, `web_event_logs` (M6-CTR-004); the other three shapes are **CONSUMED**
(read-only) so a boundary leak (M6 writing a Core/Customer/Consent table, or sending egress) is structurally
impossible here — there is no dispatcher and `external_send=OFF`.

| Capability | Rule | Contract | Where (staged under `04-artifacts/impl/M6.2A/`) |
|---|---|---|---|
| Event-registry validation (unknown → REJECT/HOLD + audit) | RULE-001/018 | CTR-003 (consumed) | `app/measurement/registry/validator.py` |
| Consent fail-closed (not VALID ⇒ no external measurement / audience / CRM) | RULE-002 | CTR-006 (consumed) | `app/measurement/consent/gate.py` |
| Guest→customer mapping with audit, never overwrite w/o evidence | RULE-006 | CTR-005 (consumed) | `app/measurement/identity/resolver.py` |
| `web_event_logs` append-only + locked idempotency (RULE-005) | RULE-007 | **CTR-004 (M6-owned)** | `app/measurement/logs/web_event_log_store.py`, `logs/idempotency.py` |
| Ingest seam (validate → append → mark egress-eligibility, never sends) | RULE-001/002/004/007 | CTR-004 | `app/measurement/ingest.py` |

Everything is **staged** — no live system, no applied migration, no external call, no flag flipped. `M6-OD-011`
was DECIDED as GREENFIELD (python 3.12, in-memory adapters; the one owned table's DDL is staged, never applied).

**Scope boundary (carried, not bled):** the HTTP `POST /api/ads/events/track` endpoint (CTR-016) + `ads_measurement_event`
(CTR-001) are **M6.2B**; external send / Pixel / CAPI / audience sync are **M6.2C/D**; attribution resolver is **M6.2E**;
no workers, no scale, Hero-SKU-only (M6-OD-001).

---

## 2. Operate (staged)

There is no service to run in production (BLOCKED/OFF). The staged build is exercised as an in-memory library + test suite.

```bash
cd 04-artifacts/impl/M6.2A
python -m app        # prints the staged posture (BLOCKED / OFF / measure-only), exit 0 — no server, no egress
```

- **Entry point for later slices:** `app/measurement/ingest.py::ingest_event(...)` is the seam M6.2B will wire into
  `POST /api/ads/events/track`. It orchestrates: **type-boundary at head → validate (registry) → resolve identity →
  bind consent to the correct subject → append `web_event_log` → mark egress-eligibility (never sends)**.
- **What it does with an event:** a **valid** event is written to `web_event_logs` (durable) with egress **blocked**;
  an **unknown / de-registered / wrong-type / mismatched-consent-subject** event is **audited** (durable reject/HOLD
  record) and **not** written — nothing is silently lost.
- **Egress is bolted shut:** `permits_external_send()` hard-returns `False` for every token while **M6-OD-003 is OPEN**;
  there is no dispatcher. Egress is framework-only regardless of consent.

---

## 3. Verify

Run the staged suite from the slice dir (target: python 3.12 · `pytest -q`):

```bash
cd 04-artifacts/impl/M6.2A
python -m pytest -q          # expect: 96 passed / 0 failed (frozen Round-4 code)
```

| Check | Expected | Evidence |
|---|---|---|
| Full staged suite | **96 passed / 0 failed**, exit 0 | `04-artifacts/test-reports/M6.2A/SMOKE_RESULTS.md`; `M6-P1004.json` |
| **M6-SMK-001** — event not in registry → `Reject/HOLD, audit rõ` | **PASS 4/4** | `SMOKE_RESULTS.md` |
| **M6-SMK-002** — valid event, missing consent → `Không external measurement, không audience sync` | **PASS 7/7** | `SMOKE_RESULTS.md` |
| Consent matrix (VALID/MISSING/EXPIRED/OPT_OUT/scope) | 6/6 | `tests/test_consent_fail_closed.py` |
| Append-only + store-level dedup (INSERT only; UPDATE/DELETE rejected; dup idempotency_key → single row) | pass | `tests/test_web_event_logs_append_only.py` |
| Identity mapping audit (missing/ambiguous → LOW/HOLD; no overwrite w/o evidence; subjects masked) | 7/7 | `tests/test_identity_mapping_audit.py` |
| Seam invariants — never-raises + every-deny-audited (350 combos); type-boundary (957 combos) | pass | `tests/test_round3_regressions.py`, `tests/test_round4_regressions.py` |
| Enabling-flag sweep (production/gateway/external-send set to any enabling value) | **none found** | `IMPLEMENTATION_NOTES.md` R4.4 |

> **Verify does NOT assert leg closure.** The suites pass within the frozen 96-test run, but legs **L1 (event
> registry) / L2 (consent) / L3 (identity)** are **SUPPORTED (staged), not closed** — the tester withheld closure
> because the boundary residuals **F1/F2** (§7) remain open. Whether L1/L2/L3 close is the **M6-P1009 Judge's** call.

---

## 4. Rollback — every change

**Baseline rollback is non-destructive: nothing is live.** All artifacts are staged under `04-artifacts/impl/M6.2A/`;
no migration is applied (`live_migrations=false`), no external call is made, no flag is written. Deleting the staged
tree reverts everything with zero runtime/data impact. Per-item detail is in `PLAN.md` §5–§10 and `IMPLEMENTATION_NOTES.md` §6.

| Change group | Files (staged) | Rollback |
|---|---|---|
| Baseline / config / entrypoint | `pyproject.toml`, `README.md`, `app/config.py`, `app/__init__.py`(+subpkgs), `app/__main__.py` | Delete files; no dependency installed, no live setting touched |
| Consumed read-models | `app/measurement/models/consumed.py` | Delete; **no schema shipped to any owner table** (M6 consume-only, RULE-018) |
| M6-owned row type | `app/measurement/models/web_event_log.py` | Delete; append-only row type removed; no table exists yet |
| Cross-cutting helpers | `masking.py`, `audit.py`, `ports.py` | Delete; audit/mask are **in-memory only**, no persisted data; ports have no write methods |
| Decision path — registry validator | `registry/validator.py` (+ `tests/test_event_registry_validation.py`) | Delete module + test; consumed registry untouched (read-only) |
| Decision path — consent gate | `consent/gate.py` (+ `tests/test_consent_fail_closed.py`) | Delete module + test; no egress path exists in this slice regardless |
| Decision path — identity resolver | `identity/resolver.py` (+ `tests/test_identity_mapping_audit.py`) | Delete module + test; no mapping written (M6 read-only on `guest_contacts`) |
| Append-only log substrate | `logs/web_event_log_store.py`, `logs/idempotency.py` (+ `tests/test_web_event_logs_append_only.py`) | Delete modules + test; no rows persisted; **integration revert = down-DDL** (below) |
| Ingest seam | `ingest.py` (+ `tests/test_ingest_measure_only.py`) | Delete module + test; no external effect (no dispatcher, `external_send=OFF`) |
| Round 2/3/4 hardening | same files above + `tests/test_round{2,3,4}_regressions.py` | No separate rollback — hardening lives in the same modules; deleting the staged tree reverts it; regression files deletable |
| **Staged migration (the one owned table)** | `migrations/0001_create_web_event_logs.sql` (up + down), `migrations/README.md` | **Never applied.** Delete staged file to revert now. **After a real (owner-controlled) apply, revert = down-DDL `DROP TABLE web_event_logs`** — append-only means no row UPDATE/DELETE, so the table is dropped, not row-deleted |
| Tests / fixtures | `tests/conftest.py`, `tests/smoke/*`, `tests/test_*.py` | Delete; test doubles only, no raw PII in any fixture |

**Consumed tables (`event_registry`, `guest_contacts`, `guest_marketing_consent_snapshot`, `customers/…`) are never
mutated by M6** → there is nothing to roll back on the Core / Customer / Consent side. (Exit-gate leg **L8** = this
rollback documentation.)

---

## 5. Decision deltas produced / observed by this slice

*(For the operator to reconcile into `DECISION_REGISTER` out-of-band; the analyst does not write `00-spec/`.)*

| Decision | Movement in this slice | Effect |
|---|---|---|
| **M6-OD-011** (target repo / stack) | **DECIDED** 2026-07-23 — GREENFIELD, staged-only, python 3.12 | Unlocked staged implementation; the owned table's DDL is engine-neutral + staged |
| **M6-OD-003** (hash policy / permitted external-send fields) | **Re-scoped** by M6-P1006 to **NOT-in-scope-for-M6.2A** (belongs at M6.2D) | Hard **forward gate before M6.2C/D external send**; the fail-closed egress lock (`permits_external_send()` → `False`) is present and executed-verified while OD-003 is OPEN |
| **M6-OD-012** (masking format on export) | **OPEN** (forward) | Pack default `abc***xy` used as a parameter in `masking.py`; masking-on-export must land before any durable binding |
| **Owner override** `M6-OVERRIDE-M6P1000-STAGED` | Recorded 2026-07-29 (owner) | "Proceed into M6.2A **staged only**, keep the lock tight, fix upstream later." **Not a Judge PASS.** RULE-020 (entry-evidence gate) satisfied only by owner risk-acceptance |
| **ENTRY-001 / ENTRY-003** | **Risk-accepted, NOT closed** | Encoded as fail-closed design constraints; re-checked at the **mandatory M6.2G re-gate** |

---

## 6. Changelog delta produced by this slice

**No `SCHEMA_CHANGELOG` row is required for M6.2A.** The slice adds **no schema change beyond the harmonized
contracts** (SCHEMA_CHANGELOG rows 9–33, judged PASS at M6-P0715 SIGNED). It **realizes** the already-locked
`web_event_logs` (CTR-004) as **staged code + a staged (un-applied) DDL**, and **consumes** CTR-003/005/006. The new
tokens introduced during hardening — `TS_NOT_TZ_AWARE`, `CONSENT_MISSING/EXPIRED/OPT_OUT`, `CONSENT_SUBJECT_MISMATCH`,
`CONSENT_SNAPSHOT_UNTRUSTED_TYPE`, `FIELD_TYPE_INVALID`, `INVALID_EVENT_CODE[…]` — are **implementation-internal audit
vocabulary**, not owner-facing schema, so they carry **no** SCHEMA_CHANGELOG row. This "empty schema diff" is itself
recorded here per the changelog discipline. (If the owner later ratifies any of these as a contract enum, that becomes
a harmonization/DECISION delta at that time — not here.)

---

## 7. Handoff to M6.2B (and the forward gates)

**M6.2B wires the exact `ingest_event` seam into `POST /api/ads/events/track` (CTR-016) + `ads_measurement_event`
(CTR-001).** The seam's fail-closed contract (audited-deny, no-raise, no-junk-accept, egress-off) must be preserved
end-to-end at the HTTP boundary — where today's *armed-not-fired* residuals become **live** consent-bypass / double-count
/ data-loss bugs.

### 7.1 MUST-FIX before / at M6.2B — boundary residuals (M6-P1005, routed to CODER)
- **F1 [MAJOR] — audit-integrity:** the seam does not turn *every* callee exception into an audited deny; throwing
  registry / identity / store adapters (and a too-narrow `normalize_ts` catch) can escape with **0 audit** → a lost row
  **and** lost audit (breaks SMK-001 "audit rõ" for that input class). Consequence is loss, **not** a grant/send.
- **F2 [MAJOR] — consent type boundary:** a `ConsentSnapshot` **subclass** that skips `__post_init__` can bypass the
  seam `isinstance` guard, reopening the gate substring fail-open. Egress stays bolted (armed-not-fired), but on the
  M6.2B path this is a live consent bypass.
- **O2 [data-quality, owner-visible]:** a registry-VALID event with a **naive / non-tz-aware `event_ts`** is fail-closed
  and the **whole measurement row is dropped** (audited `TS_NOT_TZ_AWARE`) — an under-count. Owner-visible DQ decision
  (distinct from F1: here the drop *is* audited).
- Plus **MINOR-6..9**. Full detail: `04-artifacts/boundary-reports/M6.2A_boundary.md`.

### 7.2 Forward — security/PII residuals (M6-P1006, routed to CODER)
- **SEC-PII-01:** an identifier-shaped `event_code` is stored **verbatim** in the in-memory audit sink — latent only
  (nothing serialized/exported; staged). Tighten before M6.2B / any durable binding.
- **SEC-PII-02:** audit `detail` is deliberately **not** identity-masked (contract-guarded: enum / machine-reason /
  pre-masked text only).
- **O1 / M6-OD-012:** `session_id` + `correlation_id` are stored **raw** in the in-memory `web_event_logs`;
  masking-on-export must land before any export / durable binding.
- Full detail: `04-artifacts/security-reports/M6.2A_security.md`.

### 7.3 Hard forward gates (immovable)
- **M6-OD-003** (hash policy + permitted external-send fields) **MUST be decided before M6.2C/D external send.** Until
  then the egress lock stands.
- **M6.2G Scale-Gate re-gate (MANDATORY):** M6-ENTRY-001/002/003 are re-checked before **any** scale or external send;
  upstream fixes must land first — `CORE_EVENT_REGISTRY_PATCH` (per-event `attribution_channel` / `data_sensitivity` /
  `external_send_policy` + Core ownership; today the live registry is **Platform/P0-06-owned, not Core-owned**) and
  `M3_SELLABLE_GATE_FAILOPEN_PATCH` (FAIL_OPEN_RECALL at `SellableGateAdminServiceImpl:805`; QuoteSnapshot producer
  missing; PREPAID_TO_VERIFIED not E2E-proven).
- **Posture stays `BLOCKED` / `OFF` / `OFF`** — M6.2B remains staged; it does not flip any flag.

---

## 8. Pointers for the slice-gate Judge (M6-P1009)

This runbook and `M6_2A_EVIDENCE_INDEX.md` are **descriptive**. The slice verdict is the Judge's, rendered strictly
from the evidence files. When rendering it, weigh:
1. **Entry** — opened by **owner override**; M6-P1000 Judge verdict is **BLOCKED**; ENTRY-001/003 **risk-accepted, not
   closed** (`M6-P1000.json`, `M6-P1000_JUDGE_FINAL_SIGN_OFF.json`).
2. **Legs L1/L2/L3** — "supported (staged)", closure withheld by the tester because of **F1/F2** audit-integrity /
   fail-closed residuals. Read `M6.2A_boundary.md` and `SMOKE_RESULTS.md` directly, not this summary.
3. **Forward items** — SEC-PII-01 / O1 (before durable binding), O2 (owner-visible DQ), M6-OD-003 (before M6.2C/D).
4. **The M6.2G re-gate is mandatory regardless of this slice's verdict** — nothing here authorizes real scale or send.

*Analysis-only: no code, no migration, no flag, no external call, no self-certification. `04-artifacts/state/` untouched.*
