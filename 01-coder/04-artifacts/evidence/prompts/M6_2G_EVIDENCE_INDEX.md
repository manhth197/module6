# M6.2G — Slice Evidence Index

| Field | Value |
|---|---|
| Slice | **M6.2G** — Scale Request (the **mandatory Scale-Gate re-gate**; final ADS Phase-1 slice) |
| Assembled by | **M6-P1607** — `M6_2G_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, analysis_only) |
| Assembled on | 2026-08-28 (UTC) |
| Purpose | Index every band's evidence file / artifact / test report / boundary+security report, mapped to the slice exit-gate checklist, and list unresolved blockers — for the slice-gate Judge (M6-P1609). |
| Governance (immutable) | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `HASH_POLICY_RATIFIED=False`, `SCALE_MODEL_RATIFIED=False`, `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False`, `SCALE_EXECUTION_ENABLED=False`, `live_migrations=false`. This index flips nothing and self-certifies nothing; **the Scale Gate authorizes no scale.** |

> **Altitude note (read first).** This is an **index of collected evidence**, not a verdict. M6.2G is the
> **mandatory Scale-Gate re-gate** that every prior slice deferred to. The band is clean — all seven band prompts
> self-report PASS, and the in-scope fail gate **M6-FAIL-006 (auto scale) held** (five independent executed reasons;
> the scale gate *computes/assembles/proposes and never acts*). The entry gate **M6-P1600 gave a design-altitude
> PASS reversing its prior BLOCKED** because all four entry-evidence rows (ENTRY-001/002/003/004) were **cured in
> substance via the honest path** (owner filed/upgraded evidence, independently re-judged) — **not** a break-glass
> override. But that same entry judge recorded **four attestation over-claims as hard true-ups** and a long list of
> **hard forward gates** that stand before any *real* scale or external send; `M6-P1000` and `M6-P1309` verdicts
> **remain BLOCKED (not converted)**. Exit-gate items **5 and 6 are NOT yet met** (M6-P1608 docs and the M6-P1609
> slice-gate Judge have not run). The authoritative slice verdict is the Judge's, strictly from the evidence.

---

## 1. Slice prompt band — evidence status

Source: `04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv` (rows 138–147) + each evidence JSON.

| Prompt | Role | Title | Ledger status | Evidence JSON | Self-reported | `fail_gate_tripped` | Primary artifact(s) |
|---|---|---|---|---|---|---|---|
| M6-P1600 | JUDGE | M6_2G_ENTRY_GATE_JUDGE | **SIGNED** | `04-artifacts/evidence/prompts/M6-P1600.json` | PASS (design-altitude) | false | `04-artifacts/evidence/judge/M6-P1600_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS) |
| M6-P1601 | CODER | M6_2G_CODER_PLAN | PASS | `04-artifacts/evidence/prompts/M6-P1601.json` | PASS | false | `04-artifacts/impl/M6.2G/PLAN.md` |
| M6-P1602 | CODER | M6_2G_CODER_IMPLEMENT | PASS | `04-artifacts/evidence/prompts/M6-P1602.json` | PASS | false | `04-artifacts/impl/M6.2G/IMPLEMENTATION_NOTES.md` + staged `app/` tree |
| M6-P1603 | TESTER | M6_2G_TESTER_BUILD | PASS | `04-artifacts/evidence/prompts/M6-P1603.json` | PASS | false | `04-artifacts/impl/M6.2G/tests/TEST_MANIFEST.md` |
| M6-P1604 | TESTER | M6_2G_TESTER_RUN | PASS | `04-artifacts/evidence/prompts/M6-P1604.json` | PASS | false | `04-artifacts/test-reports/M6.2G/SMOKE_RESULTS.md` |
| M6-P1605 | BOUNDARY_ADVERSARY | M6_2G_BOUNDARY_ADVERSARY | PASS | `04-artifacts/evidence/prompts/M6-P1605.json` | PASS | false | `04-artifacts/boundary-reports/M6.2G_boundary.md` |
| M6-P1606 | SECURITY_PII | M6_2G_SECURITY_REVIEW | PASS | `04-artifacts/evidence/prompts/M6-P1606.json` | PASS | false | `04-artifacts/security-reports/M6.2G_security.md` |
| **M6-P1607** | PM_ORCHESTRATOR | M6_2G_EVIDENCE_COLLECT | **RUNNING** | `04-artifacts/evidence/prompts/M6-P1607.json` | (this index) | false | `04-artifacts/evidence/prompts/M6_2G_EVIDENCE_INDEX.md` |
| M6-P1608 | ANALYST_ARCHITECT | M6_2G_DOCS | **TODO** | — (not produced) | — | — | `04-artifacts/analysis/slices/M6_2G_RUNBOOK.md` (pending) |
| M6-P1609 | JUDGE | M6_2G_SLICE_GATE_JUDGE | **TODO** | — (not produced) | — | — | `04-artifacts/evidence/judge/M6-P1609_JUDGE_FINAL_SIGN_OFF.json` (pending) |

