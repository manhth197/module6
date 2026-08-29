# M6.2K Evidence Index — Smoke & Evidence Pack (the doc §22 owner review package)

| Field | Value |
|---|---|
| Prompt | **M6-P2007** — `M6_2K_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, `analysis_only`) |
| Slice | **M6.2K** — the FINAL build slice: re-run the full P0 smoke matrix (SMK-001…018) and assemble the doc §22 evidence plan (10 categories) into an **owner sign-off package** with an honest gap/blocker list |
| Depends on | M6.2J (entry judge M6-P2000 chains to the M6.2J slice judge M6-P1909 SIGNED — all build slices M6.2A…M6.2J closed) |
| Purpose | Map every band evidence file / artifact / test / boundary / security report to the slice exit-gate checklist and to the 10 doc §22 categories, and present the unresolved blocker list for owner review |
| Collection verdict | **complete** — all 7 band prompts (M6-P2000…2006) PASS with `fail_gate_tripped=false`; the two downstream prompts (docs M6-P2008, judge M6-P2009) are the only PENDING exit items |
| Assembled-pack readiness | **`OWNER_REVIEW_REQUIRED`** — the terminal state. The pack's `Readiness` enum has **no PASS / READY / SCALE-READY member**; it is fail-closed `NOT_READY` on any incomplete §22 category or un-recorded smoke (M6-FAIL-007), and never self-certifies (M6-RULE-015). |
| Governance | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — **immutable, untouched, and stay OFF through M6.2K and into PR/PILOT**. `M6-P1000` + `M6-P1309` verdicts remain **BLOCKED** (not converted). Declaring ROAS Pass / Scale Ready is **owner-only** (doc §23) and is **not** done here. |

> ### ⚠ What this pack does NOT say (read first — it is the point of this slice)
> A green run is **not** a readiness verdict. This slice re-ran all 18 P0 smokes (523 tests, 0 failed) and assembled
> the 10 doc §22 categories — and it still says **only** "ready for owner review", never "ready to scale/send".
> Production/gateway/external-send stay **BLOCKED/OFF/OFF**; **8 standing blockers** (§6) remain open and are disclosed
> in every assembled pack; `M6-P1000` + `M6-P1309` are still **BLOCKED**. The success of the smoke matrix proves the
> **measurement capability is exercisable and honest**, not that anything is cleared to go live. Reviewing the §6
> blockers and deciding ROAS Pass / Scale Ready is the **owner's** job at PR/PILOT — not this pack's, not this index's.

> **This is a collection artifact, not a verdict.** Its own `status=PASS` / `open_blockers=[]` means the assembly task
> is complete and unblocked — it does **not** assert the slice or the pack passes. The honest, always-disclosed
> slice/owner blocker list lives in **§6**; per the coder's readiness rule (PLAN §4.4, adjudicated at the gate) those
> standing blockers are disclosed but do not by themselves force `NOT_READY`, because production stays BLOCKED
> regardless — reviewing them is the owner's job.

---

## 1. Band evidence (the M6.2K prompt chain — 7 of 10 prompts run)

| Prompt | Role | Evidence | Ledger | fail_gate | open_blockers | One-line result |
|---|---|---|---|---|---|---|
| **M6-P2000** | JUDGE (entry) | [M6-P2000.json](M6-P2000.json) | **SIGNED** | false | 0 | Entry gate PASS — opens M6.2K STAGED; prev gate M6-P1909 SIGNED; target LOCKED + OD-011 DECIDED; CTR-025 DRAFT_LOCKED; no owner decision names M6.2K; enumerates the standing gap list the pack must carry |
| **M6-P2001** | CODER (plan) | [M6-P2001.json](M6-P2001.json) | PASS | false | 0 | Plan: a fail-closed, **no-self-cert / no-Pass-Ready** assembler; the ONE readiness rule (§4.4); adversarial red-team (9 agents), 3 wording/consistency fixes |
| **M6-P2002** | CODER (implement) | [M6-P2002.json](M6-P2002.json) | PASS | false | 0 | Built `evidence/` package; **451 passed** (425 carried M6.2A–J + 26, = 24 initial + 2 regressions), rc 0; self-review fixed **1 MAJOR fail-open** (owner-waiver escape hatch) + 2 NIT — the MAJOR + posture NIT are regression-tested (2 regressions); the SMK-017 NIT was a verbatim-string restore |
| **M6-P2003** | TESTER (build) | [M6-P2003.json](M6-P2003.json) | PASS | false | 0 | Authored 18 evidence legs (one per smoke, 4 nodes each = 72), scenario verbatim; collect-only **523**; static verification all-CLEAN; NOT executed |
| **M6-P2004** | TESTER (run) | [M6-P2004.json](M6-P2004.json) | PASS | false | 0 | Executed: **all 18 smokes PASS** (72/72 evidence-leg nodes), correlation_id + evidence_id recorded (masked) per smoke; full staged suite **523 passed / 0 failed**, rc 0; proposed 016/017/018 **executed** (not waived) |
| **M6-P2005** | BOUNDARY_ADVERSARY | [M6-P2005.json](M6-P2005.json) | PASS | false | 0 | 43 executed attacks (DEFENDED 35 / OPEN-non-gate 8); **0** FAIL-007 breaches; pack structurally cannot overstate readiness; residuals F-EVID-1…4 (+X3/D4), all armed-not-fired |
| **M6-P2006** | SECURITY_PII | [M6-P2006.json](M6-P2006.json) | PASS | false | 0 | Scan **234 files** — 0 raw PII, 0 secrets (3 `sk-` = carried `risk-` false positives); ids masked on export; no new access surface; findings F-SEC-2K-1/2 + cross-refs, all armed-not-fired |
| M6-P2007 | PM_ORCHESTRATOR | *this collection* | RUNNING | false | 0 | This index (incl. the doc §22 10-category map) + evidence JSON |
| M6-P2008 | ANALYST_ARCHITECT (docs) | — | **TODO** | — | — | Runbook — not yet run (exit item 20) |
| M6-P2009 | JUDGE (slice gate) | — | **TODO** | — | — | Slice-gate sign-off — not yet run (exit item 21) |

**All 7 completed band prompts are PASS with `open_blockers=[]`, `fail_gate_tripped=false`, and no `findings`/`test_results`
integrity keys asserting a tripped gate.** Ledger rows confirm each; the entry judge is **SIGNED**.

## 2. Artifact inventory (every file the band produced)

**Staged implementation — `04-artifacts/impl/M6.2K/`** (carried the M6.2J tree byte-identical, then added the evidence assembler):
- `PLAN.md` (M6-P2001) · `IMPLEMENTATION_NOTES.md` (M6-P2002)
- **`app/measurement/evidence/`** — the new assembly package: `smoke_registry.py` (canonical 18 ids + doc §21 verbatim scenario/expected + owner/proposed status + test bindings), `categories.py` (the 10 doc §22 categories + mandatory-content keys), `models.py` (frozen `SmokeResult`/`CategoryStatus`/`GapBlocker`/`EvidencePack`; `Readiness` enum with **no PASS/READY member**; `to_public()` masks ids), `gap_blockers.py` (the canonical **8** `STANDING_GAP_BLOCKERS` + `STANDING_BLOCKER_IDS`), `pack_assembler.py` (`EvidencePackAssembler.assemble()` — fail-closed category completeness, **owner-waiver scope enforced**, always merges the 8 standing blockers, read-only posture snapshot, **no** pass/ready/certify/flag-flip verb), `__init__.py`
- **18 evidence-leg smoke files** `tests/smoke/test_smk_001…018_p0_evidence_pack.py` (4 nodes each) + coder tests T1–T6 + `tests/conftest.py`; `tests/TEST_MANIFEST.md`

**Test report — `04-artifacts/test-reports/M6.2K/`:** [`SMOKE_RESULTS.md`](../../test-reports/M6.2K/SMOKE_RESULTS.md) (M6-P2004 — the 18-smoke PASS table with masked correlation_id/evidence_id, verbatim scenario/expected, exit-gate legs)

**Boundary — `04-artifacts/boundary-reports/`:** [`M6.2K_boundary.md`](../../boundary-reports/M6.2K_boundary.md) (M6-P2005); harness `04-boundary/work/attacks/m6_2k_attacks.py`

**Security — `04-artifacts/security-reports/`:** [`M6.2K_security.md`](../../security-reports/M6.2K_security.md) (M6-P2006); scanner `06-security/work/pii_scan_2k.py`

**Entry-judge sign-off — `04-artifacts/evidence/judge/`:** `M6-P2000_JUDGE_FINAL_SIGN_OFF.json` (PASS)

**Test-count reconciliation (count discipline):** **523** full staged suite = **425** carried (M6.2A–J final tree) **+ 26** evidence-package tests (coder M6-P2002, → 451 carried baseline) **+ 72** evidence-leg nodes (tester M6-P2003/2004, = 18 smokes × 4). Coder baseline before any patch was 425 (byte-parity with the M6.2J final tree); coder final 451; tester added the 72 evidence-leg nodes → 523. All green, 0 failed / 0 skipped / 0 error, rc 0. The isolated 18-leg run independently confirms **72 passed**.

## 3. Contract checklist (CONTRACT_REGISTER)

| Contract | Status | This slice | Resolution |
|---|---|---|---|
| **M6-CTR-025** `Evidence package (owner review pack)` | **DRAFT_LOCKED** (content-level, doc §22) | owned/produced | Not MISSING (the slice-spec condition "if MISSING, its harmonization prompt must be PASS before entry" does not fire). Content list is locked to SPEC §19 (doc §22 table verbatim) + M6-P0714; the file **format** is pack HARDENING. Entry judge M6-P2000 confirmed this at the gate. The evidence package this slice assembles **is** the CTR-025 deliverable. → **satisfied for M6.2K.** |

No new contract is introduced beyond CTR-025 (assembly-only, no new table — RULE-018).

## 4. Doc §22 owner review package — the 10-category evidence map

Exit-gate item 1 requires all **ten** doc §22 categories assembled **with their mandatory content**. The assembler proves
completeness structurally (`test_evidence_ten_categories_mandatory_content.py` — a missing mandatory key ⇒ INCOMPLETE ⇒
`NOT_READY`, fail-closed FAIL-007); this table is the reader's map from each category to the evidence that fills it. Every
category's proof is the recorded P0 re-run (§SMOKE_RESULTS) plus the carried slice that owns the behavior.

| # | Doc §22 category | Mandatory content | Evidence in this pack | Complete? |
|---|---|---|---|---|
| 1 | **Event Registry** | screenshot/API/DB record proving event codes, owner, policy | SMK-001 (event not in registry → Reject/HOLD, audit); doc §10 event-code constants; carried M6.2A/B registry + validator | ✅ |
| 2 | **Consent** | pass/fail-closed cases, opt-out handling | SMK-002 (missing consent → no external measurement / no audience sync), SMK-008 (CRM opt-out → no sync); carried hardened `ConsentGate` (M6.2B/D fixes) | ✅ |
| 3 | **Outbox** | queued/sent/retry/error/dead-letter | SMK-016 (bounded retry + error_log + next_retry_at → dead-letter; no infinite retry / no silent loss — proposed, **executed**); carried M6.2C outbox workers | ✅ |
| 4 | **Dedup** | Pixel/CAPI/Offline duplicates handled | SMK-003 (duplicate Pixel/CAPI/Offline → dedup, no double count); carried M6.2D dedup + hash | ✅ |
| 5 | **Attribution** | ORDER_VERIFIED traced back campaign/adset/ad/page/live/comment/Messenger | SMK-006 (full source → dashboard), SMK-007 (missing source → confidence LOW/HOLD), SMK-013 (live/comment/Messenger chain trace), SMK-018 (post-verify correction → adjustment record, not mutation — proposed, **executed**); carried M6.2E resolver | ✅ |
| 6 | **Dashboard** | Revenue Verified / ROAS / CPA / AOV from correct sources | SMK-006 (ROAS/CPA/AOV update), SMK-004 (quote → no revenue/ROAS), SMK-005 (draft/unverified → not Revenue Verified), SMK-015 (quote/draft shown as revenue → Fail); carried M6.2F dashboard + Data Quality | ✅ |
| 7 | **Scale Gate** | PASS/HOLD/FAIL with owner approval flow | SMK-009 (recall/sale-lock active → FAIL/HOLD), SMK-012 (no owner approval → no scale); carried M6.2G scale-gate | ✅ |
| 8 | **Learning** | candidate → review → approve/reject/hold → rollback | SMK-011 (candidate outside safe range → hold review, no publish); carried M6.2H learning libraries | ✅ |
| 9 | **Security / Privacy** | no raw PII, consent, hash policy, access control | SMK-017 (external payload from raw-PII event → hash policy per M6-OD-003, no raw phone/email/user-id in payload or platform log — proposed, **executed**); the whole-slice PII scan (**0 raw PII across 234 files**); consent (cat 2); access-control forward requirement disclosed as M6-OD-011 | ✅ |
| 10 | **Smoke Report** | results with correlation_id + evidence_id | all 18 smokes recorded with a masked correlation_id + evidence_id ([SMOKE_RESULTS.md](../../test-reports/M6.2K/SMOKE_RESULTS.md), M6-P2004) | ✅ |

> **Honesty note on category 9 / SMK-017:** a green SMK-017 proves the **fail-closed hashing mechanism** (no raw PII ever
> leaves — raw allow-list empty, `HASH_POLICY_RATIFIED=False`, every identity value hashed, the raw branch unreachable).
> It is **not** owner ratification of a send policy. The pack preserves that distinction by disclosing **M6-OD-003** OPEN
> inside the `M6.2G-SCALE` standing blocker (§6), so the green smoke cannot be misread as cleared-to-send.

## 5. Exit-gate checklist → evidence map (all 22 legs of `slices/M6.2K.md`)

| # | Exit-gate item | Status | Evidence |
|---|---|---|---|
| 1 | Evidence pack ready for review — full P0 re-run with correlation_id + evidence_id + all 10 §22 categories with mandatory content + owner package complete | **SUPPORTED (staged)** | §4 (10/10 categories complete) + all 18 smokes recorded (§SMOKE_RESULTS); the assembler reaches the terminal `OWNER_REVIEW_REQUIRED` with the honest gap list attached. The pack is **ready for owner review**; the owner sign-off itself is owner-only (doc §23) and the judge confirmation is item 21. |
| 2–16 | Smoke **M6-SMK-001 … M6-SMK-015** executed with recorded result + evidence ref | **MET** (×15) | Each 4/4 PASS, masked correlation_id + evidence_id recorded ([SMOKE_RESULTS.md](../../test-reports/M6.2K/SMOKE_RESULTS.md) · [M6-P2004.json](M6-P2004.json)) |
| 17 | Proposed **M6-SMK-016** executed OR owner-waived | **MET** | PASS 4/4 — **executed** (outbox retry → dead-letter) |
| 18 | Proposed **M6-SMK-017** executed OR owner-waived | **MET** | PASS 4/4 — **executed** (hash policy, no raw PII) |
| 19 | Proposed **M6-SMK-018** executed OR owner-waived | **MET** | PASS 4/4 — **executed** (post-verify correction → adjustment record) |
| 20 | All slice prompts have schema-valid evidence (no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | M6-P2000…2006 present + PASS + clean; M6-P2007 (this) completing; **M6-P2008 (docs) TODO, M6-P2009 (judge) TODO** — evidence for the last two does not exist yet |
| 21 | Slice-gate judge sign-off exists with verdict PASS | **PENDING** | **M6-P2009 TODO**. The slice-gate Judge reads this index + the assembled pack |
| 22 | Rollback documented for every change this slice made | **MET** | [IMPLEMENTATION_NOTES §6](../../impl/M6.2K/IMPLEMENTATION_NOTES.md): staged-only → delete the M6.2K tree (M6.2J untouched); new `evidence/` files → delete; **no carried file patched**; **no migration**. Boundary + Security reports record "no source modified" for their analysis-only writes. |

**Summary:** MET = items 2–19 (all 18 smokes) + 22 (rollback) · SUPPORTED (staged) = item 1 (pack ready for owner review) · PENDING = items 20, 21 (the two unrun downstream prompts). No exit item is FAILED or BLOCKED.

## 6. Gap / blocker list for the owner (the honest payload — RULE-015 / FAIL-007)

**This list is the reason the slice exists.** It is carried in every assembled pack and must never be dropped. Per the
readiness rule (PLAN §4.4), the standing blockers are **disclosed but do not by themselves gate readiness** — production
stays BLOCKED regardless, and weighing them is the owner's decision at PR/PILOT. This collection prompt's own
`open_blockers` is therefore `[]`; the unresolved items are listed **here**, as the acceptance check requires.

### 6a. The 8 standing blockers (canonical, from `evidence/gap_blockers.py`)

| # | Blocker id | What must clear before any real scale / send / auto-publish / surface | Owner |
|---|---|---|---|
| 1 | **M6-P1000** | M6.2A entry-judge verdict **BLOCKED** (not converted) | owner/judge |
| 2 | **M6-P1309** | M6.2D exit-judge verdict **BLOCKED** (not converted) | owner/judge |
| 3 | **M6.2G-SCALE** | Scale-Gate forward conditions: ENTRY-001/003 real-scale conditions, the four M6-P1600 attestation true-ups, ENTRY-004 M5 DEBT-1…4 + the adversarial P4 re-gate, scale ACCESS-1/F-SCALE-\*, and **M6-OD-002/003/004/005** | owner |
| 4 | **M6.2H-LEARN** | Learning forward conditions: **M6-OD-006** (safe range), **M6-OD-007** (content fill), F-LEARN-\* | owner |
| 5 | **M6.2I-FUNNEL** | Funnel forward conditions before surfacing: **F-FUNNEL-4** (single-subject trace bind), F-SEC-2I-2 | owner |
| 6 | **M6.2J-GROWTH** | Growth forward conditions: **F-GROWTH-1** (CRM subject-bind), **F-GROWTH-3** (`verified_rows` ORDER_VERIFIED choke), F-SEC-2J-\* | owner |
| 7 | **M6-OD-011** | Admin-endpoint authN/authZ (owner-controlled integration step) | owner |
| 8 | **M6-OD-012** | PII masking-scope decision (**OPEN**) — the F-SEC-2I-2 / F-SEC-2J-2 / F-SEC-2K-1 masking-scope family ratifies here | owner |

### 6b. M6.2K slice-owned residuals (armed-not-fired; routed to CODER; none channel-reachable; none trips FAIL-007)

The boundary adversary (43 executed attacks, 0 FAIL-007 breaches) and the security review (234-file scan, 0 raw PII/secrets)
both confirmed the pack **structurally cannot overstate readiness** (no Pass/Ready enum member; fail-closed; owner-waiver
scope enforced; the 8 standing blockers always disclosed; posture read-only; ids masked). These residuals are hardening
before the pack is ever surfaced through a real endpoint:

- **B-2K-1 — F-SEC-2K-1 / F-EVID-4 (primary; CODER).** `SmokeResult.to_public()` masks `correlation_id`/`evidence_id` but exports **`status` verbatim** — the same export-masking-scope inconsistency family as M6.2I F-SEC-2I-2 (`messenger_thread_id` raw) and M6.2J F-SEC-2J-2 (`buyer_ref` opt-in mask). Trusted-input only (TESTER sets `status`). **Fix:** enum-constrain `status` to `{PASS,FAIL}` or route through `mask()`; ratifies under the OPEN **M6-OD-012** the pack already discloses.
- **B-2K-2 — F-SEC-2K-2 / F-EVID-2 (CODER).** Category completeness uses `provided.get(k)` **truthiness, not ref shape** — a whitespace/truthy ref marks a category COMPLETE, including category 9 SECURITY_PRIVACY (`no_raw_pii`/`hash_policy`/`access_control` keys). Trusted-input only (PM authors refs). **Fix:** validate ref shape (stripped-non-blank / existence).
- **B-2K-3 — F-EVID-1 (CODER).** The assembler trusts truthiness/duck values rather than a validated run-trace: whitespace ids, a duck object with `recorded=True` dodging the id-conjunction + waiver-strip, and a row appended verbatim that mislabels the displayed smoke id. **Fix:** pin the row to `spec.smoke_id` and require a stripped-non-blank `status` + `correlation_id` + `evidence_id`.
- **B-2K-4 — F-EVID-3 (CODER).** No readiness↔standing-blocker positive floor: a code-exec rebind of `pack_assembler.STANDING_GAP_BLOCKERS` empties the payload while readiness stays `OWNER_REVIEW_REQUIRED`. Code-exec-only (not channel-reachable). **Fix:** assert the 8 `STANDING_BLOCKER_IDS` are present (a positive floor).
- **B-2K-5 — X3 / D4 (CODER, minor).** Non-typed inputs fail-closed-by-crash rather than coerced; mutating `config.PRODUCTION_FLAG` in-process echoes into the snapshot (code-exec-only). **Fix:** coerce/typed-guard inputs; the read-only `MappingProxyType` snapshot already blocks the tamper via the pack.

### 6c. Standing cross-slice governance (carried forward)

- **`M6-P1000` + `M6-P1309` verdicts remain BLOCKED** (not converted) — reaffirmed, and both appear **inside** the assembled pack (blockers 1–2 above).
- **Open owner decisions the pack surfaces:** **M6-OD-002/003/004/005** (scale/hash/…, via `M6.2G-SCALE`), **M6-OD-006/007** (learning), **M6-OD-011** (admin authN/authZ), **M6-OD-012** (masking scope). M6-OD-003 (external-send hash policy) is OPEN and disclosed; the SMK-017 green proves only the fail-closed mechanism, not ratification.
- **Governance chain — resolved earlier and still on disk:** `M6-DEFER-FBC-M6.2D.json` (consent fail-open class CLOSED + wired as a Scale-Gate RequiredInput, owner-confirmed 2026-08-07), `M6-DEFER-F1F2-M6.2B.json`, `M6-DEFER-OD003-M6.2D.json`, plus the `M6-OVERRIDE-M6P1000-STAGED` / `M6-OVERRIDE-M6P1309-STAGED` staging overrides — all in `04-artifacts/evidence/decisions/`. The overrides stage the BLOCKED verdicts for the build; they do **not** convert them, which is why blockers 1–2 stand.

## 7. Reader's guide for the slice-gate Judge (M6-P2009)

1. **Read order:** this index → the 10-category map (**§4**) → the honest blocker list (**§6**) → the 7 band JSONs (§1) → the two review reports (`M6.2K_boundary.md`, `M6.2K_security.md`) → `SMOKE_RESULTS.md` → `IMPLEMENTATION_NOTES.md` (rollback). The exit-gate map is **§5**.
2. **What is proven (executed):** the full P0 matrix (all 18 smokes, 15 owner + 3 proposed, the proposed ones **executed** not waived) re-ran green — 72/72 evidence-leg nodes, full staged suite **523 passed / 0 failed**, each smoke recorded with a masked correlation_id + evidence_id. All **10** doc §22 categories are assembled with mandatory content. Boundary: **0** FAIL-007 breaches across 43 executed attacks; the pack structurally cannot overstate readiness. Security: **0** raw PII / secrets across 234 files; ids masked on export; **no new access surface** (the assembler is wired to no endpoint).
3. **What the pack refuses to say:** it never declares ROAS Pass / Scale Ready and has no method to; readiness tops at `OWNER_REVIEW_REQUIRED`; the owner-waiver escape hatch (a MAJOR fail-open the coder self-review caught) is closed — a mandatory owner smoke cannot be waived un-run. `production_flag=OFF` and the gateway/external-send posture are verified still OFF and stay OFF into PR/PILOT.
4. **What is NOT yet closed:** exit items **20 & 21** are PENDING purely because the docs prompt (M6-P2008) and this judge (M6-P2009) have not run — not because of any defect. Item 1 is SUPPORTED (staged): the pack is ready for owner review; the owner sign-off is owner-only.
5. **The finding to weigh hardest:** the **8 standing blockers (§6a)** — this is a readiness *package*, and its integrity is measured by whether it discloses everything still open. It does: the two BLOCKED verdicts and every M6.2G/H/I/J forward condition and OD-011/012 are all carried in the pack itself. The slice-owned residuals (§6b, primary **B-2K-1** masking-scope of `status`) are armed-not-fired hardening, none channel-reachable, none tripping FAIL-007.
6. **Boundary integrity of this collection:** this prompt is `analysis_only` — it read the band evidence and wrote only this index + its evidence JSON. It did not touch `04-artifacts/state/`, did not mark any ledger row, did not modify any file it indexed, computed no verdict, and declared no readiness. `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — untouched.
