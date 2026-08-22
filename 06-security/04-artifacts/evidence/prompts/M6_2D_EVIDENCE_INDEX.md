# M6.2D — Slice Evidence Index

| Field | Value |
|---|---|
| Slice | **M6.2D** — Pixel/CAPI/Offline Dedup + Hash Policy (depends on M6.2C) |
| Assembled by | **M6-P1307** — `M6_2D_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, analysis_only) |
| Assembled on | 2026-07-30 (UTC) |
| Purpose | Index every band's evidence file / artifact / test report / boundary+security report, mapped to the slice exit-gate checklist, and list unresolved blockers — for the slice-gate Judge (M6-P1309). |
| Governance (immutable) | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `HASH_POLICY_RATIFIED=False`. This index flips nothing and self-certifies nothing. |

> **Altitude note (read first).** This is an **index of collected evidence**, not a verdict. It does **not** assert
> that slice M6.2D has passed its exit gate. Two things make M6.2D distinctive and must reach the Judge:
> (1) **exit-gate leg 2 (no PII thô) is the designed "BLOCKED on M6-OD-003 where unresolved" checkpoint** — the
> hash *mechanism* is proven (SMK-017 12/12, fail-closed, no raw PII, FAIL-008 not tripped), but hash-policy
> *conformance* is uncertifiable while M6-OD-003 (the ratified permitted-send-field list + salt/normalization) is
> OPEN. The security review **M6-P1306 honestly returned BLOCKED on exactly this** (not a leak, no fail gate
> tripped); the ledger then marked M6-P1306 **SKIPPED** via an owner deferral note (`M6-DEFER-OD003-M6.2D`; OD-003
> → forward gate at M6.2G). (2) The M6.2C consent fail-OPEN residuals **F-A/F-B/F-C were closed fix-first** here,
> but a **new symmetric measurement-path borrowed-consent (F-D)** was discovered — reachable from the untrusted
> conversions body — and is routed to M6.2E. Exit-gate items **5 and 6 are also PENDING** (M6-P1308 docs and the
> M6-P1309 slice-gate Judge have not run). The authoritative slice verdict is the Judge's, strictly from the evidence.

---

## 1. Slice prompt band — evidence status

Source: `04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv` (rows 108–117) + each evidence JSON.

| Prompt | Role | Title | Ledger status | Evidence JSON | Self-reported | `fail_gate_tripped` | Primary artifact(s) |
|---|---|---|---|---|---|---|---|
| M6-P1300 | JUDGE | M6_2D_ENTRY_GATE_JUDGE | **SIGNED** | `04-artifacts/evidence/prompts/M6-P1300.json` | PASS | false | `04-artifacts/evidence/judge/M6-P1300_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS) |
| M6-P1301 | CODER | M6_2D_CODER_PLAN | PASS | `04-artifacts/evidence/prompts/M6-P1301.json` | PASS | false | `04-artifacts/impl/M6.2D/PLAN.md` |
| M6-P1302 | CODER | M6_2D_CODER_IMPLEMENT | PASS | `04-artifacts/evidence/prompts/M6-P1302.json` | PASS | false | `04-artifacts/impl/M6.2D/IMPLEMENTATION_NOTES.md` + staged `app/` tree |
| M6-P1303 | TESTER | M6_2D_TESTER_BUILD | PASS | `04-artifacts/evidence/prompts/M6-P1303.json` | PASS | false | `04-artifacts/impl/M6.2D/tests/TEST_MANIFEST.md` |
| M6-P1304 | TESTER | M6_2D_TESTER_RUN | PASS | `04-artifacts/evidence/prompts/M6-P1304.json` | PASS | false | `04-artifacts/test-reports/M6.2D/SMOKE_RESULTS.md` |
| M6-P1305 | BOUNDARY_ADVERSARY | M6_2D_BOUNDARY_ADVERSARY | PASS | `04-artifacts/evidence/prompts/M6-P1305.json` | PASS | false | `04-artifacts/boundary-reports/M6.2D_boundary.md` |
| M6-P1306 | SECURITY_PII | M6_2D_SECURITY_REVIEW | **SKIPPED** (owner deferral) | `04-artifacts/evidence/prompts/M6-P1306.json` | **BLOCKED** (on M6-OD-003) | false | `04-artifacts/security-reports/M6.2D_security.md` |
| **M6-P1307** | PM_ORCHESTRATOR | M6_2D_EVIDENCE_COLLECT | **RUNNING** | `04-artifacts/evidence/prompts/M6-P1307.json` | (this index) | false | `04-artifacts/evidence/prompts/M6_2D_EVIDENCE_INDEX.md` |
| M6-P1308 | ANALYST_ARCHITECT | M6_2D_DOCS | **TODO** | — (not produced) | — | — | `04-artifacts/analysis/slices/M6_2D_RUNBOOK.md` (pending) |
| M6-P1309 | JUDGE | M6_2D_SLICE_GATE_JUDGE | **TODO** | — (not produced) | — | — | `04-artifacts/evidence/judge/M6-P1309_JUDGE_FINAL_SIGN_OFF.json` (pending) |

