# M6.2R IMPLEMENTATION_NOTES — Recall-risk mapper: ops-core availability → risk_flags (E2 §3, S1b) (STAGED)

**Prompt**: M6-P2602 (`M6_2R_CODER_IMPLEMENT`) · **Role**: CODER · **Mode**: `implement` · **Gate**: EVIDENCE_GATE
**Slice**: M6.2R — the M6-side **recall-risk mapper**: take an ops-core `/v1/availability/check` response (a value
object / dict — **NOT a live HTTP call**) and produce the three ops-core-sourced `risk_flags` (`recall`,
`sale_lock`, `quality_hold`) that feed the **EXISTING** Scale Gate (**no gate-logic change**). Cumulative superset of
M6.2Q. **Everything STAGED** (mock response in tests; the live HTTP client is the S1b seam / go-live 2026-09-11).

> **Posture (immutable, this slice flips nothing):** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
> `external_send=OFF`, `live_migrations=false`. `app/config.py` **unchanged** (sha256[:16] = `911b32381368f355`) —
> and `scale/conditions.py` + `scale/scale_gate.py` are **byte-identical to M6.2Q** (no gate change). No self-cert
> (RULE-015); the runner gate + JUDGE (M6-P2609) decide.

Ledger verified before acting: **M6-P2602 = RUNNING** (row 252), dependency **M6-P2601 = PASS** (row 251). Built to
the approved `PLAN.md` item-by-item; owner input **M6-OD-017** DECIDED.

## 1. Carry-forward + baseline discipline

