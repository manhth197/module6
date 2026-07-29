# HARMONIZATION_PLAN — MISSING-contract → producer bijection

**Prompt**: M6-P0700 · **Phase**: CONTRACT_HARMONIZATION · **Mode**: plan_only (no schema authored here; this is
the band plan). **Entry gate**: JUDGE M6-P0309 = **SIGNED** (PHASE0 design band accepted), M6-P0700 = RUNNING.
**Anchors**: `[REG CONTRACT_REGISTER]` (26 `M6-CTR` rows), `[REG SCHEMA_CHANGELOG]` (rows 9+ reserved for this
band), the PHASE0 design baselines (`[[DATA_MODEL_BASELINE]]` etc.) as the `[PACK]` field proposals each
producer will formalize. **Feeds**: the 14 harmonization producers M6-P0701..0714.

> **Result: the bijection is complete — 22 MISSING contracts, each mapped to exactly one in-band producer, ZERO
> orphans.** No MISSING contract lacks a producer, so there is **no generation bug** and this plan is **PASS,
> not BLOCKED**. Each producer must preserve doc-named fields verbatim, append a SCHEMA_CHANGELOG row for every
> addition, and reference OPEN owner decisions as parameters — never invent values. `global_gateway_state=
> BLOCKED`, `production_flag=OFF`.

## Sourcing legend

- `[DOC]` — owner doc / extract line. **Only `[DOC]` items are owner requirements.** · `[REG]` — locked
  register. · `[PACK]` — pack convention (owner-review). · `[EXT]` — general practice, proposal only.

---

## 1. The MISSING → producer bijection (22 rows, 0 orphans) `[REG CONTRACT_REGISTER — mechanically parsed]`

Every `MISSING / OWNER_DECISION_REQUIRED` row and its single producing prompt (parsed from the register, not
eyeballed):

| CTR | Object / contract | Producer | Field basis (design) |
|---|---|---|---|
| CTR-003 | `event_registry` (consumed) | **M6-P0701** | consumed shape; `[[DATA_MODEL_BASELINE]]` §1.2 |
| CTR-004 | `web_event_logs` | **M6-P0703** | partial `[DOC L117]`; append-only |
| CTR-005 | `guest_contacts` (consumed) | **M6-P0702** | consumed identity shape |
| CTR-006 | `guest_marketing_consent_snapshot` (consumed) | **M6-P0702** | consent snapshot |
| CTR-007 | `conversion_events` | **M6-P0704** | `[[EVENT_FLOW_DESIGN]]` §2 stage 3 |
| CTR-008 | `marketing_measurement_outbox` | **M6-P0705** | partial `[DOC L252]`; retry/dead-letter |
| CTR-009 | `customer_segments` (consumed) | **M6-P0706** | consumed CRM segment shape |
| CTR-010 | `customer_segment_members` (consumed) | **M6-P0706** | "no owner-trigger" note |
| CTR-011 | `marketing_audience_outbox` | **M6-P0706** | consent fail-closed |
| CTR-012 | `ads_data_quality_check` | **M6-P0708** | `[[DASHBOARD_DESIGN]]` §3; 8 DQ items |
| CTR-013 | `ads_scale_request` | **M6-P0709** | `[[SCALE_LEARNING_DESIGN]]` §2.3 |
| CTR-014 | `ads_learning_candidate` | **M6-P0710** | `[[SCALE_LEARNING_DESIGN]]` §3.3 |
| CTR-016 | `POST /api/ads/events/track` | **M6-P0711** | `[[EVENT_FLOW_DESIGN]]` §2 stage 0 |
| CTR-017 | `POST /api/ads/conversions` | **M6-P0711** | conversions endpoint |
| CTR-018 | `GET /api/admin/ads/dashboard` | **M6-P0712** | read-only; `[[SECURITY_PRIVACY_DESIGN]]` §6.1 |
| CTR-019 | `POST /api/admin/ads/scale-requests` | **M6-P0712** | owner-approval authz |
| CTR-020 | `POST /api/admin/ads/learning-candidates` | **M6-P0712** | review authz |
| CTR-021 | worker `marketing_measurement_dispatcher` | **M6-P0713** | send_policy + hash + dedup |
| CTR-022 | worker `marketing_audience_dispatcher` | **M6-P0713** | consent fail-closed |
| CTR-023 | worker `attribution_materializer` | **M6-P0713** | no verified-revenue overwrite |
| CTR-024 | worker `data_quality_checker` | **M6-P0713** | PASS/HOLD/FAIL output |
| CTR-026 | Scale Gate approval flow | **M6-P0709** | `[[SCALE_LEARNING_DESIGN]]` §2 |

