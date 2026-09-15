# M6.2T — Evidence index (pre-wiring hardening: Scale-Gate clear-path + reader PII-reject + residuals, M6-OD-019)

| Field | Value |
|---|---|
| Prompt | **M6-P2807** — `M6_2T_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, `analysis_only`, ledger row 277 RUNNING) |
| Slice | **M6.2T** — owner-authorized (M6-OD-019) **pre-wiring hardening** that closes the 4 armed-not-fired forward findings from the M6.2R (P2609) + M6.2S (P2709) judge sign-offs, now the ops-core account is live (pin `54eb5f5`) and S1b wiring is near. **All 4 legs stricter / fail-closed-direction ONLY** (leg 1 can only HOLD more, never clear more; opens no PASS branch). The **first gate-logic change since M6.2Q** (`conditions._risk` + `scale_gate._assert_risk_clear_at_approval`). Cumulative superset of M6.2S under `04-artifacts/impl/M6.2T/`. |
| Owner input | **M6-OD-019** DECIDED 2026-09-10 (owner + tech-lead); artifact `04-artifacts/evidence/decisions/M6-OD-019.json` filed (verified by the SIGNED entry judge M6-P2800) — authorizes exactly this stricter-only hardening, no flag flip, no egress, mapper+reader UNWIRED, honest test reconciliation on the shared gate. |
| Posture (immutable, this slice flips nothing) | `global_gateway_state=BLOCKED` · `production_flag=OFF` · `external_send=OFF` · `live_migrations=false` · `SCALE_MODEL_RATIFIED=False` · `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False` · `HASH_POLICY_RATIFIED=False`. `config.py` sha256[:16] = `911b32381368f355` **unchanged**; `consumed.py`/`validator.py` **byte-identical to M6.2S**. |
| Result | Band M6-P2800 **SIGNED** (entry) → M6-P2801..2806 all **PASS**; full staged suite **743 passed / 0 failed / 0 skipped / 0 error**; SMK-032 **14/14**; boundary **0 in-scope FAIL-006/008 breach + 0 LOOSENING**; PII/secret scan **clean** (285 files, canonical 0/0/0/0/0 incl. `client_secret`). This index does **not** self-certify; the runner gate + slice Judge M6-P2809 decide (RULE-015). |

> ## ⚠ Read this before reading "stricter-only, green" as done — three load-bearing points
>
> **1. This slice CLOSES 4 carried residuals, and the closures are verified stricter-only against the ACTUAL source —
> not the self-report.** The single highest-stakes claim (the whole M6 safety posture rests on the gate being
> structurally unreachable to PASS) is that leg 1 only ever HOLDs/FAILs more. **Two independent gate reviews** concur —
> plus the coder's own in-prompt red-team, and this index's own source re-derivation: the **boundary** (M6-P2805) built
> an OLD-vs-NEW `_risk` truth table against the real M6.2S source (N4) — `_risk` NEW-PASS is a strict **subset** of
> OLD-PASS, `_assert_risk_clear_at_approval` added the `isinstance(bool)` check as an **AND**-conjunct (NEW-clear ⊆
> OLD-clear), the active-lock FAIL veto byte-identical; **security** (M6-P2806) re-verified on `conditions.py:122-133` +
> `scale_gate.py:118-136`; and the coder's own **impl red-team** (run inside the M6-P2802 implement prompt — not an
> independent gate) gate-stricter-no-nerf dimension came back CLEAN. The one carried test the change breaks
> (`test_smk_030_...:159` non-vacuity control) was **honestly reconciled to a strengthening** (re-pointed at a full-6
> no-active map still asserting PASS **+** a new 3-of-6→HOLD assertion) — and the plan red-team is what caught the
> coder's first draft falsely claiming "no test breaks / SMK-030 verified clean". On all these reads no PASS branch was
> opened, no certified M6.2G behavior loosened, and no test nerfed — **but the definitive stricter-only / no-nerf
> verdict is the exit Judge's (M6-P2809), not this index's.**
>
> **2. Reachability correction — the Scale GATE is WIRED; only the mapper + reader are unwired.** Across M6.2R/M6.2S the
> containment story was "unwired." The boundary + security both **correct** that here (N1): the recall **mapper** and
> registry **reader** stay unwired (no `app/` import), **but the Scale Gate itself is wired** via
> `app/api/scale_requests.py` (`handle_scale_decision → ScaleGate.record_owner_decision`). So the gate's containment is
> **not** "unwired" — it is (a) the **LEG-2 HOLD floor** (`is_scale_authorized` structurally False while M6-OD-002/005
> OPEN) **plus** (b) **RULE-H03** (`ScaleContext.risk_flags` is **server-assembled, not injectable** from the untrusted
> admin body — a body claiming clean cannot override a server context with an active lock). The judge and owner must
> weigh the gate on that basis, not on an "unwired" assumption.
>
> **3. The legs close MOST but not ALL of their targets — and leg 3 is NOT the primary FAIL-008 control.** Leg 3's
> input-side PII-shape reject is **best-effort input narrowing**, not a completeness guarantee: it under-catches names /
> short ids (<9 digits) / non-ASCII-TLD emails (N3), skips `updated_at` (L3c), and can over-reject legit long/prefixed
> governance codes (L3d/N2, an availability nerf, never a false-allow). **The primary FAIL-008 control for the metadata
> export remains EXPORT-side masking (M6-OD-012), which M6.2T deliberately did NOT add** — the live containment today is
> still the reader being UNWIRED (no durable sink). Do not over-attribute FAIL-008 completeness to leg 3. Leg 1 has a
> matching parity gap (**L1g**): the `isinstance(bool)` check landed in `_assert_risk_clear_at_approval` (approval) but
> **not** in `conditions._risk` (propose), so a full-6 junk-falsy map `{all6:0}` still PASSes `_risk` on presence alone —
> contained today by the HOLD floor + the `Mapping[str,bool]` type contract + RULE-H03.

---

## 1. Slice under review

M6.2T makes **4 stricter carried-file edits + the honest SMK-030 reconciliation + 3 new regressions** (NO migration, NO
config change, NO wiring, NO new secret, NO PASS branch):

- `scale/conditions.py` `_risk` (LEG 1): PASS now requires a **complete** read — `if not all(lock in ctx.risk_flags for lock in RISK_LOCKS): HOLD`. A partial no-active map → **HOLD** (was PASS); all-6-no-active → PASS, `{}` → HOLD, any active → FAIL (unchanged). Closes the M6.2R G4 forward finding; opens no PASS branch.
- `scale/scale_gate.py` `_assert_risk_clear_at_approval` (LEG 1): the clear predicate gains **bool-ness** (`isinstance(current_risk_flags[lock], bool)` AND-conjunct) — a falsy non-bool lock (`0`/`''`/`None`) no longer clears via the fresh-read path.
- `adapters/registry_feed_reader.py` (LEG 3 + N5/N6): `_looks_like_pii()` + parse-loop guard → a PII-shaped governance field (`event_code`/`event_group`/`domain`) → `feed_error:pii_shape_in_governance_field` (reject, state unchanged, input-side); `_resolve_typed` guards `isinstance(str)`/enum before the value-lookup (N5) + `malformed_fields` observability (N6).
- `scale/recall_risk_mapper.py` (LEG 4): `RecallRiskContributionError` on a `base_flags` carrying any `RECALL_RISK_KEY` (N3, no silent overwrite); `from_mapping` fail-closed → None on a non-iterable/bare-string `block_reasons` (N9).

The recall mapper + registry reader stay **UNWIRED**. The Scale Gate is **WIRED** (existing `app/api/scale_requests.py`); leg 1 hardens its existing logic and adds no new authz surface.

## 2. Band evidence (every prompt in the M6.2T band)

| Prompt | Role | Task | Ledger | Evidence file |
|---|---|---|---|---|
| **M6-P2800** | JUDGE | entry-gate judge | **SIGNED** | `M6-P2800.json` + `judge/M6-P2800_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS: 4 checks satisfied; M6-OD-019 DECIDED+filed; M6-CTR-003 DRAFT_LOCKED + M6-CTR-026 MISSING→harmonized-PASS via M6-P0709/M6-P0715; watch-items routed to the exit judge M6-P2809 — first shared-gate change, stricter-only, no nerf) |
| **M6-P2801** | CODER | plan | **PASS** | `M6-P2801.json` + `impl/M6.2T/PLAN.md` (plan red-team **prototyped leg 1 on the real SIGNED suite** → 716→715/1 FAIL; killed a false "no test breaks / SMK-030 verified clean" claim + corrected baseline 688→716 + pre-specified the honest SMK-030:159 reconciliation) |
| **M6-P2802** | CODER | implement | **PASS** | `M6-P2802.json` + `impl/M6.2T/IMPLEMENTATION_NOTES.md` (carry 716==716; final 729; M6.2S→M6.2T diff = only HOLD/reject/raise, no PASS/clear/allow; impl red-team 2 dims CLEAN; a mid-session power outage lost no on-disk edit) |
| **M6-P2803** | TESTER | build smoke | **PASS** | `M6-P2803.json` + `impl/M6.2T/tests/TEST_MANIFEST.md` (authored SMK-032 = 14 nodes, scenario/expected verbatim incl. the U+2192 arrow; collect-only 743; static-verification workflow all-CLEAN; strengthened a weak leg-iv assertion) |
| **M6-P2804** | TESTER | run smoke | **PASS** | `M6-P2804.json` + `test-reports/M6.2T/SMOKE_RESULTS.md` (executed: full staged suite **743 passed/0 failed RC0**; SMK-032 **14/14**, isolated `-k` cross-check; certified M6.2G behaviors re-run green as controls; not owner-waived) |
| **M6-P2805** | BOUNDARY_ADVERSARY | attack | **PASS** | `M6-P2805.json` + `boundary-reports/M6.2T_boundary.md` (executed harness, 26 outcomes = 18 DEFENDED / 5 OPEN_NONGATE / 3 NOTE / **0 in-scope BREACH / 0 LOOSENING**; OLD-vs-NEW `_risk` truth table vs real source; the N1 wired-gate reachability correction; posture unchanged; byte-clean) |
| **M6-P2806** | SECURITY_PII | security/PII | **PASS** | `M6-P2806.json` + `security-reports/M6.2T_security.md` (285 files scanned, canonical 0/0/0/0/0 incl. `client_secret`; leg 1 stricter-only verified on the code; SMK-030 reconciliation a strengthening; leg 3 landed but best-effort — primary FAIL-008 control is export-side M6-OD-012, deliberately not added) |
| **M6-P2807** | PM_ORCHESTRATOR | **this evidence-collect** | **RUNNING** | `M6-P2807.json` (this index's evidence, written last) + this file |
| M6-P2808 | ANALYST_ARCHITECT | docs | TODO | pending (`M6_2T_RUNBOOK.md`) |
| M6-P2809 | JUDGE | slice-gate judge | TODO | pending (`judge/M6-P2809_JUDGE_FINAL_SIGN_OFF.json`) — does the **definitive** stricter-only / no-nerf / mapper+reader-unwired verdict |

## 3. Artifacts / test reports / boundary + security reports

| Kind | Path | Note |
|---|---|---|
| Impl — gate edits | `04-artifacts/impl/M6.2T/app/measurement/scale/conditions.py`, `.../scale/scale_gate.py` | LEG 1: `_risk` all-6-to-PASS + `_assert_risk_clear_at_approval` bool-ness |
| Impl — reader/mapper | `.../adapters/registry_feed_reader.py`, `.../scale/recall_risk_mapper.py` | LEG 3 (PII-reject + N5/N6) + LEG 4 (N3/N9) |
| Impl — plan/notes | `04-artifacts/impl/M6.2T/PLAN.md`, `.../IMPLEMENTATION_NOTES.md` | plan + implementation record (**§5 rollback**) |
| Reconciled certified test | `.../tests/smoke/test_smk_030_recall_risk_mapper_to_scale_gate.py` | the ONE carried break; reconciled to a strengthening (3-of-6→HOLD added, full-6→PASS preserved) |
| Coder regressions | `.../tests/test_m6_2t_gate_clear_path_hardening.py`, `.../test_m6_2t_hold_floor_lock.py`, `.../test_m6_2t_residuals_hardening.py` | 13 cases across the 4 legs |
| Official smoke | `.../tests/smoke/test_smk_032_prewiring_hardening.py` | SMK-032, 14 nodes; scenario/expected verbatim |
| Test manifest | `.../tests/TEST_MANIFEST.md` | node→leg coverage, hardened code-under-test |
| Smoke results | `04-artifacts/test-reports/M6.2T/SMOKE_RESULTS.md` | 743 full suite / SMK-032 14/14; per-leg detail; masked synthetic trace ids |
| Boundary report | `04-artifacts/boundary-reports/M6.2T_boundary.md` | 26 outcomes, 0 in-scope breach + 0 loosening; harness `04-boundary/work/attacks/m6_2t_attacks.py` |
| Security report | `04-artifacts/security-reports/M6.2T_security.md` | PII/secret scan clean; scanner `06-security/work/pii_scan_2t.py` |

## 4. Exit-gate checklist mapping (every leg of the M6.2T done-gate, `00-spec/slices/M6.2T.md` §"Exit gate checks")

| # | Exit-gate leg | Status | Evidence |
|---|---|---|---|
| 1 | LEG 1 (G4/N2 clear-path): `_risk` PASSes only a complete all-6 no-active read (partial → HOLD); `_assert_risk_clear_at_approval` validates bool-ness (falsy non-bool does not clear); stricter-only, tests reconciled honestly (no nerf) | **MET** | SMK-032 leg-i (partial→HOLD, falsy-non-bool→ScaleGateViolation, all-6-real-bool control clears) + coder `test_m6_2t_gate_clear_path_hardening.py`; boundary N4 truth table + security code-read verify NEW-PASS ⊆ OLD-PASS; SMK-030:159 strengthened (see §5 L1g for the propose-side parity gap) |
| 2 | LEG 2 (N1 HOLD-floor lock): regression pins `is_scale_authorized` structurally unreachable while M6-OD-002/005 OPEN (no PASS branch even with both config floors monkeypatched True) | **MET** | SMK-032 leg-ii + coder `test_m6_2t_hold_floor_lock.py`; boundary "crown jewel" — max-cleared owner-approved request still HOLD, both floors flipped still HOLD |
| 3 | LEG 3 (F-FEED-PII input-side reject): a PII-shaped governance field → `feed_error` at parse, state unchanged; input-side, not export masking | **MET (as specified)** | SMK-032 leg-iii (×3 shapes × 3 fields) + legit-codes control + coder regression; boundary verified 4 shapes × 3 fields rejected, no leak. **Scoped honestly** — best-effort input narrowing, not the primary FAIL-008 control (see §5 L3c/N3/L3d) |
| 4 | LEG 4 (residuals): `recall_risk_contribution` rejects a base RECALL_RISK_KEY (N3); `from_mapping` fail-closed on non-iterable `block_reasons` (N9); reader `isinstance(str)` enum guard (N5); malformed-sibling observability (N6) | **MET** | SMK-032 leg-iv + coder `test_m6_2t_residuals_hardening.py`; boundary N3/N9/N6 CLOSED (see §5 L4c — N5 is observability-only, a hostile-eq object still coerces) |
| 5 | Proposed smoke M6-SMK-032 executed OR owner-waived | **MET (executed, not waived)** | `SMOKE_RESULTS.md` — 14/14, RC0; isolated `-k` cross-check |
| 6 | All slice prompts have evidence JSON (schema-valid, no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | M6-P2800..2806 done + clean; **M6-P2807 completing now**; **M6-P2808 (DOCS) still TODO** |
| 7 | Slice gate judge sign-off exists with verdict PASS | **PENDING** | **M6-P2809 TODO** (owner-run; does the definitive stricter-only/no-nerf/unwired verdict) |
| 8 | Rollback steps documented for every change this slice made | **MET** | `IMPLEMENTATION_NOTES.md` §5 "Rollback" (whole-slice: delete the `impl/M6.2T/` tree, M6.2S byte-identical & untouched, no live migration; per-item: scoped-revert the 4 stricter guards + the SMK-030 assertion to M6.2S bytes, delete the 3 new test files) |

**MET = legs 1, 2, 3, 4, 5, 8. PENDING = legs 6 (DOCS M6-P2808 + this JSON close it), 7 (judge M6-P2809).** Both pending legs are the normal remaining band tail, not defects.

## 5. Unresolved blockers / residuals (slice/owner-level — listed per the acceptance check; none blocks *this collection* prompt)

None blocks M6-P2807 (the collection is complete and unblocked). All residuals below are **armed-not-fired in the staged
posture** (0 in-scope FAIL-006/008 breach, 0 loosening). Reported honestly per the boundary + security routing.

**Closed by this slice (the carried residuals M6-OD-019 authorized closing — recorded so the judge can confirm):**

- **G4 (M6.2R partial-map false-clear) → CLOSED.** `conditions._risk` now HOLDs a partial no-active map (was PASS);
  verified NEW-PASS ⊆ OLD-PASS against the real source.
- **N2 (M6.2R approval-time) → CLOSED.** `_assert_risk_clear_at_approval` bool-ness: a falsy non-bool lock no longer clears.
- **F-FEED-PII / P2 input-side (M6.2S) → LANDED (partial).** The input-side reject I recommended at M6.2S is in place;
  the export-side half stays open (see L3c/N3 + M6-OD-012 below).
- **N3 (base-key overwrite), N9 (non-iterable `block_reasons`), N6 (malformed observability) → CLOSED.**

**Still open — routed (close before wiring / go-live):**

- **L1g → OWNER/CODER (leg-1 parity gap).** `conditions._risk` validates lock **presence, not bool-ness** — only
  `_assert_risk_clear_at_approval` got `isinstance(bool)`. So a full-6 junk-falsy map `{all6:0}` still PASSes `_risk` at
  propose, and the approval fallback clears via that propose PASS. **Contained today** by the LEG-2 HOLD floor
  (`is_scale_authorized` False), the `Mapping[str,bool]` type contract, and RULE-H03 (server-assembled `risk_flags`).
  **Becomes channel-reachable** if a future wiring assembles `risk_flags` from the untrusted feed/mapper without a
  full-6-real-bool validation — and the approval re-check reuses the **same** `deps.context` (not an independent second
  read). Fix: mirror `isinstance(bool)` in `_risk`; draw an independent validated read at approval.
- **L3c → SECURITY/owner.** Leg 3 checks `event_code`/`event_group`/`domain` but **not `updated_at`** — a PII-shaped
  `updated_at` applies and `to_public` echoes it raw (carried M6.2S P2 for that field). Extend the reject to `updated_at`.
- **N3 (leg-3 under-catch) → SECURITY/owner.** A shape detector under-catches names / short ids (<9 digits) /
  non-ASCII-TLD emails. **Leg 3 is best-effort input narrowing, not a complete FAIL-008 control** — the primary control
  is **export-side masking (M6-OD-012)**, which M6.2T deliberately did not add.
- **L3d / N2 (leg-3 over-broad) → OWNER.** The detector false-positive-rejects a ≥9-digit run and a customer-id
  prefix+digit (`GUEST_2`/`UID_7`/`fbid_1`), dropping the whole feed — an availability nerf (never a false-allow).
  Tighten/anchor the regexes before go-live.
- **L4c → CODER.** Leg-4 N5 is **observability-only**, not a hard block: `_resolve_typed` flags a non-str sibling
  malformed but **still calls `resolver(raw)`**, so a hostile `__eq__`/`__hash__` object still coerces to
  `ALLOW_EXTERNAL` via the enum value-lookup. In-process code-exec only; reading opens no egress. Fix: **block** (return
  the fail-closed default without calling the resolver), don't just flag. (`validator.py` byte-identical to M6.2S — no
  loosening, edge carried not closed.)

**Carried, unchanged by this slice (armed-not-fired, no durable sink → M6-OD-012 export-masking family):**

- **S3 export echoes → M6-OD-012.** `RegistryFeedRow.to_public` echoes governance metadata raw (governance ids by
  design); `OwnerDecision.to_public` (M6.2R F-SEC-2R-1) + `AdsSpendImportDecision.to_public` (M6.2Q MC-09) still echo
  `reason`/`audit_ref` verbatim. Note: the OwnerDecision **audit sink** (`scale_gate._audit_decision`) does **not** echo
  them (machine-safe) — it is the **model export** that is unhardened.
- **Untrimmed `event_code` split (M6.2S CRIT-04) → CHIEF** (RULE-001, tombstone/contract; do not self-resolve).
- **Trace-id family + F-EVID-4/5/6** — carried open evidence-trace-id residuals; M6.2T adds no new instance.
- **F-SEC-2I-1 / N1(M6.2Q) `live_session` provenance → OWNER** — carried, armed-not-fired, unaffected by M6.2T (per
  security report §9; the third carried item alongside B1→M6-OD-003 and ops-core/M3→M6-OD-011 in the forward block).

**Hard forward conditions (recorded, NOT resolved — gate any live wiring / real scale / egress):**

- **M6-OD-002 / M6-OD-005** (Scale-Gate thresholds/model) **OPEN** — the LEG-2 HOLD floor **depends on them staying
  open**; opening a PASS branch would arm the L1g residual. Leg 2 hardens *around* them; it opens no PASS branch.
- **M6-OD-003** (permit-mapping / hash) **OPEN** — the egress control alongside `EXTERNAL_SEND` OFF; N/A here (no wiring).
- **S1b wiring seam + live M3 endpoint (ENTRY-003 V221) + M6-OD-011** — server-bind/go-live; at wiring, ops-core/M3
  credentials must be a `secret_ref`, the M6.2O AST import-gate allow-list needs a deliberate update, and the
  scale-decision endpoint needs real authN. The L3c/`updated_at` reject + the M6-OD-012 export control must land **before**
  any durable sink.

**Carried operator hygiene (non-blocking; PM/JUDGE denied write root):** register **M6-OD-013** + **M6-OD-014** + the M5
`PSID_HASH_POLICY_M5_TMP` dependency in `DECISION_REGISTER.md`; reconcile the stale **ENTRY-004** row. (Contrast:
**M6-OD-019** for this slice **is** properly filed — `04-artifacts/evidence/decisions/M6-OD-019.json` exists.)

## 6. Count reconciliation + governance

- **Full staged suite 743 = 716 (M6.2S SIGNED carried) + 13 (coder regressions across the 4 legs) + 14 (official SMK-032
  nodes).** Gate invariant baseline ≤ final holds at both steps (716 ≤ 729 ≤ 743); 0 carried test dropped; 0 skip. The
  SMK-030:159 reconciliation is a **modification** of a carried test (one assertion strengthened, none deleted), inside
  the 729. Migrations stay `0001–0016`. `config.py` sha256[:16] = `911b32381368f355` unchanged.
- **Governance posture unchanged and immutable:** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
  `external_send=OFF`, both scale floors (`SCALE_MODEL_RATIFIED`, `DASHBOARD_ALERT_THRESHOLDS_DEFINED`) **False**,
  `live_migrations=false`. **M6-P1000** (M6.2A entry) + **M6-P1309** (M6.2D exit) verdicts remain **BLOCKED** (not
  converted). No flag flip, no wiring, no live HTTP, no egress, no migration, no new secret, no write to
  `04-artifacts/state/` (mechanically-verifiable posture facts). That the change opens **no PASS branch** and loosens
  **no certified M6.2G behavior** is the finding of the boundary + security gate reads (and this index's own source
  re-derivation) — the definitive verdict is the exit Judge's (M6-P2809).
- **Boundary intact:** leg 1 only makes the WIRED Scale Gate FAIL/HOLD more (never clears more, no scale executed —
  RULE-017/FAIL-006); the mapper + reader stay UNWIRED; leg 3 is an input-side PII reject (RULE-014/FAIL-008), never
  storing/exporting the PII; no CRM/egress/commission (RULE-018/019). This slice proves the hardening with staged
  evidence only; it declares no ROAS Pass / Scale Ready (owner-only).

---

*PM_ORCHESTRATOR evidence-collect, `analysis_only`. Every band evidence file, artifact, test/boundary/security report is
indexed and mapped to the 8 exit-gate legs; unresolved slice/owner-level items (and the carried residuals this slice
closed) are listed in §5. No self-certification (RULE-015): `status=PASS` on M6-P2807 means the **collection** task is
complete and unblocked — it does **not** assert the slice passes, and specifically does **not** pronounce the
stricter-only / no-nerf / unwired verdict, which is the exit Judge's (M6-P2809). The runner EVIDENCE_GATE and that Judge
decide slice closure.*
