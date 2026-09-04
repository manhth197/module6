# SMOKE_RESULTS — Slice M6.2L (post-pilot audit fix batch: A3/A4/B2/B3/B4)

| Field | Value |
|---|---|
| Prompt | M6-P2104 — `M6_2L_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test** — the M6.2L smoke suite is EXECUTED here and results recorded. Smoke legs were authored in M6-P2103 (`M6_2L_TESTER_BUILD`). |
| Smoke ids executed | **M6-SMK-019, M6-SMK-020, M6-SMK-021, M6-SMK-022, M6-SMK-023** (5 `proposed — HARDENING, owner review`; executed here, not owner-waived) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Staging root | `04-artifacts/impl/M6.2L/` (STAGED_ONLY; convention reference, not a live repo) |
| Evidence-leg result | **17 passed, 0 failed — exit 0** (3 + 3 + 4 + 4 + 3) |
| Full staged suite | **561 passed, 0 failed, 0 skipped, 0 error — RC 0** |
| Overall | **all 5 bound smoke ids PASS; no failures; nothing patched; the 5 audit fixes proven by regression** |

> **Governance (immutable — nothing in this run flips a flag; this slice only proves the fixes with regression evidence):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all scale/hash/learning flags `False`,
> `live_migrations=false`. No application code changed by the TESTER, no migration, no external call, no flag flipped,
> no ROAS Pass / Scale Ready declared. The evidence pack still tops at `OWNER_REVIEW_REQUIRED` and carries the 8
> standing blockers; `M6-P1000` / `M6-P1309` stay BLOCKED. `status` is an honest TESTER self-report; the runner
> EVIDENCE_GATE and the slice Judge (M6-P2109) decide closure.

## Per-smoke results (scenario / expected verbatim from SMOKE_REGISTER; all PASS)

The `correlation_id` / `evidence_id` per smoke are **synthetic** trace ids for the doc §22 Smoke Report, shown in
their **export-masked** form (`app.measurement.masking.mask`, RULE-014/H02); the raw synthetic value is
`corr_2l_0NN` / `ev_2l_0NN`.

| Smoke ID | Audit item | Test file (`tests/smoke/…`) | Nodes | Result | correlation_id (masked) | evidence_id (masked) | Kịch bản → Kết quả phải đạt (verbatim) |
|---|---|---|---|---|---|---|---|
| M6-SMK-019 | A3 | `test_smk_019_attribution_id_trace.py` | 3 | **PASS** | `cor***19` | `ev_***19` | "ORDER_VERIFIED with a resolved ad source" → "attribution_id present as a first-class key of AdsAttributionContext + handoff payload; ORDER_VERIFIED traces attribution_id -> campaign" |
| M6-SMK-020 | A4 | `test_smk_020_ad_hierarchy_intake.py` | 3 | **PASS** | `cor***20` | `ev_***20` | "POST /api/ads/events/track for a FACEBOOK_AD event carrying campaign/adset/ad/live_session" → "intake + normalize persist the 4 ad-hierarchy ids; resolver reaches HIGH source confidence via the real API path" |
| M6-SMK-021 | B2 / M6-OD-013 | `test_smk_021_evidence_ref_forgery_blocked.py` | 4 | **PASS** | `cor***21` | `ev_***21` | "Evidence pack assembled with a fake-but-nonblank ref, or one valid ref copy-pasted across all mandatory keys of all 10 categories" → "categories read MISSING (never COMPLETE); ref existence + uniqueness + category-binding enforced, not raw truthiness" |
| M6-SMK-022 | B3 / M6-OD-014 | `test_smk_022_gap_id_collision_floor.py` | 4 | **PASS** | `cor***22` | `ev_***22` | "Gap-blocker list carries a duplicated/shadowing standing-blocker id (M6-P1000/M6-P1309)" → "the floor detects the duplicate and FAILs (membership count, not set-subset)" |
| M6-SMK-023 | B4 | `test_smk_023_roas_verified_lock.py` | 3 | **PASS** | `cor***23` | `ev_***23` | "In-process QUOTE_SENT row + store.materialize(revenue_value>0, verified=True)" → "no revenue set (event_code enforced at materialize); dashboard Revenue Verified = 0 and ROAS = 0 (event_code filter at verified_rows)" |

**Evidence-leg nodes: 17 (3 + 3 + 4 + 4 + 3), all PASSED.**

### M6-SMK-019 — attribution_id trace (A3) · **PASS (3/3)**

- `test_smk_019_attribution_id_first_class_and_traces_to_campaign` (primary) — PASS: `attribution_id` is first-class
  on `to_public` / `as_stored`; a materialized ORDER_VERIFIED row traces `attribution_id → campaign`.
- `test_smk_019_neg_attribution_id_is_deterministic_rematerialize_stable` — PASS: two resolves yield the same id
  (idempotent, no fork).
- `test_smk_019_neg_attribution_id_is_governance_ref_not_pii_and_no_commission` — PASS: unmasked governance ref;
  no commission field (RULE-014/019).

### M6-SMK-020 — ad-hierarchy intake (A4) · **PASS (3/3)**

- `test_smk_020_track_persists_four_ad_ids_and_resolver_reaches_high` (primary) — PASS: the 4 ad-hierarchy ids
  persist through the real track intake + normalize; resolver → FACEBOOK_AD / HIGH / NONE, live_session traced.
- `test_smk_020_neg_non_string_ad_id_is_fail_closed_reject` — PASS: a non-string id → REJECTED SCHEMA_INVALID
  (field=campaign_id), RULE-H03 fail-closed.
- `test_smk_020_neg_incomplete_ad_path_plus_live_stays_multi_touch` — PASS: campaign-only + live → MULTI_TOUCH / LOW
  (narrow rule doesn't over-dominate; preserves carried SMK-007).

### M6-SMK-021 — evidence-ref forgery blocked (B2 / M6-OD-013) · **PASS (4/4)**

- `test_smk_021_fake_but_nonblank_ref_leaves_category_missing` (primary pt 1) — PASS: a fake `"x"` ref → category
  MISSING, pack NOT_READY.
- `test_smk_021_one_valid_ref_copy_pasted_everywhere_is_all_missing` (primary pt 2) — PASS: one valid ref reused for
  every slot → all categories MISSING (uniqueness + binding), NOT_READY.
- `test_smk_021_neg_wrong_category_binding_is_missing` — PASS: a Consent-bound ref placed in Dedup → Dedup MISSING.
- `test_smk_021_control_genuine_unique_bound_refs_all_complete` — PASS: honest ref set → all COMPLETE,
  OWNER_REVIEW_REQUIRED (non-vacuous).

### M6-SMK-022 — gap-id collision floor (B3 / M6-OD-014) · **PASS (4/4)**

- `test_smk_022_duplicated_standing_id_fails_floor` (primary) — PASS: a duplicated M6-P1000 → `standing_floor_ok`
  False while the naive subset check passes; a clean assembled pack passes the floor + carries all 8 standing blockers.
- `test_smk_022_neg_shadowing_standing_id_fails_floor` — PASS: a shadow M6-P1309 (same id, different content) → False.
- `test_smk_022_neg_missing_standing_id_fails_floor` — PASS: a dropped M6-P1000 → False.
- `test_smk_022_control_canonical_list_passes_floor` — PASS: the canonical list passes (non-vacuous).

### M6-SMK-023 — ROAS verified-lock (B4) · **PASS (3/3)**

- `test_smk_023_quote_materialized_verified_sets_no_revenue_and_zero_dashboard` (primary) — PASS: a QUOTE_SENT row +
  `materialize(revenue>0, verified=True)` sets **no** revenue (event_code self-check drops it WITHOUT raising);
  dashboard **Revenue Verified = 0.0** and **ROAS is None**.
- `test_smk_023_neg_verified_rows_filter_excludes_leaked_quote_row_both_choke_points` — PASS: both `verified_rows`
  choke points (data_mart + growth.reads) exclude a directly-built leaked QUOTE_SENT row.
- `test_smk_023_control_genuine_order_verified_still_counts` — PASS: a genuine ORDER_VERIFIED → Revenue Verified =
  180000.0 (non-vacuous).

## TESTER note — SMK-023 "ROAS = 0" (register wording vs frozen code; executed result)

The register EXPECTED reads "Revenue Verified = 0 and **ROAS = 0**". With zero verified revenue AND no ads spend the
frozen dashboard computes `ROAS = _safe_div(0.0, None) → None` (fail-closed, RULE-003) — a present, positive Ads Spend
would be required for `0/spend == 0`, which this scenario does not supply. The executed assertion is therefore
`metric("ROAS").value is None` — the honest fail-closed realization of "ROAS = 0" (no revenue, no spend ⇒ no ROAS),
matching the frozen code and the coder's B4 regression. The M6-P2103 adversarial critic independently adjudicated this
handling as **CORRECT (not a defect)**. **Operator-hygiene (non-blocking):** reword the SMK-023 register "ROAS = 0"
line to the fail-closed None, or a future run may supply a mapped `ads_spend` so `ROAS == 0.0` literally — flagged, not
fixed here (the TESTER does not fix code/spec under test).

## Supporting / regression coverage (inside the 561 full suite, all green)

The full staged suite re-ran green: the coder's M6.2L regression tests (`tests/test_m6_2l_a3_attribution_id_trace.py`,
`_a4_ad_hierarchy_intake.py`, `_b2_evidence_ref_forgery.py`, `_b3_gap_floor_membership.py`, `_b4_verified_lock.py`),
the carried M6.2A–K tree, and the M6.2K evidence-pack + 18-smoke suite. Full total **561 passed, 0 failed** (= carried
+ coder M6.2L baseline 544 + the 17 new official-smoke nodes).

## Commands run (from `04-artifacts/impl/M6.2L/`, no shell redirection, cache-free)

The role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path, so no redirection is used;
`PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider` keep the run cache-free.

```bash
# 1) full staged suite + per-smoke tally, counted in-process via pytest_runtest_logreport
python.exe -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider']); pytest stdout swallowed>"
#   -> RC 0 ; COUNTS passed=561 failed=0 skipped=0 error=0 ; FAILS [] ; each evidence leg pass=(3,3,4,4,3) fail=0

