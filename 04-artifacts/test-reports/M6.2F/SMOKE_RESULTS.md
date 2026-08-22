# SMOKE_RESULTS — Slice M6.2F (Dashboard & Data Quality)

| Field | Value |
|---|---|
| Prompt | M6-P1504 — `M6_2F_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test** — the M6.2F smoke suite is EXECUTED here and results recorded. Smoke files were authored in M6-P1503 (`M6_2F_TESTER_BUILD`). |
| Smoke ids executed | **M6-SMK-004, M6-SMK-005, M6-SMK-006, M6-SMK-010, M6-SMK-015** (exactly the bound set) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Staging root | `04-artifacts/impl/M6.2F/` (STAGED_ONLY; convention reference, not a live repo) |
| Bound-smoke result | **18 passed, 0 failed — exit 0** |
| Full staged suite | **273 passed, 0 failed, 0 skipped, 0 error — RC 0** |
| Overall | **all 5 bound smoke ids PASS; no failures; nothing patched** |

> **Governance (immutable — nothing in this run flips a flag):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
> `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False` (M6-OD-002 OPEN), `HASH_POLICY_RATIFIED=False`,
> `SCALE_MODEL_RATIFIED=False` (M6-OD-005 OPEN). Revenue is verified-only (RULE-003 / FAIL-001); the Data Mart is
> a support view only (RULE-012 / FAIL-005); Zone-C DQ transitions are audited (RULE-015). No pricing (M3),
> order-state (M8), CRM send, commission (RULE-019), or Core override (FAIL-004) anywhere. `status` is an honest
> self-report; the runner EVIDENCE_GATE and the slice Judge (M6-P1509) decide closure.

## Per-smoke results (scenario / expected verbatim from SMOKE_REGISTER)

| Smoke ID | Doc ID | Test file | Nodes | Result | Scenario → Expected (verbatim) |
|---|---|---|---|---|---|
| M6-SMK-004 | ADS-P0-004 | `tests/smoke/test_smk_004_quote_not_revenue.py` | 3 | **PASS** | "Quote được tạo nhưng chưa order" → "Không revenue, không ROAS" |
| M6-SMK-005 | ADS-P0-005 | `tests/smoke/test_smk_005_order_not_verified_not_revenue.py` | 4 | **PASS** | "Order Draft / Order Created chưa verified" → "Không tính Revenue Verified" |
| M6-SMK-006 | ADS-P0-006 | `tests/smoke/test_smk_006_dashboard_roas_update.py` | 4 | **PASS** | "ORDER_VERIFIED có campaign/adset/ad đầy đủ" → "ROAS/CPA/AOV dashboard cập nhật" |
| M6-SMK-010 | ADS-P0-010 | `tests/smoke/test_smk_010_data_mart_support_view_only.py` | 3 | **PASS** | "Data Mart tạo trigger CRM/scale" → "Fail - Data Mart chỉ support view" |
| M6-SMK-015 | ADS-P0-015 | `tests/smoke/test_smk_015_dashboard_quote_draft_not_revenue.py` | 4 | **PASS** | "Dashboard hiển thị quote/order draft như revenue" → "Fail" |

**Bound-smoke nodes: 18 (3 + 4 + 4 + 3 + 4), all PASSED.**

### M6-SMK-004 — Quote created, not ordered → no revenue, no ROAS · **PASS (3/3)**

- `test_smk_004_quote_is_not_revenue_and_no_roas` (primary) — PASS: `QUOTE_SENT` + mapped spend → `Revenue Verified 0.0`, `ROAS 0.0`, `AOV None`; quote counts in the funnel (`Quote Rate` trace `QUOTE_SENT=1…`).
- `test_smk_004_neg_no_spend_roas_is_fail_closed` — PASS: no spend → `ROAS None` (fail-closed), `Revenue Verified 0.0`.
- `test_smk_004_neg_quote_carrying_revenue_is_dq_fail` — PASS: fabricated quote-with-revenue → DQ Verified-Revenue item FAIL, overall FAIL (FAIL-001).

### M6-SMK-005 — Order draft / created, not verified → not Verified Revenue · **PASS (4/4)**

- `test_smk_005_order_created_not_counted_as_verified_revenue` (primary) — PASS: `ORDER_CREATED` → `Revenue Verified 0.0`, `Verified Rate 0.0`, trace `ORDER_VERIFIED=0 / ORDER_CREATED=1`.
- `test_smk_005_neg_draft_conversion_materializes_no_revenue` — PASS: an ORDER_CREATED conversion carrying revenue materializes no `revenue_value` / `order_code`.
- `test_smk_005_neg_draft_carrying_revenue_is_dq_fail` — PASS: fabricated draft-with-revenue → DQ FAIL (FAIL-001).
- `test_smk_005_control_verified_order_is_counted` — PASS: a genuine ORDER_VERIFIED IS counted (non-vacuous).

### M6-SMK-006 — ORDER_VERIFIED full source → ROAS/CPA/AOV dashboard updates · **PASS (4/4)**

- `test_smk_006_verified_order_updates_roas_cpa_aov` (primary) — PASS: full campaign/adset/ad verified order (rev 250000, mapped spend 100000) → `ROAS 2.5`, `CPA 100000`, `AOV 250000`, evidence-first, `overall_data_quality PASS`.
- `test_smk_006_neg_absent_spend_fail_closed_roas` — PASS: no spend → `ROAS`/`CPA` None; `Revenue Verified`/`AOV` intact.
- `test_smk_006_neg_unmapped_spend_excluded` — PASS: unmapped spend excluded → `Ads Spend None`, `ROAS None`.
- `test_smk_006_dashboard_updates_as_more_orders_verify` — PASS: two verified orders → `CPA 75000`, `AOV 150000`, `ROAS 2.0`.

(The carried M6.2E SMK-006 attribution smoke `tests/smoke/test_smk_006_order_verified_full_source.py` (4 nodes) also re-ran green inside the full suite as supporting coverage of the attribution input.)

### M6-SMK-010 — Data Mart cannot trigger CRM/scale → support view only · **PASS (3/3)**

- `test_smk_010_data_mart_exposes_only_read_aggregate_methods` (primary) — PASS: mart public surface ⊆ read-only aggregate allow-list; no `write/insert/update/delete/trigger/send/dispatch/scale/publish/enqueue/crm/create_crm/price/budget` verb (RULE-012, FAIL-005).
- `test_smk_010_dashboard_deps_and_view_carry_no_trigger_handle` — PASS: `DashboardDeps` holds only `{mart}`; the view has no write/trigger handle.
- `test_smk_010_neg_reading_dashboard_does_not_mutate_store` — PASS: computing the dashboard twice does not mutate the store (no trigger side effect).

### M6-SMK-015 — Dashboard showing quote/order-draft as revenue → Fail · **PASS (4/4)**

- `test_smk_015_dashboard_revenue_is_verified_only` (primary) — PASS: verified order + quote + draft → `Revenue Verified` counts only the verified order (200000); `overall_data_quality PASS`.
- `test_smk_015_dq_fails_quote_shown_as_revenue` — PASS: DQ Verified-Revenue FAIL, overall FAIL for a quote-as-revenue.
- `test_smk_015_dq_fails_order_draft_shown_as_revenue` — PASS: DQ FAIL for a draft-as-revenue.
- `test_smk_015_control_verified_revenue_item_passes` — PASS: a genuine ORDER_VERIFIED PASSES the Verified-Revenue gate (discriminating).

## Supporting / regression coverage (inside the 273 full suite, all green)

The M6.2F dashboard/DQ leg tests authored by the coder (M6-P1502) re-ran green as supporting coverage:
`test_kpi_formulas_verbatim.py` (4, the 14 CTR-015 formulas verbatim), `test_dashboard_verified_only_revenue.py`
(1), `test_dashboard_rejects_unverified_as_revenue.py` (2), `test_data_mart_support_view_only.py` (2),
`test_quote_not_revenue.py` (1), `test_order_draft_not_verified.py` (1), `test_data_quality_checker.py` (5) —
plus the carried M6.2A–E tree (239). Full total **273 passed, 0 failed**.

## Commands run (from `04-artifacts/impl/M6.2F/`, no shell redirection, cache-free)

The role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path, so no redirection is used;
`PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider` keep the run cache-free.

```bash
# 1) the five bound M6.2F smoke files (verbose)
python.exe -m pytest -v tests/smoke/test_smk_004_quote_not_revenue.py tests/smoke/test_smk_005_order_not_verified_not_revenue.py tests/smoke/test_smk_006_dashboard_roas_update.py tests/smoke/test_smk_010_data_mart_support_view_only.py tests/smoke/test_smk_015_dashboard_quote_draft_not_revenue.py -p no:cacheprovider
#   -> 18 passed in 1.59s ; EXIT 0

