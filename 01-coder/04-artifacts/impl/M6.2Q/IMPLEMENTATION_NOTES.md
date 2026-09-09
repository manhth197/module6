# M6.2Q IMPLEMENTATION_NOTES — Ads-spend import + live-session binding + CPA/ROAS-by-session (A5) (STAGED)

**Prompt**: M6-P2502 (`M6_2Q_CODER_IMPLEMENT`) · **Role**: CODER · **Mode**: `implement` · **Gate**: EVIDENCE_GATE
**Slice**: M6.2Q (A5) — the M6-side **ads-spend ingest (maker-checker) + live-session-ads-binding.v1 +
CPA/ROAS-by-live_session**, so ROAS/CPA compute from real (mock-in-test) ad spend. Cumulative superset of M6.2P.
**Everything STAGED** (in-memory stores + migration-defined tables never applied; mock CSV in tests). No real Meta
network / Marketing API, no real spend data, no new secret, no flag flipped.

> **Posture (immutable, this slice flips nothing):** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
> `external_send=OFF`, `live_migrations=false`. `app/config.py` **unchanged** (sha256[:16] = `911b32381368f355`,
> byte-identical to M6.2P). No self-cert (RULE-015); the runner gate + JUDGE (M6-P2509) decide.

Ledger verified before acting: **M6-P2502 = RUNNING** (row 242), dependency **M6-P2501 = PASS** (row 241). Target
**LOCKED** (`live_migrations=false`; M6-OD-011 DECIDED). Built to the approved `PLAN.md` item-by-item.

## 1. Carry-forward + baseline discipline

