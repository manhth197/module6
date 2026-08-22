# M6.2C — Slice Evidence Index

| Field | Value |
|---|---|
| Slice | **M6.2C** — Outbox Workers (depends on M6.2B) |
| Assembled by | **M6-P1207** — `M6_2C_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, analysis_only) |
| Assembled on | 2026-07-30 (UTC) |
| Purpose | Index every band's evidence file / artifact / test report / boundary+security report, mapped to the slice exit-gate checklist, and list unresolved blockers — for the slice-gate Judge (M6-P1209). |
| Governance (immutable) | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`. This index flips nothing and self-certifies nothing. |

> **Altitude note (read first).** This is an **index of collected evidence**, not a verdict. It does **not** assert
> that slice M6.2C has passed its exit gate. Exit-gate items **5 and 6 are NOT yet met** (docs prompt M6-P1208 and
> the slice-gate Judge M6-P1209 have not run — the steps that *follow* this one). The entry gate is a real Judge
> PASS (M6-P1200 `SIGNED`). This is the **first slice with a real egress surface** (an outbox + two dispatcher
> workers), so the consent gate is now the load-bearing M6-FAIL-002 control — and per M6-P1205/M6-P1206 it holds
> (no non-consented item reaches a transport; RULE-004 "no direct external send" holds; external send is doubly
> bolted). The authoritative slice verdict is the Judge's to render at M6-P1209, strictly from the evidence files.

---

## 1. Slice prompt band — evidence status

Source: `04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv` (rows 98–107) + each evidence JSON.

