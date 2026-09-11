# M6.2R — Slice Runbook — Recall-risk mapper: ops-core availability → Scale-Gate risk_flags (E2 §3/§5, S1b)

> **Status: STAGED — the recall-risk *mapper* is built and fail-closed, but it is UNWIRED and it flips nothing.**
> M6.2R adds the M6-side **recall-risk mapper** (`recall_risk_mapper.py`, M6-OD-017): it turns an ops-core
> `/v1/availability/check` response (a value object / dict — **not a live HTTP call**) into the three ops-core risk_flags
> (`recall = recall_hold OR recall_case_open`, `sale_lock`, `quality_hold`) that *can* feed the **existing** Scale Gate.
> Cumulative superset of M6.2Q. Everything STAGED: mock response in tests; the live ops-core HTTP client is the **S1b
> seam** (go-live gated on client_secret handover, not a date). **No gate-logic change** — `conditions.py`,
> `scale_gate.py`, `config.py` are **byte-identical to M6.2Q** (each sha256/`cmp`-checked; `config.py` = `911b3238…`);
> migrations stay `0001–0016`, none applied.
>
> **Read the three honesty points first — a naive "mapper built + feeds Scale Gate + 658 green" reading would imply
> recall now gates scale live, which is false:**
> 1. **The mapper is UNWIRED (N8 / CRIT-05).** No `app/` module imports `recall_risk_mapper` — **only the tests do**
>    (grep-confirmed by both boundary and security). Its fail-closed defenses (`recall_risk_contribution` collapse-to-`{}`,
>    `risk_picture_complete`) are real but **dormant in the shipped path**; whatever reaches `ScaleContext.risk_flags`
>    today is still assembled out-of-slice. M6.2R proves the **mechanism**, not live recall-gating.
> 2. **The real live FAIL-006 containment is the STRUCTURAL overall-HOLD floor + the executor absence — NOT the mapper —
>    and it is FRAGILE.** `is_scale_authorized` is structurally unreachable because `_funnel`/`_dashboard` have **no PASS
>    branch** while `DASHBOARD_ALERT_THRESHOLDS_DEFINED`/`SCALE_MODEL_RATIFIED` are False (M6-OD-002/005 OPEN) — verified
>    to hold even with **both config floors monkeypatched True** (boundary N1). Two distinct future-refactor fragilities:
>    **N1** (a future PASS branch on `_funnel`/`_dashboard` flips every armed-not-fired residual live at once) and **N4 /
>    CRIT-04** (`overall_status` is frozen at propose-time, never recomputed at approval — any future approval-time
>    recompute must be reviewed for FAIL-006 before merge). → lock the HOLD floor with a regression before any wiring.
> 3. **A PRE-EXISTING `conditions._risk` false-clear (G4 / N2) — not introduced by M6.2R, not fixable here.**
>    `conditions._risk()` PASSes any non-empty no-active `risk_flags` (it checks emptiness only, not that all 6
>    `RISK_LOCKS` are present), and the approval all-6 guard tests key **presence**, not bool-ness (a full-6 map of
>    junk-falsy `{lock: 0}` defeats it). Contained today by the HOLD floor + executor absence + the mapper's
>    fail-closed-by-construction contribution — routed to the **owner** to close before any live scale clear (no gate
>    change here per M6-OD-017 no-gate-change scope / RULE-018).
>
> **What is genuinely good (credited, not rosy):** the mapper is **fail-closed by construction** — a strict-bool choke
> (`isinstance(x, bool)`, so `0`/`1`/`"false"`/`None` → INCOMPLETE, never coerced), an incomplete/bare-clean read
> collapses to `{}` (gate HOLD, never a false PASS), it reads presence booleans only and fabricates no lock (RULE-018,
> so `decision=SELLABLE` cannot clear a present `recall_hold`). The RULE-017 hard veto **held** (a mapped present lock →
> Risk row FAIL even when SELLABLE, owner APPROVE refused). The impl red-team caught + fixed a real **MAJOR** (a bare
> 3-of-6 clean map would have false-cleared the gate → `recall_risk_contribution` redefined as fail-closed by
> construction) + a **MINOR** (strict-bool choke centralized in `map_risk_flags`). And the diff is minimal: **2 new
> files, no gate change, no migration, no HTTP, no secret, and no edited carried application/gate file** (the smoke
> registration touches `tests/TEST_MANIFEST.md` — see §4).
>
> Posture immutable: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all scale/hash/learning
> flags `False`, `live_migrations=false`. `M6-P1000` + `M6-P1309` remain **BLOCKED (not converted)**; the pack still tops
> at `OWNER_REVIEW_REQUIRED`. Evidence: full staged suite **658 passed / 0 failed, rc 0**; SMK-030 PASS 11/11; boundary
> **0** in-scope FAIL-006/RULE-017/018/015 breaches / 42 recorded; security **0** raw PII / **0** secrets (incl. **0**
> `client_secret`) / 277 files. Next: slice-gate Judge **M6-P2609**.

