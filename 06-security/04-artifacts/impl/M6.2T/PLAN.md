# M6.2T PLAN — Pre-wiring hardening: Scale-Gate clear-path + reader PII-reject + residuals (STAGED, plan-only)

**Prompt**: M6-P2801 (`M6_2T_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code) · **Gate**: EVIDENCE_GATE
**Slice**: M6.2T — **harden** the STAGED recall/registry mechanism + the shared **Scale-Gate clear-path** before any
live wiring (ops-core account live, pin 54eb5f5). All four legs are **stricter / fail-closed-direction ONLY** — leg 1
can only **HOLD more, never clear more**. The mapper + reader stay **UNWIRED** (wiring is the S1b/server-bind seam,
out of scope). Cumulative superset of M6.2S. **No flag flipped, no egress.**

> **Posture (immutable, this slice flips nothing):** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
> `external_send=OFF`, `live_migrations=false`; `app/config.py` **unchanged**. No self-cert (RULE-015); the runner
> gate + JUDGE (M6-P2809) decide.

Ledger verified: **M6-P2801 = RUNNING** (row 271), dependency **M6-P2800 = SIGNED** (entry gate PASS). Target
**LOCKED**, **M6-OD-011 DECIDED**. Owner input **DECIDED + FILED**: **M6-OD-019** (2026-09-10) — close the 4
armed-not-fired forward findings from the M6.2R (P2609) + M6.2S (P2709) judge sign-offs, **stricter/fail-closed only,
leg 1 opens no PASS branch, no flag flip, no egress, STAGED, mapper+reader UNWIRED, honest test reconciliation on the
shared gate, no certified M6.2G behavior loosened**. Contracts M6-CTR-026 + M6-CTR-003 resolved-for-entry. Forward
(NOT blockers): **M6-OD-002/005** (Scale-Gate thresholds/model) OPEN — the precondition leg 2 hardens **around**;
**M6-OD-003** (permit-mapping/hash) OPEN; **M6-OD-012** (decision-export masking) DISTINCT from leg 3's input-side
reject; the S1b wiring seam + live M3 endpoint — all out of scope.

## 0. Top-0.1% lens + owner authorization (verified on the real M6.2S code + the decision record)

Leg 1 is the **FIRST change to `conditions.py`/`scale_gate.py` since M6.2Q**, on the SHARED gate the certified M6.2G
scale path consumes. A real adversary (the M6.2T plan red-team) re-checks each call against the running code:

- **[leg 1 is exactly the M6.2R forward gate-hardening finding — and it breaks NO carried test]** in M6.2R I surfaced
  that `conditions._risk` returns **PASS for any non-empty no-active map** (it checks emptiness only, not all-6
  present); M6-OD-019 now authorizes closing it. The hardening: `_risk` PASSes **only** a COMPLETE read (`all(lock in
  ctx.risk_flags for lock in RISK_LOCKS)` AND none active) — a **partial no-active map → HOLD**. **Reconciliation
  (the plan red-team PROTOTYPED the two edits against the real M6.2S SIGNED suite = 716 green and ran it):** the
  hardening breaks **exactly ONE** carried test and it is HONESTLY reconciled (never nerfed):
  `tests/smoke/test_smk_030_recall_risk_mapper_to_scale_gate.py::test_smk_030_neg_mapper_never_reads_decision_or_
  block_reasons` line 159 feeds the mapper's **CLEAN 3-of-6** no-active map (`{recall:False, sale_lock:False,
  quality_hold:False}`, via `make_scale_context(risk_flags=…)` which REPLACES the all-6 default, `conftest`
  `base.update(over)`) DIRECTLY to `_risk` and asserts `PASS` as a **non-vacuity control** (proving the gate CAN
  reach PASS). Under the completeness guard that 3-of-6 map is incomplete → **HOLD**, so the `is PASS` assertion
  turns red. **HONEST FIX (M6-P2802, pre-specified so the implementer does not improvise on the certified gate):**
  re-point the non-vacuity control at a **FULL all-6 no-active map** (`{l: False for l in RISK_LOCKS}`) → still
  asserts `PASS` (the gate CAN reach PASS with a COMPLETE clean read — the non-vacuity guarantee is PRESERVED,
  STRENGTHENED to reflect the completeness requirement), **AND ADD** an assertion that the mapper's bare 3-of-6 clean
  output → **HOLD** (the new correct fail-closed behavior). This is a strengthening, **NOT** a nerf (the assertion is
  not gutted to a tautology; the "gate can PASS" proof is kept). Every OTHER carried scale test is UNCHANGED:
  `make_scale_context` (`conftest`) defaults to all-6 → PASS (unchanged); `test_scale_gate_risk_veto` builds all-6
  with one active → FAIL (unchanged); `test_risk_recheck_at_approval` feeds all-6 / `{}` / active / partial-at-
  approval → all unchanged; SMK-009 unchanged. So the ONLY carried change is a partial-no-active → HOLD (the M6.2R
  forward finding leg 1 is authorized to close). **No PASS branch opened, no clear loosened** (red-team-verified:
  only a full-6 no-active map PASSes; only an all-6 real-bool read clears at approval).
- **[leg 1 bool-ness at approval — only a real `bool False` clears]** `scale_gate._assert_risk_clear_at_approval`
  already requires all-6 present (M6.2R fix); leg 1 adds **bool-ness**: the clear predicate becomes `all(lock in
  current_risk_flags AND isinstance(current_risk_flags[lock], bool) ...)`. A **falsy non-bool** lock value (`0` / `''`
  / `None`-as-value) is NOT a genuine "observed clear" — it does NOT clear (a truthy non-bool is already caught by
  `active_risk_locks` → raise). Carried tests feed real bools, so this breaks none; `test_empty_or_partial_fresh_
  risk_read_is_failclosed` already pins partial-non-clear and stays green.
- **[leg 1 opens NO PASS branch — is_scale_authorized stays unreachable]** the `_risk` change only converts
  partial→HOLD (removes a spurious PASS); it adds no PASS. `is_scale_authorized` still needs `overall == PASS`, and
  `_funnel`/`_dashboard` are fail-closed HOLD while M6-OD-002/005 OPEN. Leg 2 **pins** this structurally.
- **[legs 3–4 are fail-closed residuals on the UNWIRED mapper/reader]** the recall mapper + registry reader are not
  called by any `app/` caller (UNWIRED); these legs only tighten their in-process fail-closed behavior. Leg 3 is an
  **input-side reject** (a feed smuggling a customer-PII shape into a governance field → `feed_error`, state
  UNCHANGED), **NOT** export masking (governance ids export as-is; DISTINCT from M6-OD-012, RULE-014/FAIL-008).

**Scope discipline**: **NO migration** (all in-memory logic + tests), **NO config change**, **NO API/HTTP/wiring**,
**NO new secret**, **NO flag flip**, **NO PASS branch**. 4 carried files edited (all stricter): `conditions.py`,
`scale_gate.py`, `recall_risk_mapper.py`, `registry_feed_reader.py`; + regression tests.

## 1. Repo summary & staging model (cumulative carry-forward)

- **Base**: the whole **M6.2S** tree (app + 16 migrations `0001–0016` + the full carried suite, **688 green**). M6.2T
  is a superset: carry M6.2S byte-identical, edit the 4 files (stricter only) + add the regressions. (The carry runs
  in **M6-P2802 implement**.)
- **Stack** (locked target): Python 3.12, `framework=""` pure functions, `pytest -q`, stdlib only; in-memory only.
- **Layers touched** (ARCH_BASELINE): **Gate** (`conditions._risk` / `scale_gate` clear-path, leg 1) + the Gate-input
  recall mapper (leg 4) + the Source registry reader (legs 3–4). All consume/measure-only; nothing sends or scales.
- **Baseline discipline (M6-P2802)**: verify green **before** any patch (parity with the M6.2S SIGNED collect =
  **716** — the red-team measured the real SIGNED tree; an earlier draft's "688" was M6.2S's implement-time count
  before its TESTER added the SMK-031 smoke + companions), then green again after; **no skips**; the diff must show
  all 4 edits are stricter (HOLD/reject added, no PASS/clear added); actual `N passed` is the count.

## 2. The 4 hardening legs — each mapped to an exit-gate leg + SMK-032 (minimal, stricter-only, rollback per item)

Legend: **Leg** = M6.2T.md "Exit gate checks" number · **Smoke** = SMK-032 · file:anchor are M6.2S-current.

### LEG 1 — shared Scale-Gate clear-path (G4/N2, M6-OD-019) → **SMK-032(i) · RULE-017**

| File : anchor | Change (stricter/fail-closed ONLY) | Rollback (staged) |
|---|---|---|
| `app/measurement/scale/conditions.py` `_risk` (:122-129) | replace the emptiness-only guard `if not ctx.risk_flags: return HOLD; return PASS` with a **completeness** guard: `if not all(lock in ctx.risk_flags for lock in RISK_LOCKS): return HOLD` **then** `return PASS` — so a **partial no-active map → HOLD** (was PASS); all-6-no-active → PASS (unchanged); `{}` → HOLD (unchanged); any active → FAIL (unchanged). Update the docstring/reason. **No PASS branch added.** | revert `_risk` to M6.2S bytes |
| `app/measurement/scale/scale_gate.py` `_assert_risk_clear_at_approval` (:118-134) | tighten the clear predicate at :129 from `all(lock in current_risk_flags for lock in RISK_LOCKS)` to `all(lock in current_risk_flags and isinstance(current_risk_flags[lock], bool) for lock in RISK_LOCKS)` — a **falsy non-bool** lock value (`0`/`''`/`None`) does NOT clear (only a real `bool` clears; a truthy non-bool is already raised by `active_risk_locks`). Update the docstring. **No clear branch added.** | revert the one predicate + docstring |

- **CODER regression** `tests/test_m6_2t_gate_clear_path_hardening.py`: (a) a **partial no-active** map (e.g. the 3
  ops-core locks all False) → `_risk` **HOLD** (not PASS); a full-6-no-active → PASS; `{}` → HOLD; an active map →
  FAIL (unchanged). (b) at approval, a map with all-6 keys where one value is a **falsy non-bool** (`0`/`''`/`None`)
  → `record_owner_decision(APPROVE, current_risk_flags=...)` **raises** `ScaleGateViolation` (does not clear); an
  all-6 real-`bool` no-active map still clears (unchanged). **Honest reconciliation of the ONE carried break
  (red-team-found)**: `test_smk_030_..._never_reads_decision_or_block_reasons` line 159's non-vacuity control (mapper
  CLEAN 3-of-6 map → `_risk` asserts PASS) is re-pointed at a **FULL all-6 no-active map** (still asserts PASS — the
  gate CAN reach PASS with a complete read) **and** a NEW assertion is added that the bare 3-of-6 clean map → **HOLD**
  (the new correct behavior) — a strengthening, not a nerf (the "gate can PASS" proof is preserved, not gutted). All
  OTHER carried scale tests are UNCHANGED (`test_scale_gate_risk_veto` all-6→FAIL on active; `test_risk_recheck_at_
  approval` all-6→PASS / `{}`→HOLD / partial-at-approval→refuse; SMK-009). The JUDGE (M6-P2809) verifies no nerf.

### LEG 2 — HOLD-floor lock (N1, test-only, no app change) → **SMK-032(ii) · FAIL-006**

| File | Change | Rollback |
|---|---|---|
| **new** `tests/test_m6_2t_hold_floor_lock.py` | monkeypatch `config.DASHBOARD_ALERT_THRESHOLDS_DEFINED=True` **and** `config.SCALE_MODEL_RATIFIED=True` (both M6-OD-002/005 floors), build the BEST achievable `ScaleContext` (all entry evidence, boundaries True, dq PASS, all-6 risk False, budget_cap + rollback set) + a recorded owner APPROVE, and assert `AdsScaleRequest.is_scale_authorized` is **STILL False** and `overall` is **HOLD** — because `_funnel`/`_dashboard` have **no PASS branch** (both return HOLD even with the floors True). Pins `is_scale_authorized` structurally UNREACHABLE while the model is unratified; a future PASS-branch refactor FAILs this loudly. | delete the file |

### LEG 3 — reader input-side PII-shape reject (F-FEED-PII) → **SMK-032(iii) · RULE-014 · FAIL-008**

| File : anchor | Change (stricter/fail-closed) | Rollback |
|---|---|---|
| `app/measurement/adapters/registry_feed_reader.py` (parse loop :90-104) | add a module `_looks_like_pii(value) -> bool` — detects a **customer-PII shape** in a value: an email shape (a local part + `@` + a dotted domain), a phone shape (VN `0` + 9 digits, or a long digit run), or a psid/customer/guest-id shape (a `psid`/`cust`/`guest` prefix + digits) — a focused local regex set (governance codes like `ORDER_VERIFIED` never match). In the parse loop, BEFORE building the row, `if _looks_like_pii(event_code) or _looks_like_pii(event_group) or _looks_like_pii(domain): return self._reject("feed_error:pii_shape_in_governance_field")` — a row whose governance metadata carries a customer-PII shape → **feed_error, version + rows UNCHANGED** (parse-all-first, so no half-apply). **Input-side reject, NOT export masking** (governance ids like `event_code` export as-is; NOT conflated with M6-OD-012). | revert the reader to M6.2S bytes (remove the helper + the check) |

### LEG 4 — small in-process residuals (mapper + reader) → **SMK-032(iv) · RULE-017 · RULE-014**

| File : anchor | Change (stricter/fail-closed) | Rollback |
|---|---|---|
| `app/measurement/scale/recall_risk_mapper.py` `recall_risk_contribution` (:155-181) | **N3**: at the top, `if base_flags and any(k in base_flags for k in RECALL_RISK_KEYS): raise RecallRiskContributionError(...)` (a new fail-closed exception) — the base map must carry only the OTHER lock sources; a base carrying a recall key would be **silently overwritten** by the read → reject instead (no silent overwrite). | revert the guard |
| `app/measurement/scale/recall_risk_mapper.py` `from_mapping` (:62-80) | **N9**: guard `block_reasons` — `br = mapping.get("block_reasons"); if br is not None and (isinstance(br, (str, bytes)) or not isinstance(br, (list, tuple))): return None` (a **non-iterable** / string `block_reasons` is malformed → fail-closed-loud `None` → the mapper surfaces `malformed_response`), else `tuple(br or ())`. Prevents the current `tuple(<non-iterable>)` `TypeError` crash on untrusted input. | revert the guard |
| `app/measurement/adapters/registry_feed_reader.py` row parse (:98-99) | **N5/BND-01**: before the `_resolve_send_policy`/`_resolve_sensitivity` value-lookup, guard the raw is `str`/enum/`None` — a **non-str non-enum** raw resolves to the fail-closed default (`BLOCKED_DEFAULT`/`PII`) via an explicit reader-side `isinstance` guard (defense-in-depth; the validator stays byte-identical). **N6**: surface a **malformed-sibling observability** note on the `RegistryFeedApplyResult` (e.g. a `reason` suffix / a `malformed` count) when a row's sibling field was a non-str coerced to the fail-closed default — so a malformation is observable, never silent. | revert the guard + the observability field |

- **CODER regression** `tests/test_m6_2t_residuals_hardening.py`: N3 — `recall_risk_contribution` with a
  `base_flags` carrying `recall`/`sale_lock`/`quality_hold` **raises** (no silent overwrite); a base with only the
  other 3 locks still merges. N9 — `from_mapping({..., "block_reasons": 5})` (non-iterable) → `None` (malformed),
  `map_pull_outcome` → incomplete `malformed_response`; a real list/tuple/absent block_reasons still parses. N5 — a
  non-str `external_send_policy`/`data_sensitivity` → `BLOCKED_DEFAULT`/`PII` (no crash, guarded). N6 — a malformed
  sibling surfaces an observability reason.

### LEGS 5–8 (other roles)

5 SMK-032 executed-or-waived (**TESTER** M6-P2803/2804). 6 all evidence schema-valid. 7 judge PASS (M6-P2809) —
verifies stricter-only, no nerf, no certified M6.2G behavior loosened, mapper+reader still UNWIRED. 8 rollback (this
§2 + §5). The coder legs never self-run/self-certify the smoke (RULE-015).

## 3. Backward-compat & honest reconciliation (verified on real code)

- **Leg 1 is stricter-only + breaks EXACTLY ONE carried test, honestly reconciled** — the plan red-team prototyped
  the two edits against the real M6.2S SIGNED suite (716 green): the sole break is the official smoke SMK-030 line
  159's non-vacuity control (mapper CLEAN 3-of-6 map → `_risk` asserts PASS), which the completeness guard flips to
  HOLD. The new HOLD is safety-CORRECT (an unobserved lock could be active — the M6.2R forward finding); it is
  reconciled HONESTLY (§0 / §2 leg 1): the non-vacuity control is re-pointed at a FULL all-6 no-active map (still
  asserts PASS) **and** a new 3-of-6→HOLD assertion is added — a strengthening, never a nerf, never skipped/relaxed.
  Every OTHER carried scale test (`conftest.make_scale_context` all-6→PASS; `test_scale_gate_risk_veto`
  all-6-active→FAIL; `test_risk_recheck_at_approval` all-6/`{}`/active/partial-at-approval; SMK-009) is UNCHANGED.
  All-6→PASS, `{}`→HOLD, active→FAIL unchanged; only the partial-no-active flips PASS→HOLD. No PASS branch opened.
- **Legs 3–4 touch UNWIRED modules** — the recall mapper + registry reader are not imported by any `app/` caller;
  their carried tests (`test_m6_2r_recall_risk_mapper`, `test_m6_2s_registry_feed_reader`, SMK-030/031) feed real
  bools / str tokens, so the stricter guards (N3 raise on a base recall key, N9 None on non-iterable, N5 isinstance)
  do not alter their green paths; new negative cases prove the fail-closed additions. `config.py`,
  `models/consumed.py`, `registry/validator.py` stay **byte-identical**.
- **No migration** (`0001–0016` unchanged); **no config change**; **no new flag/secret**.

## 4. Rules / fail gates, scope & governance

- **RULE-017** (risk veto): leg 1 tightens both the propose-time `_risk` (all-6 to PASS) and the approval re-check
  (bool-ness) — strictly more fail-closed. **RULE-014** / **FAIL-008**: leg 3 rejects a feed smuggling a customer-PII
  shape into a governance field (input-side, never stored/exported). **RULE-015**: proven by the SMK-032 regressions.
  **FAIL-006**: leg 2 pins no executable/PASS scale path exists (is_scale_authorized unreachable).
- **In scope**: the 4 hardening legs (all stricter/fail-closed). **Out of scope (untouched)**: WIRING the mapper/
  reader into any `app/` caller (S1b seam / server-bind); the live HTTP client / real ops-core pull / real M3
  endpoint (ENTRY-003 V221); the Scale-Gate thresholds/model (M6-OD-002/005) or ANY change that opens a PASS branch;
  flag flips. Posture stays OFF/BLOCKED/OFF.
- **Boundary intact**: measure/record only — leg 1 only makes the gate FAIL/HOLD more (never clears more, opens no
  PASS branch, executes no scale, RULE-010/FAIL-006); the mapper+reader stay UNWIRED; no CRM/egress/commission
  (RULE-018/019). `M6-P1000` / `M6-P1309` stay BLOCKED.
- **Forward conditions (recorded, NOT blockers)**: M6-OD-002/005 OPEN (leg 2 hardens around them); M6-OD-003 OPEN;
  the S1b wiring seam + live M3 endpoint + M6-OD-011 server-bind/go-live remain hard gates before any live wiring /
  real scale / egress. The exit judge M6-P2809 confirms stricter-only, no nerf, no certified behavior loosened,
  mapper+reader UNWIRED, posture OFF/BLOCKED/OFF.

## 5. Verification plan for M6-P2802 (commands + PASS/FAIL + rollback)

**Commands** (`PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider`): carry M6.2S → `impl/M6.2T/`
(exclude caches; keep this `PLAN.md`), baseline green + parity **before** any patch (expect **716**, the real M6.2S
SIGNED collect); apply the 4 stricter edits + the honest SMK-030:159 reconciliation + add the 3 regressions; re-run
green (no skips — the ONLY carried change is SMK-030:159, reconciled honestly); **diff the edited files to confirm
each is
stricter (a HOLD/reject/raise added, no PASS/clear/allow added)**; confirm `config.py`/`consumed.py`/`validator.py`
byte-identical, migrations `0001–0016` unchanged, no new flag/secret, mapper+reader still UNWIRED (no new `app/`
import of them), clean caches, PII scan.

**PASS/FAIL checklist**: `_risk` partial-no-active → HOLD (all-6 to PASS) + no PASS branch ✓/✗ · approval bool-ness
(falsy non-bool does not clear) ✓/✗ · HOLD-floor regression pins is_scale_authorized unreachable (both floors True)
✓/✗ · reader rejects a PII-shaped governance field (feed_error, state unchanged; input-side not export) ✓/✗ ·
recall_risk_contribution rejects a base recall key + from_mapping fail-closed on non-iterable block_reasons + reader
isinstance guard + malformed observability ✓/✗ · **carried scale/mapper/reader tests reconciled honestly, none
nerfed** ✓/✗ · full suite green (baseline ≤ final) ✓/✗ · posture + no flag/secret + no migration + mapper/reader
UNWIRED ✓/✗.

**Rollback**: staged only — delete the `04-artifacts/impl/M6.2T/` tree (M6.2S untouched). Per item: the 4 edited
carried files (`conditions.py`, `scale_gate.py`, `recall_risk_mapper.py`, `registry_feed_reader.py`) → scoped revert
of the stricter guard(s) to M6.2S bytes; the honest **SMK-030:159 reconciliation** (`tests/smoke/test_smk_030_*`) →
revert the non-vacuity assertion to the M6.2S bytes (3-of-6 → PASS); the 3 new test files → delete. No live migration
to unwind (`live_migrations=false`). Every change is a fail-closed tightening; a revert restores prior (looser)
behaviour.

---

*Plan-only: this document writes no application code, applies no migration, opens no egress, wires nothing, resolves
no owner decision, and flips no flag. It plans an owner-authorized (M6-OD-019), STAGED, stricter/fail-closed-direction
hardening of the shared Scale-Gate clear-path + the UNWIRED recall/registry mechanism. `global_gateway_state=BLOCKED`,
`production_flag=OFF`, `external_send=OFF`. The runner gate + JUDGE decide (RULE-015).*
