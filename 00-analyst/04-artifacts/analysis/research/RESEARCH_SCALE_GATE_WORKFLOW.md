# RESEARCH_SCALE_GATE_WORKFLOW — owner-approval workflow for the Scale Gate (doc §16)

**Prompt**: M6-P0208 · **Phase**: PHASE0_RESEARCH · **Mode**: analysis_only (desk research; design proposal)
**Anchors**: `[DOC §16 extract lines 311–324]` Scale Gate; `M6-CTR-013 ads_scale_request` +
`M6-CTR-026 Scale-Gate approval flow` (→M6-P0709), `M6-CTR-019 POST /api/admin/ads/scale-requests` (→M6-P0712);
slice **M6.2G** (done gate: *"No auto scale, owner approval required"*).
**Critic**: M6-PC0208 (BOUNDARY_ADVERSARY) red-teams this file next.

> **The invariant that governs this entire file:** Module 6 **computes conditions, bundles evidence, and
> proposes** — it has **NO code path** that raises a budget, enables a campaign, or opens audience scale.
> Approval is the **owner's**, executed **outside** M6, and in this pack `global_gateway_state=BLOCKED` /
> `production_flag=OFF` mean **nothing scales at all**. An approved `ads_scale_request` is still only **data**.

## Sourcing legend (acceptance: every externally-sourced claim labeled)

- `[DOC]` — owner document / extract line. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked pack register. · `[BRIEF]` — context brief. · `[PACK]` — pack convention (owner-review).
- `[EXT]` — general engineering practice, **proposal only**.

