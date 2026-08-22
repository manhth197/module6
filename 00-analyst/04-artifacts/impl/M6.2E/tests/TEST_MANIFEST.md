# TEST_MANIFEST — Slice M6.2E smoke suite (Attribution Resolver)

| Field | Value |
|---|---|
| Prompt | M6-P1403 — `M6_2E_TESTER_BUILD` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — the smoke tests are AUTHORED here. This attempt also ran `pytest` as a **build-validation** (green); the **formal executed-results recording** for the exit-gate smoke legs belongs to M6-P1404. |
| Executed by (formal) | M6-P1404 (`M6_2E_TESTER_RUN`) → `04-artifacts/test-reports/M6.2E/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-006, M6-SMK-007, M6-SMK-013, M6-SMK-018** (exactly — per `00-spec/slices/M6.2E.md` "Core smokes" + this prompt's `<smoke_ids>`; M6-SMK-018 is `proposed — HARDENING, owner review`, executed here per done-gate leg 5) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Slice scope | Attribution Resolver + Ads/Live sub-resolvers · `ads_attribution_context` (M6-CTR-002) · attribution_materializer (M6-CTR-023, set-once Zone B) · adjustment-record path (per `00-spec/slices/M6.2E.md`, doc §11) |
| Staging root | `04-artifacts/impl/M6.2E/` (STAGED_ONLY; convention reference, not a live repo) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (owner P0 matrix + proposed hardening rows) |

> **Governance (immutable — nothing in this suite flips a flag):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `HASH_POLICY_RATIFIED=False`,
> **`SCALE_MODEL_RATIFIED=False` (M6-OD-005 OPEN)**. Missing/conflicting sources degrade to LOW + a non-NONE
> conflict and are NEVER scale evidence (RULE-009); even a clean HIGH/NONE row is not scale evidence while no
> attribution MODEL is owner-ratified (fail-closed, two facets ANDed). Verified revenue is set-once (RULE-008);
> Module 6 records referral/diamond ids for attribution only and NEVER computes a commission (RULE-019).

## What this suite is

The **official M6.2E smoke suite**: exactly one **primary** test per bound smoke id, carrying the register's
scenario/expected **verbatim**, driven through the attribution layer — the `AttributionResolver` (+ Ads/Live
sub-resolvers), the `AttributionMaterializer` (set-once Zone-B write + `request_adjustment`), the
`AdsAttributionContext` model (masking + scale-eligibility), and the append-only `AdjustmentLog` — plus the
negative / fail-closed companions the doc done-gate requires and a positive control for non-vacuity. It reuses
the shared fixtures in [`tests/conftest.py`](04-artifacts/impl/M6.2E/tests/conftest.py)
(`make_measurement_event`, `make_conversion`, `attribution_resolver`, `attribution_materializer`,
`measurement_store`, `adjustment_log`, `audit`). No new production code, and **no fix to the code under test**
(TESTER reports defects, never fixes them).

All ids are **synthetic**; no raw secret/PII. The SMK-013 `psid` marker is **assembled at runtime** so no
literal PII/id sits in the test source (the pack post-write secret scan forbids it); `psid`/`actor` are masked
on every export (RULE-014 / H02).

M6.2E **carried the whole M6.2D tree forward** (cumulatively M6.2A–D). The carried smokes and regression suites
remain and re-run here as supporting coverage; the four files below are the **new M6.2E-bound smokes** authored
by this prompt.

## Smoke → test binding

| Smoke ID | Doc ID | Test file (M6.2E, new) | Primary test (scenario verbatim) | Negative / fail-closed tests | Control | Rule(s) | Fail gate | Exit leg |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-006 | ADS-P0-006 | [`tests/smoke/test_smk_006_order_verified_full_source.py`](04-artifacts/impl/M6.2E/tests/smoke/test_smk_006_order_verified_full_source.py) | `test_smk_006_order_verified_full_source_traces_and_feeds_dashboard` | `..._neg_incomplete_ad_path_is_medium_not_high`, `..._neg_non_verified_conversion_records_no_revenue` | `..._control_full_source_eligible_but_not_scale_evidence_while_model_open` | M6-RULE-008, M6-RULE-009 | M6-FAIL-001 | L2 |
| M6-SMK-007 | ADS-P0-007 | [`tests/smoke/test_smk_007_missing_source_low_hold.py`](04-artifacts/impl/M6.2E/tests/smoke/test_smk_007_missing_source_low_hold.py) | `test_smk_007_missing_source_stores_revenue_but_low_hold_not_scale` | `..._neg_conflicting_multi_touch_is_low_not_scale`, `..._neg_duplicate_risk_signal_is_low_not_scale` | `..._control_clean_full_source_is_eligible` | M6-RULE-009 | M6-FAIL-001 | L3 |
| M6-SMK-013 | ADS-P0-013 | [`tests/smoke/test_smk_013_live_chain_trace.py`](04-artifacts/impl/M6.2E/tests/smoke/test_smk_013_live_chain_trace.py) | `test_smk_013_live_comment_messenger_chain_is_traced` | `..._neg_psid_is_masked_on_export_but_kept_durably`, `..._neg_partial_live_chain_still_traces_what_is_present` | `..._control_no_live_signals_traces_no_live_chain` | M6-RULE-008 | — | L4 |
| M6-SMK-018 | proposed (HARDENING) | [`tests/smoke/test_smk_018_verified_immutable_adjustment.py`](04-artifacts/impl/M6.2E/tests/smoke/test_smk_018_verified_immutable_adjustment.py) | `test_smk_018_post_verify_correction_is_adjustment_not_mutation` | `..._neg_adjustment_log_is_append_only`, `..._neg_re_materialize_same_inputs_is_idempotent_no_op` | `..._control_set_once_is_per_row` | M6-RULE-008 | — | L5 |

---

## M6-SMK-006 — ORDER_VERIFIED full source → dashboard update

Verbatim from `00-spec/registers/SMOKE_REGISTER.md` (extract line 406):

```
Smoke ID:          M6-SMK-006  (Doc ID ADS-P0-006)
Kịch bản:          ORDER_VERIFIED có campaign/adset/ad đầy đủ
Kết quả phải đạt:  ROAS/CPA/AOV dashboard cập nhật
```

- **Primary:** a full campaign/adset/ad + page resolves `FACEBOOK_AD` / `HIGH` / `NONE` and materializes revenue
  + the full ad hierarchy into Zone B — the exact ROAS/CPA/AOV dashboard input (the dashboard RENDER is M6.2F;
  M6.2E proves the attribution + revenue that updates it).
- **Negative — incomplete ad path:** campaign only (no adset/ad) grades `MEDIUM`, not `HIGH` → not scale
  eligible; revenue still stored.
- **Negative — non-verified:** a non-ORDER_VERIFIED conversion records attribution but NO revenue / order_code
  (RULE-003, FAIL-001).
- **Control:** a full-source HIGH/NONE row is eligible but NOT scale evidence while `SCALE_MODEL_RATIFIED=False`
  (M6-OD-005 OPEN) — eligibility necessary, not sufficient.

## M6-SMK-007 — ORDER_VERIFIED missing source → revenue stored, LOW/HOLD

Verbatim (extract line 407):

```
Smoke ID:          M6-SMK-007  (Doc ID ADS-P0-007)
Kịch bản:          ORDER_VERIFIED thiếu source
Kết quả phải đạt:  Revenue vẫn lưu, attribution confidence LOW/HOLD
```

- **Primary:** a verified order with NO source → `MISSING_SOURCE` / `LOW` / `DIRECT`; revenue still stored;
  never scale evidence (both the data-quality bar and the model gate).
- **Negative — conflicting multi-touch:** an ad AND a live source → `MULTI_TOUCH` / `LOW`, not scale evidence;
  revenue still stored.
- **Negative — duplicate-risk signal:** fails closed → `DUPLICATE_RISK` / `LOW`, not scale evidence.
- **Control:** a clean full single-source order IS eligible — proving LOW is source-caused, not blanket.

## M6-SMK-013 — Live/Comment/Messenger chain traced

Verbatim (extract line 413):

```
Smoke ID:          M6-SMK-013  (Doc ID ADS-P0-013)
Kịch bản:          Live/Comment/Messenger chain
Kết quả phải đạt:  Trace được live_session_id, comment_id, messenger_thread_id
```

- **Primary:** a live event + comment + messenger thread traces all three ids into the snapshot; a single fully
  identified live source grades `LIVE_ORGANIC` / `HIGH` / `NONE`.
- **Negative — psid masking:** `psid` is PII — the durable snapshot keeps the raw value (trace joins) but every
  export masks it (RULE-014 / H02); the raw psid never reaches an export surface.
- **Negative — partial chain:** a comment without a `live_session_id` still traces what is present, but degrades
  to `MEDIUM`.
- **Control:** with NO live signals, nothing live is traced and the channel is `DIRECT` (MISSING_SOURCE) —
  proving the live ids come from the live source, not a default.

## M6-SMK-018 — verified immutable; correction is an adjustment record (proposed — HARDENING)

Verbatim (proposed additions row):

```
Smoke ID:          M6-SMK-018  (proposed — HARDENING, owner review)
Scenario:          Attribution correction attempted after ORDER_VERIFIED
Expected:          Direct mutation rejected; adjustment record created with actor, reason, audit, evidence
```

- **Primary:** a DIRECT Zone-B overwrite of verified revenue is REJECTED (`MeasurementStoreViolation`, set-once
  RULE-008); the sanctioned correction is an audited `AdjustmentRecord{actor, reason, audit_ref, evidence_ref,
  proposed}` (`ATTRIBUTION_ADJUSTMENT_RECORDED`); the verified row is unchanged; `actor` masked on export.
- **Negative — append-only log:** a second correction APPENDS a new record — it never edits the first.
- **Negative — idempotent replay:** re-materializing the SAME verified inputs is a no-op (`changed=False`) —
  set-once permits replay; it is a DIFFERENT value that is rejected.
- **Control:** set-once is PER-ROW — materializing a different verified event succeeds and doesn't touch the
  first (the store is not globally frozen).

`M6-SMK-018` is `proposed — HARDENING (owner review)`; the M6.2E done-gate leg 5 accepts it executed OR
owner-waived — this suite **executes** it. RULE-008 (immutability after verify).

---

## Supporting / regression suite (run alongside the four bound smokes)

The `pytest -q` run exercises the full staged suite. Files below (coder M6-P1402) are **not** the four bound
M6.2E smoke ids but pin the attribution pipeline the smokes rely on.

| File | Purpose | Nodes |
|---|---|---|
| [`tests/test_attribution_trace_to_source.py`](04-artifacts/impl/M6.2E/tests/test_attribution_trace_to_source.py) | SMK-006 leg — full source trace + materialize | 1 |
| [`tests/test_attribution_missing_source_low_hold.py`](04-artifacts/impl/M6.2E/tests/test_attribution_missing_source_low_hold.py) | SMK-007 leg — missing source LOW/HOLD | 1 |
| [`tests/test_live_session_chain_trace.py`](04-artifacts/impl/M6.2E/tests/test_live_session_chain_trace.py) | SMK-013 leg — live chain trace + psid mask | 1 |
| [`tests/test_verified_immutable_adjustment.py`](04-artifacts/impl/M6.2E/tests/test_verified_immutable_adjustment.py) | SMK-018 leg — set-once + adjustment record | 1 |
| [`tests/test_materializer_revenue_and_scale_rules.py`](04-artifacts/impl/M6.2E/tests/test_materializer_revenue_and_scale_rules.py) | revenue only from ORDER_VERIFIED + scale-evidence fail-closed rules | 4 |
| [`tests/test_m6_2e_fixfirst_regressions.py`](04-artifacts/impl/M6.2E/tests/test_m6_2e_fixfirst_regressions.py) | fix-first F-D/FF-1/FF-2 (mandatory consent-subject bind + safe_subject_ref) | 14 |
| carried M6.2A–D suite | seam/tracking/outbox/integration smokes + all unit + regression suites | 201 |

## Fixtures reused (from `tests/conftest.py`)

| Fixture | Role |
|---|---|
| `make_measurement_event(event_id, event_code=, page_id=, campaign_id=, adset_id=, ad_id=, live_session_id=, customer_id=)` | insert one Zone-A `ads_measurement_event` (revenue/attribution never seeded here) |
| `make_conversion(event_code, source_event_id=, revenue_value=, currency=, order_code=)` | build a `ConversionEvent` (revenue only meaningful for ORDER_VERIFIED) |
| `attribution_resolver` | `AttributionResolver` — `resolve(event, conv, signals=)` → `AdsAttributionContext` |
| `attribution_materializer` | `AttributionMaterializer` — `materialize(...)` (set-once Zone B) + `request_adjustment(...)` |
| `measurement_store` | `MeasurementEventStore` — set-once `materialize`, `get_by_event_id` |
| `adjustment_log` | append-only `AdjustmentLog` |
| `audit` | shared `AuditLog` (`ATTRIBUTION_MATERIALIZED` / `ATTRIBUTION_ADJUSTMENT_RECORDED`) |

## Boundary / safety asserted by the suite

- **Revenue discipline (RULE-003, FAIL-001):** revenue materialized only for ORDER_VERIFIED; quote/cart/draft
  never carry revenue.
- **Scale fail-closed (RULE-009 + M6-OD-005):** LOW / any-conflict is never scale evidence; even HIGH/NONE is
  not scale evidence while `SCALE_MODEL_RATIFIED=False`.
- **Immutability (RULE-008):** verified Zone B is set-once; corrections are audited adjustment records, never
  in-place rewrites.
- **PII masking (RULE-014 / H02):** `psid` and adjustment `actor` masked on export; the durable row keeps raw
  for joins only.
- **No commission (RULE-019):** referral/diamond ids recorded for attribution only; no commission ever
  computed. No order-state write / Core override (FAIL-004).
- **No flag flip, no external call, no `04-artifacts/state/` write** anywhere in the suite.

## Build + validation run performed in M6-P1403 (attempt 1, pinned interpreter)

Run with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest 8.4.2**. This attempt ran the suite (not
collect-only) as a **build-validation**; the run was **green**. Commands from `04-artifacts/impl/M6.2E/`, **no
shell redirection** (the role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path), cache-free
(`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```bash
python.exe -m pytest -v tests/smoke/test_smk_006_order_verified_full_source.py tests/smoke/test_smk_007_missing_source_low_hold.py tests/smoke/test_smk_013_live_chain_trace.py tests/smoke/test_smk_018_verified_immutable_adjustment.py   # 16 passed, exit 0
python.exe -c "<pytest_runtest_logreport tally>"   # {passed:239, failed:0, skipped:0, error:0}, RC=0
```