| Field | Value |
|---|---|
| Slice | **M6.2R** — Recall-risk mapper: ops-core availability → Scale-Gate risk_flags (E2 §3/§5); post-pilot; depends on M6.2Q; chief E2_BLOCK_REASON_V1 2026-09-10 §3/§5 + recall-lock decision (ops-core response 2026-09-09, pin a413f1f) |
| Prompt (this doc) | **M6-P2608** — `M6_2R_DOCS` (ANALYST_ARCHITECT, `analysis_only`, EVIDENCE_GATE) |
| Rules / fail gate in scope | **RULE-017** (risk hard veto / fail-closed re-check) · **RULE-015** (no self-cert) · **FAIL-006** (auto scale / publish without approval) |
| Smoke in scope | **M6-SMK-030** (recall mapper → risk_flags; FAIL-despite-SELLABLE; fail-closed on pull error) — proposed HARDENING, **executed 11/11** (not owner-waived) |
| Contract | M6-CTR-026 (Scale Gate approval flow) **MISSING/OWNER_DECISION_REQUIRED** (thresholds = M6-OD-002) → **resolved-for-entry** via harmonization M6-P0709 PASS (+ M6-P0715 SIGNED); no new contract introduced (pure mapper, no gate change) |
| Owner inputs (DECIDED) | **M6-OD-017** (recall-risk consumer — DECIDED 2026-09-10, authorizes the mapper) |

---

## 1. What this slice built (staged under `04-artifacts/impl/M6.2R/`)

M6.2R carries the **entire M6.2Q tree byte-identical** (baseline verified green **before any patch: 631 passed**,
byte-parity, `244 .py == 244 .py`, `16 .sql == 16 .sql`) and adds **exactly 2 new files** — the mapper module + its
regression test. **No gate change** (`conditions.py`/`scale_gate.py`/`config.py` byte-identical, sha256 checked), **no
migration** (still `0001–0016`), **no HTTP client**, **no new secret**, **no edited carried application/gate file**
(the only carried-file delta is `tests/TEST_MANIFEST.md` — smoke registration; see §4).

| Piece | What | File |
|---|---|---|
| **Mapper module (M6-OD-017)** | `OpsCoreAvailabilityResponse` frozen value object (presence booleans `recall_hold`/`sale_lock`/`quality_hold` + additive `recall_case_open=False`; `decision`/`block_reasons`/`sku_ref` **recorded for provenance, never read**; `from_mapping(dict)` for the dict path) · `map_risk_flags()` — `recall = recall_hold OR recall_case_open`, booleans-only, the **single strict-bool choke** both paths flow through · `map_pull_outcome()` — models the S1b seam's success/timeout/429/connection-error with **no HTTP** · `recall_risk_contribution()` — **fail-closed by construction** merge · `risk_picture_complete()` — caller-side all-6 completeness predicate · `RECALL_RISK_KEYS` — strict 3-of-6 subset of `conditions.RISK_LOCKS`, with an import-time drift guard | **new** `app/measurement/scale/recall_risk_mapper.py` |
| **Regression test** | 16 cases: 6 mapping + 2 present-lock-FAIL params + 5 pull-error params + 1 non-bool + 2 contribution-safety (covers legs 1/2/3 + the two red-team fixes) | **new** `tests/test_m6_2r_recall_risk_mapper.py` |

The three in-scope legs (per the slice done-gate), all proven staged:

| Leg | What | Gate/rule |
|---|---|---|
| **1 — E2 mapping (M6-OD-017)** | `recall = recall_hold OR recall_case_open` (additive; absent → False), `sale_lock`, `quality_hold`; output is **exactly** those 3 keys (no fabricated lock); presence **booleans only** — a `decision=SELLABLE + recall_hold=True → recall=True` test proves `decision` is never read. | RULE-018 |
| **2 — presence-flag FAIL even when SELLABLE** | feeding a mapped `{recall:True}` (from `recall_hold` **or** `recall_case_open`, with `decision=SELLABLE`) to the **existing** `ScaleGate` → Risk row **FAIL** + `record_owner_decision` raises `ScaleGateViolation`. No gate code changed. | **RULE-017** |
| **3 — fail-closed on pull error** | error/timeout/429/None/malformed/non-bool → `complete=False`, `risk_flags={}`; fed to the gate → Risk **HOLD** + approve **REFUSED** (does not clear). Never a `False` false-clear, never a fabricated `True`. | **RULE-017** / FAIL-006 |

