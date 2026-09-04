# M6.2M — Slice Runbook — Evidence Authenticity (M6-OD-013 twin)

> **Status: STAGED — proves the M6-OD-013 authenticity *mechanism* with regression evidence; it flips nothing.**
> M6.2M closes the **M6-OD-013 authenticity residual** disclosed at the M6.2L re-judge with a **twin fix** to the
> evidence assembler: **FIX-1 (ref-side)** — the `known_refs` oracle rejects a shape-valid, correctly (category,key)-bound,
> unique ref that was **never issued**, defeating canonical-string reconstruction; **FIX-2 (smoke-side)** — `SmokeResult.recorded`
> now requires **stripped-non-blank** status/correlation_id/evidence_id, closing the F-EVID-1 whitespace launder. Both
> boundary-verified, **0** FAIL-007 breaches; carried M6.2L B2/B3/B4 (forgery/collision/revenue-lock) re-verified intact.
>
> **Read the bounding honestly (this is the point of the slice):**
> 1. **FIX-1 is a *proof* + docstring, not net-new logic.** The `known_refs` oracle already landed in the M6.2L base
>    (the impl-review forward seam); M6.2M is the SMK-024 proof that it *discriminates* + a stale-docstring update. **No
>    `_ref_valid` logic change.**
> 2. **M6-OD-013 is *mechanism*-closed, not *production*-closed.** The default **no-allowlist** path still passes
>    canonical reconstruction; production ref-authenticity needs the **owner to populate the real issued-refs registry**
>    and pass it as `known_refs` — the disclosed integration step (out of scope here).
> 3. **FIX-2 closes the *whitespace* variant only.** The F-EVID-1 **duck-type** variant (a duck object with
>    `recorded=True` + `None` fields) remains OPEN (§5.4), routed to CODER.
>
> Posture immutable and untouched: `config.py` **byte-identical to M6.2L/M6.2K**; `global_gateway_state=BLOCKED`,
> `production_flag=OFF`, `external_send=OFF`, all scale/hash/learning flags `False`, `live_migrations=false`; no
> table/migration/flag (migrations stay `0001–0012`). The assembled pack still tops at `OWNER_REVIEW_REQUIRED`;
> `M6-P1000` + `M6-P1309` remain **BLOCKED (not converted)**. Next: slice-gate Judge **M6-P2209**.
>
> Evidence at a glance: full staged suite **575 passed / 0 failed / 0 skipped / 0 error, rc 0**; both smokes SMK-024/025
> PASS (7/7 nodes), masked `correlation_id` + `evidence_id`; boundary **0** FAIL-007 breaches / 25 outcomes; security
> **0** raw PII / **0** secrets / 248 files.

| Field | Value |
|---|---|
| Slice | **M6.2M** — Evidence Authenticity (M6-OD-013); post-pilot; depends on M6.2L; remediates the residual disclosed at the M6.2L re-judge (2026-09-03) |
| Prompt (this doc) | **M6-P2208** — `M6_2M_DOCS` (ANALYST_ARCHITECT, `analysis_only`, EVIDENCE_GATE) |
| Doc scope | close the M6-OD-013 authenticity residual left open by M6.2L (B2): ref-side canonical-string reconstruction + smoke-side SmokeResult truthiness twin |
| Rule / fail gate in scope | **RULE-015** (no self-cert) · **FAIL-007** (no-evidence / overstated readiness) |
| Contract | **M6-CTR-025** `Evidence package` DRAFT_LOCKED → satisfied (owned at M6.2K; this slice hardens the assembler) |

---

## 1. What this slice built (staged under `04-artifacts/impl/M6.2M/`)

M6.2M carries the **entire M6.2L tree byte-identical** (app + 12 migrations + full carried suite incl. SMK-019…023;
baseline verified green **before any patch: 561 passed**, parity with M6.2L) and patches **2 files** for the twin fix,
plus **2 new coder regression tests**. **No new migration, no new config flag, no new table** (RULE-018); `config.py`
byte-identical.

