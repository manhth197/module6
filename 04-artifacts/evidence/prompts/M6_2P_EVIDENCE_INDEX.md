# M6.2P Evidence Index — external_send_policy typed enum (B5 / M6-OD-003 vocabulary half)

| Field | Value |
|---|---|
| Prompt | **M6-P2407** — `M6_2P_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, `analysis_only`) |
| Slice | **M6.2P** — adopt the owner-signed (QĐ-1, 2026-09-07) `ExternalSendPolicy` 4-value enum `{ALLOW_EXTERNAL, INTERNAL_ONLY, BLOCKED_PII, BLOCKED_DEFAULT}` as typed, **fail-closed** code — replacing the raw `Optional[str]` token in `models/consumed.py` + the hard-`False` `permits_external_send()` in `registry/validator.py`. Cumulative superset of M6.2O. Makes the enum vocabulary real; **opens NO egress**. |
| Depends on | M6.2O (entry judge M6-P2400 chains to the M6.2O slice judge M6-P2309 SIGNED) |
| Purpose | Map every band evidence file / artifact / test / boundary / security report to the 5 exit-gate legs; list unresolved blockers — a reader's map for the slice-gate Judge (**M6-P2409**) |
| Collection verdict | **complete** — all 7 band prompts (M6-P2400…2406) PASS with `fail_gate_tripped=false`; the two downstream prompts (docs M6-P2408, judge M6-P2409) are the only PENDING exit items |
| Governance | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` (Final) — immutable, untouched; `config.py` byte-identical to M6.2O (sha256 `911b3238…`). `M6-P1000` + `M6-P1309` verdicts remain **BLOCKED** (not converted). The assembled pack still tops at `OWNER_REVIEW_REQUIRED`. |

> **This is a collection artifact, not a verdict.** Its own `status=PASS` / `open_blockers=[]` means the assembly task is
> complete and unblocked — it does **not** assert the slice passes. Slice-level unresolved items live in **§5**.

> ### ⚠ This slice makes the enum vocabulary real; it does NOT enable external send (read before §4)
> M6-OD-003 is now **PARTIAL**: the **enum-vocabulary half** is owner-signed (QĐ-1 2026-09-07, chief-confirmed —
> `M6-OD-003-enum.json` PARTIAL_DECISION; the register reconciled), and M6.2P adopts it faithfully (M6 invents no value,
> **RULE-018**). The **risk-bearing half — the permit-mapping (which events/fields are `ALLOW_EXTERNAL`) + the Pixel/CAPI/Offline
> hash policy — stays OPEN** (privacy/legal, Sếp). Egress-safety is airtight and verified by 4 independent layers: (1)
> `permits_external_send` returns True **only** for `ALLOW_EXTERNAL` (identity `is`, not `==`); (2) fail-closed coercion —
> `None`/blank/unknown/non-coercible → `BLOCKED_DEFAULT`, never auto-allow; (3) **no real registry row is `ALLOW_EXTERNAL`**
> (permit-mapping OPEN), so every real ACCEPTED event stays `send_permitted=False`; (4) `EXTERNAL_SEND` is Final `"OFF"` and
> the staged transport raises `ExternalSendBlocked` unconditionally — even a hypothetical `ALLOW_EXTERNAL` row opens no real
> send. **Split-authority honesty:** owner+tech-lead legitimately signs the internal fail-closed *vocabulary* (enables no
> egress); the real PII-egress decision is correctly reserved to privacy/legal and held OPEN — not a self-authorization
> end-run. The exit judge **M6-P2409 must confirm no registry row is `ALLOW_EXTERNAL` and `EXTERNAL_SEND` stays Final OFF.**

---

## 1. Band evidence (the M6.2P prompt chain — 7 of 10 prompts run)

