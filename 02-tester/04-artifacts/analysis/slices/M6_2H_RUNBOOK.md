# M6.2H — Slice Runbook — ADS Strategy Libraries & Learning-Engine skeleton

| Field | Value |
|---|---|
| Slice | **M6.2H — ADS Strategy Libraries** (strategy-library framework + learning-engine skeleton; **framework-only by design**) |
| Written by | **M6-P1708** — `M6_2H_DOCS` (ANALYST_ARCHITECT, `analysis_only`) |
| ADS phase | **Phase 1** (per the slice spec) — the *learning* slice, first after the M6.2G Scale-Gate re-gate |
| Depends on | M6.2G (Scale Gate; slice gate M6-P1609 SIGNED) |
| Doc source | doc §17 (Seed → Run → Learn → Review → Publish; the six libraries + mapping chain; extract 336–353) |
| Done gate (slice spec) | **Seed framework pass · no auto-publish** |
| Objective | Build the six strategy-library framework + the learning-engine skeleton. **Content fill halts at framework while M6-OD-007 is unresolved.** The slice proves capability with evidence; it flips no flag, fabricates no origin strategy, and publishes nothing. |

> **Read this first — what "framework-only" means, and what "clean" does not mean.** The band is clean: entry gate
> a real Judge PASS (M6-P1700 `SIGNED`), all seven band prompts self-report PASS, the in-scope fail gate
> **M6-FAIL-006 (auto-publish) held**, and the coder's own 3-dimension adversarial self-review returned **zero
> findings**. But "clean" here does **not** mean "the learning engine is ready to learn/publish". By design this
> slice is **framework-only**: content-fill **halts at framework** because **M6-OD-007** (content fill) is OPEN
> (`LEARNING_CONTENT_FILL_ENABLED=False` — libraries carry a canonical seed-*source* reference but **no** machine
> content), and the guarded-publish path stays **BLOCKED** because **M6-OD-006** (safe range) is OPEN
> (`LEARNING_SAFE_RANGE_RATIFIED=False` — review forces safe-range `UNKNOWN` → HELD). Both are the *designed*
> fail-closed posture, not defects. Exit legs 1/2/3 are **SUPPORTED at the staged level** (the tester marks them
> "met" and FAIL-006 is not tripped), **not** independently closed — the F-LEARN-1..4 / ACCESS-1 residuals remain
> (armed-not-fired), so final closure is the slice-gate Judge's (M6-P1709). **A standout positive:** the learning
> stage consumes only Data-Quality-passed verified normalized signals, **never raw channel text — so there is no
> prompt-injection surface** (see §5.2). Posture is immutable: `global_gateway_state=BLOCKED`,
> `production_flag=OFF`, `external_send=OFF`, the three learning chokes False, and all M6.2A–G flags False;
> `live_migrations=false`; `M6-P1000` and `M6-P1309` verdicts **remain BLOCKED (not converted)**. This runbook
> advances no gate and self-certifies nothing; the runner EVIDENCE_GATE and the slice-gate Judge (M6-P1709) decide.

---

## 1. What this slice built (staged under `04-artifacts/impl/M6.2H/`)

Everything is **staged** (convention-reference tree, never a live repo). The whole M6.2G tree is carried forward
byte-identical; M6.2H **adds** the learning layer and three config choke flags. **Nothing acts** — no code
auto-publishes, generates content/ad copy, fabricates origin strategy, applies a migration, or flips a flag.

### 1.1 The learning layer (new `app/measurement/learning/`)

