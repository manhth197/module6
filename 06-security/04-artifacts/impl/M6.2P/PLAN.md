# M6.2P PLAN — external_send_policy typed enum (B5, M6-side) (STAGED, plan-only)

**Prompt**: M6-P2401 (`M6_2P_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code) · **Gate**: EVIDENCE_GATE
**Slice**: M6.2P — adopt the **owner-signed** (QĐ-1, 2026-09-07) `external_send_policy` **4-value enum** as typed,
fail-closed code, replacing the raw `Optional[str]` token in `models/consumed.py` + the hard-`False`
`permits_external_send()` in `registry/validator.py`. Cumulative superset of M6.2O under `04-artifacts/impl/M6.2P/`.
**This slice only makes the enum vocabulary real + fail-closed; it opens NO egress** (no event is ALLOW_EXTERNAL,
`EXTERNAL_SEND` stays OFF) and depends on nothing from M3/Sếp.

> **Posture (immutable, this slice flips nothing):** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
> `external_send=OFF`, `live_migrations=false`; `config.py` unchanged. No self-cert (RULE-015); the runner gate +
> JUDGE (M6-P2409) decide.

Ledger verified: **M6-P2401 = RUNNING** (row 231), dependency **M6-P2400 = SIGNED** (entry gate PASS). Target
**LOCKED**, **M6-OD-011 DECIDED**. In-scope contract **M6-CTR-003** (event_registry) = DRAFT_LOCKED. Doc working mode
(extract L463–472): *do not guess; read the repo first; reuse conventions + test patterns; minimal change; output
files-touched + tests + commands + PASS/FAIL + rollback*.

## 0. Owner authorization & the hard forward condition (verified on the canonical decision record)

**M6-OD-003 is PARTIAL**: the **enum VOCABULARY half is SIGNED** (owner+tech-lead QĐ-1, chief-confirmed;
`04-artifacts/evidence/decisions/M6-OD-003-enum.json` = PARTIAL_DECISION, `XAC_NHAN_QD1-QD3_2026-09-07.md`;
DECISION_REGISTER reconciled to PARTIAL). This slice **adopts** that owner-signed vocabulary — it invents nothing
(RULE-018). **The PERMIT-MAPPING (which events/fields are ALLOW_EXTERNAL) + the Pixel/CAPI/Offline hash policy stay
M6-OD-003 OPEN** (privacy/legal, Sếp) → **no event may be classified ALLOW_EXTERNAL and no real egress may open**
until that half is decided. Per the entry judge, the **exit judge M6-P2409 must confirm no registry row is
ALLOW_EXTERNAL and `EXTERNAL_SEND` stays Final OFF.** This plan resolves no owner decision.

> **Top-0.1% lens (egress-safety, the load-bearing axis):** the one thing this slice must NOT do is open (or make
> reachable) an external-send path. Two independent guarantees hold: (a) `permits_external_send()` returns True ONLY
> for `ALLOW_EXTERNAL`, and **no registry row carries that value** (the conftest seeds only `None`, coerced fail-
> closed to `BLOCKED_DEFAULT`; the permit-mapping that could set ALLOW_EXTERNAL is OPEN/out-of-scope) → every real
> ACCEPTED event still yields `send_permitted=False`; (b) **even if** a row were ALLOW_EXTERNAL, the transport still
> raises `ExternalSendBlocked` because `EXTERNAL_SEND` is Final `"OFF"` (defense-in-depth, unchanged). The plan is a
> *vocabulary + fail-closed gate*, not an egress opener.

## 1. Repo summary & staging model (cumulative carry-forward)

- **Base**: the whole **M6.2O** tree (app + 13 migrations `0001–0013` + the full carried suite incl. the shipped
  B1/F2-6 + the SMK-026/027 official smokes + the OD-011 import gate). M6.2P is a **superset**: carry M6.2O byte-
  identical, apply the enum change + add a CODER regression. (The carry runs in **M6-P2402 implement**, not this
  plan.)
- **Stack** (locked target): Python 3.12, `framework=""` (framework-neutral pure functions), `pytest -q`, stdlib
  only; in-memory staged stores; physical DB/HTTP bind = owner M6-OD-011 step.
- **Layer touched** (ARCH_BASELINE): **Source** (event_registry CONSUMED read-model `consumed.py`) + **Tracking**
  (the RULE-001 validation path `registry/validator.py`). No new layer/contract object; **no new migration/flag**.
- **Baseline discipline (M6-P2402)**: verify green **before** any patch (subprocess `pytest`, parity with the M6.2O
  collect), then reach green again after the change + regression; **no skips**; actual `N passed` is the count.

## 2. The fix — one item → exit-gate leg 1 + SMK-028 (minimal change, mapped, rollback per item)

**SMK-028 (verbatim)**: *event_registry row with external_send_policy = each of ALLOW_EXTERNAL / INTERNAL_ONLY /
BLOCKED_PII / BLOCKED_DEFAULT + a None/blank/unknown token → typed `ExternalSendPolicy` enum; `permits_external_send()`
True ONLY for ALLOW_EXTERNAL; None/blank/unknown coerces fail-closed to BLOCKED_DEFAULT (no crash, no auto-allow);
every real ACCEPTED event still `send_permitted=False` (no event is ALLOW_EXTERNAL) and `EXTERNAL_SEND` stays OFF.*

**Current (M6.2O)**: `EventRegistryRow.external_send_policy: Optional[str] = None` (raw token, `consumed.py:64`);
`permits_external_send(external_send_policy: Optional[str]) -> return False` (hard-False, `validator.py:66-73`);
`validate()` calls `permits_external_send(row.external_send_policy)` (`:116`). `_resolve_sensitivity(raw)` (`:48-63`)
is the existing fail-closed-coercion **precedent** (MISSING/unknown → PII) this fix mirrors.

**Minimal change** (2 files, additive + a typed swap):

| File : anchor | Change | Rollback (staged) |
|---|---|---|
| `app/measurement/models/consumed.py` | Add `class ExternalSendPolicy(str, Enum)` `{ALLOW_EXTERNAL, INTERNAL_ONLY, BLOCKED_PII, BLOCKED_DEFAULT}` (docstring: owner-signed QĐ-1 / M6-OD-003 enum half; default fail-closed BLOCKED_DEFAULT; only ALLOW_EXTERNAL permits, and no event is ALLOW_EXTERNAL until the owner permit-mapping is signed). Retype `EventRegistryRow.external_send_policy: Optional[ExternalSendPolicy] = None` (mirrors `data_sensitivity: Optional[DataSensitivity]`); update the field comment | revert `consumed.py` to M6.2O bytes |
| `app/measurement/registry/validator.py` | Add `_resolve_send_policy(raw) -> ExternalSendPolicy` mirroring `_resolve_sensitivity`: `isinstance ExternalSendPolicy` → it; `None`/blank/`ExternalSendPolicy(raw)`-ValueError/TypeError → **BLOCKED_DEFAULT** (never crash, never auto-allow). Retype `permits_external_send(policy: ExternalSendPolicy) -> bool` → `return policy is ExternalSendPolicy.ALLOW_EXTERNAL`. In `validate()`: `policy = _resolve_send_policy(row.external_send_policy); send_permitted = permits_external_send(policy)`. Import `ExternalSendPolicy` from consumed | revert `validator.py` to M6.2O bytes |

**Backward-compat (verified)**: every carried registry row seeds `external_send_policy=None` (conftest.py:79) →
`_resolve_send_policy(None)` = BLOCKED_DEFAULT → `permits_external_send` = False; the 3 carried assertions
`test_event_registry_validation.py:13,21,39` (`external_send_permitted is False`) still hold. **No carried test
passes a raw string** to the field, and **no test calls `permits_external_send` directly** besides `validate()`
(grep-verified), so the signature swap breaks nothing. `ValidationResult.external_send_permitted: bool` is unchanged.

**CODER regression** (`tests/test_m6_2p_external_send_policy.py` → leg 1 / SMK-028): `_resolve_send_policy` maps each
of the 4 enum values to itself, and `None` / `""` / `"   "` / an unknown token → `BLOCKED_DEFAULT`;
`permits_external_send` is True **only** for `ALLOW_EXTERNAL` and False for the other three + every coerced default;
a real ACCEPTED event (row `external_send_policy=None`) → `send_permitted is False`; `config.EXTERNAL_SEND == "OFF"`
(the enum opens no egress); a non-vacuous control (a hand-built ALLOW_EXTERNAL row → `permits_external_send` True at
the policy layer, yet no real egress because EXTERNAL_SEND stays OFF).

## 3. Rules / fail gates in scope

- **RULE-014** (no raw PII): the enum makes the PII-egress governance **explicit + fail-closed** (`BLOCKED_PII` /
  `BLOCKED_DEFAULT`); it exposes no PII and opens no send — a PII event's policy resolves to a BLOCKED value, never
  auto-allow.
- **RULE-015** (no self-cert): the plan/impl write evidence and self-certify nothing; readiness/egress unchanged.
- **FAIL-007** (no-evidence): the change is proven by the SMK-028 regression; nothing is called PASS without it.

## 4. Scope & governance boundary

- **In scope**: exactly the three in-scope bullets — the `ExternalSendPolicy` enum in `consumed.py`, the fail-closed
  coercion of `EventRegistryRow.external_send_policy`, and the typed `permits_external_send()`.
- **Out of scope (untouched)**: the registry runtime SOURCE + reader adapter (M3 `event-registry-feed.v1` endpoint /
  staged file-export + SHA — waits on Phúc/M3 ENTRY-003 + chief); the `data_sensitivity` enum reconciliation (M6
  {PUBLIC,INTERNAL,PII} vs M3 {SENSITIVE,INTERNAL} — Sếp/Core); the **Sếp permit-mapping** (which events/fields are
  ALLOW_EXTERNAL) + hash policy (M6-OD-003 privacy/legal half OPEN — **no event is ALLOW_EXTERNAL by this slice**);
  any flag flip / real egress — `production_flag`/`global_gateway_state`/`external_send` stay OFF/BLOCKED/OFF.
- **Boundary intact**: measure/consume-only; M6 reads `event_registry`, never writes/invents it (RULE-018 — it adopts
  the owner-signed vocabulary). `M6-P1000`/`M6-P1309` stay BLOCKED. No raw secrets/PII (the policy token is an enum
  value, not PII).
- **Governance doc-sync (non-blocking, from the entry judge)**: `CONTRACT_EVENT_REGISTRY.contract.yaml` still
  annotates `external_send_policy` "values OPEN; NOT invented" (lags the PARTIAL signature); the canonical decision
  record (register + `M6-OD-003-enum.json` + QĐ-1) authorizes the vocabulary, so this lag does not gate — operator/
  analyst should reconcile it (00-spec is read-only to the coder).

## 5. Verification plan for M6-P2402 (commands + PASS/FAIL + rollback)

**Commands** (implement runs these; subprocess `pytest`, `PYTHONDONTWRITEBYTECODE=1 python -B`): carry M6.2O →
`04-artifacts/impl/M6.2P/` (exclude caches; keep this `PLAN.md`), baseline green + parity **before** the patch;
apply the enum + coercion + typed gate + the regression; re-run green (no skips); confirm `config.py` unchanged,
migrations `0001–0013`, no new flag, clean caches, PII scan.

**PASS/FAIL checklist**: `ExternalSendPolicy` enum present with the 4 values ✓/✗ · `_resolve_send_policy` fail-closed
(None/blank/unknown → BLOCKED_DEFAULT, no crash) ✓/✗ · `permits_external_send` True only for ALLOW_EXTERNAL ✓/✗ ·
every real ACCEPTED event `send_permitted=False` + `EXTERNAL_SEND=OFF` (no egress opened) ✓/✗ · 3 carried
`external_send_permitted is False` assertions still green ✓/✗ · full suite green (baseline ≤ final) ✓/✗ · posture +
migrations unchanged ✓/✗.

**Rollback**: staged only — delete the `04-artifacts/impl/M6.2P/` tree (M6.2O untouched). Per item: revert
`consumed.py` + `validator.py` to M6.2O bytes; delete the regression file. No migration to unwind. The change is a
typed fail-closed tightening; a revert restores the raw-token / hard-False behaviour (which permits no more egress
than the enum does — both fail closed).

---

*Plan-only: this document writes no application code, adds no migration/flag, resolves no owner decision, and flips
no flag. It adopts an owner-signed enum vocabulary as fail-closed code that opens NO egress.
`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`. The runner gate + JUDGE decide (RULE-015).*