| Fix | Twin side | File | Change | Kind |
|---|---|---|---|---|
| **FIX-1** | M6-OD-013 ref-side | `evidence/pack_assembler.py` | `_ref_valid` **docstring** only: the "residual" note → authenticity now **proven with a staged allowlist (SMK-024)**; owner-registry population remains. **No logic change** — the oracle (`if known_refs is not None and r not in known_refs: return False`; `assemble(…, known_refs=…)`) already lands in the carried M6.2L base. | **doc** |
| **FIX-2** | M6-OD-013 smoke-side | `evidence/models.py` | `+_nonblank(v)` helper; `SmokeResult.recorded` requires **stripped-non-blank** status/correlation_id/evidence_id (not raw truthiness). | code |
| **FIX-2** | M6-OD-013 smoke-side | `evidence/pack_assembler.py` | `_smokes` **normalizes** whitespace-only status/correlation_id/evidence_id → `None` (defense-in-depth; mirrors the waiver-strip). | code |
| — | tests | `tests/test_m6_2m_ref_authenticity.py`, `tests/test_m6_2m_smoke_authenticity.py` | CODER leg regressions | test |

> **Honest scope of FIX-1 (surfaced, not buried):** leg-1's exit behaviour was **already present** in the M6.2L base
> (verified by the boundary as B2-6). So M6.2M's ref-side contribution is the **SMK-024 proof** that the mechanism
> discriminates (a category is COMPLETE iff its ref is in the allowlist) + a docstring update — **not** new logic. The
> **staged** `known_refs` oracle is a concrete allowlist (`set`) passed via the existing parameter; the **real**
> issued-refs registry is owner-populated (out of scope). The one real code change this slice makes is **FIX-2**.

---

## 2. Operate

M6.2M hardens the evidence assembler; there is no new operational action, and the assembler has **no `app/api` caller**
(grep-confirmed, boundary N5) — it is a read-only owner-review input.

1. **Ref authenticity is opt-in.** When the caller passes a `known_refs` allowlist, a reconstructed-but-un-issued
   canonical ref is REJECTED (category MISSING). **Without** an allowlist, the M6.2L slot-correctness bar still applies
   (no regression) — so today, with no real registry, the default path does not yet authenticate. The load-bearing
   operating step for production is the **owner populating the real issued-refs registry** and passing it as `known_refs`
   (M6-OD-013 integration).
2. **Smoke authenticity is always on.** A whitespace / fake-but-nonblank `SmokeResult` field no longer marks a mandatory
   smoke recorded — it stays un-recorded and the pack fails closed to `NOT_READY`.
3. **What stays impossible:** the assembler exposes no pass/ready/certify/flag-flip verb; readiness tops at
   `OWNER_REVIEW_REQUIRED`; nothing here is wired to act, send, or scale. `config.py` byte-identical to M6.2L.

---

## 3. Verify

### 3.1 The 2 official smokes (each proven by its smoke AND its coder regression)

Both bound smokes **PASS** (7/7 nodes = 3+4), each recorded with a masked `correlation_id` + `evidence_id`
(`SMOKE_RESULTS.md`, M6-P2204), executed (not owner-waived):

- **SMK-024 (ref-side)** 3/3 — with a staged allowlist omitting the DEDUP slot's ref, the correctly-reconstructed
  canonical ref is REJECTED → DEDUP MISSING → NOT_READY, all issued-ref categories COMPLETE; **no allowlist → no
  regression** (honest refs all COMPLETE); a fully-issued allowlist → all COMPLETE (**discriminating**: COMPLETE iff ref
  issued).
- **SMK-025 (smoke-side)** 4/4 — a whitespace/fake-but-nonblank `SmokeResult` on mandatory SMK-001 → `recorded()` False,
  UNRUN gap, NOT_READY; whitespace fields (each truthy, `bool("  ")==True`) → recorded False (authenticity, not raw
  truthiness); `_smokes` normalizes whitespace → None; genuine set still records → OWNER_REVIEW_REQUIRED (non-vacuous).

### 3.2 Full staged suite (count discipline)

```
# from 04-artifacts/impl/M6.2M/  (venv: 02-tester/.venv, python 3.12.13, pytest 8.4.2; cache-free, no shell redirection)
python -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider'])>"   # -> RC 0 ; 575 passed / 0 failed
python -c "<tally; pytest.main([the 2 tests/smoke/test_smk_024..025 files])>"          # -> RC 0 ; 7 passed
```

