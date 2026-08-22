# M6.2E — Slice Evidence Index

| Field | Value |
|---|---|
| Slice | **M6.2E** — Attribution Resolver (depends on M6.2D) |
| Assembled by | **M6-P1407** — `M6_2E_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, analysis_only) |
| Assembled on | 2026-07-31 (UTC) |
| Purpose | Index every band's evidence file / artifact / test report / boundary+security report, mapped to the slice exit-gate checklist, and list unresolved blockers — for the slice-gate Judge (M6-P1409). |
| Governance (immutable) | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `HASH_POLICY_RATIFIED=False`, `SCALE_MODEL_RATIFIED=False`. This index flips nothing and self-certifies nothing. |

> **Altitude note (read first).** This is an **index of collected evidence**, not a verdict. It does **not** assert
> that slice M6.2E has passed its exit gate. Exit-gate items **6 and 7 are NOT yet met** (docs prompt M6-P1408 and
> the slice-gate Judge M6-P1409 have not run — the steps that *follow* this one). This is the cleanest slice band
> so far: the entry gate is a real Judge PASS (M6-P1400 `SIGNED`), **all seven band prompts self-report PASS**, and
> **both in-scope fail gates (M6-FAIL-001 revenue, M6-FAIL-004 core override) held**. The M6.2D consent fix-first
> residuals **F-D/F-E/F-F were closed** here (F-D now *mandatory*), executed-verified by both M6-P1405 and M6-P1406;
> the M6.2E slice-gate Judge (M6-P1409) will re-verify F-D. The authoritative slice verdict is the Judge's, strictly
> from the evidence.

---

## 1. Slice prompt band — evidence status

Source: `04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv` (rows 118–127) + each evidence JSON.

| Prompt | Role | Title | Ledger status | Evidence JSON | Self-reported | `fail_gate_tripped` | Primary artifact(s) |
|---|---|---|---|---|---|---|---|
| M6-P1400 | JUDGE | M6_2E_ENTRY_GATE_JUDGE | **SIGNED** | `04-artifacts/evidence/prompts/M6-P1400.json` | PASS | false | `04-artifacts/evidence/judge/M6-P1400_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS) |
| M6-P1401 | CODER | M6_2E_CODER_PLAN | PASS | `04-artifacts/evidence/prompts/M6-P1401.json` | PASS | false | `04-artifacts/impl/M6.2E/PLAN.md` |
| M6-P1402 | CODER | M6_2E_CODER_IMPLEMENT | PASS (Round 2) | `04-artifacts/evidence/prompts/M6-P1402.json` | PASS | false | `04-artifacts/impl/M6.2E/IMPLEMENTATION_NOTES.md` + staged `app/` tree |
| M6-P1403 | TESTER | M6_2E_TESTER_BUILD | PASS | `04-artifacts/evidence/prompts/M6-P1403.json` | PASS | false | `04-artifacts/impl/M6.2E/tests/TEST_MANIFEST.md` |
| M6-P1404 | TESTER | M6_2E_TESTER_RUN | PASS | `04-artifacts/evidence/prompts/M6-P1404.json` | PASS | false | `04-artifacts/test-reports/M6.2E/SMOKE_RESULTS.md` |
| M6-P1405 | BOUNDARY_ADVERSARY | M6_2E_BOUNDARY_ADVERSARY | PASS | `04-artifacts/evidence/prompts/M6-P1405.json` | PASS | false | `04-artifacts/boundary-reports/M6.2E_boundary.md` |
| M6-P1406 | SECURITY_PII | M6_2E_SECURITY_REVIEW | PASS | `04-artifacts/evidence/prompts/M6-P1406.json` | PASS | false | `04-artifacts/security-reports/M6.2E_security.md` |
| **M6-P1407** | PM_ORCHESTRATOR | M6_2E_EVIDENCE_COLLECT | **RUNNING** | `04-artifacts/evidence/prompts/M6-P1407.json` | (this index) | false | `04-artifacts/evidence/prompts/M6_2E_EVIDENCE_INDEX.md` |
| M6-P1408 | ANALYST_ARCHITECT | M6_2E_DOCS | **TODO** | — (not produced) | — | — | `04-artifacts/analysis/slices/M6_2E_RUNBOOK.md` (pending) |
| M6-P1409 | JUDGE | M6_2E_SLICE_GATE_JUDGE | **TODO** | — (not produced) | — | — | `04-artifacts/evidence/judge/M6-P1409_JUDGE_FINAL_SIGN_OFF.json` (pending) |

