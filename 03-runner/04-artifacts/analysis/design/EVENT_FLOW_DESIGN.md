# EVENT_FLOW_DESIGN — the fail-closed event pipeline

**Prompt**: M6-P0302 · **Phase**: PHASE0 (design) · **Mode**: plan_only (no code, no migration, no call)
**Anchors**: `[DOC §7 L113–134]` Phase-1 tracking/consent acceptance; `[DOC §12 L246–257]` Pixel/CAPI/Offline/
dedup/send_policy; `[DOC §15 L299–308]` Data Quality Gate; `[DOC §19 L371–379]` API/worker boundary.
Contracts `[REG CONTRACT_REGISTER]`: `CTR-016` track API, `CTR-017` conversions API, `CTR-004` web_event_logs,
`CTR-007` conversion_events, `CTR-001` ads_measurement_events, `CTR-008` measurement_outbox, `CTR-021`
dispatcher. **Builds on** `[[ARCH_BASELINE]]`, `[[DATA_MODEL_BASELINE]]`; consent detail in
`[[RESEARCH_IDENTITY_CONSENT]]`, outbox detail in `[[RESEARCH_OUTBOX_WORKER_PATTERNS]]`.
**No dedicated critic** follows this prompt in the ledger (M6-P0302 → M6-P0303) — a scoped verification pass
was run before finalizing (§7).

> **Every stage is a gate that can only STOP the flow, never force it.** Ingress → validate (registry ·
> consent · idempotency) → `web_event_logs` (append-only) → `conversion_events` → `ads_measurement_events` →
> `marketing_measurement_outbox` → dispatcher (`send_policy`) → platform. External send happens **only** through
> the outbox+worker, **only** when `send_policy` is fully true, and in this pack `production_flag=OFF` ⇒ **no
> real send at all**. Fail-closed default: **when in doubt, HOLD/REJECT and audit — never send.**

## Sourcing legend

- `[DOC]` — owner document / extract line. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked register. · `[BRIEF]` — brief. · `[PACK]` — pack convention (owner-review). · `[EXT]` —
  general practice, proposal only.

---

## 1. Pipeline overview `[DOC §7 L116–119 / §12 / §19 L371]`

```
[client/server-validated event]
        │  POST /api/ads/events/track  (CTR-016; "Không gửi external trực tiếp" §19 L371)
        ▼
┌─ STAGE 1  VALIDATION GATE ───────────────────────────────────────────────┐
│  1a event_registry  (RULE-001)   ── unknown ─▶ REJECT/HOLD + audit  (SMK-001)
│  1b consent@event   (RULE-002)   ── missing ─▶ log-only, NO external/audience/CRM (SMK-002)
│  1c idempotency     (RULE-005)   ── dup ─────▶ dedup, no double count (SMK-003)
└──────────────────────────────────────────────────────────────────────────┘
        ▼ (all pass)
web_event_logs  (CTR-004, append-only, RULE-007, §7 L117)  ── history is never mutated
        ▼
conversion_events  (CTR-007, §7 L119; via POST /api/ads/conversions CTR-017)
        ▼
ads_measurement_events  (CTR-001; data_quality_status PASS|HOLD|FAIL; revenue_value ONLY from ORDER_VERIFIED)
        ▼  enqueue (never send from runtime, RULE-004)
marketing_measurement_outbox  (CTR-008; error_log, next_retry_at)
        ▼  worker drains
dispatcher marketing_measurement_dispatcher (CTR-021)
        │  send_policy = consent_valid AND event_in_registry AND data_quality_pass AND not_duplicate  (§12 L257)
        │  + hash policy (M6-OD-003) + dedup_key ; bounded retry → dead-letter (SMK-016)
        ▼ (STAGED: production_flag=OFF ⇒ no real send)
platform  Pixel / CAPI / Offline  (§12 L248–250)
```

