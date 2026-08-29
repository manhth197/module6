# TEST_MANIFEST — Slice M6.2H smoke suite (ADS Strategy Libraries / Learning Engine)

| Field | Value |
|---|---|
| Prompt | M6-P1703 — `M6_2H_TESTER_BUILD` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — the smoke test is AUTHORED here. This attempt ran a **collect-only build-validation** (imports/collects clean, no assertions executed) per the prompt's "Build (do not yet run)"; the **formal executed-results recording** belongs to M6-P1704. |
| Executed by (formal) | M6-P1704 (`M6_2H_TESTER_RUN`) → `04-artifacts/test-reports/M6.2H/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-011** (exactly — per `00-spec/slices/M6.2H.md` "Core smokes" + this prompt's `<smoke_ids>`) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Slice scope | strategy-library framework + learning-engine skeleton (Seed → Run → Learn → Review → Publish, doc §17); six library schemas + SKU-anchored mapping chain; `ads_learning_candidate` lifecycle + review queue (M6-CTR-014); `POST /api/admin/ads/learning-candidates` (M6-CTR-020). Content fill halts at framework (M6-OD-007); no auto-publish |
| Staging root | `04-artifacts/impl/M6.2H/` (STAGED_ONLY; convention reference, not a live repo) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (owner P0 matrix, extract line 411) |

> **Governance (immutable — nothing in this suite flips a flag, and nothing is ever published):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `LEARNING_AUTOPUBLISH_ENABLED=False`,
> `LEARNING_SAFE_RANGE_RATIFIED=False` (M6-OD-006 OPEN → safe range UNKNOWN), `LEARNING_CONTENT_FILL_ENABLED=False`
> (M6-OD-007 OPEN → framework-only), `SCALE_EXECUTION_ENABLED=False`, `SCALE_MODEL_RATIFIED=False`. The machine
> **never fabricates origin strategy** (RULE-011 / LEX-006) and there is **no auto-publish path** (RULE-011 /
> LEX-006 / FAIL-006): a candidate outside/UNKNOWN the safe range is HELD in review and never published; a publish
> is authorized only via an explicit owner APPROVE **and** a WITHIN safe range — never reached in the staged
> posture. The mapping chain is read-only and never writes Core policy (RULE-013 / RULE-018). No pricing (M3),
> consult content (M4), public reply (M5), order-state (M8), CRM send, or commission (RULE-019). `status` is an
> honest self-report; the runner EVIDENCE_GATE and the slice Judge (M6-P1709) decide closure.

## What this suite is

The **official M6.2H smoke suite**: one dedicated smoke file for the bound smoke id, carrying the register's
scenario/expected **verbatim**, driven through the M6.2H learning layer — `LearningEngine.review` (fail-closed
safe-range → HOLD), `record_review_decision` (explicit owner approve/reject/hold), `AdsLearningCandidate`
(`is_publish_authorized` = APPROVED + WITHIN), the append-only `ReviewQueue`, and `guarded_publish_blocked()` —
plus the negative / fail-closed companions and a non-vacuous discriminating control. It reuses the shared fixtures
in [`tests/conftest.py`](04-artifacts/impl/M6.2H/tests/conftest.py) (`learning_engine`, `review_queue`,
`library_store`, `make_candidate`, `make_review_decision`, `make_learning_deps`). No new production code, and **no
fix to the code under test** (TESTER reports defects, never fixes them).

All ids are **synthetic**; no raw secret/PII. The owner-decision `actor` (`owner_ops`) and `sku_ref`
(`SKU_HERO_1`) are synthetic references, masked on export where applicable; no phone / email / customer_id / psid
appears anywhere.

M6.2H **carried the whole M6.2G tree forward** (cumulatively M6.2A–G, byte-identical) and the coder (M6-P1702)
added the learning layer with its own leg tests. The carried smokes and regression suites remain and re-run here
as supporting coverage; the **one file below is the new M6.2H-bound smoke** authored by this prompt.

## Smoke → test binding

| Smoke ID | Doc ID | Test file (M6.2H, new) | Nodes | Primary test (scenario verbatim) | Negative / fail-closed & control tests | Rule(s) | Fail gate | Exit leg |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-011 | ADS-P0-011 | [`tests/smoke/test_smk_011_learning_candidate_outside_safe_range_holds.py`](04-artifacts/impl/M6.2H/tests/smoke/test_smk_011_learning_candidate_outside_safe_range_holds.py) | 6 | `test_smk_011_candidate_outside_safe_range_is_held_not_published` (parametrized over OUTSIDE / UNKNOWN) | `..._neg_within_claim_is_forced_unknown_and_held`, `..._neg_no_auto_publish_method_and_guarded_publish_blocked`, `..._neg_owner_approve_still_not_publishable_while_safe_range_unknown`, `..._control_publish_authorized_is_discriminating_but_unreachable` | M6-RULE-011, M6-RULE-013, M6-RULE-018 | M6-FAIL-006 | L4 |

**New M6.2H smoke nodes: 6.**

---

## M6-SMK-011 — Learning candidate outside safe range → hold review, no publish

Verbatim from `00-spec/registers/SMOKE_REGISTER.md` (extract line 411):

```
Smoke ID:          M6-SMK-011  (Doc ID ADS-P0-011)
Kịch bản:          Learning candidate ngoài safe range
Kết quả phải đạt:  Hold review, không publish
```

- **Primary (parametrized OUTSIDE / UNKNOWN):** a candidate outside (or unknown) the safe range is put through
  `review()` → `review_state` HOLD, `safe_range_status` forced UNKNOWN (fail-closed, M6-OD-006 OPEN),
  `is_publish_authorized` False; the review queue confirms HOLD.
- **Negative — WITHIN claim forced UNKNOWN:** an untrusted `WITHIN` claim cannot bypass the unratified safe range
  — `review()` forces UNKNOWN and HOLDs it.
- **Negative — no auto-publish + guarded publish blocked:** the learning layer exposes no
  `publish/auto_publish/go_live/launch/execute/send` method, `guarded_publish_blocked()` is True, and
  `LEARNING_AUTOPUBLISH_ENABLED` / `LEARNING_SAFE_RANGE_RATIFIED` are False.
- **Negative — owner APPROVE still not publishable:** even a recorded owner APPROVE leaves `is_publish_authorized`
  False because the safe range stays UNKNOWN (M6-OD-006) — no publish.
- **Control (non-vacuous):** a directly-constructed APPROVED + WITHIN candidate WOULD be publish-authorized (the
  property can be True), but `review()` forces UNKNOWN so no reviewed candidate reaches WITHIN — the HOLD is
  caused by the unratified safe range, not a guard that always denies.

---

## Supporting / regression suite (run alongside the bound smoke)

The full staged suite re-runs. Files below (coder M6-P1702) are **not** the bound M6.2H smoke id but pin the
learning layer the smoke relies on.

| File | Purpose | Nodes |
|---|---|---|
| [`tests/test_candidate_outside_safe_range_holds.py`](04-artifacts/impl/M6.2H/tests/test_candidate_outside_safe_range_holds.py) | SMK-011 leg — candidate outside/UNKNOWN safe range → HOLD; guarded publish blocked | 3 |
| [`tests/test_no_auto_publish_review_queue_only.py`](04-artifacts/impl/M6.2H/tests/test_no_auto_publish_review_queue_only.py) | FAIL-006 — no publish method; deps inert; candidate → review queue HELD | 4 |
| [`tests/test_learn_precondition_seed_and_dq.py`](04-artifacts/impl/M6.2H/tests/test_learn_precondition_seed_and_dq.py) | RULE-011 — Learn refuses without seed; consumes only DQ-passed verified signals; scores 5 dims | 3 |
| [`tests/test_libraries_seed_from_canon_only.py`](04-artifacts/impl/M6.2H/tests/test_libraries_seed_from_canon_only.py) | RULE-011 / LEX-006 — six libraries; canonical seed only; fabricated/non-canonical rejected | 15 |
| [`tests/test_content_fill_halts_at_framework.py`](04-artifacts/impl/M6.2H/tests/test_content_fill_halts_at_framework.py) | M6-OD-007 — content fill BLOCKED; entry has seed-source ref, no content | 3 |
| [`tests/test_mapping_chain_anchored_to_sku.py`](04-artifacts/impl/M6.2H/tests/test_mapping_chain_anchored_to_sku.py) | LEX-005 / RULE-013/018 — SKU→…→Verified-Revenue chain, anchored to a sellable SKU; no Core-write | 4 |
| carried M6.2A–G suite | seam/tracking/outbox/integration/attribution/dashboard/DQ/scale smokes + all unit + regression suites | 313 |

## Fixtures reused (from `tests/conftest.py`)

| Fixture | Role |
|---|---|
| `library_store` | `StrategyLibraryStore` — canonical-only `seed`; rejects fabricated/non-canonical origin |
| `review_queue` | inert append-only `ReviewQueue` (`enqueue` / `get` / `update`) |
| `learning_engine` | `LearningEngine(library_store, review_queue, audit)` — `seed`/`run`/`learn`/`review`/`record_review_decision`; `guarded_publish_blocked()`; NO publish method |
| `make_candidate(candidate_id, *, target_dim=, kind=, score=, sku_ref=, **over)` | `AdsLearningCandidate` factory |
| `make_review_decision(state="APPROVED", **over)` | `OwnerReviewDecision` factory (actor `owner_ops`) |
| `make_learning_deps()` | `LearningDeps(engine, audit)` — inert; no publisher/transport |

## Boundary / safety asserted by the suite

- **No auto-publish (RULE-011, LEX-006, FAIL-006):** the engine / queue / store expose no
  publish/auto-publish/go-live/execute/send method; `guarded_publish_blocked()` is True; a candidate outside the
  safe range is HELD.
- **Fail-closed safe range (M6-OD-006):** `review()` forces UNKNOWN while the safe range is unratified; even an
  owner APPROVE never yields `is_publish_authorized` True in the staged posture.
- **No fabricated origin (RULE-011, LEX-006):** exercised via the supporting `test_libraries_seed_from_canon_only.py`
  / `test_content_fill_halts_at_framework.py` (canonical seed only; content None while M6-OD-007 OPEN).
- **No Core write (RULE-013/018), no commission (RULE-019), no pricing (M3), no consult (M4), no public reply
  (M5), no flag flip, no external call, no `04-artifacts/state/` write** anywhere in the suite. Actor masked; no
  raw PII.

## Build-validation performed in M6-P1703 (attempt 1, collect-only — "do not yet run")

Per the prompt's `<task>` ("Build (do not yet run)"), this attempt ran **collect-only** (imports + collects; **no
assertions executed**). Run with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest 8.4.2**, from
`04-artifacts/impl/M6.2H/`, **no shell redirection** (the role guard blocks a `>`/`2>` co-occurring with the venv
`Scripts` path), cache-free (`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```bash
python.exe -m pytest tests/smoke/test_smk_011_learning_candidate_outside_safe_range_holds.py --collect-only -q -p no:cacheprovider   # 6 nodes ; EXIT=0
python.exe -c "<in-process pytest_collection_finish tally>" --collect-only   # COLLECTED_TOTAL=351 ; EXIT=0
```

