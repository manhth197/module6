# SCALE_LEARNING_DESIGN — scale-request workflow + learning-engine skeleton

**Prompt**: M6-P0305 · **Phase**: PHASE0 (design) · **Mode**: plan_only (no code, no migration, no call)
**Anchors**: `[DOC §16 L312–324]` Scale Gate (owner decision + 8 conditions); `[DOC §17 L326–353]` Learning
Engine (Seed→…→Publish); `[SPEC §13]` state machines (Scale request; Learning lifecycle; Candidate review).
Contracts: `CTR-013 ads_scale_request` + `CTR-026 approval flow` (→M6-P0709), `CTR-014 ads_learning_candidate`
(→M6-P0710), `CTR-019/020` APIs (→M6-P0712). **Synthesizes** `[[RESEARCH_SCALE_GATE_WORKFLOW]]` (M6-P0208),
`[[RESEARCH_LEARNING_ENGINE_GUARDRAILS]]` (M6-P0209), `[[RESEARCH_STRATEGY_LIBRARIES]]` (M6-P0211) — not
restated. **No dedicated critic** follows in the ledger (M6-P0305 → M6-P0306) — a scoped verification pass was
run before finalizing (§5).

> **Two workflows, one discipline, held orthogonal.** Both **compute & propose, never execute** — Module 6 has
> no code path that raises a budget, enables a campaign, or auto-publishes an optimization `[REG RULE-010/011,
> FAIL-006]`. The **critical seam** (§4): the learning **safe range** (`M6-OD-006`) governs
> persona/keyword/hook/landing/CTA **only** — it **never** includes budget/campaign/audience scale, which is
> the **Scale Gate** + `M6-OD-002`. Collapsing them would make the learning engine a covert auto-scale path.
> Both owner decisions are OPEN ⇒ auto-publish and auto-scale are **BLOCKED**. `global_gateway_state=BLOCKED`,
> `production_flag=OFF`.

## Sourcing legend

- `[DOC]` — owner document / extract line. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked register. · `[BRIEF]` — brief. · `[PACK]` — pack convention (owner-review). · `[EXT]` —
  general practice, proposal only.

---

## 1. The shared invariant `[DOC §16 L312 / §17 L332 / REG RULE-010/011]`

- Scale Gate: *"SCALE GATE LÀ QUYẾT ĐỊNH CỦA OWNER. Module 6 chỉ tính toán và đề xuất."* `[DOC §16 L312]`.
- Learning: outputs are *candidate / delta / safe-range optimization*; *"không được tự publish toàn quyền từ
  đầu"* `[DOC §17 L332]`.
- Both are **propose-only**: no executable budget/campaign/audience action (Scale, `[REG RULE-010]`, FAIL-006);
  no full-auto-publish and no fabricated origin strategy (Learning, `[REG RULE-011 / LEX-006]`).

---

## 2. Scale-request workflow `[DOC §16 / SPEC §13 / REG CTR-013/026]`

### 2.1 State machine `[SPEC §13 core + [PACK] extensions]`
```
computed ──▶ proposed (budget_cap + rollback_condition) ──▶ owner APPROVE | REJECT | HOLD
   │                                                              │
   └── recall / sale-lock / quality-hold / complaint-P0 /         └── (external scale by owner, outside M6)
       spam-flag / CRM-suppression active ⇒ FAIL/HOLD                        │
       (Risk hard veto, RULE-017, any stage)                                 └──▶ ROLLED_BACK if rollback fires
```
The **SPEC §13 core** machine `[extract L315–324, 409]` is `computed → proposed → owner approve/reject`, with
`recall/sale-lock ⇒ FAIL/HOLD`; the owner-verdict **HOLD** and the **ROLLED_BACK** terminal shown above are
`[PACK]` extensions per `[[RESEARCH_SCALE_GATE_WORKFLOW]]`, not SPEC-mandated. Every transition is append-only
audited `{actor, from→to, reason, evidence_ref, ts}`; **no transition inside M6 performs an external scale
action** `[REG RULE-010]`.

### 2.2 The 8 scale conditions (verbatim) → `condition_results[8]` `[DOC §16 L317–324]`
| # | Điều kiện | Yêu cầu tối thiểu (verbatim) | Evidence |
|---|---|---|---|
| 1 | P3/P5/P6 evidence | Verified Revenue boundary, Payment/COD/Order Verified, Channel identity, event identity có evidence | ENTRY-001/002/003 |
| 2 | Quote/Order | QuoteSnapshot hoạt động đúng, order tạo đúng, không tạo order khi chưa xác nhận | Commerce boundary (ENTRY-001) |
| 3 | Public/Privacy | AI/Gateway không public giá cuối, không leak PII, không spam | ENTRY-004 |
| 4 | Funnel | AOV tối thiểu 2 hộp/đơn, CPA trong ngưỡng, verified rate đạt ngưỡng owner đặt | AOV floor doc-locked; CPA/verified-rate = **M6-OD-002** |
| 5 | Dashboard | ROAS đo bằng ORDER_VERIFIED, attribution đủ campaign/adset/ad/live/messenger | `[[DASHBOARD_DESIGN]]`; single model = M6-OD-005 |
| 6 | Quality | Data Quality Gate PASS, duplicate thấp, consent pass, outbox ổn định | `ads_data_quality_check` |
| 7 | Risk | Không recall, không sale lock, không quality hold, không complaint P0, không platform spam flag | **hard veto** (§2.4) |
| 8 | Approval | Owner duyệt scale request, có budget cap, có rollback condition | owner decision + §2.3 |