- Carried the whole **M6.2Q** tree byte-identical into `04-artifacts/impl/M6.2R/` (excluded caches + the prior
  `PLAN.md`/`IMPLEMENTATION_NOTES.md`; kept this slice's `PLAN.md`). Result: **244 .py = 244 .py, 16 .sql = 16 .sql**.
- **Baseline + parity BEFORE any patch**: `PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider -q` →
  **M6.2Q 631 passed == M6.2R carried 631 passed** (0 fail/error/skip), identical → clean byte-identical carry.
- **After the build**: full suite **647 passed, 0 fail / 0 error / 0 skip** (631 baseline + 16 new mapper tests).
  No test was skipped, relaxed, or deleted.

## 2. What was built (2 new files; NO migration, NO gate change, NO HTTP client, NO new secret)

| File | What |
|---|---|
| **new** `app/measurement/scale/recall_risk_mapper.py` | `OpsCoreAvailabilityResponse` frozen value object (presence booleans `recall_hold`/`sale_lock`/`quality_hold` + additive `recall_case_open=False`; `decision`/`block_reasons`/`sku_ref` RECORDED but **NEVER read**; `from_mapping(dict)` for the dict path) · `RecallRiskRead{risk_flags, complete, reason}` · `RECALL_RISK_KEYS` (strict subset of `conditions.RISK_LOCKS`, import-time drift guard) · `map_risk_flags()` (recall = recall_hold OR recall_case_open, booleans-only, never reads decision; the **single strict-bool choke** — a None/missing/non-bool presence flag → INCOMPLETE) · `map_pull_outcome()` (models the S1b seam's success/timeout/429/connection-error with **NO HTTP**) · `risk_picture_complete()` (caller-side all-6 completeness predicate) · `recall_risk_contribution()` (fail-closed-by-construction merge) |
| **new** `tests/test_m6_2r_recall_risk_mapper.py` | 16 cases covering legs 1/2/3 + the two impl-red-team fixes (16 = 6 mapping + 2 present-lock-FAIL params + 5 pull-error params + 1 non-bool + 2 contribution-safety) |

- **Leg 1 (E2 mapping, M6-OD-017)** — `recall = recall_hold OR recall_case_open` (additive; absent → False),
  `sale_lock`, `quality_hold`; output keys **exactly** the 3 (no fabricated lock); presence **booleans only**
  (a `decision=SELLABLE + recall_hold=True → recall=True` test proves `decision` is never read).
- **Leg 2 (present lock → FAIL even SELLABLE)** — feeding the mapped `{recall:True}` (from `recall_hold` **or**
  `recall_case_open`, `decision=SELLABLE`) to the **existing** `ScaleGate` → Risk row **FAIL** + `record_owner_
  decision` raises `ScaleGateViolation`. No gate code changed.
- **Leg 3 (fail-closed on pull error)** — error/timeout/429/None/malformed/non-bool → `complete=False`,
  `risk_flags={}`; fed to the gate → Risk **HOLD** + approve **REFUSED** (does not clear). Never a `False`
  false-clear, never a fabricated `True`.

## 3. Plan deltas (documented per the prompt — all from the ultracode impl red-team, each re-verified on the real gate)

The implementation red-team (3 finders prototyping + independent skeptics running the real M6.2R code against the
real gate) confirmed **boundary/compat CLEAN** and found **two real defects in my first cut of the mapper**, both
fixed:

1. **MAJOR — `recall_risk_contribution` was a footgun that contradicted its own docstring.** My first cut returned
   the bare 3-of-6 clean map `{recall:F, sale_lock:F, quality_hold:F}` for `base_flags=None`, while the docstring
   claimed it "cannot false-clear". Fed to the real gate that **false-cleared** the RULE-017 recall veto
   (`conditions._risk` reads any non-empty no-active map as PASS). **Fix (stronger than the plan, still no gate
   change):** `recall_risk_contribution` is now **fail-closed BY CONSTRUCTION** — an **active** lock → the map is
   returned (gate FAILs); a **complete** 6-lock picture with no active → the full map (clearing-eligible); an
   **incomplete** picture with no active (the mapper's clean 3-of-6 alone, or an empty read) → **`{}`** (gate HOLD,
   never a false PASS). So the mapper's output is now **always safe to feed to the gate**, and its clean output is
   structurally **never** a standalone clearing map — exactly the plan's stated intent. The false docstring claim
   was removed and `risk_picture_complete()` added as the caller-side completeness predicate. A regression feeds the
   bare merge to the real gate and asserts **HOLD + approve REFUSED**.
2. **MINOR — the value-object path bypassed the strict-bool guard.** My first cut applied `_as_bool` only in
   `from_mapping`; `map_risk_flags` used raw `bool(...)`, so a directly-constructed `OpsCoreAvailabilityResponse`
   (the S1b seam's first-class path) with a non-bool/None presence flag mapped to a **complete clean** read
   (unknown-coerced-to-clear). **Fix:** the strict-bool validation is centralized in **`map_risk_flags`** (the single
   choke both the value-object and the dict paths flow through) — any non-bool presence flag → INCOMPLETE. A
   regression proves `None/0/1/""/"false"/"true"/()/[]` all fail closed on the value-object path.

**New helper vs the plan's item list**: `risk_picture_complete()` is net-new (not named in PLAN §2 item (f)); it is
the caller-side completeness predicate that makes a clearing decision fail-closed without a gate change — a delta
serving the plan's fail-closed intent.

## 4. Forward gate-hardening finding (surfaced to the owner; NOT fixed — no gate change per M6-OD-017)

Both the plan red-team and the impl red-team confirmed a **pre-existing** RULE-017 gate limitation (NOT introduced
by M6.2R): `conditions._risk()` returns **PASS for any non-empty `risk_flags` with no active lock** (it checks
emptiness only, not that all 6 `RISK_LOCKS` are present), and `scale_gate._assert_risk_clear_at_approval`'s all-6
completeness test then falls back to that PASS — so a partial-non-empty map could false-clear. Harmless in the
staged posture (overall = HOLD via Funnel/Dashboard, `is_scale_authorized` stays False). **This slice avoids
triggering it** (the mapper's contribution is fail-closed by construction). **Owner action recommended (separate
decision):** harden `_risk` to require all 6 `RISK_LOCKS` present to PASS, OR require the Scale-Gate assembly to
merge all lock sources (and check `risk_picture_complete`) before any approval-clearing context. Flagged per
RULE-018 (M6 surfaces the risk; the owner owns the gate policy).

## 5. Backward-compat (verified green, not asserted)

- **No gate change** → `conditions.py`/`scale_gate.py`/`config.py` are **byte-identical** to M6.2Q (sha256 checked);
  SMK-009 (Recall/Sale-Lock → FAIL/HOLD) + every carried scale test (`test_scale_gate_risk_veto`,
  `test_risk_recheck_at_approval`, `test_scale_request_lifecycle`, SMK-012) re-run explicitly → all pass.
- **New module + new test only** → no carried test imports the mapper; the module-level `RISK_LOCKS` import + drift
  guard have no side effect on the suite. Migrations stay `0001–0016`.

## 6. Rollback (staged only — M6.2Q untouched)

- **Whole slice**: delete the `04-artifacts/impl/M6.2R/` tree. M6.2Q is byte-identical and untouched; no live
  migration to unwind (`live_migrations=false`).
- **Per item**: the two new files (`recall_risk_mapper.py`, `test_m6_2r_recall_risk_mapper.py`) → delete. **No
  carried file is edited** (no gate change, no migration), so there is nothing to scoped-revert.

## 7. Scope, boundary & governance

- **In scope**: the mapper + fail-closed on pull error + the `ScaleContext.risk_flags` contribution (no gate-logic
  change). **Out of scope (untouched)**: the live HTTP client to ops-core `POST /v1/availability/check` (S1b seam /
  go-live 2026-09-11); the campaign→SKU join (separate data-source decision); the M3-side `block_reason` vocabulary
  / decision gating (M3 owns) + the pause SLA (owner-side). No flag flip; posture stays OFF/BLOCKED/OFF.
- **Boundary intact**: M6 consumes ops-core booleans **for its own Scale Gate**; it does **not** own the recall
  decision, pause a campaign, send CRM, change M3 gating, or compute a commission (RULE-018/019). The response
  carries campaign/SKU refs (not PII); the mapper reads booleans only — **no raw PII**, no secret. `M6-P1000` /
  `M6-P1309` stay BLOCKED.
- **Forward conditions (recorded, NOT resolved)**: M6-OD-002 (thresholds) OPEN + the S1b live-HTTP client +
  campaign→SKU join + M3 block_reason/pause-SLA + M6-OD-011 server-bind/go-live remain hard gates before any live
  recall pull / real scale / egress; plus the §4 gate-hardening finding for the owner.

## 8. Verification commands

```
# carry (excludes caches + prior PLAN/NOTES); baseline + parity BEFORE patch:
PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider -q     # M6.2Q 631 == M6.2R 631
# after build + red-team fixes:
PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider -q     # 647 passed, 0 fail/error/skip
# no gate change: sha256[:16] of config.py/conditions.py/scale_gate.py identical M6.2Q<->M6.2R
# carried scale + SMK-009/012 re-run explicitly -> all pass; migrations 0001..0016 unchanged; caches clean; PII scan clean
```

*Implemented an owner-authorized (M6-OD-017), STAGED, mock-response recall-risk mapper feeding the EXISTING Scale
Gate. No application flag flipped, no migration applied, no gate logic changed, no egress opened, no live HTTP call,
no owner decision resolved. The runner gate + JUDGE decide (RULE-015).*
