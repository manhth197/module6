# SMOKE_RESULTS — Slice M6.2J (Phase 3 CRM / Diamond / Lifecycle growth)

| Field | Value |
|---|---|
| Prompt | M6-P1904 — `M6_2J_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test** — the M6.2J smoke suite is EXECUTED here and results recorded. Smoke files were authored in M6-P1903 (`M6_2J_TESTER_BUILD`). |
| Smoke ids executed | **M6-SMK-008, M6-SMK-010, M6-SMK-014** (the bound set) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Staging root | `04-artifacts/impl/M6.2J/` (STAGED_ONLY; convention reference, not a live repo) |
| Bound-smoke result | **11 passed, 0 failed — exit 0** |
| Full staged suite | **425 passed, 0 failed, 0 skipped, 0 error — RC 0** |
| Overall | **all three bound smoke ids PASS; no failures; nothing patched; growth layer measured only** |

> **Governance (immutable — nothing in this run flips a flag, and the growth layer only measures):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `SCALE_MODEL_RATIFIED=False`,
> `SCALE_EXECUTION_ENABLED=False`, `LEARNING_AUTOPUBLISH_ENABLED=False`. The growth layer never sends CRM
> (RULE-002 — no send surface), never computes a commission (RULE-019 — Finance owns), never turns the Data Mart
> into a trigger (RULE-012 / FAIL-005), and never overrides Core/CRM/Diamond (FAIL-004). CRM Revenue is
> verified-only and consent/eligibility/suppression gated — opt-out fail-closed excluded (SMK-008 / FAIL-002).
> Diamond referral attribution is recorded with buyer identity masked on export (RULE-014 / H02); commission-ready
> revenue is a revenue figure, never a commission (SMK-014). `status` is an honest self-report; the runner
> EVIDENCE_GATE and the slice Judge (M6-P1909) decide closure.

## Per-smoke results (scenario / expected verbatim from SMOKE_REGISTER)

| Smoke ID | Doc ID | Test file | Nodes | Result | Scenario → Expected (verbatim) |
|---|---|---|---|---|---|
| M6-SMK-008 | ADS-P0-008 | `tests/smoke/test_smk_008_crm_optout_no_sync.py` | 4 | **PASS** | "CRM opt-out" → "Không sync CRM audience/CRM event outbound" |
| M6-SMK-010 | ADS-P0-010 | `tests/smoke/test_smk_010_growth_data_mart_support_view_only.py` | 3 | **PASS** | "Data Mart tạo trigger CRM/scale" → "Fail - Data Mart chỉ support view" |
| M6-SMK-014 | ADS-P0-014 | `tests/smoke/test_smk_014_diamond_referral_no_commission.py` | 4 | **PASS** | "Diamond referral order verified" → "Gắn referral attribution, không tự tính commission" |

**Bound-smoke nodes: 11 (4 + 3 + 4), all PASSED.**

### M6-SMK-008 — CRM opt-out → no CRM audience/event outbound · **PASS (4/4)**

- `test_smk_008_crm_optout_excluded_and_no_sync_surface` (primary) — PASS: an `OPT_OUT` CRM subject → `crm_revenue() == 0.0` (excluded, fail-closed); the CRM measurement exposes no `send/sync/dispatch/transport/enqueue/publish/crm_send/send_crm` surface.
- `test_smk_008_neg_expired_or_missing_consent_excluded` — PASS: expired consent and a missing snapshot are fail-closed excluded.
- `test_smk_008_neg_consent_without_crm_scope_excluded` — PASS: VALID consent granting only `audience_sync` (not the CRM scope) is excluded.
- `test_smk_008_control_valid_crm_consent_is_counted` — PASS: VALID CRM-scope consent + eligibility + suppression → `crm_revenue() == 250000` (non-vacuous).

### M6-SMK-010 — Data Mart / growth cannot trigger CRM/scale → support view only · **PASS (3/3)**

- `test_smk_010_data_mart_and_growth_expose_no_crm_or_scale_trigger` (primary) — PASS: neither the `DataMart` nor the `GrowthReportBuilder` exposes a trigger verb (`trigger/send/sync/crm_send/scale/set_price/publish/commission/order_state/write/insert/update/delete`); the built report has `kpis` and no trigger (RULE-012/FAIL-005).
- `test_smk_010_neg_growth_report_is_data_only` — PASS: the growth report export is a plain dict of KPIs, no trigger handle.
- `test_smk_010_neg_building_growth_report_does_not_mutate_store` — PASS: building the growth report twice does not mutate the measurement store.

### M6-SMK-014 — Diamond referral order verified → referral attribution, no commission · **PASS (4/4)**

- `test_smk_014_verified_referral_records_attribution_and_measures_revenue` (primary) — PASS: a verified Diamond referral order records referral attribution (`referral_link_id`, `order_code`); `diamond_revenue() == 500000` and `commission_ready_revenue() == 500000` are measured; NO commission method exists (RULE-019).
- `test_smk_014_neg_no_commission_method_anywhere` — PASS: no commission amount/rate/payout method even with no data wired.
- `test_smk_014_neg_commission_ready_zero_without_eligibility` — PASS: with no consumed eligibility, `commission_ready_revenue() == 0.0` (fail-closed); `diamond_revenue() == 400000` still measured.
- `test_smk_014_neg_buyer_identity_masked_on_export` — PASS: `to_public()["buyer_ref"]` masked; the raw buyer id never reaches the export.

## Supporting / regression coverage (inside the 425 full suite, all green)

The M6.2J growth leg tests authored by the coder (M6-P1902) re-ran green as supporting coverage:
`test_crm_optout_excluded.py` (4), `test_crm_reorder_revenue_verified_only.py` (5),
`test_data_mart_stays_support_view.py` (3), `test_diamond_referral_no_commission.py` (5),
`test_reactivation_consent_eligibility_failclosed.py` (4), `test_growth_kpis_from_valid_signals_only.py` (3),
`test_growth_measure_only_boundary.py` (4) — plus the carried M6.2A–I tree (386). Full total **425 passed, 0
failed**.

## Commands run (from `04-artifacts/impl/M6.2J/`, no shell redirection, cache-free)

The role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path, so no redirection is used;
`PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider` keep the run cache-free.

```bash
# 1) the three bound M6.2J smoke files (verbose)
python.exe -m pytest -v tests/smoke/test_smk_008_crm_optout_no_sync.py tests/smoke/test_smk_010_growth_data_mart_support_view_only.py tests/smoke/test_smk_014_diamond_referral_no_commission.py -p no:cacheprovider
#   -> 11 passed in 0.12s ; EXIT 0

