# M6.2M Evidence Index — Evidence Authenticity (M6-OD-013 twin)

| Field | Value |
|---|---|
| Prompt | **M6-P2207** — `M6_2M_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, `analysis_only`) |
| Slice | **M6.2M** — close the M6-OD-013 authenticity residual disclosed at the M6.2L re-judge (ref-side known_refs oracle + smoke-side SmokeResult stripped-non-blank twin), as a cumulative superset of M6.2L under `04-artifacts/impl/M6.2M/`; prove the authenticity **mechanism** with regression evidence, real registry stays owner-populated |
| Depends on | M6.2L (entry judge M6-P2200 chains to the M6.2L slice judge M6-P2109 SIGNED, whose re-judge disclosed M6-OD-013) |
| Purpose | Map every band evidence file / artifact / test / boundary / security report to the 7 exit-gate legs; list unresolved blockers — a reader's map for the slice-gate Judge (**M6-P2209**) |
| Collection verdict | **complete** — all 7 band prompts (M6-P2200…2206) PASS with `fail_gate_tripped=false`; the two downstream prompts (docs M6-P2208, judge M6-P2209) are the only PENDING exit items |
| Governance | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — immutable, untouched; `config.py` byte-identical to M6.2L/M6.2K. `M6-P1000` + `M6-P1309` verdicts remain **BLOCKED** (not converted). The assembled pack still tops at `OWNER_REVIEW_REQUIRED`. |

> **This is a collection artifact, not a verdict.** Its own `status=PASS` / `open_blockers=[]` means the assembly task is
> complete and unblocked — it does **not** assert the slice passes. Slice-level unresolved items live in **§5**; all are
> forward/owner-gated or armed-not-fired carry-forwards that no band marked as tripping an in-scope fail gate.

> **This slice remediates the exact residual the M6.2L index flagged.** The M6.2L §5 "B2 authenticity residual (owner
> M6-OD-013)" — the default path proving slot-correctness, not authenticity — is **closed at the mechanism level here**:
> the ref-side known_refs oracle rejects a reconstructed-but-un-issued canonical ref (SMK-024), and the smoke-side twin
> closes the **F-EVID-1 whitespace variant** (SMK-025). The M6.2L "B2-7 hostile known_refs" wiring caveat I carried
> forward is sharpened here into the **N1/N2/F1-4 known_refs-robustness cluster** (§5). Only the owner-registry population
> and the untyped-param robustness remain.

---

## 1. Band evidence (the M6.2M prompt chain — 7 of 10 prompts run)

| Prompt | Role | Evidence | Ledger | fail_gate | open_blockers | One-line result |
|---|---|---|---|---|---|---|
| **M6-P2200** | JUDGE (entry) | [M6-P2200.json](M6-P2200.json) | **SIGNED** | false | 0 | Entry gate PASS — opens M6.2M STAGED; prev gate M6-P2109 SIGNED; target LOCKED + OD-011 DECIDED; CTR-025 DRAFT_LOCKED; M6-OD-013 is in-scope work (real registry out-of-scope); flags OD-013/OD-014 still not DECISION_REGISTER rows (doc-sync) |
| **M6-P2201** | CODER (plan) | [M6-P2201.json](M6-P2201.json) | PASS | false | 0 | Plan for the twin fix; **honesty finding** — the ref-side oracle already lands in the M6.2L base (impl-review forward seam), so leg-1 is a SMK-024 proof + docstring; FIX-2 is the genuine new code; 2-dim plan red-team 0 findings |
| **M6-P2202** | CODER (implement) | [M6-P2202.json](M6-P2202.json) | PASS | false | 0 | FIX-2 `_nonblank` + `recorded` stripped-non-blank + `_smokes` whitespace-normalize; FIX-1 docstring (no logic change); **568 passed** (561 carried M6.2L + 7); config.py byte-identical; edge-case probe confirms fail-closed + SMK-024 discriminating |
| **M6-P2203** | TESTER (build) | [M6-P2203.json](M6-P2203.json) | PASS | false | 0 | Authored 2 official smokes SMK-024/025 (7 nodes = 3+4), scenario verbatim; collect-only **575**; static verification CLEAN (1 docstring-arrow nit fixed); NOT executed |
| **M6-P2204** | TESTER (run) | [M6-P2204.json](M6-P2204.json) | PASS | false | 0 | Executed: **both smokes PASS** (7/7 nodes), correlation_id + evidence_id recorded (masked); full staged suite **575 passed / 0 failed**, rc 0; proposed 024/025 **executed** (not waived) |
| **M6-P2205** | BOUNDARY_ADVERSARY | [M6-P2205.json](M6-P2205.json) | PASS | false | 0 | 25 executed outcomes (13 DEFENDED / 11 OPEN-non-gate / 1 note); **0** FAIL-007 breaches; **verified FIX-1 (M6-OD-013 mechanism) + FIX-2 (F-EVID-1 whitespace) closed**; carried M6.2L B2/B3/B4 intact; residuals routed |
| **M6-P2206** | SECURITY_PII | [M6-P2206.json](M6-P2206.json) | PASS | false | 0 | Scan **248 files** — 0 raw PII, 0 secrets; both fixes security-positive; no new PII surface; primary carried finding F-SEC-2M-1 (status+smoke_id unmasked export → M6-OD-012), armed-not-fired |
| M6-P2207 | PM_ORCHESTRATOR | *this collection* | RUNNING | false | 0 | This index + evidence JSON |
| M6-P2208 | ANALYST_ARCHITECT (docs) | — | **TODO** | — | — | Runbook — not yet run (exit item 5) |
| M6-P2209 | JUDGE (slice gate) | — | **TODO** | — | — | Slice-gate sign-off — not yet run (exit item 6) |

**All 7 completed band prompts are PASS with `open_blockers=[]`, `fail_gate_tripped=false`, and no `findings`/`test_results`
integrity keys asserting a tripped gate.** The entry judge (M6-P2200, ledger row 210) is **SIGNED**.

## 2. Artifact inventory (every file the band produced)

**Staged implementation — `04-artifacts/impl/M6.2M/`** (carried the M6.2L tree byte-identical, `config.py` byte-identical, then applied the twin fix):
- `PLAN.md` (M6-P2201) · `IMPLEMENTATION_NOTES.md` (M6-P2202)
- **2 patched carried files:** `evidence/models.py` (FIX-2: `_nonblank` helper + `SmokeResult.recorded` stripped-non-blank) and `evidence/pack_assembler.py` (FIX-2: `_smokes` whitespace-normalize → None; FIX-1: `_ref_valid` **docstring only** — the oracle logic pre-existed in the M6.2L base). **No new migration** (migrations stay `0001–0012`, RULE-018); **no new config flag**; **no M6.2L fix touched**.
- **2 CODER regression tests** `tests/test_m6_2m_{ref,smoke}_authenticity.py`; **2 official smoke files** `tests/smoke/test_smk_024_ref_authenticity_allowlist.py`, `test_smk_025_smoke_result_authenticity.py` + `tests/TEST_MANIFEST.md`

**Test report — `04-artifacts/test-reports/M6.2M/`:** [`SMOKE_RESULTS.md`](../../test-reports/M6.2M/SMOKE_RESULTS.md) (M6-P2204 — 2-smoke PASS table with masked correlation_id/evidence_id, verbatim scenario/expected, exit-gate legs)

**Boundary — `04-artifacts/boundary-reports/`:** [`M6.2M_boundary.md`](../../boundary-reports/M6.2M_boundary.md) (M6-P2205); harness `04-boundary/work/attacks/m6_2m_attacks.py`

**Security — `04-artifacts/security-reports/`:** [`M6.2M_security.md`](../../security-reports/M6.2M_security.md) (M6-P2206); scanner `06-security/work/pii_scan_2m.py`

**Entry-judge sign-off — `04-artifacts/evidence/judge/`:** `M6-P2200_JUDGE_FINAL_SIGN_OFF.json` (PASS)

**Test-count reconciliation (count discipline):** **575** full staged suite = **561** carried (M6.2L) **+ 7** CODER M6.2M regressions (→ 568 baseline) **+ 7** official-smoke nodes (tester, = 3+4). Coder baseline before any patch was 561 (byte-parity with M6.2L). All green, 0 failed / 0 skipped / 0 error, rc 0; the isolated 2-leg run independently confirms **7 passed**.

## 3. Contract checklist (CONTRACT_REGISTER)

| Contract | Status | This slice | Resolution |
|---|---|---|---|
| **M6-CTR-025** `Evidence package` | **DRAFT_LOCKED** (content-level, doc §22) | the assembler this slice hardens | Not MISSING; owned at M6.2K. Entry judge M6-P2200 confirmed resolved-for-entry. → **satisfied.** |

No new contract is introduced (evidence-honesty tightening only, no new table — RULE-018).

## 4. Exit-gate checklist → evidence map (all 7 legs of `slices/M6.2M.md`)

| # | Exit-gate item | Status | Evidence |
|---|---|---|---|
| 1 | **Ref authenticity (M6-OD-013 ref-side)** — assembler consults the known_refs oracle; a well-formed + (category,key)-bound + unique ref NOT in the known set is REJECTED (category MISSING), so canonical-string reconstruction can no longer forge COMPLETE; absent an allowlist the M6.2L slot-correctness bar still applies (no regression) | **MET** | SMK-024 PASS 3/3 + `test_m6_2m_ref_authenticity` green: staged allowlist minus the DEDUP ref → DEDUP MISSING/NOT_READY; no allowlist → all COMPLETE/OWNER_REVIEW_REQUIRED (no regression); fully-issued → all COMPLETE (discriminating). *The oracle logic pre-existed in the M6.2L base; this leg is the proof.* Real-registry population is the forward owner step (§5). |
| 2 | **Smoke authenticity (M6-OD-013 smoke-side twin)** — `SmokeResult.recorded` + `_smokes` require stripped-non-blank status + correlation_id + evidence_id (not raw truthiness), so a whitespace/fake-but-nonblank field no longer marks a mandatory smoke recorded — it stays un-recorded, pack fails closed to NOT_READY | **MET** | SMK-025 PASS 4/4 + `test_m6_2m_smoke_authenticity` green: whitespace SmokeResult for mandatory owner smoke M6-SMK-001 → `recorded()` False, UNRUN gap, NOT_READY; `_smokes` normalizes whitespace → None (no masquerade on export); genuine set still records (OWNER_REVIEW_REQUIRED). Closes the **F-EVID-1 whitespace variant**. |
| 3 | Proposed smoke **M6-SMK-024** executed OR owner-waived | **MET** | PASS 3/3 — **executed** (not waived) |
| 4 | Proposed smoke **M6-SMK-025** executed OR owner-waived | **MET** | PASS 4/4 — **executed** (not waived) |
| 5 | All slice prompts have schema-valid evidence (no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | M6-P2200…2206 present + PASS + clean; M6-P2207 (this) completing; **M6-P2208 (docs) TODO, M6-P2209 (judge) TODO** |
| 6 | Slice-gate judge sign-off exists with verdict PASS | **PENDING** | **M6-P2209 TODO**. The slice-gate Judge reads this index |
| 7 | Rollback documented for every change this slice made | **MET** | [IMPLEMENTATION_NOTES §6](../../impl/M6.2M/IMPLEMENTATION_NOTES.md): staged-only → delete the M6.2M tree (M6.2L untouched); FIX-1 scoped **docstring-only** revert, FIX-2 scoped logic revert (drop `_nonblank`/restore raw `recorded`; drop the `_smokes` whitespace-normalize); 2 test files → delete; **no migration** to unwind |

**Summary:** MET = items 1–4 (both fixes + both smokes) + 7 (rollback) · PENDING = items 5, 6 (the two unrun downstream prompts). No exit item is FAILED, BLOCKED, or SUPPORTED-only — both authenticity legs are proven by regression **and** verified by the boundary adversary.

## 5. Unresolved blockers & carry-forwards

All residuals below are **armed-not-fired**. The load-bearing reachability floor: the boundary adversary
**grep-confirmed the evidence assembler has NO `app/api` caller** (imported only by evidence internals + tests), and the
`Readiness` enum has no Pass member — so every residual caps at `OWNER_REVIEW_REQUIRED`, never a Pass. Both reviews
self-reported `fail_gate_tripped=false` (boundary 25 outcomes / 0 FAIL-007 breaches; security 248-file scan / 0 raw
PII/secrets). This collection prompt's own `open_blockers` is therefore **empty**.

**Slice-owned residuals (M6.2M):**

- **B1 — F-SEC-2M-1 (primary security; owner M6-OD-012 + CODER).** *`SmokeResult.to_public()` masks correlation_id + evidence_id but exports `status` AND `smoke_id` unmasked, and `_smokes` appends the caller's SmokeResult without pinning it to `spec.smoke_id`.* A result stored under the M6-SMK-001 key with a different/PII `smoke_id` is displayed with that raw id — a mislabel **and** a second unmasked export slot besides `status`. **Not introduced by M6.2M** (`to_public` unchanged this slice; the `status` slot is the carried F-SEC-2K-1, the `smoke_id` slot the boundary's N4 widening of F-EVID-4) — M6.2M touched `recorded()`/`_smokes` so it was the natural place, but correctly kept it **out** of the M6-OD-013 twin scope. Same masking-scope **family** as F-SEC-2I-2 / F-SEC-2J-2 / F-SEC-2K-1 / F-SEC-2L-1 → all route to the OPEN **M6-OD-012**. Armed-not-fired (no channel caller; `status` is TESTER-set PASS/FAIL, `smoke_id` = M6-SMK-0NN — no live PII today). **Fix:** pin each `_smokes` row to `spec.smoke_id` + mask/enum-constrain `status` ({PASS,FAIL}) and `smoke_id` on export; ratify M6-OD-012.

- **B2 — M6-OD-013 owner-integration forward step (owner).** The authenticity **mechanism** is proven (SMK-024, discriminating), but production ref-authenticity needs the owner to **populate the real issued-refs registry** and pass it as `known_refs` — the default no-allowlist path still passes canonical reconstruction (the M6.2L slot-correctness bar). Legitimately **out of scope** (the slice spec places "populating the real known-refs registry" out of scope); this is the honest remaining step, not a defect.

**Robustness residuals (CODER, trusted-input; the M6.2L B2-7 caveat sharpened):**

- **B3 — `known_refs` untyped param (N1/N2/F1-4).** A **string** allowlist degrades `r not in known_refs` to substring containment; a **generator** allowlist is exhausted by the two-calls-per-key `_categories` pass → an honest fully-issued pack is FALSE-REJECTED (fail-closed, understates); a **hostile** `__contains__=True` defeats the oracle. All trusted-input (the owner supplies the allowlist). **Fix:** `isinstance(known_refs, (set, frozenset, dict))` + materialize once + evaluate `_ref_valid` once per key.
- **B4 — F-EVID-1 duck-type variant (F2-6/F2-7, CODER).** M6.2M closed the whitespace-**field** twin, not the duck-**type** variant: a duck object with `recorded=True` + None fields launders a mandatory slot (`_smokes` trusts `result.recorded` and normalizes only whitespace **string** fields), and a duck **with** a whitespace field crashes `_smokes`' `dataclasses.replace()` (fail-closed-by-crash). **Fix:** type-check the value is a real `SmokeResult`.
- **B5 — assembler input robustness (N3 + F1-6, CODER, fail-closed).** A non-Mapping `evidence_refs` value (e.g. a list) makes `provided.get()` crash so `assemble` aborts (fail-closed-by-crash, a pre-existing robustness gap); padded allowlist entries also fail-close. Trusted-input; **never overstates readiness** (a crash yields no COMPLETE), so the gate posture is unchanged. **Fix:** validate `evidence_refs` is a Mapping (else fail-closed `None`) and strip allowlist entries.

**Carry-forwards (out of the twin scope; armed-not-fired; CODER):**

- **F-EVID-5 (CODER).** Readiness gates on `recorded` (run+evidenced), not the PASS/FAIL of `status` — 18 recorded-`FAIL` smokes still reach `OWNER_REVIEW_REQUIRED`; add a `status=='PASS'` gate to drop to `NOT_READY` on any recorded FAIL/HOLD. **The compound (R3):** default-path canonical reconstruction + 18 genuine-non-blank FAIL smokes reach `OWNER_REVIEW_REQUIRED` on a forged base — but still **caps at OWNER_REVIEW_REQUIRED** (never a Pass) and discloses all 8 standing blockers + BLOCKED posture; closure needs **both** the owner allowlist (B2) **and** the `status=='PASS'` gate.
- **F-GROWTH-1 + reactivation N6 consent subject-bind (CODER).** Out of scope, disclosed in the M6.2J-GROWTH standing blocker — bind `snapshot.subject_ref` to the row's buyer/member.

**Standing cross-slice governance (carried forward):**

- **`M6-P1000` + `M6-P1309` verdicts remain BLOCKED** (not converted) and are carried inside the assembled pack.
- **Hard forward gates before any real scale / send / auto-publish / surface:** the M6.2G/H/I/J + M6-OD-011/012 + owner-gated forward conditions from the M6-P3011 readiness package remain in force.
- **Open owner decisions this slice's residuals depend on:** **M6-OD-012** (masking scope — B1), **M6-OD-013** (real issued-refs registry population — B2, the forward integration step this slice's mechanism awaits), **M6-OD-003** (hash policy — N/A this slice).
- **Operator hygiene (non-blocking, now flagged across M6.2L + M6.2M by the entry judge, coder, and security):** register **M6-OD-013** + **M6-OD-014** in `DECISION_REGISTER.md` — both are referenced by the slice specs + the gap-blocker floor + this remediation but are **still not rows** in the register (a standing doc-sync gap for a complete owner audit trail, analogous to the stale ENTRY-004 row from M6-P3011). None gates this slice (the mechanism is M6-self-doable and fully specified by the exit legs).

## 6. Reader's guide for the slice-gate Judge (M6-P2209)

1. **Read order:** this index → the 7 band JSONs (§1) → the two review reports (`M6.2M_boundary.md`, `M6.2M_security.md`) → `SMOKE_RESULTS.md` → `IMPLEMENTATION_NOTES.md` (rollback). The exit-gate map is **§4**; the residuals are **§5**.
2. **What is proven (executed + verified):** the M6-OD-013 authenticity twin holds — FIX-1 (ref-side) rejects a reconstructed-but-un-issued canonical ref when the allowlist is wired (SMK-024, discriminating), FIX-2 (smoke-side) fails a whitespace/fake-but-nonblank SmokeResult closed to NOT_READY (SMK-025), closing the F-EVID-1 whitespace variant. Full staged suite **575 passed / 0 failed**; the 2 official smokes **7/7**; the boundary adversary **0** in-scope FAIL-007 breaches and **confirmed the twin closed + the carried M6.2L B2/B3/B4 fixes intact**; security **0** raw PII / secrets across 248 files; `config.py` byte-identical to M6.2L (no posture change).
3. **What is NOT yet closed:** exit items **5 & 6** are PENDING purely because the docs prompt (M6-P2208) and this judge (M6-P2209) have not run — not because of any defect. Both fix legs (1–2) and both smoke legs (3–4) plus rollback (7) are MET.
4. **The finding to weigh hardest:** **B1 (F-SEC-2M-1)** — the `status`/`smoke_id` unmasked-export slots (M6-OD-012 masking family) — and **B2** (owner-populate the real known-refs registry, the honest remaining step for production ref-authenticity). Both armed-not-fired (no channel caller). The robustness residuals (B3 untyped `known_refs`, B4 duck-type variant) and F-EVID-5 are CODER hardening.
5. **Boundary integrity of this collection:** this prompt is `analysis_only` — it read the band evidence and wrote only this index + its evidence JSON. It did not touch `04-artifacts/state/`, did not mark any ledger row, did not modify any file it indexed, computed no verdict, and declared no readiness. `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — untouched.
