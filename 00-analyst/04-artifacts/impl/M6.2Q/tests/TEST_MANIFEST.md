# TEST_MANIFEST — Slice M6.2Q smoke suite (ads-spend import + live-session binding + CPA/ROAS-by-session, A5)

| Field | Value |
|---|---|
| Prompt | M6-P2503 — `M6_2Q_TESTER_BUILD` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — the M6.2Q official smoke is AUTHORED here. This attempt ran a **collect-only build-validation** (imports/collects clean, no assertions executed) per "Build (do not yet run)"; the **formal executed-results recording** belongs to M6-P2504. |
| Executed by (formal) | M6-P2504 (`M6_2Q_TESTER_RUN`) → `04-artifacts/test-reports/M6.2Q/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-029** (1 `proposed — HARDENING, owner review`; per `00-spec/slices/M6.2Q.md` "Core smokes" + this prompt's `<smoke_ids>`) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Slice scope | M6-side ads-spend ingest (maker-checker, M6-OD-016) + live-session-ads-binding.v1 + primary_campaign_id + CPA/ROAS-by-live_session, so ROAS/CPA compute from real (mock-in-test) ad spend. Everything STAGED (in-memory stores + migration-defined tables 0014–0016; mock CSV); **no real Meta network / Marketing API, no real spend, no flag flipped**. |
| Staging root | `04-artifacts/impl/M6.2Q/` (STAGED_ONLY; cumulative superset of M6.2P) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (proposed additions row M6-SMK-029) + `00-spec/slices/M6.2Q.md` |

> **Governance (immutable — nothing in this suite flips a flag or opens egress):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all scale/hash/learning flags `False`,
> `live_migrations=false`. No application code changed by the TESTER, no migration, no external call / real Meta
> network, no flag flipped. Ad spend is campaign-level (`campaign_id`), NOT PII; actors (`uploaded_by`/`decided_by`/
> `bound_by`) are masked on export; the checker free-text is untrusted and never reaches the audit trail raw. Verified
> revenue keeps the ORDER_VERIFIED lock (RULE-003). `M6-P1000` / `M6-P1309` stay BLOCKED. **HARD FORWARD CONDITIONS**
> (disclosed, not resolved here): M6-OD-002 (thresholds) + M6-OD-005 (attribution model) OPEN govern forward scale;
> M6-OD-011 server-bind + go-live before any real spend/egress. `status` is an honest TESTER self-report; the runner
> EVIDENCE_GATE + slice Judge (M6-P2509) decide closure.

## What this suite is

One **official smoke leg** for M6-SMK-029, carrying the register scenario/expected **verbatim** and proving the A5
chain end-to-end through the frozen M6.2Q code: a mock-CSV spend import → maker-checker approve → materialize →
live-session binding → CPA/ROAS-by-session. It **coexists with the coder's 3 regression tests**
(`tests/test_m6_2q_ads_spend_import_maker_checker.py`, `_binding_primary_campaign.py`, `_cpa_roas_by_session.py`,
M6-P2502) and reuses the shared [`tests/conftest.py`](04-artifacts/impl/M6.2Q/tests/conftest.py) fixtures (`audit`,
`measurement_store`, `make_verified_row`, `make_measurement_event`). **No production code** and **no fix to the code
under test**. All ids synthetic; PII markers assembled at runtime.

## Smoke → test binding (scenario/expected verbatim from SMOKE_REGISTER)

| Smoke ID | Fix | Test file (`tests/smoke/…`) | Nodes | Primary (scenario verbatim) | Negatives | Rule(s) | Fail gate | Exit leg |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-029 | A5 ads-spend + binding + CPA/ROAS-by-session | `test_smk_029_ads_spend_cpa_roas_by_session.py` | 5 | `test_smk_029_distinct_checker_approve_materialize_bind_session_cpa_roas` | `..._neg_self_approve_rejected_never_materializes`, `..._neg_zero_verified_session_cpa_failclosed_roas_zero`, `..._neg_spend_outside_window_or_unbound_goes_to_daily_total`, `..._neg_no_raw_pii_from_checker_reaches_audit` | M6-RULE-003, M6-RULE-015 | M6-FAIL-007 | 1–3 / 4 |

**New M6.2Q official-smoke nodes: 5.**

## Per-smoke summary (what the leg proves — maps the verbatim expected clause-by-clause)

- **Primary (end-to-end):** a mock-CSV import (rows keyed by `campaign_id`) enters PROPOSED; a **DISTINCT** checker
  (maker ≠ checker) approves → APPROVED; the worker materializes **only** the APPROVED import into a campaign-level
  spend record; a binding maps `camp_1 → ls_1`; `SessionRoasReader.for_session("ls_1")` computes
  `CPA = spend / verified-order-count` (100000/2 = 50000) and `ROAS = verified-revenue / spend` (500000/100000 = 5.0)
  from the approved spend — the record is campaign-level (`adset/ad None → .mapped False`) yet included (the sum gates
  on the **binding**, not `.mapped`); an in-window `QUOTE_SENT` contributes 0 (RULE-003). Asserts `EXTERNAL_SEND == "OFF"`.
- **Negative — self-approve rejected:** an APPROVE whose checker equals the maker raises `AdsSpendImportGateViolation`;
  the import stays PROPOSED and materializes nothing (maker-checker enforced).
- **Negative — zero-verified fail-closed:** a session with spend>0 but ZERO verified orders → `CPA is None` (no
  divide-by-zero) and `ROAS == 0.0` (wasted spend). *(Per the coder's leg-3 note, the zero-verified case carries
  spend>0 so ROAS resolves to 0.0, not None.)*
- **Negative — out-of-window / unbound → daily total:** spend whose `spend_date` is outside the session window, and
  spend on an unbound campaign, are excluded from the session and land in `daily_total()` (not session-attributed).
- **Negative / PII-safe:** a PII-shaped value in the untrusted checker free-text never reaches the audit trail raw,
  yet the decision is still audited (machine-safe, FAIL-008).

## Fixtures / APIs under test

| Fixture / API | Role |
|---|---|
| `audit`, `measurement_store`, `make_verified_row(id, revenue=, order_code=, live_session_id=, event_ts=)`, `make_measurement_event(id, event_code=, live_session_id=, event_ts=)` | conftest — seed the session's verified orders + quotes |
| `AdsSpendImportGate.propose / record_decision` (+ `AdsSpendImportGateViolation`) | maker-checker four-eyes gate (self-approve/blank refused) |
| `AdsSpendMaterializer.run_once` | drains ONLY APPROVED imports → set-once campaign-level records |
| `AdsSpendImportStore` / `AdsSpendRecordStore` | staged in-memory stores |
| `LiveSessionAdsBindingStore.bind` / `session_for_campaign` + `LiveSessionAdsBinding` | campaign→session binding.v1 |
| `SessionRoasReader(measurement_store, records, binding).for_session / daily_total` | CPA/ROAS-by-session (RULE-003 lock; fail-closed) |
| `AdsSpendRecord` (data_mart) + `config.EXTERNAL_SEND` | build out-of-window records + read the immutable egress flag |

## Boundary / safety asserted by the suite

- **Revenue only from ORDER_VERIFIED (RULE-003):** an in-window QUOTE_SENT contributes 0 to verified orders/revenue.
- **Maker-checker four-eyes (M6-OD-016):** a self-approve is refused; only APPROVED imports materialize.
- **Fail-closed CPA (FAIL-007):** spend / 0 verified → None (no divide-by-zero); no-bound-spend → None (never a
  fabricated 0).
- **No egress, no flag flipped, no real network:** the smoke READS `config.EXTERNAL_SEND == "OFF"`, uses only mock
  in-test spend, and writes nothing to `04-artifacts/state/`. **No raw PII** (campaign-level spend; masked actors;
  checker free-text never reaches audit raw).
- **No fix to code under test.** M6-P1000 / M6-P1309 stay BLOCKED.

## Build-validation performed in M6-P2503 (attempt 1, collect-only — "do not yet run")

Per the prompt's `<task>` ("Build (do not yet run)"), this attempt ran **collect-only** (imports + collects; **no
assertions executed**). Run with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest 8.4.2**, from
`04-artifacts/impl/M6.2Q/`, **no shell redirection** (the role guard blocks a `>`/`2>` co-occurring with the venv
`Scripts` path), cache-free (`-B` / `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```bash
python.exe -B -c "<in-process pytest_collection_finish tally; pytest.main(['--collect-only','-q','-p','no:cacheprovider'])>"
#   -> RC 0 ; tests/smoke/test_smk_029_ads_spend_cpa_roas_by_session.py collects 5 nodes ; full-suite collect clean ; 0 collection errors
```