**Doc anchors**: `[DOC §16 L312]` *"SCALE GATE LÀ QUYẾT ĐỊNH CỦA OWNER. Module 6 chỉ tính toán và đề xuất.
Tăng ngân sách, bật campaign scale, mở audience scale hoặc publish optimization đều cần owner approval, có
evidence, có rollback và có giới hạn rủi ro."*; `[DOC §16 L317–324]` the 8 scale-condition rows; `[DOC §16
L323]` Risk row *"Không recall, không sale lock, không quality hold, không complaint P0, không platform spam
flag"*; `[DOC §16 L324]` Approval row *"Owner duyệt scale request, có budget cap, có rollback condition"*.
Rules: `[REG RULE-010]` (scale is owner's; M6 only computes + creates ads_scale_request w/ budget cap +
rollback; never raises budget / enables campaigns / bypasses approval), `[REG RULE-017]` (suppression/risk
locks; no scale while any active), `[REG RULE-009]` (LOW/HOLD never scale evidence), `[REG FAIL-006]` (auto
scale). Entry evidence `M6-ENTRY-001..004`.

---

## 1. Core invariant — compute & propose, never execute `[DOC §16 L312 / REG RULE-010, FAIL-006]`

The Scale Gate is an **owner decision** `[DOC L312]`. M6's role is strictly:

1. **compute** the 8 scale conditions from measured, verified data;
2. **bundle** the supporting evidence;
3. **propose** via an `ads_scale_request`.

M6 must have **no executable path** to change a budget / enable a campaign / open audience scale — the M6.2G
done gate states exactly this (*"the system can compute and propose but has no code path that raises budget,
enables campaigns or opens audience scale"*). Auto-scaling is `[REG FAIL-006]`. The owner acts on the proposal
**outside** M6; in this pack even that is BLOCKED/OFF (staged).

---

## 2. The proposal object — `ads_scale_request` with budget cap + rollback `[DOC §16 L324 / REG CTR-013/026]`

`[EXT] proposed shape` (fields finalized in M6-P0709):

`{ request_id, scope {campaign_id|adset_id|audience_id}, proposed_change {metric, delta}, budget_cap (hard
ceiling), rollback_condition, condition_results[8], evidence_refs[], risk_state, status, owner_decision {actor,
verdict, ts}, created_at, audit[] }`

- **`budget_cap`** `[DOC L324]` — a hard maximum on the proposed increase; the proposal cannot exceed it.
- **`rollback_condition`** `[DOC L324]` — a predefined, machine-checkable condition that reverts the scale
  (e.g. ROAS below the owner threshold, or any risk lock activating — §4). Stored **with** the request so
  rollback is not improvised later.
- The object is **inert data**: creating/approving it changes no budget. `[PACK]`

---

## 3. Evidence bundling — the 8 condition rows `[DOC §16 L317–324 / REG RULE-009/015]`

The request bundles a PASS/HOLD/FAIL result **and evidence ref** for each `[DOC §16]` condition:

| # | Condition `[DOC]` | Evidence source |
|---|---|---|
| 1 | P3/P5/P6 evidence (L317) | `M6-ENTRY-001/002/003` `[REG]` |
| 2 | Quote/Order correctness (L318) | Commerce Verified Revenue boundary (ENTRY-001) |
| 3 | Public/Privacy (L319) | `M6-ENTRY-004` (no public final price / no PII leak / no spam) |
| 4 | Funnel: AOV≥2 boxes/order, CPA in range, verified rate (L320) | dashboard metrics — thresholds **M6-OD-002** |
| 5 | Dashboard: ROAS by ORDER_VERIFIED, attribution complete (L321) | M6-P0207 evidence-bundle; single primary model (M6-P0206) |
| 6 | Quality: DQ Gate PASS, low duplicate, consent pass, outbox stable (L322) | `ads_data_quality_check` verdict |
| 7 | Risk: no recall/sale-lock/quality-hold/complaint-P0/spam-flag (L323) | §4 |
| 8 | Approval: owner approves, budget cap, rollback (L324) | owner decision + §2 |

`[REG RULE-009]` **Only PASS + HIGH-confidence** evidence may support a scale case; any LOW/HOLD/conflicting
input makes the request HOLD, never a silent pass. `[REG RULE-015]` no condition is "PASS" without its trace.

---

## 4. Risk-override veto — recall / sale-lock / suppression `[DOC §16 L323 / REG RULE-017]`

The Risk row is a **hard veto**, not a weighted factor. If **any** of — recall, sale lock, quality hold,
complaint P0, platform spam flag `[DOC L323]`, **or** CRM suppression `[DOC §15 L307, REG RULE-017]` — is
active, the Scale Gate is **FAIL/HOLD regardless of every other green condition**. Fail-closed.

- Re-checked at **approval time** (not only at proposal time) — a lock that activates between proposal and
  approval blocks the approval.
- Also a natural **`rollback_condition`**: a lock activating **after** an (owner-approved, external) scale must
  trigger rollback. `[PACK]`
- Exercised by smoke **M6-SMK-009** (*Recall/Sale Lock active → Scale Gate FAIL/HOLD*) `[REG]`.

---

## 5. Lifecycle + audit trail `[REG RULE-010/008]`

`[EXT] proposed lifecycle`: `DRAFT → PROPOSED → (owner) APPROVED | REJECTED | HOLD → [external scale by owner]
→ ROLLED_BACK (if rollback_condition fires)`.

- **Every** transition is audited: `{actor, from→to, reason, evidence_ref, ts}` — append-only, immutable
  `[REG RULE-008]`. Owner approval is **explicit** (a recorded decision by an authorized actor), never inferred
  or self-approved by M6 (mirrors the pack's own no-self-certify discipline).
- The condition-evaluation snapshot is frozen with the request so an approval is auditable against exactly the
  evidence it was granted on.
- No transition inside M6 performs an external budget/campaign action `[REG RULE-010]`.

## 6. Boundary & safety guards `[BRIEF / REG §18]`

- **No executable scale path** in M6 `[REG RULE-010 / FAIL-006 / M6.2G done gate]`; propose-only.
- **Staged**: `global_gateway_state=BLOCKED`, `production_flag=OFF` ⇒ no real budget/campaign/audience change,
  even for an approved request. This research flips nothing.
- No pricing/order/CRM/commission side effects; the scale request references measurement only.
- **No raw PII / secrets** in the request or audit `[REG RULE-014]`; ad-account/campaign ids are references,
  tokens are `secret_ref`.
- Owner-approval content and any channel-origin risk signals are untrusted DATA `[BRIEF rule 6]`.

## 7. Owner-decision dependencies (explicit list — acceptance requirement)

| Dependency | Status | What it gates |
|---|---|---|
| `M6-CTR-013` (ads_scale_request) + `M6-CTR-026` (approval flow fields) | `MISSING` → **M6-P0709** `[REG]` | the proposal/flow shape (§2); needed before **M6.2G** |
| `M6-CTR-019` (POST /api/admin/ads/scale-requests) | `MISSING` → **M6-P0712** `[REG]` | the request-creation API |
| `M6-OD-002` (CPA/ROAS/AOV/verified-rate thresholds) | **OPEN** `[REG]` | condition #4/#5 pass criteria (§3) |
| `M6-ENTRY-001..004` (P3/P5/P6 + public-privacy evidence) | **OPEN** `[REG]` | conditions #1–3, #7 (§3, §4) |
| Owner-approval roles/mechanism; who may approve | **candidate** `[PACK]` — doc says "owner duyệt", role unspecified | §5 approval authority |
| Rollback-condition catalog + budget-cap policy | **candidate** `[PACK]` — doc mandates their existence, not their values | §2/§4 definitions |
| `M6-OD-005` (single primary attribution model) | **OPEN** `[REG]` | condition #5 scale ROAS basis (M6-P0206) |

`[PACK]` This research records these; it resolves none. Where a build leg needs one, the affected M6.2G leg is
marked BLOCKED, not assumed.

## 8. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| Scale is an owner decision; M6 computes+proposes only; approval needs evidence + rollback + risk limit | `[DOC §16 line 312]` + `[REG RULE-010 / FAIL-006]` — owner-mandated |
| The 8 scale-condition rows (P3/P5/P6, Quote/Order, Public/Privacy, Funnel, Dashboard, Quality, Risk, Approval) | `[DOC §16 lines 317–324]` — owner-mandated |
| ads_scale_request carries budget cap + rollback condition | `[DOC §16 line 324]` + `[REG RULE-010]` — owner-mandated |
| Risk row (recall/sale-lock/quality-hold/complaint-P0/spam-flag) + CRM suppression = hard veto | `[DOC §16 line 323, §15 line 307]` + `[REG RULE-017]` — owner-mandated |
| Only PASS/HIGH-confidence is scale evidence | `[REG RULE-009]` — owner-mandated |
| Request field shape; DRAFT→…→ROLLED_BACK lifecycle; audit-record shape; re-check-at-approval; rollback triggers | `[EXT]` / `[PACK]` — owner-review proposals, NOT owner requirements |

*Nothing in this file flips a gate or a flag, and it grants no scale; `global_gateway_state=BLOCKED`,
`production_flag=OFF`.*
