# M6.2I — Slice Runbook — Phase 2 Golden Hour Funnel (measure-only)

| Field | Value |
|---|---|
| Slice | **M6.2I — Phase 2 Golden Hour Funnel** (the **first Phase-2 slice**; a **derived, measure-only projection**) |
| Written by | **M6-P1808** — `M6_2I_DOCS` (ANALYST_ARCHITECT, `analysis_only`) |
| ADS phase | **Phase 2** (per the slice spec) — opened only after the full Phase-1 chain M6.2A–H completed + SIGNED |
| Depends on | M6.2H (slice gate M6-P1709 SIGNED) |
| Doc source | doc §8 conversion machine (Golden Hour states §7/§8 L138; the flow-event chain L151–157) + doc §14 funnel rates |
| Done gate (slice spec) | **Golden Hour conversion smoke pass** |
| Objective | Measure the Phase-2 conversion machine: the Golden Hour funnel across PRE→LIVE→POST→CLOSED, the AI-consult handoff, order-capture signals, and retargeting **on valid events + valid consent only**. The slice proves capability with evidence; it flips no flag, operates no session, sends nothing. |

> **Read this first — what "measure-only" means, and where the real risk is.** The band is clean: entry gate a
> real Judge PASS (M6-P1800 `SIGNED`; ENTRY-002 re-checked genuinely clean), all seven band prompts self-report
> PASS, and **both** in-scope fail gates held — **M6-FAIL-001** (revenue misuse) and **M6-FAIL-010** (phase jump).
> A strong architecture call keeps this narrow: the slice adds **no new table / migration / CTR / config flag** —
> it is a **derived read-only projection** over the existing `ads_measurement_events` (CTR-001) + `ads_attribution_context`
> (CTR-002) (RULE-018), and the Golden Hour *state* is a measurement observation, never a session controller
> (RULE-013). Its self-enforcing verified-only revenue **closes the M6.2F F-DASH-1 gap on the funnel surface**. But
> "clean" does not mean "closed": exit leg 1 is **SUPPORTED at the staged level** (the tester marks it "met" and
> both fail gates hold), not independently closed — and **the finding most worth attention is F-SEC-2I-1
> (cross-person trace stitch, §5.3)**: the funnel folds `comment_id`/`messenger_thread_id`/`psid` across *all*
> events sharing one `live_session_id` with no subject binding, so a **multi-subject live session** (the normal
> case — one broadcast, many people) would stitch **different people's identifiers into one exported trace,
> asserting a false association**. It is armed-not-fired only because the canonical tests use one-subject sessions.
> Posture is immutable: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all M6.2A–H
> flags False, `live_migrations=false`; `M6-P1000` and `M6-P1309` verdicts **remain BLOCKED (not converted)**. This
> runbook advances no gate and self-certifies nothing; the runner EVIDENCE_GATE and the slice-gate Judge (M6-P1809)
> decide.

---

## 1. What this slice built (staged under `04-artifacts/impl/M6.2I/`)

Everything is **staged** (convention-reference tree, never a live repo). The whole M6.2H tree is carried forward
byte-identical; M6.2I **adds** a small `funnel/` measurement package — and **nothing else** (no migration, no config
flag, and no patched carried file: see §5.1). **Nothing acts** — no code operates a live session, sends, scales,
publishes, changes order state, or flips a flag.

### 1.1 The funnel layer (new `app/measurement/funnel/`) — a derived read-only projection