**Reconciliation: 575 (tester-run final) = 561 carried (M6.2L) + 7 coder M6.2M regressions (→ 568 coder baseline) + 7
official-smoke nodes (3+4).** Coder baseline before any patch was 561 (byte-parity with M6.2L); the isolated 2-leg run
independently confirms 7 passed. *(pytest's terminal summary is unreliable in this harness for a long run, so totals
came from an in-process `pytest_runtest_logreport` tally with `pytest.main() RC=0` — see SMOKE_RESULTS.md "On counting".)*

### 3.3 The in-scope fail gate — FAIL-007 NOT tripped (boundary-verified; carried fixes intact)

- **FAIL-007 (no-evidence / overstated readiness):** the pack cannot be authenticated by shape alone — a not-issued ref
  (SMK-024) and a whitespace SmokeResult (SMK-025) both fail closed → NOT_READY; readiness still tops at
  `OWNER_REVIEW_REQUIRED`. Boundary: **25 outcomes (13 DEFENDED / 11 OPEN_NONGATE / 1 NOTE), 0 FAIL-007 breaches**.
- **No regression in carried fixes** (boundary REG1-3, all DEFENDED): B2 forgery (junk + copy-paste → all MISSING), B3
  floor (`STANDING_GAP_BLOCKERS=()` rebind still trips → NOT_READY, all 8 carried), B4 revenue-lock (QUOTE_SENT+OV
  mispair still drops revenue → dashboard 0, FAIL-001 unchanged).
- Security: **0** raw PII / **0** secrets across 248 files; both fixes security-positive, no new PII surface.

---

## 4. Rollback (every change this slice made) — *acceptance check 1*

Staged-only and non-destructive: nothing live, no migration applied, no flag flipped. Baseline rollback = **delete the
`04-artifacts/impl/M6.2M/` tree** (M6.2L untouched, carried byte-identical). Per change:

| Change | Rollback |
|---|---|
| **FIX-2** `evidence/models.py` (+`_nonblank`; `recorded` stripped-non-blank) | revert to M6.2L bytes (drop `_nonblank`, restore raw-truthiness `recorded`) — **scoped logic revert** |
| **FIX-2** `evidence/pack_assembler.py` — `_smokes` whitespace→None normalize | **scoped logic revert** of only the `_smokes` region |
| **FIX-1** `evidence/pack_assembler.py` — `_ref_valid` docstring | **scoped docstring-only revert** (no logic to unwind) |
| **New tests** — `tests/test_m6_2m_ref_authenticity.py`, `tests/test_m6_2m_smoke_authenticity.py` | delete the files |
| **Migration** | **none added** (migrations stay `0001–0012`, RULE-018) — nothing to unwind |
| **Config flag** | **none** — `config.py` byte-identical to M6.2L/M6.2K |
| **New table** | **none** (assembler hardening only) |
| **Carried M6.2L fixes** (forgery/collision/revenue-lock) | **untouched** — nothing to revert |
| **Boundary / security analysis-only writes** (`M6.2M_boundary.md`, `M6.2M_security.md`, harness/scanner scripts) | delete; both recorded "no source modified" |

Every change is additive or a fail-closed tightening, so a revert restores exact prior behaviour. No posture value was
ever written — nothing to revert on `global_gateway_state` / `production_flag` / `external_send`.

---

## 5. Decision deltas & governance

### 5.1 Coder self-review (M6-P2201/2202) — plan honesty finding + edge-case probe

- **Plan-level (M6-P2201):** the honest finding that **leg-1's oracle logic already exists in the base** (so FIX-1 is a
  proof + docstring, not new code); a 2-dimension red-team returned **0 findings**.
- **Impl-level (M6-P2202):** an edge-case probe confirmed `_nonblank` is fail-closed for `None`/int/whitespace and True
  only for a stripped-non-blank string; a non-string `status` → not recorded; a partial blank (one whitespace field of
  three) → not recorded; `_smokes` normalizes whitespace → None; and **SMK-024 is discriminating** (COMPLETE iff issued).
  No carried test broken (the 18 P0-pack smokes + waiver-strip + M6.2L regressions all green; 568 coder baseline).

### 5.2 The remediation — what is genuinely closed (boundary-verified)

