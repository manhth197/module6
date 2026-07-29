# DATA_MODEL_BASELINE — M6-owned data objects (doc §13)

**Prompt**: M6-P0301 · **Phase**: PHASE0 (design) · **Mode**: plan_only (no code, no migration, no DDL, no call)
**Anchors**: `[DOC §13 extract lines 261–276]` Data Object Contract catalog; `[DOC §10 L191–211]` /
`[SPEC §10.1]` ads_measurement_event (DRAFT_LOCKED, 20 fields); `[DOC §11 L215–242]` / `[SPEC §10.2]`
ads_attribution_context (DRAFT_LOCKED, 19 fields + immutability L242); `[DOC §12 L246–257]` dedup/outbox/
send_policy; `[SPEC §12]` data-model tables, `[SPEC §13]` state machines. Ownership split =
`[REG CONTRACT_REGISTER]`. **Builds on** `[[ARCH_BASELINE]]` (M6-P0300) §2 contract-to-layer index.
**No dedicated critic** follows this prompt in the ledger (M6-P0301 → M6-P0302) — an independent verification
pass was run before finalizing (§8).

> **Data-model frame.** Module 6 **owns 9 objects and consumes 5** (doc §13). The whole model is fail-closed
> around three hard boundaries: **(1) history is append-only** (`web_event_logs`, audit); **(2) attribution is
> immutable after `ORDER_VERIFIED`** — corrections are *adjustment records*, never in-place edits; **(3)
> `revenue_value` is sourced ONLY from Commerce Verified Revenue** — M6 never computes it. Only **2 objects are
> field-locked** (measurement_event, attribution_context); the rest carry a purpose and **await harmonization**
> — this baseline **invents no field** for a MISSING object. `global_gateway_state=BLOCKED`,
> `production_flag=OFF`.

## Sourcing legend (acceptance: every externally-sourced claim labeled)

- `[DOC]` — owner document / extract line, reproduced in `[SPEC]`. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked pack register. · `[BRIEF]` — context brief. · `[PACK]` — pack convention (owner-review). ·
  `[EXT]` — general engineering practice, **proposal only**.

---

## 1. Entity list — M6-owned vs consumed `[DOC §13 L261–276 / REG CONTRACT_REGISTER]`

Purpose column verbatim from `[DOC §13]`. **Ownership** and **Status** from `[REG CONTRACT_REGISTER]`
(`M6` = M6 writes; `CONSUMED` = owned elsewhere, M6 references only).

### 1.1 M6-owned objects (9)
| Object / table | CTR | Status | Purpose (verbatim) `[DOC]` | Home layer `[[ARCH_BASELINE]]` |
|---|---|---|---|---|
| `web_event_logs` | 004 | MISSING→P0703 (partial L117) | Append-only web/landing/tracking logs *(Module 6, không sửa lịch sử)* | Tracking |
| `conversion_events` | 007 | MISSING→P0704 | Source chuyển đổi nội bộ trước khi gửi measurement *(Module 6/Core)* | Outbox |
| `marketing_measurement_outbox` | 008 | MISSING→P0705 (partial L252) | Hàng đợi gửi Pixel/CAPI/Offline *(Worker only)* | Outbox |
| `marketing_audience_outbox` | 011 | MISSING→P0706 | Hàng đợi sync audience *(Worker only)* | Outbox |
| `ads_attribution_context` | 002 | **DRAFT_LOCKED** (19 fields) | Chain campaign/adset/ad/page/live/comment/messenger/referral | Attribution |
| `ads_measurement_events` | 001 | **DRAFT_LOCKED** (20 fields) | Event đã chuẩn hóa phục vụ dashboard/ROAS *(Module 6)* | Attribution |
| `ads_data_quality_check` | 012 | MISSING→P0708 | Kết quả kiểm dữ liệu *(Data Quality Gate)* | Gate |
| `ads_scale_request` | 013 | MISSING→P0709 | Đề nghị scale ngân sách *(Owner approval required)* | Gate |
| `ads_learning_candidate` | 014 | MISSING→P0710 | Candidate keyword/persona/hook/creative/landing/CTA *(Learning review queue)* | Learning |

### 1.2 Consumed objects (5) — referenced by FK, **not** M6-owned
| Object | CTR | Status | Purpose (verbatim) `[DOC]` | Owner |
|---|---|---|---|---|
| `event_registry` | 003 | MISSING→P0701 | Danh sách event hợp lệ, owner, channel, data sensitivity, external send policy | Core Event Governance |
| `guest_contacts` | 005 | MISSING→P0702 | Guest lead identity và contact fingerprint | Customer identity |
| `guest_marketing_consent_snapshot` | 006 | MISSING→P0702 | Consent tại thời điểm event | Consent (fail-closed) |
| `customer_segments` | 009 | MISSING→P0706 | Nguồn segment được duyệt | CRM/Ads segmentation |
| `customer_segment_members` | 010 | MISSING→P0706 | Thành viên trong segment *(Không lạm dụng làm trigger owner)* | CRM |