| File | What it is | Contract / Rule |
|---|---|---|
| `funnel/golden_hour.py` | `GoldenHourState` (`PRE/LIVE/POST/CLOSED/UNKNOWN`) + `observe_state()` — a **pure measurement projection** that labels an *observed* golden-hour signal. **No** `start`/`close`/`emit`/controller (RULE-013; Gateway/Live operates the session). Absent/ambiguous/non-string ⇒ **UNKNOWN** (fail-closed, M6-OD-009). `GOLDEN_HOUR_START/REMINDER` are constants only, never emitted. | RULE-013; M6-OD-009 |
| `funnel/flow.py` | `FlowStage` (the six doc §8 flows) + the **verbatim doc §8/§10 event-code → stage map** (codes referenced from canon, **none invented**, none added to the Phase-1 client allow-list) + the ordered `CHAIN` + `REVENUE_VALID_EVENT="ORDER_VERIFIED"` (RULE-003) + `FUNNEL_RATE_SPECS` (the doc §14 rate formulas verbatim). | RULE-001/003/018 |
| `funnel/models.py` | Frozen `GoldenHourFunnelView` / `FunnelRate` / `FunnelTrace`. `to_public()` masks `psid` (RULE-014/H02); **only verified revenue** is present (RULE-003); no write/trigger field (RULE-012). | CTR-001/002 (reuse) |
| `funnel/funnel.py` | `GoldenHourFunnel` — the **read-only assembler**: groups the measurement store's events by `live_session_id`, buckets by observed Golden Hour state, per-stage counts + the doc §14 rates (**reusing `kpi_metrics._safe_div`** + the §14 definitions at the per-session grain), the **self-enforcing verified-only revenue** (RULE-003, see §5.2), the **RULE-021** `capture_gate_passed` (consumed Commerce flag; absent ⇒ False), and the **SMK-013** live/comment/messenger trace from `ads_attribution_context`. No write/send/scale/publish method. | CTR-001/002; RULE-003/013/021 |
| `funnel/retargeting.py` | `RetargetingMeasurement` — measure-only eligibility: a recognized engagement signal **AND** `ConsentGate.evaluate(snapshot, ConsentScope.AUDIENCE_SYNC)` (reuse the **existing** scope; **no new scope invented**, RULE-018). Missing/expired/opt-out/scope-not-granted/unrecognized ⇒ not eligible (fail-closed). **No send/enqueue/transport surface** (`external_send=OFF`). | RULE-002/004/018; measure-only |

### 1.2 The doc §8 flow-event chain (measured; codes verbatim, extract L151–157)

`Ads → Live → Comment → Messenger → Quote → Order → Verified`, assembled per `live_session_id` and bucketable by
Golden Hour state. Event codes are **consumed canon** (doc §10 Event Taxonomy), validated upstream at ingest against
the Core `event_registry` (RULE-001); M6.2I references them as measurement-time constants and invents none. Owner
boundaries are respected: Gateway/Live operates the session, Commerce (M3) creates the QuoteSnapshot/order on
customer confirmation (RULE-021), the AI-consult *content* (M4) is never read — only the handoff *events*
(`MESSENGER_STARTED`, `AI_PROPOSAL_SENT`) are measured; **only `ORDER_VERIFIED` is revenue** (RULE-003).

### 1.3 The doc §14 funnel rates (reused, per-session grain, fail-closed)

`Comment = LIVE_COMMENT/LIVE_VIEW` · `Inbox = MESSENGER_STARTED/LIVE_COMMENT` · `Quote = QUOTE_SENT/MESSENGER_STARTED`
· `Order = ORDER_CREATED/QUOTE_SENT` · `Verified = ORDER_VERIFIED/ORDER_CREATED`. Every division is fail-closed
(0/None denominator → None, never fabricated), reusing the `kpi_metrics` formula definitions at the finer per-chain
/ per-Golden-Hour-state grain (the global compute is left untouched).

### 1.4 No new migration, no new config flag (deliberate)

Doc §13 (the minimal Data Object Contract) defines **no** golden-hour/funnel/session table; inventing one would
breach RULE-018. The projection reads the existing migrations (0002 `ads_measurement_events` + 0006
`ads_attribution_context`). Measure-only ⇒ no new posture flag. Both omissions are deliberate minimal-change calls,
not gaps.

---

## 2. Operate

