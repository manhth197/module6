# SMOKE_RESULTS — Slice M6.2P (external_send_policy enum, B5 / M6-OD-003 enum half)

| Field | Value |
|---|---|
| Prompt | M6-P2404 — `M6_2P_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test** — the M6.2P smoke suite is EXECUTED here and results recorded. The smoke leg was authored in M6-P2403 (`M6_2P_TESTER_BUILD`). |
| Smoke ids executed | **M6-SMK-028** (1 `proposed — HARDENING, owner review`; executed here, not owner-waived) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0**, run `-B` (`PYTHONDONTWRITEBYTECODE=1`), `-p no:cacheprovider` |
| Staging root | `04-artifacts/impl/M6.2P/` (STAGED_ONLY; cumulative superset of M6.2O) |
| Evidence-leg result | **4 passed, 0 failed — exit 0** |
| Full staged suite | **603 passed, 0 failed, 0 skipped, 0 error — RC 0** |
| Overall | **the bound smoke id PASS; no failures; nothing patched; the enum vocabulary is real + fail-closed; NO egress opened** |

> **Governance (immutable — nothing in this run flips a flag or opens egress):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` (Final), all scale/hash/learning flags
> `False`, `live_migrations=false`. No application code changed by the TESTER, no migration, no external call, no flag
> flipped. The smoke READS `config.EXTERNAL_SEND` (asserts `OFF`, never assigns it) and classifies no real registry
> event ALLOW_EXTERNAL. `M6-P1000` / `M6-P1309` stay BLOCKED. **HARD FORWARD CONDITION** (disclosed, not resolved
> here): the M6-OD-003 permit-mapping + hash policy (privacy/legal, Sếp) stay OPEN — no event may be classified
> ALLOW_EXTERNAL and no real egress may open until decided; the exit judge M6-P2409 confirms no registry row is
> ALLOW_EXTERNAL and EXTERNAL_SEND stays Final OFF. `status` is an honest TESTER self-report; the runner EVIDENCE_GATE
> + slice Judge (M6-P2409) decide closure.

## Per-smoke results (scenario / expected verbatim from SMOKE_REGISTER; PASS)

The `correlation_id` / `evidence_id` are **synthetic** doc-§22-style trace ids, shown export-masked
(`app.measurement.masking.mask`, RULE-014/H02); raw synthetic values `corr_2p_028` / `ev_2p_028`.

| Smoke ID | Fix | Test file (`tests/smoke/…`) | Nodes | Result | correlation_id (masked) | evidence_id (masked) | Scenario → Expected (verbatim) |
|---|---|---|---|---|---|---|---|
| M6-SMK-028 | B5 external_send_policy enum | `test_smk_028_external_send_policy_enum.py` | 4 | **PASS** | `cor***28` | `ev_***28` | "event_registry row with external_send_policy = each of ALLOW_EXTERNAL / INTERNAL_ONLY / BLOCKED_PII / BLOCKED_DEFAULT + a None/blank/unknown token (B5)" → "typed ExternalSendPolicy enum; permits_external_send() True ONLY for ALLOW_EXTERNAL; None/blank/unknown coerces fail-closed to BLOCKED_DEFAULT (no crash, no auto-allow); every real ACCEPTED event still send_permitted=False (no event is ALLOW_EXTERNAL) and EXTERNAL_SEND stays OFF" |

**Evidence-leg nodes: 4, all PASSED.**

### M6-SMK-028 — external_send_policy typed fail-closed enum · **PASS (4/4)**

- `test_smk_028_each_policy_value_gates_permits_only_allow_external` (primary) — PASS: the enum has exactly the 4
  owner-signed values; an event_registry row carrying EACH value validates ACCEPTED and `external_send_permitted` is
  True **iff** ALLOW_EXTERNAL (`permits_external_send` agrees).
- `test_smk_028_neg_none_blank_unknown_token_is_failclosed_blocked_default` — PASS: None / "" / "   " / tab /
  unknown token ("MAYBE","allow","ALLOW","true") / non-coercible (`123`, `0`, `object()`, `b"ALLOW_EXTERNAL"`) all
  `_resolve_send_policy` → `BLOCKED_DEFAULT` (never crash, never auto-allow); a row with such a token validates
  ACCEPTED with `external_send_permitted False`.