| Prompt | Role | Evidence | Ledger | fail_gate | open_blockers | One-line result |
|---|---|---|---|---|---|---|
| **M6-P2400** | JUDGE (entry) | [M6-P2400.json](M6-P2400.json) | **SIGNED** | false | 0 | Entry gate PASS (a **re-judgment** — prior BLOCKED was correct while the QĐ-1 authorization was unfiled; owner filed `M6-OD-003-enum.json` + `XAC_NHAN_QD1-QD3`, register reconciled to PARTIAL, re-judged PASS); CTR-003 DRAFT_LOCKED; **permit-mapping/hash half OPEN → forward condition to the exit judge** |
| **M6-P2401** | CODER (plan) | [M6-P2401.json](M6-P2401.json) | PASS | false | 0 | Plan: `ExternalSendPolicy` enum + `_resolve_send_policy` fail-closed + typed `permits_external_send`, mirroring `_resolve_sensitivity`; adopts owner-signed vocabulary (RULE-018); 0-finding plan red-team |
| **M6-P2402** | CODER (implement) | [M6-P2402.json](M6-P2402.json) | PASS | false | 0 | 2 app files (consumed.py + validator.py); **599 passed** (593 carried M6.2O + 6); config.py byte-identical; egress-bypass hunt 1 candidate → 0 surviving (intended coercion of a genuine token, fail-closed direction intact) |
| **M6-P2403** | TESTER (build) | [M6-P2403.json](M6-P2403.json) | PASS | false | 0 | Authored official SMK-028 (4 nodes), scenario verbatim glyph-exact; collect **603**; static verification 3/3 all-CLEAN (egress-boundary critic egress-safe); NOT executed |
| **M6-P2404** | TESTER (run) | [M6-P2404.json](M6-P2404.json) | PASS | false | 0 | Executed: **SMK-028 PASS 4/4**, correlation_id + evidence_id recorded (masked); full staged suite **603 passed / 0 failed**, rc 0; proposed 028 **executed** (not waived) |
| **M6-P2405** | BOUNDARY_ADVERSARY | [M6-P2405.json](M6-P2405.json) | PASS | false | 0 | 19 executed outcomes (16 DEFENDED / 3 OPEN-non-gate); **0** FAIL-007 breaches; **enum fail-closed over 24 junk inputs; egress crown-jewel verified (no real row ALLOW_EXTERNAL, EXTERNAL_SEND Final OFF)**; residual N1 (narrow-except, fails-loud) |
| **M6-P2406** | SECURITY_PII | [M6-P2406.json](M6-P2406.json) | PASS | false | 0 | Scan **257 files** — 0 raw PII, 0 real secrets (all non-canonical hits carried from M6.2O); **egress-safety airtight (4 layers); BLOCKED_PII a RULE-014 positive**; M6-OD-003 permit/hash half the hard forward gate; N1 → CODER |
| M6-P2407 | PM_ORCHESTRATOR | *this collection* | RUNNING | false | 0 | This index + evidence JSON |
| M6-P2408 | ANALYST_ARCHITECT (docs) | — | **TODO** | — | — | Runbook — not yet run (exit item 3) |
| M6-P2409 | JUDGE (slice gate) | — | **TODO** | — | — | Slice-gate sign-off — not yet run (exit item 4); **must confirm no row is ALLOW_EXTERNAL + EXTERNAL_SEND Final OFF** |

**All 7 completed band prompts are PASS with `open_blockers=[]`, `fail_gate_tripped=false`, and no `findings`/`test_results`
integrity keys asserting a tripped gate.** The entry judge (M6-P2400, ledger row 230) is **SIGNED**.

## 2. Artifact inventory (every file the band produced)

**Owner authorization this slice adopts (verified on disk):** [`M6-OD-003-enum.json`](../decisions/M6-OD-003-enum.json) (PARTIAL_DECISION, decided_by owner+tech-lead, enum vocabulary only, opens no egress) + [`XAC_NHAN_QD1-QD3_2026-09-07.md`](../decisions/XAC_NHAN_QD1-QD3_2026-09-07.md) (chief-auditor QĐ-1 confirmation). M6 adopts the signed vocabulary and invents nothing (RULE-018).

**Staged implementation — `04-artifacts/impl/M6.2P/`** (cumulative superset of M6.2O):
- `PLAN.md` (M6-P2401) · `IMPLEMENTATION_NOTES.md` (M6-P2402)
- **2 patched app files (the only app byte-diff M6.2O→M6.2P):** `app/measurement/models/consumed.py` (`+class ExternalSendPolicy(str, Enum)` {ALLOW_EXTERNAL, INTERNAL_ONLY, BLOCKED_PII, BLOCKED_DEFAULT}; `EventRegistryRow.external_send_policy` retyped `Optional[ExternalSendPolicy]`), `app/measurement/registry/validator.py` (`+_resolve_send_policy` fail-closed → BLOCKED_DEFAULT; `permits_external_send(policy)` → `policy is ExternalSendPolicy.ALLOW_EXTERNAL`; `validate()` coerces then gates). **No new migration** (migrations `0001–0013`); **no new config flag** (config.py byte-identical); sole app reader of the field is `validator.py:140` (grep-verified, no ripple).
- **Tests:** coder regression `tests/test_m6_2p_external_send_policy.py` (6); official smoke `tests/smoke/test_smk_028_external_send_policy_enum.py` (SMK-028, 4 nodes); `tests/TEST_MANIFEST.md`