M6.2I is a **measure-only, read-only projection**. There is no "operate a session / send / publish" step — by design.

1. **Assemble a funnel** — `GoldenHourFunnel` reads the existing measurement + attribution stores, groups by
   `live_session_id`, buckets by observed Golden Hour state, and returns per-stage counts + the §14 rates +
   verified-only revenue + the trace. It writes nothing.
2. **Observe Golden Hour state** — labels an observed signal PRE/LIVE/POST/CLOSED; absent/ambiguous ⇒ UNKNOWN
   (fail-closed). It **never** starts, closes, or emits a session — Gateway/Live operates it.
3. **Measure retargeting eligibility** — classifies an event as retargeting-eligible only on a recognized signal
   **and** valid `AUDIENCE_SYNC` consent; it **never sends or enqueues** (M6.2C/D owns send; `external_send=OFF`).
4. **What is structurally impossible here** — operating a live session, surfacing a public final price, counting a
   quote/order-created as revenue, sending/scaling/publishing, or changing order state.

> **Owner-facing caveat (do not skip).** The funnel is **not wired to any endpoint today** (the planned dashboard
> section was reverted — §5.1), so there is no live export surface yet. Before it is surfaced through
> `GET /api/admin/ads/dashboard`, the M6-OD-011 binding must (a) **authenticate/authorize the admin caller** (doc
> §22 line 429; never trust a body-supplied identity), and (b) **fix F-SEC-2I-1 / F-SEC-2I-2** (bind the trace to a
> single subject; bring trace-id masking to psid parity) — otherwise the export would assert false cross-person
> associations and leak raw per-person identifiers.

---

## 3. Verify

