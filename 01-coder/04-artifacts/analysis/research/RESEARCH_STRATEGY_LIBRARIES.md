# RESEARCH_STRATEGY_LIBRARIES — the six ADS strategy libraries (doc §17 / SPEC §8.4)

**Prompt**: M6-P0211 · **Phase**: PHASE0_RESEARCH · **Mode**: analysis_only (desk research; design proposal)
**Anchors**: `[DOC §17 extract lines 328–353]` = `[SPEC §8.4]` (verbatim lock) ADS Strategy Input Pack; mapping
core `[DOC §17 L336]`; `M6-CTR-014 ads_learning_candidate` (→M6-P0710), `M6-CTR-020` API (→M6-P0712); slice
**M6.2H**; owner decisions **M6-OD-001** (Hero SKU lock), **M6-OD-006** (safe range), **M6-OD-007** (content
fill); `[REG RULE-011]` guarded learning, `[REG LEX-001/002/005/006]`.
**Critic**: M6-PC0211 (BOUNDARY_ADVERSARY) red-teams this file next.
**Related**: `[[RESEARCH_LEARNING_ENGINE_GUARDRAILS]]` (M6-P0209) — the fail-closed lifecycle; this file is the
**library-schema + mapping-chain** angle and does not restate the guardrails.

> **Three layers, held razor-apart — the whole discipline of this file:**
> **(1) LOCKED** — each library's *purpose* + *seed-SOURCE* is reproduced **verbatim** from SPEC §8.4.
> **(2) SCHEMA (owner-review)** — the field shape of a library entry and the mapping-chain record are
> **proposals** `[PACK]/[EXT]`; the field-locked contract `M6-CTR-014` is still `MISSING`.
> **(3) CONTENT (BLOCKED)** — the actual seeds (which personas, which keywords, which hooks, which
> landings/CTAs) are **not in §8.4** and are therefore **BLOCKED**, gated by `M6-OD-007` (and `M6-OD-001`),
> **never guessed**. Inventing a seed is exactly *"machine tự bịa chiến lược gốc"* — the doc's FORBIDDEN cell
> `[REG LEX-006]`. `global_gateway_state=BLOCKED`, `production_flag=OFF` unchanged.

## Sourcing legend (acceptance: every externally-sourced claim labeled)

- `[DOC]` — owner document / extract line, reproduced in `[SPEC §8.4]`. **Only `[DOC]` items are owner
  requirements.**
- `[REG]` — locked pack register. · `[BRIEF]` — context brief. · `[PACK]` — pack convention (owner-review). ·
  `[EXT]` — general engineering practice, **proposal only**.

**Doc anchors** (verbatim): `[DOC §17 L328]` seed from *Content Block canonical, SKU Master, Phase ADS rule,
business truth*; `[DOC §17 L336]` mapping core *SKU/Product line → Persona → Behavior → Keyword → Creative Hook
→ Landing → CTA → Event → Verified Revenue*; `[DOC §17 L338–345]` the six-library table (§1); `[DOC §17
L347–353]` the five stages (Seed→Run→Learn→Review→Publish); `[DOC §17 L351]` Learn = *"score
persona/keyword/hook/landing/CTA"*. Rules: `[REG RULE-011]` guarded learning; `[REG LEX-001]` *"Hook không sale
sốc, đúng brand, đúng claim"*, `[REG LEX-002]` *"Meta-safe wording, Golden Hour Tri Ân"*, `[REG LEX-005]` *"Mọi
optimization phải gắn với sellable SKU, program, Golden Hour/24/7 policy, product public claim và brand
wording"*, `[REG LEX-006]` FORBIDDEN cell (no fabricated origin strategy / no full auto-publish).

---

## 1. The six libraries — purpose + seed-source, LOCKED VERBATIM `[SPEC §8.4 / DOC §17 L338–345]`

Reproduced exactly from the locked table (Vietnamese verbatim). **The "Nguồn seed" column is a source
constraint, not a content list** — it says *where* a seed may come from, never *what* the seed is.

| Thư viện | Mục đích `[DOC]` | Nguồn seed (verbatim) `[DOC]` |
|---|---|---|
| **Persona Library** | Nhóm khách mục tiêu | Content Block 20 SKU, customer context, CRM lifecycle |
| **Behavior Library** | Hành vi số và hành vi mua | Web/Messenger/Live/CRM events đã pass data quality |
| **Keyword Library** | Từ khóa acquisition/intent | Content Block, product public view, search/ads history |
| **Negative Keyword Library** | Chặn tệp/ý định không phù hợp | Spam/troll/low-intent/fake order signals |
| **Creative Hook Library** | Hook không sale sốc, đúng brand, đúng claim | Product effectiveness, Meta-safe wording, Golden Hour Tri Ân |
| **Landing / CTA Library** | Mapping landing và CTA theo intent | Hero SKU, Golden Hour, Diamond, CRM/reorder |

