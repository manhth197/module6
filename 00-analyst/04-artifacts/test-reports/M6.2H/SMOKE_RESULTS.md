# SMOKE_RESULTS — Slice M6.2H (ADS Strategy Libraries / Learning Engine)

| Field | Value |
|---|---|
| Prompt | M6-P1704 — `M6_2H_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test** — the M6.2H smoke suite is EXECUTED here and results recorded. Smoke file was authored in M6-P1703 (`M6_2H_TESTER_BUILD`). |
| Smoke ids executed | **M6-SMK-011** (the single bound id) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Staging root | `04-artifacts/impl/M6.2H/` (STAGED_ONLY; convention reference, not a live repo) |
| Bound-smoke result | **6 passed, 0 failed — exit 0** |
| Full staged suite | **351 passed, 0 failed, 0 skipped, 0 error — RC 0** |
| Overall | **the bound smoke id PASSES; no failures; nothing patched; nothing published** |

> **Governance (immutable — nothing in this run flips a flag, and nothing is ever published):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `LEARNING_AUTOPUBLISH_ENABLED=False`,
> `LEARNING_SAFE_RANGE_RATIFIED=False` (M6-OD-006 OPEN), `LEARNING_CONTENT_FILL_ENABLED=False` (M6-OD-007 OPEN),
> `SCALE_EXECUTION_ENABLED=False`, `SCALE_MODEL_RATIFIED=False`. The machine never fabricates origin strategy
> (RULE-011 / LEX-006) and there is no auto-publish path (RULE-011 / FAIL-006): a candidate outside/UNKNOWN the
> safe range is HELD in review and never published; a publish is authorized only via an explicit owner APPROVE
> **and** a WITHIN safe range — never reached in the staged posture. No Core-policy write (RULE-013/018), no
> pricing (M3), consult (M4), public reply (M5), order-state (M8), CRM send, or commission (RULE-019). `status`
> is an honest self-report; the runner EVIDENCE_GATE and the slice Judge (M6-P1709) decide closure.

## Per-smoke results (scenario / expected verbatim from SMOKE_REGISTER)

| Smoke ID | Doc ID | Test file | Nodes | Result | Scenario → Expected (verbatim) |
|---|---|---|---|---|---|
| M6-SMK-011 | ADS-P0-011 | `tests/smoke/test_smk_011_learning_candidate_outside_safe_range_holds.py` | 6 | **PASS** | "Learning candidate ngoài safe range" → "Hold review, không publish" |

**Bound-smoke nodes: 6, all PASSED.**

### M6-SMK-011 — Learning candidate outside safe range → hold review, no publish · **PASS (6/6)**

- `test_smk_011_candidate_outside_safe_range_is_held_not_published[SafeRangeStatus.OUTSIDE]` — PASS: `review()` → HOLD, safe_range forced UNKNOWN (M6-OD-006), `is_publish_authorized` False; queue confirms HOLD.
- `test_smk_011_candidate_outside_safe_range_is_held_not_published[SafeRangeStatus.UNKNOWN]` — PASS: same fail-closed HOLD for an unknown safe range.
- `test_smk_011_neg_within_claim_is_forced_unknown_and_held` — PASS: an untrusted `WITHIN` claim is forced UNKNOWN and HELD (fail-closed).
- `test_smk_011_neg_no_auto_publish_method_and_guarded_publish_blocked` — PASS: the learning layer exposes no `publish/auto_publish/go_live/launch/execute/send` method; `guarded_publish_blocked()` is True; `LEARNING_AUTOPUBLISH_ENABLED` / `LEARNING_SAFE_RANGE_RATIFIED` False; posture flags immutable.
- `test_smk_011_neg_owner_approve_still_not_publishable_while_safe_range_unknown` — PASS: a recorded owner APPROVE leaves `is_publish_authorized` False (safe range stays UNKNOWN).
- `test_smk_011_control_publish_authorized_is_discriminating_but_unreachable` — PASS: a directly-constructed APPROVED + WITHIN candidate would be publish-authorized (property discriminating), but `review()` forces UNKNOWN so no reviewed candidate reaches WITHIN.

## Supporting / regression coverage (inside the 351 full suite, all green)

The M6.2H learning leg tests authored by the coder (M6-P1702) re-ran green as supporting coverage:
`test_candidate_outside_safe_range_holds.py` (3), `test_no_auto_publish_review_queue_only.py` (4),
`test_learn_precondition_seed_and_dq.py` (3), `test_libraries_seed_from_canon_only.py` (15),
`test_content_fill_halts_at_framework.py` (3), `test_mapping_chain_anchored_to_sku.py` (4) — plus the carried
M6.2A–G tree (313). Full total **351 passed, 0 failed**.

## Commands run (from `04-artifacts/impl/M6.2H/`, no shell redirection, cache-free)

The role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path, so no redirection is used;
`PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider` keep the run cache-free.

```bash
# 1) the bound M6.2H smoke file (verbose)
python.exe -m pytest -v tests/smoke/test_smk_011_learning_candidate_outside_safe_range_holds.py -p no:cacheprovider
#   -> 6 passed in 0.06s ; EXIT 0

