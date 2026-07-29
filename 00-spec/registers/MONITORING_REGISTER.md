# MONITORING_REGISTER — Module 6 metrics and quality alerts

The metric table is the owner document's Dashboard KPI Contract, VERBATIM
(doc §14, extract lines 280–295). Alert thresholds are NOT in the document —
they are owner decision M6-OD-002 (OPEN). Quality alert conditions derive from
the Data Quality Gate (doc §15).

## Metrics (doc §14, verbatim)

| Chỉ số | Công thức / nguồn | Ghi chú | Extract line |
|---|---|---|---|
| Ads Spend | Từ Ads platform / approved spend import | Phải có campaign/adset/ad mapping | 282 |
| Revenue Verified | SUM(verified_revenue) | Chỉ ORDER_VERIFIED | 283 |
| ROAS | Revenue Verified / Ads Spend | Không dùng order chưa verified | 284 |
| CPA | Ads Spend / number_of_ORDER_VERIFIED | Theo campaign/adset/ad/live/session | 285 |
| AOV | Revenue Verified / verified_orders | Theo verified order | 286 |
| Boxes per Order | Verified boxes / verified_orders | Mục tiêu tăng AOV | 287 |
| Comment Rate | LIVE_COMMENT / LIVE_VIEW | Top funnel | 288 |
| Inbox Rate | MESSENGER_STARTED / LIVE_COMMENT | Handoff quality | 289 |
| Quote Rate | QUOTE_SENT / MESSENGER_STARTED | AI + Commerce quote efficiency | 290 |
| Order Rate | ORDER_CREATED / QUOTE_SENT | Sales conversion | 291 |
| Verified Rate | ORDER_VERIFIED / ORDER_CREATED | Payment/COD/fulfillment quality | 292 |
| COD Fail Rate | COD fail / COD orders | Rủi ro vận hành | 293 |
| CRM Revenue | Verified revenue từ CRM attribution | Lifecycle value | 294 |
| Diamond Revenue | Verified revenue từ referral/Diamond attribution | Growth multiplier | 295 |

## Phase 3 growth KPIs (doc §9, verbatim — thresholds M6-OD-002)

| Nhóm tăng trưởng | Signal hợp lệ | KPI | Extract line |
|---|---|---|---|
| Repeat / Reorder | CRM_REORDER_SENT, CRM_REORDER_ORDER_CREATED, ORDER_VERIFIED | Repeat rate, CRM Revenue, AOV | 173 |
| Dormant / Reactivation | Dormant segment, consent pass, CRM eligibility pass, order verified | Reactivation rate, CPA reactivation | 174 |
| Diamond | DIAMOND_LEAD_CREATED, referral_link_id, DIAMOND_REFERRAL_ORDER_VERIFIED | Diamond lead rate, Diamond Revenue, commission-ready revenue | 175 |
| Value Optimization | High-value order, boxes/order, tier upgrade, product affinity | AOV, CLV proxy, boxes/order, ads ratio reduction | 176 |
| Learning Engine | Verified business signals + data quality pass | Candidate approval rate, uplift, drift violations | 177 |

## Data Quality Gate (doc §15, verbatim — full table, both PASS and FAIL/HOLD columns)

| Gate Item | PASS khi | FAIL/HOLD khi | Extract line |
|---|---|---|---|
| Event Registry | Event code tồn tại, owner rõ, schema đúng | Unknown event, event không có owner | 301 |
| Consent | Consent valid tại thời điểm event/external send | Missing/expired/opt-out | 302 |
| Dedup | No duplicate hoặc duplicate được merge chính xác | Pixel/CAPI/Offline double count | 303 |
| Identity | guest/customer/order mapping rõ | Guest merge sai hoặc order không map được | 304 |
| Attribution | campaign/adset/ad/page/live/messenger chain đủ | Nguồn mơ hồ, conflict không xử lý | 305 |
| Verified Revenue | Revenue lấy từ Commerce Verified Revenue | Quote/order draft/unpaid được tính revenue | 306 |
| Suppression | Recall/Sale Lock/CRM suppression được phản ánh | Scale khi đang bị lock/suppression | 307 |
| Dashboard | Metric có sample evidence và trace | Dashboard chỉ là visual không có source trace | 308 |

## Threshold status

All numeric alert thresholds (CPA/ROAS/AOV/Verified Rate per stage, duplicate
rate, outbox failure rate): `MISSING / OWNER_DECISION_REQUIRED` -> M6-OD-002.
The pack does not invent thresholds.
