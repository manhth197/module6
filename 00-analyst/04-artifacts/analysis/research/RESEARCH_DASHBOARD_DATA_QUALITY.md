# RESEARCH_DASHBOARD_DATA_QUALITY — evidence-first dashboard + DQ propagation

**Prompt**: M6-P0207 · **Phase**: PHASE0_RESEARCH · **Mode**: analysis_only (desk research; design proposal)
**Anchors**: `[DOC §15 extract line 308]` Dashboard DQ gate; 14 locked KPI formulas `[DOC §14 lines 282–295 /
REG MONITORING_REGISTER]`; `M6-CTR-015` Dashboard KPI (DRAFT_LOCKED formulas, thresholds M6-OD-002),
`M6-CTR-012 ads_data_quality_check` (→M6-P0708), `M6-CTR-018 GET /api/admin/ads/dashboard` (→M6-P0712),
`M6-CTR-024 data_quality_checker` worker (→M6-P0713); reads `M6-CTR-001 ads_measurement_events` (DRAFT_LOCKED).
Slice **M6.2F** (done gate: *"Dashboard shows verified-only revenue"*).
**Critic**: M6-PC0207 (BOUNDARY_ADVERSARY) red-teams this file next.

> The dashboard is **read-only measurement**. It flips no gate, triggers nothing, and shows revenue only from
> `ORDER_VERIFIED`. `global_gateway_state=BLOCKED`, `production_flag=OFF` unchanged.

## Sourcing legend (acceptance: every externally-sourced claim labeled)

- `[DOC]` — owner document / extract line. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked pack register. · `[BRIEF]` — context brief. · `[PACK]` — pack convention (owner-review).
- `[EXT]` — general engineering practice, **proposal only**.

**Doc/reg anchors**: `[DOC §15 L308]` *"Dashboard | Metric có sample evidence và trace | Dashboard chỉ là
visual không có source trace"* (PASS needs sample-evidence + trace; a visual-only dashboard is FAIL/HOLD);
`[DOC §14 L282–295]` the 14 KPI formulas (verbatim, MONITORING_REGISTER); `[REG RULE-003]` revenue/ROAS from
Verified Revenue only; `[REG RULE-012]` Data Mart is a **support view only**, never a trigger owner; `[REG
RULE-015]` nothing is PASS without audit/evidence/trace; `[REG FAIL-001]` revenue misuse; `[REG FAIL-005]` Data
Mart abuse. `ads_measurement_event.data_quality_status: PASS|HOLD|FAIL` `[REG SPEC §10.1]`.

---

## 1. The requirement: **evidence-first, not visual-only** `[DOC §15 L308]`

The doc's Dashboard DQ gate makes a **visual with no source trace a FAIL** (`"Dashboard chỉ là visual không có
source trace"`). Therefore every displayed number must be **drillable to the rows that produced it**. A chart
that cannot show its underlying `ads_measurement_events` / verified orders is not a feature — it is a gate
failure. This is the concrete form of `[REG RULE-015]` (nothing PASS without evidence/trace) for the dashboard.

---

## 2. Semantic layer over `ads_measurement_events` `[EXT]` (formula-driven, support-view-only)

`[EXT] proposal:` a **semantic layer** defines each of the 14 metrics as a **deterministic derivation** over
`ads_measurement_events` (+ the Verified Revenue and Ads Spend sources), using the **locked §14 formulas as the
single definition** (e.g. `ROAS = Revenue Verified / Ads Spend` `[DOC L284]`; `Revenue Verified =
SUM(verified_revenue)` restricted to `ORDER_VERIFIED` `[DOC L283]`).

- One metric = one formula = one query = one trace. **No ad-hoc SQL** producing an untraceable visual (that is
  the §L308 FAIL). `[PACK]`
- **Revenue metrics restricted to `ORDER_VERIFIED` / Verified Revenue** `[REG RULE-003]`; a quote/order-draft
  shown as revenue is `[REG FAIL-001]` and fails the M6.2F done gate.
- Reads a **support view / materialized view** `[DOC CTR-018 "Chỉ đọc data mart/support view"]`; the **Data
  Mart is never a trigger owner** for CRM/pricing/Diamond/scale `[REG RULE-012 / FAIL-005]` — dashboard reads,
  it does not drive.
- Whether the layer is materialized (precomputed views) or query-time depends on the target repo/stack
  (M6-OD-011) — an implementation choice, not an owner requirement.

---

## 3. Sample-evidence per metric `[DOC §15 L308 / REG RULE-015]`

Each metric carries, at query time, an **evidence bundle** so the number is auditable `[EXT] shape`:

`{ metric, formula (verbatim §14), value, source_query_ref, sample_rows (N example ads_measurement_events /
verified orders, PII-masked), row_count, data_quality_status, computed_at }`

- The **sample_rows** let a reviewer confirm the value against real events (the "sample evidence") — masked for
  PII `[REG RULE-014, BRIEF rule 4]`.