---

## 2. Operate

M6.2R is a pure read/map layer; there is no live call, no network, no egress, and **no caller in the shipped path**
(see §5.1). The staged flow the tests exercise:

1. **Obtain an availability response (STAGED).** A caller constructs an `OpsCoreAvailabilityResponse` value object, or
   passes a dict through `from_mapping(dict)`. In this slice the response is **built in-test** — the live ops-core HTTP
   client (`POST /v1/availability/check`) is the **S1b seam** and is **not built** (secret handover pending). The module
   imports no `requests`/`httpx`/`urllib`/`http.client`/`socket`.
2. **Map to risk_flags.** `map_risk_flags()` reads the four presence booleans only (`recall_hold`/`sale_lock`/
   `quality_hold`/`recall_case_open`) through the strict-bool choke and emits `{recall, sale_lock, quality_hold}`. A
   non-bool/None/missing presence flag → INCOMPLETE (empty), never `bool()`-coerced. `decision`/`block_reasons`/`sku_ref`
   are never read.
3. **Handle a pull outcome (STAGED seam).** `map_pull_outcome()` models TIMEOUT/HTTP_429/CONNECTION_ERROR/absent/
   malformed/unrecognized → INCOMPLETE, with no HTTP.
4. **Contribute to the gate (fail-closed by construction).** `recall_risk_contribution()` returns the map **only** when
   an active lock is present (FAIL direction) or a complete 6-lock picture is clean (clearing-eligible); an
   incomplete/bare-clean read collapses to `{}` (gate HOLD). So the mapper's clean output is **structurally never** a
   standalone clearing map. **Caveat (§5.1):** nothing in `app/` calls this yet.
5. **What stays impossible:** a live ops-core call, a real network, external send, a flag flip, a gate-logic change.
   `config.py`/`conditions.py`/`scale_gate.py` byte-identical to M6.2Q.

---

## 3. Verify

### 3.1 The official smoke (SMK-030 PASS 11/11, executed not waived; masked `correlation_id`+`evidence_id`)

- scenario i — clean-lot `decision=SELLABLE` + `recall_hold=true` → `risk_flags['recall']=True` → Risk row **FAIL
  despite SELLABLE**, owner APPROVE refused (`ScaleGateViolation`, RULE-017 re-check); request stays PROPOSED.
- scenario ii — `recall_case_open=true` with `recall_hold=false` → `recall=True` (additive OR) → **FAIL despite
  SELLABLE** + approve refused; and the additive default (absent → false).
- scenario iii ×5 (TIMEOUT / HTTP_429 / CONNECTION_ERROR / None / malformed) — incomplete/unknown read is empty (never
  a false-clear, never a fabricated True) → Risk **HOLD** + approve refused (gate does not clear). *See the traceability
  note §3.4.*
- neg — `decision`/`block_reasons` never read: SELLABLE + clean block_reasons cannot clear a present `recall_hold`; a
  scary decision string cannot fabricate a lock (clean → Risk PASS, non-vacuous).
- neg — a missing key (dict path) or a non-bool value (`None`/`0`/`1`/`"false"`/`"true"`/`()`/`[]` via the value-object
  path) → incomplete empty read → HOLD.
- control (non-vacuity) — a clean complete read maps to the non-empty `{recall:False, sale_lock:False,
  quality_hold:False}` (so the empties above are error-caused); `RECALL_RISK_KEYS < RISK_LOCKS` (strict 3-of-6); the
  bare merge collapses to `{}`.
- posture — `EXTERNAL_SEND=="OFF"`, `PRODUCTION_FLAG=="OFF"`, `GLOBAL_GATEWAY_STATE=="BLOCKED"`; mapper imports no
  HTTP/transport; `sku_ref`/`decision`/`block_reasons` never enter `risk_flags`.

### 3.2 Full staged suite (count discipline)

```
# from 04-artifacts/impl/M6.2R/  (venv: 02-tester/.venv, python 3.12.14, pytest 8.4.2; -B, cache-free, no shell redirection)
python -B -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider'])>"   # -> RC 0 ; 658 passed / 0 failed
python -B -c "<tally; pytest.main(['tests/smoke/test_smk_030_recall_risk_mapper_to_scale_gate.py'])>"  # -> RC 0 ; 11 passed
```

**Reconciliation: 658 (tester-run final) = 631 carried (M6.2Q) + 16 coder M6.2R regressions (→ 647 coder baseline) + 11
official-smoke nodes (SMK-030 = 7 functions, scenario-iii parametrized ×5).** Coder baseline before any patch was 631
(byte-parity with M6.2Q); the isolated 1-leg run independently confirms 11 passed; the build-side collect-only count
(M6-P2603) was also 658. *(pytest's terminal summary is unreliable in this harness for a long run, so totals came from
an in-process `pytest_runtest_logreport` tally with `pytest.main() RC=0` — see SMOKE_RESULTS.md "On counting".)*

