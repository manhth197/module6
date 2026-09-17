# M6.2U PLAN — Recall E2 §3 conformance + migration renumber + docstring (M6-OD-020) (STAGED, plan-only)

**Prompt**: M6-P2901 (`M6_2U_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code) · **Gate**: EVIDENCE_GATE
**Slice**: M6.2U — fix the three chief-auditor 2026-09-16 M6-self-doable findings (**B3** recall E2 §3 conformance,
**B1/B4** migration renumber README, **D20** psid_hash docstring). **Leg 1 ADDS FAIL conditions** to the recall path
(NOT_SELLABLE, pull-error) — **stricter/fail-closed only, opens no PASS branch, loosens nothing**. The mapper stays
**UNWIRED**. Cumulative superset of M6.2T. No flag flipped, no egress.

> **Posture (immutable, this slice flips nothing):** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
> `external_send=OFF`, `live_migrations=false`; `app/config.py` unchanged. No self-cert (RULE-015); the runner gate +
> JUDGE (M6-P2909) decide.

Ledger verified: **M6-P2901 = RUNNING** (row 281), dependency **M6-P2900 = SIGNED** (entry gate PASS). Target
**LOCKED**, **M6-OD-011 DECIDED**. Owner input **DECIDED + FILED**: **M6-OD-020** (2026-09-17) — conform to chief
E2_BLOCK_REASON_V1 §1/§3 (canonical, wins conflicting docs); **SUPERSEDES the M6-OD-017 'never read decision' clause
ONLY** (the boolean mapping `recall = recall_hold OR recall_case_open` / `sale_lock` / `quality_hold` + presence-flag
→ FAIL stay in force). Reading `decision` is authorized **ONLY** for the sellability no-scale check; the recall
booleans are **STILL not derived from decision** (ops-core §4 preserved). Forward (NOT blockers): M6-OD-002/005 OPEN
(the gate already HOLDs, leg 1's added FAIL is armed-not-fired but conforms E2); M6-OD-011 server-bind (0017 SQL);
M6-OD-003/012 OPEN. C7 session-window is cross-team (Owner/M7), out of scope.

## 0. Top-0.1% lens + owner authorization (verified on the real M6.2T code + the decision record)

A real adversary (the M6.2U plan red-team) re-checks each call against the running `conditions.py` / mapper / tests:

- **[leg 1 mechanism — a DISTINCT `not_sellable` veto, NOT a 7th RISK_LOCK]** to make "decision ≠ SELLABLE → Risk
  FAIL" and "pull-error → Risk FAIL" while keeping the recall booleans + the M6.2T all-6 completeness UNCHANGED, the
  sellability signal is a **separate key `not_sellable`** that `_risk` checks **distinctly** (`if
  ctx.risk_flags.get("not_sellable"): return FAIL`), placed after the active-lock check and BEFORE completeness.
  `not_sellable` is **NOT** added to `RISK_LOCKS` (so `active_risk_locks`, the all-6 completeness, and every carried
  test that feeds all-6 / `{}` are UNCHANGED) and **NOT** in `RECALL_RISK_KEYS` (the `_UNKNOWN_KEYS` guard is
  unaffected). A context WITHOUT a `not_sellable` key (every non-mapper scale test) behaves exactly as before.
- **[reads `decision` ONLY for sellability; the recall booleans are untouched (ops-core §4)]** `map_risk_flags` adds
  `not_sellable = True` to `risk_flags` **only when `response.decision != "SELLABLE"`** (NOT_SELLABLE / unknown /
  missing). A **SELLABLE** response adds NO `not_sellable` key, so its `risk_flags` stays the **exact-3-key** recall
  map — carried exact-key assertions on a SELLABLE lot are unchanged. The `recall`/`sale_lock`/`quality_hold`
  booleans are still derived from the **presence booleans only** (a present recall lock FAILs even when SELLABLE).
- **[pull-error / incomplete → FAIL (not HOLD), fail-closed 'unverified']** the `_incomplete(...)` result (pull
  error / timeout / 429 / absent / malformed / non-bool) now returns `risk_flags={"not_sellable": True}` (an active
  veto → FAIL) + `unverified=True` — an unverified running campaign is treated as not-sellable (E2 §1). This is
  STRICTER than the prior empty-`{}`→HOLD; a bounded set of the mapper's OWN pull-error/incomplete tests asserted
  `HOLD`/`{}` and are reconciled honestly (§2 leg 1).
- **[stricter-only — SELLABLE + no-active still clears exactly as before; no PASS branch]** a SELLABLE, no-active,
  full-6 context → PASS (unchanged); the veto only ADDs FAILs. `is_scale_authorized` stays unreachable (M6-OD-002/005
  OPEN). Leg 1 opens NO PASS branch and loosens NOTHING.

**Scope discipline**: leg 1 = a stricter shared-gate `_risk` check + a stricter mapper (reads decision for
sellability, incomplete→FAIL) + honest reconciliation of the mapper's OWN tests. **NO migration SQL written** (leg 2
is README-only; the 0017 enforcement SQL is authored at server-bind). **NO config change, NO wiring, NO new secret,
NO flag flip, NO PASS branch.** The mapper stays UNWIRED.

## 1. Repo summary & staging model (cumulative carry-forward)

- **Base**: the whole **M6.2T** tree (app + 16 migrations `0001–0016` + the full carried suite, **729 green**).
  M6.2U is a superset: carry M6.2T byte-identical, edit `conditions.py` (leg 1) + `recall_risk_mapper.py` (leg 1) +
  `migrations/README.md` (leg 2) + `attribution_context.py` docstring (leg 3), reconcile the mapper's own tests, add
  a regression. (The carry runs in **M6-P2902 implement**.)
- **Stack** (locked target): Python 3.12, `framework=""` pure functions, `pytest -q`, stdlib only; in-memory only.
- **Layers touched** (ARCH_BASELINE): **Gate** (`_risk` sellability veto, leg 1) + the Gate-input recall mapper
  (leg 1) + a Source docstring (leg 3) + the migrations README (leg 2). Consume/measure-only; nothing sends/scales.
- **Baseline discipline (M6-P2902)**: verify green **before** any patch (parity with the M6.2T SIGNED collect =
  **729**), then green again after; **no skips**; **diff the edited files to confirm each is stricter** (a FAIL added,
  no PASS/clear added); actual `N passed` is the count.

## 2. The 3 legs — each mapped to an exit-gate leg + SMK-033 (stricter/fail-closed only, rollback per item)

Legend: **Leg** = M6.2U.md "Exit gate checks" number · **Smoke** = SMK-033 · file:anchor are M6.2T-current.

### LEG 1 — recall E2 §3 conformance (B3, M6-OD-020) → **SMK-033(i)(ii)(iii) · RULE-017 · RULE-018**

| File : anchor | Change (stricter/fail-closed ONLY) | Rollback |
|---|---|---|
| `app/measurement/scale/conditions.py` `_risk` (:122-129) | after the active-lock check (`if active: FAIL`), add a **distinct sellability veto**: `if ctx.risk_flags.get("not_sellable"): return ConditionResult(RISK, _FAIL, "sellability no-scale: decision not observed SELLABLE / unverified (E2 §3)")` — BEFORE the all-6 completeness check. `not_sellable` is **NOT** added to `RISK_LOCKS` (completeness + `active_risk_locks` unchanged). STRICTER (a new FAIL); no PASS branch. | revert the added check |
| `app/measurement/scale/recall_risk_mapper.py` `map_risk_flags` (:108-131) | read `response.decision` (M6-OD-020 authorizes it for THIS check only); after building the 3 recall booleans (unchanged), `if response.decision != "SELLABLE": flags["not_sellable"] = True`. A **SELLABLE** response adds NO `not_sellable` key (exact-3-key preserved). The recall booleans stay derived from presence booleans (ops-core §4). | revert the 2 lines |
| `app/measurement/scale/recall_risk_mapper.py` `_incomplete` (:104-105) | return `RecallRiskRead(risk_flags={"not_sellable": True}, complete=False, sellable=False, unverified=True, reason=reason)` — an incomplete / pull-error / malformed read is **'unverified' → not sellable → Risk FAIL** (fail-closed, not empty-HOLD). Add `sellable: Optional[bool] = None` + `unverified: bool = False` fields to `RecallRiskRead`. | revert the return + fields |
| `app/measurement/scale/recall_risk_mapper.py` `recall_risk_contribution` (:155-181) | **LEFT UNCHANGED** (byte-identical). **Red-team fix**: an earlier draft propagated `not_sellable` here, but that helper's return branches key ONLY on `RISK_LOCKS` — a `not_sellable`-only merged map would fall to `return {}` (HOLD, NOT the required FAIL), and a complete clean read would return a **7-key** map breaking `set(full.keys()) == RISK_LOCKS`. The veto is UNNECESSARY here (the mapper is UNWIRED; the veto reaches `_risk` via `read.risk_flags` fed DIRECTLY, exactly as SMK-030 / the regression do). Leaving it unchanged means it copies only the 3 `RECALL_RISK_KEYS`, so the carried collapse (`bare == {}`) + full-6-key-set tests stay GREEN with no reconciliation. | (unchanged) |
| `app/measurement/scale/recall_risk_mapper.py` module docstring (:1-21) | conform to **M6-OD-020**: the mapper reads `decision` **ONLY** for the sellability veto; the recall booleans are STILL not derived from decision (ops-core §4). (Supersedes the M6-OD-017 'never read decision' framing.) | revert the docstring |

- **Leg 1 (E2 §3, M6-OD-020)** — NOT_SELLABLE / unknown / missing decision → `not_sellable=True` → `_risk` **FAIL**
  (sellability no-scale, DISTINCT from the recall booleans); pull error/429/incomplete → `not_sellable=True` →
  **FAIL** (not HOLD) + `unverified`; a **SELLABLE + no-active-flag** full-6 context still **PASSes** (clears as
  before, nothing loosened). ← SMK-033(i)(ii)(iii).

- **HONEST RECONCILIATION of the mapper's OWN carried tests** (the slice mandates it; the JUDGE M6-P2909 verifies no
  nerf). This plan does NOT claim "no test breaks" — the `map_risk_flags` / `_incomplete` edits change the mapper's
  `risk_flags` output, so **every mapper test that feeds `read.risk_flags` DIRECTLY and asserts an exact key-set /
  `{}`** is affected. Two mechanical **RECONCILIATION RULES** cover them (M6-P2902 + its red-team run the real suite
  to confirm the complete list — the named tests below are the ones identified on the real code, not an exhaustive
  claim):
  - **RULE A (isolate the boolean tests): add `decision="SELLABLE"`** to any response whose test asserts the exact
    3-key recall map — so `not_sellable` is NOT added and the assertion is unchanged (the lot is made explicitly
    sellable; the recall-boolean behavior it tests is untouched). Applies to `test_recall_hold_maps_to_recall`,
    `test_output_keys_are_exactly_the_three_ops_core_locks`, and the SMK-030 `control_clean_complete_read` / the
    `clean` responses. **NOTE**: the collapse (`bare == {}`) + `test_full_six_lock` key-set tests stay GREEN with **no
    change** because `recall_risk_contribution` is unchanged (it copies only the 3 `RECALL_RISK_KEYS`, never
    `not_sellable`).
  - **RULE B (incomplete/pull-error now FAILs): `risk_flags == {}` / `_risk == HOLD` → `risk_flags ==
    {"not_sellable": True}` / `_risk == FAIL`** (the approve-refused / "does not clear" guarantee is PRESERVED — FAIL
    also refuses — a **strengthening**, not a nerf). Applies to `test_from_mapping_dict_path_and_malformed`,
    `test_pull_error_is_incomplete_and_gate_does_not_clear`, `test_value_object_nonbool_presence_flag_is_failclosed`,
    and the SMK-030 `neg_malformed_or_nonbool` (a bare `{}` fed with no `not_sellable` key still HOLDs — unchanged).
  - **`test_mapper_never_reads_decision` + SMK-030 `neg_never_reads_decision`**: rename/reframe to "never DERIVES the
    recall booleans from decision (ops-core §4); decision read ONLY for the sellability veto (M6-OD-020)"; the recall
    booleans stay unchanged, and the `decision="RECALL"` clean map now asserts booleans-unchanged + `not_sellable is
    True` + `_risk FAIL` (the new correct behavior). The certified clear-path (SELLABLE + full-6 → PASS) is untouched.

- **CODER regression** `tests/test_m6_2u_recall_e2_conformance.py`: NOT_SELLABLE + all flags false → gate **FAIL**;
  unknown / missing decision → FAIL; pull-429 → FAIL + `unverified`; a **SELLABLE + no-active + full-6** context still
  **clears** (PASS); the recall booleans are **NOT** derived from decision (recall_hold=True + decision=SELLABLE →
  recall True; recall_hold=False + decision=NOT_SELLABLE → recall False, not_sellable True); the mapper stays UNWIRED.

### LEG 2 — migration renumber README (B1/B4) → **SMK-033 (docs leg) · RULE-018**

| File | Change (docs-only) | Rollback |
|---|---|---|
| `migrations/README.md` | the README is STALE (it lists only `0001`→`0005`). Update it to list **`0001`–`0016`** (the M6.2B–M6.2Q migrations already in the tree) with the apply order, **plus** a note that the **enforcement migration is `0017`** (renumbered from the taken `0014`; `0014–0016` are M6.2Q ads_spend), **authored at server-bind — no SQL file written here**. The registry `M6-OD-011.json` / `DECISION_REGISTER` / `SCHEMA_CHANGELOG` are already corrected to `0017` (00-spec, operator-owned). | revert the README to M6.2T bytes |

### LEG 3 — psid_hash docstring (D20) → **SMK-033 (docs leg) · RULE-014**

| File : anchor | Change (docstring-only, CODE UNCHANGED) | Rollback |
|---|---|---|
| `app/measurement/models/attribution_context.py` `as_stored` docstring (:133-137) | correct the line "Trace joins use `psid_hash` (deterministic per pepper), not a raw id." → conform to **M6-OD-015 no-join**: cross-module trace joins use `live_session_id` / `comment_id` / `messenger_thread_id` + the `attribution_id` surrogate — NOT a `psid_hash` join (there is already no `psid_hash` join in code; `psid_hash` remains a one-way salted hash carried on the row, never a join key). `as_stored()` code is UNCHANGED. | revert the docstring |

### LEGS 4–7 (other roles)

4 SMK-033 executed-or-waived (**TESTER** M6-P2903/2904). 5 all evidence schema-valid. 6 judge PASS (M6-P2909) —
verifies stricter-only, no nerf, no certified clear-path loosened, recall booleans still not derived from decision,
mapper still UNWIRED. 7 rollback (this §2 + §5). The coder legs never self-run/self-certify the smoke (RULE-015).

## 3. Backward-compat & honest reconciliation (verified on real code)

- **Leg 1 is stricter-only + the ONLY carried breaks are in the mapper's OWN tests** — the `not_sellable` veto is a
  distinct key NOT in `RISK_LOCKS`, so every non-mapper scale test (`test_scale_gate_risk_veto`,
  `test_risk_recheck_at_approval`, the M6.2T hardening tests, SMK-009, `make_scale_context` all-6 / `{}`) is
  UNCHANGED (they carry no `not_sellable` key). The mapper's own tests break because the mapper's output now carries
  the sellability veto (NOT_SELLABLE / incomplete → FAIL); each is reconciled HONESTLY (§2 leg 1) to the new correct
  behavior — a **strengthening, never a nerf**; the certified clear-path (SELLABLE + full-6 → PASS) is preserved.
  M6-P2902 runs the real suite to confirm the COMPLETE reconciliation list (learning from M6.2T: the plan does not
  claim "no test breaks" — it enumerates the expected breaks + the honest fix, and the implement verifies).
- **Legs 2–3 are docs-only** (README + a docstring); no code path changes; `config.py` / `consumed.py` / `validator.py`
  stay byte-identical; migrations `0001–0016` (SQL files) unchanged (no `0017` SQL written).

## 4. Rules / fail gates, scope & governance

- **RULE-017** (risk veto): leg 1 ADDs a sellability FAIL to `_risk` — strictly more fail-closed. **RULE-018** (Core
  owner wins): M6 conforms to the chief-canonical E2 §3 (M6-OD-020 supersedes the module-level M6-OD-017 narrowing);
  the recall booleans + M3 gating are not owned/derived by M6. **RULE-015**: proven by the SMK-033 regressions.
  **FAIL-006**: leg 1 opens no PASS branch; `is_scale_authorized` stays unreachable.
- **In scope**: the 3 legs. **Out of scope (untouched)**: WIRING the mapper into any live pull / `app/` caller (S1b
  seam / server-bind); the C7 session-window design (cross-team, Owner/M7); writing the `0017_enforcement` SQL
  (authored at server-bind); opening the Scale-Gate PASS path (M6-OD-002/005); flag flips. Posture OFF/BLOCKED/OFF.
- **Boundary intact**: leg 1 only makes the gate FAIL more (never clears more, no PASS branch, no scale executed —
  RULE-010/FAIL-006); the mapper stays UNWIRED; reading `decision` is for M6's OWN sellability gate, not owning the
  recall decision or M3 gating (RULE-018); no CRM/egress/commission. `M6-P1000` / `M6-P1309` stay BLOCKED.
- **Forward conditions (recorded, NOT blockers)**: M6-OD-002/005 OPEN (leg 1's FAIL is armed-not-fired; opens no PASS
  branch); M6-OD-003/012 OPEN; the S1b wiring seam + live M3 endpoint + the `0017` enforcement SQL + M6-OD-011
  server-bind/go-live remain hard gates before any live wiring / real scale / egress.

## 5. Verification plan for M6-P2902 (commands + PASS/FAIL + rollback)

**Commands** (`PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider`): carry M6.2T → `impl/M6.2U/`
(exclude caches; keep this `PLAN.md`), baseline green + parity **before** any patch (expect **729**); apply the leg-1
gate + mapper edits + the honest reconciliations + the leg-2/3 docs; re-run green (no skips — the only carried
changes are the mapper's own reconciled tests); **diff the edited code files to confirm each is stricter (a FAIL
added, no PASS/clear/allow added)**; confirm `config.py`/`consumed.py`/`validator.py` byte-identical, migrations
`0001–0016` SQL unchanged (no `0017` SQL), no new flag/secret, mapper still UNWIRED (no new `app/` import), clean
caches, PII scan.

**PASS/FAIL checklist**: NOT_SELLABLE / unknown decision → `_risk` FAIL (sellability veto, distinct) ✓/✗ · pull-error
/ incomplete → FAIL (not HOLD) + `unverified` ✓/✗ · SELLABLE + no-active + full-6 → PASS (clears as before) ✓/✗ ·
recall booleans NOT derived from decision (present lock FAILs even SELLABLE; a clean lot's booleans False) ✓/✗ ·
`not_sellable` NOT in RISK_LOCKS (all-6 completeness + non-mapper scale tests unchanged) ✓/✗ · migrations README lists
0001-0016 + 0017-note ✓/✗ · psid_hash docstring conforms to M6-OD-015 no-join (code unchanged) ✓/✗ · the mapper's own
tests reconciled honestly, NONE nerfed, certified clear-path preserved ✓/✗ · full suite green (baseline ≤ final) ✓/✗
· posture + no flag/secret + no migration SQL + mapper UNWIRED ✓/✗.

**Rollback**: staged only — delete the `04-artifacts/impl/M6.2U/` tree (M6.2T untouched). Per item: `conditions.py` +
`recall_risk_mapper.py` → scoped revert of the stricter guards to M6.2T bytes; the reconciled mapper tests + the
SMK-030 assertions → revert to M6.2T bytes; `migrations/README.md` + the `attribution_context.py` docstring → revert
to M6.2T bytes; the new regression → delete. No live migration to unwind (`live_migrations=false`). Every change is a
fail-closed tightening or a docs correction; a revert restores prior behaviour.

---

*Plan-only: this document writes no application code, applies no migration, opens no egress, wires nothing, resolves
no owner decision, and flips no flag. It plans an owner-authorized (M6-OD-020, conforming to chief E2 §3), STAGED,
stricter/fail-closed recall-path conformance + a migration-README renumber + a docstring correction.
`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`. The runner gate + JUDGE decide (RULE-015).*
