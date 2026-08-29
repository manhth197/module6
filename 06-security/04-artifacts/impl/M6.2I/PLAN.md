# M6.2I IMPLEMENTATION PLAN — Phase 2 Golden Hour Funnel measurement (STAGED, plan-only)

**Prompt**: M6-P1801 (`M6_2I_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code this prompt)
**Slice**: M6.2I — measure the Phase-2 conversion machine (doc §8): the Golden Hour funnel across states
PRE → LIVE → POST → CLOSED, the AI-consult handoff, order-capture signals, and retargeting **on valid events +
valid consent only**. Depends on M6.2H. **Done gate**: *Golden Hour conversion smoke pass.*
**Posture (immutable)**: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
`SCALE_MODEL_RATIFIED=False`, `SCALE_EXECUTION_ENABLED=False`, `HASH_POLICY_RATIFIED=False`,
`LEARNING_AUTOPUBLISH_ENABLED=False`, `LEARNING_CONTENT_FILL_ENABLED=False`, `LEARNING_SAFE_RANGE_RATIFIED=False`,
`live_migrations=false`. This plan writes no code, applies no migration, operates no live session, sends nothing,
scales/publishes nothing, resolves no owner decision, flips no flag.

> **Top-0.1% design lens (load-bearing — it CHANGED the design, not a label).** Four failure modes a strong
> measurement architect would flag, each of which altered this plan:
> 1. **Inventing a `golden_hour_session` / `funnel` table.** Doc §13 (the minimal Data Object Contract) defines
>    **no** golden-hour/funnel/session table. Adding one invents schema Module 6 does not own (RULE-018). →
>    **No new table, no new migration, no new CTR.** M6.2I is a **derived read-only projection** over the existing
>    `ads_measurement_events` (CTR-001, mig 0002) + `ads_attribution_context` (CTR-002, mig 0006).
> 2. **Building a live-session controller** (`start()/close()`). Operating live sessions is Gateway/Live's, and
>    explicitly **out of scope** (slice §Out-of-scope; RULE-013). → The Golden Hour **state is a measurement
>    observation only** — it labels observed events; it never commands a real session.
> 3. **Requiring `GOLDEN_HOUR_START/REMINDER` to derive state.** Those codes are **M6-OD-009 OPEN**
>    (optional/disabled-by-default; Gateway/Live owns emission — `base_events.py` already fences them off). →
>    State defaults to **UNKNOWN (fail-closed)** when the signals are absent; the funnel measures the chain
>    **regardless**. (The M6-P1800 entry judge flagged OD-009 as design-scoping, not an entry blocker.)
> 4. **Recomputing the funnel rates / re-deciding order validity.** The doc §14 funnel formulas already live in
>    `kpi_metrics.py`; and treating `ORDER_CREATED` as a *valid captured order* would usurp Commerce's gate
>    (RULE-021). → **Reuse** the existing rate definitions; add only the per-chain / per-state grain. **Record**
>    the consumed Commerce-gate-passed flag (RULE-021), never perform/own that validation.
> The invariants this slice must not breach: revenue only from ORDER_VERIFIED (RULE-003 / FAIL-001, SMK-004);
> the live/comment/messenger chain is traceable (SMK-013); no phase jump (FAIL-010 — Phase 1 gate SIGNED at
> M6-P1800); measure-only at every module edge.

---

## 1. Entry-gate verification

| Precondition | Source | Result |
|---|---|---|
| This prompt RUNNING | ledger (order 157) | **M6-P1801 = RUNNING** ✓ |
| Dependency resolved | ledger | **M6-P1800 = SIGNED** (M6.2I entry judge PASS, opens the slice STAGED) ✓; M6.2H exit **M6-P1709 = SIGNED** ✓ |
| Target LOCKED + M6-OD-011 | `04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json` | `status=LOCKED`, `STAGED_ONLY`, safety all false; **M6-OD-011 DECIDED** 2026-07-23 ✓ |
| Slice contracts | slice §Contract-checklist + M6-P1800 | **CTR-001** (ads_measurement_event) + **CTR-002** (ads_attribution_context) both **DRAFT_LOCKED** and already BUILT (M6.2B/M6.2E) — resolved-for-entry ✓ |
| OPEN owner decisions vs scope | DECISION_REGISTER (M6.2I sweep) + M6-P1800 | only **M6-OD-009** (GOLDEN_HOUR_START/REMINDER config) names M6.2I → **design-scoping** (optional/disabled-by-default, Gateway/Live owns; fail-closed to UNKNOWN), **not** an entry blocker ✓ |
| Phase order (**RULE-016**) | ledger A..H chain PASS/SIGNED | Phase 1 (M6.2A..H) complete + sequential → **FAIL-010 phase-jump not tripped** (M6.2I is the first Phase-2 slice, opened only after Phase-1 gates); the Audit→Implementation→Verify/Gate rhythm is honored as separate prompts (this plan-only prompt M6-P1801 → CODER-implement M6-P1802 → TESTER M6-P1803/1804 → judge M6-P1809) ✓ |
| Flags | manifest/brief | BLOCKED/OFF/OFF + all scale/hash/learning flags unchanged; `live_migrations=false` ✓ |
| M6.2H foundation | `04-artifacts/impl/M6.2H/` (345 tests green) | present; carries the M6.2A..H tree (CTR-001/002, resolver, kpi_metrics funnel rates, ConsentGate, DataMart) — the reuse surface for §5 ✓ |

**Conclusion**: open for **STAGED, measure-only** M6.2I. Build a derived Golden Hour funnel projection over the
existing event/attribution stores; no new table, no live-session operation, no send, no flag flip.

---

## 2. Working mode, conventions & staging model

Reuse the M6.2A–H baseline verbatim (pytest, frozen dataclasses, read-only ports + in-memory staged adapters,
framework-neutral pure functions, mask-on-export, fail-closed everywhere; PII markers assembled at runtime — the
pack secret-scan forbids literal PII in source). **Cumulative snapshot**: the whole **M6.2H** tree (final slice
state, 345 tests) is carried forward **byte-identical** into `04-artifacts/impl/M6.2I/`; M6.2I **adds** a small
`funnel/` measurement package and a thin, reversible dashboard read-only wiring. The change set (§5) is the diff.
**No new migration; no new config flag; no new contract.** `production_flag=OFF` immutable.

---

## 3. Scope lock (anchored strictly to `00-spec/slices/M6.2I.md`)

**In scope (4 measurement capabilities):**
1. **Golden Hour state measurement** PRE/LIVE/POST/CLOSED (+ UNKNOWN, fail-closed) — a passive observation over
   events; **never operates a session** (RULE-013; Gateway/Live owns). `GOLDEN_HOUR_START/REMINDER` optional
   (M6-OD-009) → absent ⇒ UNKNOWN.
2. **Flow-chain funnel measurement** — the doc §8 chain **Ads → Live → Comment → Messenger → Quote → Order →
   Verified** assembled per live-session and **bucketable by Golden Hour state**, with per-stage counts + the doc
   §14 funnel rates (Comment/Inbox/Quote/Order/Verified) **reusing** `kpi_metrics` formula definitions. Revenue
   **only** from ORDER_VERIFIED (RULE-003; quote/order-created are funnel stages, never revenue — SMK-004).
3. **Retargeting eligibility measurement** on **consent-valid** events only — a measure-only classifier reusing
   `ConsentGate` (egress-eligibility, never sends). Missing/expired/opt-out consent ⇒ not eligible (fail-closed).
4. **Order-capture validity metadata (RULE-021)** — record whether Commerce's stock/fulfillment/trust/policy +
   customer-confirmation gate passed **before send-to-Core**, as a **consumed flag**; absent ⇒ not-validated
   (fail-closed). Module 6 **records** it; it never performs/owns/bypasses that validation.

**Out of scope (explicit — deferred / other-owner):**
- **Operating live sessions** (Gateway/Live) — no session controller / start / close / emit. Module 6 only
  measures observed signals.
- **Public final price** (M6-LEX-003/004) — the funnel measures the QUOTE **event**, never surfaces a final
  price; no pricing (M3 QuoteSnapshot is a reference id only).
- **Revenue from live signals** (Module 7 boundary) — LIVE_VIEW/LIVE_COMMENT/quote/order-created are **never**
  revenue (RULE-003); only ORDER_VERIFIED is.
- **AI consult content** (M4) — only the handoff/consult **events** (MESSENGER_STARTED, AI_PROPOSAL_SENT) are
  measured; the advisory content itself is never read, written, or influenced.
- **Sending / audience sync / CRM / scale / publish / commission** — the audience outbox + dispatcher (M6.2C/D,
  consent fail-closed) already own send; M6.2I **measures**, it does not enqueue or send. No new API/table/flag.

---

## 4. Locked doc content (build to the exact spec)

### 4.1 The Golden Hour states (VERBATIM, doc §7/§8, extract L138)

`Golden Hour phải vận hành theo trạng thái PRE → LIVE → POST → CLOSED.` Module 6 **measures** the observed state;
Gateway/Live operates it. A 5th sentinel **UNKNOWN** is the fail-closed default (no observed golden-hour signal →
UNKNOWN, never assumed PRE/LIVE). `GOLDEN_HOUR_START / REMINDER` = *"Tùy cấu hình khi mở phiên Giờ Vàng"*
(optional; M6-OD-009 OPEN) — treated as optional inputs, never required.

### 4.2 The doc §8 flow-event chain (event codes VERBATIM, extract L151–157; boundary column glossed in English)

| Flow | Event / Object (doc §8/§10 codes — referenced, never invented) | Owner / boundary |
|---|---|---|
| **Ads → Live** | campaign_id, adset_id, ad_id, live_session_id | Module 6 measures; Gateway/Live operates; **không tính revenue** |
| **Live → Comment** | LIVE_VIEW, LIVE_COMMENT | Gateway normalizes; M6 receives signal |
| **Comment → Messenger** | MESSENGER_STARTED, messenger_thread_id | Gateway handoff; AI consults privately (content = M4) |
| **Messenger → Quote** | AI_PROPOSAL_SENT, QUOTE_CART_CREATED, QUOTE_SNAPSHOT_CREATED, QUOTE_SENT | AI orchestrates; **Commerce** creates QuoteSnapshot (M3) |
| **Quote → Order** | ORDER_CONFIRMATION_SENT, CUSTOMER_CONFIRMED_ORDER, ORDER_CREATED | **Commerce** creates order **on customer confirmation** (RULE-021) |
| **Order → Verified** | ORDER_VERIFIED, PAYMENT_COMPLETED (if any) | Commerce/Payment/Shipping confirm; **M6 consumes verified revenue** (RULE-003) |

Event codes are **consumed canon** (doc §10 Event Taxonomy), validated upstream at ingest against the Core
`event_registry` (RULE-001, `EventValidator`). M6.2I references them as measurement-time constants; it **adds
none** to the Phase-1 client allow-list (`base_events.py`) and **invents none** (RULE-001/018).

### 4.3 The funnel rates (VERBATIM, doc §14 — reuse `kpi_metrics` definitions)

`Comment Rate = LIVE_COMMENT/LIVE_VIEW` · `Inbox Rate = MESSENGER_STARTED/LIVE_COMMENT` ·
`Quote Rate = QUOTE_SENT/MESSENGER_STARTED` · `Order Rate = ORDER_CREATED/QUOTE_SENT` ·
`Verified Rate = ORDER_VERIFIED/ORDER_CREATED`. Every division **fail-closed** (0/None denominator → None, never
fabricated). The per-chain / per-Golden-Hour-state grain is the new contribution; the **formula definitions are
reused** (re-applied at the finer per-chain / per-state grain over event counts) — `kpi_metrics`' global compute
is left untouched, not called.

---

## 5. Minimal change set (all target-relative, staged under `04-artifacts/impl/M6.2I/`)

Legend: **Leg** = M6.2I exit-gate leg — **L1** = *Golden Hour conversion chain measured end-to-end across
PRE/LIVE/POST/CLOSED (+ live/comment/messenger trace)*; **L2** = *SMK-004 (quote ≠ revenue)*; **L3** = *SMK-013
(live/comment/messenger trace)*. Rollback: new files → delete; patched carried-forward files → revert to M6.2H.

### 5.1 New — the `funnel/` measurement package (derived, read-only)

| # | Target file (new) | Purpose | Contract/Rule | Leg | Smoke |
|---|---|---|---|---|---|
| C1 | `app/measurement/funnel/__init__.py` | package marker | — | — | — |
| C2 | `app/measurement/funnel/golden_hour.py` | `GoldenHourState` enum (PRE/LIVE/POST/CLOSED/**UNKNOWN**) + `observe_state(signals)` — a pure measurement projection: derive the observed state from optional `GOLDEN_HOUR_START/REMINDER` signals (M6-OD-009) + observed live events; **absent/ambiguous ⇒ UNKNOWN** (fail-closed). **No** `start`/`close`/`emit`/controller method (RULE-013; live-ops is Gateway/Live's). | RULE-013; OD-009 | **L1** | — |
| C3 | `app/measurement/funnel/flow.py` | `FlowStage` enum (ADS_TO_LIVE … ORDER_TO_VERIFIED) + the **verbatim doc §8** event-code → stage map (§4.2) + the ordered chain + `REVENUE_VALID_STAGE = ORDER_TO_VERIFIED` (RULE-003). Codes referenced from doc §8/§10 canon; none invented (RULE-001/018). | RULE-001/003/018 | **L1** | — |
| C4 | `app/measurement/funnel/models.py` | frozen result dataclasses: `FunnelStageCount{stage, event_code, count}`, `GoldenHourFunnelView{live_session_id, golden_hour_state, stage_counts, rates, verified_revenue, capture_gate_passed, trace}` — `to_public()` masks psid (RULE-014/H02); **no revenue field except verified** (RULE-003). | CTR-001/002 (reuse) | L1 | SMK-004/013 |
| C5 | `app/measurement/funnel/funnel.py` | `GoldenHourFunnel` assembler: given measured events (+ their attribution contexts) it groups by `live_session_id`, buckets by `GoldenHourState`, produces per-stage counts + the §14 rates (**reusing** `kpi_metrics` formula definitions), the verified-only revenue (RULE-003), the RULE-021 `capture_gate_passed` flag (consumed; absent⇒False), and threads the live/comment/messenger trace from `ads_attribution_context` (SMK-013). **Read-only projection** — no write/send/scale/publish method. | CTR-001/002; RULE-003/013/021 | **L1/L2/L3** | **SMK-004/013** |
| C6 | `app/measurement/funnel/retargeting.py` | `RetargetingMeasurement`: measure-only eligibility classifier — an event is retargeting-eligible iff it is a valid retargeting signal **AND** `ConsentGate.evaluate(snapshot, ConsentScope.AUDIENCE_SYNC)` passes (reuse the EXISTING `AUDIENCE_SYNC` scope — retargeting is audience; **invent no new consent scope**, RULE-018; egress-eligibility, **never sends**). Missing/expired/opt-out/scope-not-granted ⇒ not eligible (fail-closed). Counts eligibles; **does not** enqueue to the audience outbox (M6.2C/D owns send; `external_send=OFF`). | RULE-002(consent)/004/018; measure-only | L1 | — |

### 5.2 Patched (carried-forward) — surface on the existing dashboard support-view (CTR-018)

| # | Target file (patched) | Change | Leg | Rollback |
|---|---|---|---|---|
| P1 | `app/measurement/dashboard/models.py` | Add an optional **read-only** `golden_hour_funnel` section to the dashboard view model (a list of `GoldenHourFunnelView.to_public()`). No revenue/trigger field beyond verified (RULE-003/012). | L1 | revert to M6.2H |
| P2 | `app/api/dashboard.py` | Wire the `GoldenHourFunnel` output into the existing **GET /api/admin/ads/dashboard** handler (CTR-018) as a support-view section — **read-only**, no new endpoint, no trigger (RULE-012; Data Mart / dashboard never a trigger owner). Untrusted request body = DATA (RULE-H03). | L1 | revert to M6.2H |

**No new migration** (doc §13 defines no golden-hour/funnel/session table — inventing one breaches RULE-018; the
projection reads `ads_measurement_events` mig 0002 + `ads_attribution_context` mig 0006). **No new config flag**
(measure-only, no send/scale/publish; posture flags already cover the boundary). Both omissions are deliberate
minimal-change calls, not gaps.

---

## 6. Test plan → done-gate / smoke mapping (`pytest -q`; TESTER authors + executes the official smokes)

Fixtures extend `conftest.py` with a `GoldenHourFunnel`, a `RetargetingMeasurement`, golden-hour-state signal
builders, and multi-stage measured-event builders across PRE/LIVE/POST/CLOSED (reusing the M6.2E resolver +
M6.2F DataMart fixtures). Carried-forward M6.2H tests stay green. PII markers assembled at runtime.

| # | Target test (new) | Proves | Leg | Smoke | Fail-gate |
|---|---|---|---|---|---|
| T1 | `tests/test_golden_hour_funnel_chain.py` | **L1**: the full Ads→Live→Comment→Messenger→Quote→Order→Verified chain is measured end-to-end **across PRE/LIVE/POST/CLOSED**; each stage counted + bucketed by state; §14 rates computed fail-closed; verified-only revenue. | **L1** | Golden-Hour conversion smoke | FAIL-001 (guard) |
| T2 | `tests/test_golden_hour_state_measure_only.py` | **L1 / RULE-013 / OD-009**: state is a measurement observation (no `start`/`close`/controller method); absent `GOLDEN_HOUR_START/REMINDER` ⇒ **UNKNOWN** (fail-closed); state never drives a session. | L1 | — | — |
| T3 | `tests/test_quote_in_funnel_not_revenue.py` | **L2 / SMK-004 / RULE-003 / FAIL-001**: a QUOTE_SENT counts as a funnel stage but contributes **0** revenue / no ROAS; a quote carrying a revenue figure is a DQ FAIL. | **L2** | **SMK-004** | **FAIL-001** |
| T4 | `tests/test_live_chain_trace_in_funnel.py` | **L3 / SMK-013**: the funnel threads `live_session_id` + `comment_id` + `messenger_thread_id` from `ads_attribution_context`; psid **masked** on every export (RULE-014/H02). | **L3** | **SMK-013** | — |
| T5 | `tests/test_retargeting_consent_valid_only.py` | **L1**: retargeting eligibility measured **only** on consent-valid events; missing/expired/opt-out ⇒ not eligible (fail-closed); **no send surface** (measure-only, `external_send=OFF`). | L1 | — | (FAIL-002-adjacent) |
| T6 | `tests/test_order_capture_commerce_gate_rule021.py` | **L1 / RULE-021**: order-capture signals measured; `capture_gate_passed` True **only** with the consumed Commerce-gate flag; absent ⇒ False (fail-closed); M6 never performs/owns the validation. | L1 | — | — |
| T7 | `tests/test_funnel_measure_only_boundary.py` | boundary: the funnel/retargeting/dashboard-section expose **no** write/send/scale/publish/order-state/pricing method; read-only projection (RULE-012/013/018; measure-only). | L1/L2/L3 | — | FAIL-001 (guard) |

**Smoke → test binding**: SMK-004 = T3; SMK-013 = T4; the *Golden Hour conversion smoke* (exit-check 1) = T1
(+T2 state coverage, +T4 trace). **Execution + recorded results/evidence is the TESTER's** (M6-P1803 build /
M6-P1804 run → `04-artifacts/test-reports/M6.2I/`). No self-run / self-certify (RULE-015).

---

## 7. Master traceability matrix

| Item | Files | Contract | Rule(s) | Leg | Smoke | Fail-gate | Rollback |
|---|---|---|---|---|---|---|---|
| Golden Hour state (measure-only) | C2 | CTR-001 (reuse) | RULE-013; OD-009 | **L1** | GH conversion | — | delete |
| Flow-chain stage map (doc §8) | C3 | — | RULE-001/003/018 | L1 | — | — | delete |
| Funnel view models | C4 | CTR-001/002 | RULE-003/014 | L1 | SMK-004/013 | FAIL-001 | delete |
| Golden Hour funnel assembler | C5 | CTR-001/002 | RULE-003/013/021 | **L1/L2/L3** | SMK-004/013 | FAIL-001 | delete |
| Retargeting measurement | C6 | — | RULE-002/004 | L1 | — | — | delete |
| Dashboard support-view section | P1,P2 | **CTR-018** | RULE-012/H03 | L1 | — | — | revert to M6.2H |
| Phase-order / separate-prompt rhythm | (governance; no code) | — | **RULE-016** | (entry) | — | FAIL-010 | n/a |
| Tests | T1–T7 | — | — | L1/L2/L3 | SMK-004/013 | FAIL-001 | delete |

**Legs**: L1 (Golden-Hour conversion chain across PRE/LIVE/POST/CLOSED + trace — T1/T2/T4) ✓; L2 (SMK-004 quote ≠
revenue — T3) ✓; L3 (SMK-013 live/comment/messenger trace — T4) ✓; retargeting (T5) + RULE-021 (T6) + measure-only
boundary (T7) ✓. TESTER executes the official smokes (M6-P1803/1804); evidence (M6-P1807), docs (M6-P1808), judge
(M6-P1809) are downstream process legs.

---

## 8. Rollback strategy (global)

1. **Nothing live / nothing sends / no session operated.** Staged under `04-artifacts/impl/M6.2I/`; no migration
   (none added), no external call, no flag written. Baseline rollback = delete the M6.2I tree (M6.2H untouched).
2. **Per-item** (§5): new `funnel/` files → delete; patched `dashboard/models.py` + `api/dashboard.py` → revert
   to M6.2H (the dashboard funnel section is additive + read-only; reverting removes only that section).
3. **The projection is derived + read-only** — it writes nothing to the stores; removing it leaves the underlying
   `ads_measurement_events` / `ads_attribution_context` rows exactly as M6.2H left them.

---

## 9. Plan-deltas & notes

- **No new table / migration / CTR (RULE-018)** — the primary architecture call. Doc §13 defines no
  golden-hour/funnel/session object; M6.2I is a derived projection over CTR-001/002. Adding schema would invent
  what Module 6 does not own.
- **Golden Hour state = measurement only (RULE-013)** — no `start`/`close`/controller; Gateway/Live operates the
  session. `GOLDEN_HOUR_START/REMINDER` optional (M6-OD-009) → absent ⇒ UNKNOWN (fail-closed). T2 asserts no
  controller surface.
- **Revenue only from ORDER_VERIFIED (RULE-003 / FAIL-001, SMK-004)** — quote/order-created are funnel stages,
  never revenue; the funnel reuses the DataMart's single verified-revenue choke. T3.
- **Live/comment/messenger trace (SMK-013)** — threaded from the existing `ads_attribution_context` (M6.2E); psid
  masked on export (RULE-014/H02). T4.
- **Retargeting = consent-valid-only, measure-only (doc §8 L143)** — reuse `ConsentGate` under the EXISTING
  `ConsentScope.AUDIENCE_SYNC` (retargeting is audience; **no new scope invented**, RULE-018; egress-eligibility,
  never sends); no audience enqueue (M6.2C/D owns send; `external_send=OFF`). T5.
- **Phase order locked (RULE-016)** — Phase 1→2→3 with no jump: honored at entry (FAIL-010 phase-jump cleared,
  §1; the full A..H chain is PASS/SIGNED), and the Audit→Implementation→Verify/Gate rhythm is run as SEPARATE
  prompts (this plan-only M6-P1801 → implement M6-P1802 → TESTER build/run M6-P1803/1804 → judge M6-P1809), never
  one prompt for everything. This plan writes no code and cannot jump a phase.
- **RULE-021 order-capture** — M6 records the consumed Commerce-gate-passed flag; absent ⇒ not-validated
  (fail-closed); never performs/owns/bypasses Commerce's stock/fulfillment/trust/policy + confirmation gate. T6.
- **Reuse, not duplicate** — funnel rates reuse `kpi_metrics` §14 formulas; consent reuses `ConsentGate`;
  attribution/trace reuses the M6.2E resolver + `ads_attribution_context`. The new grain is per-chain /
  per-Golden-Hour-state assembly.
- **Module boundary intact** — no live-ops (M7), no consult content (M4), no public reply (M5), no pricing /
  QuoteSnapshot write (M3), no order-state change (M8), no CRM send, no commission (Finance), no scale/publish.
- **Governance unchanged** — `M6-P1000` + `M6-P1309` verdicts stay BLOCKED (not converted); the M6.2G/M6.2H
  before-real-scale/send/auto-publish forward conditions remain in force; no flag flipped.
- **Ultracode note** — this plan was reviewed by an independent adversarial design red-team (§ below) driving the
  claims against the real M6.2H tree before finalizing.

---

## 10. Acceptance self-map

1. *Every item → leg or smoke* → §5–§7. ✓  2. *Rollback per item* → §5/§8. ✓  3. *No scope beyond the slice* →
§3 (live-ops/pricing/send/scale/publish/commission deferred or other-owner; measure-only). ✓  4. *Target LOCKED +
M6-OD-011 decided* → §1. ✓  5. *Reuse conventions / test patterns from the locked target* → §2/§4.3 (M6.2H
baseline; kpi_metrics/ConsentGate/resolver reuse). ✓  Plus the **load-bearing invariants**: no invented schema
(RULE-018), Golden Hour state measure-only (RULE-013), revenue verified-only (RULE-003/FAIL-001, SMK-004), live
chain traceable (SMK-013), retargeting consent-valid-only, RULE-021 order-capture recorded-not-owned — each with a
test and the M6.2H suite staying green.

*Plan-only: no code, no migration, no live session operated, nothing sent/scaled/published, no flag flipped;
`global_gateway_state=BLOCKED`, `production_flag=OFF`.*