**Mechanical check** `[REG]`: `total_CTR_rows=26 · missing_count=22 · orphan_count=0`. Every MISSING row's
producer matches the register's "Producing prompt" column and is a real prompt in the ledger (M6-P0701..0714,
all present). **No orphan ⇒ no generation bug.**

---

## 2. The 4 DRAFT_LOCKED contracts + their binding prompts `[REG CONTRACT_REGISTER]`

Not MISSING (field schemas already exist), but part of this band's job — bound/parameterized, not produced:

| CTR | Status | Binding prompt | What binds |
|---|---|---|---|
| CTR-001 `ads_measurement_event` | DRAFT_LOCKED (20 fields, SPEC §10.1) | **M6-P0707** | storage binding (physical table) |
| CTR-002 `ads_attribution_context` | DRAFT_LOCKED (19 fields, SPEC §10.2) | — (locked; embeds into CTR-001 storage) | — |
| CTR-015 Dashboard KPI | DRAFT_LOCKED formulas; thresholds OPEN | **M6-P0714** | thresholds (M6-OD-002) |
| CTR-025 Evidence package | DRAFT_LOCKED content (doc §22) | **M6-P0714** | file format (pack HARDENING) |

**So P0707 and P0714 are binding prompts, not schema producers** — that is why they do not appear in §1's
producer column. Every one of the 14 band prompts has a defined job (below); none is idle.

## 3. Producer coverage (each band prompt has a job; no idle producer) `[REG]`

| Producer | Produces / binds |
|---|---|
| M6-P0701 | CTR-003 |
| M6-P0702 | CTR-005, CTR-006 |
| M6-P0703 | CTR-004 |
| M6-P0704 | CTR-007 |
| M6-P0705 | CTR-008 |
| M6-P0706 | CTR-009, CTR-010, CTR-011 |
| M6-P0707 | binds CTR-001 storage |
| M6-P0708 | CTR-012 |
| M6-P0709 | CTR-013, CTR-026 |
| M6-P0710 | CTR-014 |
| M6-P0711 | CTR-016, CTR-017 |
| M6-P0712 | CTR-018, CTR-019, CTR-020 |
| M6-P0713 | CTR-021, CTR-022, CTR-023, CTR-024 |
| M6-P0714 | binds CTR-015 thresholds + CTR-025 format |

**12 producers** cover the 22 MISSING schemas; **2 binding prompts** (P0707, P0714) parameterize DRAFT_LOCKED
contracts. Sum = 14 = the whole band. No producer without a contract; no contract without a producer.

## 4. Harmonization discipline every producer must honor (acceptance requirements) `[REG SCHEMA_CHANGELOG]`

Each M6-P07xx, when it defines its contract(s), MUST:
1. **Preserve doc-named fields verbatim** — where the doc gives partial fields (`web_event_logs` L117:
   page/session/source/consent-snapshot/event_ts/idempotency; `marketing_measurement_outbox` L252:
   error_log/next_retry_at), those exact fields carry through unchanged.
