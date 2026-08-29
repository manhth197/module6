# SMOKE_RESULTS — Slice M6.2I (Phase 2 Golden Hour Funnel)

| Field | Value |
|---|---|
| Prompt | M6-P1804 — `M6_2I_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test** — the M6.2I smoke suite is EXECUTED here and results recorded. Smoke files were authored in M6-P1803 (`M6_2I_TESTER_BUILD`). |
| Smoke ids executed | **M6-SMK-004, M6-SMK-013** (the bound set) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Staging root | `04-artifacts/impl/M6.2I/` (STAGED_ONLY; convention reference, not a live repo) |
| Bound-smoke result | **8 passed, 0 failed — exit 0** |
| Full staged suite | **386 passed, 0 failed, 0 skipped, 0 error — RC 0** |
| Overall | **both bound smoke ids PASS; no failures; nothing patched; funnel measured only** |

> **Governance (immutable — nothing in this run flips a flag, and the funnel only measures):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `SCALE_MODEL_RATIFIED=False`,
> `SCALE_EXECUTION_ENABLED=False`, `LEARNING_AUTOPUBLISH_ENABLED=False`. The funnel is measure-only (RULE-013 —
> no live-session controller; RULE-018 — no new table; no send/scale/publish/order-state). Revenue is
> verified-only and self-enforcing (RULE-003 / FAIL-001): a quote / order-created is a funnel stage, never
> revenue. The live/comment/messenger trace is threaded with psid masked on export (RULE-014 / H02). No pricing
> (M3), consult content (M4), public reply (M5), live ops (M7), order-state (M8), CRM send, or commission
> (RULE-019). `status` is an honest self-report; the runner EVIDENCE_GATE and the slice Judge (M6-P1809) decide
> closure.

## Per-smoke results (scenario / expected verbatim from SMOKE_REGISTER)

| Smoke ID | Doc ID | Test file | Nodes | Result | Scenario → Expected (verbatim) |
|---|---|---|---|---|---|
| M6-SMK-004 | ADS-P0-004 | `tests/smoke/test_smk_004_quote_in_golden_hour_funnel_not_revenue.py` | 4 | **PASS** | "Quote được tạo nhưng chưa order" → "Không revenue, không ROAS" |
| M6-SMK-013 | ADS-P0-013 | `tests/smoke/test_smk_013_funnel_live_chain_trace.py` | 4 | **PASS** | "Live/Comment/Messenger chain" → "Trace được live_session_id, comment_id, messenger_thread_id" |

**Bound-smoke nodes: 8 (4 + 4), all PASSED.**

### M6-SMK-004 — Quote in the Golden Hour funnel is measured but not revenue · **PASS (4/4)**

- `test_smk_004_quote_in_funnel_is_measured_but_not_revenue` (primary) — PASS: a `QUOTE_SENT` counts in the funnel Quote stage (`MESSENGER_TO_QUOTE`=1, Quote Rate numerator=1) but `verified_revenue == 0.0` (RULE-003 / FAIL-001).
- `test_smk_004_neg_order_created_not_verified_is_not_revenue` — PASS: an `ORDER_CREATED` is a funnel stage (`QUOTE_TO_ORDER`) but 0 verified revenue.
- `test_smk_004_neg_quote_carrying_revenue_is_still_zero` — PASS: a `QUOTE_SENT` row force-materialized with a `revenue_value` still reports 0 funnel revenue (self-enforcing RULE-003 choke).
- `test_smk_004_neg_no_roas_from_quote_same_choke_as_dashboard` — PASS: with only a quote, the funnel reports 0 revenue AND the M6.2F dashboard (same store) reports Revenue Verified 0 with ROAS None — no ROAS on either surface.

### M6-SMK-013 — Funnel threads the live/comment/messenger chain · **PASS (4/4)**

- `test_smk_013_funnel_threads_live_comment_messenger_trace` (primary) — PASS: the funnel `trace` threads `live_session_id`, `comment_id`, `messenger_thread_id` from the materialized attribution_context.
- `test_smk_013_neg_psid_masked_on_export` — PASS: `to_public()["trace"]["psid"]` is masked (≠ raw, not None); the raw psid never appears in the export.
- `test_smk_013_neg_partial_chain_traces_what_is_present` — PASS: a comment with no messenger thread traces `comment_id`, leaves `messenger_thread_id` None (never fabricated).
- `test_smk_013_control_no_live_chain_traces_none` — PASS: a session with no live/comment/messenger source traces neither id; the session key itself is still traced.

## Supporting / regression coverage (inside the 386 full suite, all green)

The M6.2I funnel leg tests authored by the coder (M6-P1802) re-ran green as supporting coverage:
`test_golden_hour_funnel_chain.py` (3), `test_golden_hour_state_measure_only.py` (4),
`test_quote_in_funnel_not_revenue.py` (4), `test_live_chain_trace_in_funnel.py` (3),
`test_retargeting_consent_valid_only.py` (6), `test_order_capture_commerce_gate_rule021.py` (4),
`test_funnel_measure_only_boundary.py` (3) — plus the carried M6.2A–H tree (351). Full total **386 passed, 0
failed**.

## Commands run (from `04-artifacts/impl/M6.2I/`, no shell redirection, cache-free)

The role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path, so no redirection is used;
`PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider` keep the run cache-free.

```bash
# 1) the two bound M6.2I smoke files (verbose)
python.exe -m pytest -v tests/smoke/test_smk_004_quote_in_golden_hour_funnel_not_revenue.py tests/smoke/test_smk_013_funnel_live_chain_trace.py -p no:cacheprovider
#   -> 8 passed in 0.09s ; EXIT 0