# 2) the full staged suite, counted via an in-process pytest_runtest_logreport tally
python.exe -c "<pytest_runtest_logreport tally + pytest.main(['-q','-p','no:cacheprovider'])>"
#   -> COUNTS={'passed': 425, 'failed': 0, 'skipped': 0, 'error': 0} RC=0 ; FAILS=[]
```

> **On counting.** In this harness pytest's terminal summary line is not reliably captured for a long `-q` run,
> so the full-suite total (**425**) was obtained via an in-process `pytest_runtest_logreport` tally
> ({passed:425, failed:0, skipped:0, error:0}) with `pytest.main() RC=0` and an empty failure list — all
> agreeing with the M6-P1903 `--collect-only` total of 425. The three smoke files' `11 passed` summary IS
> captured.

Cache hygiene: `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

## Correlation / trace ids (all synthetic; PII masked on export)

All ids exercised are **synthetic**, never real customer data: order codes `ord_o`, `ord_e`, `ord_s`, `ord_v`,
`ord_m`, `ord_m2`, `ord_d`, `ord_d2`, `ord_d3`; consent subject `subj_crm`; referral ids `ref_1`, `ref_2`,
`ref_3`; `diamond_id` `dia_1`. The Diamond buyer-identity marker (`cust_dia_smk14`) is synthetic and is **masked**
on every referral-attribution export via `app.measurement.masking.mask` (e.g. `cus***14`). No raw phone / email /
address / customer_id / guest_id / psid / token appears in any test, log, or this report (RULE-014 / H02).

## Boundary / safety observed during this run

- **Consent-gated CRM revenue (RULE-002, FAIL-002):** opt-out / expired / missing / scope-not-granted subjects
  were fail-closed excluded; the CRM layer exposed no send/sync surface.
- **Support view only (RULE-012, FAIL-005):** the Data Mart + growth builder exposed no trigger; the growth
  report was read-only data; building it mutated nothing.
- **No commission (RULE-019):** the Diamond layer recorded referral attribution + measured verified /
  commission-ready revenue but computed no commission amount/rate/payout; buyer identity masked.
- **No fix to code under test:** all 425 passed, so nothing needed reporting as a failure, and nothing was
  patched. No application code / migration / external call / CRM send / commission / Data-Mart trigger / Core
  override / order-state / pricing / flag flip / `04-artifacts/state/` write occurred.

## Exit-gate legs closed by this run (slice M6.2J done-gate)

| Leg | Requirement | Status |
|---|---|---|
| L1 | CRM revenue verified (only from eligibility + suppression + ORDER_VERIFIED; clicks/chats never revenue) | met — SMK-008 + `test_crm_reorder_revenue_verified_only.py` green |
| L2 | Diamond revenue verified (referral attribution; commission measured-not-computed) | met — SMK-014 + `test_diamond_referral_no_commission.py` green |
| L3 | Smoke M6-SMK-008 executed with recorded result | **PASS** (4/4) |
| L4 | Smoke M6-SMK-010 executed with recorded result | **PASS** (3/3) |
| L5 | Smoke M6-SMK-014 executed with recorded result | **PASS** (4/4) |

> This run does NOT self-certify gate advancement (RULE-015). It is the honest executed-results record of the
> TESTER. The runner EVIDENCE_GATE and the slice Judge (M6-P1909) decide closure; M6-P1905 (boundary adversary)
> and M6-P1906 (security/PII) review the growth layer next.
