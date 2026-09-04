# M6.2L PLAN — Post-Pilot Audit Fix Batch (STAGED, plan-only)

**Prompt**: M6-P2101 (`M6_2L_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code) · **Gate**: EVIDENCE_GATE
**Slice**: M6.2L — close the **5 M6-self-doable** defects from the 2026-09-03 chief-auditor audit (against commit
`5f09894`), as a **cumulative superset** of the M6.2K staged tree under `04-artifacts/impl/M6.2L/`. This slice
proves the fixes with **regression evidence only**; cross-module / owner-gated audit items are tracked separately.

> **Posture (immutable, this slice flips nothing):** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
> `external_send=OFF`; all scale/hash/learning flags `False`; `live_migrations=false`. No code declares ROAS Pass /
> Scale Ready, self-certifies (RULE-015), flips a flag, applies a migration, sends externally, or exposes raw PII.
> Status here is **coder self-reported**; the runner gate + JUDGE (M6-P2109) decide.

Implementation target **LOCKED**, **M6-OD-011 DECIDED 2026-07-23** (verified in
`04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json`). Ledger verified: **M6-P2101 = RUNNING**, dependency
**M6-P2100 = SIGNED**. Doc working mode (extract L463–472): *do not guess; read the repo first; reuse conventions +
test patterns; minimal change; output files-touched + tests + commands + PASS/FAIL + rollback*.

---

## 0. Adversarial red-team of this plan — what a 12-agent review changed (top-0.1% lens, verified on real code)

Before finalizing, an independent 3-dimension review (each finding re-verified by a separate skeptic reading the
real M6.2K files) was run against a first draft. It **confirmed two serious defects** in the draft — both now
fixed in this plan — plus minor items. This is the honest record of what changed:

- **[was CRITICAL, now fixed] B4 backward-compat premise was FALSE.** The draft claimed "no carried test calls
  `measurement_store.materialize(...)` directly." **Four** carried tests do; two of them —
  `tests/test_quote_in_funnel_not_revenue.py:34` and the **TESTER-owned smoke**
  `tests/smoke/test_smk_004_quote_in_golden_hour_funnel_not_revenue.py:57` — call
  `materialize("e_bad_q", …, revenue_value=500000.0, verified=True)` on a **QUOTE_SENT** row **not** wrapped in
  `pytest.raises`, deliberately forcing revenue onto a quote row to prove the *funnel* choke still reports 0. The
  draft's "make materialize **raise**" would ERROR both (one un-editable). → B4 redesigned: **self-check the stored
  row's own `event_code` and fail-closed *drop* (never record) illegitimate revenue — without raising** (§2-B4).
- **[was MAJOR, now fixed] A4 leg-2/SMK-020 "HIGH" was unreachable within the draft's scope.** The resolver counts
  a persisted `live_session_id` as a competing `LIVE_ORGANIC` channel → `FACEBOOK_AD + live = MULTI_TOUCH → LOW`
  (`resolver.py:147-191`), so an event carrying all 4 ids can never be HIGH; the draft touched only
  `track.py`+`normalize.py`. **And** the carried TESTER smoke `test_smk_007_neg_conflicting_multi_touch` (SMK-007,
  `:62-69`) sets `campaign_id` (an **incomplete** ad path) `+ live_session_id` and asserts **MULTI_TOUCH/LOW**. →
  A4 scope corrected to include a **narrow resolver rule** that reconciles both pack smokes: **a COMPLETE ad path
  (campaign+adset+ad) dominates a co-present `live_session_id` (→ FACEBOOK_AD/HIGH); an INCOMPLETE ad path + live
  stays MULTI_TOUCH** (§2-A4). This rule is *determined by the pack's own smokes* (SMK-007 ∧ SMK-020), not an open
  M6-OD-005 model choice.
- **[NIT, folded in] A3 `attribution_id` already exists as a column.** `migrations/0006:17` declares
  `attribution_id TEXT NOT NULL PRIMARY KEY -- PACK surrogate id`, one per measurement row
  (`uq_aac_measurement_event`). → A3 now **surfaces that existing surrogate id** as a first-class model field +
  handoff key, derived 1:1 from `event_id` — no new column, model↔DDL coherent (§2-A3).
- **[NIT, folded in] second `verified_rows`.** `growth/reads.py:23` has its own `verified_rows(store)` (used by CRM
  + Diamond revenue). → the B4 `event_code` filter is applied at **both** choke points (§2-B4).
- **[NIT, folded in] rollback granularity + PII.** `pack_assembler.py` is edited by B2 **and** B3 → §6 clarifies a
  shared-file rollback is a *scoped partial revert*; the 5 new test files get an explicit rollback. The 4 A4 ids
  are structured platform ids (same class as the existing type-checked-only `page_id`/`session_id`), not free
  text — disclosed, not scanned (§2-A4).

The lens also **confirmed** (unchanged): B2 (structural existence+uniqueness+category-binding keeps the 18 TESTER
`*_p0_evidence_pack.py` smokes COMPLETE) and B3 (membership-count floor, `len==8` unchanged) hold as drafted; every
fix stays measure/record-only, adds **no** migration/flag/table (RULE-018), and strengthens FAIL-001/007 +
RULE-003/009/014/015.

---

## 1. Repo summary & staging model (cumulative carry-forward)

- **Base**: the whole **M6.2K** tree (app + 12 migrations `0001–0012` + full carried suite incl. the 18 P0 smokes).
  M6.2L is a **superset**: carry M6.2K byte-identical, apply the 5 fixes + add CODER regression tests. (The carry
  runs in **M6-P2102 implement**, not this plan prompt.)
- **Stack** (locked target): Python 3.12, `framework=""` (framework-neutral pure functions), `pytest -q`, stdlib
  only; in-memory staged stores; physical DB/HTTP bind = owner M6-OD-011 step.
- **Layers touched** (ARCH_BASELINE): **Tracking** (A4 intake), **Attribution** (A3 id, A4 resolver rule, B4
  materialize choke), **Dashboard** + **Growth-reads** (B4 verified_rows), **Evidence** (B2 ref-validation, B3 gap
  floor). No new layer/contract object.
- **Baseline discipline (M6-P2102)**: verify green **before** any patch (subprocess `pytest`, parity with the
  M6.2K collect), then reach green again after the fixes + regressions; **no skips**; actual `N passed` is the count.

---

## 2. The 5 fixes — one item per exit-gate leg + smoke (minimal change, mapped, rollback per item)

Legend: **Leg** = M6.2L.md "Exit gate checks" number · **Smoke** = SMOKE_REGISTER id · file refs are M6.2K-current.

### FIX A3 — `attribution_id` trace  → **Leg 1 · SMK-019 · RULE-014**

- **SMK-019 (verbatim)**: *ORDER_VERIFIED with a resolved ad source → attribution_id present as a first-class key
  of AdsAttributionContext + handoff payload; ORDER_VERIFIED traces attribution_id → campaign.*
- **Current**: `AdsAttributionContext` (`models/attribution_context.py`) has 19 fields, **no `attribution_id`**;
  `to_public()`/`as_stored()` expose no trace key. But `migrations/0006_create_ads_attribution_context.sql:17`
  **already declares** `attribution_id TEXT NOT NULL PRIMARY KEY` (PACK surrogate id, one per measurement row via
  `uq_aac_measurement_event`). So A3 **surfaces an existing column**, not a new concept.
- **Minimal change** (2 files, additive):
  1. `models/attribution_context.py` — add `attribution_id: Optional[str] = None` (field #20 = the CTR-002
     surrogate id already in 0006, an M6-owned key on M6's **own** contract — no Core schema invention, RULE-018
     intact). Expose it in `to_public()` **and** `as_stored()` (governance/trace ref, **not PII** → no masking; no
     commission field, RULE-019).
  2. `attribution/resolver.py` — set a **deterministic** `attribution_id`, 1:1 with the measurement row (matching
     0006's `uq_aac_measurement_event`): `attr_` + a stable digest of `event_id` (the `normalize.event_id_for`
     pattern; no clock/randomness → re-materialize stays a no-op, store idempotency preserved).
- **Trace**: a materialized ORDER_VERIFIED row now carries `attribution_context["attribution_id"]` alongside
  `campaign_id` → id → row → campaign.
- **Backward-compat (verified)**: default field → existing constructors unaffected; additive keys don't break
  `data_mart._attr` (`:119`) / growth `attribution_value` (`reads.py:15`) / the "no commission" assertion
  (`test_materializer_revenue_and_scale_rules.py:59`); deterministic id keeps `test_rematerialize_is_idempotent`
  green.
- **CODER regression**: `tests/test_m6_2l_a3_attribution_id_trace.py` — attribution_id is a first-class field, is in
  `to_public()`+`as_stored()`, an ORDER_VERIFIED row exposes id→campaign, two resolves of the same inputs yield the
  **same** id.
- **Rollback**: revert the two files to M6.2K bytes (drop field + resolver line); no DDL (column pre-exists in 0006).

### FIX A4 — ad-hierarchy intake + resolver reconciliation  → **Leg 2 · SMK-020 · RULE-014**

- **SMK-020 (verbatim)**: *POST /api/ads/events/track for a FACEBOOK_AD event carrying campaign/adset/ad/
  live_session → intake + normalize persist the 4 ad-hierarchy ids; resolver reaches HIGH source confidence via the
  real API path.*
- **Current**: `AdsMeasurementEvent` **already has** `campaign_id/adset_id/ad_id/live_session_id`
  (`models/measurement_event.py:52-55`); the resolver reads them (`resolver.py:70-91`). Two gaps:
  1. **Intake** — `handle_track_request` (`app/api/track.py`) never reads the 4 ids from the body;
     `normalize_to_measurement_event` (`normalize.py`) never accepts/sets them → a real-API FACEBOOK_AD event lands
     with them unset.
  2. **Resolver grading** — even once persisted, a co-present `live_session_id` makes `live.present=True`
     (`resolver.py:65-67`), so `_entry_channels` appends **both** FACEBOOK_AD and LIVE_ORGANIC (`:147-156`) and
     `_grade` returns **MULTI_TOUCH/LOW** for `len(channels)>1` (`:190-191`) — **HIGH is unreachable**.
- **Minimal change** (3 files, additive/narrow):
  1. `app/api/track.py` — read **optional** `campaign_id/adset_id/ad_id/live_session_id` from the untrusted body
     (RULE-H03): each a `str` if present (else reject `SCHEMA_INVALID`), else `None`. These are **M6-owned ad-link/
     UTM platform ids** (not PII, not channel free-text) — the same class as the existing type-checked-only
     `page_id`/`session_id`/`source` (`track.py:87-90`); persisted structured, not content-scanned (the payload PII
     tripwire still guards the free-form `payload`). Thread them into `normalize_to_measurement_event(...)`.
  2. `app/measurement/normalize.py` — add the 4 optional params, set them on the Zone-A `AdsMeasurementEvent`
     (Zone-B/revenue unset; DQ still `HOLD`).
  3. `app/measurement/attribution/resolver.py` — **narrow rule**: a `live_session_id` co-present with a **COMPLETE**
     ad path (`ads.complete` = campaign ∧ adset ∧ ad) is the ad funnel's **downstream live trace**, not a competing
     `LIVE_ORGANIC` entry → append `LIVE_ORGANIC` only when `live.present AND NOT ads.complete`. So a fully-
     identified FACEBOOK_AD event carrying a live_session resolves to a **single FACEBOOK_AD channel → HIGH/NONE**.
- **Why this reconciles the pack's own smokes (not an M6-OD-005 model choice)**: SMK-007's carried TESTER smoke
  `test_smk_007_neg_conflicting_multi_touch` (`:62-69`) uses `campaign_id` **only** (an *incomplete* ad path) +
  `live_session_id` and requires **MULTI_TOUCH/LOW**; SMK-020 requires a **complete** ad path + live_session →
  **HIGH**. The rule above is the *unique* behavior satisfying both: complete-ad dominates live; incomplete-ad+live
  stays MULTI_TOUCH.
- **Backward-compat (verified on real tests)**: every carried live-chain test is live **without** an ad path →
  LIVE_ORGANIC unchanged (`test_smk_013_*`, `test_live_session_chain_trace.py`); the only ad+live carried case
  (SMK-007 evt_multi, campaign-only) stays MULTI_TOUCH (incomplete path); ad+diamond MULTI_TOUCH
  (`test_materializer_revenue_and_scale_rules.py:28-43`) is untouched (live-specific rule). Implement re-confirms
  by baseline-green.
- **CODER regression**: `tests/test_m6_2l_a4_ad_hierarchy_intake.py` — a track body carrying the 4 ids → `ACCEPTED`,
  the stored row persists all 4; resolving that complete-ad FACEBOOK_AD event → **HIGH/NONE via the real API path**;
  a **non-string** id → `REJECTED SCHEMA_INVALID`; a control that incomplete-ad+live stays MULTI_TOUCH (rule is
  narrow, non-vacuous).
- **Rollback**: revert `track.py`+`normalize.py`+`resolver.py` to M6.2K bytes; no DDL (columns pre-exist in 0002).

### FIX B2 — evidence-forgery blocked (M6-OD-013)  → **Leg 3 · SMK-021 · RULE-015 / FAIL-007**

- **SMK-021 (verbatim)**: *a fake-but-nonblank ref, or one valid ref copy-pasted across all mandatory keys of all
  10 categories → categories read MISSING (never COMPLETE); ref existence + uniqueness + category-binding enforced,
  not raw truthiness.*
- **Current**: `_categories` (`evidence/pack_assembler.py:77-86`) marks a key present on **raw truthiness**
  (`provided.get(k)` non-empty) → `"x"` passes, and one valid ref pasted everywhere passes (FAIL-007 hole).
- **Minimal change** (1 file, backward-compatible): `pack_assembler.py` `_categories` (+ a private
  `_ref_valid_for(...)` helper), replacing truthiness with three checks — a key counts present **only** when its
  ref:
  1. **exists** — well-formed evidence ref, not blank/whitespace/junk (rejects the fake `"x"`). Optional injected
     `known_refs` oracle (forward seam) tightens existence to membership; absent it, existence = structural
     well-formedness.
  2. **category-binding** — bound to **this** `category`(+key), from the ref's self-describing shape
     (`ev::{category}::{key}`, the convention `conftest.full_evidence_refs:773` already uses).
  3. **uniqueness** — a **pack-wide** pass: a ref value used for >1 (category,key) slot is a duplicate and satisfies
     **none** (defeats the copy-paste forgery).
  Signature stays compatible: `assemble(smoke_results=None, evidence_refs=None, known_refs=None)`.
- **Result**: `"x"` → MISSING; one ref across all keys → MISSING (uniqueness ∧ binding); `full_evidence_refs`
  (unique+bound) → all COMPLETE → the **18 TESTER `*_p0_evidence_pack.py` smokes stay OWNER_REVIEW_REQUIRED**
  (verified: they assert that, and require all-COMPLETE) + `test_evidence_ten_categories_mandatory_content.py`
  (mine) unchanged.
- **CODER regression**: `tests/test_m6_2l_b2_evidence_ref_forgery.py` — fake ref ⇒ MISSING + NOT_READY; one ref
  pasted across all 10 categories' keys ⇒ **all** MISSING + NOT_READY; genuine `full_evidence_refs` still
  all-COMPLETE (non-vacuous).
- **Rollback**: revert `pack_assembler.py`'s `_categories`/helper (restore truthiness); B3's edit is a *separate*
  region (see §6).

### FIX B3 — gap-id collision/shadow floor (M6-OD-014)  → **Leg 4 · SMK-022 · RULE-015 / FAIL-007**

- **SMK-022 (verbatim)**: *gap-blocker list carries a duplicated/shadowing standing-blocker id (M6-P1000/M6-P1309)
  → the floor detects the duplicate and FAILs (membership count, not set-subset).*
- **Current**: the only "floor" is a **set-subset** assertion (`test_gap_blocker_list_carries_standing_blockers.py:15`)
  — a duplicate/shadow defeats it (a set still "contains" the id).
- **Minimal change** (2 regions, additive): 
  1. `evidence/gap_blockers.py` — add `standing_floor_ok(gaps) -> bool` (membership-count floor): PASS **iff** each
     canonical standing id appears **exactly once** and matches its canonical `(kind, description)` (no **shadow**);
     any duplicate/shadow/missing ⇒ **FAIL**. Governance refs only, no PII.
  2. `evidence/pack_assembler.py` — call the floor over the **emitted** gap list defensively (a shadow injected by
     any path degrades the pack to `NOT_READY` rather than silently passing). Normal output unchanged (the
     canonical list always passes).
- **Backward-compat (verified)**: `STANDING_GAP_BLOCKERS` still **8** distinct ids →
  `test_standing_blocker_list_covers_all_slice_forward_conditions` (`len==8`) + the subset assertions stay green.
- **CODER regression**: `tests/test_m6_2l_b3_gap_floor_membership.py` — canonical list passes; a **duplicated**
  `M6-P1000` FAILs; a **shadow** `M6-P1309` (same id, different description) FAILs.
- **Rollback**: revert the `gap_blockers.py` validator + the assembler's defensive call (scoped partial revert of
  the shared file — see §6).

### FIX B4 — ROAS verified-lock at materialize() + verified_rows()  → **Leg 5 · SMK-023 · RULE-003 / FAIL-001**

- **SMK-023 (verbatim)**: *in-process QUOTE_SENT row + store.materialize(revenue_value>0, verified=True) → no
  revenue set (event_code enforced at materialize); dashboard Revenue Verified = 0 and ROAS = 0 (event_code filter
  at verified_rows).*
- **Current hole**: `MeasurementEventStore.materialize` (`store/measurement_event_store.py:99`) gates revenue on the
  **caller's `verified` boolean**; `DataMart.verified_rows` (`data_mart.py:63-64`) and `growth.reads.verified_rows`
  (`reads.py:23-25`) filter only on `revenue_value is not None`.
- **The reconciliation constraint** (verified, load-bearing): two carried tests
  (`test_quote_in_funnel_not_revenue.py:28-37`, TESTER-owned `test_smk_004_...:49-60`) call
  `measurement_store.materialize("e_bad_q", …, revenue_value=500000.0, verified=True)` on a **QUOTE_SENT** row
  **not** wrapped in `pytest.raises`, then assert the **funnel** reports 0 (`funnel._verified_revenue` already ANDs
  `event_code==ORDER_VERIFIED`, `funnel.py:155-158`). Making `materialize` **raise** would ERROR them (one is a
  TESTER smoke). So the store must fail-closed **without raising**.
- **Minimal change** (3 files, self-checking, no new param):
  1. `store/measurement_event_store.py` `materialize(...)` — **self-check the STORED row's own `event_code`**
     (authoritative, fetched at `:96` — **not** a caller-supplied boolean/string): revenue/`order_code` are recorded
     **only** when `row.event_code == "ORDER_VERIFIED"`; otherwise the illegitimate revenue is **dropped**
     (`revenue_value` left None, no raise) and the refusal audited. The `verified` kwarg stays accepted (the 4
     direct callers pass it) but is **no longer the revenue authority**. The set-once RULE-008 raise and the
     `revenue-requires-order_code` raise (both on the ORDER_VERIFIED path) are unchanged — so
     `test_verified_immutable_adjustment.py:27-31` (a set-once overwrite on an ORDER_VERIFIED row) still raises.
  2. `dashboard/data_mart.py` `verified_rows()` — filter `revenue_value is not None AND event_code ==
     "ORDER_VERIFIED"` → `revenue_verified()`/ROAS inherit it (dashboard 0 for a leaked quote).
  3. `growth/reads.py` `verified_rows()` — the **same** filter (the parallel CRM/Diamond choke; F-GROWTH-3
     consistency).
- **Why "drop, not raise" is correct here**: SMK-023 requires "no revenue set" — a self-checked drop satisfies it;
  the two carried funnel smokes stay green (no raise; the row simply holds no revenue, funnel still reports 0); the
  authoritative dashboard/CRM/Diamond lock is the `verified_rows` `event_code` filter. Self-checking the *stored
  row's* code (not a passed value) also closes the "caller-trust" gap the audit named.
- **Backward-compat (verified on real tests + grep)**: no `make_verified_row(` overrides `event_code` (all default
  ORDER_VERIFIED); every revenue-bearing row reaching either `verified_rows()` is ORDER_VERIFIED
  (`test_dashboard_revenue_counts_only_verified`, CRM/Diamond/KPI); the fabricated non-OV+revenue rows in
  `test_dashboard_rejects_unverified_as_revenue.py:34` / `test_smk_005_*:59` go to the `DataQualityChecker`, **not**
  `verified_rows()`; the ORDER_VERIFIED materialize path (`make_verified_row`, SMK-006/007) still records revenue.
- **CODER regression**: `tests/test_m6_2l_b4_verified_lock.py` — `store.materialize(revenue>0, verified=True)` on a
  QUOTE_SENT row sets **no** revenue (dropped, no raise); a QUOTE_SENT row that somehow carries revenue is excluded
  by **both** `verified_rows()` (dashboard Revenue Verified 0, ROAS 0); the genuine ORDER_VERIFIED path still
  records revenue (non-vacuous control).
- **Rollback**: revert the three files to M6.2K bytes (restore the `verified` gate + single-predicate
  `verified_rows` ×2); no DDL.

---

## 3. Change-set summary (files touched — minimal, all under `04-artifacts/impl/M6.2L/`)

| # | File | Change | Kind |
|---|---|---|---|
| A3 | `app/measurement/models/attribution_context.py` | +`attribution_id` field (= 0006 surrogate id); expose in `to_public`/`as_stored` | code |
| A3 | `app/measurement/attribution/resolver.py` | set deterministic `attribution_id` (1:1 with event_id) | code |
| A4 | `app/api/track.py` | read+validate 4 optional ad-hierarchy ids (untrusted), pass to normalize | code |
| A4 | `app/measurement/normalize.py` | accept+set the 4 ids on the Zone-A row | code |
| A4 | `app/measurement/attribution/resolver.py` | LIVE_ORGANIC competes only when `NOT ads.complete` (complete-ad dominates live) | code |
| B2 | `app/measurement/evidence/pack_assembler.py` | `_categories`: existence+uniqueness+category-binding (opt `known_refs`) | code |
| B3 | `app/measurement/evidence/gap_blockers.py` | +`standing_floor_ok` membership-count floor | code |
| B3 | `app/measurement/evidence/pack_assembler.py` | defensive floor call over emitted gaps | code |
| B4 | `app/measurement/store/measurement_event_store.py` | `materialize`: self-check stored row's `event_code`, drop illegit revenue (no raise) | code |
| B4 | `app/measurement/dashboard/data_mart.py` | `verified_rows()` +`event_code==ORDER_VERIFIED` | code |
| B4 | `app/measurement/growth/reads.py` | `verified_rows()` +`event_code==ORDER_VERIFIED` (parallel choke) | code |
| — | **new** `tests/test_m6_2l_{a3,a4,b2,b3,b4}_*.py` (5) | CODER leg regressions (§4) | test |

`resolver.py` (A3 + A4) and `pack_assembler.py` (B2 + B3) are each touched by two fixes in **distinct regions**
(A3 adds a field-set; A4 changes `_entry_channels`; B2 changes `_categories`; B3 adds a defensive call) — per-item
rollback is a **scoped partial revert** (§6), not a whole-file byte-revert. **No new migration** (attribution_id
column pre-exists in 0006; ad-hierarchy columns in 0002 — RULE-018), **no new config flag**, **no TESTER smoke
edited**. Migrations stay `0001–0012`.

## 4. Test → leg → smoke mapping (CODER regressions; TESTER authors the official SMK-019..023 in M6-P2103)

| CODER regression (new) | Proves | Leg | Smoke |
|---|---|---|---|
| `tests/test_m6_2l_a3_attribution_id_trace.py` | attribution_id first-class + in handoff payload; id→campaign; deterministic | **1** | SMK-019 |
| `tests/test_m6_2l_a4_ad_hierarchy_intake.py` | track+normalize persist 4 ids; complete-ad FACEBOOK_AD → HIGH via real API; non-string rejected; incomplete-ad+live stays MULTI_TOUCH | **2** | SMK-020 |
| `tests/test_m6_2l_b2_evidence_ref_forgery.py` | fake ref & copy-paste-one-ref ⇒ MISSING/NOT_READY; genuine refs still COMPLETE | **3** | SMK-021 |
| `tests/test_m6_2l_b3_gap_floor_membership.py` | canonical floor OK; duplicate/shadow standing id ⇒ floor FAIL | **4** | SMK-022 |
| `tests/test_m6_2l_b4_verified_lock.py` | materialize self-checks stored event_code (drop, no raise); both verified_rows exclude non-OV ⇒ Rev/ROAS 0 | **5** | SMK-023 |

Legs 6–10 (SMK-019..023 executed OR owner-waived), 11 (all evidence schema-valid), 12 (judge PASS), 13 (rollback
documented — §2/§6) are completed by TESTER (M6-P2103/2104), PM (M6-P2107), JUDGE (M6-P2109). The **official**
smokes `tests/smoke/test_smk_019..023_*.py` are the TESTER's to author + run (RULE-015; I never self-run/self-
certify them).

## 5. Scope & governance boundary

- **In scope (built here)**: exactly the 5 M6-self-doable fixes A3/A4/B2/B3/B4 + their CODER regressions. A4's
  resolver rule is included because leg 2 **mandates** the HIGH outcome and the pack's own smokes (SMK-007 ∧
  SMK-020) uniquely determine the rule — it resolves no OPEN owner decision.
- **Out of scope (owner-gated / cross-module, per M6.2L.md — untouched)**: B1 psid_hash (M6-OD-003); A1/A2
  order_verified wire (M3); A6/B5 event-taxonomy runtime; A5 ads_spend, B6 authN/authZ, B8 DB/HTTP bind
  (M6-OD-011/owner); all C-band + M5 DEBT-1..4; **flipping any flag**.
- **Boundary intact**: measure/record-only — no pricing/order-state/CRM-send/commission/consult/public-reply/
  live-ops. attribution_id + the ad-hierarchy ids are **recorded**, never acted on. `M6-P1000`/`M6-P1309` verdicts
  stay **BLOCKED** and keep appearing in the pack; the G/H/I/J + OD-011/012 forward conditions stay in the
  standing-blocker floor.
- **No self-cert / no Pass-Ready**: B2/B3 strengthen honesty gates; readiness still tops at
  `OWNER_REVIEW_REQUIRED`. No secrets/PII (attribution_id / ad ids are governance/platform ids; correlation/evidence
  ids still masked on export; `psid` still masked).
- **Governance doc-sync (non-blocking, from M6-P2100 sign-off)**: `M6-OD-013`/`M6-OD-014` are fix-decision-ids not
  yet rows in `DECISION_REGISTER.md` — operator/analyst hygiene (00-spec is read-only to me), not a coder blocker.

## 6. Verification plan for M6-P2102 (commands + PASS/FAIL + rollback)

**Commands** (implement runs these; subprocess `pytest`, no cache):
- carry M6.2K → `04-artifacts/impl/M6.2L/` (exclude caches; keep `PLAN.md`); baseline
  `python -m pytest -q -p no:cacheprovider` → record `N passed`, parity with the M6.2K collect **before** any patch.
- apply the 5 fixes + 5 regressions; re-run → green, no skips. Extra targeted guard: re-run
  `test_smk_004_*`/`test_quote_in_funnel_*` (B4) and `test_smk_007_*`/`test_smk_013_*` (A4) to confirm the two
  contested carried areas stay green.
- import smoke; confirm migrations still `0001–0012`; clean `__pycache__`/`.pytest_cache`.

**PASS/FAIL checklist** (per leg): A3 attribution_id first-class + trace ✓/✗ · A4 4-ids persisted + complete-ad→HIGH
via real path + incomplete-ad+live stays MULTI_TOUCH ✓/✗ · B2 fake/copy-paste ⇒ MISSING, genuine ⇒ COMPLETE ✓/✗ ·
B3 duplicate/shadow ⇒ floor FAIL ✓/✗ · B4 materialize drops non-OV revenue + both verified_rows filter ⇒ Rev/ROAS 0
✓/✗ · full suite green (baseline ≤ final) ✓/✗ · the two contested carried smokes (SMK-004, SMK-007) still green ✓/✗
· posture BLOCKED/OFF/OFF unchanged ✓/✗ · no new migration/flag, no TESTER smoke edited ✓/✗.

**Rollback**: staged-only — baseline rollback = delete the `04-artifacts/impl/M6.2L/` tree (M6.2K untouched).
Per-item: revert the named file(s) to M6.2K bytes; for the two shared files (`resolver.py`, `pack_assembler.py`)
the per-item rollback is a **scoped partial revert** of only that fix's region (A3 field-set vs A4 `_entry_channels`;
B2 `_categories` vs B3 defensive call), leaving the co-resident fix intact. The 5 new CODER test files roll back by
**deletion**. No migration to unwind (none added); every change is additive or a fail-closed tightening.

---

*Plan-only: this document writes no application code, adds no migration/flag, sends nothing, scales/publishes
nothing, resolves no owner decision, and flips no flag. `global_gateway_state=BLOCKED`, `production_flag=OFF`. The
5 fixes are proven by regression evidence in M6-P2102+; the runner gate + JUDGE decide (RULE-015).*