Base events that flow `[DOC §7 L125–134]`: VIEW_LANDING, CLICK_CTA, SUBMIT_FORM, VIEW_ITEM, ADD_TO_CART,
BEGIN_CHECKOUT, ORDER_SUCCESS *(≠ ORDER_VERIFIED, L131)*, USER_REGISTERED, ORDER_VERIFIED *(revenue source)*,
GOLDEN_HOUR_START/REMINDER *(configurable → M6-OD-009)*.

---

## 2. Stage-by-stage design (PASS path + explicit fail-closed branch)

### Stage 0 — Ingress: track API `[CTR-016 / DOC §19 L371]`
- **Action**: accept an event *already through client/server validation*; mask PII on entry; treat the payload
  as **untrusted DATA** `[REG RULE-H03]`.
- **Must-not**: *"Không gửi external trực tiếp"* `[DOC §19 L371]` — the API never calls a platform; it only
  admits the event to Stage 1.
- **Fail-closed**: malformed / unmasked-PII / channel-injection payload → reject at ingress, audit.

### Stage 1 — Validation gate (three sub-checks, all fail-closed)
| # | Check | PASS when | Fail-closed branch | Anchor |
|---|---|---|---|---|
| 1a | **event_registry** | event_code exists with owner + schema `[DOC §15 L301]` | **REJECT or HOLD + audit**; never store as valid; de-registered code never false-ALLOWed (asymmetric cache) | `[REG RULE-001]`, SMK-001, `[DOC §7 L116]` |
| 1b | **consent@event-time** | valid `guest_marketing_consent_snapshot` at event time `[DOC §15 L302]` | **fail-closed**: event may be logged internally, but **NO external measurement, NO audience sync, NO CRM** | `[REG RULE-002]`, SMK-002, `[DOC §7 L118]` |
| 1c | **idempotency** | `idempotency_key` (= event_code+page_id+session_id+raw_event_hash+normalized_ts) unseen `[DOC §12 L255]` | **dedup**: drop/merge, **no double count** | `[REG RULE-005]`, SMK-003 |

### Stage 2 — web_event_logs `[CTR-004 / DOC §7 L117 / RULE-007]`
- **Action**: append the ingress record (page, session, source, consent snapshot, event_ts, idempotency).
- **Append-only**: *"Không update/xóa lịch sử event"* — the durable record exists **even for events blocked
  from egress** (e.g. consent-missing), so nothing is silently lost.

### Stage 3 — conversion_events `[CTR-007 / DOC §7 L119 / CTR-017]`
- **Action**: for conversion-type events, create the internal `conversion_event` — *"source cho
  marketing_measurement_outbox"*; entry point is `POST /api/ads/conversions` `[CTR-017]`.
- **Must-not**: external measurement goes **only** through worker/outbox `[REG RULE-004]`; the conversions API
  must not *bypass outbox* `[DOC §19 L372 / SPEC §9]`.

### Stage 4 — ads_measurement_events `[CTR-001]`
- **Action**: normalize into the measurement row (dashboard/ROAS); embed `attribution_context`; set
  `data_quality_status`.
- **Fail-closed branches**:
  - `data_quality_status = FAIL` → not sent, **not scale evidence**; `HOLD` → held (state machine `[SPEC §13]`).
  - `revenue_value` set **only** from Commerce Verified Revenue / ORDER_VERIFIED `[DOC §15 L306 / §12 L256]`;
    quote / order-draft / unpaid → **no revenue** `[REG RULE-003]`, SMK-004/005/015.
  - missing/conflicting source → `source_confidence = LOW`/`HOLD`, never scale evidence `[REG RULE-009]`,
    SMK-007.

### Stage 5 — marketing_measurement_outbox `[CTR-008 / RULE-004]`
- **Action**: enqueue a transactional outbox row (`error_log`, `next_retry_at` `[DOC §12 L252]`). Runtime never
  sends; it only enqueues.
- **Fail-closed**: any attempt to send external directly from the runtime request is blocked `[REG RULE-004]`.