Reconciliation: the full-suite collect total = M6.2Q coder baseline **626** (603 carried M6.2P + 23 coder M6.2Q
regressions) + these **5** new official-smoke nodes = **631**. A read-only **adversarial static verification** (1
logic verifier tracing all 5 nodes through the frozen import-gate/materializer/binding/SessionRoasReader + a
verbatim-string auditor + a completeness/PII/boundary critic) was run alongside — findings recorded in the M6-P2503
evidence.

> **This build does NOT self-certify gate advancement.** Collect-only proves the smoke file imports + collects against
> the frozen M6.2Q code; it does not execute assertions. The **formal executed-results recording** (with a
> correlation_id + evidence_id) is produced by **M6-P2504**. The runner EVIDENCE_GATE + slice Judge decide.

## Execution plan for M6-P2504 (`M6_2Q_TESTER_RUN`)

```bash
python -m pytest -q                                                                    # full staged suite: expected 631 passed
python -m pytest -q tests/smoke/test_smk_029_ads_spend_cpa_roas_by_session.py           # expected 5 passed
```

Record per smoke id PASS/FAIL/BLOCKED + detail + correlation_id + evidence_id. Confirm the zero-verified session
gives `CPA is None` + `ROAS == 0.0` (spend>0), the by-session sum gates on the binding (campaign-level record
`.mapped False` still included), and `config.EXTERNAL_SEND == "OFF"`.