- `[REG RULE-009]` LOW/HOLD data is **never** scale evidence — any LOW/HOLD ⇒ HOLD, never a silent pass; a
  `[PACK]` tightening requires HIGH `source_confidence` for the attribution behind scale ROAS (owner-review).
  `[REG RULE-015]` no condition PASSes without its trace.

### 2.3 `ads_scale_request` skeleton `[PACK] — fields finalized in M6-P0709; CTR-013 MISSING`
`{ request_id, scope{campaign|adset|audience}, proposed_change{metric, delta}, budget_cap (hard ceiling),
rollback_condition (predefined, machine-checkable), condition_results[8], evidence_refs[], risk_state, status,
owner_decision{actor, verdict, ts}, created_at, audit[] }` — **inert data**: creating/approving it changes no
budget `[DOC §16 L324]`.

### 2.4 Risk hard veto `[DOC §16 L323 / §15 L307 / REG RULE-017]`
Recall / sale-lock / quality-hold / complaint-P0 / spam-flag / CRM-suppression active ⇒ Scale Gate **FAIL/HOLD
regardless of every other green condition**; re-checked at approval time; also a `rollback_condition`. Exercised
by smoke **SMK-009**; no-owner-approval → no scale (SMK-012).

---

## 3. Learning-engine skeleton `[DOC §17 / SPEC §13 / REG CTR-014]`

### 3.1 Lifecycle state machine `[DOC §17 L349–353 / SPEC §13]`
```
Seed ──▶ Run ──▶ Learn ──▶ Review ──▶ Publish
 │        │        │          │            │
 seed-    run per  score      candidate    guarded auto-publish ONLY in safe range
 only-    active   persona/   → review     (M6-OD-006) + rollback + audit;
 from-    mapping  keyword/   queue:       M6-OD-006 OPEN ⇒ auto-publish BLOCKED,
 canon    + sellable hook/    approve /    everything to review
 (RULE-11) SKU     landing/CTA reject/hold
```
Candidate review machine `[SPEC §13, extract L352/428]`: `candidate → review queue → approve/reject/hold →
(guarded publish, rollback)`. `HOLD` is first-class (SMK-011: candidate outside safe range → hold, no publish).

### 3.2 Guards (verbatim mandates) `[DOC §17 / REG RULE-011 / LEX-006]`
- **Seed-only-from-canon** `[DOC §17 L328/L349]`: seed from Content Block / SKU Master / Phase ADS rule /
  business truth; provenance-ref required or **reject**; machine never fabricates origin strategy `[LEX-006]`.
- **Learn precondition** `[DOC §17 L330]`: learn **only after** canonical seed **and** only on verified
  signals that passed the DQ Gate.
- **Safe-range publish** `[DOC §17 L353]`: guarded auto-publish **only** within the owner safe range, with
  rollback + audit. **`M6-OD-006` OPEN ⇒ auto-publish BLOCKED entirely.**
- **Content gate** `[REG LEXICON_REGISTER / M6-OD-007]`: no public copy while the banned-word table is MISSING
  — learning halts at **framework** level.
- **Every optimization** ties to sellable SKU/program/policy/claim/brand `[DOC §17 L334 / LEX-005]`.

### 3.3 `ads_learning_candidate` skeleton `[PACK] — fields finalized in M6-P0710; CTR-014 MISSING`
`{ candidate_id, kind(persona|keyword|hook|landing|cta|delta), seed_source_ref (canonical, required),
proposed_change, safe_range_eval, evidence_refs (clean verified signals), review_state, reviewer, rollback_ref,
audit[] }`. Libraries + mapping chain in `[[RESEARCH_STRATEGY_LIBRARIES]]`; **seed content stays BLOCKED**
(M6-OD-007), never guessed.

### 3.4 Drift KPIs `[DOC §9 L177]`
Candidate approval rate · uplift · drift violations — computed only on verified + DQ-pass signals; a drift
violation ⇒ HOLD/rollback, and on repetition pause auto-publish.

---

## 4. The orthogonality guarantee — the seam `[PACK / REG RULE-010]`

