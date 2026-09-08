# TEST_MANIFEST — Slice M6.2P smoke suite (external_send_policy enum, B5 / M6-OD-003 enum half)

| Field | Value |
|---|---|
| Prompt | M6-P2403 — `M6_2P_TESTER_BUILD` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **build** — the M6.2P official smoke is AUTHORED here. This attempt ran a **collect-only build-validation** (imports/collects clean, no assertions executed) per "Build (do not yet run)"; the **formal executed-results recording** belongs to M6-P2404. |
| Executed by (formal) | M6-P2404 (`M6_2P_TESTER_RUN`) → `04-artifacts/test-reports/M6.2P/SMOKE_RESULTS.md` |
| Smoke ids in scope | **M6-SMK-028** (1 `proposed — HARDENING, owner review`; per `00-spec/slices/M6.2P.md` "Core smokes" + this prompt's `<smoke_ids>`) |
| Verify env | `02-tester/.venv` — **python 3.12.13 · pytest 8.4.2 · pluggy 1.6.0** (matches `IMPLEMENTATION_TARGET_LOCKED.json` 3.12 pin) |
| Slice scope | Adopt the owner-signed (QĐ-1, 2026-09-07) `ExternalSendPolicy` 4-value enum as typed, fail-closed code — replacing the raw `Optional[str]` token in `models/consumed.py` + the hard-False `permits_external_send()` in `registry/validator.py`. Makes the enum vocabulary real + fail-closed only; **opens NO egress** (no event is ALLOW_EXTERNAL; `EXTERNAL_SEND` stays Final OFF); depends on nothing from M3/Sếp. |
| Staging root | `04-artifacts/impl/M6.2P/` (STAGED_ONLY; cumulative superset of M6.2O) |
| Source of truth | `00-spec/registers/SMOKE_REGISTER.md` (proposed additions row M6-SMK-028) + `00-spec/slices/M6.2P.md` |

> **Governance (immutable — nothing in this suite flips a flag or opens egress):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` (Final), all scale/hash/learning flags
> `False`, `live_migrations=false`. No application code changed by the TESTER, no migration, no external call, no flag
> flipped. The smoke asserts `config.EXTERNAL_SEND == "OFF"` (reads, never writes) and never classifies a real
> registry event ALLOW_EXTERNAL. `M6-P1000` / `M6-P1309` stay BLOCKED. **HARD FORWARD CONDITION** (disclosed, not
> resolved here): the M6-OD-003 permit-mapping + hash policy (privacy/legal, Sếp) stay OPEN — no event may be
> classified ALLOW_EXTERNAL and no real egress may open until decided; the exit judge M6-P2409 confirms no registry
> row is ALLOW_EXTERNAL and EXTERNAL_SEND stays Final OFF. `status` is an honest TESTER self-report; the runner
> EVIDENCE_GATE + slice Judge (M6-P2409) decide closure.

## What this suite is

One **official smoke leg** for M6-SMK-028, carrying the register scenario/expected **verbatim** and proving the typed
fail-closed `ExternalSendPolicy` enum through the frozen M6.2P validator. It **coexists with the coder's regression
test** (`tests/test_m6_2p_external_send_policy.py`, M6-P2402) and reuses the shared
[`tests/conftest.py`](04-artifacts/impl/M6.2P/tests/conftest.py) `validator` fixture (VIEW_LANDING: ACTIVE + owner +
`external_send_policy=None` → coerced BLOCKED_DEFAULT) plus the coder's `_Reg` stub pattern. **No production code** and
**no fix to the code under test**. All event codes are synthetic.

## Smoke → test binding (scenario/expected verbatim from SMOKE_REGISTER)

| Smoke ID | Fix | Test file (`tests/smoke/…`) | Nodes | Primary (scenario verbatim) | Negatives / control | Rule(s) | Fail gate | Exit leg |
|---|---|---|---|---|---|---|---|---|
| M6-SMK-028 | B5 external_send_policy enum | `test_smk_028_external_send_policy_enum.py` | 4 | `test_smk_028_each_policy_value_gates_permits_only_allow_external` | `..._neg_none_blank_unknown_token_is_failclosed_blocked_default`, `..._neg_real_accepted_event_stays_send_permitted_false`, `..._control_allow_external_gates_true_but_external_send_off` | M6-RULE-014, M6-RULE-015 | M6-FAIL-007 | 1 / 2 |

**New M6.2P official-smoke nodes: 4.**

## Per-smoke summary (what the leg proves)

- **Primary (scenario verbatim):** the enum has exactly the 4 owner-signed values {ALLOW_EXTERNAL, INTERNAL_ONLY,
  BLOCKED_PII, BLOCKED_DEFAULT}; an event_registry row carrying EACH value validates ACCEPTED and its resolved
  `external_send_permitted` is True **iff** the policy is ALLOW_EXTERNAL (and `permits_external_send` agrees).
- **Negative / fail-closed:** `_resolve_send_policy` maps None / blank / whitespace / an unknown token / non-coercible
  junk (`123`, `object()`, `b"ALLOW_EXTERNAL"`, `"allow"`, `"true"`) → `BLOCKED_DEFAULT` (never crash, never
  auto-allow); a row carrying such a token validates ACCEPTED with `external_send_permitted False`.
- **Negative / real-world:** the conftest VIEW_LANDING row (policy=None) → ACCEPTED, `external_send_permitted False` —
  no real registry event is ALLOW_EXTERNAL (permit-mapping OPEN).
- **Control / defense-in-depth:** an explicitly ALLOW_EXTERNAL row makes the policy gate genuinely True (the gate is
  real, not a dead hard-False) **yet** `config.EXTERNAL_SEND == "OFF"` — no real egress opens; the slice flips no flag.

## Fixtures / APIs under test (from `tests/conftest.py` + the frozen app)

| Fixture / API | Role |
|---|---|
| `validator` (conftest) | `EventValidator` over the seeded registry (VIEW_LANDING policy=None) — the real-ACCEPTED-event case |
| `app.measurement.models.consumed.ExternalSendPolicy` | the owner-signed 4-value enum {ALLOW_EXTERNAL, INTERNAL_ONLY, BLOCKED_PII, BLOCKED_DEFAULT} |
| `app.measurement.registry.validator._resolve_send_policy` | fail-closed coercion (member/token → member; None/blank/unknown/non-coercible → BLOCKED_DEFAULT) |
| `app.measurement.registry.validator.permits_external_send` | True ONLY for ALLOW_EXTERNAL |
| `EventValidator(_Reg([row]), AuditLog()).validate(code)` | end-to-end validate → `ValidationResult.accepted` + `.external_send_permitted` |
| `EventRegistryRow`, `RegistrationState`, `AuditLog`, `config.EXTERNAL_SEND` | build seeded rows + read the immutable second-gate flag |

## Boundary / safety asserted by the suite

- **Fail-closed egress vocabulary (RULE-014 / FAIL-007):** nothing that is not the value ALLOW_EXTERNAL ever becomes
  ALLOW_EXTERNAL; None/blank/unknown → BLOCKED_DEFAULT; `permits_external_send` True only for ALLOW_EXTERNAL.
- **No egress opened, no flag flipped:** the smoke reads `config.EXTERNAL_SEND == "OFF"` (never writes it), classifies
  no real event ALLOW_EXTERNAL, and adds only test vocabulary. Posture BLOCKED/OFF/OFF unchanged.
- **No fix to code under test; no application code / migration / external call / flag flip / `04-artifacts/state/`
  write** by the TESTER. M6-P1000 / M6-P1309 stay BLOCKED.

## Build-validation performed in M6-P2403 (attempt 1, collect-only — "do not yet run")

Per the prompt's `<task>` ("Build (do not yet run)"), this attempt ran **collect-only** (imports + collects; **no
assertions executed**). Run with the pack venv (`02-tester/.venv`), **python 3.12.13 · pytest 8.4.2**, from
`04-artifacts/impl/M6.2P/`, **no shell redirection** (the role guard blocks a `>`/`2>` co-occurring with the venv
`Scripts` path), cache-free (`-B` / `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```bash
python.exe -B -c "<in-process pytest_collection_finish tally; pytest.main(['--collect-only','-q','-p','no:cacheprovider'])>"
#   -> RC 0 ; tests/smoke/test_smk_028_external_send_policy_enum.py collects 4 nodes ; full-suite collect clean ; 0 collection errors
```

Reconciliation: the full-suite collect total = M6.2P coder baseline **599** (593 carried M6.2O + 6 coder M6.2P
regressions) + these **4** new official-smoke nodes = **603**. A read-only **adversarial static verification**
(1 logic verifier + a verbatim-string auditor + a completeness/PII/egress-boundary critic) was run alongside —
findings recorded in the M6-P2403 evidence.

> **This build does NOT self-certify gate advancement.** Collect-only proves the smoke file imports + collects against
> the frozen M6.2P code; it does not execute assertions. The **formal executed-results recording** (with a
> correlation_id + evidence_id) is produced by **M6-P2404**. The runner EVIDENCE_GATE + slice Judge decide.

## Execution plan for M6-P2404 (`M6_2P_TESTER_RUN`)

```bash
python -m pytest -q                                                            # full staged suite: expected 603 passed
python -m pytest -q tests/smoke/test_smk_028_external_send_policy_enum.py       # expected 4 passed
```

Record per smoke id PASS/FAIL/BLOCKED + detail + correlation_id + evidence_id. Confirm `external_send_permitted` is
True only for the explicit ALLOW_EXTERNAL control row, every real ACCEPTED event stays False, and
`config.EXTERNAL_SEND == "OFF"`.

## Exit-gate legs (slice M6.2P done-gate, itemized)

| Leg | Requirement | Covered by |
|---|---|---|
| 1 | external_send_policy typed enum + fail-closed (4 values; None/blank/unknown → BLOCKED_DEFAULT; permits True only ALLOW_EXTERNAL; every real ACCEPTED event send_permitted=False; EXTERNAL_SEND OFF) | SMK-028 leg (built here) + coder `tests/test_m6_2p_external_send_policy.py`; run by M6-P2404 |
| 2 | Proposed smoke M6-SMK-028 executed OR owner-waived | the leg; executed by M6-P2404 |
| 3 | All slice prompts have schema-valid evidence JSON | this evidence + downstream |
| 4 | Slice gate judge sign-off PASS | M6-P2409 (downstream; also confirms no row ALLOW_EXTERNAL + EXTERNAL_SEND Final OFF) |
| 5 | Rollback steps documented | new smoke file → delete (no carried-forward file patched); the enum shipped-code rollback is per impl PLAN.md |

## Traceability

| Item | Meaning (per `00-spec/registers/`) |
|---|---|
| M6-RULE-014 | PII-egress governance explicit + fail-closed — the egress vocabulary never auto-allows; None/blank/unknown → BLOCKED_DEFAULT. |
| M6-RULE-015 | No self-certification; the module adopts the owner-signed enum, invents nothing. |
| M6-FAIL-007 | No evidence → called PASS — the SMK-028 regression proves each policy value + the fail-closed default. |

## Provenance / notes

- Scenario & expected text quoted **verbatim** from `00-spec/registers/SMOKE_REGISTER.md` (proposed additions row
  M6-SMK-028; derivation: chief-auditor 2026-09-07 item B5; M6-OD-003 enum half signed QĐ-1). Test patterns reused
  from the coder's `tests/test_m6_2p_external_send_policy.py` + the shared conftest `validator` fixture (doc working
  mode, extract line 466).
- **Rollback:** the new `tests/smoke/test_smk_028_external_send_policy_enum.py` → delete; no production code, no
  migration, no flag flipped. The enum shipped-code rollback is in the impl `PLAN.md`.
- No self-certification of PASS or of gate/leg advancement: the runner EVIDENCE_GATE and the slice Judge decide. This
  manifest and the smoke leg are the *build*; the formal executed results are produced in M6-P2404.
