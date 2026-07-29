# ARCH_BASELINE — Module 6 architecture baseline (1:1 to doc §5)

**Prompt**: M6-P0300 · **Phase**: PHASE0 (design) · **Mode**: plan_only (no code, no migration, no external call)
**Anchors**: `[DOC §5 extract lines 86–98]` the nine-layer operating architecture (verbatim); `[DOC §4 L72–81]`
boundary lock (must-not-do); `[REG CONTRACT_REGISTER]` all 26 `M6-CTR` contracts; `[REG RULES_LOCKED]`
RULE-001..021 + H01–H03. **Downstream**: this baseline is the reference map for the PHASE0 design prompts
(M6-P0301+). **No dedicated critic** follows this prompt in the ledger (M6-P0300 → M6-P0301) — so an
independent verification pass over the contract-placement / rule-citation / owner-decision-preemption axes was
run before finalizing (see §4).

> **Baseline frame.** Module 6 is **one measurement system**, not "vài đoạn code Pixel/CAPI hoặc một dashboard
> ROAS" `[DOC §4 L83]`. The nine §5 layers form the spine: **Source → Tracking → {Outbox → Integration} +
> {Attribution → Dashboard → Gate → Learning}**, with **Evidence** cross-cutting all of them. Every layer is
> **fail-closed** and **consume/measure-only** at its module boundaries; `global_gateway_state=BLOCKED`,
> `production_flag=OFF` — nothing in this baseline sends externally, scales, or publishes.

## Sourcing legend (acceptance: every externally-sourced claim labeled)

- `[DOC]` — owner document / extract line. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked pack register (doc-derived). · `[BRIEF]` — context brief. · `[PACK]` — pack convention
  (owner-review). · `[EXT]` — general engineering practice, **proposal only**.

## 0. Provenance — the accepted research this baseline folds in `[REG evidence/prompts]`

The baseline maps the **accepted** Phase-0 research. **All twelve research critics passed with zero blockers**
(verified this prompt): `M6-PC0200..0211` each `status=PASS`, `fail_gate=False`, `open_blockers=0`. There is
**no outstanding BLOCKER critic finding to address or escalate** (acceptance-check satisfied by verification,
not assumption). Non-blocking findings the research recorded are folded into the per-layer notes and §4.

| Layer (§5) | Research basis (accepted, critic-PASS) |
|---|---|
| Source / Tracking | `[[RESEARCH_EVENT_REGISTRY_INTEGRATION]]` (M6-P0201), `[[RESEARCH_IDENTITY_CONSENT]]` (M6-P0202) |
| Outbox / Integration | `[[RESEARCH_OUTBOX_WORKER_PATTERNS]]` (M6-P0203), `[[RESEARCH_META_PIXEL_CAPI_DEDUP]]` (M6-P0204), `[[RESEARCH_OFFLINE_CONVERSIONS]]` (M6-P0205) |
| Attribution / Dashboard | `[[RESEARCH_ATTRIBUTION_MODELS]]` (M6-P0206), `[[RESEARCH_DASHBOARD_DATA_QUALITY]]` (M6-P0207) |
| Gate / Learning | `[[RESEARCH_SCALE_GATE_WORKFLOW]]` (M6-P0208), `[[RESEARCH_LEARNING_ENGINE_GUARDRAILS]]` (M6-P0209), `[[RESEARCH_STRATEGY_LIBRARIES]]` (M6-P0211) |
| Cross-cutting | `[[RESEARCH_CROSS_MODULE_CONTRACTS]]` (M6-P0210), `[[RESEARCH_REPO_AUDIT_PLAN]]` (M6-P0200) |

---

## 1. The nine-layer baseline (1:1 to doc §5) `[DOC §5 L88–98]`

Each layer reproduces the §5 **Thành phần** (component) column verbatim, states its responsibility, its
**must-not-do** (traced to a `[DOC §4]` boundary cell + the normative RULE), and **which `M6-CTR` contracts
live in it**. Contract owner/status is `[REG CONTRACT_REGISTER]`.

### 1.1 Source `[DOC §5 L90]`
- **Components (verbatim)**: Core event_registry, Customer/Guest identity, Consent snapshot, Commerce Verified
  Revenue.
