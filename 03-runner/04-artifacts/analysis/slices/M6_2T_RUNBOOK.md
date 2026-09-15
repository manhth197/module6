# M6.2T — Slice Runbook — Pre-wiring hardening: Scale-Gate clear-path + reader PII-reject + residuals (M6-OD-019)

> **Status: STAGED — the FIRST gate-logic change since M6.2Q, verified stricter/fail-closed-direction ONLY. It flips
> nothing, wires nothing, and opens no PASS branch.**
> M6.2T is the owner-authorized (M6-OD-019, DECIDED 2026-09-10) **pre-wiring hardening** that closes the 4
> armed-not-fired forward findings routed to the owner by the M6.2R (M6-P2609) + M6.2S (M6-P2709) judge sign-offs, now
> the ops-core account is live (pin `54eb5f5`) and S1b wiring is near. Four legs, cumulative superset of M6.2S. Because
> leg 1 edits `conditions.py` + `scale_gate.py`, the **gate byte-identity streak (M6.2Q→R→S) is deliberately broken** —
> so the load-bearing question is not "did it pass" but **"is every change strictly in the fail-closed direction, with
> no certified behavior loosened and no test nerfed?"** — and the boundary (M6-P2805) + security (M6-P2806) reviews both
> answer yes on the actual source (PASS-eligible, not self-certifying); the definitive verdict is the Judge's (M6-P2809).
>
> **Read the three honesty points first — for a gate-touching slice they matter more than the green count:**
> 1. **Stricter-only was verified on the actual M6.2S→M6.2T source by the boundary + security reviews (PASS-eligible;
>    the definitive verdict is M6-P2809's), not merely asserted.** `conditions._risk`: **NEW-PASS ⊂
>    OLD-PASS** — a partial no-active map now returns HOLD (was PASS, closes the M6.2R G4/N2 finding); the certified
>    all-6-no-active → PASS path is preserved; `{}` → HOLD is behaviorally preserved (the HOLD branch was rewritten/
>    re-messaged, not byte-identical); only any active → FAIL is byte-identical. `scale_gate.
>    _assert_risk_clear_at_approval`: an `isinstance(bool)` **AND-conjunct** is added so a falsy non-bool lock
>    (`0`/`''`/`None`) no longer clears — **NEW-clear ⊂ OLD-clear**; the active-veto + proposal-PASS fallback are
>    unchanged. **No new PASS/clear branch was opened.** The ONE carried test the change touches (`test_smk_030` line
>    ~159) is a **strengthening, not a nerf**: the "gate CAN PASS" non-vacuity proof is preserved (re-pointed at a
>    complete all-6 no-active map, still asserting PASS) **and** a new `3-of-6 → HOLD` assertion is added; no assertion
>    deleted/weakened. This was verified by **two independent gate reviews** (boundary N4 OLD→NEW truth table + security
>    line-level code-read) **plus the coder's own in-prompt red-team** — and the honesty machinery worked: the **plan
>    red-team caught the coder's first-draft false "no test breaks" claim** and pre-specified the honest reconciliation.
> 2. **Reachability correction — the Scale GATE is WIRED (this retracts the M6.2R/M6.2S "unwired" framing for the gate).**
>    The Scale Gate is reachable via `app/api/scale_requests.py` (`handle_scale_decision` → `ScaleGate.
>    record_owner_decision`); it is **only the recall mapper + registry reader that stay UNWIRED**. So the gate's
>    FAIL-006 containment is **not** an "unwired" story — it is (a) the **leg-2 HOLD floor** (`is_scale_authorized`
>    structurally unreachable while M6-OD-002/005 are OPEN) and (b) **RULE-H03** (`ScaleContext.risk_flags` is
>    server-assembled, not injectable from the untrusted admin body). The junk-falsy residual below is contained by these
>    two, not by non-reachability.
> 3. **The legs close MOST, not ALL, of their targets — stated so "closed" is not overread:**
>    - **L1g (parity gap):** leg 1 added bool-ness to the approval path (`_assert`) but **not** to `conditions._risk`,
>      which still validates lock **presence** only — so a full-6 junk-falsy map (`{all6: 0}`) still PASSes `_risk` at
>      propose, and the approval fallback then clears via that propose-time PASS. Contained today by the HOLD floor + the
>      `Mapping[str,bool]` type contract + RULE-H03. Owner/CODER: mirror `isinstance(bool)` in `_risk` for full parity.
>    - **Leg 3 is best-effort INPUT narrowing, NOT the primary FAIL-008 control.** The primary control is **export-side
>      masking (M6-OD-012), which M6.2T deliberately did NOT add.** A shape detector under-catches (not `updated_at` —
>      L3c; a customer name or a <9-digit id slips it — N3) and can over-reject legit governance codes (L3d/N2). Do not
>      over-attribute FAIL-008 completeness to leg 3.
>    - **L4c:** leg-4's N5 handling is **observability-only, not a hard block** — `_resolve_typed` flags a non-str
>      sibling as malformed but **still calls `resolver(raw)`**, so a hostile `__eq__`/`__hash__` object could still
>      coerce to `ALLOW_EXTERNAL` (in-process only; validator byte-identical, so no loosening — but the edge is carried,
>      not closed). The coder's IMPL_NOTES phrased this as "non-str → fail-closed default"; the boundary (executed) +
>      security (code-read) find it flag-not-block — the executed reading is authoritative.
>
> Posture immutable: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, both scale floors
> `False`, `live_migrations=false`. `M6-P1000` + `M6-P1309` remain **BLOCKED (not converted)**; the pack still tops at
> `OWNER_REVIEW_REQUIRED`. Evidence: full staged suite **743 passed / 0 failed, rc 0**; SMK-032 PASS 14/14; boundary
> **26 outcomes = 18 DEFENDED / 5 OPEN_NONGATE / 3 NOTE / 0 in-scope FAIL-006/008 breach / 0 LOOSENING**; security
> **0** raw PII / **0** secrets (incl. **0** `client_secret`) / 285 files. Next: slice-gate Judge **M6-P2809** (the
> definitive stricter-only / no-nerf / unwired verdict).

| Field | Value |
|---|---|
| Slice | **M6.2T** — Pre-wiring hardening: Scale-Gate clear-path + reader PII-reject + residuals; post-pilot; depends on M6.2S; closes the M6.2R (P2609) + M6.2S (P2709) forward findings; ops-core account live 2026-09-10 (pin `54eb5f5`) |
| Prompt (this doc) | **M6-P2808** — `M6_2T_DOCS` (ANALYST_ARCHITECT, `analysis_only`, EVIDENCE_GATE) |
| Rules / fail gates in scope | **RULE-017** (risk hard veto) · **RULE-014** (no raw PII) · **RULE-015** (no self-cert) · **FAIL-006** (auto scale/publish) · **FAIL-008** (raw PII on a durable/export surface) |
| Smoke in scope | **M6-SMK-032** (4-leg hardening) — proposed HARDENING, **executed 14/14** (not owner-waived) |
| Contracts | M6-CTR-026 + M6-CTR-003 → resolved-for-entry (per the M6.2R/M6.2S harmonization chain) |
| Owner inputs (DECIDED) | **M6-OD-019** (pre-wiring hardening — DECIDED 2026-09-10; artifact filed) |

---

## 1. What this slice built (staged under `04-artifacts/impl/M6.2T/`)

M6.2T carries the **entire M6.2S tree byte-identical** (baseline verified green **before any patch: 716 passed**,
byte-parity, `251 .py == 251 .py`, `16 .sql == 16 .sql`) and makes **4 stricter carried-file edits + 1 honest test
reconciliation + 3 new regression tests**. **No migration** (still `0001–0016`), **no config change**, **no new enum**,
**no wiring**. The **reuse-only trio is byte-identical to M6.2S** (independently sha256-verified this turn:
`config.py`=`911b32381368f355`, `consumed.py`, `validator.py`); the **4 hardening files differ** (verified this turn) —
that is the entire delta breaking the byte-identity streak, nothing else.

| Leg | Edit (stricter / fail-closed ONLY) | File |
|---|---|---|
| **1 — clear-path (closes G4; N2 approval path hardened, propose-time L1g open)** | `_risk` PASS now requires a **complete** read: a partial no-active map → **HOLD** (was PASS); all-6-no-active → PASS (preserved); `{}` → HOLD (behaviorally preserved — the HOLD branch was rewritten, not byte-identical); active → FAIL (byte-identical). **NEW-PASS ⊂ OLD-PASS.** | **edited** `app/measurement/scale/conditions.py` |
| **1 — approval bool-ness** | `_assert_risk_clear_at_approval` gains an `isinstance(current_risk_flags[lock], bool)` AND-conjunct — a falsy non-bool lock (`0`/`''`/`None`) no longer clears the fresh-read path. **NEW-clear ⊂ OLD-clear.** | **edited** `app/measurement/scale/scale_gate.py` |
| **1 — honest reconciliation** | `test_smk_030` ~line 159: the non-vacuity control is re-pointed at a full all-6 no-active map (still asserts PASS) **and** a new `3-of-6 → HOLD` assertion added. A **strengthening, not a nerf** (the one carried test the leg-1 change affects). | **edited** `tests/smoke/test_smk_030_...py` |
| **3 — input-side PII reject (F-FEED-PII)** | `_looks_like_pii()` + a parse-loop guard: `event_code`/`event_group`/`domain` carrying a customer-PII shape (email/phone/`\d{9,}`/psid-prefix) → `feed_error:pii_shape_in_governance_field` (reject, state UNCHANGED; input-side, not export masking). Plus leg-4 `_resolve_typed` `isinstance(str)`/enum guard (N5) + `malformed_fields` observability (N6). | **edited** `app/measurement/adapters/registry_feed_reader.py` |
| **4 — mapper residuals (N3/N9)** | `RecallRiskContributionError` — `recall_risk_contribution` rejects a `base_flags` carrying any `RECALL_RISK_KEY` (no silent overwrite); `from_mapping` fail-closed on a non-iterable / bare-string `block_reasons` → `None` (prevents the `tuple(<non-iterable>)` crash). | **edited** `app/measurement/scale/recall_risk_mapper.py` |
| **2 — HOLD-floor lock (regression only, no app change)** | pins `is_scale_authorized` structurally unreachable even with BOTH config floors monkeypatched True (`_funnel`/`_dashboard` have no PASS branch). | **new** `tests/test_m6_2t_hold_floor_lock.py` |
| **1 + 4 regressions** | leg-1 (partial→HOLD, full-6→PASS, {}→HOLD, active→FAIL, all-6-real-bool clears, falsy-non-bool does not clear); leg-3 PII reject + legit-code non-trip; leg-4 N5/N6/N3/N9. PII-shaped values assembled at runtime (no literal PII in source). | **new** `tests/test_m6_2t_gate_clear_path_hardening.py`, `tests/test_m6_2t_residuals_hardening.py` |

---

## 2. Operate

M6.2T changes only the fail-closed *direction* of an already-staged mechanism; there is no new surface, no wiring, no
egress. What the hardening does at runtime:

1. **Scale-Gate clear-path (leg 1, the WIRED gate).** The gate is reachable via `app/api/scale_requests.py`. At propose,
   `conditions._risk` now returns HOLD unless all 6 `RISK_LOCKS` are observed and none active; at approval,
   `_assert_risk_clear_at_approval` refuses to clear on a falsy non-bool lock. Both directions only add HOLD/refuse — no
   new PASS/clear path. `ScaleContext.risk_flags` is **server-assembled** (RULE-H03), so the untrusted admin body cannot
   inject a clean risk picture.
2. **HOLD floor (leg 2).** `is_scale_authorized` stays structurally unreachable while M6-OD-002/005 are OPEN; the leg-2
   regression pins this even with both config floors monkeypatched True — a future PASS-branch refactor will FAIL it
   **loudly** instead of silently arming the residuals. *The containment depends on M6-OD-002/005 staying OPEN (§5.6).*
3. **Registry reader (leg 3, still UNWIRED).** `RegistryFeedReader.apply` rejects fail-closed at parse a governance
   field carrying a PII shape (`feed_error:pii_shape_in_governance_field`, version+rows unchanged); the reject reason is
   a static token (no PII echoed). Best-effort input narrowing — see §5.3.
4. **Mapper residuals (leg 4, still UNWIRED).** `recall_risk_contribution` raises on a base carrying a mapper-owned key;
   `from_mapping` fails closed on a non-iterable `block_reasons`; `_resolve_typed` flags a non-str sibling (observable),
   though it does not hard-block it (L4c, §5.5).
5. **What stays impossible:** a live ops-core/M3 call, wiring the mapper/reader, external send, a flag flip, a PASS
   branch, an event write/invent/reconcile. `config.py`/`consumed.py`/`validator.py` byte-identical to M6.2S.

---

## 3. Verify

### 3.1 The official smoke (SMK-032 PASS 14/14, executed not waived; masked `correlation_id`+`evidence_id`)

14 nodes across 10 functions (`leg_i_falsy` ×3, `leg_iii_pii` ×3, + 8 single):
- leg i — `_risk` on a partial 3-of-6 no-active map → **HOLD** (all-6 required); complete all-6 no-active → PASS
  (non-vacuous); `{}` → HOLD; active → FAIL (unchanged). A falsy non-bool lock (`0`/`''`/`None`) at approval does **not**
  clear → `ScaleGateViolation`, request stays PROPOSED. Control: an all-6 real-bool fresh read still clears → APPROVED.
- leg ii — both config floors monkeypatched True + best context + owner APPROVE → `is_scale_authorized` False, overall
  HOLD; monkeypatching `_funnel`/`_dashboard` to PASS lifts the sole floor (demonstrating the structural unreachability
  the regression pins — a real PASS branch would flip it and fail loudly).
- leg iii ×3 (email / phone / long-digit on `event_code`/`event_group`/`domain`) — rejected fail-closed
  `feed_error:pii_shape_in_governance_field`, version+rows UNCHANGED. Control: `ORDER_VERIFIED`/`ads.core`/`ads` apply
  (the reject is shape-caused, not blanket).
- leg iv — `recall_risk_contribution` raises `RecallRiskContributionError` on a base carrying `recall`/`sale_lock`/
  `quality_hold` (an other-locks base is accepted, returns the full 6-lock no-active map); `from_mapping` → None on a
  non-iterable/bare-string `block_reasons`; a non-str `data_sensitivity`/`external_send_policy` → `PII`/`BLOCKED_DEFAULT`
  with `malformed_fields == 2` (N5/N6).
- posture — `EXTERNAL_SEND=="OFF"`, `PRODUCTION_FLAG=="OFF"`, `GLOBAL_GATEWAY_STATE=="BLOCKED"`.

### 3.2 Full staged suite (count discipline)

```
# from 04-artifacts/impl/M6.2T/  (venv: 02-tester/.venv, python 3.12.14, pytest 8.4.2; -B, cache-free, no shell redirection)
python -B -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider'])>"   # -> RC 0 ; 743 passed / 0 failed
python -B -c "<tally; pytest.main(['-k','test_smk_032','-p','no:cacheprovider'])>"          # -> RC 0 ; 14 passed
```

**Reconciliation: 743 (tester-run final) = 716 carried (M6.2S SIGNED) + 13 coder M6.2T regression cases (→ 729 coder
baseline) + 14 official-smoke nodes (SMK-032 = 10 functions).** Coder baseline before any patch was 716 (byte-parity);
the gate invariant `baseline ≤ coder ≤ final (716 ≤ 729 ≤ 743)` holds, **0 carried test dropped, 0 skip**; the isolated
`-k` run independently confirms 14 passed; the build-side collect-only count (M6-P2803) was also 743. *(The plan red-team
also corrected the baseline figure **688 → 716** — 688 was M6.2S's implement-time count; the SIGNED M6.2S tree collects
716, the real baseline used throughout. The SMK-030 reconciliation edits an existing test's assertions — it adds no
node; the +13 is the 3 new regression files' cases. pytest's terminal
summary is unreliable here, so totals came from an in-process `pytest_runtest_logreport` tally with `pytest.main() RC=0`
— see SMOKE_RESULTS.md "On counting".)*

### 3.3 The in-scope gates — stricter-only PROVEN, FAIL-006/008 not tripped, 0 loosening

- **Boundary (M6-P2805): 26 outcomes = 18 DEFENDED / 5 OPEN_NONGATE / 3 NOTE / 0 in-scope FAIL-006/008 breach / 0
  LOOSENING.** The load-bearing negative result (N4): stricter-only verified against the **actual M6.2S source** —
  `_risk` NEW-PASS ⊂ OLD-PASS (no new PASS branch), `_assert` added the `isinstance(bool)` conjunct (NEW-clear ⊂
  OLD-clear), the `active_risk_locks` FAIL veto byte-identical. L2 crown jewel: a maximally-cleared all-6-clean
  owner-APPROVED request still yields `overall=HOLD` / `is_scale_authorized=False`, holding even with both floors
  monkeypatched True.
- **Security (M6-P2806): 0 raw PII / 0 real secrets / 285 files** (canonical `0/0/0/0/0`, incl. **0** `client_secret`;
  the 4 non-canonical hits carried from M6.2O, benign). The leg-3 regexes are patterns, not literal digit runs; leg-3/4
  tests assemble PII-shaped values at runtime (no literal PII in source). Security concurs leg 1 is stricter-only on the
  code and the SMK-030 reconciliation is a strengthening.
- **On-disk byte-identity (independently verified this turn):** `config.py`/`consumed.py`/`validator.py` byte-identical
  S↔T; `conditions.py`/`scale_gate.py`/`recall_risk_mapper.py`/`registry_feed_reader.py` differ (exactly the 4 hardening
  files); migrations `0001–0016` unchanged; tree delta +4 .py (3 coder + 1 tester smoke).

---

## 4. Rollback (every change this slice made) — *acceptance check 1*

Staged-only and non-destructive: nothing live, no migration applied (`live_migrations=false`), no flag flipped, no
egress opened, no wiring. **First slice since M6.2Q where rollback includes a scoped revert of edited application code**
(the 4 hardening files) — every edit is a fail-closed *tightening*, so a revert restores the prior (looser) M6.2S
behaviour.

| Change | Rollback |
|---|---|
| **Whole slice** | delete the `04-artifacts/impl/M6.2T/` tree — M6.2S is byte-identical and untouched; no live migration to unwind |
| **Edited gate — `conditions.py` `_risk` (leg 1)** | **scoped revert** the all-6-completeness guard to M6.2S bytes (restores the looser partial-no-active → PASS) |
| **Edited gate — `scale_gate.py` `_assert_risk_clear_at_approval` (leg 1)** | **scoped revert** the `isinstance(bool)` conjunct to M6.2S bytes |
| **Edited reader — `registry_feed_reader.py` (leg 3 + N5/N6)** | **scoped revert** `_looks_like_pii`, the parse-loop guard, the `_resolve_typed` `isinstance(str)` flag, and `malformed_fields` to M6.2S bytes |
| **Edited mapper — `recall_risk_mapper.py` (leg 4 N3/N9)** | **scoped revert** `RecallRiskContributionError` + the base-key guard + the `from_mapping` non-iterable guard to M6.2S bytes |
| **Edited test — `tests/smoke/test_smk_030_...py` (leg 1 reconciliation)** | **scoped revert** the non-vacuity assertion to the M6.2S bytes (3-of-6 → PASS); this is the one carried test the leg-1 change touched |
| **New tests** — `test_m6_2t_gate_clear_path_hardening.py`, `test_m6_2t_hold_floor_lock.py`, `test_m6_2t_residuals_hardening.py` | delete the files |
| **New official smoke** — `tests/smoke/test_smk_032_prewiring_hardening.py` (+ `tests/TEST_MANIFEST.md` delta) | delete the file / revert the manifest delta |
| **Reuse-only files** — `config.py`/`consumed.py`/`validator.py` | **none** — byte-identical to M6.2S (each sha256-verified) |
| **Migration / config flag / new enum** | **none** — migrations `0001–0016`, `config.py` byte-identical, no new enum |
| **Boundary / security / tester / PM / docs analysis-only + evidence writes** (`M6.2T_boundary.md`, `M6.2T_security.md`, harness/scanner scripts under `work/`; `test-reports/M6.2T/SMOKE_RESULTS.md`; `evidence/prompts/M6_2T_EVIDENCE_INDEX.md` + band `M6-P2800…2808.json`; this `analysis/slices/M6_2T_RUNBOOK.md` + `M6-P2808.json`) | delete / revert — all analysis-only or evidence-collection writes; none modified any source, gate, migration, or `04-artifacts/state/` |

---

## 5. Decision deltas & governance

### 5.1 Honesty point 1 — stricter-only was verified by the boundary + security reviews (Judge M6-P2809 definitive), and the one test break was honestly reconciled (the gate-change crux)

This is the first change to `conditions.py`/`scale_gate.py` since M6.2Q, so the entire risk is a **loosening** (a
hardening that accidentally clears/passes more) or a **nerfed test**. Both are refuted **on the actual source**:
- `conditions._risk` — **NEW-PASS ⊂ OLD-PASS**: the change only *removes* a spurious PASS (partial no-active → HOLD).
  The certified all-6-no-active → PASS path is preserved; `{}` → HOLD and active → FAIL unchanged. No new PASS branch.
- `scale_gate._assert_risk_clear_at_approval` — the `isinstance(bool)` conjunct is ANDed onto the existing clear
  predicate: **NEW-clear ⊂ OLD-clear**. The active-lock veto and proposal-PASS fallback are unchanged.
- **The one carried test break was caught and reconciled honestly.** `test_smk_030` line ~159's non-vacuity control
  (mapper CLEAN 3-of-6 → PASS, which is now correctly HOLD) was re-pointed at a complete all-6 no-active map (still
  asserting PASS — the "gate CAN PASS" proof preserved) **and** a `3-of-6 → HOLD` assertion added. A **strengthening,
  not a nerf**; no assertion deleted/skipped/weakened. **The plan red-team caught the coder's first-draft false "no test
  breaks" claim** (a prototype on the SIGNED suite went 716 → 715/1 FAIL) and pre-specified this reconciliation — the
  honesty machinery worked as designed.
- **Verified by two independent gate reviews** (boundary N4 OLD→NEW truth table + security line-level code-read) **plus
  the coder's own in-prompt red-team.** (Not "three independent reads" — the impl red-team ran inside the coder's own
  M6-P2802 prompt, not as an independent gate.)

