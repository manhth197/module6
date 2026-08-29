# SMOKE_RESULTS — Slice M6.2G (Scale Gate / owner-decision workflow)

| Field | Value |
|---|---|
| Prompt | M6-P1604 — `M6_2G_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test** — the M6.2G smoke suite is EXECUTED here and results recorded. Smoke files were authored in M6-P1603 (`M6_2G_TESTER_BUILD`). |
| Smoke ids executed | **M6-SMK-009, M6-SMK-012** (exactly the bound set) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Staging root | `04-artifacts/impl/M6.2G/` (STAGED_ONLY; convention reference, not a live repo) |
| Bound-smoke result | **14 passed, 0 failed — exit 0** |
| Full staged suite | **313 passed, 0 failed, 0 skipped, 0 error — RC 0** |
| Overall | **both bound smoke ids PASS; no failures; nothing patched; nothing scaled** |

> **Governance (immutable — nothing in this run flips a flag, and nothing is ever scaled):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `SCALE_EXECUTION_ENABLED=False`,
> `SCALE_MODEL_RATIFIED=False` (M6-OD-005 OPEN), `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False` (M6-OD-002 OPEN),
> `HASH_POLICY_RATIFIED=False`. The Risk row is a hard veto (RULE-017); there is no executable scale path
> (RULE-010 / FAIL-006); a scale is authorized only via an explicit owner APPROVE **and** a clean PASS — never
> reached in the staged posture. No pricing (M3), order-state (M8), CRM send, or commission (RULE-019).
> `status` is an honest self-report; the runner EVIDENCE_GATE and the slice Judge (M6-P1609) decide closure.

## Per-smoke results (scenario / expected verbatim from SMOKE_REGISTER)

| Smoke ID | Doc ID | Test file | Nodes | Result | Scenario → Expected (verbatim) |
|---|---|---|---|---|---|
| M6-SMK-009 | ADS-P0-009 | `tests/smoke/test_smk_009_recall_sale_lock_scale_fail.py` | 10 | **PASS** | "Recall/Sale Lock active" → "Scale Gate FAIL/HOLD" |
| M6-SMK-012 | ADS-P0-012 | `tests/smoke/test_smk_012_scale_no_owner_approval.py` | 4 | **PASS** | "Scale request không owner approval" → "Không scale" |

**Bound-smoke nodes: 14 (10 + 4), all PASSED.**

### M6-SMK-009 — Recall / Sale Lock active → Scale Gate FAIL/HOLD · **PASS (10/10)**

- `test_smk_009_active_risk_lock_forces_scale_gate_fail[recall|sale_lock|quality_hold|complaint_p0|platform_spam_flag|crm_suppression]` (primary, 6 params) — PASS: each active Risk-row lock → Risk condition FAIL and overall gate FAIL (RULE-017 hard veto, the full doc §16 line 323 row).
- `test_smk_009_recall_locked_request_cannot_be_approved` — PASS: a recall-locked proposal is overall FAIL; an owner APPROVE with recall active is refused (`ScaleGateViolation`); request stays PROPOSED, `is_scale_authorized` False.
- `test_smk_009_neg_unobserved_risk_is_hold_not_pass` — PASS: empty `risk_flags` → Risk fail-closed HOLD, overall HOLD (the HOLD half, never a clean PASS).
- `test_smk_009_neg_risk_recheck_catches_lock_after_clean_proposal` — PASS: a clean proposal (overall HOLD) still cannot be approved if a sale_lock is active at approval time (fresh-read veto, RULE-017).
- `test_smk_009_control_no_active_locks_risk_passes` — PASS: full risk row observed, no lock active → Risk PASS (FAIL is lock-caused); overall still HOLD in the staged posture.

### M6-SMK-012 — Scale request without owner approval → no scale · **PASS (4/4)**

- `test_smk_012_no_owner_approval_means_not_scale_authorized` (primary) — PASS: a proposed request (budget cap + rollback) with no owner decision stays PROPOSED and `is_scale_authorized` False (RULE-015).
- `test_smk_012_neg_gate_cannot_self_approve` — PASS: the gate exposes no `approve/auto_approve/self_approve/approve_all/authorize` (nor `scale/execute/raise_budget/enable_campaign`) entry point; `SCALE_EXECUTION_ENABLED is False`; `PRODUCTION_FLAG==OFF`, `GLOBAL_GATEWAY_STATE==BLOCKED`.
- `test_smk_012_neg_recorded_owner_approve_still_not_scale_in_staged_posture` — PASS: even a recorded owner APPROVE leaves `is_scale_authorized` False because overall is HOLD (`SCALE_MODEL_RATIFIED=False`, M6-OD-005); nothing is executed.
- `test_smk_012_control_owner_reject_is_recorded_no_scale` — PASS: an explicit owner REJECT is recorded (REJECTED) and is never a scale.

## Supporting / regression coverage (inside the 313 full suite, all green)

The M6.2G scale leg tests authored by the coder (M6-P1602) re-ran green as supporting coverage:
`test_scale_gate_risk_veto.py` (7), `test_scale_request_needs_owner_approval.py` (2),
`test_no_executable_scale_path.py` (4), `test_scale_request_lifecycle.py` (5),
`test_scale_conditions_failclosed.py` (4), `test_risk_recheck_at_approval.py` (4) — plus the carried M6.2A–F
tree (273). Full total **313 passed, 0 failed**.

## Commands run (from `04-artifacts/impl/M6.2G/`, no shell redirection, cache-free)

The role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path, so no redirection is used;
`PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider` keep the run cache-free.

```bash
# 1) the two bound M6.2G smoke files (verbose)
python.exe -m pytest -v tests/smoke/test_smk_009_recall_sale_lock_scale_fail.py tests/smoke/test_smk_012_scale_no_owner_approval.py -p no:cacheprovider
#   -> 14 passed in 0.10s ; EXIT 0