# 2) the full staged suite, counted via an in-process pytest_runtest_logreport tally
python.exe -c "<pytest_runtest_logreport tally + pytest.main(['-q','-p','no:cacheprovider'])>"
#   -> COUNTS={'passed': 273, 'failed': 0, 'skipped': 0, 'error': 0} RC=0 ; FAILS=[]
```

> **On counting.** In this harness pytest's terminal summary line is not reliably captured for a long `-q` run,
> so the full-suite total (**273**) was obtained via an in-process `pytest_runtest_logreport` tally
> ({passed:273, failed:0, skipped:0, error:0}) with `pytest.main() RC=0` and an empty failure list — all
> agreeing with the M6-P1503 `--collect-only` total of 273. The five smoke files' `18 passed` summary IS
> captured verbatim.

Cache hygiene: `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

## Correlation / trace ids (all synthetic; PII masked on export)

All ids exercised are **synthetic**, never real customer data: measurement correlation ids default to `corr_ame`
(`make_measurement_event`) / `corr_c` (`make_conversion`); the DQ negative fabricated events use `corr_q`,
`corr_d`, `corr_v`; order codes `ORD_1/2/3/9/A/B/V/OK/DRAFT`; campaign/adset/ad `c1/a1/ad1`. Where a correlation
id reaches a dashboard metric's `sample_evidence_ref` it is **masked** by `app.measurement.masking.mask`
(e.g. `ame:verified;corr=cor***me`). No raw phone / email / address / customer_id / guest_id / psid / token
appears in any test, log, or this report (RULE-014 / H02); the "revenue on a non-verified event" negatives are
fabricated in-memory events fed straight to the DQ checker (the store would never persist them).