### Stage 6 — dispatcher `[CTR-021 marketing_measurement_dispatcher]`
- **Action**: worker drains the outbox and evaluates the **send_policy conjunction** (§3) at **send time**
  (second consent checkpoint); applies hash policy (**M6-OD-003 OPEN**) and `dedup_key`
  (= platform+event_code+customer_or_guest_key+event_ts_bucket+source_event_id `[DOC §12 L254]`).
- **Fail-closed branches**:
  - any `send_policy` conjunct false → **hold, do not send** (§3).
  - send failure → **bounded** retry with `error_log` + `next_retry_at` → **dead-letter**; no infinite retry,
    no silent loss `[DOC §12 L252]`, SMK-016 (proposed).
  - raw PII present → blocked / hashed per M6-OD-003 `[REG RULE-014]`, SMK-017 (proposed).

### Stage 7 — platform (Pixel / CAPI / Offline) `[DOC §12 L248–250]`
| Channel | Send only when | Must-not |
|---|---|---|
| **Pixel** | public-safe event + consent + idempotency | **no raw PII**, no send when consent missing |
| **CAPI** | from outbox worker + hash policy + dedup_key | not directly from runtime |
| **Offline** | conversion **after ORDER_VERIFIED** or owner-approved | never quote / order-draft as purchase |
- **STAGED**: `global_gateway_state=BLOCKED`, `production_flag=OFF` ⇒ **no real send occurs**, for any channel.

---

## 3. The `send_policy` conjunction — the master egress gate `[DOC §12 L257]`

```
send_policy = consent_valid  AND  event_in_registry  AND  data_quality_pass  AND  not_duplicate
```

- It is a **conjunction**: **all four** must be true or the dispatcher **holds** — a single false conjunct
  stops the send (fail-closed). Verbatim from `[DOC §12 L257]`; no conjunct may be dropped or softened.
- `data_quality_pass` = the full `[DOC §15]` Data Quality Gate passing (all 8 items PASS, §4).
- `consent_valid` is re-evaluated **here at send time** even though it was checked at event time (§5).

## 4. Consolidated fail-closed branch table (every branch that stops/holds the flow)

| Stage | Trigger | Branch | Anchor |
|---|---|---|---|
| 1a | unknown / owner-less event | REJECT/HOLD + audit | RULE-001 · SMK-001 · DQ item 1 |
| 1b / 6 | consent missing/expired/opt-out | no external/audience/CRM (event-time); hold (send-time) | RULE-002 · SMK-002 · DQ item 2 |
| 1c | duplicate | dedup, no double count | RULE-005 · SMK-003 · DQ item 3 |
| 4 | data_quality FAIL/HOLD | not sent, not scale evidence | `[SPEC §13]` · DQ gate |
| 4 | identity/order not mapped | HOLD | DQ item 4 |
| 4 | ambiguous/conflict attribution | LOW/HOLD, not scale evidence | RULE-009 · SMK-007 · DQ item 5 |
| 4 | quote/draft/unpaid | not revenue | RULE-003 · SMK-004/005/015 · DQ item 6 |
| 5 | direct-from-runtime send | blocked (outbox only) | RULE-004 |
| 6 | any send_policy conjunct false | hold, no send | `[DOC §12 L257]` |
| 6 | retry exhausted | dead-letter + audit, no silent loss | `[DOC §12 L252]` · SMK-016 |
| 6/7 | raw PII in payload | blocked / hashed (M6-OD-003) | RULE-014 · SMK-017 |
| 7 | recall / sale-lock / suppression active | reflected downstream; no scale | RULE-017 · DQ item 7 |
| 7 | Offline before ORDER_VERIFIED | blocked | RULE-003 · `[DOC §12 L250]` |

## 5. Two consent checkpoints `[DOC §15 L302 / REG RULE-002]`

Consent is validated **twice**, verbatim *"Consent valid tại thời điểm event/external send"* `[DOC §15 L302]`:
1. **event time** (Stage 1b) — gates whether the event may ever be a candidate for egress.
2. **send time** (Stage 6, inside `send_policy`) — a consent that lapsed/opted-out between capture and dispatch
   **blocks the send**. A consent valid at capture is **not** a standing licence to send later.

