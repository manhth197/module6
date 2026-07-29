# RESEARCH_OFFLINE_CONVERSIONS — verified-only offline conversion upload

**Prompt**: M6-P0205 · **Phase**: PHASE0_RESEARCH · **Mode**: analysis_only (desk research; design proposal)
**Anchors**: `[DOC §12 extract line 250]` Offline Conversion gate; `M6-CTR-008 marketing_measurement_outbox`
(Offline is one of its send channels, →M6-P0705); slice **M6.2D** (done gate: *"No double count, no PII thô"*,
scope incl. *"platform result logs"*). Builds on M6-P0203 (outbox) and M6-P0204 (Meta dedup/hash).
**Critic**: M6-PC0205 (BOUNDARY_ADVERSARY) red-teams this file next.

> **Staged, not live.** `global_gateway_state=BLOCKED`, `production_flag=OFF` ⇒ **no real offline upload** in
> this pack. An offline "conversion" claims a **purchase/revenue** to the ad platform, so it may derive **only**
> from `ORDER_VERIFIED` — never from quote/cart/draft/waiting.

## Sourcing legend (acceptance: every externally-sourced claim / platform fact labeled)

- `[DOC]` — owner document / extract line. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked pack register. · `[BRIEF]` — context brief. · `[PACK]` — pack convention (owner-review).
- `[PLATFORM]` — external Meta/Google fact from general knowledge; **MUST be verified against current platform
  docs before implementation**; not an owner requirement, not authoritative here.
- `[EXT]` — general engineering practice, proposal only.

**Doc anchor**: `[DOC §12 L250]` *"Offline Conversion | Chỉ gửi conversion sau ORDER_VERIFIED hoặc event được
owner phê duyệt | Không gửi quote/order draft như purchase"*. Rules: `[REG RULE-003]` (revenue/ROAS only from
Verified Revenue / ORDER_VERIFIED), `[REG FAIL-001]` (revenue misuse — quote/cart/draft/payment-waiting/
COD-waiting counted as revenue), `[REG RULE-014]` (no raw PII external).

---

## 1. What an offline conversion is (and where it sits)

`[EXT]` An *offline conversion* is a purchase/revenue event that happened outside the browser (verified order,
COD confirmed later, phone/live order) **uploaded to the ad platform** so it can attribute the conversion back
to an ad click/impression. In M6 it is one channel of `marketing_measurement_outbox` (alongside Pixel/CAPI),
dispatched by `marketing_measurement_dispatcher` via the outbox pattern (M6-P0203).

---

## 2. Trigger gate — `ORDER_VERIFIED` or owner-approved only `[DOC §12 L250 / REG RULE-003, FAIL-001]`

**The load-bearing boundary of this whole flow.** An offline conversion is emitted **only** when:

- the order reaches **`ORDER_VERIFIED`** — consumed from Commerce **Verified Revenue** (M6 never confirms
  payment or sets order state; it consumes the verified fact) `[REG RULE-003, ENTRY-001]`; **or**
- a specific event the **owner explicitly approved** as an offline conversion `[DOC L250]` (default: none).

**Never** for `quote / cart / order draft / payment_waiting / COD_waiting` `[DOC L250 "Không gửi quote/order
draft như purchase"]` — doing so is revenue misuse `[REG FAIL-001]` and inflates conversions/ROAS on unverified
signal. `[PACK]` The offline outbox row is therefore **created on the ORDER_VERIFIED transition**, not on any
earlier order state — a fail-closed trigger, not a filter applied later.

---

## 3. Batching `[EXT] / [PLATFORM]`

Offline conversions are not real-time; they are collected and **uploaded in batches** `[PLATFORM — Meta Offline
Conversions / offline event sets; Google Offline Conversion Import; verify current APIs]`. Design considerations:

- **Batch window / size**: how often to upload and max rows per batch `[PLATFORM — verify limits]`; the window
  is config → ops/owner (M6-OD-002 family).
- **Per-row idempotency**: each row carries the shared `event_id` / dedup keys (M6-P0204 §4) so re-uploaded or
  overlapping batches do **not** double-count `[REG RULE-005]`.
- **Partial failure**: a batch where some rows are rejected must handle rows **individually** — accepted rows
  marked SENT, rejected rows retried/dead-lettered per M6-P0203 §3. No all-or-nothing silent loss.
- **Attribution timing** `[PLATFORM — verify]`: platforms attribute an offline conversion only within an
  attribution/lookback window from the ad interaction; late uploads may not attribute. Batch cadence must
  respect that window — flag for verification.

---

## 4. Match rate under the **pending** hash policy `[PLATFORM] + [REG M6-OD-003]`