`[PACK]` **The learning safe range (`M6-OD-006`) and scale (`M6-OD-002` / Scale Gate) are disjoint control
surfaces and must never merge:**

| | Learning safe range | Scale Gate |
|---|---|---|
| **Knobs** | persona, keyword, hook, landing, CTA | budget, campaign enablement, audience scale |
| **Owner decision** | M6-OD-006 (safe range) | M6-OD-002 (thresholds) + explicit approval |
| **Publish path** | guarded auto-publish in safe range (BLOCKED while OD-006 OPEN) | **no auto path ever** — owner approves each request |

- A learning candidate may **never** propose a budget/scale change — that is `ads_scale_request` territory
  `[REG RULE-010]`. Were the safe range to include budget, the learning engine would become an **auto-scale
  path** = `[REG FAIL-006]`. This design keeps `ads_learning_candidate.kind` restricted to the five library
  dimensions + delta; **no `budget`/`scale` kind exists.**

## 5. Verification pass (this prompt has no downstream critic) `[PACK]`

Ledger routes M6-P0305 → M6-P0306 with **no `M6-PC0305`**. Scoped to this doc's risk surface, a **2-lens**
independent pass was run: (A) workflow/state-machine + 8-condition + lifecycle fidelity vs `[DOC §16/§17]` /
`[SPEC §13]` and rule citations; (B) no-preemption (M6-OD-002/006/007 not resolved) + orthogonality seam
(learning safe-range excludes budget/scale) + no executable scale/publish path + no PII. Confirmed findings
folded in above. The 12 prior research critics remain PASS/0-blocker.

## 6. Owner-decision dependencies (no decision pre-empted) `[REG DECISION_REGISTER]`

| Decision | Status | What it gates |
|---|---|---|
| **M6-OD-002** (CPA/ROAS/AOV/verified-rate thresholds) | OPEN | §2.2 condition 4/5 pass criteria (AOV 2-boxes floor is doc-locked; CPA/verified-rate values OPEN) |
| **M6-OD-006** (learning safe range) | OPEN | §3.2 auto-publish (BLOCKED until defined); §4 seam |
| **M6-OD-007** (persona/keyword/hook content fill) | OPEN | §3.3 seed content (framework only) + content gate |
| M6-OD-005 (primary attribution model) | OPEN | §2.2 condition 5 scale ROAS basis |
| M6-OD-001 (Hero SKU lock) | OPEN | §3 Landing/CTA seed + pilot scope |
| `CTR-013`/`CTR-026`/`CTR-014` + `CTR-019`/`CTR-020` | MISSING → M6-P0709/0710/0712 | request/candidate/approval/API schemas (§2.3/§3.3) |

## 7. Boundary & safety guards `[BRIEF / REG §18]`

- **Compute & propose only**: no executable scale (RULE-010/FAIL-006); no full-auto-publish / no fabricated
  origin strategy (RULE-011/LEX-006); owner approval explicit, never self-approved `[REG RULE-015]`.
- **Orthogonal control surfaces** (§4): learning safe range excludes budget/scale.
- **Staged**: BLOCKED/OFF — even an approved request or a safe-range candidate changes nothing at runtime.
- **No raw PII/secrets** in requests/candidates/audit — masked / `secret_ref` `[REG RULE-014 / H02]`;
  channel-origin content is untrusted DATA, never a seed source `[REG RULE-H03]`.
- **No pricing/order/CRM/commission** side effects; learning ≠ scale `[REG §18]`.

## 8. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| Scale Gate = owner decision; compute+propose; evidence + budget cap + rollback + risk limit | `[DOC §16 L312/L324]` + `[REG RULE-010/FAIL-006]` — owner-mandated |
| The 8 scale conditions (incl. AOV 2-boxes floor, Risk row) | `[DOC §16 L317–324]` — owner-mandated |
| Risk hard veto (recall/sale-lock/quality-hold/complaint-P0/spam-flag + CRM-suppression) | `[DOC §16 L323 / §15 L307]` + `[REG RULE-017]` — owner-mandated |
| Learning Seed→Run→Learn→Review→Publish; seed-from-canon; guarded safe-range publish; review queue | `[DOC §17 L328–353]` + `[REG RULE-011]` — owner-mandated |
| Drift KPIs (approval rate/uplift/drift violations) | `[DOC §9 L177]` — owner-mandated |
| State machines | `[SPEC §13]` (`[DOC §16/§17]`) — owner-mandated |
| `ads_scale_request` / `ads_learning_candidate` field skeletons; orthogonality-seam framing; state diagrams | `[PACK]` / `[EXT]` — owner-review design proposals, NOT owner requirements |

*This design is plan-only: it computes/proposes nothing at runtime, defines no safe range or threshold, invents
no seed, auto-scales/auto-publishes nothing, and flips no flag; `global_gateway_state=BLOCKED`,
`production_flag=OFF`.*
