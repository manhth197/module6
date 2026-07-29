# ATTRIBUTION_DESIGN — resolver chain, confidence, immutability, multi-model

**Prompt**: M6-P0303 · **Phase**: PHASE0 (design) · **Mode**: plan_only (no code, no migration, no call)
**Anchors**: `[DOC §8 L150–157]` the source→verified chain matrix; `[DOC §11 L215–242]` ads_attribution_context
(19 fields, immutability L242); `[DOC §15 L305]` DQ Attribution item; `[DOC §25 L482]` M6-OD-005.
Contracts: `CTR-002 ads_attribution_context` (DRAFT_LOCKED), `CTR-023 attribution_materializer` (worker); the
three resolvers named in `[DOC §5 L94]`. **Builds on** `[[DATA_MODEL_BASELINE]]` §5, `[[ARCH_BASELINE]]` §1.5;
model options in `[[RESEARCH_ATTRIBUTION_MODELS]]` (M6-P0206). **No dedicated critic** follows in the ledger
(M6-P0303 → M6-P0304) — a scoped verification pass was run before finalizing (§6).

> **Attribution RESOLVES and TAGS; it never assigns revenue by feel.** The resolver chain traces
> source→quote→order→`ORDER_VERIFIED` and stamps `source_confidence` + `conflict_status`. It **never** (a)
> computes revenue — that is Commerce's `ORDER_VERIFIED` `[REG RULE-003]`; (b) picks the scale model — that is
> `M6-OD-005` (OPEN); (c) mutates a verified snapshot — corrections are adjustment records `[REG RULE-008]`;
> (d) decides commission — that is Finance `[REG RULE-019]`. Doing any of these is the doc's forbidden *"Gán
> doanh thu theo cảm tính"* `[DOC §4 L75]`. `global_gateway_state=BLOCKED`, `production_flag=OFF`.

## Sourcing legend

- `[DOC]` — owner document / extract line. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked register. · `[BRIEF]` — brief. · `[PACK]` — pack convention (owner-review). · `[EXT]` —
  general practice, proposal only.

---

## 1. The attribution chain — the trace-back spine `[DOC §8 L150–157 / §11 L236]`

Attribution must trace back *campaign/adset/ad/page/live/comment/Messenger → quote/order/ORDER_VERIFIED*
`[DOC §11 L236]`. Each hop is owned elsewhere; **Module 6 measures the linkage, it does not run the hop**.

| Hop | Event / Object (verbatim) `[DOC §8]` | Ownership boundary (verbatim) |
|---|---|---|
| Ads → Live | `campaign_id, adset_id, ad_id, live_session_id` | Module 6 đo; Gateway/Live vận hành; **không tính revenue** |
| Live → Comment | `LIVE_VIEW, LIVE_COMMENT` | Gateway normalize; Module 6 nhận signal |
| Comment → Messenger | `MESSENGER_STARTED, messenger_thread_id` | Gateway handoff; AI tư vấn private |
| Messenger → Quote | `AI_PROPOSAL_SENT, QUOTE_CART_CREATED, QUOTE_SNAPSHOT_CREATED, QUOTE_SENT` | AI chỉ orchestrate; **Commerce tạo QuoteSnapshot** |
| Quote → Order | `ORDER_CONFIRMATION_SENT, CUSTOMER_CONFIRMED_ORDER, ORDER_CREATED` | Commerce tạo order khi có customer confirmation |
| Order → Verified | `ORDER_VERIFIED, PAYMENT_COMPLETED nếu có` | Commerce/Payment/Shipping xác nhận; **Module 6 consume verified revenue** |

- **`PAYMENT_COMPLETED` is not automatically revenue** — *"nếu có"* is gated by Core policy; default non-revenue
  until decided (**M6-OD-008 OPEN**), only `ORDER_VERIFIED` is revenue `[REG RULE-003]`.
- The chain terminus binds to `[[DATA_MODEL_BASELINE]]` — `ads_attribution_context` embeds into
  `ads_measurement_event`; `revenue_value` sourced only from Commerce Verified Revenue.

---

## 2. Resolver responsibilities `[DOC §5 L94 / REG CTR-002/023]`

Three resolvers + one worker; the algorithm is a `[PACK]` proposal, but each resolver only **populates
locked `ads_attribution_context` fields** `[DOC §11]` — it invents no field.