- **Ref-side mechanism proven (M6-OD-013 / FAIL-007):** boundary F1-2 — a reconstructed **un-issued** ref is REJECTED
  when the allowlist is passed → canonical-string reconstruction can no longer forge COMPLETE. The mechanism
  discriminates (SMK-024).
- **Smoke-side whitespace twin closed (F-EVID-1 whitespace):** boundary F2-1 — `_nonblank` makes a whitespace/tab/newline
  status/corr/ev not-recorded → UNRUN → NOT_READY (SMK-025).
- **Carried fixes intact:** boundary REG1-3 confirm B2/B3/B4 unregressed.

### 5.3 The bounding — what "closed" does and does not mean (top-0.1% lens)

The slice OBJECTIVE says "close the M6-OD-013 authenticity residual"; the honest reading, surfaced so no reader mistakes
it for "authenticity solved":
- **Mechanism, not production.** The default **no-allowlist** path still passes canonical reconstruction (boundary F1-3,
  OPEN_NONGATE) — production ref-authenticity requires the **owner to populate the real issued-refs registry** and pass
  it (M6-OD-013 integration, §5.5). Today it is a **proven mechanism**, not a live authenticity guarantee.
- **Whitespace, not duck-type.** FIX-2 closes the whitespace-*field* variant; the F-EVID-1 **duck-*type*** variant
  (boundary F2-6/F2-7 — a duck object with `recorded=True` + `None` fields launders a mandatory slot, or with a
  whitespace field crashes `_smokes`' `dataclasses.replace` fail-closed) remains OPEN → CODER (type-check a real
  `SmokeResult`).
- **Structural floor (why none of this trips a gate):** the evidence assembler has **no `app/api` caller** (boundary
  N5), and `Readiness` has no Pass member — so every residual requires in-process code to construct the hostile object
  and every one caps at `OWNER_REVIEW_REQUIRED`.

### 5.4 Residuals (armed-not-fired; none channel-reachable — no assembler caller, external_send=OFF)

- **F-SEC-2M-1 (primary security; carried + widened; M6-OD-012 + CODER).** `SmokeResult.to_public()` masks
  correlation/evidence ids but exports **`status` + `smoke_id` unmasked**, and `_smokes` appends the caller's row
  **without pinning to `spec.smoke_id`** → a result under the SMK-001 key with a different/PII `smoke_id` is displayed
  with that raw id (a mislabel + a **second** unmasked slot). **Not introduced by M6.2M** (`to_public` unchanged;
  `status` = carried F-SEC-2K-1, `smoke_id` = boundary **N4** widening of F-EVID-4). Same **export-masking-scope family**
  as F-SEC-2I-2 / F-SEC-2J-2 / F-SEC-2K-1 / F-SEC-2L-1 → **M6-OD-012**. `status`/`smoke_id` are TESTER-set today (no live
  PII). **Fix:** pin each row to `spec.smoke_id` + mask/enum-constrain `status`+`smoke_id`.
- **`known_refs` untyped-param + entry-hygiene robustness (boundary N1/N2/F1-4/F1-6; CODER).** A **string** allowlist
  degrades `r not in known_refs` to substring (N1); a **generator** is exhausted by the two-calls-per-key pass → an
  honest pack false-rejected (N2, fail-closed direction but a real robustness regression); a hostile `__contains__`
  always-True (F1-4); and the oracle strips the *provided* ref but **not** the allowlist entries, so a **whitespace-padded
  registry entry** fails to match → fail-closed MISSING (F1-6, NOTE). All trusted-input. **Fix:**
  `isinstance(known_refs,(set,frozenset,dict))` + materialize once + evaluate `_ref_valid` once per key + **strip
  allowlist entries** (the M6.2L B2-7 caveat sharpened).
- **F-EVID-1 duck-type variant (boundary F2-6/F2-7; CODER).** See §5.3 — type-check the value is a real `SmokeResult`.
- **Assembler input robustness (boundary N3; CODER).** A non-Mapping `evidence_refs` crashes `provided.get` → assemble
  aborts fail-closed-by-crash (pre-existing). **Fix:** validate `evidence_refs` is a Mapping.