| File | What it is | Contract / Rule |
|---|---|---|
| `learning/libraries.py` | The **six libraries** (Persona / Behavior / Keyword / Negative-Keyword / Creative-Hook / Landing-CTA) with the doc §17 purpose + `CANONICAL_SEED_SOURCES` per kind. `StrategyLibraryStore.seed()` **rejects** a missing/non-canonical seed source **and rejects any machine-generated `content`** while `LEARNING_CONTENT_FILL_ENABLED=False` (framework-only). **The machine never fabricates origin strategy.** | CTR-014-adj; RULE-011/018; LEX-006 |
| `learning/mapping.py` | `StrategyMapping` — the doc §17 chain `SKU/Product line → Persona → Behavior → Keyword → Creative Hook → Landing → CTA → Event → Verified Revenue`; every mapping anchored to a **sellable SKU** (LEX-005, enforced in `__post_init__`); read-only refs, never writes Core policy. | CTR-014; RULE-013/018 |
| `learning/candidate.py` | `AdsLearningCandidate` (CTR-014, **inert**) + `LearningCandidateKind` + `TargetDim` (the 5 Learn dims) + `ReviewState` (`CANDIDATE/IN_REVIEW/APPROVED/REJECTED/HOLD`) + `SafeRangeStatus` (`WITHIN/OUTSIDE/UNKNOWN`) + `OwnerReviewDecision`. `is_publish_authorized` requires `APPROVED` **and** safe-range `WITHIN` → **always False in staged posture** (safe range is forced UNKNOWN while M6-OD-006 is open). `actor` masked on export. | CTR-014 |
| `learning/review_queue.py` | Inert append-only queue (candidates + review history). A candidate outside/UNKNOWN safe range → HOLD. No publish/send method. | CTR-014/020 |
| `learning/learning_engine.py` | The **5-stage skeleton**: `seed()` (canonical-only), `run()` (records a SKU-anchored active mapping; nothing runs), `learn()` (**precondition: a canonical seed exists AND consumes only DQ-passed verified signals**; scores the 5 doc dims), `review()` (candidate → queue; not-WITHIN → HOLD, SMK-011), `record_review_decision()` (explicit owner approve/reject/hold; machine-safe audit). **No publish/auto-publish method**; `guarded_publish_blocked()` reports True. | CTR-014; RULE-011; LEX-006 |
| `api/learning_candidates.py` | **CTR-020 `POST /api/admin/ads/learning-candidates`**: `handle_learning_candidate_create` (→ review queue, inert) + `handle_learning_review_decision` (record owner approve/reject/hold). `LearningDeps` holds only the inert engine + audit — **no publisher/Transport/auto-publish handle**. Untrusted body = DATA (RULE-H03); the candidate is built server-side; owner decision requires **all** of actor/reason/audit/evidence (RULE-015). **Never publishes.** | CTR-020; RULE-011/FAIL-006 |

### 1.2 The six libraries + canonical seed sources (doc §17, extract 338–345)

| # | Library | Purpose (doc §17) | Canonical seed source (required) |
|---|---|---|---|
| 1 | **Persona** | Nhóm khách mục tiêu | Content Block 20 SKU, customer context, CRM lifecycle |
| 2 | **Behavior** | Hành vi số và hành vi mua | Web/Messenger/Live/CRM events **đã pass data quality** |
| 3 | **Keyword** | Từ khóa acquisition/intent | Content Block, product public view, search/ads history |
| 4 | **Negative Keyword** | Chặn tệp/ý định không phù hợp | Spam/troll/low-intent/fake-order signals |
| 5 | **Creative Hook** | Hook không sale sốc, đúng brand, đúng claim | Product effectiveness, Meta-safe wording, Golden Hour Tri Ân |
| 6 | **Landing / CTA** | Mapping landing và CTA theo intent | Hero SKU, Golden Hour, Diamond, CRM/reorder |

**Seed-only-from-canon (RULE-011 / LEX-006 forbidden cell):** an entry without a canonical seed source, or a
machine-fabricated origin strategy, is **rejected**. The Learn stage scores the **5 doc dims**
(persona / keyword / hook / landing / CTA, doc §17 L351); Behavior and Negative-Keyword are seed libraries
(framework) but not doc-mandated Learn-scoring dims.

