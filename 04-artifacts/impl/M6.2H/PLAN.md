# M6.2H IMPLEMENTATION PLAN — ADS Strategy Libraries & Learning-Engine skeleton (STAGED, plan-only)

**Prompt**: M6-P1701 (`M6_2H_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code this prompt)
**Slice**: M6.2H — build the six strategy-library framework + the learning-engine skeleton (Seed → Run → Learn →
Review → Publish, doc §17). **Content fill HALTS at framework while M6-OD-007 is unresolved.** Depends on M6.2G.
**Done gate**: *Seed framework pass; no auto-publish.*
**Posture (immutable)**: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
`SCALE_MODEL_RATIFIED=False`, `SCALE_EXECUTION_ENABLED=False`, `HASH_POLICY_RATIFIED=False`, `live_migrations=false`.
This plan writes no code, applies no migration, calls nothing external, generates no content/ad copy, publishes
nothing, resolves no owner decision, flips no flag.

> **Governance — framework-only by design (JUDGE-SIGNED entry M6-P1700 = PASS).** Two OPEN owner decisions scope
> this slice, both fail-closed, neither an entry blocker: **M6-OD-007** (persona/keyword/hook content fill) OPEN →
> **content fill HALTS at framework** (the framework may proceed; the machine never fabricates origin strategy,
> LEX-006); **M6-OD-006** (guarded auto-publish safe range) OPEN → **the guarded-publish path is BLOCKED** (SMK-011
> boundary values depend on it) — the ONLY publish path is explicit owner/marketing approval. M6.2G exit
> M6-P1609 = SIGNED (ADS Phase 1 complete). `M6-P1000` + `M6-P1309` verdicts stay BLOCKED (not converted); the
> M6.2G before-real-scale/send/auto-publish forward conditions remain in force. This plan builds the guarded
> framework + skeleton ONLY; nothing auto-publishes, nothing fabricates origin strategy.

---

## 1. Entry-gate verification

| Precondition | Source | Result |
|---|---|---|
| This prompt RUNNING | ledger (order 147) | **M6-P1701 = RUNNING** ✓ |
| Dependency resolved | ledger | **M6-P1700 = SIGNED** (entry judge PASS, opens M6.2H STAGED) ✓; M6.2G slice gate **M6-P1609 = SIGNED** ✓ |
| Target LOCKED + M6-OD-011 | manifest | `status=LOCKED`, `STAGED_ONLY`, safety all false; M6-OD-011 **DECIDED** ✓ |
| Slice contracts | M6-P1700 + CONTRACT_REGISTER | **CTR-014** (ads_learning_candidate), **CTR-020** (POST learning-candidates) = MISSING but harmonized-for-entry (producers M6-P0710 / M6-P0712 PASS, gate M6-P0715 SIGNED) ✓ |
| OPEN owner decisions | DECISION_REGISTER | **M6-OD-007** (content fill) → framework-only (fail-closed); **M6-OD-006** (safe range) → guarded publish BLOCKED (fail-closed); neither gates entry ✓ |
| Flags | manifest/brief | BLOCKED/OFF/OFF, SCALE/HASH_POLICY_RATIFIED=False, SCALE_EXECUTION_ENABLED=False, live_migrations=false ✓ |
| M6.2G foundation | `04-artifacts/impl/M6.2G/` (299 tests green) | present; M6.2F Data Quality Gate (PASS/HOLD/FAIL) + M6.2E verified revenue feed the Learn-stage precondition — carried forward per §2 ✓ |

**Conclusion**: open for **STAGED, framework-only** M6.2H. Build the guarded libraries + learning skeleton; the
machine never fabricates origin strategy; no auto-publish; content fill + guarded publish are fail-closed
(M6-OD-007/006 OPEN).

---

## 2. Working mode, conventions & staging model

Reuse the M6.2A–G baseline (pytest, frozen dataclasses, read-only ports + in-memory staged adapters, framework-
neutral pure handlers, staged migrations up+down, mask-on-export, fail-closed everywhere). **Cumulative snapshot**:
the whole **M6.2G** tree (final slice state) is carried forward byte-identical; M6.2H **adds** the learning layer
and a tiny config choke. The change set (§5) is the diff. **Nothing auto-publishes, nothing generates content, no
origin strategy is fabricated.** `production_flag=OFF` immutable.

---

## 3. Scope lock (anchored strictly to `00-spec/slices/M6.2H.md`)

**In scope (3 capabilities):**
1. **Six library schemas + the mapping chain** (§4.1) — SKU/Product line → Persona → Behavior → Keyword → Creative
   Hook → Landing → CTA → Event → Verified Revenue, with the doc §17 **seed-source constraints enforced** (each
   library seeds ONLY from its canonical source; the machine never fabricates origin strategy, RULE-011/LEX-006).
2. **`ads_learning_candidate` lifecycle + review queue** (CTR-014) — candidates land in the review queue only;
   owner/marketing approve/reject/hold; a candidate outside safe range → HOLD, no publish (SMK-011).
3. **POST /api/admin/ads/learning-candidates** (CTR-020) — create a candidate (→ review queue) + an owner-review
   decision handler. Inert (never publishes).

**Out of scope (explicit):**
- **Auto-publish outside safe range** (FAIL-006, RULE-011, LEX-006) — there is **no** auto-publish code path.
  Guarded safe-range publish is BLOCKED while **M6-OD-006** (safe range) is OPEN; the only publish path is explicit
  owner/marketing approval. `LEARNING_AUTOPUBLISH_ENABLED=False`.
- **Generating public ad copy / origin content** while the lexicon/claim table is MISSING (LEXICON_REGISTER;
  **M6-OD-007** OPEN) — content fill HALTS at framework. The libraries hold seed-SOURCE references + framework
  structure, NOT machine-generated persona/keyword/hook/copy. `LEARNING_CONTENT_FILL_ENABLED=False`.
- **Real ad run / spend / audience action** (M7/live ops), **scale** (M6.2G, done), **Core policy override**
  (RULE-013/018 — no pricing/program/member-right/CRM/Diamond/Golden-Hour/24-7 change), **commission** (Finance,
  RULE-019). The Run stage is a skeleton (records active mapping per sellable SKU; nothing runs).

---

## 4. Locked contract content (build to the exact spec)

### 4.1 The six libraries + seed sources (VERBATIM, doc §17, extract 338–345)

| # | Thư viện (Library) | Mục đích (Purpose) | Nguồn seed (Canonical seed source — REQUIRED) |
|---|---|---|---|
| 1 | **Persona Library** | Nhóm khách mục tiêu | Content Block 20 SKU, customer context, CRM lifecycle |
| 2 | **Behavior Library** | Hành vi số và hành vi mua | Web/Messenger/Live/CRM events đã **pass data quality** |
| 3 | **Keyword Library** | Từ khóa acquisition/intent | Content Block, product public view, search/ads history |
| 4 | **Negative Keyword Library** | Chặn tệp/ý định không phù hợp | Spam/troll/low-intent/fake order signals |
| 5 | **Creative Hook Library** | Hook không sale sốc, đúng brand, đúng claim | Product effectiveness, Meta-safe wording, Golden Hour Tri Ân |
| 6 | **Landing / CTA Library** | Mapping landing và CTA theo intent | Hero SKU, Golden Hour, Diamond, CRM/reorder |

**Mapping chain (doc §17 L336):** `SKU/Product line → Persona → Behavior → Keyword → Creative Hook → Landing →
CTA → Event → Verified Revenue`. Every optimization is anchored to a **sellable SKU** + program/Golden-Hour/24-7
policy + product public claim + brand wording (LEX-005). **Seed-only-from-canon (RULE-011):** an entry without a
canonical seed source, or a machine-fabricated origin strategy, is **rejected** (LEX-006 forbidden cell).

### 4.2 The 5-stage lifecycle (VERBATIM, doc §17, extract 347–353)

| Stage | Mô tả | Staged enforcement |
|---|---|---|
| **Seed** | Fill thư viện từ Content Block/SKU/Rule đã khóa; không để machine tự bịa chiến lược gốc | canonical seed-source REQUIRED; content fill BLOCKED (M6-OD-007) → framework-only |
| **Run** | Chạy acquisition/retargeting theo mapping active và sellable SKU | skeleton: records active mapping per sellable SKU; nothing actually runs (staged) |
| **Learn** | Đọc signal hiệu quả, score persona/keyword/hook/landing/CTA | runs ONLY after canonical seed exists AND consumes ONLY DQ-passed verified signals (RULE-011); scores the 5 doc dims |
| **Review** | Sinh candidate vào review queue; owner/marketing approve/reject/hold | candidate → review queue; owner decision; a candidate outside safe range → HOLD (SMK-011) |
| **Publish** | Guarded auto-publish trong safe range, có rollback và audit | **BLOCKED** (M6-OD-006 safe range OPEN); no auto-publish path; owner-approval-only, with rollback + audit (framework) |

---

## 5. Minimal change set (all target-relative, staged under `04-artifacts/impl/M6.2H/`)

Legend: **Leg** = M6.2H exit-gate leg (L1 = *seed framework pass*; L2 = *no auto-publish*; L3 = *learning-input
precondition*). Rollback: new files → delete; patched carried-forward files → revert to M6.2G.

### 5.1 New — the Strategy-library layer

| # | Target file (new) | Purpose | Contract/Rule | Leg | Smoke |
|---|---|---|---|---|---|
| L1 | `app/measurement/learning/__init__.py` | package marker | — | — | — |
| L2 | `app/measurement/learning/libraries.py` | the six library models + `StrategyLibraryKind` enum (Persona/Behavior/Keyword/NegativeKeyword/CreativeHook/LandingCTA) + `SeedSource` (canonical sources) + `LibraryEntry{entry_id, kind, purpose, seed_source(REQUIRED), content(None while OD-007 OPEN)}` + `StrategyLibraryStore`. **Seed-only-from-canon (RULE-011/LEX-006):** an entry with a missing/non-canonical seed source, or machine-generated `content` while `LEARNING_CONTENT_FILL_ENABLED=False`, is REJECTED (fail-closed). | CTR-014-adjacent; **RULE-011/018/LEX-006** | **L1** | — |
| L3 | `app/measurement/learning/mapping.py` | `StrategyMapping{sku_ref, persona, behavior, keyword, creative_hook, landing, cta, event, verified_revenue_ref}` — the doc §17 chain; every mapping anchored to a **sellable SKU** (LEX-005); never overrides Core policy (RULE-013/018). Read-only over consumed canon. | CTR-014; RULE-013/018 | L1 | — |
| L4 | `app/measurement/learning/candidate.py` | `AdsLearningCandidate` (CTR-014, **inert**): `{candidate_id, kind(delta/safe_range/optimization), target_dim(persona/keyword/hook/landing/cta), score, sku_ref, evidence_refs, review_state, safe_range_status}` + `ReviewState`(CANDIDATE/IN_REVIEW/APPROVED/REJECTED/HOLD) + `SafeRangeStatus`(WITHIN/OUTSIDE/UNKNOWN). PII masked. | CTR-014 | L2 | **SMK-011** |
| L5 | `app/measurement/learning/learning_engine.py` | `LearningEngine` — the 5-stage skeleton: `seed()` (canonical-only, rejects fabricated origin); `run()` (records active mapping per sellable SKU; nothing runs); `learn()` (**precondition: seed exists + only DQ-passed verified signals**, RULE-011; scores the 5 doc dims); `review()` (candidate → queue); **NO auto-publish method** — publish is BLOCKED (M6-OD-006), owner-approval-only (RULE-011/LEX-006/FAIL-006). | **CTR-014**; **RULE-011/LEX-006** | **L1/L2/L3** | **SMK-011** |
| L6 | `app/measurement/learning/review_queue.py` | inert review-queue store: candidates + owner-review decisions (approve/reject/hold), append-only. A candidate outside/UNKNOWN safe range → HOLD (SMK-011); no publish op. | CTR-014/020 | L2 | SMK-011 |
| L7 | `app/api/learning_candidates.py` | **CTR-020 POST /api/admin/ads/learning-candidates**: `handle_learning_candidate_create` (→ review queue, inert) + `handle_learning_review_decision` (owner approve/reject/hold). `LearningDeps` holds no publisher/Transport/auto-publish handle; untrusted body = DATA (RULE-H03); PII masked; NEVER publishes. | CTR-020; RULE-011/FAIL-006 | L2 | SMK-011 |

### 5.2 Staged migrations & config

| # | Target file (new/patched) | Change | Leg | Rollback |
|---|---|---|---|---|
| M1 | `migrations/0011_create_ads_strategy_libraries.sql` (new) | Staged DDL (up+down): the six libraries (kind + purpose + seed_source REQUIRED + nullable content) + the strategy mapping (chain columns, sku_ref); a comment that content is BLOCKED (M6-OD-007) and seed_source is mandatory (RULE-011). Never applied. | L1 | down-DDL DROP; delete |
| M2 | `migrations/0012_create_ads_learning_candidate.sql` (new) | Staged DDL (up+down): `ads_learning_candidate` (CTR-014) — candidate + kind + target_dim + score + sku_ref + evidence + review_state + safe_range_status; CHECK review_state ∈ {CANDIDATE,IN_REVIEW,APPROVED,REJECTED,HOLD} and safe_range_status ∈ {WITHIN,OUTSIDE,UNKNOWN}; a comment that NO trigger/auto-publish path exists (FAIL-006). Never applied. | L2 | down-DDL DROP; delete |
| A1 | `app/config.py` (**extend**) | Add `LEARNING_AUTOPUBLISH_ENABLED = False` (RULE-011/LEX-006/FAIL-006 — no auto-publish path; a single explicit choke) + `LEARNING_CONTENT_FILL_ENABLED = False` (M6-OD-007 OPEN → framework-only, no fabricated content) + `LEARNING_SAFE_RANGE_RATIFIED = False` (M6-OD-006 OPEN → guarded publish BLOCKED). None is an enabling flag; none is read to act. | L1/L2 | revert to M6.2G |

---

## 6. Test plan → done-gate / smoke mapping (`pytest -q`; TESTER executes L4–L6)

Fixtures extend `conftest.py` with a `StrategyLibraryStore`, a `LearningEngine`, a review queue, staged canonical
seed sources, and DQ-passed / non-passed verified signals from the M6.2F/M6.2E layers. Carried-forward M6.2G tests
stay green. PII markers assembled at runtime (no literal PII in source).

| # | Target test (new) | Proves | Leg | Smoke | Fail-gate |
|---|---|---|---|---|---|
| T1 | `tests/test_libraries_seed_from_canon_only.py` | **leg 1**: the six libraries exist; an entry seeded from a canonical source is accepted; a missing/non-canonical seed source, or a machine-fabricated origin strategy, is REJECTED (RULE-011, LEX-006 — machine never fabricates origin). | **L1** | — | — |
| T2 | `tests/test_content_fill_halts_at_framework.py` | **leg 1**: while `LEARNING_CONTENT_FILL_ENABLED=False` (M6-OD-007 OPEN), a library entry carries a seed-source reference but NO machine-generated content; the framework proceeds, content is blocked. | L1 | — | — |
| T3 | `tests/test_candidate_outside_safe_range_holds.py` | **leg 2 / SMK-011 / FAIL-006**: a learning candidate outside (or UNKNOWN, since M6-OD-006 OPEN) safe range → HOLD in review, NOT published; no auto-publish path exists. | **L2** | **SMK-011** | **FAIL-006** |
| T4 | `tests/test_no_auto_publish_review_queue_only.py` | **leg 2**: candidates land in the review queue only; the learning layer/handlers/deps expose NO auto-publish/execute method; publish requires explicit owner approval; guarded safe-range publish is BLOCKED (`LEARNING_SAFE_RANGE_RATIFIED=False`); `LEARNING_AUTOPUBLISH_ENABLED is False`. | **L2** | SMK-011 | **FAIL-006** |
| T5 | `tests/test_learn_precondition_seed_and_dq.py` | **leg 3 / RULE-011**: the Learn stage refuses to run without a canonical seed; and consumes ONLY DQ-passed verified signals (a HOLD/FAIL/unverified signal is excluded); scores the 5 doc dims. | **L3** | — | — |
| T6 | `tests/test_mapping_chain_anchored_to_sku.py` | **leg 1**: the SKU→Persona→…→Verified Revenue mapping chain resolves; every mapping is anchored to a sellable SKU (LEX-005); the layer never overrides Core policy / never writes pricing/program (RULE-013/018). | L1 | — | — |

**Smoke → test binding**: SMK-011 = T3(+T4). Execution + recorded results/evidence (legs L4–L6) is the
**TESTER**'s (M6-P1703/1704). No self-run / self-certify (RULE-015).

---

## 7. Master traceability matrix

| Item | Files | Contract | Rule(s) | Leg | Smoke | Fail-gate | Rollback |
|---|---|---|---|---|---|---|---|
| Six libraries (seed-from-canon) | L2 | CTR-014-adj | RULE-011/018/LEX-006 | **L1** | — | — | delete |
| Mapping chain (SKU-anchored) | L3 | CTR-014 | RULE-013/018/LEX-005 | L1 | — | — | delete |
| ads_learning_candidate (inert) | L4 | CTR-014 | RULE-011 | L2 | SMK-011 | FAIL-006 | delete |
| Learning engine (5-stage skeleton) | L5 | CTR-014 | **RULE-011/LEX-006** | **L1/L2/L3** | SMK-011 | FAIL-006 | delete |
| Review queue (inert, no publish) | L6 | CTR-014/020 | RULE-011 | L2 | SMK-011 | FAIL-006 | delete |
| POST /learning-candidates + review | L7 | CTR-020 | RULE-011/FAIL-006 | L2 | SMK-011 | FAIL-006 | delete |
| Migrations + config | M1,M2,A1 | CTR-014 | RULE-011/LEX-006 | L1/L2 | — | — | down-DDL / revert |
| Tests | T1–T6 | — | — | L1/L2/L3 (+L4–L6 runnable) | SMK-011 | FAIL-006 | delete |

**Legs**: L1 ✓ (seed framework pass — T1/T2/T6); L2 ✓ (no auto-publish — T3/T4); L3 ✓ (learning-input precondition
— T5); L4–L6 ✓ *made runnable* (TESTER executes SMK-011); L7 (evidence — process), L8 (judge — process), **L9 ✓
(this doc — rollback per item)**.

---

## 8. Rollback strategy (global)

1. **Nothing live / nothing publishes.** Staged under `04-artifacts/impl/M6.2H/`; no migration applied, no
   external call, no content generated, no auto-publish, no flag written. Baseline rollback = delete the M6.2H
   tree (M6.2G untouched).
2. **Per-item** (§5): new files → delete; patched `config.py` → revert to M6.2G. Migrations 0011/0012 → down-DDL
   DROP (staged; not executed).
3. **Review-queue records are inert + append-only** (in-memory); a reject/hold is a new recorded decision, never
   a published change.

---

## 9. Plan-deltas & notes

- **Framework-only, machine-never-fabricates-origin (RULE-011, LEX-006 forbidden cell)** — the primary constraint:
  the libraries hold canonical seed-SOURCE references + framework structure; `content` stays None while
  `LEARNING_CONTENT_FILL_ENABLED=False` (M6-OD-007 OPEN). A fabricated/non-canonical origin strategy is rejected.
- **No auto-publish (FAIL-006, exit-leg 2)** — enforced STRUCTURALLY: the learning layer has NO auto-publish
  method; publish is BLOCKED (`LEARNING_SAFE_RANGE_RATIFIED=False`, M6-OD-006) and owner-approval-only. A candidate
  outside/UNKNOWN safe range → HOLD (SMK-011). T4 asserts no auto-publish surface.
- **Learn precondition (RULE-011, exit-leg 3)** — Learn runs ONLY after a canonical seed exists AND consumes ONLY
  DQ-passed verified signals (from the M6.2F Data Quality Gate + M6.2E verified revenue); fail-closed otherwise.
- **Learn scores the 5 doc dims** (persona/keyword/hook/landing/CTA, doc §17 L351). Behavior/Negative-Keyword are
  SEED libraries (framework) but not doc-mandated Learn-scoring dims (ARCH_BASELINE §1.8 `[EXT]`).
- **No Core-policy override (RULE-013/018)** — the layer reads canonical sources; it never writes pricing/program/
  member-right/CRM/Diamond/Golden-Hour/24-7. **No commission** (RULE-019). **No public ad copy** (LEX-001/002/006).
- **Forward gates** — M6-OD-007 (content) + M6-OD-006 (safe range) before any real seed content / guarded publish;
  the M6.2G before-real-scale/send/auto-publish conditions stand; `M6-P1000`/`M6-P1309` stay BLOCKED. Smoke
  execution (legs L4–L6) is the TESTER's (M6-P1703/1704).

---

## 10. Acceptance self-map

1. *Every item → leg or smoke* → §5–§7. ✓  2. *Rollback per item* → §5/§8. ✓  3. *No scope beyond the slice* →
§3 (auto-publish/content-generation/real-run/scale/Core-override deferred; framework-only). ✓  4. *Target LOCKED +
M6-OD-011 decided* → §1. ✓  5. *Reuse conventions/test patterns* → §2 (M6.2G baseline). ✓  Plus the **load-bearing
invariants**: machine-never-fabricates-origin (RULE-011/LEX-006, T1/T2), no auto-publish (FAIL-006, T3/T4,
SMK-011), Learn-input precondition (RULE-011, T5) — each with a test and the M6.2G suite staying green.

*Plan-only: no code, no migration applied, nothing generated/published/scaled/sent, no flag flipped; BLOCKED/OFF/OFF.*
