# SMOKE_RESULTS — Slice M6.2Q (ads-spend import + live-session binding + CPA/ROAS-by-session, A5)

| Field | Value |
|---|---|
| Prompt | M6-P2504 — `M6_2Q_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test** — the M6.2Q smoke suite is EXECUTED here and results recorded. The smoke leg was authored in M6-P2503 (`M6_2Q_TESTER_BUILD`). |
| Smoke ids executed | **M6-SMK-029** (1 `proposed — HARDENING, owner review`; executed here, not owner-waived) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0**, run `-B` (`PYTHONDONTWRITEBYTECODE=1`), `-p no:cacheprovider` |
| Staging root | `04-artifacts/impl/M6.2Q/` (STAGED_ONLY; cumulative superset of M6.2P) |
| Evidence-leg result | **5 passed, 0 failed — exit 0** |
| Full staged suite | **631 passed, 0 failed, 0 skipped, 0 error — RC 0** |
| Overall | **the bound smoke id PASS; no failures; nothing patched; CPA/ROAS compute from mock approved spend; no egress, no real network** |

> **Governance (immutable — nothing in this run flips a flag, opens egress, or calls a real network):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all scale/hash/learning flags `False`,
> `live_migrations=false`. No application code changed by the TESTER, no migration, no external call / real Meta
> network / Marketing API, no real spend (mock in-test only), no flag flipped. Ad spend is campaign-level
> (`campaign_id`), NOT PII; actors masked on export; the checker free-text never reaches the audit trail raw. Verified
> revenue keeps the ORDER_VERIFIED lock (RULE-003). `M6-P1000` / `M6-P1309` stay BLOCKED. **HARD FORWARD CONDITIONS**
> (disclosed, not resolved here): M6-OD-002 (thresholds) + M6-OD-005 (attribution model) OPEN govern forward scale;
> M6-OD-011 server-bind + go-live before any real spend/egress. `status` is an honest TESTER self-report; the runner
> EVIDENCE_GATE + slice Judge (M6-P2509) decide closure.

## Per-smoke results (scenario / expected verbatim from SMOKE_REGISTER; PASS)

The `correlation_id` / `evidence_id` are **synthetic** doc-§22-style trace ids, shown export-masked
(`app.measurement.masking.mask`, RULE-014/H02); raw synthetic values `corr_2q_029` / `ev_2q_029`.

| Smoke ID | Fix | Test file (`tests/smoke/…`) | Nodes | Result | correlation_id (masked) | evidence_id (masked) | Scenario → Expected (verbatim) |
|---|---|---|---|---|---|---|---|
| M6-SMK-029 | A5 ads-spend + binding + CPA/ROAS-by-session | `test_smk_029_ads_spend_cpa_roas_by_session.py` | 5 | **PASS** | `cor***29` | `ev_***29` | "A spend import (mock CSV rows keyed by campaign_id) approved by a DISTINCT checker + a live-session-ads-binding; a self-approved import; a live_session with spend but no verified order (A5)" → "maker-checker enforced (self-approve rejected; only APPROVED imports materialize); CPA-by-live_session = spend / verified-order-count + ROAS = verified-revenue / spend computed per session from approved spend; spend outside a session window → daily total (not attributed to a session); no verified order → CPA fail-closed (no div-by-zero), ROAS=0; no PII, external_send OFF" |

**Evidence-leg nodes: 5, all PASSED.**

### M6-SMK-029 — ads-spend maker-checker + binding + CPA/ROAS-by-session · **PASS (5/5)**

- `test_smk_029_distinct_checker_approve_materialize_bind_session_cpa_roas` (primary) — PASS: a mock-CSV import →
  PROPOSED → a DISTINCT checker APPROVES → the worker materializes ONLY the APPROVED import into a campaign-level
  record (`adset/ad None → .mapped False`); bind `camp_1 → ls_1`; `SessionRoasReader.for_session("ls_1")` →
  `session_spend 100000.0` (bound + in-window, included despite `.mapped False`), `verified_orders 2` (in-window
  QUOTE_SENT contributes 0, RULE-003), `verified_revenue 500000.0`, `CPA 50000.0`, `ROAS 5.0`; `EXTERNAL_SEND == "OFF"`.
- `test_smk_029_neg_self_approve_rejected_never_materializes` — PASS: a self-approve (maker == checker) raises
  `AdsSpendImportGateViolation`; the import stays PROPOSED and materializes nothing.
- `test_smk_029_neg_zero_verified_session_cpa_failclosed_roas_zero` — PASS: a session with spend>0 but ZERO verified
  orders → `CPA is None` (no divide-by-zero) + `ROAS == 0.0` (wasted spend).
- `test_smk_029_neg_spend_outside_window_or_unbound_goes_to_daily_total` — PASS: out-of-window camp_1 spend + an
  unbound-campaign record → `daily_total() == 80000.0`, not session-attributed (the in-window record stays on ls_1).
- `test_smk_029_neg_no_raw_pii_from_checker_reaches_audit` — PASS: a PII-shaped value in the untrusted checker
  free-text never reaches the audit trail raw, yet `ADS_SPEND_IMPORT_APPROVED` is still audited (FAIL-008).

## Supporting / regression coverage (inside the 631 full suite, all green)

The full staged suite re-ran green: the coder's 3 A5 regression tests
(`tests/test_m6_2q_ads_spend_import_maker_checker.py`, `_binding_primary_campaign.py`, `_cpa_roas_by_session.py`),
the carried M6.2A–P tree, and the evidence-pack + P0-smoke suites. Full total **631 passed, 0 failed** (= 626 coder
M6.2Q baseline + the 5 new official-smoke nodes).

## Commands run (from `04-artifacts/impl/M6.2Q/`, no shell redirection, cache-free)

The role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path, so no redirection is used; `-B`
(`PYTHONDONTWRITEBYTECODE=1`) + `-p no:cacheprovider` keep the run cache-free.

```bash
# 1) full staged suite + per-smoke tally, counted in-process via pytest_runtest_logreport
python.exe -B -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider']); pytest stdout swallowed>"
#   -> RC 0 ; COUNTS passed=631 failed=0 skipped=0 error=0 ; FAILS [] ; SMK-029 5/5