# 2) the full staged suite, counted via an in-process pytest_runtest_logreport tally
python.exe -c "<pytest_runtest_logreport tally + pytest.main(['-q','-p','no:cacheprovider'])>"
#   -> COUNTS={'passed': 351, 'failed': 0, 'skipped': 0, 'error': 0} RC=0 ; FAILS=[]
```

> **On counting.** In this harness pytest's terminal summary line is not reliably captured for a long `-q` run,
> so the full-suite total (**351**) was obtained via an in-process `pytest_runtest_logreport` tally
> ({passed:351, failed:0, skipped:0, error:0}) with `pytest.main() RC=0` and an empty failure list — all
> agreeing with the M6-P1703 `--collect-only` total of 351. The smoke file's `6 passed` summary IS captured.

Cache hygiene: `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

## Correlation / trace ids (all synthetic; PII masked on export)

All ids exercised are **synthetic**, never real customer data: candidate ids `lc_out`, `lc_within_claim`,
`lc_appr`, `lc_ctrl`, `lc_ctrl2`; `sku_ref` `SKU_HERO_1` (a sellable-SKU reference, not PII); owner-decision
`actor` `owner_ops` (a synthetic operator id, masked on export via `app.measurement.masking.mask`). No raw phone
/ email / address / customer_id / guest_id / psid / token appears in any test, log, or this report (RULE-014 /
H02).

## Boundary / safety observed during this run

- **No auto-publish (RULE-011, LEX-006, FAIL-006):** the engine / queue / store exposed no
  publish/auto-publish/go-live/execute/send method; `guarded_publish_blocked()` True; nothing was published; a
  candidate outside the safe range was HELD.
- **Fail-closed safe range (M6-OD-006):** `review()` forced UNKNOWN while the safe range is unratified; even an
  owner APPROVE never yielded `is_publish_authorized` True.
- **No fabricated origin (RULE-011, LEX-006):** exercised via the supporting seed/content tests — canonical seed
  only, content None while M6-OD-007 OPEN.
- **No fix to code under test:** all 351 passed, so nothing needed reporting as a failure, and nothing was
  patched. No application code / migration / external call / content generation / Core-policy write / order-state
  / pricing / CRM send / commission / flag flip / `04-artifacts/state/` write occurred.

## Exit-gate legs closed by this run (slice M6.2H done-gate)

| Leg | Requirement | Status |
|---|---|---|
| L1 | Seed framework pass (six libraries, seed-source constraints, machine never fabricates origin) | met — supporting `test_libraries_seed_from_canon_only.py` / `test_content_fill_halts_at_framework.py` / `test_mapping_chain_anchored_to_sku.py` green |
| L2 | No auto-publish (candidates → review queue only; publish requires owner approval / guarded safe range, BLOCKED) | met — SMK-011 + `test_no_auto_publish_review_queue_only.py` green |
| L3 | Learning-input precondition (Learn only after canonical seed + only DQ-passed verified signals) | met — supporting `test_learn_precondition_seed_and_dq.py` green |
| L4 | Smoke M6-SMK-011 executed with recorded result | **PASS** (6/6) |

> This run does NOT self-certify gate advancement (RULE-015). It is the honest executed-results record of the
> TESTER. The runner EVIDENCE_GATE and the slice Judge (M6-P1709) decide closure; M6-P1705 (boundary adversary)
> and M6-P1706 (security/PII) review the learning layer next.
