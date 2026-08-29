# TEST_MANIFEST — Slice M6.2G smoke suite (Scale Gate / owner-decision workflow)

| Field | Value |
|---|---|
| Prompt | M6-P1603 — `M6_2G_TESTER_BUILD` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — the smoke tests are AUTHORED here. This attempt ran a **collect-only build-validation** (imports/collects clean, no assertions executed) per the prompt's "Build (do not yet run)"; the **formal executed-results recording** belongs to M6-P1604. |
| Executed by (formal) | M6-P1604 (`M6_2G_TESTER_RUN`) → `04-artifacts/test-reports/M6.2G/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-009, M6-SMK-012** (exactly — per `00-spec/slices/M6.2G.md` "Core smokes" + this prompt's `<smoke_ids>`) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Slice scope | doc §16 Scale Gate as an owner-decision workflow: the 8 scale conditions (Risk = hard veto), `ads_scale_request` lifecycle (M6-CTR-013/026), `POST /api/admin/ads/scale-requests` (M6-CTR-019); compute conditions, assemble evidence, PROPOSE — **never act** |
| Staging root | `04-artifacts/impl/M6.2G/` (STAGED_ONLY; convention reference, not a live repo) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (owner P0 matrix, extract lines 409 / 412) |

> **Governance (immutable — nothing in this suite flips a flag, and nothing is ever scaled):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `SCALE_EXECUTION_ENABLED=False`,
> `SCALE_MODEL_RATIFIED=False` (M6-OD-005 OPEN), `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False` (M6-OD-002 OPEN),
> `HASH_POLICY_RATIFIED=False`. The **Risk row is a hard veto** (RULE-017): any active recall / sale-lock /
> quality-hold / complaint-P0 / platform-spam-flag / CRM-suppression forces Risk = FAIL and the gate to FAIL; an
> unobserved risk state is fail-closed HOLD. **No executable scale path** exists (RULE-010 / FAIL-006): the
> module computes and proposes; raising a budget / enabling a campaign / opening audience scale is OWNER-only,
> outside Module 6. The system **never approves its own request** (RULE-015); a scale is authorized only on an
> explicit owner APPROVE **and** a clean PASS — never reached in the staged posture. No pricing (M3), order-state
> (M8), CRM send, or commission (RULE-019). `status` is an honest self-report; the runner EVIDENCE_GATE and the
> slice Judge (M6-P1609) decide closure.

## What this suite is

The **official M6.2G smoke suite**: one dedicated smoke file per bound smoke id, each carrying the register's
scenario/expected **verbatim**, driven through the M6.2G scale layer — `evaluate_conditions` (the 8 doc §16
conditions + worst-status overall), the `ScaleGate` (`propose` = compute + assemble evidence + inert PROPOSED
request; `record_owner_decision` = explicit APPROVE/REJECT with a fail-closed Risk re-check), the inert
`AdsScaleRequest` / `OwnerDecision` models, and the append-only `ScaleRequestStore` — plus the negative /
fail-closed companions the doc done-gate requires and positive controls for non-vacuity. It reuses the shared
fixtures in [`tests/conftest.py`](04-artifacts/impl/M6.2G/tests/conftest.py) (`scale_gate`, `scale_store`,
`make_scale_context`, `make_owner_decision`, `make_scale_deps`). No new production code, and **no fix to the code
under test** (TESTER reports defects, never fixes them).

All ids are **synthetic**; no raw secret/PII. The owner-decision `actor` (`owner_ops`) is a synthetic operator
id, masked on export; no phone / email / customer_id / psid appears anywhere.

M6.2G **carried the whole M6.2F tree forward** (cumulatively M6.2A–F, byte-identical) and the coder (M6-P1602)
added the scale layer with its own leg tests. The carried smokes and regression suites remain and re-run here as
supporting coverage; the **two files below are the new M6.2G-bound smokes** authored by this prompt.

## Smoke → test binding

| Smoke ID | Doc ID | Test file (M6.2G, new) | Nodes | Primary test (scenario verbatim) | Negative / fail-closed & control tests | Rule(s) | Fail gate | Exit leg |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-009 | ADS-P0-009 | [`tests/smoke/test_smk_009_recall_sale_lock_scale_fail.py`](04-artifacts/impl/M6.2G/tests/smoke/test_smk_009_recall_sale_lock_scale_fail.py) | 10 | `test_smk_009_active_risk_lock_forces_scale_gate_fail` (parametrized over the 6 Risk locks) | `..._recall_locked_request_cannot_be_approved`, `..._neg_unobserved_risk_is_hold_not_pass`, `..._neg_risk_recheck_catches_lock_after_clean_proposal`, `..._control_no_active_locks_risk_passes` | M6-RULE-017, M6-RULE-010 | M6-FAIL-006 | L3 |
| M6-SMK-012 | ADS-P0-012 | [`tests/smoke/test_smk_012_scale_no_owner_approval.py`](04-artifacts/impl/M6.2G/tests/smoke/test_smk_012_scale_no_owner_approval.py) | 4 | `test_smk_012_no_owner_approval_means_not_scale_authorized` | `..._neg_gate_cannot_self_approve`, `..._neg_recorded_owner_approve_still_not_scale_in_staged_posture`, `..._control_owner_reject_is_recorded_no_scale` | M6-RULE-020, M6-RULE-015, M6-RULE-010 | M6-FAIL-006 | L4 |

**New M6.2G smoke nodes: 14** (10 + 4).

---

## M6-SMK-009 — Recall / Sale Lock active → Scale Gate FAIL/HOLD

Verbatim from `00-spec/registers/SMOKE_REGISTER.md` (extract line 409):

```
Smoke ID:          M6-SMK-009  (Doc ID ADS-P0-009)
Kịch bản:          Recall/Sale Lock active
Kết quả phải đạt:  Scale Gate FAIL/HOLD
```

- **Primary (parametrized over the 6 Risk locks — doc §16 line 323 in full):** any active
  recall / sale_lock / quality_hold / complaint_p0 / platform_spam_flag / crm_suppression → Risk condition FAIL
  and overall gate FAIL (RULE-017 hard veto).
- **Approval refused:** a recall-locked proposal is overall FAIL and an owner APPROVE with recall active is
  refused (`ScaleGateViolation`, RULE-017 re-check); the request stays PROPOSED, `is_scale_authorized` False.
- **Negative — unobserved risk (the HOLD half):** empty `risk_flags` → Risk fail-closed HOLD, overall HOLD
  (never a clean PASS).
- **Negative — re-check catches a late lock:** a proposal computed while risk was clean (overall HOLD) still
  cannot be approved if a sale_lock is active at approval time (fresh-read veto).
- **Control:** the full risk row observed with NO lock active → Risk PASS (not FAIL) — the FAILs are lock-caused;
  overall is still HOLD in the staged posture.

## M6-SMK-012 — Scale request without owner approval → no scale

Verbatim (extract line 412):

```
Smoke ID:          M6-SMK-012  (Doc ID ADS-P0-012)
Kịch bản:          Scale request không owner approval
Kết quả phải đạt:  Không scale
```

- **Primary:** a proposed request (budget cap + rollback) with NO owner decision stays PROPOSED and
  `is_scale_authorized` is False — no scale (RULE-015).
- **Negative — no self-approve:** the gate exposes no `approve/auto_approve/self_approve/approve_all/authorize`
  (nor `scale/execute/raise_budget/enable_campaign`) entry point, and `SCALE_EXECUTION_ENABLED is False`
  (RULE-010 / RULE-015).
- **Negative — recorded APPROVE still not a scale:** even an explicit owner APPROVE (clean risk, cap + rollback)
  leaves `is_scale_authorized` False because the overall is HOLD (`SCALE_MODEL_RATIFIED=False`, M6-OD-005) — the
  honest fail-closed truth; nothing is executed.
- **Control:** an explicit owner REJECT is recorded (REJECTED) and is never a scale — the lifecycle records
  decisions, never executes one.

---

## Supporting / regression suite (run alongside the two bound smokes)

The full staged suite re-runs. Files below (coder M6-P1602) are **not** the two bound M6.2G smoke ids but pin
the scale layer the smokes rely on.

| File | Purpose | Nodes |
|---|---|---|
| [`tests/test_scale_gate_risk_veto.py`](04-artifacts/impl/M6.2G/tests/test_scale_gate_risk_veto.py) | SMK-009 leg — any active Risk lock → FAIL; risk-locked request cannot be approved | 7 |
| [`tests/test_scale_request_needs_owner_approval.py`](04-artifacts/impl/M6.2G/tests/test_scale_request_needs_owner_approval.py) | SMK-012 leg — no owner decision → stays PROPOSED; no self-approve | 2 |
| [`tests/test_no_executable_scale_path.py`](04-artifacts/impl/M6.2G/tests/test_no_executable_scale_path.py) | RULE-010 / FAIL-006 — no raise-budget/enable/open/send/publish method; `SCALE_EXECUTION_ENABLED is False` | 4 |
| [`tests/test_scale_request_lifecycle.py`](04-artifacts/impl/M6.2G/tests/test_scale_request_lifecycle.py) | CTR-013/026 — evidence + budget_cap + rollback; APPROVED only via explicit OwnerDecision; no-raw-PII-in-audit | 5 |
| [`tests/test_scale_conditions_failclosed.py`](04-artifacts/impl/M6.2G/tests/test_scale_conditions_failclosed.py) | CTR-013 — 8 conditions; Funnel/Dashboard fail-closed HOLD; never a clean PASS | 4 |
| [`tests/test_risk_recheck_at_approval.py`](04-artifacts/impl/M6.2G/tests/test_risk_recheck_at_approval.py) | RULE-017 — Risk re-checked at approval; empty/partial fresh read fail-closed | 4 |
| carried M6.2A–F suite | seam/tracking/outbox/integration/attribution/dashboard/DQ smokes + all unit + regression suites | 273 |

## Fixtures reused (from `tests/conftest.py`)

| Fixture | Role |
|---|---|
| `scale_store` | inert append-only `ScaleRequestStore` (`create` / `update_state` / `get` / `all` / `history`) |
| `scale_gate` | `ScaleGate(scale_store, audit)` — `propose(...)` (inert PROPOSED request) + `record_owner_decision(...)` (explicit APPROVE/REJECT, fail-closed Risk re-check) |
| `make_scale_context(**over)` | `ScaleContext` factory — best staged posture by default (entry evidence present, boundaries attested, DQ PASS, no risk locks, owner NOT approved) → still overall HOLD |
| `make_owner_decision(kind="APPROVE", **over)` | `OwnerDecision` factory (actor `owner_ops`, reason/audit/evidence) |
| `make_scale_deps(context)` | `ScaleRequestDeps(scale_gate, context, audit)` — inert; no transport/budget/execute handle |

## Boundary / safety asserted by the suite

- **No executable scale path (RULE-010, FAIL-006):** the gate / store / request / deps expose no
  raise-budget/enable/open/scale/send/publish/execute method; `SCALE_EXECUTION_ENABLED is False`.
- **Risk hard veto (RULE-017):** any active Risk-row lock → FAIL; unobserved risk → fail-closed HOLD; the veto
  is re-checked at approval time (a late lock refuses the approval).
- **Owner-decision gated (RULE-015 / RULE-020):** a scale is authorized only via an explicit owner APPROVE with a
  clean PASS + cap + rollback; the system never self-approves; in the staged posture no scale is ever authorized.
- **No commission (RULE-019), no pricing (M3), no order-state (M8), no CRM send, no flag flip, no external call,
  no `04-artifacts/state/` write** anywhere in the suite. Owner `actor` masked; no raw PII.

## Build-validation performed in M6-P1603 (attempt 1, collect-only — "do not yet run")

Per the prompt's `<task>` ("Build (do not yet run)"), this attempt ran **collect-only** (imports + collects; **no
assertions executed**). Run with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest 8.4.2**, from
`04-artifacts/impl/M6.2G/`, **no shell redirection** (the role guard blocks a `>`/`2>` co-occurring with the venv
`Scripts` path), cache-free (`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```bash
python.exe -m pytest tests/smoke/test_smk_009_recall_sale_lock_scale_fail.py tests/smoke/test_smk_012_scale_no_owner_approval.py --collect-only -q -p no:cacheprovider   # per-file: 10,4 ; EXIT=0
python.exe -c "<in-process pytest_collection_finish tally>" --collect-only   # COLLECTED_TOTAL=313 ; EXIT=0
```

