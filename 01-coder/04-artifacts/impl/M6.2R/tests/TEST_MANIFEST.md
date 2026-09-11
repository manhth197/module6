# TEST_MANIFEST — Slice M6.2R (recall-risk mapper: ops-core availability → Scale-Gate risk_flags, E2 §3/§5, M6-OD-017)

| Field | Value |
|---|---|
| Prompt | M6-P2603 — `M6_2R_TESTER_BUILD` (mode=build, "do not yet run") |
| Role / agent | TESTER / m6-tester |
| Bound smoke ids | **M6-SMK-030** (1 — `proposed — HARDENING, owner review`) |
| New smoke file | `tests/smoke/test_smk_030_recall_risk_mapper_to_scale_gate.py` (11 collected nodes) |
| Staging root | `04-artifacts/impl/M6.2R/` (cumulative superset of M6.2Q) |
| Verify env | `02-tester/.venv` — python 3.12.14 · pytest 8.4.2 · pluggy 1.6.0, run `-B` (`PYTHONDONTWRITEBYTECODE=1`), `-p no:cacheprovider` |
| Build validation | **collect-only** (imports/collects, no assertions executed) — new file 11 nodes RC 0; full staged suite 658 collected (= 647 coder baseline + 11 new), 0 collection errors |
| Rules / fail gates in scope | M6-RULE-017 (risk hard veto), M6-RULE-015 (no self-cert), M6-FAIL-006 (no scale action) |

> **Governance (immutable — this build flips no flag, opens no egress, builds no live client):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `SCALE_MODEL_RATIFIED=False`,
> `live_migrations=false`. The ops-core availability response is a value object / dict built in the test (STAGED);
> the live HTTP client to ops-core `POST /v1/availability/check` is the S1b seam / go-live and is **not** built or
> called here. No application code changed by the TESTER, no gate-logic change, no migration, no real Meta/ops-core
> network. Refs are campaign/SKU refs (not PII). `M6-P1000` / `M6-P1309` stay BLOCKED. This manifest is a BUILD
> record; execution + per-smoke results are recorded by M6-P2604 (`M6_2R_TESTER_RUN`).

## Bound smoke — scenario / expected (verbatim from SMOKE_REGISTER row M6-SMK-030)

- **Scenario:** "Ops-core availability responses fed to the M6 recall mapper: (i) decision=SELLABLE + recall_hold=true (clean-lot); (ii) recall_case_open=true (additive); (iii) a pull error/timeout/429"
- **Expected:** "mapper sets risk_flags['recall']=recall_hold OR recall_case_open, sale_lock, quality_hold; Scale-Gate Risk row FAILs on any presence-flag true EVEN when decision=SELLABLE; the mapper never reads decision/block_reasons; a pull error → incomplete/unknown risk read → gate FAIL (fail-closed, RULE-017); no PII, external_send OFF"

The scenario and expected are pasted verbatim (including the U+2192 `→` glyphs) into the smoke file's module docstring.

## What is under test (code frozen by the CODER in M6-P2602 — the TESTER does not modify it)

