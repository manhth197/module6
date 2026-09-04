# M6.2M PLAN — Evidence Authenticity (M6-OD-013) (STAGED, plan-only)

**Prompt**: M6-P2201 (`M6_2M_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code) · **Gate**: EVIDENCE_GATE
**Slice**: M6.2M — close the **M6-OD-013 authenticity residual** disclosed at the M6.2L re-judge, as a **cumulative
superset** of M6.2L under `04-artifacts/impl/M6.2M/`. Two twin holes: **ref-side** (a reconstructed canonical
`ev::{cat}::{key}` that is slot-correct but was never issued) and **smoke-side** (a whitespace / fake-but-nonblank
`SmokeResult` field marking a mandatory smoke "recorded"). Proven by regression evidence with a **staged** known-refs
oracle; the real issued-refs registry stays **owner-populated** (out of scope).

> **Posture (immutable, this slice flips nothing):** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
> `external_send=OFF`; all scale/hash/learning flags `False`; `live_migrations=false`; `config.py` unchanged. No
> self-cert (RULE-015), no Pass/Ready, no migration/flag/table (RULE-018), no external send, no raw PII. Status here
> is **coder self-reported**; the runner gate + JUDGE (M6-P2209) decide.

Implementation target **LOCKED**, **M6-OD-011 DECIDED 2026-07-23** (verified:
`04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json`). Ledger verified: **M6-P2201 = RUNNING** (row 211),
dependency **M6-P2200 = SIGNED** (entry gate PASS). Doc working mode (extract L463–472): *do not guess; read the
repo first; reuse conventions + test patterns; minimal change; output files-touched + tests + commands + PASS/FAIL +
rollback*. Single in-scope contract **M6-CTR-025** (Evidence package) = DRAFT_LOCKED.

---

## 0. Top-0.1% lens — the honest delta (verified against the carried M6.2L code, not assumed)

The lens forced one load-bearing correction to how this slice is framed, and confirmed the backward-compat guard:

- **[honesty — the ref-side mechanism ALREADY landed in the carried base]** `pack_assembler._ref_valid` in the
  M6.2L tree **already consults the oracle**: line 76 `if known_refs is not None and r not in known_refs: return
  False`, and `assemble(..., known_refs=None)` threads it (default None → the M6.2L slot-correctness bar, no
  regression). This wiring landed as the M6.2L impl-review "forward seam" (documented in M6.2L IMPLEMENTATION_NOTES
  §5 + the `_ref_valid` NOTE). So **leg-1's exit behaviour is already satisfied by the base** — M6.2M must NOT
  pretend to newly "wire" it. M6.2M's ref-side deliverable is therefore the **SMK-024 regression that PROVES it**
  (a reconstructed-but-not-issued canonical ref → category MISSING; no-oracle → no regression) + a one-line
  **docstring-honesty** update replacing the now-closed "residual" note. No `_ref_valid` **logic** change.
- **[the genuine new code is the smoke-side twin]** `SmokeResult.recorded` (`models.py:47`) uses **raw truthiness**
  `bool(self.status) and bool(self.correlation_id) and bool(self.evidence_id)` → a whitespace field (`"  "`) is
  truthy → a mandatory smoke can be marked **recorded** with fake-but-nonblank content (FAIL-007 hole, the doc "vá
  cả hai một lượt" twin of B2). This is real, new work (leg-2).
- **[backward-compat guard — cannot force the oracle by default]** the 18 TESTER `tests/smoke/
  test_smk_0XX_p0_evidence_pack.py` + `test_pack_never_declares_pass_or_ready.py` call `assemble(...)` **without**
  a `known_refs` oracle and require `OWNER_REVIEW_REQUIRED` (all categories COMPLETE). Making the oracle mandatory
  would flip all of them to `NOT_READY` — a self-inflicted regression on un-editable TESTER smokes. → the oracle
  stays **opt-in** (authenticity is proven WHEN an allowlist is supplied); the default path keeps the M6.2L
  slot-correctness bar. This is exactly what SMK-024's expected column states ("with no allowlist … no regression").
- **[confirmed, unchanged]** the `recorded` tightening is backward-compatible: every carried
  `SmokeResult(status="PASS", correlation_id="corr_…", evidence_id="ev_…")` (conftest `all_smokes_recorded` /
  `make_smoke_result`) is stripped-non-blank → still recorded; every un-run case passes `None` → still un-recorded.
  Verified by reading the fixtures + all `SmokeResult(`/`.recorded` call sites.

The lens **confirmed** (unchanged): no scope beyond the two in-scope items; the M6.2L forgery/collision/ROAS-lock
fixes are carried forward untouched; measure/record-only; no migration/flag/table (RULE-018); the slice STRENGTHENS
FAIL-007 + RULE-015. `known_refs`/`SmokeResult` values are governance ids, never PII.

---

## 1. Repo summary & staging model (cumulative carry-forward)

- **Base**: the whole **M6.2L** tree (app + 12 migrations `0001–0012` + full carried suite incl. the 18 P0 smokes +
  the 21 M6.2L regressions). M6.2M is a **superset**: carry M6.2L byte-identical, apply the smoke-side twin + the
  ref-side docstring touch + 2 CODER regressions. (The carry runs in **M6-P2202 implement**, not this plan prompt.)
- **Stack** (locked target): Python 3.12, `framework=""` (framework-neutral pure functions), `pytest -q`, stdlib
  only; in-memory staged stores; physical DB/HTTP bind = owner M6-OD-011 step.
- **Layer touched** (ARCH_BASELINE): **Evidence** only (`evidence/models.py`, `evidence/pack_assembler.py`). No new
  layer/contract object; no other layer touched.
- **Baseline discipline (M6-P2202)**: verify green **before** any patch (subprocess `pytest`, parity with the M6.2L
  collect), then reach green again after the twin + regressions; **no skips**; actual `N passed` is the count.

---

## 2. The 2 twin fixes — one item per exit-gate leg + smoke (minimal change, mapped, rollback per item)

Legend: **Leg** = M6.2M.md "Exit gate checks" number · **Smoke** = SMOKE_REGISTER id · file refs are M6.2L-current.

### FIX-1 — Ref authenticity (M6-OD-013 ref-side)  → **Leg 1 · SMK-024 · RULE-015 / FAIL-007**

- **SMK-024 (verbatim)**: *Evidence pack assembled with a known-refs allowlist + a ref that is shape-valid, uniquely
  used, correctly (category,key)-bound, but NOT in the allowlist (canonical-string reconstruction) → that category
  reads MISSING (authenticity, not just slot-correctness); with no allowlist the M6.2L slot-correctness bar still
  holds (no regression).*
- **Current (carried M6.2L)**: `pack_assembler._ref_valid` **already** rejects a slot-correct ref not in the oracle
  (`:76 if known_refs is not None and r not in known_refs: return False`); `assemble(..., known_refs=None)` keeps
  the default slot-correctness bar. So the **leg-1 behaviour exists in the base**.
- **Minimal change** (no logic change; doc + proof only):
  1. `evidence/pack_assembler.py` — update the `_ref_valid` **docstring** "NOTE (residual, gated on M6-OD-013)" to
     state the authenticity path is now **proven with a staged oracle (SMK-024)**; the remaining owner item is only
     *populating the real issued-refs registry* (integration step). No behavioural change.
  2. The **staged known-refs oracle** is a concrete allowlist (a `set`/`frozenset` of issued canonical refs) passed
     via the existing `known_refs` parameter — **no new registry code**; the real registry is owner-populated
     (explicitly out of scope). The CODER regression (below) builds the staged allowlist inline from the genuine
     issued refs.
- **CODER regression**: `tests/test_m6_2m_ref_authenticity.py` — (a) allowlist = the genuine issued refs **minus one
  target slot**; the pack carries the correctly-reconstructed canonical ref for that slot ⇒ that category MISSING,
  the other 9 COMPLETE, pack NOT_READY (authenticity beyond slot-correctness); (b) the **same** pack with **no**
  `known_refs` ⇒ all COMPLETE / OWNER_REVIEW_REQUIRED (no regression); (c) a fully-issued allowlist ⇒ all COMPLETE
  (non-vacuous control).
- **Rollback**: revert the `_ref_valid` docstring to its M6.2L bytes; delete the regression file. No logic to unwind.

### FIX-2 — Smoke authenticity twin (M6-OD-013 smoke-side)  → **Leg 2 · SMK-025 · RULE-015 / FAIL-007**

- **SMK-025 (verbatim)**: *SmokeResult for a mandatory owner smoke carries whitespace / fake-but-nonblank
  status/correlation_id/evidence_id → recorded() is False (stripped-non-blank required, not raw truthiness); the
  mandatory smoke stays un-recorded → pack NOT_READY.*
- **Current (carried M6.2L)**: `SmokeResult.recorded` (`models.py:47`) = `bool(self.status) and
  bool(self.correlation_id) and bool(self.evidence_id)` — a whitespace string is truthy ⇒ **recorded** on
  fake-but-nonblank content (the FAIL-007 twin of the ref-side hole).
- **Minimal change** (2 files, fail-closed tightening):
  1. `evidence/models.py` — `SmokeResult.recorded` requires each of `status` / `correlation_id` / `evidence_id` to
     be a **stripped-non-blank** string (a small `_nonblank(v) = isinstance(v, str) and v.strip() != ""` helper),
     not raw truthiness. Waiver semantics (proposed-only) unchanged.
  2. `evidence/pack_assembler.py` — `_smokes` **normalizes** any whitespace-only `status`/`correlation_id`/
     `evidence_id` to `None` (defense-in-depth + clean `to_public`), mirroring the existing waiver-strip pattern, so
     a whitespace field cannot masquerade downstream. Readiness/gap paths already read `.recorded`, so a stripped
     mandatory smoke stays un-recorded → `UNRUN_SMOKE` gap → `NOT_READY` (fail-closed).
- **Backward-compat (verified)**: `all_smokes_recorded` / `make_smoke_result` use real non-blank values → still
  recorded; the 18 P0-pack smokes + `test_pack_never_declares_pass_or_ready` (un-run cases pass `None`) stay green;
  the M6.2K waiver-strip tests (SMK-001 owner-waiver, proposed-waiver) unaffected (waiver path unchanged).
- **CODER regression**: `tests/test_m6_2m_smoke_authenticity.py` — a mandatory owner smoke (e.g. `M6-SMK-001`) whose
  `SmokeResult` carries whitespace `status`/`correlation_id`/`evidence_id` ⇒ `recorded is False`, an `UNRUN_SMOKE`
  gap for it, pack `NOT_READY`; a genuinely-recorded result stays recorded (non-vacuous control); `to_public`
  shows the normalized (non-whitespace) values.
- **Rollback**: revert `models.py` (`recorded`) + `pack_assembler.py` (`_smokes` normalize) to their M6.2L bytes;
  delete the regression file.

---

## 3. Change-set summary (files touched — minimal, all under `04-artifacts/impl/M6.2M/`)

| Fix | File | Change | Kind |
|---|---|---|---|
| FIX-1 | `app/measurement/evidence/pack_assembler.py` | `_ref_valid` docstring: "residual" → "proven via staged oracle (SMK-024)"; real-registry population = owner | doc |
| FIX-2 | `app/measurement/evidence/models.py` | `SmokeResult.recorded` requires stripped-non-blank status/correlation_id/evidence_id | code |
| FIX-2 | `app/measurement/evidence/pack_assembler.py` | `_smokes` normalizes whitespace-only fields → None (defense-in-depth) | code |
| — | **new** `tests/test_m6_2m_ref_authenticity.py`, `tests/test_m6_2m_smoke_authenticity.py` | CODER leg regressions | test |

**No new migration** (no evidence-pack table; RULE-018). **No new config flag.** **No** carried TESTER smoke edited.
**No** change to the M6.2L forgery/collision/ROAS-lock fixes (carried unchanged). Migrations stay `0001–0012`.

## 4. Tests → leg → smoke mapping (TESTER authors the official SMK-024/025 in M6-P2203)

| CODER regression (new) | Proves | Leg | Smoke |
|---|---|---|---|
| `tests/test_m6_2m_ref_authenticity.py` | reconstructed-but-not-issued canonical ref ⇒ category MISSING under an allowlist; no-oracle ⇒ no regression; fully-issued ⇒ COMPLETE | **1** | SMK-024 |
| `tests/test_m6_2m_smoke_authenticity.py` | whitespace/fake-but-nonblank SmokeResult ⇒ recorded False ⇒ UNRUN gap ⇒ NOT_READY; genuine ⇒ recorded | **2** | SMK-025 |

Legs 3–4 (SMK-024/025 executed OR owner-waived), 5 (all evidence schema-valid), 6 (judge PASS), 7 (rollback
documented — this §2/§6) are completed by the TESTER (M6-P2203/2204), PM (M6-P2207) and JUDGE (M6-P2209). The
**official** smokes `tests/smoke/test_smk_024_*.py` / `test_smk_025_*.py` are the TESTER's to author + run
(RULE-015; no self-run/self-certify).

## 5. Scope & governance boundary

- **In scope (built here)**: exactly the two M6-OD-013 twin items — ref-side oracle **proof** (behaviour present in
  the base; regression + docstring) and smoke-side `recorded`/`_smokes` stripped-non-blank tightening + regressions.
- **Out of scope (untouched)**: populating the **real** known-refs registry (owner-provided integration step); any
  change to the M6.2L forgery/collision/ROAS-lock fixes; flipping any flag. Nothing here resolves an OPEN owner
  decision (M6-OD-013 is the in-scope residual this slice closes with evidence; the real-registry population is the
  forward owner step, same pattern as M6-OD-011).
- **Boundary intact**: measure/record-only — the evidence pack is a read-only owner-review input; no
  pricing/order-state/CRM-send/commission; the assembler still exposes no pass/ready/certify/flag-flip method
  (RULE-015); readiness still tops at `OWNER_REVIEW_REQUIRED`. `M6-P1000`/`M6-P1309` stay BLOCKED and remain in the
  assembled pack; the G/H/I/J + OD-011/012 forward conditions remain in the standing-blocker floor.
- **No raw secrets/PII**: `known_refs` entries + `SmokeResult` fields are governance ids; correlation/evidence ids
  are still masked on export (`to_public`).
- **Governance doc-sync (non-blocking, carried)**: `M6-OD-013`/`M6-OD-014` are referenced by slice specs but not yet
  rows in `DECISION_REGISTER.md` — operator/analyst hygiene (00-spec is read-only to the coder), not a blocker.

## 6. Verification plan for M6-P2202 (commands + PASS/FAIL checklist + rollback)

**Commands** (implement prompt runs these; subprocess `pytest`, no cache):
- carry M6.2L → `04-artifacts/impl/M6.2M/` (exclude caches; keep this `PLAN.md`), then baseline
  `python -m pytest -q -p no:cacheprovider` → record `N passed`, parity with the M6.2L collect **before** any patch.
- apply FIX-1 (docstring) + FIX-2 (recorded + _smokes) + the 2 regressions; re-run → green, no skips.
- confirm migrations still `0001–0012`; `config.py` byte-identical to M6.2L; clean `__pycache__`/`.pytest_cache`;
  PII scan the changed files.

**PASS/FAIL checklist** (each maps to a leg): FIX-1 not-issued canonical ref ⇒ MISSING under allowlist, no-oracle ⇒
no regression ✓/✗ · FIX-2 whitespace SmokeResult ⇒ recorded False ⇒ NOT_READY, genuine ⇒ recorded ✓/✗ · full suite
green (baseline ≤ final) ✓/✗ · 18 P0-pack smokes + M6.2L regressions still green ✓/✗ · posture BLOCKED/OFF/OFF
unchanged, no new migration/flag, no TESTER smoke edited ✓/✗.

**Rollback** (per §2 per-item, + baseline): staged-only — baseline rollback = delete the `04-artifacts/impl/M6.2M/`
tree (M6.2L untouched). Per item: revert `models.py` / `pack_assembler.py` to their M6.2L bytes (FIX-1 is a scoped
docstring-only revert; FIX-2 a scoped logic revert), delete the 2 new test files. No migration to unwind (none
added); every change is additive or a fail-closed tightening, so a revert restores exact prior behaviour.

---

*Plan-only: this document writes no application code, adds no migration/flag, sends nothing, scales/publishes
nothing, resolves no owner decision, and flips no flag. `global_gateway_state=BLOCKED`, `production_flag=OFF`. The
two twin fixes are proven by regression evidence in M6-P2202+; the runner gate + JUDGE decide (RULE-015).*
