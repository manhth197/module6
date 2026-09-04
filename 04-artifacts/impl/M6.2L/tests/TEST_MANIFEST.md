# TEST_MANIFEST — Slice M6.2L smoke suite (post-pilot audit fix batch: A3/A4/B2/B3/B4)

| Field | Value |
|---|---|
| Prompt | M6-P2103 — `M6_2L_TESTER_BUILD` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — the M6.2L official smoke legs are AUTHORED here. This attempt ran a **collect-only build-validation** (imports/collects clean, no assertions executed) per the prompt's "Build (do not yet run)"; the **formal executed-results recording** belongs to M6-P2104. |
| Executed by (formal) | M6-P2104 (`M6_2L_TESTER_RUN`) → `04-artifacts/test-reports/M6.2L/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-019, M6-SMK-020, M6-SMK-021, M6-SMK-022, M6-SMK-023** (5 `proposed — HARDENING, owner review`; per `00-spec/slices/M6.2L.md` "Core smokes" + this prompt's `<smoke_ids>`) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Slice scope | Close the 5 M6-self-doable defects from the 2026-09-03 chief-auditor audit (against commit 5f09894) — A3 attribution_id trace, A4 ad-hierarchy intake, B2 evidence-ref forgery, B3 gap-id collision floor, B4 ROAS verified-lock — as a cumulative superset of M6.2K under `04-artifacts/impl/M6.2L/`. Regression evidence only; cross-module + owner-gated items tracked separately. |
| Staging root | `04-artifacts/impl/M6.2L/` (STAGED_ONLY; convention reference, not a live repo) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (proposed additions rows M6-SMK-019..023) + `00-spec/slices/M6.2L.md` |

> **Governance (immutable — nothing in this suite flips a flag; this slice only proves the fixes with regression evidence):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all scale/hash/learning flags `False`,
> `live_migrations=false`. No application code changed by the TESTER, no migration, no external call, no flag flipped,
> no ROAS Pass / Scale Ready declared. The evidence pack still tops out at `OWNER_REVIEW_REQUIRED` and carries the 8
> standing blockers; `M6-P1000` / `M6-P1309` stay BLOCKED. `status` is an honest TESTER self-report; the runner
> EVIDENCE_GATE and the slice Judge (M6-P2109) decide closure.

## What this suite is

Five **official smoke legs**, one per new smoke id, each carrying the register scenario/expected **verbatim** and
proving one audit fix through the frozen M6.2L code. They **coexist with the coder's regression tests** (M6-P2102,
`tests/test_m6_2l_*.py`) — the coder's tests pin the fix internally; these official smokes are the register-bound
proof surface. They reuse the shared [`tests/conftest.py`](04-artifacts/impl/M6.2L/tests/conftest.py) fixtures
(`make_measurement_event`, `make_conversion`, `attribution_resolver`, `make_verified_row`, `track_deps`,
`make_track_body`, `measurement_store`, `make_dashboard_deps`, `evidence_assembler`, `full_evidence_refs`,
`all_smokes_recorded`) — extended by the coder for the 4 ad-hierarchy ids. **No production code** and **no fix to the
code under test** (TESTER reports defects, never fixes them). All ids are synthetic; no raw secret/PII.

## Smoke → test binding (scenario/expected verbatim from SMOKE_REGISTER)

| Smoke ID | Audit item | New smoke leg (`tests/smoke/…`) | Nodes | Primary (scenario verbatim) | Negatives / control | Rule(s) | Fail gate | Exit leg |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-019 | A3 | `test_smk_019_attribution_id_trace.py` | 3 | `test_smk_019_attribution_id_first_class_and_traces_to_campaign` | `..._neg_attribution_id_is_deterministic_rematerialize_stable`, `..._neg_attribution_id_is_governance_ref_not_pii_and_no_commission` | M6-RULE-014 | — | 1 / 6 |
| M6-SMK-020 | A4 | `test_smk_020_ad_hierarchy_intake.py` | 3 | `test_smk_020_track_persists_four_ad_ids_and_resolver_reaches_high` | `..._neg_non_string_ad_id_is_fail_closed_reject`, `..._neg_incomplete_ad_path_plus_live_stays_multi_touch` | M6-RULE-014 (+RULE-H03) | — | 2 / 7 |
| M6-SMK-021 | B2 / M6-OD-013 | `test_smk_021_evidence_ref_forgery_blocked.py` | 4 | `test_smk_021_fake_but_nonblank_ref_leaves_category_missing` + `..._one_valid_ref_copy_pasted_everywhere_is_all_missing` | `..._neg_wrong_category_binding_is_missing`, `..._control_genuine_unique_bound_refs_all_complete` | M6-RULE-015 | M6-FAIL-007 | 3 / 8 |
| M6-SMK-022 | B3 / M6-OD-014 | `test_smk_022_gap_id_collision_floor.py` | 4 | `test_smk_022_duplicated_standing_id_fails_floor` | `..._neg_shadowing_standing_id_fails_floor`, `..._neg_missing_standing_id_fails_floor`, `..._control_canonical_list_passes_floor` | M6-RULE-015 | M6-FAIL-007 | 4 / 9 |
| M6-SMK-023 | B4 | `test_smk_023_roas_verified_lock.py` | 3 | `test_smk_023_quote_materialized_verified_sets_no_revenue_and_zero_dashboard` | `..._neg_verified_rows_filter_excludes_leaked_quote_row_both_choke_points`, `..._control_genuine_order_verified_still_counts` | M6-RULE-003 | M6-FAIL-001 | 5 / 10 |

**New M6.2L official-smoke nodes: 17 (3 + 3 + 4 + 4 + 3).**

## Per-smoke summary (what each leg proves)

- **M6-SMK-019 (A3):** `attribution_id` is a first-class key of `AdsAttributionContext`, present on both handoff
  surfaces (`to_public` / `as_stored`); a materialized ORDER_VERIFIED row traces `attribution_id → campaign`. It is
  deterministic (a re-materialize is stable — no fork), a governance ref (not masked, RULE-014), and there is no
  commission field (RULE-019).
- **M6-SMK-020 (A4):** `POST /api/ads/events/track` + normalize persist the 4 M6-owned ad-hierarchy ids
  (campaign/adset/ad/live_session); a COMPLETE FACEBOOK_AD path reaches FACEBOOK_AD / HIGH / NONE via the real API
  path (live_session traced, not a competing channel). Fail-closed: a non-string id is a SCHEMA_INVALID reject
  (RULE-H03); an incomplete ad path + live stays MULTI_TOUCH / LOW (preserves carried SMK-007).
- **M6-SMK-021 (B2 / M6-OD-013):** the pack assembler enforces evidence-ref **existence + uniqueness +
  (category,key)-binding**, not raw truthiness — a fake-but-nonblank ref, one valid ref copy-pasted everywhere, and a
  wrong-category binding all leave categories MISSING → `NOT_READY`; the honest full ref set still completes
  (OWNER_REVIEW_REQUIRED).
- **M6-SMK-022 (B3 / M6-OD-014):** `standing_floor_ok` counts membership, not a set-subset — a duplicated or
  shadowing standing-blocker id (M6-P1000 / M6-P1309), or a missing one, FAILs the floor; the canonical list and a
  clean assembled pack pass and carry all 8 standing blockers.
- **M6-SMK-023 (B4):** verified revenue counts only from ORDER_VERIFIED at BOTH choke points — `store.materialize()`
  self-checks the STORED event_code and fail-closed DROPS a QUOTE_SENT row's illegitimate revenue WITHOUT raising;
  `verified_rows()` (data_mart + growth.reads) filters by event_code. Dashboard Revenue Verified = 0; a genuine
  ORDER_VERIFIED still counts.

## TESTER note — SMK-023 "ROAS = 0" (register wording vs frozen code)

The register EXPECTED text reads "dashboard Revenue Verified = 0 and **ROAS = 0**". With zero verified revenue AND no
ads spend the frozen dashboard computes `ROAS = safe_div(0, None) → None` (fail-closed, M6-RULE-003), so the smoke
asserts `metric("ROAS").value is None` — the honest realization of the register's "ROAS = 0" (no revenue, no spend ⇒
no ROAS). The scenario/expected are still quoted verbatim in the docstring; the assertion matches the FROZEN code (the
TESTER does not fix code under test). This is the same behavior the coder's B4 regression asserts. **Operator-hygiene
(non-blocking):** reword the SMK-023 register line's "ROAS = 0" to the fail-closed "ROAS = None (no spend)", or the
run may instead supply a mapped ads_spend so `ROAS == 0.0` literally — flagged for the operator / M6-P2104, not fixed
here.

## Fixtures reused (from `tests/conftest.py`)

| Fixture | Role |
|---|---|
| `make_measurement_event(event_id, event_code=, page_id=, campaign_id=, adset_id=, ad_id=)` | seed a Zone-A event (now with the ad-hierarchy ids, A3/A4) |
| `make_conversion(event_code, source_event_id=)` | build a ConversionEvent for `attribution_resolver.resolve` |
| `attribution_resolver` | `AttributionResolver` — `.resolve(event, conv, signals=)` → ctx (attribution_id, entry_channel, source_confidence, conflict_status) |
| `make_verified_row(event_id, revenue=, order_code=, signals=, campaign_id=, adset_id=, ad_id=)` | seed + materialize a verified ORDER_VERIFIED row |
| `track_deps`, `make_track_body(event_code=, guest_id=, campaign_id=, adset_id=, ad_id=, live_session_id=)` | the real `handle_track_request` path (A4) |
| `measurement_store`, `make_dashboard_deps` | store + `handle_dashboard_request` dashboard view (B4) |
| `evidence_assembler`, `full_evidence_refs`, `all_smokes_recorded` | the pack assembler + honest ref set + recorded smokes (B2/B3) |

## Boundary / safety asserted by the suite

- **Revenue only from ORDER_VERIFIED (RULE-003, FAIL-001):** QUOTE_SENT never becomes revenue at either choke point.
- **No overstated readiness / no forged evidence (RULE-015, FAIL-007):** evidence refs must be real+unique+bound; the
  standing-blocker floor cannot be fooled by a duplicate/shadow; the pack still tops at OWNER_REVIEW_REQUIRED.
- **PII-safe (RULE-014):** attribution_id / ad ids are governance refs (synthetic); no raw phone/email/user-id.
- **No fix to code under test; no application code / migration / external call / flag flip / `04-artifacts/state/`
  write** anywhere in the suite. M6-P1000 / M6-P1309 stay BLOCKED and remain in the assembled pack.

## Build-validation performed in M6-P2103 (attempt 1, collect-only — "do not yet run")

Per the prompt's `<task>` ("Build (do not yet run)"), this attempt ran **collect-only** (imports + collects; **no
assertions executed**). Run with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest 8.4.2**, from
`04-artifacts/impl/M6.2L/`, **no shell redirection** (the role guard blocks a `>`/`2>` co-occurring with the venv
`Scripts` path), cache-free (`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```bash
python.exe -c "<in-process pytest_collection_finish tally; pytest.main(['--collect-only','-q','-p','no:cacheprovider'])>"
#   -> RC 0 ; COLLECTED_TOTAL=561 ; NEW_TOTAL=17 (019:3, 020:3, 021:4, 022:4, 023:3) ; 0 collection errors
```