| Prompt | Role | Title | Ledger status | Evidence JSON | Self-reported | `fail_gate_tripped` | Primary artifact(s) |
|---|---|---|---|---|---|---|---|
| M6-P1200 | JUDGE | M6_2C_ENTRY_GATE_JUDGE | **SIGNED** | `04-artifacts/evidence/prompts/M6-P1200.json` | PASS | false | `04-artifacts/evidence/judge/M6-P1200_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS) |
| M6-P1201 | CODER | M6_2C_CODER_PLAN | PASS | `04-artifacts/evidence/prompts/M6-P1201.json` | PASS | false | `04-artifacts/impl/M6.2C/PLAN.md` |
| M6-P1202 | CODER | M6_2C_CODER_IMPLEMENT | PASS | `04-artifacts/evidence/prompts/M6-P1202.json` | PASS | false | `04-artifacts/impl/M6.2C/IMPLEMENTATION_NOTES.md` + staged `app/` tree |
| M6-P1203 | TESTER | M6_2C_TESTER_BUILD | PASS | `04-artifacts/evidence/prompts/M6-P1203.json` | PASS | false | `04-artifacts/impl/M6.2C/tests/TEST_MANIFEST.md` |
| M6-P1204 | TESTER | M6_2C_TESTER_RUN | PASS | `04-artifacts/evidence/prompts/M6-P1204.json` | PASS | false | `04-artifacts/test-reports/M6.2C/SMOKE_RESULTS.md` |
| M6-P1205 | BOUNDARY_ADVERSARY | M6_2C_BOUNDARY_ADVERSARY | PASS | `04-artifacts/evidence/prompts/M6-P1205.json` | PASS | false | `04-artifacts/boundary-reports/M6.2C_boundary.md` |
| M6-P1206 | SECURITY_PII | M6_2C_SECURITY_REVIEW | PASS | `04-artifacts/evidence/prompts/M6-P1206.json` | PASS | false | `04-artifacts/security-reports/M6.2C_security.md` |
| **M6-P1207** | PM_ORCHESTRATOR | M6_2C_EVIDENCE_COLLECT | **RUNNING** | `04-artifacts/evidence/prompts/M6-P1207.json` | (this index) | false | `04-artifacts/evidence/prompts/M6_2C_EVIDENCE_INDEX.md` |
| M6-P1208 | ANALYST_ARCHITECT | M6_2C_DOCS | **TODO** | — (not produced) | — | — | `04-artifacts/analysis/slices/M6_2C_RUNBOOK.md` (pending) |
| M6-P1209 | JUDGE | M6_2C_SLICE_GATE_JUDGE | **TODO** | — (not produced) | — | — | `04-artifacts/evidence/judge/M6-P1209_JUDGE_FINAL_SIGN_OFF.json` (pending) |

The **seven** band evidence JSONs that exist (M6-P1200 … M6-P1206) are schema-valid, self-report PASS, and declare
`fail_gate_tripped=false`; the entry gate M6-P1200 is a genuine Judge `SIGNED` verdict PASS. This prompt's own
`M6-P1207.json` is produced at completion (written **last**, after this index — pack hard-rule 2).

---

## 2. Artifact inventory (existence verified on disk)

### 2.1 Implementation (staged, `04-artifacts/impl/M6.2C/`)
- `PLAN.md` — minimal staged change set + master traceability + per-item rollback.
- `IMPLEMENTATION_NOTES.md` — realized plan + deltas; §7 rollback.
- Carried-forward M6.2B tree (byte-identical) + new outbox layer: `models/conversion_event.py` (CTR-007),
  `models/measurement_outbox.py` (CTR-008), `models/audience_outbox.py` (CTR-011), `models/segments.py` (CTR-009/010,
  consumed), `store/conversion_event_store.py`, `outbox/outbox_store.py`, `outbox/transport.py` (StagedBlockedTransport
  — refuses every real send), `outbox/enqueue.py` (fan-out; runtime holds NO transport), `outbox/measurement_dispatcher.py`
  (CTR-021), `outbox/audience_dispatcher.py` (CTR-022), `adapters/segment_reader.py`, `api/conversions.py` (CTR-017).
  Additive extensions: `ports.py` (+SegmentReader), `config.py` (+OUTBOX_MAX_RETRIES).
- Migrations (staged, never applied): `migrations/0003_create_conversion_events.sql`,
  `0004_create_marketing_measurement_outbox.sql`, `0005_create_marketing_audience_outbox.sql` (up + down-DDL).

### 2.2 Tests
- Manifest: `04-artifacts/impl/M6.2C/tests/TEST_MANIFEST.md`.
- Bound smoke: `tests/smoke/test_smk_002_outbox_consent_failclosed.py` (4),
  `tests/smoke/test_smk_016_outbox_retry_deadletter.py` (4).
- Leg-supporting: `tests/test_no_direct_external_send.py` (L1), `tests/test_dispatcher_retry_deadletter.py` (L2),
  `tests/test_consent_failclosed_at_send.py`, `tests/test_audience_chain.py`,
  `tests/test_measurement_outbox_fanout_dedup.py`, `tests/test_conversions_endpoint.py` + carried-forward suites.
- Full staged suite **171 passed / 0 failed** (139 carried-forward + 24 coder + 8 new smoke nodes).

### 2.3 Reports
- Test report: `04-artifacts/test-reports/M6.2C/SMOKE_RESULTS.md` (SMK-002 4/4, SMK-016 4/4, L1/L2 supporting 13/13).
- Boundary report: `04-artifacts/boundary-reports/M6.2C_boundary.md`.
- Security/PII report: `04-artifacts/security-reports/M6.2C_security.md`.
- Entry-gate Judge sign-off: `04-artifacts/evidence/judge/M6-P1200_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS).

### 2.4 Governing spec / registers / decisions indexed
- `00-spec/slices/M6.2C.md`, `00-spec/registers/SMOKE_REGISTER.md`, `00-spec/registers/CONTRACT_REGISTER.md`.
- `04-artifacts/evidence/decisions/M6-OVERRIDE-M6P1000-STAGED.json`, `M6-DEFER-F1F2-M6.2B.json` (inherited context).

---

## 3. Contract checklist (from the slice spec)

All eight are `MISSING / OWNER_DECISION_REQUIRED` in the CONTRACT_REGISTER but **satisfied-for-entry** per the
slice checklist ("if MISSING, its harmonization prompt must be PASS"): producers all PASS and gate M6-P0715 SIGNED,
staged schemas present. The **canon-flip is deferred, non-blocking operator housekeeping** (see B5).

