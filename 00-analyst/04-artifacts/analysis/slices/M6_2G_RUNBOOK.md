# M6.2G — Slice Runbook — Scale Gate as an owner-decision workflow

| Field | Value |
|---|---|
| Slice | **M6.2G — Scale Request** (the **mandatory Scale-Gate re-gate**; the **final ADS Phase-1 slice**) |
| Written by | **M6-P1608** — `M6_2G_DOCS` (ANALYST_ARCHITECT, `analysis_only`) |
| Depends on | M6.2F (dashboard + Data Quality Gate) |
| Doc source | doc §16 Scale Gate (extract lines 312–324) + §15 L307 (CRM suppression) + §19/§22 (admin endpoint, access control) |
| Done gate (slice spec) | **No auto scale · owner approval required** |
| Objective | Turn the doc §16 Scale Gate into an owner-decision workflow: **compute conditions, assemble evidence, propose — never act.** The slice proves capability with evidence; it flips no flag and authorizes no scale. |

> **Read this first — what "clean re-gate" does and does not mean.** M6.2G is the re-gate that every prior slice
> deferred to, and the band is clean: all seven band prompts self-report PASS, the in-scope fail gate
> **M6-FAIL-006 (auto scale) held** (five independent executed reasons), and the coder self-found and fixed two
> fail-closed/PII holes before evidence. But "clean" here means **the scale gate authorizes nothing** — it is a
> *never-act* workflow. Exit legs 1 and 2 are **SUPPORTED at the staged level** (the tester marks them "met" and
> FAIL-006 is not tripped), not independently closed: `is_scale_authorized` is structurally unreachable in the
> staged posture, and armed-not-fired residuals (F-SCALE-1..4, ACCESS-1) remain for the CODER / the M6-OD-011
> binding. The entry gate **M6-P1600 gave a design-altitude PASS that reversed its prior BLOCKED** because the
> four entry rows were cured *in substance* — **not** a break-glass override — while recording **four attestation
> true-ups** and a long list of **hard forward gates**; **`M6-P1000` and `M6-P1309` verdicts remain BLOCKED (not
> converted).** Posture is immutable: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
> `SCALE_EXECUTION_ENABLED=False`, `SCALE_MODEL_RATIFIED=False`, `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False`,
> `HASH_POLICY_RATIFIED=False`, `live_migrations=false`. This runbook advances no gate and self-certifies nothing;
> the runner EVIDENCE_GATE and the slice-gate Judge (M6-P1609) decide closure.

---

## 1. What this slice built (staged under `04-artifacts/impl/M6.2G/`)

Everything is **staged** (convention-reference tree, never a live repo). The whole M6.2F tree is carried forward
byte-identical; M6.2G **adds** the Scale-Gate layer and one config choke flag. **Nothing acts** — no code raises a
budget, enables a campaign, opens audience scale, sends, publishes, applies a migration, or flips a flag.

### 1.1 The Scale-Gate layer (new `app/measurement/scale/`)

