# M6.2K — Slice Runbook — Smoke & Evidence Pack (the FINAL build slice)

> **Status: STAGED — proves capability with evidence, NOT readiness.**
> M6.2K re-ran the whole P0 smoke matrix (18 smokes) and assembled the doc §22 evidence plan (10 categories)
> into an **owner sign-off package**. The assembled pack's readiness tops out at **`OWNER_REVIEW_REQUIRED`** —
> its `Readiness` enum has **no PASS / READY / SCALE-READY member**, so "ready to scale/send" is *unrepresentable*.
> A green run is **not** a verdict: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
> all scale/hash/learning flags `False` — **immutable, untouched, and they stay OFF through M6.2K and into
> PR/PILOT**. `M6-P1000` (M6.2A entry) and `M6-P1309` (M6.2D exit) verdicts remain **BLOCKED** (not converted).
> Declaring ROAS Pass / Scale Ready is **owner-only** (doc §23) and is **not** done here.
> **8 standing blockers** (§5.4) remain open and are carried inside every assembled pack.
>
> Evidence at a glance: full staged suite **523 passed / 0 failed / 0 skipped / 0 error, rc 0**;
> **18/18** P0 smokes PASS (72/72 evidence-leg nodes), each recorded with a masked `correlation_id` + `evidence_id`;
> boundary **0** FAIL-007 breaches across 43 executed attacks; security **0** raw PII / **0** secrets across 234 files.
> Nothing patched, no migration, no new flag, no new endpoint. Next: slice-gate Judge **M6-P2009** (fresh session).

| Field | Value |
|---|---|
| Slice | **M6.2K** — Smoke & Evidence Pack (cross-phase; depends on M6.2J; the last build slice before PR/PILOT) |
| Prompt (this doc) | **M6-P2008** — `M6_2K_DOCS` (ANALYST_ARCHITECT, `analysis_only`, EVIDENCE_GATE) |
| Doc scope | doc §20 (P0 tests), §21 (smoke register), **§22 (evidence plan → owner review package)**, §23 (owner-only sign-off) |
| Rule / fail gate in scope | **M6-RULE-015** (executors write evidence, never self-certify) · **M6-FAIL-007** ("No evidence": calling PASS without audit/evidence/smoke) |
| Contract | **M6-CTR-025** `Evidence package (owner review pack)` — DRAFT_LOCKED (content-level = doc §22 verbatim + M6-P0714; file format = pack HARDENING). The pack this slice assembles **is** the CTR-025 deliverable. |
| Deliverable state | STAGED under `04-artifacts/impl/M6.2K/`; no live integration. Readiness = **`OWNER_REVIEW_REQUIRED`**. |

---

## 1. What this slice built (staged under `04-artifacts/impl/M6.2K/`)

M6.2K carries the **entire M6.2J app forward byte-identical** (baseline verified green **before any patch: 425 passed,
rc 0** — exact parity with M6.2J) and adds **one** package: the read-only evidence-pack assembler. It writes nothing,
sends nothing, flips nothing — it reads recorded smoke results + evidence refs and returns a frozen report object.

### 1.1 The evidence assembler (new `app/measurement/evidence/`) — a read-only, no-self-cert aggregator

| File | Purpose |
|---|---|
| `smoke_registry.py` | canonical **18** P0 smoke ids (SMK-001…018) + scenario/expected **verbatim from doc §21** + `owner`/`proposed` status + `test_smk_<nnn>_*.py` bindings (proposed = executed **or** owner-waived). |
| `categories.py` | the **10** doc §22 evidence categories + their mandatory-content requirement keys. |
| `models.py` | frozen `SmokeResult` / `CategoryStatus` / `GapBlocker` / `EvidencePack`; the `Readiness` enum with **no PASS/READY member** (only `OWNER_REVIEW_REQUIRED` / `NOT_READY`); `to_public()` masks `correlation_id` / `evidence_id` (RULE-014 / H02). |
| `gap_blockers.py` | the canonical **8** `STANDING_GAP_BLOCKERS` + `STANDING_BLOCKER_IDS` (the honest payload). |
| `pack_assembler.py` | `EvidencePackAssembler.assemble()` — category COMPLETE only with all mandatory content (else INCOMPLETE, fail-closed); a `SmokeResult` per registered smoke (un-provided ⇒ un-run); **owner-smoke waiver stripped** (only a *proposed* smoke may be waived); **always merges the 8 standing blockers**; readiness per the ONE rule; records a **read-only** `MappingProxyType` posture snapshot. It has **no** pass/ready/certify/sign_off/approve/enable/flag-flip method. |