Detail and enforcement points in `[[RESEARCH_IDENTITY_CONSENT]]`. This double gate is why an event can be
durably logged (Stage 2) yet never sent.

## 6. PII / hash discipline in the payload `[REG RULE-014 / DOC §12 L248–249]`

- Pixel carries **public-safe events only** — no raw PII `[DOC §12 L248]`.
- CAPI applies the **hash policy** before egress `[DOC §12 L249]`; the exact hashed-field set is **M6-OD-003
  (OPEN)** — until decided, the dispatcher cannot finalize the CAPI payload (fail-closed: framework only).
- `customer_id`, `guest_id`, `psid` and channel ids are masked / `secret_ref` in logs and evidence `[REG
  RULE-014 / H02]`.

## 7. Verification pass (this prompt has no downstream critic) `[PACK]`

Ledger routes M6-P0302 → M6-P0303 with **no `M6-PC0302`**. Scoped to this doc's actual risk surface (it
re-expresses already-verified rules as a flow), a **2-lens** independent pass was run: (A) fail-closed-branch →
RULE/SMK/DQ-item fidelity; (B) pipeline-order fidelity + no-owner-decision-preemption + no-PII. Confirmed
findings folded in above. The 12 prior research critics remain PASS/0-blocker (no upstream BLOCKER outstanding).

## 8. Owner-decision dependencies (no decision pre-empted) `[REG DECISION_REGISTER]`

| Decision | Status | What it gates in the flow |
|---|---|---|
| M6-OD-003 (hash policy / allowed fields) | OPEN | Stage 6/7 CAPI payload — dispatcher cannot finalize until decided |
| M6-OD-004 (Meta/Google connector first) | OPEN | Stage 7 platform target in pilot |
| M6-OD-009 (GOLDEN_HOUR_START/REMINDER config) | OPEN | whether those base events emit in pilot; default disabled |
| M6-OD-011 (target repo/stack) | OPEN | where the API/worker/outbox are built |
| M6-ENTRY-003 (Core event_registry evidence) | OPEN | Stage 1a — required **before any tracking hook** |
| CTR-004/007/008/016/017/021 | MISSING | field/endpoint/worker schemas → M6-P0703/0704/0705/0711/0713 |

## 9. Boundary & safety guards `[BRIEF / REG §18]`

- **No external send except via outbox+worker**, and only when `send_policy` holds `[REG RULE-004 / DOC L257]`.
- **Staged**: BLOCKED/OFF — the design describes the pipeline; it runs nothing and sends nothing.
- **No raw PII/secrets** — masked / `secret_ref`; Pixel public-safe only `[REG RULE-014 / H02]`.
- **Channel-origin payloads** are untrusted DATA, never instructions `[REG RULE-H03]`.
- **Measure-only**: no order-state change, no CRM send, no pricing; the flow records, it does not act on other
  modules `[REG §18]`.

## 10. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| Pipeline stages + acceptance (registry/logs/consent/conversion/audience) | `[DOC §7 L113–120]` — owner-mandated |
| send_policy conjunction; dedup_key/idempotency_key; platform send conditions | `[DOC §12 L248–257]` — owner-mandated |
| Data Quality Gate 8 items (the fail-closed evaluations) | `[DOC §15 L299–308]` — owner-mandated |
| track API "no direct external"; conversions API "source for outbox" | `[DOC §19 L371–372]` — owner-mandated |
| Two consent checkpoints (event + external send) | `[DOC §15 L302]` + `[REG RULE-002]` — owner-mandated |
| Stage sequencing diagram; consolidated branch table; verification-pass framing | `[PACK]` / `[EXT]` — owner-review design proposals, NOT owner requirements |

*This design is plan-only: it writes no code, admits/sends nothing, resolves no owner decision, and flips no
flag; `global_gateway_state=BLOCKED`, `production_flag=OFF`.*