- **Responsibility**: *"Nguồn sự thật để đo lường và attribution"* — the truth inputs M6 **consumes**; owns
  none of them.
- **Contracts here**: `CTR-003` event_registry *(CONSUMED, Core Event Governance, MISSING→M6-P0701)*, `CTR-005`
  guest_contacts *(CONSUMED, MISSING→M6-P0702)*, `CTR-006` guest_marketing_consent_snapshot *(CONSUMED,
  MISSING→M6-P0702)*. Commerce Verified Revenue enters as the **ENTRY-001** boundary (not a CTR).
- **Must-not-do**: `[DOC §4 L74]` *"Tự tạo event ngoài event_registry; ghi event không rõ consent hoặc
  identity"* → `[REG RULE-001]` (event must be registered), `[REG RULE-006]` (identity chain audited),
  `[REG RULE-018]` (Core owner wins; never invent events/policy).
- **Accepted finding**: consume-only; **asymmetric cache staleness** — a de-registered event code must never be
  false-ALLOWed `[[RESEARCH_EVENT_REGISTRY_INTEGRATION]]`. Entry evidence **ENTRY-001/002/003 OPEN** → Source
  inputs gated fail-closed.

### 1.2 Tracking `[DOC §5 L91]`
- **Components (verbatim)**: Web hooks, landing events, Facebook/Meta events, Messenger events, live events, CRM
  events.
- **Responsibility**: *"Thu tín hiệu đầu vào theo event code đã khóa"* — ingest signals under **already-locked**
  event codes only.
- **Contracts here**: `CTR-004` web_event_logs *(M6, MISSING→M6-P0703)*, `CTR-016` POST /api/ads/events/track
  *(M6, MISSING→M6-P0711)*.
- **Must-not-do**: `[DOC §19 L371]` *"Không gửi external trực tiếp"*; `[DOC §18 L361]` no raw-webhook processing
  / no public reply (that is Module 5) → `[REG RULE-001]` (registered events only), `[REG RULE-007]`
  (web_event_logs append-only), `[REG RULE-002]` (consent at event time).
- **Accepted finding**: ingest is append-only; channel-origin text is **untrusted DATA** `[REG RULE-H03]`.

### 1.3 Outbox `[DOC §5 L92]`
- **Components (verbatim)**: conversion_events, marketing_measurement_outbox, marketing_audience_outbox.
- **Responsibility**: *"Tách runtime request khỏi external sync, chống mất dữ liệu và retry có kiểm soát"* — the
  transactional-outbox seam between runtime and external egress.
- **Contracts here**: `CTR-007` conversion_events *(M6/Core, MISSING→M6-P0704)*, `CTR-008`
  marketing_measurement_outbox *(M6 worker, MISSING→M6-P0705)*, `CTR-011` marketing_audience_outbox *(M6
  worker, MISSING→M6-P0706)*, `CTR-017` POST /api/ads/conversions *(M6, MISSING→M6-P0711)*. **Consumed audience
  inputs**: `CTR-009 customer_segments` / `CTR-010 customer_segment_members` *(CONSUMED, MISSING→M6-P0706;
  CTR-010 doc note "không lạm dụng làm trigger owner")*.
- **Must-not-do**: `[DOC §19 L372]` conversion API is the *"Nguồn cho measurement outbox"* and must not bypass
  it; `[DOC §4 L77]` no direct send from runtime → `[REG RULE-004]` (all external via outbox+worker; audience
  only from approved customer_segments), `[REG RULE-002]` (consent fail-closed).
- **Accepted finding**: at-least-once + `idempotency_key` = effectively-once; bounded retry →
  `error_log`/`next_retry_at` → dead-letter, no infinite retry, no silent loss (proposed smoke **SMK-016**)
  `[[RESEARCH_OUTBOX_WORKER_PATTERNS]]`.

### 1.4 Integration `[DOC §5 L93]`
- **Components (verbatim)**: Pixel, CAPI, Offline Conversion, Google/Meta connectors.
- **Responsibility**: *"Gửi dữ liệu ra nền tảng ngoài khi consent và dedup pass"* — external egress, **gated on
  consent + dedup**.
