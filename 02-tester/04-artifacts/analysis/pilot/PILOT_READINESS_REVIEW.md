# M6 — Pilot Readiness Review (against the doc §16 Scale-Gate conditions)

> ## ⚠ Headline (read first): against the doc §16 scale conditions, the gate is fail-closed **HOLD** — **NOT scale-ready**, by design
> This review reports pilot readiness **per doc §16 condition, honestly**. In the staged posture the Scale Gate
> **cannot compute a scale-ready PASS** — two conditions (Funnel, Dashboard-as-scale-evidence) are fail-closed HOLD
> because their thresholds/model are **OPEN owner decisions**, and the Risk row is a hard veto. This is the correct
> fail-closed truth, not a defect: the Scale Gate is a **propose-only, never-act** workflow that proves capability and
> **authorizes nothing**. `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
> `SCALE_MODEL_RATIFIED=False`, `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False`, `SCALE_EXECUTION_ENABLED=False` —
> immutable, untouched.
>
> **Thresholds are reported OPEN, not assumed** (per the task): the CPA / verified-rate / ROAS / CPA-AOV thresholds
> are **M6-OD-002 (OPEN)** and the attribution scale model is **M6-OD-005 (OPEN)** — no numeric threshold is invented
> anywhere in this review. **Scale Ready is an owner declaration** (SPEC §20 / doc §23: *"Chỉ khi pilot pass, no P0,
> AOV/CPA/ROAS đạt, owner approve"*) — this pack cannot and does not make it.

| Field | Value |
|---|---|
| Prompt | **M6-P3005** — `PILOT_READINESS_REVIEW` (ANALYST_ARCHITECT, `analysis_only`, EVIDENCE_GATE, phase PR_PILOT) |
| Entry gate | **M6-P3005=RUNNING** (order 191); dependency **M6-P3004=PASS** (owner sign-off packet) |
| Reviewed against | doc §16 Scale-Gate — the **8 conditions** (extract 317–324) + the SPEC §20 **Scale-Ready** definition |
| Canonical sources | `SPEC.md` §6 L108 (funnel minimum), §7 L126 (RULE-017 risk locks), L314 (scale-request flow), §20 L387 (Scale-Ready); `M6_2G_RUNBOOK.md` §1.2 (the 8-condition staged evaluation, judge-SIGNED); `DECISION_REGISTER.md` (M6-OD-002/005) |
| Verdict framing | **NOT scale-ready** (fail-closed HOLD by design); measurement + scale-gate capability **proven** (SMK-009/012 PASS, FAIL-006 not tripped); readiness for real scale requires the owner to close §6 |

---

## 1. Scope & method

The task: review pilot readiness **against the doc §16 scale conditions**, reporting per-condition status honestly with
thresholds pending M6-OD-002 reported as **OPEN, not assumed**. This is `analysis_only` — it reads the canonical §16
conditions + the scale-gate evidence and reports status; it authorizes nothing, invents no threshold, and flips no flag.

I confirmed the 8 conditions and the Scale-Ready definition **directly against `SPEC.md`** (not only the M6.2G runbook):
SPEC §6 L108 states the funnel scale minimum with thresholds bound to M6-OD-002; SPEC §7 L126 lists the six RULE-017
risk locks; SPEC L314 gives the scale-request flow (`computed → proposed [budget cap + rollback] → owner approve/reject;
recall/sale-lock ⇒ FAIL/HOLD`); SPEC §20 L387 defines Scale Ready as owner-only. The M6.2G runbook §1.2 (judge-SIGNED
at M6-P1609) is the faithful per-condition staged mapping and matches canon.

---

## 2. The canonical criteria

**doc §16 Scale-Gate — the 8 conditions** (extract 317–324): P3/P5/P6 evidence · Quote/Order · Public/Privacy · Funnel ·
Dashboard · Quality · Risk · Approval. The gate takes the **worst status** across all eight (FAIL > HOLD > PASS); the
**Risk row is a hard veto** (RULE-017).

**SPEC §20 Scale-Ready** (doc §23, owner declaration): *"Chỉ khi **pilot pass**, **no P0**, **AOV/CPA/ROAS đạt**,
**owner approve**"* — four owner-side conditions. **ROAS Pass** (the prerequisite): *"Chỉ khi ORDER_VERIFIED revenue,
attribution pass, dashboard pass, data quality pass"*. Both are owner declarations this pack cannot make.

---

## 3. Per-condition status against the 8 doc §16 conditions (honest)

Legend — **Mechanism**: is the enforcement built + proven? **Staged status**: how the condition evaluates in the staged
posture. **Gap to real-scale readiness**: what must close (OPEN owner decision / forward gate / real pilot data).

| # | Condition (doc §16) | Mechanism | Staged status | Gap to real-scale readiness |
|---|---|---|---|---|
| 1 | **P3/P5/P6 evidence** | ✅ built (entry-evidence refs ENTRY-001..004 required, RULE-020) | **HOLD (conditional)** — refs present but carry **four attestation true-ups** | The four true-ups (§6a) + ENTRY-001 (real VNPAY-HMAC prepaid→VERIFIED e2e, merge re-confirm) + ENTRY-003 (send) + ENTRY-004 (M5 DEBT-1..4 + P4 re-gate) |
| 2 | **Quote/Order** | ✅ consumed boundary signal (M3/M8-owned; M6 never validates, RULE-021) | **HOLD** — not independently attested in staged | Boundary owner (M3/M8) attestation at real-scale time |
| 3 | **Public/Privacy** | ✅ consumed boundary signal (M4/M5) | **HOLD** — not independently attested in staged | Boundary owner (M4/M5) attestation |
| 4 | **Funnel** (AOV ≥ 2 boxes, CPA in range, verified-rate ≥ owner threshold) | ✅ computed fail-closed | **HOLD (fail-closed)** | **M6-OD-002 OPEN** — CPA / verified-rate thresholds are **not set** and **not assumed**; AOV ≥ 2 boxes is doc-fixed but needs **real pilot data** |
| 5 | **Dashboard** (ROAS by ORDER_VERIFIED, attribution complete) | ✅ ROAS-verified-only is structural (RULE-003, M6.2F) | **HOLD (fail-closed as scale evidence)** | **M6-OD-005 OPEN** (`SCALE_MODEL_RATIFIED=False`) — no model is scale-authoritative; RULE-009 (LOW/HOLD never scale evidence) |
| 6 | **Quality** (DQ Gate PASS, low dup, consent pass, outbox stable) | ✅ built (M6.2F Data Quality Gate; closes F-DASH-4) | **PASS iff DQ overall PASS** — proven on staged test data | **Real pilot data** — DQ overall must be observed PASS on live pilot traffic (no real-data observation yet) |
| 7 | **Risk** (no recall / sale-lock / quality-hold / complaint-P0 / platform-spam / CRM-suppression) | ✅ built — HARD VETO, all 6 locks, re-checked at approval (SMK-009 10/10) | **VETO-ready** — any active lock ⇒ FAIL/HOLD for the whole gate | Must be observed clear at real-scale time; the fresh-read-must-be-complete fix (F-SCALE-1) hardening |
| 8 | **Approval** (owner approves + budget cap + rollback) | ✅ built — explicit owner-decision record required (SMK-012 4/4) | **not authorized** — no owner approval in staged; a recorded APPROVE still yields `is_scale_authorized=False` while overall is HOLD | **ACCESS-1 / M6-OD-011** — the endpoint must authenticate the caller **is** the owner (today `actor` is body-supplied); owner approval + budget_cap + rollback at real-scale time |

**Overall (worst-status):** **HOLD** — conditions 4 and 5 are fail-closed HOLD, condition 1 is conditional-HOLD, and the
Risk veto stands ready. The Scale Gate **cannot reach overall PASS** in the staged posture (see §5). This is the honest
per-condition truth: the capability is built and proven; **no condition is scale-ready** because the thresholds (OD-002),
scale model (OD-005), entry true-ups, and owner-authN (ACCESS-1) are OPEN.

---

## 4. The SPEC §20 Scale-Ready gate (owner declaration — each part's status)

| Scale-Ready part (SPEC §20) | Status | Note |
|---|---|---|
| **Pilot pass** | **NOT MET** | No real pilot has run; `production_flag=OFF`. A pilot is itself owner-gated. |
| **No P0** | **partially evidenced** | No P0 fail gate tripped across the build (FAIL-001..007 held; boundary full pass 0 breaches) — but "no P0" for a *pilot* is measured on real pilot traffic, not yet observed. |
| **AOV / CPA / ROAS đạt** | **OPEN (not assumed)** | Thresholds are **M6-OD-002 (OPEN)**; the attribution model is **M6-OD-005 (OPEN)**. No numeric threshold is set or invented. |
| **Owner approve** | **owner-only** | The Scale-Ready declaration itself; `is_scale_authorized` is structurally False in the staged posture (§5); the owner performs any real scale **outside** Module 6. |

**Scale Ready is NOT met and cannot be asserted by this pack.** Its ROAS-Pass prerequisite (ORDER_VERIFIED revenue +
attribution pass + dashboard pass + DQ pass) is structurally supported (verified-only revenue is enforced at the core —
see the E2E chain review) but is likewise an **owner declaration** on real pilot data.

---

## 5. Why the gate cannot compute a scale-ready PASS in the staged posture (the fail-closed truth)

The boundary + security review of M6.2G established this **by execution**, and FAIL-006 (auto scale) is **not tripped**
(30 boundary outcomes, 0 FAIL-006 breaches; five independent executed reasons):

1. **No executable scale path exists** — a token sweep of all five scale modules finds 0 action defs and 0 posture-flag
   writes; no raise-budget / enable-campaign / open-audience / scale / send / publish / auto-approve method anywhere.
2. **`is_scale_authorized` is structurally unreachable** — Funnel (OD-002) and Dashboard (OD-005) are fail-closed HOLD in
   both branches; an **exhaustive 1296-cell `ScaleContext` cross-product yields overall==PASS in 0 cases**.
3. **Config flips don't help** — flipping both `DASHBOARD_ALERT_THRESHOLDS_DEFINED` and `SCALE_MODEL_RATIFIED` True
   in-process still yields overall HOLD (triple fail-closed).
4. **No consumer arms it** — nothing reads a posture flag to branch into an action; even a `True` `is_scale_authorized`
   would execute nothing.
5. **Nothing is wire-forgeable** — conditions are computed server-side, never from the untrusted request body; a recorded
   owner APPROVE stays not-authorized while overall is HOLD.

**Evidence:** SMK-009 (recall/sale-lock → FAIL/HOLD) PASS 10/10 covering all 6 risk locks; SMK-012 (no owner approval →
no scale) PASS 4/4; full staged suite 313 passed / 0 failed. The Scale Gate proves capability and **authorizes nothing**.

---

## 6. Hard forward gates before ANY real scale / pilot-with-scale (the honest OPEN/BLOCKED list)

None blocks this never-act review; **all must close before any real scale or external send** (from M6.2G §5.4 + the
standing blockers).

### 6a. The four entry attestation true-ups (recorded by the M6.2G entry judge M6-P1600, hard before real scale)
- **(a)** ENTRY-001's M3-owner-confirmation field contradicts a carried note; no standalone M3-owner-signature artifact.
- **(b)** ENTRY-003 cites an internal-approval file that **does not exist** in the pack (11-code set adversary-verified; external_send BLOCKED regardless).
- **(c)** ENTRY-004 claims the M4-owner CONFIRMED while its cited artifact lists that sign under `remaining_to_close`.
- **(d)** the M5 `_OWNER_RISK_ACCEPTANCE.md` still has a draft title + placeholder sha.

### 6b. OPEN owner decisions on the scale path (reported OPEN, not assumed) + the M6-OD-011 integration condition
- **M6-OD-002** — dashboard/scale thresholds (CPA / verified-rate / ROAS / AOV) — **OPEN** (condition 4).
- **M6-OD-005** — attribution scale model — **OPEN** (condition 5; `SCALE_MODEL_RATIFIED=False`).
- **M6-OD-003** — hash policy + permitted send fields — **OPEN** (still BLOCKED at M6.2D; before any real send).
- **M6-OD-004** — connector (Meta/Google) — **OPEN**.
- **The M6-OD-011 target — ACCESS-1 authorization-integrity gate (condition 8; a forward *integration* condition, NOT an
  OPEN owner decision).** The owner *decision* M6-OD-011 (target repo/stack) is **DECIDED 2026-07-23** (GREENFIELD;
  `IMPLEMENTATION_TARGET_LOCKED.json`=LOCKED); what remains open at its HTTP binding is admin-endpoint authN/authZ — the
  endpoint must authenticate that the caller **is** the owner and bind `OwnerDecision.actor` to the authenticated
  identity, never a body-supplied string (runtime framework/authN still unresolved in the manifest). (+ MISSING
  CTR-018/019/020, the admin-endpoint contracts.)
- **M6-OD-012** — owner free-text masking on export (F-SCALE-PII-1).

### 6c. Entry-condition forward work (before real scale)
- **ENTRY-001** — real VNPAY-HMAC prepaid→VERIFIED e2e; re-confirm the `FAIL_OPEN_RECALL` fix on dev at merge (unmerged branch).
- **ENTRY-003 / send** — wire `requireExternalSendAllowed` to a real egress client + M6-OD-003/004 + secret_ref-only tokens.
- **ENTRY-004 / M5** — close DEBT-1..4 + run the mandatory adversarial P4 re-gate before real posting.

### 6d. Scale-layer CODER hardening (armed-not-fired; none trips FAIL-006)
- **F-SCALE-2** (in-process; closest to a real FAIL-006 if an executor is ever wired) — `update_state` must re-run
  `evaluate_conditions` on load, never trust a stored `overall_status`; reject a transition mutating target/cap/conditions.
- **F-SCALE-1** (complete fresh risk read to approve), **F-SCALE-3** (`isfinite(cap) and cap>0`), **F-SCALE-4**
  (content-validate rollback), **F-SCALE-PII-1** (mask/bound owner free-text on export).

### 6e. Standing governance
- **M6-P1000** (M6.2A entry) + **M6-P1309** (M6.2D exit) verdicts remain **BLOCKED (not converted)**; the M6.2G entry
  PASS (M6-P1600) was a **design-altitude, honest-path** cure of the four entry rows for a never-act slice — **not** a
  conversion of those BLOCKED verdicts.

---

## 7. Immutable posture & honest verdict

- **Posture (untouched):** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
  `SCALE_MODEL_RATIFIED=False`, `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False`, `SCALE_EXECUTION_ENABLED=False`,
  `HASH_POLICY_RATIFIED=False`, `live_migrations=false`. This review writes no enabling value anywhere.
- **Verdict (honest):** against the doc §16 scale conditions, the pilot is **NOT scale-ready** — the gate is fail-closed
  **HOLD** and structurally cannot reach a scale-ready PASS in the staged posture. This is **by design**: the
  measurement + Scale-Gate capability is **built and proven** (SMK-009/012 PASS, FAIL-006 not tripped, 313 tests), and
  the gate correctly **refuses to authorize** any scale. Real-scale readiness requires the owner to close §6 — most
  importantly **M6-OD-002** (thresholds, condition 4), **M6-OD-005** (scale model, condition 5), the four entry
  attestation true-ups (condition 1), and **ACCESS-1 / M6-OD-011** owner authN (condition 8) — and then, owner-side, to
  make the **Scale-Ready** declaration (SPEC §20: pilot pass + no P0 + AOV/CPA/ROAS met + owner approve). This review
  makes no such declaration and authorizes nothing.

*Assembly note: `analysis_only` — read the canonical §16 conditions + scale-gate evidence + registers and wrote only this
file and its evidence JSON. Touched no `04-artifacts/state/`, marked no ledger row, invented no threshold, computed no
verdict, flipped no flag. `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — untouched;
`M6-P1000` + `M6-P1309` verdicts remain BLOCKED (not converted).*