All seven band evidence JSONs (M6-P1300 … M6-P1306) exist, are schema-valid, and declare `fail_gate_tripped=false`.
Six self-report PASS; **M6-P1306 self-reports BLOCKED** (on the OPEN in-scope owner decision M6-OD-003 — a clean
scan, no leak, no tripped fail gate) and its ledger row is **SKIPPED** via the owner deferral `M6-DEFER-OD003-M6.2D`.
This prompt's own `M6-P1307.json` is produced at completion (written **last**, after this index — pack hard-rule 2).

---

## 2. Artifact inventory (existence verified on disk)

### 2.1 Implementation (staged, `04-artifacts/impl/M6.2D/`)
- `PLAN.md` — minimal staged change set + master traceability + per-item rollback.
- `IMPLEMENTATION_NOTES.md` — realized plan + deltas (incl. §4.3, the flagged measurement-path F-D); §7 rollback.
- Carried-forward M6.2C tree + fix-first patches (`consent/gate.py` F-B, `outbox/enqueue.py` + `outbox/audience_dispatcher.py`
  F-C, both dispatchers F-A) + new **integration layer**: `integration/hash_policy.py` (fail-closed hash mechanism,
  empty raw allow-list), `integration/payload.py` (PII-safe payload + shared platform `event_id`),
  `integration/result_log.py` (PII-safe PlatformResultLog), `integration/platform_transport.py`
  (StagedPlatformTransport — builds + logs then raises `ExternalSendBlocked`, never sends), `config.py`
  (+`MEASUREMENT_HASH_ALGO=sha256`, +`HASH_POLICY_RATIFIED=False` fail-closed marker).
- **No new migration** (M6.2D is a send-discipline layer over CTR-008; the result log is a staged in-memory store).

### 2.2 Tests
- Manifest: `04-artifacts/impl/M6.2D/tests/TEST_MANIFEST.md`.
- Bound smoke: `tests/smoke/test_smk_003_platform_dedup.py` (4), `tests/smoke/test_smk_017_hash_policy_no_raw_pii.py` (12).
- Leg-supporting: `tests/test_platform_dedup_event_id.py` (L1), `tests/test_hash_policy_no_raw_pii.py` (L2),
  `tests/test_offline_after_order_verified.py`, `tests/test_staged_no_real_send.py`,
  `tests/test_m6_2d_fixfirst_regressions.py` (F-A/F-B/F-C) + carried-forward suites.
- Full staged suite **201 passed / 0 failed** (185 carried-forward + 16 new smoke nodes).

