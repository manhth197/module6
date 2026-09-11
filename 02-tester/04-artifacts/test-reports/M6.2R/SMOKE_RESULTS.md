# SMOKE_RESULTS — Slice M6.2R (recall-risk mapper: ops-core availability → Scale-Gate risk_flags, E2 §3/§5, M6-OD-017)

| Field | Value |
|---|---|
| Prompt | M6-P2604 — `M6_2R_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test** — the M6.2R smoke suite is EXECUTED here and results recorded. The smoke leg was authored in M6-P2603 (`M6_2R_TESTER_BUILD`). |
| Smoke ids executed | **M6-SMK-030** (1 — `proposed — HARDENING, owner review`; executed here, not owner-waived) |
| Verify env | `02-tester/.venv` — **python 3.12.14 · pytest 8.4.2 · pluggy 1.6.0**, run `-B` (`PYTHONDONTWRITEBYTECODE=1`), `-p no:cacheprovider` |
| Staging root | `04-artifacts/impl/M6.2R/` (STAGED_ONLY; cumulative superset of M6.2Q) |
| Evidence-leg result | **11 passed, 0 failed — exit 0** |
| Full staged suite | **658 passed, 0 failed, 0 skipped, 0 error — RC 0** |
| Overall | **the bound smoke id PASS; no failures; nothing patched; the mapper feeds the existing Scale Gate; no egress, no real network** |

> **Governance (immutable — nothing in this run flips a flag, opens egress, builds a live client, or calls a real network):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `SCALE_MODEL_RATIFIED=False`,
> `live_migrations=false`. The ops-core availability response is a value object / dict built in-test (STAGED); the
> live HTTP client to ops-core `POST /v1/availability/check` is the S1b seam / go-live and is **not** built or
> called. No application code changed by the TESTER, no gate-logic change, no migration, no external call / real
> Meta or ops-core network. Refs are campaign/SKU refs (not PII); actors masked; no raw secret/PII. `M6-P1000` /
> `M6-P1309` stay BLOCKED. **HARD FORWARD CONDITIONS** (disclosed, not resolved here): M6-OD-002 (thresholds) OPEN;
> the S1b live-HTTP client + campaign→SKU join + M3 block_reason/pause-SLA + M6-OD-011 server-bind/go-live before
> any live recall pull / real scale / egress. `status` is an honest TESTER self-report; the runner EVIDENCE_GATE +
> the slice Judge (M6-P2609) decide closure.

## Per-smoke results (scenario / expected verbatim from SMOKE_REGISTER row M6-SMK-030; PASS)

The `correlation_id` / `evidence_id` are **synthetic** trace ids, shown export-masked
(`app.measurement.masking.mask`, RULE-014); raw synthetic values `corr_2r_030` / `ev_2r_030`.

| Smoke ID | Fix | Test file (`tests/smoke/…`) | Nodes | Result | correlation_id (masked) | evidence_id (masked) | Scenario → Expected (verbatim) |
|---|---|---|---|---|---|---|---|
| M6-SMK-030 | E2 §3/§5 recall-risk mapper → existing Scale Gate (M6-OD-017) | `test_smk_030_recall_risk_mapper_to_scale_gate.py` | 11 | **PASS** | `cor***30` | `ev_***30` | "Ops-core availability responses fed to the M6 recall mapper: (i) decision=SELLABLE + recall_hold=true (clean-lot); (ii) recall_case_open=true (additive); (iii) a pull error/timeout/429" → "mapper sets risk_flags['recall']=recall_hold OR recall_case_open, sale_lock, quality_hold; Scale-Gate Risk row FAILs on any presence-flag true EVEN when decision=SELLABLE; the mapper never reads decision/block_reasons; a pull error → incomplete/unknown risk read → gate FAIL (fail-closed, RULE-017); no PII, external_send OFF" |

**Evidence-leg nodes: 11, all PASSED.**

### M6-SMK-030 — recall-risk mapper → Scale Gate · **PASS (11/11)**

- `test_smk_030_scenario_i_recall_hold_maps_and_gate_fails_even_when_sellable` (scenario i) — PASS: a clean-lot
  response (decision=SELLABLE) with `recall_hold=true` maps to `risk_flags['recall']=True` (sale_lock/quality_hold
  map through); fed to the existing Scale Gate the Risk row is **FAIL despite SELLABLE**, and an owner APPROVE is
  refused (`ScaleGateViolation`, RULE-017 re-check) — the request stays PROPOSED / not authorized.
- `test_smk_030_scenario_ii_recall_case_open_additive_and_gate_fails` (scenario ii) — PASS: `recall_case_open=true`
  with `recall_hold=false` → `recall=True` (additive OR); Risk **FAIL despite SELLABLE** + approve refused; and the
  additive default (absent → false → recall follows recall_hold only).
- `test_smk_030_scenario_iii_pull_error_incomplete_gate_does_not_clear` **[read0..4]** (scenario iii, ×5:
  TIMEOUT / HTTP_429 / CONNECTION_ERROR / None / malformed) — PASS: an incomplete/unknown risk read is empty (never
  a False false-clear, never a fabricated True); the Risk row is fail-closed **HOLD** (not PASS), and the owner
  APPROVE is refused (the gate **does not clear**). See the traceability note below on "gate FAIL" vs asserted HOLD.
- `test_smk_030_neg_mapper_never_reads_decision_or_block_reasons` — PASS: decision=SELLABLE + block_reasons cannot
  clear a present `recall_hold` (recall stays True); a scary decision string + block_reasons cannot fabricate a lock
  (clean maps to Risk PASS — non-vacuous).
- `test_smk_030_neg_malformed_or_nonbool_presence_flag_is_failclosed` — PASS: a missing key (dict path) or a non-bool
  value (None/0/1/`"false"`/`"true"`/`()`/`[]` via the value-object path) is an incomplete empty read, never
  `bool()`-coerced to a clear; the empty read is HOLD at the gate.
- `test_smk_030_control_clean_complete_read_maps_non_empty` — PASS (non-vacuous control): a clean complete read maps
  to the non-empty `{recall:False, sale_lock:False, quality_hold:False}` (so the empties above are error-caused);
  `RECALL_RISK_KEYS < RISK_LOCKS` (strict 3-of-6), and the bare merge collapses to `{}` (partial, never a standalone
  clearing map).
- `test_smk_030_no_pii_external_send_off_and_posture_unchanged` — PASS: `config.EXTERNAL_SEND == "OFF"`,
  `config.PRODUCTION_FLAG == "OFF"`, `config.GLOBAL_GATEWAY_STATE == "BLOCKED"`; the mapper module imports no
  HTTP/transport surface (no `requests`/`httpx`/`urllib`/`http.client`/`socket` — the S1b live client is not built);
  `sku_ref`/`decision`/`block_reasons` never enter `risk_flags`.

## Supporting / regression coverage (inside the 658 full suite, all green)

The full staged suite re-ran green: the coder's A5/M6.2R regression tests (`tests/test_m6_2r_recall_risk_mapper.py`,
16 cases), the carried M6.2A–Q tree, and the evidence-pack + P0-smoke suites. Full total **658 passed, 0 failed**
(= 647 coder M6.2R baseline + the 11 new official-smoke nodes). The sibling risk-lock smoke
`tests/smoke/test_smk_009_recall_sale_lock_scale_fail.py` and the scale-gate carried tests re-ran green.

## Commands run (from `04-artifacts/impl/M6.2R/`, no shell redirection, cache-free)

The role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path, so no redirection is used; `-B`
(`PYTHONDONTWRITEBYTECODE=1`) + `-p no:cacheprovider` keep the run cache-free.

```bash
# 1) full staged suite + per-smoke tally, counted in-process via pytest_runtest_logreport
python.exe -B -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider']); pytest stdout swallowed>"
#   -> RC 0 ; passed=658 failed=0 skipped=0 error=0 ; FAILS [] ; SMK-030 11/11