- Carried the whole **M6.2P** tree byte-identical into `04-artifacts/impl/M6.2Q/` (excluded `__pycache__` /
  `.pytest_cache` / `*.pyc` + the prior `PLAN.md` / `IMPLEMENTATION_NOTES.md`; kept this slice's `PLAN.md`). Result:
  **230 .py = 230 .py**, **13 .sql = 13 .sql** identical.
- **Baseline + parity BEFORE any patch**: `PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider -q` →
  **M6.2P 603 passed / M6.2Q carried 603 passed** (0 fail/error/skip), identical → clean byte-identical carry.
- **After the build**: full suite **626 passed, 0 fail / 0 error / 0 skip** (603 baseline + 23 new: 18 leg
  regressions + 5 red-team alias cases). No test was skipped, relaxed, or deleted.

## 2. What was built — 3 legs (each mapped to an M6.2Q exit-gate leg + SMK-029)

### LEG 1 — ads_spend_import + maker-checker + materialize worker (M6-OD-016) → SMK-029 · RULE-015 · FAIL-007

| File | What |
|---|---|
| **new** `app/measurement/models/ads_spend_import.py` | `AdsSpendImportState{PROPOSED,APPROVED,REJECTED}`, `ImportDecisionKind{APPROVE,REJECT}`; frozen `AdsSpendImportRow{campaign_id, spend_value, spend_date, currency}`, `AdsSpendImportDecision{actor,reason,audit_ref,evidence_ref,decision,at}`, `AdsSpendImport{import_id, rows, window_start/end, uploaded_by (maker), state, decision, decided_by (checker), created_at, decided_at}`; `to_public()` masks actors (RULE-014) |
| **new** `app/measurement/store/ads_spend_import_store.py` | inert store (create dup-guard, update_state unknown-guard, append-only `history`) — mirrors `ScaleRequestStore` |
| **new** `app/measurement/ads_spend/import_gate.py` | `propose()` (PROPOSED + audit); `record_decision()` — **four-eyes fail-closed**: an APPROVE is REFUSED when the (canonicalized) checker equals the maker, or the checker is blank; machine-safe audit (checker free-text never echoed; actor masked) |
| **new** `app/measurement/ads_spend/materializer.py` | `run_once()` drain: materializes **only APPROVED-and-not-yet-materialized** imports into set-once campaign-level records (adset_id/ad_id None); PROPOSED/REJECTED → nothing; idempotent |
| **new** `app/measurement/store/ads_spend_record_store.py` | set-once record store keyed by import_id (identical re-materialize = no-op; altered = loud refuse; no update/delete) |
| **new** `app/api/ads_spend_imports.py` | `handle_import_create` / `_decision` / `_materialize`; `AdsSpendImportDeps` holds ONLY gate+worker+audit — **no Meta/Marketing-API/network**; missing decision fields → `OWNER_DECISION_INCOMPLETE`; gate refusal → `APPROVAL_REFUSED` |
| **new** `migrations/0014_create_ads_spend_import.sql` + `0015_create_ads_spend_record.sql` | STAGED DDL; 0014 = import header + `ads_spend_import_row` child (mock CSV rows); 0015 = materialized records; maker≠checker documented as **app-enforced** |

**Regression** `tests/test_m6_2q_ads_spend_import_maker_checker.py` (12 cases): PROPOSED→distinct-checker APPROVED;
self-approve / alias-self-approve / missing checker rejected; only APPROVED materializes; second materialize no-op;
re-decide refused; API create/decide/materialize; **no raw PII in the audit trail**.

### LEG 2 — live-session-ads-binding.v1 + primary_campaign_id (M6-OD-011) → SMK-029 · RULE-015

| File | What |
|---|---|
| `app/measurement/models/attribution_context.py` | **+`primary_campaign_id: Optional[str] = None`** (after `campaign_id`) + emitted in `to_public()` (so `as_stored()` carries it). Additive; **NOT** wired into `.complete`/`_grade` |
| `app/measurement/attribution/resolver.py` | set `primary_campaign_id = getattr(event,"campaign_id",None) or signals.get("primary_campaign_id")` (deterministic, pure) + pass to the `AdsAttributionContext(...)` call; **not** fed into grading |
| **new** `app/measurement/models/live_session_ads_binding.py` | frozen `LiveSessionAdsBinding{live_session_id, primary_campaign_id, adset_id?, ad_id?, bound_at, bound_by}` + `to_public()`/`as_stored()` (bound_by masked) |
| **new** `app/measurement/store/live_session_ads_binding_store.py` | keyed by live_session_id + reverse index; `session_for_campaign(campaign_id)->live_session_id|None`; set-once + campaign-unambiguous |
| **new** `migrations/0016_create_live_session_ads_binding.sql` | STAGED DDL + `UNIQUE(live_session_id, primary_campaign_id)` + ix on primary_campaign_id |

**Regression** `tests/test_m6_2q_binding_primary_campaign.py` (6 cases): primary_campaign_id first-class + in
to_public/as_stored + deterministic on replay; **NOT** in grading (complete FACEBOOK_AD still HIGH — SMK-020;
incomplete-ad+live still MULTI_TOUCH — SMK-007); binding maps campaign→session; set-once + unambiguous.

### LEG 3 — CPA/ROAS-by-live_session (M6-CTR-015; RULE-003 lock) → SMK-029 · RULE-003 · FAIL-007

| File | What |
|---|---|
| `app/measurement/dashboard/data_mart.py` | **+`spend_date: Optional[datetime] = None`** on `AdsSpendRecord` (additive; positional ctor + `mapped` unchanged) + `datetime` import. **No new DataMart method** |
| **new** `app/measurement/dashboard/session_roas.py` | standalone `SessionRoasReader` (NOT a DataMart method, NOT a 15th metric): per session, `CPA=_safe_div(spend, verified_orders)`, `ROAS=_safe_div(verified_revenue, spend)`; spend included **iff** its campaign is bound to the session (`session_for_campaign`) **and** `spend_date ∈ [min,max event_ts]` — gates on the **campaign-binding, NOT `.mapped`**; `daily_total()` for out-of-window / unbound spend; verified via ORDER_VERIFIED + set-once revenue (RULE-003) |

**Regression** `tests/test_m6_2q_cpa_roas_by_session.py` (5 cases): a **campaign-level** (`.mapped is False`) bound
in-window record **is included** (CPA/ROAS non-None) — proves the gate is the binding, not `.mapped`; CPA=spend/2,
ROAS=rev/spend; zero-verified → CPA None / ROAS 0.0; no bound spend → CPA None / ROAS None; out-of-window + unbound
→ `daily_total()`; reading writes nothing (SMK-010 purity).

## 3. Plan deltas (documented per the prompt)

1. **Four-eyes distinctness is CANONICALIZED (strip + casefold), not raw `==`** — a hardening beyond the plan's
   literal `decision.actor != uploaded_by`. **Why**: the ultracode adversarial red-team (independent skeptic that
   reproduced it on the running code) found that a raw `==` let a case/whitespace variant of the maker's own ref
   self-approve (e.g. maker `maker_ops`, checker `Maker_Ops` / `maker_ops ` / ` ` → APPROVED + materialized). A
   latent segregation-of-duties gap today (staged actors are unauthenticated free text) that would become live the
   moment M6-OD-011 binds a real case/variant identity. **Fix** (`import_gate.py` `_canon_actor`): compare
   `strip().casefold()` refs and refuse a blank/whitespace-only checker (the recorded raw `decided_by` is
   unchanged). Added a parametrized regression (5 alias/whitespace cases → refused). This strengthens the control;
   it relaxes nothing.
2. **Migration 0014 adds a child `ads_spend_import_row` table** for the mock-CSV rows (the plan named the import
   header + records table). A completeness addition — engine-neutral, staged, never applied.

The other 2 red-team dimensions (CPA/ROAS math + fail-closed; backward-compat + boundary) returned **CLEAN**
(no findings) after prototyping against the real code.

## 4. Backward-compat & the pinned surfaces (verified green, not asserted)

- **DataMart allow-set** (`test_data_mart_support_view_only.py` + TESTER `test_smk_010_*`) and the **14-metric
  verbatim** test (`test_kpi_formulas_verbatim.py`) stay exactly green — the by-session reader is a separate module,
  not a DataMart method and not a 15th metric. `AdsSpendRecord.spend_date` is additive (SMK-006 positional ctor
  still valid). Explicitly re-ran these + SMK-006/007 → all pass.
- `primary_campaign_id` is additive + not in `.complete`/`_grade` → A4 / SMK-020 / SMK-006 / SMK-007 / A3
  attribution_id determinism all unaffected (deterministic → replay idempotent).

## 5. Rollback (staged only — M6.2P untouched)

- **Whole slice**: delete the `04-artifacts/impl/M6.2Q/` tree. M6.2P is byte-identical and untouched; no live
  migration to unwind (`live_migrations=false`).
- **Per item**: new files (leg-1 ads_spend + stores + gate + worker + API; leg-2 binding model/store; leg-3
  `session_roas.py`; migrations 0014–0016; the 3 regression files) → delete. The 3 edited carried files
  (`attribution_context.py`, `resolver.py`, `data_mart.py`) → scoped revert of the additive field/line to M6.2P
  bytes. `import_gate.py` four-eyes canon → revert to the plain-`==` form (the plan's literal). Every change is
  additive or a fail-closed control; a revert restores prior behaviour.

## 6. Scope, boundary & governance

- **In scope**: the 3 legs above. **Out of scope (untouched)**: real CSV source / Meta network / Marketing API
  (phase 2 go-live); real spend data + external send; `board_id`/`segment_id` (C1/M7); DB/HTTP server-bind (B9 /
  M6-OD-011). No flag flip; `production_flag`/`global_gateway_state`/`external_send` stay OFF/BLOCKED/OFF.
- **Boundary intact**: measure/record only — no pricing / order-state / CRM-send / **commission** (RULE-019: the
  binding + spend side carries no commission field); ad spend is **campaign-level (campaign_id), not user PII**;
  `uploaded_by`/`decided_by`/`bound_by` are actor/governance refs masked on export, never raw PII; no new secret
  (M6-OD-016). `M6-P1000` / `M6-P1309` stay BLOCKED.
- **Forward conditions (recorded, not resolved here)**: M6-OD-002 (thresholds) + M6-OD-005 (scale-authoritative
  attribution model) OPEN govern forward scale decisions, not this slice's numbers; M6-OD-011 server-bind + go-live
  remain hard gates before any real spend / egress.

## 7. Verification commands

```
# carry (excludes caches + prior PLAN/NOTES); baseline + parity BEFORE patch:
PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider -q     # M6.2P 603 == M6.2Q 603
# after build + red-team fix:
PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider -q     # 626 passed, 0 fail/error/skip
# pinned surfaces (explicit): test_data_mart_support_view_only + test_kpi_formulas_verbatim + test_smk_010_*(x2) + smk_006/007  -> all pass
# posture: app/config.py sha256[:16] == 911b32381368f355 (unchanged); migrations 0001..0016 contiguous
```

*Implemented an owner-authorized (M6-OD-016 / M6-OD-011 / M6-OD-015), STAGED, mock-CSV ads-spend path. No
application flag flipped, no migration applied, no egress opened, no owner decision resolved. The runner gate +
JUDGE decide (RULE-015).*