- `test_smk_028_neg_real_accepted_event_stays_send_permitted_false` — PASS: the conftest VIEW_LANDING (ACTIVE + owner
  + `external_send_policy=None`) validates ACCEPTED with `external_send_permitted False` — no real registry event is
  ALLOW_EXTERNAL (permit-mapping OPEN).
- `test_smk_028_control_allow_external_gates_true_but_external_send_off` — PASS (non-vacuity + defense-in-depth): an
  explicitly ALLOW_EXTERNAL row makes the policy gate genuinely True (the gate is real, not a dead hard-False) **yet**
  `config.EXTERNAL_SEND == "OFF"` (independent second gate → no real egress).

## Supporting / regression coverage (inside the 603 full suite, all green)

The full staged suite re-ran green: the coder's B5 regression test (`tests/test_m6_2p_external_send_policy.py`), the
carried M6.2A–O tree (incl. the M6.2N/O B1 psid_hash + F2-6 duck-coerce work), and the evidence-pack + P0-smoke
suites. Full total **603 passed, 0 failed** (= 599 coder M6.2P baseline + the 4 new official-smoke nodes).

## Commands run (from `04-artifacts/impl/M6.2P/`, no shell redirection, cache-free)

The role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path, so no redirection is used; `-B`
(`PYTHONDONTWRITEBYTECODE=1`) + `-p no:cacheprovider` keep the run cache-free.

```bash
# 1) full staged suite + per-smoke tally, counted in-process via pytest_runtest_logreport
python.exe -B -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider']); pytest stdout swallowed>"
#   -> RC 0 ; COUNTS passed=603 failed=0 skipped=0 error=0 ; FAILS [] ; SMK-028 4/4

# 2) the evidence leg isolated (cross-check, with node names)
python.exe -B -c "<tally; pytest.main(['tests/smoke/test_smk_028_external_send_policy_enum.py','-p','no:cacheprovider'])>"
#   -> RC 0 ; SUBSET passed=4 failed=0 skipped=0 error=0 ; FAILS [] ; 4 node names present (primary + 2 neg + control)
```

> **On counting.** pytest's terminal summary is not reliably captured in this harness, so the full-suite total
> (**603**) and the per-smoke breakdown came from an in-process `pytest_runtest_logreport` tally
> (`passed=603, failed=0, skipped=0, error=0`) with `pytest.main() RC=0`; the isolated leg run independently confirms
> `4 passed`. pytest's own per-item output was swallowed (`redirect_stdout`).

Cache hygiene: `-B` / `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider`; no `__pycache__` / `.pytest_cache` written.

## Boundary / safety observed during this run

- **Fail-closed egress vocabulary (RULE-014 / FAIL-007):** nothing that is not the value ALLOW_EXTERNAL becomes
  ALLOW_EXTERNAL; None/blank/unknown → BLOCKED_DEFAULT; `permits_external_send` True only for ALLOW_EXTERNAL; every
  real ACCEPTED event stays `send_permitted=False`.
- **No egress opened, no flag flipped:** the smoke READS `config.EXTERNAL_SEND == "OFF"` (never writes it), classifies
  no real event ALLOW_EXTERNAL (the ALLOW_EXTERNAL row is a synthetic in-test `_Reg` control), and flips no flag.
  Posture BLOCKED/OFF/OFF unchanged.
- **No fix to code under test:** all 603 passed, so nothing needed reporting as a failure, and nothing was patched.
  No application code / migration / external call / flag flip / `04-artifacts/state/` write occurred.

## Exit-gate legs closed by this run (slice M6.2P done-gate)

| Leg | Requirement | Status |
|---|---|---|
| 1 | external_send_policy typed enum + fail-closed (4 values; None/blank/unknown → BLOCKED_DEFAULT; permits True only ALLOW_EXTERNAL; every real ACCEPTED event send_permitted=False; EXTERNAL_SEND OFF) | met — SMK-028 + coder `tests/test_m6_2p_external_send_policy.py` green |
| 2 | Proposed smoke M6-SMK-028 executed | **PASS** (4/4) — executed |

> This run does NOT self-certify gate advancement (RULE-015). It is the honest executed-results record of the TESTER.
> The runner EVIDENCE_GATE and the slice Judge (M6-P2409) decide closure; M6-P2405 (boundary), M6-P2406 (security/PII),
> and the PM evidence-collect M6-P2407 come next. Posture stays BLOCKED/OFF/OFF; the M6-OD-003 hard forward condition
> remains open for the exit judge (no event ALLOW_EXTERNAL, EXTERNAL_SEND stays Final OFF).
