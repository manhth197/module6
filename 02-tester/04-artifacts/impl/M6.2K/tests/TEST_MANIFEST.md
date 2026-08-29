# TEST_MANIFEST — Slice M6.2K smoke suite (full P0 re-run → doc §22 owner evidence pack)

| Field | Value |
|---|---|
| Prompt | M6-P2003 — `M6_2K_TESTER_BUILD` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — the M6.2K smoke legs are AUTHORED here. This attempt ran a **collect-only build-validation** (imports/collects clean, no assertions executed) per the prompt's "Build (do not yet run)"; the **formal executed-results recording** belongs to M6-P2004. |
| Executed by (formal) | M6-P2004 (`M6_2K_TESTER_RUN`) → `04-artifacts/test-reports/M6.2K/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-001 … M6-SMK-018** — the WHOLE P0 matrix (15 owner + 3 proposed), per `00-spec/slices/M6.2K.md` "Core smokes" + this prompt's `<smoke_ids>` |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Slice scope | Re-run the full P0 matrix and record a `correlation_id` + `evidence_id` per smoke; assemble the doc §22 evidence plan (10 categories) into an OWNER sign-off package with an honest gap/blocker list. Production/scale stays BLOCKED regardless of results — this slice only proves readiness for owner review. |
| Staging root | `04-artifacts/impl/M6.2K/` (STAGED_ONLY; convention reference, not a live repo) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (owner P0 matrix extract lines 401–415 + proposed additions 016/017/018) |

> **Governance (immutable — nothing in this suite flips a flag, and the pack only measures/assembles):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `SCALE_MODEL_RATIFIED=False`,
> `SCALE_EXECUTION_ENABLED=False`, `HASH_POLICY_RATIFIED=False`, `LEARNING_AUTOPUBLISH_ENABLED=False`,
> `LEARNING_CONTENT_FILL_ENABLED=False`, `LEARNING_SAFE_RANGE_RATIFIED=False`. This slice **re-runs** the smokes and
> **assembles** an owner package; it **never** declares ROAS Pass / Scale Ready and **never** self-certifies
> (M6-RULE-015; doc §23; M6-FAIL-007). The evidence pack's readiness enum has **no PASS/READY member** — it tops out
> at `OWNER_REVIEW_REQUIRED`, and is fail-closed `NOT_READY` on any incomplete §22 category or any un-recorded smoke.
> `status` here is an honest TESTER self-report; the runner EVIDENCE_GATE and the slice Judge (M6-P2009) decide closure.

## What this suite is

M6.2K is the **full P0 matrix re-run**. Every one of the 18 smoke ids is re-bound to M6.2K, so each gets a NEW
slice-appropriate **evidence-pack leg** — `tests/smoke/test_smk_<nnn>_p0_evidence_pack.py` — that proves the smoke's
re-run result flows correctly into the doc §22 owner review package (the M6.2K-new layer, `app/measurement/evidence/`
authored by the coder in M6-P2002). These 18 new legs **coexist with the carried behavioral legs** authored across
M6.2A–J (the same coexistence pattern used for re-bound smokes like SMK-004 / SMK-010 / SMK-013 across earlier
slices): the carried leg proves the *behavior* ("executed"); the new evidence leg proves the *recorded result +
evidence ref* — together they close each per-smoke exit-gate leg ("Smoke M6-SMK-00X executed with recorded result and
evidence ref"). Both re-run in the same staged suite.

The 18 new legs reuse the coder-provided M6.2K evidence-pack fixtures in
[`tests/conftest.py`](04-artifacts/impl/M6.2K/tests/conftest.py) — `evidence_assembler`, `full_evidence_refs`,
`all_smokes_recorded`, `make_smoke_result` — plus the frozen `app/measurement/evidence/` package. **No new production
code**, and **no fix to the code under test** (TESTER reports defects, never fixes them). All ids are **synthetic**;
`correlation_id` / `evidence_id` are **masked on export** (M6-RULE-014 / H02) — no raw secret/PII anywhere.

## Smoke → test binding (all 18 ids; scenario/expected verbatim from SMOKE_REGISTER)

| Smoke ID | Doc ID | Status | New M6.2K evidence leg (`tests/smoke/…`) | Nodes | Carried behavioral leg(s) re-run in the suite | Kịch bản → Kết quả phải đạt (verbatim) | Exit leg |
|---|---|---|---|---|---|---|---|
| M6-SMK-001 | ADS-P0-001 | owner | `test_smk_001_p0_evidence_pack.py` | 4 | `test_smk_001_event_not_in_registry.py`, `test_smk_001_track_unknown_event.py` | "Event không có trong event_registry" → "Reject/HOLD, audit rõ" | 2 |
| M6-SMK-002 | ADS-P0-002 | owner | `test_smk_002_p0_evidence_pack.py` | 4 | `test_smk_002_outbox_consent_failclosed.py`, `test_smk_002_valid_event_missing_consent.py` | "Event hợp lệ nhưng thiếu consent" → "Không external measurement, không audience sync" | 3 |
| M6-SMK-003 | ADS-P0-003 | owner | `test_smk_003_p0_evidence_pack.py` | 4 | `test_smk_003_duplicate_dedup.py`, `test_smk_003_platform_dedup.py` | "Duplicate Pixel/CAPI/Offline" → "Dedup, không double count" | 4 |
| M6-SMK-004 | ADS-P0-004 | owner | `test_smk_004_p0_evidence_pack.py` | 4 | `test_smk_004_quote_not_revenue.py`, `test_smk_004_quote_in_golden_hour_funnel_not_revenue.py` | "Quote được tạo nhưng chưa order" → "Không revenue, không ROAS" | 5 |
| M6-SMK-005 | ADS-P0-005 | owner | `test_smk_005_p0_evidence_pack.py` | 4 | `test_smk_005_order_not_verified_not_revenue.py` | "Order Draft / Order Created chưa verified" → "Không tính Revenue Verified" | 6 |
| M6-SMK-006 | ADS-P0-006 | owner | `test_smk_006_p0_evidence_pack.py` | 4 | `test_smk_006_order_verified_full_source.py`, `test_smk_006_dashboard_roas_update.py` | "ORDER_VERIFIED có campaign/adset/ad đầy đủ" → "ROAS/CPA/AOV dashboard cập nhật" | 7 |
| M6-SMK-007 | ADS-P0-007 | owner | `test_smk_007_p0_evidence_pack.py` | 4 | `test_smk_007_missing_source_low_hold.py` | "ORDER_VERIFIED thiếu source" → "Revenue vẫn lưu, attribution confidence LOW/HOLD" | 8 |
| M6-SMK-008 | ADS-P0-008 | owner | `test_smk_008_p0_evidence_pack.py` | 4 | `test_smk_008_crm_optout_no_sync.py` | "CRM opt-out" → "Không sync CRM audience/CRM event outbound" | 9 |
| M6-SMK-009 | ADS-P0-009 | owner | `test_smk_009_p0_evidence_pack.py` | 4 | `test_smk_009_recall_sale_lock_scale_fail.py` | "Recall/Sale Lock active" → "Scale Gate FAIL/HOLD" | 10 |
| M6-SMK-010 | ADS-P0-010 | owner | `test_smk_010_p0_evidence_pack.py` | 4 | `test_smk_010_data_mart_support_view_only.py`, `test_smk_010_growth_data_mart_support_view_only.py` | "Data Mart tạo trigger CRM/scale" → "Fail - Data Mart chỉ support view" | 11 |
| M6-SMK-011 | ADS-P0-011 | owner | `test_smk_011_p0_evidence_pack.py` | 4 | `test_smk_011_learning_candidate_outside_safe_range_holds.py` | "Learning candidate ngoài safe range" → "Hold review, không publish" | 12 |
| M6-SMK-012 | ADS-P0-012 | owner | `test_smk_012_p0_evidence_pack.py` | 4 | `test_smk_012_scale_no_owner_approval.py` | "Scale request không owner approval" → "Không scale" | 13 |
| M6-SMK-013 | ADS-P0-013 | owner | `test_smk_013_p0_evidence_pack.py` | 4 | `test_smk_013_live_chain_trace.py`, `test_smk_013_funnel_live_chain_trace.py` | "Live/Comment/Messenger chain" → "Trace được live_session_id, comment_id, messenger_thread_id" | 14 |
| M6-SMK-014 | ADS-P0-014 | owner | `test_smk_014_p0_evidence_pack.py` | 4 | `test_smk_014_diamond_referral_no_commission.py` | "Diamond referral order verified" → "Gắn referral attribution, không tự tính commission" | 15 |
| M6-SMK-015 | ADS-P0-015 | owner | `test_smk_015_p0_evidence_pack.py` | 4 | `test_smk_015_dashboard_quote_draft_not_revenue.py` | "Dashboard hiển thị quote/order draft như revenue" → "Fail" | 16 |
| M6-SMK-016 | proposed | proposed | `test_smk_016_p0_evidence_pack.py` | 4 | `test_smk_016_outbox_retry_deadletter.py` | "Outbox item fails to send N times" → "Bounded retry with error_log + next_retry_at, then dead-letter; no infinite retry, no silent loss" | 17 |
| M6-SMK-017 | proposed | proposed | `test_smk_017_p0_evidence_pack.py` | 4 | `test_smk_017_hash_policy_no_raw_pii.py` | "External payload (CAPI/Offline) built from an event containing raw PII" → "Hash policy applied per M6-OD-003; no raw phone/email/user-id in the outbound payload or platform result log" | 18 |
| M6-SMK-018 | proposed | proposed | `test_smk_018_p0_evidence_pack.py` | 4 | `test_smk_018_verified_immutable_adjustment.py` | "Attribution correction attempted after ORDER_VERIFIED" → "Direct mutation rejected; adjustment record created with actor, reason, audit, evidence" | 19 |

**New M6.2K evidence-leg nodes: 72 (18 files × 4).**

## What each new M6.2K evidence leg asserts (shared 4-test shape; test 3 branches owner vs proposed)

Every `test_smk_<nnn>_p0_evidence_pack.py` carries the register scenario/expected **verbatim** (module + primary-test
docstring) and drives the frozen `EvidencePackAssembler` for that one smoke id (`_SMK`):

1. **Primary — recorded result is in the owner pack (scenario verbatim):** with the full matrix recorded
   (`all_smokes_recorded`) and all 10 §22 categories complete (`full_evidence_refs`), the assembled pack lists this
   smoke as `recorded` (status `PASS` + `correlation_id` + `evidence_id`); pack readiness is the terminal
   `OWNER_REVIEW_REQUIRED` (never Pass/Ready); the pack still discloses every standing blocker
   (`has_standing_blockers()`). The recorded result IS the per-smoke evidence ref the exit gate requires.
2. **Negative / fail-closed — an un-run smoke can never be "recorded":** replacing this smoke with an un-run result
   (no `correlation_id`/`evidence_id`) → `recorded is False`, an `UNRUN` gap carrying its id, and readiness drops to
   `NOT_READY` (M6-FAIL-007). The smoke cannot silently pass.
3. **Negative / fail-closed — waiver scope:**
   - **Owner smokes (001–015):** `get_spec(_SMK).status is SmokeStatus.OWNER`; an owner-smoke waiver is **INVALID and
     stripped** by the assembler → stays un-run → `NOT_READY` (a mandatory smoke can never vanish from the honest gap
     list via a waiver — FAIL-007 defense-in-depth).
   - **Proposed smokes (016–018):** `get_spec(_SMK).status is SmokeStatus.PROPOSED`; per the M6.2K exit gate a proposed
     smoke is executed **OR** explicitly owner-waived — a recorded waiver counts as `recorded` (disclosed as `waived`),
     readiness stays `OWNER_REVIEW_REQUIRED`. (The un-run **AND** un-waived case is the fail-closed negative in test 2.)
4. **PII-safe — recorded ids masked on export (M6-RULE-014 / H02):** `SmokeResult.to_public()` masks
   `correlation_id`/`evidence_id` (masked ≠ raw; the raw id never appears in the public view).

## The doc §22 evidence-pack contract (coder M6-P2002; re-run/assembled, never self-certified)

The 18 recorded smoke results + the 10 doc §22 evidence categories assemble (via `EvidencePackAssembler.assemble`)
into the owner review package. The **10 §22 categories** (all mandatory content required, else INCOMPLETE →
fail-closed `NOT_READY`, FAIL-007): Event Registry, Consent, Outbox, Dedup, Attribution, Dashboard, Scale Gate,
Learning, Security/Privacy, Smoke Report. The pack **always** carries the 8 canonical **standing gap/blockers**
(M6-P1000 + M6-P1309 BLOCKED verdicts, the M6.2G/H/I/J forward conditions, M6-OD-011/012) — disclosed but not a
readiness gate (production stays BLOCKED regardless). **Readiness** = `NOT_READY` iff any category INCOMPLETE OR any
smoke un-recorded, else `OWNER_REVIEW_REQUIRED`. There is **no** Pass/Ready/certify/flag-flip method (RULE-015; doc
§23). The 18-node aggregate contract is also exercised by the carried coder tests
[`test_pack_never_declares_pass_or_ready.py`](04-artifacts/impl/M6.2K/tests/test_pack_never_declares_pass_or_ready.py),
[`test_evidence_ten_categories_mandatory_content.py`](04-artifacts/impl/M6.2K/tests/test_evidence_ten_categories_mandatory_content.py),
[`test_gap_blocker_list_carries_standing_blockers.py`](04-artifacts/impl/M6.2K/tests/test_gap_blocker_list_carries_standing_blockers.py),
[`test_pack_posture_immutable_and_pii_safe.py`](04-artifacts/impl/M6.2K/tests/test_pack_posture_immutable_and_pii_safe.py),
[`test_smoke_registry_complete_18.py`](04-artifacts/impl/M6.2K/tests/test_smoke_registry_complete_18.py) and the
meta-check [`test_full_p0_matrix_runs_green.py`](04-artifacts/impl/M6.2K/tests/test_full_p0_matrix_runs_green.py).

## Fixtures reused (from `tests/conftest.py`)

| Fixture | Role |
|---|---|
| `evidence_assembler` | `EvidencePackAssembler()` — read-only owner-pack assembler (no self-cert / no flag-flip) |
| `full_evidence_refs` | a COMPLETE `evidence_refs` mapping — every one of the 10 §22 categories has all its mandatory keys |
| `all_smokes_recorded` | all 18 smokes recorded with a synthetic `correlation_id` (`corr_0NN`) + `evidence_id` (`ev_0NN`) |
| `make_smoke_result(smoke_id, status=, correlation_id=, evidence_id=, waived=)` | build one `SmokeResult` (un-run / waived cases) |

Plus the frozen `app/measurement/evidence/` package (`models`, `pack_assembler`, `smoke_registry`, `categories`,
`gap_blockers`) and `app/measurement/masking.mask`. The carried behavioral legs reuse their own M6.2A–J fixtures.

## Boundary / safety asserted by the suite

- **No overstated readiness (M6-RULE-015 / M6-FAIL-007 / doc §23):** readiness never reaches Pass/Ready; it is
  `OWNER_REVIEW_REQUIRED` at best and fail-closed `NOT_READY` on any incomplete category / un-recorded smoke.
- **Honest gap/blocker list always disclosed:** the 8 standing blockers are present in every assembled pack.
- **PII-safe (M6-RULE-014 / H02):** `correlation_id` / `evidence_id` masked on export; all ids synthetic; no raw
  phone/email/address/customer_id/psid/token anywhere.
- **No fix to code under test; no application code / migration / external call / CRM send / commission / Data-Mart
  trigger / Core override / order-state / pricing / flag flip / `04-artifacts/state/` write** anywhere in the suite.

## Build-validation performed in M6-P2003 (attempt 1, collect-only — "do not yet run")

Per the prompt's `<task>` ("Build (do not yet run)"), this attempt ran **collect-only** (imports + collects; **no
assertions executed**). Run with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest 8.4.2**, from
`04-artifacts/impl/M6.2K/`, **no shell redirection** (the role guard blocks a `>`/`2>` co-occurring with the venv
`Scripts` path), cache-free (`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```bash
python.exe -c "<in-process pytest_collection_finish tally; pytest.main(['--collect-only','-q','-p','no:cacheprovider'])>"
#   -> RC 0 ; COLLECTED_TOTAL=523 ; NEW_TOTAL=72 (each new file = 4 nodes) ; 0 collection errors
```