### 2.3 Reports
- Test report: `04-artifacts/test-reports/M6.2D/SMOKE_RESULTS.md` (SMK-003 4/4, SMK-017 12/12, L1/L2 supporting 10/10).
- Boundary report: `04-artifacts/boundary-reports/M6.2D_boundary.md`.
- Security/PII report: `04-artifacts/security-reports/M6.2D_security.md` (verdict BLOCKED on M6-OD-003; scan clean).
- Entry-gate Judge sign-off: `04-artifacts/evidence/judge/M6-P1300_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS).

---

## 3. Contract checklist (from the slice spec)

| Contract | Shape | Ownership | Status (canon) | Harmonization |
|---|---|---|---|---|
| M6-CTR-008 | marketing_measurement_outbox | M6 (worker only) | MISSING / OWNER_DECISION_REQUIRED | M6-P0705 (PASS); gate M6-P0715 SIGNED |

`MISSING / OWNER_DECISION_REQUIRED` in the CONTRACT_REGISTER but **satisfied-for-entry** per the slice checklist
(harmonization producer PASS, gate SIGNED, staged schema present). The canon-flip is deferred, non-blocking
operator housekeeping.

---

## 4. Exit-gate checklist → evidence map

Legend: **MET** = evidence present and sufficient at the staged level · **SUPPORTED (staged)** = the bound suites
pass and the boundary adversary executed the check, but the tester withheld leg-*closure* ("supported") and
residuals remain · **PARTIAL** = capability proven but a policy-conformance half is deferred on an OPEN owner
decision · **PENDING** = the producing prompt has not run yet. Caveats are carry-forwards (see §5); none trips an
in-scope fail gate (M6-FAIL-001/002/008 — all held).

| # | Exit-gate check (slice spec) | Verdict | Evidence refs | Notes / caveats |
|---|---|---|---|---|
| 1 | **No double count** — duplicate Pixel/CAPI/Offline collapse via the locked dedup_key; platform result logs prove single delivery | **SUPPORTED (staged)** | `04-artifacts/test-reports/M6.2D/SMOKE_RESULTS.md` (SMK-003 4/4) + `tests/test_platform_dedup_event_id.py` (4/4) + `tests/test_offline_after_order_verified.py` (2/2); `app/measurement/integration/payload.py` (shared `event_id`), `integration/result_log.py`; boundary `M6.2D_boundary.md` (FAIL-001 not tripped) | RULE-005/003. Tester (M6-P1304) calls leg **L1 "supported"**. Shared `event_id=hash(source_event_id+event_code)` collapses Pixel/CAPI/Offline of one source event. Caveats B3-F-E (unescaped `event_id` join, non-injective — under-count, not FAIL-001) + O-2 (`event_id` excludes customer → under-count DQ). Final L1 closure is the slice-gate Judge's call. |
| 2 | **No PII thô** — no raw PII in any external payload or platform result log; **hash policy per M6-OD-003 applied (BLOCKED on that decision where unresolved)** | **PARTIAL — mechanism MET, policy conformance BLOCKED/DEFERRED on M6-OD-003** | `SMOKE_RESULTS.md` (SMK-017 12/12) + `tests/test_hash_policy_no_raw_pii.py` (3/3); `app/measurement/integration/hash_policy.py` (empty raw allow-list, `HASH_POLICY_RATIFIED=False`), `payload.py`, `result_log.py`; `04-artifacts/security-reports/M6.2D_security.md` | RULE-014; guards M6-FAIL-008 (NOT tripped). **Mechanism proven** (doubly fail-closed: nothing raw formed or emitted; scan clean over 101 files). **Conformance uncertifiable** while M6-OD-003 (permitted-send fields + hashing approach incl. salt/pepper O-1 + normalization) is OPEN — this is the slice-designed exit checkpoint. **M6-P1306 (security) returned BLOCKED here**; ledger SKIPPED it via owner deferral `M6-DEFER-OD003-M6.2D` (OD-003 → forward gate at M6.2G). See §5 B2. |
| 3 | **Smoke M6-SMK-003 executed** with recorded result + evidence ref | **MET** | `04-artifacts/test-reports/M6.2D/SMOKE_RESULTS.md` (4/4, exit 0); `04-artifacts/evidence/prompts/M6-P1304.json` | No double count proven via the shared platform `event_id` end-to-end. |
| 4 | **Proposed smoke M6-SMK-017 executed OR explicitly waived** by owner decision note | **MET** | `04-artifacts/test-reports/M6.2D/SMOKE_RESULTS.md` (12/12, exit 0); `04-artifacts/evidence/prompts/M6-P1304.json` | **Executed, not waived**: every identity field hashed (`h_` prefix), no raw PII in payload or result log, across 3 PII shapes × 3 platforms + fail-closed check. |
| 5 | **All slice prompts have evidence JSON** (schema-valid, no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | `04-artifacts/evidence/prompts/M6-P1300.json` … `M6-P1306.json` present (7); `M6-P1307.json` produced at this prompt's completion | **Not yet complete:** M6-P1308 (Docs) and M6-P1309 (Judge) evidence not produced (both TODO). Note: M6-P1306 is present + schema-valid + `fail_gate_tripped=false`, but self-reports **BLOCKED** (ledger SKIPPED via owner deferral) — the Judge should weigh that when assessing this leg. |
| 6 | **Slice-gate Judge sign-off exists with verdict PASS** | **PENDING (not met)** | — | `04-artifacts/evidence/judge/M6-P1309_JUDGE_FINAL_SIGN_OFF.json` does **not** exist; M6-P1309 is TODO. (The existing `M6-P1300_JUDGE_FINAL_SIGN_OFF.json` is the *entry* gate, verdict PASS — not the slice gate.) |
| 7 | **Rollback steps documented** for every change this slice made | **MET** | `04-artifacts/impl/M6.2D/PLAN.md` (per-item Rollback) + `IMPLEMENTATION_NOTES.md` §7 (new files → delete; 5 patched carried-forward files → revert to M6.2C version) | All changes staged ⇒ non-destructive; **no new table → no down-DDL** (the result log is a staged in-memory store). |

**Summary:** items **3, 4 and 7 are MET** (SMK-017 executed, not waived); item **1 is SUPPORTED at the staged
level**; item **2 is PARTIAL** — the no-raw-PII *mechanism* is met (FAIL-008 not tripped) but *hash-policy
conformance* is the designed **BLOCKED-on-M6-OD-003** checkpoint (M6-P1306 BLOCKED, ledger-SKIPPED via owner
deferral); items **5 and 6 are PENDING** (M6-P1308 docs, then M6-P1309 slice-gate Judge). Coverage: **every
exit-gate checklist item is indexed** (acceptance check 1).

### 4.1 Smoke register bindings

| Smoke ID | Doc ID | Scenario (verbatim) | Expected (verbatim) | Result | Evidence |
|---|---|---|---|---|---|
| M6-SMK-003 | ADS-P0-003 | `Duplicate Pixel/CAPI/Offline` | `Dedup, không double count` | **PASS 4/4** | `SMOKE_RESULTS.md`, `M6-P1304.json` |
| M6-SMK-017 | proposed (HARDENING) | `External payload (CAPI/Offline) built from an event containing raw PII` | `Hash policy applied per M6-OD-003; no raw phone/email/user-id in the outbound payload or platform result log` | **PASS 12/12** (executed, not waived) | `SMOKE_RESULTS.md`, `M6-P1304.json` |

---

## 5. Unresolved blockers / carry-forwards (acceptance check 2)

None of the following is an open blocker of the **evidence-collection** task itself (all seven inputs present, all
artifacts on disk, index complete), and none trips an in-scope fail gate (M6-FAIL-001/002/008 — all held). Each was
already adjudicated by the responsible upstream prompt and is carried forward as governance context for the
slice-gate Judge (M6-P1309) and the owner. **B2 and B5 are the load-bearing items for this slice.**

- **B1 — Slice exit gate is not complete (expected at this step).** Item 5 pending M6-P1308/M6-P1309 evidence;
  item 6 pending the M6-P1309 slice-gate Judge PASS sign-off.

- **B2 — Exit-gate leg 2 hash-policy CONFORMANCE is BLOCKED on M6-OD-003 (the designed M6.2D-exit checkpoint).**
  The hash *mechanism* is proven (SMK-017 12/12; doubly fail-closed — `HASH_POLICY_RATIFIED=False` + empty raw
  allow-list; nothing raw formed or emitted; the PlatformResultLog stores no `user_data`; scan clean over 101
  files; FAIL-008 not tripped). But *conformance* cannot be certified because **M6-OD-003** — which identity fields
  may be sent to Pixel/CAPI/Offline, the hashing approach incl. **salt/pepper (O-1: the code uses unsalted sha256,
  the Meta CAPI standard)**, and normalization — is **OPEN** (privacy/legal). The security review **M6-P1306
  self-reported BLOCKED** on precisely this (not a leak, no fail gate tripped); the ledger marked M6-P1306
  **SKIPPED** via owner deferral **`M6-DEFER-OD003-M6.2D`** (note: `scan-clean; no-send; OD003-forward-gate-M6.2G`).
  The interim staged posture is the correct fail-closed default. **M6-OD-003 (+ the O-1 salt/normalization
  sub-question) must be resolved by privacy/legal before the M6.2D exit can certify conformance and before any real
  external send.** *Ref:* `04-artifacts/security-reports/M6.2D_security.md`, `04-artifacts/evidence/prompts/M6-P1306.json`.

- **B3 — CODER consent / robustness residuals (armed-not-fired; none trips an in-scope fail gate; routed to CODER).**
  - **F-D [MINOR, consent fail-OPEN — the measurement-path twin of F-C, REACHABLE from the untrusted conversions
    body]:** the measurement path never binds the conversion's `customer_or_guest_key` to the consent snapshot's
    `subject_ref` (the endpoint pairs both from the untrusted body; `permits_send` checks only the snapshot's own
    subject), so a conversion for subject X citing subject Y's VALID consent builds a payload on **borrowed
    consent**. The audience F-C fix was **not** applied to the symmetric measurement path. Both M6-P1305 and
    M6-P1306 confirmed OPEN; the coder flagged it (IMPLEMENTATION_NOTES §4.3) and **committed to fix it fix-first at
    M6.2E**. Armed-not-fired only because `StagedPlatformTransport` blocks the real send. **Must close before
    `external_send` can flip.**
  - **F-E [MINOR, latent]:** `payload.py` joins `source_event_id`+`event_code` for the platform `event_id`
    **unescaped** (non-injective — the M6.2A MAJOR-5 class); not endpoint-reachable (event_code registry-constrained);
    a collision is an under-count, not FAIL-001. Escape/canonicalize like the outbox `_hash_key`.
  - **F-F [MINOR, latent]:** `getattr(snap,'subject_ref',None)` at `measurement_dispatcher.py:82` runs *before* the
    F-A try/except and only swallows `AttributeError`, so a snapshot whose `subject_ref` property *raises* crashes
    `run_once` (residual F-A nick); needs a hostile consent adapter. Wrap it.
  - Observations: **O-1** (unsalted sha256 — an M6-OD-003 sub-question, see B2), **O-2/O-4** (DQ: `event_id`
    excludes the customer → under-count; staged held items re-drain each run appending unbounded BLOCKED
    result-log records — PII-safe) → M6.2F.
  - *Ref:* `04-artifacts/boundary-reports/M6.2D_boundary.md`, `04-artifacts/security-reports/M6.2D_security.md`.

- **B4 — Fix-first F-A/F-B/F-C CLOSED (positive).** The M6.2C consent fail-OPEN residuals bound by the entry gate
  were closed fix-first and **executed-verified by both M6-P1305 and M6-P1306**: F-B (`scope in
  frozenset(snapshot.consent_scope)` — completes the M6.2B/F2 fix), F-C (audience `member_key ↔ subject_ref`
  binding), F-A (`permits_send`/`current_state` wrapped fail-closed in both dispatchers). The newly-found **F-D**
  (symmetric measurement-path analogue) remains open → M6.2E (B3).

- **B5 — Governance / traceability gaps (process — for the operator/owner; NOT a collection blocker).**
  - The ledger SKIP of **M6-P1306** cites `SKIP_APPROVED:M6-DEFER-OD003-M6.2D`, but **no decision file
    `M6-DEFER-OD003-M6.2D.json` exists** in `04-artifacts/evidence/decisions/` (that directory holds only
    `M6-OD-011.json`, `M6-OVERRIDE-M6P1000-STAGED.json`, `M6-DEFER-F1F2-M6.2B.json`). The deferral is recorded only
    in the ledger Note; the backing decision artifact is missing.
  - **`M6-DEFER-FBC-M6.2D.json`** — recommended by **both** M6-P1209 and M6-P1300 to bind F-B/F-C/F-A (and now F-D)
    into the M6.2G gate (M6-P1600) RequiredInputs so a real send can never be enabled with an open consent fail-open
    — was **never created**. The binding is in force via the sign-offs and F-A/B/C were closed anyway, but the
    decision file + the M6-P1600 RequiredInputs wiring remain an operator/owner TODO (F-D is still open).

- **B6 — Contract housekeeping (non-blocking).** M6-CTR-008 is `MISSING / OWNER_DECISION_REQUIRED` in canon but
  satisfied-for-entry (producer M6-P0705 PASS, gate M6-P0715 SIGNED). The canon-flip is deferred operator housekeeping.

- **B7 — Inherited cross-slice carry-forwards (still in force).** ENTRY-001 (P3 verified-revenue) and ENTRY-003
  (event_registry gaps; Platform/P0-06-owned) remain **risk-accepted** under `M6-OVERRIDE-M6P1000-STAGED` (M6-P1000
  verdict stays **BLOCKED**, not converted), bound to M6.2A entry + the **mandatory M6.2G Scale-Gate re-gate**. Open
  owner decisions: **M6-OD-003** (hash — the live leg-2 blocker, B2), **M6-OD-004** (connector — no real transport
  exists), **M6-OD-008** (revenue — offline only after ORDER_VERIFIED is the fail-closed default), **M6-OD-012**
  (masking format). Forward at the M6-OD-011 / M6-OD-004 binding: request authN/authZ on the endpoints + worker
  service-account scoping for the two dispatchers; real connector tokens **secret_ref-only**.

- **B8 — Immutable governance posture.** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
  `HASH_POLICY_RATIFIED=False` unchanged; no real platform send occurs (StagedPlatformTransport builds+logs then
  blocks; no connector). The **mandatory M6.2G Scale-Gate re-gate** stands before any real scale or external send.

---

## 6. Reader's guide for the slice-gate Judge (M6-P1309)

1. Start from `00-spec/slices/M6.2D.md` "Exit gate checks" (the 7 items in §4 above).
2. For legs 1, 3, 4, 7, read the reports/evidence in the §4 "Evidence refs" cells directly (do not rely on this index).
3. **Leg 2 is the crux:** decide whether the slice may exit with the hash *mechanism* proven while *conformance*
   is deferred on M6-OD-003 — weigh `04-artifacts/evidence/prompts/M6-P1306.json` (BLOCKED), the ledger SKIP note,
   and the **missing `M6-DEFER-OD003-M6.2D.json` decision file** (§5 B5). Per the slice spec, leg 2 is explicitly
   "BLOCKED on that decision where unresolved".
4. Confirm items 5 & 6 by re-reading the ledger and `04-artifacts/evidence/judge/` (M6-P1309 sign-off is the Judge's own output).
5. Verify **F-A/F-B/F-C closure** (executed-confirmed by M6-P1305/M6-P1306) **and** that **F-D** (the reachable
   measurement-path borrowed-consent) is bound to close before `external_send` can ever flip — and consider whether
   `M6-DEFER-FBC-M6.2D.json` should be formalized now (§5 B5).

*This index is descriptive. It advances no gate and self-certifies nothing; the runner EVIDENCE_GATE and the
slice-gate Judge decide closure.*
