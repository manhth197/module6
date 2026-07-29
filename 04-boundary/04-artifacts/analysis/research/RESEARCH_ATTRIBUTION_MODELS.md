# RESEARCH_ATTRIBUTION_MODELS — briefing for owner decision M6-OD-005

**Prompt**: M6-P0206 · **Phase**: PHASE0_RESEARCH · **Mode**: analysis_only (desk research; **briefs, does not
decide**, M6-OD-005)
**Anchors**: `M6-OD-005` `[REG DECISION_REGISTER]` *"Attribution model chính thức: first touch, last touch,
weighted hay cohort? | Dashboard có thể hiển thị nhiều model nhưng scale gate cần một model chính"* `[DOC §25
extract line 482]`; `M6-CTR-002 ads_attribution_context` (DRAFT_LOCKED, 19 fields, SPEC §10.2 / doc §11); slice
**M6.2E** (out_of_scope: *"attribution model final choice (M6-OD-005: multi-model display, single-model scale
evidence pending owner)"*).
**Critic**: M6-PC0206 (BOUNDARY_ADVERSARY) red-teams this file next.

> This file **compares options and states their data needs** so the owner can choose. It does **not** pick a
> model — that is M6-OD-005. `global_gateway_state=BLOCKED`, `production_flag=OFF` unchanged.

## Sourcing legend (acceptance: every externally-sourced claim labeled)

- `[DOC]` — owner document / extract line. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked pack register. · `[BRIEF]` — context brief. · `[PACK]` — pack convention (owner-review).
- `[EXT]` — general attribution/marketing engineering knowledge, **descriptive, proposal only**.

**Doc/reg anchors**: `[DOC §25 L482]` multi-model display allowed, scale gate needs **one primary** model;
`[DOC §11 L236]` *"Attribution phải truy ngược được từ campaign/adset/ad/page/live/comment/Messenger tới
quote/order/ORDER_VERIFIED"*; `[REG RULE-008]` attribution snapshots immutable once verified; `[REG RULE-009]`
missing/conflicting source ⇒ LOW/HOLD, **never** scale evidence; `[REG RULE-010]` scale is an owner decision;
`[REG RULE-019]` Diamond commission is Finance-owned, not Ads.

Available fields to work from (`ads_attribution_context`, `[REG SPEC §10.2]`, 19): campaign/adset/ad ids+names,
page_id, live_session_id, comment_id, messenger_thread_id, psid, referral_link_id, diamond_id, entry_channel,
**attribution_window**, **first_touch_event_id**, **last_touch_event_id**, source_confidence, conflict_status.

---

## 1. What the doc already fixes `[DOC §25 L482]`

- The **dashboard may show multiple models** (comparison/insight).
- The **scale gate must use exactly one primary model** — you cannot gate a budget increase on ambiguous
  multi-model ROAS.
- `[REG RULE-009]` only **HIGH-confidence, non-conflicting** attribution counts as scale evidence; `[REG
  RULE-008]` a verified order's attribution snapshot is **immutable** (re-attribution = audited adjustment).

So M6.2E builds **multi-model display**; M6-OD-005 selects the **single primary** used for scale evidence.

---

## 2. Model comparison `[EXT]` (descriptive — not a recommendation)

| Model | Credit assignment | Strength | Weakness / bias | Best for |
|---|---|---|---|---|
| **First touch** | 100% to the **first** ad interaction | rewards discovery/acquisition; simple, stable | ignores nurturing & closing; over-credits top-of-funnel | valuing acquisition channels |
| **Last touch** | 100% to the **last** interaction before conversion | simple; closest to platform-reported conversions; easy to reconcile | ignores discovery; over-credits retargeting/branded | closing/retargeting efficiency |
| **Weighted (multi-touch)** — linear / time-decay / position-based | credit **distributed** across the touch path | most "fair"; sees the whole journey | needs the **full ordered path**; harder to reconcile with platform numbers; parameter choices are subjective | balanced journey analysis |
| **Cohort** | groups conversions by **acquisition cohort** and tracks value over time | LTV/retention lens; fits Phase-3 growth (repeat, Diamond, CLV) | not a per-conversion credit model; needs **longitudinal** data; slow to read | lifecycle/retention value, not per-campaign credit |

---

## 3. Data requirements vs the locked `ads_attribution_context` fields `[REG SPEC §10.2]`

| Model | Needs | Available in the contract today? |
|---|---|---|
| **First touch** | `first_touch_event_id` + that touch's campaign/adset/ad + `entry_channel` | **YES** — `first_touch_event_id` is already a field ✅ (lowest data cost) |
| **Last touch** | `last_touch_event_id` + that touch's campaign/adset/ad | **YES** — `last_touch_event_id` is already a field ✅ (lowest data cost) |
| **Weighted** | the **full ordered sequence** of touches between first and last, per identity, within `attribution_window` | **PARTIAL** — the contract stores only first/last touch ids, **not** the full path ⇒ a **data gap**: needs an ordered touch-event series (new structure/contract) |
| **Cohort** | acquisition-cohort assignment + **time-series** verified revenue per cohort (guest→customer→orders over time) | **GAP** — different data shape (cohort tables + longitudinal identity from M6-P0202); overlaps Phase-3 growth KPIs (CLV proxy, repeat) |

`[PACK]` **Factual readiness note (not a recommendation):** first-touch and last-touch are directly supported by
existing fields; **weighted and cohort each require additional data contracts** beyond the current 19 fields.
The owner should weigh this data cost when choosing under M6-OD-005 — but the choice remains the owner's.

`[EXT]` `attribution_window` bounds every model's look-back; `source_confidence`/`conflict_status` gate whether
a given attribution is usable as scale evidence (§4).

---

## 4. Implications for scale-gate evidence `[DOC §25 L482 / REG RULE-008/009/010]`

- The primary model determines **which campaigns/adsets get credited** → **which get proposed for scale**.
  First-touch shifts budget toward acquisition; last-touch toward retargeting/closing. This is a real
  **budget-allocation consequence**, which is exactly why M6-OD-005 is an **owner** decision, not a pack one.
- Only attributions with `source_confidence = HIGH` and `conflict_status = NONE` may count as scale evidence
  `[REG RULE-009]`; LOW/HOLD/conflicting attributions are excluded (never inflate the scale case).
- The scale ROAS/CPA/AOV shown to the Scale Gate must be computed under the **single primary** model `[DOC
  L482]`, even if the dashboard also shows the others for insight.
- `[REG RULE-008]` a verified order's attribution is immutable; switching the primary model **later** re-computes
  going-forward and requires audited adjustments for historical snapshots — a migration cost to flag.
- `[REG RULE-010]` attribution feeds a scale **proposal**; it never auto-scales.

---

## 5. Boundary guards `[BRIEF / REG §18]`

- M6 **measures** attribution; it never tweaks attribution to favor a campaign `[REG RULE-008/009]`, and never
  auto-scales `[REG RULE-010]`.
- **Diamond/referral** attribution may be recorded (`diamond_id`, `referral_link_id`) but **commission is
  Finance-owned** `[REG RULE-019]` — no cohort/LTV output computes commission.
- **No raw PII**: `psid` and identity fields are references, masked in logs/evidence `[REG RULE-014]`.
- Channel-origin identifiers are untrusted DATA `[BRIEF rule 6]`.

## 6. Owner-decision dependencies (explicit list — acceptance requirement)

| Dependency | Status | What it gates |
|---|---|---|
| **M6-OD-005** (primary attribution model for scale evidence) | **OPEN** `[REG]` | **this file briefs it**; blocks M6.2E design finalization + M6.2G scale evidence |
| If owner picks **weighted** or **cohort**: new data contracts (ordered touch-path / cohort tables) | **conditional candidate** `[PACK]` | additional CTR/data requirements beyond the 19-field context |
| `attribution_window` value + confidence thresholds for scale eligibility | **candidate** `[PACK]` — links M6-OD-002 | RULE-009 scale-evidence gating (§4) |
| `M6-CTR-002` (ads_attribution_context) | DRAFT_LOCKED `[REG]` | the fields available today (§3) |
| `M6-OD-004` (connector) | **OPEN** `[REG]` | reconciliation of M6's model vs platform-reported attribution |

`[PACK]` This research records these and **briefs** M6-OD-005; it resolves nothing. Where M6.2E/M6.2G needs the
decision, the affected leg is marked BLOCKED, not assumed.

## 7. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| Multi-model display allowed; scale gate uses one primary model | `[DOC §25 line 482]` — owner-mandated |
| Attribution must trace campaign…→ORDER_VERIFIED; immutable once verified; low/conflict never scale evidence | `[DOC §11 line 236]` + `[REG RULE-008/009]` — owner-mandated |
| `ads_attribution_context` 19 fields incl. first/last_touch_event_id, attribution_window | `[REG SPEC §10.2 / DOC §11]` — owner-mandated (DRAFT_LOCKED) |
| Model comparison table; per-model data needs; readiness asymmetry; weighted/cohort data gaps; scale/budget implications | `[EXT]` / `[PACK]` — descriptive briefing, **NOT owner requirements or a recommendation of a specific model** |

*Nothing in this file flips a gate or a flag, and it selects no model; `global_gateway_state=BLOCKED`,
`production_flag=OFF`.*