# 2) the full staged suite, counted via an in-process pytest_runtest_logreport tally
python.exe -c "<pytest_runtest_logreport tally + pytest.main(['-q','-p','no:cacheprovider'])>"
#   -> COUNTS={'passed': 386, 'failed': 0, 'skipped': 0, 'error': 0} RC=0 ; FAILS=[]
```

> **On counting.** In this harness pytest's terminal summary line is not reliably captured for a long `-q` run,
> so the full-suite total (**386**) was obtained via an in-process `pytest_runtest_logreport` tally
> ({passed:386, failed:0, skipped:0, error:0}) with `pytest.main() RC=0` and an empty failure list — all
> agreeing with the M6-P1803 `--collect-only` total of 386. The two smoke files' `8 passed` summary IS captured.

Cache hygiene: `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

## Correlation / trace ids (all synthetic; PII masked on export)

All ids exercised are **synthetic**, never real customer data: live-session ids `ls_q`, `ls_o`, `ls_bad`,
`ls_q2`, `ls_1`, `ls_2`, `ls_p`, `ls_3`; order codes `ord_9`, `ord_bad`, `ord_live`, `ord_live2`, `ord_live3`;
comment/thread ids `cmt_1`, `th_1`, `cmt_2`, `th_2`, `cmt_only`. The `psid` marker is **assembled at runtime**
(no literal id in the test source) and is **masked** on every funnel export via `app.measurement.masking.mask`.
No raw phone / email / address / customer_id / guest_id / psid / token appears in any test, log, or this report
(RULE-014 / H02).

## Boundary / safety observed during this run

- **Measure-only (RULE-013/018):** the funnel projection wrote nothing, sent nothing, and exposed no
  live-session controller / new table / write / send / scale / publish / order-state verb.
- **Verified-only revenue, self-enforcing (RULE-003, FAIL-001):** a quote / order-created — even one
  force-carrying a `revenue_value` — reported 0 funnel revenue; the funnel and the dashboard agreed (0 revenue,
  no ROAS).
- **PII masking (RULE-014 / H02):** psid masked on every funnel export; the raw value never reached an export
  surface.
- **No fix to code under test:** all 386 passed, so nothing needed reporting as a failure, and nothing was
  patched. No application code / migration / external call / live-session op / order-state / pricing / CRM send /
  commission / flag flip / `04-artifacts/state/` write occurred.

## Exit-gate legs closed by this run (slice M6.2I done-gate)

| Leg | Requirement | Status |
|---|---|---|
| L1 | Golden Hour conversion smoke pass (Ads→…→Verified chain measured PRE→LIVE→POST→CLOSED, live/comment/messenger trace passing) | met — supporting `test_golden_hour_funnel_chain.py` / `test_golden_hour_state_measure_only.py` + SMK-013 green |
| L2 | Smoke M6-SMK-004 executed with recorded result | **PASS** (4/4) |
| L3 | Smoke M6-SMK-013 executed with recorded result | **PASS** (4/4) |

> This run does NOT self-certify gate advancement (RULE-015). It is the honest executed-results record of the
> TESTER. The runner EVIDENCE_GATE and the slice Judge (M6-P1809) decide closure; M6-P1805 (boundary adversary)
> and M6-P1806 (security/PII) review the funnel layer next.