Reconciliation: **313** collected = carried M6.2G baseline **299** (273 carried M6.2F tree + 26 coder M6.2G scale
leg tests) + these new smokes **14**. Both files import + collect clean (scale fixtures wired). A read-only
adversarial static verification (one verifier per smoke file tracing every assertion through the implementation,
+ a completeness critic) was run alongside — findings are recorded in the M6-P1603 evidence.

> **On counting.** In this harness pytest's terminal summary line is not captured for a long run, so the total
> (**313**) was obtained via an in-process `pytest_collection_finish` tally (`len(session.items)`) with pytest
> RC=0 and the `--collect-only` per-file sum agreeing.

Cache hygiene: `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

> **This build does NOT self-certify gate advancement.** Collect-only proves the smoke files import + collect
> against the frozen M6.2G code; it does not execute assertions. The **formal executed-results recording** is
> produced by **M6-P1604** into `04-artifacts/test-reports/M6.2G/SMOKE_RESULTS.md`. The runner EVIDENCE_GATE and
> the slice Judge decide closure.

## Execution plan for M6-P1604 (`M6_2G_TESTER_RUN`)

Run the full staged suite and the two bound smokes, then record structured results + evidence refs for the M6.2G
exit-gate smoke legs L3 (SMK-009) and L4 (SMK-012):

```bash
python -m pytest -q                    # full staged suite: expected 313 passed
python -m pytest -q tests/smoke/test_smk_009_recall_sale_lock_scale_fail.py tests/smoke/test_smk_012_scale_no_owner_approval.py   # expected 14 passed
```

## Exit-gate legs (slice M6.2G done-gate, itemized)

| Leg | Requirement | Covered by |
|---|---|---|
| L1 | No auto scale (no code path raises budget / enables campaign / opens audience scale) | SMK-009/012 boundary asserts + `test_no_executable_scale_path.py` |
| L2 | Owner approval required (request carries evidence + budget cap + rollback; transitions only via explicit owner approval) | SMK-012 + `test_scale_request_lifecycle.py` |
| L3 | Smoke M6-SMK-009 executed with recorded result | closed by M6-P1604 (built here) |
| L4 | Smoke M6-SMK-012 executed with recorded result | closed by M6-P1604 (built here) |

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-010 | Module 6 never executes a scale; it computes and proposes only (SMK-009/012; no executable path). |
| M6-RULE-015 | The system never approves its own request; transitions only via an explicit audited owner decision (SMK-012). |
| M6-RULE-017 | Risk row is a hard veto, re-checked at approval; unobserved risk is fail-closed (SMK-009). |
| M6-RULE-020 | Scale governance — a scale proceeds only through an owner-approved `ads_scale_request` (SMK-012); see the register for the full text. |
| M6-FAIL-006 | Auto-scale / acting without owner approval — the slice never acts (SMK-009/012 + `test_no_executable_scale_path.py`). |

## Provenance / notes

- Scenario & expected text quoted **verbatim** from `00-spec/registers/SMOKE_REGISTER.md` (rows M6-SMK-009,
  M6-SMK-012; extract lines 409 / 412). Test patterns reused from the existing `tests/conftest.py` scale fixtures
  and the coder's `tests/test_scale_gate_risk_veto.py`, `tests/test_scale_request_needs_owner_approval.py`,
  `tests/test_no_executable_scale_path.py` (doc working mode, extract line 466).
- No self-certification of PASS or of gate/leg advancement: the runner EVIDENCE_GATE and the slice Judge decide.
  This manifest and the two smoke files are the *build*; the formal executed results are produced in M6-P1604.