### 3.3 The in-scope gate — FAIL-006 not tripped, RULE-017 veto held (boundary-verified)

- **Boundary (M6-P2605): 42 outcomes = 36 DEFENDED / 4 OPEN_NONGATE / 2 NOTE / 0 in-scope FAIL-006/RULE-017/018/015
  breaches.** The mapper's strict-bool fail-closed read, the collapse-to-`{}` contribution, the RULE-017 hard veto (FAIL
  despite SELLABLE), the executor absence, and — deepest — the structural overall-HOLD floor all held under executed
  attack. `is_scale_authorized` is structurally unreachable while M6-OD-002/005 are OPEN, so no scale can be authorized
  regardless of any mapper/risk quirk. **No-transport verified package-wide (N7):** the no-HTTP claim was extended
  across the **whole scale-package source closure (7 files)** — no HTTP/queue import anywhere, not only in the mapper
  module; the S1b live client is absent package-wide.
- **Security (M6-P2606): 0 raw PII / 0 real secrets / 277 files** (canonical `0/0/0/0/0`, incl. **0** `client_secret`;
  the 4 non-canonical hits are all carried from M6.2O, benign — the mapper adds none). The recall/availability data is
  **product-level** (`recall_hold`/`sale_lock`/`quality_hold`/`recall_case_open` booleans + a `sku_ref` campaign/SKU ref)
  — **not customer PII**. No ops-core token / `client_secret` in the code (the live client is not built). Posture
  BLOCKED/OFF/OFF unchanged; byte-clean.

### 3.4 Traceability note (non-blocking; carried honestly from the tester + boundary)

SMOKE_REGISTER phrases the leg-iii pull-error outcome as "gate FAIL", while scenario iii asserts the Risk row is
`DataQualityStatus.HOLD` plus a refused owner APPROVE (`ScaleGateViolation`). This is the **correct fail-closed
does-not-clear** semantics — an unobserved risk read is HOLD (never PASS), the approval is refused, the request stays
PROPOSED — matching the frozen `conditions._risk` (empty `risk_flags` → HOLD) and the sibling SMK-009 "FAIL/HOLD"
pairing (HOLD is the unobserved-risk half). The exit-gate leg #3 itself frames the incomplete read as "does not clear".
The per-test docstring states HOLD honestly rather than claiming a FAIL status. Not a defect; a register-wording nit.

---

## 4. Rollback (every change this slice made) — *acceptance check 1*

Staged-only and non-destructive: nothing live, no migration applied (`live_migrations=false`), no flag flipped, no
egress opened, **no carried application/gate file edited**. This is a pure additive, non-destructive rollback.

| Change | Rollback |
|---|---|
| **Whole slice** | delete the `04-artifacts/impl/M6.2R/` tree — M6.2Q is byte-identical and untouched; no live migration to unwind |
| **New file** — `app/measurement/scale/recall_risk_mapper.py` | delete the file |
| **New file** — `tests/test_m6_2r_recall_risk_mapper.py` | delete the file |
| **New official smoke** — `tests/smoke/test_smk_030_recall_risk_mapper_to_scale_gate.py` (+ `TEST_MANIFEST.md` delta) | delete the file / revert the manifest delta |
| **Edited carried files (application / gate code)** | **none** — `conditions.py`/`scale_gate.py`/`config.py` byte-identical to M6.2Q (each sha256/`cmp`-checked); nothing to scoped-revert. The only carried-file delta is `tests/TEST_MANIFEST.md` (smoke registration — see the row above) |
| **Migration** | **none** — migrations stay `0001–0016`, none applied |
| **Config flag** | **none** — `config.py` byte-identical to M6.2Q (sha256 `911b3238…`) |
| **Boundary / security analysis-only writes** (`M6.2R_boundary.md`, `M6.2R_security.md`, harness/scanner scripts under `work/`) | delete; both recorded "no source modified" |
| **Tester / PM / docs analysis-only + evidence writes** (`test-reports/M6.2R/SMOKE_RESULTS.md`; `evidence/prompts/M6_2R_EVIDENCE_INDEX.md` + band `M6-P2600…2608.json`; this `analysis/slices/M6_2R_RUNBOOK.md` + `M6-P2608.json`) | delete / revert — all are analysis-only or evidence-collection writes; none modified any source, gate, migration, or `04-artifacts/state/` |

Every change is a pure additive read layer + its tests, so deleting the two files restores M6.2Q exactly. No posture
value was ever written.

