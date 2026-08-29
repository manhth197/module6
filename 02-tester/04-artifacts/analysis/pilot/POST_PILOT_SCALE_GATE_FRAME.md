# M6 — Post-Pilot Scale-Gate Frame (the gate the OWNER runs after the pilot)

> ## What this is — and the boundary that governs it (read first)
> **The pack FRAMES; the OWNER decides.** This document gives the owner the *structure* to run the post-pilot scale gate
> — the doc §16 checklist rows, the required pilot evidence, and the rollback triggers — so the owner can run it once a
> real pilot has produced evidence. **It runs no gate, sets no threshold, and declares no Scale Ready.** Scale Ready is an
> owner declaration (SPEC §20 / doc §23: *"Chỉ khi pilot pass, no P0, AOV/CPA/ROAS đạt, owner approve"*); Module 6
> measures and proposes, it never scales or sends.
>
> **Thresholds are placeholders, not numbers.** Every numeric criterion below is written as `[pending M6-OD-002]` — the
> CPA / verified-rate / ROAS / AOV thresholds are the OPEN owner decision **M6-OD-002** and are **not invented here**.
> The one doc-fixed figure is AOV ≥ 2 boxes/order (SPEC §6 L108); the *range* CPA/verified-rate/ROAS must sit in is
> owner-set.
>
> **The gate cannot produce a PASS today** — it is fail-closed HOLD until the §2 preconditions close (M6-P3005 proved
> this: the 1296-cell condition cross-product yields overall==PASS in 0 cases while M6-OD-002/005 are OPEN).
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — immutable, untouched; this frame flips
> nothing. `M6-P1000` + `M6-P1309` verdicts remain **BLOCKED (not converted)**.

| Field | Value |
|---|---|
| Prompt | **M6-P3010** — `POST_PILOT_SCALE_GATE_FRAME` (ANALYST_ARCHITECT, `analysis_only`, EVIDENCE_GATE, phase PR_PILOT) |
| Entry gate | **M6-P3010=RUNNING** (order 196); dependency **M6-P3009=PASS** (pilot-evidence collect); the last executor prompt before **M6-P3011** FINAL_REVIEW_JUDGE |
| Task | Frame the owner's post-pilot scale gate: the checklist (doc §16 rows + thresholds once M6-OD-002 lands), required pilot evidence, and the rollback triggers |
| Canonical sources | `SPEC.md` §16 the 8 scale conditions (extract 317–324), §6 L108 funnel minimum, §7 L126 RULE-017 risk locks, L314 scale-request flow, §20 L387 Scale Ready; `M6_2G_RUNBOOK.md` (the scale-gate workflow); `DECISION_REGISTER.md` (M6-OD-002/005) |

---

## 1. Scope & method

`analysis_only` framing. It consolidates the canonical scale-gate criteria (doc §16 + SPEC §20) plus the pack's
propose-only scale-gate workflow (M6.2G) into an owner-runnable frame, and states honestly what must be true *before* the
gate can run. It invents no threshold, runs no evaluation, authorizes nothing, and writes no enabling value. The 8 doc
§16 conditions and the SPEC §20 Scale-Ready definition were confirmed against `SPEC.md` in M6-P3005 (PILOT_READINESS_REVIEW);
this frame reuses that confirmed canon and adds the pilot-evidence and rollback-trigger structure.

**The division of labor:** the pack supplies the checklist rows, the evidence requirements, and the rollback triggers
(this document + the M6.2G propose-only workflow). The owner lands M6-OD-002/005, closes the preconditions, runs a real
pilot, evaluates the gate on that evidence, and makes the Scale-Ready declaration. The pack never crosses that line.

---

## 2. Preconditions — what must close before the gate can run to a PASS

The gate is **fail-closed HOLD** until every item here is resolved by the owner. These are not this frame's to close;
they are surfaced so the owner runs the gate only when it can honestly reach a decision.

| Precondition | Why the gate needs it | Owner action |
|---|---|---|
| **M6-OD-002** (thresholds) — **OPEN** | Conditions 4 (Funnel) + the Scale-Ready `AOV/CPA/ROAS đạt` are un-evaluable without owner thresholds | Set CPA / verified-rate / ROAS thresholds per stage |
| **M6-OD-005** (attribution scale model) — **OPEN** | Condition 5 (Dashboard-as-scale-evidence) is fail-closed while `SCALE_MODEL_RATIFIED=False` | Ratify the one authoritative scale model |
| **The two BLOCKED verdicts** — `M6-P1000` (M6.2A entry), `M6-P1309` (M6.2D exit) | Staged via owner override, **not converted**; a real scale needs them resolved, not overridden | Convert (a real re-gate) or accept with recorded rationale |
| **The four entry attestation true-ups** (M6-P1600) | Dossier-vs-artifact over-claims recorded as hard-before-real-scale | Close (a)–(d): M3 owner signature, ENTRY-003 internal-approval file, ENTRY-004 M4 confirm, M5 risk-acceptance sha/title |
| **ACCESS-1 / M6-OD-011 admin authN** | The scale-request endpoint takes `actor` from the request body — no owner authentication; + MISSING CTR-018/019/020 | Wire authN/authZ at the M6-OD-011 target; bind `OwnerDecision.actor` to the authenticated identity |
| **M6-OD-003** (hash policy) — **OPEN** | Any real external send needs the permitted-field list ratified (still fail-closed today) | Ratify with privacy/legal; **only if** the pilot involves external send |
| **ENTRY-001/003/004 forward work** | real VNPAY-HMAC prepaid→VERIFIED e2e; egress client wiring; M5 DEBT-1..4 + adversarial P4 re-gate | Close before real scale/send |
| **The 3 proposed smokes** (SMK-016/017/018) | Executed but still labeled "proposed" — owner acceptance pending | Accept (or waive with a decision note) |