### 1.3 The 5-stage lifecycle (doc §17, extract 347–353) — staged enforcement

| Stage | Staged enforcement |
|---|---|
| **Seed** | Canonical seed-source required; content fill BLOCKED (M6-OD-007) → framework-only, no fabricated origin. |
| **Run** | Skeleton: records an active mapping per sellable SKU; **nothing actually runs** (staged). |
| **Learn** | Runs **only** after a canonical seed exists **and** consumes **only** DQ-passed verified signals (RULE-011); scores the 5 dims. |
| **Review** | Candidate → review queue; owner/marketing approve/reject/hold; a candidate outside/UNKNOWN safe range → HOLD (SMK-011). |
| **Publish** | **BLOCKED** (M6-OD-006 safe range OPEN → safe-range UNKNOWN); **no auto-publish path**; owner-approval-only, with rollback + audit (framework). |

### 1.4 Staged migrations & config

- `migrations/0011_create_ads_strategy_libraries.sql` — the six libraries (`seed_source NOT NULL`, `content NULL` while M6-OD-007) + the SKU-anchored mapping; comment: no content generation, no trigger. Staged, **never applied**.
- `migrations/0012_create_ads_learning_candidate.sql` — CTR-014 inert candidate (kind/target_dim/score/sku_ref/review_state/safe_range_status); CHECK enums; comment: **no trigger/auto-publish path**. Staged, **never applied**.
- `app/config.py` — adds three fail-closed learning chokes, **none an enabling flag, none read to act**:
  `LEARNING_AUTOPUBLISH_ENABLED = False` (no auto-publish path — RULE-011/LEX-006/FAIL-006),
  `LEARNING_CONTENT_FILL_ENABLED = False` (M6-OD-007 → framework-only),
  `LEARNING_SAFE_RANGE_RATIFIED = False` (M6-OD-006 → guarded publish BLOCKED, safe range UNKNOWN).

### 1.5 Coder adversarial self-review — 0 findings (but not "0 residuals")

The coder's own 3-dimension self-review (M6-P1702 §5) returned **zero** defects — it **preempted** the recurring
failure modes the M6.2E/F/G reviews surfaced (machine-safe audit detail, fail-closed defaults, no untrusted-body
injection, structural absence of any publish/execute path). This is a genuine step up. **But a clean self-review is
not a clean slate:** the independent boundary (M6-P1705) and security (M6-P1706) passes still surfaced the
**F-LEARN-1..4 / ACCESS-1 / F-LEARN-PII-1** residuals below (all armed-not-fired). "Zero self-review findings" means
the coder anticipated the known classes, not that nothing remains for the M6-OD-011 binding.

---

## 2. Operate

M6.2H is a **framework-only, never-publish** workflow. There is no "publish an optimization" step — by design. What
an operator/owner can do at the staged level (and what stays impossible):

1. **Seed a library** — only from a canonical source; a non-canonical source or any machine content is rejected
   (content fill BLOCKED, M6-OD-007). Libraries carry seed-*source* references + framework structure, never
   machine-generated persona/keyword/hook/copy.
2. **Learn** — runs only after a canonical seed exists and consumes only DQ-passed verified signals; returns a
   plain score dict. There is **no** learn→publish bridge.
3. **Create a candidate + record an owner review** — `POST /api/admin/ads/learning-candidates` builds a candidate
   server-side (a malicious body claiming `APPROVED`/`WITHIN` is ignored), enqueues it for review, and records an
   explicit owner approve/reject/hold. **A recorded APPROVE authorizes nothing** — review forces safe-range UNKNOWN,
   so `is_publish_authorized` stays False.
4. **What is structurally impossible here** — auto-publishing, generating origin content, running a real ad,
   self-approving, or having a request body fake a state. There is no publisher, executor, or content generator
   anywhere in the slice (see §3).