# 2) the 5 evidence legs isolated (cross-check)
python.exe -c "<tally; pytest.main([<the 5 tests/smoke/test_smk_019..023 files>, '-p','no:cacheprovider'])>"
#   -> RC 0 ; SUBSET passed=17 failed=0 skipped=0 error=0 ; FAILS []
```

> **On counting.** pytest's terminal summary is not reliably captured in this harness, so the full-suite total
> (**561**) and the per-smoke breakdown came from an in-process `pytest_runtest_logreport` tally
> (`passed=561, failed=0, skipped=0, error=0`) with `pytest.main() RC=0`; the isolated 5-leg run independently
> confirms `17 passed`. pytest's own per-item output was swallowed (`redirect_stdout`) so the tally prints cleanly.

Cache hygiene: `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

## Boundary / safety observed during this run

- **Revenue only from ORDER_VERIFIED (RULE-003, FAIL-001):** QUOTE_SENT never became revenue at either choke point.
- **No forged evidence / no overstated readiness (RULE-015, FAIL-007):** evidence refs required real+unique+bound; the
  standing-blocker floor rejected duplicate/shadow/missing; the pack still tops at OWNER_REVIEW_REQUIRED.
- **PII-safe (RULE-014):** attribution_id / ad ids are synthetic governance refs; correlation/evidence ids masked on
  export; no raw phone/email/user-id.