- **Carry-forwards (out of the M6-OD-013 twin scope; CODER/owner):** **F-EVID-5** (readiness gates on `recorded`, not
  PASS/FAIL — 18 recorded-`FAIL` smokes still reach OWNER_REVIEW_REQUIRED; add a `status=='PASS'` gate; the boundary R3
  compound with the default-path reconstruction still caps at OWNER_REVIEW_REQUIRED and discloses all 8 standing
  blockers); **F-EVID-4/R2** (a genuine non-blank `status` carrying PII survives normalization — enum-constrain/mask);
  **F-GROWTH-1 + reactivation N6** consent subject-bind (disclosed in M6.2J-GROWTH).

### 5.5 New owner decisions + housekeeping

- **M6-OD-013** (evidence-ref authenticity) — the mechanism is proven; the **production step is the owner populating the
  real issued-refs registry** and passing it as `known_refs`. **M6-OD-012** governs the F-SEC-2M-1 masking family.
- **Operator hygiene (non-blocking, now flagged across M6.2L + M6.2M by the entry judge / coder / security):**
  **M6-OD-013** and **M6-OD-014** are referenced by the slice specs, the gap-blocker floor, and this remediation but are
  **still not rows in `DECISION_REGISTER.md`** — a standing doc-sync gap (analogous to the stale ENTRY-004 row carried
  from M6-P3011). The PM/analyst should record them as formal decision rows for a complete owner audit trail.

### 5.6 Immutable posture & forward gates

