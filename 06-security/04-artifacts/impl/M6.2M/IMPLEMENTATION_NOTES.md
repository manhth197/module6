# M6.2M IMPLEMENTATION NOTES — Evidence Authenticity (M6-OD-013) (STAGED)

**Prompt**: M6-P2202 (`M6_2M_CODER_IMPLEMENT`) · **Role**: CODER · **Mode**: `implement` · **Gate**: EVIDENCE_GATE
**Follows**: [PLAN.md](PLAN.md) (M6-P2201). Built item-by-item; **no plan-deltas**. **Posture unchanged & immutable**:
`config.py` byte-identical to M6.2L; `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all
scale/hash/learning flags `False`, `live_migrations=false`. No self-cert (RULE-015), no Pass/Ready, no
migration/flag/table (migrations stay `0001–0012`, RULE-018), no external send, no raw PII.

> **Status: coder self-reported PASS** (the runner gate + JUDGE decide, RULE-015). The two M6-OD-013 twin
> authenticity holes are closed and proven by regression; the suite is green (**568 passed**), the evidence-pack
> area and the 18 P0-pack smokes stay green, and an edge-case probe confirmed the twin is fail-closed and the
> SMK-024 regression is discriminating.

## 1. Staging model — cumulative carry-forward

The whole **M6.2L** tree (app + 12 migrations + full carried suite incl. the 18 P0 smokes + the M6.2L regressions +
the TESTER-authored SMK-019..023) was carried byte-identical into `04-artifacts/impl/M6.2M/` (caches excluded;
M6.2L `PLAN.md`/`IMPLEMENTATION_NOTES.md` not carried; M6.2M `PLAN.md` kept, this file added). Baseline verified
green **BEFORE any patch: 561 passed**, parity with the M6.2L collect (both 561). Final suite: **568 passed** (561
carried + 7 new CODER regressions). Subprocess counts; no skips.

## 2. Change set (all under `04-artifacts/impl/M6.2M/`)

| Fix | File | Change | Kind |
|---|---|---|---|
| FIX-2 | `app/measurement/evidence/models.py` | `+_nonblank(v)` helper; `SmokeResult.recorded` requires **stripped-non-blank** status/correlation_id/evidence_id (not raw truthiness) | code |
| FIX-2 | `app/measurement/evidence/pack_assembler.py` | `_smokes` **normalizes** whitespace-only status/correlation_id/evidence_id → `None` (defense-in-depth; mirrors the waiver-strip) | code |
| FIX-1 | `app/measurement/evidence/pack_assembler.py` | `_ref_valid` **docstring**: the "residual" note → authenticity now **proven with a staged allowlist (SMK-024)**; only owner-registry population remains. **No logic change.** | doc |
| — | **new** `tests/test_m6_2m_ref_authenticity.py`, `tests/test_m6_2m_smoke_authenticity.py` | CODER leg regressions | test |

**FIX-1 carries no `_ref_valid` logic change**: the ref-side oracle consultation already lands in the carried M6.2L
base (`_ref_valid`: `if known_refs is not None and r not in known_refs: return False`; `assemble(..., known_refs=…)`
threads it) — the M6.2L impl-review "forward seam". So leg-1's exit behaviour is already present; M6.2M **proves** it
(SMK-024) and updates the now-stale docstring. The **staged known-refs oracle is a concrete allowlist** (a `set`)
supplied via the existing `known_refs` parameter — **no new registry code**; the real issued-refs registry is
owner-populated (out of scope). **No new migration/flag.** **No** carried TESTER smoke edited. **No** change to the
M6.2L forgery/collision/ROAS-lock fixes.

## 3. Tests → leg → smoke mapping (TESTER authors the official SMK-024/025 in M6-P2203)

| CODER regression (new) | Proves | Leg | Smoke |
|---|---|---|---|
| `tests/test_m6_2m_ref_authenticity.py` | reconstructed-but-not-issued canonical ref ⇒ category MISSING under an allowlist; no-oracle ⇒ no regression; fully-issued ⇒ COMPLETE (discriminating) | **1** | SMK-024 |
| `tests/test_m6_2m_smoke_authenticity.py` | whitespace/fake-but-nonblank SmokeResult ⇒ recorded False ⇒ UNRUN gap ⇒ NOT_READY; `_smokes` normalizes → None; genuine ⇒ recorded | **2** | SMK-025 |

The OFFICIAL smokes `tests/smoke/test_smk_024_*.py` / `test_smk_025_*.py` + their recorded correlation_id/evidence_id
are the TESTER's (M6-P2203/2204). No self-run / self-certify (RULE-015).

## 4. Backward-compat + edge-case verification

- **No carried test broken** by the `recorded` tightening: `all_smokes_recorded` / `make_smoke_result` use real
  non-blank values (still recorded); un-run cases pass `None` (still un-recorded). The 18 P0-pack smokes +
  `test_pack_never_declares_pass_or_ready` + the M6.2K waiver-strip tests + the M6.2L regressions + SMK-019..023 all
  stay green (568 passed; evidence-pack area re-run green).
- **Edge-case probe** (throwaway snippet against the running code) confirmed: `_nonblank` is fail-closed for
  `None`/int/whitespace and True only for a stripped-non-blank string; a non-string `status` ⇒ not recorded; a
  proposed-smoke owner waiver still records; a **partial** blank (one whitespace field of three) ⇒ not recorded;
  `_smokes` normalizes whitespace → `None` so `to_public` masks `None` safely and readiness ⇒ `NOT_READY`; and
  SMK-024 is **discriminating** — the target category is COMPLETE iff its ref is in the allowlist (`w/o-issue=False,
  w/issue=True`), so the authenticity assertion is non-vacuous.

## 5. Scope & governance (unchanged)

In scope built: exactly the two M6-OD-013 twin items — ref-side authenticity **proof** (behaviour present in the
base; regression + docstring) and the smoke-side `recorded`/`_smokes` stripped-non-blank tightening + regressions.
OUT (untouched): populating the **real** known-refs registry (owner integration step); any change to the M6.2L
fixes; flipping any flag. Boundary intact: the evidence pack is a read-only owner-review input; the assembler still
exposes no pass/ready/certify/flag-flip method and readiness tops at `OWNER_REVIEW_REQUIRED` (RULE-015);
`known_refs` entries + `SmokeResult` fields are governance ids (no PII; correlation/evidence ids still masked on
export). `M6-P1000`/`M6-P1309` stay BLOCKED and remain in the assembled pack; the G/H/I/J + OD-011/012 forward
conditions remain in the standing-blocker floor. Doc-sync flag (non-blocking, carried): `M6-OD-013`/`M6-OD-014` are
referenced by slice specs but not yet rows in `DECISION_REGISTER.md` (00-spec is read-only to the coder).

## 6. Rollback

Staged only — baseline rollback = delete the `04-artifacts/impl/M6.2M/` tree (M6.2L untouched). Per item: revert
`models.py` (drop `_nonblank` + restore the raw-truthiness `recorded`) and `pack_assembler.py` (drop the `_smokes`
whitespace-normalize; restore the `_ref_valid` docstring) to their M6.2L bytes — FIX-1 is a scoped docstring-only
revert, FIX-2 a scoped logic revert. The 2 new CODER test files roll back by deletion. No migration to unwind (none
added); every change is additive or a fail-closed tightening, so a revert restores exact prior behaviour.