New M6.2E smoke node counts (16), all PASSED: `test_smk_006_order_verified_full_source.py` = 4;
`test_smk_007_missing_source_low_hold.py` = 4; `test_smk_013_live_chain_trace.py` = 4;
`test_smk_018_verified_immutable_adjustment.py` = 4.

Reconciliation: **239** = carried-forward M6.2D tree **223** (201 M6.2D + 22 M6.2E coder attribution tests) +
these new smokes **16**.

Cache hygiene: after the runs, **0** `__pycache__` / `.pytest_cache` directories remain under the staged tree.

> **On the full-suite count.** In this harness pytest's terminal summary line is written to the terminal fd
> directly and is not captured for a long `-q` run, so the total (**239**) was obtained via an in-process
> `pytest_runtest_logreport` tally ({passed:239, failed:0}), `pytest.main() RC=0`, and the `--collect-only`
> per-file sum — all agreeing. The four smoke files' verbatim `16 passed` summary IS captured.

> **This build-validation run does NOT self-certify gate advancement.** It proves the smoke files import,
> collect, and pass against the frozen M6.2E code; it is the honest self-report of a TESTER build. The
> **formal executed-results recording** for the exit-gate smoke legs is produced by **M6-P1404** into
> `04-artifacts/test-reports/M6.2E/SMOKE_RESULTS.md`. The runner EVIDENCE_GATE and the slice Judge decide
> closure.