---

## 5. Decision deltas & governance

### 5.1 Honesty point 1 — the mapper is UNWIRED (N8 / CRIT-05; top-0.1% lens: do not over-attribute recall safety to the mapper)

**No `app/` module imports `recall_risk_mapper` — only the tests do** (grep-confirmed independently by boundary §4 and
security §5). The mapper's fail-closed defenses (`recall_risk_contribution` collapse-to-`{}`, `risk_picture_complete`,
the strict-bool choke) are real but **dormant in the shipped path**; whatever reaches `ScaleContext.risk_flags` today is
assembled out-of-slice. So M6.2R proves the **mapper mechanism** — it does **not** make recall gate scale live. The
sign-off must not read as "recall now blocks scale." **Forward:** a future caller must be **forced** to route
`ScaleContext.risk_flags` through `recall_risk_contribution` + `risk_picture_complete` before any live recall-gating.

### 5.2 Honesty point 2 — the real live FAIL-006 containment is the structural HOLD floor + no executor, and it is fragile (N1 / CRIT-01)

The live FAIL-006 containment is **not** the mapper. It is (1) the **structural overall-HOLD floor** —
`_funnel`/`_dashboard` have no PASS branch while `DASHBOARD_ALERT_THRESHOLDS_DEFINED`/`SCALE_MODEL_RATIFIED` are False
(M6-OD-002/005 OPEN), so `is_scale_authorized` is structurally unreachable, **verified to hold even with both config
floors monkeypatched True** (boundary N1) — and (2) the **absence of any executor** (no class on the scale path holds a
Transport/budget/campaign/audience handle; "APPROVED" is a recorded `OwnerDecision`, not a trigger). This is robust
today but **fragile to two future refactors**:
- **N1** — if a future slice adds a PASS branch to `_funnel`/`_dashboard`, **every armed-not-fired residual below
  becomes a live breach at once**.
- **N4 / CRIT-04** — `overall_status` is **frozen at propose-time** and never recomputed at approval; a future
  "recompute overall at approval" refactor must be reviewed for FAIL-006 before merge.

**Route (owner/coder forward): lock the HOLD floor with a regression** (assert `is_scale_authorized` stays False even
with both floors flipped) so a future PASS branch cannot silently open FAIL-006.

### 5.3 Honesty point 3 — a pre-existing `conditions._risk` false-clear (G4 / N2), not introduced here, not fixable here

`conditions._risk()` returns **PASS for any non-empty `risk_flags` with no active lock** — it checks emptiness only, not
that all 6 `RISK_LOCKS` are present; and `_assert_risk_clear_at_approval`'s all-6 completeness test then falls back to
that PASS. Two ways it bites:
- **G4** — a raw 3-of-6 clean map fed **directly** as `ScaleContext.risk_flags` (bypassing `recall_risk_contribution`)
  clears `_risk` though 3 of the 6 locks are unobserved.
- **N2** — a full-6 map of **junk-falsy** values (`{lock: 0}` for all 6) clears `_risk` **and** the approval all-6 guard,
  because that guard tests key **presence**, not bool-ness.

**Not introduced by M6.2R** (`conditions.py` byte-identical; the mapper's contribution is fail-closed by construction and
avoids triggering it) and **not fixable here** — hardening the gate is out of scope per M6-OD-017 (no-gate-change) /
RULE-018 (M6 surfaces the risk; the owner owns gate policy). Contained today by the HOLD floor + executor absence + the
mapper's collapse-to-`{}`. **Route: owner** — harden `_risk` to require all-6 `RISK_LOCKS` present to PASS, and validate
bool-ness (not mere presence) in the approval all-6 guard, before any live scale clear. This is the sharpest residual.

### 5.4 The positive worth crediting — the mapper is fail-closed by construction, and the red-team fixed a real MAJOR

- **Fail-closed by construction (real integrity properties, boundary-executed):** the strict-bool choke
  (`isinstance(x, bool)`) fails closed on `None`/`0`/`1`/`"false"`/`"true"`/`()`/`[]`/`{}` on **both** the value-object
  and the dict paths; an incomplete/bare-clean read collapses to `{}` (HOLD, never a false PASS); the mapper reads
  presence booleans only and fabricates no lock (RULE-018), so `decision=SELLABLE` cannot clear a present `recall_hold`
  and a scary decision string cannot invent one.
- **RULE-017 hard veto held:** each of the three mapped locks (recall via `recall_hold` or `recall_case_open`, sale_lock,
  quality_hold) independently forces Risk **FAIL despite SELLABLE** and refuses the owner APPROVE.
