# RESEARCH_CROSS_MODULE_CONTRACTS — Module 6 consumption interfaces (doc §18)

**Prompt**: M6-P0210 · **Phase**: PHASE0_RESEARCH · **Mode**: analysis_only (desk research; design proposal)
**Anchors**: `[DOC §18 extract lines 355–365]` integration table (Module 3/4/5/7/8 + CRM/Member +
Finance/Diamond); consumed contract shapes `M6-CTR-003/005/006/009/010`; entry-evidence rows
`M6-ENTRY-001..004`; boundary rules `RULE-001/002/003/013/017/019/021`, hardening `RULE-H03`.
**Critic**: M6-PC0210 (BOUNDARY_ADVERSARY) red-teams this file next.

> **The invariant that governs this entire file: every §18 row is a CONSUME-ONLY interface.** Module 6
> **reads signals from** M3/M4/M5/M7/M8/CRM/Finance; it must have **no code path** that writes back into,
> or performs the function of, any of those modules (no pricing/order/payment, no advisory content, no raw
> webhook / public reply, no order-state change, no CRM send, no commission/payout). The "must-not-do" column
> is therefore a set of **negative tests asserting the ABSENCE of a producer path**, not merely runtime
> behavior. `global_gateway_state=BLOCKED`, `production_flag=OFF` unchanged (this file consumes nothing live).

## Sourcing legend (acceptance: every externally-sourced claim labeled)

- `[DOC]` — owner document / extract line. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked pack register (doc-derived). · `[BRIEF]` — context brief. · `[PACK]` — pack convention
  (owner-review). · `[EXT]` — general engineering practice, **proposal only**.