*(Evidence/audit objects — `CTR-025` evidence package, audit log — are cross-cutting Evidence-layer artifacts,
not row-storage entities; covered by `[[ARCH_BASELINE]]` §1.9.)*

---

## 2. The two field-locked schemas `[SPEC §10.1/§10.2 / DOC §10–11]`

These are the **only** objects with a locked field-level schema. Reproduced faithfully; **PII-class fields are
flagged** — they are stored/referenced masked or as `secret_ref`, never raw, in any evidence `[REG RULE-014 /
H02]`.

### 2.1 `ads_measurement_event` — DRAFT_LOCKED, 20 fields `[DOC §10 L191–211]`
`event_id`, `event_code`, `event_ts`, `customer_id?` **[PII→ref/mask]**, `guest_id?` **[PII→ref/mask]**,
`page_id?`, `live_session_id?`, `campaign_id?`, `adset_id?`, `ad_id?`, `sales_session_id?`,
`quote_snapshot_id?`, `order_code?`, `revenue_value?` **[from Verified Revenue only — §5]**, `currency: VND`
**(locked)**, `attribution_context: object` **(embeds §2.2)**, `consent_snapshot_id?`, `idempotency_key`,
`correlation_id`, `data_quality_status: PASS|HOLD|FAIL` **(state machine, `[SPEC §13]`)**.

### 2.2 `ads_attribution_context` — DRAFT_LOCKED, 19 fields `[DOC §11 L215–234]`
`campaign_id?`, `campaign_name?`, `adset_id?`, `adset_name?`, `ad_id?`, `ad_name?`, `page_id`,
`live_session_id?`, `comment_id?`, `messenger_thread_id?`, `psid?` **[PII→mask]**, `referral_link_id?`,
`diamond_id?`, `entry_channel: FACEBOOK_AD|LIVE_ORGANIC|DIAMOND_LINK|CRM|DIRECT`, `attribution_window`,
`first_touch_event_id?`, `last_touch_event_id?`, `source_confidence: HIGH|MEDIUM|LOW`,
`conflict_status: NONE|MULTI_TOUCH|MISSING_SOURCE|DUPLICATE_RISK`.

- **Traceability requirement** `[DOC §11 L236]`: the context must trace back
  *campaign/adset/ad/page/live/comment/Messenger → quote/order/ORDER_VERIFIED*.
- **Diamond + Ads co-occurrence** `[DOC §11 L238]`: store the **full** context; **Finance/Commission owner**
  decides commission, never Ads Measurement `[REG RULE-019]`.
- **Missing/conflict** `[DOC §11 L240]`: `source_confidence=LOW` or `HOLD` — **never** scale evidence
  `[REG RULE-009]`.

---

## 3. Relationships (reference graph) `[PACK — derived from DOC §10–13 refs]`

The order comes from `[DOC §11 L236]` + `[[ARCH_BASELINE]]`; the edge model is a `[PACK]` proposal.

```
web_event_logs ──(normalized source)──▶ conversion_events ──(feeds)──▶ ads_measurement_events
                                                                          │  embeds
                                                                          ▼
                                                              ads_attribution_context
ads_measurement_events ──refs──▶ event_registry(event_code) [CONSUMED, RULE-001]
                       ──refs──▶ guest_contacts(customer_id|guest_id) [CONSUMED]
                       ──refs──▶ guest_marketing_consent_snapshot(consent_snapshot_id) [CONSUMED]
                       ──refs──▶ quote_snapshot_id, order_code  [Commerce, CONSUMED]
                       ──enqueue──▶ marketing_measurement_outbox ──worker──▶ Pixel/CAPI/Offline [egress]
customer_segments/members [CONSUMED] ──▶ marketing_audience_outbox ──worker──▶ audience sync
ads_attribution_context ──traces──▶ campaign/adset/ad/page/live/comment/messenger/referral
                                    → quote/order/ORDER_VERIFIED  [DOC §11 L236]
Commerce Verified Revenue [CONSUMED] ──(sole source)──▶ ads_measurement_events.revenue_value  [DOC §12 L256]
ads_data_quality_check ──evaluates──▶ measurement_events + attribution  → PASS/HOLD/FAIL
ads_scale_request ──bundles──▶ dq_check + attribution + dashboard evidence + entry evidence [DOC §16]
ads_learning_candidate ──scored from──▶ verified+DQ-pass signals + strategy libraries [DOC §17]
```