### 5.2 Honesty point 2 — the reachability correction: the Scale GATE is WIRED (retracting the earlier "unwired" framing)

My own M6.2R and M6.2S runbooks leaned on "unwired" as the FAIL-006 containment story. **For the gate that is now
inaccurate and is corrected here:** the Scale Gate is **wired** via `app/api/scale_requests.py` (`handle_scale_decision`
→ `ScaleGate.record_owner_decision`). It is **only the recall mapper + registry reader that stay UNWIRED** (no non-test
`app/` module imports them — grep-clean, verified). So the gate's containment is:
- the **leg-2 HOLD floor** — `_funnel`/`_dashboard` have no PASS branch while M6-OD-002/005 are OPEN, so
  `is_scale_authorized` is structurally unreachable (holds even with both config floors monkeypatched True); and
- **RULE-H03** — `ScaleContext.risk_flags` is **server-assembled**, not injectable from the untrusted admin body (a body
  claiming a clean picture cannot override a server context with an active lock → FAIL).

The junk-falsy residual (§5.3) is contained by these two, **not** by non-reachability. One mechanism the judge should
note: the approval re-check reads `deps.context.risk_flags` — the **same source as propose**, not an independent second
observation — so a propose-time `_risk` PASS on a full-6 junk-falsy map is exactly what the approval bool-ness check
falls back to and clears. That is why closing L1g needs **both** mirroring `isinstance(bool)` in `conditions._risk`
**and** drawing an independent validated read at approval (§5.6); the current "fresh-read" clears against the
propose-time picture, not a fresh independent one. The judge should read the containment story this way.