2. **Append a SCHEMA_CHANGELOG row for every addition** `[REG SCHEMA_CHANGELOG]` — new field/enum/state beyond
   the doc gets a row (`# ≥ 9`, dated, `ADDITION`/`CORRECTION`, authorized-by, notes). **An empty diff ("no
   change beyond doc") is itself recorded.** No silent renames, ever.
3. **Reference OPEN owner decisions as parameters, never invent values** — see §6. A schema that needs an OPEN
   decision's value stays parameterized/`BLOCKED` on that decision, per the design baselines.
4. **Consumed shapes** (CTR-003/005/006/009/010) define only the *consumed* shape M6 reads — M6 owns/writes none
   of them `[REG CONTRACT_REGISTER ownership=CONSUMED]`.

## 5. SCHEMA_CHANGELOG state + carried observation `[REG SCHEMA_CHANGELOG]`

- Current rows: **1–8** (DOC_LOCK + audit + readiness changes). Rows **9+** reserved for this band; each
  harmonization prompt appends its own.
- `[PACK]` **Carried observation** (non-blocking, from `[[PHASE0_CONSOLIDATION]]` §6 / M6-P0112): hardening
  pack-rules **M6-RULE-H01/H02/H03** were introduced as label additions under changelog **row 2** ("pack-level
  IDs … labels only") but lack the *dedicated* per-item rows that M6-FAIL-008/009/010 (row 3) and
  M6-SMK-016/017/018 (row 4) received. Asymmetric, non-blocking; recorded for the owner/registry — **not this
  prompt's to fix** (00-spec is read-only to this role). Flagged so a harmonization prompt or the owner may
  normalize the changelog granularity.

## 6. Owner-decision parameters per producer (referenced, never resolved) `[REG DECISION_REGISTER]`

| Producer | OPEN decisions it must reference as parameters |
|---|---|
| P0702 (consent) | PII masking M6-OD-012; consent shape gates M6.2A |
| P0704 (conversion_events) | M6-OD-008 (PAYMENT_COMPLETED non-revenue default) |
| P0708 (dq_check) | M6-OD-002 (threshold-based DQ items) |
| P0709 (scale_request/approval) | M6-OD-002 (thresholds), M6-OD-005 (scale ROAS model), approver-role catalog (owner) |
| P0710 (learning_candidate) | M6-OD-006 (safe range → auto-publish BLOCKED), M6-OD-007 (content → framework), M6-OD-001 (Hero SKU) |
| P0711/0713 (track API / dispatcher) | M6-OD-003 (hash policy / allowed fields → CAPI framework-only) |
| P0712 (admin APIs) | approver-role catalog (owner), M6-OD-002 (dashboard thresholds) |
| P0707 / P0714 (bindings) | M6-OD-011 (storage stack), M6-OD-002 (thresholds), M6-OD-012 (evidence format) |

Entry evidence **M6-ENTRY-001..004** gates the slices these contracts serve (M6.2A onward), fail-closed.

## 7. Verification pass (this prompt gates the whole band; no downstream critic) `[PACK]`

Ledger routes M6-P0700 → M6-P0701 with **no `M6-PC0700`**. The bijection (§1) was established by a **mechanical
parse** of CONTRACT_REGISTER (deterministic: 22 MISSING, 0 orphans) and cross-checked against the ledger (all
14 producers present); an **independent re-derivation** confirmed no orphan, no MISSING row with two producers,
every producer real and in-band, and the reverse coverage (P0707/P0714 correctly the DRAFT_LOCKED binders).
Findings folded above.

## 8. Boundary & safety guards `[BRIEF / REG §18]`

- **Plan-only**: this prompt authors **no schema** — it inventories and maps; the producers author schemas next.
- **No owner value invented**: every OPEN decision stays a parameter (§6); no threshold/model/safe-range/
  hash-field/seed/role resolved here.
- **No raw PII/secrets** — CTR ids and field *names* only, masked/`secret_ref` `[REG RULE-014 / H02]`.
- **Staged**: `global_gateway_state=BLOCKED`, `production_flag=OFF` — unchanged.

## 9. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| The 26 contracts, their MISSING/DRAFT_LOCKED status, producing prompts | `[REG CONTRACT_REGISTER]` — owner-mandated |
| SCHEMA_CHANGELOG discipline (verbatim doc fields; row per addition; no silent rename) | `[REG SCHEMA_CHANGELOG]` — owner-mandated |
| Open owner decisions as parameters | `[REG DECISION_REGISTER]` — owner-mandated (statuses) |
| The bijection map framing; producer-coverage table; per-producer OD parameter mapping; changelog observation | `[PACK]` — owner-review analysis, NOT owner requirements |

*This plan is plan-only: it authors no schema, invents no owner value, maps every MISSING contract to its single
producer (0 orphans → PASS, not BLOCKED), and flips no flag; `global_gateway_state=BLOCKED`,
`production_flag=OFF`.*