# 2) the evidence leg isolated (cross-check, with node names)
python.exe -B -c "<tally; pytest.main(['tests/smoke/test_smk_029_ads_spend_cpa_roas_by_session.py','-p','no:cacheprovider'])>"
#   -> RC 0 ; SUBSET passed=5 failed=0 skipped=0 error=0 ; FAILS [] ; 5 node names present (primary + 4 neg)
```

> **On counting.** pytest's terminal summary is not reliably captured in this harness, so the full-suite total
> (**631**) and the per-smoke breakdown came from an in-process `pytest_runtest_logreport` tally
> (`passed=631, failed=0, skipped=0, error=0`) with `pytest.main() RC=0`; the isolated leg run independently confirms
> `5 passed`. pytest's own per-item output was swallowed (`redirect_stdout`).

Cache hygiene: `-B` / `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

## Boundary / safety observed during this run

- **Revenue only from ORDER_VERIFIED (RULE-003):** an in-window QUOTE_SENT contributed 0 to verified orders/revenue.
- **Maker-checker four-eyes (M6-OD-016):** a self-approve was refused; only the APPROVED import materialized.
- **Fail-closed CPA (FAIL-007):** spend / 0 verified → None (no divide-by-zero); ROAS = 0.0 for wasted spend.
- **No egress, no flag flipped, no real network:** the smoke READS `config.EXTERNAL_SEND == "OFF"`, used only mock
  in-test spend + in-memory stores, and wrote nothing to `04-artifacts/state/`. No raw PII (campaign-level spend;
  masked actors; checker free-text never reached audit raw).
- **No fix to code under test:** all 631 passed, so nothing needed reporting as a failure, and nothing was patched.
  No application code / migration / external call / flag flip / `04-artifacts/state/` write occurred.

## Exit-gate legs closed by this run (slice M6.2Q done-gate)

| Leg | Requirement | Status |
|---|---|---|
| 1 | ads_spend_import + maker-checker (M6-OD-016): distinct-checker APPROVED; only APPROVED materialize; self-approve rejected | met — SMK-029 primary + self-approve neg + coder `test_m6_2q_ads_spend_import_maker_checker.py` green |
| 2 | live-session-ads-binding.v1 + primary_campaign_id; spend attributed by campaign×session-window; out-of-window → daily total | met — SMK-029 primary + out-of-window neg + coder `test_m6_2q_binding_primary_campaign.py` green |
| 3 | CPA/ROAS-by-live_session from APPROVED spend (RULE-003); zero-verified → CPA fail-closed None, ROAS 0 | met — SMK-029 primary + zero-verified neg + coder `test_m6_2q_cpa_roas_by_session.py` green |
| 4 | Proposed smoke M6-SMK-029 executed | **PASS** (5/5) — executed |

> This run does NOT self-certify gate advancement (RULE-015). It is the honest executed-results record of the TESTER.
> The runner EVIDENCE_GATE and the slice Judge (M6-P2509) decide closure; M6-P2505 (boundary), M6-P2506 (security/PII),
> and the PM evidence-collect M6-P2507 come next. Posture stays BLOCKED/OFF/OFF; the M6-OD-002/005 + M6-OD-011 hard
> forward conditions remain open for the exit judge (no real spend/egress until decided).