| File | What it is | Contract / Rule |
|---|---|---|
| `scale/conditions.py` | The **8 doc §16 conditions** (verbatim, extract 317–324): `evaluate_conditions(ctx)` → 8 `ConditionResult`s + a **worst-status** overall (FAIL > HOLD > PASS, reusing the M6.2F `worst_status`). **Risk row = hard veto** (RULE-017). **Funnel** (thresholds = M6-OD-002 OPEN) and **Dashboard-as-scale-evidence** (M6-OD-005 / `SCALE_MODEL_RATIFIED=False`) are **fail-closed HOLD**; a missing boundary signal → HOLD. Consequence: **the gate can never compute a clean scale-ready PASS in the staged posture** — the honest fail-closed truth. | CTR-013; RULE-017 |
| `scale/models.py` | `AdsScaleRequest` (CTR-013, **inert data**), `ApprovalState` enum (`COMPUTED/PROPOSED/APPROVED/REJECTED`), `OwnerDecision{actor,reason,audit_ref,evidence_ref,decision,at}`. `budget_cap` / `rollback_condition` are **request fields, not actions**. `is_scale_authorized` requires an owner APPROVE **and** `overall==PASS` **and** cap **and** rollback → **always False in staged posture**. Frozen; `actor` masked on export. | CTR-013/026 |
| `scale/scale_gate.py` | `ScaleGate` (CTR-026 flow): `propose(ctx)` = compute + assemble evidence refs + build an inert PROPOSED request; `record_owner_decision(req, decision)` = record an explicit APPROVE/REJECT, **re-checking the Risk row at approval** (RULE-017, fail-closed), requiring `budget_cap` + `rollback` + a non-FAIL request — else REFUSED. **Deliberately no method that raises budget / enables a campaign / opens audience scale / sends / publishes** (RULE-010). **Never self-approves** (RULE-015). | CTR-026; RULE-010/015/017 |
| `scale/scale_request_store.py` | Inert append-only store (requests + lifecycle history). A transition is a new record, never an executed action. No scale/send/trigger method. | CTR-013/026 |
| `app/api/scale_requests.py` | **CTR-019 `POST /api/admin/ads/scale-requests`**: `handle_scale_request_create` (compute + propose, inert) + `handle_scale_decision` (record an owner approve/reject). **Conditions come from `deps.context` (server-side), never the untrusted body** (RULE-H03). The decision handler requires **all** of `actor`/`reason`/`audit_ref`/`evidence_ref` and rejects a bad decision kind. `ScaleRequestDeps` holds only the inert gate + server context + audit — **no Transport, no budget/campaign/audience handle**. | CTR-019; RULE-010/012/H03 |

### 1.2 The 8 doc §16 Scale-Gate conditions (staged evaluation)

| # | Condition (doc §16) | Staged evaluation |
|---|---|---|
| 1 | **P3/P5/P6 evidence** | PASS iff the required entry-evidence refs (ENTRY-001/002/003/004) are present; else HOLD (RULE-020). |
| 2 | **Quote/Order** | Consumed boundary signal (M3/M8-owned); PASS if attested, else HOLD (M6 never validates it, RULE-021). |
| 3 | **Public/Privacy** | Consumed boundary signal (M4/M5); PASS if attested, else HOLD. |
| 4 | **Funnel** (AOV≥2 boxes, CPA in range, verified-rate ≥ owner threshold) | **fail-closed HOLD** — CPA/verified-rate thresholds are M6-OD-002 (OPEN); no numeric threshold is invented. |
| 5 | **Dashboard** (ROAS by ORDER_VERIFIED, attribution complete) | ROAS-is-verified-only is structural (M6.2F, RULE-003), but **as scale evidence** it is **fail-closed HOLD** until M6-OD-005 (`SCALE_MODEL_RATIFIED=False`). |
| 6 | **Quality** (Data Quality Gate PASS, low dup, consent pass, outbox stable) | PASS iff the **M6.2F Data Quality Gate overall is PASS**; HOLD/FAIL otherwise. **(This closes M6.2F F-DASH-4 — see §5.)** |
| 7 | **Risk** (no recall / sale lock / quality hold / complaint P0 / platform spam flag) | **HARD VETO (RULE-017)**: any active lock — including **CRM suppression** (§15 L307) — ⇒ **FAIL/HOLD** for the whole gate; re-checked at approval time. |
| 8 | **Approval** (owner approves, budget cap, rollback condition) | PASS only when an explicit owner-approval record exists **and** `budget_cap` + `rollback_condition` are set (SMK-012). |

### 1.3 Staged migrations & config

- `migrations/0009_create_ads_scale_request.sql` — CTR-013 inert request DDL (up+down): 8 condition statuses + `overall_status` + `approval_state` + `budget_cap` + `rollback_condition` + evidence refs; CHECK enums; comment: **no trigger / no executable scale path**. Staged, **never applied**.
- `migrations/0010_create_ads_scale_approval.sql` — CTR-026 owner-decision records DDL (up+down): `{actor, reason, audit_ref, evidence_ref, decision, at}`; FK to the request; append-only; comment: **an APPROVE never triggers a scale**. Staged, **never applied**.
- `app/config.py` — adds `SCALE_EXECUTION_ENABLED = False`: a single explicit choke asserting Module 6 ships **no** scale-execution path (RULE-010). **Not an enabling flag; never read to act.**