- **Impl red-team caught + fixed 2 real defects before the gate** (M6-P2602 self-review): a **MAJOR** — the first cut of
  `recall_risk_contribution` returned the bare 3-of-6 clean map for `base_flags=None`, which fed to the real gate would
  **false-clear** the RULE-017 recall veto → redefined as **fail-closed by construction** (active → returned FAIL,
  complete-6-clean → returned, incomplete/bare-clean → `{}`) with a regression asserting HOLD + approve refused; and a
  **MINOR** — the value-object path bypassed the strict-bool guard → centralized the guard in `map_risk_flags` (the
  single choke both paths flow through).

### 5.5 Residuals (armed-not-fired; none trips an in-scope gate; reachability floor: mapper reads product-level booleans, no HTTP, `is_scale_authorized` structurally unreachable, external_send Final OFF)

- **`conditions._risk` partial/junk-falsy false-clear (G4/N2 — owner, the sharpest):** §5.3. Harden `_risk` to require
  all-6 `RISK_LOCKS` present + validate bool-ness at the approval guard. Not PII; not introduced by M6.2R.
- **`OwnerDecision.to_public()` unmasked decision-export (F-SEC-2R-1 = boundary N5 → M6-OD-012 + CODER):** masks `actor`
  but exports **`reason`/`audit_ref`/`evidence_ref` verbatim**; `reason`/`audit_ref` flow from the untrusted admin body
  (`handle_scale_decision` copies them into `OwnerDecision`), so a PII-shaped reason would export unmasked on the
  durable/export surface. **Carried M6.2G, byte-identical this slice** (the boundary re-surfaced it because the recall
  work feeds the same Scale Gate). It is a **two-instance pattern** with the M6.2Q **MC-09** (`AdsSpendImportDecision.
  to_public()` — reason/audit_ref raw). The audit sink already drops these; `to_public()` should mirror it (mask/drop,
  or route the free-text through the raw-PII tripwire at intake). Channel-reachable at the data-flow level but
  PII-hygiene, not a scale-authorization path (armed-not-fired for FAIL-006).
- **`recall_risk_contribution` overwrites its own keys (N3 → CODER):** a `base_flags` that (violating the docstring
  contract) asserts `recall=True` is silently erased to False by a clean read. Safe today by contract + the floor, no
  runtime guard; in-process/caller-assembled, not channel-reachable. Fix: fail-closed if `base_flags` contains any
  `RECALL_RISK_KEYS`.
- **`from_mapping` non-iterable `block_reasons` (N9 → CODER):** `tuple(mapping.get("block_reasons") or ())` raises
  `TypeError` on a non-iterable truthy (`block_reasons=5`). Fail-closed **loud** (a crash never false-clears),
  block_reasons is provenance-only → CODER robustness parity with the strict-bool choke.
- **Malformed-sibling downgrade observability gap (N6 → CODER):** a malformed sibling downgrades an active recall
  FAIL→HOLD and renders it as "not checked" (identical to never-observed). Fail-closed for FAIL-006, but monitoring keyed
  on "active lock observed" loses the malformed-with-active-lock vs unobserved distinction.
- **S1b secret-handover forward (→ owner M6-OD-011):** when the live ops-core HTTP client is built, its credential must
  be a **`secret_ref`** (never a raw token in code/evidence/log), and the M6.2O AST import-scan gate (no HTTP client in
  `app/`) will need its allow-list updated **deliberately** for the one egress client. Verified now: **no ops-core
  credential is in the code** and the mapper takes a value object, not a live call.

### 5.6 Owner decisions + immutable posture

- **DECIDED (authorizes this slice):** **M6-OD-017** (recall-risk consumer — DECIDED 2026-09-10). The mapper consumes
  ops-core booleans **for M6's own Scale Gate**; M6 does not own the recall decision, pause a campaign, send CRM, change
  M3 gating, or compute a commission (RULE-018/019).
- **Hard forward gates (before any live recall pull / real scale / egress):** **M6-OD-002** (thresholds); **M6-OD-005**
  (scale-authoritative attribution model); **M6-OD-011** (server-bind + go-live + ops-core client_secret handover +
  import-gate allow-list + scale-endpoint authN); **M6-OD-012** (durable-export masking — the `OwnerDecision` +
  `AdsSpendImportDecision` reason/audit_ref two-instance pattern + carried trace-id family); **M6-OD-003** (real psid
  pepper + privacy/legal, carried); plus the **S1b live-HTTP client** + the **campaign→SKU join** + the **M3
  block_reason / pause-SLA**. `M6-P1000` + `M6-P1309` remain **BLOCKED (not converted)**.