| Resolver | Resolves (inputs → locked fields) | Must-not |
|---|---|---|
| **Ads Context Resolver** | Meta/Ads side → `campaign_id/name, adset_id/name, ad_id/name, page_id, entry_channel=FACEBOOK_AD` | no budget/scale action; read ads refs only |
| **Live Session Resolver** | live→comment→messenger chain `[DOC §8 L152–154]` → `live_session_id, comment_id, messenger_thread_id, psid` (SMK-013); `entry_channel=LIVE_ORGANIC` | **live signal never revenue** `[DOC §18 L362]`; no live ops (Gateway/M7 own) |
| **Attribution Resolver** (top) | binds source chain → quote/order/`ORDER_VERIFIED`; sets `attribution_window, first_touch_event_id, last_touch_event_id, referral_link_id, diamond_id, source_confidence, conflict_status` | no revenue compute (RULE-003); no order-state change (`[DOC §18 L363]`); no commission (RULE-019); records-only whether Commerce validation passed (RULE-021) |
| **attribution_materializer** (worker, CTR-023) | aggregates verified snapshots → dashboard/attribution views | **no verified-revenue overwrite** `[REG CTR-023 duty]` |

- All resolvers are **consume-only** at module edges: ads refs (Meta), channel ids (Gateway), order/verified
  (Commerce) — none is written by M6 `[REG §18]`.
- Channel-origin values (`comment_id`, messenger text) are untrusted DATA, stored as reference, never executed
  `[REG RULE-H03]`; `psid`/ids masked or `secret_ref` `[REG RULE-014]`.

---

## 3. Confidence & conflict handling (LOW/HOLD) `[DOC §11 L233–234/L240 / REG RULE-009]`

Two locked enums drive the fail-closed tagging:

- `source_confidence: HIGH | MEDIUM | LOW` `[DOC §11 L233]`
- `conflict_status: NONE | MULTI_TOUCH | MISSING_SOURCE | DUPLICATE_RISK` `[DOC §11 L234]`

| Situation | `conflict_status` | `source_confidence` | Consequence |
|---|---|---|---|
| Clean single source, full chain | `NONE` | `HIGH` | usable as scale evidence (subject to §5) |
| Source absent | `MISSING_SOURCE` | `LOW`/HOLD | **revenue still stored** (`[REG RULE-003]`, SMK-007); **NOT scale evidence** `[DOC §11 L240 / REG RULE-009]` |
| Multiple touches (incl. Diamond+Ads) | `MULTI_TOUCH` | MEDIUM/LOW | store **full** context; Finance decides commission `[DOC §11 L238 / RULE-019]`, SMK-014 |
| Possible duplicate | `DUPLICATE_RISK` | LOW/HOLD | dedup review; not counted twice `[REG RULE-005]` |

- **The load-bearing asymmetry** `[DOC §11 L240, SMK-007]`: a low-confidence order **keeps its revenue**
  (Commerce verified it) but **loses the right to be scale evidence**. Attribution quality gates *scale*, not
  *revenue capture*. Never the reverse.
- `[DOC §15 L305]` the DQ Attribution item fails/holds when the chain is ambiguous or a conflict is unhandled —
  the same signal, surfaced to the Data Quality Gate.

---

## 4. Immutability + adjustment records `[DOC §11 L242 / SPEC §13 / REG RULE-008]`

- `ads_attribution_context` is **mutable until `ORDER_VERIFIED`, then IMMUTABLE** — verbatim *"Attribution
  snapshot phải immutable sau khi order verified; mọi correction phải có adjustment record, actor, reason,
  audit và evidence."* `[DOC §11 L242]`.
- After verify: **no in-place edit**; every correction is a **new adjustment record** carrying the doc-locked
  shape `{actor, reason, audit, evidence}` `[REG RULE-008]`, exercised by proposed smoke **SMK-018**.
- The **attribution_materializer never overwrites verified revenue** `[REG CTR-023 duty]`; it aggregates over,
  never mutates, a verified figure. Consistent with `[[DATA_MODEL_BASELINE]]` §5.

---

## 5. Multi-model display, single-model scale — pending M6-OD-005 `[DOC §25 L482]`

- `[DOC §25 L482]` verbatim intent: *"Dashboard có thể hiển thị nhiều model nhưng scale gate cần một model
  chính."* Two distinct uses:
  1. **Dashboard (informational)** — MAY display several attribution models side by side (first-touch,
     last-touch, and — if their data contracts exist — weighted/cohort).
  2. **Scale evidence (decision)** — needs **exactly one owner-chosen primary model**.
