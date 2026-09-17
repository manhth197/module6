# M6.2U — Slice Runbook — Recall E2 §3 conformance (sellability veto + pull-error FAIL) + migration renumber + docstring (M6-OD-020)

> **Status: STAGED — a stricter/fail-closed recall conformance fix. It flips nothing, wires nothing, opens no PASS
> branch — but the new sellability veto is DEAD on every channel-reachable path today and is INVERTED by the module's
> own sanctioned helper, so "B3 closed + green" must NOT be read as "recall sellability is enforced."**
> M6.2U is the owner-authorized (M6-OD-020, DECIDED 2026-09-17) fix of three chief-auditor 2026-09-16 M6-self-doable
> findings: **B3** (recall E2 §3 conformance — a distinct `not_sellable` sellability veto + a pull-error→FAIL), **B1/B4**
> (migration renumber README), **D20** (psid_hash docstring). Cumulative superset of M6.2T. Leg 1 edits
> `conditions.py` + `recall_risk_mapper.py` **stricter/fail-closed only** (it ADDs FAIL conditions, opens no PASS branch,
> loosens nothing). `scale_gate.py` is **untouched this slice** (byte-identical to M6.2T), as are `config.py`,
> `consumed.py`, `validator.py`, and **all 16 migration SQL** (no `0017` SQL written) — independently sha256-verified.
>
> **Read the three honesty points first:**
> 1. **The new sellability veto is DEAD today and INVERTED by the sanctioned helper (N1/N6 — the sharpest finding of the
>    series).** The only producer of `not_sellable` is the **UNWIRED** mapper, so `conditions._risk`'s new
>    `not_sellable → FAIL` branch is **dead code on every channel-reachable input today** (N6). Worse, at wiring the veto
>    is honored on **only one narrow path** — a direct `read.risk_flags` feed — and is **dropped or inverted** through
>    `recall_risk_contribution`, the module's own helper whose docstring still says *"FAIL-CLOSED BY CONSTRUCTION — always
>    safe in every case"*: a NOT_SELLABLE-clean read merged with a complete base **drops `not_sellable` and returns a full
>    clean map → Risk PASS** — an affirmative clear of a NOT_SELLABLE lot (worse than HOLD); with no base → `{}` → HOLD.
>    So the E2 §3 veto is enforced on the path the tests use and **lost — or inverted — on the paths the codebase's own
>    API steers a caller toward.** **"B3 closed"** is true only as a *mechanism on a future direct-feed wiring*; it is not
>    live and not safe through the sanctioned helper. **N1 (propagate the veto through `recall_risk_contribution`) + A2
>    (mirror it at approval) + N3 (three carriers, one honored) must be hardened BEFORE the S1b wiring seam.**
> 2. **Stricter-only was verified EXHAUSTIVELY against the actual M6.2T source by the boundary + coder red-team
>    (PASS-eligible; the definitive verdict is the Judge's, M6-P2909), not asserted here.** An independent red-team
>    enumerated `conditions._risk` over **all 2187 combinations** of the 6 RISK_LOCKS + `not_sellable` (M6.2T vs M6.2U):
>    **0 inputs less strict, 0 new PASS, 64 strictly stricter** (63 HOLD→FAIL + the 1 full-6-no-active-but-`not_sellable`
>    PASS→FAIL — the veto correctly overriding a would-be-clear). `not_sellable` is **not** a RISK_LOCK, so the all-6
>    completeness, `active_risk_locks`, and every non-mapper scale context are unchanged; the certified clear-path
>    (SELLABLE + all-6 → PASS) is preserved; and **ops-core §4 / RULE-018 holds** — the recall booleans stay
>    presence-derived, never from `decision`. The **17 reconciled mapper tests are strengthenings**, including the honest
>    rename `test_mapper_never_reads_decision → …_never_derives_recall_booleans_from_decision` (the mapper now DOES read
>    `decision`, only for the veto, so the old name was a false claim).
> 3. **A governance-conformance slice: M6-OD-020 supersedes M6-OD-017's "never read decision" clause ONLY; the migration
>    + docstring legs are documentation-only.** The mapper now reads `decision` for the sellability veto but **not** for
>    deriving the recall booleans (ops-core §4 in force). The migration change is **README-only** — no `0017` SQL, all 16
>    SQL byte-identical; it renumbers the (unwritten) enforcement migration `0014 → 0017` (`0014–0016` are the M6.2Q
>    ads-spend tables). And it **resolves the M6.2R/M6.2S traceability note**: SMK-030(iii)'s register Expected always
>    read "pull error → gate FAIL", but M6.2R under-implemented it as HOLD — M6-OD-020's veto now makes it FAIL,
>    conforming the smoke to its own quoted Expected.
>
> Posture immutable: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, both scale floors
> `False`, `live_migrations=false`. `M6-P1000` + `M6-P1309` remain **BLOCKED (not converted)**; the pack still tops at
> `OWNER_REVIEW_REQUIRED`. Evidence: full staged suite **768 passed / 0 failed, rc 0**; SMK-033 PASS 14/14; boundary
> **23 outcomes = 16 DEFENDED / 5 OPEN_NONGATE / 2 NOTE / 0 in-scope FAIL-006 breach / 0 LOOSENING**; security **0** raw
> PII / **0** secrets / 287 files. Next: slice-gate Judge **M6-P2909** (the definitive stricter-only / no-nerf / unwired
> verdict).

| Field | Value |
|---|---|
| Slice | **M6.2U** — Recall E2 §3 conformance + migration renumber + docstring; post-pilot; depends on M6.2T; chief-auditor 2026-09-16 items B3 + B1/B4 + D20; ops-core account live (pin `54eb5f5`) |
| Prompt (this doc) | **M6-P2908** — `M6_2U_DOCS` (ANALYST_ARCHITECT, `analysis_only`, EVIDENCE_GATE) |
| Rules / fail gate in scope | **RULE-017** (risk hard veto) · **RULE-018** (invent no lock/decision) · **RULE-015** (no self-cert) · **FAIL-006** (auto scale/publish). *(FAIL-008 not in scope this slice; the carried export family is M6-OD-012 forward context.)* |
| Smoke in scope | **M6-SMK-033** (sellability no-scale veto + pull-error FAIL) — proposed HARDENING, **executed 14/14** (not owner-waived) |
| Contract | M6-CTR-026 → resolved-for-entry (per the M6.2R/M6.2T harmonization chain) |
| Owner inputs (DECIDED) | **M6-OD-020** (recall E2 §3 conformance — DECIDED 2026-09-17; artifact filed; **supersedes M6-OD-017's decision-exclusion clause ONLY**) |

---

## 1. What this slice built (staged under `04-artifacts/impl/M6.2U/`)

M6.2U carries the **entire M6.2T tree byte-identical** (baseline verified green **before any patch: 743 passed**) and
makes **3 legs = 7 changed files + 2 new test files** (full-slice surface `2 new + 7 changed`, byte-hash compared).
**No migration SQL written** (all 16 SQL byte-identical, no `0017`), **no config change**, **no new enum**, **no
wiring**. The **untouched set is byte-identical to M6.2T** (independently sha256-verified this turn: `config.py`=`911b3238…`,
`scale_gate.py`, `consumed.py`, `validator.py`, all 16 migration SQL); the **edited set differs** (verified this turn).

| Leg | Change (stricter/fail-closed or docs) | File |
|---|---|---|
| **1 — B3 sellability veto (M6-OD-020)** | after the active-lock FAIL and **before** the M6.2T all-6 completeness/PASS, added `if ctx.risk_flags.get("not_sellable"): return FAIL`. `not_sellable` is **not** a RISK_LOCK, so `active_risk_locks`, the all-6 check, and every non-mapper scale context are unchanged. Only an added FAIL — **NEW severity ≥ OLD, no PASS branch**. | **edited** `app/measurement/scale/conditions.py` |
| **1 — B3 mapper read** | `map_risk_flags` reads `decision` **once**: `sellable = (decision == "SELLABLE")`; a non-SELLABLE decision adds `not_sellable=True` (a SELLABLE read adds no key → exact-3-key output). The 3 recall booleans stay **presence-derived, byte-identical** (ops-core §4, never from `decision`). `_incomplete` (pull-error/timeout/429/absent/malformed) now returns `{"not_sellable": True}`, `complete=False`, `unverified=True` (was `{}`→HOLD — **stricter**). `RecallRiskRead` gained `sellable`/`unverified`. | **edited** `app/measurement/scale/recall_risk_mapper.py` |
| **1 — deliberately UNCHANGED** | `recall_risk_contribution` is **byte-identical to M6.2T** by design — per the plan red-team the veto must NOT propagate through it (it copies only the 3 `RECALL_RISK_KEYS`; propagating `not_sellable` would pollute the 6-lock completeness and mis-route the veto to `{}`→HOLD). **This is exactly why N1 exists (§5.1).** | *(within the edited mapper file)* |
| **1 — test reconciliation** | the 17 carried mapper tests that feed `read.risk_flags` directly were reconciled as **strengthenings** (RULE A: add `decision="SELLABLE"` to isolate the boolean tests; RULE B: `{}`/HOLD → `{"not_sellable":True}`/FAIL; the honest rename `never_reads_decision → never_derives_recall_booleans_from_decision`). No assertion deleted/skipped; count unchanged. | **edited** 2 mapper test files (incl. `test_smk_030`) |
| **2 — B1/B4 migration renumber (docs-only)** | `migrations/README.md` was stale (listed only `0001–0005`); rewritten to `0001–0016` (descriptions from each SQL header, not invented) + a note that the enforcement migration is **`0017`** (renumbered from the taken `0014`; `0014–0016` are M6.2Q ads-spend), **authored at server-bind — no SQL written**. | **edited** `migrations/README.md` |
| **3 — D20 psid_hash docstring (docs-only)** | `attribution_context.as_stored` docstring corrected "Trace joins use `psid_hash`" → the **M6-OD-015 no-join** policy (`psid_hash` is within-row provenance, not a cross-module join key; correlation uses `live_session_id`/`comment_id`/`messenger_thread_id` + `attribution_id`). **Code byte-identical** (no join ever existed). | **edited** `app/measurement/models/attribution_context.py` |
| **coder + tester tests** | leg-1 regression (11 cases) + the official SMK-033 smoke. | **new** `tests/test_m6_2u_recall_e2_conformance.py`, `tests/smoke/test_smk_033_recall_e2_conformance.py` |

---

## 2. Operate

M6.2U conforms the recall path's fail-closed direction; there is no new surface, no wiring, no egress. What the change
does at runtime:

1. **Recall mapper (still UNWIRED).** `map_risk_flags` derives the 3 recall booleans from presence booleans only, and
   separately sets `not_sellable=True` when `decision != "SELLABLE"`; `_incomplete` returns `{"not_sellable": True}` +
   `unverified=True` on any pull error. `RecallRiskRead` exposes `risk_flags['not_sellable']`, `sellable`, and
   `unverified`.
2. **Scale-Gate `_risk` (the WIRED gate).** On a `not_sellable` map, `_risk` returns FAIL (after the active-lock FAIL,
   before completeness). On any map without `not_sellable`, `_risk` is byte-identical to M6.2T. `ScaleContext.risk_flags`
   is **server-assembled (RULE-H03)** — the untrusted admin body cannot inject it.
3. **The veto's reach (the load-bearing caveat).** The veto reaches `_risk` **only** when the read's `risk_flags` is fed
   directly (as the tests + regression do). Through `recall_risk_contribution` it is dropped (→HOLD) or **inverted**
   (→ affirmative PASS with a complete base). And `_assert_risk_clear_at_approval` (byte-identical to M6.2T) ignores
   `not_sellable` entirely (A2). See §5.1.
4. **HOLD floor unchanged.** `is_scale_authorized` stays structurally unreachable while M6-OD-002/005 are OPEN (the veto
   only makes overall *worse*); the containment of the N1 inversion today is the HOLD floor + the mapper being unwired.
5. **What stays impossible:** live wiring, a live ops-core pull, external send, a flag flip, a PASS branch, a migration
   apply, an event write/invent/reconcile. `scale_gate.py`/`config.py`/`consumed.py`/`validator.py` + 16 SQL
   byte-identical to M6.2T.

---

## 3. Verify

### 3.1 The official smoke (SMK-033 PASS 14/14, executed not waived; masked `correlation_id`+`evidence_id`)

14 nodes across 8 functions (`scenario_ii` ×3, `scenario_iii` ×5):
- scenario i — decision=NOT_SELLABLE + all flags false → a COMPLETE read whose recall booleans are all False (not
  derived from decision) and whose distinct veto sets `not_sellable=True`; merged onto an otherwise-clearing full-6
  no-active picture, Risk row **FAIL** (sellability no-scale).
- scenario ii ×3 (UNKNOWN / wrong-case `sellable` / None) — a decision not exactly `SELLABLE` → `not_sellable=True` →
  Risk **FAIL**; recall booleans stay False.
- scenario iii ×5 (HTTP_429 / TIMEOUT / CONNECTION_ERROR / None / malformed) — an incomplete read is UNVERIFIED →
  `complete=False`, `unverified=True`, `risk_flags == {"not_sellable": True}` → Risk **FAIL** (not HOLD) + the
  running-campaign 'unverified' signal.
- not-derived control — a present recall lock FAILs even under SELLABLE (recall from the presence boolean); a clean lot
  with NOT_SELLABLE keeps recall False (decision fabricates no recall boolean) while setting the veto.
- clear-path control (non-vacuous) — SELLABLE + no-active + COMPLETE all-6 → Risk **PASS**; a partial SELLABLE 3-of-6 →
  HOLD (M6.2T completeness unchanged).
- distinctness — `not_sellable ∉ RISK_LOCKS / RECALL_RISK_KEYS`. unwired — no app runtime module imports the mapper.
  posture — `EXTERNAL_SEND/PRODUCTION_FLAG/GLOBAL_GATEWAY_STATE` = OFF/OFF/BLOCKED.

### 3.2 Full staged suite (count discipline)

```
# from 04-artifacts/impl/M6.2U/  (venv: 02-tester/.venv, python 3.12.14, pytest 8.4.2; -B, cache-free, no shell redirection)
python -B -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider'])>"   # -> RC 0 ; 768 passed / 0 failed
python -B -c "<tally; pytest.main(['-k','test_smk_033','-p','no:cacheprovider'])>"          # -> RC 0 ; 14 passed
```

**Reconciliation: 768 (tester-run final) = 743 carried (M6.2T SIGNED) + 11 coder M6.2U regression cases (→ 754 coder
baseline) + 14 official-smoke nodes (SMK-033 = 8 functions).** Coder baseline before any patch was 743 (byte-parity;
743 is the M6.2T **SIGNED** count — M6.2T grew from its 729 implement-time count to 743 via its TESTER's later official
smokes, so 743 not 729 is the correct carry baseline);
the invariant `baseline ≤ coder ≤ final (743 ≤ 754 ≤ 768)` holds; **the 17 reconciled tests changed assertions/names,
not the count — 0 skip, 0 xfail, 0 deletion**; the isolated `-k` run independently confirms 14 passed; the build-side
collect-only count (M6-P2903) was also 768. *(pytest's terminal summary is unreliable here, so totals came from an
in-process `pytest_runtest_logreport` tally with `pytest.main() RC=0` — see SMOKE_RESULTS.md "On counting".)*

### 3.3 The in-scope gate — stricter-only verified exhaustively by the reviews (boundary + coder red-team + security; PASS-eligible, Judge M6-P2909 definitive), FAIL-006 not tripped, 0 loosening

- **Boundary (M6-P2905): 23 outcomes = 16 DEFENDED / 5 OPEN_NONGATE / 2 NOTE / 0 in-scope FAIL-006 breach / 0
  LOOSENING.** Stricter-only verified against the actual M6.2T source (S1): `_risk` gains ONLY the `not_sellable → FAIL`
  branch; the active veto + completeness + PASS are byte-identical; the certified clear-path (SELLABLE + all-6 → PASS)
  and ops-core §4 (recall from presence, not decision) preserved. HOLD floor unchanged (crown jewel).
- **Exhaustive stricter-only proof (coder red-team, corroborated by boundary S1 + security §4):** `_risk` enumerated
  over all **2187** combinations of the 6 RISK_LOCKS + `not_sellable`, M6.2T vs M6.2U — **0 less strict, 0 new PASS, 64
  strictly stricter** (63 HOLD→FAIL, 1 PASS→FAIL). The veto is airtight on its direct channel across every decision
  variant (casing/whitespace/non-str/None; value-object + dict paths).
- **Security (M6-P2906): 0 raw PII / 0 real secrets / 287 files** (canonical `0/0/0/0/0`; all non-canonical hits
  carried from M6.2O, benign). RULE-018-clean: reading `decision` for a FAIL-direction veto **consumes** ops-core's
  signal; M6 invents no lock/decision. Leg 3 is a security-positive psid-no-join doc fix.
- **On-disk byte-identity (independently verified this turn):** `config.py`/`scale_gate.py`/`consumed.py`/`validator.py`
  + all 16 migration SQL byte-identical T↔U; `conditions.py`/`recall_risk_mapper.py`/`attribution_context.py`/
  `migrations/README.md`/`TEST_MANIFEST.md` differ; no `0017` SQL; tree delta +2 .py (1 coder + 1 tester smoke).

---

## 4. Rollback (every change this slice made) — *acceptance check 1*

Staged-only and non-destructive: nothing live, no migration applied (`live_migrations=false`), no flag flipped, no
egress, no wiring. Every edit is a fail-closed *tightening* or a docs correction, so a scoped revert restores the prior
M6.2T behaviour.

| Change | Rollback |
|---|---|
| **Whole slice** | delete the `04-artifacts/impl/M6.2U/` tree — M6.2T is byte-identical and untouched; no live migration to unwind |
| **Edited gate — `conditions.py` `_risk` (leg 1)** | **scoped revert** the `not_sellable → FAIL` branch to M6.2T bytes |
| **Edited mapper — `recall_risk_mapper.py` (leg 1)** | **scoped revert** the `decision`-read veto + the `_incomplete` `{"not_sellable":True}`/`unverified` change to M6.2T bytes (`recall_risk_contribution` is already byte-identical — nothing to revert there) |
| **Edited docstring — `attribution_context.py` (leg 3)** | **scoped revert** the `as_stored` docstring to M6.2T bytes (code already byte-identical) |
| **Edited docs — `migrations/README.md` (leg 2)** | **scoped revert** to M6.2T bytes (the stale `0001–0005` listing) — no SQL to unwind |
| **Edited tests — the 2 reconciled mapper test files (incl. `test_smk_030`)** | **scoped revert** the reconciled assertions/renames to M6.2T bytes |
| **New tests** — `tests/test_m6_2u_recall_e2_conformance.py`, `tests/smoke/test_smk_033_recall_e2_conformance.py` (+ `tests/TEST_MANIFEST.md` delta) | delete the files / revert the manifest delta |
| **Untouched set** — `config.py`/`scale_gate.py`/`consumed.py`/`validator.py`/all 16 migration SQL | **none** — byte-identical to M6.2T (each sha256-verified) |
| **Migration SQL / config flag / new enum** | **none** — no `0017` SQL written, `config.py` byte-identical, no new enum |
| **Boundary / security / tester / PM / docs analysis-only + evidence writes** (`M6.2U_boundary.md`, `M6.2U_security.md`, harness/scanner scripts under `work/`; `test-reports/M6.2U/SMOKE_RESULTS.md`; `evidence/prompts/M6_2U_EVIDENCE_INDEX.md` + band `M6-P2900…2908.json`; this `analysis/slices/M6_2U_RUNBOOK.md` + `M6-P2908.json`) | delete / revert — all analysis-only or evidence-collection writes; none modified any source, gate, migration, or `04-artifacts/state/` |

---

## 5. Decision deltas & governance

### 5.1 Honesty point 1 — the sellability veto is dead today and inverted by the sanctioned helper (N1/N6, highest priority before S1b)

The B3 closure is real **as a mechanism on a direct feed**, but two facts must be foregrounded so "green" is not misread:
- **N6 (dead on the wired path):** the only producer of `not_sellable` is the **unwired** mapper (no `app/**` module
  imports it), so `conditions._risk`'s new branch has **zero behavioral effect on any channel-reachable input today** —
  the same adapter-built-ahead-of-wiring pattern as M6.2R/M6.2S/M6.2T; the sign-off must not over-attribute a live
  effect to it.
- **N1 (inverted by the sanctioned helper — the sharpest finding):** the same NOT_SELLABLE-clean read fed three ways:
  (A) direct `read.risk_flags` → **FAIL** (works); (B) `recall_risk_contribution` + a complete base → drops
  `not_sellable`, returns the full clean map → **Risk PASS** (an affirmative clear of a NOT_SELLABLE lot — worse than
  HOLD); (C) helper + no base → `{}` → **HOLD**. The helper's docstring still reads *"FAIL-CLOSED BY CONSTRUCTION —
  always safe in every case."* This is **by design and byte-identical to M6.2T** (propagating `not_sellable` through the
  helper would pollute the 6-lock completeness) — but it means the E2 §3 veto is enforced on the one path the tests use
  and **lost or inverted on the path the codebase's own API steers a caller toward**.
- **Compounding gaps:** `_assert_risk_clear_at_approval` (byte-identical to M6.2T) ignores `not_sellable` (A2 — a fresh
  NOT_SELLABLE at approval clears the risk re-check via the all-6 path); and three carriers expose the signal
  (`risk_flags['not_sellable']`, `read.sellable`, `read.unverified`) while the gate reads only `ctx.risk_flags` — an
  integrator keying off `sellable`/`unverified` silently drops it (N3).
- **The approval-side defense is single-point today.** The refusal of a `not_sellable` lot rests **entirely on the
  propose-time overall-FAIL coupling** (A1: a `not_sellable` propose → Risk FAIL → overall FAIL → APPROVE refused),
  **not** on `_assert_risk_clear_at_approval` (which ignores `not_sellable`, A2). So at any future wiring that routes the
  read through `recall_risk_contribution`, **N1-B (helper → Risk PASS, overall HOLD) + A2 compound**, and the only
  remaining protection is the structurally-unreachable `is_scale_authorized` — a single-point defense. This is why **A2
  must land alongside N1** before S1b, not after it.

**Contained today** by: the mapper is unwired (N6), overall is capped at the HOLD floor (`is_scale_authorized`
structurally unreachable), and this is **not a loosening** vs M6.2T (M6.2T also PASSed this all-6-clean input — it had
no `not_sellable` at all). **Route (owner/CODER, highest priority before the S1b wiring seam):** make the veto two-deep
— propagate `not_sellable` through `recall_risk_contribution` (N1) + mirror it in `_assert_risk_clear_at_approval` (A2)
+ map `sellable`/`unverified` into `risk_flags` or a typed gate field (N3); and feed the read's `risk_flags` directly,
not through the helper.

### 5.2 Honesty point 2 — stricter-only was proven exhaustively by the reviews (Judge M6-P2909 definitive), and no test nerfed

The worst outcome for a gate-direction change is a loosening or a nerfed test; both are refuted **on the actual source**
by the boundary (S1, OLD→NEW vs the real M6.2T) + the coder red-team's exhaustive **2187-combination** enumeration
(0 less strict, 0 new PASS, 64 strictly stricter) + the security line-level code-read (§4) — all PASS-eligible; the
definitive verdict is M6-P2909's. `not_sellable` is not a RISK_LOCK (`active_risk_locks` / all-6 completeness /
non-mapper contexts unchanged; a present `not_sellable=False` behaves as key-absent → PASS, no false-value bypass). The
certified clear-path (SELLABLE + all-6 → PASS) is preserved; ops-core §4 / RULE-018 holds (recall booleans
presence-derived, decision consumed only for the veto). The **17 reconciled tests are strengthenings**, and the honest
rename `never_reads_decision → never_derives_recall_booleans_from_decision` records truthfully that the mapper now reads
`decision` (only for the veto).

