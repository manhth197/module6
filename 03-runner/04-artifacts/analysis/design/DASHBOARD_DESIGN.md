# DASHBOARD_DESIGN — dashboard KPIs + data-quality layer

**Prompt**: M6-P0304 · **Phase**: PHASE0 (design) · **Mode**: plan_only (no code, no migration, no query run)
**Anchors**: `[DOC §14 L280–295]` = `[REG MONITORING_REGISTER]` the 14 locked KPIs (formulas locked, thresholds
OPEN); `[DOC §15 L299–308]` Data Quality Gate (8 items); `[DOC §9 L169]` Data Mart support-view. Contracts:
`CTR-015 Dashboard KPI contract` (DRAFT_LOCKED formulas, thresholds M6-OD-002), `CTR-018 GET
/api/admin/ads/dashboard`. **Builds on** `[[DATA_MODEL_BASELINE]]`, `[[ATTRIBUTION_DESIGN]]`,
`[[RESEARCH_DASHBOARD_DATA_QUALITY]]` (M6-P0207). **No dedicated critic** follows in the ledger (M6-P0304 →
M6-P0305) — a scoped verification pass was run before finalizing (§6).

> **A dashboard that cannot be prettied with unverified data.** Verified-only revenue is enforced
> **structurally at the query layer** — every revenue metric's *definition* keys on `ORDER_VERIFIED`, so no
> query path can sum quote/draft/unpaid `[DOC §4 L78 forbidden: "Làm đẹp dashboard bằng dữ liệu chưa
> verified"]`. Data-quality status **propagates worst-first** onto every metric; a metric with no source trace
> is a DQ **FAIL** `[DOC §15 L308]`. The data mart is **read-only support view** — never a trigger owner `[REG
> RULE-012]`. Thresholds are **M6-OD-002 (OPEN)** — no alert value is invented. `global_gateway_state=BLOCKED`,
> `production_flag=OFF`.

## Sourcing legend

- `[DOC]` — owner document / extract line. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked register. · `[BRIEF]` — brief. · `[PACK]` — pack convention (owner-review). · `[EXT]` —
  general practice, proposal only.

---

## 1. The 14 locked metrics + source trace `[DOC §14 L282–295 / REG MONITORING_REGISTER]`

Formula/source and note columns are **verbatim**; the **source trace** (which locked object/field the metric
resolves from) and **rev?** (verified-revenue-bearing) columns are `[PACK]` derivations for the query layer.
Revenue enforcement in §2, DQ propagation in §3.

| # | Chỉ số | Công thức / nguồn (verbatim) | Ghi chú (verbatim) | Source trace `[PACK]` | rev? |
|---|---|---|---|---|---|
| 1 | Ads Spend | Từ Ads platform / approved spend import | Phải có campaign/adset/ad mapping | approved spend import (external), keyed by `ads_attribution_context` campaign/adset/ad | — |
| 2 | Revenue Verified | SUM(verified_revenue) | Chỉ ORDER_VERIFIED | `ads_measurement_events.revenue_value` ← Commerce Verified Revenue, `ORDER_VERIFIED` only | ✅ |
| 3 | ROAS | Revenue Verified / Ads Spend | Không dùng order chưa verified | metric 2 / metric 1 | ✅ |
| 4 | CPA | Ads Spend / number_of_ORDER_VERIFIED | Theo campaign/adset/ad/live/session | metric 1 / count(`ORDER_VERIFIED`) | ✅ |
| 5 | AOV | Revenue Verified / verified_orders | Theo verified order | metric 2 / count(verified orders) | ✅ |
| 6 | Boxes per Order | Verified boxes / verified_orders | Mục tiêu tăng AOV | verified boxes / verified orders (Commerce verified) | ✅ |
| 7 | Comment Rate | LIVE_COMMENT / LIVE_VIEW | Top funnel | event counts (`ads_measurement_events`, Gateway-sourced) | — |
| 8 | Inbox Rate | MESSENGER_STARTED / LIVE_COMMENT | Handoff quality | event counts | — |
| 9 | Quote Rate | QUOTE_SENT / MESSENGER_STARTED | AI + Commerce quote efficiency | event counts | — |
| 10 | Order Rate | ORDER_CREATED / QUOTE_SENT | Sales conversion | event counts | — |
| 11 | Verified Rate | ORDER_VERIFIED / ORDER_CREATED | Payment/COD/fulfillment quality | count(`ORDER_VERIFIED`) / count(`ORDER_CREATED`) | ✅(verified-keyed) |
| 12 | COD Fail Rate | COD fail / COD orders | Rủi ro vận hành | Commerce COD outcome (consumed) | — |
| 13 | CRM Revenue | Verified revenue từ CRM attribution | Lifecycle value | metric 2 filtered by `attribution_context.entry_channel=CRM` | ✅ |
| 14 | Diamond Revenue | Verified revenue từ referral/Diamond attribution | Growth multiplier | metric 2 filtered by `referral_link_id`/`diamond_id` | ✅ |