Reconciliation: **523** collected = carried M6.2K baseline **451** (M6.2J tree 425 + coder M6.2K evidence tests 26) +
these **72** new evidence-leg nodes (18 × 4). Every new file imports + collects clean (evidence fixtures wired). A
static self-check confirmed each file's `_SMK` matches its filename and the owner/proposed split is correct (001–015
OWNER, 016–018 PROPOSED). A read-only **adversarial static verification** (3 logic verifiers tracing every assertion
through the frozen `evidence/` source, 1 verbatim-string auditor vs SMOKE_REGISTER, 1 completeness/PII/boundary critic)
was run alongside — findings recorded in the M6-P2003 evidence.

> **On counting.** In this harness pytest's terminal summary line is not reliably captured for a long run, so the
> total (**523**) was obtained via an in-process `pytest_collection_finish` tally (`len(session.items)`) with pytest
> `RC=0`; pytest's own per-item collect output was swallowed (`redirect_stdout`) so the tally prints cleanly.

Cache hygiene: `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

> **This build does NOT self-certify gate advancement.** Collect-only proves the smoke files import + collect against
> the frozen M6.2K code; it does not execute assertions. The **formal executed-results recording** (per-smoke
> `correlation_id` + `evidence_id`) is produced by **M6-P2004** into
> `04-artifacts/test-reports/M6.2K/SMOKE_RESULTS.md`. The runner EVIDENCE_GATE and the slice Judge decide closure.

## Execution plan for M6-P2004 (`M6_2K_TESTER_RUN`)

Run the full staged suite and the 18 new evidence legs, then record a structured result **plus a `correlation_id` +
`evidence_id` per smoke** for the owner package (exit-gate leg L1 + the per-smoke legs 2–19):

```bash
python -m pytest -q                                  # full staged suite: expected 523 passed
python -m pytest -q tests/smoke/test_smk_001_p0_evidence_pack.py … test_smk_018_p0_evidence_pack.py   # expected 72 passed
```

Record for each of the 18 smoke ids: PASS/FAIL/BLOCKED + detail + the `correlation_id` and `evidence_id` (synthetic,
masked). Proposed smokes 016/017/018 are executed here (not waived). The runner report feeds the PM evidence-collect
(M6-P2007) which assembles the 10-category owner package; the pack must reach `OWNER_REVIEW_REQUIRED` (never Pass/Ready)
while disclosing the 8 standing blockers.

## Exit-gate legs (slice M6.2K done-gate, itemized)

| Leg | Requirement | Covered by |
|---|---|---|
| 1 (L1) | Evidence pack ready for review: all P0 smokes re-run with recorded correlation_id + evidence_id, all 10 §22 categories with mandatory content, owner package + honest gap/blocker list | the 18 evidence legs (built here) + coder T1–T6 + M6-P2004 run + PM M6-P2007 |
| 2–16 | Smoke M6-SMK-001 … M6-SMK-015 executed with recorded result + evidence ref | per-id evidence leg (built here) + carried behavioral leg; closed by M6-P2004 |
| 17–19 | Proposed smoke M6-SMK-016 / 017 / 018 executed OR owner-waived | per-id evidence leg (built here) + carried behavioral leg; executed by M6-P2004 |
| 20 | All slice prompts have schema-valid evidence JSON (no raw secret/PII, fail_gate_tripped=false) | this evidence + downstream prompts |
| 21 | Slice gate judge sign-off PASS | M6-P2009 (downstream) |
| 22 | Rollback steps documented | new files → delete (no carried-forward file patched) |

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-015 | No self-certification: the module records honest status; the runner gate + Judge decide. The pack never declares ROAS Pass / Scale Ready (owner-only, doc §23). |
| M6-FAIL-007 | "No evidence → called PASS": fail-closed — a missing §22 category or an un-recorded smoke forces `NOT_READY`; a mandatory-smoke waiver is stripped. |
| M6-RULE-014 / H02 | No raw PII/secret: `correlation_id` / `evidence_id` masked on export; all ids synthetic. |

## Provenance / notes

- Scenario & expected text quoted **verbatim** from `00-spec/registers/SMOKE_REGISTER.md` (rows M6-SMK-001…018;
  owner extract lines 401–415, proposed additions 016/017/018). Test patterns reused from the coder's M6.2K
  evidence-pack fixtures + tests and the M6.2A–J carried smoke suite (doc working mode, extract line 466).
- **Rollback:** the 18 new `tests/smoke/test_smk_<nnn>_p0_evidence_pack.py` files → delete; **no carried-forward file
  is patched**, no production code added, no migration, no flag flipped.
- No self-certification of PASS or of gate/leg advancement: the runner EVIDENCE_GATE and the slice Judge decide. This
  manifest and the 18 evidence legs are the *build*; the formal executed results (with correlation_id + evidence_id)
  are produced in M6-P2004.
