# M6.2Q Evidence Index — Ads-spend import + live-session binding + CPA/ROAS-by-session (A5)

| Field | Value |
|---|---|
| Prompt | **M6-P2507** — `M6_2Q_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, `analysis_only`) |
| Slice | **M6.2Q** — the A5 "đường-tới-tiền" leg: M6-side ads-spend ingest (maker-checker) + `live-session-ads-binding.v1` + CPA/ROAS-by-`live_session`, so ROAS/CPA compute from **mock-in-test** approved spend. Cumulative superset of M6.2P. Everything **STAGED** (in-memory stores + migration DDL never applied; mock CSV) — no real Meta network / Marketing API, no real spend, no flag flipped. |
| Depends on | M6.2P (entry judge M6-P2500 chains to the M6.2P slice judge M6-P2409 SIGNED) |
| Purpose | Map every band evidence file / artifact / test / boundary / security report to the 7 exit-gate legs; list unresolved blockers — a reader's map for the slice-gate Judge (**M6-P2509**) |
| Collection verdict | **complete** — all 7 band prompts (M6-P2500…2506) PASS with `fail_gate_tripped=false`; the two downstream prompts (docs M6-P2508, judge M6-P2509) are the only PENDING exit items |
| Governance | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — immutable, untouched; `config.py` byte-identical to M6.2P (sha256 `911b3238…`). `M6-P1000` + `M6-P1309` verdicts remain **BLOCKED** (not converted). Owner decisions consumed: **M6-OD-016** (spend source, DECIDED 2026-09-09), **M6-OD-011** (binding direction), **M6-OD-015** (psid-no-join). |

> **This is a collection artifact, not a verdict.** Its own `status=PASS` / `open_blockers=[]` means the assembly task is
> complete and unblocked — it does **not** assert the slice passes. Slice-level unresolved items live in **§5**.

> ### ⚠ Two load-bearing honesty points for the money leg (read before §4)
> This slice makes ROAS/CPA compute from real (mock) spend and adds the pack's **first real authorization control** — but:
> 1. **The maker-checker four-eyes is a *structural* control, not authenticated identity.** The gate fail-closed refuses a
>    self-approve — canonicalized (strip+casefold, a red-team fix over raw `==`) so a case/whitespace alias of the maker
>    cannot self-approve, blank checker refused, only APPROVED materializes (set-once). **But actor identity is
>    unauthenticated free-text** — `uploaded_by`/`decision.actor` are plain request strings, so the gate enforces two
>    *distinct strings*, not two *authenticated principals*: a single person can supply maker=A + checker=B. The control's
>    security value is **conditional on the M6-OD-011 server-bind + authenticated-identity step — DECIDED, but not yet implemented** (HTTP bind + real authN/authZ, a separate session).
>    Do not read "maker-checker enforced, self-approve rejected" as production segregation-of-duties.
> 2. **ROAS revenue provenance is asymmetric (N1 / F-SEC-2I-1).** Spend is *authenticated* to a session (campaign→session
>    binding), but revenue is joined by each event's own **un-provenanced `live_session_id`** — so a verified-revenue event
>    on a different campaign tagged with the bound session's `live_session_id` inflates that session's ROAS. A5 turns the
>    standing M6.2I-FUNNEL trace-bind gap into a **money number**. Armed-not-fired (reader internal, events from the trusted
>    store), routed to owner.
>
> Both are armed-not-fired in this staged posture (no real spend, no egress, no HTTP surface wired) and neither trips an
> in-scope gate; both are the sharpest items in §5. The exit judge M6-P2509 confirms no flag flip / no real spend / no Meta
> network / posture OFF-BLOCKED-OFF.

---

## 1. Band evidence (the M6.2Q prompt chain — 7 of 10 prompts run)

| Prompt | Role | Evidence | Ledger | fail_gate | open_blockers | One-line result |
|---|---|---|---|---|---|---|
| **M6-P2500** | JUDGE (entry) | [M6-P2500.json](M6-P2500.json) | **SIGNED** | false | 0 | Entry gate PASS — verified the DECIDED+FILED M6-OD-016 (spend source, 2026-09-09) + M6-OD-011 + M6-OD-015 authorize the slice; CTR-015/002 DRAFT_LOCKED; M6-OD-002/005 OPEN = forward conditions |
| **M6-P2501** | CODER (plan) | [M6-P2501.json](M6-P2501.json) | PASS | false | 0 | Plan: 3 legs (spend+maker-checker / binding+primary_campaign_id / CPA-ROAS-by-session); red-team caught + fixed 1 MAJOR (by-session sum wrongly gated on `.mapped` — campaign-level source has adset/ad None → would always be None) |
| **M6-P2502** | CODER (implement) | [M6-P2502.json](M6-P2502.json) | PASS | false | 0 | Built 13 new .py + 3 migrations (0014–0016) + 3 edited additive; **626 passed** (603 carried M6.2P + 23); self-review fixed the four-eyes raw-`==` alias self-approve (canonicalized); config.py byte-identical; pinned DataMart/14-metric tests green |
| **M6-P2503** | TESTER (build) | [M6-P2503.json](M6-P2503.json) | PASS | false | 0 | Authored official SMK-029 (5 nodes end-to-end), scenario verbatim; collect **631**; static verification launched; NOT executed |
| **M6-P2504** | TESTER (run) | [M6-P2504.json](M6-P2504.json) | PASS | false | 0 | Executed: **SMK-029 PASS 5/5**, correlation_id + evidence_id recorded (masked); full staged suite **631 passed / 0 failed**, rc 0; proposed 029 **executed** (not waived) |
| **M6-P2505** | BOUNDARY_ADVERSARY | [M6-P2505.json](M6-P2505.json) | PASS | false | 0 | 30 recorded outcomes (29 executed [23 DEFENDED / 6 OPEN-non-gate] + 1 documented-not-executed NOTE); **0** in-scope FAIL-007/RULE-003 breaches; four-eyes + set-once + RULE-003 lock + campaign-binding gate verified; residuals incl. N1 (ROAS provenance, highest-value), MC9/N4 (four-eyes edges), value-sanity |
| **M6-P2506** | SECURITY_PII | [M6-P2506.json](M6-P2506.json) | PASS | false | 0 | Scan **274 files** — 0 raw PII, 0 real secrets (ad spend is campaign-level, not PII; actors masked; no Meta token); RULE-003 lock held; **the four-eyes is the pack's first real authz — structurally sound but identity unauthenticated (→ M6-OD-011)**; MC-09 (checker free-text export → M6-OD-012) |
| M6-P2507 | PM_ORCHESTRATOR | *this collection* | RUNNING | false | 0 | This index + evidence JSON |
| M6-P2508 | ANALYST_ARCHITECT (docs) | — | **TODO** | — | — | Runbook — not yet run (exit item 5) |
| M6-P2509 | JUDGE (slice gate) | — | **TODO** | — | — | Slice-gate sign-off — not yet run (exit item 6); confirms no flag flip / no real spend / no Meta network |

**All 7 completed band prompts are PASS with `open_blockers=[]`, `fail_gate_tripped=false`, and no `findings`/`test_results`
integrity keys asserting a tripped gate.** The entry judge (M6-P2500, ledger row 240) is **SIGNED**.

## 2. Artifact inventory (every file the band produced)

**Owner authorizations this slice consumes (verified on disk):** [`M6-OD-016.json`](../decisions/M6-OD-016.json) (spend source = phase-1 CSV Ads Manager + maker-checker; no Marketing API / new secret; staged; DECIDED 2026-09-09) + [`M6-OD-015.json`](../decisions/M6-OD-015.json) (psid-no-join). M6-OD-011 (binding direction) DECIDED.

**Staged implementation — `04-artifacts/impl/M6.2Q/`** (carried M6.2P byte-identical [230 .py + 13 .sql], then added 13 .py + 3 .sql + 3 additive edits):
- `PLAN.md` (M6-P2501) · `IMPLEMENTATION_NOTES.md` (M6-P2502)
- **Leg 1 (spend + maker-checker):** `models/ads_spend_import.py`, `store/ads_spend_import_store.py`, `ads_spend/import_gate.py` (four-eyes fail-closed, `_canon_actor` strip+casefold), `ads_spend/materializer.py` (drains only APPROVED, set-once), `store/ads_spend_record_store.py` (set-once), `api/ads_spend_imports.py` (no Meta/network dep), `migrations/0014` + `0015`
- **Leg 2 (binding):** `models/attribution_context.py` (+`primary_campaign_id`, additive, not in `.complete`/`_grade`), `attribution/resolver.py` (deterministic set), `models/live_session_ads_binding.py`, `store/live_session_ads_binding_store.py` (`session_for_campaign`, set-once, campaign-unambiguous), `migrations/0016`
- **Leg 3 (CPA/ROAS):** `dashboard/data_mart.py` (+`spend_date` on `AdsSpendRecord`, additive), `dashboard/session_roas.py` (standalone `SessionRoasReader` — CPA/ROAS per session, spend gated on the **campaign-binding not `.mapped`**, RULE-003 ORDER_VERIFIED lock, `_safe_div` fail-closed, `daily_total()` bucket)
- **Tests:** 3 coder regressions (`test_m6_2q_{ads_spend_import_maker_checker,binding_primary_campaign,cpa_roas_by_session}.py`); official smoke `tests/smoke/test_smk_029_ads_spend_cpa_roas_by_session.py` (5 nodes); `tests/TEST_MANIFEST.md`. **No new config flag** (config.py byte-identical); migrations `0001–0016` contiguous.

**Test report — `04-artifacts/test-reports/M6.2Q/`:** [`SMOKE_RESULTS.md`](../../test-reports/M6.2Q/SMOKE_RESULTS.md) (M6-P2504)

**Boundary — `04-artifacts/boundary-reports/`:** [`M6.2Q_boundary.md`](../../boundary-reports/M6.2Q_boundary.md) (M6-P2505); harness `04-boundary/work/attacks/m6_2q_attacks.py`

**Security — `04-artifacts/security-reports/`:** [`M6.2Q_security.md`](../../security-reports/M6.2Q_security.md) (M6-P2506); scanner `06-security/work/pii_scan_2q.py`

**Entry-judge sign-off — `04-artifacts/evidence/judge/`:** `M6-P2500_JUDGE_FINAL_SIGN_OFF.json` (PASS)

**Test-count reconciliation (count discipline):** **631** full staged suite = **626** coder M6.2Q baseline (603 carried M6.2P **+ 23** coder regressions [18 leg + 5 red-team alias]) **+ 5** official-smoke nodes (tester, SMK-029). Baseline before any patch was 603 (byte-parity with M6.2P). All green, 0 failed / 0 skipped / 0 error, rc 0; the isolated 1-leg run independently confirms **5 passed**.

## 3. Contract checklist (CONTRACT_REGISTER)

| Contract | Status | This slice | Resolution |
|---|---|---|---|
| **M6-CTR-015** `Dashboard KPI contract` | **DRAFT_LOCKED** (formulas; thresholds OPEN via M6-OD-002) | CPA/ROAS-by-session formulas | Not MISSING; owned at M6.2F (14 metrics verbatim). The slice computes the **numbers** (formulas), not the thresholds — M6-OD-002 governs Scale-Gate/alert thresholds, not the computation. → **satisfied for M6.2Q.** |
| **M6-CTR-002** `ads_attribution_context` | **DRAFT_LOCKED** | `primary_campaign_id` added (additive) | Not MISSING; owned at M6.2E. → **satisfied.** |

No new contract is introduced (measure/record-only; the new tables are staged migrations `0014–0016`, never applied — RULE-018 respected).

## 4. Exit-gate checklist → evidence map (all 7 legs of `slices/M6.2Q.md`)

| # | Exit-gate item | Status | Evidence |
|---|---|---|---|
| 1 | **ads_spend_import + maker-checker (M6-OD-016)** — CSV rows keyed by campaign_id enter PROPOSED; a DISTINCT approver (maker != checker) moves to APPROVED; only APPROVED materialize (a worker); self-approve / single-actor rejected; staged in-memory + migration ≥0014; mock CSV, no real network | **MET** (staged) | SMK-029 primary + self-approve neg + `test_m6_2q_ads_spend_import_maker_checker.py` green; boundary + security verified the four-eyes fail-closed + canonicalized + set-once materialize. **Caveat (§5 B1):** the control is *structural* (two distinct strings) — authenticated identity is the M6-OD-011 server-bind, DECIDED but not yet implemented (a forward step). |
| 2 | **live-session-ads-binding.v1 + primary_campaign_id** — primary_campaign_id first-class; binding {live_session_id, primary_campaign_id, adset_id?, ad_id?, bound_at, bound_by}; spend attributed to a session by campaign_id × session-window; out-of-window spend → daily total, not session-attributed | **MET** | SMK-029 primary + out-of-window neg + `test_m6_2q_binding_primary_campaign.py` green; binding set-once + campaign-unambiguous; primary_campaign_id additive, **not** in `.complete`/`_grade` (A4/SMK-020/007 unaffected) |
| 3 | **CPA/ROAS-by-live_session** — CPA = spend / count(ORDER_VERIFIED in session), ROAS = verified_revenue / spend, from APPROVED spend only (verified revenue keeps the ORDER_VERIFIED lock, RULE-003); spend + zero verified → CPA fail-closed (guarded None) + ROAS = 0; no spend → no CPA number | **MET** | SMK-029 primary + zero-verified neg + `test_m6_2q_cpa_roas_by_session.py` green; RULE-003 lock verified on **both** the CPA denominator and the ROAS numerator (a quote/draft contributes 0); `_safe_div` fail-closed; campaign-binding gate (not `.mapped`). **Caveat (§5 B2):** the ROAS revenue side is un-provenanced (N1) — the sharpest residual, routed to owner. |
| 4 | Proposed smoke **M6-SMK-029** executed OR owner-waived | **MET** | PASS 5/5 — **executed** (not waived) ([SMOKE_RESULTS.md](../../test-reports/M6.2Q/SMOKE_RESULTS.md) · [M6-P2504.json](M6-P2504.json)) |
| 5 | All slice prompts have schema-valid evidence (no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | M6-P2500…2506 present + PASS + clean; M6-P2507 (this) completing; **M6-P2508 (docs) TODO, M6-P2509 (judge) TODO** |
| 6 | Slice-gate judge sign-off exists with verdict PASS | **PENDING** | **M6-P2509 TODO**. The slice-gate Judge reads this index + confirms no flag flip / no real spend / no Meta network |
| 7 | Rollback documented for every change this slice made | **MET** | [IMPLEMENTATION_NOTES §5](../../impl/M6.2Q/IMPLEMENTATION_NOTES.md): staged-only → delete the M6.2Q tree (M6.2P untouched); new files delete; 3 additive edits scoped-revert; four-eyes canon → revert to plain `==`; **no live migration** to unwind |

**Summary:** MET = items 1–4 (all 3 legs + SMK-029) + 7 (rollback) · PENDING = items 5, 6 (the two unrun downstream prompts). No exit item is FAILED or BLOCKED. Items 1 & 3 are MET as **staged** mechanisms with the B1 (authenticated identity) and B2 (ROAS provenance) forward conditions in §5.

## 5. Unresolved blockers & carry-forwards

All residuals below are **armed-not-fired** in the staged posture. The reachability floor: ad spend is campaign-level
(not PII); actors + `bound_by` are masked on export; the `SessionRoasReader` + import gate have **no HTTP/durable-export
surface wired** (that is the forward M6-OD-011 server-bind); events come from the trusted measurement store;
`external_send` is Final OFF. Both reviews self-reported `fail_gate_tripped=false` (boundary 30 outcomes / 0 in-scope
FAIL-007/RULE-003 breaches; security 274-file scan / 0 raw PII / 0 real secrets). This collection prompt's own
`open_blockers` is therefore **empty** — but B1 and B2 are hard forward conditions for the owner/exit judge.

**Primary forward conditions (owner + exit judge M6-P2509):**

- **B1 — the maker-checker four-eyes is STRUCTURAL, not authenticated (owner M6-OD-011; the pack's first real authz control).** The gate fail-closed refuses a self-approve, canonicalizes distinctness (strip+casefold — a red-team fix over raw `==`), refuses a blank checker, and materializes only APPROVED (set-once) — **but** `uploaded_by`/`decision.actor` are unauthenticated request-body strings, so it enforces two *distinct strings*, not two *authenticated principals*; a single person can satisfy four-eyes with maker=A + checker=B. Its security value is conditional on the **M6-OD-011** server-bind + authenticated-identity step — **DECIDED** (2026-07-23; framework/DB 2026-09-04) but **not yet implemented** (HTTP + authN/authZ, a separate session; per P0307 the concrete approver identities are an owner call). Two armed-not-fired edge instances until identity is bound: **MC9** (a Unicode full-width homoglyph of the maker bypasses casefold — casefold ≠ NFKC — → distinct → self-approve) and **N4** (a blank *maker* + any distinct checker → APPROVED; the gate refuses a blank checker but not a blank maker). **Fix:** owner binds authenticated identity (M6-OD-011); CODER hardens — NFKC-normalize before strip+casefold in `_canon_actor` (closes MC9) + require a non-blank maker (closes N4).

- **B2 — N1 / F-SEC-2I-1: ROAS revenue-provenance asymmetry (owner; highest-value).** `SessionRoasReader` authenticates the **spend** side (campaign→session binding, unambiguous) but groups **revenue** by each event's own un-provenanced `live_session_id` (`_session_key`) — so a verified-revenue event on a *different* campaign tagged with the bound session's `live_session_id` is counted in that session's `verified_revenue`, inflating ROAS. This is the standing **M6.2I-FUNNEL** blocker (F-SEC-2I-1 single-subject / `live_session` bind), which A5 turns into a **money number**. Armed-not-fired (reader internal, no channel export; events from the trusted measurement store). **Fix:** owner binds revenue provenance (single-subject / `live_session`) before any real spend/ROAS surface.

**Slice-owned security residual (owner M6-OD-012 + CODER):**

- **B3 — MC-09: checker free-text exports verbatim.** `AdsSpendImportDecision.to_public()` masks the actor but exports `reason`/`audit_ref`/`evidence_ref` **verbatim** — checker free-text (human-typed at approval, the likeliest accidental-PII spot). The **audit trail is already safe** (`import_gate._audit_decision` does not echo `reason`/`audit_ref` — only `import_id` + the decision enum + a masked actor); the gap is only the decision object's `to_public` export. Same durable-export masking-scope family as F-SEC-2K-1 / F-SEC-2M-1 → **M6-OD-012**. Armed-not-fired (no durable-export surface wired). **Fix:** M6-OD-012 masking scope; cheap defense-in-depth — run `reason`/`audit_ref` through the raw-PII tripwire at import (email-shaped reject is false-positive-safe) or mask on export (CODER).

**CODER value-sanity + robustness (armed-not-fired):**

- **B4 — value-sanity (N2 / RO10, RULE-009-adjacent).** Neither the spend write nor the verified-revenue write checks finiteness/sign — a negative spend/revenue → negative CPA/ROAS; a **NaN** revenue → `verified_revenue`/ROAS NaN and `to_public` emits raw NaN (breaks the JSON export contract). Spend is maker-checker-approved (trusted); revenue is Commerce-supplied via a genuine OV row (the more-reachable twin). **Fix:** `math.isfinite(v) and v >= 0` on **both** writes.
- **B5 — order_code double-count (N3 / ROAS-12, carried F-DASH-3).** Two ORDER_VERIFIED events sharing `order_code` but distinct `idempotency_key` both count → `verified_orders` 2 + `verified_revenue` doubled (the store dedups only on `idempotency_key`). Reachable only if one order yields two distinct-key OV events. **Fix (owner/CODER):** confirm `order_code` uniqueness, or dedup `_verified` by `order_code`.
- **B6 — misc robustness (CODER).** ROAS-15 a tz-aware `spend_date` vs tz-naive `event_ts` raises TypeError → crashes `by_session()`/`daily_total()` (availability, fails loud not silent-wrong; normalize tz); BIND-07 a blank `primary_campaign_id` (guarded to None today; reject at bind); ROAS-14 a rogue `event_ts` widens the derived `[min,max]` session window (→ owner/attribution-model **M6-OD-005**).
- **EVID-10 (owner).** The A5 `SessionRoasReader` RULE-003 lock is proven by SMK-029 (proposed/HARDENING), **not** a registered P0 smoke — a future regression letting a quote/draft inflate CPA/ROAS-by-session would not on its own drop pack readiness. **Owner:** decide whether the A5 reader needs a P0-registry floor.

**What this slice PROVED / IMPROVED (worth the Judge's note):**

- **The RULE-003 verified-revenue lock held in the new money math** — both the CPA denominator (verified-order count) and the ROAS numerator (verified_revenue) filter `event_code == ORDER_VERIFIED`; a quote/draft in-window contributes 0. The đường-tới-tiền number cannot count a non-verified row.
- **The pack's first real authz control** — a maker-checker segregation-of-duties on spend approval, fail-closed + red-team-hardened (canonicalized distinctness, blank-checker refused), set-once materialize. Its shape is correct; B1 is the identity-authentication forward condition.
- **Fail-closed money math** — guarded `_safe_div` (no divide-by-zero), campaign-binding gate (not the 3-id `.mapped`), inclusive window, `daily_total()` bucket for out-of-window/unbound spend; input validation `_parse_rows` fail-closed; config.py byte-identical (no posture change); no new secret; no Meta network; no egress.

**Standing cross-slice governance (carried forward):**

- **`M6-P1000` + `M6-P1309` verdicts remain BLOCKED** (not converted), carried inside the assembled pack.
- **Hard forward gates before any real spend / scale / egress:** **M6-OD-011** (server-bind + authenticated identity — B1; the *decision* is DECIDED, the server-bind/authN is the not-yet-implemented forward step), **M6-OD-002** (thresholds, OPEN), **M6-OD-005** (scale-authoritative attribution model, OPEN — also governs ROAS-14 window), **M6-OD-012** (masking scope — B3), **M6-OD-003** (psid hash/pepper + privacy/legal — carried; tightened by the now-recorded M6-OD-015 psid-no-join + OD-003 stage-1, but the real pepper + full privacy/legal remain), plus the M6.2G/H/I/J conditions incl. **F-SEC-2I-1** (B2). M6-OD-016 (spend source) is DECIDED.
- **Operator hygiene (non-blocking, carried):** register **M6-OD-013 + M6-OD-014** and the M5 `PSID_HASH_POLICY_M5_TMP` dependency as `DECISION_REGISTER.md` rows; fix the stale `CONTRACT_EVENT_REGISTRY.contract.yaml` line-137 note (from M6.2P) and the stale ENTRY-004 row. None gates this slice.

## 6. Reader's guide for the slice-gate Judge (M6-P2509)

1. **Read order:** this index → the 7 band JSONs (§1) → the owner authorizations (`M6-OD-016.json`, `M6-OD-015.json`) → the two review reports (`M6.2Q_boundary.md`, `M6.2Q_security.md`) → `SMOKE_RESULTS.md` → `IMPLEMENTATION_NOTES.md` (rollback). The exit-gate map is **§4**; the residuals are **§5**.
2. **What is proven (executed + verified):** the A5 chain works staged — a mock-CSV import → distinct-checker APPROVE → materialize (only APPROVED, set-once) → bind campaign→session → CPA/ROAS-by-session under the ORDER_VERIFIED lock; fail-closed on zero-verified (CPA None, ROAS 0) and out-of-window (daily_total). Full staged suite **631 passed / 0 failed**; SMK-029 **5/5**; boundary **0** in-scope FAIL-007/RULE-003 breaches; security **0** raw PII / 0 real secrets across 274 files; `config.py` byte-identical to M6.2P.
3. **The two things to weigh hardest (this is a money leg):** **B1** — the maker-checker is a *structural* control until M6-OD-011 binds authenticated identity (do not read it as production segregation-of-duties); and **B2 (N1/F-SEC-2I-1)** — the ROAS revenue side is un-provenanced while spend is authenticated, so ROAS is inflatable; bind revenue provenance before any real spend/ROAS surface. Both armed-not-fired staged, both hard forward conditions.
4. **What is NOT yet closed:** exit items **5 & 6** are PENDING purely because the docs prompt (M6-P2508) and this judge (M6-P2509) have not run. All 3 legs (1–3) + SMK-029 (4) + rollback (7) are MET (staged).
5. **Boundary integrity of this collection:** this prompt is `analysis_only` — it read the band evidence and wrote only this index + its evidence JSON. It did not touch `04-artifacts/state/`, did not mark any ledger row, did not modify any file it indexed, computed no verdict, declared no readiness, opened no egress, and authorized no real spend. `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — untouched.