# 2) the evidence leg isolated (cross-check)
python.exe -B -c "<tally; pytest.main(['tests/smoke/test_smk_030_recall_risk_mapper_to_scale_gate.py','-p','no:cacheprovider'])>"
#   -> RC 0 ; passed=11 failed=0 skipped=0 error=0 ; FAILS []
```

> **On counting.** pytest's terminal summary is not reliably captured in this harness, so the full-suite total
> (**658**) and the per-smoke breakdown came from an in-process `pytest_runtest_logreport` tally
> (`passed=658, failed=0, skipped=0, error=0`) with `pytest.main() RC=0`; the isolated leg run independently confirms
> `11 passed`. pytest's own per-item output was swallowed (`redirect_stdout`/`redirect_stderr`). The build-side
> collect-only count (M6-P2603) was 658, matching this executed total.

## Boundary / safety observed during this run

- **Presence booleans only (M6-OD-017, RULE-018):** the mapper produced `recall`/`sale_lock`/`quality_hold` from
  the presence booleans and never read `decision`/`block_reasons`; a SELLABLE decision did not clear a present lock.
- **Risk hard veto (RULE-017):** a mapped present lock (recall_hold or recall_case_open) forced the existing Scale
  Gate Risk row to FAIL and refused the owner approve — no gate-logic change.
- **Fail-closed on pull error (leg iii):** an incomplete/unknown read (timeout / 429 / connection error / None /
  malformed / non-bool) left the locks unobserved → the gate did **not** clear (Risk HOLD, approve refused). See the
  traceability note below.
- **No egress, no flag flipped, no real network:** the smoke READS `config.EXTERNAL_SEND == "OFF"` (and
  PRODUCTION_FLAG OFF / GLOBAL_GATEWAY_STATE BLOCKED), used only an in-test value object / dict, and wrote nothing to
  `04-artifacts/state/`. The mapper imports no HTTP/transport (the S1b live client is not built). No raw PII
  (campaign/SKU refs; masked actors).
- **No fix to code under test:** all 658 passed, so nothing needed reporting as a failure, and nothing was patched.
  No application code / gate-logic change / migration / external call / flag flip / `04-artifacts/state/` write.

> **Traceability note (non-blocking, for the boundary adversary + judge).** SMOKE_REGISTER phrases the leg-(iii)
> pull-error outcome as "gate FAIL", while scenario (iii) asserts the Risk row is `DataQualityStatus.HOLD` plus a
> refused owner APPROVE (`ScaleGateViolation`). This is the correct fail-closed **does-not-clear** semantics — an
> unobserved risk read is HOLD (never PASS), the approval is refused, and the request stays PROPOSED — matching the
> frozen `conditions._risk` (empty `risk_flags` → HOLD) and the sibling SMK-009 "FAIL/HOLD" pairing (HOLD is the
> unobserved-risk half). The slice exit-gate check #3 itself frames the incomplete read as "does not clear". The
> per-test docstring states HOLD honestly rather than claiming a FAIL status. The independent adversarial
> static-verification pass (M6-P2603, run wf_75ddbbea-b00) flagged only this same non-material mapping and was
> otherwise all-CLEAN.

## Exit-gate legs closed by this run (slice M6.2R done-gate)

| Leg | Requirement | Status |
|---|---|---|
| 1 | E2 mapping (M6-OD-017): recall = recall_hold OR recall_case_open, sale_lock, quality_hold; additive; no fabricated lock; presence booleans only | met — SMK-030 scenario i/ii + neg-decision-never-read + control + coder `test_m6_2r_recall_risk_mapper.py` green |
| 2 | presence-flag FAIL even when SELLABLE: a mapped present lock fails the existing Scale-Gate Risk row despite decision==SELLABLE (recall_hold and recall_case_open) | met — SMK-030 scenario i + scenario ii |
| 3 | fail-closed on pull error: a pull error/timeout/429/None/malformed → INCOMPLETE read → gate does not clear (RULE-017); no false-clear | met — SMK-030 scenario iii (×5) + non-bool neg (asserted as HOLD + approve refused; see traceability note) |
| 4 | Proposed smoke M6-SMK-030 executed | **PASS** (11/11) — executed |

> This run does NOT self-certify gate advancement (RULE-015). It is the honest executed-results record of the TESTER.
> The runner EVIDENCE_GATE and the slice Judge (M6-P2609) decide closure; M6-P2605 (boundary), M6-P2606
> (security/PII), and the PM evidence-collect M6-P2607 come next. Posture stays BLOCKED/OFF/OFF; the M6-OD-002 +
> M6-OD-011 hard forward conditions remain open for the exit judge (no real spend/egress until decided).