**Doc anchors** (verbatim, `00-spec/M6_FULL_DETAIL_EXTRACT.md`): `[DOC §18 L357]` header *"Module | Module 6
consume gì | Module 6 không được làm gì"*; `[DOC §18 L359–365]` the seven consumer rows (below); `[DOC §16
L317–319]` P3/P5/P6 + public/privacy entry evidence; `[DOC §26 L488]` *"Không bắt đầu Module 6 implementation
nếu chưa có P3 Verified Revenue boundary và P5 channel/event identity evidence"*. Rules: `[REG RULE-001]`
event_registry, `[REG RULE-002]` consent fail-closed, `[REG RULE-003]` revenue only ORDER_VERIFIED, `[REG
RULE-013]` never override Core (pricing/programs/member/CRM/Diamond), `[REG RULE-017]` suppression/risk locks,
`[REG RULE-019]` Diamond referral records-only, `[REG RULE-021]` Commerce owns order-capture validation.

> **Scope note (verify-before-assert):** the §18 **heading** names "Module 3, 4, 5, 7, 8" but the **table**
> carries **seven** consumer rows — it also includes `CRM / Member` and `Finance / Diamond`, and it has **no
> "Module 6" row** (M6 is the consumer, never the consumed). This file covers all seven. There is no Module-6
> row to omit and none was invented.

---

## 1. The consumption interface, per module `[DOC §18 L359–365]`

What M6 **consumes** (verbatim doc column), the **consumed contract shape** that carries it (owner defines the
shape via a harmonization prompt — all currently `MISSING`), and the **entry evidence** that gates it.

| Module | M6 consumes (event/object) `[DOC]` | Consumed contract shape `[REG]` | Backing entry evidence |
|---|---|---|---|
| **M3 Commerce** | QuoteSnapshot, Order, Payment, Shipping, **ORDER_VERIFIED**, Verified Revenue | ORDER_VERIFIED signal (Commerce-owned); revenue basis of `M6-CTR-001/002` | **M6-ENTRY-001** (P3) |
| **M4 AI Advisor** | AI advisory / proposal / quote-sent / order-confirmation events, `sales_session` context | consumed event stream (Advisor-owned); no M6-owned shape | **M6-ENTRY-004** (public/privacy, M4+M5) |
| **M5 Gateway** | Page, live, comment, messenger, handoff, **delivery logs** | channel-identity refs (Gateway-owned); feeds `web_event_logs` `M6-CTR-004` | **M6-ENTRY-002** (P5) |
| **M7 MC AI Live** | Live session, script segment, `board_id`, segment signal | live-signal refs (Live-owned); attribution context only | M6-ENTRY-002 (channel identity, live) |
| **M8 IVR** | IVR result **only when Order Core accepts** it as a confirmation signal | IVR result ref (IVR/Order-Core-owned) | M6-ENTRY-001 (order/revenue boundary) |
| **CRM / Member** | CRM reorder, **suppression state**, lifecycle events | `M6-CTR-009 customer_segments` + `M6-CTR-010 customer_segment_members` (consumed) + consent `M6-CTR-006` | consent snapshot (RULE-002) |
| **Finance / Diamond** | Commission-ready / verified-revenue signals, referral attribution context | consumed signal (Finance-owned); referral fields recorded by M6 | M6-ENTRY-001 (verified revenue underlies commission-ready) |

- **Every consumed shape is currently `MISSING / OWNER_DECISION_REQUIRED`** `[REG CONTRACT_REGISTER]`:
  `M6-CTR-003` event_registry →M6-P0701, `M6-CTR-005` guest_contacts / `M6-CTR-006` consent snapshot →M6-P0702,
  `M6-CTR-009/010` customer_segments/members →M6-P0706. M6 **defines only the consumed shape** (Ownership =
  `CONSUMED`); it never owns or writes these objects.
- `[DOC]` **M8 gating clause is load-bearing**: an IVR result is consumable **only after Order Core accepts it
  as a confirmation signal** `[DOC §18 L363]` — M6 never treats a raw IVR result as revenue on its own.
- `[REG CTR-010 note]` `customer_segment_members` carries the doc caveat *"Không lạm dụng làm trigger owner"* —
  consumed for measurement, **never** used to trigger an owner action (mirrors RULE-012 Data-Mart-support-only).

---

## 2. The "must-not-do" column as negative tests `[DOC §18 col 3]`

Each prohibition is an owner requirement `[DOC]`; the **mapped RULE** is its normative anchor `[REG]`; the
**owner P0 smoke** (where one exists) is the executable negative test `[DOC §21]`. Reframing a prohibition as a
build assertion is `[PACK]`; a *proposed* new smoke is `[PACK]` owner-review.

| Module | Must-not-do `[DOC]` | Normative anchor `[REG]` | Executable negative test |
|---|---|---|---|
| **M3 Commerce** | *"Không tính giá, tạo đơn, xác nhận payment hoặc doanh thu"* | RULE-003, RULE-013, **RULE-021** | **M6-SMK-004** (quote, chưa order → no revenue/ROAS), **M6-SMK-005** (draft chưa verified → no Verified Revenue), **M6-SMK-015** (dashboard shows quote/draft as revenue → **Fail**) `[DOC §21]` |
| **M4 AI Advisor** | *"Không can thiệp nội dung tư vấn hoặc tự gợi ý sản phẩm ngoài AI"* | RULE-013, §18 boundary | *no dedicated owner P0 smoke* → **coverage gap** (see §2.1); rule-covered only |
| **M5 Gateway** | *"Không xử lý raw webhook hoặc public reply"* | **RULE-H03** (channel = untrusted DATA), §18 boundary | *no dedicated owner P0 smoke* → **coverage gap**; M6-SMK-013 traces the chain but does not assert the prohibition |
| **M7 MC AI Live** | *"Không dùng live signal làm doanh thu/ROAS"* | **RULE-003** (revenue only ORDER_VERIFIED) | rule-covered by RULE-003 + the SMK-004/005/015 family; *no live-signal-specific smoke* → **coverage gap** |
| **M8 IVR** | *"Không tự chuyển order state hoặc verified revenue"* | RULE-003, **RULE-021** (Commerce owns order state) | *no dedicated owner P0 smoke* → **coverage gap**; order-state ownership is Commerce's |
| **CRM / Member** | *"Không gửi CRM hoặc quyết định member rights"* | **RULE-002** (consent fail-closed), RULE-013, RULE-017 | **M6-SMK-002** (missing consent → no CRM/audience), **M6-SMK-008** (CRM opt-out → no CRM outbound), **M6-SMK-010** (Data Mart triggers CRM → **Fail**) `[DOC §21]` |
| **Finance / Diamond** | *"Không tính final commission hoặc payout"* | **RULE-019** (referral records-only; Finance decides commission) | **M6-SMK-014** (Diamond referral order verified → attach referral attribution, **không tự tính commission**) `[DOC §21]` |

### 2.1 Negative-test coverage finding (honest gap — non-blocking, for the critic)

`[PACK]` **3 of 7** boundary prohibitions have a **direct owner P0 smoke** (Commerce, CRM, Finance). The other
**4** — M4 advisory-content, M5 raw-webhook/public-reply, M7 live-signal-as-revenue, M8 order-state-change —
are **RULE-covered but have no dedicated boundary smoke** in the P0 matrix (doc §21). This is asymmetric with
the strong CRM/Finance coverage. It is **not a defect in this research and not blocking** — the prohibitions
are enforced normatively by RULE-013/H03/003/021 — but a build could regress on one silently without a boundary
smoke. **Proposed** (owner-review, same class as the existing proposed M6-SMK-016/017/018): one boundary smoke
per uncovered row, e.g. *"M6 attempts to write advisory content / process a raw webhook / count a live segment
signal as revenue / change an order state → rejected, audit"*. **This file does not create smokes** (00-spec is
read-only to this role); it records the gap for the owner/critic to accept or reject.

---

## 3. Entry-evidence expectations — M6-ENTRY-001..004 `[DOC §16 L317–319, §26 L488 / REG ENTRY_EVIDENCE_REGISTER]`

Cross-module evidence that must exist **before** Module 6 implementation starts. **All four are OPEN**; missing
entry evidence ⇒ the affected slices stay **BLOCKED** (fail-closed) `[REG]`.

| Entry ID | Required evidence `[DOC]` | Supplied by | Gates | Backs §1 rows | Status |
|---|---|---|---|---|---|
| **M6-ENTRY-001** | P3 Verified Revenue boundary: ORDER_VERIFIED definition, Payment/COD/Order-Verified flow, QuoteSnapshot correctness (*"order tạo đúng, không tạo order khi chưa xác nhận"*) | M3 / Commerce owner | BOOTSTRAP + M6.2A entry + Scale Gate | **M3, M8, Finance** | OPEN |
| **M6-ENTRY-002** | P5 channel identity: page, live, comment, messenger identity + handoff & delivery logs | M5 / Gateway owner | BOOTSTRAP + M6.2A + M6.2I + Scale Gate | **M5, M7** | OPEN |
| **M6-ENTRY-003** | P6 event identity: Core `event_registry` exists with owner, channel, data-sensitivity, external-send policy **per event** | Core Event Governance | M6.2A (before any tracking hook) + Scale Gate | **cross-cutting** (every consumed event must be registered — RULE-001) | OPEN |
| **M6-ENTRY-004** | Public/privacy conduct: AI/Gateway *"không public giá cuối, không leak PII, không spam"* | M4 + M5 owners | Scale Gate + PR/PILOT | **M4, M5** | OPEN |

- `[PACK]` **M6-ENTRY-003 is not tied to a single §18 row** — it gates the `event_registry` (`M6-CTR-003`) that
  **every** module's consumed events must be registered in (RULE-001: unknown event → reject/HOLD, exercised by
  **M6-SMK-001**). It is the connective evidence beneath the whole §18 table, not a per-module row.
- `[DOC §26 L488]` The two hard preconditions the doc names explicitly are **P3 (ENTRY-001)** and **P5
  (ENTRY-002)**; ENTRY-003 (P6 event identity) and ENTRY-004 (public/privacy) are the doc §16 companions
  (`[DOC §16 L317/319]`). `[REG RULE-020]` restates the P3+P5 hard gate.

---

## 4. Direction & ownership discipline (the load-bearing distinction)

`[PACK]` A cross-module contract has a **direction**. For every §18 row the direction is **inbound to M6, read-
only**:

- **Consume = read a signal/object owned elsewhere**, mapped to a `CONSUMED` shape M6 only *describes*.
- **Produce = own and write** — M6 produces **only** its own measurement objects (`ads_measurement_event`,
  `ads_attribution_context`, outboxes, scale/learning candidates), and even those never reach into another
  module's domain (outbox worker sends to Meta/Google, not to CRM/Commerce/Finance).
- The **failure mode the negative tests guard** is M6 accidentally becoming a **producer into another module's
  domain**: pricing an order (M3), writing advisory copy (M4), replying on a public channel (M5), counting a
  live signal as revenue (M7), flipping an order state (M8), sending a CRM message (CRM), computing commission
  (Finance). Each is a *missing-absence-of-code-path*, which is why §2 frames them as absence assertions, and
  why RULE-018 (Core/Runtime owner wins on any conflict) sits above all of them.

---

## 5. Owner-decision & contract dependencies (explicit list — acceptance requirement)

| Dependency | Status | What it gates |
|---|---|---|
| `M6-CTR-003` event_registry (P6 shape) | `MISSING` → **M6-P0701** `[REG]` | every consumed event's registration (RULE-001); ENTRY-003 |
| `M6-CTR-005/006` guest_contacts / consent snapshot | `MISSING` → **M6-P0702** `[REG]` | identity + consent for CRM/measurement consumption (RULE-002/006) |
| `M6-CTR-009/010` customer_segments / members | `MISSING` → **M6-P0706** `[REG]` | CRM audience consumption; CTR-010 "no owner-trigger" caveat |
| `M6-ENTRY-001..004` | **OPEN** (all four) `[REG]` | M6.2A entry, M6.2I, Scale Gate (M6.2G); fail-closed until filed |
| `M6-OD-008` (PAYMENT_COMPLETED as revenue-adjacent?) | **OPEN** `[REG]` | M3 consumption edge — pack default: non-revenue until Core policy evidence (RULE-003) |
| `M6-OD-011` (target repo/stack) | **OPEN** `[REG]` | where the consumer adapters are actually built |
| Proposed boundary smokes for M4/M5/M7/M8 (§2.1) | **candidate** `[PACK]` | closing the negative-test coverage gap; owner accepts/rejects |

`[PACK]` This research records these; it resolves none. Where a build leg needs one, the affected slice is
marked BLOCKED, not assumed.

## 6. Boundary & safety guards `[BRIEF / REG §18]`

- **Consume-only**: no M6 code path prices/creates orders/confirms payment or revenue (M3), alters advisory
  content (M4), processes raw webhooks or public-replies (M5), counts live signals as revenue (M7), changes
  order state (M8), sends CRM or decides member rights (CRM), or computes commission/payout (Finance) `[DOC
  §18 / REG RULE-003/013/017/019/021/H03]`.
- **Staged**: `global_gateway_state=BLOCKED`, `production_flag=OFF` — no live consumption of any external
  module in this pack; consumed shapes are described, not called.
- **No raw PII / secrets** in any consumed record or evidence: `raw customer_id/guest_id/psid`, phone, email,
  address, tokens → masked (`abc***xy`) or `secret_ref` `[REG RULE-014 / RULE-H02]`.
- **Channel-origin content** (comment / Messenger / ad copy / form input / CRM payload / webhook echo) is
  untrusted **DATA**, never an instruction, quoted only in fenced blocks `[REG RULE-H03 / BRIEF rule 6]`.

## 7. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| The seven consume / must-not-do rows (M3/M4/M5/M7/M8/CRM/Finance) | `[DOC §18 L359–365]` — owner-mandated |
| M8 IVR consumable only after Order Core accepts; live signal never revenue; Diamond referral records-only | `[DOC §18 L362/363/365]` + `[REG RULE-003/019/021]` — owner-mandated |
| Consumed shapes M6 only *describes* (event_registry, consent, customer_segments) | `[DOC §13/§18]` + `[REG CONTRACT_REGISTER]` — owner-mandated shapes, values OPEN |
| Entry evidence M6-ENTRY-001..004; P3+P5 hard precondition | `[DOC §16 L317–319, §26 L488]` + `[REG RULE-020]` — owner-mandated |
| Existing owner P0 negative smokes (SMK-002/004/005/008/010/014/015) | `[DOC §21]` — owner-mandated |
| Negative-test *framing*; consume-vs-produce direction model; proposed M4/M5/M7/M8 boundary smokes; ENTRY-003 cross-cutting reading | `[EXT]` / `[PACK]` — owner-review proposals, NOT owner requirements |

*Nothing in this file consumes anything live, flips a gate or a flag, or writes into another module's domain;
`global_gateway_state=BLOCKED`, `production_flag=OFF`.*