- `app/measurement/scale/recall_risk_mapper.py` — `OpsCoreAvailabilityResponse` value object (presence booleans
  `recall_hold` / `sale_lock` / `quality_hold` + additive `recall_case_open=False`; `decision` / `block_reasons` /
  `sku_ref` recorded for provenance, never read); `map_risk_flags` (the single strict-bool choke — `recall =
  recall_hold OR recall_case_open`, other presence booleans map through; any None/missing/non-bool → INCOMPLETE
  empty read); `map_pull_outcome` (models the S1b seam's error/timeout/429/None/dict with no HTTP);
  `recall_risk_contribution` (fail-closed-by-construction merge) + `risk_picture_complete`; `RECALL_RISK_KEYS`
  (strict subset of `conditions.RISK_LOCKS`).
- `app/measurement/scale/conditions.py` — `evaluate_conditions` / `_risk`: any active lock → Risk **FAIL**; empty
  `risk_flags` → Risk **HOLD** (fail-closed, never PASS); non-empty + no active → PASS. **Unchanged by this slice.**
- `app/measurement/scale/scale_gate.py` — `ScaleGate.propose` / `record_owner_decision` re-checks RULE-017 at
  approval (`_assert_risk_clear_at_approval`): active lock → `ScaleGateViolation`; empty/partial fresh read → falls
  back to the proposal's Risk condition (HOLD/FAIL) → `ScaleGateViolation`. **Unchanged by this slice.**

## Node → clause coverage (one smoke file for the one bound id; primary + negatives/fail-closed + control)

| # | Node | Scenario part / expected clause proved |
|---|---|---|
| 1 | `test_smk_030_scenario_i_recall_hold_maps_and_gate_fails_even_when_sellable` | (i) decision=SELLABLE + recall_hold=true → `recall`=True, sale_lock/quality_hold map through; gate Risk **FAIL** despite SELLABLE; owner APPROVE refused (`ScaleGateViolation`), request stays PROPOSED / not authorized |
| 2 | `test_smk_030_scenario_ii_recall_case_open_additive_and_gate_fails` | (ii) recall_case_open=true (recall_hold=false) → `recall`=True (additive OR); gate **FAIL** despite SELLABLE; approve refused; + additive default (absent → false → recall follows recall_hold) |
| 3 | `test_smk_030_scenario_iii_pull_error_incomplete_gate_does_not_clear` (×5: TIMEOUT / HTTP_429 / CONNECTION_ERROR / None / malformed) | (iii) pull error/timeout/429 → INCOMPLETE empty read → Risk **HOLD** (fail-closed, not PASS); approve refused (does not clear) |
| 4 | `test_smk_030_neg_mapper_never_reads_decision_or_block_reasons` | "the mapper never reads decision/block_reasons" — SELLABLE + block_reasons cannot clear a present lock; a scary decision string + block_reasons cannot fabricate a lock (non-vacuous: clean maps to Risk PASS) |
| 5 | `test_smk_030_neg_malformed_or_nonbool_presence_flag_is_failclosed` | fail-closed non-vacuity — missing key (dict path) / non-bool (value-object path) → INCOMPLETE empty, never `bool()`-coerced to a clear; empty → HOLD |
| 6 | `test_smk_030_control_clean_complete_read_maps_non_empty` | non-vacuous control — a clean complete read maps to non-empty `{recall:False,…}` (so the empties above are error-caused); bare 3-of-6 merge collapses to `{}` (partial, never a standalone clearing map) |
| 7 | `test_smk_030_no_pii_external_send_off_and_posture_unchanged` | "no PII, external_send OFF" — `EXTERNAL_SEND==OFF`, `PRODUCTION_FLAG==OFF`, `GLOBAL_GATEWAY_STATE==BLOCKED`; mapper imports no HTTP/transport (no egress, S1b client not built); sku_ref/decision/block_reasons never enter risk_flags |

## Fixtures / APIs reused (existing patterns — acceptance check 3)

- conftest scale fixtures: `make_scale_context`, `scale_gate`, `scale_store`, `make_owner_decision` (same as the
  sibling risk-lock smoke `test_smk_009_recall_sale_lock_scale_fail.py`, whose structure this file follows).
- gate surface: `evaluate_conditions`, `ScaleCondition.RISK`, `RISK_LOCKS`, `DataQualityStatus`,
  `ScaleGate.propose` / `record_owner_decision`, `ScaleGateViolation`.
- mapper surface: `OpsCoreAvailabilityResponse`, `map_risk_flags`, `map_pull_outcome`, `recall_risk_contribution`,
  `risk_picture_complete`, `RECALL_RISK_KEYS`.

## Exit-gate legs this smoke exercises (slice M6.2R done-gate legs 1–3)

| Leg | Requirement | Node(s) |
|---|---|---|
| 1 | E2 mapping (M6-OD-017): `recall`=recall_hold OR recall_case_open, sale_lock, quality_hold; additive; no fabricated lock; presence booleans only | 1, 2, 4, 6 |
| 2 | presence-flag FAIL even when SELLABLE: a mapped present lock (recall_hold; recall_case_open) fails the existing Scale-Gate Risk row despite decision==SELLABLE | 1, 2 |
| 3 | fail-closed on pull error: a pull error/timeout/429/None/malformed → INCOMPLETE read → gate does not clear (RULE-017); no false-clear of an unknown flag | 3, 5 |

## Execution plan for M6-P2604 (`M6_2R_TESTER_RUN`)

1. Run the full staged suite from `04-artifacts/impl/M6.2R/`, cache-free (`-B` / `PYTHONDONTWRITEBYTECODE=1`,
   `-p no:cacheprovider`), no shell redirection — expected **658 passed, 0 failed/skipped/error**.
2. Run the bound smoke leg `tests/smoke/test_smk_030_recall_risk_mapper_to_scale_gate.py` — expected **11 passed**.
3. Record per-smoke PASS/FAIL/BLOCKED + a synthetic masked `correlation_id` / `evidence_id`, verbatim
   scenario/expected, exact commands, and the exit-gate legs into `04-artifacts/test-reports/M6.2R/SMOKE_RESULTS.md`.
4. Report failures, do not fix code under test (TESTER executes and reports only).

> This BUILD does not self-certify PASS (RULE-015). The runner EVIDENCE_GATE and the slice Judge (M6-P2609) decide
> closure. Forward gate-hardening finding (recorded by the CODER for the owner, not this slice): `conditions._risk`
> PASSes a partial-non-empty map — a clearing decision must assemble the full 6-lock picture and check
> `risk_picture_complete` first. HARD FORWARD CONDITIONS: M6-OD-002 (thresholds) OPEN; the S1b live-HTTP client +
> campaign→SKU join + M3 block_reason/pause-SLA + M6-OD-011 server-bind/go-live before any live recall pull / real
> scale / egress.