**Verify env:** `02-tester/.venv` — python **3.12.13**, pytest **8.4.2**, pluggy 1.6.0 (matches the
`IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin). Run from `04-artifacts/impl/M6.2I/` (STAGED_ONLY), cache-free.

### 3.1 Bound smoke

| Smoke ID | Doc ID | Scenario → Expected (verbatim, SMOKE_REGISTER) | Test file | Result |
|---|---|---|---|---|
| **M6-SMK-004** | ADS-P0-004 | `Quote được tạo nhưng chưa order` → `Không revenue, không ROAS` | `tests/smoke/test_smk_004_quote_in_golden_hour_funnel_not_revenue.py` | **PASS 4/4** |
| **M6-SMK-013** | ADS-P0-013 | `Live/Comment/Messenger chain` → `Trace được live_session_id, comment_id, messenger_thread_id` | `tests/smoke/test_smk_013_funnel_live_chain_trace.py` | **PASS 4/4** |

Bound-smoke total: **8 passed, 0 failed — exit 0**. SMK-004 covers: a quote counts as a funnel stage but 0 verified
revenue; an order-created (not verified) is 0 revenue; a quote **force-carrying** a `revenue_value` still reports 0
(the self-enforcing choke); and no ROAS from a quote on either the funnel or the M6.2F dashboard. SMK-013 covers:
the live/comment/messenger trace threaded from `ads_attribution_context`; psid masked on export; partial chains
trace only what is present (never fabricated); a no-live-chain session traces neither id.

```bash
# from 04-artifacts/impl/M6.2I/  (venv: 02-tester/.venv, python 3.12.13)
python -m pytest -v tests/smoke/test_smk_004_quote_in_golden_hour_funnel_not_revenue.py tests/smoke/test_smk_013_funnel_live_chain_trace.py -p no:cacheprovider
# -> 8 passed ; exit 0
```

### 3.2 Full staged suite

**386 passed, 0 failed, 0 skipped, 0 error — RC 0.**
Breakdown: **351 carried-forward** (M6.2A–H) **+ 35 new M6.2I nodes** (27 funnel-leg + 8 bound smoke).

> **Test-count reconciliation (be precise).** The **tester-run final is 386** (M6-P1804 / SMOKE_RESULTS.md). The
> coder note (M6-P1802) records **378** = 351 carried + the **27 funnel-leg tests it authored** (26 initial + 1
> review regression); the **8 bound smoke** nodes (SMK-004 4 + SMK-013 4) were authored by the **TESTER** in
> M6-P1803 and run in M6-P1804, so the tester-run final adds them (378 + 8 = 386). Per test-count discipline this
> runbook cites the **tester-run final 386**. (Continuity note: the 351 carried matches the M6.2H **tester-run
> final** 351, not the M6.2H coder intermediate 345 — the tree collects 351.)

The 27 funnel-leg tests (supporting coverage, all green inside the 386): `test_golden_hour_funnel_chain.py` (3),
`test_golden_hour_state_measure_only.py` (4), `test_quote_in_funnel_not_revenue.py` (4),
`test_live_chain_trace_in_funnel.py` (3), `test_retargeting_consent_valid_only.py` (6),
`test_order_capture_commerce_gate_rule021.py` (4), `test_funnel_measure_only_boundary.py` (3).

### 3.3 Both in-scope fail gates — NOT tripped

- **M6-FAIL-001 (revenue misuse) — held.** The funnel's verified-only revenue is **self-enforcing** (see §5.2): it
  sums revenue only from a row whose **own** `event_code == ORDER_VERIFIED` and that carries a revenue value, so a
  quote/order-created — even one force-carrying a `revenue_value` — reports 0. Boundary + security concurred; the
  PII/secret scan was clean over **186 files**.
- **M6-FAIL-010 (phase jump) — held.** The funnel is a measure-only derived projection with **no** later-phase
  (scale/learning/outbox/Phase-3) transitive import, and Phase 1 (M6.2A–H) is complete/sequential/SIGNED before this
  first Phase-2 slice (RULE-016). No new table/migration/CTR/flag, no live-session controller.

---

## 4. Rollback (every change this slice made) — *acceptance check 1*

Everything is **staged** ⇒ rollback is non-destructive. The projection writes nothing to the stores.

| Change | Rollback |
|---|---|
| **Baseline (all M6.2I)** | Delete the `04-artifacts/impl/M6.2I/` tree. M6.2H is untouched (carried forward byte-identical). |
| `funnel/__init__.py`, `golden_hour.py`, `flow.py`, `models.py`, `funnel.py`, `retargeting.py` (new) | Delete the files. |
| New tests (7 funnel-leg files + 2 bound smoke files) + `conftest.py` fixtures | Delete the files / revert the fixture additions. |
| **Patched carried-forward files** | **None.** The planned dashboard wiring (PLAN §5 P1/P2) was **reverted to M6.2H byte-identical** (see §5.1), so there is no carried file to revert. |
| **Migrations** | **None added.** No new table (RULE-018); nothing to unwind. |

The projection is derived + read-only: removing it leaves `ads_measurement_events` / `ads_attribution_context`
exactly as M6.2H left them. There is **no** production/state/flag change to reverse.

---

## 5. Decision deltas & governance

### 5.1 Plan-delta: the dashboard wiring was reverted (a correct role-boundary call)

The plan (M6-P1801 §5 P1/P2) proposed surfacing the funnel as an optional read-only section on the existing
`GET /api/admin/ads/dashboard` (CTR-018). Implementing it **broke two carried-forward tests** that assert
`set(vars(DashboardDeps).keys()) == {"mart"}` — including the **TESTER-owned** smoke
`tests/smoke/test_smk_010_data_mart_support_view_only.py`. Editing a TESTER-owned smoke to make a CODER patch pass
is out of the CODER role (the M6.2E Round-1 lesson; RULE-015 / role boundary). Since the dashboard section is not
required by any M6.2I exit-gate leg, both edits were **reverted to M6.2H byte-identical** and the funnel ships as a
**standalone measurement layer**; wiring it (with a corresponding TESTER smoke update) belongs to the owner
integration step (M6-OD-011). This is the right call — the alternative (a role moving another role's goalposts to
green its own change) is exactly what the pack forbids.

### 5.2 Positive: self-enforcing verified-only revenue closes the M6.2F F-DASH-1 gap (on the funnel surface)

The coder's own 3-dimension adversarial self-review caught **one MINOR** (fixed + regressed): the funnel's
`_verified_revenue` first gated on `revenue_value is not None` **only**, never on the row's own event code — the
**same pattern as the M6.2F F-DASH-1 gap**. Fixed: the choke now ANDs `event_code == ORDER_VERIFIED` with revenue
presence, so a mispaired/forced revenue on a non-verified row contributes 0. **On the funnel surface F-DASH-1 is
closed**, and SMK-004 confirms the funnel and the M6.2F dashboard agree at 0 (no ROAS) for a quote. (Honest scope
note: this fixes the *funnel's* revenue choke and demonstrates the correct self-enforcing pattern; whether the
M6.2F *dashboard materializer* itself was retrofitted with the same per-row assertion is a separate M6.2F/CODER item
— not claimed closed here.)

### 5.3 Funnel residuals (armed-not-fired; none trips FAIL-001/010) — routed to CODER / M6-OD-011

| ID | Sev | What | Route / fix |
|---|---|---|---|
| **F-SEC-2I-1** | **PRIMARY — load-bearing** | **Cross-person trace stitch.** `GoldenHourFunnel._trace` folds `comment_id`/`messenger_thread_id`/`psid` **each independently** (`x = x or ctx.get(x)`) across **all** events grouped under one `live_session_id` — a *session-level shared key* (one broadcast, many people) — with **no subject binding**. A multi-subject session stitches person A's `comment_id` next to person B's `messenger_thread_id` (+ person C's psid) into one exported `FunnelTrace`, **asserting a false association between distinct identifiable people** (attribution-integrity + PII; masking psid does not cure it — `comment_id`/`messenger_thread_id` export raw). Armed-not-fired for a hard breach only because the canonical tests use one-subject sessions. | CODER: bind the trace to a **single subject** (`customer_or_guest_key`) or record **per-subject** traces. Close before any admin export. |
| **F-SEC-2I-2** | → M6-OD-012 | `FunnelTrace.to_public` masks **only** `psid`; `comment_id`/`messenger_thread_id`/`live_session_id` export **raw** — but `messenger_thread_id` is a per-person Messenger conversation handle (same identity-boundary family as psid). Masking-scope inconsistency; parallels M6.2E O-2b; interacts with F-SEC-2I-1. | CODER + M6-OD-012: ratify the trace-id masking scope; at minimum bring `messenger_thread_id` to psid parity. |
| **F-FUNNEL-1** | primary (in-process) | The revenue-choke `event_code == REVENUE_VALID_EVENT` dispatches to the left operand's `__eq__`, so a `str`-subclass with override-True `__eq__` (plus an `object.__setattr__` store-guard bypass) could count a quote row as verified revenue. **Not channel-reachable** (both need arbitrary in-process code exec; ingest yields plain JSON strings, RULE-001) — a defense-in-depth inconsistency vs the consent-scope type-hardening (M6.2B/D F2). | CODER: compare via `type(x) is str AND == …` (and on `stage_for`/`_count_code`). |
| **F-FUNNEL-2 / F-FUNNEL-3** | in-process | The funnel `dict()`-copies its two consumed maps but reads each event's `attribution_context` **live/unsnapshotted**, so a hostile `Mapping.get` **executes attacker code inside `assemble()` — the executed PoC drove a real in-process `store.materialize()` Zone-B write**, i.e. the "read-only / writes nothing" guarantee is breachable in-process (F-FUNNEL-2). The same unsnapshotted `ctx` also makes the projection non-deterministic / measurement drift (F-FUNNEL-3, TOCTOU). Not channel-reachable (the injector already holds store capability; the store's set-once / forbidden-op guards remain the backstop). | CODER: snapshot `ctx = dict(ctx)` before reading — closes both. |
| **N-1 / N-2** | Note | **N-1**: a non-finite (NaN/Inf) revenue on a genuine verified row **poisons the session's `verified_revenue`** (no guard in the store or the funnel sum; propagates to the view / any downstream rollup) — DQ robustness; fix `math.isfinite(v) and v>=0`. **N-2**: frozen-view / str-subclass forge — in-process code exec only, not channel-reachable. | CODER (N-1); defense-in-depth (N-2). |

### 5.4 Forward gates (new this slice + inherited)

None blocks this measure-only slice; **all bind before the funnel is surfaced / before any real scale, publish, or send.**

- **New (M6.2I):** **F-SEC-2I-1** + **F-SEC-2I-2** (attribution-integrity / trace-id masking) and the **ACCESS**
  forward requirement (authenticate/authorize the admin caller per doc §22 line 429 **and** apply trace-id masking)
  when the funnel is bound to `GET /api/admin/ads/dashboard` at the M6-OD-011 integration — mirrors ACCESS-1 from
  M6.2G/M6.2H. **M6-OD-009** (GOLDEN_HOUR_START/REMINDER event set) stays a design-scoping decision (optional /
  disabled-by-default; absent ⇒ UNKNOWN fail-closed). **M6-OD-012** (masking scope, now with F-SEC-2I-2).
- **Inherited (M6.2G + M6.2H, still in force):** the **four attestation true-ups**; ENTRY-001/003/004 real-scale /
  M5 conditions; **M6-OD-002/003/004/005**; the M6.2G **F-SCALE-*** + M6.2H **F-LEARN-*** residuals + the
  **M6-OD-006/007** learning gates; and ACCESS-1 / authN + store/queue-laundering fixes at the M6-OD-011 binding.
  The mandatory M6.2G Scale-Gate re-gate stands before any real scale/publish/send.

### 5.5 Immutable posture (intact across M6.2A–I)

`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, and all M6.2A–H scale/hash/learning flags
remain **False**; `live_migrations=false`. `M6-P1000` + `M6-P1309` verdicts remain **BLOCKED (not converted)**.
FAIL-001/010 not tripped; the funnel measures only — nothing is sent, scaled, published, or live-operated.

---

## 6. Changelog delta — *acceptance check 2*

- **No new `SCHEMA_CHANGELOG` row is appended by this slice.** This is an `analysis_only` docs prompt (the analyst
  is denied write to `00-spec/registers/` anyway), and the slice introduces **no canon schema change**.
- **No canon-flip is pending for this slice.** Unlike the earlier slices, the two contracts it uses —
  **CTR-001** (`ads_measurement_event`, 20 fields, doc §10) and **CTR-002** (`ads_attribution_context`, 19 fields,
  doc §11) — are already **`DRAFT_LOCKED`** in the canon `CONTRACT_REGISTER` (built at M6.2B / M6.2E). The funnel
  **reads** them; it does not re-define them, and it introduces no new contract.
- **This slice deliberately adds no schema at all** (RULE-018): **no new table, no new migration, no new config
  flag, no new CTR** — the concrete artifact this slice added is only the staged `app/measurement/funnel/` package
  (a derived read-only projection). The planned dashboard-section patch was reverted (§5.1), so there is no
  register/schema footprint from it either.

---

## 7. Handoff

- **What this slice is.** The **first Phase-2 slice** — a measure-only Golden Hour funnel projection over the
  existing Phase-1 stores. It opened only after the full Phase-1 chain (M6.2A–H) was complete and SIGNED (RULE-016;
  FAIL-010 not tripped).
- **Exit-gate state at this docs step** (from the evidence index §4, carried faithfully — M6.2I has **6** exit-gate
  items):
  - Items **2, 3, 6 = MET** (SMK-004 4/4; SMK-013 4/4; rollback documented per item).
  - Item **1 = SUPPORTED (staged)** — the tester marks leg L1 "met" and both fail gates hold, but the
    F-FUNNEL-1/2/3 + **F-SEC-2I-1** residuals remain (armed-not-fired), so **final closure is the slice-gate Judge's call**.
  - Item **4** (all slice prompts have evidence JSON) closes when **M6-P1808** (this docs prompt) and **M6-P1809**
    (Judge) produce their evidence — after this prompt, only **M6-P1809.json** is outstanding.
  - Item **5** (slice-gate Judge PASS sign-off) closes only at **M6-P1809**.
- **Next slice.** After the M6.2I slice-gate Judge (M6-P1809), the next prompt is the **M6.2J entry-gate Judge
  (M6-P1900)** (ledger row 168).
- **CODER TODO (before the funnel is bound to any admin export at M6-OD-011):** **F-SEC-2I-1** (bind the trace to a
  single subject / per-subject traces — the top item), **F-SEC-2I-2** (trace-id masking parity), F-FUNNEL-1
  (`type(x) is str AND ==`), F-FUNNEL-2/3 (`dict(ctx)` snapshot), N-1 (`math.isfinite(v) and v>=0`).
- **Owner / M6-OD-011 binding:** authenticate the admin caller (doc §22 line 429) **and** apply trace-id masking
  when the funnel is surfaced through `GET /api/admin/ads/dashboard`; **M6-OD-012** (masking scope); **M6-OD-009**
  (event set) stays a design-scoping decision — plus the inherited M6.2G/M6.2H forward chain (the four attestation
  true-ups, ENTRY-001/003/004, M6-OD-002/003/004/005, F-SCALE-*/F-LEARN-*/OD-006/007).

---

## 8. Pointers for the slice-gate Judge (M6-P1809)

The Judge renders the slice verdict **strictly from the evidence files** (this runbook is descriptive, not a
verdict). Suggested reading order:

1. `00-spec/slices/M6.2I.md` "Exit gate checks" — the 6 items.
2. For legs 1–3 + 6, read the primary evidence directly (do **not** rely on this runbook or the index):
   `04-artifacts/test-reports/M6.2I/SMOKE_RESULTS.md`, `04-artifacts/boundary-reports/M6.2I_boundary.md`,
   `04-artifacts/security-reports/M6.2I_security.md`, `04-artifacts/impl/M6.2I/PLAN.md` +
   `IMPLEMENTATION_NOTES.md` §4 (plan-delta) + §6 (rollback).
3. **Confirm the measure-only posture** (no new table/migration/CTR/flag; no live-session controller) and that the
   verified-only revenue choke is **self-enforcing** (closing the F-DASH-1 gap on the funnel surface), and that
   **both in-scope fail gates (FAIL-001, FAIL-010) are not tripped**.
4. **Weigh F-SEC-2I-1 as the load-bearing item** (§5.3): the cross-person trace stitch is armed-not-fired only
   because the canonical tests are one-subject — a normal multi-subject live session would fire it. F-SEC-2I-2
   (trace-id masking scope) and the ACCESS forward requirement close alongside it at the M6-OD-011 binding; the
   F-FUNNEL-1/2/3 items are in-process-only defense-in-depth.
5. **Confirm items 4 & 5** by re-reading the ledger and `04-artifacts/evidence/judge/` (the M6-P1809 sign-off is
   the Judge's own output).
6. Treat the inherited **B6 forward-gate chain (§5.4)** and the standing **BLOCKED `M6-P1000` / `M6-P1309`**
   verdicts as the conditions before any real scale, publish, send, or admin export — none of which this measure-only
   slice satisfies or claims to.

*This runbook advances no gate and self-certifies nothing. The runner EVIDENCE_GATE and the slice-gate Judge
(M6-P1809) decide closure. `global_gateway_state=BLOCKED`, `production_flag=OFF`; the funnel only measures.*