## Exit-gate legs (slice M6.2Q done-gate, itemized)

| Leg | Requirement | Covered by |
|---|---|---|
| 1 | ads_spend_import + maker-checker (M6-OD-016): PROPOSED → distinct-checker APPROVED; only APPROVED materialize; self/single-actor rejected | SMK-029 primary + self-approve neg + coder `test_m6_2q_ads_spend_import_maker_checker.py`; run by M6-P2504 |
| 2 | live-session-ads-binding.v1 + primary_campaign_id; spend attributed by campaign×session-window; out-of-window → daily total | SMK-029 primary + out-of-window neg + coder `test_m6_2q_binding_primary_campaign.py`; run by M6-P2504 |
| 3 | CPA/ROAS-by-live_session from APPROVED spend (RULE-003); zero-verified → CPA fail-closed None, ROAS 0 | SMK-029 primary + zero-verified neg + coder `test_m6_2q_cpa_roas_by_session.py`; run by M6-P2504 |
| 4 | Proposed smoke M6-SMK-029 executed OR owner-waived | the leg; executed by M6-P2504 |
| 5 | All slice prompts have schema-valid evidence JSON | this evidence + downstream |
| 6 | Slice gate judge sign-off PASS | M6-P2509 (downstream; confirms no flag flip / no real spend / no Meta network / posture OFF-BLOCKED-OFF) |
| 7 | Rollback steps documented | new smoke file → delete (no carried-forward file patched); the A5 shipped-code rollback is per impl PLAN.md |

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-003 | Revenue only from ORDER_VERIFIED — an in-window quote contributes 0 to CPA/ROAS. |
| M6-RULE-015 | No self-certification; the maker-checker four-eyes control refuses a self-approve. |
| M6-FAIL-007 | No evidence → called PASS — fail-closed CPA (no divide-by-zero); only APPROVED spend materializes. |

## Provenance / notes

- Scenario & expected text quoted **verbatim** from `00-spec/registers/SMOKE_REGISTER.md` (proposed additions row
  M6-SMK-029; derivation: chief-auditor 2026-09-07 A3/A5 + C4; owner M6-OD-016 spend source + M6-OD-011 binding
  direction). Test patterns reused from the coder's M6.2Q regression tests + the shared conftest fixtures (doc working
  mode, extract line 466).
- **Rollback:** the new `tests/smoke/test_smk_029_ads_spend_cpa_roas_by_session.py` → delete; no production code, no
  migration, no flag flipped. The A5 shipped-code rollback is in the impl `PLAN.md`.
- No self-certification of PASS or of gate/leg advancement: the runner EVIDENCE_GATE and the slice Judge decide. This
  manifest and the smoke leg are the *build*; the formal executed results are produced in M6-P2504.
