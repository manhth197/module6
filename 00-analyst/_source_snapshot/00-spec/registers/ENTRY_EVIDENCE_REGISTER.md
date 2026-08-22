# ENTRY_EVIDENCE_REGISTER — cross-module evidence required BEFORE Module 6 work

The owner document conditions Module 6 implementation on evidence from other
modules/phases. Doc §16 extract line 317, verbatim: "P3/P5/P6 evidence |
Verified Revenue boundary, Payment/COD/Order Verified, Channel identity, event
identity có evidence" (decomposed below into M6-ENTRY-001/002/003). Doc §26
extract line 488: "Không bắt đầu Module 6 implementation nếu chưa có P3
Verified Revenue boundary và P5 channel/event identity evidence".

Status is OPEN until the operator files the referenced evidence under
`04-artifacts/evidence/entry/` and the Bootstrap/Slice-A entry-gate judge
reviews it. Missing entry evidence ⇒ affected slices stay BLOCKED (fail-closed).

| Entry ID | Required evidence | Supplied by | Checked at | Status | Source |
|---|---|---|---|---|---|
| M6-ENTRY-001 | P3 (Commerce Runtime) Verified Revenue boundary evidence: ORDER_VERIFIED definition, Payment/COD/Order Verified flow, QuoteSnapshot correctness ("QuoteSnapshot hoạt động đúng, order tạo đúng, không tạo order khi chưa xác nhận") | Module 3 / Commerce owner | BOOTSTRAP readiness + M6.2A entry gate + Scale Gate | RISK-ACCEPTED — filed 2026-07-22, judged M6-P1000=BLOCKED (all PARTIAL); staged work proceeds under `04-artifacts/evidence/decisions/M6-OVERRIDE-M6P1000-STAGED.json`, re-gate at M6.2G mandatory | extract lines 317–318, 488 |
| M6-ENTRY-002 | P5 (Facebook Gateway) channel identity evidence: page, live, comment, messenger identity + handoff and delivery logs | Module 5 / Gateway owner | BOOTSTRAP readiness + M6.2A entry gate; M6.2I entry; Scale Gate (M6.2G) | FILED 2026-07-22 — clean at M6-P1000 (READY_FOR_JUDGE); re-check M6.2I + M6.2G | extract lines 317, 361, 488 |
| M6-ENTRY-003 | P6 event identity evidence: Core event_registry exists with owner, channel, data sensitivity and external send policy per event | Core Event Governance | M6.2A entry gate (before any tracking hook); Scale Gate (M6.2G) | RISK-ACCEPTED — filed 2026-07-22, judged M6-P1000=BLOCKED (2 PARTIAL + 3 GAP: channel/data_sensitivity/external_send_policy); staged work proceeds under `04-artifacts/evidence/decisions/M6-OVERRIDE-M6P1000-STAGED.json`, re-gate at M6.2G mandatory | extract lines 317, 263, 490 |
| M6-ENTRY-004 | Public/privacy conduct evidence: AI/Gateway "không public giá cuối, không leak PII, không spam" | Module 4 + Module 5 owners | Scale Gate (M6.2G) and PR/PILOT | OPEN — not yet commissioned (M4 + M5 owners); hard-blocks M6.2G (RequiredInput of M6-P1600, file not yet on disk) | extract line 319 |

## Consumed-boundary reference (doc §18 — what Module 6 may consume; not evidence rows)

| Module | Module 6 consumes | Module 6 must NOT do | Source |
|---|---|---|---|
| Module 3 Commerce | QuoteSnapshot, Order, Payment, Shipping, ORDER_VERIFIED, Verified Revenue | Không tính giá, tạo đơn, xác nhận payment hoặc doanh thu | extract line 359 |
| Module 4 AI Advisor | AI advisory/proposal/quote sent/order confirmation events, sales_session context | Không can thiệp nội dung tư vấn hoặc tự gợi ý sản phẩm ngoài AI | extract line 360 |
| Module 5 Gateway | Page, live, comment, messenger, handoff, delivery logs | Không xử lý raw webhook hoặc public reply | extract line 361 |
| Module 7 MC AI Live | Live session, script segment, board_id, segment signal | Không dùng live signal làm doanh thu/ROAS | extract line 362 |
| Module 8 IVR | IVR result only when Order Core accepts as confirmation signal | Không tự chuyển order state hoặc verified revenue | extract line 363 |
| CRM / Member | CRM reorder, suppression state, lifecycle events | Không gửi CRM hoặc quyết định member rights | extract line 364 |
| Finance / Diamond | Commission-ready/verified revenue signals, referral attribution context | Không tính final commission hoặc payout | extract line 365 |
