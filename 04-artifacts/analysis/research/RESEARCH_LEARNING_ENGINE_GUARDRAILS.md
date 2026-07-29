# RESEARCH_LEARNING_ENGINE_GUARDRAILS — guarded learning for doc §17

**Prompt**: M6-P0209 · **Phase**: PHASE0_RESEARCH · **Mode**: analysis_only (desk research; design proposal)
**Anchors**: `[DOC §17 extract lines 325–353]` ADS Strategy Input Pack & Learning Engine; `[DOC §9 line 177]`
drift KPIs; `M6-CTR-014 ads_learning_candidate` (→M6-P0710), `M6-CTR-020 POST /api/admin/ads/learning-
candidates` (→M6-P0712); slice **M6.2H**; owner decisions **M6-OD-006** (safe range) and **M6-OD-007** (content
fill). `[REG RULE-011]` guarded learning.
**Critic**: M6-PC0209 (BOUNDARY_ADVERSARY) red-teams this file next.

> **The learning engine is the highest runaway-risk component.** Every stage is **fail-closed**: no canonical
> seed ⇒ no learn; unclean/unverified signal ⇒ no learn; outside the safe range ⇒ review, not publish;
> `M6-OD-006` undefined ⇒ **no auto-publish at all**; banned-word/claim table missing ⇒ framework only, **no
> public copy**. `global_gateway_state=BLOCKED`, `production_flag=OFF` unchanged (staged; no real publish).

## Sourcing legend (acceptance: every externally-sourced claim labeled)

- `[DOC]` — owner document / extract line. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked pack register. · `[BRIEF]` — context brief. · `[PACK]` — pack convention (owner-review).
- `[EXT]` — general engineering/ML-ops practice, **proposal only**.

