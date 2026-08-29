# SMOKE_RESULTS — Slice M6.2K (full P0 matrix re-run → doc §22 owner evidence pack)

| Field | Value |
|---|---|
| Prompt | M6-P2004 — `M6_2K_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test** — the M6.2K smoke suite is EXECUTED here and results recorded. Smoke legs were authored in M6-P2003 (`M6_2K_TESTER_BUILD`). |
| Smoke ids executed | **M6-SMK-001 … M6-SMK-018** — the WHOLE P0 matrix (15 owner + 3 proposed); the proposed 016/017/018 are **executed** here (not owner-waived) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Staging root | `04-artifacts/impl/M6.2K/` (STAGED_ONLY; convention reference, not a live repo) |
| Evidence-leg result | **72 passed, 0 failed — exit 0** (18 legs × 4 nodes) |
| Full staged suite | **523 passed, 0 failed, 0 skipped, 0 error — RC 0** |
| Overall | **all 18 bound smoke ids PASS; no failures; nothing patched; the pack measures/assembles only** |

> **Governance (immutable — nothing in this run flips a flag; this slice proves capability with evidence only):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `SCALE_MODEL_RATIFIED=False`,
> `SCALE_EXECUTION_ENABLED=False`, `HASH_POLICY_RATIFIED=False`, `LEARNING_AUTOPUBLISH_ENABLED=False`. The evidence
> pack **never** declares ROAS Pass / Scale Ready and **never** self-certifies (M6-RULE-015; doc §23): its readiness
> enum has no PASS/READY member — it tops out at `OWNER_REVIEW_REQUIRED` and is fail-closed `NOT_READY` on any
> incomplete §22 category or un-recorded smoke (M6-FAIL-007). `status` here is an honest TESTER self-report; the
> runner EVIDENCE_GATE and the slice Judge (M6-P2009) decide closure. The 8 standing gap/blockers (M6-P1000 +
> M6-P1309 BLOCKED, the M6.2G/H/I/J forward conditions, M6-OD-011/012) remain disclosed in the pack.

## Per-smoke results — the M6.2K evidence legs (all PASS; scenario/expected verbatim from SMOKE_REGISTER)

Each evidence leg re-runs the smoke's result THROUGH the doc §22 owner review package and records it with a
`correlation_id` + `evidence_id` (doc §22 Smoke Report). Ids are **synthetic** and shown in their **export-masked**
form (`app.measurement.masking.mask`, RULE-014/H02) — the raw synthetic value is `corr_0NN` / `ev_0NN`.

| Smoke ID | Doc ID | Status | Test file (`tests/smoke/…`) | Nodes | Result | correlation_id (masked) | evidence_id (masked) | Kịch bản → Kết quả phải đạt (verbatim) |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-001 | ADS-P0-001 | owner | `test_smk_001_p0_evidence_pack.py` | 4 | **PASS** | `cor***01` | `ev_***01` | "Event không có trong event_registry" → "Reject/HOLD, audit rõ" |
| M6-SMK-002 | ADS-P0-002 | owner | `test_smk_002_p0_evidence_pack.py` | 4 | **PASS** | `cor***02` | `ev_***02` | "Event hợp lệ nhưng thiếu consent" → "Không external measurement, không audience sync" |
| M6-SMK-003 | ADS-P0-003 | owner | `test_smk_003_p0_evidence_pack.py` | 4 | **PASS** | `cor***03` | `ev_***03` | "Duplicate Pixel/CAPI/Offline" → "Dedup, không double count" |
| M6-SMK-004 | ADS-P0-004 | owner | `test_smk_004_p0_evidence_pack.py` | 4 | **PASS** | `cor***04` | `ev_***04` | "Quote được tạo nhưng chưa order" → "Không revenue, không ROAS" |
| M6-SMK-005 | ADS-P0-005 | owner | `test_smk_005_p0_evidence_pack.py` | 4 | **PASS** | `cor***05` | `ev_***05` | "Order Draft / Order Created chưa verified" → "Không tính Revenue Verified" |
| M6-SMK-006 | ADS-P0-006 | owner | `test_smk_006_p0_evidence_pack.py` | 4 | **PASS** | `cor***06` | `ev_***06` | "ORDER_VERIFIED có campaign/adset/ad đầy đủ" → "ROAS/CPA/AOV dashboard cập nhật" |
| M6-SMK-007 | ADS-P0-007 | owner | `test_smk_007_p0_evidence_pack.py` | 4 | **PASS** | `cor***07` | `ev_***07` | "ORDER_VERIFIED thiếu source" → "Revenue vẫn lưu, attribution confidence LOW/HOLD" |
| M6-SMK-008 | ADS-P0-008 | owner | `test_smk_008_p0_evidence_pack.py` | 4 | **PASS** | `cor***08` | `ev_***08` | "CRM opt-out" → "Không sync CRM audience/CRM event outbound" |
| M6-SMK-009 | ADS-P0-009 | owner | `test_smk_009_p0_evidence_pack.py` | 4 | **PASS** | `cor***09` | `ev_***09` | "Recall/Sale Lock active" → "Scale Gate FAIL/HOLD" |
| M6-SMK-010 | ADS-P0-010 | owner | `test_smk_010_p0_evidence_pack.py` | 4 | **PASS** | `cor***10` | `ev_***10` | "Data Mart tạo trigger CRM/scale" → "Fail - Data Mart chỉ support view" |
| M6-SMK-011 | ADS-P0-011 | owner | `test_smk_011_p0_evidence_pack.py` | 4 | **PASS** | `cor***11` | `ev_***11` | "Learning candidate ngoài safe range" → "Hold review, không publish" |
| M6-SMK-012 | ADS-P0-012 | owner | `test_smk_012_p0_evidence_pack.py` | 4 | **PASS** | `cor***12` | `ev_***12` | "Scale request không owner approval" → "Không scale" |
| M6-SMK-013 | ADS-P0-013 | owner | `test_smk_013_p0_evidence_pack.py` | 4 | **PASS** | `cor***13` | `ev_***13` | "Live/Comment/Messenger chain" → "Trace được live_session_id, comment_id, messenger_thread_id" |
| M6-SMK-014 | ADS-P0-014 | owner | `test_smk_014_p0_evidence_pack.py` | 4 | **PASS** | `cor***14` | `ev_***14` | "Diamond referral order verified" → "Gắn referral attribution, không tự tính commission" |
| M6-SMK-015 | ADS-P0-015 | owner | `test_smk_015_p0_evidence_pack.py` | 4 | **PASS** | `cor***15` | `ev_***15` | "Dashboard hiển thị quote/order draft như revenue" → "Fail" |
| M6-SMK-016 | proposed | proposed | `test_smk_016_p0_evidence_pack.py` | 4 | **PASS** | `cor***16` | `ev_***16` | "Outbox item fails to send N times" → "Bounded retry with error_log + next_retry_at, then dead-letter; no infinite retry, no silent loss" |
| M6-SMK-017 | proposed | proposed | `test_smk_017_p0_evidence_pack.py` | 4 | **PASS** | `cor***17` | `ev_***17` | "External payload (CAPI/Offline) built from an event containing raw PII" → "Hash policy applied per M6-OD-003; no raw phone/email/user-id in the outbound payload or platform result log" |
| M6-SMK-018 | proposed | proposed | `test_smk_018_p0_evidence_pack.py` | 4 | **PASS** | `cor***18` | `ev_***18` | "Attribution correction attempted after ORDER_VERIFIED" → "Direct mutation rejected; adjustment record created with actor, reason, audit, evidence" |

**Evidence-leg nodes: 72 (18 × 4), all PASSED.**

### What each leg asserted (all 4 nodes PASS per id)

1. **Primary (scenario verbatim):** the recorded result (status `PASS` + `correlation_id` + `evidence_id`) is
   `recorded` in the assembled owner pack; with the full matrix recorded + all 10 §22 categories complete, readiness
   is the terminal `OWNER_REVIEW_REQUIRED` (never Pass/Ready), and the pack still discloses every standing blocker.
2. **Negative / fail-closed — un-run cannot be recorded:** an un-run smoke → `recorded=False`, an `UNRUN` gap
   carrying its id, readiness `NOT_READY` (M6-FAIL-007).
3. **Negative / fail-closed — waiver scope:** owner smokes 001–015 — an owner-smoke waiver is **stripped** (stays
   un-run → `NOT_READY`); proposed smokes 016–018 — a recorded owner waiver **counts** (disclosed as `waived`) →
   `OWNER_REVIEW_REQUIRED` (executed OR owner-waived).
4. **PII-safe:** `to_public()` masks `correlation_id`/`evidence_id` (masked ≠ raw; raw id absent from the public view).

## Supporting / regression coverage (inside the 523 full suite, all green)

The full staged suite re-ran green: the **carried behavioral legs** for all 18 smoke ids (the "executed" half of each
smoke — e.g. `test_smk_001_event_not_in_registry.py`, `test_smk_008_crm_optout_no_sync.py`,
`test_smk_017_hash_policy_no_raw_pii.py`), the coder's **evidence-pack tests** T1–T6
(`test_pack_never_declares_pass_or_ready.py`, `test_evidence_ten_categories_mandatory_content.py`,
`test_gap_blocker_list_carries_standing_blockers.py`, `test_pack_posture_immutable_and_pii_safe.py`,
`test_smoke_registry_complete_18.py`, `test_full_p0_matrix_runs_green.py`), and the carried M6.2A–J unit/regression
suites. Full total **523 passed, 0 failed** (= carried baseline 451 + the 72 new evidence-leg nodes).

## Commands run (from `04-artifacts/impl/M6.2K/`, no shell redirection, cache-free)

The role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path, so no redirection is used;
`PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider` keep the run cache-free (no `__pycache__` / `.pytest_cache`).

```bash
# 1) full staged suite + per-smoke tally, counted in-process via pytest_runtest_logreport
python.exe -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider']); pytest stdout swallowed>"
#   -> RC 0 ; COUNTS passed=523 failed=0 skipped=0 error=0 ; FAILS [] ; each evidence leg pass=4 fail=0