- **No fix to code under test:** all 561 passed, so nothing needed reporting as a failure, and nothing was patched.
  No application code / migration / external call / flag flip / `04-artifacts/state/` write occurred.

## Exit-gate legs closed by this run (slice M6.2L done-gate)

| Leg | Requirement | Status |
|---|---|---|
| 1 | attribution_id trace (A3) | met — SMK-019 + coder `test_m6_2l_a3_*` green |
| 2 | ad-hierarchy intake (A4) | met — SMK-020 + coder `test_m6_2l_a4_*` green |
| 3 | evidence forgery blocked (B2 / M6-OD-013) | met — SMK-021 + coder `test_m6_2l_b2_*` green |
| 4 | gap-id collision/shadow detected (B3 / M6-OD-014) | met — SMK-022 + coder `test_m6_2l_b3_*` green |
| 5 | ROAS verified-lock (B4) | met — SMK-023 + coder `test_m6_2l_b4_*` green |
| 6 | Proposed smoke M6-SMK-019 executed | **PASS** (3/3) — executed |
| 7 | Proposed smoke M6-SMK-020 executed | **PASS** (3/3) — executed |
| 8 | Proposed smoke M6-SMK-021 executed | **PASS** (4/4) — executed |
| 9 | Proposed smoke M6-SMK-022 executed | **PASS** (4/4) — executed |
| 10 | Proposed smoke M6-SMK-023 executed | **PASS** (3/3) — executed |

> This run does NOT self-certify gate advancement (M6-RULE-015). It is the honest executed-results record of the
> TESTER. The runner EVIDENCE_GATE and the slice Judge (M6-P2109) decide closure; M6-P2105 (boundary adversary),
> M6-P2106 (security/PII), and the PM evidence-collect M6-P2107 come next. Posture stays BLOCKED/OFF/OFF.