### 1.2 The doc §22 owner review package — 18 P0 smokes × 10 evidence categories

- **18 P0 smokes re-run** (15 owner `SMK-001…015` + 3 proposed `SMK-016/017/018`); the three proposed smokes were
  **executed**, not owner-waived. Each smoke recorded a masked `correlation_id` + `evidence_id` (doc §22 Smoke Report).
- **All 10 doc §22 categories** assembled **with mandatory content**: Event Registry, Consent, Outbox, Dedup,
  Attribution, Dashboard, Scale Gate, Learning, Security/Privacy, Smoke Report. Completeness is proven **structurally**
  (a missing mandatory key ⇒ INCOMPLETE ⇒ `NOT_READY`, fail-closed FAIL-007) — not asserted by prose.
- The full 10-category → evidence map is in `04-artifacts/evidence/prompts/M6_2K_EVIDENCE_INDEX.md` §4 (M6-P2007).

### 1.3 No new migration, no new config flag, no patched carried file (deliberate)

doc §13 defines **no** evidence-pack table, so **RULE-018 forbids inventing one** — the assembler is assembly-only over
the carried subsystems. **No carried-forward file was patched**; **no migration** was added; **no config flag** was
introduced. This keeps rollback trivial (§4) and the security surface tiny (no new identity handling, egress, or endpoint).

---

## 2. Operate

The evidence pack is a **library artifact for owner review**, not a service. There is no runtime to "operate" in
production terms — nothing here is wired to an endpoint (§5.5). Operation = **assembling and reading the owner package**.

1. **Assemble the pack (staged, read-only).** From `04-artifacts/impl/M6.2K/`:
   `EvidencePackAssembler().assemble(smoke_results, evidence_refs)` returns a frozen `EvidencePack` describing which
   §22 categories are complete, which smokes are recorded, the honest gap/blocker list, the readiness enum, and a
   read-only posture snapshot. It **writes nothing and changes no posture**.
2. **Read the owner package.** The reader's map is `M6_2K_EVIDENCE_INDEX.md`: §1 band evidence, §2 artifact inventory,
   §3 CTR-025, **§4 the 10-category evidence map**, §5 the 22-leg exit-gate map, **§6 the honest gap/blocker list**,
   §7 the Judge reader's guide. The per-smoke recorded ids are in `test-reports/M6.2K/SMOKE_RESULTS.md`.
3. **Interpret readiness correctly (the one operating rule that matters).** `readiness == OWNER_REVIEW_REQUIRED` means
   *"the measurement capability is exercisable and honestly evidenced, and the package is ready for the owner to
   review."* It does **not** mean ready-to-scale or ready-to-send. `readiness == NOT_READY` is the fail-closed state on
   any incomplete category or un-recorded smoke. **No third, higher state exists.**
4. **The owner decision is out of scope here.** Reviewing the §6 blockers and deciding ROAS Pass / Scale Ready is the
   **owner's** job at PR/PILOT (doc §23) — not this pack's, not this runbook's. `production_flag` is verified STILL OFF
   at owner sign-off.

---

## 3. Verify

### 3.1 The 18 P0 smokes (the whole matrix, each recorded)

All 18 bound smoke ids **PASS** (4 nodes each = 72/72 evidence-leg nodes), each recorded with a masked
`correlation_id` + `evidence_id`. The 3 proposed smokes were **executed**, not waived
(`SMOKE_RESULTS.md`, M6-P2004):

- Owner `SMK-001…015` — PASS 4/4 each (event-registry reject, consent fail-closed, dedup, quote≠revenue,
  draft≠verified, full attribution → dashboard, missing-source HOLD, CRM opt-out, recall/sale-lock FAIL/HOLD,
  Data-Mart-not-trigger, learning-hold, no-approval-no-scale, live/comment/Messenger trace, Diamond referral
  no-commission, quote-shown-as-revenue Fail).