### 5.3 Honesty point 3 — the legs close most, not all, of their targets

- **L1g (leg-1 parity gap → owner/CODER):** bool-ness landed in the approval path (`_assert`) but **not** in
  `conditions._risk`, which still validates lock **presence** only. A full-6 junk-falsy map (`{all6: 0}`) still PASSes
  `_risk` at propose, and the approval fallback clears via that propose PASS. Contained today by the HOLD floor +
  `Mapping[str,bool]` type contract + RULE-H03; it becomes channel-reachable only if a future wiring assembles
  `deps.context.risk_flags` from the feed/mapper without a full-6-real-bool validation. Fix: mirror `isinstance(bool)`
  in `_risk`.
- **Leg 3 is best-effort INPUT narrowing, NOT the primary FAIL-008 control.** The primary control for the
  governance-metadata export is **export-side masking (M6-OD-012), which M6.2T deliberately did NOT add** — and the live
  containment is still that the reader is UNWIRED (no durable sink). A shape detector inherently under-catches: it does
  not check `updated_at` (L3c — a PII-shaped `updated_at` is applied + echoed raw); a customer **name** (no `@`, no
  ≥9-digit run, no listed prefix) and a **short id** (<9 digits) slip `_looks_like_pii` (N3); and it can **over-reject**
  a legit ≥9-digit or prefixed governance code, stalling the whole delta (L3d/N2 — fail-closed, an availability/tuning
  concern that would surface at go-live). Do not over-attribute FAIL-008 completeness to leg 3.
