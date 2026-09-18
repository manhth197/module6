# TEST_MANIFEST — Slice M6.2U (recall E2 §3 conformance: sellability no-scale veto + pull-error FAIL, M6-OD-020)

| Field | Value |
|---|---|
| Prompt | M6-P2903 — `M6_2U_TESTER_BUILD` (mode=build, "do not yet run") |
| Role / agent | TESTER / m6-tester |
| Bound smoke ids | **M6-SMK-033** (1 — `proposed — HARDENING, owner review`) |
| New smoke file | `tests/smoke/test_smk_033_recall_e2_conformance.py` (14 collected nodes) |
| Staging root | `04-artifacts/impl/M6.2U/` (cumulative superset of M6.2T) |
| Verify env | `02-tester/.venv` — python 3.12.14 · pytest 8.4.2 · pluggy 1.6.0, run `-B` (`PYTHONDONTWRITEBYTECODE=1`), `-p no:cacheprovider` |
| Build validation | **collect-only** (imports/collects, no assertions executed) — full staged suite 768 collected (= 754 coder baseline + 14 new), 0 collection errors |
| Rules / fail gates in scope | M6-RULE-017 (risk hard veto), M6-RULE-018 (no cross-module ownership), M6-RULE-015 (no self-cert); M6-FAIL-006 (no scale action) |

> **Governance (immutable — this build flips no flag, opens no egress, wires nothing):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `live_migrations=false`. Leg 1 ADDS a
> FAIL to the recall path (a distinct sellability no-scale veto + a pull-error/unverified FAIL) — **stricter/fail-closed
> only, it opens no PASS branch and loosens nothing**. The mapper stays **UNWIRED** (wiring is the S1b / server-bind
> seam, out of scope). No application code changed by the TESTER, no migration, no config change. `M6-P1000` /
> `M6-P1309` stay BLOCKED. This manifest is a BUILD record; execution + per-smoke results are recorded by M6-P2904
> (`M6_2U_TESTER_RUN`).

## Bound smoke — scenario / expected (verbatim from SMOKE_REGISTER row M6-SMK-033)

- **Scenario:** "Recall E2 §3 conformance (M6.2U): (i) an availability response decision=NOT_SELLABLE with all recall/sale/quality flags false; (ii) decision unknown/missing; (iii) a pull error/timeout/429"
- **Expected:** "(i)+(ii) decision not observed as SELLABLE → Scale-Gate Risk row FAIL (sellability no-scale, E2 §1/§3); the recall booleans are still NOT derived from decision (ops-core §4 preserved); (iii) pull error → Risk FAIL (not HOLD) + a running-campaign 'unverified' signal; a SELLABLE + no-active-flag response still clears as before (nothing loosened); no flag flip, no egress"

The scenario and expected are pasted verbatim (including the two U+2192 `→` glyphs) into the smoke file's module docstring.

## What is under test (code hardened by the CODER in M6-P2902 — the TESTER does not modify it)

- **LEG 1** `recall_risk_mapper.map_risk_flags` — the 3 recall booleans (recall = recall_hold OR recall_case_open,
  sale_lock, quality_hold) stay derived from the **presence booleans only** (ops-core §4, never from decision);
  separately, decision is read ONCE for a sellability veto — `decision != "SELLABLE"` (exact string) sets
  `flags["not_sellable"] = True` (a SELLABLE response adds no key → exact-3-key preserved); `RecallRiskRead` gained
  `sellable` / `unverified`. `_incomplete` (pull-error/timeout/429/absent/malformed/non-bool) → `risk_flags =
  {"not_sellable": True}`, `complete=False`, `sellable=False`, `unverified=True`. `recall_risk_contribution`
  byte-identical (carries only the 3 RECALL_RISK_KEYS — the veto never leaks there).
- **LEG 1** `conditions._risk` — after the active-lock FAIL and **before** the M6.2T all-6 completeness HOLD:
  `if ctx.risk_flags.get("not_sellable"): return FAIL`. `not_sellable` is **not** a RISK_LOCK (so `active_risk_locks`,
  the all-6 completeness, and every non-mapper scale context are unchanged). **Unchanged by the TESTER.**
- LEG 2 (migrations/README 0001–0016 + 0017 note, docs-only) and LEG 3 (attribution_context docstring, code
  byte-identical) are docs-only and out of this smoke's runtime scope.

## Node → clause coverage (one smoke file for the one bound id; the 3 scenarios + invariant + controls)