**Test report — `04-artifacts/test-reports/M6.2P/`:** [`SMOKE_RESULTS.md`](../../test-reports/M6.2P/SMOKE_RESULTS.md) (M6-P2404)

**Boundary — `04-artifacts/boundary-reports/`:** [`M6.2P_boundary.md`](../../boundary-reports/M6.2P_boundary.md) (M6-P2405); harness `04-boundary/work/attacks/m6_2p_attacks.py`

**Security — `04-artifacts/security-reports/`:** [`M6.2P_security.md`](../../security-reports/M6.2P_security.md) (M6-P2406); scanner `06-security/work/pii_scan_2p.py`

**Entry-judge sign-off — `04-artifacts/evidence/judge/`:** `M6-P2400_JUDGE_FINAL_SIGN_OFF.json` (PASS)

**Test-count reconciliation (count discipline):** **603** full staged suite = **599** coder M6.2P baseline (593 carried M6.2O **+ 6** coder M6.2P regressions) **+ 4** official-smoke nodes (tester, SMK-028). Coder baseline before any patch was 593 (byte-parity with M6.2O). All green, 0 failed / 0 skipped / 0 error, rc 0; the isolated 1-leg run independently confirms **4 passed**.

## 3. Contract checklist (CONTRACT_REGISTER)

| Contract | Status | This slice | Resolution |
|---|---|---|---|
| **M6-CTR-003** `event_registry (consumed shape)` | **DRAFT_LOCKED** | the shape carrying `external_send_policy` | Not MISSING; CONSUMED (Core Event Governance), owned/harmonized at M6.2A (M6-P0701). Entry judge M6-P2400 confirmed resolved-for-entry. → **satisfied.** *(Doc-sync note — corrected vs the band: the `CONTRACT_EVENT_REGISTRY.contract.yaml` `external_send_policy` **field annotation is already reconciled** to the owner-signed enum (lines 78–79: vocabulary SIGNED 2026-09-07, RULE-018 satisfied; only the permit-mapping/hash half marked OPEN) per SCHEMA_CHANGELOG row 20 (2026-09-08) — the same batch that set the DECISION_REGISTER M6-OD-003 PARTIAL row. The band evidence flagged it as lagging, but that was true only pre-reconciliation; the current file wins. The one residual is a **stale historical note at contract line 137** ("external_send_policy values = M6-OD-003 (OPEN)") — a non-blocking operator-hygiene item, §5.)* |

No new contract is introduced (adopts the owner-signed vocabulary; no new table — RULE-018).

## 4. Exit-gate checklist → evidence map (all 5 legs of `slices/M6.2P.md`)