**Per-library seed-source notes** (what the source constraint implies for the build):

- **Persona / Keyword / Creative Hook** seed from **Content Block (20 SKU)** → their content is gated by
  **M6-OD-007** (*"Danh sách persona/keyword/hook fill từ Content Block 20 SKU đã khóa chưa? Nếu chưa khóa, chỉ
  dừng ở framework"*) `[DOC §25 L484]`. Until the Content Block is locked, these three stay **framework only**.
- **Behavior / Negative Keyword** seed from **runtime signals** (DQ-passed events / spam-troll-fake signals) —
  not a fixed owner list, so there is no static content to lock; entries populate **from verified data at
  runtime**, gated by the **Data Quality Gate** and consent `[REG RULE-002]`. Still nothing is invented here.
- **Landing / CTA** seeds from **Hero SKU** (+ Golden Hour / Diamond / CRM-reorder) → additionally gated by
  **M6-OD-001** (*"Danh sách Hero SKU Phase 1 chính thức là gì?"* — OPEN) `[DOC §25 L478]`.
- **Creative Hook** carries **extra wording locks**: `[REG LEX-001]` *"Hook không sale sốc, đúng brand, đúng
  claim"* + `[REG LEX-002]` *"Meta-safe wording, Golden Hour Tri Ân"*, and **no public copy** may be generated
  while the **banned-word / claim table is MISSING** `[REG LEXICON_REGISTER → M6-OD-007]`.

---

## 2. Schema per library `[PACK]/[EXT] — proposal; field-locked shape = M6-CTR-014 MISSING → M6-P0710]`

`M6-CTR-014 ads_learning_candidate` has **no field-level schema yet** `[REG CONTRACT_REGISTER]`; the shapes
below are **owner-review proposals**, not owner requirements. **Every library entry shares three mandatory
fields** (the fail-closed spine, per `[[RESEARCH_LEARNING_ENGINE_GUARDRAILS]]` §2 / `[REG RULE-011]`):

- `seed_source_ref` — a canonical provenance pointer (Content Block id / SKU Master id / Phase ADS rule id /
  DQ-passed signal ref). **An entry lacking a canonical provenance is rejected** — fail-closed.
- `status` — `FRAMEWORK` (schema only, no content) | `SEEDED` (content from a locked source) | `ACTIVE`.
- `provenance_audit[]` — append-only `{actor, source_ref, ts}`.

`[EXT] proposed per-library fields` (structure only — **no example content**, which is BLOCKED, §5):

| Library | Proposed entry shape (beyond the shared spine) |
|---|---|
| **Persona** | `{ persona_id, label, source_kind (content_block_sku\|customer_context\|crm_lifecycle), attributes{} (empty until M6-OD-007) }` |
| **Behavior** | `{ behavior_id, kind (digital\|purchase), signal_source (web\|messenger\|live\|crm), dq_pass_ref (mandatory) }` |
| **Keyword** | `{ keyword_id, intent (acquisition\|intent), source_kind (content_block\|product_public_view\|search_ads_history) }` |
| **Negative Keyword** | `{ neg_keyword_id, block_reason (spam\|troll\|low_intent\|fake_order), signal_source_ref }` |
| **Creative Hook** | `{ hook_id, brand_claim_ref, lexicon_check (LEX-001+LEX-002), meta_safe_flag, banned_word_check (BLOCKED until M6-OD-007), public_copy=false-until-table-locked }` |
| **Landing / CTA** | `{ mapping_id, intent, landing_ref, cta_ref, source_kind (hero_sku\|golden_hour\|diamond\|crm_reorder) }` |

- `[PACK]` The **Creative Hook** entry is the only one that can emit **public-facing text**; its
  `banned_word_check` and `public_copy` fields are hard-gated by the MISSING banned-word table (M6-OD-007) so
  the library can be **structured** now and **filled** only after the owner locks wording.

---

## 3. The mapping chain as a data structure `[DOC §17 L336 — order verbatim; structure = PACK]`

The mapping is *"lõi để Ads không chạy cảm tính"* `[DOC L336]`. The **order is owner-mandated and verbatim**;
expressing it as a record is a `[PACK]` proposal:

```
SKU/Product line → Persona → Behavior → Keyword → Creative Hook → Landing → CTA → Event → Verified Revenue
```

`[PACK] proposed mapping record` (one row = one traceable acquisition path):

```
ads_strategy_mapping {
  mapping_id
  sku_or_product_line_ref     // node 0 — MUST be a sellable SKU (LEX-005) and, for pilot, a Hero SKU (M6-OD-001)
  persona_id                  // → Persona Library
  behavior_id                 // → Behavior Library
  keyword_id[]                // → Keyword Library
  negative_keyword_id[]       // → Negative Keyword Library (filter, applied to the above)
  hook_id                     // → Creative Hook Library (LEX-001/002 checked)
  landing_id, cta_id          // → Landing/CTA Library
  event_code                  // → Core event_registry (RULE-001; must be registered)
  verified_revenue_binding    // → ads_attribution_context / ads_measurement_event (CTR-002/001)
  status, evidence_refs[]
}
```

- **The terminal edge is the measurement spine, not marketing taxonomy.** `Event → Verified Revenue` binds the
  chain to `M6-CTR-001/002` and `[REG RULE-003]` (revenue only from ORDER_VERIFIED). A mapping node whose
  `event_code` is unregistered `[REG RULE-001]` or whose `verified_revenue_binding` is absent is
  **unmeasurable ⇒ not scale-eligible** — fail-closed, consistent with `[[RESEARCH_ATTRIBUTION_MODELS]]` and
  the Scale Gate evidence bundle `[[RESEARCH_SCALE_GATE_WORKFLOW]]`.
- **Node 0 is constrained**: `[REG LEX-005]` every optimization ties to a *sellable SKU + program + Golden
  Hour/24-7 policy + public claim + brand wording*; a mapping anchored to a non-sellable / non-Hero SKU (pilot)
  is invalid until M6-OD-001 locks the Hero list.
- **Negative Keyword is a filter edge, not a chain node** — it prunes the audience/intent reached by the
  Persona/Keyword nodes; modeled as a set applied across the path, not a position in the linear order.

---

## 4. Review / scoring hooks for the learning engine `[DOC §17 L351–353]`

How the libraries plug into the Learn → Review → Publish stages (fail-closed detail in
`[[RESEARCH_LEARNING_ENGINE_GUARDRAILS]]`; not restated):

- **Learn (score)** `[DOC L351]` — the doc's Learn stage scores **exactly five** dimensions, verbatim:
  *persona / keyword / hook / landing / CTA*. `[PACK]` proposed score fields on those five library entries:
  `{ effectiveness_score, sample_size, confidence }` — computed **only from verified business signals that
  passed the DQ Gate** `[DOC §17 L330]`, never from dirty or unconsented data.
  - **Precise verbatim note (verify-before-assert):** L351 names **five** scored dimensions; **Behavior
    Library** and **Negative Keyword Library** are **not** in the doc's score list — Behavior is a targeting
    input and Negative Keyword is a filter. Scoring them would be `[EXT]`, so it is a **candidate**, not an
    owner requirement; flagged for the owner rather than silently added.
- **Review (candidate → queue)** `[DOC L352]` — a scored change becomes an `ads_learning_candidate`
  (`M6-CTR-014`, MISSING → M6-P0710) placed in the **review queue**; owner/marketing **approve / reject /
  hold**. Default = review-only; **no full-auto-publish path** `[REG LEX-006]`. `HOLD` is first-class (smoke
  **M6-SMK-011**: *candidate outside safe range → hold review, không publish*) `[REG]`.
- **Publish (guarded)** `[DOC L353]` — guarded auto-publish **only within the owner-defined safe range**, with
  rollback + audit. **M6-OD-006 is OPEN ⇒ auto-publish BLOCKED entirely**; every candidate goes to review.
- **Content gate** — even an approved candidate emits **no public copy** while the banned-word table is MISSING
  `[REG M6-OD-007]`.

---

## 5. Seed CONTENT is BLOCKED, not guessed (the fail-closed core) `[REG LEX-006 / RULE-011 / M6-OD-007/001]`

Per the prompt: *any library seed not present in SPEC §8.4 is a BLOCKED item, not a build-time guess.* §8.4
locks **purpose + seed-source**; it contains **no actual seeds**. Therefore:

| Library | Content status | Blocker | May proceed now |
|---|---|---|---|
| Persona | **BLOCKED** (no personas listed in §8.4) | **M6-OD-007** (Content Block 20 SKU lock) | schema (§2) + mapping slot (§3) — framework only |
| Keyword | **BLOCKED** | **M6-OD-007** | schema + mapping slot |
| Creative Hook | **BLOCKED** (+ no public copy) | **M6-OD-007** + banned-word table MISSING | schema + LEX-001/002 checks — framework only |
| Landing / CTA | **BLOCKED** | **M6-OD-001** (Hero SKU) + M6-OD-007 | schema + mapping slot |
| Behavior | data-derived, not a static list | Data Quality Gate + consent (RULE-002) | schema; entries populate from DQ-passed signals |
| Negative Keyword | data-derived, not a static list | spam/troll/fake-order signal availability | schema; entries populate from signals |

**This file invents zero seeds.** No example persona, keyword, hook, landing or CTA appears anywhere in it —
deliberately. Where the build legs need content, the affected **M6.2H** leg is marked **BLOCKED**, not assumed.

## 6. Owner-decision & contract dependencies (explicit list — acceptance requirement)

| Dependency | Status | What it gates |
|---|---|---|
| **M6-OD-007** (persona/keyword/hook fill from Content Block 20 SKU locked?) | **OPEN** `[REG]` | all Persona/Keyword/Hook **content**; any public copy; framework may proceed |
| **M6-OD-001** (Hero SKU Phase 1 lock) | **OPEN** `[REG]` | Landing/CTA + mapping node-0 sellable-SKU constraint |
| **M6-OD-006** (safe range) | **OPEN** `[REG]` | guarded auto-publish (§4); BLOCKED until defined |
| `M6-CTR-014` (ads_learning_candidate) | `MISSING` → **M6-P0710** `[REG]` | the field-locked library/candidate schema (§2/§4) |
| `M6-CTR-020` (learning-candidates API) | `MISSING` → **M6-P0712** `[REG]` | candidate submission API |
| Score fields for Behavior / Negative Keyword (§4) | **candidate** `[EXT]` | not in doc's 5-dim Learn list; owner accepts/rejects |
| Banned-word / claim table | `MISSING` → **M6-OD-007** `[REG]` | Creative Hook public copy |

`[PACK]` This research records these; it resolves none.

## 7. Boundary & safety guards `[BRIEF / REG §18]`

- **No fabricated origin strategy, no full auto-publish** `[REG LEX-006 / RULE-011]` — outputs are
  candidate/delta/safe-range only.
- **No public copy** while the banned-word/claim table is MISSING `[REG M6-OD-007]`; Creative Hook halts at
  framework.
- **Staged**: `production_flag=OFF` ⇒ no real publish even for a safe-range candidate.
- No pricing/order/CRM/commission/scale side effects; learning ≠ scale (safe range excludes budget/scale —
  that is the Scale Gate + M6-OD-002) `[REG §18]`, per `[[RESEARCH_LEARNING_ENGINE_GUARDRAILS]]` §6.
- **No raw PII** in library entries, signals or audit `[REG RULE-014]`; channel-origin content (comments, ad
  copy) is untrusted **DATA** — never a seed source, never an instruction `[REG RULE-H03 / BRIEF rule 6]`.

## 8. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| Six libraries: purpose + seed-source (verbatim) | `[DOC §17 L338–345 / SPEC §8.4]` — owner-mandated |
| Seed from canon only; no fabricated origin strategy; no full auto-publish | `[DOC §17 L328/L332]` + `[REG RULE-011/LEX-006]` — owner-mandated |
| Mapping chain order SKU→Persona→…→Event→Verified Revenue | `[DOC §17 L336]` — owner-mandated |
| Learn scores persona/keyword/hook/landing/CTA (5 dims) | `[DOC §17 L351]` — owner-mandated |
| Creative Hook wording locks; every optimization tied to sellable SKU/program/policy/claim/brand | `[REG LEX-001/002/005]` (`[DOC §17 L344/L334]`) — owner-mandated |
| Content BLOCKED until Content Block 20 SKU / Hero SKU locked | `[DOC §25 L484/L478]` (`[REG M6-OD-007/001]`) — owner-mandated |
| Per-library **field schema**; mapping **record** shape; score fields; Behavior/Negative-keyword scoring; filter-edge modeling | `[EXT]` / `[PACK]` — owner-review proposals, NOT owner requirements |

*This file locks purpose + seed-source verbatim, proposes schema + mapping structure, and BLOCKS all seed
content — it invents no seed, flips no gate or flag; `global_gateway_state=BLOCKED`, `production_flag=OFF`.*