| # | Node(s) | Scenario / expected clause proved |
|---|---|---|
| 1 | `test_smk_033_scenario_i_not_sellable_all_flags_false_fails_risk` | (i) decision=NOT_SELLABLE + all flags false → complete read, recall booleans False, `not_sellable`=True → Risk **FAIL** (sellability no-scale) |
| 2 | `test_smk_033_scenario_ii_unknown_or_missing_decision_fails_risk` (×3: UNKNOWN / wrong-case 'sellable' / None) | (ii) decision not observed exactly SELLABLE → `not_sellable`=True → Risk **FAIL**; recall booleans stay False |
| 3 | `test_smk_033_scenario_iii_pull_error_unverified_fails_risk` (×5: HTTP_429 / TIMEOUT / CONNECTION_ERROR / None / malformed) | (iii) pull error → `unverified`=True, `risk_flags == {not_sellable: True}` → Risk **FAIL** (not HOLD) + the 'unverified' signal |
| 4 | `test_smk_033_recall_booleans_not_derived_from_decision` | ops-core §4 preserved: present recall lock + SELLABLE → recall True (no veto), FAIL from the lock; clean lot + NOT_SELLABLE → recall False + veto |
| 5 | `test_smk_033_sellable_no_active_still_clears` | clear-path preserved (non-vacuous): SELLABLE + no-active + full-6 → Risk **PASS**; a 3-of-6 SELLABLE map → HOLD |
| 6 | `test_smk_033_not_sellable_distinct_from_risk_locks` | `not_sellable` ∉ RISK_LOCKS / RECALL_RISK_KEYS; all-6 no-active → PASS, active → FAIL (non-mapper contexts unchanged) |
| 7 | `test_smk_033_mapper_unwired_no_egress` | "no egress" — no app runtime module imports `recall_risk_mapper` (UNWIRED) |
| 8 | `test_smk_033_posture_immutable_no_flag_flip` | "no flag flip" — EXTERNAL_SEND/PRODUCTION_FLAG/GLOBAL_GATEWAY_STATE = OFF/OFF/BLOCKED |

## Fixtures / APIs reused (existing patterns — acceptance check 3)

- coder-regression helpers `_full6(read)` (merge onto a complete all-6 no-active base to isolate the veto) and
  `_risk_status(ctx)`, mirroring `tests/test_m6_2u_recall_e2_conformance.py`; the shared conftest fixture
  `make_scale_context`.
- gate/mapper surface: `evaluate_conditions`, `ScaleCondition.RISK`, `RISK_LOCKS`, `DataQualityStatus`;
  `map_risk_flags`, `map_pull_outcome`, `OpsCoreAvailabilityResponse`, `RECALL_RISK_KEYS`; `config`.

## Exit-gate legs this smoke exercises (slice M6.2U done-gate leg 1)

| Leg | Requirement | Node(s) |
|---|---|---|
| 1 | decision not observed SELLABLE (NOT_SELLABLE / unknown / missing) → Risk FAIL, distinct from the recall booleans (ops-core §4 preserved); pull error/incomplete → Risk FAIL (not HOLD) + 'unverified'; a SELLABLE + no-active response still clears (nothing loosened; no test nerfed) | 1, 2, 3, 4, 5, 6 |

> LEG 2 (migration README renumber) and LEG 3 (docstring) are docs-only and verified by the CODER + the judge, not
> by this runtime smoke.

## Execution plan for M6-P2904 (`M6_2U_TESTER_RUN`)

1. Run the full staged suite from `04-artifacts/impl/M6.2U/`, cache-free (`-B` / `PYTHONDONTWRITEBYTECODE=1`,
   `-p no:cacheprovider`), no shell redirection — expected **768 passed, 0 failed/skipped/error**.
2. Run the bound smoke leg — expected **14 passed**.
3. Record per-smoke PASS/FAIL/BLOCKED + a synthetic masked `correlation_id` / `evidence_id`, verbatim
   scenario/expected, exact commands, and the exit-gate leg into `04-artifacts/test-reports/M6.2U/SMOKE_RESULTS.md`.
4. Report failures, do not fix code under test (TESTER executes and reports only).

> This BUILD does not self-certify PASS (RULE-015). The runner EVIDENCE_GATE and the slice Judge (M6-P2909) decide
> closure — the judge also verifies stricter-only (a FAIL added, no PASS/clear/allow branch), `not_sellable` not in
> RISK_LOCKS, the certified clear-path (SELLABLE + full-6 → PASS) preserved, the recall booleans still not derived
> from decision, no test nerfed, and the mapper still UNWIRED. HARD FORWARD CONDITIONS: M6-OD-002/005 OPEN (leg 1's
> FAIL is armed-not-fired, opens no PASS branch); M6-OD-003/012 OPEN; the S1b wiring seam + live M3 endpoint + the
> 0017 enforcement SQL + M6-OD-011 server-bind/go-live before any live wiring / real scale / egress. Forward note
> (CODER, recorded): the S1b wiring step must feed the mapper read's `risk_flags` / `sellable` / `unverified`
> directly — not route the sellability veto through `recall_risk_contribution` (which carries only the 3 recall keys).
