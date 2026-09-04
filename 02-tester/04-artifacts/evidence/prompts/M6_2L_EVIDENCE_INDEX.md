# M6.2L Evidence Index — Post-Pilot Audit Fix Batch (A3/A4/B2/B3/B4)

| Field | Value |
|---|---|
| Prompt | **M6-P2107** — `M6_2L_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, `analysis_only`) |
| Slice | **M6.2L** — close the 5 M6-self-doable defects from the 2026-09-03 chief-auditor audit (against commit `5f09894`), as a cumulative superset of M6.2K under `04-artifacts/impl/M6.2L/`; prove the fixes with regression evidence only |
| Depends on | M6.2K (entry judge M6-P2100 chains to the PR/PILOT final judge M6-P3011 SIGNED) |
| Purpose | Map every band evidence file / artifact / test / boundary / security report to the 13 exit-gate legs; list unresolved blockers — a reader's map for the slice-gate Judge (**M6-P2109**) |
| Collection verdict | **complete** — all 7 band prompts (M6-P2100…2106) PASS with `fail_gate_tripped=false`; the two downstream prompts (docs M6-P2108, judge M6-P2109) are the only PENDING exit items |
| Governance | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — immutable, untouched; `config.py` byte-identical to M6.2K. `M6-P1000` + `M6-P1309` verdicts remain **BLOCKED** (not converted). The assembled pack still tops at `OWNER_REVIEW_REQUIRED`. |

> **This is a collection artifact, not a verdict.** Its own `status=PASS` / `open_blockers=[]` means the assembly task is
> complete and unblocked — it does **not** assert the slice passes. Slice-level unresolved items live in **§5**; all are
> forward/owner-gated or armed-not-fired carry-forwards that no band marked as tripping an in-scope fail gate.

> **What makes this slice unusual — it is remediation, and the boundary line verified its own residuals closed.** Three of
> the five fixes close residuals the pack's own boundary/security lines had raised: **B4** closes F-DASH-1 / F-GROWTH-3
> (the M6.2K/M6-P3002 revenue mispair), **B2** closes F-EVID-2 (junk/whitespace evidence refs), **B3** closes F-EVID-3
> (no readiness↔standing cross-check). The M6.2L boundary adversary (M6-P2105) re-executed the old attacks and confirmed
> all three **CLOSED**, with **0** in-scope FAIL-001/FAIL-007 breaches.

---

## 1. Band evidence (the M6.2L prompt chain — 7 of 10 prompts run)

| Prompt | Role | Evidence | Ledger | fail_gate | open_blockers | One-line result |
|---|---|---|---|---|---|---|
| **M6-P2100** | JUDGE (entry) | [M6-P2100.json](M6-P2100.json) | **SIGNED** | false | 0 | Entry gate PASS — opens M6.2L STAGED; prev gate M6-P3011 SIGNED; target LOCKED + OD-011 DECIDED; CTR-002/025 DRAFT_LOCKED, CTR-016 MISSING but harmonization M6-P0711 PASS; flags OD-013/OD-014 not yet DECISION_REGISTER rows (doc-sync, non-blocking) |
| **M6-P2101** | CODER (plan) | [M6-P2101.json](M6-P2101.json) | PASS | false | 0 | Plan for the 5 fixes; 12-agent adversarial review forced 2 load-bearing pre-code corrections (B4 drop-not-raise; A4 resolver rule reconciling SMK-007 ∧ SMK-020); no new table/migration/flag |
| **M6-P2102** | CODER (implement) | [M6-P2102.json](M6-P2102.json) | PASS | false | 0 | Built the 5 fixes across 8 carried files + 5 CODER regressions; **544 passed** (523 carried M6.2K + 21), rc 0; impl-review 0 CRITICAL/MAJOR + 3 minor (B2 hardened, 2 documented) |
| **M6-P2103** | TESTER (build) | [M6-P2103.json](M6-P2103.json) | PASS | false | 0 | Authored 5 official smokes SMK-019…023 (17 nodes = 3+3+4+4+3), scenario verbatim; collect-only **561**; static verification 7/7 all-CLEAN; NOT executed |
| **M6-P2104** | TESTER (run) | [M6-P2104.json](M6-P2104.json) | PASS | false | 0 | Executed: **all 5 smokes PASS** (17/17 nodes), correlation_id + evidence_id recorded (masked); full staged suite **561 passed / 0 failed**, rc 0; proposed 019…023 **executed** (not waived) |
| **M6-P2105** | BOUNDARY_ADVERSARY | [M6-P2105.json](M6-P2105.json) | PASS | false | 0 | 30 executed outcomes (20 DEFENDED / 9 OPEN-non-gate / 1 note); **0** FAIL-001/FAIL-007 breaches; **verified B4/B2/B3 close F-DASH-1/F-GROWTH-3, F-EVID-2, F-EVID-3**; residuals routed |
| **M6-P2106** | SECURITY_PII | [M6-P2106.json](M6-P2106.json) | PASS | false | 0 | Scan **244 files** — 0 raw PII, 0 secrets; B2/B3/B4 security-positive, A3 PII-neutral; one new finding F-SEC-2L-1 (A4 intake ids → M6-OD-012), armed-not-fired |
| M6-P2107 | PM_ORCHESTRATOR | *this collection* | RUNNING | false | 0 | This index + evidence JSON |
| M6-P2108 | ANALYST_ARCHITECT (docs) | — | **TODO** | — | — | Runbook — not yet run (exit item 11) |
| M6-P2109 | JUDGE (slice gate) | — | **TODO** | — | — | Slice-gate sign-off — not yet run (exit item 12) |

**All 7 completed band prompts are PASS with `open_blockers=[]`, `fail_gate_tripped=false`, and no `findings`/`test_results`
integrity keys asserting a tripped gate.** The entry judge (M6-P2100, ledger row 200) is **SIGNED**.

## 2. Artifact inventory (every file the band produced)

**Staged implementation — `04-artifacts/impl/M6.2L/`** (carried the M6.2K tree byte-identical, `config.py` byte-identical, then applied the 5 fixes):
- `PLAN.md` (M6-P2101) · `IMPLEMENTATION_NOTES.md` (M6-P2102)
- **8 patched carried files** (the 5 fixes' named sites): `models/attribution_context.py` + `attribution/resolver.py` (A3 attribution_id), `api/track.py` + `normalize.py` + `attribution/resolver.py` (A4 ad-hierarchy intake + resolver rule), `evidence/pack_assembler.py` (B2 existence+uniqueness+(category,key)-binding), `evidence/gap_blockers.py` + `evidence/pack_assembler.py` (B3 membership floor), `store/measurement_event_store.py` + `dashboard/data_mart.py` + `growth/reads.py` (B4 verified-lock). **No new migration** (attribution_id pre-exists in `0006`; ad-hierarchy columns in `0002` — RULE-018); **no new config flag**; migrations stay `0001–0012`.
- **5 CODER regression tests** `tests/test_m6_2l_{a3,a4,b2,b3,b4}_*.py`; **5 official smoke files** `tests/smoke/test_smk_019…023_*.py` + `tests/TEST_MANIFEST.md`

**Test report — `04-artifacts/test-reports/M6.2L/`:** [`SMOKE_RESULTS.md`](../../test-reports/M6.2L/SMOKE_RESULTS.md) (M6-P2104 — 5-smoke PASS table with masked correlation_id/evidence_id, verbatim scenario/expected, the SMK-023 ROAS note, exit-gate legs)

**Boundary — `04-artifacts/boundary-reports/`:** [`M6.2L_boundary.md`](../../boundary-reports/M6.2L_boundary.md) (M6-P2105); harness `04-boundary/work/attacks/m6_2l_attacks.py`

**Security — `04-artifacts/security-reports/`:** [`M6.2L_security.md`](../../security-reports/M6.2L_security.md) (M6-P2106); scanner `06-security/work/pii_scan_2l.py`

**Entry-judge sign-off — `04-artifacts/evidence/judge/`:** `M6-P2100_JUDGE_FINAL_SIGN_OFF.json` (PASS)

**Test-count reconciliation (count discipline):** **561** full staged suite = **523** carried (M6.2K) **+ 21** CODER M6.2L regressions (19 initial + 2 review-driven B2, → 544 baseline) **+ 17** official-smoke nodes (tester, = 3+3+4+4+3). Coder baseline before any patch was 523 (byte-parity with M6.2K). All green, 0 failed / 0 skipped / 0 error, rc 0; the isolated 5-leg run independently confirms **17 passed**.

## 3. Contract checklist (CONTRACT_REGISTER)

| Contract | Status | This slice | Resolution |
|---|---|---|---|
| **M6-CTR-002** `ads_attribution_context` | **DRAFT_LOCKED** | consumed / extended | A3 surfaces the `attribution_id` surrogate **already declared in migration `0006`** as a first-class field (no new column). Owned/locked at M6.2E. → **satisfied.** |
| **M6-CTR-016** `POST /api/ads/events/track` | **MISSING / OWNER_DECISION_REQUIRED** | A4 touches this endpoint | Not a blocker: harmonization prompt **M6-P0711 (CONTRACT_TRACK_APIS) is PASS**, so resolved-for-entry (entry judge M6-P2100 confirmed). The HTTP routing/authN of this endpoint is the OPEN **M6-OD-011** owner-integration step. → **resolved-for-entry.** |
| **M6-CTR-025** `Evidence package` | **DRAFT_LOCKED** (content-level, doc §22) | B2/B3 harden the assembler | Not MISSING; owned at M6.2K. → **satisfied.** |

No new contract is introduced (measure/record-only, no new table — RULE-018).

## 4. Exit-gate checklist → evidence map (all 13 legs of `slices/M6.2L.md`)

| # | Exit-gate item | Status | Evidence |
|---|---|---|---|
| 1 | **attribution_id trace (A3)** — `attribution_id` first-class on `AdsAttributionContext` + handoff (`to_public`/`as_stored`); an ORDER_VERIFIED traces `attribution_id → campaign` | **MET** | SMK-019 PASS 3/3 + `test_m6_2l_a3_*` green; deterministic (`attr_`+sha256(event_id)[:24], 1:1, idempotent); governance ref, not PII |
| 2 | **ad-hierarchy intake (A4)** — `POST /api/ads/events/track` + normalize accept/persist campaign/adset/ad/live_session; a FACEBOOK_AD event reaches HIGH confidence via the real API path | **MET** | SMK-020 PASS 3/3 + `test_m6_2l_a4_*` green; 4 ids persist → FACEBOOK_AD/HIGH; non-string → fail-closed SCHEMA_INVALID (RULE-H03); incomplete-ad+live stays MULTI_TOUCH (preserves carried SMK-007) |
| 3 | **evidence forgery blocked (B2 / M6-OD-013)** — assembler validates ref existence + uniqueness + category-binding, not raw truthiness; a fake-but-nonblank ref, or one ref copy-pasted across all keys of all 10 categories, leaves categories MISSING | **MET** | SMK-021 PASS 4/4: both named forgeries → MISSING/NOT_READY; wrong-category binding MISSING; honest refs all-COMPLETE. **Authenticity residual** (default path proves slot-correctness, not authenticity — a canonical-string reconstruction still passes without the `known_refs` oracle) is the forward M6-OD-013 seam → **B2 in §5**. |
| 4 | **gap-id collision/shadow (B3 / M6-OD-014)** — floor pins/de-dups gap ids and counts membership, not a set-subset; a duplicated/shadowing standing-blocker id makes the floor FAIL | **MET** | SMK-022 PASS 4/4: duplicated M6-P1000 → floor False (naive subset would pass); shadow M6-P1309 / missing M6-P1000 → False; canonical list + clean pack pass and carry all 8 standing blockers |
| 5 | **ROAS verified-lock (B4)** — verified revenue counts only from ORDER_VERIFIED at BOTH `data_mart.verified_rows()` and `store.materialize()` (self-checks the stored `event_code`, not a caller boolean); an in-process QUOTE_SENT + `materialize(verified=True)` yields dashboard Revenue Verified = 0 and ROAS = 0 | **MET** | SMK-023 PASS 3/3: `materialize` drops non-OV revenue **without raising** → Revenue Verified = 0.0; both `verified_rows` choke points exclude a leaked QUOTE_SENT row; genuine ORDER_VERIFIED counts 180000.0. **ROAS wording note:** with no ads spend the fail-closed value is `ROAS is None` (`_safe_div(0, None)`) — the honest realization of "ROAS = 0"; the register "ROAS = 0" line is a **non-blocking doc-sync hygiene item** (§5). |
| 6–10 | Proposed smokes **M6-SMK-019 … 023** executed OR owner-waived | **MET** (×5) | All 5 **executed** (not waived): PASS 3/3, 3/3, 4/4, 4/4, 3/3 ([SMOKE_RESULTS.md](../../test-reports/M6.2L/SMOKE_RESULTS.md) · [M6-P2104.json](M6-P2104.json)) |
| 11 | All slice prompts have schema-valid evidence (no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | M6-P2100…2106 present + PASS + clean; M6-P2107 (this) completing; **M6-P2108 (docs) TODO, M6-P2109 (judge) TODO** |
| 12 | Slice-gate judge sign-off exists with verdict PASS | **PENDING** | **M6-P2109 TODO**. The slice-gate Judge reads this index |
| 13 | Rollback documented for every change this slice made | **MET** | [IMPLEMENTATION_NOTES §7](../../impl/M6.2L/IMPLEMENTATION_NOTES.md): staged-only → delete the M6.2L tree (M6.2K untouched); per-item revert to M6.2K bytes; **scoped partial revert** for the two dual-fix files (`resolver.py` A3-vs-A4 regions; `pack_assembler.py` B2-vs-B3 regions); 5 test files → delete; **no migration** to unwind |

**Summary:** MET = items 1–10 (all 5 fixes + all 5 smokes) + 13 (rollback) · PENDING = items 11, 12 (the two unrun downstream prompts). No exit item is FAILED, BLOCKED, or SUPPORTED-only — every fix leg is proven by regression **and** verified by the boundary adversary.

## 5. Unresolved blockers & carry-forwards

All residuals below are **armed-not-fired**: every band self-reported `fail_gate_tripped=false`; the boundary adversary
(30 executed outcomes, 0 in-scope breaches) and the security review (244-file scan, 0 raw PII/secrets) confirmed none is
channel-reachable to a gate trip while the export surfaces are unwired and `external_send=OFF`. This collection prompt's
own `open_blockers` is therefore **empty**.

**Slice-owned residuals (M6.2L):**

- **B1 — F-SEC-2L-1 (primary security; owner M6-OD-012 + CODER).** *A4 intake ids are not PII-scanned and export unmasked.* The 4 ad-hierarchy ids + `live_session_id` are type-validated (non-string → fail-closed SCHEMA_INVALID) but **not** run through the RULE-014 free-text `payload` tripwire (which by design scans only the payload, as it already did for `page_id`/`session_id`), and they export **unmasked** via `AdsAttributionContext.to_public()` and `FunnelTrace.to_public()` (which mask only `psid`). The export **predates A4** (M6.2K already emitted these); A4's new contribution is that a **channel-supplied** value can now populate them via the untrusted track body. **Adjudication (security):** campaign/adset/ad are ad-platform **object ids, not PII** (masking them would be wrong; a phone/digit scan would false-positive legitimate numeric platform ids); `live_session_id` + the siblings `comment_id`/`messenger_thread_id` are live/comment/messenger **trace-join** ids, `messenger_thread_id` (a 1:1 DM thread) the most identifying → this is the **M6-OD-012** masking-scope decision, the **same family** as F-SEC-2I-2 / F-SEC-2J-2 / F-SEC-2K-1. **Fix/route:** M6-OD-012; plus an optional **email-only** reject on the intake ids as false-positive-safe defense-in-depth (a phone/digit reject is **not** safe). Armed-not-fired (export unwired; the endpoint's own HTTP/authN is the OPEN M6-OD-011).

- **B2 — B2 authenticity residual (owner M6-OD-013).** *The B2 default path proves slot-correctness, not authenticity.* Existence + (category,key)-binding + pack-wide uniqueness defeat the two named SMK-021 forgeries, but a forger reconstructing the exact canonical `ev::{category}::{key}` string still passes **in the default path**; authenticity against a registry of issued refs is the injected `known_refs` oracle — a forward owner-integration seam (**M6-OD-013**), exercised by a regression. It **compounds with F-EVID-5**: canonical-reconstructed refs + all 18 smokes recorded `status='FAIL'` reach `OWNER_REVIEW_REQUIRED` (still capping there, never a Pass, still disclosing the 8 standing blockers). Trusted-input (PM authors refs). **Fix/route:** wire the `known_refs` authenticity oracle at the M6-OD-013 owner step — and the oracle must be a real `set`/`frozenset`, not a hostile always-`True` container (boundary B2-7, trusted-input/code-exec).

**Carry-forwards (out of the 5-fix scope; armed-not-fired; CODER/owner):**

- **F-EVID-5 (CODER).** Readiness gates on `recorded` (run+evidenced), not the PASS/FAIL of the status, so an all-`FAIL` recorded matrix still reaches `OWNER_REVIEW_REQUIRED` — add a `status=='PASS'` gate to drop to `NOT_READY` on any recorded FAIL/HOLD. Compounds with B2 above.
- **F-EVID-1 / F-EVID-4 (CODER).** Whitespace-id smoke recorded; `SmokeResult.status` exported verbatim (masking-scope family).
- **F-GROWTH-1 + N6 reactivation borrowed consent (CODER).** The CRM gate (F-GROWTH-1) and reactivation `_member_eligible` (N6) validate consent by `order_code`/`consent_snapshot_id` but never bind `snapshot.subject_ref` to the row's buyer/member — bind it. Disclosed in the M6.2J-GROWTH standing blocker.
- **RULE-009 value-sanity (N4, CODER).** A genuine ORDER_VERIFIED conversion carrying NaN/negative/inf revenue is not finiteness-checked before banking (row is genuinely OV so not FAIL-001) — add `math.isfinite(v) and v >= 0` on the verified-revenue write.
- **N5 RULE-009 scale-evidence (neutralized).** Fabricated A4 ad ids can launder a MULTI_TOUCH into FACEBOOK_AD/HIGH/eligible, but `scale_evidence` remains gated behind `SCALE_MODEL_RATIFIED=False` (M6-OD-005) — the channel-reachable acceptance is **neutralized by the immutable scale flag**.
- **B4 silent-drop audit-trail / drop-path idempotency (RN-01/RN-04, CODER/audit).** B4's fail-closed drop of illegitimate revenue leaves **no audit record**, and the drop path carries an idempotency note. The boundary files this at its lowest **audit/robustness** tier (not a gate item; B4 still holds FAIL-001) — a future hardening pass should emit an audit line on the drop.
- **Housekeeping (R5).** The M6.2J-GROWTH standing-blocker text still lists F-GROWTH-3 as a forward condition even though **B4 closed it**, and the B3 membership floor now locks that text by value → a future slice must update the disclosure floor-aware. Over-disclosure (safe), not a leak.

**Standing cross-slice governance (carried forward):**

- **`M6-P1000` + `M6-P1309` verdicts remain BLOCKED** (not converted) and are carried inside the assembled pack.
- **Hard forward gates before any real scale / send / auto-publish / surface:** the M6.2G/H/I/J + M6-OD-011/012 + owner-gated forward conditions from the M6-P3011 readiness package remain in force. `SCALE_MODEL_RATIFIED` / `HASH_POLICY_RATIFIED` / learning flags stay `False`.
- **Open owner decisions this slice's residuals depend on:** **M6-OD-012** (masking scope — B1), **M6-OD-013** (evidence-ref authenticity — B2), **M6-OD-003** (hash policy — N/A this slice; B1 psid_hash out of scope). **M6-OD-014** governs the B3 gap-floor.
- **Operator hygiene (non-blocking, flagged by the entry judge + coder + tester):** register **M6-OD-013** + **M6-OD-014** in `DECISION_REGISTER.md` — both are referenced by the slice spec as fix-decision-ids but are **not yet rows** in the register (a doc-sync gap analogous to the stale ENTRY-004 row flagged at M6-P3011, which also still needs reconciliation); and reword the SMK-023 SMOKE_REGISTER "ROAS = 0" line to the fail-closed `None`. None gates this slice (the fixes are M6-self-doable and fully specified by the exit legs).

## 6. Reader's guide for the slice-gate Judge (M6-P2109)

1. **Read order:** this index → the 7 band JSONs (§1) → the two review reports (`M6.2L_boundary.md`, `M6.2L_security.md`) → `SMOKE_RESULTS.md` → `IMPLEMENTATION_NOTES.md` (rollback). The exit-gate map is **§4**; the residuals are **§5**.
2. **What is proven (executed + verified):** all 5 M6-self-doable audit fixes hold — A3 (attribution_id first-class + traces to campaign), A4 (4 ad-hierarchy ids persist via the real track path → HIGH; non-string fail-closed; carried SMK-007 preserved), B2 (evidence-ref existence+uniqueness+(category,key)-binding defeats both named forgeries), B3 (membership floor FAILs duplicate/shadow/missing standing ids), B4 (verified-revenue event_code lock at both `materialize` and both `verified_rows`, drop-not-raise). Full staged suite **561 passed / 0 failed**; the 5 official smokes **17/17**; the boundary adversary **0** in-scope FAIL-001/FAIL-007 breaches and **confirmed B4/B2/B3 close F-DASH-1/F-GROWTH-3, F-EVID-2, F-EVID-3**; security **0** raw PII / secrets across 244 files; `config.py` byte-identical to M6.2K (no posture change).
3. **What is NOT yet closed:** exit items **11 & 12** are PENDING purely because the docs prompt (M6-P2108) and this judge (M6-P2109) have not run — not because of any defect. Every fix leg (1–5) and every smoke leg (6–10) plus rollback (13) is MET.
4. **The finding to weigh hardest:** **B1 (F-SEC-2L-1)** — A4 lets a channel-supplied value populate the ad-hierarchy/trace-join ids that export unmasked; the security line adjudicated campaign/adset/ad as non-PII platform ids and routed the trace-join ids (`live_session_id`/`comment_id`/`messenger_thread_id`) to the OPEN **M6-OD-012** masking decision, with an email-only intake reject as false-positive-safe defense-in-depth. Armed-not-fired (export unwired). **B2 authenticity** (M6-OD-013) is the second — the default path proves slot-correctness, not authenticity.
5. **Boundary integrity of this collection:** this prompt is `analysis_only` — it read the band evidence and wrote only this index + its evidence JSON. It did not touch `04-artifacts/state/`, did not mark any ledger row, did not modify any file it indexed, computed no verdict, and declared no readiness. `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — untouched.