| # | Exit-gate item | Status | Evidence |
|---|---|---|---|
| 1 | **external_send_policy typed enum + fail-closed** — new `ExternalSendPolicy` {4 values}; `EventRegistryRow.external_send_policy` coerced to it, None/blank/unknown → `BLOCKED_DEFAULT` (never crash, never auto-allow, mirroring `_resolve_sensitivity` MISSING→PII); `permits_external_send()` True ONLY for `ALLOW_EXTERNAL`; no real row is `ALLOW_EXTERNAL` so every real ACCEPTED event stays `send_permitted=False`; even an `ALLOW_EXTERNAL` row does not egress (`EXTERNAL_SEND` Final OFF); a regression smoke proves each value + the fail-closed default | **MET** | SMK-028 PASS 4/4 + `test_m6_2p_external_send_policy.py` green; **boundary** verified fail-closed over 24 junk inputs + the egress crown-jewel; **security** verified egress-safety airtight (4 layers) + `BLOCKED_PII` a RULE-014 positive. Central leg proven + verified. |
| 2 | Proposed smoke **M6-SMK-028** executed OR owner-waived | **MET** | PASS 4/4 — **executed** (not waived) ([SMOKE_RESULTS.md](../../test-reports/M6.2P/SMOKE_RESULTS.md) · [M6-P2404.json](M6-P2404.json)) |
| 3 | All slice prompts have schema-valid evidence (no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | M6-P2400…2406 present + PASS + clean; M6-P2407 (this) completing; **M6-P2408 (docs) TODO, M6-P2409 (judge) TODO** |
| 4 | Slice-gate judge sign-off exists with verdict PASS | **PENDING** | **M6-P2409 TODO**. The slice-gate Judge reads this index and must confirm no row is `ALLOW_EXTERNAL` + `EXTERNAL_SEND` Final OFF |
| 5 | Rollback documented for every change this slice made | **MET** | [IMPLEMENTATION_NOTES §7](../../impl/M6.2P/IMPLEMENTATION_NOTES.md): staged-only → delete the M6.2P tree (M6.2O untouched); revert consumed.py + validator.py to M6.2O bytes; delete the coder test; **no migration** to unwind; the revert restores the raw-token/hard-False behavior (which permits no more egress — both fail closed) |

**Summary:** MET = items 1, 2, 5 · PENDING = items 3, 4 (the two unrun downstream prompts). No exit item is FAILED or BLOCKED. Item 1 is fully MET (the enum is real + fail-closed) **while opening no egress** — the risk-bearing permit-mapping/hash half of M6-OD-003 is a forward condition (§5), not part of this leg.

## 5. Unresolved blockers & carry-forwards

All residuals below are **armed-not-fired**. The reachability floor: `external_send_policy` is **registry-sourced from M3**
(trusted upstream, plain tokens — not channel free-text), the sole app reader is `validator.py:140`, and egress is
independently blocked by `EXTERNAL_SEND` Final OFF + the staged transport. Both reviews self-reported
`fail_gate_tripped=false` (boundary 19 outcomes / 0 FAIL-007 breaches / no egress opened; security 257-file scan / 0 raw
PII / 0 real secrets). This collection prompt's own `open_blockers` is therefore **empty** — but the **M6-OD-003 permit/hash
half is a hard forward condition for the exit judge/owner.**

**Primary forward condition (owner/privacy-legal + exit judge M6-P2409):**

- **B1 — M6-OD-003 permit-mapping + hash policy (OPEN; the sharpest item).** The **vocabulary** half is SIGNED (QĐ-1) and adopted here; the **permit-mapping** (which events/fields are `ALLOW_EXTERNAL`) + the Pixel/CAPI/Offline **hash policy** stay OPEN (privacy/legal, Sếp). **No event may be classified `ALLOW_EXTERNAL` and no real egress may open until decided.** The exit judge M6-P2409 must confirm no registry row is `ALLOW_EXTERNAL` and `EXTERNAL_SEND` stays Final OFF. (This is the same M6-OD-003 decision whose psid-hash half gated B1 at M6.2O — now PARTIAL, with the enum-vocabulary sub-decision closed.)

**Slice-owned residual (new; CODER robustness):**

- **B2 — N1 coercion totality / narrow-except (CODER, fails-loud not open).** `_resolve_send_policy`'s `except (ValueError, TypeError)` (and the mirrored `_resolve_sensitivity`) is narrower than the consent-coercion's bare `except Exception`; a hostile dunder (`__hash__`/`__eq__`/`.strip()`) raising a non-(ValueError,TypeError) exception propagates uncaught and crashes the coercion. It **fails LOUD** (never `ALLOW_EXTERNAL`, no permit, no egress — fail-away-from-send), **not** fail-open, and is **not channel-reachable** (registry-sourced plain tokens). **Fix:** broaden **both** coercions' `except` to `Exception → fail-closed default` (totality / mirror-parity). Robustness only — not a gate/PII issue.
- **P6/N2 (no action).** A value that *is* `'ALLOW_EXTERNAL'` (str-subclass / hostile-`__eq__` / foreign enum with that value) coerces to `ALLOW_EXTERNAL` — the **intended** coercion of the genuine owner-signed token; the fail-closed direction is unaffected, trusted-input (registry hands plain tokens), no row is `ALLOW_EXTERNAL`, `EXTERNAL_SEND` OFF. A str-exact-type guard would wrongly reject a valid token → no change warranted.

**Carried residuals (unaffected by this slice — M6.2P touches only the enum; armed-not-fired; CODER/owner):**

- **F-SEC-2O-1 — masking-scope family (owner M6-OD-012).** `messenger_thread_id`/`live_session_id`/`comment_id` + `SmokeResult.status` still export raw → M6-OD-012.
- **B1 psid_hash real-pepper + privacy/legal (owner M6-OD-003).** Carried from M6.2O — the real `secret_ref` pepper + legal sufficiency of the HMAC/pepper pseudonymization stay OPEN.
- **F-EVID-4 / F-EVID-5 / F-EVID-6 (CODER / M6-OD-012).** Evidence-honesty residuals carried from M6.2M/M6.2O.
- **`known_refs` untyped param (CODER).** Carried from M6.2M.
- **F-GROWTH-1 + reactivation N6 consent subject-bind (CODER).** Carried; disclosed in the M6.2J-GROWTH standing blocker.

**What this slice IMPROVED (worth the Judge's note):**

- **A RULE-014 positive:** `BLOCKED_PII` makes PII-egress governance **explicit + fail-closed** in the vocabulary, strengthening the egress posture vs the prior raw `Optional[str]` token (an unknown token no longer sits untyped — it coerces to `BLOCKED_DEFAULT`).
- **Honest M6-OD-003 progress:** the enum-vocabulary sub-decision is now real + operationalized, while the risk-bearing permit/hash half stays correctly gated — a genuine split-authority advance, not a self-authorization end-run.
- **The typed gate is non-vacuous:** the control smoke proves `permits_external_send` genuinely returns True for an `ALLOW_EXTERNAL` row (not a dead hard-False) — yet no real row is `ALLOW_EXTERNAL` and `EXTERNAL_SEND` stays OFF, so the gate is real without opening egress.

**Standing cross-slice governance (carried forward):**

- **`M6-P1000` + `M6-P1309` verdicts remain BLOCKED** (not converted), carried inside the assembled pack.
- **Hard forward gates before any real scale / send / auto-publish / surface / egress:** M6.2G/H/I/J + M6-OD-011/012 + **M6-OD-003 permit/hash half** remain in force.
- **Open owner decisions:** **M6-OD-003** (now PARTIAL — vocabulary SIGNED, permit-mapping + hash OPEN), **M6-OD-012** (masking scope).
- **Operator hygiene (non-blocking):** the `CONTRACT_EVENT_REGISTRY.contract.yaml` `external_send_policy` **field annotation is already reconciled** to the owner-signed enum (lines 78–79; SCHEMA_CHANGELOG row 20, 2026-09-08) — the band evidence (M6-P2400/2401/2402/2406) flagged it as lagging, but that was reconciled in the same 2026-09-08 batch, so the current file wins (corrected here vs the carried band claim). The one residual doc-sync is the **stale historical note at contract line 137** ("external_send_policy values = M6-OD-003 (OPEN)"), which should be updated to reference the PARTIAL signature. Also register **M6-OD-013 + M6-OD-014** and the M5 `PSID_HASH_POLICY_M5_TMP` dependency as `DECISION_REGISTER.md` rows. None gates this slice (the canonical decision record authorizes the vocabulary).

## 6. Reader's guide for the slice-gate Judge (M6-P2409)

1. **Read order:** this index → the 7 band JSONs (§1) → the owner authorization (`M6-OD-003-enum.json`, `XAC_NHAN_QD1-QD3`) → the two review reports (`M6.2P_boundary.md`, `M6.2P_security.md`) → `SMOKE_RESULTS.md` → `IMPLEMENTATION_NOTES.md` (rollback). The exit-gate map is **§4**; the residuals are **§5**.
2. **What is proven (executed + verified):** the `ExternalSendPolicy` enum is real, typed, and fail-closed — None/blank/unknown/junk (24 inputs) → `BLOCKED_DEFAULT`, `permits_external_send` True only for `ALLOW_EXTERNAL` (identity), no real row is `ALLOW_EXTERNAL`, and `EXTERNAL_SEND` is Final OFF with the transport blocking unconditionally (4-layer egress-safety). Full staged suite **603 passed / 0 failed**; SMK-028 **4/4**; boundary **0** in-scope FAIL-007 breaches + no egress opened; security **0** raw PII / 0 real secrets across 257 files; `config.py` byte-identical to M6.2O.
3. **The mandate the entry judge set for YOU:** **confirm no registry row is `ALLOW_EXTERNAL` and `EXTERNAL_SEND` stays Final OFF** — the M6-OD-003 permit-mapping + hash policy stay OPEN (privacy/legal, Sếp); this slice signed only the vocabulary.
4. **What is NOT yet closed:** exit items **3 & 4** are PENDING purely because the docs prompt (M6-P2408) and this judge (M6-P2409) have not run. Item 1 (the enum) + item 2 (SMK-028) + item 5 (rollback) are MET.
5. **Boundary integrity of this collection:** this prompt is `analysis_only` — it read the band evidence and wrote only this index + its evidence JSON. It did not touch `04-artifacts/state/`, did not mark any ledger row, did not modify any file it indexed, computed no verdict, declared no readiness, and opened no egress. `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — untouched.
