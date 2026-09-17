# SMOKE_RESULTS — Slice M6.2U (recall E2 §3 conformance: sellability no-scale veto + pull-error FAIL, M6-OD-020)

| Field | Value |
|---|---|
| Prompt | M6-P2904 — `M6_2U_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test** — the M6.2U smoke suite is EXECUTED here and results recorded. The smoke leg was authored in M6-P2903 (`M6_2U_TESTER_BUILD`). |
| Smoke ids executed | **M6-SMK-033** (1 — `proposed — HARDENING, owner review`; executed here, not owner-waived) |
| Verify env | `02-tester/.venv` — **python 3.12.14 · pytest 8.4.2 · pluggy 1.6.0**, run `-B` (`PYTHONDONTWRITEBYTECODE=1`), `-p no:cacheprovider` |
| Staging root | `04-artifacts/impl/M6.2U/` (STAGED_ONLY; cumulative superset of M6.2T) |
| Evidence-leg result | **14 passed, 0 failed — exit 0** |
| Full staged suite | **768 passed, 0 failed, 0 skipped, 0 error — RC 0** |
| Overall | **the bound smoke id PASS; no failures; nothing patched; leg 1 ADDS a FAIL (stricter/fail-closed); the certified clear-path is preserved; no flag flipped, no egress** |

> **Governance (immutable — nothing in this run flips a flag, opens egress, or wires the mapper):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `live_migrations=false`. Leg 1 ADDS a
> FAIL to the recall path (a distinct sellability no-scale veto + a pull-error/unverified FAIL) — stricter/fail-closed
> only; it opens no PASS branch and loosens nothing. The mapper stays UNWIRED (wiring is the S1b / server-bind seam,
> out of scope). No application code changed by the TESTER, no migration, no config change. `M6-P1000` / `M6-P1309`
> stay BLOCKED. **HARD FORWARD CONDITIONS** (disclosed, not resolved here): M6-OD-002/005 OPEN (leg 1's FAIL is
> armed-not-fired, opens no PASS branch); M6-OD-003/012 OPEN; the S1b wiring seam + live M3 endpoint + the 0017
> enforcement SQL + M6-OD-011 server-bind/go-live before any live wiring / real scale / egress. `status` is an honest
> TESTER self-report; the runner EVIDENCE_GATE + the slice Judge (M6-P2909) decide closure.

## Per-smoke results (scenario / expected verbatim from SMOKE_REGISTER row M6-SMK-033; PASS)

The `correlation_id` / `evidence_id` are **synthetic** trace ids, shown export-masked
(`app.measurement.masking.mask`, RULE-014); raw synthetic values `corr_2u_033` / `ev_2u_033`.

| Smoke ID | Fix | Test file (`tests/smoke/…`) | Nodes | Result | correlation_id (masked) | evidence_id (masked) | Scenario → Expected (verbatim) |
|---|---|---|---|---|---|---|---|
| M6-SMK-033 | recall E2 §3 conformance: sellability no-scale veto + pull-error FAIL (M6-OD-020) | `test_smk_033_recall_e2_conformance.py` | 14 | **PASS** | `cor***33` | `ev_***33` | "Recall E2 §3 conformance (M6.2U): (i) an availability response decision=NOT_SELLABLE with all recall/sale/quality flags false; (ii) decision unknown/missing; (iii) a pull error/timeout/429" → "(i)+(ii) decision not observed as SELLABLE → Scale-Gate Risk row FAIL (sellability no-scale, E2 §1/§3); the recall booleans are still NOT derived from decision (ops-core §4 preserved); (iii) pull error → Risk FAIL (not HOLD) + a running-campaign 'unverified' signal; a SELLABLE + no-active-flag response still clears as before (nothing loosened); no flag flip, no egress" |

**Evidence-leg nodes: 14, all PASSED.** (8 test functions; `scenario_ii` ×3, `scenario_iii` ×5.)

### M6-SMK-033 — recall E2 §3 conformance · **PASS (14/14)**

- **(i)** `test_smk_033_scenario_i_not_sellable_all_flags_false_fails_risk` — PASS: decision=NOT_SELLABLE + all flags
  false → a COMPLETE read whose recall booleans are all False (NOT derived from decision) and whose distinct
  sellability veto sets `not_sellable=True`; merged onto an otherwise-clearing full-6 no-active picture, the
  Scale-Gate Risk row is **FAIL** (sellability no-scale, E2 §1/§3).
- **(ii)** `test_smk_033_scenario_ii_unknown_or_missing_decision_fails_risk` **[×3: UNKNOWN / wrong-case 'sellable'
  / None]** — PASS: a decision not observed exactly `SELLABLE` sets `not_sellable=True` → Risk **FAIL**; the recall
  booleans stay False.
- **(iii)** `test_smk_033_scenario_iii_pull_error_unverified_fails_risk` **[×5: HTTP_429 / TIMEOUT /
  CONNECTION_ERROR / None / malformed]** — PASS: an incomplete read is UNVERIFIED → `complete=False`,
  `unverified=True`, `risk_flags == {"not_sellable": True}` (recall booleans unobserved) → Risk **FAIL** (not HOLD;
  the M6.2U conformance, asserted on the raw output and via full-6) + the running-campaign 'unverified' signal.
- `test_smk_033_recall_booleans_not_derived_from_decision` — PASS (ops-core §4 preserved): a present recall lock
  FAILs even when decision=SELLABLE (recall from the presence boolean, no veto); a clean lot with NOT_SELLABLE keeps
  recall False (decision fabricates no recall boolean) while setting the veto.
- `test_smk_033_sellable_no_active_still_clears` — PASS (clear-path preserved, non-vacuous): SELLABLE + no-active +
  COMPLETE all-6 → Risk **PASS** (exact-3-key, no veto — nothing loosened); a partial SELLABLE 3-of-6 map → HOLD.
- `test_smk_033_not_sellable_distinct_from_risk_locks` — PASS: `not_sellable` ∉ RISK_LOCKS / RECALL_RISK_KEYS (all-6
  completeness + non-mapper contexts unchanged; all-6 no-active → PASS, active → FAIL).
- `test_smk_033_mapper_unwired_no_egress` — PASS: no app runtime module imports `recall_risk_mapper` (UNWIRED → no
  egress).
- `test_smk_033_posture_immutable_no_flag_flip` — PASS: `config.EXTERNAL_SEND == "OFF"`,
  `config.PRODUCTION_FLAG == "OFF"`, `config.GLOBAL_GATEWAY_STATE == "BLOCKED"`.

## Supporting / regression coverage (inside the 768 full suite, all green)

The full staged suite re-ran green: the coder's M6.2U regression `tests/test_m6_2u_recall_e2_conformance.py` (11
cases), the honestly-reconciled M6.2R/SMK-030 mapper tests (strengthenings, not nerfs), the carried M6.2A–T tree,
and the evidence-pack + P0-smoke suites. Full total **768 passed, 0 failed** (= 754 coder M6.2U baseline + the 14
new official-smoke nodes). The certified clear-path (SELLABLE + full-6 → PASS) and the ops-core-§4 invariant re-ran
green — nothing loosened, no test nerfed.

## Commands run (from `04-artifacts/impl/M6.2U/`, no shell redirection, cache-free)

The role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path, so no redirection is used; `-B`
(`PYTHONDONTWRITEBYTECODE=1`) + `-p no:cacheprovider` keep the run cache-free.

```bash
# 1) full staged suite + per-smoke tally, counted in-process via pytest_runtest_logreport
python.exe -B -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider']); stdout/stderr swallowed>"
#   -> RC 0 ; passed=768 failed=0 skipped=0 error=0 ; FAILS [] ; SMK-033 14/14 (all 'passed')

