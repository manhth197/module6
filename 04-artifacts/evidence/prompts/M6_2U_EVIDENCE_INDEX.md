# M6.2U — Evidence index (recall E2 §3 conformance + migration renumber + psid_hash docstring, M6-OD-020, chief 2026-09-16 fix)

| Field | Value |
|---|---|
| Prompt | **M6-P2907** — `M6_2U_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, `analysis_only`, ledger row 287 RUNNING) |
| Slice | **M6.2U** — fixes three chief-auditor 2026-09-16 M6-self-doable findings (owner M6-OD-020): **B3** recall E2 §3 conformance (a distinct sellability no-scale veto + pull-error→FAIL), **B1/B4** migration renumber README, **D20** psid_hash docstring. Cumulative superset of M6.2T. Leg 1 **ADDs a FAIL** to the recall path — stricter/fail-closed only, opens no PASS branch. Mapper stays UNWIRED. |
| Owner input | **M6-OD-020** DECIDED 2026-09-17 (owner + tech-lead, conforming to chief `E2_BLOCK_REASON_V1` §1/§3); artifact `04-artifacts/evidence/decisions/M6-OD-020.json` filed (verified by SIGNED entry judge M6-P2900). **Supersedes the M6-OD-017 "never read decision" clause ONLY** — a legitimate owner conformance to the chief canonical, not a contradiction; the recall-boolean mapping stays in force. |
| Posture (immutable, this slice flips nothing) | `global_gateway_state=BLOCKED` · `production_flag=OFF` · `external_send=OFF` · `live_migrations=false` · both scale floors (`SCALE_MODEL_RATIFIED`, `DASHBOARD_ALERT_THRESHOLDS_DEFINED`) **False**. `config.py` sha256[:16] = `911b32381368f355`, `scale_gate.py`/`consumed.py`/`validator.py` **byte-identical to M6.2T**; **all 16 migration SQL byte-identical (no 0017 SQL written).** |
| Result | Band M6-P2900 **SIGNED** (entry) → M6-P2901..2906 all **PASS**; full staged suite **768 passed / 0 failed / 0 skipped / 0 error**; SMK-033 **14/14**; boundary **0 in-scope FAIL-006 breach + 0 LOOSENING**; PII/secret scan **clean** (287 files, canonical 0/0/0/0/0 incl. `client_secret`). This index does **not** self-certify; the runner gate + slice Judge M6-P2909 decide (RULE-015). |

> ## ⚠ Read this before reading "B3 closed + green" as "recall sellability is now enforced" — three honesty points
>
> **1. The new veto is DEAD CODE on every channel-reachable path today, and FRAGILE even at wiring.** The only producer
> of `not_sellable` is the **UNWIRED** recall mapper, so `conditions._risk`'s new `if not_sellable → FAIL` branch has
> **zero behavioral effect on any current wired path** (boundary/security N6). "B3 closed" is true only for a **future
> direct-feed wiring**. Worse, the veto is honored on **one narrow path** (a direct `read.risk_flags` feed) and is
> **dropped or inverted** through the module's own sanctioned "always safe to feed the gate" helper
> `recall_risk_contribution` (boundary/security **N1, highest-priority-before-S1b**): a NOT_SELLABLE-clean read merged
> with a **complete** base returns a full clean map → **Risk PASS** — an *affirmative clear* of a NOT_SELLABLE lot,
> worse than HOLD; with no base → `{}` → HOLD. So the exit Judge/owner must not read this as "sellability is enforced":
> it is a mechanism proven correct on its direct channel, inert today, and needing N1 + A2 (approval-time re-check
> ignores `not_sellable`) + N3 (three carriers, one honored) hardened **before** any S1b wiring.
>
> **2. Stricter-only is verified against the ACTUAL source, exhaustively — but the wins are conditional on §1.** An
> independent red-team enumerated `_risk` over **all 2187 combinations** of the 6 RISK_LOCKS + `not_sellable`
> (absent/True/False), M6.2T vs M6.2U: **0 inputs less strict, 0 new PASS, 64 strictly stricter** (63 HOLD→FAIL, 1
> PASS→FAIL — the full-6-no-active-but-`not_sellable` case, the veto correctly overriding). `not_sellable` is **not** a
> RISK_LOCK, so the all-6 completeness, `active_risk_locks`, and every non-mapper context are unchanged; the certified
> clear-path (SELLABLE + all-6 → PASS) is preserved; ops-core §4 holds (the recall booleans stay presence-derived,
> **never** from decision). The 17 reconciled mapper tests are **strengthenings** — including the honest rename
> `never_reads_decision → never_derives_recall_booleans_from_decision` (the mapper now *does* read `decision`, only for
> the veto, so the old name was a false claim).
>
> **3. The migration change is README-only + a latent-conformance fix.** No `0017` SQL is written (authored at
> server-bind); all 16 SQL files are byte-identical. And a subtle legitimacy note: SMK-030(iii)'s **verbatim** register
> Expected has always read "a pull error → gate FAIL", but M6.2R **under-implemented** it as HOLD — M6-OD-020's veto
> brings the smoke into conformance with its own quoted Expected (the verbatim block untouched; only author-prose +
> assertions updated). So leg 1 also closes a latent under-implementation, not merely adds strictness.

---

## 1. Slice under review

M6.2U's **CODER-implement footprint** is a surface diff of **1 new + 6 changed files** (byte-hash); the **TESTER** then
adds the official SMK-033 smoke file + updates `TEST_MANIFEST.md`, so the **full delivered slice differs from M6.2T by
2 new + 7 changed**. NO migration SQL, NO config change, NO wiring, NO new secret, NO PASS branch:

- `scale/conditions.py` `_risk` (LEG 1): after the active-lock FAIL and **before** the M6.2T all-6 completeness check,
  adds `if ctx.risk_flags.get("not_sellable"): return FAIL`. `not_sellable` is **not** in `RISK_LOCKS`.
- `scale/recall_risk_mapper.py` (LEG 1): `map_risk_flags` keeps the 3 recall booleans **presence-derived** (ops-core §4)
  and, separately, reads `decision` **once** → `not_sellable=True` only when `decision != "SELLABLE"`; `_incomplete`
  (pull-error/timeout/429/absent/malformed) → `{"not_sellable": True}`, `unverified=True` → FAIL (was `{}`→HOLD).
  `RecallRiskRead` gains `sellable`/`unverified`. **`recall_risk_contribution` LEFT byte-identical** (the plan red-team's
  key fix — propagating the veto there would fall to `{}`→HOLD and pollute the 6-lock map; see §5 N1).
- `models/attribution_context.py` (LEG 3): `as_stored` docstring corrected to the M6-OD-015 no-join policy; **code
  byte-identical** (`return dict(self.to_public())` — no psid_hash join ever existed).
- `migrations/README.md` (LEG 2): rewritten from a stale `0001–0005` to list `0001–0016` + a `0017_enforcement` note
  (renumbered from the taken `0014`; `0014–0016` are M6.2Q ads-spend). **No SQL file written.**
- 2 reconciled carried mapper test files + 1 new regression (`tests/test_m6_2u_recall_e2_conformance.py`, 11 tests);
  plus the TESTER's official SMK-033 smoke (`tests/smoke/test_smk_033_recall_e2_conformance.py`, 14 nodes) + a
  `TEST_MANIFEST.md` update — together the 2-new + 7-changed full-slice delta.

The recall mapper stays **UNWIRED**. The Scale Gate is wired (existing `app/api/scale_requests.py`), but its
`risk_flags` is server-assembled (RULE-H03, not body-injectable); M6.2U adds no new authz surface.

## 2. Band evidence (every prompt in the M6.2U band)

| Prompt | Role | Task | Ledger | Evidence file |
|---|---|---|---|---|
| **M6-P2900** | JUDGE | entry-gate judge | **SIGNED** | `M6-P2900.json` + `judge/M6-P2900_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS: 4 checks; M6-OD-020 DECIDED+filed, supersedes M6-OD-017 decision-exclusion ONLY; M6-CTR-026 MISSING→harmonized-PASS; watch-items routed to exit judge — stricter-only, booleans still not derived from decision, README-only renumber) |
| **M6-P2901** | CODER | plan | **PASS** | `M6-P2901.json` + `impl/M6.2U/PLAN.md` (plan red-team's MAJOR fix: **DROP** the `recall_risk_contribution` not_sellable propagation — it would fall to `{}`→HOLD not FAIL + pollute the 6-lock map; leave the helper byte-identical; two mechanical reconciliation RULES; did **not** claim "no test breaks", learning from M6.2T) |
| **M6-P2902** | CODER | implement | **PASS** | `M6-P2902.json` + `impl/M6.2U/IMPLEMENTATION_NOTES.md` (carry 743==743; final 754; surface diff 1 new + 6 changed by byte-hash; **2187-combo** stricter-only proof by an independent red-team = 0 loosening/0 new PASS/64 stricter; 17 tests reconciled as strengthenings) |
| **M6-P2903** | TESTER | build smoke | **PASS** | `M6-P2903.json` + `impl/M6.2U/tests/TEST_MANIFEST.md` (authored SMK-033 = 14 nodes, scenario/expected verbatim incl. two U+2192 arrows; collect-only 768; static-verification workflow all-CLEAN) |
| **M6-P2904** | TESTER | run smoke | **PASS** | `M6-P2904.json` + `test-reports/M6.2U/SMOKE_RESULTS.md` (executed: full staged suite **768 passed/0 failed RC0**; SMK-033 **14/14**, isolated `-k` cross-check; clear-path + ops-core-§4 controls green; not owner-waived) |
| **M6-P2905** | BOUNDARY_ADVERSARY | attack | **PASS** | `M6-P2905.json` + `boundary-reports/M6.2U_boundary.md` (executed harness, 23 outcomes = 16 DEFENDED / 5 OPEN_NONGATE / 2 NOTE / **0 in-scope BREACH / 0 LOOSENING**; stricter-only vs real M6.2T source; surfaced the **N1 veto-inversion triad** + N6 dead-code honesty; posture unchanged; byte-clean) |
| **M6-P2906** | SECURITY_PII | security/PII | **PASS** | `M6-P2906.json` + `security-reports/M6.2U_security.md` (287 files scanned, canonical 0/0/0/0/0 incl. `client_secret`; leg 1 stricter-only + RULE-018-clean on the code; leg 3 a **security-positive** psid-no-join doc fix; confirms N1/N6) |
| **M6-P2907** | PM_ORCHESTRATOR | **this evidence-collect** | **RUNNING** | `M6-P2907.json` (this index's evidence, written last) + this file |
| M6-P2908 | ANALYST_ARCHITECT | docs | TODO | pending (`M6_2U_RUNBOOK.md`) |
| M6-P2909 | JUDGE | slice-gate judge | TODO | pending — does the **definitive** stricter-only / no-nerf / booleans-not-derived / mapper-unwired verdict |

## 3. Artifacts / test reports / boundary + security reports

| Kind | Path | Note |
|---|---|---|
| Impl — gate + mapper | `04-artifacts/impl/M6.2U/app/measurement/scale/conditions.py`, `.../scale/recall_risk_mapper.py` | LEG 1: `not_sellable→FAIL` branch + the mapper veto/`_incomplete` FAIL |
| Impl — docstrings | `.../models/attribution_context.py` (LEG 3, docstring-only), `migrations/README.md` (LEG 2, no SQL) | |
| Impl — plan/notes | `04-artifacts/impl/M6.2U/PLAN.md`, `.../IMPLEMENTATION_NOTES.md` | plan + implementation record (rollback in the **"Rollback"** section) |
| Reconciled carried tests | `.../tests/test_m6_2r_recall_risk_mapper.py`, `.../tests/smoke/test_smk_030_recall_risk_mapper_to_scale_gate.py` | 17 tests reconciled (RULE A/B + reframe); verbatim register blocks untouched |
| Coder regression | `.../tests/test_m6_2u_recall_e2_conformance.py` | 11 cases |
| Official smoke | `.../tests/smoke/test_smk_033_recall_e2_conformance.py` | SMK-033, 14 nodes; scenario/expected verbatim |
| Test manifest / smoke results | `.../tests/TEST_MANIFEST.md`, `04-artifacts/test-reports/M6.2U/SMOKE_RESULTS.md` | 768 full suite / SMK-033 14/14 |
| Boundary report | `04-artifacts/boundary-reports/M6.2U_boundary.md` | 23 outcomes, 0 in-scope breach + 0 loosening; harness `04-boundary/work/attacks/m6_2u_attacks.py` |
| Security report | `04-artifacts/security-reports/M6.2U_security.md` | PII/secret scan clean; scanner `06-security/work/pii_scan_2u.py` |

## 4. Exit-gate checklist mapping (every leg of the M6.2U done-gate, `00-spec/slices/M6.2U.md` §"Exit gate checks")

| # | Exit-gate leg | Status | Evidence |
|---|---|---|---|
| 1 | LEG 1 (B3 E2 §3, M6-OD-020): decision not observed SELLABLE (NOT_SELLABLE / unknown / missing) → Risk **FAIL** (sellability, distinct from the recall booleans; ops-core §4 preserved); pull error/incomplete → Risk **FAIL** (not HOLD) + 'unverified'; SELLABLE + no-active still clears (nothing loosened); no test nerfed | **MET (as specified)** | SMK-033 i/ii/iii + not-derived + clear-path control + distinctness + coder `test_m6_2u_recall_e2_conformance.py`; boundary S1 + security verify stricter-only on the code; 2187-combo proof. **Honestly scoped** — dead code today + fragile at wiring (see §5 N1/N6) |
| 2 | LEG 2 (B1/B4 migration renumber): README lists `0001–0016` + `0017_enforcement` with apply order (renumbered from the taken 0014); no new SQL written | **MET** | `migrations/README.md`; all 16 SQL byte-identical, no 0017 SQL (byte-hash); boundary/security L23 docs-only |
| 3 | LEG 3 (D20 docstring): `attribution_context` psid_hash docstring conforms to M6-OD-015 no-join; code path unchanged | **MET** | `attribution_context.py` docstring; `as_stored()` byte-identical; security calls it a **security-positive** fix (reduces future cross-module psid-join risk) |
| 4 | Proposed smoke M6-SMK-033 executed OR owner-waived | **MET (executed, not waived)** | `SMOKE_RESULTS.md` — 14/14, RC0; isolated `-k` cross-check |
| 5 | All slice prompts have evidence JSON (schema-valid, no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | M6-P2900..2906 done + clean; **M6-P2907 completing now**; **M6-P2908 (DOCS) still TODO** |
| 6 | Slice gate judge sign-off exists with verdict PASS | **PENDING** | **M6-P2909 TODO** (owner-run; definitive stricter-only/no-nerf/unwired verdict) |
| 7 | Rollback steps documented for every change this slice made | **MET** | `IMPLEMENTATION_NOTES.md` "Rollback" section (whole-slice: delete the `impl/M6.2U/` tree, M6.2T untouched, no live migration; per-item: revert the 2 code + 2 doc files + reconciled tests to M6.2T bytes, delete the new regression) |

**MET = legs 1, 2, 3, 4, 7. PENDING = legs 5 (DOCS M6-P2908 + this JSON close it), 6 (judge M6-P2909).** Both pending legs are the normal remaining band tail, not defects.

## 5. Unresolved blockers / residuals (slice/owner-level — listed per the acceptance check; none blocks *this collection* prompt)

None blocks M6-P2907 (the collection is complete and unblocked). All are **armed-not-fired today** (0 in-scope FAIL-006
breach, 0 loosening; the only producer of `not_sellable` is the unwired mapper). Reported per the boundary + security
routing.

**Load-bearing — the E2 §3 veto is real but fragile; harden before S1b wiring:**

- **N1 → OWNER/CODER (highest-priority, before S1b).** The `not_sellable` veto is enforced ONLY on a direct
  `read.risk_flags` feed and is **dropped (→HOLD) or inverted (→affirmative PASS)** through `recall_risk_contribution`
  — the module's own documented "always safe to feed the gate" helper (it copies only the 3 `RECALL_RISK_KEYS`). A
  wiring that uses the sanctioned helper would **silently lose or invert** the veto. `recall_risk_contribution` MUST
  propagate `not_sellable` before any live wiring. (Note: a base carrying `not_sellable=True` *survives* to FAIL — N2 —
  so the honored-vs-dropped split depends on **where** the caller places the key, a fragile undocumented split.)
- **A2 → OWNER/CODER.** The approval-time re-check `scale_gate._assert_risk_clear_at_approval` is byte-identical to
  M6.2T and checks only the 6 RISK_LOCKS — a fresh NOT_SELLABLE at approval clears the risk re-check via the all-6 path.
  Contained today (a `not_sellable` propose already FAILs overall → refused; the fresh-only case sits behind the
  overall-FAIL guard + the HOLD floor). Mirror the `not_sellable` check at approval before wiring.
- **N3 → OWNER/CODER.** Three veto carriers (`risk_flags['not_sellable']`, `sellable=False`, `unverified`) but the gate
  reads only `ctx.risk_flags` — an integrator keying off `read.sellable`/`unverified` drops the veto. Map them into
  `risk_flags` at wiring.
- **N6 → the exit-judge honesty note.** The `not_sellable` branch is **dead code on every channel-reachable input
  today**; the approval refusal is a **single-point defense** (the overall-FAIL coupling). "B3 closed" = a future
  direct-feed wiring only. Not a defect — the honest scope.

**Code-hardening (CODER, in-process-only today — a JSON/S1b wire yields a plain `str`; mapper unwired):**

- **N5 → CODER.** `decision == "SELLABLE"` dispatches to the operand's `__eq__`, so a hostile `str`-subclass could spoof
  sellability. Add a `type(decision) is str` guard.
- **N2 → CODER (documentation).** Document the base-vs-read veto-placement split (base=honored, read=dropped through the
  helper).

**Carried, unchanged by this slice (armed-not-fired, no durable sink → M6-OD-012 export-masking family):**

- **S3 export echoes → M6-OD-012.** `OwnerDecision` / `AdsSpendImportDecision` / `RegistryFeedRow` `to_public` still
  echo `reason`/`audit_ref`/metadata raw (audit sinks hardened, model exports not) — the **export-side masking decision
  remains the primary FAIL-008 control**; M6.2U adds no new instance.
- **Pre-existing stale M6.2T mapper docstrings** (`recall_risk_mapper` module + `risk_picture_complete`) still describe
  `_risk` as "reads any non-empty no-active map as PASS / does not require all 6" — a limitation M6.2T's all-6 hardening
  already closed. **Stale in the conservative direction** (understates the gate's safety); authoritative source
  (`conditions.py`) is correct. Out of M6-OD-020 scope → a docs pass. (Distinct from the LEG-3 psid_hash docstring,
  which this slice **did** fix.)
- **M6.2U-introduced stale in-file comments → docs pass (behavior-neutral).** `recall_risk_mapper.py`'s
  `OpsCoreAvailabilityResponse` class docstring (~line 60) and its `decision` field comment (~line 69) still say
  `decision` is "NEVER read" — now contradicted by this slice's own veto (line 153 `sellable = (response.decision ==
  "SELLABLE")`). The module-top docstring **and** the test rename (`never_reads_decision → never_derives_recall_booleans_from_decision`)
  were updated to acknowledge the read, but these two in-file spots were missed. Does **not** change the stricter-only
  verdict (the `decision`-read is only the fail-closed veto; the recall booleans stay presence-derived); a docs correction.
- **Untrimmed `event_code` split (M6.2S CRIT-04) → CHIEF**; **trace-id family + F-EVID-4/5/6**; **F-SEC-2I-1 / N1(M6.2Q)
  `live_session` provenance → OWNER** — all carried, armed-not-fired.

**Hard forward conditions (recorded, NOT resolved — gate any live wiring / real scale / egress):**

- **M6-OD-002 / M6-OD-005** (Scale-Gate thresholds/model) **OPEN** — leg 1's added FAIL opens no PASS branch; the HOLD
  floor depends on them staying open.
- **M6-OD-003** (permit-mapping / hash) **OPEN** — B1 real-pepper + privacy/legal; the egress control. N/A here.
- **S1b wiring seam + live M3 endpoint + the `0017_enforcement` SQL + M6-OD-011** — server-bind/go-live; at wiring,
  ops-core/M3 credentials must be a `secret_ref`, the M6.2O import-gate allow-list needs a deliberate update, the
  `0017` SQL is authored, and the endpoint needs real authN. **N1 + A2 + N3 must land before the veto is trusted live.**

**Carried operator hygiene (non-blocking; PM/JUDGE denied write root):** register **M6-OD-013** + **M6-OD-014** + the M5
`PSID_HASH_POLICY_M5_TMP` dependency in `DECISION_REGISTER.md`; reconcile the stale **ENTRY-004** row. (Contrast:
**M6-OD-020** for this slice **is** properly filed — `04-artifacts/evidence/decisions/M6-OD-020.json` exists.)

## 6. Count reconciliation + governance

- **Full staged suite 768 = 743 (M6.2T SIGNED carried) + 11 (coder regression `test_m6_2u_recall_e2_conformance.py`) +
  14 (official SMK-033 nodes).** Gate invariant baseline ≤ final holds at both steps (743 ≤ 754 ≤ 768); the 17
  reconciled tests changed assertions/names, **not** the count; 0 skip/xfail/deletion. `config.py` sha256[:16] =
  `911b32381368f355` unchanged; `scale_gate.py`/`consumed.py`/`validator.py` + all 16 migration SQL byte-identical.
- **Governance posture unchanged and immutable:** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
  `external_send=OFF`, both scale floors **False**, `live_migrations=false`. **M6-P1000** (M6.2A entry) + **M6-P1309**
  (M6.2D exit) verdicts remain **BLOCKED** (not converted). No flag flip, no wiring, no live HTTP, no egress, no
  migration SQL, no new secret, no write to `04-artifacts/state/`.
- **Boundary intact:** leg 1 only makes the WIRED Scale Gate FAIL more (never clears more, no scale executed —
  RULE-017/FAIL-006); the recall mapper stays UNWIRED; reading `decision` is for M6's **own** sellability gate, not
  owning the recall decision or M3 gating (RULE-018 — the recall booleans stay presence-derived); no CRM/egress/
  commission. This slice proves the conformance with staged evidence only; it declares no ROAS Pass / Scale Ready.

---

*PM_ORCHESTRATOR evidence-collect, `analysis_only`. Every band evidence file, artifact, test/boundary/security report is
indexed and mapped to the 7 exit-gate legs; unresolved slice/owner-level items are listed in §5. No self-certification
(RULE-015): `status=PASS` on M6-P2907 means the **collection** task is complete and unblocked — it does **not** assert
the slice passes, and specifically does **not** pronounce the stricter-only / no-nerf / mapper-unwired verdict, which is
the exit Judge's (M6-P2909). The runner EVIDENCE_GATE and that Judge decide slice closure.*