- **Carried residuals (unaffected; distinct from this slice's local labels — the label collision the PM index
  disambiguated):** the M6.2Q **MC-09** (`AdsSpendImportDecision` export — twin of F-SEC-2R-1) + the M6.2Q
  **ROAS-provenance** finding (F-SEC-2I-1) + maker-checker identity binding; the F-SEC-2K-1/2M-1 masking family +
  F-EVID-4/5/6; the psid_hash real-pepper + privacy/legal (M6-OD-003). *(This slice's local G4/N2 and the structural-HOLD
  N1 must not be confused with the carried "B1 psid_hash real-pepper" / "N1 ROAS-provenance" tokens.)*
- **Posture (untouched):** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all flags `False`,
  `live_migrations=false`; `conditions.py`/`scale_gate.py`/`config.py` byte-identical to M6.2Q. Out of scope (untouched):
  the live ops-core HTTP client (S1b); the campaign→SKU join; the M3-side block_reason vocabulary / pause-SLA; any flag
  flip.

---

## 6. Changelog delta — *acceptance check 2*

| Kind | Delta this slice introduced |
|---|---|
| **Code (staged, new)** | **2 new files**: `app/measurement/scale/recall_risk_mapper.py` (the mapper + `OpsCoreAvailabilityResponse` value object + `RECALL_RISK_KEYS` drift guard) and `tests/test_m6_2r_recall_risk_mapper.py` (16 cases). |
| **Code (staged, edited)** | **none** — no carried file edited. |
| **Migration** | **none** — migrations stay `0001–0016`, none applied. |
| **Tests (staged)** | 16 coder regression cases (in the new test file) + the official **SMK-030** (11 nodes = 7 functions, scenario-iii parametrized ×5). Suite **631 → 658**. |
| **Config flag** | **none**; `config.py` byte-identical to M6.2Q. |
| **Gate logic** | **none** — `conditions.py`/`scale_gate.py` byte-identical (sha256 checked). |
| **Contract** | M6-CTR-026 (Scale Gate approval flow) MISSING/OWNER_DECISION_REQUIRED (thresholds = M6-OD-002) → resolved-for-entry via harmonization M6-P0709 PASS. No new contract. |
| **Owner decisions** | **M6-OD-017** DECIDED (authorizes the slice); forward gates M6-OD-002 / M6-OD-005 / M6-OD-011 / M6-OD-012 / M6-OD-003 carried. |
| **New capability** | the recall-risk **mapper mechanism** (ops-core availability booleans → 3 risk_flags), fail-closed by construction, able to feed the existing Scale Gate in the FAIL/HOLD direction — **staged and unwired** (no `app/` caller). |
| **Governance verdicts** | `M6-P1000` + `M6-P1309` **remain BLOCKED** (not converted). |
| **Posture** | unchanged — `BLOCKED / OFF / OFF`, all flags `False`, gate byte-identical. **No live ops-core call / real network / egress / flag flip / gate change.** |
| **Readiness** | assembled pack still `OWNER_REVIEW_REQUIRED`; the mapper is a **mechanism, not live recall-gating**, and this slice declares no ROAS-Pass / Scale-Ready (owner-only). |

---

## 7. Handoff

**Exit-gate status (7 legs, per the slice done-gate — the full map is `M6_2R_EVIDENCE_INDEX.md` §4):**

| Exit leg | Status | Evidence |
|---|---|---|
| 1 — E2 mapping (`recall = recall_hold OR recall_case_open`, `sale_lock`, `quality_hold`; additive; booleans-only; no fabricated lock) | **MET** | SMK-030 scenario i/ii + neg-decision-never-read + control + coder regression |
| 2 — presence-flag FAIL even when SELLABLE (recall_hold and recall_case_open) | **MET** | SMK-030 scenario i + ii; RULE-017 veto; no gate change |
| 3 — fail-closed on pull error (does not clear) | **MET** | SMK-030 scenario iii ×5 + non-bool neg (asserted HOLD + approve refused; see §3.4) |
| 4 — SMK-030 executed or owner-waived | **MET** | executed 11/11, not waived |
| 5 — all slice prompts have evidence JSON | **PENDING** | M6-P2608 (this doc) + Judge M6-P2609 still to produce evidence |
| 6 — slice-gate judge sign-off PASS | **PENDING** | M6-P2609 to run (fresh session) |
| 7 — rollback documented for every change | **MET** | §4 |

Legs 1–4 + 7 are MET; legs 5–6 are PENDING only because this docs prompt and the judge are the last two to run. None is FAILED/BLOCKED.

- **Immediate next (JUDGE, fresh session): M6-P2609 `M6_2R_SLICE_GATE_JUDGE`.** Checks the 7 exit-gate legs (E2 mapping;
  presence-flag FAIL even SELLABLE; fail-closed on pull error; SMK-030 executed; every-prompt evidence; judge sign-off;
  rollback) **AND confirms no flag flip / no live HTTP / no gate change / posture OFF-BLOCKED-OFF.** The judge must weigh
  the **three honesty points**, not the green count. Judges never modify what they judge. See §8.