All seven band evidence JSONs (M6-P1600 … M6-P1606) exist, are schema-valid, self-report **PASS**, and declare
`fail_gate_tripped=false`; the entry gate M6-P1600 is a genuine Judge `SIGNED` verdict (design-altitude PASS — see §5 B2).
This prompt's own `M6-P1607.json` is produced at completion (written **last**, after this index — pack hard-rule 2).

---

## 2. Artifact inventory (existence verified on disk)

### 2.1 Implementation (staged, `04-artifacts/impl/M6.2G/`)
- `PLAN.md` — minimal staged change set + master traceability + per-item rollback.
- `IMPLEMENTATION_NOTES.md` — realized plan + 2 self-fixed defects (risk-recheck empty-map fail-closed; audit-detail PII); §6 rollback.
- Carried-forward M6.2F tree + new **scale layer**: `scale/conditions.py` (the 8 doc §16 conditions verbatim,
  worst-status roll-up; **Risk = hard veto** RULE-017; Funnel [OD-002] + Dashboard [OD-005] fail-closed HOLD),
  `scale/models.py` (inert `AdsScaleRequest` CTR-013 + `ApprovalState` + `OwnerDecision`; `budget_cap`/`rollback_condition`
  are fields; `is_scale_authorized` requires owner-APPROVE **and** overall==PASS → always False in staged posture),
  `scale/scale_gate.py` (CTR-026 `propose()`/`record_owner_decision()`, Risk re-check at approval, **no executable
  scale method**), `scale/scale_request_store.py` (inert append-only), `api/scale_requests.py` (CTR-019 POST
  /api/admin/ads/scale-requests + owner-decision handler; conditions from server-side deps, RULE-H03),
  `config.py` (+`SCALE_EXECUTION_ENABLED=False`).
- Migrations (staged, never applied): `migrations/0009_create_ads_scale_request.sql`,
  `migrations/0010_create_ads_scale_approval.sql` (+ carried 0001–0008).

### 2.2 Tests
- Manifest: `04-artifacts/impl/M6.2G/tests/TEST_MANIFEST.md`.
- Bound smoke: `tests/smoke/test_smk_009_recall_sale_lock_scale_fail.py` (10),
  `tests/smoke/test_smk_012_scale_no_owner_approval.py` (4).
- Leg-supporting: `tests/test_no_executable_scale_path.py`, `test_scale_gate_risk_veto.py`,
  `test_scale_request_needs_owner_approval.py`, `test_scale_request_lifecycle.py`,
  `test_scale_conditions_failclosed.py`, `test_risk_recheck_at_approval.py` + carried suites.
- Full staged suite **313 passed / 0 failed** = 273 carried-forward (M6.2A–F) + **40 new M6.2G nodes** (26 scale-leg tests + 14 bound smoke SMK-009/012).