**Doc anchors**: `[DOC §17 L328]` seed from *Content Block canonical, SKU Master, Phase ADS rule, business
truth*; `[DOC §17 L330]` *"chỉ được học sau khi có seed chuẩn và dữ liệu verified business signal đủ sạch"*;
`[DOC §17 L332]` outputs = *candidate, delta recommendation, safe-range optimization; không được tự publish
toàn quyền từ đầu*; `[DOC §17 L334]` every optimization tied to sellable SKU/program/Golden Hour/24-7 policy/
public claim/brand wording; `[DOC §17 L349–353]` Seed→Run→Learn→Review→Publish (L353 *"Guarded auto-publish
trong safe range, có rollback và audit"*); `[DOC §9 L177]` *Candidate approval rate, uplift, drift violations*.
Rules: `[REG RULE-011]` (guarded learning), `[REG LEX-006 / doc §4 L80]` (no fabricated origin strategy / no
full auto-publish), `[REG LEXICON_REGISTER]` (banned-word table MISSING → M6-OD-007, no public copy).

---

## 1. Lifecycle: Seed → Run → Learn → Review → Publish `[DOC §17 L349–353]`

| Stage | Doc mandate | Guardrail |
|---|---|---|
| **Seed** (L349) | fill the six libraries from Content Block/SKU/Rule already locked; machine never invents origin strategy | provenance-enforced (§2) |
| **Run** (L350) | run acquisition/retargeting per the **active mapping** and **sellable SKU** only | no run on unmapped/unsellable |
| **Learn** (L351) | read effective signals; score persona/keyword/hook/landing/CTA | **only after seed + only clean verified signals** (§2) |
| **Review** (L352) | candidates go to a **review queue**; owner/marketing approve/reject/hold | default path; no bypass (§3) |
| **Publish** (L353) | **guarded auto-publish only within the safe range, with rollback + audit** | safe range = M6-OD-006 (§4) |

---

## 2. Seed-only-from-canon enforcement `[DOC §17 L328/L330/L349 / REG RULE-011]`

- The six libraries (Persona / Behavior / Keyword / Negative Keyword / Creative Hook / Landing-CTA) may be
  seeded **only** from canonical sources `[DOC L328]`; the machine **never fabricates origin strategy** `[DOC
  L349, REG LEX-006]`.
- `[PACK]` **Provenance enforcement**: every library entry carries a `seed_source_ref` (Content Block id / SKU
  Master id / Phase ADS rule id / business-truth ref). An entry lacking a canonical provenance is **rejected**
  — fail-closed, not "flagged".
- **Learn precondition** `[DOC L330]`: the Learn/scoring stage runs **only after** the canonical seed exists
  **and** consumes **only** verified business signals that passed the Data Quality Gate. No seed ⇒ no learn;
  unclean/unverified signal ⇒ excluded from learning. (This is the M6.2H "Learning-input precondition" leg.)
- `[DOC L334]` every optimization must tie to a **sellable SKU + program + Golden Hour/24-7 policy + public
  claim + brand wording** — an optimization not anchored to all of these is invalid.

---

## 3. Review queue states `[DOC §17 L352 / REG CTR-014]`

`[EXT] proposed candidate lifecycle` (fields finalized in M6-P0710):

`CANDIDATE → (owner/marketing review) APPROVED | REJECTED | HOLD → APPROVED then PUBLISHED (only within safe
range, §4) | else remains queued`

`ads_learning_candidate` `[EXT] shape`: `{ candidate_id, kind (persona|keyword|hook|landing|cta|delta),
seed_source_ref, proposed_change, safe_range_eval, evidence_refs (clean verified signals), review_state,
reviewer, rollback_ref, audit[] }`.

- **Default = review-queue-only** `[DOC L332 "không được tự publish toàn quyền từ đầu"]`; the machine has **no
  full-auto-publish path**.
- `HOLD` is a first-class state (owner may park a candidate) — exercised by smoke **M6-SMK-011** (*candidate
  outside safe range → hold review, không publish*) `[REG]`.

---

## 4. Safe-range publish + rollback `[DOC §17 L353 / REG M6-OD-006, RULE-011]`

- **Guarded auto-publish is permitted ONLY within the owner-defined safe range**, and **only** with **rollback
  + audit** `[DOC L353]`. Anything outside the safe range → review queue (§3), never auto-published.
- **`M6-OD-006` is OPEN**, so the safe range is undefined ⇒ **auto-publish is BLOCKED entirely**; every
  candidate goes to review until the owner defines it (M6.2H "No auto-publish" leg) `[REG]`.
- **Rollback** `[DOC L353]`: a published candidate that breaches its bound or a drift threshold (§5) is
  **auto-reverted**, with an audit record; the rollback condition is stored **with** the candidate (not
  improvised).
- **Content gate** `[REG LEXICON_REGISTER, M6-OD-007]`: no candidate may generate **public ad copy** while the
  banned-word / claim table is MISSING — learning halts at **framework** level (no public copy), independent of
  the safe range.

---

## 5. Drift detection `[DOC §9 L177]`

Line 177 KPIs — *Candidate approval rate, uplift, **drift violations*** — are the guardrail signals:

- **Candidate approval rate** `[EXT]`: falling approval rate ⇒ the engine is proposing worse candidates ⇒
  tighten the gate / investigate seed quality.
- **Uplift** `[EXT]`: measured effect of published candidates vs baseline (verified-signal-based); negative
  uplift ⇒ rollback trigger.
- **Drift violations** `[DOC L177]`: candidates that would exceed the safe range, or performance drifting
  outside expected bounds; a drift violation ⇒ **HOLD / rollback** and, on repetition, **pause auto-publish**.
- All three computed **only from verified business signals that passed DQ** `[DOC §9 L177 "Verified business
  signals + data quality pass"]` — drift is never measured on dirty data.

## 6. What **M6-OD-006** needs to define the safe range (decidability)

`[PACK]` To make the safe range decidable, the owner must fix (each a question, not a proposed answer):

1. **Which knobs** auto-publish may touch (e.g. keyword add/remove, hook selection, landing/CTA mapping) —
   **explicitly excluding** budget/scale (those are the Scale Gate + M6-OD-002, never the learning safe range).
2. **Bounds per knob** (max delta, allowed value sets, min sample/uplift before publish).
3. **Eligibility** — only canonical-seeded, already-approved SKUs/personas.
4. **Rollback triggers** — the drift/uplift thresholds that auto-revert (§5).
5. **Who may widen the safe range** (owner/marketing authority).
6. **Is auto-publish enabled for pilot at all?** Default until decided: **off / review-only**.

## 7. Boundary & safety guards `[BRIEF / REG §18]`

- Outputs are **candidate / delta / safe-range optimization** only — **never** full auto-publish `[REG RULE-011
  / LEX-006]`; machine never fabricates origin strategy.
- **No public ad copy** while the banned-word/claim table is missing `[REG LEXICON_REGISTER / M6-OD-007]`.
- **Staged**: `production_flag=OFF` ⇒ no real publish, even for a safe-range candidate.
- No pricing/order/CRM/commission side effects; no scale action (learning ≠ scale) `[REG §18]`.
- **No raw PII** in candidates/signals/audit `[REG RULE-014]`; channel-origin content (comments, ad copy) is
  untrusted **DATA** `[BRIEF rule 6]` — never a seed source and never an instruction.

## 8. Owner-decision dependencies (explicit list — acceptance requirement)

| Dependency | Status | What it gates |
|---|---|---|
| **M6-OD-006** (safe range) | **OPEN** `[REG]` | all guarded auto-publish; **this file makes it decidable** (§6); until then auto-publish BLOCKED |
| **M6-OD-007** (content fill / Content Block 20 SKU lock + banned-word table) | **OPEN** `[REG]` | whether libraries fill with real content / any public copy (§4 content gate) |
| `M6-CTR-014` (ads_learning_candidate) | `MISSING` → **M6-P0710** `[REG]` | candidate object/states (§3); needed before **M6.2H** |
| `M6-CTR-020` (learning-candidates API) | `MISSING` → **M6-P0712** `[REG]` | candidate submission API |
| Drift/uplift/approval-rate thresholds | **candidate** `[PACK]` — links M6-OD-002 family | §5 rollback triggers |

`[PACK]` This research records these; it resolves none. Where a build leg needs one, the affected M6.2H leg is
marked BLOCKED, not assumed.

## 9. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| Seed from canon only; machine never fabricates origin strategy | `[DOC §17 L328/L349]` + `[REG RULE-011/LEX-006]` — owner-mandated |
| Learn only after seed + only on clean verified signals (DQ pass) | `[DOC §17 L330]` — owner-mandated |
| Outputs = candidate/delta/safe-range; no full auto-publish; review queue approve/reject/hold | `[DOC §17 L332/L352]` + `[REG RULE-011]` — owner-mandated |
| Guarded auto-publish only within safe range, with rollback + audit | `[DOC §17 L353]` — owner-mandated |
| Every optimization tied to sellable SKU/program/policy/claim/brand | `[DOC §17 L334]` — owner-mandated |
| Drift-violation / approval-rate / uplift KPIs on verified+DQ-pass signals | `[DOC §9 L177]` — owner-mandated |
| Candidate lifecycle/field shape; provenance-ref enforcement; drift thresholds; safe-range parameterization | `[EXT]` / `[PACK]` — owner-review proposals, NOT owner requirements |

*Nothing in this file flips a gate or a flag, and it publishes nothing; `global_gateway_state=BLOCKED`,
`production_flag=OFF`.*