- **L4c (leg-4 N5 flag-not-block → CODER):** `_resolve_typed` **flags** a non-str sibling as malformed but **still calls
  `resolver(raw)`**, so a hostile `__eq__`/`__hash__` object could still coerce to `ALLOW_EXTERNAL` via the enum
  value-lookup — in-process code-exec only (a JSON feed yields `str`/`None`/`int`, all fail-closed); the validator is
  byte-identical to M6.2S (no loosening), but the edge is **carried, not closed**. The coder's IMPL_NOTES phrased this
  as "non-str → fail-closed default"; the boundary (executed) + security (code-read) find it flag-not-block — the
  executed reading is authoritative. Fix: **block** (return the fail-closed default without calling the resolver).

### 5.4 What is genuinely good (credited, not rosy)

- The four legs **do** close the exact residuals the M6.2R + M6.2S judges routed to the owner (G4/N2 clear-path;
  F-FEED-PII input-side; N3/N9 mapper; N5/N6 reader; the HOLD-floor lock), all in the fail-closed direction, with **0
  loosening** proven against the actual source.
- The leg-2 HOLD-floor regression is a durable safety asset: it converts a silent future-refactor risk (a PASS branch on
  `_funnel`/`_dashboard`) into a **loud test failure**.
- The honesty process caught its own miss: the plan red-team killed a false "no test breaks" claim and pre-specified the
  honest SMK-030 reconciliation — the slice records the one test break rather than hiding it.