### 1.4 Two coder self-fixes (M6-P1602 adversarial self-review — both fixed + locked with regressions)

| # | Class | Defect (confirmed) | Fix |
|---|---|---|---|
| 1 | fail-closed (MEDIUM, RULE-017) | `_assert_risk_clear_at_approval` branched on `is not None`; the API forwards `deps.context.risk_flags` which can be `{}`/partial (risk never fully observed) → read as "clear" and an APPROVE recorded (no scale executes — `is_scale_authorized` still needs PASS — but the fail-closed re-check was defeated). | A fresh risk read clears **only when COMPLETE** (all 6 `RISK_LOCKS` observed, none active); empty/partial → fall back to the proposal's Risk (PASS required). Regressions: `test_empty_or_partial_fresh_risk_read_is_failclosed`, `test_api_approval_with_unobserved_risk_is_refused`. |
| 2 | PII (LOW, hard-rule-4) | `_audit_decision` embedded untrusted `reason`/`audit_ref` verbatim in the audit `detail`, which the sink does not PII-mask → raw PII could land in the log. | Audit `detail` is now machine-safe only (`request={id};decision={enum}`); free text lives in the durable `OwnerDecision` record; `actor` stays masked. Regression: `test_no_raw_pii_from_owner_decision_reaches_audit`. |

---

## 2. Operate

M6.2G is a **propose-only, never-act** workflow. There is no operational "run a scale" step — by design. What an
operator/owner can do at the staged level (and what stays impossible):

1. **Compute + propose** — `POST /api/admin/ads/scale-requests` (create): the server assembles a `ScaleContext`
   from its own state (never the request body), evaluates the 8 conditions, and records an **inert PROPOSED**
   `ads_scale_request` carrying evidence refs + `budget_cap` + `rollback_condition`. In the staged posture the
   overall is **HOLD at best** (Funnel + Dashboard-as-scale-evidence are fail-closed) — it **cannot** be a clean
   scale-ready PASS.
2. **Record an owner decision** — `POST /api/admin/ads/scale-requests` (decision): records an explicit owner
   APPROVE/REJECT (`OwnerDecision`), re-checking the Risk row. **A recorded APPROVE authorizes nothing** — with
   overall HOLD, `is_scale_authorized` stays False. The owner performs any actual scale **outside** Module 6,
   gated by `production_flag=OFF`.
3. **What is structurally impossible here** — raising a budget, enabling a campaign, opening audience scale,
   self-approving, or having a request body fake a condition. There is no such method, endpoint, connector, or
   deserializer anywhere in the slice (see §3 boundary result).

> **Owner-facing caveat (do not skip).** An APPROVE recorded through this endpoint is the owner's **authorization
> for a scale performed outside Module 6**. Before that authorization can mean anything real, the **hard forward
> gates in §5** must close — most importantly **ACCESS-1** (the endpoint must authenticate that the caller *is* the
> owner; today `actor` is taken from the request body) and **M6-OD-002 / M6-OD-005** (thresholds / scale model).

---

## 3. Verify

