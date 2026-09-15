# TEST_MANIFEST — Slice M6.2T (pre-wiring hardening: Scale-Gate clear-path + reader PII-reject + residuals, M6-OD-019)

| Field | Value |
|---|---|
| Prompt | M6-P2803 — `M6_2T_TESTER_BUILD` (mode=build, "do not yet run") |
| Role / agent | TESTER / m6-tester |
| Bound smoke ids | **M6-SMK-032** (1 — `proposed — HARDENING, owner review`) |
| New smoke file | `tests/smoke/test_smk_032_prewiring_hardening.py` (14 collected nodes) |
| Staging root | `04-artifacts/impl/M6.2T/` (cumulative superset of M6.2S) |
| Verify env | `02-tester/.venv` — python 3.12.14 · pytest 8.4.2 · pluggy 1.6.0, run `-B` (`PYTHONDONTWRITEBYTECODE=1`), `-p no:cacheprovider` |
| Build validation | **collect-only** (imports/collects, no assertions executed) — full staged suite 743 collected (= 729 coder baseline + 14 new), 0 collection errors |
| Rules / fail gates in scope | M6-RULE-017 (risk hard veto), M6-RULE-014 (PII masked), M6-RULE-015 (no self-cert); M6-FAIL-006 (no scale action), M6-FAIL-008 (no PII/secret leak) |

> **Governance (immutable — this build flips no flag, opens no egress, wires nothing):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `live_migrations=false`. All four legs
> are **stricter/fail-closed-direction only** (leg 1 can only HOLD more, never clear more — it opens no PASS branch).
> The mapper + reader stay **UNWIRED** (wiring is the S1b / server-bind seam, out of scope). No application code
> changed by the TESTER, no migration, no config change. `M6-P1000` / `M6-P1309` stay BLOCKED. This manifest is a
> BUILD record; execution + per-smoke results are recorded by M6-P2804 (`M6_2T_TESTER_RUN`).

## Bound smoke — scenario / expected (verbatim from SMOKE_REGISTER row M6-SMK-032)

- **Scenario:** "Pre-wiring hardening (M6.2T): (i) a propose with a partial no-active risk map (only the 3 ops-core locks) + a falsy-non-bool lock value at approval; (ii) a monkeypatched PASS branch on _funnel/_dashboard; (iii) a feed row with an email/phone-shaped governance field; (iv) base_flags carrying a RECALL_RISK_KEY + a non-iterable block_reasons"
- **Expected:** "(i) conditions._risk → HOLD not PASS (all-6 required); approval does NOT clear on a falsy-non-bool lock (bool-ness validated); (ii) the HOLD-floor regression FAILs loudly (structural unreachability pinned); (iii) reader rejects fail-closed (feed_error, input-side PII-shape); (iv) recall_risk_contribution rejects the base-key overwrite + from_mapping fail-closed-loud on non-iterable; all stricter/fail-closed, no certified behavior loosened, no flag flip, no egress"

The scenario and expected are pasted verbatim (including the single U+2192 `→` glyph) into the smoke file's module docstring.

## What is under test (code hardened by the CODER in M6-P2802 — the TESTER does not modify it)