- **Contracts here**: `CTR-021` worker marketing_measurement_dispatcher *(M6, MISSING→M6-P0713; drains CTR-008,
  sends Pixel/CAPI/Offline)*, `CTR-022` worker marketing_audience_dispatcher *(M6, MISSING→M6-P0713; drains
  CTR-011, consent fail-closed)*. Connectors themselves are **external endpoints** (no M6-owned schema).
- **Must-not-do**: `[DOC §4 L77]` *"Gửi trực tiếp từ request runtime hoặc gửi dữ liệu không có consent"* →
  `[REG RULE-004]` (via worker only), `[REG RULE-005]` (mandatory dedup; locked `dedup_key`/`idempotency_key`,
  no double count), `[REG RULE-014]` (no raw PII; CAPI hash policy = **M6-OD-003 OPEN**).
- **Accepted finding**: internal `dedup_key`/`idempotency_key` are **internal**; Meta dedup uses the shared
  `event_id + event_name` — a different `event_id` → double count → FAIL-001. **Staged**: BLOCKED/OFF ⇒ **no
  real send**; connectors are described, not called. Connector-first-in-pilot = **M6-OD-004 OPEN**
  `[[RESEARCH_META_PIXEL_CAPI_DEDUP]]`.

### 1.5 Attribution `[DOC §5 L94]`
- **Components (verbatim)**: Attribution Resolver, Ads Context Resolver, Live Session Resolver.
- **Responsibility**: *"Gắn nguồn ads/live/page/comment/Messenger tới quote/order/verified revenue"* — resolve
  the source→revenue chain, traceable end-to-end `[DOC §11 L236]`.
- **Contracts here**: `CTR-001` ads_measurement_event *(M6, **DRAFT_LOCKED**, SPEC §10.1)*, `CTR-002`
  ads_attribution_context *(M6, **DRAFT_LOCKED**, SPEC §10.2)*, `CTR-023` worker attribution_materializer *(M6,
  MISSING→M6-P0713; no verified-revenue overwrite)*.
- **Must-not-do**: `[DOC §4 L75]` *"Gán doanh thu theo cảm tính; sửa attribution sau khi verified mà không
  audit"* → `[REG RULE-003]` (revenue only ORDER_VERIFIED), `[REG RULE-008]` (immutable after verified;
  adjustment record with actor/reason/audit/evidence — proposed smoke **SMK-018**), `[REG RULE-009]` (missing
  source → LOW/HOLD, never scale evidence). Live signal is **never** revenue `[DOC §18 L362]`.
- **Accepted finding**: dashboard may show multiple models but the **Scale Gate needs one primary model** —
  choice is **M6-OD-005 OPEN** (this layer does not pick) `[[RESEARCH_ATTRIBUTION_MODELS]]`.

### 1.6 Dashboard `[DOC §5 L95]`
- **Components (verbatim)**: ROAS/CPA/AOV/Funnel/CRM/Diamond dashboards.
- **Responsibility**: *"Báo cáo hiệu quả và cảnh báo chất lượng dữ liệu"* — report + surface data-quality; a
  **support view**, never a trigger owner.
- **Contracts here**: `CTR-015` Dashboard KPI contract *(M6, **DRAFT_LOCKED** formulas §14; thresholds =
  M6-OD-002 via M6-P0714)*, `CTR-018` GET /api/admin/ads/dashboard *(M6, MISSING→M6-P0712)*.
- **Must-not-do**: `[DOC §4 L78]` *"Làm đẹp dashboard bằng dữ liệu chưa verified"*; `[DOC §19 L373]` *"Chỉ đọc
  data mart/support view"* → `[REG RULE-003]` (verified revenue only; SMK-004/005/015), `[REG RULE-012]` (Data
  Mart support-view only, never trigger CRM/pricing/Diamond/scale; SMK-010).
- **Accepted finding**: evidence-first (visual-only = FAIL, doc L308); **worst-status DQ propagation**
  (FAIL>HOLD>PASS); thresholds **M6-OD-002 OPEN** `[[RESEARCH_DASHBOARD_DATA_QUALITY]]`.

### 1.7 Gate `[DOC §5 L96]`
- **Components (verbatim)**: Data Quality Gate, Scale Gate, Owner Approval Gate.
- **Responsibility**: *"Chặn scale khi chưa đủ điều kiện"* — compute conditions, bundle evidence, **propose**;
  approval is the owner's.