# 2) the evidence leg isolated (cross-check) via -k node filter
python.exe -B -c "<tally; pytest.main(['-k','test_smk_033','-p','no:cacheprovider'])>"
#   -> RC 0 ; passed=14 failed=0 skipped=0 error=0 ; FAILS [] ; 8 distinct functions present
```

> **On counting.** pytest's terminal summary is not reliably captured in this harness, so the full-suite total
> (**768**) and the per-smoke breakdown came from an in-process `pytest_runtest_logreport` tally
> (`passed=768, failed=0, skipped=0, error=0`) with `pytest.main() RC=0`; the isolated `-k` run independently
> confirms `14 passed`. pytest's own per-item output was swallowed (`redirect_stdout`/`redirect_stderr`). The
> build-side collect-only count (M6-P2903) was 768, matching this executed total.

## Boundary / safety observed during this run

- **Stricter/fail-closed only (leg 1, added FAILs):** decision not observed SELLABLE (NOT_SELLABLE / unknown /
  missing) → Risk FAIL; a pull error / incomplete read → Risk FAIL + `unverified`. No PASS branch opened.
- **ops-core §4 preserved:** the recall booleans are still derived from the presence booleans only (never from
  decision) — a present lock FAILs even under SELLABLE; a clean lot's booleans stay False under any decision.
- **Certified clear-path preserved (nothing loosened):** a SELLABLE + no-active + COMPLETE all-6 picture still
  reaches Risk PASS; a partial 3-of-6 map → HOLD (M6.2T all-6 completeness unchanged).
- **`not_sellable` is a distinct signal, not a RISK_LOCK:** the all-6 completeness, `active_risk_locks`, and every
  non-mapper scale context are unchanged.
- **No egress, no flag flipped, no wiring:** the smoke READS `config.EXTERNAL_SEND == "OFF"` (and PRODUCTION_FLAG
  OFF / GLOBAL_GATEWAY_STATE BLOCKED), the mapper stays UNWIRED (no app runtime import), and nothing was written to
  `04-artifacts/state/`. No PII in scope (availability responses carry campaign/SKU governance metadata, not customer
  PII).
- **No fix to code under test:** all 768 passed, so nothing needed reporting as a failure, and nothing was patched.
  No application code / config change / migration / wiring / flag flip / `04-artifacts/state/` write.

## Exit-gate legs closed by this run (slice M6.2U done-gate)

| Leg | Requirement | Status |
|---|---|---|
| 1 | recall path honors E2 §3: NOT_SELLABLE / unknown / missing decision → Risk FAIL (distinct from the recall booleans; ops-core §4 preserved); pull error/incomplete → Risk FAIL (not HOLD) + 'unverified'; a SELLABLE + no-active response still clears (nothing loosened, no test nerfed) | met — SMK-033 scenarios i/ii/iii + not-derived + clear-path control + distinctness + coder `test_m6_2u_recall_e2_conformance.py` green |
| 4 | Proposed smoke M6-SMK-033 executed | **PASS** (14/14) — executed |

> LEG 2 (migration README renumber) and LEG 3 (attribution_context docstring) are docs-only and verified by the
> CODER + the slice Judge, not by this runtime smoke.

> This run does NOT self-certify gate advancement (RULE-015). It is the honest executed-results record of the TESTER.
> The runner EVIDENCE_GATE and the slice Judge (M6-P2909) decide closure — the judge also verifies stricter-only (a
> FAIL added, no PASS/clear/allow branch, `not_sellable` not a RISK_LOCK, no test nerfed) and that the mapper stays
> UNWIRED. M6-P2905 (boundary), M6-P2906 (security/PII), and the PM evidence-collect M6-P2907 come next. Posture stays
> BLOCKED/OFF/OFF; the M6-OD-002/005 + M6-OD-003/012 + M6-OD-011 hard forward conditions remain open for the exit
> judge (no live wiring / real scale / egress until decided).