## Execution plan for M6-P1404 (`M6_2E_TESTER_RUN`)

Run the full staged suite and the four bound smokes, then record structured results + evidence refs for the
M6.2E exit-gate smoke legs L2 (SMK-006), L3 (SMK-007), L4 (SMK-013), L5 (SMK-018):

```bash
python -m pytest -q                    # full staged suite: expected 239
python -m pytest -q tests/smoke/test_smk_006_order_verified_full_source.py tests/smoke/test_smk_007_missing_source_low_hold.py tests/smoke/test_smk_013_live_chain_trace.py tests/smoke/test_smk_018_verified_immutable_adjustment.py
```

## Exit-gate legs (slice M6.2E done-gate, itemized)

| Leg | Requirement | Covered by |
|---|---|---|
| L1 | Order Verified trace to source (ads_attribution_context) | SMK-006/007/013 collectively + `test_attribution_*` / `test_live_session_chain_trace.py` |
| L2 | Smoke M6-SMK-006 executed | closed by M6-P1404 (built here) |
| L3 | Smoke M6-SMK-007 executed | closed by M6-P1404 (built here) |
| L4 | Smoke M6-SMK-013 executed | closed by M6-P1404 (built here) |
| L5 | Proposed smoke M6-SMK-018 executed OR owner-waived | executed here (not waived); closed by M6-P1404 |

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-008 | Verified attribution/revenue snapshots immutable (set-once); corrections are audited adjustments (SMK-006/018). |
| M6-RULE-009 | Missing/conflicting sources degrade to LOW/HOLD; never scale evidence (SMK-006/007). |
| M6-RULE-019 | Module 6 never computes commission; referral/diamond ids recorded for attribution only. |
| M6-FAIL-001 | Double count / revenue misuse — revenue only from ORDER_VERIFIED (SMK-006/007 guard). |
| M6-FAIL-004 | Core/order-state override — the resolver reads consumed sources only, never overrides Core. |
| Exit legs | L1 trace-to-source, L2 SMK-006, L3 SMK-007, L4 SMK-013, L5 SMK-018 (`00-spec/slices/M6.2E.md`). |

## Provenance / notes

- Scenario & expected text quoted **verbatim** from `00-spec/registers/SMOKE_REGISTER.md` (rows M6-SMK-006,
  M6-SMK-007, M6-SMK-013 and the proposed M6-SMK-018 row). Test patterns reused from the existing
  `tests/conftest.py` and the coder's `tests/test_attribution_*.py` / `tests/test_verified_immutable_adjustment.py`
  (doc working mode, extract line 466).
- No self-certification of PASS or of gate/leg advancement: the runner EVIDENCE_GATE and the slice Judge
  decide. This manifest and the four smoke files are the *build*; the formal executed results are produced in
  M6-P1404.
