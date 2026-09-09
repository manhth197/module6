# M6.2Q PLAN — Ads-spend import + live-session binding + CPA/ROAS-by-session (A5) (STAGED, plan-only)

**Prompt**: M6-P2501 (`M6_2Q_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code) · **Gate**: EVIDENCE_GATE
**Slice**: M6.2Q — build the M6-side **ads-spend ingest (maker-checker) + live-session-ads-binding.v1 +
CPA/ROAS-by-live_session** so ROAS/CPA compute from real (mock-in-test) ad spend — the *đường-tới-tiền* piece.
Cumulative superset of M6.2P under `04-artifacts/impl/M6.2Q/`. **Everything STAGED** (in-memory stores +
migration-defined tables never applied; mock CSV in tests). No real Meta network / Marketing API, no real spend
data, no new secret, no flag flipped.

> **Posture (immutable, this slice flips nothing):** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
> `external_send=OFF`, `live_migrations=false`; `config.py` unchanged. No self-cert (RULE-015); the runner gate +
> JUDGE (M6-P2509) decide.

Ledger verified: **M6-P2501 = RUNNING** (row 241), dependency **M6-P2500 = SIGNED** (entry gate PASS). Target
**LOCKED**, **M6-OD-011 DECIDED**. In-scope contracts **M6-CTR-015** (Dashboard KPI) + **M6-CTR-002** (attribution)
= DRAFT_LOCKED. Owner inputs **DECIDED + FILED**: **M6-OD-016** (spend source = phase-1 CSV Ads Manager +
maker-checker; no Marketing API/new secret; staged), **M6-OD-011** (binding direction: reuse live_session_id +
primary_campaign_id), **M6-OD-015** (psid-no-join, supports binding-by-live_session_id).

## 0. Top-0.1% lens + owner authorization + forward conditions (verified on real code + the decision record)

A 4-reader understand-sweep over the real M6.2P code grounded this plan; the lens changed three load-bearing calls:

- **[the by-session KPI must NOT touch two PINNED surfaces]** `DataMart`'s public method set is pinned by
  `tests/test_data_mart_support_view_only.py:11-14` **and** the TESTER-owned smoke
  `tests/smoke/test_smk_010_data_mart_support_view_only.py:21-24` (an exact allow-set of 11 read methods);
  `kpi_metrics.compute_metrics` is pinned to **exactly 14** verbatim metrics by `test_kpi_formulas_verbatim.py:11-32`.
  → the CPA/ROAS-by-session reader is a **NEW standalone module** (mirroring `funnel.assemble`), **not** a new
  `DataMart` method and **not** a 15th metric — so both pinned tests stay green (RULE-012/SMK-010 intact).
- **[maker≠checker is genuinely NEW — no precedent enforces it]** the scale approval flow records **no proposer
  identity** (`scale/models.py:59-74` `AdsScaleRequest` has none; `OwnerDecision.actor` is the approver only) and
  its "no self-approve" is only RULE-015 (no auto-approve method). → the ads-spend import must carry a new
  `uploaded_by` (maker) field and the approve path a new fail-closed guard `decision.actor != uploaded_by` (self-
  approve / single-actor **rejected**). This is the security-load-bearing control SMK-029 tests.
- **[`AdsSpendRecord` is time-less — the load-bearing data gap]** `data_mart.py:22-34` `AdsSpendRecord` has
  amount + campaign/adset/ad only, **no time** → cutting spend to a session start/end window is impossible without a
  `spend_date`. → add `spend_date: Optional[datetime] = None` (additive; positional constructors unchanged).
- **[adversarial red-team fix — MAJOR]** a 2-dimension plan red-team (skeptics prototyping against the real M6.2P
  code) caught that gating the by-session spend sum on `AdsSpendRecord.mapped` (which requires campaign **+ adset +
  ad**, `data_mart.py:32-34`) would drop **every** campaign-level import row (M6-OD-016 spend is campaign-only → a
  materialized record has `adset_id=None, ad_id=None` → `.mapped=False`) → CPA/ROAS always None, the whole
  đường-tới-tiền deliverable dead. → leg 3 gates inclusion on the **campaign-binding** (`session_for_campaign`) +
  `spend_date ∈ window`, **NOT** the 3-id `.mapped` predicate (§2 leg 3). The review also confirmed **CLEAN**: the
  maker-checker guard is airtight + genuinely new; the pinned `DataMart` allow-set + the 14-metric test stay green
  (the reader is a separate module); and the `_safe_div` fail-closed math is correct.

**Forward conditions (recorded, NOT blockers):** **M6-OD-002** (Scale-Gate/alert thresholds) + **M6-OD-005**
(scale-authoritative attribution model) stay OPEN — they govern *forward scale decisions*, not the deterministic
spend→session binding or the CPA/ROAS numbers this slice computes; the exit judge M6-P2509 confirms no flag flip,
no real spend/Meta network, and posture OFF/BLOCKED/OFF. **M6-OD-011 server-bind + go-live** remain hard gates
before any real spend/egress.

## 1. Repo summary & staging model (cumulative carry-forward)

- **Base**: the whole **M6.2P** tree (app + 13 migrations `0001–0013` + the full carried suite). M6.2Q is a
  **superset**: carry M6.2P byte-identical, add the A5 modules/migrations + CODER regressions. (The carry runs in
  **M6-P2502 implement**, not this plan.)
- **Stack** (locked target): Python 3.12, `framework=""` (framework-neutral pure functions), `pytest -q`, stdlib
  only; in-memory staged stores; engine-neutral migration DDL never applied (`live_migrations=false`).
- **Layers touched** (ARCH_BASELINE): **Outbox/Gate** (new ads-spend import + maker-checker + materialize worker),
  **Attribution** (primary_campaign_id + binding.v1), **Dashboard** (CPA/ROAS-by-session reader). No Core
  event/policy invented (RULE-018 — the tables are M6-owned measurement/attribution stores, owner-decided shapes).
- **Baseline discipline (M6-P2502)**: verify green **before** any patch (subprocess `pytest`, parity with the M6.2P
  collect), then green again after; **no skips**; actual `N passed` is the count.

## 2. The 3 fixes — each mapped to an exit-gate leg + SMK-029 (minimal change, rollback per item)

Legend: **Leg** = M6.2Q.md "Exit gate checks" number · **Smoke** = SMK-029 · file:anchor are M6.2P-current.

### LEG 1 — ads_spend_import + maker-checker + materialize worker (M6-OD-016) → **SMK-029 · RULE-015 · FAIL-007**

*Reuses the scale approval precedent (`scale_gate.py:41-115`, `scale_request_store.py:19-51`) + a drain-loop worker
(`outbox/measurement_dispatcher.py:53-74`) + a set-once destination store (`measurement_event_store.materialize`
`:79-136`).*

| File : anchor | Change | Rollback (staged) |
|---|---|---|
| **new** `app/measurement/models/ads_spend_import.py` | `AdsSpendImportState(str,Enum){PROPOSED,APPROVED,REJECTED}`; frozen `AdsSpendImportRow{campaign_id, spend_value, currency, spend_date}` (one mock-CSV row); frozen `AdsSpendImport{import_id, rows, window_start, window_end, uploaded_by (maker), state, decided_by?, created_at, decided_at?}` + `to_public()` (actors masked, RULE-014; machine-safe) | delete the file |
| **new** `app/measurement/store/ads_spend_import_store.py` | frozen-row store: `create` raises on dup id, `update_state` raises on unknown, append-only `history`, `get`/`all` (copy `scale_request_store.py:19-51`; fail-loud) | delete the file |
| **new** `app/measurement/ads_spend/import_gate.py` | `AdsSpendImportGateViolation`; `propose(import_)`→PROPOSED+audit; `record_decision(import_id, actor, reason, audit_ref, evidence_ref, decision)` — **fail-closed `if actor == import_.uploaded_by: raise Violation("self-approve rejected: uploader != approver")`** + reject single-actor/missing checker BEFORE recording APPROVED; `replace()`→APPROVED/REJECTED; machine-safe audit (no owner free-text in detail, mirror `scale_gate._audit_decision:146-156`) | delete the file |
| **new** `app/measurement/ads_spend/materializer.py` | `run_once()` drain: select **APPROVED-and-not-yet-materialized** imports → write each row set-once into the record store; non-APPROVED skipped; audit `ADS_SPEND_IMPORT_MATERIALIZED` | delete the file |
| **new** `app/measurement/store/ads_spend_record_store.py` | set-once store for materialized `AdsSpendRecord` rows (keyed by import_id); refuse a second/altered materialize (loud `Violation`), forbid update/delete | delete the file |
| **new** `app/api/ads_spend_imports.py` | framework-neutral handlers `handle_import_create` / `handle_import_decision` / `handle_import_materialize` on the `api/scale_requests.py:49-111` template — Deps hold ONLY store+gate+worker+audit, **NO Meta/network/connector**; require all owner-decision fields → `OWNER_DECISION_INCOMPLETE`; `Violation`→`APPROVAL_REFUSED` | delete the file |
| **new** `migrations/0014_create_ads_spend_import.sql` + `0015_create_ads_spend_record.sql` | STAGED DDL (copy the `0009/0010` inert header + enum CHECK + append-only + FK + commented DOWN); import table carries `uploaded_by`/`decided_by`/`state`; **maker≠checker documented as app-enforced** (not a single-column CHECK); records table = materialized spend | delete the files |

- **CODER regression** `tests/test_m6_2q_ads_spend_import_maker_checker.py`: an import enters PROPOSED; a **DISTINCT**
  checker → APPROVED; a **self-approve** (`actor == uploaded_by`) → `Violation` (rejected); a single-actor/missing
  checker → rejected; the worker materializes **only** APPROVED imports (a PROPOSED/REJECTED import materializes
  nothing); a second materialize of the same import is a no-op/loud refuse; the approve/reject/materialize audit
  carries no raw PII (scan the blob, mirror `test_scale_request_lifecycle.py:62-79`).

### LEG 2 — live-session-ads-binding.v1 + primary_campaign_id → **SMK-029 · RULE-015**

| File : anchor | Change | Rollback (staged) |
|---|---|---|
| `app/measurement/models/attribution_context.py` | add `primary_campaign_id: Optional[str] = None` (:67, after `campaign_id`) + emit it in `to_public()` dict literal (:~106) so `as_stored()` (:133) carries it; docstring | revert the added field + to_public line to M6.2P bytes |
| `app/measurement/attribution/resolver.py` | in `resolve_ads_context` set `primary_campaign_id = getattr(event,"campaign_id",None) or signals.get("primary_campaign_id")` (deterministic, pure) + pass it to the `AdsAttributionContext(...)` call (:142). **NOT wired into `.complete`/`_grade`** (A4/SMK-020/006/007 unaffected) | revert the 2 lines |
| **new** `app/measurement/models/live_session_ads_binding.py` | frozen `LiveSessionAdsBinding{live_session_id, primary_campaign_id, adset_id?, ad_id?, bound_at, bound_by}` + `to_public()`/`as_stored()`; `bound_by` = actor/governance ref (not PII) | delete the file |
| **new** `app/measurement/store/live_session_ads_binding_store.py` | in-memory store keyed by `live_session_id` + reverse index by `primary_campaign_id`; `session_for_campaign(campaign_id)->live_session_id|None` (the spend→session join hook); bound-once (set-once precedent) | delete the file |
| **new** `migrations/0016_create_live_session_ads_binding.sql` | STAGED DDL (0006 style): binding table + `UNIQUE(live_session_id, primary_campaign_id)` + `ix` on primary_campaign_id | delete the file |

- **CODER regression** `tests/test_m6_2q_binding_primary_campaign.py`: `primary_campaign_id` is a first-class field,
  in `to_public()`/`as_stored()`, **deterministic** (a re-materialize of the same row is a no-op — the set-once
  idempotency guard `measurement_event_store.py:119` holds); it is **NOT** in `.complete` (a complete FACEBOOK_AD
  path still grades HIGH — SMK-020 unaffected; an incomplete-ad+live still MULTI_TOUCH — SMK-007); the binding
  maps `campaign_id → live_session_id` via `session_for_campaign`.

### LEG 3 — CPA/ROAS-by-live_session (M6-CTR-015; RULE-003 lock) → **SMK-029 · RULE-003 · FAIL-007**

| File : anchor | Change | Rollback (staged) |
|---|---|---|
| `app/measurement/dashboard/data_mart.py` | add `spend_date: Optional[datetime] = None` to `AdsSpendRecord` (:22-34) — the session-window cut key; additive (positional constructors + `mapped` unchanged; `test_smk_006` `AdsSpendRecord(amt,c,a,ad)` still valid → `spend_date=None`). **No new `DataMart` method** (pinned allow-set) | revert the field |
| **new** `app/measurement/dashboard/session_roas.py` | standalone reader (mirrors `funnel.assemble`), NOT a `DataMart` method + NOT a `compute_metrics` metric: `SessionCpaRoas{live_session_id, session_spend, verified_orders, verified_revenue, cpa, roas}`; `by_session()` groups measurement rows by session (funnel `_session_key`), derives the window `[min,max event_ts]`, sums **APPROVED** spend records whose `campaign_id` is **bound to the session** (via `session_for_campaign`) **and** `spend_date ∈ window` — the spend source is **campaign-level** (M6-OD-016), so inclusion gates on the **campaign-binding**, **NOT** the 3-id `AdsSpendRecord.mapped` predicate (a campaign-only record has `adset_id=None`/`ad_id=None` and would be wrongly dropped by `.mapped`); then `CPA=_safe_div(session_spend, verified_order_count)`, `ROAS=_safe_div(session_verified_revenue, session_spend)`; a `daily_total()` bucket for spend **outside** any session window **or on an unbound campaign**. Verified revenue/orders via `verified_rows()` (ORDER_VERIFIED + revenue_value, RULE-003) — a quote/draft in-window contributes 0 | delete the file |

- **Fail-closed matrix (verified against `_safe_div`)**: a session with **spend + zero verified orders** →
  `CPA=None` (den 0) and `ROAS=0.0` (`_verified_revenue`=0.0 / spend>0 — the wasted-spend case); **no bound spend**
  → `session_spend=None` → `CPA=None` (no CPA number) and `ROAS=None` (a genuine 0/0, fail-closed, no fabricated 0).
  A spend record whose `campaign_id` is **unbound / None** is excluded from the session (it falls to
  `daily_total()`), never fabricated. No divide-by-zero. *(Coordination: SMK-029's "no verified order → ROAS=0" is
  satisfiable only with spend>0; the TESTER's SMK-029 fixture for that case must carry spend, matching the leg-3
  regression's spend-with-zero-verified row.)*
- **CODER regression** `tests/test_m6_2q_cpa_roas_by_session.py`: a **campaign-level** approved spend record **bound**
  to a session (via `session_for_campaign`) with `spend_date ∈ window` **is included** (CPA/ROAS non-None) — i.e. the
  sum gates on the binding, **not** `.mapped`; per-session CPA = approved-spend / verified-order-count + ROAS =
  verified-revenue / spend; spend **outside** the window or on an **unbound** campaign → `daily_total()` (not
  session-attributed); a spend-with-zero-verified session → CPA None / ROAS 0.0; **no bound spend** → CPA None /
  ROAS None; a quote in the window contributes 0 (RULE-003); reading writes nothing to the store (SMK-010 purity).

### LEGS 4–7 (other roles)

4 SMK-029 executed-or-waived (**TESTER** M6-P2503/2504). 5 all evidence schema-valid. 6 judge PASS (M6-P2509).
7 rollback documented (this §2 + §4). The coder legs never self-run/self-certify the smoke (RULE-015).

## 3. Backward-compat & the pinned surfaces (verified on real code)

- **`DataMart` allow-set untouched** — the by-session reader is `dashboard/session_roas.py`, not a `DataMart`
  method → `test_data_mart_support_view_only.py` + the TESTER `test_smk_010_*` allow-sets stay exact (RULE-012).
- **14-metric `compute_metrics` untouched** — CPA/ROAS-by-session is a separate collection → `test_kpi_formulas_
  verbatim.py` (len==14, verbatim) stays green.
- **`primary_campaign_id` additive** — no test enumerates the attribution to_public key-set; it is NOT in
  `.complete`/`_grade` → A4/SMK-020/SMK-006/SMK-007/A3-attribution_id all unaffected; deterministic → re-materialize
  idempotency (`test_m6_2l_a3` determinism) holds.
- **`AdsSpendRecord.spend_date` additive** — positional `AdsSpendRecord(amt,campaign,adset,ad)` still valid
  (`test_smk_006`) → `spend_date=None`; the existing `ConsumedFacts.ads_spend` daily aggregate is untouched.
- **Maker-checker is net-new behaviour** with no carried test to break (the scale "no self-approve" is a different,
  RULE-015 assertion). The new ads-spend gate/worker/store/API add files; they patch no carried behaviour.

## 4. Rules / fail gates, scope & governance

- **RULE-003** (verified-only revenue): CPA/ROAS use `verified_rows()` (ORDER_VERIFIED + revenue_value) — a
  quote/draft never enters the numerator/denominator; a spend-with-zero-verified session fails closed.
- **RULE-015** (no self-cert) + **FAIL-007**: proven by the SMK-029 regressions; the maker-checker rejects
  self-approve; nothing is called PASS without evidence.
- **In scope**: the 3 legs above. **Out of scope (untouched)**: real CSV source / Meta network / Marketing API
  (phase 2); real spend data + external send; `board_id`/`segment_id` (C1, M7); DB/HTTP server-bind (B9 /
  M6-OD-011). No flag flip; `production_flag`/`global_gateway_state`/`external_send` stay OFF/BLOCKED/OFF.
- **Boundary intact**: measure/record-only — no pricing/order-state/CRM-send/**commission** (the binding/attribution
  side has no commission field, RULE-019); ad spend is **campaign-level (campaign_id), not user PII**; `uploaded_by`/
  `bound_by` are actor/governance refs (masked on export), never raw PII; no new secret (M6-OD-016). `M6-P1000`/
  `M6-P1309` stay BLOCKED.

## 5. Verification plan for M6-P2502 (commands + PASS/FAIL + rollback)

**Commands** (`PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider`): carry M6.2P → `impl/M6.2Q/`
(exclude caches; keep this `PLAN.md`), baseline green + parity **before** any patch; add the leg-1/2/3 modules +
migrations 0014–0016 + the 3 regressions; re-run green (no skips); confirm `config.py` unchanged, migrations
`0001–0016`, no new flag/secret, clean caches, PII scan.

**PASS/FAIL checklist**: maker-checker self-approve rejected + only APPROVED materializes ✓/✗ · binding maps
campaign→session + primary_campaign_id additive/deterministic/not-in-.complete ✓/✗ · CPA=spend/orders,
ROAS=rev/spend from approved spend; spend outside window → daily total; zero-verified → CPA None/ROAS 0.0; no spend
→ CPA None (RULE-003) ✓/✗ · pinned `DataMart` allow-set + 14-metric tests still green ✓/✗ · full suite green
(baseline ≤ final) ✓/✗ · posture + no flag/secret ✓/✗.

**Rollback**: staged only — delete the `04-artifacts/impl/M6.2Q/` tree (M6.2P untouched). Per item: §2 tables (new
files → delete; the 3 edited carried files — `attribution_context.py`, `resolver.py`, `data_mart.py` — → scoped
revert to M6.2P bytes). No live migration to unwind (`live_migrations=false`). Every change is additive or a
fail-closed control; a revert restores prior behaviour.

---

*Plan-only: this document writes no application code, applies no migration, opens no egress, resolves no owner
decision, and flips no flag. It plans an owner-authorized (M6-OD-016/011/015), STAGED, mock-CSV ads-spend path.
`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`. The runner gate + JUDGE decide (RULE-015).*