Reconciliation: **561** collected = M6.2L carried+coder baseline **544** (M6.2K 523 + 21 coder M6.2L regressions) +
these **17** new official-smoke nodes. Every new file imports + collects clean. A read-only **adversarial static
verification** (5 logic verifiers — one per fix, tracing every assertion through the frozen source — + 1
verbatim-string auditor + 1 completeness/PII/boundary critic that adjudicates the SMK-023 ROAS wording) was run
alongside — findings recorded in the M6-P2103 evidence.

> **On counting.** pytest's terminal summary is not reliably captured in this harness, so the total (**561**) came
> from an in-process `pytest_collection_finish` tally (`len(session.items)`) with pytest `RC=0`; pytest's own
> per-item output was swallowed (`redirect_stdout`).

Cache hygiene: `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

> **This build does NOT self-certify gate advancement.** Collect-only proves the smoke files import + collect against
> the frozen M6.2L code; it does not execute assertions. The **formal executed-results recording** (with a
> correlation_id + evidence_id per smoke) is produced by **M6-P2104** into
> `04-artifacts/test-reports/M6.2L/SMOKE_RESULTS.md`. The runner EVIDENCE_GATE and the slice Judge decide closure.

## Execution plan for M6-P2104 (`M6_2L_TESTER_RUN`)

Run the full staged suite and the 5 new smoke legs, then record structured results + a correlation_id + evidence_id
per smoke:

```bash
python -m pytest -q                                  # full staged suite: expected 561 passed
python -m pytest -q tests/smoke/test_smk_019_attribution_id_trace.py … test_smk_023_roas_verified_lock.py   # expected 17 passed
```

Record per smoke id PASS/FAIL/BLOCKED + detail + correlation_id + evidence_id (synthetic, masked). For SMK-023, assert
Revenue Verified == 0 and `ROAS is None` (no-spend fail-closed) OR supply a mapped ads_spend for `ROAS == 0` — see the
TESTER note above.

## Exit-gate legs (slice M6.2L done-gate, itemized)

| Leg | Requirement | Covered by |
|---|---|---|
| 1 | attribution_id trace (A3) | SMK-019 leg + coder `test_m6_2l_a3_*`; run by M6-P2104 |
| 2 | ad-hierarchy intake (A4) | SMK-020 leg + coder `test_m6_2l_a4_*`; run by M6-P2104 |
| 3 | evidence forgery blocked (B2 / M6-OD-013) | SMK-021 leg + coder `test_m6_2l_b2_*`; run by M6-P2104 |
| 4 | gap-id collision/shadow detected (B3 / M6-OD-014) | SMK-022 leg + coder `test_m6_2l_b3_*`; run by M6-P2104 |
| 5 | ROAS verified-lock (B4) | SMK-023 leg + coder `test_m6_2l_b4_*`; run by M6-P2104 |
| 6–10 | Proposed smoke M6-SMK-019 … 023 executed OR owner-waived | the 5 legs (built here); executed by M6-P2104 |
| 11 | All slice prompts have schema-valid evidence JSON | this evidence + downstream |
| 12 | Slice gate judge sign-off PASS | M6-P2109 (downstream) |
| 13 | Rollback steps documented | new smoke files → delete (no carried-forward file patched) |

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-003 | Revenue only from ORDER_VERIFIED (SMK-023). |
| M6-RULE-014 | No raw PII; attribution_id / ad ids are governance refs (SMK-019/020). |
| M6-RULE-015 | No self-certification; the pack declares no Pass/Ready (SMK-021/022). |
| M6-FAIL-001 | Revenue misuse — quote/draft counted as revenue (SMK-023 guard). |
| M6-FAIL-007 | No evidence → called PASS — forged evidence ref / dropped standing blocker (SMK-021/022 guard). |

## Provenance / notes

- Scenario & expected text quoted **verbatim** from `00-spec/registers/SMOKE_REGISTER.md` (proposed additions rows
  M6-SMK-019..023; derivation: FIX_M6 audit 2026-09-03 items A3/A4/B2/B3/B4). Test patterns reused from the coder's
  M6.2L regression tests (`tests/test_m6_2l_*.py`) and the shared conftest fixtures (doc working mode, extract line 466).
- **Rollback:** the 5 new `tests/smoke/test_smk_019..023_*.py` files → delete; **no carried-forward file is patched**,
  no production code added, no migration, no flag flipped.
- No self-certification of PASS or of gate/leg advancement: the runner EVIDENCE_GATE and the slice Judge decide. This
  manifest and the 5 smoke legs are the *build*; the formal executed results are produced in M6-P2104.
