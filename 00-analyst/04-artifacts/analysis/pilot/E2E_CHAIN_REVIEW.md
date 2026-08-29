# M6 — End-to-End Chain Review — Ads → Live → Comment → Messenger → Quote → Order → Verified

> **Status: STAGED review — the chain is coherent and its core invariants hold at the staged altitude, but it is NOT
> cleared to go live.** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all scale/hash/learning
> flags `False`, `live_migrations=false` — immutable, untouched. This review MEASURES the chain across all slice
> evidence; it declares no ROAS Pass / Scale Ready (owner-only, doc §23) and flips nothing. `M6-P1000` (M6.2A entry) and
> `M6-P1309` (M6.2D exit) verdicts remain **BLOCKED** (not converted).
>
> **Headline finding (honest, not rosy):** every hop is measured, and verified-only revenue **is** enforced at the
> core (store set-once Zone-B + dashboard `verified_rows()`), proven by SMK-003/004/005/006/007/013/014/015 all PASS in
> the M6.2K re-run (523 passed, rc 0). But two chain-integrity conditions are **OPEN** and must clear before the chain
> is surfaced or fed to Finance/scale:
> 1. **Attribution is not yet single-subject bound** — `F-SEC-2I-1` (the standing blocker's "F-FUNNEL-4"): a
>    multi-subject live session can stitch different people's `comment_id` / `messenger_thread_id` into one trace. The
>    one **channel-reachable** chain finding; armed-not-fired only because tests are single-subject and no export
>    endpoint is wired yet.
> 2. **Verified-only is not self-enforcing on the Finance-facing growth path** — `F-GROWTH-3`: the
>    `event_code == 'ORDER_VERIFIED'` choke adopted at M6.2I (to close F-DASH-1) was **not carried forward** into the
>    M6.2J growth reads (`revenue_value is not None`). Trusted-input/code-exec-only, but it reaches a commission-ready
>    figure.
>
> Both, plus `F-GROWTH-1` (CRM subject-bind) and `F-SEC-2I-2` (raw `messenger_thread_id`), are disclosed in the pack's
> 8 standing blockers and routed. None trips a fail gate from a reachable path **today** (staged, no export surface).

| Field | Value |
|---|---|
| Prompt | **M6-P3000** — `E2E_CHAIN_REVIEW` (ANALYST_ARCHITECT, `analysis_only`, EVIDENCE_GATE, phase PR_PILOT) |
| Task | Review the end-to-end chain across all slice evidence: every hop measured, attribution traceable, verified-only revenue enforced end to end |
| Entry gate | **M6-P3000=RUNNING**; dependency **M6-P2009=SIGNED** (M6.2K slice-gate Judge verdict PASS, `fail_gate_tripped=false`) — the whole build sequence M6.2A…M6.2K is closed STAGED |
| Method | synthesis over the 11 slice runbooks + the M6.2K owner evidence package + the DECISION / FAIL_GATE registers; three read-only per-segment evidence gathers; three adversarial verification lenses |
| Fail gates weighed | M6-FAIL-001 (revenue misuse), -002 (consent), -003 (event drift), -004 (core/commission), -008 (raw PII) — **none tripped** from a reachable path at staged altitude |

---

## 1. Scope & method

The chain under review is the doc-canonical funnel spine, consumed verbatim (M6.2I §1.2, doc §10 Event Taxonomy —
"invents none"):

```
Ads  →  Live  →  Comment  →  Messenger  →  Quote  →  Order  →  Verified
(campaign/    (live_        (comment_     (messenger_   (QUOTE_   (ORDER_    (ORDER_
 adset/ad)     session_id)   id)           thread_id)    SENT)     CREATED)   VERIFIED = revenue)
```

Sources read: the 11 slice runbooks `M6_2A…M6_2K_RUNBOOK.md`; the M6.2K owner evidence package
(`M6_2K_EVIDENCE_INDEX.md`, `SMOKE_RESULTS.md`, the M6.2K boundary + security reports); `M6-P2009_JUDGE_FINAL_SIGN_OFF.json`;
`00-spec/registers/FAIL_GATE_REGISTER.md`; `00-spec/registers/DECISION_REGISTER.md`. Three per-segment gathers extracted
the hop mechanisms with file citations; three adversarial lenses (overclaim / completeness / factual) checked this
review. This is `analysis_only` — no code, migration, flag, or state-ledger write; no external call.

The three questions the task poses map to §3.1 (every hop measured), §3.2 (attribution traceable), §3.3 (verified-only
enforced end to end).

---

## 2. The chain, hop by hop

| Hop | Event code(s) measured | Attribution key carried | Verified-only status | Evidence (smoke · code · slice) |
|---|---|---|---|---|
| **Ads** | ad-measurement events; campaign/adset/ad | resolver builds `ads_attribution_context` from `ads_measurement_event` + `conversion_event` | not a revenue hop | SMK-006/007 · `attribution/resolver.py` (CTR-002) · M6.2E §1–3 |
| **Live** | `LIVE_*`, buckets by Golden Hour state | `live_session_id` (session-level shared key) | not a revenue hop | SMK-013 · `funnel.py` `GoldenHourFunnel` · M6.2I §1.1–1.2 |
| **Comment** | `LIVE_COMMENT` | `comment_id` (folded across the session) | not a revenue hop | SMK-013 · M6.2I §1.1, §3.1 |
| **Messenger** | `MESSENGER_STARTED`, `AI_PROPOSAL_SENT` (handoff *events* only; M4 content never read) | `messenger_thread_id` (per-person handle) | not a revenue hop | SMK-013 · M6.2I §1.2 |
| **Quote** | `QUOTE_SENT` | joins to order via M3 `capture_gate_passed` (RULE-021, consumed) | **0.0 revenue, no ROAS** (FAIL-001) | SMK-004/015 · store Zone-A + `verified_rows()` · M6.2F §2 |
| **Order** | `ORDER_CREATED` / order-draft | order/QuoteSnapshot created by Commerce (M3), not M6 | **not Revenue Verified** until verified | SMK-005 · M6.2F §2 |
| **Verified** | `ORDER_VERIFIED` | resolver grades HIGH/LOW; adjustment append-only | **the ONLY revenue source** (RULE-003); set-once Zone-B | SMK-006 · `attribution_materializer` (CTR-023) · M6.2E §1–2 |

Cross-source **dedup** sits under the whole chain: one source event stamps a shared
`event_id = hash(source_event_id + event_code)` across its Pixel/CAPI/Offline variants, so a single conversion is not
double-counted (SMK-003 PASS 4/4; `integration/payload.py`, CTR-008; M6.2D §1–2).

---

## 3. The three end-to-end invariants

### 3.1 Every hop is measured — PASS at core (fail-closed on drift + consent)

- **Event-registry enforcement (no invented event, FAIL-003 / RULE-001):** two independent layers — the frontend hook
  rejects a code outside the locked base vocab (9 events `VIEW_LANDING…ORDER_VERIFIED`, `tracking/base_events.py`), and
  the server endpoint `POST /api/ads/events/track` re-rejects a code not ACTIVE in the CONSUMED read-only `event_registry`
  (`app/api/track.py`, `registry/validator.py`); an unknown / de-registered / wrong-type event is audited and not
  written — "nothing silently lost" (M6.2A §1–2, M6.2B §1–2). SMK-001 PASS.
- **Consent fail-closed on the external path (FAIL-002):** not-VALID ⇒ no external measurement / audience / CRM
  (`consent/gate.py`, RULE-002; SMK-002 PASS). Egress is independently bolted shut: `permits_external_send()` hard-returns
  `False` for every token while M6-OD-003 is OPEN — "framework-only regardless of consent" (M6.2A §2). The conversions
  seam's borrowed-consent hole (M6.2D `F-D`) was **closed fix-first at M6.2E**: the endpoint now MANDATORY-binds
  `customer_or_guest_key ↔ consent subject_ref` and rejects borrowed consent (`app/api/conversions.py`, RULE-002/FAIL-002).
- **Dedup:** SMK-003 PASS (shared platform `event_id`). Cross-source dedup has no double-count: F-E (non-injective
  join) was **closed fix-first at M6.2E** (escaped → injective; M6.2E §1); the one remaining residual is O-2
  (customer-excluded key) — an **under-count**, not a double-count, and it does not trip FAIL-001 (M6.2D §7.2). A
  separate **verified-revenue** double-count on the dashboard (`F-DASH-3`, rows sharing `order_code`) is covered in §3.3.

### 3.2 Attribution traceable end to end — PASS at core; ONE channel-reachable OPEN (single-subject bind)

- **Resolver trace (PASS):** the `AttributionResolver` traces `campaign/adset/ad/page/live/comment/messenger` and grades
  a missing source → `MISSING_SOURCE`/`LOW`, a conflict → `MULTI_TOUCH`/`DUPLICATE_RISK`/`LOW`-`HOLD`, only a complete
  single channel → `HIGH` (M6.2E §2; SMK-006 full source → dashboard, SMK-007 missing source → LOW/HOLD, SMK-013
  live/comment/messenger trace — all PASS). A LOW/HOLD row is flagged not-scale-evidence, and even a clean HIGH row is
  not scale evidence while `SCALE_MODEL_RATIFIED=False` — doubly fail-closed. A verified row is immutable; a correction
  is an audited append-only `AdjustmentRecord` (RULE-008).
- **OPEN — `F-SEC-2I-1` single-subject trace bind (PRIMARY; the one channel-reachable chain finding):** the funnel folds
  `comment_id` / `messenger_thread_id` / `psid` **each independently** across all events sharing one `live_session_id`,
  with **no subject binding**. A multi-subject live session (the normal case — one broadcast, many people) would stitch
  person A's `comment_id` next to person B's `messenger_thread_id` into one exported `FunnelTrace`, asserting a false
  association between distinct identifiable people (M6.2I §5.3). *Reachability:* **channel-reachable** — armed-not-fired
  only because (a) the canonical tests use single-subject sessions and (b) the funnel is not wired to any endpoint today
  (no live export surface). *Route:* CODER — bind the trace to a single `customer_or_guest_key` (or record per-subject
  traces) **before any admin export**; gated at the **M6-OD-011** integration binding. **Label note:** the pack's
  standing-blocker list calls this "**F-FUNNEL-4** (single-subject trace bind)"; the M6.2I runbook that owns it calls it
  **F-SEC-2I-1 ("Cross-person trace stitch")** — the same defect (see §4, label reconciliation).
- **OPEN — `F-SEC-2I-2` raw `messenger_thread_id`:** `FunnelTrace.to_public` masks only `psid`; `messenger_thread_id`
  (a per-person handle) / `comment_id` / `live_session_id` export raw — a masking-scope inconsistency that ratifies
  under **M6-OD-012** (same family as M6.2E O-2b, M6.2J F-SEC-2J-2). Not a present leak (staged, no export). *Route:*
  CODER + M6-OD-012 (M6.2I §5.3).

### 3.3 Verified-only revenue enforced end to end — PASS at core (store set-once + `verified_rows()`), with open write-path residuals (F-DASH-1/3) and a growth regression (F-GROWTH-3)

This is the invariant the chain exists to protect, and it has a **traceable three-slice arc** worth stating plainly:

- **Core enforcement (PASS):** revenue is verified-only *by construction*. The store's set-once `materialize()` writes
  `revenue_value` **only** on the ORDER_VERIFIED path (Zone-B, RULE-003; `attribution_materializer`, CTR-023, M6.2E
  §1–2); Zone-A UPDATE/DELETE and "revenue without ORDER_VERIFIED" are rejected at the store (CTR-001, M6.2B §3). The
  dashboard reads **only** `verified_rows()` — "quote/cart/draft/waiting contribute 0.0 revenue and no ROAS"; a
  quote/order-draft shown as revenue is an immediate DQ FAIL (M6.2F §2). Proven: SMK-004 (quote → no revenue), SMK-005
  (draft/unverified → not Revenue Verified), SMK-015 (quote shown as revenue → Fail), SMK-006 (verified → ROAS/CPA/AOV)
  — all PASS. Only ORDER_VERIFIED is revenue is reaffirmed as the fail-closed default for the OPEN M6-OD-008.
- **OPEN — `F-GROWTH-3` verified-only choke not carried to the Finance-facing growth path (RULE-003 cross-slice
  regression):** at M6.2F the materializer derived "verified" from the *conversion's* event_code and never asserted the
  measurement event's own `event_code == ORDER_VERIFIED` (`F-DASH-1`, armed-not-fired). M6.2I adopted the self-enforcing
  `event_code == 'ORDER_VERIFIED'` choke to close F-DASH-1 **on the funnel surface only** — the M6.2F dashboard
  materializer itself was **not** retrofitted, so **F-DASH-1 still stands on the dashboard write path** (armed-not-fired:
  the materializer is test-wired only, not channel-reachable; M6.2F §7.1, M6.2I §5.2). **M6.2J did not carry it forward
  to growth either** — `reads.verified_rows`
  keys off `revenue_value is not None`, so a mispaired (ORDER_VERIFIED conversion, QUOTE_SENT event) row stamps revenue
  onto quote content that the growth layer then counts as CRM / Diamond / **commission-ready** revenue (M6.2J §5.2).
  *Reachability:* trusted-input / code-exec-only (materializer test-wired; FAIL-001 out of scope for M6.2J) — **not
  channel-reachable** — but it reaches a Finance-facing figure. *Route:* CODER — `verified_rows` must AND
  `event_code == 'ORDER_VERIFIED'` with revenue presence (adopt the M6.2I lesson). **This is why "verified-only revenue
  enforced end to end" is TRUE at the store/dashboard core but NOT yet self-enforcing on the growth path.**
- **OPEN — `F-GROWTH-1 / F-SEC-2J-1` CRM subject-bind (borrowed consent, PRIMARY):** the CRM growth gate evaluates the
  consent snapshot fetched by `order_code` but never asserts `snapshot.subject_ref` equals the verified row's buyer, so
  a different subject's VALID CRM consent authorized the buyer's CRM Revenue KPI (executed: `crm_revenue() == 650000`).
  The M6.2E conversions seam already enforces this exact bind (the F-D fix), and the Diamond path in the same slice
  already reads the row's `customer_id`/`guest_id` — the CRM growth gate simply omits it. *Reachability:* trusted-input /
  code-exec-only (`consent_by_order` is a consumed Consent/CRM map, not channel input) — FAIL-002 held. *Route:* CODER
  (top item), mirror the M6.2E F-D bind (M6.2J §5.2).
- **OPEN — dashboard revenue-integrity residuals (armed-not-fired, M6.2F/CODER; not in the 8 standing blockers):**
  `F-DASH-3` — `revenue_verified()` sums per-row while `verified_order_count()` dedups by `order_code`, so two verified
  rows sharing an `order_code` double-count Revenue Verified + AOV (M6.2F §7.1; fix: dedup revenue by `order_code`). Plus
  a data-quality robustness family — a non-finite (`NaN`/`Inf`) or negative `revenue_value` on a genuine verified row
  poisons the verified-revenue rollup and breaks idempotent replay (M6.2E O-5, M6.2F N-1/N-2, M6.2I N-1; fix:
  `math.isfinite(v) and v >= 0`). Both are trusted-input/data-quality, not channel-reachable; neither trips FAIL-001.
- **Diamond stays measure-only (PASS, FAIL-004 / RULE-019):** Module 6 records referral attribution and a
  `commission-ready revenue` subset (verified × a consumed Finance eligibility flag, fail-closed to 0) but has **no**
  commission amount/rate/payout method — a token sweep finds 0 override defs; Finance owns commission (SMK-014 PASS,
  M6.2J §1–3).

---

## 4. Honest OPEN / BLOCKED reporting *(acceptance check 2)*

### 4a. The 8 standing blockers carried inside the M6.2K owner package (never dropped)

| # | Blocker id | Chain relevance | Owner |
|---|---|---|---|
| 1 | **M6-P1000** | M6.2A entry-judge verdict **BLOCKED** (not converted); M6.2A opened via `M6-OVERRIDE-M6P1000-STAGED`, re-gated at M6.2G | owner/judge |
| 2 | **M6-P1309** | M6.2D exit-judge verdict **BLOCKED** (not converted); M6.2E opened via `M6-OVERRIDE-M6P1309-STAGED` (stages, does not convert) — leg-2 (no raw PII) conformance deferred on OPEN **M6-OD-003** + the discovered consent fail-open F-D (since closed at M6.2E) | owner/judge |
| 3 | **M6.2G-SCALE** | ENTRY-001/003 real-scale conditions, the four M6-P1600 attestation true-ups, ENTRY-004 M5 DEBT-1…4 + the adversarial P4 re-gate, scale ACCESS-1/F-SCALE-\*, and **M6-OD-002/003/004/005** (M6-OD-005 attribution-model choice is the live scale-evidence gate for §3.2) | owner |
| 4 | **M6.2H-LEARN** | **M6-OD-006/007**, F-LEARN-\* | owner |
| 5 | **M6.2I-FUNNEL** | **F-SEC-2I-1** single-subject trace bind (§3.2, the "F-FUNNEL-4" label) + **F-SEC-2I-2** raw `messenger_thread_id` | owner |
| 6 | **M6.2J-GROWTH** | **F-GROWTH-1** CRM subject-bind + **F-GROWTH-3** verified-only choke (§3.3) + F-SEC-2J-\* | owner |
| 7 | **M6-OD-011** | admin-endpoint authN/authZ — the integration step that must also fix F-SEC-2I-1/2 before any surface | owner |
| 8 | **M6-OD-012** | PII masking scope — the F-SEC-2I-2 / F-SEC-2J-2 / F-SEC-2K-1 family ratifies here | owner |

### 4b. OPEN owner decisions that touch the chain

- **M6-OD-005** (attribution model: first/last/weighted/cohort) — OPEN; the dashboard may display multiple models but
  the scale gate needs one authoritative model; no model is scale-authoritative while `SCALE_MODEL_RATIFIED=False`.
- **M6-OD-003** (hash policy + permitted Pixel/CAPI/Offline send fields) — OPEN; the hard forward gate before any real
  external send; the SMK-017 green proves only the fail-closed hashing mechanism, not owner ratification.
- **M6-OD-008** (PAYMENT_COMPLETED as revenue) — OPEN; fail-closed default keeps ORDER_VERIFIED the only revenue source.
- **M6-OD-004** (Meta vs Google connector), **M6-OD-009** (Golden Hour event set), **M6-OD-012** (masking scope — OPEN, above).
- **M6-OD-011 — DECIDED, not an OPEN decision (precision per the brief's SoT rule):** the owner *decision* M6-OD-011
  (target repo/stack) is **DECIDED 2026-07-23** (GREENFIELD; `DECISION_REGISTER.md` + `IMPLEMENTATION_TARGET_LOCKED.json`
  = LOCKED). The standing blocker #7 labeled "M6-OD-011" is the pack's shorthand for the **admin-endpoint authN/authZ
  integration step** that the decision deferred (runtime framework/DB/authN still unresolved in the manifest — its own
  gated decision before surfacing). It is a forward *integration condition*, not an open owner question.

### 4c. Label reconciliation (a real cross-reference discrepancy, surfaced not buried)

The canonical standing-blocker list (`evidence/gap_blockers.py`, and the M6-P2009 judge notes) labels the
single-subject trace-bind defect **"F-FUNNEL-4"**. The M6.2I runbook that owns the finding has **no F-FUNNEL-4** — its
F-FUNNEL series is 1/2/3 (in-process code-exec-only, defense-in-depth), and the single-subject trace-bind defect is
**F-SEC-2I-1 ("Cross-person trace stitch")**. Same defect, two labels. Anyone tracing the standing blocker to its source
should read M6.2I `F-SEC-2I-1`. This does not change the posture; it is flagged for traceability.

### 4d. FBC deferral status (resolved)

M6.2F noted `M6-DEFER-FBC-M6.2D.json` as "still not filed"; **M6.2J supersedes it — the file is FILED** (owner-confirmed
2026-08-07; consent fail-open class CLOSED + wired as a Scale-Gate RequiredInput). One canon step remains (add its path
to `M6-P1600.inputs_expected` in `00-spec`) — **operator** TODO.

### 4e. Chain-surface residuals worth an owner's eye that are NOT among the 8 standing blockers

Armed-not-fired M6.2F/CODER items on the dashboard surface through which verified revenue + attribution flow — disclosed
here because a reader relying on the review + the 8 standing blockers would otherwise not see them:

- **F-VIEW-1 (the primary M6.2F security finding) — raw psid in the staged dashboard support view.** The staged `0008`
  support view (`ads_dashboard_kpi_source`) `SELECT`s the raw `attribution_context` column, which carries raw `psid`
  (+ comment/thread/live ids) — a reader role would see raw psid, broader exposure than the PII-safe app. Latent (view
  staged, never applied). *Route:* CODER, before the M6-OD-011 durable DB binding; align with M6-OD-012 (M6.2F §7.1).
- **F-DASH-4 — scale-evidence eligibility is incomplete.** `is_scale_evidence_eligible` consults only attribution
  HIGH+NONE, never the 8-item DQ overall; it is AND-gated by `SCALE_MODEL_RATIFIED=False` today and owned by the M6.2G
  re-gate (M6-P1600) (M6.2F §7.2).

---

## 5. Immutable posture & module boundary (verified, untouched)

- `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`; `SCALE_MODEL_RATIFIED` /
  `SCALE_EXECUTION_ENABLED` / `HASH_POLICY_RATIFIED` / `LEARNING_AUTOPUBLISH_ENABLED` / `DASHBOARD_ALERT_THRESHOLDS_DEFINED`
  = `False`; `live_migrations=false`. No enabling value is written anywhere by this review.
- Module boundary intact across every hop: Module 6 **measures** — it never creates revenue/orders, confirms payment,
  prices (M3 owns QuoteSnapshot), sends CRM, computes commission (Finance owns it), scales budget, or publishes
  optimizations. Order/QuoteSnapshot creation is M3 on customer confirmation (RULE-021, consumed); commission is
  measured-not-computed (RULE-019).
- `M6-P1000` + `M6-P1309` verdicts remain **BLOCKED** (not converted). Production/gateway/external-send stay OFF through
  PR/PILOT; the production flag must be verified STILL OFF at owner sign-off (doc §23).

---

## 6. Review outcome (analysis-only — no self-certification)

The end-to-end chain is **coherent and honestly evidenced at the staged altitude**: every hop is measured with
registry + consent fail-closed enforcement, attribution traces campaign→live→comment→messenger→verified with fail-closed
grading, and verified-only revenue is enforced at the store/dashboard core by construction (set-once Zone-B +
read-only `verified_rows()`; SMK-003/004/005/006/007/013/014/015 all PASS in the 523-passed M6.2K re-run) — with the
armed-not-fired materializer per-row-assertion residual F-DASH-1 (§3.3/§4e) noted. No fail gate
(FAIL-001/002/003/004/008) trips from a reachable path today.

It is **not** a production/ROAS-pass/scale-ready declaration, and this review does not make one — that is owner-only at
PR/PILOT. Two chain-integrity conditions are **OPEN** and are the load-bearing forward gates: **F-SEC-2I-1** (attribution
must be single-subject bound before any export — the one channel-reachable item) and **F-GROWTH-3** (the verified-only
`event_code == 'ORDER_VERIFIED'` choke must be carried into the Finance-facing growth reads), with **F-GROWTH-1** (CRM
subject-bind) and **F-SEC-2I-2** (raw `messenger_thread_id`) alongside. All four are disclosed in the pack's 8 standing
blockers and routed to CODER / owner; none is channel-reachable to a gate trip while the funnel is unwired and
`external_send=OFF`.

**Next:** operator runs the machine EVIDENCE_GATE for M6-P3000. The chain's OPEN conditions above are the owner's
PR/PILOT agenda alongside the 8 standing blockers; the M6-OD-011 integration binding is where F-SEC-2I-1/2 must be closed
before the funnel or dashboard is surfaced. Nothing here authorizes scale, external send, auto-publish, CRM send,
commission computation, or a readiness/Pass declaration.
