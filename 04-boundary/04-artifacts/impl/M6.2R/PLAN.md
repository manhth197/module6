# M6.2R PLAN — Recall-risk mapper: ops-core availability → risk_flags (E2 §3, S1b) (STAGED, plan-only)

**Prompt**: M6-P2601 (`M6_2R_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code) · **Gate**: EVIDENCE_GATE
**Slice**: M6.2R — the M6-side **recall-risk mapper**: take an ops-core `/v1/availability/check` response (a value
object / dict — **NOT a live HTTP call**) and produce the three ops-core-sourced `risk_flags` (`recall`, `sale_lock`,
`quality_hold`) that feed the **EXISTING** Scale Gate. **No gate-logic change** — the gate already FAILs on active
locks (RULE-017) and refuses to clear on an incomplete read. Cumulative superset of M6.2Q under
`04-artifacts/impl/M6.2R/`. **Everything STAGED** (mock response object in tests; the live HTTP client is the S1b
seam / go-live 2026-09-11). No live HTTP, no flag flipped.

> **Posture (immutable, this slice flips nothing):** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
> `external_send=OFF`, `live_migrations=false`; `app/config.py` unchanged. No self-cert (RULE-015); the runner gate +
> JUDGE (M6-P2609) decide.

Ledger verified: **M6-P2601 = RUNNING** (row 251), dependency **M6-P2600 = SIGNED** (entry gate PASS). Target
**LOCKED**, **M6-OD-011 DECIDED**, `live_migrations=false`. Owner input **DECIDED + FILED**: **M6-OD-017**
(recall-risk consumer — PULL path, mapper `recall = recall_hold OR recall_case_open` / `sale_lock` / `quality_hold`,
read presence **booleans only** (never `decision`/`block_reasons`), any presence-flag true → Scale-Gate Risk row
**FAIL even when SELLABLE**, pull error/timeout/429 → **INCOMPLETE → fail-closed** (RULE-017), FAIL gate only + **no
auto-pause**, STAGED live-HTTP-out, no flag flipped). Contract **M6-CTR-026** resolved-for-entry (harmonization
M6-P0709 PASS). Forward conditions (NOT blockers): **M6-OD-002** (Scale-Gate thresholds) OPEN, and the S1b live-HTTP
client + campaign→SKU join + M3 block_reason vocabulary/pause-SLA — all out of scope.

## 0. Top-0.1% lens + owner authorization (verified on the real M6.2Q code + the decision record)

The lens changed three load-bearing calls; a real adversary (the M6.2R plan red-team) re-checked each against the
running `scale/conditions.py` + `scale/scale_gate.py`:

- **[NO gate-logic change — leg 2 rides the EXISTING RULE-017 veto]** `conditions.py` already has
  `RISK_LOCKS = (recall, sale_lock, quality_hold, complaint_p0, platform_spam_flag, crm_suppression)`,
  `active_risk_locks()`, and `_risk()` (any active lock ⇒ **FAIL**, RULE-017 hard veto; empty map ⇒ HOLD, fail-closed).
  → the mapper is a **NEW module** that only *produces* a `risk_flags` mapping; it **touches no gate code**. Feeding
  `{recall: True}` to the existing gate FAILs the Risk row by construction — so SMK-009 + every carried scale test
  stay green, and leg 2 needs no new gate logic. The mapper's 3 keys are a **subset** of `RISK_LOCKS` (consistent).
- **[fail-closed on pull error = INCOMPLETE (unobserved), NOT a fabricated `recall=True`]** M6-OD-017 + slice leg 3
  say the pull error path is an **INCOMPLETE risk read**, and leg 1 says the mapper **reads presence booleans only /
  fabricates no lock**. So on error/timeout/429/None the mapper returns an **empty** ops-core map (the locks are
  *unobserved*), NOT `recall=True` (which would fabricate a value it never read). Fed to the gate **as the sole risk
  source**, an empty map makes `_risk` **HOLD** (`if not ctx.risk_flags`) and `_assert_risk_clear_at_approval`
  **REFUSE** the approval (`ScaleGateViolation`) — that is leg-3 fail-closed for the mapper-alone case (SMK-030(iii)).
  **Precise wording for the TESTER**: SMK-030's "pull error → gate FAIL" is realized as **Risk HOLD + approval
  REFUSED (does not clear)** — assert *approve refused / overall ≠ PASS*, not a literal `_risk == FAIL`.
- **[adversarial red-team fix — MAJOR: the mapper's CLEAN output is a PARTIAL risk picture, never a standalone
  clearing map]** the M6.2R plan red-team (an independent skeptic that *prototyped* this wiring against the running
  M6.2Q gate) caught that `conditions._risk()` returns **PASS for ANY non-empty map with no active lock** — it only
  distinguishes empty (→HOLD) from non-empty, it does **NOT** require all 6 `RISK_LOCKS` present. So the mapper's
  normal clean read `{recall:False, sale_lock:False, quality_hold:False}` (a 3-of-6 subset) fed as the **sole**
  `ScaleContext.risk_flags` would read Risk=**PASS** at propose (while `complaint_p0`/`platform_spam_flag`/
  `crm_suppression` are **unobserved**), and `_assert_risk_clear_at_approval`'s all-6 completeness test then falls
  back to that spurious PASS → a false **CLEAR** (approval recorded on a 3-of-6 risk picture) — the exact RULE-017
  hole the completeness re-check exists to prevent. **The completeness backstop I claimed only fires for the EMPTY
  map, not a partial-nonempty one.** → **Fix (in scope, no gate change):** the mapper is a **PARTIAL risk
  contributor**, used only in the **FAIL** direction (a present recall lock ⇒ gate FAIL, leg 2) and the
  **incomplete/empty** direction (pull error ⇒ HOLD/refused, leg 3). Its clean all-false 3-key output is **NEVER**
  presented as the sole clearing `ScaleContext.risk_flags`; a clearing decision requires the **full 6-lock** picture
  assembled from all lock sources (the other 3 are out of this slice's scope). The plan **removes** the false
  backstop claim and surfaces the gate's `_risk` partial-at-propose false-clear as a **forward gate-hardening finding
  for the owner** (§4) — a pre-existing gate limitation this slice does not introduce and, per its "no gate-logic
  change" scope (M6-OD-017), does not fix.
- **[malformed input is fail-closed too; `recall_case_open` is additive]** `recall_case_open` **absent → treated
  False** (additive; the other flags unaffected). A **required** presence flag (`recall_hold`/`sale_lock`/
  `quality_hold`) that is **missing or not a real `bool`** → the read is **INCOMPLETE** (fail-closed), never
  `bool()`-coerced (so a stray `"false"` string can never coerce to a truthy clear/lock). The mapper **never** reads
  `decision`/`block_reasons` — proven by a `decision=SELLABLE + recall_hold=True → recall=True` fixture.

**This slice is LEAN**: one new pure module + one regression test. **No migration** (the mapper is a pure in-memory
consumer of a value object — no new table, no store), **no gate change**, **no API/HTTP client** (the live client is
the S1b seam, out of scope), **no new secret**, **no flag flip**.

## 1. Repo summary & staging model (cumulative carry-forward)

- **Base**: the whole **M6.2Q** tree (app + 16 migrations `0001–0016` + the full carried suite, 626 green). M6.2R
  is a **superset**: carry M6.2Q byte-identical, add the mapper module + its CODER regression. (The carry runs in
  **M6-P2602 implement**, not this plan.)
- **Stack** (locked target): Python 3.12, `framework=""` pure functions, `pytest -q`, stdlib only; in-memory only.
- **Layer touched** (ARCH_BASELINE): **Scale-Gate input** only — a new consumer that maps a CONSUMED ops-core
  availability response into the existing `ScaleContext.risk_flags`. M6 consumes ops-core booleans **for its own
  gate**; it does **not** own the recall decision, pause campaigns, or change M3 gating (RULE-018 boundary).
- **Baseline discipline (M6-P2602)**: verify green **before** any patch (subprocess `pytest`, parity with the M6.2Q
  collect = 626), then green again after; **no skips**; actual `N passed` is the count.

## 2. The change — mapped to each exit-gate leg + SMK-030 (minimal change, rollback per item)

Legend: **Leg** = M6.2R.md "Exit gate checks" number · **Smoke** = SMK-030 · file:anchor are M6.2Q-current.

### The recall-risk mapper → **legs 1 + 3 · SMK-030(i)(ii)(iii) · RULE-017 · RULE-015 · FAIL-006**

| File : anchor | Change | Rollback (staged) |
|---|---|---|
| **new** `app/measurement/scale/recall_risk_mapper.py` | (a) frozen value object `OpsCoreAvailabilityResponse{recall_hold: bool, sale_lock: bool, quality_hold: bool, recall_case_open: bool = False, decision: Optional[str] = None, sku_ref: Optional[str] = None}` — `decision`/`sku_ref` are RECORDED for provenance and **NEVER read** by the mapper; `from_mapping(dict)` classmethod for the dict path (missing `recall_case_open` → False; a missing/`non-bool` required presence flag → signalled malformed). (b) frozen result `RecallRiskRead{risk_flags: Mapping[str,bool], complete: bool, reason: str}`. (c) `RECALL_RISK_KEYS = ("recall","sale_lock","quality_hold")` (subset of `conditions.RISK_LOCKS`). (d) `map_risk_flags(pull) -> RecallRiskRead`: a valid response → `{recall: bool(recall_hold or recall_case_open), sale_lock: bool(sale_lock), quality_hold: bool(quality_hold)}`, `complete=True`; a **pull error / None / malformed** → `risk_flags={}`, `complete=False`, `reason="pull_error:<kind>"` (the ops-core locks left **unobserved**, never a `False` false-clear, never a fabricated `True`). (e) `map_pull_outcome(response=None, *, error=None)` (or an `AvailabilityPull{response?, error?}` value in) to model the S1b seam's success/timeout/429/connection-error WITHOUT any HTTP. (f) `recall_risk_contribution(read, base_flags=None) -> Mapping[str,bool]` — the wiring **MERGES** the mapper's observed recall locks **onto** a caller-supplied `base_flags` (the other lock sources), returning a fresh map; it is a **PARTIAL contribution**, NOT a standalone clearing map. On a **present** lock the merged map has an active lock ⇒ gate FAIL (leg 2). On an **incomplete** read the recall keys are left **absent** from the contribution (unobserved). **Fail-closed contract (documented on the helper):** the mapper's 3-key output is a **subset** of the 6 `RISK_LOCKS`; because the gate's `_risk` reads a non-empty no-active map as PASS, a bare 3-key map must **NEVER** be passed alone as a clearing `ScaleContext.risk_flags` — a clearing decision requires the **full 6-lock** map (all sources merged). The helper's docstring states this and, when `base_flags` is omitted, it does not synthesize the missing 3 locks (they stay absent, so the all-6 completeness re-check cannot clear). **No import of, or change to, the gate logic** — only `conditions.RISK_LOCKS` is referenced (read) for the key-subset assertion + the completeness note. | delete the file |

- **Leg 1 (E2 mapping, M6-OD-017)** — `recall = recall_hold OR recall_case_open`, `sale_lock`, `quality_hold`;
  `recall_case_open` additive (absent → False); output keys are **exactly** `{recall, sale_lock, quality_hold}` (no
  other lock fabricated); presence **booleans only** (never `decision`/`block_reasons`). ← SMK-030(i)(ii).
- **Leg 3 (fail-closed on pull error)** — error/timeout/429/None/malformed → `complete=False`, `risk_flags={}`
  (unobserved). Fed to the gate **as the sole risk source**, an empty map makes `_risk` **HOLD** (`if not
  ctx.risk_flags`) and `_assert_risk_clear_at_approval` **REFUSE** the approval (fail-closed, RULE-017) — SMK-030(iii).
  The mapper never false-clears an unknown flag (never emits `recall=False` on an error). **Precision (red-team
  fix):** the completeness re-check backstops the **empty** map only; a partial-**non-empty** map is NOT fail-closed
  by the gate (`_risk` PASSes it), so the mapper's clean output is never presented as a bare clearing map (§0 red-team
  bullet + item (f)). ← SMK-030(iii).

### Leg 2 rides the EXISTING gate (no new file) → **SMK-030(i)(ii) · RULE-017**

- Feeding the mapped `risk_flags` (e.g. `{recall: True}` from `recall_hold=True` or `recall_case_open=True`, with
  `decision=SELLABLE`) to the **existing** `ScaleGate` / `evaluate_conditions` makes the **Risk row FAIL even when
  `decision==SELLABLE`** (the mapper ignored `decision`), and `record_owner_decision(..., current_risk_flags=...)`
  is **REFUSED** by the RULE-017 re-check. **No gate code changes.**

### CODER regression (net-new test, no carried behaviour touched)

| File | Change | Rollback |
|---|---|---|
| **new** `tests/test_m6_2r_recall_risk_mapper.py` | **Leg 1**: `recall_hold=True → recall=True`; `recall_case_open=True` alone → `recall=True` (additive); `recall_case_open` absent → False; `sale_lock`/`quality_hold` map through; output keys == `{recall,sale_lock,quality_hold}` (no fabricated lock); `decision=SELLABLE + recall_hold=True → recall=True` (mapper ignores `decision`); `from_mapping` dict path. **Leg 2**: feed `{recall:True}` (SELLABLE) to the existing `ScaleGate` → `_risk` FAIL + `record_owner_decision` raises `ScaleGateViolation` (FAIL-despite-SELLABLE), for `recall_hold` **and** for `recall_case_open`. **Leg 3**: pull error / timeout / 429 / None / malformed → `complete=False`, `risk_flags={}`; fed to the gate → Risk **HOLD** + approve **REFUSED** (does not clear); the mapper never emits a `False` for an unknown lock. **Partial-contribution safety (red-team fix)**: assert the clean output keys are a **strict subset** of `conditions.RISK_LOCKS` (`set(RECALL_RISK_KEYS) < set(RISK_LOCKS)`, 3 of 6) and that `recall_risk_contribution(clean_read, base_flags=None)` does **NOT** contain `complaint_p0`/`platform_spam_flag`/`crm_suppression` (they stay absent, so the all-6 completeness re-check cannot clear) — i.e. the mapper's clean output is documented as a **partial** picture, never a standalone clearing map. Reuses the carried `scale_gate` / `make_scale_context` / `make_owner_decision` fixtures. | delete the file |

### LEGS 4–7 (other roles)

4 SMK-030 executed-or-waived (**TESTER** M6-P2603/2604). 5 all evidence schema-valid. 6 judge PASS (M6-P2609).
7 rollback documented (this §2 + §5). The coder legs never self-run/self-certify the smoke (RULE-015).

## 3. Backward-compat & the pinned surfaces (verified on real code)

- **No gate change** → `conditions.py` / `scale_gate.py` are byte-identical to M6.2Q; SMK-009 (Recall/Sale-Lock →
  FAIL/HOLD) + every carried scale test (`test_scale_gate_risk_veto`, `test_risk_recheck_at_approval`,
  `test_scale_request_lifecycle`, SMK-012) stay green. The mapper only **reads** `RISK_LOCKS` (a tuple) for its
  key-subset assertion.
- **New module + new test only** → no carried test enumerates a `scale/` module set or imports the mapper; nothing
  to break. `RISK_LOCKS` unchanged (the 3 mapper keys are a subset). `config.py` untouched.
- **No migration / no store / no API** → migrations stay `0001–0016`; no new table; the DB/HTTP bind stays the
  M6-OD-011 / S1b forward step.

## 4. Rules / fail gates, scope & governance

- **RULE-017** (risk veto re-checked at approval): the mapper FEEDS the existing fail-closed re-check — a present
  lock FAILs, an unknown read never clears. **RULE-015** (no self-cert): proven by the SMK-030 regressions; nothing
  is called PASS without evidence. **FAIL-006** (no executable scale path): unaffected — the mapper produces
  read-only flags, adds no scale/act surface.
- **In scope**: the mapper (availability response → `risk_flags`) + fail-closed on pull error + wiring into
  `ScaleContext.risk_flags` (no gate-logic change). **Out of scope (untouched)**: the live HTTP client to ops-core
  `POST /v1/availability/check` (S1b seam / go-live 2026-09-11); the campaign→SKU join to enumerate running
  campaigns on a recalled SKU (separate data-source decision); the M3-side `block_reason` vocabulary / decision
  gating (M3 owns) + the pause SLA (owner-side). No flag flip; posture stays OFF/BLOCKED/OFF.
- **Boundary intact**: M6 consumes ops-core booleans **for its own Scale Gate**; it does **not** own the recall
  decision, pause a campaign, send CRM, change M3 gating, or compute a commission (RULE-018/019). The response
  carries campaign/SKU refs (not PII); the mapper reads booleans only — **no raw PII**, no secret (the live client's
  auth is the S1b seam, out of scope). `M6-P1000` / `M6-P1309` stay BLOCKED.
- **Forward conditions (recorded, NOT blockers)**: **M6-OD-002** (Scale-Gate thresholds) OPEN governs the gate's
  Funnel/Dashboard rows + M6.2G exit, not this mapper; the S1b live-HTTP client + campaign→SKU join + M3
  block_reason/pause-SLA + M6-OD-011 server-bind/go-live remain hard gates before any **live** recall pull / real
  scale / egress. The exit judge M6-P2609 confirms no flag flip, no live HTTP, posture OFF/BLOCKED/OFF.
- **Forward gate-hardening FINDING (surfaced to the owner; NOT fixed in this slice — no gate change per M6-OD-017)**:
  the plan red-team found that `conditions._risk()` returns **PASS for any non-empty `risk_flags` with no active
  lock** — it checks emptiness only, not that all 6 `RISK_LOCKS` are present — so a partial-**non-empty** map at
  propose (e.g. this mapper's clean 3-of-6 output, or any single-source subset) reads Risk=PASS, and
  `_assert_risk_clear_at_approval`'s all-6 completeness test then falls back to that PASS → a false **CLEAR** with
  locks unobserved. This is a **pre-existing** RULE-017 gate limitation (not introduced by M6.2R; harmless today
  because the staged overall is HOLD via Funnel/Dashboard, so `is_scale_authorized` stays False), but it becomes a
  live scale-authorization false-clear once M6-OD-002/005 ratify and the overall can reach PASS. **This slice avoids
  triggering it** (the mapper is a partial contributor, never a standalone clearing map — §0/§2). **Owner action
  recommended (separate decision):** harden `_risk` to require all 6 `RISK_LOCKS` present to PASS (mirror the
  approval-time completeness), OR require the Scale-Gate assembly to merge all 6 lock sources before any
  approval-clearing `ScaleContext`. Flagged here per RULE-018 (M6 surfaces the risk; the owner owns the gate policy).

## 5. Verification plan for M6-P2602 (commands + PASS/FAIL + rollback)

**Commands** (`PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider`): carry M6.2Q → `impl/M6.2R/`
(exclude caches; keep this `PLAN.md`), baseline green + parity **before** any patch (expect 626); add
`recall_risk_mapper.py` + the regression; re-run green (no skips); confirm `config.py` unchanged, migrations
`0001–0016` (unchanged), no new flag/secret, clean caches, PII scan.

**PASS/FAIL checklist**: `recall = recall_hold OR recall_case_open` + additive + booleans-only + no fabricated lock
✓/✗ · Risk row FAIL even when SELLABLE (recall_hold & recall_case_open) + approve REFUSED ✓/✗ · pull
error/timeout/429/None/malformed → incomplete (empty) → gate does not clear / approve REFUSED, no false-clear ✓/✗ ·
clean output is a strict subset of `RISK_LOCKS` (partial contribution, never a standalone clearing map) ✓/✗ ·
carried scale tests + SMK-009 still green + `conditions.py`/`scale_gate.py` byte-identical ✓/✗ · full suite green
(baseline ≤ final) ✓/✗ · posture + no flag/secret + no migration change ✓/✗.

**Rollback**: staged only — delete the `04-artifacts/impl/M6.2R/` tree (M6.2Q untouched). Per item: the two new
files → delete. No carried file is edited (no gate change, no migration), so there is nothing to scoped-revert. No
live migration to unwind (`live_migrations=false`). Every change is additive; a revert restores prior behaviour.

---

*Plan-only: this document writes no application code, applies no migration, opens no egress, makes no live HTTP
call, resolves no owner decision, and flips no flag. It plans an owner-authorized (M6-OD-017), STAGED,
mock-response recall-risk mapper feeding the EXISTING Scale Gate. `global_gateway_state=BLOCKED`,
`production_flag=OFF`, `external_send=OFF`. The runner gate + JUDGE decide (RULE-015).*
