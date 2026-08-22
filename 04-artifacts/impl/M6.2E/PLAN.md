# M6.2E IMPLEMENTATION PLAN — Attribution Resolver & Materializer (STAGED, plan-only)

**Prompt**: M6-P1401 (`M6_2E_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code this prompt)
**Slice**: M6.2E — resolve the full attribution chain to verified revenue; missing/conflicting sources degrade to
LOW/HOLD and never become scale evidence (RULE-009); attribution snapshots immutable after verify, corrections
only via an adjustment record (RULE-008); doc §11. Depends on M6.2D.
**Posture (immutable)**: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
`HASH_POLICY_RATIFIED=False`. This plan writes no code, applies no migration, calls nothing external, flips no flag.

> **Governance — JUDGE-SIGNED entry under an OWNER OVERRIDE, with fix-first bindings.** M6.2D slice-exit
> (M6-P1309) verdict was **BLOCKED** (a governance hold on the OPEN in-scope M6-OD-003 hash-policy conformance +
> chain gaps — NOT a leak, NOT a tripped fail gate; the *mechanism* passed SMK-003/017 and F-B/F-C/F-A were
> confirmed closed). The owner filed **M6-OVERRIDE-M6P1309-STAGED** (+ **M6-DEFER-OD003-M6.2D**) to open M6.2E
> **STAGED only** (verdict stays BLOCKED, not converted). The M6.2E entry gate (M6-P1400 = SIGNED) **binds
> fix-first**: **F-D** (measurement-path borrowed consent — my own M6.2D §4.3 flag, now formal; verified at the
> M6.2E exit M6-P1409) and carries **F-E / F-F** (latent residuals in my M6.2D code) to close before
> `external_send` can ever flip. **O-1** (unsalted sha256) folds into M6-OD-003; **O-2/O-4** (DQ) route to M6.2F.
> **Governance gap (re-escalated):** `M6-DEFER-FBC-M6.2D.json` (binding F-B/F-C/F-A + F-D) is STILL not filed —
> an operator/owner action; this plan closes F-D/F-E/F-F regardless per the override + entry-gate binding.

---

## 1. Entry-gate verification

| Precondition | Source | Result |
|---|---|---|
| This prompt RUNNING | ledger row 119 | **M6-P1401 = RUNNING** ✓ |
| Dependency resolved | ledger row 118 | **M6-P1400 = SIGNED** (opens M6.2E STAGED via M6-OVERRIDE-M6P1309-STAGED; M6-P1309 stays BLOCKED) ✓ |
| Target LOCKED + M6-OD-011 | manifest | LOCKED / STAGED_ONLY / safety all false; M6-OD-011 DECIDED ✓ |
| Slice contracts | M6-P1400 evidence | **CTR-002** `ads_attribution_context` = **DRAFT_LOCKED** (SPEC §10.2, 19 fields); **CTR-023** `attribution_materializer` harmonized + satisfied-for-entry (producer M6-P0713 PASS, gate M6-P0715 SIGNED) ✓ |
| Fix-first bindings | M6-P1400 + M6-P1309 sign-off | **F-D fix-first (exit-verified); F-E/F-F carried** — §5.1 ✓ |
| Forward/OPEN owner decisions | DECISION_REGISTER | M6-OD-005 (attribution model) OPEN → multi-model *display*, single-model *scale evidence* pending owner (scope OUT); M6-OD-003/004 before real send; commission = Finance (RULE-019, OUT) ✓ |
| Flags | manifest/brief | BLOCKED/OFF/OFF, HASH_POLICY_RATIFIED=False, live_migrations=false ✓ |
| M6.2D foundation | `04-artifacts/impl/M6.2D/` (185 tests green) | present; carried forward per §2 ✓ |

**Conclusion**: open for **STAGED** M6.2E; F-D fix-first (M6-P1409 verifies), F-E/F-F closed here; real send /
scale gated forward (M6-OD-003/004/005, M6.2G re-gate).

---

## 2. Working mode, conventions & staging model

Reuse the M6.2D/C/B/A baseline (pytest, frozen dataclasses, read-only ports + in-memory staged adapters, staged
migrations up+down, workers as plain callables, forgiving-seam, mask-on-export). **Cumulative snapshot**: the
whole **M6.2D** tree (185 tests) is carried forward byte-identical; M6.2E **patches** the F-D/F-E/F-F sites and
**adds** the attribution layer. The change set (§5) is the diff; carried-forward files touched are noted (§9.1).
Nothing sends; `external_send=OFF` immutable.

---

## 3. Scope lock (anchored strictly to `00-spec/slices/M6.2E.md`)

**In scope (4 capabilities):**
1. **Attribution Resolver / Ads Context Resolver / Live Session Resolver** — resolve the source chain
   (campaign/adset/ad/page/live/comment/messenger/quote/order/verified) from an `ads_measurement_event` +
   `conversion_event` into an `ads_attribution_context`; missing/conflicting → LOW confidence / HOLD
   (`conflict_status`), never scale evidence (RULE-009).
2. **`ads_attribution_context` population** (CTR-002, 19 DRAFT_LOCKED fields, SPEC §10.2).
3. **`attribution_materializer` worker** (CTR-023) — materialize the snapshot and write **Zone B** of the
   `ads_measurement_event` (attribution_context, `revenue_value` from ORDER_VERIFIED only, order_code), **set-once**,
   immutable after verify (RULE-008/003); idempotent recompute; LOW/HOLD never scale evidence (RULE-009).
4. **Adjustment-record path** — a post-verify correction is NOT a direct mutation (rejected) but an
   `AdjustmentRecord{actor, reason, audit, evidence}` (RULE-008, SMK-018).

**Out of scope (explicit):**
- **Commission computation** — Finance owns; Module 6 records referral attribution only (RULE-019; FAIL-004 Core
  override). Diamond fields (`referral_link_id`, `diamond_id`) recorded, never a commission number.
- **Attribution model final choice** (M6-OD-005) — implement **multi-model display** (first_touch/last_touch
  recorded); the **single-model scale-evidence** designation is fail-closed pending the owner (no model is marked
  scale-authoritative until M6-OD-005).
- **Dashboards / ROAS-CPA-AOV rendering** (M6.2F — SMK-006 here proves the *materialized Zone B* that feeds it, not
  the dashboard); **DQ checker** transitions (CTR-024, M6.2F; O-2/O-4); **scale/learning** (M6.2G+).
- **Real send / hashing policy** (M6-OD-003/004; `external_send=OFF`).

---

## 4. Design overview — resolve → materialize (set-once) over the existing measurement store

```
 ads_measurement_event (Zone A, M6.2B) + conversion_event (M6.2C)  ── ORDER_VERIFIED?
        │
        ▼  Attribution Resolver (+ Ads Context / Live Session sub-resolvers)
   ads_attribution_context (CTR-002, 19 fields): campaign..ad / page / live/comment/messenger / quote/order /
        referral / first_touch+last_touch / entry_channel / source_confidence(HIGH|MEDIUM|LOW) /
        conflict_status(NONE|MULTI_TOUCH|MISSING_SOURCE|DUPLICATE_RISK)
        │  missing source -> conflict=MISSING_SOURCE + confidence=LOW ; conflict -> MULTI_TOUCH/DUPLICATE_RISK + LOW/HOLD
        ▼  attribution_materializer (CTR-023, worker)
   store.materialize(event_id, attribution_context, revenue_value(ORDER_VERIFIED only), order_code)  [SET-ONCE]
        │  already-verified + change -> DIRECT MUTATION REJECTED -> AdjustmentRecord{actor,reason,audit,evidence}
        ▼
   ads_measurement_event Zone B populated (immutable after verify, RULE-008); LOW/HOLD flagged NOT scale-evidence (RULE-009)
```

**Load-bearing invariants (top-0.1% core):**
- **Revenue only from ORDER_VERIFIED (RULE-003, FAIL-001).** The materializer sets `revenue_value` **only** when
  the source is ORDER_VERIFIED; quote/cart/draft/waiting never carry revenue. (SMK-006 vs SMK-004/005.)
- **Immutable after verify + adjustment record (RULE-008, SMK-018).** Zone B is **set-once**; a post-verify
  correction is a **rejected** direct mutation that must be an audited `AdjustmentRecord` — verified revenue is
  **never silently overwritten**.
- **Missing/conflicting → LOW/HOLD, never scale evidence (RULE-009, SMK-007, FAIL-004-adjacent).** A missing or
  conflicting source degrades `source_confidence`/`conflict_status`; such a row is flagged **not-scale-evidence**;
  revenue is still stored (SMK-007). No model is marked scale-authoritative until M6-OD-005.
- **Full source trace (leg 1, SMK-006/013).** An ORDER_VERIFIED traces back through quote/order to
  campaign/adset/ad/page/live/comment/messenger (Live Session Resolver → live_session_id/comment_id/
  messenger_thread_id).
- **No commission, no order-state, no Core override (RULE-019, FAIL-004).** Record referral attribution only.
- **Consent fail-closed (F-D) / injective ids (F-E) / crash-hardened (F-F)** — §5.1.

---

## 5. Minimal change set (all target-relative, staged under `04-artifacts/impl/M6.2E/`)

Legend: **Leg** = M6.2E exit-gate leg. Rollback: new files → delete; patched carried-forward files → revert to M6.2D.

### 5.1 Fix-first BINDING — DONE FIRST (per M6-P1400 / M6-P1309)

| # | Target file(s) (patched) | Fix | Rule | Leg | Regression constraint |
|---|---|---|---|---|---|
| **F-D** | `app/api/conversions.py` (+ `ConversionDeps` gains a read-only `consent_reader`) | Bind `customer_or_guest_key ↔ consent snapshot subject_ref` at conversion creation (checkpoint 1), mirroring the F-C audience fix: resolve the consent snapshot; if its `subject_ref` != `customer_or_guest_key` → reject `CONSENT_MISSING_OR_INVALID` (**borrowed consent refused**). Closes the measurement borrowed-consent reachable from the untrusted `/conversions` body. | RULE-002; **FAIL-002** | 1 | carried M6.2C/D conversion tests green (default body's cs_valid.subject == customer_or_guest_key) |
| **F-E** | `app/measurement/integration/payload.py` | `platform_event_id` joins `source_event_id|event_code` UNESCAPED → non-injective (two distinct events can collide → **under-count**). Fix: escape the delimiter before joining (same injective serialization as the RULE-005 `_escape`), so distinct events never share an event_id. | RULE-005; FAIL-001-adjacent | (SMK-003) | M6.2D dedup/event_id tests green; distinct events → distinct ids |
| **F-F** | `app/measurement/outbox/measurement_dispatcher.py` + `audience_dispatcher.py` | `subject = getattr(snap, "subject_ref", None)` sits BEFORE the F-A `try/except` and only swallows `AttributeError` — a hostile `subject_ref` **property that raises** crashes `run_once`. Fix: extract `subject_ref` inside a fail-closed guard (any exception → None), so a raising property can never crash the worker. | seam robustness | 1 | normal path unchanged; a raising property → deny, no crash |

> **Fix-first order (top-0.1% check):** F-D is a **more-reachable twin of F-C** (from the untrusted `/conversions`
> body) — armed-not-fired only because `external_send=OFF`; it MUST close before any real send. F-E/F-F are latent
> bugs in the M6.2D send discipline (my own code) — an under-counting id and a crashable worker. All three land
> and prove green **before** the attribution build; the M6.2E exit gate (M6-P1409, FAIL-002 in scope) verifies F-D.

### 5.2 New — the attribution layer

| # | Target file (new) | Purpose | Contract/Rule | Leg | Smoke |
|---|---|---|---|---|---|
| B1 | `app/measurement/models/attribution_context.py` | `AdsAttributionContext` (CTR-002): the 19 DRAFT_LOCKED fields (campaign/adset/ad ids+names, page_id, live_session_id, comment_id, messenger_thread_id, psid[PII], referral_link_id, diamond_id, entry_channel enum, attribution_window, first/last_touch_event_id) + `SourceConfidence(HIGH\|MEDIUM\|LOW)` + `ConflictStatus(NONE\|MULTI_TOUCH\|MISSING_SOURCE\|DUPLICATE_RISK)`; frozen; psid masked on export. | CTR-002; RULE-009/014 | 1 | SMK-006/007/013 |
| B2 | `app/measurement/attribution/__init__.py`, `app/measurement/attribution/resolver.py` | `AttributionResolver` (+ `resolve_ads_context`, `resolve_live_session`): build the context from an event+conversion; **missing source → conflict=MISSING_SOURCE, confidence=LOW; conflict → MULTI_TOUCH/DUPLICATE_RISK, LOW/HOLD** (RULE-009); trace live/comment/messenger (SMK-013). Read-only over consumed sources; never a Core override (FAIL-004). | CTR-002; RULE-009 | **1** | **SMK-006/007/013** |
| B3 | `app/measurement/attribution/materializer.py` | `AttributionMaterializer` (CTR-023 worker): materialize the snapshot and call the store's **set-once** Zone-B write — `revenue_value` ONLY from ORDER_VERIFIED (RULE-003); idempotent (deterministic; re-run yields same); a LOW/HOLD row is flagged **not scale evidence** (RULE-009); NEVER overwrites verified revenue (RULE-008). Multi-model: records first/last touch; scale-authoritative model deferred (M6-OD-005). | CTR-023; RULE-003/008/009 | 1 | SMK-006/007 |
| B4 | `app/measurement/attribution/adjustment.py` | `AdjustmentRecord{actor, reason, audit_ref, evidence_ref, at}` + an `AdjustmentLog`; a post-verify correction goes here (audited), NEVER a direct row mutation (RULE-008, SMK-018). PII masked. | RULE-008 | 1 | **SMK-018** |
| B5 | `app/measurement/store/measurement_event_store.py` (**patched, carried-forward** — §9.1) | Add `materialize(event_id, *, attribution_context, revenue_value, order_code, verified)`: **set-once** Zone-B enrichment (replace the frozen row with Zone B populated) — refuses to overwrite an already-verified `revenue_value`/`attribution_context` (raises `MeasurementStoreViolation` → caller must use an adjustment record); `insert()`'s no-revenue-at-Zone-A guard stays. | CTR-001; RULE-003/007/008 | 1 | SMK-006/018 |

### 5.3 Staged migration & config

| # | Target file (new/patched) | Change | Leg | Rollback |
|---|---|---|---|---|
| M1 | `migrations/0006_create_ads_attribution_context.sql` | Staged DDL (up+down): CTR-002 19 fields + keys/indexes + an immutability-after-verify guard comment (Zone-B set-once); never applied. (`ads_measurement_events` Zone B already exists in the 0002 DDL — this is the standalone attribution snapshot table per M6-OD-011 embed-vs-FK.) | 1 | down-DDL DROP; delete file |
| A1 | `app/config.py` (**extend**) | add `SCALE_MODEL_RATIFIED = False` (M6-OD-005 OPEN → no attribution model is scale-authoritative; fail-closed) + `SCALE_EVIDENCE_MIN_CONFIDENCE = "HIGH"` (RULE-009 gate constant). No enabling flag changed. | 1 | revert to M6.2D |

---

## 6. Test plan → done-gate / smoke mapping (`pytest -q`; TESTER executes L2–L5)

Fixtures extend `conftest.py` with an attribution resolver, the materializer, an adjustment log, and seed
events/conversions (fully-sourced ORDER_VERIFIED; source-missing ORDER_VERIFIED; a live/comment/messenger chain).
Carried-forward M6.2D **185 tests stay green**. PII markers assembled at runtime (no literal PII in source).

| # | Target test (new) | Proves | Leg | Smoke | Fail-gate |
|---|---|---|---|---|---|
| T1 | `tests/test_attribution_trace_to_source.py` | leg 1: an ORDER_VERIFIED with full campaign/adset/ad + page traces back to source; context populated; confidence HIGH, conflict NONE. | **L1** | **SMK-006** | FAIL-001 |
| T2 | `tests/test_attribution_missing_source_low_hold.py` | SMK-007: ORDER_VERIFIED with NO source → revenue STILL stored (Zone B), `source_confidence=LOW` / `conflict=MISSING_SOURCE`, row flagged **not scale evidence** (RULE-009). | L1 | **SMK-007** | FAIL-001 |
| T3 | `tests/test_live_session_chain_trace.py` | SMK-013: a live/comment/messenger event traces `live_session_id`, `comment_id`, `messenger_thread_id` into the context (Live Session Resolver). | L1 | **SMK-013** | — |
| T4 | `tests/test_verified_immutable_adjustment.py` | SMK-018: a post-verify correction — a direct Zone-B mutation is **rejected**; an `AdjustmentRecord{actor,reason,audit,evidence}` is created instead; verified revenue never overwritten (RULE-008). | L1 | **SMK-018** | — |
| T5 | `tests/test_materializer_revenue_and_scale_rules.py` | revenue ONLY from ORDER_VERIFIED (RULE-003; a non-verified source → no revenue); LOW/HOLD never scale evidence (RULE-009); NO commission computed (RULE-019); idempotent re-materialize. | L1 | SMK-006/007 | FAIL-001/004 |
| T6 | `tests/test_m6_2e_fixfirst_regressions.py` | **F-D** (a conversion citing another subject's consent → `CONSENT_MISSING_OR_INVALID`, borrowed consent refused); **F-E** (two distinct events whose components would collide across the `|` join get DISTINCT event_ids); **F-F** (a snapshot whose `subject_ref` property raises → dispatcher denies, `run_once` does not crash). | **L1** | (SMK-002) | **FAIL-002** |

**Smoke → test binding**: SMK-006 = T1(+T5); SMK-007 = T2; SMK-013 = T3; SMK-018 = T4. Execution + recorded
results/evidence (legs L2–L5) is the **TESTER**'s (M6-P1403/1404). SMK-018 is proposed; leg 5 satisfied by
executing it. No self-run / self-certify (RULE-015).

---

## 7. Master traceability matrix

| Item | Files | Contract | Rule(s) | Leg | Smoke | Fail-gate | Rollback |
|---|---|---|---|---|---|---|---|
| F-D borrowed-consent bind | conversions.py | CTR-017/006 | RULE-002 | L1 | (SMK-002) | FAIL-002 | revert to M6.2D |
| F-E injective event_id | payload.py | CTR-008 | RULE-005 | (SMK-003) | — | — | revert to M6.2D |
| F-F crash-harden subject | both dispatchers | CTR-021/022 | seam | L1 | — | — | revert to M6.2D |
| Attribution context model | B1 | CTR-002 | RULE-009/014 | L1 | SMK-006/007/013 | — | delete |
| Resolver (+live/ads) | B2 | CTR-002 | RULE-009 | **L1** | **SMK-006/007/013** | FAIL-004 | delete |
| Materializer (set-once) | B3,B5 | CTR-023/001 | RULE-003/008/009 | **L1** | SMK-006/007 | FAIL-001 | delete / revert store |
| Adjustment record | B4 | — | RULE-008 | L1 | **SMK-018** | — | delete |
| Migration + config | M1,A1 | CTR-002 | RULE-008/009/H01 | L1 | — | — | down-DDL / revert |
| Tests | T1–T6 | — | — | L1 (+L2–L5 runnable) | SMK-006/007/013/018 | FAIL-001/002/004 | delete |

**Legs**: L1 ✓ (trace-to-source + all the above); L2–L5 ✓ *made runnable* (TESTER executes SMK-006/007/013/018);
L6 (evidence — process), L7 (judge — process; verifies F-D), **L8 ✓ (this doc — rollback per item)**. ✓

---

## 8. Rollback strategy (global)

1. **Nothing live.** Staged under `04-artifacts/impl/M6.2E/`; no migration applied, no external call, no flag
   written. Baseline rollback = delete the M6.2E tree (M6.2D untouched).
2. **Per-item** (§5): new files → delete; patched carried-forward files (`conversions.py`, `payload.py`, both
   dispatchers, `measurement_event_store.py`, `config.py`) → revert to their M6.2D version.
3. **Zone-B / immutability caveat**: after a real apply, a materialized+verified row is set-once — a correction is
   the adjustment-record path, never a row rewrite; reverting the attribution table uses M1 down-DDL.

---

## 9. Plan-deltas & notes

### 9.1 Deltas
- **`measurement_event_store.py` gains a `materialize()` Zone-B set-once method** (carried-forward patch). The
  frozen row + forbidden `update()`/`delete()` (RULE-007) stay; `materialize()` is the ONLY Zone-B write and is
  set-once (verified revenue never overwritten, RULE-008). `insert()`'s no-revenue guard is unchanged.
- **`ConversionDeps` gains a read-only `consent_reader`** for F-D (default `None` → binding skipped, backward-
  compatible for carried tests that build deps without a reader; M6.2E wires it so F-D is enforced + tested).
- **F-E** changes the *serialization* of `platform_event_id` (escaped join) only — the shared-event_id
  cross-platform-dedup property is preserved; the M6.2D dedup tests stay green.
- **Multi-model (M6-OD-005 OPEN)**: record `first_touch_event_id` + `last_touch_event_id`; NO model is marked
  scale-authoritative (`SCALE_MODEL_RATIFIED=False`, fail-closed). Scale-evidence eligibility also requires
  `source_confidence=HIGH` + `conflict=NONE` (RULE-009).

### 9.2 Open items / governance
- **Governance gap (re-escalated)**: `M6-DEFER-FBC-M6.2D.json` (binding F-B/F-C/F-A + F-D) still not filed;
  operator/owner action; wire into the M6.2G gate (M6-P1600) RequiredInputs. This plan closes F-D/F-E/F-F under
  the M6-OVERRIDE-M6P1309-STAGED binding regardless.
- **O-1** (unsalted sha256) — a sub-question of **M6-OD-003** (salt/pepper + normalization); the payload hash
  mechanism stays fail-closed; the salted approach applies when M6-OD-003 ratifies. Not a M6.2E code change.
- **O-2/O-4** (DQ under-count + unbounded BLOCKED result-log records) — **M6.2F** (data-quality checker CTR-024);
  carried, not closed here.
- **M6-OD-003/004** (hash/connector) before real send; **M6-OD-005** (attribution model) before scale evidence;
  **M6-OD-008** → revenue ORDER_VERIFIED-only (RULE-003). Commission = Finance (RULE-019, OUT). The **MANDATORY
  M6.2G re-gate** (ENTRY-001/002/003; M6-P1000 + M6-P1309 verdicts BLOCKED, not converted) stands before any real
  scale or external send. Smoke execution (legs L2–L5) is the TESTER's (M6-P1403/1404).

---

## 10. Acceptance self-map

1. *Every item → leg or smoke* → §5–§7. ✓  2. *Rollback per item* → §5/§8. ✓  3. *No scope beyond the slice* →
§3 (commission/model-choice/dashboards/DQ/real-send deferred). ✓  4. *Target LOCKED + M6-OD-011 decided* → §1. ✓
5. *Reuse conventions* → §2 (M6.2D baseline). ✓  Plus the **BINDING**: F-D fix-first (exit-verified) + F-E/F-F,
each with a test (T6) and a regression constraint (M6.2D 185-test suite stays green). ✓

*Plan-only: no code, no migration applied, nothing sent/scaled/published, no flag flipped; BLOCKED/OFF/OFF.*