- **Contracts here**: `CTR-012` ads_data_quality_check *(M6, MISSING→M6-P0708)*, `CTR-013` ads_scale_request
  *(M6, MISSING→M6-P0709)*, `CTR-026` Scale-Gate approval flow *(M6+Owner, MISSING→M6-P0709)*, `CTR-019` POST
  /api/admin/ads/scale-requests *(M6, MISSING→M6-P0712)*, `CTR-024` worker data_quality_checker *(M6,
  MISSING→M6-P0713; PASS/HOLD/FAIL output)*.
- **Must-not-do**: `[DOC §4 L79]` *"Tự tăng ngân sách, tự bật campaign, bỏ qua owner approval"* → `[REG
  RULE-010]` (**no executable scale path**; FAIL-006 auto-scale), `[REG RULE-017]` (risk/suppression **hard
  veto**; SMK-009), `[REG RULE-009]` (LOW/HOLD never scale evidence); SMK-012 (no owner approval → no scale).
- **Accepted finding**: `ads_scale_request` = inert data with `budget_cap` + `rollback_condition`; Risk row is a
  hard veto re-checked at approval time; thresholds **M6-OD-002 OPEN** `[[RESEARCH_SCALE_GATE_WORKFLOW]]`.

### 1.8 Learning `[DOC §5 L97]`
- **Components (verbatim)**: Strategy libraries, scoring, candidate generation, review queue, guarded publish.
- **Responsibility**: *"Tối ưu có kiểm soát theo dữ liệu thật"* — seed→run→learn→review→publish, guarded at
  every stage.
- **Contracts here**: `CTR-014` ads_learning_candidate *(M6, MISSING→M6-P0710)*, `CTR-020` POST
  /api/admin/ads/learning-candidates *(M6, MISSING→M6-P0712)*.
- **Must-not-do**: `[DOC §4 L80]` *"Cho machine tự publish toàn quyền hoặc bịa persona/keyword/hook gốc"* →
  `[REG RULE-011]` (guarded learning; seed-only-from-canon; learn only after seed + clean verified signals),
  `[REG LEX-006]` (forbidden cell). Auto-publish **BLOCKED** while **M6-OD-006 OPEN**; content **framework-only**
  while **M6-OD-007 OPEN**; SMK-011 (candidate outside safe range → hold).
- **Accepted finding**: six libraries lock **purpose + seed-source** verbatim; **seed content is BLOCKED, never
  guessed**; Learn scores exactly 5 dims (persona/keyword/hook/landing/CTA) — Behavior/Negative-Keyword scoring
  is `[EXT]` candidate, not doc-mandated `[[RESEARCH_STRATEGY_LIBRARIES]]`.

### 1.9 Evidence `[DOC §5 L98]`
- **Components (verbatim)**: Audit log, evidence item, smoke report, release review.
- **Responsibility**: *"Chứng minh đủ điều kiện cho từng phase"* — the proof layer every other layer writes into.
- **Contracts here**: `CTR-025` Evidence package (owner review pack) *(M6, **DRAFT_LOCKED** content-level §22;
  file format = pack HARDENING)*.