> **Owner-facing caveat (do not skip).** A review APPROVE recorded through this endpoint is the **human
> authorization a future (owner-performed, outside-M6) publish would rely on**. Before that can mean anything real,
> the forward gates in §5 must close — most importantly **ACCESS-1** (the endpoint must authenticate that the caller
> *is* the reviewer; today `actor` is taken from the request body), **F-LEARN-1** (the M6-OD-011 binding must never
> auto-wire the review queue to a publisher), and the two owner decisions **M6-OD-006** (safe range) / **M6-OD-007**
> (content).

---

## 3. Verify

**Verify env:** `02-tester/.venv` — python **3.12.13**, pytest **8.4.2**, pluggy 1.6.0 (matches the
`IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin). Run from `04-artifacts/impl/M6.2H/` (STAGED_ONLY), cache-free.

### 3.1 Bound smoke

| Smoke ID | Doc ID | Scenario → Expected (verbatim, SMOKE_REGISTER) | Test file | Result |
|---|---|---|---|---|
| **M6-SMK-011** | ADS-P0-011 | `Learning candidate ngoài safe range` → `Hold review, không publish` | `tests/smoke/test_smk_011_learning_candidate_outside_safe_range_holds.py` | **PASS 6/6** |

The 6 nodes cover: OUTSIDE → HOLD; UNKNOWN → HOLD; an untrusted `WITHIN` claim forced UNKNOWN and HELD; no
auto-publish method + `guarded_publish_blocked()` True; a recorded owner APPROVE still not publishable (safe range
UNKNOWN); and the discriminating-but-unreachable control (a directly-constructed `APPROVED+WITHIN` would be
publish-authorized, but `review()` forces UNKNOWN so no reviewed candidate reaches WITHIN).

```bash
# from 04-artifacts/impl/M6.2H/  (venv: 02-tester/.venv, python 3.12.13)
python -m pytest -v tests/smoke/test_smk_011_learning_candidate_outside_safe_range_holds.py -p no:cacheprovider
# -> 6 passed ; exit 0
```

### 3.2 Full staged suite

**351 passed, 0 failed, 0 skipped, 0 error — RC 0.**
Breakdown: **313 carried-forward** (M6.2A–G) **+ 38 new M6.2H nodes** (32 learning-leg + 6 bound smoke).

> **Test-count reconciliation (be precise).** The **tester-run final is 351** (M6-P1704 / SMOKE_RESULTS.md). The
> coder note (M6-P1702) records **345** = 313 carried + the **32 learning-leg tests it authored**; the **6 bound
> smoke** nodes (SMK-011) were authored by the **TESTER** in M6-P1703 and run in M6-P1704, so the tester-run final
> adds them (345 + 6 = 351). Per test-count discipline this runbook cites the **tester-run final 351**, not the
> coder intermediate 345 — both are internally consistent, they count different authoring stages.

The 32 learning-leg tests (supporting coverage, all green inside the 351): `test_libraries_seed_from_canon_only.py`
(15), `test_content_fill_halts_at_framework.py` (3), `test_mapping_chain_anchored_to_sku.py` (4),
`test_no_auto_publish_review_queue_only.py` (4), `test_candidate_outside_safe_range_holds.py` (3),
`test_learn_precondition_seed_and_dq.py` (3).

### 3.3 FAIL-006 (auto-publish) — NOT tripped (boundary + security, layered executed reasons)

The boundary adversary (M6-P1705) executed **29 outcomes** (DEFENDED 24, OPEN_NONGATE 4, NOTE 1, **FAIL-006
breaches 0**); the security review (M6-P1706) concurred from the code side and reported a **clean** PII/secret scan
over **171 files**. FAIL-006 holds for layered, executed reasons:

1. **No publish executor exists.** `LearningEngine` exposes only `seed/run/learn/review/record_review_decision/
   guarded_publish_blocked/active_mappings`; the `ReviewQueue` only `enqueue/update/get/all/history`; no
   publish/auto_publish/go_live/launch/execute/send/dispatch attribute anywhere; a token sweep finds **0** action
   defs and **0** posture-flag writes.
2. **`is_publish_authorized` has zero real consumers.** It is read by nothing outside its own definition; the
   learning package is not imported by the outbox/scale layers; a forged `APPROVED+WITHIN` record produces **0**
   publish audit lines.
3. **Review is fail-closed.** `review()` forces `safe_range_status` UNKNOWN while M6-OD-006 is OPEN → HELD unless
   WITHIN, and it can never be WITHIN while the flag is False; an untrusted WITHIN claim is forced UNKNOWN; even a
   recorded owner APPROVE leaves `is_publish_authorized` False.
4. **Config flips don't reach an executor.** Flipping both `LEARNING_SAFE_RANGE_RATIFIED` and
   `LEARNING_AUTOPUBLISH_ENABLED` True can make the authorization *property* True for a WITHIN+APPROVED candidate —
   **but there is still no publish method**, so nothing publishes.
5. **No learn→publish bridge.** `learn()` returns a plain `Dict[TargetDim,float]`; a top-scoring (0.99) learned
   score routed through review+approve is still not publishable.
6. **Body can't fake it.** A malicious create body (`review_state=APPROVED`, `safe_range_status=WITHIN`, …) is
   ignored — the candidate is built server-side and HELD.

---

## 4. Rollback (every change this slice made) — *acceptance check 1*

Everything is **staged** ⇒ rollback is non-destructive. Nothing is live, nothing publishes, no migration was applied.

| Change | Rollback |
|---|---|
| **Baseline (all M6.2H)** | Delete the `04-artifacts/impl/M6.2H/` tree. M6.2G is untouched (carried forward byte-identical). |
| `learning/__init__.py`, `libraries.py`, `mapping.py`, `candidate.py`, `review_queue.py`, `learning_engine.py` (new) | Delete the files. |
| `api/learning_candidates.py` (new) | Delete the file. |
| `app/config.py` (patched: `+LEARNING_AUTOPUBLISH_ENABLED / +LEARNING_CONTENT_FILL_ENABLED / +LEARNING_SAFE_RANGE_RATIFIED`, all False) | Revert to the M6.2G version. |
| `migrations/0011_create_ads_strategy_libraries.sql` (new, staged, never applied) | `down`-DDL `DROP` the six-library + mapping tables; delete the file. |
| `migrations/0012_create_ads_learning_candidate.sql` (new, staged, never applied) | `down`-DDL `DROP TABLE ads_learning_candidate`; delete the file. |
| New tests (6 learning-leg files + 1 bound smoke file) | Delete the files. |
| Review-queue records (in-memory, inert, append-only) | A reject/hold is a **new recorded decision**, never a published change; discard the in-memory queue. |

There is **no** production/state/flag change to reverse: `analysis_only` here, and every upstream band prompt ran
read-only or staged-only. Rollback of the whole slice = delete the tree.

---

## 5. Decision deltas & governance

### 5.1 Two OPEN owner decisions scope this slice — both fail-closed (the objective's designed halt)

- **M6-OD-007 (content fill) OPEN → the framework halts at framework.** `LEARNING_CONTENT_FILL_ENABLED=False`:
  libraries carry a canonical seed-*source* reference but **no** machine-generated content. The machine never
  fabricates origin strategy (RULE-011 / LEX-006). **Resolve M6-OD-007 (and provide the lexicon/claim table) before
  any real seed content.**
- **M6-OD-006 (safe range) OPEN → guarded publish is BLOCKED.** `LEARNING_SAFE_RANGE_RATIFIED=False`: `review()`
  forces safe-range UNKNOWN → every candidate is HELD; the only publish path is explicit owner/marketing approval,
  and even that authorizes nothing while the safe range is unratified. **Resolve M6-OD-006 before any guarded
  publish.**

These are the *designed* posture, not defects — the slice proves the framework capability with evidence and fills
no content and publishes nothing.

### 5.2 Positive: no prompt-injection surface (a real architectural strength for a learning slice)

A "learning" slice is exactly where feeding untrusted channel text into a model would be catastrophic. This design
structurally avoids it: `learn()` consumes **only `VerifiedSignal` normalized effectiveness scores that passed the
Data Quality Gate (`dq==PASS`) and are verified — never raw comment / Messenger / ad-copy text**. Channel-origin
text is neither ingested nor interpreted here, and machine content fill is BLOCKED (M6-OD-007). The security review
(M6-P1706) independently confirmed **no prompt-injection / untrusted-content surface**. Credited as a designed
property, not luck.

### 5.3 Learning-layer residuals (armed-not-fired; none trips FAIL-006) — routed to CODER / M6-OD-011

| ID | Sev | What | Route / fix |
|---|---|---|---|
| **ACCESS-1** | **load-bearing forward** | The review-decision handler takes **`actor` from the request body**; no authentication that the caller *is* the owner/marketing reviewer. Inert today (an APPROVE authorizes nothing), but at the M6-OD-011 HTTP binding this is the load-bearing authz — a review APPROVE is the human authorization a future publish relies on. | Owner / M6-OD-011: authenticate the caller, authorize APPROVE to the reviewer role only, bind `OwnerReviewDecision.actor` to the **authenticated identity** — never a body-supplied string. |
| **F-LEARN-1** | in-process (cross-ref) | `ReviewQueue.update()` is a second, unguarded write path (validates only `candidate_id` existence), so an in-process caller can swap a forged `APPROVED+WITHIN` record in, defeating `review()`'s UNKNOWN-forcing. The **M6.2H analog of the M6.2G store-laundering finding (F-SCALE-2)**. Not wire-exposed (the API never calls `update()`); inert. | CODER + M6-OD-011: `update()` must reject illegal transitions / re-force UNKNOWN; the binding must **never auto-wire the review queue to a publisher**. |
| **F-LEARN-2** | MINOR | The create handler under-validates `score`: NaN/inf pass `isinstance(float)`, and `score=10**400` makes `float(score)` raise an **unhandled `OverflowError`** — the untrusted admin body escapes the handler's own `REJECTED_INPUT` fail-closed contract (500-shaped crash). Not FAIL-006 (score never gates publish). | CODER: reject non-finite + bound magnitude + wrap `float()` fail-closed. |
| **F-LEARN-3** | MINOR | `review()` re-derives `review_state` (discards a forged APPROVED — good) but does **not** scrub the incoming `decision`, so a forged `OwnerReviewDecision` can ride onto a CANDIDATE record (inert; visible via `to_public`). | CODER: reset `decision=None` on review. |
| **F-LEARN-4** | MINOR | `StrategyMapping` anchors on **truthiness only** (a monetary value / Core object / policy token passes as the sellable SKU; `verified_revenue_ref` accepts a literal value despite its "never a value" contract). **But `run()` writes no Core value → RULE-013 holds in effect**; input-validation gap only. | CODER: validate `sku_ref` against a sellable-SKU set + reject value-shaped `verified_revenue_ref`. |
| **F-LEARN-PII-1** | Observation (evidence index rates MINOR) | `OwnerReviewDecision.to_public()` echoes owner free-text (`reason`/`audit_ref`/`evidence_ref`) unmasked on export (excluded from the audit per the D5 fix; contract-non-PII; no leak today). Same class as M6.2G F-SCALE-PII-1. | CODER + M6-OD-012: document the field contract / bound / mask on the export surface. |
| **N-1 / N-2** | Note | **N-1**: frozen-candidate `object.__setattr__` forge — requires in-process code exec, publishes nothing. **N-2**: the no-auto-publish denylist test omits `run/activate/promote/deploy` and leaves the inert public `run` + `active_mappings` uncovered — a future edit making `run()` do real work would pass the guard. | Defense-in-depth: harden the denylist / add a CI guard asserting `is_publish_authorized` and `run` reach no send path. |

### 5.4 Forward gates (new this slice + inherited from M6.2G)

None blocks this framework-only slice; **all bind before any real seed content, guarded publish, scale, or external send.**

- **New (M6.2H):** **M6-OD-007** (content fill) before any real seed content; **M6-OD-006** (safe range) before any
  guarded publish; **ACCESS-1** reviewer authN + **F-LEARN-1** never-auto-wire-queue-to-publisher at the M6-OD-011 binding.
- **Inherited (M6.2G, still in force):** the **four attestation true-ups**; **ENTRY-001/003** real-scale
  conditions (real-VNPAY e2e + the unmerged `@a3aad246` branch; egress wiring + M6-OD-003/004); **ENTRY-004** M5
  DEBT-1..4 + the mandatory adversarial P4 re-gate; **M6-OD-002/005**; the M6.2G **F-SCALE-*** scale-boundary
  residuals; and ACCESS-1 + the store/queue-laundering fixes at the M6-OD-011 binding. The mandatory M6.2G
  Scale-Gate re-gate stands before any real scale/publish/external send.

### 5.5 Immutable posture (intact across M6.2A–H)

`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, the three learning chokes
(`LEARNING_AUTOPUBLISH_ENABLED` / `LEARNING_CONTENT_FILL_ENABLED` / `LEARNING_SAFE_RANGE_RATIFIED`) and all M6.2A–G
flags remain **False**; `live_migrations=false`. `M6-P1000` + `M6-P1309` verdicts remain **BLOCKED (not
converted)**. FAIL-006 not tripped; nothing is published, scaled, or sent; no origin strategy is fabricated.

---

## 6. Changelog delta — *acceptance check 2*

- **No new `SCHEMA_CHANGELOG` row is appended by this slice.** This is an `analysis_only` docs prompt (the analyst
  is denied write to `00-spec/registers/` anyway), and the slice introduces **no canon schema change** to the owner
  document.
- **Contracts CTR-014 / CTR-020 remain `MISSING / OWNER_DECISION_REQUIRED` in the canon `CONTRACT_REGISTER`.** Their
  approved schemas are **staged** (harmonization producers **M6-P0710 / M6-P0712 = PASS**, harmonization gate
  **M6-P0715 = SIGNED**), so they are **satisfied-for-entry**. Per **SCHEMA_CHANGELOG row 18 (CANON-03)**, a
  still-`MISSING` row means "**not yet applied to canon**", not "no approved schema exists"; the canon-flip is
  **deferred, non-blocking operator housekeeping** at each slice's own entry.
- **Concrete artifacts this slice added** (staged, not canon): the `app/measurement/learning/` package, the
  `app/api/learning_candidates.py` endpoint, migrations **0011**/**0012** (staged DDL, **never applied**), and the
  **three fail-closed learning choke flags**.
- **Governance-marker delta:** `LEARNING_AUTOPUBLISH_ENABLED=False`, `LEARNING_CONTENT_FILL_ENABLED=False`
  (M6-OD-007), `LEARNING_SAFE_RANGE_RATIFIED=False` (M6-OD-006) join the immutable posture chain. No enabling value
  written anywhere.

---

## 7. Handoff

- **What this slice is.** The first slice after the M6.2G Scale-Gate re-gate — the ADS Strategy Libraries + the
  learning-engine skeleton (Seed → Run → Learn → Review → Publish), **still ADS Phase 1 per the slice spec**. It is
  framework-only: it fabricates no content and publishes nothing.
- **Exit-gate state at this docs step** (from the evidence index §4, carried faithfully):
  - Items **4 and 7 = MET** (SMK-011 6/6; rollback documented per item).
  - Items **1, 2, 3 = SUPPORTED (staged)** — the tester marks legs L1/L2/L3 "met" and FAIL-006 is not tripped, but
    the F-LEARN-1..4 / ACCESS-1 residuals remain (armed-not-fired), so **final closure is the slice-gate Judge's call**.
  - Item **5** (all slice prompts have evidence JSON) closes when **M6-P1708** (this docs prompt) and **M6-P1709**
    (Judge) produce their evidence — after this prompt, only **M6-P1709.json** is outstanding.
  - Item **6** (slice-gate Judge PASS sign-off) closes only at **M6-P1709**.
- **Next slice.** After the M6.2H slice-gate Judge (M6-P1709), the next prompt is the **M6.2I entry-gate Judge
  (M6-P1800)** (ledger row 158; its entry evidence includes ENTRY-002).
- **Operator TODO before any durable binding / real learning work:** wire the M6-OD-011 binding with **ACCESS-1**
  reviewer authN and **F-LEARN-1** (never auto-wire the queue to a publisher; `update()` rejects illegal transitions).
- **Owner TODO:** **M6-OD-006** (safe range), **M6-OD-007** (content fill), **M6-OD-012** (owner free-text masking,
  F-LEARN-PII-1) — plus the inherited M6.2G chain (M6-OD-002/003/004/005, the four attestation true-ups, the ENTRY
  forward conditions).
- **CODER TODO:** F-LEARN-1 (queue transition validation), F-LEARN-2 (reject non-finite / bound / wrap `float()`),
  F-LEARN-3 (scrub `decision` on review), F-LEARN-4 (validate `sku_ref` / reject value-shaped
  `verified_revenue_ref`), F-LEARN-PII-1 (document/mask owner free-text on export); harden the no-auto-publish
  denylist / add a CI guard (N-2).

---

## 8. Pointers for the slice-gate Judge (M6-P1709)

The Judge renders the slice verdict **strictly from the evidence files** (this runbook is descriptive, not a
verdict). Suggested reading order:

1. `00-spec/slices/M6.2H.md` "Exit gate checks" — the 7 items.
2. For legs 1–4 + 7, read the primary evidence directly (do **not** rely on this runbook or the index):
   `04-artifacts/test-reports/M6.2H/SMOKE_RESULTS.md`, `04-artifacts/boundary-reports/M6.2H_boundary.md`,
   `04-artifacts/security-reports/M6.2H_security.md`, `04-artifacts/impl/M6.2H/PLAN.md` +
   `IMPLEMENTATION_NOTES.md` §6 + migrations `0011`/`0012` down-DDL.
3. **Confirm the framework-only fail-closed posture is faithful:** content-fill halts at framework (M6-OD-007) and
   guarded publish is BLOCKED (M6-OD-006), both fail-closed — the slice proves capability and fills/publishes
   nothing, and **FAIL-006 is not tripped**.
4. **Confirm the residuals are armed-not-fired and correctly routed** (§5.3): none trips FAIL-006; ACCESS-1 +
   F-LEARN-1 are the load-bearing forward items at the M6-OD-011 binding; and the **no-prompt-injection-surface**
   positive (§5.2) is independently confirmed by the security review.
5. **Confirm items 5 & 6** by re-reading the ledger and `04-artifacts/evidence/judge/` (the M6-P1709 sign-off is
   the Judge's own output).
6. Treat the **B6 forward gates (§5.4)** — the two new M6.2H owner decisions plus the inherited M6.2G chain — and
   the standing **BLOCKED `M6-P1000` / `M6-P1309`** verdicts as the conditions before any real content, publish,
   scale, or external send — none of which this framework-only slice satisfies or claims to.

*This runbook advances no gate and self-certifies nothing. The runner EVIDENCE_GATE and the slice-gate Judge
(M6-P1709) decide closure. `global_gateway_state=BLOCKED`, `production_flag=OFF`; the learning engine never
auto-publishes and never fabricates origin strategy.*
