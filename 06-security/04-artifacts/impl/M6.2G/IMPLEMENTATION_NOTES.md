# M6.2G IMPLEMENTATION NOTES — Scale Gate as an owner-decision workflow (STAGED)

**Prompt**: M6-P1602 (`M6_2G_CODER_IMPLEMENT`) · **Role**: CODER · **Mode**: `implement` · **Gate**: EVIDENCE_GATE
**Follows**: [PLAN.md](PLAN.md) (M6-P1601). Built item-by-item; one small plan-delta (§4). **Posture unchanged &
immutable**: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `HASH_POLICY_RATIFIED=False`,
`SCALE_MODEL_RATIFIED=False`, `SCALE_EXECUTION_ENABLED=False`, `live_migrations=false`. No code raises a budget,
enables a campaign, opens audience scale, sends, publishes, applies a migration, or flips a flag. **Nothing acts.**

> **Status: coder self-reported PASS** (the runner gate + JUDGE decide, RULE-015). The two module-critical
> invariants held CLEAN under adversarial review — **no executable scale path** (RULE-010/FAIL-006) and the
> **Risk-veto / owner-approval** discipline (RULE-017/RULE-015, SMK-009/012). The review confirmed 2 fail-closed/
> PII defects in new code — both **FIXED and locked with regressions** (§5) before this evidence.

## 1. Staging model — cumulative carry-forward

The whole **M6.2F** tree (273 tests as the slice finally stood after M6-P1503–1509) was carried forward
byte-identical into `04-artifacts/impl/M6.2G/` (caches excluded; `PLAN.md` kept, this file added). Baseline
verified green (273, rc 0) BEFORE any patch. Final suite: **299 passed, rc 0** (273 carried + 26 new). Subprocess counts.

## 2. Change set (all under `04-artifacts/impl/M6.2G/`)

**New — Scale-Gate layer**
| File | Purpose |
|---|---|
| `app/measurement/scale/conditions.py` | The 8 doc §16 conditions (verbatim, extract 317–324) — `evaluate_conditions(ctx)` → 8 `ConditionResult`s + worst-status overall. **Risk = hard veto** (RULE-017); **Funnel** (M6-OD-002) + **Dashboard-as-scale-evidence** (M6-OD-005/`SCALE_MODEL_RATIFIED=False`) are **fail-closed HOLD**; missing boundary signal → HOLD. So the gate can never be a clean scale-ready PASS in the staged posture. Reuses the M6.2F `worst_status`. |
| `app/measurement/scale/models.py` | `AdsScaleRequest` (CTR-013, **inert**) + `ApprovalState` (COMPUTED/PROPOSED/APPROVED/REJECTED) + `OwnerDecision`. `budget_cap`/`rollback_condition` are FIELDS, not actions. `is_scale_authorized` requires owner-APPROVE **and** overall==PASS + cap + rollback → **always False in staged posture** (honest fail-closed). |
| `app/measurement/scale/scale_gate.py` | `ScaleGate` (CTR-026 flow): `propose()` = compute + assemble evidence + inert PROPOSED request; `record_owner_decision()` = record explicit APPROVE/REJECT, **Risk re-checked at approval** (RULE-017, fail-closed), requires budget_cap + rollback + non-FAIL — else REFUSED. **No method raises budget / enables campaign / opens audience / sends / publishes** (RULE-010). Never self-approves (RULE-015). |
| `app/measurement/scale/scale_request_store.py` | Inert append-only store (requests + lifecycle history). No scale/send/trigger method. |
| `app/api/scale_requests.py` | **CTR-019 POST /api/admin/ads/scale-requests**: `handle_scale_request_create` (propose, inert) + `handle_scale_decision` (record owner decision). `ScaleRequestDeps` holds ONLY the inert gate + server-side `ScaleContext` + audit — no Transport/budget API. **Conditions come from `deps.context` (server-side), never the untrusted body** (RULE-H03). Owner-decision requires all of actor/reason/audit/evidence (RULE-015). |

**Patched (carried-forward) + staged migrations**
| File | Change |
|---|---|
| `app/config.py` | `SCALE_EXECUTION_ENABLED=False` — a single explicit choke asserting Module 6 ships no scale-execution path (RULE-010). Not an enabling flag; never read to act. |
| `migrations/0009_create_ads_scale_request.sql` | Staged DDL (up+down): CTR-013 inert request (8 condition statuses + overall + approval_state + budget_cap + rollback + evidence refs); CHECK enums; comment: no trigger/executable path. |
| `migrations/0010_create_ads_scale_approval.sql` | Staged DDL (up+down): CTR-026 owner-decision records (actor/reason/audit/evidence/decision); FK; comment: an APPROVE never triggers a scale. |

## 3. Tests → smoke/leg mapping (TESTER executes L3–L5)