*Phase-3 growth KPIs (Repeat/Reactivation/Diamond/Value-Opt/Learning) exist in `[DOC §9 L173–177]` with
thresholds M6-OD-002; adjacent to the 14 and out of this contract's core scope.*

---

## 2. Verified-only revenue enforcement at the query layer `[DOC §14 L283 / §4 L78 / REG RULE-003]`

- **Structural, not incidental.** The **definition** of every revenue-bearing metric (2,3,4,5,6,11,13,14 above)
  keys on `ORDER_VERIFIED` / `verified_revenue` / `verified_orders`. There is **no query path** that admits
  quote, cart, order-draft, payment-waiting or COD-waiting into a revenue figure `[REG RULE-003]`.
- `Revenue Verified = SUM(verified_revenue)` **WHERE order state = `ORDER_VERIFIED`** `[DOC §14 L283 "Chỉ
  ORDER_VERIFIED"]`; `revenue_value` is sourced only from Commerce Verified Revenue `[DOC §12 L256]`, never
  computed by M6.
- **Fail-closed checks**: a dashboard showing quote/order-draft as revenue is a **FAIL** — smoke **SMK-015**;
  quote-without-order → no revenue/ROAS (SMK-004); draft-not-verified → no Verified Revenue (SMK-005). DQ item 6
  (Verified Revenue) FAILs when *"Quote/order draft/unpaid được tính revenue"* `[DOC §15 L306]`.
- `PAYMENT_COMPLETED` does **not** enter revenue by default (**M6-OD-008 OPEN**); only `ORDER_VERIFIED` does.

---

## 3. Data-quality gate propagation `[DOC §15 L299–308 / REG RULE-015]`

The 8 `[DOC §15]` gate items each yield PASS / HOLD / FAIL:

| # | Gate Item | PASS (verbatim) | FAIL/HOLD (verbatim) |
|---|---|---|---|
| 1 | Event Registry | Event code tồn tại, owner rõ, schema đúng | Unknown event, event không có owner |
| 2 | Consent | Consent valid tại thời điểm event/external send | Missing/expired/opt-out |
| 3 | Dedup | No duplicate hoặc duplicate được merge chính xác | Pixel/CAPI/Offline double count |
| 4 | Identity | guest/customer/order mapping rõ | Guest merge sai hoặc order không map được |
| 5 | Attribution | campaign/adset/ad/page/live/messenger chain đủ | Nguồn mơ hồ, conflict không xử lý |
| 6 | Verified Revenue | Revenue lấy từ Commerce Verified Revenue | Quote/order draft/unpaid được tính revenue |
| 7 | Suppression | Recall/Sale Lock/CRM suppression được phản ánh | Scale khi đang bị lock/suppression |
| 8 | Dashboard | Metric có sample evidence và trace | Dashboard chỉ là visual không có source trace |

- **Worst-status propagation** `[PACK]` (per `[[RESEARCH_DASHBOARD_DATA_QUALITY]]`): a metric inherits the
  **worst** DQ status of its inputs — `FAIL > HOLD > PASS`. E.g. ROAS shows HOLD/FAIL if its Ads Spend mapping,
  or the attribution/verified-revenue inputs behind Revenue Verified (DQ items 5 and 6), is not PASS. **A green
  metric is never shown over a held/failed input.**
- **Evidence-first** `[DOC §15 L308]`: every metric must carry **sample evidence + source trace**; a
  visual-only metric with no trace is a **FAIL** — the dashboard proves, it does not decorate `[REG RULE-015]`.
- Suppression (item 7) surfaces recall/sale-lock/CRM-suppression into the dashboard and gates scale
  `[REG RULE-017]`.

---

## 4. Data mart = read-only support view `[DOC §9 L169 / REG RULE-012]`

- The data mart / dashboard is a **support view only**; it **never** becomes a trigger owner for CRM, pricing,
  Diamond or budget scale `[REG RULE-012 / DOC §9 L169]`.