Until these close, the gate **cannot** produce a PASS; running it early yields HOLD/FAIL by construction (M6-FAIL-006 not
tripped, `is_scale_authorized` structurally unreachable — M6-P3005).

---

## 3. The post-pilot scale-gate checklist (the 8 doc §16 rows)

The owner runs these 8 conditions on **real pilot data**; the gate takes the **worst status** (FAIL > HOLD > PASS); the
**Risk row is a hard veto** (RULE-017). Overall PASS is required before any owner Scale-Ready declaration — and even a
computed PASS only *enables the owner to decide*, it does not itself scale.

| # | doc §16 condition | What the owner checks on pilot data | Pass criterion |
|---|---|---|---|
| 1 | **P3/P5/P6 evidence** | entry-evidence ENTRY-001..004 present + the four attestation true-ups closed | all refs present + true-ups closed → PASS, else HOLD |
| 2 | **Quote/Order** | M3/M8-owned boundary signal attested (M6 never validates it, RULE-021) | attested → PASS, else HOLD |
| 3 | **Public/Privacy** | M4/M5-owned boundary signal attested | attested → PASS, else HOLD |
| 4 | **Funnel** | AOV ≥ **2 boxes/order** (doc-fixed, SPEC L108); CPA ≤ `[ceiling — pending M6-OD-002]`; verified-rate ≥ `[floor — pending M6-OD-002]` | all three met → PASS; any below its owner threshold → HOLD |
| 5 | **Dashboard** | ROAS computed from ORDER_VERIFIED only (structural, RULE-003); attribution complete; ROAS ≥ `[floor — pending M6-OD-002]` under the `[M6-OD-005]` model | verified-only ROAS meets the owner floor under the ratified model → PASS; else HOLD |
| 6 | **Quality** | M6.2F Data Quality Gate overall = PASS (low dup, consent pass, outbox stable) on pilot data | DQ overall PASS → PASS; HOLD/FAIL otherwise |
| 7 | **Risk** (hard veto) | no active lock: recall / sale-lock / quality-hold / complaint-P0 / platform-spam / CRM-suppression (RULE-017); re-checked at approval | all clear → PASS; **any active → FAIL/HOLD for the whole gate** |
| 8 | **Approval** | explicit owner approval recorded + `budget_cap` set + `rollback_condition` set (via the authenticated endpoint, post-ACCESS-1) | owner APPROVE + cap + rollback → PASS; else not authorized |

> **Threshold discipline:** rows 4 and 5 carry `[pending M6-OD-002]` placeholders, never numbers. When M6-OD-002 lands,
> the owner substitutes the ratified CPA / verified-rate / ROAS values; the *shape* of the check (≥ floor / ≤ ceiling,
> per stage) is framed here, the *values* are the owner's. AOV ≥ 2 boxes is the only doc-fixed figure (SPEC L108).

---

## 4. Required pilot evidence (what the pilot must produce for the owner to run §3)

The gate is only as honest as the evidence it reads. The pilot must produce, on **real pilot traffic**, the doc §22
evidence categories plus the SPEC §20 Scale-Ready inputs:

**Per doc §22 (real-data, not staged smoke):**
1. **Event Registry** — pilot events all in registry (0 drift). 2. **Consent** — external measurement/audience only on
valid consent (fail-closed). 3. **Outbox** — queued/sent/retry/error/dead-letter healthy. 4. **Dedup** — Pixel/CAPI/Offline
duplicates collapsed. 5. **Attribution** — every pilot ORDER_VERIFIED traces back campaign/adset/ad/page/live/comment/
messenger; confidence HIGH (LOW/HOLD never scale evidence, RULE-009). 6. **Dashboard** — Revenue Verified / ROAS / CPA /
AOV from ORDER_VERIFIED-only sources. 7. **Scale Gate** — the §3 computation recorded with its condition statuses. 8.
**Learning** — (if in pilot scope) candidate→review→approve/reject/hold→rollback, no publish outside safe range. 9.
**Security/Privacy** — 0 raw PII in payloads/logs; hash policy applied; access control enforced. 10. **Smoke Report** —
the P0 matrix re-run on pilot config, each with a masked `correlation_id` + `evidence_id`.

