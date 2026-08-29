# M6.2H — Slice Evidence Index

| Field | Value |
|---|---|
| Slice | **M6.2H** — ADS Strategy Libraries (strategy-library framework + learning-engine skeleton; **framework-only**) |
| Assembled by | **M6-P1707** — `M6_2H_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, analysis_only) |
| Assembled on | 2026-08-28 (UTC) |
| Purpose | Index every band's evidence file / artifact / test report / boundary+security report, mapped to the slice exit-gate checklist, and list unresolved blockers — for the slice-gate Judge (M6-P1709). |
| Governance (immutable) | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `LEARNING_AUTOPUBLISH_ENABLED=False`, `LEARNING_CONTENT_FILL_ENABLED=False` (M6-OD-007), `LEARNING_SAFE_RANGE_RATIFIED=False` (M6-OD-006), + all M6.2A–G flags. This index flips nothing and self-certifies nothing; **the learning engine never auto-publishes and never fabricates origin strategy.** |

> **Altitude note (read first).** This is an **index of collected evidence**, not a verdict. The band is clean —
> entry gate a real Judge PASS (M6-P1700 `SIGNED`), **all seven band prompts self-report PASS**, and the in-scope
> fail gate **M6-FAIL-006 (auto-publish) held** (no publish executor; `is_publish_authorized` has **zero** real
> consumers; the learning package is not wired to any sender). By design this slice is **framework-only**:
> content-fill **halts at framework** because **M6-OD-007** (content fill) is unresolved, and the guarded-publish
> safe range stays BLOCKED because **M6-OD-006** (safe range) is unresolved — both fail-closed. A notable positive:
> the learning stage consumes only DQ-passed verified signals, **never raw channel text — so there is no
> prompt-injection surface**. Exit-gate items **5 and 6 are NOT yet met** (M6-P1708 docs and the M6-P1709
> slice-gate Judge have not run). The authoritative slice verdict is the Judge's, strictly from the evidence.

---

## 1. Slice prompt band — evidence status

Source: `04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv` (rows 148–157) + each evidence JSON.

| Prompt | Role | Title | Ledger status | Evidence JSON | Self-reported | `fail_gate_tripped` | Primary artifact(s) |
|---|---|---|---|---|---|---|---|
| M6-P1700 | JUDGE | M6_2H_ENTRY_GATE_JUDGE | **SIGNED** | `04-artifacts/evidence/prompts/M6-P1700.json` | PASS | false | `04-artifacts/evidence/judge/M6-P1700_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS) |
| M6-P1701 | CODER | M6_2H_CODER_PLAN | PASS | `04-artifacts/evidence/prompts/M6-P1701.json` | PASS | false | `04-artifacts/impl/M6.2H/PLAN.md` |
| M6-P1702 | CODER | M6_2H_CODER_IMPLEMENT | PASS | `04-artifacts/evidence/prompts/M6-P1702.json` | PASS | false | `04-artifacts/impl/M6.2H/IMPLEMENTATION_NOTES.md` + staged `app/` tree |
| M6-P1703 | TESTER | M6_2H_TESTER_BUILD | PASS | `04-artifacts/evidence/prompts/M6-P1703.json` | PASS | false | `04-artifacts/impl/M6.2H/tests/TEST_MANIFEST.md` |
| M6-P1704 | TESTER | M6_2H_TESTER_RUN | PASS | `04-artifacts/evidence/prompts/M6-P1704.json` | PASS | false | `04-artifacts/test-reports/M6.2H/SMOKE_RESULTS.md` |
| M6-P1705 | BOUNDARY_ADVERSARY | M6_2H_BOUNDARY_ADVERSARY | PASS | `04-artifacts/evidence/prompts/M6-P1705.json` | PASS | false | `04-artifacts/boundary-reports/M6.2H_boundary.md` |
| M6-P1706 | SECURITY_PII | M6_2H_SECURITY_REVIEW | PASS | `04-artifacts/evidence/prompts/M6-P1706.json` | PASS | false | `04-artifacts/security-reports/M6.2H_security.md` |
| **M6-P1707** | PM_ORCHESTRATOR | M6_2H_EVIDENCE_COLLECT | **RUNNING** | `04-artifacts/evidence/prompts/M6-P1707.json` | (this index) | false | `04-artifacts/evidence/prompts/M6_2H_EVIDENCE_INDEX.md` |
| M6-P1708 | ANALYST_ARCHITECT | M6_2H_DOCS | **TODO** | — (not produced) | — | — | `04-artifacts/analysis/slices/M6_2H_RUNBOOK.md` (pending) |
| M6-P1709 | JUDGE | M6_2H_SLICE_GATE_JUDGE | **TODO** | — (not produced) | — | — | `04-artifacts/evidence/judge/M6-P1709_JUDGE_FINAL_SIGN_OFF.json` (pending) |