# 2) the 18 evidence legs isolated (cross-check)
python.exe -c "<tally; pytest.main(['tests/smoke','-k','p0_evidence_pack','-p','no:cacheprovider'])>"
#   -> RC 0 ; SUBSET passed=72 failed=0 skipped=0 error=0 ; FAILS []
```

> **On counting.** In this harness pytest's terminal summary line is not reliably captured for a long `-q` run, so
> the full-suite total (**523**) and the per-smoke breakdown were obtained via an in-process
> `pytest_runtest_logreport` tally (`passed=523, failed=0, skipped=0, error=0`) with `pytest.main() RC=0` and an
> empty failure list; the isolated 18-leg run independently confirms `72 passed`. pytest's own per-item output was
> swallowed (`redirect_stdout`) so the tally prints cleanly.

## Correlation / evidence ids (all synthetic; masked on export)

The recorded `correlation_id` / `evidence_id` per smoke (`corr_0NN` / `ev_0NN` from the `all_smokes_recorded`
fixture) are **synthetic** — never real customer data — and are **masked on every export** via
`app.measurement.masking.mask` (e.g. `corr_001 → cor***01`, `ev_001 → ev_***01`). No raw phone / email / address /
customer_id / guest_id / psid / token appears in any test, log, or this report (RULE-014 / H02).

## Boundary / safety observed during this run

- **No overstated readiness (M6-RULE-015 / M6-FAIL-007 / doc §23):** the assembled pack reaches `OWNER_REVIEW_REQUIRED`
  only when the full matrix is recorded + all 10 categories complete, and is fail-closed `NOT_READY` otherwise; there
  is no Pass/Ready/certify/flag-flip method. Nothing here declares ROAS Pass or Scale Ready.
- **Honest gap/blocker list always disclosed:** the 8 standing blockers remain in every assembled pack.
- **PII-safe:** correlation/evidence ids masked on export; all ids synthetic.
- **No fix to code under test:** all 523 passed, so nothing needed reporting as a failure, and nothing was patched.
  No application code / migration / external call / CRM send / commission / Data-Mart trigger / Core override /
  order-state / pricing / flag flip / `04-artifacts/state/` write occurred.

## Exit-gate legs closed by this run (slice M6.2K done-gate)

| Leg | Requirement | Status |
|---|---|---|
| 1 (L1) | Evidence pack ready for review: all P0 smokes re-run with recorded correlation_id + evidence_id; the 10 §22 categories are assembled by the PM (M6-P2007) | smoke re-run + per-smoke ids recorded **here**; category assembly + owner package = M6-P2007 |
| 2–16 | Smoke M6-SMK-001 … M6-SMK-015 executed with recorded result + evidence ref | **PASS** (4/4 each) |
| 17 | Proposed smoke M6-SMK-016 executed OR owner-waived | **PASS** (4/4) — executed |
| 18 | Proposed smoke M6-SMK-017 executed OR owner-waived | **PASS** (4/4) — executed |
| 19 | Proposed smoke M6-SMK-018 executed OR owner-waived | **PASS** (4/4) — executed |

> This run does NOT self-certify gate advancement (M6-RULE-015). It is the honest executed-results record of the
> TESTER. The runner EVIDENCE_GATE and the slice Judge (M6-P2009) decide closure; M6-P2005 (boundary adversary),
> M6-P2006 (security/PII), and the PM evidence-collect M6-P2007 (10-category owner package) come next. Production /
> gateway / external_send stay immutably OFF through M6.2K and into PR/PILOT.