**Per SPEC §20 Scale-Ready:**
- **Pilot pass** — the pilot ran and met its acceptance criteria (owner-defined).
- **No P0** — no P0 fail gate tripped on pilot traffic (FAIL-001..007 held, real data).
- **AOV/CPA/ROAS đạt** — the row-4/5 thresholds met once M6-OD-002 lands.
- **Owner approve** — recorded through the authenticated endpoint with `budget_cap` + `rollback_condition`.

**Chain-integrity evidence the owner should demand before scaling** (from the E2E chain review, all OPEN today): the
**F-SEC-2I-1** single-subject trace bind fixed before any funnel export; the **F-GROWTH-3** verified-only choke carried
into the growth reads; **F-GROWTH-1** CRM subject-bind; and the export-masking family under M6-OD-012 — these are the
CODER hardening items the pilot must not re-expose.

---

## 5. Rollback triggers (halt / HOLD / reverse — the owner's stop conditions)

Every scale request carries a mandatory `budget_cap` + `rollback_condition` (SPEC L314); these triggers are the frame for
that rollback condition. **A trigger firing means: HOLD the gate and, if a scale is already live, reverse it.**

**Immediate hard-veto triggers (RULE-017 risk locks — any one FAILs/HOLDs the gate and halts a live scale):**
- **Recall** active · **Sale-lock** active · **Quality-hold** active · **Complaint-P0** open · **Platform-spam-flag** set
  · **CRM-suppression** active. The gate re-checks these at approval time and (in a live posture) continuously.

**Measurement-integrity triggers (once M6-OD-002 lands):**
- Verified-rate drops below `[floor — pending M6-OD-002]` · CPA rises above `[ceiling — pending M6-OD-002]` · ROAS drops
  below `[floor — pending M6-OD-002]` · AOV drops below 2 boxes/order.
- **Data Quality Gate flips to HOLD/FAIL** (dup spike, consent breach, outbox backlog/dead-letter, attribution confidence
  degradation).
- **Any owner P0 fail gate trips** on live traffic — FAIL-001 revenue misuse, FAIL-002 consent, FAIL-003 event drift,
  FAIL-004 core override, FAIL-005 data-mart, FAIL-006 auto-scale, FAIL-007 no-evidence (the owner P0 set, doc §23) —
  **or the raw-PII hardening gate FAIL-008** (a pack HARDENING extension, per FAIL_GATE_REGISTER).

**Reversal mechanism (owner integration, not this staged build):** the staged build's rollback is delete-the-tree
(M6-P3007) — that reverses the *implementation*, not a *live scale*. Reversing a real, already-executed scale
(budget-down, campaign-off, audience-scale-close) is an action **outside Module 6** performed by the owner/operator at
the M6-OD-011 integration; Module 6 records the rollback decision, it never executes the scale or its reversal. The
owner's post-pilot runbook must define the concrete reversal steps for the real platform before any scale is enabled.

---

## 6. Governance frame (the boundary this document lives inside)

- **The pack frames; the owner decides.** This document is a checklist + evidence spec + trigger list. Running the gate,
  setting M6-OD-002/005, judging the pilot, and declaring Scale Ready are **owner-only** (SPEC §20 / doc §23).
- **The scale gate authorizes nothing.** M6.2G is a propose-only, never-act workflow: `is_scale_authorized` requires an
  owner APPROVE **and** overall==PASS **and** cap **and** rollback, and even then Module 6 executes no scale — the owner
  performs any real scale outside Module 6, gated by `production_flag=OFF`.
- **Module boundary intact:** Module 6 measures and proposes; it never raises a budget, enables a campaign, opens audience
  scale, sends, or publishes. Order/QuoteSnapshot is M3 (RULE-021); commission is Finance (RULE-019); recall/sale-lock are
  the risk owners' (RULE-017).

---

## 7. Immutable posture & honest verdict

- **Posture (untouched):** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
  `SCALE_MODEL_RATIFIED=False`, `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False`, `SCALE_EXECUTION_ENABLED=False`,
  `HASH_POLICY_RATIFIED=False`, `live_migrations=false`. This frame writes no enabling value and sets no threshold.
- **Verdict (honest):** this is a **frame, not a gate result**. It gives the owner a complete, runnable post-pilot
  scale-gate structure — the 8 doc §16 checklist rows with `[pending M6-OD-002]` threshold placeholders, the required
  pilot evidence (doc §22 on real data + SPEC §20 Scale-Ready inputs), and the rollback triggers (RULE-017 locks +
  threshold/DQ/P0 breaches). The gate **cannot run to a PASS** until the §2 preconditions close (thresholds, scale model,
  the two BLOCKED verdicts, the attestation true-ups, ACCESS-1 authN). Nothing here declares Scale Ready, sets a
  threshold, or authorizes a scale — those are the owner's, after a real pilot.

*Assembly note: `analysis_only` — read the confirmed doc §16/§20 canon + the M6.2G workflow + the PR/PILOT band evidence +
registers, and wrote only this file and its evidence JSON. Invented no threshold, ran no gate, computed no verdict,
flipped no flag, touched no `04-artifacts/state/`. `global_gateway_state=BLOCKED`, `production_flag=OFF`,
`external_send=OFF` — untouched; `M6-P1000` + `M6-P1309` verdicts remain BLOCKED (not converted).*