All seven band evidence JSONs (M6-P1400 … M6-P1406) exist, are schema-valid, self-report **PASS**, and declare
`fail_gate_tripped=false`; the entry gate M6-P1400 is a genuine Judge `SIGNED` verdict PASS. (M6-P1402 required a
Round 2 to close two additional F-D bind sites and re-key two carried hash-policy test fixtures — owner-authorized
via operator brief — before landing PASS.) This prompt's own `M6-P1407.json` is produced at completion (written
**last**, after this index — pack hard-rule 2).

---

## 2. Artifact inventory (existence verified on disk)

### 2.1 Implementation (staged, `04-artifacts/impl/M6.2E/`)
- `PLAN.md` — minimal staged change set + master traceability + per-item rollback.
- `IMPLEMENTATION_NOTES.md` — realized plan + Round-2 deltas; §6 rollback.
- Carried-forward M6.2D tree + fix-first patches (`app/api/conversions.py` F-D mandatory bind,
  `integration/payload.py` F-E escaped join, `outbox/transport.py` + both dispatchers + `outbox/enqueue.py` F-F
  `safe_subject_ref`) + new **attribution layer**: `models/attribution_context.py` (CTR-002, 19 fields; psid masked
  on export), `attribution/resolver.py` (+ Ads/Live sub-resolvers; missing/conflicting → LOW/HOLD, RULE-009),
  `attribution/materializer.py` (CTR-023; revenue only from ORDER_VERIFIED, set-once Zone-B, RULE-003/008/009, no
  commission RULE-019), `attribution/adjustment.py` (append-only AdjustmentRecord, RULE-008),
  `store/measurement_event_store.py` (+`materialize()` set-once), `config.py` (+`SCALE_MODEL_RATIFIED=False`
  +`SCALE_EVIDENCE_MIN_CONFIDENCE=HIGH`, fail-closed).
- Migration (staged, never applied): `migrations/0006_create_ads_attribution_context.sql` (up + down-DDL).

### 2.2 Tests
- Manifest: `04-artifacts/impl/M6.2E/tests/TEST_MANIFEST.md`.
- Bound smoke: `tests/smoke/test_smk_006_order_verified_full_source.py`, `test_smk_007_missing_source_low_hold.py`,
  `test_smk_013_live_chain_trace.py`, `test_smk_018_verified_immutable_adjustment.py` (4 nodes each).
- Leg-supporting: `tests/test_attribution_trace_to_source.py`, `test_attribution_missing_source_low_hold.py`,
  `test_live_session_chain_trace.py`, `test_verified_immutable_adjustment.py`,
  `test_materializer_revenue_and_scale_rules.py`, `test_m6_2e_fixfirst_regressions.py` (F-D/F-E/F-F) + carried suites.
- Full staged suite **239 passed / 0 failed** (223 carried-forward + 16 new smoke nodes).