- Proposed `SMK-016` outbox retry → dead-letter · `SMK-017` hash policy → no raw PII on external payload/log ·
  `SMK-018` post-verify correction → adjustment record (not mutation). PASS 4/4 each — **executed**.

Each evidence leg asserts 4 nodes: (1) recorded → terminal `OWNER_REVIEW_REQUIRED`; (2) un-run → `UNRUN` gap +
`NOT_READY`; (3) waiver scope (owner waiver stripped, proposed waiver counts); (4) `to_public()` masks the ids.

### 3.2 Full staged suite (count discipline)

```
# from 04-artifacts/impl/M6.2K/  (venv: 02-tester/.venv, python 3.12.13, pytest 8.4.2; cache-free, no shell redirection)
python -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider'])>"
# -> RC 0 ; passed=523 failed=0 skipped=0 error=0
python -c "<tally; pytest.main(['tests/smoke','-k','p0_evidence_pack','-p','no:cacheprovider'])>"
# -> RC 0 ; subset passed=72 failed=0
```

**Reconciliation: 523 = 425 carried (M6.2A–J final tree) + 26 coder evidence-package tests (→ 451 baseline) + 72
tester evidence-leg nodes (18 × 4).** All green; 0 failed / skipped / error. The isolated 18-leg run independently
confirms 72 passed. *(pytest's terminal summary is not reliably captured in this harness for a long run, so the total
was taken from an in-process `pytest_runtest_logreport` tally with `pytest.main() RC=0` and an empty failure list — see
`SMOKE_RESULTS.md` "On counting".)*

### 3.3 The in-scope fail gate — FAIL-007 does NOT trip (plus carried-gate cross-checks)

- **FAIL-007 / RULE-015** (the whole game for this slice): the pack **cannot overstate readiness** —
  `Readiness` has no Pass/Ready member; `_readiness` is fail-closed `NOT_READY` on any incomplete category or
  un-recorded smoke; an owner-smoke waiver is stripped; the 8 standing blockers are always disclosed; the posture
  snapshot is read-only; ids are masked on export. Boundary: **0** FAIL-007 breaches across **43 executed attacks**
  (35 DEFENDED / 8 OPEN_NONGATE armed-not-fired). Security: **0** raw PII / **0** real secrets across **234 files**
  (the 3 `sk-` regex hits are `risk-accept…` governance prose, not tokens — the risk-excluding high-entropy count is 0).
- **Carried gates re-confirmed hollow-proof** (boundary Group W, all DEFENDED): FAIL-001 (quote/draft ≠ verified
  revenue), FAIL-002 (consent fail-closed — CRM revenue `0` on opt-out / no consumed facts), FAIL-004
  (Diamond has no commission math — Finance owns it, RULE-019), FAIL-005 (neither `DataMart` nor `EvidencePack`
  exposes a trigger/scale/send/write verb, RULE-012). The full P0 evidence is **not hollow**.

---

## 4. Rollback (every change this slice made) — *acceptance check 1*

Staged-only; the rollback is trivial because M6.2K patched nothing.

| Change this slice made | Rollback |
|---|---|
| **New `app/measurement/evidence/` package** (`smoke_registry.py`, `categories.py`, `models.py`, `gap_blockers.py`, `pack_assembler.py`, `__init__.py`) | delete these files. |
| **New tests** (18 evidence-leg `tests/smoke/test_smk_0NN_p0_evidence_pack.py`, coder T1–T6, `tests/conftest.py` fixtures, `tests/TEST_MANIFEST.md`) | delete these files. |
| **Whole M6.2K staged tree** (`04-artifacts/impl/M6.2K/`) | delete the tree — the M6.2J tree is **untouched** (byte-identical carry-forward); baseline rollback returns to the M6.2J final state. |
| **Patched carried-forward file** | **none** — assembly-only; no carried file was modified. |
| **Migration** | **none** — doc §13 defines no evidence-pack table (RULE-018); nothing to unwind. |
| **Config flag** | **none** — no flag added; posture is read snapshot-only. |
| **Boundary / security analysis-only writes** (`boundary-reports/M6.2K_boundary.md`, `security-reports/M6.2K_security.md`, their harness/scanner scripts) | delete the reports/scripts; both roles recorded "no source modified" — no source rollback needed. |