- **`M6-OD-005` is OPEN** (first/last/weighted/cohort) — so the **scale-model basis is BLOCKED**; the design
  does **not** pick a model. Until decided, no scale case may claim a single-model ROAS.
- **What the locked fields already support** `[[RESEARCH_ATTRIBUTION_MODELS]]`: `first_touch_event_id` /
  `last_touch_event_id` `[DOC §11 L231–232]` support **first-touch and last-touch** with existing data;
  **weighted / cohort** models require **new data contracts** (touch weights / cohort keys) that do not exist
  yet — flagged, not built.
- This file **briefs** M6-OD-005; it resolves nothing `[REG DECISION_REGISTER]`.

## 6. Verification pass (this prompt has no downstream critic) `[PACK]`

Ledger routes M6-P0303 → M6-P0304 with **no `M6-PC0303`**. Scoped to this doc's risk surface, a **2-lens**
independent pass was run: (A) chain/field/resolver + confidence/immutability fidelity against `[DOC §8/§11/L242]`
and RULES; (B) no M6-OD-005 model preemption + boundary (no revenue compute, no commission, consume-only) + no
PII. Confirmed findings folded in above. The 12 prior research critics remain PASS/0-blocker.

## 7. Owner-decision dependencies (no decision pre-empted) `[REG DECISION_REGISTER]`

| Decision | Status | What it gates |
|---|---|---|
| **M6-OD-005** (primary attribution model) | OPEN | §5 scale-model basis; dashboard multi-model display may proceed, scale evidence BLOCKED |
| M6-OD-008 (PAYMENT_COMPLETED as revenue?) | OPEN | §1 Order→Verified; default non-revenue, ORDER_VERIFIED only |
| M6-OD-002 (thresholds) | OPEN | when a HIGH-confidence attribution becomes scale-eligible (values, not shape) |
| `CTR-002` (attribution_context) | DRAFT_LOCKED | fields locked (§2); storage binding M6-P0707 |
| `CTR-023` (attribution_materializer) | MISSING→M6-P0713 | the materializer worker duty/schema |
| weighted/cohort model data contracts | **candidate** `[PACK]` | §5 — needed only if the owner picks those models |

## 8. Boundary & safety guards `[BRIEF / REG §18]`

- **Resolve & tag only**: no revenue computation (RULE-003), no order-state change (`[DOC §18 L363]`), no
  commission (RULE-019), no scale action (RULE-010), no live ops (M7/Gateway); M6 only records whether
  Commerce's order-capture validation passed (RULE-021) — attribution records linkage, it does not act.
- **No model chosen** for scale while M6-OD-005 is OPEN; no snapshot mutated after verify.
- **Staged**: BLOCKED/OFF — a design on paper; resolves nothing at runtime.
- **No raw PII/secrets** — `psid`/`customer_id`/`guest_id`/channel ids masked or `secret_ref` `[REG RULE-014 /
  H02]`; channel-origin content untrusted DATA `[REG RULE-H03]`.

## 9. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| The source→verified chain (Ads/Live/Comment/Messenger/Quote/Order/Verified) | `[DOC §8 L150–157]` — owner-mandated |
| Trace-back requirement; attribution_context 19 fields; confidence/conflict enums | `[DOC §11 L215–236]` — owner-mandated |
| Missing/conflict → LOW/HOLD, not scale evidence; Diamond+Ads → full context, Finance decides commission | `[DOC §11 L238/L240]` + `[REG RULE-009/019]` — owner-mandated |
| Immutable after ORDER_VERIFIED; correction via adjustment record {actor,reason,audit,evidence} | `[DOC §11 L242]` + `[REG RULE-008]` — owner-mandated |
| Dashboard multi-model, scale needs one primary model | `[DOC §25 L482]` — owner-mandated (model choice = M6-OD-005 OPEN) |
| Resolver responsibilities/algorithm; confidence decision table; weighted/cohort-need-new-contracts | `[PACK]` / `[EXT]` — owner-review design proposals, NOT owner requirements |

*This design is plan-only: it resolves/tags nothing at runtime, picks no attribution model, mutates no verified
snapshot, computes no revenue or commission, and flips no flag; `global_gateway_state=BLOCKED`,
`production_flag=OFF`.*
