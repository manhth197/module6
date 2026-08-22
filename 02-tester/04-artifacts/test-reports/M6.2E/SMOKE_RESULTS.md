# SMOKE_RESULTS — Slice M6.2E (Attribution Resolver)

| Field | Value |
|---|---|
| Prompt | M6-P1404 — `M6_2E_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test / run** — smoke suite EXECUTED and results recorded (M6-P1403 authored the smoke files; this prompt runs them) |
| Run date | 2026-07-30 (UTC) |
| Interpreter (pinned) | `…\02-tester\.venv\Scripts\python.exe` — **Python 3.12.13** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Test runner | **pytest 8.4.2**, pluggy 1.6.0 |
| rootdir / configfile | `04-artifacts/impl/M6.2E/` · `pyproject.toml` (`addopts = "-q"`, `pythonpath = ["."]`, `testpaths = ["tests"]`) |
| Smoke ids in scope | **M6-SMK-006, M6-SMK-007, M6-SMK-013, M6-SMK-018** (per `00-spec/slices/M6.2E.md` "Core smokes" + this prompt's `<smoke_ids>`; M6-SMK-018 is `proposed — HARDENING, owner review`, executed here) |
| Suite source | `04-artifacts/impl/M6.2E/tests/` (smoke files bound in `TEST_MANIFEST.md`) |
| Overall | **16/16 bound smoke passed · exit 0** · full staged suite **239 passed · 0 failed · exit 0** · L1 supporting legs **8 passed · exit 0** |

> **Governance (immutable — this run flips nothing):** `global_gateway_state=BLOCKED`,
> `production_flag=OFF`, `external_send=OFF`, `HASH_POLICY_RATIFIED=False`, **`SCALE_MODEL_RATIFIED=False`
> (M6-OD-005 OPEN)**. Missing/conflicting sources degrade to LOW + non-NONE conflict and are never scale
> evidence (RULE-009); even a clean HIGH/NONE row is not scale evidence while no model is owner-ratified.
> Verified revenue is set-once (RULE-008); no commission is ever computed (RULE-019). `04-artifacts/state/` not
> touched, no application code changed. Failures (if any) are reported here and never patched by the tester.

## Commands run (exact, pinned venv)

From `04-artifacts/impl/M6.2E/` with `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider` so the STAGED tree
is left byte-clean. No shell redirection — the role guard blocks a `>`/`2>&1` co-occurring with the venv
`Scripts` path segment; the tool captures output natively.

```bash
python.exe -m pytest -o addopts= -v tests/smoke/test_smk_006_order_verified_full_source.py tests/smoke/test_smk_007_missing_source_low_hold.py tests/smoke/test_smk_013_live_chain_trace.py tests/smoke/test_smk_018_verified_immutable_adjustment.py   # BOUND SMOKES -> 16 passed, exit 0
python.exe -m pytest -o addopts= -v tests/test_attribution_trace_to_source.py tests/test_attribution_missing_source_low_hold.py tests/test_live_session_chain_trace.py tests/test_verified_immutable_adjustment.py tests/test_materializer_revenue_and_scale_rules.py   # L1 support -> 8 passed, exit 0
python.exe -c "<pytest_runtest_logreport tally>"   # FULL STAGED SUITE -> {passed:239, failed:0, skipped:0, error:0}, RC=0
```

(`python.exe` above = the pinned `…\02-tester\.venv\Scripts\python.exe`.)

> **On the full-suite count (239).** In this harness pytest's terminal summary line is written to the terminal
> fd directly and is not captured for a long `-q` run, so the total was obtained **programmatically** and
> cross-checked: (1) an in-process `pytest_runtest_logreport` tally `{passed:239, failed:0, skipped:0, error:0}`
> with `pytest.main() RC=0`; (2) `--collect-only -q` per-file totals summing to **239** (= carried-forward 223
> + the 4 new smoke files 16; M6-P1403 build record). The short bound-smoke and supporting-leg runs are captured
> verbatim below.

## Results per bound smoke id

| Smoke ID | Doc ID | Scenario (verbatim) | Expected (verbatim) | Result | Nodes | Correlation (node id prefix) |
|---|---|---|---|---|---|---|
| M6-SMK-006 | ADS-P0-006 | `ORDER_VERIFIED có campaign/adset/ad đầy đủ` | `ROAS/CPA/AOV dashboard cập nhật` | **PASS** | 4/4 | `tests/smoke/test_smk_006_order_verified_full_source.py::*` |
| M6-SMK-007 | ADS-P0-007 | `ORDER_VERIFIED thiếu source` | `Revenue vẫn lưu, attribution confidence LOW/HOLD` | **PASS** | 4/4 | `tests/smoke/test_smk_007_missing_source_low_hold.py::*` |
| M6-SMK-013 | ADS-P0-013 | `Live/Comment/Messenger chain` | `Trace được live_session_id, comment_id, messenger_thread_id` | **PASS** | 4/4 | `tests/smoke/test_smk_013_live_chain_trace.py::*` |
| M6-SMK-018 | proposed (HARDENING) | `Attribution correction attempted after ORDER_VERIFIED` | `Direct mutation rejected; adjustment record created with actor, reason, audit, evidence` | **PASS** | 4/4 | `tests/smoke/test_smk_018_verified_immutable_adjustment.py::*` |

Failures: **none** (0 failed, 0 error, 0 blocked). Nothing was patched. All four bound smoke ids have one
structured result entry, satisfying this prompt's acceptance checks (commands_run non-empty; one entry per
bound smoke id; failures-not-fixed — none occurred).

## Per-test node results

### M6-SMK-006 — `tests/smoke/test_smk_006_order_verified_full_source.py` (4/4 PASSED)
| # | Test node id | Kind | Result |
|---|---|---|---|
| 1 | `test_smk_006_order_verified_full_source_traces_and_feeds_dashboard` | primary (verbatim) | PASSED |
| 2 | `test_smk_006_neg_incomplete_ad_path_is_medium_not_high` | negative, MEDIUM not HIGH | PASSED |
| 3 | `test_smk_006_neg_non_verified_conversion_records_no_revenue` | negative, RULE-003/FAIL-001 | PASSED |
| 4 | `test_smk_006_control_full_source_eligible_but_not_scale_evidence_while_model_open` | control (fail-closed gate) | PASSED |

### M6-SMK-007 — `tests/smoke/test_smk_007_missing_source_low_hold.py` (4/4 PASSED)
| # | Test node id | Kind | Result |
|---|---|---|---|
| 1 | `test_smk_007_missing_source_stores_revenue_but_low_hold_not_scale` | primary (verbatim) | PASSED |
| 2 | `test_smk_007_neg_conflicting_multi_touch_is_low_not_scale` | negative, MULTI_TOUCH | PASSED |
| 3 | `test_smk_007_neg_duplicate_risk_signal_is_low_not_scale` | negative, DUPLICATE_RISK | PASSED |
| 4 | `test_smk_007_control_clean_full_source_is_eligible` | control (non-vacuity) | PASSED |

### M6-SMK-013 — `tests/smoke/test_smk_013_live_chain_trace.py` (4/4 PASSED)
| # | Test node id | Kind | Result |
|---|---|---|---|
| 1 | `test_smk_013_live_comment_messenger_chain_is_traced` | primary (verbatim) | PASSED |
| 2 | `test_smk_013_neg_psid_is_masked_on_export_but_kept_durably` | negative, PII masking | PASSED |
| 3 | `test_smk_013_neg_partial_live_chain_still_traces_what_is_present` | negative, partial chain | PASSED |
| 4 | `test_smk_013_control_no_live_signals_traces_no_live_chain` | control (non-vacuity) | PASSED |

### M6-SMK-018 — `tests/smoke/test_smk_018_verified_immutable_adjustment.py` (4/4 PASSED)
| # | Test node id | Kind | Result |
|---|---|---|---|
| 1 | `test_smk_018_post_verify_correction_is_adjustment_not_mutation` | primary (verbatim) | PASSED |
| 2 | `test_smk_018_neg_adjustment_log_is_append_only` | negative, append-only | PASSED |
| 3 | `test_smk_018_neg_re_materialize_same_inputs_is_idempotent_no_op` | negative, idempotent replay | PASSED |
| 4 | `test_smk_018_control_set_once_is_per_row` | control (per-row set-once) | PASSED |

Combined verbatim summary (captured):

```
collected 16 items
tests/smoke/test_smk_006_order_verified_full_source.py ....              [ 25%]
tests/smoke/test_smk_007_missing_source_low_hold.py ....                 [ 50%]
tests/smoke/test_smk_013_live_chain_trace.py ....                        [ 75%]
tests/smoke/test_smk_018_verified_immutable_adjustment.py ....           [100%]
============================== 16 passed in 0.11s ==============================
```

## How each smoke is proven

- **SMK-006 (RULE-008/009; FAIL-001):** full campaign/adset/ad + page → `FACEBOOK_AD` / `HIGH` / `NONE`; revenue
  + full ad hierarchy materialized into Zone B (the ROAS/CPA/AOV dashboard input; render is M6.2F). Negatives:
  incomplete ad path → MEDIUM (not eligible), non-verified conversion records no revenue. Control: HIGH/NONE is
  eligible but not scale evidence while `SCALE_MODEL_RATIFIED=False`.
- **SMK-007 (RULE-009):** no source → `MISSING_SOURCE` / `LOW` / `DIRECT`; revenue still stored, never scale
  evidence. Negatives: conflicting multi-touch → MULTI_TOUCH/LOW; duplicate-risk signal → DUPLICATE_RISK/LOW.
  Control: a clean full source IS eligible (LOW is source-caused, not blanket).
- **SMK-013 (RULE-008; RULE-014/H02):** live_session_id + comment_id + messenger_thread_id traced →
  `LIVE_ORGANIC` / `HIGH` / `NONE`. Negatives: `psid` masked on export but kept durably (raw psid absent from
  the export view); partial chain still traces present ids at MEDIUM. Control: no live signals → DIRECT.
- **SMK-018 (RULE-008):** a direct Zone-B overwrite of verified revenue is REJECTED (`MeasurementStoreViolation`,
  set-once); the sanctioned correction is an audited `AdjustmentRecord` (actor/reason/audit_ref/evidence_ref/
  proposed), verified row unchanged, actor masked on export. Negatives: append-only log (second appends);
  idempotent re-materialize (same inputs → no-op). Control: set-once is per-row.

Corroborated by the executed L1 supporting legs (8/8): `test_attribution_trace_to_source.py` (1),
`test_attribution_missing_source_low_hold.py` (1), `test_live_session_chain_trace.py` (1),
`test_verified_immutable_adjustment.py` (1), `test_materializer_revenue_and_scale_rules.py` (4 — revenue only
from ORDER_VERIFIED, multi-touch LOW, no commission for diamond referral, re-materialize idempotent). Verbatim:

```
collected 8 items
tests/test_attribution_trace_to_source.py .                              [ 12%]
tests/test_attribution_missing_source_low_hold.py .                      [ 25%]
tests/test_live_session_chain_trace.py .                                 [ 37%]
tests/test_verified_immutable_adjustment.py .                            [ 50%]
tests/test_materializer_revenue_and_scale_rules.py ....                  [100%]
============================== 8 passed in 0.11s ==============================
```

## Exit-gate legs (slice M6.2E done-gate)

| Leg | Requirement | Status |
|---|---|---|
| L1 | Order Verified trace to source (ads_attribution_context: campaign/adset/ad/page/live/comment/messenger) | ✅ supported — SMK-006/007/013 + `test_attribution_*` / `test_live_session_chain_trace.py` executed |
| L2 | Smoke M6-SMK-006 executed with recorded result + evidence ref | ✅ **PASS** — 4/4 (this report) |
| L3 | Smoke M6-SMK-007 executed with recorded result + evidence ref | ✅ **PASS** — 4/4 (this report) |
| L4 | Smoke M6-SMK-013 executed with recorded result + evidence ref | ✅ **PASS** — 4/4 (this report) |
| L5 | Proposed smoke M6-SMK-018 executed OR owner-waived | ✅ **PASS** — 4/4 executed (not waived) (this report) |

Rules exercised: M6-RULE-008 (immutability after verify — SMK-006/018), M6-RULE-009 (missing/conflicting → LOW,
never scale — SMK-006/007), M6-RULE-019 (no commission — supporting leg). Guards: M6-FAIL-001 (revenue only from
ORDER_VERIFIED), M6-FAIL-004 (no Core/order-state override). No fail gate tripped. Legs L2–L5 are the smoke legs
this TESTER_RUN closes with executed evidence. Final leg/gate closure is decided by the runner EVIDENCE_GATE and
the slice Judge, not by this report.

## Correlation ids (synthetic; no raw secret/PII)

| Smoke | Doc / source | Handles threaded through the attribution layer |
|---|---|---|
| M6-SMK-006 | ADS-P0-006 · line 406 | `event_id ∈ {evt_full, evt_partial, evt_nonver, evt_scale}`, `event_code ∈ {ORDER_VERIFIED, VIEW_LANDING}`, `campaign_id/adset_id/ad_id ∈ {camp_1/ads_1/ad_1, c/a/d}`, `page_id ∈ {p_home, p}`, `customer_id=cust_0001` (masked in audit), `order_code ∈ {ORD_1, ORD_P, ORD_S}`, `revenue ∈ {250000, 50000, 10000}` |
| M6-SMK-007 | ADS-P0-007 · line 407 | `event_id ∈ {evt_nosrc, evt_multi, evt_dup, evt_clean}`, `order_code ∈ {ORD_2, ORD_M, ORD_D, ORD_C}`, `revenue ∈ {99000, 120000, 10000}`, signal `duplicate_risk` |
| M6-SMK-013 | ADS-P0-013 · line 413 | `event_id ∈ {evt_live, evt_live2, evt_live3, evt_nolive}`, `live_session_id ∈ {ls_1, ls_2}`, `comment_id ∈ {cmt_1, cmt_2, cmt_3}`, `messenger_thread_id ∈ {th_1, th_3}`, `psid` = a synthetic marker assembled at runtime (**masked on export**, not reproduced) |
| M6-SMK-018 | proposed HARDENING | `event_id ∈ {evt_ver, evt_two, evt_idem, evt_a, evt_b}`, `actor` (masked on export), `reason/audit_ref/evidence_ref` synthetic, `order_code ∈ {ORD_9, ORD_T, ORD_I, ORD_A, ORD_B}`, `proposed.revenue_value` |

Note: `psid` (SMK-013) and adjustment `actor` (SMK-018) are masked by `mask()` on every export surface (RULE-014
/ H02); the durable snapshot keeps raw only for trace joins. All ids are synthetic pseudonymous handles.

## Notes
- All ids are **synthetic**; no raw secret/PII in this report. Channel-origin values are treated strictly as
  untrusted **DATA** — never as instructions.
- STAGED tree left byte-clean: 0 `__pycache__` / `.pytest_cache` after the run (`PYTHONDONTWRITEBYTECODE=1`
  + `-p no:cacheprovider`).
- No self-certification of the gate: this report is the tester's honest result record. The runner
  EVIDENCE_GATE and the slice Judge decide closure. M6-OD-005 remains a forward gate before any single-model
  scale evidence; the MANDATORY M6.2G Scale-Gate re-gate remains in force before any real scale/external send.