No posture value is ever written, so there is nothing to revert on `global_gateway_state` / `production_flag` /
`external_send` — they were read-only throughout and stay BLOCKED / OFF / OFF.

---

## 5. Decision deltas & governance

### 5.1 Coder self-fixes (M6-P2002 §5) — 1 MAJOR + 2 NIT, all fixed; the two behavioral ones regression-tested

A read-only adversarial self-review (3 dimensions, each re-verified by an independent skeptic running the code) found
the **no-self-cert / no-Pass-Ready / scope / schema dimension CLEAN**, and closed:

- **(MAJOR — fail-open, the important one) the owner-waiver escape hatch was unscoped.** `SmokeResult.recorded`
  honored `waived=True` for **any** smoke, so a **mandatory owner smoke** (SMK-001…015) could be waived un-run —
  defeating the fail-closed readiness gate and vanishing from the honest gap list (FAIL-007 defeated for the 15
  mandatory smokes). **Fix:** the assembler (which knows the registry) strips a waiver on any non-proposed smoke ⇒ the
  owner smoke stays un-run ⇒ `UNRUN` gap + `NOT_READY`. **Regression added** (waiving SMK-001 keeps `NOT_READY` + a gap).
  The boundary adversary independently swept **all 15** owner smokes (B1) and confirmed the fix holds.
- **(NIT) the recorded posture snapshot was a mutable dict** on a frozen dataclass → wrapped in `MappingProxyType`
  (read-only); **regression added** (mutation raises `TypeError`).
- **(NIT) SMK-017 scenario/expected dropped `(CAPI/Offline)` + `platform`** vs SMOKE_REGISTER → restored **verbatim**
  (a string restore, no behavior change — so 26 new tests = 24 initial + **2** regressions, not 3).

### 5.2 The readiness-honesty discipline — the point of the slice (top-0.1% lens applied)

**Top-0.1% lens — what it changed:** the dominant failure mode of a *final-slice / evidence-pack* runbook is the
victory lap — letting "523 green, 18/18, 0 breaches" read as *readiness*. The lens moved the honesty to the front of
this document (banner + this section) instead of burying it under the green numbers, and made §2 step 3 the single
operating rule. The green matrix proves the **measurement capability is exercisable and honest**; it does **not** clear
anything to go live. Concretely, the pack **refuses to overstate**, and this is verified structurally, not asserted:

1. `Readiness` has **no PASS/READY/SCALE-READY member** — "Pass" is unrepresentable (boundary A1/A2, DEFENDED).
2. `_readiness` is **fail-closed** `NOT_READY` on any incomplete category **or** any un-recorded smoke (A3/A4/A5, B7).
3. An **owner-smoke waiver is stripped** (only a proposed smoke may be waived — B1 across all 15, DEFENDED).
4. The **8 standing blockers are always disclosed**, even in a fully complete pack (C1/C5, DEFENDED).
5. The **posture snapshot is read-only** and the assembler has **no** pass/ready/certify/enable/flip verb (A6, D2/D3/D5).

### 5.3 Slice-owned residuals (armed-not-fired; none channel-reachable; none trips FAIL-007) — routed to CODER

Every residual is the same shape: the assembler applies a **truthiness / trust** test where a **shape / type** test
would be stricter, and the enabling input arrives only from a **trusted upstream role** (TESTER-authored
`smoke_results`, PM-authored `evidence_refs`) or from **in-process code-exec** — never from a channel. These are
hardening before the pack is ever surfaced through a real endpoint, not open gates.

- **F-EVID-1 (primary) — assembler trusts truthiness/duck values, not a validated run-trace.** Three instances:
  a whitespace `status`/`correlation_id`/`evidence_id` reads as `recorded` (boundary B3); a duck object exposing
  `recorded=True` with no trace + `waived=False` is counted and never stripped (X1, the cleanest single-object
  launder); a row appended verbatim so its `smoke_id` (≠ `spec.smoke_id`) can mislabel/duplicate a displayed row (X2).
  **Fix:** pin each row to `spec.smoke_id`; require a `SmokeResult` whose stripped `status`+`correlation_id`+`evidence_id`
  are all non-blank before `recorded` is True.
