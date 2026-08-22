# M6.2A IMPLEMENTATION PLAN — ADS Phase 1 Data Foundation (STAGED, plan-only)

**Prompt**: M6-P1001 (`M6_2A_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code this prompt)
**Slice**: M6.2A — clean measurement foundation: valid events · correct identity · fail-closed consent
**Posture (immutable to this role)**: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`.
This plan writes no code, applies no migration, calls nothing external, scales/publishes nothing, and flips no flag.

> **Governance banner — the entry gate is OWNER-OVERRIDDEN, not judge-PASSED.**
> M6-P1000 (M6.2A entry-gate judge) verdict is **BLOCKED** (unchanged). The ledger status is **SKIPPED** via
> `04-artifacts/evidence/decisions/M6-OVERRIDE-M6P1000-STAGED.json` (owner: Nguyen Duc Manh, 2026-07-29):
> *"proceed into M6.2A **staged only**, keep the lock tight, fix upstream later."* This is explicitly **NOT** a PASS.
> **RULE-020** (entry-evidence gate: no implementation start without PROVEN P3 Verified-Revenue + P5 channel/event
> identity evidence) is therefore satisfied only by an **owner risk-acceptance**, not by proven evidence. The
> accepted gaps (ENTRY-001, ENTRY-003) are carried into this plan as **fail-closed design constraints** (§9) and a
> **MANDATORY re-gate at M6.2G Scale Gate** stands before any scale or external send.

---

## 1. Entry-gate verification (what was confirmed before planning)

| Precondition | Source checked | Result |
|---|---|---|
| This prompt is the active one (RUNNING) | `04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv` row 79 | **M6-P1001 = RUNNING** ✓ |
| Dependency resolved | ledger row 78 | **M6-P1000 = SKIPPED** (owner override; note `SKIP_APPROVED:OWNER_OVERRIDE:...;prod-locked;regate-M6.2G;judge-BLOCKED`) ✓ |
| Implementation target LOCKED | `04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json` | `status=LOCKED`, `workspace_mode=STAGED_ONLY`, stack `python 3.12` / `pytest -q` / `python -m app` ✓ |
| M6-OD-011 decided | same manifest + M6-P1000 evidence | `M6-OD-011 = DECIDED` (2026-07-23), GREENFIELD ✓ |
| Slice contracts satisfied | M6-P1000 evidence + `00-spec/contracts/` | CTR-003/004/005/006 = **DRAFT_LOCKED**, covering schemas applied, judged PASS at M6-P0715 (SIGNED) ✓ |
| Upstream harmonization gate | ledger row 77 | **M6-P0715 = SIGNED** ✓ |
| Prod/scale flags | brief + manifest `safety` | BLOCKED/OFF, `production_access=false`, `external_platform_calls=false`, `live_migrations=false` ✓ |

**Conclusion**: entry is open for **STAGED** M6.2A work under the owner override. No flag flips; the block is isolated to
the ENTRY-001/ENTRY-003 risk-acceptance carried in §9.

---

## 2. Working mode & conventions

**Target repository state (verified on disk, `D:\M6\Module6-workspace\work-root\target-repo`): EMPTY greenfield.**
There are no existing files, conventions, or test patterns to literally reuse (acceptance check 5, "reuse conventions
from the locked target repository", is honestly reported: nothing to reuse yet). This slice therefore **establishes**
the baseline Python conventions the whole M6.2x chain will reuse, consistent with the LOCKED stack:

- Language **Python 3.12**; single import package **`app/`**; run entrypoint **`python -m app`**.
- Tests **`pytest -q`**, co-located under **`tests/`**, one test module per decision path; fixtures in `tests/conftest.py`.
- Pure-standard-library where possible (dataclasses, `enum`, `hashlib`, `datetime`); **no new third-party dependency
  proposed in M6.2A** (any dependency is a separate decision — none needed for a fail-closed in-memory foundation).
- Persistence is abstracted behind **ports** (interfaces); the physical storage stack binding is `M6-OD-011`-decided
  but the append-only table's DDL is staged (§6), not applied.

**Staging path mapping (LOCKED target is a read-only convention reference; nothing lands in the repo):**
every target-relative path `X` below is physically **staged** at `04-artifacts/impl/M6.2A/X`. Target `code_root = "."`.

---

## 3. Scope lock (anchored strictly to `00-spec/slices/M6.2A.md`)

**In scope (5 capabilities):**
1. Consume `customers/customer_profiles/customer_addresses/customer_devices/guest_contacts` (read-only).
2. `guest → customer` mapping **with audit** (RULE-006).
3. `event_registry` **validation path** (RULE-001).
4. `web_event_logs` **append-only store** (RULE-007) + locked idempotency key (RULE-005).
5. `guest_marketing_consent_snapshot` **fail-closed enforcement** (RULE-002).

**Out of scope (explicit — no scope bleed):**
- HTTP `POST /api/ads/events/track` (CTR-016) + `ads_measurement_event` (CTR-001) + request idempotency handling →
  **M6.2B** (verified against `00-spec/slices/M6.2B.md`).
- External measurement send / Pixel / CAPI / Offline / audience sync → M6.2C / M6.2D.
- Attribution resolver → M6.2E. Dashboards → M6.2F. Scale/learning → M6.2G+.
- **No workers** (dispatchers CTR-021/022, materializer CTR-023, DQ checker CTR-024 all belong to M6.2C–G).
- 13/20 SKU parallel campaigns (Hero SKU only, M6-OD-001).
- End-to-end duplicate-event smoke **SMK-003** (M6.2B/M6.2D); M6.2A proves only the *store-level* dedup invariant.
- Verified-revenue / QuoteSnapshot boundary (ENTRY-001) — risk-accepted, re-gated at M6.2G (§9).

---

## 4. Design overview — a fail-closed measurement substrate

Three independent **decision paths**, each defaulting to the safe answer, over one **append-only** durable record.
M6 **owns and writes only `web_event_logs`**; the other three tables are **CONSUMED** (read-only ports), so a boundary
leak (M6 writing a Core/Customer/Consent table, or sending egress) is structurally impossible in this slice — there is
no dispatcher and `external_send=OFF`.

```
                 ┌───────────────── ports (read-only) ─────────────────┐
 event_registry ─┤ EventRegistryReader   guest_contacts ─┤ GuestContactReader
 (CTR-003 CONSUMED)                       (CTR-005 CONSUMED)
 consent_snapshot┤ ConsentReader         customers/... ──┤ CustomerRefReader (minimal)
 (CTR-006 CONSUMED)                       (no M6-CTR; minimal consumed fields)
                 └──────────────────────────────────────────────────────┘
        │validate(RULE-001)        │resolve(RULE-006)        │gate(RULE-002)
        ▼                          ▼                          ▼
  EventValidator ──► IngestService ──► WebEventLogStore (RULE-007 append-only, RULE-005 dedup)  [M6-OWNED]
        │  reject/HOLD+audit        │ writes one immutable row          │
        └──────────► AuditLog ◄─────┴── ConsentGate marks egress-eligibility only (NEVER sends)
```

**Entry-gap-driven fail-closed defaults** (direct consequence of the §9 override — this is where the override *changes*
the design, not just restates boundaries):
- `event_registry.external_send_policy` is an ENTRY-003 GAP (may be MISSING per risk-acceptance) → the validator treats
  **MISSING/unknown `external_send_policy` as BLOCKED** (egress framework-only; consistent with M6-OD-003 OPEN).
- `event_registry.data_sensitivity` is an ENTRY-003 GAP → treat **MISSING as most-restrictive (PII)** → mask.
- `event_registry.registration_state` **not `ACTIVE` (or ambiguous/stale) → REJECT/HOLD**, never false-ALLOW.
- Any consent `!= VALID` (incl. MISSING/absent snapshot) → **deny** external measurement / audience / CRM.
- Any missing/ambiguous `guest→customer` mapping → **LOW/HOLD**, never a guessed merge, never an overwrite.

---

## 5. Minimal change set — files to create (all staged under `04-artifacts/impl/M6.2A/`)

Legend: **Leg** = exit-gate check # in the slice file (L1..L8). **Contract/Rule** = anchor. **Rollback** = per-item.
Because everything is **staged** (no live system, no applied migration), every rollback is non-destructive: removing the
staged file reverts the item with zero runtime/data impact. Item-specific notes call out what reverting *means* at the
eventual owner-controlled integration step.

### 5.1 Project baseline / config

| # | Target-relative file | Purpose | Contract/Rule | Leg | Smoke | Rollback |
|---|---|---|---|---|---|---|
| A1 | `pyproject.toml` | pytest config, python 3.12 pin, package metadata (greenfield baseline convention) | stack manifest | L1–L5 (enables tests) | — | Delete file; no dependency added, nothing installed. |
| A2 | `README.md` | Staged-slice notes: BLOCKED/OFF, measure-only, no egress, override banner | brief / RULE-H01 | L8 | — | Delete file (doc only). |
| A3 | `app/__init__.py`, `app/measurement/__init__.py` (+ subpackage inits) | package scaffolding | convention | L1–L5 | — | Delete files; no behavior. |
| A4 | `app/config.py` | Immutable staged-posture constants: `GLOBAL_GATEWAY_STATE="BLOCKED"`, `PRODUCTION_FLAG="OFF"`, `EXTERNAL_SEND="OFF"`, masking format (M6-OD-012 pack default `abc***xy`) | RULE-H01/H02 | L8 | — | Delete file; no persisted config, no live setting touched. |

### 5.2 Models (ownership split = the meaningful axis)

| # | Target-relative file | Purpose | Contract/Rule | Leg | Smoke | Rollback |
|---|---|---|---|---|---|---|
| B1 | `app/measurement/models/consumed.py` | Read-model dataclasses for the 3 CONSUMED shapes: `EventRegistryRow` (CTR-003: event_code, owner, channel, data_sensitivity, external_send_policy, schema_ref, registration_state), `GuestContact` (CTR-005: guest_id, contact_fingerprint, mapped_customer_id, mapping_audit_ref, first_seen_at), `ConsentSnapshot` (CTR-006: consent_snapshot_id, subject_ref, consent_state{VALID\|MISSING\|EXPIRED\|OPT_OUT}, captured_at, consent_scope, source_channel). Field-names only; PII fields flagged. | CTR-003/005/006; RULE-018 (consume-only) | L1,L2,L3 | — | Delete file; no schema shipped to any owner table. |
| B2 | `app/measurement/models/web_event_log.py` | The one **M6-OWNED** row `WebEventLog` (CTR-004: log_id, page_id, session_id, source, consent_snapshot_id, event_ts, idempotency_key, event_code, ingested_at, correlation_id); frozen/immutable dataclass to encode append-only intent | CTR-004; RULE-007 | L1,L4 | — | Delete file; append-only row type removed; no table exists yet. |

### 5.3 Cross-cutting helpers

| # | Target-relative file | Purpose | Contract/Rule | Leg | Smoke | Rollback |
|---|---|---|---|---|---|---|
| C1 | `app/measurement/masking.py` | `mask(value)` → `abc***xy`; applied to guest_id/customer_id/subject_ref/contact_fingerprint/session_id before any log/evidence | RULE-014/H02; M6-OD-012 (OPEN) | L3 | — | Delete file; no data emitted (nothing logged live). |
| C2 | `app/measurement/audit.py` | `AuditRecord` + in-memory `AuditLog` sink for reject/HOLD decisions and identity-mapping decisions (actor, reason, evidence_ref, masked subject) | RULE-001/006 audit; RULE-015 | L1,L3,L4 | SMK-001 | Delete file; audit sink is in-memory only, no persisted audit. |
| C3 | `app/measurement/ports.py` | Read-only port interfaces: `EventRegistryReader`, `GuestContactReader`, `ConsentReader`, `CustomerRefReader` (minimal customer existence/id for the mapping). No write methods exist → M6 cannot mutate consumed tables. | RULE-018; boundary | L1,L2,L3 | — | Delete file; interfaces only, no adapters bound to any real source. |

### 5.4 Decision paths (the load-bearing core)

| # | Target-relative file | Purpose | Contract/Rule | Leg | Smoke | Rollback |
|---|---|---|---|---|---|---|
| D1 | `app/measurement/registry/validator.py` | `validate_event(event_code, ...)`: lookup via `EventRegistryReader`; **unknown → REJECT/HOLD + audit**; `registration_state != ACTIVE` → REJECT/HOLD; returns validity + (data_sensitivity, external_send_policy) with **fail-closed defaults** (§4). M6 never inserts/invents an event code. | CTR-003; RULE-001/018; **prevents FAIL-003** | **L1**, L4 | **SMK-001** | Delete module + its test; consumed registry untouched (read-only). |
| D2 | `app/measurement/consent/gate.py` | `evaluate_consent(snapshot, scope)`: **fail-closed** — only `consent_state==VALID` (and scope permitted) allows external_measurement/audience/crm; MISSING/EXPIRED/OPT_OUT/absent → **deny**. Two-checkpoint aware (event-time snapshot here; send-time re-check is the future dispatcher's job, out of scope). Marks eligibility only — **never sends**. | CTR-006; RULE-002; **prevents FAIL-002** | **L2**, L5 | **SMK-002** | Delete module + its test; no egress path exists in this slice regardless. |
| D3 | `app/measurement/identity/resolver.py` | `resolve_identity(guest_id)`: read `guest_contacts` mapping; require `mapping_audit_ref` present with `mapped_customer_id`; **missing/ambiguous → LOW/HOLD** (RULE-009 confidence), **never overwrite without evidence** (RULE-006). Emits masked audit. | CTR-005; RULE-006 | **L3** | — | Delete module + its test; no mapping written (M6 read-only on guest_contacts). |

### 5.5 Append-only log substrate

| # | Target-relative file | Purpose | Contract/Rule | Leg | Smoke | Rollback |
|---|---|---|---|---|---|---|
| E1 | `app/measurement/logs/idempotency.py` | `build_idempotency_key(...)` = **LOCKED** RULE-005 formula `event_code + page_id + session_id + raw_event_hash + normalized_ts` (via `hashlib`); formula not altered | CTR-004; RULE-005 | L1,L4 | (SMK-003 is M6.2B/D) | Delete file; pure function, no state. |
| E2 | `app/measurement/logs/web_event_log_store.py` | `WebEventLogStore` append-only: **`append()` = INSERT only**; `UPDATE`/`DELETE` not implemented and actively rejected; duplicate `idempotency_key` → **no second row / no double log** (store-level dedup). In-memory adapter for staged tests; DB binding deferred to M6-OD-011 + §6 DDL. | CTR-004; RULE-007/005 | L1,L4 | (store-level dedup; SMK-003 e2e later) | Delete module + its test; no rows persisted; at integration, revert = §6 down-DDL. |

### 5.6 Ingest orchestration (thin seam)

| # | Target-relative file | Purpose | Contract/Rule | Leg | Smoke | Rollback |
|---|---|---|---|---|---|---|
| F1 | `app/measurement/ingest.py` | `ingest_event(...)`: orchestrates **validate (D1) → append to log (E2) → attach consent snapshot ref + evaluate egress-eligibility (D2, marks only)**; a rejected/HELD event is still **logged internally, never silently lost**; returns a measure-only result (no send, no scale). This is the seam the M6.2B HTTP endpoint will later call. | CTR-004; RULE-001/002/004/007 | L1,L2,L4,L5 | SMK-001, SMK-002 | Delete module + its test; no external effect (no dispatcher, `external_send=OFF`). |

### 5.7 `app/__main__.py`

| # | Target-relative file | Purpose | Contract/Rule | Leg | Smoke | Rollback |
|---|---|---|---|---|---|---|
| G1 | `app/__main__.py` | Minimal `python -m app` entrypoint that prints the staged posture (BLOCKED/OFF/measure-only) and exits 0 — satisfies the LOCKED `run_command` without starting any server or egress | stack manifest; RULE-H01 | L8 | — | Delete file; entrypoint prints only, does nothing external. |

---

## 6. Staged migration (the only M6-OWNED table)

M6 owns exactly one table in this slice: `web_event_logs` (CTR-004). The three consumed tables
(`event_registry`, `guest_contacts`, `guest_marketing_consent_snapshot`) and `customers/...` are **NOT** migrated by
M6 (their owners write them) — M6 reads them via ports (test doubles in fixtures).

| # | Target-relative file | Purpose | Contract/Rule | Leg | Rollback |
|---|---|---|---|---|---|
| M1 | `migrations/0001_create_web_event_logs.sql` | **Staged DDL** (up + down) creating append-only `web_event_logs` with the CTR-004 columns, `UNIQUE(idempotency_key)`, and an append-only guard comment (DB-level enforcement — e.g. revoke UPDATE/DELETE / trigger — chosen at the M6-OD-011 stack). **Never applied** (`live_migrations=false`). | CTR-004; RULE-007/005 | L1 | **Down-DDL `DROP TABLE web_event_logs`** included in the same file; staged-only so no live schema changes; deleting the staged file fully reverts. |
| M2 | `migrations/README.md` | Migration posture note: staged, never applied to any live DB; application order; append-only enforcement rationale | RULE-H01 | L8 | Delete file (doc only). |

---

## 7. Test plan → done-gate / smoke mapping (`pytest -q`)

Fixtures (`tests/conftest.py`) provide **in-memory port adapters** and seed data as **test doubles** for the consumed
tables (registry rows incl. a DEREGISTERED one; consent snapshots in each state; guest contacts mapped/unmapped). All
subjects masked; no raw PII in any fixture. These doubles stand in for Core/Customer/Consent-owned tables that M6 only reads.

| # | Target-relative test | Proves | Leg | Smoke | Fail-gate guarded | Rollback |
|---|---|---|---|---|---|---|
| T1 | `tests/test_event_registry_validation.py` | unknown event → REJECT/HOLD + audit; DEREGISTERED/stale → not false-ALLOWed; valid+ACTIVE → pass with sensitivity/send-policy | **L1** | **SMK-001** | FAIL-003 | Delete test. |
| T2 | `tests/test_consent_fail_closed.py` | VALID → eligible; MISSING/EXPIRED/OPT_OUT/absent → **no external measurement, no audience sync, no CRM** | **L2** | **SMK-002** | FAIL-002 | Delete test. |
| T3 | `tests/test_identity_mapping_audit.py` | mapping requires audit_ref; missing/ambiguous → LOW/HOLD; overwrite-without-evidence rejected; subjects masked | **L3** | — | — | Delete test. |
| T4 | `tests/test_web_event_logs_append_only.py` | INSERT works; UPDATE/DELETE rejected; duplicate idempotency_key → single row (RULE-005/007) | L1 | (store-level; SMK-003 e2e in M6.2B/D) | — | Delete test. |
| T5 | `tests/test_ingest_measure_only.py` | ingest logs even a rejected/HELD event (never lost); returns measure-only result; **no send/scale path reachable** (boundary guard, `external_send=OFF`) | L1,L2 | SMK-001, SMK-002 | FAIL-002/003 | Delete test. |

**Smoke → test binding**: SMK-001 = T1 (+T5 path); SMK-002 = T2 (+T5 path). Actual smoke *execution with recorded
results and evidence refs* (exit-gate legs **L4/L5**) is the **TESTER** role's job (M6-P1003 build / M6-P1004 run) — this
plan only wires the code and tests that make those smokes runnable. This CODER slice does not self-run or self-certify.

---

## 8. Master traceability matrix (every item → leg + smoke + rule + rollback)

| Item | Files | Contract | Rule(s) | Done-gate leg | Smoke | Fail-gate prevented | Rollback (staged ⇒ non-destructive) |
|---|---|---|---|---|---|---|---|
| Event validity path | D1,B1(part),C2,C3 | CTR-003 | RULE-001/018 | **L1** (+L4) | **SMK-001** | FAIL-003 | delete modules+T1; registry read-only |
| Consent fail-closed | D2,B1(part),C3 | CTR-006 | RULE-002 | **L2** (+L5) | **SMK-002** | FAIL-002 | delete module+T2; no egress exists |
| Identity mapping + audit | D3,B1(part),C1,C2,C3 | CTR-005 | RULE-006 (RULE-009 conf.) | **L3** | — | — | delete module+T3; guest_contacts read-only |
| Append-only log store | E1,E2,B2 | CTR-004 | RULE-007/005 | L1 (+L4) | store-level dedup | — | delete modules+T4; integration revert = M1 down-DDL |
| Ingest seam | F1 | CTR-004 | RULE-001/002/004/007 | L1,L2 (+L4,L5) | SMK-001/002 | FAIL-002/003 | delete module+T5 |
| Staged migration | M1,M2 | CTR-004 | RULE-007 | L1 | — | — | down-DDL in file; never applied live |
| Baseline/config/entrypoint | A1–A4,G1 | stack | RULE-H01/H02 | L8 | — | — | delete files; no live setting touched |
| Rollback documentation | this PLAN §5–§10 | — | — | **L8** | — | — | n/a (doc) |

**Coverage of the slice's exit-gate legs**: L1 ✓ (D1/E2/F1/T1/T4/M1), L2 ✓ (D2/F1/T2), L3 ✓ (D3/T3), L4/L5 ✓ *made
runnable* (handed to TESTER M6-P1003/1004), L6 (evidence per prompt — process), L7 (judge sign-off — process),
**L8 ✓ (this document — rollback per item)**. Every planned item maps to a leg and/or a smoke (acceptance check 1). ✓

---

## 9. Entry-gap constraints carried from the owner override (RULE-020)

The override risk-accepts two entry-evidence dossiers. This plan does **not** close them; it encodes them as constraints
so the staged slice stays inert until the M6.2G re-gate:

- **ENTRY-001 (P3 Verified-Revenue boundary, M3/Commerce)** — PARTIAL (fail-open recall, QuoteSnapshot missing, no
  runtime proof). *M6.2A design consequence*: this slice **never treats anything as revenue** (revenue = ORDER_VERIFIED
  only, and that's M6.2E/F). Identity resolution stops at `guest→customer`; the `order→verified revenue` legs are out of
  scope. No dependency on the unproven boundary is introduced.
- **ENTRY-003 (P6 event identity / Core `event_registry`)** — 2 PARTIAL + 3 GAP (`channel`, `data_sensitivity`,
  `external_send_policy` may be absent; owner not runtime-enforced). *M6.2A design consequence*: the §4 **fail-closed
  defaults** — MISSING `external_send_policy` ⇒ BLOCKED; MISSING `data_sensitivity` ⇒ treat as PII (mask); registry
  writes/owner enforcement are Core's, M6 stays consume-only (RULE-018). Egress remains framework-only regardless.
- **Mechanical locks preserved**: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — the plan
  writes no enabling value anywhere. **MANDATORY**: M6-ENTRY-001/002/003 are re-checked at M6.2G before ANY scale or
  external send; upstream fixes (`CORE_EVENT_REGISTRY_PATCH`, `M3_SELLABLE_GATE_FAILOPEN_PATCH`) must land first.

---

## 10. Rollback strategy (global)

1. **Nothing is live.** All artifacts are staged under `04-artifacts/impl/M6.2A/`; no migration is applied
   (`live_migrations=false`), no external call is made, no flag is written. Baseline rollback = delete the staged tree.
2. **Per-item rollback** is tabulated in §5–§8 (each file: what removing it reverts).
3. **Append-only caveat for the eventual integration step** (owner-controlled, not this slice): because `web_event_logs`
   is append-only (no row UPDATE/DELETE), reverting the table after a real apply requires the **down-DDL in `M1`**
   (`DROP TABLE`), not row deletion. Staged now ⇒ this is documented, not executed.
4. **Consumed tables are never mutated** by M6, so there is nothing to roll back on Core/Customer/Consent sides.

---

## 11. Acceptance self-map (this prompt's acceptance_checks)

1. *Every planned item maps to a done-gate leg or smoke id* → §5–§8 matrices (each row carries a Leg and/or Smoke). ✓
2. *Rollback step per item* → §5–§8 Rollback columns + §10. ✓
3. *No scope beyond the slice file* → §3 scope lock; HTTP/workers/attribution/egress explicitly deferred; verified
   against M6.2A + M6.2B slice files. ✓
4. *Implementation target LOCKED and M6-OD-011 decided* → §1 verification table. ✓
5. *Reuse conventions/test patterns from the locked target repository* → target repo verified **empty greenfield**; §2
   honestly reports there is nothing to reuse yet and **establishes** the reusable Python/pytest baseline instead. ✓

---

## 12. Notes / open items (parameters, not blockers for a staged plan)

- **M6-OD-011** (physical storage stack) DECIDED as GREENFIELD python; the concrete DB engine for `web_event_logs`
  append-only enforcement is realized at the owner-controlled integration step (M1 DDL is engine-neutral + noted).
- **M6-OD-003** (external_send_policy values / CAPI hash) OPEN → egress stays framework-only; not exercised in M6.2A.
- **M6-OD-012** (masking format) OPEN, pack default `abc***xy` used in `masking.py` as a parameter.
- Smoke **execution** (L4/L5) and the test *manifest/run* are the TESTER prompts (M6-P1003/M6-P1004); this plan makes
  them runnable but does not run or self-certify them (RULE-015).

*Plan-only: no code written, no migration applied, nothing sent/scaled/published, no flag flipped;
`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`.*
