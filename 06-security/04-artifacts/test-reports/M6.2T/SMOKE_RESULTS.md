# SMOKE_RESULTS — Slice M6.2T (pre-wiring hardening: Scale-Gate clear-path + reader PII-reject + residuals, M6-OD-019)

| Field | Value |
|---|---|
| Prompt | M6-P2804 — `M6_2T_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test** — the M6.2T smoke suite is EXECUTED here and results recorded. The smoke leg was authored in M6-P2803 (`M6_2T_TESTER_BUILD`). |
| Smoke ids executed | **M6-SMK-032** (1 — `proposed — HARDENING, owner review`; executed here, not owner-waived) |
| Verify env | `02-tester/.venv` — **python 3.12.14 · pytest 8.4.2 · pluggy 1.6.0**, run `-B` (`PYTHONDONTWRITEBYTECODE=1`), `-p no:cacheprovider` |
| Staging root | `04-artifacts/impl/M6.2T/` (STAGED_ONLY; cumulative superset of M6.2S) |
| Evidence-leg result | **14 passed, 0 failed — exit 0** |
| Full staged suite | **743 passed, 0 failed, 0 skipped, 0 error — RC 0** |
| Overall | **the bound smoke id PASS; no failures; nothing patched; all four hardening legs are stricter/fail-closed; no flag flipped, no egress** |

> **Governance (immutable — nothing in this run flips a flag, opens egress, or wires the mapper/reader):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `live_migrations=false`. All four legs
> are stricter/fail-closed-direction only (leg 1 can only HOLD more, never clear more — it opens no PASS branch). The
> mapper + reader stay UNWIRED (wiring is the S1b / server-bind seam, out of scope). No application code changed by
> the TESTER, no migration, no config change. `M6-P1000` / `M6-P1309` stay BLOCKED. **HARD FORWARD CONDITIONS**
> (disclosed, not resolved here): M6-OD-002/005 OPEN (leg 2 hardens around them, opens no PASS branch); M6-OD-003
> OPEN; the S1b wiring seam + live M3 endpoint + M6-OD-011 server-bind/go-live before any live wiring / real scale /
> egress. `status` is an honest TESTER self-report; the runner EVIDENCE_GATE + the slice Judge (M6-P2809) decide
> closure.

## Per-smoke results (scenario / expected verbatim from SMOKE_REGISTER row M6-SMK-032; PASS)

The `correlation_id` / `evidence_id` are **synthetic** trace ids, shown export-masked
(`app.measurement.masking.mask`, RULE-014); raw synthetic values `corr_2t_032` / `ev_2t_032`.

| Smoke ID | Fix | Test file (`tests/smoke/…`) | Nodes | Result | correlation_id (masked) | evidence_id (masked) | Scenario → Expected (verbatim) |
|---|---|---|---|---|---|---|---|
| M6-SMK-032 | pre-wiring hardening: Scale-Gate clear-path + HOLD-floor lock + reader PII-reject + residuals (M6-OD-019) | `test_smk_032_prewiring_hardening.py` | 14 | **PASS** | `cor***32` | `ev_***32` | "Pre-wiring hardening (M6.2T): (i) a propose with a partial no-active risk map (only the 3 ops-core locks) + a falsy-non-bool lock value at approval; (ii) a monkeypatched PASS branch on _funnel/_dashboard; (iii) a feed row with an email/phone-shaped governance field; (iv) base_flags carrying a RECALL_RISK_KEY + a non-iterable block_reasons" → "(i) conditions._risk → HOLD not PASS (all-6 required); approval does NOT clear on a falsy-non-bool lock (bool-ness validated); (ii) the HOLD-floor regression FAILs loudly (structural unreachability pinned); (iii) reader rejects fail-closed (feed_error, input-side PII-shape); (iv) recall_risk_contribution rejects the base-key overwrite + from_mapping fail-closed-loud on non-iterable; all stricter/fail-closed, no certified behavior loosened, no flag flip, no egress" |

**Evidence-leg nodes: 14, all PASSED.** (10 test functions; `leg_i_falsy` ×3, `leg_iii_pii` ×3.)

### M6-SMK-032 — pre-wiring hardening (4 legs, stricter/fail-closed) · **PASS (14/14)**

- **LEG (i)** `test_smk_032_leg_i_partial_no_active_risk_map_holds_not_pass` — PASS: `conditions._risk` on a partial
  3-of-6 no-active map → **HOLD** (all 6 RISK_LOCKS required to clear); a complete all-6 no-active map → PASS
  (non-vacuous); `{}` → HOLD, an active lock → FAIL (unchanged).
- **LEG (i)** `test_smk_032_leg_i_falsy_non_bool_lock_does_not_clear_at_approval` **[×3: 0 / '' / None]** — PASS: a
  falsy non-bool lock value at approval does not clear via the fresh-read path (bool-ness) → `ScaleGateViolation`,
  request stays PROPOSED.
- **LEG (i)** `test_smk_032_leg_i_control_all_six_real_bool_fresh_read_clears` — PASS (control, certified behavior
  unchanged): an all-6 real-bool no-active fresh read still clears → APPROVED.
- **LEG (ii)** `test_smk_032_leg_ii_hold_floor_regression_pins_unreachability` — PASS: both config floors
  monkeypatched True + best context + owner APPROVE → `is_scale_authorized` False, overall HOLD (`_funnel`/`_dashboard`
  have no PASS branch); monkeypatching those two functions to PASS lifts the sole HOLD floor → overall PASS,
  demonstrating the structural unreachability the regression pins (a real PASS-branch would flip it and fail loudly).
- **LEG (iii)** `test_smk_032_leg_iii_pii_shape_in_governance_field_rejected` **[×3: email / phone / long-digit on
  event_code / event_group / domain]** — PASS: rejected fail-closed `feed_error:pii_shape_in_governance_field`,
  version + rows UNCHANGED (input-side reject, not export masking).
- **LEG (iii)** `test_smk_032_leg_iii_control_legit_governance_codes_do_not_trip` — PASS (control): ORDER_VERIFIED /
  ads.core / ads applies (the PII reject is shape-caused, not blanket).
- **LEG (iv)** `test_smk_032_leg_iv_recall_contribution_rejects_base_recall_key` — PASS: `recall_risk_contribution`
  raises `RecallRiskContributionError` on a base carrying recall / sale_lock / quality_hold; an other-locks base is
  accepted and returns the full 6-lock no-active map (`set(out.keys()) == RISK_LOCKS`, none active).
- **LEG (iv)** `test_smk_032_leg_iv_from_mapping_non_iterable_block_reasons_failclosed` — PASS:
  `from_mapping` → None on a non-iterable / bare-string `block_reasons`; `map_pull_outcome` complete False; a valid
  list / absent parses.
- **LEG (iv)** `test_smk_032_leg_iv_non_str_enum_sibling_failclosed_and_observable` — PASS: a non-str
  `data_sensitivity` / `external_send_policy` → PII / BLOCKED_DEFAULT with `malformed_fields == 2` (N5/N6); a
  well-formed feed → `malformed_fields == 0`.
- **posture** `test_smk_032_posture_immutable_no_flag_flip_no_egress` — PASS: `config.EXTERNAL_SEND == "OFF"`,
  `config.PRODUCTION_FLAG == "OFF"`, `config.GLOBAL_GATEWAY_STATE == "BLOCKED"`.

## Supporting / regression coverage (inside the 743 full suite, all green)

The full staged suite re-ran green: the coder's M6.2T regressions (`test_m6_2t_gate_clear_path_hardening.py`,
`test_m6_2t_hold_floor_lock.py`, `test_m6_2t_residuals_hardening.py`), the honestly-reconciled SMK-030 non-vacuity
control, the carried M6.2A–S tree, and the evidence-pack + P0-smoke suites. Full total **743 passed, 0 failed**
(= 729 coder M6.2T baseline + the 14 new official-smoke nodes). The certified M6.2G scale-gate behaviors re-ran green
(active → FAIL, all-6 real-bool → clear) — no test nerfed.

## Commands run (from `04-artifacts/impl/M6.2T/`, no shell redirection, cache-free)

The role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path, so no redirection is used; `-B`
(`PYTHONDONTWRITEBYTECODE=1`) + `-p no:cacheprovider` keep the run cache-free.

```bash
# 1) full staged suite + per-smoke tally, counted in-process via pytest_runtest_logreport
python.exe -B -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider']); stdout/stderr swallowed>"
#   -> RC 0 ; passed=743 failed=0 skipped=0 error=0 ; FAILS [] ; SMK-032 14/14 (all 'passed')