- **F-EVID-2 / F-SEC-2K-2 — category completeness uses ref truthiness, not shape** (boundary E1). A whitespace ref
  marks a category COMPLETE — including category 9 **SECURITY_PRIVACY** itself. Caught downstream (security + judge
  re-check the actual ref content), not shipped. **Fix:** validate ref shape (stripped-non-blank / existence).
- **F-EVID-3 — no readiness↔standing-blocker positive floor** (boundary X5). A code-exec rebind of
  `pack_assembler.STANDING_GAP_BLOCKERS` empties the honesty payload while readiness still reads
  `OWNER_REVIEW_REQUIRED`. Code-exec-only. **Fix:** assert the 8 `STANDING_BLOCKER_IDS` are present (a positive floor).
- **F-EVID-4 / F-SEC-2K-1 (primary security) — `SmokeResult.status` exported unmasked** (boundary X7). `to_public()`
  masks the ids but emits `status` verbatim. No live leak today (TESTER sets `"PASS"`/`"FAIL"`), but it is the **same
  export-masking-scope family** as M6.2I **F-SEC-2I-2** (`messenger_thread_id` raw) and M6.2J **F-SEC-2J-2** (`buyer_ref`
  opt-in mask). **Fix:** enum-constrain `status` to `{PASS,FAIL}` or route through `mask()`. **Ratifies under the OPEN
  M6-OD-012** the pack already discloses.
- **Robustness (boundary X3)** — a truthy non-`SmokeResult` / non-`Mapping` input fails **closed by crash** (no pack
  emitted → nothing overstated), but as an unhandled exception. **Fix:** coerce/validate inputs, fail-closed to
  un-run/empty rather than raise.
- **D4 (module-global, carried every slice)** — mutating `config.PRODUCTION_FLAG` in-process makes the snapshot echo
  it; code-exec-only, no channel path writes `config`, and the flag never *declares* readiness. Owner-controlled
  integration hardens config immutability outside Module 6.

### 5.4 The 8 standing blockers carried inside every assembled pack (the honest payload — RULE-015 / FAIL-007)

This list is the reason the slice exists; it is never dropped. Per the coder's ONE readiness rule (PLAN §4.4,
adjudicated at the gate) these are **disclosed but do not by themselves force `NOT_READY`** — production stays BLOCKED
regardless, and weighing them is the **owner's** decision at PR/PILOT.

| # | Blocker id | What must clear before any real scale / send / auto-publish / surface | Owner |
|---|---|---|---|
| 1 | **M6-P1000** | M6.2A entry-judge verdict **BLOCKED** (not converted) | owner/judge |
| 2 | **M6-P1309** | M6.2D exit-judge verdict **BLOCKED** (not converted) | owner/judge |
| 3 | **M6.2G-SCALE** | ENTRY-001/003 real-scale conditions, the four M6-P1600 attestation true-ups, ENTRY-004 M5 DEBT-1…4 + the adversarial P4 re-gate, scale ACCESS-1/F-SCALE-\*, and **M6-OD-002/003/004/005** | owner |
| 4 | **M6.2H-LEARN** | **M6-OD-006** (safe range), **M6-OD-007** (content fill), F-LEARN-\* | owner |
| 5 | **M6.2I-FUNNEL** | **F-FUNNEL-4** (single-subject trace bind), F-SEC-2I-2 | owner |
| 6 | **M6.2J-GROWTH** | **F-GROWTH-1** (CRM subject-bind), **F-GROWTH-3** (`verified_rows` ORDER_VERIFIED choke), F-SEC-2J-\* | owner |
| 7 | **M6-OD-011** | Admin-endpoint authN/authZ (owner-controlled integration step) | owner |
| 8 | **M6-OD-012** | PII masking-scope decision (**OPEN**) — the F-SEC-2I-2 / F-SEC-2J-2 / F-SEC-2K-1 masking-scope family ratifies here | owner |

Governance chain still on disk (`04-artifacts/evidence/decisions/`): `M6-DEFER-FBC-M6.2D.json` (consent fail-open class
CLOSED + wired as a Scale-Gate RequiredInput, owner-confirmed 2026-08-07), `M6-DEFER-F1F2-M6.2B.json`,
`M6-DEFER-OD003-M6.2D.json`, and the `M6-OVERRIDE-M6P1000-STAGED` / `M6-OVERRIDE-M6P1309-STAGED` staging overrides — the
overrides **stage** the BLOCKED verdicts for the build; they do **not** convert them, which is why blockers 1–2 stand.