### 5.5 Residuals (armed-not-fired; none trips an in-scope gate; 0 loosening)

- **L1g (owner/CODER):** mirror `isinstance(bool)` in `conditions._risk` (propose-time presence-only gap). §5.3.
- **L3c (SECURITY/owner):** extend the leg-3 field set to `updated_at` (or a value-scrub). §5.3.
- **N3 (SECURITY/owner):** leg-3 under-catch (names / short ids) — the primary FAIL-008 control is the M6-OD-012
  export-side masking, not the shape detector. §5.3.
- **L3d/N2 (owner/CODER):** the leg-3 detector over-rejects legit ≥9-digit / prefixed governance codes (availability at
  go-live) — confirm no legit code matches, or anchor/tighten the regexes.
- **L4c (CODER):** `_resolve_typed` block-not-flag (carried M6.2P/M6.2S N5). §5.3.
- **S3 carried export residuals (→ M6-OD-012 / chief):** `RegistryFeedRow`/`OwnerDecision` (M6.2R **F-SEC-2R-1**)/
  `AdsSpendImportDecision` (M6.2Q **MC-09**) `to_public` echo free-text raw (the audit sinks are hardened —
  `scale_gate._audit_decision` does not echo — but the model exports are not); the untrimmed `event_code` split (M6.2S
  CRIT-04 → chief, RULE-001); and the carried trace-id / evidence-id export residuals (**F-EVID-4/5/6**, masked in
  evidence today) route with the M6-OD-012 export family. Unchanged by M6.2T (correctly scoped to input-side +
  gate-clear-path).