# 2) the full staged suite, counted via an in-process pytest_runtest_logreport tally
python.exe -c "<pytest_runtest_logreport tally + pytest.main(['-q','-p','no:cacheprovider'])>"
#   -> COUNTS={'passed': 313, 'failed': 0, 'skipped': 0, 'error': 0} RC=0 ; FAILS=[]
```

> **On counting.** In this harness pytest's terminal summary line is not reliably captured for a long `-q` run,
> so the full-suite total (**313**) was obtained via an in-process `pytest_runtest_logreport` tally
> ({passed:313, failed:0, skipped:0, error:0}) with `pytest.main() RC=0` and an empty failure list — all
> agreeing with the M6-P1603 `--collect-only` total of 313. The two smoke files' `14 passed` summary IS captured.

Cache hygiene: `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

## Correlation / trace ids (all synthetic; PII masked on export)

All ids exercised are **synthetic**, never real customer data: scale-request ids `scr_recall`, `scr_clean`,
`scr_1`, `scr_appr`, `scr_rej`; `scale_target` campaign ref `c1`; owner-decision `actor` `owner_ops` (a synthetic
operator id, masked on export via `app.measurement.masking.mask`); budget caps and rollback strings are literal
request fields (`1000000.0` / `"revert to baseline"`), not actions. No raw phone / email / address / customer_id
/ guest_id / psid / token appears in any test, log, or this report (RULE-014 / H02).

## Boundary / safety observed during this run

- **No executable scale path (RULE-010, FAIL-006):** the gate / store / request / deps exposed no
  raise-budget/enable/open/scale/send/publish/execute method; `SCALE_EXECUTION_ENABLED is False`; nothing was
  scaled, no budget raised, no campaign enabled.
- **Risk hard veto (RULE-017):** every active Risk-row lock forced Risk FAIL / overall FAIL; unobserved risk was
  fail-closed HOLD; the veto was re-checked at approval and refused a late lock.
- **Owner-decision gated (RULE-015 / RULE-020):** no scale was ever authorized — a recorded APPROVE still rolled
  up to HOLD; the system never self-approved.
- **No fix to code under test:** all 313 passed, so nothing needed reporting as a failure, and nothing was
  patched. No application code / migration / external call / order-state / pricing / CRM send / commission /
  flag flip / `04-artifacts/state/` write occurred.

## Exit-gate legs closed by this run (slice M6.2G done-gate)

| Leg | Requirement | Status |
|---|---|---|
| L1 | No auto scale (no code path raises budget / enables campaign / opens audience scale) | met — SMK-009/012 boundary asserts + `test_no_executable_scale_path.py` green |
| L2 | Owner approval required (request carries evidence + budget cap + rollback; transitions only via explicit owner approval) | met — SMK-012 + `test_scale_request_lifecycle.py` green |
| L3 | Smoke M6-SMK-009 executed with recorded result | **PASS** (10/10) |
| L4 | Smoke M6-SMK-012 executed with recorded result | **PASS** (4/4) |

> This run does NOT self-certify gate advancement (RULE-015). It is the honest executed-results record of the
> TESTER. The runner EVIDENCE_GATE and the slice Judge (M6-P1609) decide closure; M6-P1605 (boundary adversary)
> and M6-P1606 (security/PII) review the scale layer next.