`config.py` byte-identical to M6.2L/M6.2K; `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
`HASH_POLICY_RATIFIED=False`, `SCALE_MODEL_RATIFIED=False`, all learning flags `False`, `live_migrations=false` —
unchanged. **M6-P1000 + M6-P1309 verdicts remain BLOCKED (not converted)** and are carried in the assembled pack; the
M6.2G/H/I/J + M6-OD-011/012/013 + owner-gated forward conditions remain hard gates. Out of scope (untouched): populating
the real known-refs registry (owner integration), any change to the M6.2L forgery/collision/ROAS-lock fixes, any flag flip.

---

## 6. Changelog delta — *acceptance check 2*

| Kind | Delta this slice introduced |
|---|---|
| **Code (staged, patched)** | 2 files: `evidence/models.py` (FIX-2 `_nonblank` + `recorded`), `evidence/pack_assembler.py` (FIX-2 `_smokes` normalize + **FIX-1 docstring-only**). The one real logic change is FIX-2; FIX-1 is a proof + docstring of pre-existing oracle logic. |
| **Tests (staged, new)** | 2 coder regressions + 2 official smokes (SMK-024/025, 7 nodes). Suite total **561 → 575** (+7 coder, +7 smoke nodes). |
| **Migration** | **none** (RULE-018; migrations stay `0001–0012`). |
| **Config flag** | **none**; `config.py` byte-identical to M6.2L/M6.2K. |
| **New table** | **none** (assembler hardening only). |
| **Contract** | CTR-025 DRAFT_LOCKED → satisfied; no new contract. |
| **Owner decisions** | references **M6-OD-013** (mechanism proven; owner-populate the real registry is the forward step) + the **M6-OD-012** masking family (F-SEC-2M-1); neither M6-OD-013 nor M6-OD-014 yet a DECISION_REGISTER row (operator hygiene). |
| **Residuals closed** | M6-OD-013 ref-side **mechanism** (SMK-024) + F-EVID-1 **whitespace** variant (SMK-025) — boundary-verified. Not closed: production ref-authenticity (owner registry), the F-EVID-1 duck-type variant. |
| **Governance verdicts** | `M6-P1000` + `M6-P1309` **remain BLOCKED** (not converted), carried in the pack. |
| **Posture** | unchanged — `BLOCKED / OFF / OFF`, all flags `False`, `config.py` byte-identical. |
| **Readiness** | assembled pack still `OWNER_REVIEW_REQUIRED` (no Pass/Ready). |

---

## 7. Handoff

- **Immediate next (JUDGE, fresh session): M6-P2209 `M6_2M_SLICE_GATE_JUDGE`.** Reads the evidence index + the band and
  checks the 7 exit-gate legs: ref authenticity (leg 1), smoke authenticity (leg 2), SMK-024/025 recorded (3–4),
  every-prompt evidence (5), judge sign-off (6), rollback (7). Judges never modify what they judge. See §8.
- **OWNER (the load-bearing forward step):** **populate the real issued-refs registry** and pass it as `known_refs`
  (M6-OD-013 integration) — the registry must store **un-padded canonical refs** (`ev::{category}::{key}`; a
  whitespace-padded entry silently false-rejects an honest pack → NOT_READY, boundary F1-6). Until then, the default
  no-allowlist path is not production-authenticated. Plus M6-OD-012 (the F-SEC-2M-1 masking family) and the standing
  M6.2G/H/I/J + M6-OD-011 forward conditions.
- **CODER:** F-SEC-2M-1 (pin rows to `spec.smoke_id` + mask/enum-constrain `status`+`smoke_id`); the F-EVID-1 duck-type
  variant (type-check a real `SmokeResult`); the `known_refs` robustness (`isinstance` + materialize once + evaluate once
  per key); the non-Mapping `evidence_refs` guard; F-EVID-5 `status=='PASS'` gate; F-GROWTH-1 + N6 subject-bind.
- **OPERATOR (doc-sync, non-blocking):** register **M6-OD-013** + **M6-OD-014** in `DECISION_REGISTER.md`; reconcile the
  stale ENTRY-004 row.
- **Posture carried forward unchanged:** `BLOCKED / OFF / OFF`, all flags `False`; `M6-P1000` + `M6-P1309` BLOCKED.

---

## 8. Pointers for the slice-gate Judge (M6-P2209)

1. **Read order:** `M6_2M_EVIDENCE_INDEX.md` → the 7 band JSONs (M6-P2200…2206) → the two review reports
   (`M6.2M_boundary.md`, `M6.2M_security.md`) → `SMOKE_RESULTS.md` → `IMPLEMENTATION_NOTES.md` (rollback §6). The 7-leg
   exit-gate map is index §4; the residuals are index §5.
2. **What is proven (executed + boundary-verified):** the M6-OD-013 ref-side authenticity **mechanism** (SMK-024
   discriminating — a reconstructed un-issued ref is rejected under an allowlist; no-allowlist → no regression) and the
   smoke-side **whitespace** twin (SMK-025 — `recorded` requires stripped-non-blank). Full suite **575 passed / 0
   failed**; smokes **7/7**; boundary **0** FAIL-007 breaches / 25 outcomes; carried M6.2L B2/B3/B4 **intact** (REG1-3);
   security **0** raw PII/secrets / 248 files; `config.py` byte-identical.
3. **What "closed" does NOT mean (weigh this):** (a) FIX-1 is a **proof + docstring** of oracle logic already in the
   M6.2L base — not net-new code; (b) M6-OD-013 is **mechanism**-closed, **not production**-closed — the default
   no-allowlist path still passes reconstruction, and the **owner must populate the real issued-refs registry** (the
   load-bearing forward step); (c) FIX-2 closes the **whitespace** variant, not the F-EVID-1 **duck-type** variant. All
   three are surfaced in §5.3 and honestly out of scope.
4. **What is NOT yet closed:** exit items **5 & 6** are PENDING only because this docs prompt (M6-P2208) and the judge
   (M6-P2209) are the last two to run — not a defect. Legs 1–4 + 7 (rollback) are MET.
5. **The finding to weigh hardest:** **F-SEC-2M-1** — `status`+`smoke_id` exported unmasked and `_smokes` not pinned to
   `spec.smoke_id`; **carried, not introduced here** (`to_public` unchanged), armed-not-fired (no assembler caller),
   routes to the OPEN **M6-OD-012** masking family. Plus the `known_refs` robustness + duck-type residuals (§5.4), all
   trusted-input/code-exec, none channel-reachable.
6. **Boundary integrity of this docs prompt (M6-P2208):** `analysis_only` — it read the band evidence and wrote only this
   runbook + its evidence JSON. It touched no `04-artifacts/state/`, marked no ledger row, modified no file it documented,
   computed no verdict, and declared no readiness. `global_gateway_state=BLOCKED`, `production_flag=OFF`,
   `external_send=OFF` — untouched; `M6-P1000` + `M6-P1309` remain BLOCKED (not converted).