- **Carried (unaffected):** the F-SEC-2I-1 / M6.2Q N1 live_session provenance → owner; B1 real-pepper + privacy/legal →
  M6-OD-003; the ops-core + M3 credential handovers as `secret_ref` + import-gate allow-list → M6-OD-011 before wiring.

### 5.6 Owner decisions + immutable posture

- **DECIDED (authorizes this slice):** **M6-OD-019** (pre-wiring hardening — DECIDED 2026-09-10; artifact filed). All 4
  legs stricter/fail-closed-direction only; the gate is made to FAIL/HOLD more, never clear more.
- **Entry precondition satisfied:** `IMPLEMENTATION_TARGET_LOCKED.json = LOCKED`, M6-OD-011 decided-for-target (the
  staged-only target-gate) — so "M6-OD-011 open below" refers only to the forward credential-handover / import-gate /
  authN specifics at wiring, not the target lock, which was met at entry.
- **Hard forward gates (before any live wiring / real scale / egress):** **M6-OD-002 / M6-OD-005 must stay OPEN** — the
  leg-2 HOLD floor and the L1g containment both depend on them; **opening a PASS branch on `_funnel`/`_dashboard` arms
  L1g and must first close L1g + draw an independent validated read at approval** (the leg-2 regression will fail loudly
  to force this). **M6-OD-012** (export-side masking — the primary FAIL-008 control leg 3 does not replace) + extend leg
  3 to `updated_at`, **before** wiring the reader to any durable sink. **M6-OD-011** (ops-core/M3 credentials as
  `secret_ref` + import-gate allow-list + scale-decision endpoint authN at the S1b/server-bind wiring). **M6-OD-003**
  (permit-mapping/hash) OPEN. `M6-P1000` + `M6-P1309` remain **BLOCKED (not converted)**.