All seven band evidence JSONs (M6-P1700 … M6-P1706) exist, are schema-valid, self-report **PASS**, and declare
`fail_gate_tripped=false`; the entry gate M6-P1700 is a genuine Judge `SIGNED` verdict PASS. This prompt's own
`M6-P1707.json` is produced at completion (written **last**, after this index — pack hard-rule 2).

---

## 2. Artifact inventory (existence verified on disk)

### 2.1 Implementation (staged, `04-artifacts/impl/M6.2H/`)
- `PLAN.md` — minimal staged change set + master traceability + per-item rollback.
- `IMPLEMENTATION_NOTES.md` — realized plan (adversarial self-review returned zero findings); §6 rollback.
- Carried-forward M6.2G tree + new **learning layer**: `learning/libraries.py` (the six libraries —
  Persona/Behavior/Keyword/Negative-Keyword/Creative-Hook/Landing-CTA — with locked doc §17 purpose + per-kind
  canonical seed sources; `seed()` rejects a non-canonical seed source **and** any machine content while content-fill
  is BLOCKED), `learning/mapping.py` (the SKU-anchored chain), `learning/candidate.py` (inert `AdsLearningCandidate`
  CTR-014; `is_publish_authorized` requires APPROVED **and** WITHIN → always False in staged posture),
  `learning/review_queue.py` (inert append-only), `learning/learning_engine.py` (the 5-stage skeleton —
  seed/run/learn/review/record_review_decision — with **no publish method**; `learn()` refuses before a canonical
  seed and consumes only DQ-passed verified signals), `api/learning_candidates.py` (CTR-020 POST
  /api/admin/ads/learning-candidates + owner-review handler), `config.py` (+3 fail-closed learning chokes).
- Migrations (staged, never applied): `migrations/0011_create_ads_strategy_libraries.sql` (seed_source NOT NULL,
  content NULL while OD-007), `migrations/0012_create_ads_learning_candidate.sql`.

### 2.2 Tests
- Manifest: `04-artifacts/impl/M6.2H/tests/TEST_MANIFEST.md`.
- Bound smoke: `tests/smoke/test_smk_011_learning_candidate_outside_safe_range_holds.py` (6).
- Leg-supporting: `tests/test_libraries_seed_from_canon_only.py` (15), `test_content_fill_halts_at_framework.py` (3),
  `test_mapping_chain_anchored_to_sku.py` (4), `test_no_auto_publish_review_queue_only.py` (4),
  `test_candidate_outside_safe_range_holds.py` (3), `test_learn_precondition_seed_and_dq.py` (3) + carried suites.
- Full staged suite **351 passed / 0 failed** = 313 carried-forward (M6.2A–G) + 38 new M6.2H nodes (32 learning-leg + 6 bound smoke).