Reconciliation: **351** collected = carried M6.2H baseline **345** (313 carried M6.2G tree + 32 coder M6.2H
learning leg tests) + this new smoke **6**. The file imports + collects clean (learning fixtures wired). A
read-only adversarial static verification (a verifier tracing every assertion through the implementation +
a completeness critic) was run alongside — findings are recorded in the M6-P1703 evidence.

> **On counting.** In this harness pytest's terminal summary line is not captured for a long run, so the total
> (**351**) was obtained via an in-process `pytest_collection_finish` tally (`len(session.items)`) with pytest
> RC=0 and the `--collect-only` per-file sum agreeing.

Cache hygiene: `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

> **This build does NOT self-certify gate advancement.** Collect-only proves the smoke file imports + collects
> against the frozen M6.2H code; it does not execute assertions. The **formal executed-results recording** is
> produced by **M6-P1704** into `04-artifacts/test-reports/M6.2H/SMOKE_RESULTS.md`. The runner EVIDENCE_GATE and
> the slice Judge decide closure.

## Execution plan for M6-P1704 (`M6_2H_TESTER_RUN`)

Run the full staged suite and the bound smoke, then record structured results + evidence refs for the M6.2H
exit-gate smoke leg L4 (SMK-011):

```bash
python -m pytest -q                    # full staged suite: expected 351 passed
python -m pytest -q tests/smoke/test_smk_011_learning_candidate_outside_safe_range_holds.py   # expected 6 passed
```

## Exit-gate legs (slice M6.2H done-gate, itemized)

| Leg | Requirement | Covered by |
|---|---|---|
| L1 | Seed framework pass (six libraries, seed-source constraints, machine never fabricates origin) | `test_libraries_seed_from_canon_only.py`, `test_content_fill_halts_at_framework.py`, `test_mapping_chain_anchored_to_sku.py` |
| L2 | No auto-publish (candidates → review queue only; publish requires owner approval / guarded safe range, BLOCKED) | SMK-011 + `test_no_auto_publish_review_queue_only.py` |
| L3 | Learning-input precondition (Learn only after canonical seed + only DQ-passed verified signals) | `test_learn_precondition_seed_and_dq.py` |
| L4 | Smoke M6-SMK-011 executed with recorded result | closed by M6-P1704 (built here) |

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-011 | Learning is guarded: the machine never fabricates origin strategy and never auto-publishes; candidates are held for review (SMK-011). |
| M6-RULE-013 | The mapping chain reads Core references only; it never writes Core policy (supporting `test_mapping_chain_anchored_to_sku.py`). |
| M6-RULE-018 | Module 6 records/consumes boundaries it does not own; it never validates or overrides them (mapping read-only). |
| M6-LEX-006 | Machine never fabricates origin strategy (the doc's FORBIDDEN cell) — canonical seed only, content None while M6-OD-007 OPEN. |
| M6-FAIL-006 | Auto-publish / acting without owner approval — the framework never auto-publishes (SMK-011 + `test_no_auto_publish_review_queue_only.py`). |

## Provenance / notes

- Scenario & expected text quoted **verbatim** from `00-spec/registers/SMOKE_REGISTER.md` (row M6-SMK-011; extract
  line 411). Test patterns reused from the existing `tests/conftest.py` learning fixtures and the coder's
  `tests/test_candidate_outside_safe_range_holds.py`, `tests/test_no_auto_publish_review_queue_only.py` (doc
  working mode, extract line 466).
- No self-certification of PASS or of gate/leg advancement: the runner EVIDENCE_GATE and the slice Judge decide.
  This manifest and the smoke file are the *build*; the formal executed results are produced in M6-P1704.
