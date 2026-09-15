# M6.2T IMPLEMENTATION_NOTES — Pre-wiring hardening: Scale-Gate clear-path + reader PII-reject + residuals (STAGED)

**Prompt**: M6-P2802 (`M6_2T_CODER_IMPLEMENT`) · **Role**: CODER · **Mode**: `implement` · **Gate**: EVIDENCE_GATE
**Slice**: M6.2T — harden the STAGED recall/registry mechanism + the shared **Scale-Gate clear-path** before any live
wiring. All four legs are **stricter / fail-closed-direction ONLY** (leg 1 can only HOLD more, never clear more; opens
no PASS branch). The mapper + reader stay **UNWIRED**. Cumulative superset of M6.2S. **No flag flipped, no egress.**

> **Posture (immutable, this slice flips nothing):** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
> `external_send=OFF`, `live_migrations=false`. `app/config.py` **unchanged** (sha256[:16] = `911b32381368f355`) —
> and `models/consumed.py` + `registry/validator.py` are **byte-identical to M6.2S** (reuse-only). No self-cert
> (RULE-015); the runner gate + JUDGE (M6-P2809) decide.

Ledger verified: **M6-P2802 = RUNNING** (row 272), dependency **M6-P2801 = PASS** (row 271). Built to the approved
`PLAN.md` item-by-item; owner input **M6-OD-019** DECIDED.

## 1. Carry-forward + baseline discipline