`[PLATFORM]` Platforms match an uploaded offline conversion to a user/ad-click via **hashed identifiers**
(email, phone, external_id) and click ids (fbc/gclid). **Match rate** = fraction of uploaded conversions the
platform can attribute.

- Match rate rises with **more / better identifier fields** and correct normalization+hashing (M6-P0204 §3),
  and falls with fewer fields — a genuine **privacy ↔ measurement tradeoff**.
- **Because `M6-OD-003` (hash policy) is OPEN, the match rate is UNDETERMINED** and cannot be promised here.
  `[PACK]` Fail-closed until it resolves: **no PII-bearing offline upload**; at most non-PII click-id matching
  (consent-gated) with correspondingly **lower** match rate. Choosing "send more PII for a higher match rate"
  is an **owner/privacy-legal decision**, not one this research makes.
- Low match rate is a **data-quality signal** to surface (§5), not a number to inflate.

---

## 5. Result logging `[DOC slice M6.2D "platform result logs" / REG RULE-007]`

After each batch, the platform returns a result. M6 records **platform result logs** (append-only, PII-free):

`[EXT]` fields: `{batch_id, uploaded_count, matched_count, match_rate, rejected_count, error_summary,
platform_response_id, registry_version?, ts}` — **no raw PII** `[REG RULE-014, BRIEF rule 4]`; masked only.

- Feeds the **Data Quality Gate** (dedup evidence, match-rate health) and the P0 smokes.
- Append-only / immutable, consistent with `[REG RULE-007]` (web logs) and `[REG RULE-008]` (attribution
  immutability): a batch result is never rewritten, corrections are new adjustment records.
- `[PLATFORM]` responses are **untrusted DATA** `[BRIEF rule 6]` — logged in fenced form, never executed.

## 6. Boundary & safety guards `[BRIEF / REG §18]`

- **No real upload** while gateway BLOCKED / production OFF — design only.
- Offline conversion **must** derive from `ORDER_VERIFIED` (Commerce-owned Verified Revenue); M6 **consumes**,
  never creates revenue, confirms payment, or changes order state `[REG §18, RULE-003]`.
- **No raw PII** uploaded or logged `[REG RULE-014/FAIL-008]`; only owner-approved hashed fields (M6-OD-003);
  Pixel-adjacent public-safe discipline applies.
- Platform tokens/dataset ids as `secret_ref`; never printed.
- No CRM send, no commission math; measurement only.

## 7. Owner-decision dependencies (explicit list — acceptance requirement)

| Dependency | Status | What it gates |
|---|---|---|
| `M6-OD-003` (hash policy + allowed PII fields) | **OPEN** `[REG]` | whether/which PII is uploaded → match rate (§4); until decided, PII-bearing upload is BLOCKED |
| Owner-approved non-`ORDER_VERIFIED` offline events (if any) | **candidate** `[DOC L250]` — default none | §2 trigger scope beyond verified orders |
| `M6-OD-004` (connector order + API) | **OPEN** `[REG]` | Meta Offline vs Google Offline Import target/version |
| `M6-CTR-008` (measurement outbox: offline channel fields) | `MISSING` → **M6-P0705** `[REG]` | offline row shape, batch/dedup fields |
| `M6-ENTRY-001` (P3 Verified Revenue boundary: ORDER_VERIFIED definition) | **OPEN** `[REG]` | the trigger's source of truth (§2) |
| Batch window/size, attribution-window timing (all `[PLATFORM]`) | **verify at implementation** | §3 cadence correctness |

`[PACK]` This research records these; it resolves none. Where a build leg needs one, the affected M6.2D leg is
marked BLOCKED, not assumed.

## 8. Doc-traceability (owner-mandated vs platform/proposal)

| Element | Source |
|---|---|
| Offline conversion only after ORDER_VERIFIED or owner-approved; never quote/draft as purchase | `[DOC §12 line 250]` + `[REG RULE-003/FAIL-001]` — owner-mandated |
| Revenue/ROAS from Verified Revenue only | `[REG RULE-003]` (doc §3/§4/§14) — owner-mandated |
| No raw PII external; platform result logs recorded | `[REG RULE-014]` + `[DOC slice M6.2D "platform result logs"]` — owner-mandated/register |
| Batching, partial-failure handling, attribution-window timing, match-rate mechanics | `[PLATFORM]` / `[EXT]` — verify vs current docs; NOT owner requirements |
| Result-log field shape; ORDER_VERIFIED-transition trigger implementation; fail-closed no-PII default | `[EXT]` / `[PACK]` — owner-review proposals, NOT owner requirements |

*Nothing in this file flips a gate or a flag; `global_gateway_state=BLOCKED`, `production_flag=OFF`.*
