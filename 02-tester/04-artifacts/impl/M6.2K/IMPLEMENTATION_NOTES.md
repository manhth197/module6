# M6.2K IMPLEMENTATION NOTES — Smoke & Evidence Pack (STAGED)

**Prompt**: M6-P2002 (`M6_2K_CODER_IMPLEMENT`) · **Role**: CODER · **Mode**: `implement` · **Gate**: EVIDENCE_GATE
**Follows**: [PLAN.md](PLAN.md) (M6-P2001). Built item-by-item; **no plan-deltas**. **Posture unchanged & immutable**:
`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all scale/hash/learning flags `False`,
`live_migrations=false`. No code declares ROAS Pass / Scale Ready, self-certifies, flips a flag, applies a migration,
or exposes raw PII.

> **Status: coder self-reported PASS** (the runner gate + JUDGE decide, RULE-015). The module-critical invariant of
> THIS slice — the pack **never overstates readiness** (no self-cert, no Pass/Ready, fail-closed on missing evidence,
> honest gap/blocker list) — held under a 3-dimension adversarial review driven against the running code: the
> no-self-cert/scope/schema dimension CLEAN; **4 CONFIRMED** findings (1 MAJOR fail-open + 2 NIT + 1 duplicate)
> **fixed + regressed** (§5). The MAJOR was a genuine fail-open (a mandatory-smoke waiver could hide an un-run smoke)
> — exactly the honesty hole this slice must not have — now closed.

## 1. Staging model — cumulative carry-forward

The whole **M6.2J** tree (final slice state, post-TESTER; all 18 smokes present) was carried forward byte-identical
into `04-artifacts/impl/M6.2K/` (caches excluded; `PLAN.md` kept, this file added). Baseline verified green **BEFORE
any patch: 425 passed, rc 0** (parity with M6.2J confirmed exactly, both 425). Final suite: **451 passed, rc 0** (425
carried + 26 new: 24 initial + 2 review regressions). Subprocess counts; no skips.

## 2. Change set (all under `04-artifacts/impl/M6.2K/`)

**New — the `evidence/` assembly package (read-only, no self-cert)**
| File | Purpose |
|---|---|
| `app/measurement/evidence/smoke_registry.py` | the canonical 18 smoke ids (SMK-001..018) + scenario/expected (doc §21 verbatim) + `owner`/`proposed` status + `test_smk_<nnn>_*.py` bindings. Proposed = executed OR owner-waived. |
| `app/measurement/evidence/categories.py` | the 10 doc §22 categories + mandatory-content requirement keys (English gloss; category-1 keeps the `screenshot_api_db_record` proof-form to match the slice exit-gate). |
| `app/measurement/evidence/models.py` | frozen `SmokeResult` / `CategoryStatus` / `GapBlocker` / `EvidencePack`; `Readiness` enum has **NO PASS/READY member** (only `OWNER_REVIEW_REQUIRED` / `NOT_READY`); `to_public()` masks correlation_id/evidence_id (RULE-014/H02). |
| `app/measurement/evidence/gap_blockers.py` | the canonical `STANDING_GAP_BLOCKERS` (8): M6-P1000 + M6-P1309 BLOCKED, the M6.2G/H/I/J forward conditions, M6-OD-011/012. |
| `app/measurement/evidence/pack_assembler.py` | `EvidencePackAssembler.assemble()` — category COMPLETE only with all mandatory content (else INCOMPLETE, fail-closed); a SmokeResult per registered smoke (un-provided ⇒ un-run); **waiver scope enforced** (a waiver counts ONLY for a proposed smoke; an owner-smoke waiver is stripped, stays un-run); ALWAYS merges `STANDING_GAP_BLOCKERS`; readiness per the ONE rule (§4.4); records the **read-only** posture snapshot. NO pass/ready/certify/sign_off/enable/flag-flip method. |

**Patched (carried-forward)** — none (assembly-only; the smoke suite runs as-is). **No new migration** (doc §13
defines no evidence-pack table — RULE-018). **No new config flag**.

**Tests (new)** + `tests/conftest.py` fixtures (`evidence_assembler`, `full_evidence_refs`, `all_smokes_recorded`,
`make_smoke_result`).

## 3. Tests → leg mapping (TESTER re-runs the P0 matrix + records results)

| Test | Proves | Leg |
|---|---|---|
| `test_evidence_ten_categories_mandatory_content.py` | 10 §22 categories; a missing mandatory key ⇒ INCOMPLETE ⇒ NOT_READY (FAIL-007); empty pack all-incomplete | **L1** |
| `test_smoke_registry_complete_18.py` | all 18 smoke ids; 15 owner + 3 proposed; each binds to a real test file | L1 |
| `test_gap_blocker_list_carries_standing_blockers.py` | the pack ALWAYS carries the 8 standing blockers; they are disclosed but do NOT force NOT_READY (§4.4) | **L1** |
| `test_pack_never_declares_pass_or_ready.py` | readiness enum has no PASS/READY; complete ⇒ OWNER_REVIEW_REQUIRED; incomplete/un-run ⇒ NOT_READY; proposed waiver counts; **owner-smoke waiver rejected** (regression); no self-cert/flag-flip method | **L1** |
| `test_pack_posture_immutable_and_pii_safe.py` | records immutable BLOCKED/OFF/OFF posture; **posture snapshot read-only** (regression); correlation_id/evidence_id masked | L1 |
| `test_full_p0_matrix_runs_green.py` | meta-check the carried 18-smoke suite is present + collectable (the OFFICIAL re-run is the TESTER's) | L1 |

The OFFICIAL P0 re-run (all 18, recorded correlation_id + evidence_id) + the completed owner package is the TESTER's
(M6-P2003/2004) + PM's (M6-P2007). No self-run / self-certify (RULE-015).

## 4. (No plan-deltas)

Everything matches PLAN §5. The ONE readiness rule (PLAN §4.4) is implemented in `pack_assembler._readiness`; the
standing blockers are always disclosed but do not gate readiness.

## 5. Adversarial self-review (ultracode) — 4 CONFIRMED (fixed), no-self-cert dimension CLEAN

A read-only adversarial review (3 dimensions, each finding re-verified by an independent skeptic RUNNING the code)
found the no-self-cert/no-Pass-Ready/scope/schema dimension **CLEAN** (no Pass/Ready method, readiness tops at
OWNER_REVIEW_REQUIRED, no new table, assembly-only), and **four** issues (all fixed):
- **(MAJOR — fail-open, the important one) the owner-waiver escape hatch was unscoped**: `SmokeResult.recorded`
  honored `waived=True` for ANY smoke, so a MANDATORY owner smoke (SMK-001..015) could be waived un-run — bypassing
  the fail-closed readiness gate and vanishing from the honest gap list (FAIL-007 defeated for the 15 mandatory
  smokes). **Fix**: the assembler (which knows the registry) now STRIPS a waiver on any non-proposed smoke, so an
  owner smoke stays un-run → UNRUN_SMOKE gap + NOT_READY. **Regression added** (waiving SMK-001 keeps NOT_READY +
  a gap).
- **(NIT) the recorded posture snapshot was a mutable dict** on a frozen dataclass (could be tampered in-memory, e.g.
  production_flag flipped) → wrapped in `MappingProxyType` (read-only); **regression added** (mutation raises).
- **(NIT) SMK-017 scenario/expected dropped `(CAPI/Offline)` + `platform`** vs SMOKE_REGISTER → restored verbatim.
Config stays authoritative for the posture regardless; the readiness enum never reaches Pass/Ready; the pack carries
the 8 standing blockers and leaks no PII. Not a gate sign-off — the runner gate + JUDGE (M6-P2009) decide.

## 6. Rollback

Staged only — baseline rollback = delete the M6.2K tree (M6.2J untouched). Per-item: new `evidence/` files → delete;
**no carried-forward file is patched**; no migration to unwind (none added). The assembler is pure — it reads smoke
results + evidence refs and returns a report object, writing nothing and changing no posture.

## 7. Scope & governance (unchanged)

In scope built: the P0 smoke registry (18), the 10 doc §22 evidence categories, the evidence-pack result models, the
canonical standing gap/blocker list, and the fail-closed no-self-cert assembler. OUT (owner-only, doc §23): flipping
any gate/flag, declaring ROAS Pass or Scale Ready. OUT (other-owner): re-authoring/re-executing the smokes (TESTER),
pricing/consult/reply/live-ops/order-state/CRM send/commission. The pack NEVER self-certifies (RULE-015) and is
fail-closed on missing evidence (FAIL-007). No raw secrets/PII (correlation_id/evidence_id masked; governance refs
only). `M6-P1000` + `M6-P1309` verdicts stay BLOCKED (not converted) and appear IN the pack; the M6.2G/H/I/J forward
conditions appear IN the pack; production/gateway/external_send stay immutably OFF through M6.2K and into PR/PILOT.
