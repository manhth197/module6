# M6.2L IMPLEMENTATION NOTES — Post-Pilot Audit Fix Batch (STAGED)

**Prompt**: M6-P2102 (`M6_2L_CODER_IMPLEMENT`) · **Role**: CODER · **Mode**: `implement` · **Gate**: EVIDENCE_GATE
**Follows**: [PLAN.md](PLAN.md) (M6-P2101). Built item-by-item; **no plan-deltas** (the plan already scoped A4 to
the resolver and B4 to the drop-not-raise self-check after the plan-level adversarial review). **Posture unchanged &
immutable**: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all scale/hash/learning
flags `False`, `live_migrations=false`, `config.py` byte-identical to M6.2K. No code declares ROAS Pass / Scale
Ready, self-certifies (RULE-015), flips a flag, applies a migration, sends externally, or exposes raw PII.

> **Status: coder self-reported PASS** (the runner gate + JUDGE decide, RULE-015). The 5 M6-self-doable audit fixes
> are implemented and proven by regression; the suite is green (544 passed) with the two contested carried areas
> (SMK-004 funnel, SMK-007 resolver) verified still green. The implementation was adversarially reviewed AFTER the
> code was written (§5): the plan-level review had already forced two load-bearing corrections (B4/A4) before any
> code; the impl-level review found **3 minor residuals** (1 fixed — B2 binding hardened; 2 documented owner/tester
> notes) and **no CRITICAL/MAJOR**.

## 1. Staging model — cumulative carry-forward