- **Posture (untouched):** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, both scale floors
  `False`, `live_migrations=false`; `config.py`/`consumed.py`/`validator.py` byte-identical to M6.2S. **Operator hygiene
  (non-blocking, carried):** register M6-OD-013/014 + the M5 `PSID_HASH_POLICY_M5_TMP` dependency in
  `DECISION_REGISTER.md`; reconcile the stale ENTRY-004 row.

---

## 6. Changelog delta — *acceptance check 2*

| Kind | Delta this slice introduced |
|---|---|
| **Gate logic (STAGED, edited — the notable delta)** | **the first gate-logic change since M6.2Q, stricter/fail-closed only:** `conditions._risk` (partial no-active → HOLD; NEW-PASS ⊂ OLD-PASS) + `scale_gate._assert_risk_clear_at_approval` (`isinstance(bool)` conjunct; NEW-clear ⊂ OLD-clear). No PASS/clear branch opened. The M6.2Q→R→S byte-identity streak is intentionally broken. |
| **Code (STAGED, edited)** | `registry_feed_reader.py` (leg-3 PII reject + N5/N6) and `recall_risk_mapper.py` (leg-4 N3/N9) — all fail-closed additions. |
| **Code (STAGED, new)** | 3 regression test files (leg-1 clear-path, leg-2 HOLD-floor lock, leg-3/4 residuals) = 13 cases. |
| **Test reconciliation** | `test_smk_030` non-vacuity control re-pointed to all-6→PASS + a new 3-of-6→HOLD assertion — a strengthening, not a nerf (the one carried test the leg-1 change touched). |
| **Reuse-only (unchanged)** | `config.py`/`consumed.py`/`validator.py` byte-identical to M6.2S (sha256-verified); migrations `0001–0016`; no new enum. |
| **Tests (staged)** | +13 coder cases + the official **SMK-032** (14 nodes = 10 functions). Suite **716 → 743** (729 coder baseline + 14 smoke). |
| **Contract / owner decisions** | contracts resolved-for-entry; **M6-OD-019** DECIDED (authorizes the slice); forward gates M6-OD-002/005 (must stay OPEN), M6-OD-012, M6-OD-011, M6-OD-003 carried. |
| **New capability** | the shared Scale-Gate clear-path + the staged recall/registry mechanism are **hardened stricter/fail-closed** ahead of wiring; the HOLD floor is pinned by a regression. |
| **Governance verdicts** | `M6-P1000` + `M6-P1309` **remain BLOCKED** (not converted). |
| **Posture** | unchanged — `BLOCKED / OFF / OFF`, both floors `False`. **No flag flip / wiring / live call / egress / PASS branch / certified behavior loosened / test nerfed.** |
| **Readiness** | assembled pack still `OWNER_REVIEW_REQUIRED`; this slice **hardens the staged mechanism** and declares no ROAS-Pass / Scale-Ready (owner-only). |

---

## 7. Handoff

**Exit-gate status (8 legs, per the slice done-gate — the full map is `M6_2T_EVIDENCE_INDEX.md`):**

| Exit leg | Status | Evidence |
|---|---|---|
| 1 — clear-path hardening (`_risk` all-6→PASS, partial→HOLD; `_assert` bool-ness; certified behavior preserved) | **MET** | SMK-032 leg-i + boundary N4 OLD→NEW truth table + security code-read + coder regression |
| 2 — HOLD-floor lock (`is_scale_authorized` structurally unreachable while M6-OD-002/005 OPEN) | **MET** | SMK-032 leg-ii + coder `test_m6_2t_hold_floor_lock.py` |
| 3 — input-side PII-shape reject (governance field → `feed_error`, state unchanged; not export masking) | **MET** | SMK-032 leg-iii ×3 + legit-code control |
| 4 — residuals (N3 base-key reject; N9 non-iterable block_reasons; N5/N6 enum guard + observability) | **MET** | SMK-032 leg-iv |
| 5 — SMK-032 executed or owner-waived | **MET** | executed 14/14, not waived |
| 6 — all slice prompts have evidence JSON | **PENDING** | M6-P2808 (this doc) + Judge M6-P2809 still to produce evidence |
| 7 — slice-gate judge sign-off PASS | **PENDING** | M6-P2809 to run (fresh session) |
| 8 — rollback documented for every change | **MET** | §4 + IMPLEMENTATION_NOTES §5 |

Legs 1–5 + 8 are MET; legs 6–7 are PENDING only because this docs prompt and the judge are the last two to run. None is FAILED/BLOCKED.