- **Every measurement event's `event_code` must resolve in `event_registry`** before storage/send
  `[REG RULE-001]`; an unregistered code is rejected/held, never stored as valid.
- **`revenue_value` has exactly one source** — Commerce Verified Revenue `[DOC §12 L256]`; no other edge writes
  it `[REG RULE-003]`.

---

## 4. Append-only zones `[DOC §13 L264 / REG RULE-007/008]`

| Zone | Rule | Behavior |
|---|---|---|
| `web_event_logs` | `[DOC §13 L264]` *"Append-only … không sửa lịch sử"* + `[REG RULE-007]` | insert-only; **never** update/delete event history |
| Adjustment records (attribution) + audit log | `[DOC L242 / REG RULE-008]` | append-only, immutable; the **doc-locked** adjustment-record shape is `{actor, reason, audit, evidence}` (status-transition audit adds `{from→to, evidence_ref, ts}` `[PACK]`) |
| `ads_measurement_events` | `[PACK]` (measurement history) | events appended; corrections handled via attribution adjustment (§5), not row mutation |

**Append-only ≠ status-transition.** The outboxes and request/candidate objects have a **row status that
transitions** (queued→sent/retry→dead-letter; DRAFT→PROPOSED→…; CANDIDATE→APPROVED/…) — those transitions are
**audited** `[REG RULE-008]`, not history rewrites. See §5 for what is truly immutable.

---

## 5. Immutability boundaries — the crux `[DOC §11 L242 / SPEC §13 / REG RULE-008]`

- **`ads_attribution_context` is mutable UNTIL `ORDER_VERIFIED`, then IMMUTABLE** `[SPEC §13 state machine,
  extract L242]`: *"Attribution snapshot phải immutable sau khi order verified; mọi correction phải có
  adjustment record, actor, reason, audit và evidence."* After verify, **no in-place edit** — every correction
  is a **new adjustment record** (`{actor, reason, audit, evidence}`), exercised by proposed smoke **SMK-018**
  `[[ARCH_BASELINE]] §1.5`.
- **Verified revenue is never overwritten** `[REG CONTRACT_REGISTER CTR-023 attribution_materializer duty: "no
  verified-revenue overwrite"]`; the materializer aggregates snapshots but cannot mutate a verified figure.
- **`revenue_value` is consume-only** `[DOC §12 L256]` — M6 records what Commerce verified; it never
  (re)computes revenue `[REG RULE-003]`.
- **Boundary summary**: history = append-only (§4); pre-verify attribution = mutable; **post-verify attribution
  + verified revenue = immutable**; status objects = audited transitions. This is the fail-closed spine of the
  model.

---

## 6. Which fields await harmonization `[REG CONTRACT_REGISTER]`

The baseline **reproduces** locked fields and **invents none** for MISSING objects — it names the harmonization
prompt that must produce each schema before the dependent slice's entry gate may pass.

| Object | Field status | Awaiting |
|---|---|---|
| `ads_measurement_event` (001) | **field-locked** (20 fields, §2.1) | — (locked; storage binding M6-P0707) |
| `ads_attribution_context` (002) | **field-locked** (19 fields, §2.2) | — (locked) |
| `web_event_logs` (004) | **partial** — page, session, source, consent snapshot, event_ts, idempotency `[DOC L117]` | full schema **M6-P0703** |
| `marketing_measurement_outbox` (008) | **partial** — error_log, next_retry_at `[DOC L252]` | full schema **M6-P0705** |
| `conversion_events` (007) | **no field schema** (purpose only) | **M6-P0704** |
| `marketing_audience_outbox` (011) | **no field schema** | **M6-P0706** |
| `ads_data_quality_check` (012) | **no field schema** (gate items exist §15) | **M6-P0708** |
| `ads_scale_request` (013) | **no field schema** (conditions exist §16) | **M6-P0709** |
| `ads_learning_candidate` (014) | **no field schema** (lifecycle exists §17) | **M6-P0710** |
| consumed: `event_registry`(003), `guest_contacts`(005), `consent_snapshot`(006), `customer_segments`(009), `segment_members`(010) | **consumed shape undefined** | **M6-P0701 / P0702 / P0706** |

`[PACK]` Where a build leg needs a MISSING schema, the affected slice is **BLOCKED**, not assumed.

## 7. Cross-cutting data invariants `[DOC §12 / REG RULES_LOCKED]`

- **Locked keys** `[DOC §12 L254–255 / REG RULE-005]`: `dedup_key = platform + event_code +
  customer_or_guest_key + event_ts_bucket + source_event_id`; `idempotency_key = event_code + page_id +
  session_id + raw_event_hash + normalized_ts`. Verbatim; no double count.
- **send_policy** `[DOC §12 L257]`: `consent_valid AND event_in_registry AND data_quality_pass AND
  not_duplicate` — all four required before any external row is sent.