| Contract | Shape | Ownership | Status (canon) | Harmonization |
|---|---|---|---|---|
| M6-CTR-007 | conversion_events | M6/Core | MISSING / OWNER_DECISION_REQUIRED | M6-P0704 (PASS) |
| M6-CTR-008 | marketing_measurement_outbox | M6 (worker only) | MISSING / OWNER_DECISION_REQUIRED | M6-P0705 (PASS) |
| M6-CTR-009 | customer_segments (consumed) | CONSUMED | MISSING / OWNER_DECISION_REQUIRED | M6-P0706 (PASS) |
| M6-CTR-010 | customer_segment_members (consumed; never a trigger owner) | CONSUMED | MISSING / OWNER_DECISION_REQUIRED | M6-P0706 (PASS) |
| M6-CTR-011 | marketing_audience_outbox | M6 (worker only) | MISSING / OWNER_DECISION_REQUIRED | M6-P0706 (PASS) |
| M6-CTR-017 | POST /api/ads/conversions | M6 | MISSING / OWNER_DECISION_REQUIRED | M6-P0711 (PASS) |
| M6-CTR-021 | worker: marketing_measurement_dispatcher | M6 | MISSING / OWNER_DECISION_REQUIRED | M6-P0713 (PASS) |
| M6-CTR-022 | worker: marketing_audience_dispatcher | M6 | MISSING / OWNER_DECISION_REQUIRED | M6-P0713 (PASS) |

---

## 4. Exit-gate checklist → evidence map

Legend: **MET** = evidence present and sufficient at the staged level · **SUPPORTED (staged)** = the bound suites
pass and the boundary adversary executed the check, but the tester withheld leg-*closure* (called the leg
"supported") and residuals remain, so final closure is the slice-gate Judge's call · **PENDING** = the producing
prompt has not run yet. Caveats are carry-forwards (see §5); none trips the in-scope fail gate (M6-FAIL-002).

