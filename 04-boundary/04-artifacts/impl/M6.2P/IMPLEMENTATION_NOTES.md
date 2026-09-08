# M6.2P IMPLEMENTATION NOTES — external_send_policy typed enum (B5, M6-side) (STAGED)

**Prompt**: M6-P2402 (`M6_2P_CODER_IMPLEMENT`) · **Role**: CODER · **Mode**: `implement` · **Gate**: EVIDENCE_GATE
**Follows**: [PLAN.md](PLAN.md) (M6-P2401). Built item-by-item; **no plan-deltas**. Adopts the owner-signed (QĐ-1,
2026-09-07) `ExternalSendPolicy` 4-value enum as typed, fail-closed code. **Opens NO egress.**

> **Posture (immutable, verified untouched):** `config.py` sha256 **911b3238…** byte-identical to M6.2O;
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `live_migrations=false`. No self-cert
> (RULE-015); the runner gate + JUDGE (M6-P2409) decide.

Ledger verified: **M6-P2402 = RUNNING** (row 232), dependency **M6-P2401 = PASS**. Target **LOCKED**, **M6-OD-011
DECIDED**.

## 1. Staging model — cumulative carry-forward

Carried **M6.2O** byte-identical (caches + the M6.2O-scoped docs PLAN/IMPLEMENTATION_NOTES/INVARIANTS excluded — the
C7 invariant remains recorded in M6.2O and is referenced as this slice's forward condition in [PLAN.md](PLAN.md) §0).
Baseline verified green **BEFORE any patch: 593 passed** (parity with M6.2O). Final suite: **599 passed** (593
carried + 6 new CODER regressions). `PYTHONDONTWRITEBYTECODE=1 python -B`; no skips, no regress.

## 2. Change set (all under `04-artifacts/impl/M6.2P/`; only 2 app files — verified byte-diff)

| File : anchor | Change | Fix |
|---|---|---|
| `app/measurement/models/consumed.py` | +`class ExternalSendPolicy(str, Enum)` `{ALLOW_EXTERNAL, INTERNAL_ONLY, BLOCKED_PII, BLOCKED_DEFAULT}` (:34); retyped `EventRegistryRow.external_send_policy: Optional[ExternalSendPolicy] = None` (:79, mirrors `data_sensitivity: Optional[DataSensitivity]`); docstring | leg 1 / SMK-028 |
| `app/measurement/registry/validator.py` | +`_resolve_send_policy(raw) -> ExternalSendPolicy` (:68, mirrors `_resolve_sensitivity`: real member / valid token → member; None / blank / whitespace / unknown / non-coercible → **BLOCKED_DEFAULT**, never crash, never auto-allow); retyped `permits_external_send(policy: ExternalSendPolicy) -> bool` → `policy is ExternalSendPolicy.ALLOW_EXTERNAL` (:99); `validate()` coerces then gates (:140); imported the enum | leg 1 / SMK-028 |
| **new** `tests/test_m6_2p_external_send_policy.py` | 6 CODER regressions (below) | leg 1 / SMK-028 |

**No new migration** (migrations `0001–0013`). **No new config flag** (`config.py` sha256 identical to M6.2O). The
**only** `app/` reader of `external_send_policy` is `validator.py:140` (grep-verified) — the field retype has no
ripple. `ValidationResult.external_send_permitted: bool` unchanged.

## 3. Tests → leg → smoke (TESTER authors the official SMK-028 in M6-P2403)

`tests/test_m6_2p_external_send_policy.py` (→ leg 1 / SMK-028): the 4 enum values exist; `_resolve_send_policy` maps
each member/token to its member and **fail-closes** `None`/`""`/`"   "`/`"\t"`/unknown/`int`/`object`/`bytes` →
BLOCKED_DEFAULT (no crash); `permits_external_send` True **only** for ALLOW_EXTERNAL (False for the other three + a
coerced default + an unknown token); a real ACCEPTED event (VIEW_LANDING, policy `None`) → `send_permitted is False`;
a **non-vacuous** control — an explicitly ALLOW_EXTERNAL row makes the POLICY gate genuinely True (the gate is not a
dead hard-False), **yet `config.EXTERNAL_SEND == "OFF"`** so no real egress opens (defense-in-depth). The OFFICIAL
SMK-028 smoke is the TESTER's (M6-P2403/2404); no self-run/self-certify (RULE-015).

## 4. Egress-safety (the crown-jewel invariant) — verified airtight

- `permits_external_send` returns True **only** for `ExternalSendPolicy.ALLOW_EXTERNAL`; **no registry row is
  ALLOW_EXTERNAL** (conftest seeds only `None` → coerced BLOCKED_DEFAULT; the permit-mapping that could set
  ALLOW_EXTERNAL is the OPEN M6-OD-003 privacy/legal half, out of scope) → every real ACCEPTED event yields
  `send_permitted=False`.
- Independent second gate: `config.EXTERNAL_SEND` is Final `"OFF"` and the staged transport still raises
  `ExternalSendBlocked`, so even an ALLOW_EXTERNAL row opens no real send (defense-in-depth, unchanged).
- **Fail-closed direction airtight**: nothing that is NOT the value `"ALLOW_EXTERNAL"` ever coerces to ALLOW_EXTERNAL
  (None/blank/unknown/junk → BLOCKED_DEFAULT).

**Adversarial self-review (ultracode):** the plan red-team (2 agents, prototyped the exact coercion/gate) returned 0
findings; a follow-up egress-bypass hunt on the SHIPPED code found **1 candidate → 0 surviving**: a str-subclass /
custom-`__eq__` object whose VALUE equals `"ALLOW_EXTERNAL"` coerces to the ALLOW_EXTERNAL member — verified **NONE
(not exploitable)**: that is the INTENDED coercion of a genuine ALLOW_EXTERNAL token (the fail-closed direction is
unaffected — no non-`"ALLOW_EXTERNAL"` value becomes ALLOW_EXTERNAL), the registry source hands plain tokens (no
hostile subclass path), no row is ALLOW_EXTERNAL, and EXTERNAL_SEND stays OFF. No code change warranted (a
str-exact-type guard would wrongly reject a valid ALLOW_EXTERNAL token).

## 5. Rules / fail gates & scope

- **RULE-014**: the enum makes PII-egress governance explicit + fail-closed (BLOCKED_PII / BLOCKED_DEFAULT); no PII
  exposed, no send opened. **RULE-015**: no self-cert. **FAIL-007**: proven by the SMK-028 regression.
- **In scope**: the enum + fail-closed coercion + typed gate (2 files) + the regression. **Out of scope
  (untouched)**: the M3 registry-runtime source/reader adapter; the `data_sensitivity` enum reconciliation; the Sếp
  permit-mapping + hash policy (M6-OD-003 privacy/legal half OPEN — **no event is ALLOW_EXTERNAL**); any flag flip.
- **Boundary intact**: consume/measure-only; M6 adopts the owner-signed vocabulary, invents nothing (RULE-018);
  `M6-P1000`/`M6-P1309` stay BLOCKED; no raw secrets/PII (the policy token is an enum value).
- **Governance doc-sync (non-blocking, from the entry judge)**: `CONTRACT_EVENT_REGISTRY.contract.yaml` still
  annotates `external_send_policy` "values OPEN; NOT invented" — the canonical decision record authorizes the
  vocabulary (M6-OD-003 PARTIAL); operator/analyst should reconcile the annotation (00-spec is read-only here).

## 6. Hard forward condition (carried)

The M6-OD-003 **permit-mapping** (which events/fields are ALLOW_EXTERNAL) + the Pixel/CAPI/Offline **hash policy**
stay OPEN (privacy/legal, Sếp) — **no event may be classified ALLOW_EXTERNAL and no real egress may open** until
decided. The exit judge **M6-P2409** must confirm no registry row is ALLOW_EXTERNAL and `EXTERNAL_SEND` stays Final
OFF.

## 7. Rollback

Staged only — delete the `04-artifacts/impl/M6.2P/` tree (M6.2O untouched). Per item: revert `consumed.py` +
`validator.py` to M6.2O bytes; delete `tests/test_m6_2p_external_send_policy.py`. No migration to unwind
(`live_migrations=false`). The change is a typed fail-closed tightening; a revert restores the raw-token / hard-False
behaviour (which permits no more egress than the enum does — both fail closed).
