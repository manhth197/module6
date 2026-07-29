# RESEARCH_OUTBOX_WORKER_PATTERNS — Module 6 measurement/audience outbox + dispatchers

**Prompt**: M6-P0203 · **Phase**: PHASE0_RESEARCH · **Mode**: analysis_only (desk research; design proposal)
**Objects** `[REG CONTRACT_REGISTER]` (all `MISSING`): `M6-CTR-007 conversion_events` (M6/Core →M6-P0704),
`M6-CTR-008 marketing_measurement_outbox` (M6 worker-only →M6-P0705), `M6-CTR-011 marketing_audience_outbox`
(M6 worker-only →M6-P0706), `M6-CTR-021 marketing_measurement_dispatcher` + `M6-CTR-022
marketing_audience_dispatcher` (M6 workers →M6-P0713). Slice **M6.2C** (done gate: *"No direct external send,
retry/dead-letter pass"*); proposed smoke **M6-SMK-016**.
**Critic**: M6-PC0203 (BOUNDARY_ADVERSARY) red-teams this file next.

> **Staged, not live.** `global_gateway_state=BLOCKED`, `production_flag=OFF` ⇒ the dispatchers make **no real
> external call** in this pack; this research designs the pattern only. M6 sends **measurement + audience**
> (Pixel/CAPI/Offline/audience) through outbox+worker — it **never sends CRM** (CRM-owned) and never calls a
> platform from a runtime request.

## Sourcing legend (acceptance: every externally-sourced claim labeled)

- `[DOC]` — owner document / extract line. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked pack register. · `[BRIEF]` — context brief. · `[PACK]` — pack convention (owner-review).
- `[EXT]` — general engineering practice, **proposal only** (owner/architecture review).

**Doc anchors**: `[DOC §12 L248]` *"Pixel Browser | Chỉ gửi event public-safe, có consent và idempotency key |
Không gửi PII thô, không gửi khi consent missing"*; `[DOC §12 L249]` *"CAPI Server | Gửi từ
marketing_measurement_outbox worker … | Không gửi trực tiếp từ request runtime"*; `[DOC §12 L250]` *"Offline
Conversion | Chỉ gửi conversion sau ORDER_VERIFIED …"*; `[DOC §12 L251]` *"Audience Sync | Gửi từ
customer_segments + marketing_audience_outbox + consent pass | Không sync audience từ ad hoc query hoặc data
mart"*; `[DOC §12 L252]` *"Retry / Dead Letter | Retry có giới hạn, lưu error_log và next_retry_at | Không
retry vô hạn, không mất event không dấu vết"*; `[DOC §12 L254-255]` dedup_key / idempotency_key formulas;
`[DOC §12 L257]` *"send_policy = consent_valid AND event_in_registry AND data_quality_pass AND
not_duplicate"*; `[DOC §19 L376]` dispatcher *"Retry, dedup, error log"*; `[DOC §19 L377]` audience dispatcher
*"Consent fail-closed"*. Rules: `[REG RULE-004]` (outbox-only external send), `[REG RULE-005]` (dedup),
`[REG RULE-002]` (consent fail-closed at send time).

---

## 1. Objects & ownership

| Object | Role | Owner |
|---|---|---|
| `conversion_events` (CTR-007) | internal conversion source, written before external send `[DOC §13 L267]` | M6/Core |
| `marketing_measurement_outbox` (CTR-008) | queue for Pixel/CAPI/Offline `[DOC §13 L268]`; has `error_log`, `next_retry_at` `[DOC L252]` | M6 (worker-only) |
| `marketing_audience_outbox` (CTR-011) | queue for audience sync `[DOC §13 L271]` | M6 (worker-only) |
| `marketing_measurement_dispatcher` (CTR-021) | worker: send Pixel/CAPI/Offline; retry, dedup, error log `[DOC §19 L376]` | M6 |
| `marketing_audience_dispatcher` (CTR-022) | worker: audience sync; consent fail-closed `[DOC §19 L377]` | M6 |

---

## 2. Transactional enqueue + worker isolation `[DOC §12 L249 / §13 L268 / REG RULE-004]` + `[EXT]`

**Rule** `[DOC L249, RULE-004]`: external sends go **only** via outbox+worker, **never** directly from a runtime
request. `[EXT] transactional-outbox pattern`: the runtime that writes a `conversion_event` also inserts the
matching outbox row **in the same database transaction**. Consequences:

- Atomicity `[EXT]`: the outbox row exists **iff** the source event committed — no lost sends, no phantom sends.
- The request path does **zero** external I/O `[DOC L249]` — latency and failures of Meta/Google/CRM never
  touch the user request.
- A **separate worker** (dispatcher) reads due outbox rows and performs the external call asynchronously
  `[DOC L268 "Worker only"]`. Two isolated workers: measurement (CTR-021) and audience (CTR-022).

---

## 3. Dispatch loop: bounded retry, `error_log`/`next_retry_at`, dead-letter `[DOC §12 L252]`

`[DOC L252]` retry is **bounded**; store `error_log` and `next_retry_at`; **never infinite retry, never lose an
event without a trace**. Proposed row lifecycle `[EXT]` (fields `error_log`/`next_retry_at` are `[DOC]`):

`status: PENDING → IN_FLIGHT → SENT` | on failure `→ PENDING` (reschedule) | on exhaustion `→ DEAD_LETTER`

- Worker selects rows where `status=PENDING AND next_retry_at <= now` `[EXT]`.
- On failure: increment `attempt_count`, append to `error_log`, set `next_retry_at = now + backoff`
  (`[EXT]` exponential backoff + jitter), status back to PENDING.
- When `attempt_count >= max_attempts` → `status=DEAD_LETTER` with full trace; **not deleted** `[DOC L252 "không
  mất event không dấu vết"]`. Dead-letter rows surface for ops review and manual replay after the cause is fixed.
- `max_attempts`, backoff parameters, and the **outbox-failure-rate** alert threshold are config → **M6-OD-002**
  (§7), not invented here.
- **M6-SMK-016** `[REG]` exercises exactly this: fail N times → bounded retry with error_log/next_retry_at →
  dead-letter, no infinite retry, no silent loss.

---

## 4. Idempotent + deduped dispatch `[DOC §12 L248/L254-255 / REG RULE-005]`

Two independent mechanisms:

- **`dedup_key`** `[DOC L254]` (`platform + event_code + customer_or_guest_key + event_ts_bucket +
  source_event_id`) — prevents **duplicate outbox rows** for the same logical event (internal dedup, RULE-005).
- **`idempotency_key`** `[DOC L255]` (`event_code + page_id + session_id + raw_event_hash + normalized_ts`) —
  carried on the external dispatch so the **platform** collapses duplicates `[DOC L248 "có idempotency key"]`.

**Delivery-semantics insight** `[EXT]`: a crash **between** the external send and the `status=SENT` write causes
an at-least-once re-send. This is **safe and intended** — the `idempotency_key` makes the platform dedup, so
**at-least-once delivery + idempotency_key ⇒ effectively-once** downstream. Do **not** attempt fragile
exactly-once delivery infrastructure; do **not** drop the idempotency_key (that would double-count and trip
`[REG FAIL-001]` revenue-misuse / RULE-005). Mark `SENT` only after a confirmed dispatch; treat unconfirmed as
retryable.

---

## 5. Send-time gate chain (fail-closed, evaluated **in the worker**) `[DOC §12 L257]`

Before any external dispatch the worker evaluates `send_policy = consent_valid AND event_in_registry AND
data_quality_pass AND not_duplicate` `[DOC L257]` — **all four AND-terms**, plus doc-specific gates:

1. `consent_valid` — **re-validated at send time** (per M6-P0202 §3; audience dispatcher is *"Consent
   fail-closed"* `[DOC L377]`). Consent withdrawn between enqueue and dispatch ⇒ **drop, do not send**.
2. `event_in_registry` — per M6-P0201; plus the event's `external_send_policy` must permit the send.
3. `data_quality_pass` — the Data Quality Gate verdict.
4. `not_duplicate` — dedup_key check.
5. Channel specifics: **Offline** only after `ORDER_VERIFIED` or owner-approved event `[DOC L250]`; **Audience**
   only from approved `customer_segments` + consent pass, never ad-hoc/data-mart `[DOC L251, RULE-004]`; **Pixel**
   public-safe only, no raw PII `[DOC L248]`.

Any failed term ⇒ fail-closed (hold/skip with audit), never a partial/"best-effort" send.

---

## 6. Boundary & safety guards `[BRIEF / REG §18]`

- **Staged**: dispatchers perform **no real external call** while `global_gateway_state=BLOCKED` /
  `production_flag=OFF`; design only. This research flips nothing.
- **No CRM send** `[BRIEF, REG §18]` — M6's outbox is measurement + audience only; CRM messaging is CRM-owned.
- **No raw PII** in outbox payloads/logs `[REG RULE-014, BRIEF rule 4]`: Pixel public-safe `[DOC L248]`; CAPI/
  Offline apply hash policy (M6-OD-003); `error_log` masks any PII; `secret_ref` for platform tokens.
- Platform responses/echoes are **untrusted DATA** `[BRIEF rule 6]` — logged in fenced form, never executed.
- Worker runs isolated from the request path `[DOC L249]`; no order-state / pricing / commission side effects.

## 7. Owner-decision dependencies (explicit list — acceptance requirement)

| Dependency | Status | What it gates |
|---|---|---|
| `M6-CTR-007/008/011` shapes | `MISSING` → **M6-P0704/0705/0706** `[REG]` | table/queue fields; needed before **M6.2C** |
| `M6-CTR-021/022` worker duties | `MISSING` → **M6-P0713** `[REG]` | dispatcher contracts |
| `M6-OD-002` (thresholds inc. outbox failure rate) | **OPEN** `[REG]` | `max_attempts`, backoff, failure-rate alert (§3) |
| `M6-OD-003` (hash policy + allowed fields) | **OPEN** `[REG]` | CAPI/Offline payload PII handling (§5) |
| `M6-OD-004` (Meta vs Google connector first) | **OPEN** `[REG]` | which platform the measurement dispatcher targets in pilot |
| Consent scope/expiry (from M6-P0202) | **candidate** `[PACK]` | send-time `consent_valid` semantics (§5) |
| Retry-lifecycle state names, backoff shape, dead-letter replay procedure | **candidate** `[EXT]` | §3 mechanics (owner-review, not doc) |

`[PACK]` This research records these; it resolves none. Where a build leg needs one, the affected M6.2C leg is
marked BLOCKED, not assumed.

## 8. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| External send only via outbox+worker; never from runtime request | `[DOC §12 L249, §13 L268]` + `[REG RULE-004]` — owner-mandated |
| Bounded retry, `error_log` + `next_retry_at`, no infinite retry, no silent loss (dead-letter) | `[DOC §12 L252]` + `[DOC §19 L376]` — owner-mandated |
| dedup_key / idempotency_key formulas; Pixel carries idempotency key, public-safe, no raw PII | `[DOC §12 L248/L254/L255]` + `[REG RULE-005]` — owner-mandated |
| send_policy AND-chain; Offline-after-ORDER_VERIFIED; audience from approved segments + consent | `[DOC §12 L250/L251/L257]` + `[REG RULE-004/002]` — owner-mandated |
| Audience dispatcher consent fail-closed | `[DOC §19 L377]` — owner-mandated |
| Transactional enqueue (same-tx outbox insert); PENDING/IN_FLIGHT/SENT/DEAD_LETTER lifecycle; exponential backoff+jitter; at-least-once + idempotency_key = effectively-once; state/threshold specifics | `[EXT]` / `[PACK]` — **owner-review proposals, NOT owner requirements** |

*Nothing in this file flips a gate or a flag; `global_gateway_state=BLOCKED`, `production_flag=OFF`.*
