# M6.2U IMPLEMENTATION_NOTES — Recall E2 §3 sellability conformance + migration renumber README + psid_hash docstring

**Prompt**: M6-P2902 (`M6_2U_CODER_IMPLEMENT`) · **Role**: CODER · **Mode**: `implement` (STAGED) · **Gate**: RUNNER_GATE
**Slice**: M6.2U — a cumulative superset of M6.2T. Implements the approved `PLAN.md` (M6-OD-020, conforming to chief
`E2_BLOCK_REASON_V1` §3). **Leg 1 is stricter / fail-closed ONLY: it ADDs FAIL conditions and opens NO PASS branch,
loosens nothing.** The mapper stays **UNWIRED**. No flag flipped, no egress, no migration SQL written.

> **Posture (immutable, unchanged this slice):** `app/config.py` **byte-identical** to M6.2T
> (sha256[:16] = `911b32381368f355`); `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
> `live_migrations=false`. No self-cert (RULE-015) — the runner gate + JUDGE (M6-P2909) decide.

Ledger verified before acting: **M6-P2902 = RUNNING** (row 282); dependency **M6-P2901 = PASS** (row 281, plan SIGNED).

## Carry-forward (cumulative)

`work/carry_2u.py` copied the whole **M6.2T** tree byte-identical (excluding `__pycache__` / `.pytest_cache` / `*.pyc`
and the prior `PLAN.md` / `IMPLEMENTATION_NOTES.md` / INVARIANT docs). Parity confirmed: **M6.2T 743 passed ==
M6.2U carried 743 passed** (0 fail/error/skip) **before any patch** — the real SIGNED baseline (M6.2T grew from its
729 implement-time count to 743 via the TESTER's later official smokes).

## The 3 legs (exactly the approved PLAN §2)

### LEG 1 — recall E2 §3 sellability conformance (B3, M6-OD-020) — stricter/fail-closed only

A **DISTINCT** `not_sellable` sellability veto, **separate from the recall booleans and NOT a RISK_LOCK**:

- `app/measurement/scale/conditions.py` `_risk`: after the active-lock FAIL check and **before** the M6.2T all-6
  completeness check, added `if ctx.risk_flags.get("not_sellable"): return ConditionResult(RISK, _FAIL, …)`.
  `not_sellable` is **not** added to `RISK_LOCKS`, so `active_risk_locks`, the all-6 completeness, and every
  non-mapper scale context (which carries no `not_sellable` key) are **unchanged**. The only new behavior is an
  added FAIL — no PASS/clear branch is opened.
- `app/measurement/scale/recall_risk_mapper.py`:
  - `map_risk_flags`: the 3 recall booleans (`recall = recall_hold OR recall_case_open`, `sale_lock`,
    `quality_hold`) are **byte-identical in derivation** — still from the **presence booleans only** (ops-core §4,
    never from `decision`). Separately, `decision` is read **once** and `flags["not_sellable"] = True` is set
    **only when `response.decision != "SELLABLE"`**. A **SELLABLE** response adds **no** `not_sellable` key, so its
    output stays the **exact-3-key** recall map. `RecallRiskRead.sellable` records the decision-based sellability.
  - `_incomplete` (pull error / timeout / 429 / absent / malformed / non-bool): now returns
    `risk_flags={"not_sellable": True}, complete=False, sellable=False, unverified=True` — an **unverified** read is
    treated as **not sellable → Risk FAIL** (fail-closed, **stricter** than the prior empty-`{}`→HOLD). The recall
    booleans stay **unobserved** (absent). `RecallRiskRead` gained `sellable` / `unverified` fields.
  - `recall_risk_contribution`: **LEFT UNCHANGED (byte-identical to M6.2T)**. Per the plan-stage red-team, the veto
    must **not** propagate through this helper — it copies only the 3 `RECALL_RISK_KEYS`, so `not_sellable` never
    pollutes the merged 6-lock map (which would break `set(full)==RISK_LOCKS` and mis-route a veto to `{}`→HOLD).
    The veto reaches `_risk` via `read.risk_flags` fed **directly** (as SMK-030 and the regression do).
  - module docstring: conformed to **M6-OD-020** (the mapper reads `decision` **only** for the sellability veto; the
    recall booleans are still not derived from decision).

### LEG 2 — migration renumber README (B1/B4, docs-only)

`migrations/README.md` was **stale** (listed only `0001`–`0005`). Rewrote it to list **`0001`–`0016`** (the tables
actually in the tree — descriptions taken from each SQL file's own header, not invented) with the full apply order,
**plus** a note that the **enforcement migration is `0017`** (renumbered from the taken `0014`; `0014`–`0016` are the
M6.2Q ads-spend tables), **authored at server-bind — no SQL file written here**. No SQL file changed; **no `0017`
SQL** exists in the staged folder.

### LEG 3 — psid_hash docstring (D20, docstring-only, code unchanged)

`app/measurement/models/attribution_context.py` `as_stored` docstring: corrected "Trace joins use `psid_hash` …" to
conform to **M6-OD-015 (psid-no-join)** — cross-module correlation uses the channel-origin keys `live_session_id` /
`comment_id` / `messenger_thread_id` + the `attribution_id` surrogate, **never** a `psid_hash` join. `as_stored()`
**code is byte-identical** (`return dict(self.to_public())`).

## Honest reconciliation of the carried tests (no nerf; the JUDGE M6-P2909 verifies)

The `map_risk_flags` / `_incomplete` edits change the mapper's `risk_flags` output, so the mapper's own tests that
feed `read.risk_flags` directly and assert an exact key-set / `{}` / HOLD were reconciled by the plan's two rules.
Running the real suite confirmed the **complete** break list = **17 tests** (all in the two mapper test files), each
reconciled as a **strengthening**:

- **RULE A** (isolate the boolean tests): added `decision="SELLABLE"` so no `not_sellable` key is added and the
  exact-3-key assertion is unchanged — `test_recall_hold_maps_to_recall`,
  `test_output_keys_are_exactly_the_three_ops_core_locks`, SMK-030 `control_clean_complete_read`.
- **RULE B** (incomplete/pull-error now FAILs): `risk_flags == {}` / `_risk HOLD` → `risk_flags == {"not_sellable":
  True}` / `_risk FAIL` — the "does not clear" guarantee is preserved and **strengthened** (FAIL also refuses the
  approve). Applies to `test_from_mapping_dict_path_and_malformed`, `test_pull_error_is_incomplete_and_gate_does_not_clear`
  (×5), `test_value_object_nonbool_presence_flag_is_failclosed`, SMK-030 `scenario_iii` (×5), `neg_malformed_or_nonbool`.
- **Reframe** `test_mapper_never_reads_decision` → `test_mapper_never_derives_recall_booleans_from_decision`, and
  SMK-030 `neg_never_reads_decision` → `neg_never_derives_recall_booleans_from_decision`: the mapper now DOES read
  `decision` (only for the veto), so the old name was a false claim. The reframed tests assert the still-true
  invariant (recall booleans not derived from decision) **plus** the new veto (`not_sellable` True + `_risk` FAIL for
  a non-SELLABLE decision). The certified clear-path (SELLABLE + full-6 → PASS) is asserted preserved.

**Note on SMK-030 (iii):** the official smoke's **verbatim** register Expected reads "a pull error → … → gate FAIL",
but the M6.2R implementation under-implemented it as HOLD; M6-OD-020's veto now makes it FAIL, bringing the smoke
into conformance with its own quoted Expected. The verbatim Scenario/Expected block was left untouched; only the
author-prose + assertions were updated.

**CODER regression** (new): `tests/test_m6_2u_recall_e2_conformance.py` (11 tests) — pins: `not_sellable` distinct
from `RISK_LOCKS` / `RECALL_RISK_KEYS`; NOT_SELLABLE / unknown / missing decision → Risk FAIL (isolated against an
otherwise-clearing full-6 picture); pull-error/429/incomplete → FAIL + `unverified`; recall booleans not derived from
decision (present lock FAILs even SELLABLE; clean lot's booleans False under any decision); SELLABLE + no-active +
full-6 → Risk PASS (clear-path preserved) while a 3-of-6 partial → HOLD; mapper UNWIRED (no `app/**` import).

## Verification (RULE-015: evidence, not self-cert)

Command: `PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider -q`.

- **Full suite: 754 passed, 0 failed, 0 error, 0 skipped** (authoritative via pytest terminalreporter stats).
  Baseline **743** (carried) + **11** CODER regression = **754**; the 17 reconciled tests changed assertions/names,
  not the count. No skips, no xfails, no deletions.
- **Surface diff (M6.2T ↔ M6.2U), byte-hash compared:** only the expected files differ — 1 new
  (`tests/test_m6_2u_recall_e2_conformance.py`) + 6 changed (the 4 leg files + the 2 reconciled test files).
  `app/config.py`, `app/measurement/scale/scale_gate.py`, `app/measurement/models/consumed.py`,
  `app/measurement/registry/validator.py` **byte-identical**; **all 16 migration SQL byte-identical**; **no `0017`
  SQL**. `attribution_context.py` diff is **docstring-only**.
- **Stricter-only (verified on real code, not just claimed):** an independent adversarial red-team enumerated
  `_risk` over **all 2187** combinations of the 6 RISK_LOCKS + `not_sellable` (absent/True/False), M6.2T vs M6.2U:
  **0** inputs where M6.2U is less strict, **0** new PASS; 64 inputs strictly stricter (63 HOLD→FAIL, 1 PASS→FAIL —
  the full-6 no-active-but-`not_sellable` case, the veto correctly overriding a would-be-clear). The mapper's veto is
  airtight on its direct channel across every decision variant (casing / whitespace / non-str / None / both the
  value-object and dict paths). No CRITICAL/MAJOR findings; the reconciliations were verified as strengthenings, not
  nerfs.
- Caches cleaned (`__pycache__` / `.pytest_cache` / `*.pyc` = 0). PII scan over the 7 changed files: 0 hits.

## Forward notes (recorded for the owner / TESTER / integrator — NOT blockers, NOT changed here)

1. **`recall_risk_contribution` does not carry the sellability veto (forward-wiring caveat).** By design (and
   byte-identical to M6.2T), this helper copies only the 3 `RECALL_RISK_KEYS`, so a **non-sellable-but-recall-clean**
   lot assembled into a full-6 picture **through this helper** would clear Risk to PASS (the veto silently would not
   fire). M6.2U introduces **no** loosening (identical in M6.2T), the helper is **unwired**, and the airtight veto
   channel is feeding `read.risk_flags` directly / checking `read.sellable` / `read.unverified` (which every test and
   the regression use). This is a sibling of the already-surfaced 3-of-6 partial-clear "forward gate-hardening
   finding." The S1b wiring step should feed the read's `risk_flags` (or `sellable`/`unverified`) directly, not route
   the veto through `recall_risk_contribution`.
2. **Pre-existing stale mapper docstrings (M6.2T, out of M6-OD-020 scope, left untouched).** The
   `recall_risk_mapper` module docstring and `risk_picture_complete` docstring still describe the gate's `_risk` as
   "reads any non-empty no-active map as PASS / does not require all 6 RISK_LOCKS" — a limitation that **M6.2T's**
   `_risk` all-6 hardening (M6-OD-019) already closed (see `conditions.py` `_risk` comment). The claim is stale in the
   **conservative** direction (it understates the gate's safety); the authoritative source (`conditions.py`) is
   correct. Fixing it spans multiple docstrings beyond the M6-OD-020 scope, so it is surfaced here rather than fixed.

## Rollback

Staged only — delete `04-artifacts/impl/M6.2U/` (M6.2T untouched). Per item: revert the `conditions.py` +
`recall_risk_mapper.py` stricter guards, the reconciled tests, `migrations/README.md`, and the `attribution_context.py`
docstring to M6.2T bytes; delete the new regression. No live migration to unwind (`live_migrations=false`). Every
change is a fail-closed tightening or a docs correction.

---

*STAGED implementation: no application runs against a live system, no migration is applied, no egress is opened, the
mapper is wired nowhere, no owner decision is resolved, no flag is flipped. `global_gateway_state=BLOCKED`,
`production_flag=OFF`, `external_send=OFF`. The runner gate + JUDGE decide (RULE-015).*
