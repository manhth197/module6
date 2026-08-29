# M6.2H IMPLEMENTATION NOTES — ADS Strategy Libraries & Learning-Engine skeleton (STAGED)

**Prompt**: M6-P1702 (`M6_2H_CODER_IMPLEMENT`) · **Role**: CODER · **Mode**: `implement` · **Gate**: EVIDENCE_GATE
**Follows**: [PLAN.md](PLAN.md) (M6-P1701). Built item-by-item; no plan-deltas. **Posture unchanged & immutable**:
`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `SCALE_MODEL_RATIFIED=False`,
`SCALE_EXECUTION_ENABLED=False`, `HASH_POLICY_RATIFIED=False`, `LEARNING_AUTOPUBLISH_ENABLED=False`,
`LEARNING_CONTENT_FILL_ENABLED=False`, `LEARNING_SAFE_RANGE_RATIFIED=False`, `live_migrations=false`. No code
auto-publishes, generates content/ad copy, fabricates origin strategy, applies a migration, or flips a flag.

> **Status: coder self-reported PASS** (the runner gate + JUDGE decide, RULE-015). The two module-critical
> invariants — **the machine never fabricates origin strategy** (LEX-006, the doc's FORBIDDEN cell) and **no
> auto-publish** (FAIL-006) — plus the Learn precondition, held CLEAN under a 3-dimension adversarial review with
> **zero findings** (§5). I proactively applied the M6.2E/F/G review lessons (machine-safe audit detail,
> fail-closed defaults, no untrusted-body injection, structural absence of any publish/execute path).

## 1. Staging model — cumulative carry-forward

The whole **M6.2G** tree (313 tests as the slice finally stood after M6-P1603–1609) was carried forward
byte-identical into `04-artifacts/impl/M6.2H/` (caches excluded; `PLAN.md` kept, this file added). Baseline
verified green (313, rc 0) BEFORE any patch. Final suite: **345 passed, rc 0** (313 carried + 32 new). Subprocess counts.

## 2. Change set (all under `04-artifacts/impl/M6.2H/`)

**New — learning layer**
| File | Purpose |
|---|---|
| `app/measurement/learning/libraries.py` | The six libraries (Persona/Behavior/Keyword/Negative-Keyword/Creative-Hook/Landing-CTA) with locked purpose (doc §17) + `CANONICAL_SEED_SOURCES` per kind. `StrategyLibraryStore.seed()` **rejects** a missing/non-canonical seed source and **rejects** any machine-generated `content` while `LEARNING_CONTENT_FILL_ENABLED=False` (framework-only) — the machine never fabricates origin strategy (RULE-011, LEX-006). |
| `app/measurement/learning/mapping.py` | `StrategyMapping` — the SKU→Persona→…→Verified Revenue chain; anchored to a sellable SKU (LEX-005, enforced in `__post_init__`); read-only refs, never writes Core policy (RULE-013/018). |
| `app/measurement/learning/candidate.py` | `AdsLearningCandidate` (CTR-014, inert) + `LearningCandidateKind` + `TargetDim` (5 Learn dims) + `ReviewState` + `SafeRangeStatus` + `OwnerReviewDecision`. `is_publish_authorized` requires APPROVED **and** safe-range WITHIN → **always False** in staged posture (safe range UNKNOWN, M6-OD-006). Actor masked. |
| `app/measurement/learning/review_queue.py` | Inert append-only queue (candidates + review history). No publish/send method. |
| `app/measurement/learning/learning_engine.py` | The 5-stage skeleton: `seed()` (canonical-only), `run()` (records SKU-anchored mapping; nothing runs), `learn()` (**precondition: seed exists + only DQ-passed verified signals**, RULE-011; scores the 5 dims), `review()` (→ queue; not-WITHIN → HOLD, SMK-011), `record_review_decision()` (explicit owner approve/reject/hold; machine-safe audit). **No publish/auto-publish method**; `guarded_publish_blocked()` reports True. |
| `app/api/learning_candidates.py` | **CTR-020 POST /api/admin/ads/learning-candidates**: `handle_learning_candidate_create` (→ review queue, inert) + `handle_learning_review_decision` (owner approve/reject/hold). `LearningDeps` holds only the inert engine + audit — no publisher/Transport. Untrusted body = DATA; owner decision requires all of actor/reason/audit/evidence (RULE-015). |

**Patched (carried-forward) + staged migrations**
| File | Change |
|---|---|
| `app/config.py` | `LEARNING_AUTOPUBLISH_ENABLED=False` (no auto-publish path, RULE-011/LEX-006/FAIL-006) + `LEARNING_CONTENT_FILL_ENABLED=False` (M6-OD-007 → framework-only) + `LEARNING_SAFE_RANGE_RATIFIED=False` (M6-OD-006 → guarded publish BLOCKED, safe range UNKNOWN). None enabling; none read to act. |
| `migrations/0011_create_ads_strategy_libraries.sql` | Staged DDL (up+down): the six libraries (seed_source NOT NULL, content NULL while OD-007) + the SKU-anchored mapping; comment: no content generation, no trigger. |
| `migrations/0012_create_ads_learning_candidate.sql` | Staged DDL (up+down): CTR-014 inert candidate (kind/target_dim/score/sku_ref/review_state/safe_range_status); CHECK enums; comment: no trigger/auto-publish path. |

## 3. Tests → smoke/leg mapping (TESTER executes L4–L6)

| Test | Proves | Leg / smoke |
|---|---|---|
| `test_libraries_seed_from_canon_only.py` | six libraries; canonical seed accepted; missing/non-canonical/fabricated seed rejected (RULE-011/LEX-006) | L1 |
| `test_content_fill_halts_at_framework.py` | content fill BLOCKED (M6-OD-007); entry has seed-source ref, no content; content attempt rejected | L1 |
| `test_candidate_outside_safe_range_holds.py` | candidate outside/UNKNOWN safe range → HOLD, not publishable; guarded publish blocked | **L2 / SMK-011 / FAIL-006** |
| `test_no_auto_publish_review_queue_only.py` | no publish/auto-publish method; deps inert; candidate → review queue HELD; posture flags | **L2 / FAIL-006** |
| `test_learn_precondition_seed_and_dq.py` | Learn refuses without seed; consumes only DQ-passed verified signals; scores 5 dims (RULE-011) | **L3** |
| `test_mapping_chain_anchored_to_sku.py` | SKU→…→Verified-Revenue chain; anchored to sellable SKU (LEX-005); no Core-write method (RULE-013/018) | L1 |

Smoke EXECUTION (legs L4–L6) is the TESTER's (M6-P1703/1704) — no self-run (RULE-015).

## 4. (No plan-deltas)

Everything matches PLAN §5. Learn scores the 5 doc dims (persona/keyword/hook/landing/CTA); Behavior/Negative-Keyword
are seed libraries, not Learn-scoring dims (ARCH_BASELINE §1.8).

## 5. Adversarial self-review (ultracode) — 0 findings, all dimensions CLEAN

A read-only adversarial review (3 dimensions, 3 agents) found **zero** defects — **no-publish/no-fabricated-origin
CLEAN, learn-precondition-and-review CLEAN, fail-closed/untrusted/PII CLEAN**. I preempted the recurring failure
modes the M6.2E/F/G reviews surfaced: the `record_review_decision` audit detail is machine-safe (no untrusted
free-text reason/audit_ref — the M6.2G finding), fail-closed defaults everywhere (safe range UNKNOWN, no seed →
Learn refuses, non-usable signals excluded), no untrusted-body injection (conditions/state are server-side), and
no publish/execute method exists on any surface. Not a gate sign-off — the runner gate + JUDGE (M6-P1709) decide.

## 6. Rollback

Staged only — baseline rollback = delete the M6.2H tree (M6.2G untouched). Per-item: new files → delete; patched
`config.py` → revert to M6.2G; migrations 0011/0012 → down-DDL DROP (staged; not applied). Review-queue records are
inert + append-only (in-memory); a reject/hold is a new recorded decision, never a published change.

## 7. Scope & governance (unchanged)

In scope built: the six library schemas + SKU-anchored mapping chain (seed-only-from-canon), the ads_learning_candidate
lifecycle + review queue (CTR-014), CTR-020 POST /learning-candidates + owner-review handler. OUT (not built):
auto-publish outside safe range, generating public ad copy / origin content while the lexicon/claim table is MISSING
(M6-OD-007), real ad run / scale / Core-policy override (RULE-013/018), commission (RULE-019). HARD FORWARD GATES:
M6-OD-007 (content) before any real seed content; M6-OD-006 (safe range) before any guarded publish; the M6.2G
before-real-scale/send/auto-publish forward conditions stand. `M6-P1000` + `M6-P1309` verdicts stay BLOCKED (not
converted). Module boundary intact (no M4 consult content, no M5 public reply, no auto-publish). No raw secrets/PII
(audit machine-safe, actor masked, content None). FAIL-006 not tripped (framework never auto-publishes).