- **State-machine enums (locked)** `[SPEC §13]`: `data_quality_status` PASS/HOLD/FAIL; `source_confidence`
  HIGH/MEDIUM/LOW (LOW/HOLD never scale evidence); `conflict_status`
  NONE/MULTI_TOUCH/MISSING_SOURCE/DUPLICATE_RISK; `entry_channel` five-value enum (§2.2).
- **PII discipline** `[REG RULE-014 / H02]`: `customer_id`, `guest_id`, `psid`, guest "contact fingerprint",
  `comment_id`/`messenger_thread_id` (channel-scoped) are PII/identity-class — masked or `secret_ref` at rest
  and in evidence; `currency` locked to `VND` `[DOC L206]`.

## 8. Verification pass (this prompt has no downstream critic) `[PACK]`

Ledger routes M6-P0301 → M6-P0302 with **no `M6-PC0301`**; an independent 3-lens verification was run before
finalizing (findings folded in above):

- **Field fidelity & ownership** `[PACK]`: the 20 + 19 locked fields match `[DOC §10/§11]`/`[SPEC §10.1/10.2]`
  exactly; the 9-owned / 5-consumed split matches `[REG CONTRACT_REGISTER]`.
- **Immutability & append-only** `[PACK]`: §4/§5 match `[SPEC §13]` state machines and `[DOC L242/L264/L256]`
  (no boundary invented or relaxed).
- **No invented fields / no OD preemption** `[PACK]`: no field schema written for any MISSING object; no OPEN
  owner decision resolved (§9).

## 9. Owner-decision dependencies (no decision pre-empted) `[REG DECISION_REGISTER]`

| Decision | Status | What it gates in the data model |
|---|---|---|
| M6-OD-003 (hash policy / allowed fields for Pixel/CAPI/Offline) | OPEN | which PII fields may be hashed vs dropped in outbox payloads |
| M6-OD-008 (PAYMENT_COMPLETED as revenue-adjacent?) | OPEN | whether `PAYMENT_COMPLETED` ever touches `revenue_value`; default = non-revenue, ORDER_VERIFIED only |
| M6-OD-002 (thresholds) | OPEN | `ads_data_quality_check` / `ads_scale_request` pass criteria (field values, not shape) |
| M6-OD-005 (primary attribution model) | OPEN | how `first/last_touch_event_id` + confidence feed the scale model |
| M6-OD-011 (target repo/stack) | OPEN | the physical storage tech for all tables |
| M6-CTR-004/007/008/011/012/013/014 + consumed 003/005/006/009/010 | MISSING | field schemas (§6) — produced by M6-P0701..0710 |

## 10. Boundary & safety guards `[BRIEF / REG §18]`

- **Plan-only**: no DDL, no migration, no table creation, no data write — a model on paper.
- **No raw PII / secrets** in the model or evidence — masked / `secret_ref` `[REG RULE-014 / H02]`.
- **Consume-only at module edges**: `revenue_value`←Commerce, identity←Customer, consent←Consent,
  segments←CRM, event_registry←Core; M6 writes none of them `[REG RULE-003/013/018 / §18]`.
- **Staged**: `global_gateway_state=BLOCKED`, `production_flag=OFF` — unchanged.
- **Channel-origin content** (comment_id/messenger text) is untrusted DATA, stored as reference, never executed
  `[REG RULE-H03]`.

## 11. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| Object catalog (14 objects, purpose, owner) | `[DOC §13 L261–276]` — owner-mandated (verbatim) |
| measurement_event 20 fields · attribution_context 19 fields | `[DOC §10 L191–211 / §11 L215–234]` (`[SPEC §10.1/10.2]`) — owner-mandated |
| Attribution immutable after ORDER_VERIFIED; corrections via adjustment record | `[DOC §11 L242]` (`[SPEC §13]`) — owner-mandated |
| web_event_logs append-only; verified revenue never overwritten; revenue_value from Commerce only | `[DOC §13 L264 / §12 L256]` + `[REG RULE-007/003 / CTR-023]` — owner-mandated |
| dedup_key / idempotency_key / send_policy; state-machine enums | `[DOC §12 L254–257]` (`[SPEC §13]`) — owner-mandated |
| Ownership split (9 owned / 5 consumed); which prompt harmonizes each MISSING schema | `[REG CONTRACT_REGISTER]` — owner-mandated |
| Reference-graph edge model; PII-class flagging; append-only-vs-status-transition framing | `[PACK]` / `[EXT]` — owner-review design proposals, NOT owner requirements |

*This baseline is plan-only: it writes no code/DDL, invents no field for any MISSING object, resolves no owner
decision, and flips no flag; `global_gateway_state=BLOCKED`, `production_flag=OFF`.*