- **LEG 1** `conditions._risk` — PASS requires all 6 RISK_LOCKS observed AND none active; a partial no-active map →
  HOLD (was PASS); `{}` → HOLD; active → FAIL (unchanged). `scale_gate._assert_risk_clear_at_approval` — the
  fresh-read clear predicate now requires each of the 6 locks present **as a real `bool`**; a falsy non-bool value
  (0/''/None) no longer clears (falls back to the proposal's Risk row). Stricter/fail-closed only; no PASS branch.
- **LEG 2** `AdsScaleRequest.is_scale_authorized` — True only when APPROVED + APPROVE decision + `overall_status ==
  PASS` + budget cap + rollback; `_funnel`/`_dashboard` have no PASS branch (fail-closed HOLD while M6-OD-002/005
  OPEN), so scale is structurally unreachable. **Unchanged; the smoke pins the floor.**
- **LEG 3** `RegistryFeedReader.apply` — `_looks_like_pii` + a parse-loop guard reject a row whose governance field
  (event_code/event_group/domain) carries a customer-PII shape → `feed_error:pii_shape_in_governance_field`, state
  unchanged (input-side reject, not export masking).
- **LEG 4** `recall_risk_mapper` — `recall_risk_contribution` raises `RecallRiskContributionError` when `base_flags`
  carries a RECALL_RISK_KEY; `OpsCoreAvailabilityResponse.from_mapping` returns None on a non-iterable/bare-string
  `block_reasons`; `RegistryFeedReader._resolve_typed` guards `isinstance(str)` before the enum lookup and surfaces
  `malformed_fields` (N5/N6). **All unchanged by the TESTER.**

## Node → clause coverage (one smoke file for the one bound id; the 4 legs + negatives/fail-closed + controls)

| # | Node(s) | Scenario leg / expected clause proved |
|---|---|---|
| 1 | `test_smk_032_leg_i_partial_no_active_risk_map_holds_not_pass` | (i) `conditions._risk` → HOLD not PASS on a partial no-active map; complete all-6 → PASS (non-vacuous); `{}` → HOLD, active → FAIL (unchanged) |
| 2 | `test_smk_032_leg_i_falsy_non_bool_lock_does_not_clear_at_approval` (×3: 0/''/None) | (i) approval does NOT clear on a falsy-non-bool lock (bool-ness validated) → `ScaleGateViolation`, stays PROPOSED |
| 3 | `test_smk_032_leg_i_control_all_six_real_bool_fresh_read_clears` | control (certified behavior unchanged): all-6 real-bool no-active fresh read clears → APPROVED |
| 4 | `test_smk_032_leg_ii_hold_floor_regression_pins_unreachability` | (ii) both config floors True + APPROVE → `is_scale_authorized` False (overall HOLD); a monkeypatched PASS branch on `_funnel`/`_dashboard` → overall PASS (the sole floor lifts → the regression would FAIL loudly) |
| 5 | `test_smk_032_leg_iii_pii_shape_in_governance_field_rejected` (×3: email/phone/long-digit) | (iii) reader rejects fail-closed `feed_error:pii_shape_in_governance_field`, state unchanged (input-side) |
| 6 | `test_smk_032_leg_iii_control_legit_governance_codes_do_not_trip` | control (non-vacuous): ORDER_VERIFIED/ads.core/ads applies (the PII reject is shape-caused, not blanket) |
| 7 | `test_smk_032_leg_iv_recall_contribution_rejects_base_recall_key` | (iv) `recall_risk_contribution` raises `RecallRiskContributionError` on a base RECALL_RISK_KEY; other-locks base accepted |
| 8 | `test_smk_032_leg_iv_from_mapping_non_iterable_block_reasons_failclosed` | (iv) `from_mapping` → None on non-iterable/bare-str block_reasons; `map_pull_outcome` complete False; valid list parses |
| 9 | `test_smk_032_leg_iv_non_str_enum_sibling_failclosed_and_observable` | (iv N5/N6) non-str enum sibling → PII / BLOCKED_DEFAULT + `malformed_fields`; well-formed → 0 |
| 10 | `test_smk_032_posture_immutable_no_flag_flip_no_egress` | tail: "no flag flip, no egress" — EXTERNAL_SEND/PRODUCTION_FLAG/GLOBAL_GATEWAY_STATE = OFF/OFF/BLOCKED |

## Fixtures / APIs reused (existing patterns — acceptance check 3)

- conftest scale fixtures: `make_scale_context`, `scale_gate`, `scale_store`, `make_owner_decision`; mirrors the
  coder M6.2T regressions `test_m6_2t_gate_clear_path_hardening.py`, `_hold_floor_lock.py`, `_residuals_hardening.py`.
- gate/conditions: `evaluate_conditions`, `ScaleCondition`, `ConditionResult`, `RISK_LOCKS`, `DataQualityStatus`,
  `ScaleGate.propose` / `record_owner_decision`, `ScaleGateViolation`; `conditions._funnel`/`_dashboard` monkeypatch.
- mapper/reader: `OpsCoreAvailabilityResponse`, `RecallRiskContributionError`, `map_risk_flags`, `map_pull_outcome`,
  `recall_risk_contribution`; `RegistryFeedReader`, `DataSensitivity`, `ExternalSendPolicy`.
- PII-shaped test values assembled at runtime (`chr(64)`, digit repetition) — no literal PII in source.

## Exit-gate legs this smoke exercises (slice M6.2T done-gate legs 1–4)

| Leg | Requirement | Node(s) |
|---|---|---|
| 1 | clear-path hardening: `_risk` all-6 to PASS (partial → HOLD); `_assert_risk_clear_at_approval` bool-ness (falsy non-bool does not clear) | 1, 2, 3 |
| 2 | HOLD-floor lock: `is_scale_authorized` structurally unreachable while M6-OD-002/005 OPEN (no PASS branch) | 4 |
| 3 | input-side PII-shape reject: a PII-shaped governance field → `feed_error`, state unchanged (not export masking) | 5, 6 |
| 4 | residuals: base-key overwrite reject (N3); non-iterable block_reasons fail-closed (N9); non-str enum guard + malformed_fields (N5/N6) | 7, 8, 9 |

## Execution plan for M6-P2804 (`M6_2T_TESTER_RUN`)

1. Run the full staged suite from `04-artifacts/impl/M6.2T/`, cache-free (`-B` / `PYTHONDONTWRITEBYTECODE=1`,
   `-p no:cacheprovider`), no shell redirection — expected **743 passed, 0 failed/skipped/error**.
2. Run the bound smoke leg — expected **14 passed**.
3. Record per-smoke PASS/FAIL/BLOCKED + a synthetic masked `correlation_id` / `evidence_id`, verbatim
   scenario/expected, exact commands, and the exit-gate legs into `04-artifacts/test-reports/M6.2T/SMOKE_RESULTS.md`.
4. Report failures, do not fix code under test (TESTER executes and reports only).

> This BUILD does not self-certify PASS (RULE-015). The runner EVIDENCE_GATE and the slice Judge (M6-P2809) decide
> closure — the judge also verifies stricter-only (no certified M6.2G behavior loosened, no test nerfed) and that the
> mapper + reader stay UNWIRED. HARD FORWARD CONDITIONS: M6-OD-002/005 OPEN (leg 2 hardens around them, opens no PASS
> branch); M6-OD-003 OPEN; the S1b wiring seam + live M3 endpoint + M6-OD-011 server-bind/go-live remain hard gates
> before any live wiring / real scale / egress.