### 2.3 Reports
- Test report: `04-artifacts/test-reports/M6.2G/SMOKE_RESULTS.md` (SMK-009 10/10, SMK-012 4/4; full suite 313).
- Boundary report: `04-artifacts/boundary-reports/M6.2G_boundary.md`.
- Security/PII report: `04-artifacts/security-reports/M6.2G_security.md` (verdict PASS; scan clean over 155 files).
- Entry-gate Judge sign-off: `04-artifacts/evidence/judge/M6-P1600_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS, design-altitude).

---

## 3. Contract checklist (from the slice spec)

| Contract | Shape | Ownership | Status (canon) | Harmonization |
|---|---|---|---|---|
| M6-CTR-013 | ads_scale_request | M6 | MISSING / OWNER_DECISION_REQUIRED | M6-P0709 (PASS) |
| M6-CTR-019 | POST /api/admin/ads/scale-requests | M6 | MISSING / OWNER_DECISION_REQUIRED | M6-P0712 (PASS) |
| M6-CTR-026 | Scale Gate approval flow (request → owner approve/reject → budget cap → rollback) | M6 + Owner | MISSING / OWNER_DECISION_REQUIRED (thresholds = M6-OD-002) | M6-P0709 (PASS) |

All three are `MISSING` in canon but **satisfied-for-entry** (harmonization producers PASS, gate M6-P0715 SIGNED).
Canon-flips are deferred, non-blocking operator housekeeping.

---

## 4. Exit-gate checklist → evidence map

Legend: **MET** = evidence present and sufficient at the staged level · **SUPPORTED (staged)** = the bound suites
pass and the boundary adversary executed the check, with open (armed-not-fired) residuals · **PENDING** = the
producing prompt has not run yet. Caveats are carry-forwards (see §5); none trips the in-scope fail gate (M6-FAIL-006 — held).

| # | Exit-gate check (slice spec) | Verdict | Evidence refs | Notes / caveats |
|---|---|---|---|---|
| 1 | **No auto scale** — the system can compute and propose but has no code path that raises budget, enables campaigns or opens audience scale | **SUPPORTED (staged)** | `04-artifacts/test-reports/M6.2G/SMOKE_RESULTS.md` (SMK-009/012) + `tests/test_no_executable_scale_path.py` + `test_scale_conditions_failclosed.py`; `app/measurement/scale/scale_gate.py`, `scale/models.py`, `config.py` (`SCALE_EXECUTION_ENABLED=False`); boundary `M6.2G_boundary.md` + security `M6.2G_security.md` (FAIL-006 not tripped — 5 executed reasons) | RULE-010. Tester marks leg **L1 "met"**. `is_scale_authorized` structurally unreachable (exhaustive 1296-cell sweep → 0 PASS; config-flip triple fail-closed). Caveats B3-F-SCALE-2 (in-process bait-and-switch — not wire-exposed, inert, closest shape to a real FAIL-006 *if* an executor is ever wired) + F-SCALE-1/3/4 (validation residuals). Final L1 closure is the slice-gate Judge's call. |
| 2 | **Owner approval required** — ads_scale_request carries evidence refs, budget cap and rollback condition, and transitions only via explicit owner approval | **SUPPORTED (staged)** | `SMOKE_RESULTS.md` (SMK-012) + `tests/test_scale_request_lifecycle.py` + `test_scale_request_needs_owner_approval.py`; `scale/scale_gate.py` (never self-approves), `api/scale_requests.py` | RULE-015/020. Tester marks leg **L2 "met"**. Owner APPROVE requires fresh risk-clear + budget_cap + rollback + non-FAIL; a recorded APPROVE still authorizes nothing (overall HOLD). Caveat B4-ACCESS-1: the decision handler takes `actor` from the request body — at the M6-OD-011 binding it MUST authenticate the caller and bind `OwnerDecision.actor` to the authenticated identity. |
| 3 | **Smoke M6-SMK-009 executed** with recorded result + evidence ref | **MET** | `SMOKE_RESULTS.md` (10/10, exit 0); `04-artifacts/evidence/prompts/M6-P1604.json` | Every Risk-row lock (recall/sale_lock/quality_hold/complaint_p0/platform_spam_flag/crm_suppression) → Risk FAIL / overall FAIL (RULE-017 hard veto). |
| 4 | **Smoke M6-SMK-012 executed** with recorded result + evidence ref | **MET** | `SMOKE_RESULTS.md` (4/4, exit 0); `04-artifacts/evidence/prompts/M6-P1604.json` | No owner approval → not scale-authorized; the gate has no self/auto-approve or scale/execute entry point. |
| 5 | **All slice prompts have evidence JSON** (schema-valid, no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | `04-artifacts/evidence/prompts/M6-P1600.json` … `M6-P1606.json` present (7); `M6-P1607.json` produced at this prompt's completion | **Not yet complete:** M6-P1608 (Docs) and M6-P1609 (Judge) evidence not produced (both TODO). |
| 6 | **Slice-gate Judge sign-off exists with verdict PASS** | **PENDING (not met)** | — | `04-artifacts/evidence/judge/M6-P1609_JUDGE_FINAL_SIGN_OFF.json` does **not** exist; M6-P1609 is TODO. (The existing `M6-P1600_JUDGE_FINAL_SIGN_OFF.json` is the *entry* gate.) |
| 7 | **Rollback steps documented** for every change this slice made | **MET** | `04-artifacts/impl/M6.2G/PLAN.md` (per-item Rollback) + `IMPLEMENTATION_NOTES.md` §6 (new files → delete; patched `config.py` → revert to M6.2F); `migrations/0009`, `0010` down-DDL | All changes staged ⇒ non-destructive; lifecycle records inert + append-only. |

**Summary:** items **3, 4 and 7 are MET**; items **1 and 2 are SUPPORTED at the staged level** (tester marks L1/L2
"met" and FAIL-006 is not tripped, but the F-SCALE-1..4 / ACCESS-1 residuals remain — armed-not-fired — so final
closure is the slice-gate Judge's call); items **5 and 6 are PENDING** (M6-P1608 docs, then M6-P1609 slice-gate
Judge). Coverage: **every exit-gate checklist item is indexed** (acceptance check 1).

### 4.1 Smoke register bindings

| Smoke ID | Doc ID | Scenario (verbatim) | Expected (verbatim) | Result | Evidence |
|---|---|---|---|---|---|
| M6-SMK-009 | ADS-P0-009 | `Recall/Sale Lock active` | `Scale Gate FAIL/HOLD` | **PASS 10/10** | `SMOKE_RESULTS.md`, `M6-P1604.json` |
| M6-SMK-012 | ADS-P0-012 | `Scale request không owner approval` | `Không scale` | **PASS 4/4** | `SMOKE_RESULTS.md`, `M6-P1604.json` |

---

## 5. Unresolved blockers / carry-forwards (acceptance check 2)

None of the following is an open blocker of the **evidence-collection** task itself, and none trips the in-scope
fail gate (M6-FAIL-006 — held). Each was already adjudicated by the responsible upstream prompt and is carried
forward for the slice-gate Judge (M6-P1609) and the owner. **B2 and B7 are the load-bearing governance content of
this re-gate slice.**

- **B1 — Slice exit gate is not complete (expected at this step).** Item 5 pending M6-P1608/M6-P1609 evidence;
  item 6 pending the M6-P1609 slice-gate Judge PASS sign-off.

- **B2 — Entry gate is a DESIGN-ALTITUDE PASS with four recorded attestation true-ups.** M6-P1600 reversed its
  prior BLOCKED because all four entry rows were cured *in substance* (ENTRY-004 filed — M4 half PROVEN, M5 half
  owner-ratified-risk-accepted, ceiling-bounded; ENTRY-001 PROVEN via `_REJUDGE_VERDICT_2026-08-11`; ENTRY-003
  PROVEN via `_JUDGE_VERDICT_2026-08-27`; `M6-DEFER-FBC-M6.2D.json` filed recording F-A..F-F CLOSED). It is a
  **design-altitude** PASS (M6.2G never acts) — **not** a conversion of the underlying BLOCKED verdicts
  (`M6-P1000` and `M6-P1309` remain BLOCKED). M6-P1600 recorded **four real dossier-vs-artifact over-claims** as
  **hard true-ups before any real scale/send** (none touches the proven technical boundaries):
  - **(a)** ENTRY-001's M3-owner-confirmation field contradicts a carried note + no standalone M3-owner-signature artifact (runtime XML is present).
  - **(b)** ENTRY-003 cites `M6-ENTRY-003_INTERNAL_APPROVED_2026-08-27.md` which **does not exist** in the pack (the 11-code set was independently adversary-verified; external_send BLOCKED regardless).
  - **(c)** ENTRY-004 claims M4-owner CONFIRMED while its cited artifact lists that sign under `remaining_to_close`.
  - **(d)** the M5 `_OWNER_RISK_ACCEPTANCE.md` still has a **draft title + placeholder sha** (RATIFIED status line + `[x]` override for validity).
  - *Ref:* `04-artifacts/evidence/prompts/M6-P1600.json`, `04-artifacts/evidence/judge/M6-P1600_JUDGE_FINAL_SIGN_OFF.json`, `04-artifacts/evidence/entry/M6-ENTRY-004/`.

- **B3 — Scale-layer boundary residuals (M6-P1605), armed-not-fired, none trips M6-FAIL-006; routed to CODER / M6-OD-011.**
  - **F-SCALE-1 [MINOR]:** at approval, an empty/partial fresh risk read falls back to the *stale* proposal Risk
    condition; no scale authorized regardless (overall HOLD). Fix: require a **complete** fresh risk read to approve.
  - **F-SCALE-2 [in-process only — the closest shape to a real FAIL-006 if an executor is ever wired]:**
    `ScaleRequestStore.update_state` doesn't pin `scale_target`/`budget_cap`/`condition_results`, so an in-process
    `replace()`+`update_state` can bait-and-switch a genuine APPROVE onto a larger target/budget. Not wire-exposed,
    inert today. Fix: reject any transition mutating target/cap/condition_results **and** the M6-OD-011 binding must
    **re-run `evaluate_conditions` on load** (never trust a stored `overall_status`).
  - **F-SCALE-3 [MINOR]:** `budget_cap` accepts -1/0/+inf/NaN as "present". Fix: `math.isfinite` **and** `>0`.
  - **F-SCALE-4 [MINOR]:** `rollback_condition=' '` (whitespace) satisfies the cap+rollback pairing. Fix: content-validate.
  - N-1/N-2 (frozen-record forge / module-global mutation) require in-process code exec — defense-in-depth, not channel-reachable.
  - *Ref:* `04-artifacts/boundary-reports/M6.2G_boundary.md`.

- **B4 — Security residuals (M6-P1606), forward-routed.**
  - **ACCESS-1 [load-bearing forward requirement]:** the decision handler takes `actor` **from the request body**;
    there is no authentication that the caller *is* that owner. Inert today (APPROVE authorizes nothing), but at the
    M6-OD-011 HTTP binding the endpoint **must** authenticate the caller, authorize APPROVE to the owner role only,
    and bind `OwnerDecision.actor` to the authenticated identity — an APPROVE is the owner's authorization for a
    scale performed *outside* Module 6.
  - **F-SCALE-PII-1 [MINOR]:** `OwnerDecision.to_public()` and the `0010` approval record **echo** owner free-text
    (`reason`/`audit_ref`/`evidence_ref`) unmasked on export (excluded from the audit per the D5 fix; contract-non-PII,
    no leak today). Route: document/bound/mask on the export surface + M6-OD-012.
  - *Ref:* `04-artifacts/security-reports/M6.2G_security.md`.

- **B5 — Positive closure (the re-gate doing its job).** The M6.2F residual **F-DASH-4** (scale-eligibility ignored
  the 8-item DQ overall) is **CLOSED here**: the scale gate's Quality condition requires `dq_overall==PASS`, so a DQ
  HOLD/FAIL row makes overall HOLD/FAIL → never scale-authorized. The mandatory re-gate incorporates the DQ overall
  that the M6.2F attribution-level `is_scale_evidence_eligible` did not.

- **B6 — Contract housekeeping (non-blocking).** CTR-013/019/026 are `MISSING / OWNER_DECISION_REQUIRED` in canon
  but satisfied-for-entry (producers M6-P0709/M6-P0712 PASS, gate M6-P0715 SIGNED). Canon-flips deferred.

- **B7 — HARD FORWARD GATES before ANY real scale or external send (per M6-P1600; none blocks this never-act design
  slice, all must close before real egress/PR-PILOT).**
  - The **four attestation true-ups** (B2 a–d).
  - **ENTRY-001** conditions-before-real-scale: real-VNPAY-HMAC prepaid→VERIFIED e2e; prune TRUSTED enum/query drift;
    re-verify the Golden-Hour create-gate; read-side runtime revenue assertion; **re-confirm on dev at merge** (the
    `FAIL_OPEN_RECALL` fix `@a3aad246` is an unmerged personal branch).
  - **ENTRY-003 / send:** wire `requireExternalSendAllowed` to a real egress client + resolve **M6-OD-003** (hash
    policy, still BLOCKED at M6.2D) + **M6-OD-004** (connector) + secret_ref-only platform tokens.
  - **M5 (ENTRY-004):** close **DEBT-1..4** + run the **mandatory adversarial P4 re-gate** before real posting.
  - **M6-OD-005** (attribution scale model) before any row is scale evidence (`SCALE_MODEL_RATIFIED=False`);
    **M6-OD-002** (dashboard/scale thresholds).
  - **M6-OD-011 binding:** ACCESS-1 owner authN + F-SCALE-2 re-run-conditions-on-load + wire **no** scale executor
    while the posture stands.

- **B8 — Immutable governance posture (intact across M6.2A–G).** `global_gateway_state=BLOCKED`,
  `production_flag=OFF`, `external_send=OFF`, `HASH_POLICY_RATIFIED=False`, `SCALE_MODEL_RATIFIED=False`,
  `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False`, `SCALE_EXECUTION_ENABLED=False`, `live_migrations=false` — all
  unchanged. `M6-P1000` + `M6-P1309` verdicts remain **BLOCKED (not converted)**. FAIL-006 not tripped; the Scale
  Gate proves capability and authorizes nothing.

---

## 6. Reader's guide for the slice-gate Judge (M6-P1609)

1. Start from `00-spec/slices/M6.2G.md` "Exit gate checks" (the 7 items in §4 above).
2. For legs 1–4 + 7, read the reports/evidence in the §4 "Evidence refs" cells directly (do not rely on this index).
3. **This is the mandatory Scale-Gate re-gate.** Weigh the design-altitude entry PASS (§5 B2) — that it cured the
   four entry rows *in substance* while recording four attestation true-ups and keeping `M6-P1000`/`M6-P1309`
   BLOCKED — and confirm the exit legs prove *no auto scale* + *owner approval required* (FAIL-006 not tripped).
4. Confirm items 5 & 6 by re-reading the ledger and `04-artifacts/evidence/judge/` (M6-P1609 sign-off is the Judge's own output).
5. Treat the **B7 hard forward gates** (four attestation true-ups; ENTRY-001 real-VNPAY e2e + merge; ENTRY-003
   real egress wiring + OD-003/004; M5 DEBT-1..4 + P4 re-gate; OD-005/OD-002; ACCESS-1 + F-SCALE-2 at M6-OD-011) as
   the standing conditions before *any* real scale or external send — none of which this design slice satisfies or
   claims to.

*This index is descriptive. It advances no gate and self-certifies nothing; the runner EVIDENCE_GATE and the
slice-gate Judge decide closure.*