| Test | Proves | Smoke / leg |
|---|---|---|
| `test_scale_gate_risk_veto.py` | any active Risk-row lock → Risk + overall FAIL; can't be approved (RULE-017) | **SMK-009** / L1 |
| `test_scale_request_needs_owner_approval.py` | no owner decision → stays PROPOSED, not authorized; no self-approve | **SMK-012** / L2 |
| `test_no_executable_scale_path.py` | scale layer/deps/request expose NO raise-budget/enable/open/send/publish method; `SCALE_EXECUTION_ENABLED is False` | L1 / RULE-010 / FAIL-006 |
| `test_scale_request_lifecycle.py` | request carries evidence + budget_cap + rollback; APPROVED only via explicit OwnerDecision; REJECT recorded; +no-raw-PII-in-audit regression | L2 / CTR-013/026 |
| `test_scale_conditions_failclosed.py` | 8 conditions; Funnel/Dashboard fail-closed HOLD; Quality mirrors DQ; never a clean PASS | L1 / CTR-013 |
| `test_risk_recheck_at_approval.py` | Risk re-checked at approval; +empty/partial fresh-read fail-closed regression | L2 / RULE-017 |

Smoke EXECUTION (legs L3–L5) is the TESTER's (M6-P1603/1604) — no self-run (RULE-015).

## 4. Plan-delta

- **`is_scale_authorized` requires overall == PASS** (not merely not-FAIL). In the staged posture the gate is
  fail-closed HOLD, so an owner APPROVE is *recordable* (demonstrating the CTR-026 transition) but a scale is never
  *authorized* — the honest fail-closed truth while M6-OD-002/005 are OPEN. Everything else matches PLAN §5.

## 5. Adversarial self-review (ultracode) — 2 CONFIRMED, both FIXED

A read-only adversarial review (3 dimensions, each finding re-verified by running the code; 5 agents):
**no-executable-scale-path CLEAN, risk-veto-and-approval CLEAN** (the module-critical safety invariants hold);
**2 CONFIRMED** fail-closed/PII defects in new code — both fixed and locked:

| # | Dim | Finding (confirmed) | Fix |
|---|---|---|---|
| 1 | fail-closed (MEDIUM, RULE-017) | `_assert_risk_clear_at_approval` branched on `is not None`; the API forwards `deps.context.risk_flags` which can be `{}`/partial (risk never fully observed) → read as "clear" and an APPROVE recorded (no scale executes — `is_scale_authorized` still needs PASS — but the fail-closed re-check was defeated). | A fresh risk read now clears ONLY when COMPLETE (all 6 `RISK_LOCKS` observed, none active); empty/partial → fall back to the proposal's Risk (PASS required). Regressions: `test_empty_or_partial_fresh_risk_read_is_failclosed`, `test_api_approval_with_unobserved_risk_is_refused`. |
| 2 | PII (LOW, hard-rule-4) | `_audit_decision` embedded untrusted `reason`/`audit_ref` verbatim in the audit `detail`, which the sink does not PII-mask → raw PII could land in the log. | Audit `detail` is now machine-safe only (`request={id};decision={enum}`); the free-text lives in the durable OwnerDecision record; actor stays masked. Regression: `test_no_raw_pii_from_owner_decision_reaches_audit`. |

Not a gate sign-off — the runner gate + JUDGE (M6-P1609) decide.

## 6. Rollback

Staged only — baseline rollback = delete the M6.2G tree (M6.2F untouched). Per-item: new files → delete; patched
`config.py` → revert to M6.2F; migrations 0009/0010 → down-DDL DROP (staged; not applied). Lifecycle records are
inert + append-only (in-memory); a reject/rollback is a new recorded decision, never an executed budget change.

## 7. Scope & governance (unchanged)

In scope built: the 8 doc §16 scale conditions (Risk hard veto), the ads_scale_request lifecycle (CTR-013/026),
CTR-019 POST /scale-requests + owner-decision handler, Risk row full (recall/sale-lock/quality-hold/complaint-P0/
platform-spam-flag + CRM suppression). OUT (not built): threshold values (M6-OD-002), any budget/campaign mutation,
scale model choice (M6-OD-005), learning, real send. HARD FORWARD GATES before any REAL scale/send (per M6-P1600):
the 4 attestation true-ups, real-VNPAY e2e (ENTRY-001), wire `requireExternalSendAllowed` + M6-OD-003/004, M5
DEBT-1..4 + P4 re-gate, M6-OD-005 (`SCALE_MODEL_RATIFIED=False`), M6-OD-002 thresholds. `M6-P1000` + `M6-P1309`
verdicts stay BLOCKED (not converted). Module boundary intact (no pricing/order-state/commission/CRM). No raw
secrets/PII (audit machine-safe, actor masked). FAIL-006 not tripped (the slice never acts).