### 2.3 Reports
- Test report: `04-artifacts/test-reports/M6.2H/SMOKE_RESULTS.md` (SMK-011 6/6; full suite 351).
- Boundary report: `04-artifacts/boundary-reports/M6.2H_boundary.md`.
- Security/PII report: `04-artifacts/security-reports/M6.2H_security.md` (verdict PASS; scan clean over 171 files; no prompt-injection surface).
- Entry-gate Judge sign-off: `04-artifacts/evidence/judge/M6-P1700_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS).

---

## 3. Contract checklist (from the slice spec)

| Contract | Shape | Ownership | Status (canon) | Harmonization |
|---|---|---|---|---|
| M6-CTR-014 | ads_learning_candidate | M6 | MISSING / OWNER_DECISION_REQUIRED | M6-P0710 (PASS) |
| M6-CTR-020 | POST /api/admin/ads/learning-candidates | M6 | MISSING / OWNER_DECISION_REQUIRED | M6-P0712 (PASS) |

Both are `MISSING` in canon but **satisfied-for-entry** (harmonization producers PASS, gate M6-P0715 SIGNED).
Canon-flips are deferred, non-blocking operator housekeeping.

---

## 4. Exit-gate checklist → evidence map

Legend: **MET** = evidence present and sufficient at the staged level · **SUPPORTED (staged)** = the bound/supporting
suites pass and the boundary adversary executed the check, with open (armed-not-fired) residuals · **PENDING** = the
producing prompt has not run yet. Caveats are carry-forwards (see §5); none trips the in-scope fail gate (M6-FAIL-006 — held).

| # | Exit-gate check (slice spec) | Verdict | Evidence refs | Notes / caveats |
|---|---|---|---|---|
| 1 | **Seed framework pass** — the six libraries exist with the doc §17 seed-source constraints enforced; machine never fabricates origin strategy | **SUPPORTED (staged)** | `tests/test_libraries_seed_from_canon_only.py` (15) + `test_content_fill_halts_at_framework.py` (3) + `test_mapping_chain_anchored_to_sku.py` (4) within the 351; `app/measurement/learning/libraries.py`, `mapping.py`; boundary `M6.2H_boundary.md` (RULE-011/LEX-006 seed-only-from-canon, content fill BLOCKED) | RULE-011/013/LEX-006. Tester marks leg **L1 "met"**. Machine never fabricates origin (canonical seed only; content NULL while M6-OD-007 open). Caveats B3-F-LEARN-4 (mapping SKU anchor is truthiness-only) + F-LEARN-1 (unguarded ReviewQueue.update). Final L1 closure is the slice-gate Judge's call. |
| 2 | **No auto-publish** — candidates land in the review queue only; publish requires owner/marketing approval or guarded safe range (safe range = M6-OD-006, BLOCKED until decided) | **SUPPORTED (staged)** | `04-artifacts/test-reports/M6.2H/SMOKE_RESULTS.md` (SMK-011 6/6) + `tests/test_no_auto_publish_review_queue_only.py` (4) + `test_candidate_outside_safe_range_holds.py` (3); `learning/learning_engine.py` (no publish method), `candidate.py`; boundary + security (FAIL-006 not tripped — no publish executor, `is_publish_authorized` 0 consumers) | RULE-011/FAIL-006. Tester marks leg **L2 "met"**. Review forces safe-range UNKNOWN while OD-006 open → HELD; an owner APPROVE still authorizes nothing. Caveats B3-F-LEARN-1 (in-process queue laundering) + B4-ACCESS-1 (reviewer authN at binding). |
| 3 | **Learning-input precondition** — the Learn/scoring stage runs only after the canonical seed exists and consumes only verified business signals that passed the Data Quality Gate | **SUPPORTED (staged)** | `tests/test_learn_precondition_seed_and_dq.py` (3) within the 351; `learning/learning_engine.py` (`learn()` refuses before a canonical seed; consumes only DQ-PASS + verified signals); boundary confirmed | RULE-011. Tester marks leg **L3 "met"**. Learn refuses before a canonical seed; HOLD/FAIL/unverified signals excluded. **No prompt-injection surface** (normalized DQ-passed scores, never raw channel text). |
| 4 | **Smoke M6-SMK-011 executed** with recorded result + evidence ref | **MET** | `SMOKE_RESULTS.md` (6/6, exit 0); `04-artifacts/evidence/prompts/M6-P1704.json` | Candidate outside/UNKNOWN safe range → HELD in review, never publishable. |
| 5 | **All slice prompts have evidence JSON** (schema-valid, no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | `04-artifacts/evidence/prompts/M6-P1700.json` … `M6-P1706.json` present (7); `M6-P1707.json` produced at this prompt's completion | **Not yet complete:** M6-P1708 (Docs) and M6-P1709 (Judge) evidence not produced (both TODO). |
| 6 | **Slice-gate Judge sign-off exists with verdict PASS** | **PENDING (not met)** | — | `04-artifacts/evidence/judge/M6-P1709_JUDGE_FINAL_SIGN_OFF.json` does **not** exist; M6-P1709 is TODO. (The existing `M6-P1700_JUDGE_FINAL_SIGN_OFF.json` is the *entry* gate.) |
| 7 | **Rollback steps documented** for every change this slice made | **MET** | `04-artifacts/impl/M6.2H/PLAN.md` (per-item Rollback) + `IMPLEMENTATION_NOTES.md` §6 (new files → delete; patched `config.py` → revert to M6.2G); `migrations/0011`, `0012` down-DDL | All changes staged ⇒ non-destructive; review-queue records inert + append-only. |

**Summary:** items **4 and 7 are MET**; items **1, 2 and 3 are SUPPORTED at the staged level** (the tester marks
legs L1/L2/L3 "met" and FAIL-006 is not tripped, but the F-LEARN-1..4 / ACCESS-1 residuals remain — armed-not-fired
— so final closure is the slice-gate Judge's call); items **5 and 6 are PENDING** (M6-P1708 docs, then M6-P1709
slice-gate Judge). Coverage: **every exit-gate checklist item is indexed** (acceptance check 1).

### 4.1 Smoke register bindings

| Smoke ID | Doc ID | Scenario (verbatim) | Expected (verbatim) | Result | Evidence |
|---|---|---|---|---|---|
| M6-SMK-011 | ADS-P0-011 | `Learning candidate ngoài safe range` | `Hold review, không publish` | **PASS 6/6** | `SMOKE_RESULTS.md`, `M6-P1704.json` |

---

## 5. Unresolved blockers / carry-forwards (acceptance check 2)

None of the following is an open blocker of the **evidence-collection** task itself, and none trips the in-scope
fail gate (M6-FAIL-006 — held). Each was already adjudicated by the responsible upstream prompt and is carried
forward for the slice-gate Judge (M6-P1709) and the owner.

- **B1 — Slice exit gate is not complete (expected at this step).** Item 5 pending M6-P1708/M6-P1709 evidence;
  item 6 pending the M6-P1709 slice-gate Judge PASS sign-off.

- **B2 — Framework-only by design (the objective's fail-closed halt).** Content-fill **halts at framework** because
  **M6-OD-007** (content fill) is OPEN (`LEARNING_CONTENT_FILL_ENABLED=False`: libraries carry a canonical seed-source
  ref but **no** machine content), and the guarded-publish path stays BLOCKED because **M6-OD-006** (safe range) is
  OPEN (`LEARNING_SAFE_RANGE_RATIFIED=False`: review forces safe-range UNKNOWN → HELD). This is the *designed* posture,
  not a defect — the slice proves the framework capability with evidence and never fills content or publishes.

- **B3 — Boundary residuals (M6-P1705), armed-not-fired, none trips M6-FAIL-006; routed to CODER / M6-OD-011.**
  - **F-LEARN-1 [in-process only]:** `ReviewQueue.update()` is a second, unguarded write path (validates only
    candidate_id existence), so an in-process caller can swap a forged APPROVED+WITHIN record in, defeating
    `review()`'s UNKNOWN-forcing — the M6.2H analog of the M6.2G store-laundering finding. Not wire-exposed (the API
    never calls `update()`), inert (no publish consumer). Fix: reject illegal transitions / re-force UNKNOWN; the
    M6-OD-011 binding must **never auto-wire the review queue to a publisher**.
  - **F-LEARN-2 [MINOR]:** the create handler under-validates `score` — NaN/inf pass `isinstance(float)` and an
    extreme-magnitude score makes `float(score)` raise an **unhandled OverflowError**, so an untrusted admin body
    escapes the handler's REJECTED_INPUT fail-closed contract with a crash. Not FAIL-006 (score never gates publish).
    Fix: reject non-finite + bound magnitude + wrap `float()`.
  - **F-LEARN-3 [MINOR]:** `review()` re-derives `review_state` (discards a forged APPROVED — good) but does **not**
    scrub the incoming `decision` field, so a forged `OwnerReviewDecision` can ride onto a CANDIDATE record (inert;
    visible via `to_public`). Fix: reset `decision=None` on review.
  - **F-LEARN-4 [MINOR]:** `StrategyMapping` anchors on **truthiness only** (a monetary value / Core object / policy
    token passes as the sellable SKU; `verified_revenue_ref` accepts a literal value despite its "never a value"
    contract) — but `run()` writes no Core value (so RULE-013 holds in effect); input-validation gap only. Fix:
    validate `sku_ref` against a sellable-SKU set + reject value-shaped `verified_revenue_ref`.
  - N-1: an in-process `object.__setattr__` can forge an APPROVED+WITHIN candidate — a defense-in-depth limit only
    (requires arbitrary in-process code exec, publishes nothing, not channel-reachable).
  - N-2: the no-auto-publish denylist test omits `run/activate/promote/deploy` and leaves the inert public `run` +
    `active_mappings` uncovered — harden the denylist / add a CI guard.
  - *Ref:* `04-artifacts/boundary-reports/M6.2H_boundary.md`.

- **B4 — Security (M6-P1706), forward-routed.**
  - **ACCESS-1 [load-bearing forward requirement]:** the decision handler takes `actor` **from the request body**;
    there is no authentication that the caller is that owner/marketing reviewer. Inert today (an APPROVE authorizes
    nothing), but at the M6-OD-011 HTTP binding the endpoint **must** authenticate the caller, authorize APPROVE to
    the reviewer role, and bind `OwnerReviewDecision.actor` to the authenticated identity.
  - **F-LEARN-PII-1 [MINOR]:** `OwnerReviewDecision.to_public()` echoes owner free-text (`reason`/`audit_ref`/
    `evidence_ref`) unmasked on export (excluded from the audit per the D5 fix; contract-non-PII, no leak today).
    Route: document/bound/mask + M6-OD-012. (Same class as M6.2G F-SCALE-PII-1.)
  - **Positive:** PII/secret scan clean over 171 files; libraries hold framework metadata not customer data; and the
    learning stage has **no prompt-injection surface** (consumes only DQ-passed verified normalized scores, never raw channel text).
  - *Ref:* `04-artifacts/security-reports/M6.2H_security.md`.

- **B5 — Contract housekeeping (non-blocking).** CTR-014/020 are `MISSING / OWNER_DECISION_REQUIRED` in canon but
  satisfied-for-entry (producers M6-P0710/M6-P0712 PASS, gate M6-P0715 SIGNED). Canon-flips deferred.

- **B6 — Open owner decisions + inherited forward gates.** **M6-OD-006** (safe range — guarded publish, BLOCKED until
  decided) and **M6-OD-007** (content fill — framework-may-proceed) are the two OPEN decisions scoped to M6.2H. The
  full M6.2G before-real-scale/send/auto-publish forward-gate chain remains in force: the four attestation true-ups;
  ENTRY-001/003 real-scale conditions; ENTRY-004 M5 DEBT-1..4 + P4 re-gate; M6-OD-002/003/004/005; the M6.2G
  **F-SCALE-*** scale-boundary residuals; and the M6.2G/M6.2H ACCESS-1 reviewer/owner authN + store/queue-laundering
  fixes at the M6-OD-011 binding.

- **B7 — Immutable governance posture.** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
  the three learning chokes (`LEARNING_AUTOPUBLISH_ENABLED` / `LEARNING_CONTENT_FILL_ENABLED` / `LEARNING_SAFE_RANGE_RATIFIED`)
  and all M6.2A–G flags remain **False**; `live_migrations=false`. `M6-P1000` + `M6-P1309` verdicts remain **BLOCKED
  (not converted)**. FAIL-006 not tripped; nothing is published, scaled, or sent; no origin strategy is fabricated;
  the mandatory M6.2G Scale-Gate re-gate stands before any real scale/publish/external send.

---

## 6. Reader's guide for the slice-gate Judge (M6-P1709)

1. Start from `00-spec/slices/M6.2H.md` "Exit gate checks" (the 7 items in §4 above).
2. For legs 1–4 + 7, read the reports/evidence in the §4 "Evidence refs" cells directly (do not rely on this index).
3. Confirm the **framework-only** posture is faithful: content-fill halts at framework (OD-007) and guarded publish
   is BLOCKED (OD-006), both fail-closed — the slice proves capability and fills/publishes nothing.
4. Confirm items 5 & 6 by re-reading the ledger and `04-artifacts/evidence/judge/` (M6-P1709 sign-off is the Judge's own output).
5. Weigh the B3/B4 residuals (F-LEARN-1..4, ACCESS-1, F-LEARN-PII-1) as "close before the M6-OD-011 durable binding
   and before OD-006/OD-007 ratify any publish/content", plus the inherited B6 forward-gate chain and the standing
   BLOCKED `M6-P1000`/`M6-P1309` verdicts.

*This index is descriptive. It advances no gate and self-certifies nothing; the runner EVIDENCE_GATE and the
slice-gate Judge decide closure.*