- **Must-not-do**: nothing is PASS without audit/evidence/smoke/dashboard-trace/rollback; executors **never
  self-certify** → `[REG RULE-015]` (mirrors the pack's own no-self-certify discipline).
- **Accepted finding** `[PACK]`: a **SCHEMA_CHANGELOG gap** for hardening rules H01/H02/H03 was flagged in DOC
  consolidation (M6-P0112) — non-blocking, recorded for owner/registry, not fixed here (00-spec read-only).

---

## 2. Contract-to-layer index — "where each `M6-CTR` lives" `[REG CONTRACT_REGISTER]`

All **26** contracts, each assigned to exactly one home layer (consumed inputs noted where they cross).

| CTR | Object | Owner | Status | Home layer |
|---|---|---|---|---|
| 001 | ads_measurement_event | M6 | DRAFT_LOCKED | Attribution |
| 002 | ads_attribution_context | M6 | DRAFT_LOCKED | Attribution |
| 003 | event_registry | CONSUMED | MISSING→P0701 | Source |
| 004 | web_event_logs | M6 | MISSING→P0703 | Tracking |
| 005 | guest_contacts | CONSUMED | MISSING→P0702 | Source |
| 006 | guest_marketing_consent_snapshot | CONSUMED | MISSING→P0702 | Source |
| 007 | conversion_events | M6/Core | MISSING→P0704 | Outbox |
| 008 | marketing_measurement_outbox | M6 | MISSING→P0705 | Outbox |
| 009 | customer_segments | CONSUMED | MISSING→P0706 | Outbox (consumed) |
| 010 | customer_segment_members | CONSUMED | MISSING→P0706 | Outbox (consumed) |
| 011 | marketing_audience_outbox | M6 | MISSING→P0706 | Outbox |
| 012 | ads_data_quality_check | M6 | MISSING→P0708 | Gate |
| 013 | ads_scale_request | M6 | MISSING→P0709 | Gate |
| 014 | ads_learning_candidate | M6 | MISSING→P0710 | Learning |
| 015 | Dashboard KPI contract | M6 | DRAFT_LOCKED (thresholds OPEN) | Dashboard |
| 016 | POST /api/ads/events/track | M6 | MISSING→P0711 | Tracking |
| 017 | POST /api/ads/conversions | M6 | MISSING→P0711 | Outbox |
| 018 | GET /api/admin/ads/dashboard | M6 | MISSING→P0712 | Dashboard |
| 019 | POST /api/admin/ads/scale-requests | M6 | MISSING→P0712 | Gate |
| 020 | POST /api/admin/ads/learning-candidates | M6 | MISSING→P0712 | Learning |
| 021 | worker marketing_measurement_dispatcher | M6 | MISSING→P0713 | Integration |
| 022 | worker marketing_audience_dispatcher | M6 | MISSING→P0713 | Integration |
| 023 | worker attribution_materializer | M6 | MISSING→P0713 | Attribution |
| 024 | worker data_quality_checker | M6 | MISSING→P0713 | Gate |
| 025 | Evidence package | M6 | DRAFT_LOCKED (content) | Evidence |
| 026 | Scale Gate approval flow | M6+Owner | MISSING→P0709 | Gate |

**Placement totals**: Source 3 · Tracking 2 · Outbox 4 (+2 consumed) · Integration 2 · Attribution 3 ·
Dashboard 2 · Gate 5 · Learning 2 · Evidence 1 = **26**. Every CTR placed exactly once; 4 DRAFT_LOCKED
(001/002/015-formulas/025-content), the rest MISSING with a named producing prompt.

## 3. Cross-cutting invariants (the spine across layers) `[REG RULES_LOCKED]`

These are not a layer; they hold **across** layers and every design prompt must preserve them:

- **Event-registry gate** `[RULE-001]` (Source→Tracking): unknown event → reject/HOLD (SMK-001).
- **Consent fail-closed, two checkpoints** `[RULE-002]` (Source→Outbox→Integration): valid consent required at
  **event time** and re-validated at **send time**; else no external/audience/CRM (SMK-002)
  `[[RESEARCH_IDENTITY_CONSENT]]`.
- **Revenue only from ORDER_VERIFIED** `[RULE-003]` (Attribution→Dashboard→Gate): quote/cart/draft/waiting are
  never revenue (SMK-004/005/015).
- **Outbox-not-direct** `[RULE-004]` (Tracking→Outbox→Integration): no external send from a runtime request.
- **Mandatory dedup** `[RULE-005]` (Integration): locked keys; no double count (SMK-003).
- **No executable scale path** `[RULE-010]` + **risk hard-veto** `[RULE-017]` (Gate): compute & propose only.
- **Guarded learning** `[RULE-011]` + **no fabricated origin / no full auto-publish** `[LEX-006]` (Learning).
- **Staged immutables** `[RULE-H01]`: `global_gateway_state=BLOCKED`, `production_flag=OFF` — no layer flips
  them.
- **No raw PII / secrets** `[RULE-014 / H02]`: masked / `secret_ref` in every layer.
- **Core owner wins on conflict** `[RULE-018]`: M6 invents no event/pricing/policy/trigger/scale rule.
- **No self-certify** `[RULE-015]` (Evidence): executors write evidence; the gate/judge decides.

## 4. Verification pass + accepted findings (this prompt has no downstream critic) `[PACK]`

Because the ledger routes M6-P0300 → M6-P0301 with **no `M6-PC0300`**, an independent verification pass was run
over this baseline before finalizing (results folded in above):

- **Critic-blocker check** `[REG]`: all 12 research critics `M6-PC0200..0211` = PASS / 0 open_blockers
  (verified). **No BLOCKER finding outstanding.**
- **Contract completeness** `[PACK]`: all 26 CTRs placed exactly once (§2), owner/status matched to
  CONTRACT_REGISTER; no CTR dropped or duplicated.
- **Must-not-do traceability** `[PACK]`: each layer's prohibition traced to a `[DOC §4]`/`[DOC §9]` cell **and**
  its normative RULE.
- **Owner-decision preemption** `[PACK]`: no OPEN decision resolved — OD-002/003/004/005/006/007/011 remain
  gates, placed in §5, never answered here.

Non-blocking findings folded in: outbox retry/dead-letter (SMK-016 proposed), attribution immutability
(SMK-018 proposed), the 4/7 cross-module boundary-smoke coverage gap `[[RESEARCH_CROSS_MODULE_CONTRACTS]] §2.1`,
and the H01/H02/H03 SCHEMA_CHANGELOG gap (§1.9). None blocks this baseline; all are owner/registry items.

## 5. Owner-decision dependencies mapped to layers (no decision pre-empted) `[REG DECISION_REGISTER]`

| Decision | Status | Layer(s) it gates |
|---|---|---|
| M6-OD-002 (CPA/ROAS/AOV/verified-rate thresholds) | OPEN | Dashboard (alerts), Gate (scale conditions) |
| M6-OD-003 (hash policy / allowed Pixel-CAPI-Offline fields) | OPEN | Integration (CAPI hash) |
| M6-OD-004 (Meta/Google connector first) | OPEN | Integration (pilot scope) |
| M6-OD-005 (primary attribution model) | OPEN | Attribution, Gate (scale ROAS basis) |
| M6-OD-006 (learning safe range) | OPEN | Learning (auto-publish BLOCKED until defined) |
| M6-OD-007 (persona/keyword/hook content fill) | OPEN | Learning (framework-only until locked) |
| M6-OD-001 (Hero SKU Phase-1 lock) | OPEN | Learning (Landing/CTA), pilot config |
| M6-OD-011 (target repo/stack) | OPEN | all layers — where components are actually built |
| M6-ENTRY-001..004 | OPEN | Source (revenue/channel/event/public-privacy inputs) — fail-closed |

## 6. Boundary & safety guards `[BRIEF / REG §18]`

- **Measure-only** at every module edge: no pricing/order/payment (M3), advisory content (M4), raw
  webhook/public reply (M5), live-as-revenue (M7), order-state change (M8), CRM send (CRM), commission
  (Finance) — `[REG RULE-003/010/012/013/017/019/021/H03]`.
- **Staged**: BLOCKED/OFF — this baseline sends nothing, scales nothing, publishes nothing; it is a plan.
- **No raw PII / secrets** anywhere — masked / `secret_ref` `[REG RULE-014 / H02]`.
- **Channel-origin content** is untrusted DATA, never instructions `[REG RULE-H03 / BRIEF rule 6]`.

## 7. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| The nine layers + their components + roles | `[DOC §5 L88–98]` — owner-mandated (verbatim) |
| Per-layer must-not-do | `[DOC §4 L72–81]` / `[DOC §19 L371–379]` + `[REG RULES_LOCKED]` — owner-mandated |
| Contract identities, owners, statuses, producing prompts | `[REG CONTRACT_REGISTER]` (`[DOC §13/§10/§11/§14/§19]`) — owner-mandated shapes; MISSING values OPEN |
| Cross-cutting invariants | `[REG RULES_LOCKED RULE-001..021 + H01–H03]` — owner-mandated (H01–H03 = pack hardening) |
| Layer→contract **assignment**; data-flow ordering; verification-pass framing; folded-in non-blocking findings | `[PACK]` / `[EXT]` — owner-review design proposals, NOT owner requirements |

*This baseline is plan-only: it writes no code, sends nothing, scales/publishes nothing, resolves no owner
decision, and flips no flag; `global_gateway_state=BLOCKED`, `production_flag=OFF`.*