- `source_query_ref` + `formula` are the **trace** (which rows, which formula).
- This bundle is what the M6.2F evidence pack and the P0 smokes assert against; a metric without it is
  HOLD/FAIL `[DOC L308]`. Sample size / retention is a `[PACK]` config (owner/ops review).

---

## 4. PASS/HOLD/FAIL propagation from `ads_data_quality_check` `[DOC §15 / REG CTR-012]`

The `data_quality_checker` worker (CTR-024) evaluates the 8 §15 gate items (Event Registry, Consent, Dedup,
Identity, Attribution, Verified Revenue, Suppression, Dashboard — `[DOC §15 L301–308]`) and writes
`ads_data_quality_check` (CTR-012) verdicts. These must **propagate visibly** to the dashboard:

- Each `ads_measurement_event` carries `data_quality_status: PASS|HOLD|FAIL` `[REG SPEC §10.1]`.
- **Propagation rule** `[EXT]`: a metric's displayed status = the **worst** status among its source rows —
  **FAIL dominates HOLD dominates PASS**. A metric backed by any FAIL rows is shown **flagged (HOLD/FAIL)**,
  never as a clean green number. This is exactly what blocks *"làm đẹp dashboard bằng dữ liệu chưa verified"*
  `[REG FAIL-001 / §4 boundary]`.
- Gate→metric mapping example `[EXT]`: `Dedup=FAIL` (double count) ⇒ ROAS/CPA/AOV flagged; `Verified
  Revenue=FAIL` ⇒ all revenue metrics flagged; `Consent=FAIL` ⇒ affected send-derived metrics flagged;
  `Suppression` reflects recall/sale-lock/CRM-suppression `[REG RULE-017]`.
- **Scale-evidence link** `[REG RULE-009]`: only metrics that are **PASS** (and, for attribution, HIGH-confidence
  / non-conflicting) may feed the Scale Gate; HOLD/FAIL metrics are **never** scale evidence.
- A dashboard/metric may **not** be marked PASS while its DQ verdict is HOLD/FAIL — fail-closed display.

---

## 5. Boundary & safety guards `[BRIEF / REG §18]`

- **Read-only**, support-view-only `[DOC CTR-018 / REG RULE-012]`; Data Mart never triggers CRM/pricing/scale
  `[REG FAIL-005]`; the dashboard **auto-scales nothing** `[REG RULE-010]`.
- Revenue strictly `ORDER_VERIFIED` `[REG RULE-003 / FAIL-001]`.
- **No raw PII** in metrics, sample evidence, or logs `[REG RULE-014]` — sample rows masked; `secret_ref` for
  any credential.
- Alert **thresholds** are **not** invented — `MISSING → M6-OD-002` `[REG]`; the dashboard computes the locked
  formulas without numeric alert bands until the owner sets them.
- Channel-origin content shown in the dashboard (comments, ad copy) is untrusted DATA `[BRIEF rule 6]`.

## 6. Owner-decision dependencies (explicit list — acceptance requirement)

| Dependency | Status | What it gates |
|---|---|---|
| `M6-CTR-012` (ads_data_quality_check) | `MISSING` → **M6-P0708** `[REG]` | the DQ verdict shape/fields (§4); needed before **M6.2F** |
| `M6-CTR-024` (data_quality_checker worker) | `MISSING` → **M6-P0713** `[REG]` | how the 8 gate items produce PASS/HOLD/FAIL |
| `M6-CTR-018` (GET /api/admin/ads/dashboard) | `MISSING` → **M6-P0712** `[REG]` | the read-only dashboard API shape |
| `M6-OD-002` (alert thresholds) | **OPEN** `[REG]` | dashboard alert bands (formulas are locked; numbers pending) |
| Semantic-layer tech (materialized vs query-time), sample size/retention | **candidate** `[PACK/EXT]` — depends on M6-OD-011 stack | §2/§3 implementation |
| `M6-CTR-015` (Dashboard KPI) | DRAFT_LOCKED (formulas) `[REG]` | the 14 metric definitions used by §2 |

`[PACK]` This research records these; it resolves none. Where a build leg needs one, the affected M6.2F leg is
marked BLOCKED, not assumed.

## 7. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| Metric needs sample-evidence + source trace; visual-only dashboard is FAIL/HOLD | `[DOC §15 line 308]` + `[REG RULE-015]` — owner-mandated |
| 14 KPI formulas; revenue/ROAS from Verified Revenue only | `[DOC §14 lines 282–295]` + `[REG RULE-003]` — owner-mandated |
| Data Mart support-view-only, never a trigger owner; read-only dashboard | `[REG RULE-012 / FAIL-005]` + `[DOC CTR-018]` — owner-mandated |
| `ads_measurement_event.data_quality_status` enum; 8 §15 gate items | `[REG SPEC §10.1 / DOC §15]` — owner-mandated |
| Semantic layer; evidence-bundle shape; worst-status propagation rule; gate→metric mapping; materialization choice | `[EXT]` / `[PACK]` — owner-review proposals, NOT owner requirements |

*Nothing in this file flips a gate or a flag; `global_gateway_state=BLOCKED`, `production_flag=OFF`.*