The whole **M6.2K** tree (app + 12 migrations `0001–0012` + full carried suite incl. the 18 P0 smokes) was carried
byte-identical into `04-artifacts/impl/M6.2L/` (caches excluded; M6.2K's `PLAN.md`/`IMPLEMENTATION_NOTES.md` NOT
carried; M6.2L's own `PLAN.md` kept, this file added). Baseline verified green **BEFORE any patch: 523 passed,
parity with the M6.2K collect confirmed (both 523)**. Final suite: **544 passed** (523 carried + 21 new: 19 initial
regressions + 2 review-driven B2 regressions). Subprocess counts; no skips.

## 2. Change set (all under `04-artifacts/impl/M6.2L/`)

| Fix | File | Change |
|---|---|---|
| A3 | `app/measurement/models/attribution_context.py` | +`attribution_id` field (the CTR-002 surrogate id already in migration 0006) + expose in `to_public`/`as_stored` |
| A3 | `app/measurement/attribution/resolver.py` | `derive_attribution_id()` — deterministic `attr_`+sha256(event_id)[:24], 1:1 with the row; set on the context |
| A4 | `app/api/track.py` | read + validate 4 optional ad-hierarchy ids (untrusted; present-but-non-string ⇒ fail-closed SCHEMA_INVALID), thread to normalize |
| A4 | `app/measurement/normalize.py` | 4 optional params → set campaign/adset/ad/live_session on the Zone-A row |
| A4 | `app/measurement/attribution/resolver.py` | `_entry_channels`: append `LIVE_ORGANIC` only when `live.present AND NOT ads.complete` (a complete ad path dominates a co-present live_session as downstream trace) |
| B2 | `app/measurement/evidence/pack_assembler.py` | `_categories`/`_ref_valid`/`_ref_binding`: existence(well-formed) + **(category,key)-binding** + pack-wide uniqueness; optional `known_refs` authenticity oracle |
| B3 | `app/measurement/evidence/gap_blockers.py` | `standing_floor_ok()` membership-count floor (duplicate/shadow/missing standing id ⇒ FAIL) |
| B3 | `app/measurement/evidence/pack_assembler.py` | defensive floor call in `assemble` ⇒ `NOT_READY` if the emitted list fails the floor |
| B4 | `app/measurement/store/measurement_event_store.py` | `materialize`: self-check the **stored row's own** `event_code`; drop non-ORDER_VERIFIED revenue/order_code fail-closed **without raising** |
| B4 | `app/measurement/dashboard/data_mart.py` | `verified_rows()` +`event_code == ORDER_VERIFIED` filter |
| B4 | `app/measurement/growth/reads.py` | `verified_rows()` +`event_code == ORDER_VERIFIED` filter (parallel CRM/Diamond choke, F-GROWTH-3) |

**Patched carried files** are the 8 above (each a fix's named site; `resolver.py` and `pack_assembler.py` each
carry two fixes in distinct regions). **No new migration** (attribution_id column pre-exists in 0006; ad-hierarchy
columns in 0002 — RULE-018). **No new config flag.** **No carried TESTER smoke edited.** Migrations stay `0001–0012`.

**New tests** (`tests/test_m6_2l_{a3,a4,b2,b3,b4}_*.py`) — CODER leg regressions (§3).

## 3. Tests → leg → smoke mapping (TESTER authors the official SMK-019..023 in M6-P2103)

| CODER regression (new) | Proves | Leg | Smoke |
|---|---|---|---|
| `test_m6_2l_a3_attribution_id_trace.py` | attribution_id first-class + in to_public/as_stored; ORDER_VERIFIED row traces id→campaign; deterministic | **1** | SMK-019 |
| `test_m6_2l_a4_ad_hierarchy_intake.py` | track+normalize persist 4 ids; complete-ad FACEBOOK_AD → HIGH via the real API path; non-string rejected; incomplete-ad+live stays MULTI_TOUCH | **2** | SMK-020 |
| `test_m6_2l_b2_evidence_ref_forgery.py` | fake ref / copy-paste-one-ref / wrong-category / wrong-key ⇒ MISSING; genuine refs COMPLETE; oracle tightens existence | **3** | SMK-021 |
| `test_m6_2l_b3_gap_floor_membership.py` | canonical floor OK; duplicate/shadow/missing standing id ⇒ floor FAIL; assembled pack passes + carries all 8 | **4** | SMK-022 |
| `test_m6_2l_b4_verified_lock.py` | materialize drops non-OV revenue (no raise); both verified_rows exclude non-OV ⇒ Rev/ROAS 0 | **5** | SMK-023 |

The OFFICIAL P0 smokes `tests/smoke/test_smk_019..023_*.py` + their recorded correlation_id/evidence_id are the
TESTER's (M6-P2103/2104). No self-run/self-certify (RULE-015).

## 4. Contested carried areas — re-verified green (the two the reviews flagged)

- **B4 / SMK-004 funnel**: `test_quote_in_funnel_not_revenue.py` + `test_smk_004_quote_in_golden_hour_funnel_not_revenue.py`
  (TESTER) call `measurement_store.materialize(..., verified=True)` on a QUOTE_SENT row, un-wrapped, then assert the
  funnel reports 0. The store now **drops** the illegitimate revenue (no raise) → both stay green.
- **A4 / SMK-007 resolver**: `test_smk_007_neg_conflicting_multi_touch` (TESTER) uses an **incomplete** ad path
  (campaign only) + live_session and requires MULTI_TOUCH/LOW → the narrow rule (dominate only when `ads.complete`)
  keeps it MULTI_TOUCH; SMK-013 live-chain (live, no ad) stays LIVE_ORGANIC. All green.
- Set-once RULE-008 (`test_verified_immutable_adjustment` / SMK-018) still raises on an ORDER_VERIFIED overwrite.

## 5. Adversarial review (ultracode) — plan-level (2 fixed pre-code) + impl-level (3 minor)

**Plan-level** (12-agent, before any code): forced two load-bearing corrections into the plan — (a) B4 must
**drop, not raise** (four carried tests call `store.materialize` directly; two un-wrapped on a QUOTE_SENT row); (b)
A4 must include a **resolver rule** reconciling SMK-007 (incomplete-ad+live = MULTI_TOUCH) with SMK-020
(complete-ad+live = HIGH). Both are implemented here.

**Impl-level** (7-agent, against the running code): **no CRITICAL/MAJOR**; 3 CONFIRMED minor items:
- **(B2, fixed) existence was convention-shape-only in the default**: a `ev::{category}::FORGED` ref (right category,
  bogus key) completed a category. **Fixed**: binding is now on **(category, key)** — the demonstrated forgery is
  rejected (wrong key ⇒ unbound), and all carried/regression tests stay green. **Residual (gated on M6-OD-013)**:
  the default path proves *slot-correctness* (well-formed-shape + (category,key)-binding + uniqueness), NOT
  *authenticity* — a forger reconstructing the exact canonical `ev::{category}::{key}` string still passes in the
  default. Authenticity against a registry of issued refs is the injected `known_refs` oracle (a forward
  owner-integration seam, M6-OD-013), exercised by `test_known_refs_authenticity_oracle_tightens_existence`. The two
  named SMK-021 forgeries are defeated in the default path.
- **(SMK-023 wording, tester/operator note) "ROAS = 0" vs `None`**: with the register scenario (a quote, **no ads
  spend**), verified revenue is 0 and ROAS = `_safe_div(0, None)` = **`None`** (fail-closed division, RULE-003), not
  `0`. This is correct-as-designed; the CODER regression asserts `ROAS is None`. **Note for the TESTER writing the
  official SMK-023**: assert `Revenue Verified == 0` and `ROAS is None` (no spend), OR supply a mapped
  `AdsSpendRecord` (then `ROAS == 0.0`). Do not assert `ROAS == 0` under the bare no-spend scenario. (Doc-sync flag:
  the SMOKE_REGISTER prose says "ROAS = 0"; 00-spec is read-only to the coder.)
- **(A4 ad-id PII, owner/security note) ad-hierarchy ids are treated as non-PII platform identifiers**: the 4 ad
  ids get a type/non-empty check but are NOT run through the free-text `payload` RAW_PII tripwire, and
  campaign/adset/ad/live_session are surfaced unmasked by `to_public()` (that export predates A4 — M6.2K already
  emitted these fields; A4 only adds the intake). This matches the audit's classification and the existing
  `page_id`/`session_id` treatment. A full PII scan is deliberately NOT added: the VN-phone heuristic would
  false-positive legitimate long **numeric** platform ids. **Deferred to M6-P2106 (SECURITY_PII) + owner** (also
  covered by standing blocker `M6-OD-012`, PII masking scope): if defense-in-depth is wanted, an **email-only**
  reject on these ids is false-positive-safe; a phone reject is not.

## 6. Scope, governance & boundary (unchanged)

In scope built: exactly the 5 M6-self-doable fixes A3/A4/B2/B3/B4 + CODER regressions. A4's resolver rule is
included because leg 2 mandates the HIGH outcome and the pack's own smokes (SMK-007 ∧ SMK-020) uniquely determine
it — no OPEN owner decision resolved. OUT (owner-gated/cross-module, untouched): B1 psid_hash (M6-OD-003), A1/A2
(M3), A6/B5 (registry+M3/M5/M7), A5/B6/B8 (M6-OD-011/owner), C-band + M5 DEBT-1..4, any flag flip. Boundary intact:
measure/record-only — attribution_id + the ad-hierarchy ids are recorded, never acted on; no pricing/order-state/
CRM-send/commission. `M6-P1000`/`M6-P1309` stay BLOCKED and appear in the assembled pack; the G/H/I/J + OD-011/012
forward conditions stay in the standing-blocker floor. No raw secrets/PII (attribution_id / ad ids are governance/
platform ids; correlation/evidence ids + psid still masked on export). No self-cert; readiness still tops at
OWNER_REVIEW_REQUIRED.

## 7. Rollback

Staged only — baseline rollback = delete the `04-artifacts/impl/M6.2L/` tree (M6.2K untouched). Per item: revert the
named file(s) to their M6.2K bytes; for the two dual-fix files the rollback is a **scoped partial revert** of only
that fix's region (`resolver.py`: A3 `derive_attribution_id`+field-set vs A4 `_entry_channels`; `pack_assembler.py`:
B2 `_categories`/`_ref_*` vs B3 defensive floor call). The 5 new CODER test files roll back by **deletion**. No
migration to unwind (none added); every change is additive or a fail-closed tightening, so a revert restores exact
prior behavior.
