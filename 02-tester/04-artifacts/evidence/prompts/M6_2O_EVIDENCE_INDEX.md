# M6.2O Evidence Index — Out-of-band Backfill: psid_hash (B1) + duck-coerce (F2-6)

| Field | Value |
|---|---|
| Prompt | **M6-P2307** — `M6_2O_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, `analysis_only`) |
| Slice | **M6.2O** — retroactive on-ledger certification of two already-shipped, self-disclosed **off-ledger** changes: **B1** (raw PSID → one-way HMAC `psid_hash`, landed in impl/M6.2N) and **F2-6** (`_smokes` duck-coerce to a canonical `SmokeResult`, landed in impl/M6.2O). Closes the process debt that impl/M6.2N + impl/M6.2O carried no slice-spec / ledger row / gate. Coder legs **RECORD** the shipped code (no re-implementation); tester/boundary/security/judge **verify** it. Cumulative superset of M6.2M. |
| Depends on | M6.2M (entry judge M6-P2300 chains to the M6.2M slice judge M6-P2209 SIGNED) |
| Purpose | Map every band evidence file / artifact / test / boundary / security report to the 7 exit-gate legs; list unresolved blockers — a reader's map for the slice-gate Judge (**M6-P2309**) |
| Collection verdict | **complete** — all 7 band prompts (M6-P2300…2306) PASS with `fail_gate_tripped=false`; the two downstream prompts (docs M6-P2308, judge M6-P2309) are the only PENDING exit items |
| Governance | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — immutable, untouched; `config.py` byte-identical to M6.2M (sha256 `911b3238…`). `M6-P1000` + `M6-P1309` verdicts remain **BLOCKED** (not converted). The assembled pack still tops at `OWNER_REVIEW_REQUIRED`. |

> **This is a collection artifact, not a verdict.** Its own `status=PASS` / `open_blockers=[]` means the assembly task is
> complete and unblocked — it does **not** assert the slice passes. Slice-level unresolved items live in **§5**.

> ### ⚠ B1 is a staged MECHANISM proof, NOT a production-safe certification (read before §4)
> The security review (M6-P2306) is explicit: **it does NOT certify B1 production-safe.** B1 removes raw PSID from every
> durable/export surface *in staging* (a genuine FAIL-008 reduction), but two hard conditions gate any **real** deploy,
> both privacy-critical: (1) the staged `_MOCK_PEPPER` is a **public source constant** → a staged synthetic `psid_hash`
> is brute-force reversible (safe only because staged ids are synthetic); one-wayness is real **only** once the owner
> provisions the real `secret_ref` pepper — *a real deploy on the mock pepper would itself be a FAIL-008 exposure*; and
> (2) whether HMAC+pepper pseudonymization is **legally sufficient**, and the status of the M5-issued
> `PSID_HASH_POLICY_M5_TMP` (explicitly TEMPORARY), is the **OPEN M6-OD-003** privacy/legal decision. The entry judge
> (M6-P2300) mandated that the **exit judge M6-P2309 must weigh whether the internal HMAC/pepper scheme itself needs
> M6-OD-003 sign-off before B1 is deemed closed.** This is the sharpest item in §5.

---

## 1. Band evidence (the M6.2O prompt chain — 7 of 10 prompts run)

| Prompt | Role | Evidence | Ledger | fail_gate | open_blockers | One-line result |
|---|---|---|---|---|---|---|
| **M6-P2300** | JUDGE (entry) | [M6-P2300.json](M6-P2300.json) | **SIGNED** | false | 0 | Entry gate PASS (a **re-judgment** — prior BLOCKED was correct while the spec was missing; operator ran gen_slices.py, spec regenerated, re-judged PASS); CTR-025 DRAFT_LOCKED; **M6-OD-003 flagged as the hard forward condition routed to the exit judge**; B1 = internal PII-minimization (external_send OFF) |
| **M6-P2301** | CODER (plan) | [M6-P2301.json](M6-P2301.json) | PASS | false | 0 | RECORDS the shipped change-set (no re-implementation); honesty finding — config.py byte-identical to M6.2M, 0 raw `.psid` in app, fail-closed pepper, `_smokes` coerce; 0-finding plan red-team |
| **M6-P2302** | CODER (implement) | [M6-P2302.json](M6-P2302.json) | PASS | false | 0 | RECORD leg (no app code written); **executed byte-diff M6.2N→M6.2O app = only `pack_assembler.py` (F2-6); B1 carried unchanged**; **593 passed**; documented the +9 delta vs plan's 584 = 3 official verify artifacts |
| **M6-P2303** | TESTER (build) | [M6-P2303.json](M6-P2303.json) | PASS | false | 0 | Formalized the 2 shipped-green smoke files as official SMK-026/027 (docstring-only, scenario verbatim glyph-exact; assertions unchanged); collect **593**; NOT executed |
| **M6-P2304** | TESTER (run) | [M6-P2304.json](M6-P2304.json) | PASS | false | 0 | Executed: **both smokes PASS** (SMK-026 4/4, SMK-027 3/3), correlation_id + evidence_id recorded (masked); full staged suite **593 passed / 0 failed**, rc 0; proposed 026/027 **executed** (not waived) |
| **M6-P2305** | BOUNDARY_ADVERSARY | [M6-P2305.json](M6-P2305.json) | PASS | false | 0 | 24 executed outcomes (18 DEFENDED / 4 OPEN-non-gate / 2 note); **0** FAIL-007/FAIL-008 breaches; **B1 no-raw-PSID + fail-closed verified; F2-6 closes 3 M6.2M residuals (duck/smoke_id-leak/crash)**; record-leg diff confirms only the F2-6 one-file delta |
| **M6-P2306** | SECURITY_PII | [M6-P2306.json](M6-P2306.json) | PASS | false | 0 | Scan **258 files** — 0 raw PII, 0 real secrets (mock pepper labeled non-secret); **B1 a genuine FAIL-008 reduction (staged); F2-6 + import-gate security-positive**; **explicitly does NOT certify B1 production-safe → M6-OD-003 the hard forward gate**; F-SEC-2O-1 masking family SHRUNK |
| M6-P2307 | PM_ORCHESTRATOR | *this collection* | RUNNING | false | 0 | This index + evidence JSON |
| M6-P2308 | ANALYST_ARCHITECT (docs) | — | **TODO** | — | — | Runbook — not yet run (exit item 5) |
| M6-P2309 | JUDGE (slice gate) | — | **TODO** | — | — | Slice-gate sign-off — not yet run (exit item 6); **must weigh the M6-OD-003 question before B1 is deemed closed** |

**All 7 completed band prompts are PASS with `open_blockers=[]`, `fail_gate_tripped=false`, and no `findings`/`test_results`
integrity keys asserting a tripped gate.** The entry judge (M6-P2300, ledger row 220) is **SIGNED**.

## 2. Artifact inventory (every file the band produced)

**The process debt being reconciled (the reason this slice exists):** the ledger jumps **M6.2M → M6.2O (no M6.2N rows)** — impl/M6.2N was the off-ledger folder where B1 shipped. The two self-disclosed off-ledger evidence files [`M6-B1-PSID-HASH.json`](M6-B1-PSID-HASH.json) + [`M6-F2-6-DUCK-SMOKE.json`](M6-F2-6-DUCK-SMOKE.json) are on disk (the original off-ledger record now retro-certified on-ledger by this slice). **Record-leg honesty was verified** (M6-P2302 + boundary M6-P2305): an executed `diff -rq impl/M6.2N/app impl/M6.2O/app` shows the **only** app delta is `pack_assembler.py` (the F2-6 `_smokes` change); `config.py` byte-identical; every B1 file carried unchanged — **no B1 modification smuggled under "record only".**

**Staged implementation — `04-artifacts/impl/M6.2O/`** (cumulative superset of M6.2M):
- `PLAN.md` (M6-P2301, the record plan) · `IMPLEMENTATION_NOTES.md` (M6-P2302, RECORD leg) · `INVARIANTS_M5_RUNTIME_CONTROLS.md`
- **B1 files (shipped in M6.2N, carried unchanged):** `app/measurement/identity/psid_hash.py` (one-way HMAC-SHA256(pepper, psid); fail-closed `resolve_pepper`; labeled non-secret dev mock), `models/attribution_context.py` (psid → **psid_hash**; `as_stored()`=`to_public()`, no raw psid field), `attribution/resolver.py` (hash at the resolve seam), `funnel/funnel.py` + `funnel/models.py`, `migrations/0013_psid_to_psid_hash` (append-only) + `0006` comment-only
- **F2-6 file (the only M6.2N→M6.2O app delta):** `evidence/pack_assembler.py` (`_smokes` coerces every provided object to a canonical `SmokeResult`, pins `smoke_id` to `spec.smoke_id`, recomputes `recorded`)
- **Tests:** coder regressions `tests/test_b1_psid_hash.py`, `tests/test_duck_smoke_recorded.py`; official smokes `tests/smoke/test_b1_psid_hash_smoke.py` (SMK-026), `test_f2_6_duck_recorded_coerced.py` (SMK-027); the security/OD-011 import gate `tests/test_no_http_client_import.py`; `tests/TEST_MANIFEST.md`. **No new config flag; migrations `0001–0013`.**

**Test report — `04-artifacts/test-reports/M6.2O/`:** [`SMOKE_RESULTS.md`](../../test-reports/M6.2O/SMOKE_RESULTS.md) (M6-P2304)

**Boundary — `04-artifacts/boundary-reports/`:** [`M6.2O_boundary.md`](../../boundary-reports/M6.2O_boundary.md) (M6-P2305); harness `04-boundary/work/attacks/m6_2o_attacks.py`

**Security — `04-artifacts/security-reports/`:** [`M6.2O_security.md`](../../security-reports/M6.2O_security.md) (M6-P2306); scanner `06-security/work/pii_scan_2o.py`

**Entry-judge sign-off — `04-artifacts/evidence/judge/`:** `M6-P2300_JUDGE_FINAL_SIGN_OFF.json` (PASS)

**Test-count reconciliation (count discipline):** **593** full staged suite = **584** coder record-baseline (M6.2M `575` + the shipped B1/F2-6 code and its coder regressions) **+ 9** official verify artifacts (SMK-026 `4` + SMK-027 `3` + the no-HTTP-client import gate `2`). All green, 0 failed / 0 skipped / 0 error, rc 0; the isolated 2-leg run independently confirms **7 passed**.

## 3. Contract checklist (CONTRACT_REGISTER)

| Contract | Status | This slice | Resolution |
|---|---|---|---|
| **M6-CTR-025** `Evidence package` | **DRAFT_LOCKED** (content-level, doc §22) | the assembler F2-6 hardens | Not MISSING; owned at M6.2K. Entry judge M6-P2300 confirmed resolved-for-entry. → **satisfied.** |

No new contract is introduced (retroactive certification of shipped code; no new table — RULE-018).

## 4. Exit-gate checklist → evidence map (all 7 legs of `slices/M6.2O.md`)

| # | Exit-gate item | Status | Evidence |
|---|---|---|---|
| 1 | **psid_hash (B1)** — a raw PSID is never stored on any durable/export surface; `as_stored()` carries only a one-way `psid_hash:` HMAC value, deterministic per pepper + collision-sensitive; production with the pepper env unset fails closed (`PsidHashPolicyError`); the pepper is a secret_ref; the dev mock is labeled non-secret | **MET (staged mechanism)** | SMK-026 PASS 4/4 + `test_b1_psid_hash.py` green; boundary + security **verified** the FAIL-008 reduction (no raw PSID on any surface; one-way; fail-closed production with `PRODUCTION_FLAG` asserted still OFF). **Caveat (§5 B1):** this is a *staged mechanism* proof — the security review does **not** certify B1 production-safe; **M6-OD-003** + the real secret_ref pepper gate any real deploy, and the exit judge M6-P2309 must weigh whether the internal HMAC/pepper scheme needs M6-OD-003 sign-off before B1 is deemed closed. |
| 2 | **duck-coerce (F2-6)** — `_smokes` rebuilds every provided smoke into a canonical frozen `SmokeResult` from its fields, so a duck with a fake `.recorded=True` + blank status/correlation_id/evidence_id cannot mark a mandatory owner smoke recorded — it stays un-recorded and the pack fails closed to NOT_READY | **MET** | SMK-027 PASS 3/3 + `test_duck_smoke_recorded.py` green: duck for M6-SMK-001 → coerced, recorded recomputed False → UNRUN gap → NOT_READY; isolation flips readiness; genuine set → OWNER_REVIEW_REQUIRED. Boundary confirmed it **closes 3 M6.2M residuals** (F-EVID-1 duck variant, N4/X2 smoke_id mislabel/leak, COMP-4 missing-attr crash). |
| 3 | Proposed smoke **M6-SMK-026** executed OR owner-waived | **MET** | PASS 4/4 — **executed** (not waived) |
| 4 | Proposed smoke **M6-SMK-027** executed OR owner-waived | **MET** | PASS 3/3 — **executed** (not waived) |
| 5 | All slice prompts have schema-valid evidence (no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | M6-P2300…2306 present + PASS + clean; M6-P2307 (this) completing; **M6-P2308 (docs) TODO, M6-P2309 (judge) TODO** |
| 6 | Slice-gate judge sign-off exists with verdict PASS | **PENDING** | **M6-P2309 TODO**. The slice-gate Judge reads this index and (per the entry judge) must weigh the M6-OD-003 question |
| 7 | Rollback documented for every change this slice made | **MET** | [IMPLEMENTATION_NOTES §6](../../impl/M6.2O/IMPLEMENTATION_NOTES.md): staged-only → delete the M6.2O tree (M6.2N + M6.2M untouched); per-item B1 files revert/delete, F2-6 `_smokes` revert, coder tests delete; **no live migration** to unwind (`live_migrations=false`); every change is a privacy tightening (B1) or fail-closed tightening (F2-6) |

**Summary:** MET = items 1–4 (both fixes + both smokes) + 7 (rollback) · PENDING = items 5, 6 (the two unrun downstream prompts). No exit item is FAILED or BLOCKED — but item 1's MET is a **staged mechanism** proof, with M6-OD-003 as the hard forward condition (§5 B1).

## 5. Unresolved blockers & carry-forwards

All residuals below are **armed-not-fired**. The load-bearing reachability floor: the boundary + security grep-confirmed the
psid seam and the evidence assembler have **NO `app/api` caller** (the only raw-psid read is the in-process resolver signals
seam, hashed immediately); the `Readiness` enum has no Pass member. Both reviews self-reported `fail_gate_tripped=false`
(boundary 24 outcomes / 0 FAIL-007/008 breaches; security 258-file scan / 0 raw PII / 0 real secrets). This collection
prompt's own `open_blockers` is therefore **empty** — but **B1 (M6-OD-003) is a hard forward condition for the exit judge/owner**.

**Primary forward condition (owner + exit judge M6-P2309):**

- **B1 — M6-OD-003 privacy/legal hash-policy (the sharpest item; owner decides, NOT self-decided).** B1 is **internal PII-minimization** (pseudonymize psid at rest; `external_send` immutably OFF; B1 does not touch the M6.2D CAPI/Offline payload builder), so the mechanism is verifiable-clean **now, in staging**. But two hard conditions gate any **real** deploy: (1) the staged `_MOCK_PEPPER` is a public source constant → a staged synthetic `psid_hash` is brute-force reversible; one-wayness is real **only** with the owner-provisioned `secret_ref` pepper (`M6_PSID_HASH_PEPPER`; production fail-closes if unset) — *a real deploy on the mock pepper would be a FAIL-008 exposure*; (2) whether HMAC+pepper pseudonymization is **legally sufficient**, and the status of the TEMPORARY M5 `PSID_HASH_POLICY_M5_TMP`, is the OPEN **M6-OD-003** decision. The security review **does not certify B1 production-safe**; the entry judge routed to the exit judge M6-P2309 to weigh whether the internal scheme needs M6-OD-003 sign-off **before B1 is deemed closed** for real deploy / cross-module join (C7) / any external send of hashed data.

**Slice-owned residual (new; CODER):**

- **B2 — F-EVID-6 (boundary N2, CODER).** *No trace↔smoke binding.* F2-6 pins `smoke_id` and kills the `.recorded`-lie, but nothing binds `correlation_id`/`evidence_id` **to** the smoke — so a genuine SMK-002 trace filed under the SMK-001 registry key marks SMK-001 recorded with the wrong trace (a cross-slot relabel). Trusted-input. **Fix:** bind the trace ids to the smoke.

**Carried residuals (out of the two-fix scope; armed-not-fired; CODER/owner):**

- **F-SEC-2O-1 — masking-scope family, now SHRUNK (owner M6-OD-012).** `messenger_thread_id`/`live_session_id`/`comment_id` still export raw (B1 hashed only `psid`). The **clearest-PII field `psid` is now hashed** and the `smoke_id` slot is closed by F2-6, so the F-SEC-2I-2/2J-2/2K-1/2L-1/2M-1 masking-scope debt **shrinks** — leaving the live/comment/messenger trace-join ids (`messenger_thread_id` most identifying) → **M6-OD-012**.
- **F-EVID-4 / F-EVID-5 (owner M6-OD-012 / CODER).** `SmokeResult.status` still exported verbatim → M6-OD-012; readiness gates on `recorded` not the PASS/FAIL of `status` → add a `status=='PASS'` gate.
- **`known_refs` untyped param (CODER).** Carried from M6.2M (isinstance guard + materialize once + evaluate once per key).
- **F-GROWTH-1 + reactivation N6 consent subject-bind (CODER).** Out of scope, disclosed in the M6.2J-GROWTH standing blocker.
- **Audit `detail` unmasked sink (boundary MC-6, security note).** Defended by caller discipline; no current/channel path plants a raw psid — monitor at the M6-OD-011 integration.

**What this slice IMPROVED (worth the Judge's note):**

- **B1 is a genuine FAIL-008 reduction** — the M6.2L reversible `mask(psid)` at rest is replaced by a one-way HMAC; raw PSID now reaches no durable/export surface.
- **F2-6 closes three M6.2M residuals I flagged** (F-EVID-1 duck variant, N4/X2 `smoke_id` mislabel/leak, COMP-4 missing-attr crash) → the masking-scope family shrinks.
- **New security-positive import-scan gate** (`test_no_http_client_import.py`): an AST scan fails the build if any `app/**.py` imports an HTTP/egress client — a static complement to `EXTERNAL_SEND=OFF` keeping egress outbox-worker-only even after the M6-OD-011 bind.
- **The process debt is closed** — the two off-ledger changes are now on-ledger with band evidence + a pending judge sign-off, and the record-leg diff proved no code was smuggled under "record only". *(Gate-ID precision: this off-ledger / skipped-gate class is the **M6-FAIL-009 "Gate bypass"** concept per FAIL_GATE_REGISTER — **not** the in-scope FAIL-007/008. **FAIL-008 = raw-PII exposure** is the separate gate B1 reduces, used correctly in §4 leg 1 and the header box. The SIGNED entry judge M6-P2300 labeled this debt "FAIL-008"; the register corrects it to the FAIL-009 concept.)*

**Standing cross-slice governance (carried forward):**

- **`M6-P1000` + `M6-P1309` verdicts remain BLOCKED** (not converted), carried inside the assembled pack.
- **Hard forward gates before any real scale / send / auto-publish / surface / psid_hash-deploy:** M6.2G/H/I/J + M6-OD-011/012 + **M6-OD-003** (B1) remain in force.
- **Open owner decisions:** **M6-OD-003** (hash policy — the B1 forward gate), **M6-OD-012** (masking scope — the shrunk family), **M6-OD-013/M6-OD-014** (still referenced but not yet DECISION_REGISTER rows).
- **Operator hygiene (non-blocking, now flagged across M6.2L / M6.2M / M6.2O):** register **M6-OD-013 + M6-OD-014** and the M5 `PSID_HASH_POLICY_M5_TMP` dependency as `DECISION_REGISTER.md` rows for a complete owner audit trail. None gates this slice.

## 6. Reader's guide for the slice-gate Judge (M6-P2309)

1. **Read order:** this index → the 7 band JSONs (§1) → the two review reports (`M6.2O_boundary.md`, `M6.2O_security.md`) → `SMOKE_RESULTS.md` → `IMPLEMENTATION_NOTES.md` (rollback + record-leg honesty). The exit-gate map is **§4**; the residuals are **§5**.
2. **What is proven (executed + verified):** B1 keeps no raw PSID on any durable/export surface *in staging* (one-way HMAC, hashed at the resolve seam, fail-closed in production with `PRODUCTION_FLAG` asserted OFF, real pepper as secret_ref), and F2-6 fails a lying-duck `.recorded` closed to NOT_READY (closing three M6.2M residuals). Full staged suite **593 passed / 0 failed**; the 2 official smokes **7/7**; boundary **0** in-scope FAIL-007/FAIL-008 breaches with the record-leg diff confirming only the F2-6 one-file app delta; security **0** raw PII / 0 real secrets across 258 files; `config.py` byte-identical to M6.2M.
3. **The mandate the entry judge set for YOU:** weigh whether the internal HMAC/pepper scheme itself needs **M6-OD-003** privacy/legal sign-off **before B1 is deemed closed** — the security review verified the staged mechanism but explicitly **did not certify B1 production-safe** (public mock pepper is reversible; legal sufficiency is OPEN). This is the load-bearing judgment of the slice.
4. **What is NOT yet closed:** exit items **5 & 6** are PENDING purely because the docs prompt (M6-P2308) and this judge (M6-P2309) have not run. Both fix legs (1–2) and both smoke legs (3–4) plus rollback (7) are MET (item 1 as a staged mechanism proof).
5. **Boundary integrity of this collection:** this prompt is `analysis_only` — it read the band evidence and wrote only this index + its evidence JSON. It did not touch `04-artifacts/state/`, did not mark any ledger row, did not modify any file it indexed, computed no verdict, and declared no readiness. `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — untouched.
