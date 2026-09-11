# M6.2R Evidence Index — Recall-risk mapper: ops-core availability → Scale-Gate risk_flags (E2 §3/§5)

| Field | Value |
|---|---|
| Prompt | **M6-P2607** — `M6_2R_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, `analysis_only`) |
| Slice | **M6.2R** — the M6-side recall-risk mapper (chief E2 §3/§5, M6-OD-017): map an ops-core `/v1/availability/check` response (a value object / dict — **NOT a live HTTP call**) → three ops-core-sourced `risk_flags` (`recall`, `sale_lock`, `quality_hold`) that feed the **EXISTING** Scale Gate (**no gate-logic change**). Cumulative superset of M6.2Q. STAGED — mock response in tests; the live HTTP client is the S1b seam (ops-core account live, gated on secret handover). |
| Depends on | M6.2Q (entry judge M6-P2600 chains to the M6.2Q slice judge M6-P2509 SIGNED) |
| Purpose | Map every band evidence file / artifact / test / boundary / security report to the 7 exit-gate legs; list unresolved blockers — a reader's map for the slice-gate Judge (**M6-P2609**) |
| Collection verdict | **complete** — all 7 band prompts (M6-P2600…2606) PASS with `fail_gate_tripped=false`; the two downstream prompts (docs M6-P2608, judge M6-P2609) are the only PENDING exit items |
| Governance | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — immutable, untouched; `config.py` + `scale/conditions.py` + `scale/scale_gate.py` **byte-identical to M6.2Q** (no gate change). `M6-P1000` + `M6-P1309` verdicts remain **BLOCKED** (not converted). Owner decision consumed: **M6-OD-017** (recall-risk consumer, DECIDED 2026-09-10). |

> **This is a collection artifact, not a verdict.** Its own `status=PASS` / `open_blockers=[]` means the assembly task is
> complete and unblocked — it does **not** assert the slice passes. Slice-level unresolved items live in **§5**.

> ### ⚠ Three honesty points for the recall/scale leg (read before §4)
> This slice proves a recall-risk **mapper mechanism** — it does **not** make recall risk gate scale *live*:
> 1. **The mapper is UNWIRED (N8/CRIT-05).** No `app/` module imports `recall_risk_mapper` — only tests do (grep-confirmed
>    by boundary + security). Its fail-closed defenses (collapse-to-`{}`, `risk_picture_complete`) are **dormant in the
>    shipped path**. M6.2R proves the mapper *mechanism*; a future caller must be forced to route ScaleContext.risk_flags
>    through `recall_risk_contribution` + `risk_picture_complete`. The sign-off must **not** over-attribute live recall
>    safety to the unwired mapper.
> 2. **The real (and fragile) live containment is the structural overall-HOLD floor (N1/CRIT-01) + the executor absence.**
>    `is_scale_authorized` is *structurally* unreachable — `_funnel`/`_dashboard` have **no PASS branch** (verified to hold
>    even with both config floors `SCALE_MODEL_RATIFIED`/`DASHBOARD_ALERT_THRESHOLDS_DEFINED` monkeypatched True), and no
>    executor verb exists — so no scale can be authorized while M6-OD-002/005 are OPEN. **But** if a future slice adds a
>    PASS branch to `_funnel`/`_dashboard`, every armed-not-fired residual below becomes a live FAIL-006 breach at once →
>    lock the structural HOLD floor with a regression test.
> 3. **A pre-existing `conditions._risk` partial-map false-clear (G4/N2) — routed to owner.** The gate PASSes a non-empty
>    no-active `risk_flags` map without requiring all 6 RISK_LOCKS present; the approval-time all-6 guard tests key
>    *presence* not *bool-ness*. Pre-existing (NOT introduced by M6.2R); this slice avoids triggering it (the mapper's
>    contribution is fail-closed by construction) and the HOLD floor contains it — but it is a real gate limitation the
>    owner must close before any live scale clear (no gate change here — M6-OD-017 no-gate-change scope, RULE-018).
>
> What IS proven and clean: the mapper is fail-closed (strict-bool, incomplete→`{}`, booleans-only, no fabricated lock,
> RULE-018), a present lock forces the Risk row FAIL even when `decision=SELLABLE` (RULE-017 veto, owner APPROVE refused),
> posture is BLOCKED/OFF/OFF, no live HTTP/egress, no gate change, PII/secret-clean. The exit judge M6-P2609 confirms no
> flag flip / no live HTTP / no gate change / posture OFF-BLOCKED-OFF.

---

## 1. Band evidence (the M6.2R prompt chain — 7 of 10 prompts run)

| Prompt | Role | Evidence | Ledger | fail_gate | open_blockers | One-line result |
|---|---|---|---|---|---|---|
| **M6-P2600** | JUDGE (entry) | [M6-P2600.json](M6-P2600.json) | **SIGNED** | false | 0 | Entry gate PASS — verified DECIDED+FILED M6-OD-017 authorizes the mapper; CTR-026 MISSING but harmonization M6-P0709 PASS (+M6-P0715 SIGNED) → resolved-for-entry; M6-OD-002 OPEN = forward |
| **M6-P2601** | CODER (plan) | [M6-P2601.json](M6-P2601.json) | PASS | false | 0 | Plan: pure mapper + fail-closed + ScaleContext.risk_flags wiring, no gate change; red-team caught 1 MAJOR (a bare 3-of-6 clean map would false-clear the gate's partial-map PASS) → redefined the contribution as a partial merge; surfaced the gate limitation to the owner |
| **M6-P2602** | CODER (implement) | [M6-P2602.json](M6-P2602.json) | PASS | false | 0 | Built 2 new files (`recall_risk_mapper.py` + test); **647 passed** (631 carried M6.2Q + 16); self-review fixed 1 MAJOR (contribution now fail-closed by construction) + 1 MINOR (strict-bool choke centralized); conditions.py/scale_gate.py/config.py byte-identical |
| **M6-P2603** | TESTER (build) | [M6-P2603.json](M6-P2603.json) | PASS | false | 0 | Authored official SMK-030 (11 nodes; scenario iii parametrized ×5), scenario verbatim (U+2192 glyph-exact); collect **658**; static verification 3/3 all-CLEAN; NOT executed |
| **M6-P2604** | TESTER (run) | [M6-P2604.json](M6-P2604.json) | PASS | false | 0 | Executed: **SMK-030 PASS 11/11**, correlation_id + evidence_id recorded (masked); full staged suite **658 passed / 0 failed**, rc 0; proposed 030 **executed**; traceability note (register "gate FAIL" leg-iii = asserted Risk HOLD + approve refused) |
| **M6-P2605** | BOUNDARY_ADVERSARY | [M6-P2605.json](M6-P2605.json) | PASS | false | 0 | 42 executed outcomes (36 DEFENDED / 4 OPEN-non-gate / 2 note); **0** in-scope FAIL-006 breaches; mapper fail-closed + RULE-017 veto + **is_scale_authorized structurally unreachable (crown jewel)** verified; residuals G4/N2 (gate partial-map), N8 (unwired), N1 (structural floor), N5 (decision export) |
| **M6-P2606** | SECURITY_PII | [M6-P2606.json](M6-P2606.json) | PASS | false | 0 | Scan **277 files** — 0 raw PII, 0 real secrets (incl. **0 client_secret**; recall flags are product-level, not PII; no ops-core token — live client not built); mapper PII-safe/no-HTTP/no-secret; F-SEC-2R-1 (OwnerDecision export → M6-OD-012, twin of M6.2Q MC-09); honest unwired note |
| M6-P2607 | PM_ORCHESTRATOR | *this collection* | RUNNING | false | 0 | This index + evidence JSON |
| M6-P2608 | ANALYST_ARCHITECT (docs) | — | **TODO** | — | — | Runbook — not yet run (exit item 5) |
| M6-P2609 | JUDGE (slice gate) | — | **TODO** | — | — | Slice-gate sign-off — not yet run (exit item 6); confirms no flag flip / no live HTTP / no gate change |

**All 7 completed band prompts are PASS with `open_blockers=[]`, `fail_gate_tripped=false`, and no `findings`/`test_results`
integrity keys asserting a tripped gate.** The entry judge (M6-P2600, ledger row 250) is **SIGNED**.

## 2. Artifact inventory (every file the band produced)

**Owner authorization this slice consumes (verified on disk):** [`M6-OD-017.json`](../decisions/M6-OD-017.json) (recall-risk consumer, DECIDED 2026-09-10 owner+tech-lead: pull-path mapper, read presence booleans only, presence-flag → FAIL even SELLABLE, pull error → fail-closed, FAIL gate only + no auto-pause, STAGED live-HTTP-out, no flag flip).

**Staged implementation — `04-artifacts/impl/M6.2R/`** (carried M6.2Q byte-identical [244 .py + 16 .sql], then added 2 new files — no carried file edited):
- `PLAN.md` (M6-P2601) · `IMPLEMENTATION_NOTES.md` (M6-P2602)
- **`app/measurement/scale/recall_risk_mapper.py`** — `OpsCoreAvailabilityResponse` value object (presence booleans + additive `recall_case_open`; `decision`/`block_reasons`/`sku_ref` recorded but **never read**; `from_mapping`), `RecallRiskRead`, `RECALL_RISK_KEYS` (strict subset of `conditions.RISK_LOCKS` + import-time drift guard), `map_risk_flags` (recall = recall_hold OR recall_case_open; the single strict-bool choke → non-bool/None/missing → INCOMPLETE), `map_pull_outcome` (S1b seam success/timeout/429/connection-error, **no HTTP**), `risk_picture_complete` (caller-side all-6 predicate), `recall_risk_contribution` (**fail-closed by construction** — active lock → returned; complete 6-lock clean → returned; incomplete/bare-clean → `{}` → gate HOLD)
- **`tests/test_m6_2r_recall_risk_mapper.py`** (16 coder cases) + official smoke `tests/smoke/test_smk_030_recall_risk_mapper_to_scale_gate.py` (11 nodes) + `tests/TEST_MANIFEST.md`. **No migration** (0001–0016 unchanged); **no config flag**; **no gate change**.

**Test report — `04-artifacts/test-reports/M6.2R/`:** [`SMOKE_RESULTS.md`](../../test-reports/M6.2R/SMOKE_RESULTS.md) (M6-P2604)

**Boundary — `04-artifacts/boundary-reports/`:** [`M6.2R_boundary.md`](../../boundary-reports/M6.2R_boundary.md) (M6-P2605); harness `04-boundary/work/attacks/m6_2r_attacks.py`

**Security — `04-artifacts/security-reports/`:** [`M6.2R_security.md`](../../security-reports/M6.2R_security.md) (M6-P2606); scanner `06-security/work/pii_scan_2r.py`

**Entry-judge sign-off — `04-artifacts/evidence/judge/`:** `M6-P2600_JUDGE_FINAL_SIGN_OFF.json` (PASS)

**Test-count reconciliation (count discipline):** **658** full staged suite = **631** carried (M6.2Q) **+ 16** coder M6.2R regressions (→ 647 baseline) **+ 11** official-smoke nodes (tester, SMK-030 = 7 functions with scenario-iii parametrized ×5). Baseline before any patch was 631 (byte-parity with M6.2Q). All green, 0 failed / 0 skipped / 0 error, rc 0; the isolated 1-leg run independently confirms **11 passed**.

## 3. Contract checklist (CONTRACT_REGISTER)

| Contract | Status | This slice | Resolution |
|---|---|---|---|
| **M6-CTR-026** `Scale Gate approval flow` | **MISSING / OWNER_DECISION_REQUIRED** (thresholds = M6-OD-002) | the mapper feeds this gate's Risk row | Not a blocker: the harmonization prompt **M6-P0709 (CONTRACT_SCALE_REQUEST) is PASS** (+ harmonization gate M6-P0715 SIGNED), so resolved-for-entry (entry judge M6-P2600 verified on the real ledger). The M6-OD-002 thresholds inside CTR-026 stay OPEN but gate the Scale Gate, not this mapper (which feeds risk_flags in the FAIL/HOLD direction). → **resolved-for-entry.** |

No new contract is introduced (a pure mapper + no gate change; no new table — migrations `0001–0016` unchanged).

## 4. Exit-gate checklist → evidence map (all 7 legs of `slices/M6.2R.md`)

| # | Exit-gate item | Status | Evidence |
|---|---|---|---|
| 1 | **E2 mapping (M6-OD-017)** — `risk_flags['recall'] = recall_hold OR recall_case_open`, `sale_lock`, `quality_hold`; recall_case_open additive (absent → false); no other lock fabricated; reads presence booleans only, never decision/block_reasons | **MET** | SMK-030 scenario i/ii + `test_smk_030_neg_mapper_never_reads_decision_or_block_reasons` + control + `test_m6_2r_recall_risk_mapper.py` green; booleans-only, additive OR, strict 3-of-6 subset. *(Mechanism proven; the mapper is UNWIRED — §5 N8.)* |
| 2 | **presence-flag FAIL even when SELLABLE** — any of recall_hold/sale_lock/quality_hold/recall_case_open true → the existing Scale-Gate Risk row FAILs even if decision==SELLABLE; test proves FAIL-despite-SELLABLE for recall_hold and recall_case_open | **MET** | SMK-030 scenario i (recall_hold) + ii (recall_case_open): Risk FAIL despite SELLABLE, owner APPROVE refused (`ScaleGateViolation`, RULE-017), request stays PROPOSED / not authorized. No gate-logic change. |
| 3 | **fail-closed on pull error** — pull error/timeout/429/None/absent → INCOMPLETE risk read → the Scale Gate's fail-closed re-check (RULE-017) does not clear → gate does not clear; the mapper never defaults an unknown flag to false-clear | **MET** | SMK-030 scenario iii (×5: TIMEOUT/HTTP_429/CONNECTION_ERROR/None/malformed) + non-bool neg: INCOMPLETE → empty read → Risk **HOLD** + approve refused (does-not-clear). **Traceability note:** the register phrases leg-iii as "gate FAIL"; the honest assertion is Risk HOLD + refused approve (the fail-closed *does-not-clear* half, matching `conditions._risk` empty→HOLD and sibling SMK-009) — non-blocking, flagged by tester + boundary. |
| 4 | Proposed smoke **M6-SMK-030** executed OR owner-waived | **MET** | PASS 11/11 — **executed** (not waived) ([SMOKE_RESULTS.md](../../test-reports/M6.2R/SMOKE_RESULTS.md) · [M6-P2604.json](M6-P2604.json)) |
| 5 | All slice prompts have schema-valid evidence (no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | M6-P2600…2606 present + PASS + clean; M6-P2607 (this) completing; **M6-P2608 (docs) TODO, M6-P2609 (judge) TODO** |
| 6 | Slice-gate judge sign-off exists with verdict PASS | **PENDING** | **M6-P2609 TODO**. The slice-gate Judge reads this index + confirms no flag flip / no live HTTP / no gate change |
| 7 | Rollback documented for every change this slice made | **MET** | [IMPLEMENTATION_NOTES §6](../../impl/M6.2R/IMPLEMENTATION_NOTES.md): staged-only → delete the M6.2R tree (M6.2Q untouched); the 2 new files → delete; **no carried file edited** (no gate change, no migration) so nothing to scoped-revert |

**Summary:** MET = items 1–4 (mapper mechanism + SMK-030) + 7 (rollback) · PENDING = items 5, 6. No exit item is FAILED or BLOCKED. Items 1–3 prove the **mapper mechanism** (staged, fail-closed, feeds the existing gate in the FAIL/HOLD direction); they do **not** assert recall risk gates scale *live* — the mapper is unwired and the live containment is the structural floor (§5).

## 5. Unresolved blockers & carry-forwards

All residuals below are **armed-not-fired** in the staged posture. The reachability floor: recall/availability data is
product-level (recall/sale/quality booleans + a SKU/campaign ref — not customer PII); the mapper is a pure function over a
value object with **no HTTP/transport import** (the S1b live client is not built); `is_scale_authorized` is structurally
unreachable (the overall-HOLD floor, N1); and the mapper is **unwired** (N8). Both reviews self-reported
`fail_gate_tripped=false` (boundary 42 outcomes / 0 in-scope FAIL-006 breaches; security 277-file scan / 0 raw PII / 0 real
secrets incl. client_secret). This collection prompt's own `open_blockers` is therefore **empty** — but the items below are
hard forward conditions for the owner/CODER/judge.

**Primary owner forward — the Scale-Gate hardening (owner; no gate change here per M6-OD-017 / RULE-018):**

- **B1 — G4 + N2: `conditions._risk` partial-map / junk-falsy false-clear.** `conditions._risk` returns PASS for any non-empty no-active `risk_flags` map (checks emptiness only, **not** that all 6 RISK_LOCKS are present); and the approval-time all-6 completeness guard tests key **presence**, not bool-ness — so a full-6 **junk-falsy** map (`{lock:0}` for all six) also clears it. **Pre-existing** RULE-017 limitations, NOT introduced by M6.2R. Contained today by the structural overall-HOLD floor (N1) + the executor absence + the mapper's fail-closed-by-construction contribution (which this slice added, so the mapper never triggers it). **Owner action:** require all 6 RISK_LOCKS present **and** clean-bool for a `_risk`/approval clear, or force the Scale-Gate assembly to merge all lock sources + check `risk_picture_complete` before any clearing context. A live scale-authorization false-clear risk once M6-OD-002/005 ratify — the sharpest gate item.

**Scope-honesty + load-bearing invariants (for the judge):**

- **N8 / CRIT-05 — the mapper is UNWIRED.** No `app/` module imports `recall_risk_mapper` (only tests). Its collapse/completeness defenses are dormant in the shipped path; the LIVE FAIL-006 containment is the overall-HOLD floor + the executor absence, **not** the mapper. A future caller must be forced to route ScaleContext.risk_flags through `recall_risk_contribution` + `risk_picture_complete`.
- **N1 / CRIT-01 — the structural HOLD floor is the real, fragile containment.** `_funnel`/`_dashboard` have no PASS branch (verified even with both config floors monkeypatched True), so `is_scale_authorized` is structurally unreachable while M6-OD-002/005 are OPEN. If a future slice adds a PASS branch, every armed-not-fired residual becomes a live FAIL-006 breach at once → **lock the structural HOLD floor with a regression test** (owner/CODER).
- **N4 / CRIT-04 — `overall_status` is frozen at propose-time, never recomputed at approval.** A **distinct** containment-fragility from N1 (N1 = a future PASS branch in `_funnel`/`_dashboard`; N4 = a future approval-time recompute of `overall`): today the frozen-at-propose `overall` is safe (it cannot silently flip to PASS at approval), but any future "recompute overall at approval" refactor must be reviewed for FAIL-006 **before merge**. Same judge-facing "what future change could break FAIL-006 containment" set as N1 — flagged so that caution is complete, not just the PASS-branch case.

**Security (owner M6-OD-012 + CODER):**

- **B2 — F-SEC-2R-1 / N5: `OwnerDecision.to_public()` exports `reason`/`audit_ref`/`evidence_ref` verbatim.** Only the actor is masked; `reason`/`audit_ref` flow from the **untrusted admin body** (`handle_scale_decision` copies request fields into `OwnerDecision`), so a PII-shaped reason exports unmasked on the durable/export surface. **Carried** (the M6.2G scale `OwnerDecision`, byte-identical this slice) — re-surfaced because the recall work feeds the same gate. Now a **two-instance pattern** with the M6.2Q **MC-09** (`AdsSpendImportDecision.to_public` reason/audit_ref raw) → the decision-object-export masking-scope family, all → **M6-OD-012**. The **audit sink already drops** reason/audit_ref (machine-safe); `to_public` should mirror it, or run the free-text through the raw-PII tripwire at intake. Channel-reachable at the data-flow level but the durable-export surface is M6-OD-011-forward; PII-hygiene, not a scale path (armed-not-fired for FAIL-006). **Fix:** M6-OD-012 + CODER.

**CODER robustness (armed-not-fired; contained today):**

- **B3 — N3: `recall_risk_contribution` overwrites its own keys.** It unconditionally overwrites its 3 keys from the read, so a `base_flags` asserting `recall=True` is erased by a clean read; safe today by the docstring contract (base carries the *other* 3 keys) + the floor, no runtime guard. **Fix:** fail-closed if `base_flags` contains any `RECALL_RISK_KEYS`.
- **B4 — N9: `from_mapping` block_reasons parse.** `tuple(mapping.get('block_reasons') or ())` raises TypeError on a non-iterable truthy — fail-closed **loud** (a crash never false-clears), block_reasons is provenance-only. **Fix:** guard for parity with the strict-bool choke.
- **N6: malformed-sibling downgrade (observability).** A malformed sibling downgrades an active recall FAIL→HOLD rendered as "not checked" — fail-closed for FAIL-006, but an observability gap. **Fix:** distinguish malformed-with-active-lock from unobserved.

**Secret-handover forward (M6-OD-011 integration; verified clean now):**

- When the **S1b live client** to ops-core `POST /v1/availability/check` is built, its credential must be a **secret_ref** (never raw in code/evidence/log), and the M6.2O AST import-scan gate (no HTTP client in `app/`) will need its allow-list **deliberately** updated for the one egress client — an owner-controlled integration decision (M6-OD-011). Verified now: **no ops-core credential in code** (no HTTP client, no `client_secret` literal); the mapper takes a value object, not a live call.

**Standing cross-slice governance (carried forward):**

- **`M6-P1000` + `M6-P1309` verdicts remain BLOCKED** (not converted), carried inside the assembled pack.
- **Hard forward gates before any live recall pull / real scale / egress:** **M6-OD-002** (thresholds), **M6-OD-005** (attribution model), **M6-OD-011** (server-bind + go-live + ops-core secret handover + import-gate allow-list), **M6-OD-012** (masking scope — B2 + the carried family), **M6-OD-003** (psid pepper + privacy/legal — carried), plus the **S1b live-HTTP client** + the **campaign→SKU join** + the **M3 block_reason vocabulary / pause-SLA**. M6-OD-017 (recall-risk consumer) is DECIDED.
- **Carried residuals (unaffected by this slice — these are the *carried* findings, distinct from this slice's local labels B1 [=G4+N2] and N1 [=structural HOLD floor]):** the M6.2Q **MC-09** (twin of B2) + the M6.2Q **ROAS-provenance** finding (F-SEC-2I-1: spend authenticated / revenue un-provenanced) + the maker-checker identity binding; the F-SEC-2K-1/2M-1 masking family + F-EVID-4/5/6; **psid_hash real-pepper + privacy/legal (M6-OD-003)** — all disclosed in their standing blockers.
- **Operator hygiene (non-blocking, carried):** register **M6-OD-013 + M6-OD-014** and the M5 `PSID_HASH_POLICY_M5_TMP` dependency as `DECISION_REGISTER.md` rows; reconcile the stale ENTRY-004 row and the `CONTRACT_EVENT_REGISTRY.contract.yaml` line-137 note. None gates this slice.

**What this slice PROVED / IMPROVED (worth the Judge's note):**

- **The mapper is fail-closed by construction** — strict-bool choke (non-bool/None/missing → INCOMPLETE, never coerced-to-clear), incomplete/bare-clean → `{}` (never a partial clearing map), reads presence booleans only (never decision/block_reasons → no fabricated lock, RULE-018), owns a strict 3-of-6 subset.
- **The RULE-017 veto holds** — a present recall/sale/quality lock forces the existing Scale-Gate Risk row FAIL even when `decision=SELLABLE`, owner APPROVE refused.
- **The FAIL-006 crown jewel** — `is_scale_authorized` is *structurally* unreachable (no PASS branch even with both config floors flipped) and there is no executor verb, so no scale can be authorized in this posture; **no gate change** (conditions.py/scale_gate.py/config.py byte-identical); no live HTTP client; no ops-core secret; PII/secret-clean over 277 files.

## 6. Reader's guide for the slice-gate Judge (M6-P2609)

1. **Read order:** this index → the 7 band JSONs (§1) → the owner authorization (`M6-OD-017.json`) → the two review reports (`M6.2R_boundary.md`, `M6.2R_security.md`) → `SMOKE_RESULTS.md` → `IMPLEMENTATION_NOTES.md` (rollback + §4 gate-hardening finding). The exit-gate map is **§4**; the residuals are **§5**.
2. **What is proven (executed + verified):** the recall-risk mapper mechanism holds — booleans-only fail-closed mapping (INCOMPLETE on any non-bool/error read), a present lock → Risk FAIL even SELLABLE (RULE-017 veto, approve refused), a pull error → gate does-not-clear (HOLD). Full staged suite **658 passed / 0 failed**; SMK-030 **11/11**; boundary **0** in-scope FAIL-006 breaches with `is_scale_authorized` structurally unreachable; security **0** raw PII / 0 real secrets (incl. client_secret) across 277 files; conditions.py/scale_gate.py/config.py byte-identical (no gate change).
3. **The three things to weigh hardest (do not over-read the green):** **N8** — the mapper is **unwired** (dormant), so this proves a mechanism, not live recall-gating; **N1** — the real live containment is the structural HOLD floor + no-executor, which flips fragile if a future PASS branch is added (lock it with a regression); **B1 (G4/N2)** — the pre-existing `conditions._risk` partial/junk-falsy false-clear the owner must close before any live scale clear. Plus **B2** (decision free-text export → M6-OD-012, twin of M6.2Q MC-09).
4. **What is NOT yet closed:** exit items **5 & 6** are PENDING purely because the docs prompt (M6-P2608) and this judge (M6-P2609) have not run. Legs 1–4 + 7 are MET (mapper mechanism, staged).
5. **Boundary integrity of this collection:** this prompt is `analysis_only` — it read the band evidence and wrote only this index + its evidence JSON. It did not touch `04-artifacts/state/`, did not mark any ledger row, did not modify any file it indexed, computed no verdict, declared no readiness, opened no egress, built no live client, and changed no gate. `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — untouched.