- The dashboard API is **read-only**: *"Chỉ đọc data mart/support view — never write, never trigger"*
  `[DOC §19 L373]` (`CTR-018 GET /api/admin/ads/dashboard`).
- **Fail-closed check**: a data mart that creates a CRM/scale trigger is a **FAIL** — smoke **SMK-010**.
- The dashboard **presents** scale-readiness conditions to the owner; it does **not** act — scale stays the
  owner decision `[REG RULE-010]`, consistent with `[[RESEARCH_SCALE_GATE_WORKFLOW]]`.

## 5. Thresholds & alerts — pending M6-OD-002 `[REG MONITORING_REGISTER / DECISION_REGISTER]`

- **All numeric alert thresholds** (CPA/ROAS/AOV/Verified-Rate per stage, duplicate rate, outbox failure rate)
  are **`MISSING / OWNER_DECISION_REQUIRED` → M6-OD-002 (OPEN)** `[REG MONITORING_REGISTER]`. The pack **invents
  no threshold**.
- Consequence: the dashboard may **display** all 14 metrics and their DQ status now, but **alert firing** (and
  any threshold-based scale-readiness verdict) is **BLOCKED** until the owner sets M6-OD-002. Fail-closed: no
  alert with a guessed bound.

## 6. Verification pass (this prompt has no downstream critic) `[PACK]`

Ledger routes M6-P0304 → M6-P0305 with **no `M6-PC0304`**. Scoped to this doc's risk surface, a **2-lens**
independent pass was run: (A) 14-metric verbatim fidelity + verified-revenue-enforcement + rev?-classification;
(B) DQ-propagation correctness + data-mart-read-only + no-threshold-preemption (M6-OD-002) + no PII. Confirmed
findings folded in above. The 12 prior research critics remain PASS/0-blocker.

## 7. Owner-decision dependencies (no decision pre-empted) `[REG DECISION_REGISTER]`

| Decision | Status | What it gates |
|---|---|---|
| **M6-OD-002** (CPA/ROAS/AOV/Verified-Rate thresholds) | OPEN | §5 alert firing + scale-readiness verdicts (values, not formulas) |
| M6-OD-008 (PAYMENT_COMPLETED as revenue?) | OPEN | §2 whether it ever enters revenue; default non-revenue |
| M6-OD-005 (primary attribution model) | OPEN | which model backs the revenue attribution behind ROAS/CPA for **scale** (dashboard may show many) |
| `CTR-015` (Dashboard KPI) | DRAFT_LOCKED formulas | thresholds via M6-P0714 |
| `CTR-018` (dashboard API) | MISSING→M6-P0712 | the read-only query endpoint |

## 8. Boundary & safety guards `[BRIEF / REG §18]`

- **Read-only / support-view**: no write, no trigger; the dashboard never drives CRM/pricing/Diamond/scale
  `[REG RULE-012 / RULE-010]`.
- **Verified-only revenue** enforced structurally (§2); no unverified data prettifies a metric `[DOC §4 L78]`.
- **Staged**: BLOCKED/OFF — a design; it runs no query and fires no alert.
- **No raw PII/secrets** — metrics are aggregates; any identity dimension masked / `secret_ref`; no
  customer-level PII surfaced `[REG RULE-014 / H02]`.
- **Channel-origin content** (comment/messenger counts) is untrusted DATA aggregated as counts, never executed
  `[REG RULE-H03]`.

## 9. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| The 14 KPI formulas + notes | `[DOC §14 L282–295]` (`[REG MONITORING_REGISTER]`) — owner-mandated (verbatim) |
| Verified-only revenue (Chỉ ORDER_VERIFIED); no prettifying with unverified data | `[DOC §14 L283 / §4 L78]` + `[REG RULE-003]` — owner-mandated |
| Data Quality Gate 8 items; evidence-first (no trace → FAIL) | `[DOC §15 L299–308]` + `[REG RULE-015]` — owner-mandated |
| Data mart support-view only, no trigger; dashboard API read-only | `[DOC §9 L169 / §19 L373]` + `[REG RULE-012]` — owner-mandated |
| Thresholds OPEN (no value invented) | `[REG MONITORING_REGISTER / M6-OD-002]` — owner-mandated status |
| Source-trace column; worst-status DQ propagation; rev?-classification; alert-firing-blocked framing | `[PACK]` / `[EXT]` — owner-review design proposals, NOT owner requirements |

*This design is plan-only: it runs no query, fires no alert, invents no threshold, triggers nothing, and flips
no flag; `global_gateway_state=BLOCKED`, `production_flag=OFF`.*