- **OWNER (the load-bearing forward steps):** **harden `conditions._risk`** to require all-6 `RISK_LOCKS` present +
  validate bool-ness at the approval all-6 guard (G4/N2, the sharpest — §5.3); **lock the structural HOLD floor with a
  regression** before any wiring (N1/N4 — §5.2); **M6-OD-012** durable-export masking (`OwnerDecision` +
  `AdsSpendImportDecision` reason/audit_ref, two-instance pattern — mirror the audit-sink drop); **M6-OD-011** ops-core
  client_secret handover as a `secret_ref` + import-gate allow-list update + scale-endpoint authN before the S1b live
  client; **M6-OD-002 / M6-OD-005** thresholds + attribution model; and **force a future risk-flags caller through
  `recall_risk_contribution` + `risk_picture_complete`** (N8 — §5.1).
- **CODER:** `recall_risk_contribution` base-key guard (N3); `from_mapping` non-iterable `block_reasons` guard (N9);
  malformed-sibling observability (N6); mirror the audit-sink drop on `to_public()`.
- **Posture carried forward unchanged:** `BLOCKED / OFF / OFF`, all flags `False`; `M6-P1000` + `M6-P1309` BLOCKED.

---

## 8. Pointers for the slice-gate Judge (M6-P2609)

1. **Read order:** `M6_2R_EVIDENCE_INDEX.md` → the 7 band JSONs (M6-P2600…2606) → the two review reports
   (`M6.2R_boundary.md` §2–4 the fail-closed mapper + RULE-017 veto + the structural HOLD floor + residuals,
   `M6.2R_security.md` §4–6 the fail-closed/PII-safe mapper + F-SEC-2R-1 + the honest wiring note) → `SMOKE_RESULTS.md`
   (SMK-030 11/11 + the traceability note) → `IMPLEMENTATION_NOTES.md` (rollback §6 + the §4 gate-hardening finding). The
   7-leg exit-gate map is index §4.
2. **What is proven (executed + boundary/security-verified):** the mapper is fail-closed by construction (strict-bool
   choke, incomplete→`{}`, booleans-only, no fabricated lock — RULE-018); the RULE-017 hard veto holds (present lock →
   Risk FAIL even SELLABLE, approve refused); no gate change (`conditions.py`/`scale_gate.py`/`config.py` byte-identical);
   the red-team caught + fixed a real MAJOR. Full suite **658 passed**; SMK-030 11/11; boundary **0** in-scope FAIL-006/
   RULE-017/018/015 breaches / 42 recorded; security **0** raw PII / **0** secrets (incl. **0** `client_secret`) / 277
   files.
3. **The three honesty points to weigh hardest (not the green count):** **(1) the mapper is UNWIRED (N8)** — no `app/`
   caller, so this proves a mechanism, not live recall-gating; **(2) the live FAIL-006 containment is the STRUCTURAL
   overall-HOLD floor + no-executor (N1), and it is fragile** — a future PASS branch on `_funnel`/`_dashboard` (N1) or an
   approval-time overall-recompute (N4) would flip every armed-not-fired residual live at once; lock the floor with a
   regression; **(3) the pre-existing `conditions._risk` partial/junk-falsy false-clear (G4/N2)** the owner must close
   before any live scale clear (not introduced here, not fixable here per the no-gate-change scope).
4. **What is NOT yet closed:** exit items **5 & 6** are PENDING only because this docs prompt (M6-P2608) and the judge
   (M6-P2609) are the last two to run. Legs 1–4 + 7 (rollback) are MET. The mapper is **staged + unwired** and this slice
   declares no ROAS-Pass / Scale-Ready — thresholds (M6-OD-002) + the scale-authoritative model (M6-OD-005) + server-bind
   (M6-OD-011) stay OPEN.
5. **Confirm the posture:** no flag flip, no live ops-core HTTP, no gate change, `config.py`/`conditions.py`/
   `scale_gate.py` byte-identical, migrations `0001–0016` unchanged, `M6-P1000` + `M6-P1309` BLOCKED (not converted).
6. **Boundary integrity of this docs prompt (M6-P2608):** `analysis_only` — it read the band evidence and wrote only this
   runbook + its evidence JSON. It touched no `04-artifacts/state/`, marked no ledger row, modified no file it documented,
   opened no egress, computed no verdict, and declared no readiness. `global_gateway_state=BLOCKED`, `production_flag=OFF`,
   `external_send=OFF` — untouched; `M6-P1000` + `M6-P1309` remain BLOCKED (not converted).