## Boundary / safety observed during this run

- **Verified-only revenue (RULE-003, FAIL-001):** every revenue metric sourced only the set-once Zone-B
  `revenue_value` of ORDER_VERIFIED; quote/draft never became revenue; a non-verified figure presented as
  revenue was a DQ Verified-Revenue FAIL (SMK-004/005/015).
- **Support view only (RULE-012, FAIL-005):** the Data Mart / dashboard deps / view exposed no
  write/CRM/scale/trigger surface; reading the dashboard mutated nothing (SMK-010).
- **Audited DQ transitions (RULE-015):** exercised via the supporting `test_data_quality_checker.py` (Zone-C
  written only by the store's audited setter).
- **No fix to code under test:** the TESTER executes and reports; all 273 passed so nothing needed reporting as
  a failure, and nothing was patched. No application code / migration / external call / order-state / pricing /
  CRM send / commission / flag flip / `04-artifacts/state/` write occurred.

## Exit-gate legs closed by this run (slice M6.2F done-gate)

| Leg | Requirement | Status |
|---|---|---|
| L1 | Dashboard shows verified-only revenue (quote/draft as revenue = FAIL) | met — SMK-004/005/015 + supporting dashboard/DQ tests green |
| L2 | Smoke M6-SMK-004 executed with recorded result | **PASS** (3/3) |
| L3 | Smoke M6-SMK-005 executed with recorded result | **PASS** (4/4) |
| L4 | Smoke M6-SMK-006 executed with recorded result | **PASS** (4/4) |
| L5 | Smoke M6-SMK-010 executed with recorded result | **PASS** (3/3) |
| L6 | Smoke M6-SMK-015 executed with recorded result | **PASS** (4/4) |

> This run does NOT self-certify gate advancement (RULE-015). It is the honest executed-results record of the
> TESTER. The runner EVIDENCE_GATE and the slice Judge (M6-P1509) decide closure; M6-P1505 (boundary adversary)
> and M6-P1506 (security/PII) review the dashboard/DQ layer next.