| # | Exit-gate check (slice spec) | Verdict | Evidence refs | Notes / caveats |
|---|---|---|---|---|
| 1 | **No direct external send** — every external measurement/audience payload originates from an outbox row processed by a worker, never from a runtime request | **SUPPORTED (staged)** | `04-artifacts/test-reports/M6.2C/SMOKE_RESULTS.md` (SMK-002 transport-never-called + `test_no_direct_external_send.py` 3/3); `app/api/conversions.py` + `outbox/enqueue.py` (hold NO transport), `outbox/transport.py` (StagedBlockedTransport raises), dispatchers; boundary `M6.2C_boundary.md` (RULE-004 holds, executed) | RULE-004. Tester (M6-P1204) calls leg **L1 "supported", not "closed"**. Egress **doubly bolted**: `permits_external_send()` hard-False + StagedBlockedTransport raises on every deliver. Caveat B2-F-A (dispatcher robustness). Final L1 closure is the slice-gate Judge's call. |
| 2 | **Retry / dead-letter pass** — bounded retry with error_log + next_retry_at; exhausted items dead-letter with full trace, no silent loss | **SUPPORTED (staged)** | `SMOKE_RESULTS.md` (SMK-016 4/4) + `tests/test_dispatcher_retry_deadletter.py` (3/3); `outbox/outbox_store.py`, dispatchers; boundary confirmed bounded RETRY→DEAD_LETTER, no infinite retry, no silent loss | RULE-004 / doc §12. Tester calls leg **L2 "supported", not "closed"**. Policy-block (consent/dq) is a *distinct* terminal DEAD_LETTER (never a retry loop); transport-failure is the bounded-retry path. Final L2 closure is the slice-gate Judge's call. |
| 3 | **Smoke M6-SMK-002 executed** with recorded result + evidence ref | **MET** | `04-artifacts/test-reports/M6.2C/SMOKE_RESULTS.md` (4/4, exit 0); `04-artifacts/evidence/prompts/M6-P1204.json` | Both clauses proven (no external measurement + no audience sync) via the RULE-002 two-checkpoint consent gate; guards M6-FAIL-002. |
| 4 | **Proposed smoke M6-SMK-016 executed OR explicitly waived** by owner decision note | **MET** | `04-artifacts/test-reports/M6.2C/SMOKE_RESULTS.md` (4/4, exit 0); `04-artifacts/evidence/prompts/M6-P1204.json` | **Executed, not waived** (the stronger option): bounded retry → dead-letter, no infinite retry, no silent loss. |
| 5 | **All slice prompts have evidence JSON** (schema-valid, no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | `04-artifacts/evidence/prompts/M6-P1200.json` … `M6-P1206.json` present (7); `M6-P1207.json` produced at this prompt's completion | **Not yet complete:** M6-P1208 (Docs) and M6-P1209 (Judge) evidence not produced (both TODO). |
| 6 | **Slice-gate Judge sign-off exists with verdict PASS** | **PENDING (not met)** | — | `04-artifacts/evidence/judge/M6-P1209_JUDGE_FINAL_SIGN_OFF.json` does **not** exist; M6-P1209 is TODO. (The existing `M6-P1200_JUDGE_FINAL_SIGN_OFF.json` is the *entry* gate, verdict PASS — not the slice gate.) |
| 7 | **Rollback steps documented** for every change this slice made | **MET** | `04-artifacts/impl/M6.2C/PLAN.md` (per-item Rollback) + `IMPLEMENTATION_NOTES.md` §7 (new files → delete; 3 extended files → revert to M6.2B version); `migrations/0003…0005` down-DDL | All changes staged ⇒ non-destructive; append-only outbox table revert = down-DDL `DROP TABLE`. |

**Summary:** items **3, 4 and 7 are MET** (SMK-016 executed, not waived); items **1 and 2 are SUPPORTED at the
staged level** — the bound smoke + supporting suites pass within the 171-test run and the boundary adversary
executed both RULE-004 (no direct send) and the bounded retry/dead-letter mechanic, but the tester withheld
leg-*closure* on L1/L2 and the F-A/F-B/F-C residuals remain, so **final L1/L2 closure is the slice-gate Judge's
call**; items **5 and 6 are PENDING** (M6-P1208 docs, then M6-P1209 slice-gate Judge). Coverage: **every exit-gate
checklist item is indexed** (acceptance check 1).

### 4.1 Smoke register bindings

| Smoke ID | Doc ID | Scenario (verbatim) | Expected (verbatim) | Result | Evidence |
|---|---|---|---|---|---|
| M6-SMK-002 | ADS-P0-002 | `Event hợp lệ nhưng thiếu consent` | `Không external measurement, không audience sync` | **PASS 4/4** | `SMOKE_RESULTS.md`, `M6-P1204.json` |
| M6-SMK-016 | proposed (HARDENING) | `Outbox item fails to send N times` | `Bounded retry with error_log + next_retry_at, then dead-letter; no infinite retry, no silent loss` | **PASS 4/4** (executed, not waived) | `SMOKE_RESULTS.md`, `M6-P1204.json` |

---

## 5. Unresolved blockers / carry-forwards (acceptance check 2)

None of the following is an open blocker of the **evidence-collection** task itself, and none trips the in-scope
fail gate (M6-FAIL-002) — each was already adjudicated by the responsible upstream prompt and is carried forward
as governance context for the slice-gate Judge (M6-P1209) and the owner.

- **B1 — Slice exit gate is not complete (expected at this step).**
  - Item 5 pending: **M6-P1208** (Docs) and **M6-P1209** (Judge) evidence JSONs not yet produced.
  - Item 6 pending: **M6-P1209** slice-gate Judge PASS sign-off does not exist.
  - *Disposition:* normal sequence — these are the prompts that follow M6-P1207.

- **B2 — M6.2C boundary/security residuals, all armed-not-fired, routed to CODER before M6.2D wires a real
    transport (none trips M6-FAIL-002; the two consent fail-OPEN residuals need hostile/misconfigured CONSUMED data
    and are blocked by the staged transport today).**
  - **F-A [MINOR, robustness]:** the two dispatchers + the audience enqueue wrap `reader.get` but **not**
    `permits_send` / `evaluate` / `current_state`, so a hostile consent adapter (raises, or returns a duck lacking
    `consent_state`) escapes `run_once` and aborts the drain batch (lost audit + drain-DoS; no send). Wrap fail-closed.
  - **F-B [MINOR, consent fail-OPEN, NEW]:** a `set`-subclass `consent_scope` with a lying `__contains__` (empty
    backing → vacuous element check) defeats the F2 guard (which validates container/element *types* but trusts
    `__contains__` for the grant) → `permits_send` True → would SEND (executed with an injected transport). Fix:
    `scope in frozenset(snapshot.consent_scope)`.
  - **F-C [MINOR, consent fail-OPEN, NEW]:** `enqueue_audience_sync` never binds `member.member_key` to
    `snap.subject_ref`, so a mispointed CONSUMED membership → a member ADDed on **another subject's** VALID consent
    (borrowed consent). The measurement path binds subject (the M6.2A MAJOR-2 fix); the audience path never did.
    Fix: bind `member_key ↔ subject_ref` before ADD.
  - *Ref:* `04-artifacts/boundary-reports/M6.2C_boundary.md`.

- **B3 — Security / data-quality observations (M6-P1206), forward-routed.**
  - **O-2:** the AUDIENCE outbox row + conversion_events hold one raw identity ref each (`member_key` /
    `customer_or_guest_key`) **by design** — masked on every export, hashed into the dedup key, PII-safe payload_ref;
    in-memory/staged and never sinked (no leak today). Enforce OD-012 masking + pseudonymous-id charset validation
    before durable binding / M6.2D. (The MEASUREMENT outbox row carries no raw PII — key hashed, refs only.)
  - **O-4 [DQ]:** a NaN/Inf `revenue_value` on ORDER_VERIFIED passes the `isinstance` number check (fix:
    `math.isfinite`); DQ gap → M6.2F / CODER.
  - Forward at the M6-OD-011 binding: request **authN/authZ** on the conversions endpoint + **worker
    service-account scoping** for the two dispatchers (they become the credentialed egress principals at M6.2D —
    secret_ref-scoped least-privilege tokens, identity distinct from the runtime API).
  - *Ref:* `04-artifacts/security-reports/M6.2C_security.md`.

- **B4 — External-send FORWARD gates (hard, before any M6.2D real send).** **M6-OD-003** (hash policy + permitted
  send fields) and **M6-OD-004** (connector). In M6.2C egress is doubly bolted (`permits_external_send()` hard-False
  + `StagedBlockedTransport` raises), so these are forward gates, not entry blockers. At M6.2D the platform
  Pixel/CAPI/Offline + audience transports' access/verify tokens **must be secret_ref-only**.

- **B5 — Contract housekeeping (non-blocking).** All eight slice contracts (CTR-007/008/009/010/011/017/021/022)
  are `MISSING / OWNER_DECISION_REQUIRED` in canon but satisfied-for-entry (harmonization producers PASS, gate
  M6-P0715 SIGNED). The canon-flip (apply staged schemas to `00-spec/contracts/` + `CONTRACT_REGISTER` DRAFT_LOCKED
  + SCHEMA_CHANGELOG) is deferred operator housekeeping.

- **B6 — Inherited cross-slice carry-forwards (still in force).** ENTRY-001 (P3 verified-revenue) and ENTRY-003
  (event_registry gaps; Platform/P0-06-owned) remain **risk-accepted** under `M6-OVERRIDE-M6P1000-STAGED`
  (M6-P1000 verdict stays **BLOCKED**, not converted), bound to M6.2A entry + the **mandatory M6.2G Scale-Gate
  re-gate**, not checked at M6.2C. The **M6.2B** endpoint residuals (its own F-A deep-JSON RecursionError, F-B
  over-broad hash, O-1, MINOR-6, MINOR-9-res — *distinct* from M6.2C's F-A/F-B above) bind at the same owner
  HTTP/durable integration step. Open owner decisions: **M6-OD-003** (hash, M6.2D), **M6-OD-004** (connector,
  M6.2D), **M6-OD-008** (revenue — CTR-017 defaults ORDER_VERIFIED-only, fail-closed), **M6-OD-012** (masking format).

- **B7 — Immutable governance posture.** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`
  unchanged; platform-specific dedup/hash (M6.2D) and attribution (M6.2E) are **out of scope** for M6.2C. The
  **mandatory M6.2G Scale-Gate re-gate** stands before any real scale or external send.

---

## 6. Reader's guide for the slice-gate Judge (M6-P1209)

1. Start from `00-spec/slices/M6.2C.md` "Exit gate checks" (the 7 items in §4 above).
2. For legs 1–4 + 7, read the reports/evidence in the §4 "Evidence refs" cells directly (do not rely on this index).
3. Confirm items 5 & 6 by re-reading the ledger and `04-artifacts/evidence/judge/` (M6-P1209 sign-off is the Judge's own output).
4. This is the first real egress surface: weigh that the load-bearing consent control (FAIL-002) and RULE-004
   no-direct-send both **hold** (executed) **and** the B2 consent fail-OPEN residuals (F-B/F-C) + robustness F-A —
   all armed-not-fired, "close before M6.2D wires a real transport" — plus the B4 forward gates (OD-003/004) and the
   inherited B6 risk-acceptances + mandatory M6.2G re-gate.

*This index is descriptive. It advances no gate and self-certifies nothing; the runner EVIDENCE_GATE and the
slice-gate Judge decide closure.*