### 5.3 Honesty point 3 — a governance-conformance slice: M6-OD-020 supersedes M6-OD-017's decision-exclusion clause only

- **M6-OD-020 supersedes M6-OD-017's "never read decision" clause ONLY** — a legitimate owner conformance to the chief
  E2 canonical. The recall-boolean mapping (presence-derived, never from decision — ops-core §4) **stays in force**; the
  supersession authorizes reading `decision` **solely** for the distinct sellability veto. This is the first
  owner-decision supersession in the slice series and must be read narrowly: M6-OD-017 is not voided, only its
  decision-exclusion clause.
- **The migration change is README-only + a latent-conformance fix.** No `0017` SQL; all 16 SQL byte-identical; the
  README (was stale at `0001–0005`) now lists `0001–0016` + the `0017` enforcement note (renumbered from the taken
  `0014`). The registers (`M6-OD-011.json` / `DECISION_REGISTER` / `SCHEMA_CHANGELOG`) were already corrected to `0017`;
  this brings the README into line.
- **It resolves the M6.2R/M6.2S traceability note.** SMK-030(iii)'s register Expected always read "pull error → gate
  FAIL"; M6.2R under-implemented it as HOLD (which I flagged in the M6.2R/M6.2S runbooks as a register-wording nit).
  M6-OD-020's pull-error→FAIL brings the smoke into conformance with its own quoted Expected — the nit is now closed by
  behavior, not just noted.