# 2) the evidence leg isolated (cross-check) via -k node filter
python.exe -B -c "<tally; pytest.main(['-k','test_smk_032','-p','no:cacheprovider'])>"
#   -> RC 0 ; passed=14 failed=0 skipped=0 error=0 ; FAILS [] ; 10 distinct functions present
```

> **On counting.** pytest's terminal summary is not reliably captured in this harness, so the full-suite total
> (**743**) and the per-smoke breakdown came from an in-process `pytest_runtest_logreport` tally
> (`passed=743, failed=0, skipped=0, error=0`) with `pytest.main() RC=0`; the isolated `-k` run independently
> confirms `14 passed`. pytest's own per-item output was swallowed (`redirect_stdout`/`redirect_stderr`). The
> build-side collect-only count (M6-P2803) was 743, matching this executed total.

## Boundary / safety observed during this run

- **Stricter/fail-closed only (leg 1):** `_risk` now HOLDs a partial no-active map (was PASS); the approval bool-ness
  check refuses a falsy non-bool lock. The certified behaviors are preserved as controls (complete all-6 → PASS;
  all-6 real-bool clears; active → FAIL) — no PASS branch opened, no certified M6.2G behavior loosened, no test nerfed.
- **HOLD-floor lock (leg 2, FAIL-006):** `is_scale_authorized` stayed False even with both config floors True + an
  owner APPROVE; the monkeypatch demonstration (test-local, via the `monkeypatch` fixture) confirmed `_funnel`/
  `_dashboard` are the sole structural floor.
- **Input-side PII reject (leg 3, RULE-014/FAIL-008):** a PII-shaped governance field was rejected at parse
  (`feed_error`), never stored or exported; a legit governance code was unaffected. PII-shaped test values were
  assembled at runtime (no literal PII in source).
- **Residuals fail-closed (leg 4):** base-key overwrite rejected (`RecallRiskContributionError`); a non-iterable
  `block_reasons` failed closed to None; a non-str enum sibling resolved to the fail-closed default with observable
  `malformed_fields`.
- **No egress, no flag flipped, no wiring:** the smoke READS `config.EXTERNAL_SEND == "OFF"` (and PRODUCTION_FLAG
  OFF / GLOBAL_GATEWAY_STATE BLOCKED), exercised only the staged gate/mapper/reader, and wrote nothing to
  `04-artifacts/state/`. The mapper + reader stay UNWIRED.
- **No fix to code under test:** all 743 passed, so nothing needed reporting as a failure, and nothing was patched.
  No application code / config change / migration / wiring / flag flip / `04-artifacts/state/` write.

## Exit-gate legs closed by this run (slice M6.2T done-gate)

| Leg | Requirement | Status |
|---|---|---|
| 1 | clear-path hardening: `_risk` all-6 to PASS (partial → HOLD); `_assert_risk_clear_at_approval` bool-ness (falsy non-bool does not clear); certified behavior preserved | met — SMK-032 leg-i partial/falsy/control + coder `test_m6_2t_gate_clear_path_hardening.py` green |
| 2 | HOLD-floor lock: `is_scale_authorized` structurally unreachable while M6-OD-002/005 OPEN (no PASS branch) | met — SMK-032 leg-ii + coder `test_m6_2t_hold_floor_lock.py` green |
| 3 | input-side PII-shape reject: a PII-shaped governance field → `feed_error`, state unchanged (not export masking) | met — SMK-032 leg-iii (×3) + legit-codes control + coder `test_m6_2t_residuals_hardening.py` green |
| 4 | residuals: base-key overwrite reject (N3); non-iterable block_reasons fail-closed (N9); non-str enum guard + malformed_fields (N5/N6) | met — SMK-032 leg-iv (×3 functions) |
| 5 | Proposed smoke M6-SMK-032 executed | **PASS** (14/14) — executed |

> This run does NOT self-certify gate advancement (RULE-015). It is the honest executed-results record of the TESTER.
> The runner EVIDENCE_GATE and the slice Judge (M6-P2809) decide closure — the judge also verifies stricter-only (no
> certified M6.2G behavior loosened, no test nerfed) and that the mapper + reader stay UNWIRED. M6-P2805 (boundary),
> M6-P2806 (security/PII), and the PM evidence-collect M6-P2807 come next. Posture stays BLOCKED/OFF/OFF; the
> M6-OD-002/005 + M6-OD-003 + M6-OD-011 hard forward conditions remain open for the exit judge (no live wiring / real
> scale / egress until decided).