### 5.5 Forward gates & immutable posture

- **No new endpoint / access surface.** `EvidencePackAssembler` is a library returning a report object; a grep across
  `impl/M6.2K/app/` finds no `app/api/*` import or wiring of the assembler. When the owner package is eventually
  surfaced through an admin endpoint, that endpoint must authN/authZ the caller and export masking must be complete —
  both carried in the pack as **M6-OD-011** + **M6-OD-012**.
- **Hash policy (M6-OD-003)** is **N/A** for a send-less aggregator but honestly **surfaced**: a green SMK-017 proves
  only the **fail-closed hashing mechanism** (raw allow-list empty, `HASH_POLICY_RATIFIED=False`, every identity value
  hashed, raw branch unreachable) — **not** owner ratification of a send policy, which stays OPEN inside `M6.2G-SCALE`.
- **Immutable posture:** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
  `SCALE_MODEL_RATIFIED`/`SCALE_EXECUTION_ENABLED`/`HASH_POLICY_RATIFIED`/`LEARNING_AUTOPUBLISH_ENABLED` = `False`,
  `live_migrations=false`. Untouched; they stay OFF through M6.2K and into PR/PILOT.

---

## 6. Changelog delta — *acceptance check 2*

| Kind | Delta this slice introduced |
|---|---|
| **Code (staged, new)** | `app/measurement/evidence/` package: `smoke_registry.py`, `categories.py`, `models.py` (`Readiness` enum w/ no Pass/Ready member; `to_public()` masks ids), `gap_blockers.py` (8 standing blockers), `pack_assembler.py` (fail-closed, no-self-cert), `__init__.py`. |
| **Tests (staged, new)** | 18 evidence-leg `tests/smoke/test_smk_0NN_p0_evidence_pack.py` (72 nodes) + coder T1–T6 + `tests/conftest.py` fixtures + `tests/TEST_MANIFEST.md`. Suite total **425 → 523** (+26 coder, +72 tester legs). |
| **Migration** | **none** (RULE-018 — no evidence-pack table exists in doc §13). |
| **Config flag** | **none**; posture is read snapshot-only. |
| **Carried file patched** | **none** (assembly-only). |
| **Contract** | **M6-CTR-025** DRAFT_LOCKED — satisfied for M6.2K (the assembled pack IS the deliverable); not MISSING, so no harmonization prompt fires. |
| **Owner decisions** | none newly opened by this slice; the pack **surfaces** the standing set (M6-OD-002/003/004/005, OD-006/007, OD-011, OD-012) inside its blocker list. **M6-OD-012** is the ratification point for the F-SEC-2I-2 / F-SEC-2J-2 / F-SEC-2K-1 masking-scope family. |
| **Governance verdicts** | `M6-P1000` + `M6-P1309` **remain BLOCKED** (not converted), reaffirmed and carried inside the pack. |
| **Posture** | unchanged — `BLOCKED / OFF / OFF`, all flags `False`. |
| **Readiness** | assembled pack = **`OWNER_REVIEW_REQUIRED`** (terminal); no Pass/Ready declared. |

---

## 7. Handoff

- **Immediate next (JUDGE, fresh session): M6-P2009 `M6_2K_SLICE_GATE_JUDGE`.** Reads the evidence index + the
  assembled pack and checks the 22 exit-gate legs: pack ready for review; SMK-001…015 + proposed 016/017/018 recorded;
  every-prompt evidence (items 20/21 close once this docs prompt + the judge run); rollback (§4). Judges never modify
  what they judge; the verdict comes strictly from the evidence files. See §8.
- **Then: PR/PILOT — M6-P3000 `E2E_CHAIN_REVIEW`** (ANALYST_ARCHITECT), the owner sign-off flow (doc §23), where
  `production_flag` is verified **STILL OFF** at sign-off. Nothing in M6.2K authorizes that flip.
