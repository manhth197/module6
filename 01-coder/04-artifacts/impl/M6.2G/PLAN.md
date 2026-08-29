# M6.2G IMPLEMENTATION PLAN — Scale Gate as an owner-decision workflow (STAGED, plan-only)

**Prompt**: M6-P1601 (`M6_2G_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code this prompt)
**Slice**: M6.2G — turn the doc §16 Scale Gate into an owner-decision workflow: **compute conditions, assemble
evidence, propose; NEVER act** (RULE-010). Depends on M6.2F.
**Done gate**: *No auto scale; owner approval required.* There must be **no code path that raises budget, enables
campaigns, or opens audience scale** (exit-leg 1, FAIL-006), and `ads_scale_request` transitions only via an
explicit owner approval (exit-leg 2).
**Posture (immutable)**: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
`HASH_POLICY_RATIFIED=False`, `SCALE_MODEL_RATIFIED=False`, `live_migrations=false`. This plan writes no code,
applies no migration, calls nothing external, resolves no owner decision, flips no flag, scales nothing.

> **Governance — the MANDATORY Scale-Gate re-gate cleared at DESIGN ALTITUDE.** M6.2G is the re-gate every prior
> slice pointed to. Its entry judge **M6-P1600 = SIGNED (PASS)** re-judged all four entry rows on real source:
> **ENTRY-001** PROVEN (verified-revenue boundary), **ENTRY-002** clean, **ENTRY-003** PROVEN (fail-closed event
> governance), **ENTRY-004** filed (M4 PROVEN; M5 owner-ratified risk-accepted, ceiling-bounded); `M6-DEFER-FBC-
> M6.2D.json` filed (consent fail-opens F-A..F-F CLOSED). PASS is at **design altitude** for a **never-act** slice:
> production stays BLOCKED and no in-scope path can effect a real scale/send. **HARD FORWARD GATES (recorded by
> M6-P1600; none blocks this design slice, all bind before ANY real scale/send)**: 4 attestation true-ups
> (ENTRY-001 M3-owner-signature; the missing ENTRY-003 internal-approved file; the M4-owner sign; the M5
> risk-acceptance title+sha), real-VNPAY e2e + TRUSTED-drift prune (ENTRY-001), wire `requireExternalSendAllowed`
> + M6-OD-003/004 (ENTRY-003/send), M5 DEBT-1..4 + adversarial P4 re-gate, **M6-OD-005** before any row is scale
> evidence (`SCALE_MODEL_RATIFIED=False`), **M6-OD-002** thresholds. `M6-P1000` + `M6-P1309` verdicts stay BLOCKED
> (not converted). This plan builds the never-act workflow ONLY.

---

## 1. Entry-gate verification

| Precondition | Source | Result |
|---|---|---|
| This prompt RUNNING | ledger (order 137) | **M6-P1601 = RUNNING** ✓ |
| Dependency resolved | ledger | **M6-P1600 = SIGNED** (entry judge PASS, opens M6.2G STAGED/never-act) ✓; M6.2F slice gate **M6-P1509 = SIGNED** ✓ |
| Target LOCKED + M6-OD-011 | manifest | `status=LOCKED`, `STAGED_ONLY`, safety all false; M6-OD-011 **DECIDED** ✓ |
| Slice contracts | M6-P1600 + CONTRACT_REGISTER | **CTR-013** (ads_scale_request), **CTR-019** (POST /scale-requests), **CTR-026** (Scale-Gate approval flow) = MISSING but harmonized-for-entry (producers M6-P0709 / M6-P0712 PASS); conditions locked doc §16 (extract 315–324); flow = a proposal + owner-approve, budget cap is a **request field**, not a mutation ✓ |
| Entry evidence (all four rows) | M6-P1600 | ENTRY-001/002/003/004 SATISFIED at design altitude (with forward true-ups) ✓ |
| OPEN owner decisions | DECISION_REGISTER | **M6-OD-002** (thresholds) OUT; **M6-OD-005** (scale model) → no row is scale evidence (`SCALE_MODEL_RATIFIED=False`, fail-closed) ✓ |
| Flags | manifest/brief | BLOCKED/OFF/OFF, HASH/SCALE_MODEL_RATIFIED=False, live_migrations=false ✓ |
| M6.2F foundation | `04-artifacts/impl/M6.2F/` (255 tests green) | present; dashboard KPIs + DQ gate (PASS/HOLD/FAIL) feed the Quality/Dashboard scale conditions — carried forward per §2 ✓ |

**Conclusion**: open for **STAGED, never-act** M6.2G. Compute/assemble/propose only; every executable scale path
is structurally absent; real scale gated forward (M6-OD-002/005, the forward true-ups, production_flag=OFF).

---

## 2. Working mode, conventions & staging model

Reuse the M6.2A–F baseline (pytest, frozen dataclasses, read-only ports + in-memory staged adapters, framework-
neutral pure handlers, staged migrations up+down, mask-on-export, fail-closed everywhere). **Cumulative snapshot**:
the whole **M6.2F** tree (final slice state) is carried forward byte-identical; M6.2G **adds** the Scale-Gate layer
and (if anything) a tiny config note. The change set (§5) is the diff. **Nothing acts**: no budget/campaign/
audience mutation, no send, no scale, no flag. `production_flag=OFF` immutable.

---

## 3. Scope lock (anchored strictly to `00-spec/slices/M6.2G.md`)

**In scope (4 capabilities):**
1. **Scale-condition evaluation across the 8 doc §16 condition rows** (§4.1) — each PASS/HOLD/FAIL; the **Risk row
   is a HARD VETO** (RULE-017); fail-closed where an OPEN owner decision gates it.
2. **`ads_scale_request` lifecycle** (CTR-013 / CTR-026) — `computed → proposed → owner approve/reject`; inert
   data carrying evidence refs + budget_cap + rollback_condition.
3. **POST /api/admin/ads/scale-requests** (CTR-019) — create a proposal (compute + assemble + propose); + an
   owner-decision handler that records approve/reject. Both inert (write proposal/decision records only).
4. **Risk row FAIL/HOLD in full** (doc §16 L323 + §15 L307): recall / sale lock / quality hold / complaint P0 /
   platform spam flag **+ CRM suppression** — any active ⇒ gate FAIL/HOLD, re-checked at approval time.

**Out of scope (explicit):**
- **Threshold values** (M6-OD-002 OPEN) — the Funnel (CPA/verified-rate) condition is evaluated **fail-closed
  HOLD** while thresholds are unratified; NO numeric threshold is invented.
- **Any budget / campaign / audience mutation** (RULE-010, FAIL-006) — there is **no** executable scale path,
  method, endpoint, or connector anywhere in this slice. `budget_cap` / `rollback_condition` are request **fields**,
  never actions. "Approved" is a **recorded owner decision**, not a trigger.
- **Scale MODEL choice** (M6-OD-005) — no row is scale evidence (`SCALE_MODEL_RATIFIED=False`); the Dashboard/
  attribution scale condition is fail-closed HOLD until the owner ratifies a model.
- **Learning** (M6.2H+), **real send / connectors** (M6-OD-003/004; external_send=OFF), **owner self-approval**
  (RULE-015 — the system never approves its own request).

---

## 4. Locked contract content (build to the exact spec)

### 4.1 The 8 doc §16 Scale-Gate conditions (VERBATIM, extract lines 317–324)

| # | Điều kiện scale | Yêu cầu tối thiểu | Staged evaluation |
|---|---|---|---|
| 1 | **P3/P5/P6 evidence** | Verified Revenue boundary, Payment/COD/Order Verified, Channel identity, event identity có evidence | PASS if the required entry-evidence refs (ENTRY-001/002/003/004) are present; else HOLD |
| 2 | **Quote/Order** | QuoteSnapshot hoạt động đúng, order tạo đúng, không tạo order khi chưa xác nhận | consumed boundary signal (M3/M8-owned); PASS if attested, else HOLD (M6 never validates it, RULE-021) |
| 3 | **Public/Privacy** | AI/Gateway không public giá cuối, không leak PII, không spam | consumed boundary signal (M4/M5); PASS if attested, else HOLD |
| 4 | **Funnel** | AOV tối thiểu 2 hộp/đơn, CPA trong ngưỡng, verified rate đạt ngưỡng owner đặt | **fail-closed HOLD** — CPA/verified-rate thresholds are M6-OD-002 (OPEN); AOV≥2 boxes is structural (from the M6.2F Boxes/Order metric) |
| 5 | **Dashboard** | ROAS đo bằng ORDER_VERIFIED, attribution đủ campaign/adset/ad/live/messenger | ROAS-is-verified-only is structural (M6.2F, RULE-003) → PASS; but as **scale evidence** it is fail-closed HOLD until M6-OD-005 (`SCALE_MODEL_RATIFIED=False`) |
| 6 | **Quality** | Data Quality Gate PASS, duplicate thấp, consent pass, outbox ổn định | PASS iff the M6.2F Data Quality Gate overall is PASS; HOLD/FAIL otherwise |
| 7 | **Risk** | Không recall, không sale lock, không quality hold, không complaint P0, không platform spam flag | **HARD VETO (RULE-017)**: any active lock (incl. CRM suppression, §15 L307) ⇒ **FAIL/HOLD** for the whole gate |
| 8 | **Approval** | Owner duyệt scale request, có budget cap, có rollback condition | PASS only when an explicit owner-approval record exists AND budget_cap + rollback_condition are set (SMK-012) |

**Roll-up**: overall gate = worst of the 8 (FAIL > HOLD > PASS). In the current staged posture the gate can reach
**HOLD at best** (Funnel + Dashboard-as-scale-evidence are fail-closed) — it can **never** compute a clean
scale-ready PASS, which is the honest fail-closed truth while M6-OD-002/005 are OPEN.

### 4.2 Lifecycle (CTR-026, SPEC §13 state machine)

`computed → proposed (budget_cap + rollback_condition + evidence_refs) → owner approve / reject`. A recall / sale-
lock (or any Risk-row item) forces **FAIL/HOLD** and blocks approval (re-checked at approval time, RULE-017). No
state, including "approved", executes anything (RULE-010): M6 records the decision; the owner performs any scale
outside M6, gated by `production_flag=OFF`.

---

## 5. Minimal change set (all target-relative, staged under `04-artifacts/impl/M6.2G/`)

Legend: **Leg** = M6.2G exit-gate leg (L1 = *no auto scale*; L2 = *owner approval required*). Rollback: new files
→ delete; patched carried-forward files → revert to M6.2F.

### 5.1 New — the Scale-Gate layer

| # | Target file (new) | Purpose | Contract/Rule | Leg | Smoke |
|---|---|---|---|---|---|
| S1 | `app/measurement/scale/__init__.py` | package marker | — | — | — |
| S2 | `app/measurement/scale/conditions.py` | `ScaleCondition` enum (the 8 doc §16 rows) + `ConditionResult{condition,status,detail,evidence_ref}` + `evaluate_conditions(context)` → 8 results; **Risk = hard veto** (RULE-017); Funnel + Dashboard-as-scale-evidence **fail-closed HOLD** (M6-OD-002 / SCALE_MODEL_RATIFIED). Reuses the M6.2F DQ `worst_status` roll-up. | CTR-013; **RULE-017** | **L1** | **SMK-009** |
| S3 | `app/measurement/scale/models.py` | `AdsScaleRequest` (CTR-013, **inert data**): `{request_id, scale_target(campaign/adset/ad ref), budget_cap, rollback_condition, evidence_refs[], condition_results[8], overall_status, approval_state}` + `ApprovalState` enum (`COMPUTED/PROPOSED/APPROVED/REJECTED`) + `OwnerDecision{actor,reason,audit_ref,evidence_ref,decision,at}`. Frozen; PII masked; budget_cap/rollback_condition are FIELDS, not actions. | CTR-013/026 | L1/L2 | SMK-012 |
| S4 | `app/measurement/scale/scale_gate.py` | `ScaleGate` (CTR-026 flow): `propose(context)` = compute conditions + assemble evidence_refs + build a PROPOSED request (never a clean-PASS while fail-closed); `record_owner_decision(request, decision)` = APPROVE/REJECT via an explicit `OwnerDecision`, **re-checking the Risk row at approval** (active lock ⇒ refuse/force HOLD, RULE-017); audited. **Deliberately NO method that raises budget / enables a campaign / opens audience scale / publishes** (RULE-010, FAIL-006). The system can NEVER approve its own request (RULE-015). | **CTR-026**; **RULE-010/017/015** | **L1/L2** | **SMK-009/012** |
| S5 | `app/measurement/scale/scale_request_store.py` | Inert in-memory store: append-only scale_requests + owner-decision records; a lifecycle transition is a new record, never an executed action. NO scale/send/trigger method. | CTR-013/026 | L1 | — |
| S6 | `app/api/scale_requests.py` | **CTR-019 POST /api/admin/ads/scale-requests**: `handle_scale_request_create(body, deps)` (compute + propose, inert) + `handle_scale_decision(body, deps)` (record owner approve/reject). Read/create only; `ScaleRequestDeps` holds no Transport, no budget API, no store-mutator beyond the inert request store; untrusted body = DATA (RULE-H03); PII masked. | CTR-019; RULE-010/012 | L1/L2 | SMK-012 |

### 5.2 Staged migrations & config

| # | Target file (new/patched) | Change | Leg | Rollback |
|---|---|---|---|---|
| M1 | `migrations/0009_create_ads_scale_request.sql` (new) | Staged DDL (up+down): `ads_scale_request` (CTR-013) — request + `budget_cap` + `rollback_condition` + the 8 condition statuses + `overall_status` + `approval_state` + evidence refs; CHECK `approval_state ∈ {COMPUTED,PROPOSED,APPROVED,REJECTED}` and statuses ∈ {PASS,HOLD,FAIL}; a comment that this is INERT proposal data with **no trigger / no executable scale** (RULE-010). Never applied. | L1 | down-DDL DROP; delete |
| M2 | `migrations/0010_create_ads_scale_approval.sql` (new) | Staged DDL (up+down): `ads_scale_approval` (CTR-026) — owner-decision records {actor, reason, audit_ref, evidence_ref, decision, at}; FK to the request; append-only; the approval NEVER triggers a scale (comment). Never applied. | L2 | down-DDL DROP; delete |
| A1 | `app/config.py` (**extend**) | Add `SCALE_EXECUTION_ENABLED = False` (M6 never executes a scale — RULE-010; a single explicit choke asserting no executable path) + a comment that budget/campaign/audience mutation is owner-only, out of M6, gated by `production_flag=OFF`. NOT an enabling flag. | L1 | revert to M6.2F |

---

## 6. Test plan → done-gate / smoke mapping (`pytest -q`; TESTER executes L3–L5)

Fixtures extend `conftest.py` with a `ScaleGate`, a scale-request store, staged consumed inputs (risk/suppression
flags, entry-evidence refs, boundary attestations), and a `DashboardView` / DQ result from the M6.2F layer.
Carried-forward M6.2F **255 tests stay green**. PII markers assembled at runtime (no literal PII in source).

| # | Target test (new) | Proves | Leg | Smoke | Fail-gate |
|---|---|---|---|---|---|
| T1 | `tests/test_scale_gate_risk_veto.py` | **SMK-009**: any active Risk-row item (recall / sale lock / quality hold / complaint P0 / platform spam flag / CRM suppression) → the Risk condition and the overall gate are **FAIL/HOLD**, and the request cannot be approved (RULE-017). | **L1** | **SMK-009** | — |
| T2 | `tests/test_scale_request_needs_owner_approval.py` | **SMK-012**: a proposed scale_request with NO owner decision stays `PROPOSED` (never `APPROVED`); the system cannot self-approve (RULE-015); no scale occurs. | **L2** | **SMK-012** | FAIL-006 |
| T3 | `tests/test_no_executable_scale_path.py` | **leg 1 / RULE-010 / FAIL-006**: the scale layer + handlers + deps expose **NO** method/attribute that raises budget, enables a campaign, opens audience scale, sends, or publishes; `AdsScaleRequest` is inert data; `config.SCALE_EXECUTION_ENABLED is False`. | **L1** | — | **FAIL-006** |
| T4 | `tests/test_scale_request_lifecycle.py` | **leg 2 / CTR-013/026**: a request carries `evidence_refs` + `budget_cap` + `rollback_condition`, and transitions `COMPUTED→PROPOSED→APPROVED` ONLY via an explicit `OwnerDecision{actor,reason,audit,evidence}`; REJECT path recorded; audited. | L2 | SMK-012 | — |
| T5 | `tests/test_scale_conditions_failclosed.py` | **CTR-013**: the 8 conditions evaluate; Funnel + Dashboard-as-scale-evidence are **fail-closed HOLD** (M6-OD-002 / SCALE_MODEL_RATIFIED=False) so the overall gate can never be a clean scale-ready PASS in staged posture; Quality mirrors the M6.2F DQ overall; worst-status roll-up. | L1 | (SMK-009) | — |
| T6 | `tests/test_risk_recheck_at_approval.py` | **RULE-017**: a PROPOSED request is **refused approval** if a Risk-row lock is active at approval time (re-checked at approval, not only at propose). | L2 | SMK-009 | — |

**Smoke → test binding**: SMK-009 = T1(+T6); SMK-012 = T2(+T4). Execution + recorded results/evidence (legs
L3–L5) is the **TESTER**'s (M6-P1603/1604). No self-run / self-certify (RULE-015).

---

## 7. Master traceability matrix

| Item | Files | Contract | Rule(s) | Leg | Smoke | Fail-gate | Rollback |
|---|---|---|---|---|---|---|---|
| 8 scale conditions + Risk veto | S2 | CTR-013 | RULE-017 | **L1** | SMK-009 | — | delete |
| ads_scale_request (inert) | S3 | CTR-013/026 | RULE-010 | L1/L2 | SMK-012 | FAIL-006 | delete |
| Scale-Gate flow (propose/decide) | S4 | CTR-026 | RULE-010/017/015 | **L1/L2** | SMK-009/012 | FAIL-006 | delete |
| Scale-request store (inert) | S5 | CTR-013/026 | RULE-010 | L1 | — | — | delete |
| POST /scale-requests + decision | S6 | CTR-019 | RULE-010/012 | L1/L2 | SMK-012 | FAIL-006 | delete |
| Migrations + config | M1,M2,A1 | CTR-013/026 | RULE-010 | L1/L2 | — | — | down-DDL / revert |
| Tests | T1–T6 | — | — | L1/L2 (+L3–L5 runnable) | SMK-009/012 | FAIL-006 | delete |

**Legs**: L1 ✓ (no auto scale — structural absence + T3/T5); L2 ✓ (owner approval required — T2/T4/T6); L3–L5 ✓
*made runnable* (TESTER executes SMK-009/012); L6 (evidence — process), L7 (judge — process), **L8 ✓ (this doc —
rollback per item)**.

---

## 8. Rollback strategy (global)

1. **Nothing live / nothing acts.** Staged under `04-artifacts/impl/M6.2G/`; no migration applied, no external
   call, no scale, no trigger, no flag written. Baseline rollback = delete the M6.2G tree (M6.2F untouched).
2. **Per-item** (§5): new files → delete; patched `config.py` → revert to M6.2F. Migrations 0009/0010 → down-DDL
   DROP (staged; not executed).
3. **Lifecycle records are inert + append-only** (in-memory in the staged slice); a "reject/rollback" is a new
   recorded decision, never an executed budget change.

---

## 9. Plan-deltas & notes

- **No executable scale path is the primary design constraint (RULE-010, FAIL-006, exit-leg 1)** — enforced
  STRUCTURALLY: the scale layer produces only DATA (proposals + recorded owner decisions). There is no Transport,
  no budget/campaign/audience API, no connector. "Approved" is a recorded decision, not a trigger; T3 asserts the
  public surface has no such method and `SCALE_EXECUTION_ENABLED is False`.
- **Risk row is a hard veto re-checked at approval (RULE-017, SMK-009)** — active recall/sale-lock/quality-hold/
  complaint-P0/platform-spam-flag/CRM-suppression ⇒ FAIL/HOLD; approval is refused while any lock is active.
- **Fail-closed in staged posture** — Funnel (M6-OD-002 thresholds) and Dashboard-as-scale-evidence (M6-OD-005 /
  SCALE_MODEL_RATIFIED=False) can only reach HOLD, so the gate can never compute a clean scale-ready PASS today.
  This is the honest truth, not a limitation to paper over.
- **Consumed staged inputs** (risk/suppression flags, entry-evidence refs, Quote/Order + Public/Privacy boundary
  attestations) are read-only — M6 records whether a boundary passed, never validates/owns it (RULE-021/018).
- **Owner self-approval is impossible (RULE-015)** — the ScaleGate has no auto-approve; an approval requires an
  explicit external `OwnerDecision`. **The 4 attestation true-ups + M6-OD-002/005 + the ENTRY forward gates** (per
  M6-P1600) remain hard gates before any REAL scale/send; `M6-P1000`/`M6-P1309` stay BLOCKED. Smoke execution
  (legs L3–L5) is the TESTER's (M6-P1603/1604).

---

## 10. Acceptance self-map

1. *Every item → leg or smoke* → §5–§7. ✓  2. *Rollback per item* → §5/§8. ✓  3. *No scope beyond the slice* →
§3 (thresholds/model/mutation/learning/real-send deferred; never-act). ✓  4. *Target LOCKED + M6-OD-011 decided*
→ §1. ✓  5. *Reuse conventions/test patterns* → §2 (M6.2F baseline). ✓  Plus the **load-bearing invariants**: no
executable scale path (RULE-010, FAIL-006, T3/T5), owner approval required (SMK-012, T2/T4), Risk hard veto
(RULE-017, SMK-009, T1/T6) — each with a test and the M6.2F 255-test suite staying green.

*Plan-only: no code, no migration applied, nothing sent/scaled/triggered/approved/published, no flag flipped;
BLOCKED/OFF/OFF.*