- Carried the whole **M6.2S** tree byte-identical into `04-artifacts/impl/M6.2T/` (excluded caches + the prior
  `PLAN.md`/`IMPLEMENTATION_NOTES.md`; kept this slice's `PLAN.md`). Result: **251 .py = 251 .py, 16 .sql = 16 .sql**.
- **Baseline + parity BEFORE any patch**: `PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider -q` →
  **M6.2S 716 passed == M6.2T carried 716 passed** (0 fail/error/skip). (The plan's earlier "688" was M6.2S's
  implement-time count; the SIGNED tree collects **716** — the real baseline used here, per the plan's corrected §1.)
- **After the build**: full suite **729 passed, 0 fail / 0 error / 0 skip** (716 baseline + 13 new). The gate
  invariant **baseline ≤ final (716 ≤ 729)** holds; no test skipped/relaxed/deleted.

## 2. What was built (4 stricter carried-file edits + SMK-030 reconciliation + 3 regressions)

Verified by a M6.2S→M6.2T diff of the 4 edited files: **every behavioral addition is a HOLD / reject / raise / more-
fail-closed coercion — NO PASS / clear / allow branch added** (stricter-only, per the slice's leg-1 requirement).

| File / edit | Change (stricter/fail-closed ONLY) |
|---|---|
| `app/measurement/scale/conditions.py` `_risk` (LEG 1) | PASS now requires a COMPLETE read: `if not all(lock in ctx.risk_flags for lock in RISK_LOCKS): return HOLD` — a **partial no-active map → HOLD** (was PASS). all-6-no-active → PASS, `{}` → HOLD, any active → FAIL (all unchanged). Closes the M6.2R forward finding; opens NO PASS branch. |
| `app/measurement/scale/scale_gate.py` `_assert_risk_clear_at_approval` (LEG 1) | the clear predicate gains **bool-ness**: `all(lock in current_risk_flags and isinstance(current_risk_flags[lock], bool) ...)` — a falsy non-bool lock value (`0`/`''`/`None`) no longer clears via the fresh-read path (only a real `bool`). |
| `tests/smoke/test_smk_030_...py` line ~159 (LEG 1 honest reconciliation) | the non-vacuity control (mapper CLEAN 3-of-6 map → PASS) is **re-pointed at a FULL all-6 no-active map** (still asserts PASS — the gate CAN reach PASS with a complete read) **and** a new assertion `3-of-6 → HOLD` is added. A **strengthening, NOT a nerf** (the "gate can PASS" proof is preserved, not gutted). This is the ONE carried test the leg-1 change affects (red-team-found + reconciled). |
| `app/measurement/adapters/registry_feed_reader.py` (LEG 3 + N5/N6) | `_looks_like_pii()` + a parse-loop guard: a governance field (`event_code`/`event_group`/`domain`) carrying a customer-PII shape (email/phone/psid) → `feed_error:pii_shape_in_governance_field` (reject, state UNCHANGED; input-side, NOT export masking). `_resolve_typed()` guards `isinstance(str)`/enum before the value-lookup (N5, non-str → fail-closed default) + `malformed_fields` observability on the result (N6). |
| `app/measurement/scale/recall_risk_mapper.py` (LEG 4 N3 + N9) | `RecallRiskContributionError` + a guard: `recall_risk_contribution` rejects a `base_flags` carrying any RECALL_RISK_KEY (N3, no silent overwrite). `from_mapping` fail-closed on a non-iterable / bare-string `block_reasons` → `None` (N9, prevents the `tuple(<non-iterable>)` crash). |

| **new** `tests/test_m6_2t_gate_clear_path_hardening.py` | LEG 1 regression (partial→HOLD, full-6→PASS, {}→HOLD, active→FAIL; all-6-real-bool clears at approval; a falsy-non-bool lock does not clear). |
| **new** `tests/test_m6_2t_hold_floor_lock.py` | LEG 2 regression (no app change): `is_scale_authorized` structurally unreachable even with BOTH config floors monkeypatched True (`_funnel`/`_dashboard` have no PASS branch → overall HOLD). |
| **new** `tests/test_m6_2t_residuals_hardening.py` | LEG 3 (PII reject + a legit-governance-code non-trip) + LEG 4 (N5/N6 non-str sibling; N3 base-key reject; N9 non-iterable block_reasons). PII-shaped test values assembled at runtime (no literal PII in source). |

- **Leg 1** → SMK-032(i); **Leg 2** → SMK-032(ii); **Leg 3** → SMK-032(iii); **Leg 4** → SMK-032(iv).

## 3. Plan deltas (documented per the prompt)

1. **Baseline figure 688 → 716** — the plan's §1/§5 already carried this correction (surfaced by the plan red-team);
   the implement uses the real M6.2S SIGNED collect **716**.
2. No other deviation — the implementation follows the approved (red-team-corrected) plan item-by-item, including the
   pre-specified honest SMK-030:159 reconciliation.

**Impl red-team (ultracode, 2 dimensions + independent skeptics): BOTH CLEAN (0 findings).** The gate-stricter-no-nerf
dimension confirmed on the running code that the `_risk`/`_assert` edits are stricter-only (no new PASS/clear
branch) and the SMK-030 reconciliation is an honest strengthening (not a nerf; the gate-can-PASS proof preserved).
The legs-3/4 dimension confirmed the PII reject has no false-positive on legitimate governance codes
(ORDER_VERIFIED / ads.core / v20260915 / evt_123 etc. do not trip), the N5/N6 non-str handling is fail-closed +
observable, and N3/N9 fail-closed without crashing.

## 4. Backward-compat & honest reconciliation (verified green)

- **Stricter-only, ONE carried break, honestly reconciled** → the M6.2S→M6.2T diff of the 4 edited files shows only
  HOLD/reject/raise/more-fail-closed additions (no PASS/clear/allow). The sole carried behavior change is the
  official SMK-030:159 non-vacuity control (3-of-6 → PASS became → HOLD), reconciled honestly (§2) — a strengthening,
  never a nerf, never skipped/relaxed. Every other carried scale test (`test_scale_gate_risk_veto`,
  `test_risk_recheck_at_approval`, SMK-009, the M6.2R mapper tests) is UNCHANGED.
- **Reuse-only, no shared-surface loosening** → `config.py` / `models/consumed.py` / `registry/validator.py` are
  **byte-identical** to M6.2S (sha256 checked). Migrations stay `0001–0016`. Mapper + reader stay **UNWIRED** (no
  `app/` file imports them — verified).

## 5. Rollback (staged only — M6.2S untouched)

- **Whole slice**: delete the `04-artifacts/impl/M6.2T/` tree. M6.2S is byte-identical and untouched; no live
  migration to unwind (`live_migrations=false`).
- **Per item**: the 4 edited carried files (`conditions.py`, `scale_gate.py`, `recall_risk_mapper.py`,
  `registry_feed_reader.py`) → scoped revert of the stricter guard(s) to M6.2S bytes; `test_smk_030_*` → revert the
  non-vacuity assertion to the M6.2S bytes (3-of-6 → PASS); the 3 new test files → delete. Every change is a
  fail-closed tightening; a revert restores prior (looser) behaviour.

## 6. Scope, boundary & governance

- **In scope**: the 4 hardening legs (all stricter/fail-closed). **Out of scope (untouched)**: WIRING the mapper/
  reader into any `app/` caller (S1b seam / server-bind); the live HTTP client / real ops-core pull / real M3
  endpoint (ENTRY-003 V221); the Scale-Gate thresholds/model (M6-OD-002/005) or ANY change that opens a PASS branch;
  flag flips. Posture stays OFF/BLOCKED/OFF.
- **Boundary intact**: leg 1 only makes the gate FAIL/HOLD more (never clears more, opens no PASS branch, executes no
  scale — RULE-010/FAIL-006); the mapper+reader stay UNWIRED; no CRM/egress/commission (RULE-018/019); leg 3 is an
  input-side PII reject (RULE-014/FAIL-008), never storing/exporting the PII. `M6-P1000` / `M6-P1309` stay BLOCKED.
- **Forward conditions (recorded, NOT resolved)**: M6-OD-002/005 OPEN (leg 2 hardens around them, opens no PASS
  branch); M6-OD-003 OPEN; the S1b wiring seam + live M3 endpoint + M6-OD-011 server-bind/go-live remain hard gates
  before any live wiring / real scale / egress.

## 7. Verification commands

```
# carry (excludes caches + prior PLAN/NOTES); baseline + parity BEFORE patch:
PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider -q     # M6.2S 716 == M6.2T 716
# after build:
PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider -q     # 729 passed, 0 fail/error/skip
# stricter-only: a M6.2S->M6.2T diff of the 4 edited files shows only HOLD/reject/raise (no PASS/clear/allow)
# reuse-only: sha256[:16] of config.py/consumed.py/validator.py identical M6.2S<->M6.2T
# migrations 0001..0016 unchanged; mapper+reader UNWIRED (no app/ import); caches clean; PII scan clean
```

*Implemented an owner-authorized (M6-OD-019), STAGED, stricter/fail-closed-direction hardening of the shared
Scale-Gate clear-path + the UNWIRED recall/registry mechanism. No application flag flipped, no migration applied, no
live wiring, no egress, no PASS branch opened, no certified M6.2G behavior loosened, no test nerfed (the SMK-030:159
reconciliation is a strengthening). The runner gate + JUDGE decide (RULE-015).*