**Verify env:** `02-tester/.venv` — python **3.12.13**, pytest **8.4.2**, pluggy 1.6.0 (matches the
`IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin). Run from `04-artifacts/impl/M6.2G/` (STAGED_ONLY), cache-free.

### 3.1 Bound smoke (the exact slice set)

| Smoke ID | Doc ID | Scenario → Expected (verbatim, SMOKE_REGISTER) | Test file | Result |
|---|---|---|---|---|
| **M6-SMK-009** | ADS-P0-009 | `Recall/Sale Lock active` → `Scale Gate FAIL/HOLD` | `tests/smoke/test_smk_009_recall_sale_lock_scale_fail.py` | **PASS 10/10** |
| **M6-SMK-012** | ADS-P0-012 | `Scale request không owner approval` → `Không scale` | `tests/smoke/test_smk_012_scale_no_owner_approval.py` | **PASS 4/4** |

Bound-smoke total: **14 passed, 0 failed — exit 0**. SMK-009 covers every one of the 6 Risk-row locks
(recall/sale_lock/quality_hold/complaint_p0/platform_spam_flag/crm_suppression) → Risk FAIL / overall FAIL, plus
the late-lock fresh-read veto and the unobserved-risk-is-HOLD-not-PASS negative. SMK-012 covers no-owner-decision →
not authorized, no self-approve entry point, recorded-APPROVE-still-HOLD, and owner-REJECT-recorded-no-scale.

```bash
# from 04-artifacts/impl/M6.2G/  (venv: 02-tester/.venv, python 3.12.13)
python -m pytest -v tests/smoke/test_smk_009_recall_sale_lock_scale_fail.py tests/smoke/test_smk_012_scale_no_owner_approval.py -p no:cacheprovider
# -> 14 passed ; exit 0
```

### 3.2 Full staged suite

**313 passed, 0 failed, 0 skipped, 0 error — RC 0.**
Breakdown: **273 carried-forward** (M6.2A–F) **+ 40 new M6.2G nodes** (26 scale-leg tests + 14 bound smoke).

> **Test-count reconciliation (be precise).** The **tester-run final is 313** (M6-P1604 / SMOKE_RESULTS.md). The
> coder note (M6-P1602) records **299** = 273 carried + the **26 scale-leg tests it authored**; the **14 bound
> smoke** nodes (SMK-009/012) were authored by the **TESTER** in M6-P1603 and run in M6-P1604, so the
> tester-run final adds them (299 + 14 = 313). Per test-count discipline this runbook cites the **tester-run final
> 313**, not the coder intermediate 299 — both are internally consistent, they count different authoring stages.

The 26 scale-leg tests (supporting coverage, all green inside the 313): `test_scale_gate_risk_veto.py` (7),
`test_scale_request_needs_owner_approval.py` (2), `test_no_executable_scale_path.py` (4),
`test_scale_request_lifecycle.py` (5), `test_scale_conditions_failclosed.py` (4), `test_risk_recheck_at_approval.py` (4).

### 3.3 FAIL-006 (auto scale) — NOT tripped (boundary + security, five independent executed reasons)

The boundary adversary (M6-P1605) executed **30 outcomes** (DEFENDED 24, OPEN_NONGATE 4, NOTE 2, **FAIL-006
breaches 0**); the security review (M6-P1606) concurred from the code side and reported a **clean** PII/secret scan
over **155 files**. FAIL-006 holds for five independent, executed reasons:

1. **No executable path exists.** No raise-budget / enable-campaign / open-audience / scale / execute / send /
   publish / auto-approve attribute anywhere; a token sweep of all five scale modules finds **0** action defs and
   **0** posture-flag writes.
2. **`is_scale_authorized` is structurally unreachable.** Funnel (OD-002) and Dashboard (OD-005) are hard-wired
   HOLD in both branches; an **exhaustive 1296-cell** `ScaleContext` cross-product yields **overall==PASS in 0
   cases**.
3. **Config flips don't help.** Flipping both `DASHBOARD_ALERT_THRESHOLDS_DEFINED` and `SCALE_MODEL_RATIFIED`
   True in-process still yields overall HOLD (triple fail-closed).
4. **No consumer arms it.** The scale surface reads no posture flag to branch into an action, and there is no
   `is_scale_authorized` consumer — even a `True` would execute nothing.
5. **Nothing is wire-forgeable.** No deserializer on the scale surface, so every forge/laundering vector requires
   in-process code execution (not a channel breach); a recorded owner APPROVE stays not-authorized; the untrusted
   body can never fake a condition (conditions are server-side).

---

## 4. Rollback (every change this slice made) — *acceptance check 1*

Everything is **staged** ⇒ rollback is non-destructive. Nothing is live, nothing acts, no migration was applied.

| Change | Rollback |
|---|---|
| **Baseline (all M6.2G)** | Delete the `04-artifacts/impl/M6.2G/` tree. M6.2F is untouched (carried forward byte-identical). |
| `app/measurement/scale/__init__.py`, `conditions.py`, `models.py`, `scale_gate.py`, `scale_request_store.py` (new) | Delete the files. |
| `app/api/scale_requests.py` (new) | Delete the file. |
| `app/config.py` (patched: `+SCALE_EXECUTION_ENABLED=False`) | Revert to the M6.2F version. |
| `migrations/0009_create_ads_scale_request.sql` (new, staged, never applied) | `down`-DDL `DROP TABLE ads_scale_request`; delete the file. |
| `migrations/0010_create_ads_scale_approval.sql` (new, staged, never applied) | `down`-DDL `DROP TABLE ads_scale_approval`; delete the file. |
| New tests (6 scale-leg files + 2 bound smoke files) | Delete the files. |
| Lifecycle records (in-memory, inert, append-only) | A reject/rollback is a **new recorded decision**, never an executed budget change; discard the in-memory store. |

There is **no** production/state/flag change to reverse: `analysis_only` here, and every upstream band prompt ran
read-only or staged-only. Rollback of the whole slice = delete the tree.

---

## 5. Decision deltas & governance

### 5.1 Entry gate — a design-altitude PASS with four attestation true-ups (B2)

The entry gate **M6-P1600 = SIGNED (PASS)** reversed its own prior BLOCKED because all four entry rows were cured
**in substance via the honest path** (owner filed/upgraded evidence, independently re-judged) — **not** a
break-glass override, and **not** a conversion of the underlying BLOCKED verdicts. `M6-P1000` (M6.2A entry) and
`M6-P1309` (M6.2D staged) **remain BLOCKED**. The PASS is at **design altitude** for a **never-act** slice:
production stays BLOCKED and no in-scope path can effect a real scale/send.

The same entry judge recorded **four dossier-vs-artifact over-claims** as **hard true-ups before any real
scale/send** (none touches the proven technical boundaries):

- **(a)** ENTRY-001's M3-owner-confirmation field contradicts a carried note + there is **no** standalone
  M3-owner-signature artifact (the runtime XML is present).
- **(b)** ENTRY-003 cites `M6-ENTRY-003_INTERNAL_APPROVED_2026-08-27.md`, which **does not exist** in the pack
  (the 11-code set was independently adversary-verified; external_send BLOCKED regardless).
- **(c)** ENTRY-004 claims the M4-owner **CONFIRMED** while its cited artifact lists that sign under
  `remaining_to_close`.
- **(d)** the M5 `_OWNER_RISK_ACCEPTANCE.md` still has a **draft title + placeholder sha** (RATIFIED status line +
  `[x]` override for validity).

### 5.2 Positive closure — the re-gate doing its job (B5)

The M6.2F residual **F-DASH-4** (scale-eligibility ignored the 8-item DQ overall) is **CLOSED here**: the scale
gate's Quality condition requires `dq_overall==PASS`, so a DQ HOLD/FAIL row makes overall HOLD/FAIL → never
scale-authorized. The mandatory re-gate incorporates the DQ overall that the M6.2F attribution-level
`is_scale_evidence_eligible` did not.

### 5.3 Scale-layer residuals (armed-not-fired; none trips FAIL-006) — routed to CODER / M6-OD-011

| ID | Sev | What | Route / fix |
|---|---|---|---|
| **ACCESS-1** | **load-bearing forward** | The decision handler takes **`actor` from the request body**; there is no authentication that the caller *is* that owner. Inert today (APPROVE authorizes nothing), but at the M6-OD-011 HTTP binding this is the **most important authz control in the slice** — an APPROVE is the owner's authorization for a scale **outside** M6. | Owner / M6-OD-011: authenticate the caller, authorize APPROVE to the owner role only, bind `OwnerDecision.actor` to the **authenticated identity** — never a body-supplied string. |
| **F-SCALE-2** | in-process only — closest shape to a real FAIL-006 *if an executor is ever wired* | `ScaleRequestStore.update_state` doesn't pin `scale_target`/`budget_cap`/`condition_results`, so an in-process `replace()`+`update_state` can bait-and-switch a genuine APPROVE onto a larger target/budget. Not wire-exposed; inert. | CODER + M6-OD-011: reject any transition mutating target/cap/condition_results; the persistence binding must **re-run `evaluate_conditions` on load** (never trust a stored `overall_status`). |
| **F-SCALE-1** | MINOR | At approval, an empty/partial fresh risk read falls back to the *stale* proposal Risk; no scale authorized regardless. | CODER: require a **complete** fresh risk read to approve (refuse on empty/partial). |
| **F-SCALE-3** | MINOR | `budget_cap` accepts `-1/0/+inf/NaN` as "present". | CODER: `math.isfinite(cap) and cap > 0`. |
| **F-SCALE-4** | MINOR | `rollback_condition=' '` (whitespace) satisfies the cap+rollback pairing. | CODER: content-validate (min length / structured predicate). |
| **F-SCALE-PII-1** | Observation | `OwnerDecision.to_public()` + the 0010 record **echo** owner free-text (`reason`/`audit_ref`/`evidence_ref`) unmasked on export (excluded from the audit per the D5 fix; contract-non-PII; no leak today). | CODER + M6-OD-012: document the field contract / bound / mask on the export surface. |
| **N-1 / N-2** | Note | Frozen-record `object.__setattr__` forge / module-global mutation of `RISK_LOCKS` / `REQUIRED_ENTRY_EVIDENCE` — require **in-process code execution**, authorize no scale. | Defense-in-depth: source the locks/entry set from a frozen/validated registry. |

### 5.4 Hard forward gates before ANY real scale or external send (B7)

None blocks this never-act design slice; **all must close before any real egress / PR-PILOT.**

- The **four attestation true-ups** (§5.1 a–d).
- **ENTRY-001:** real-VNPAY-HMAC prepaid→VERIFIED e2e; prune TRUSTED enum/query drift; re-verify the Golden-Hour
  create-gate; read-side runtime revenue assertion; **re-confirm on dev at merge** (the `FAIL_OPEN_RECALL` fix
  `@a3aad246` is an unmerged personal branch).
- **ENTRY-003 / send:** wire `requireExternalSendAllowed` to a real egress client + **M6-OD-003** (hash policy,
  still BLOCKED at M6.2D) + **M6-OD-004** (connector) + secret_ref-only platform tokens.
- **M5 (ENTRY-004):** close **DEBT-1..4** + run the mandatory **adversarial P4 re-gate** before real posting.
- **M6-OD-005** (attribution scale model) before any row is scale evidence (`SCALE_MODEL_RATIFIED=False`);
  **M6-OD-002** (dashboard/scale thresholds).
- **M6-OD-011 binding:** **ACCESS-1** owner authN + **F-SCALE-2** re-run-conditions-on-load; wire **no** scale
  executor while the posture stands.

### 5.5 Immutable posture (intact across M6.2A–G) (B8)

`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `HASH_POLICY_RATIFIED=False`,
`SCALE_MODEL_RATIFIED=False`, `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False`, `SCALE_EXECUTION_ENABLED=False`,
`live_migrations=false` — all unchanged. `M6-P1000` + `M6-P1309` verdicts remain **BLOCKED (not converted)**.
FAIL-006 not tripped; the Scale Gate proves capability and authorizes nothing.

---

## 6. Changelog delta — *acceptance check 2*

- **No new `SCHEMA_CHANGELOG` row is appended by this slice.** This is an `analysis_only` docs prompt (the
  analyst is denied write to `00-spec/registers/` anyway), and the slice introduces **no canon schema change** to
  the owner document.
- **Contracts CTR-013 / CTR-019 / CTR-026 remain `MISSING / OWNER_DECISION_REQUIRED` in the canon
  `CONTRACT_REGISTER`.** Their approved schemas are **staged** (harmonization producers **M6-P0709 / M6-P0712 =
  PASS**, harmonization gate **M6-P0715 = SIGNED**), so they are **satisfied-for-entry**. Per **SCHEMA_CHANGELOG
  row 18 (CANON-03)**, a still-`MISSING` row means "**not yet applied to canon**", not "no approved schema
  exists"; the canon-flip is **deferred, non-blocking operator housekeeping** at each slice's own entry
  (only CTR-003/004/005/006 were flipped for M6.2A, rows 9–12).
- **Concrete artifacts this slice added** (staged, not canon): the `app/measurement/scale/` package, the
  `app/api/scale_requests.py` endpoint, migrations **0009**/**0010** (staged DDL, **never applied**), and the
  config choke **`SCALE_EXECUTION_ENABLED=False`** (a governance marker in the posture chain, not a schema field).
- **Governance-marker delta:** `SCALE_EXECUTION_ENABLED=False` joins the immutable posture chain
  (BLOCKED/OFF/OFF + `HASH_POLICY_RATIFIED=False` + `SCALE_MODEL_RATIFIED=False` +
  `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False` + `live_migrations=false`). No enabling value written anywhere.

---

## 7. Handoff

- **This is the final ADS Phase-1 measurement slice.** After the M6.2G slice-gate Judge (M6-P1609), the next
  prompt is the **M6.2H entry-gate Judge (M6-P1700)** — Phase 2 territory (learning, per the ledger). M6.2G closes
  the Phase-1 measurement arc: ingest → attribution → outbox/track → admin/workers → dashboard/DQ → **scale gate**.
- **Exit-gate state at this docs step** (from the evidence index §4, carried faithfully):
  - Items **3, 4, 7 = MET** (SMK-009 10/10, SMK-012 4/4, rollback documented per item).
  - Items **1, 2 = SUPPORTED (staged)** — the tester marks legs L1/L2 "met" and FAIL-006 is not tripped, but the
    F-SCALE-1..4 / ACCESS-1 residuals remain (armed-not-fired), so **final closure is the slice-gate Judge's call**.
  - Item **5** (all slice prompts have evidence JSON) closes when **M6-P1608** (this docs prompt) and **M6-P1609**
    (Judge) produce their evidence — after this prompt, only **M6-P1609.json** is outstanding.
  - Item **6** (slice-gate Judge PASS sign-off) closes only at **M6-P1609**.
- **Operator TODO before any durable binding / Phase-2 real work:** the four attestation true-ups (§5.1); wire
  `M6-OD-011` with **ACCESS-1** owner authN + **F-SCALE-2** re-run-on-load and **no** executor.
- **Owner TODO:** **M6-OD-002** (thresholds), **M6-OD-005** (scale model), **M6-OD-003** (hash, still BLOCKED at
  M6.2D), **M6-OD-004** (connector), **M6-OD-012** (owner free-text masking, F-SCALE-PII-1).
- **CODER TODO:** F-SCALE-1 (complete fresh risk read), F-SCALE-2 (pin target/cap on `update_state`), F-SCALE-3
  (`isfinite`/`>0`), F-SCALE-4 (content-validate rollback), F-SCALE-PII-1 (document/mask owner free-text on export).

---

## 8. Pointers for the slice-gate Judge (M6-P1609)

The Judge renders the slice verdict **strictly from the evidence files** (this runbook is descriptive, not a
verdict). Suggested reading order:

1. `00-spec/slices/M6.2G.md` "Exit gate checks" — the 7 items.
2. For legs 1–4 + 7, read the primary evidence directly (do **not** rely on this runbook or the index):
   `04-artifacts/test-reports/M6.2G/SMOKE_RESULTS.md`, `04-artifacts/boundary-reports/M6.2G_boundary.md`,
   `04-artifacts/security-reports/M6.2G_security.md`, `04-artifacts/impl/M6.2G/PLAN.md` +
   `IMPLEMENTATION_NOTES.md` §6 + migrations `0009`/`0010` down-DDL.
3. **Weigh the design-altitude entry PASS (§5.1):** confirm it cured the four entry rows *in substance* while
   recording the four attestation true-ups and keeping `M6-P1000` / `M6-P1309` **BLOCKED (not converted)**; confirm
   the exit legs prove *no auto scale* + *owner approval required* and that **FAIL-006 is not tripped**.
4. **Confirm the residuals are armed-not-fired and correctly routed** (§5.3): none trips FAIL-006; ACCESS-1 +
   F-SCALE-2 are the load-bearing forward items at the M6-OD-011 binding.
5. **Confirm items 5 & 6** by re-reading the ledger and `04-artifacts/evidence/judge/` (the M6-P1609 sign-off is
   the Judge's own output).
6. Treat the **B7 hard forward gates (§5.4)** as the standing conditions before *any* real scale or external send —
   none of which this design slice satisfies or claims to.

*This runbook advances no gate and self-certifies nothing. The runner EVIDENCE_GATE and the slice-gate Judge
(M6-P1609) decide closure. `global_gateway_state=BLOCKED`, `production_flag=OFF`; the Scale Gate authorizes no scale.*