- **Immediate next (JUDGE, fresh session): M6-P2809 `M6_2T_SLICE_GATE_JUDGE`** — the **definitive** stricter-only /
  no-nerf / mapper+reader-unwired verdict: `_risk` NEW-PASS ⊂ OLD-PASS, `_assert` `isinstance(bool)` conjunct, the
  SMK-030 reconciliation a strengthening, no certified M6.2G behavior loosened, no test nerfed; the Scale GATE is WIRED
  (contained by the HOLD floor + RULE-H03) while the mapper + reader stay UNWIRED; no flag flip / no egress / posture
  OFF-BLOCKED-OFF. Judges never modify what they judge. See §8.
- **OWNER (before wiring / go-live):** **M6-OD-012** export-side masking is the **primary FAIL-008 control** (leg 3 is
  only input-side narrowing) + extend leg 3 to `updated_at`; mirror `isinstance(bool)` in `conditions._risk` (L1g);
  **keep M6-OD-002/005 OPEN** (the HOLD floor depends on them — opening a PASS branch arms L1g and must close it first);
  **M6-OD-011** ops-core/M3 credentials as `secret_ref` + import-gate allow-list + scale-decision authN.
- **CODER:** `_resolve_typed` block-not-flag (L4c); tighten/anchor the leg-3 over-broad regexes (L3d/N2).
- **CHIEF (RULE-001):** untrimmed `event_code` + tombstone semantics.
- **Posture carried forward unchanged:** `BLOCKED / OFF / OFF`, both floors `False`; `M6-P1000` + `M6-P1309` BLOCKED.

---

## 8. Pointers for the slice-gate Judge (M6-P2809)

1. **Read order:** `M6_2T_EVIDENCE_INDEX.md` → the 7 band JSONs (M6-P2800…2806) → the two review reports
   (`M6.2T_boundary.md` §2 the stricter-only DEFENDED set + §3 the OPEN_NONGATE residuals + §4 NOTES,
   `M6.2T_security.md` §4 leg-1 stricter-only + §5 leg-3 honest scope + §7 the wired-gate correction) → `SMOKE_RESULTS.md`
   (SMK-032 14/14) → `IMPLEMENTATION_NOTES.md` (**rollback §5**; the M6.2S→M6.2T stricter-only diff §2). The 8-leg
   exit-gate map is the index.
2. **What is proven (executed + boundary/security-verified on the actual source):** leg 1 is stricter-only —
   `conditions._risk` NEW-PASS ⊂ OLD-PASS, `scale_gate._assert` added `isinstance(bool)` (NEW-clear ⊂ OLD-clear),
   active-veto byte-identical; the SMK-030 reconciliation is a strengthening (proof preserved + a stricter assertion
   added), not a nerf; the leg-2 HOLD floor keeps `is_scale_authorized` structurally unreachable. Full suite **743
   passed**; SMK-032 14/14; boundary **0** in-scope breach / **0 LOOSENING** / 26 recorded; security **0** raw PII / **0**
   secrets (incl. **0** `client_secret`) / 285 files; `config.py`/`consumed.py`/`validator.py` byte-identical (verified),
   exactly the 4 hardening files edited.
3. **The three honesty points to weigh hardest (this is a gate change, not the green count):** **(1)** stricter-only is
   proven, not asserted, and the one carried test break was honestly reconciled (the plan red-team caught the coder's
   false "no test breaks" claim); **(2)** the reachability correction — the Scale GATE is **WIRED** (`app/api/
   scale_requests.py`), so the FAIL-006 containment is the **HOLD floor + RULE-H03**, not "unwired"; only the mapper +
   reader are unwired; **(3)** the legs close **most, not all** — L1g (`_risk` presence-only, not bool-ness), leg 3 is
   best-effort input narrowing not the primary FAIL-008 control (that is M6-OD-012 export-masking, deliberately not
   added), L4c `_resolve_typed` flag-not-block.
4. **What is NOT yet closed:** exit items **6 & 7** are PENDING only because this docs prompt (M6-P2808) and the judge
   (M6-P2809) are the last two to run. Legs 1–5 + 8 are MET. The slice **hardens the staged mechanism** and declares no
   ROAS-Pass / Scale-Ready — M6-OD-002/005 (must stay OPEN), M6-OD-012, M6-OD-011, M6-OD-003 stay OPEN.
5. **Confirm the posture:** no flag flip, no wiring, no live call, no egress, no PASS branch opened, no certified
   behavior loosened, no test nerfed; `config.py`/`consumed.py`/`validator.py` byte-identical, migrations `0001–0016`
   unchanged, `M6-P1000` + `M6-P1309` BLOCKED (not converted).
6. **Boundary integrity of this docs prompt (M6-P2808):** `analysis_only` — it read the band evidence and wrote only
   this runbook + its evidence JSON. It touched no `04-artifacts/state/`, marked no ledger row, modified no file it
   documents, opened no egress, computed no verdict, and declared no readiness. `global_gateway_state=BLOCKED`,
   `production_flag=OFF`, `external_send=OFF` — untouched; `M6-P1000` + `M6-P1309` remain BLOCKED (not converted).