### 2.3 Reports
- Test report: `04-artifacts/test-reports/M6.2E/SMOKE_RESULTS.md` (SMK-006/007/013/018 all 4/4, L1 supporting 8/8).
- Boundary report: `04-artifacts/boundary-reports/M6.2E_boundary.md`.
- Security/PII report: `04-artifacts/security-reports/M6.2E_security.md` (verdict PASS; scan clean over 117 files).
- Entry-gate Judge sign-off: `04-artifacts/evidence/judge/M6-P1400_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS).

---

## 3. Contract checklist (from the slice spec)

| Contract | Shape | Ownership | Status (canon) | Harmonization |
|---|---|---|---|---|
| M6-CTR-002 | ads_attribution_context | M6 | **DRAFT_LOCKED** | 19 fields, doc §11 / SPEC §10.2; enforced by `models/attribution_context.py` |
| M6-CTR-023 | worker: attribution_materializer | M6 | MISSING / OWNER_DECISION_REQUIRED | M6-P0713 (PASS); gate M6-P0715 SIGNED — satisfied-for-entry; canon-flip deferred (non-blocking) |

---

## 4. Exit-gate checklist → evidence map

Legend: **MET** = evidence present and sufficient at the staged level · **SUPPORTED (staged)** = the bound suites
pass and the boundary adversary executed the check, but the tester withheld leg-*closure* ("supported") · **PENDING**
= the producing prompt has not run yet. Caveats are carry-forwards (see §5); none trips an in-scope fail gate
(M6-FAIL-001/004 — both held).

| # | Exit-gate check (slice spec) | Verdict | Evidence refs | Notes / caveats |
|---|---|---|---|---|
| 1 | **Order Verified trace to source** — an ORDER_VERIFIED can be traced back through quote/order to campaign/adset/ad/page/live/comment/messenger per the ads_attribution_context contract | **SUPPORTED (staged)** | `04-artifacts/test-reports/M6.2E/SMOKE_RESULTS.md` (SMK-006 4/4 + SMK-013 4/4) + `tests/test_attribution_trace_to_source.py` + `tests/test_live_session_chain_trace.py`; `app/measurement/attribution/resolver.py`, `models/attribution_context.py`, `attribution/materializer.py` (writes Zone-B); boundary `M6.2E_boundary.md` (FAIL-001/004 not tripped) | RULE-008/009. Tester (M6-P1404) calls leg **L1 "supported"**. Grading fail-closed (missing/dup/multi → LOW/HOLD, never scale evidence; only complete single channel → HIGH). Caveat B3-F-G (adjustment path under-validated). Final L1 closure is the slice-gate Judge's call. |
| 2 | **Smoke M6-SMK-006 executed** with recorded result + evidence ref | **MET** | `SMOKE_RESULTS.md` (4/4, exit 0); `04-artifacts/evidence/prompts/M6-P1404.json` | Full campaign/adset/ad+page → HIGH/NONE; revenue + ad hierarchy materialized into Zone-B (dashboard input; render is M6.2F). |
| 3 | **Smoke M6-SMK-007 executed** with recorded result + evidence ref | **MET** | `SMOKE_RESULTS.md` (4/4, exit 0); `04-artifacts/evidence/prompts/M6-P1404.json` | Missing source → MISSING_SOURCE/LOW/DIRECT; revenue still stored, never scale evidence (RULE-009). |
| 4 | **Smoke M6-SMK-013 executed** with recorded result + evidence ref | **MET** | `SMOKE_RESULTS.md` (4/4, exit 0); `04-artifacts/evidence/prompts/M6-P1404.json` | live_session_id + comment_id + messenger_thread_id all traced; psid masked on export (RULE-014). |
| 5 | **Proposed smoke M6-SMK-018 executed OR explicitly waived** by owner decision note | **MET** | `SMOKE_RESULTS.md` (4/4, exit 0); `04-artifacts/evidence/prompts/M6-P1404.json` | **Executed, not waived**: direct Zone-B overwrite of verified revenue REJECTED (set-once, RULE-008); correction is an audited append-only AdjustmentRecord. |
| 6 | **All slice prompts have evidence JSON** (schema-valid, no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | `04-artifacts/evidence/prompts/M6-P1400.json` … `M6-P1406.json` present (7); `M6-P1407.json` produced at this prompt's completion | **Not yet complete:** M6-P1408 (Docs) and M6-P1409 (Judge) evidence not produced (both TODO). |
| 7 | **Slice-gate Judge sign-off exists with verdict PASS** | **PENDING (not met)** | — | `04-artifacts/evidence/judge/M6-P1409_JUDGE_FINAL_SIGN_OFF.json` does **not** exist; M6-P1409 is TODO. (The existing `M6-P1400_JUDGE_FINAL_SIGN_OFF.json` is the *entry* gate, verdict PASS — not the slice gate.) |
| 8 | **Rollback steps documented** for every change this slice made | **MET** | `04-artifacts/impl/M6.2E/PLAN.md` (per-item Rollback) + `IMPLEMENTATION_NOTES.md` §6 (new files → delete; patched carried-forward files → revert to M6.2D version); `migrations/0006` down-DDL | All changes staged ⇒ non-destructive; attribution table revert = down-DDL `DROP TABLE`. |

**Summary:** items **2, 3, 4, 5 and 8 are MET** (SMK-018 executed, not waived); item **1 is SUPPORTED at the
staged level** (the bound smokes + supporting suites pass within the 239-test run and the boundary adversary
executed the fail-closed grading across all 12 confidence×conflict combos, but the tester withheld leg-*closure*
on L1); items **6 and 7 are PENDING** (M6-P1408 docs, then M6-P1409 slice-gate Judge). Coverage: **every exit-gate
checklist item is indexed** (acceptance check 1).

### 4.1 Smoke register bindings

| Smoke ID | Doc ID | Scenario (verbatim) | Expected (verbatim) | Result | Evidence |
|---|---|---|---|---|---|
| M6-SMK-006 | ADS-P0-006 | `ORDER_VERIFIED có campaign/adset/ad đầy đủ` | `ROAS/CPA/AOV dashboard cập nhật` | **PASS 4/4** | `SMOKE_RESULTS.md`, `M6-P1404.json` |
| M6-SMK-007 | ADS-P0-007 | `ORDER_VERIFIED thiếu source` | `Revenue vẫn lưu, attribution confidence LOW/HOLD` | **PASS 4/4** | `SMOKE_RESULTS.md`, `M6-P1404.json` |
| M6-SMK-013 | ADS-P0-013 | `Live/Comment/Messenger chain` | `Trace được live_session_id, comment_id, messenger_thread_id` | **PASS 4/4** | `SMOKE_RESULTS.md`, `M6-P1404.json` |
| M6-SMK-018 | proposed (HARDENING) | `Attribution correction attempted after ORDER_VERIFIED` | `Direct mutation rejected; adjustment record created with actor, reason, audit, evidence` | **PASS 4/4** (executed, not waived) | `SMOKE_RESULTS.md`, `M6-P1404.json` |

---

## 5. Unresolved blockers / carry-forwards (acceptance check 2)

None of the following is an open blocker of the **evidence-collection** task itself, and none trips an in-scope
fail gate (M6-FAIL-001/004 — both held). Each was already adjudicated by the responsible upstream prompt and is
carried forward as governance context for the slice-gate Judge (M6-P1409) and the owner.

- **B1 — Slice exit gate is not complete (expected at this step).** Item 6 pending M6-P1408/M6-P1409 evidence;
  item 7 pending the M6-P1409 slice-gate Judge PASS sign-off.

- **B2 — Fix-first F-D/F-E/F-F CLOSED (positive).** The M6.2D consent/robustness residuals bound by the entry gate
  were closed and **executed-verified by both M6-P1405 and M6-P1406**: **F-D** (measurement/conversions
  borrowed-consent) is now **MANDATORY** — the conversions endpoint binds `safe_subject_ref(snap) ==
  customer_or_guest_key`, rejects a conversion citing another subject's consent, and fails closed on a missing
  reader; **F-E** (platform_event_id escaped join → injective); **F-F** (`safe_subject_ref` via `type(x) is str` in
  both dispatchers + the two Round-2 bind sites). The M6.2E slice-gate Judge (M6-P1409) specifically re-verifies F-D.

- **B3 — M6.2E new residuals (armed-not-fired; none trips M6-FAIL-001/004; routed to CODER).**
  - **F-G [MINOR]:** the adjustment path is under-validated (three same-class sub-gaps) — (a) accepts empty
    `actor`/`reason`/`audit_ref`/`evidence_ref`; (b) never checks the target row exists/verified (an adjustment can
    be recorded against a non-existent event); (c) `AdjustmentRecord.proposed` is a plain mutable dict (post-append
    mutable). In every case the verified row is unchanged (the overlay is never applied) → **not** FAIL-004; a
    data-quality / accountability / immutability-completeness gap. Fix: require non-empty fields; assert the row
    exists+verified; store `proposed` immutably.
  - **O-1:** `AdjustmentRecord.proposed` has no field allow-list (a caller can park e.g. `commission_value` — stored
    but never computed/applied, so RULE-019 holds; constrain to attribution/revenue fields).
  - **O-5:** a NaN/Inf `revenue_value` breaks the set-once idempotent replay (`NaN != NaN`); reject non-finite
    (`math.isfinite`) → M6.2F / CODER.
  - **O-4:** `materializer.verified_event_codes` is a constructor default (ORDER_VERIFIED correct); a mis-wire could
    book non-verified revenue — wiring discipline, not channel-reachable.
  - **O-3:** a carried **M6.2A ingest** raw-subject comparison (`snapshot.subject_ref == guest_id`, not via
    `safe_subject_ref`) could raise on a hostile ConsentSnapshot subclass — FAIL-002-adjacent, armed-not-fired
    (external_send=OFF), coder-flagged for a later hardening (the ingest-path analogue of F-D/F-F).
  - *Ref:* `04-artifacts/boundary-reports/M6.2E_boundary.md`, `04-artifacts/security-reports/M6.2E_security.md`.

- **B4 — Security / privacy observations (M6-P1406), forward-routed.**
  - **O-2 (→ M6-OD-012):** the durable Zone-B `ads_attribution_context` keeps raw `psid` (masked on export via
    `to_public`; in-memory/staged, no sink → not a leak today).
  - **O-2b (NEW, → M6-OD-012):** export masks **only** `psid` — `messenger_thread_id` / `comment_id` /
    `live_session_id` are exported raw. Defensible (object ids vs user id), but a `messenger_thread_id` can resolve
    to a person, so whether the M6-OD-012 masking policy covers conversation/thread identifiers is an owner /
    privacy-legal call worth making explicit. Not a present leak.
  - Forward at the M6-OD-011 binding: the `attribution_materializer` worker must run under a scoped service account
    distinct from the runtime API.

- **B5 — Governance / decision-file status (UPDATE to what M6-P1307 flagged).**
  - **RESOLVED:** `M6-DEFER-OD003-M6.2D.json` **now exists** in `04-artifacts/evidence/decisions/` — the owner filed
    it (its retro-note legitimizes the earlier phantom-referenced M6-P1306 SKIP that M6-P1307 flagged). The owner
    also filed **`M6-OVERRIDE-M6P1309-STAGED.json`**, which opened M6.2E STAGED after the M6.2D slice-gate Judge
    (M6-P1309) returned **BLOCKED** (verdict unmodified, **not** converted to PASS — same mechanism as M6.2A's
    `M6-OVERRIDE-M6P1000-STAGED`).
  - **STILL OPEN:** `M6-DEFER-FBC-M6.2D.json` — recommended by M6-P1209, M6-P1300, and re-escalated by M6-P1400/1401
    to bind F-B/F-C/F-A + F-D into the M6.2G gate (M6-P1600) RequiredInputs — was **never created**. The substance
    is now largely carried by `M6-OVERRIDE-M6P1309-STAGED` (which binds F-D to M6.2E/M6.2G) and F-D/F-E/F-F are
    closed, but the dedicated decision file + the M6-P1600 RequiredInputs wiring remain an operator/owner TODO.

- **B6 — Contract housekeeping (non-blocking).** M6-CTR-002 is `DRAFT_LOCKED`; M6-CTR-023 is
  `MISSING / OWNER_DECISION_REQUIRED` in canon but satisfied-for-entry (producer M6-P0713 PASS, gate M6-P0715
  SIGNED). The CTR-023 canon-flip is deferred operator housekeeping.

- **B7 — Open owner decisions (forward gates).** **M6-OD-005** (attribution model final choice) OPEN → M6.2E
  implements **multi-model DISPLAY** only; single-model **SCALE evidence** is fail-closed pending the owner
  (`SCALE_MODEL_RATIFIED=False` + `SCALE_EVIDENCE_MIN_CONFIDENCE=HIGH`; even a clean HIGH/NONE row is not scale
  evidence). **M6-OD-003** (hash) remains the recorded blocker at M6.2D (N/A for M6.2E — no external-send data
  path). **M6-OD-004** (connector), **M6-OD-008** (revenue — ORDER_VERIFIED-only default), **M6-OD-012** (masking —
  now incl. the O-2b conversation/thread-id question).

- **B8 — Inherited cross-slice carry-forwards (still in force).** ENTRY-001 (P3 verified-revenue) and ENTRY-003
  (event_registry gaps; Platform/P0-06-owned) remain **risk-accepted** under `M6-OVERRIDE-M6P1000-STAGED` (M6-P1000
  verdict BLOCKED, not converted). The **M6.2D slice exit** was itself via owner override
  (`M6-OVERRIDE-M6P1309-STAGED`; M6-P1309 verdict BLOCKED, not converted). The **mandatory M6.2G Scale-Gate re-gate**
  (ENTRY-001/002/003) stands before any real scale or external send.

- **B9 — Immutable governance posture.** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
  `HASH_POLICY_RATIFIED=False`, `SCALE_MODEL_RATIFIED=False` unchanged; no real send and no scale occur; the
  mandatory M6.2G re-gate stands.

---

## 6. Reader's guide for the slice-gate Judge (M6-P1409)

1. Start from `00-spec/slices/M6.2E.md` "Exit gate checks" (the 8 items in §4 above).
2. For legs 1–5 + 8, read the reports/evidence in the §4 "Evidence refs" cells directly (do not rely on this index).
3. **Explicitly re-verify F-D closure** (the override condition + the M6.2D coder commitment): confirm the
   conversions endpoint mandatorily binds `customer_or_guest_key ↔ consent subject_ref` and fails closed
   (M6-P1405/M6-P1406 executed-confirmed it).
4. Confirm items 6 & 7 by re-reading the ledger and `04-artifacts/evidence/judge/` (M6-P1409 sign-off is the Judge's own output).
5. Weigh the B3 residuals (F-G/O-1/O-3/O-4/O-5) and B4 privacy items (O-2/O-2b) as "close before scale / real
   send", plus the still-open **`M6-DEFER-FBC-M6.2D.json`** governance TODO (§5 B5), and the inherited B8
   risk-acceptances + the mandatory M6.2G re-gate.

*This index is descriptive. It advances no gate and self-certifies nothing; the runner EVIDENCE_GATE and the
slice-gate Judge decide closure.*