### 5.4 What is genuinely good (credited, not rosy)

- The `_risk` change is exhaustively (2187-combo) verified stricter-only by the red-team — a rigorous, not asserted,
  check (the definitive verdict remains M6-P2909's).
- The pull-error→FAIL brings the recall path into conformance with the register's own long-standing Expected (§5.3).
- Leg 3 is security-positive: it reduces the risk of a future dev implementing a cross-module `psid_hash` join, aligning
  the doc with the owner's M6-OD-015 no-join decision. Leg 2 corrects a genuinely stale README from real SQL headers.
- The test reconciliation is honest — the rename admits the mapper now reads `decision`, rather than hiding it.
- `recall_risk_contribution` being left byte-identical is a deliberate, defensible choice (avoids polluting the 6-lock
  completeness) — but it is exactly why the veto must be propagated another way before wiring (§5.1).

### 5.5 Residuals (armed-not-fired; none trips FAIL-006; 0 loosening)

- **N1 (owner/CODER — highest priority before S1b):** `recall_risk_contribution` drops/inverts the `not_sellable` veto;
  propagate it (or feed `read.risk_flags`/`sellable`/`unverified` directly). §5.1.
- **A2 (owner/CODER):** mirror the `not_sellable` check in `scale_gate._assert_risk_clear_at_approval` for propose/approve
  parity. §5.1.
- **N3 (owner/CODER):** three veto carriers, one honored — at wiring, map `sellable`/`unverified` into
  `risk_flags['not_sellable']` (or a typed gate field). §5.1.
- **N5 (CODER):** `decision == "SELLABLE"` dispatches to the operand's `__eq__` — a hostile str-subclass could read
  NOT_SELLABLE as sellable; use `type(decision) is str and …`. In-process only (a wire feed yields a plain str).
- **N2 (CODER, contract-clarity):** the base-vs-read veto-placement split (`base_flags` carrying `not_sellable=True`
  survives to FAIL — the *sole* helper route that honors the veto — while a `read`-placed key is dropped) is fragile and
  undocumented; document/normalize it.
- **M6.2U-introduced stale in-file comments (docs-pass, behavior-neutral):** the `OpsCoreAvailabilityResponse` class
  docstring (~line 60) + the `decision` field comment (~line 69) still say "decision NEVER read" while the veto at
  ~line 153 reads it — surfaced for a docs pass (verified against source; no behavior change).
- **Pre-existing stale M6.2T mapper docstrings (out of M6-OD-020 scope):** the mapper module + `risk_picture_complete`
  docstrings still describe `_risk` as "reads any non-empty no-active map as PASS" — a limitation M6.2T's all-6
  hardening already closed; stale in the **conservative** direction (understates safety); the authoritative source
  (`conditions.py`) is correct. Surfaced, not fixed (spans docstrings beyond this scope).
- **Carried export family (S3 → M6-OD-012, the primary FAIL-008 control):** `OwnerDecision`/`AdsSpendImportDecision`/
  `RegistryFeedRow` `to_public` echo free-text raw (audit sinks hardened, model exports not); untrimmed `event_code`
  (→ CHIEF, RULE-001); trace-id / F-EVID-4/5/6; F-SEC-2I-1 live_session provenance (→ owner). Unchanged this slice
  (FAIL-008 not in scope here).

### 5.6 Owner decisions + immutable posture

- **DECIDED (authorizes this slice):** **M6-OD-020** (recall E2 §3 conformance — DECIDED 2026-09-17; artifact filed;
  supersedes M6-OD-017's decision-exclusion clause only). Leg 1 stricter/fail-closed only.
- **Entry precondition satisfied:** `IMPLEMENTATION_TARGET_LOCKED.json = LOCKED`, M6-OD-011 decided-for-target — so
  "M6-OD-011 open forward" refers to the credential-handover / import-gate / `0017`-SQL / authN specifics at wiring, not
  the target lock.
- **Hard forward gates (before any live wiring / real scale / egress):** **N1 + A2 + N3 (make the veto two-deep) must
  land before the S1b wiring seam** or the sellability veto silently won't fire (or will invert). **M6-OD-002/005 must
  stay OPEN** (the HOLD floor that contains N1's inversion depends on them). **M6-OD-012** (export-side masking — the
  primary FAIL-008 control for the carried decision/metadata export). **M6-OD-011** (ops-core/M3 credentials as
  `secret_ref` + import-gate allow-list + the `0017` enforcement SQL + scale-decision authN at server-bind).
  **M6-OD-003** (permit-mapping / hash / real pepper) OPEN. `M6-P1000` + `M6-P1309` remain **BLOCKED (not converted)**.
- **Posture (untouched):** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, both scale floors
  `False`, `live_migrations=false`. **Operator hygiene (non-blocking, carried):** register M6-OD-013/014 + the M5
  `PSID_HASH_POLICY_M5_TMP` dependency in `DECISION_REGISTER.md`; reconcile the stale ENTRY-004 row.

---

## 6. Changelog delta — *acceptance check 2*

| Kind | Delta this slice introduced |
|---|---|
| **Gate logic (STAGED, edited — stricter/fail-closed)** | `conditions._risk` gains a `not_sellable → FAIL` branch (after the active veto, before completeness; `not_sellable` not a RISK_LOCK). NEW severity ≥ OLD, no PASS branch. Exhaustively proven stricter-only (2187 combos). |
| **Code (STAGED, edited)** | `recall_risk_mapper.py` — `decision` read once for the veto (recall booleans still presence-derived); `_incomplete` → `{"not_sellable":True}`/`unverified` (was `{}`→HOLD). `recall_risk_contribution` **deliberately byte-identical** (→ N1). |
| **Docs (STAGED, edited)** | `migrations/README.md` renumber (README-only, no `0017` SQL, all 16 SQL byte-identical); `attribution_context.as_stored` docstring → M6-OD-015 no-join (code byte-identical). |
| **Test reconciliation** | 17 carried mapper tests reconciled as strengthenings ({}/HOLD → not_sellable/FAIL; the honest rename); no assertion deleted, count unchanged. |
| **Untouched (unchanged)** | `config.py`/`scale_gate.py`/`consumed.py`/`validator.py` + all 16 migration SQL byte-identical to M6.2T (sha256-verified); no new enum; no `0017` SQL. |
| **Tests (staged)** | +11 coder cases + the official **SMK-033** (14 nodes = 8 functions). Suite **743 → 768** (754 coder baseline + 14 smoke). |
| **Owner decisions** | **M6-OD-020** DECIDED (authorizes the slice; **supersedes M6-OD-017's decision-exclusion clause only**); forward gates N1/A2/N3, M6-OD-002/005 (stay OPEN), M6-OD-012, M6-OD-011, M6-OD-003 carried. |
| **New capability** | the recall path now conforms to E2 §3 (a distinct sellability veto + pull-error→FAIL) **as a staged mechanism on a direct feed** — dead on wired paths today, inverted through the sanctioned helper (N1). |
| **Governance verdicts** | `M6-P1000` + `M6-P1309` **remain BLOCKED** (not converted). |
| **Posture** | unchanged — `BLOCKED / OFF / OFF`, both floors `False`. **No flag flip / wiring / live call / egress / PASS branch / migration apply / certified clear-path loosened / test nerfed.** |
| **Readiness** | assembled pack still `OWNER_REVIEW_REQUIRED`; this slice conforms the recall path + fixes docs and declares no ROAS-Pass / Scale-Ready (owner-only). |

---

## 7. Handoff

**Exit-gate status (7 legs, per the slice done-gate — the full map is `M6_2U_EVIDENCE_INDEX.md`):**

| Exit leg | Status | Evidence |
|---|---|---|
| 1 — B3 recall E2 §3 conformance (NOT_SELLABLE/unknown/pull-error → Risk FAIL; distinct from recall booleans; clear-path preserved; no nerf) | **MET** | SMK-033 i/ii/iii + not-derived + clear-path controls + boundary S1 + 2187-combo proof + coder regression |
| 2 — B1/B4 migration renumber README (no SQL) | **MET** | `migrations/README.md` (0001–0016 + 0017 note); all 16 SQL byte-identical |
| 3 — D20 psid_hash docstring → M6-OD-015 no-join (code unchanged) | **MET** | `attribution_context.as_stored` docstring; code byte-identical |
| 4 — SMK-033 executed or owner-waived | **MET** | executed 14/14, not waived |
| 5 — all slice prompts have evidence JSON | **PENDING** | M6-P2908 (this doc) + Judge M6-P2909 still to produce evidence |
| 6 — slice-gate judge sign-off PASS | **PENDING** | M6-P2909 to run (fresh session) |
| 7 — rollback documented for every change | **MET** | §4 + IMPLEMENTATION_NOTES 'Rollback' |

Legs 1–4 + 7 are MET; legs 5–6 are PENDING only because this docs prompt and the judge are the last two to run. None is FAILED/BLOCKED.

- **Immediate next (JUDGE, fresh session): M6-P2909 `M6_2U_SLICE_GATE_JUDGE`** — the **definitive** stricter-only /
  no-nerf / mapper-unwired verdict: `conditions._risk` adds only `not_sellable → FAIL` (not a RISK_LOCK, NEW severity ≥
  OLD), the recall booleans still presence-derived (ops-core §4 / RULE-018), the certified clear-path (SELLABLE + all-6 →
  PASS) preserved, the 17 reconciliations strengthenings, the mapper UNWIRED,
  `scale_gate.py`/`config.py`/`consumed.py`/`validator.py` + 16 SQL byte-identical (no `0017` SQL), no flag flip / no
  egress / posture OFF-BLOCKED-OFF. Judges never modify what they judge. See §8.
- **OWNER/CODER (BEFORE the S1b wiring seam — highest priority):** propagate the `not_sellable` veto through
  `recall_risk_contribution` (N1 — today dropped→HOLD or inverted→PASS through the "always safe" helper) + mirror it at
  approval (A2) + map `sellable`/`unverified` into `risk_flags` (N3); `type()`-guard the SELLABLE compare (N5);
  document/normalize the base-vs-read placement split (N2).
- **OWNER:** **M6-OD-012** export-side masking (the primary FAIL-008 control for the carried decision/metadata export);
  **keep M6-OD-002/005 OPEN** (the HOLD floor that contains N1's inversion depends on them); **M6-OD-011** ops-core/M3
  credentials as `secret_ref` + import-gate allow-list + the `0017` enforcement SQL + authN at wiring; **M6-OD-003**.
- **CHIEF (RULE-001):** untrimmed `event_code` + tombstone semantics. A docs pass for the M6.2U-introduced + carried
  M6.2T stale mapper docstrings (behavior-neutral, conservative-direction).
- **Posture carried forward unchanged:** `BLOCKED / OFF / OFF`, both floors `False`; `M6-P1000` + `M6-P1309` BLOCKED.

---

## 8. Pointers for the slice-gate Judge (M6-P2909)

1. **Read order:** `M6_2U_EVIDENCE_INDEX.md` → the 7 band JSONs (M6-P2900…2906) → the two review reports
   (`M6.2U_boundary.md` §2 the stricter-only DEFENDED set + §3 the N1/A2/N3/N5 residuals + §4 the N6 dead-code framing,
   `M6.2U_security.md` §4 leg-1 stricter-only + RULE-018 + §7 N1/N6 + §5 leg-3) → `SMOKE_RESULTS.md` (SMK-033 14/14) →
   `IMPLEMENTATION_NOTES.md` (**Rollback** section; the 2187-combo proof; the `recall_risk_contribution` forward note).
   The 7-leg exit-gate map is the index.
2. **What is proven (executed + boundary/security-verified on the actual source):** leg 1 is stricter-only —
   `conditions._risk` gains only `not_sellable → FAIL`, `not_sellable` not a RISK_LOCK, NEW severity ≥ OLD over all 2187
   combinations (0 less strict, 0 new PASS, 64 stricter); the recall booleans stay presence-derived (ops-core §4 /
   RULE-018); the certified clear-path preserved; the 17 reconciliations strengthenings not nerfs. Full suite **768
   passed**; SMK-033 14/14; boundary **0** in-scope breach / **0 LOOSENING** / 23 recorded; security **0** raw PII / **0**
   secrets / 287 files; `scale_gate.py`/`config.py`/`consumed.py`/`validator.py` + 16 SQL byte-identical (verified).
3. **The three honesty points to weigh hardest (not the green count):** **(1)** the veto is **dead on wired paths today**
   (mapper unwired, N6) and **inverted to an affirmative PASS through `recall_risk_contribution`** (N1, the sharpest) —
   "B3 closed" is a direct-feed mechanism, not live enforcement; make it two-deep (N1+A2+N3) before S1b; **(2)**
   stricter-only was proven exhaustively by the reviews (definitive verdict is yours), no test nerfed; **(3)** M6-OD-020
   supersedes M6-OD-017's decision-exclusion clause **only** (recall booleans still presence-derived), and the migration
   leg is README-only (no `0017` SQL) — resolving the SMK-030(iii) register/HOLD traceability nit.
4. **What is NOT yet closed:** exit items **5 & 6** are PENDING only because this docs prompt (M6-P2908) and the judge
   (M6-P2909) are the last two to run. Legs 1–4 + 7 are MET. The slice **conforms the recall path as a staged mechanism**
   and declares no ROAS-Pass / Scale-Ready — N1/A2/N3, M6-OD-002/005 (stay OPEN), M6-OD-012, M6-OD-011, M6-OD-003 stay
   OPEN.
5. **Confirm the posture:** no flag flip, no wiring, no live call, no egress, no PASS branch opened, no migration apply,
   no certified clear-path loosened, no test nerfed; `scale_gate.py`/`config.py`/`consumed.py`/`validator.py` + 16 SQL
   byte-identical, no `0017` SQL, `M6-P1000` + `M6-P1309` BLOCKED (not converted).
6. **Boundary integrity of this docs prompt (M6-P2908):** `analysis_only` — it read the band evidence and wrote only
   this runbook + its evidence JSON. It touched no `04-artifacts/state/`, marked no ledger row, modified no file it
   documents, opened no egress, computed no verdict, and declared no readiness. `global_gateway_state=BLOCKED`,
   `production_flag=OFF`, `external_send=OFF` — untouched; `M6-P1000` + `M6-P1309` remain BLOCKED (not converted).