- **CODER (hardening before any real surface):** close the F-EVID-1 family (pin rows to `spec.smoke_id`; require
  shape-valid `SmokeResult` before `recorded`), F-EVID-2 / F-SEC-2K-2 (validate ref shape), F-EVID-3 (positive
  standing-blocker floor), F-EVID-4 / F-SEC-2K-1 (enum/mask `status`), and the X3 robustness coerce. None is
  channel-reachable; all are trusted-input / code-exec-only.
- **OWNER (at PR/PILOT):** weigh the **8 standing blockers** (§5.4) and the OPEN owner decisions
  (M6-OD-002/003/004/005, OD-006/007, OD-011, OD-012); the masking-scope family ratifies together under **M6-OD-012**.
  Declaring ROAS Pass / Scale Ready is owner-only and is not done anywhere in this build.
- **Posture carried forward unchanged:** `BLOCKED / OFF / OFF`, all flags `False`; `M6-P1000` + `M6-P1309` BLOCKED.

---

## 8. Pointers for the slice-gate Judge (M6-P2009)

1. **Read order:** `M6_2K_EVIDENCE_INDEX.md` → the 10-category map (§4) → the honest blocker list (§6) → the 7 band
   JSONs (M6-P2000…2006) → the two review reports (`M6.2K_boundary.md`, `M6.2K_security.md`) → `SMOKE_RESULTS.md` →
   `IMPLEMENTATION_NOTES.md` (rollback). This runbook is the operate/verify/rollback + changelog/handoff companion; the
   22-leg exit-gate map is index §5.
2. **What is proven (executed):** the full P0 matrix (18 smokes, 3 proposed **executed** not waived) re-ran green —
   72/72 evidence-leg nodes, full staged suite **523 passed / 0 failed**, each smoke recorded with a masked
   `correlation_id` + `evidence_id`; all 10 doc §22 categories complete with mandatory content; boundary **0** FAIL-007
   breaches / 43 attacks; security **0** raw PII / **0** secrets / 234 files; **no new access surface**.
3. **What the pack refuses to say:** it never declares ROAS Pass / Scale Ready and has **no method** to; readiness tops
   at `OWNER_REVIEW_REQUIRED`; the owner-waiver escape hatch (the MAJOR fail-open) is **closed**; `production_flag=OFF`
   and gateway/external-send verified still OFF into PR/PILOT.
4. **What is NOT yet closed:** exit items **20 & 21** are PENDING purely because this docs prompt (M6-P2008) and the
   judge (M6-P2009) are the last two to run — **not** because of any defect. Item 1 is SUPPORTED (staged): the pack is
   ready for owner review; the sign-off itself is owner-only.
5. **The finding to weigh hardest — the 8 standing blockers (§5.4).** This is a readiness *package*; its integrity is
   whether it discloses everything still open. It does: the two BLOCKED verdicts + every M6.2G/H/I/J forward condition
   + OD-011/012 are carried inside the pack itself. The slice-owned residuals (§5.3, primary **F-EVID-1** run-trace
   trust and **F-SEC-2K-1** unmasked `status`) are armed-not-fired hardening — none channel-reachable, none tripping
   FAIL-007.
6. **One evidence-report internal inconsistency to note (not a defect in the pack):** in `M6.2K_boundary.md`, the
   authoritative header counts reconcile — **43 recorded = 35 DEFENDED + 8 OPEN_NONGATE** (35 + 8 = 43) — but the
   **Group X sub-heading** reads "4 DEFENDED, 4 OPEN_NONGATE" while its rows are actually **3 DEFENDED / 5
   OPEN_NONGATE** (X1, X2, X3, X5, X7 are OPEN_NONGATE; X4, X6, X8 DEFENDED), and the §4 title "Attack log (35
   outcomes)" is the DEFENDED count, not the 43-row total. The overall verdict (0 FAIL-007 breaches) is unaffected; the
   8 OPEN_NONGATE residuals are the F-EVID-1…4 + X3 + D4 family already routed to CODER.
7. **Boundary integrity of this docs prompt (M6-P2008):** `analysis_only` — it read the band evidence and wrote only
   this runbook + its evidence JSON. It touched no `04-artifacts/state/`, marked no ledger row, modified no file it
   documented, computed no verdict, and declared no readiness. `global_gateway_state=BLOCKED`, `production_flag=OFF`,
   `external_send=OFF` — untouched.
