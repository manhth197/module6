# M6.2O — Slice Runbook — Out-of-band Backfill: psid_hash (B1) + duck-coerce (F2-6)

> **Status: STAGED — a retroactive on-ledger certification of two already-shipped, off-ledger changes; it re-implements
> nothing and flips nothing.** M6.2O brings **B1** (raw PSID → one-way HMAC-SHA256(pepper, psid), shipped in
> `impl/M6.2N`) and **F2-6** (`_smokes` duck-coerce to a canonical `SmokeResult`, shipped in `impl/M6.2O`) onto the
> ledger with proper gates, closing the **process debt** that `impl/M6.2N` + `impl/M6.2O` carried no
> slice-spec / ledger-row / gate. The coder legs **RECORD** the shipped code; the executed `impl/M6.2N → impl/M6.2O`
> app byte-diff is a **single file** (the F2-6 `_smokes` change), `config.py` byte-identical — proving **no code was
> smuggled under "record only"**.
>
> **Two honesty framings this runbook leads with:**
> 1. **B1 is a genuine FAIL-008 *reduction* — but a STAGED mechanism proof, NOT production-safe.** It replaces the M6.2L
>    reversible `mask(psid)` with a one-way HMAC and keeps no raw PSID on any durable/export surface (SMK-026). **But**
>    the staged `_MOCK_PEPPER` is a **public** source constant (a staged synthetic `psid_hash` is brute-force
>    recoverable), so one-wayness is real **only** with the owner-provisioned secret_ref pepper. **M6-OD-003**
>    (privacy/legal hash policy + real pepper) is the **HARD forward gate** before any real deploy / cross-module join /
>    external send; security explicitly does **not** certify B1 production-safe, and the exit judge **M6-P2309** must
>    weigh whether the internal HMAC/pepper scheme needs M6-OD-003 sign-off before B1 is deemed closed. **The residual
>    risk sits in the decision, not the code.**
> 2. **The process debt is a FAIL-009 (gate-bypass) class, not FAIL-008.** The entry judge M6-P2300 labelled the
>    off-ledger debt "FAIL-008 process debt"; per FAIL_GATE_REGISTER that off-ledger/skipped-gate concept is **M6-FAIL-009
>    (Gate bypass)** — FAIL-008 is raw-PII exposure, which B1 separately *reduces*. (Correction carried from the PM index.)
>
> Posture immutable and untouched: `config.py` **byte-identical to M6.2M** (sha256 `911b3238…`); `global_gateway_state=BLOCKED`,
> `production_flag=OFF`, `external_send=OFF`, `HASH_POLICY_RATIFIED=False`, all flags `False`, `live_migrations=false`.
> `M6-P1000` + `M6-P1309` remain **BLOCKED (not converted)**; the assembled pack still tops at `OWNER_REVIEW_REQUIRED`.
> Evidence: full suite **593 passed / 0 failed, rc 0**; SMK-026/027 PASS (7/7); boundary **0** FAIL-007/FAIL-008
> breaches / 24 outcomes; security **0** raw PII / **0** secrets / 258 files.

| Field | Value |
|---|---|
| Slice | **M6.2O** — Out-of-band Backfill (post-pilot; depends on M6.2M; chief-auditor 2026-09-07 item B4). Ledger jumps M6.2M→M6.2O (no M6.2N rows — the debt this slice closes). |
| Prompt (this doc) | **M6-P2308** — `M6_2O_DOCS` (ANALYST_ARCHITECT, `analysis_only`, EVIDENCE_GATE) |
| Rules / fail gates in scope | **RULE-009 · RULE-014** (no raw PII — B1) **· RULE-015** · **FAIL-008** (raw PII — B1 reduces) **· FAIL-007** (no-evidence — F2-6) |
| Contract | **M6-CTR-025** DRAFT_LOCKED → satisfied for entry |
| Entry note | Entry judge M6-P2300 is a **re-judgment**: the prior BLOCKED was the correct fail-closed call while `00-spec/slices/M6.2O.md` was missing; the operator ran `gen_slices.py`, the spec regenerated, re-judged **PASS**. |

---

## 1. What this slice records (staged under `04-artifacts/impl/M6.2O/`)

M6.2O carries the **entire M6.2M tree byte-identical** and **records** (does not re-implement) two changes already
shipped off-ledger. The coder RECORD leg (M6-P2302) wrote **no application code** and proved it by an executed
`impl/M6.2N → impl/M6.2O` app byte-diff = **only** `pack_assembler.py` (F2-6); B1 is carried from M6.2N unchanged;
`config.py` byte-identical.

| Change | Shipped in | What it does | Files | Gate |
|---|---|---|---|---|
| **B1 psid_hash** | `impl/M6.2N` (carried) | raw PSID → one-way `psid_hash:`+base64url(HMAC-SHA256(pepper, psid)); hashed **at the resolver signals seam** (`resolve_live_session`), so the raw psid never enters `LiveContext` or the stored row; `as_stored() = dict(to_public())` carries only `psid_hash`, no reversible raw-psid key; deterministic per pepper, collision-sensitive; `resolve_pepper(production=True)` with the env unset → `PsidHashPolicyError` (fail-closed; `production` is a **call arg**, `PRODUCTION_FLAG` stays OFF). Real pepper = `os.environ["M6_PSID_HASH_PEPPER"]` **secret_ref**; dev `_MOCK_PEPPER` a labelled non-secret. | `identity/psid_hash.py` (new), `models/attribution_context.py` (psid→psid_hash), `attribution/resolver.py`, `funnel/funnel.py`, `funnel/models.py`, **`migrations/0013_psid_to_psid_hash`** (new), `migrations/0006` (comment) | **FAIL-008** / RULE-014 |
| **F2-6 duck-coerce** | `impl/M6.2O` | `pack_assembler._smokes` rebuilds every provided smoke into a canonical frozen `SmokeResult` from its `getattr` fields, **pins `smoke_id` to `spec.smoke_id`**, and **recomputes `recorded`** — the caller's `.recorded` is never trusted. | `evidence/pack_assembler.py` (`_smokes` only) | **FAIL-007** / RULE-015 |

**New security-positive control (verify artifact):** `tests/test_no_http_client_import.py` — an AST import-scan gate
that fails the build if any `app/**` module imports an HTTP/egress client (`httpx`/`requests`/`aiohttp`/…). It is the
static complement to `EXTERNAL_SEND=OFF`, keeping egress outbox-worker-only even after the M6-OD-011 runtime bind.

**No new config flag.** **One new migration** (`0013`, from B1 in M6.2N) — migrations are now `0001–0013`.

---

## 2. Operate

M6.2O records existing mechanisms; there is no new operational action, and the psid seam + evidence assembler have
**no `app/api` caller** (boundary N3/N5).

1. **B1 hashes at the seam.** The raw psid arrives only via the in-process, trusted resolver **signals** seam and is
   one-way hashed **immediately**; the raw value lives only as the `hash_psid` argument in RAM, never on a durable or
   export surface. In staging (`PRODUCTION_FLAG=OFF`) the mock pepper is used; in production with the pepper env unset
   the path **fails closed** (`PsidHashPolicyError`).
2. **F2-6 coerces every smoke.** The assembler rebuilds each provided smoke to a canonical `SmokeResult` and recomputes
   `recorded` — a lying duck cannot mark a mandatory smoke recorded; readiness fails closed to `NOT_READY`.
3. **The record-leg discipline.** This slice's coder legs **record**; the byte-diff (§1) is the operational proof that
   no B1 modification was smuggled under "record only".
4. **What stays impossible:** no real psid_hash deploy (M6-OD-003 + real pepper gate it), no external send
   (`external_send=OFF` + the import gate), no flag flip, no self-cert. `config.py` byte-identical to M6.2M.

---

## 3. Verify

### 3.1 The 2 official smokes (each proven by its smoke AND its coder regression)

Both bound smokes **PASS** (7/7 nodes = 4+3), each recorded with a masked `correlation_id` + `evidence_id`
(`SMOKE_RESULTS.md`, M6-P2304), executed (not owner-waived):

- **SMK-026 (B1 psid_hash)** 4/4 — no raw psid in `as_stored()` (`_PSID not in str(as_stored())`); one-way + `psid_hash:`
  prefix + deterministic + collision-sensitive; `production=True` injected + pepper env removed → `PsidHashPolicyError`
  with `PRODUCTION_FLAG` asserted still `OFF` (no flag flip); None/blank psid → None.
- **SMK-027 (F2-6 duck-coerce)** 3/3 — a duck `recorded=True` + None fields on mandatory SMK-001 → coerced, `recorded`
  recomputed False → `UNRUN:M6-SMK-001` gap → `NOT_READY`; the duck alone among 18 still flips readiness (isolation);
  genuine set still records → `OWNER_REVIEW_REQUIRED`.

### 3.2 Full staged suite (count discipline)

```
# from 04-artifacts/impl/M6.2O/  (venv: 02-tester/.venv, python 3.12.13, pytest 8.4.2; -B, cache-free, no shell redirection)
python -B -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider'])>"   # -> RC 0 ; 593 passed / 0 failed
python -B -c "<tally; pytest.main([the 2 tests/smoke/test_b1_… test_f2_6_… files])>"       # -> RC 0 ; 7 passed
```

**Reconciliation: 593 (tester-run final) = 584 coder record-baseline (M6.2M 575 + the shipped B1/F2-6 code + coder
regressions) + 9 official verify artifacts** (SMK-026 4 + SMK-027 3 + the no-HTTP-client import gate 2 = the documented
+9 delta vs the plan's 584). The isolated 2-leg run independently confirms 7 passed. *(pytest's terminal summary is
unreliable in this harness for a long run, so totals came from an in-process `pytest_runtest_logreport` tally with
`pytest.main() RC=0` — see SMOKE_RESULTS.md "On counting".)*

### 3.3 The in-scope fail gates — NOT tripped (boundary-verified; carried fixes intact; record-leg honest)

- **FAIL-008 (raw PII) — B1:** no raw PSID on any durable/export surface (boundary B1-1..6 DEFENDED; security §4 verified
  on the code). B1 is a genuine FAIL-008 **reduction** vs the M6.2L reversible mask. **Two honest NOTEs**: the mock
  pepper is reversible (B1-7 → M6-OD-003) and other identity fields still export raw (B1-8 → M6-OD-012).
- **FAIL-007 (no-evidence / overstated readiness) — F2-6:** a lying duck cannot mark a mandatory smoke recorded → pack
  `NOT_READY`; readiness still tops at `OWNER_REVIEW_REQUIRED`. Boundary Group F2-6 7/8 DEFENDED.
- **No regression in carried fixes** (boundary REG1-3): B2 forgery, B3 standing-floor, the M6.2M known_refs oracle all
  intact. Boundary total: **24 outcomes (18 DEFENDED / 4 OPEN_NONGATE / 2 NOTE), 0 in-scope breaches**; the executed
  record-leg diff confirms only the F2-6 one-file delta. Security: **0** raw PII / **0** secrets / 258 files.

---

## 4. Rollback (every change this slice made) — *acceptance check 1*

Staged-only and non-destructive: nothing live, no live migration applied (`live_migrations=false`), no flag flipped.
Baseline rollback = **delete the `04-artifacts/impl/M6.2O/` tree** (M6.2N + M6.2M untouched). Per change:

| Change | Rollback |
|---|---|
| **B1** `identity/psid_hash.py` (new) | delete the file |
| **B1** `models/attribution_context.py` (psid→psid_hash) | revert to the pre-B1 (M6.2M) bytes — restores the `mask(psid)` field *(a deliberate privacy regression, not a routine undo)* |
| **B1** `attribution/resolver.py`, `funnel/funnel.py`, `funnel/models.py` (hash-at-seam) | revert to M6.2M bytes |
| **B1** `migrations/0013_psid_to_psid_hash` (new, staged, **never applied**) | `down`-DDL for `0013`; delete the file — no live migration to unwind |
| **B1** `migrations/0006` (comment-only) | revert the comment |
| **F2-6** `evidence/pack_assembler.py` — `_smokes` coerce | **scoped revert** of only the `_smokes` region (B2/B3/`_ref_valid`/`_categories`/`standing_floor_ok` untouched) |
| **New tests** — coder `tests/test_b1_psid_hash.py`, `tests/test_duck_smoke_recorded.py`; official `tests/smoke/test_b1_psid_hash_smoke.py`, `tests/smoke/test_f2_6_duck_recorded_coerced.py`; the import gate `tests/test_no_http_client_import.py`; `tests/TEST_MANIFEST.md` | delete the files |
| **Config flag** | **none** — `config.py` byte-identical to M6.2M |
| **The process debt itself** | closed by the ledger rows M6-P2300…2309 existing (the on-ledger certification) — the "rollback" of that is the ledger, not a file |
| **Boundary / security analysis-only writes** (`M6.2O_boundary.md`, `M6.2O_security.md`, harness/scanner scripts) | delete; both recorded "no source modified" |

Every code change is a privacy tightening (B1) or a fail-closed tightening (F2-6), so a revert is a deliberate
regression, not a routine undo. No posture value was ever written.

---

## 5. Decision deltas & governance

### 5.1 The crux — B1 is a staged mechanism proof, NOT production-safe (top-0.1% lens)

The dominant failure mode of certifying a psid_hash slice is letting "B1 verified clean / FAIL-008 reduced" read as
**production-safe**. It is not, and the runbook states so plainly:
- **The staged pepper is public/reversible.** `_MOCK_PEPPER = b"m6-staged-mock-pepper-not-a-secret-dev-only"` is a source
  constant → a staged synthetic `psid_hash` is brute-force recoverable. Safe in staging (synthetic ids only); one-wayness
  is real **only** with the owner-provisioned secret_ref pepper. **A real deploy on the mock pepper would be a FAIL-008
  exposure** (boundary B1-7, security §5).
- **Legal sufficiency is undecided.** Whether HMAC-SHA256+pepper pseudonymization is legally adequate, and the status of
  the M5-issued **`PSID_HASH_POLICY_M5_TMP` (explicitly temporary)**, is **M6-OD-003 (OPEN)** — privacy/legal.
- **Why B1 is not BLOCKED now (the scope that justifies the disposition):** B1 is **internal PII-minimization** — it
  pseudonymizes the PSID *at rest* and does **not** touch external send. `external_send` is immutably OFF and B1 does
  **not** modify the M6.2D CAPI/Offline payload builder (`integration/hash_policy.py`); so `HASH_POLICY_RATIFIED=False`
  (which gates the M6.2D *external-send* hash path) does **not** gate B1's internal mechanism — B1 is verifiable-clean in
  staging **without** a ratified external-send policy. That is why the review completes cleanly rather than BLOCKED.
- **Disposition:** not BLOCKED (the mechanism is proven in staging, `production_flag` OFF, review completes cleanly), but
  **explicitly forward-gated**. Security does **not** certify B1 production-safe; **M6-OD-003 (+ the real secret_ref
  pepper) is the HARD forward condition** before any real psid_hash deploy / cross-module join (C7) / external send of
  hashed data, and the exit judge **M6-P2309** must weigh whether the internal scheme needs M6-OD-003 sign-off before B1
  is deemed closed. **The residual risk sits in the decision, not the code.**

### 5.2 The process-debt closure — honest framing (FAIL-009 class, record-leg diff)

- **What the debt was:** B1 and F2-6 were shipped **off-ledger** — `impl/M6.2N` + `impl/M6.2O` carried no slice-spec /
  ledger-row / gate. That off-ledger/skipped-gate class is the **M6-FAIL-009 (Gate bypass)** concept per FAIL_GATE_REGISTER
  — **not** FAIL-008. (The entry judge M6-P2300 labelled it "FAIL-008 process debt"; the PM index corrected the label
  against the register — FAIL-008 = raw-PII exposure, which B1 separately reduces.)
- **How M6.2O closes it honestly:** the coder legs **record**, and the executed `impl/M6.2N → impl/M6.2O` app byte-diff
  (single file, F2-6 `_smokes`; `config.py` byte-identical) **proves no B1 modification was smuggled under "record
  only"** (boundary §5). The slice regularizes two *real, already-shipped, verified-clean* changes; it invents no code.
- **Entry re-judgment (honest process):** M6-P2300's prior BLOCKED was the correct fail-closed call while the spec file
  was missing; the operator regenerated it (`gen_slices.py`) and it re-judged PASS — the gate worked as designed.

### 5.3 The remediation win — F2-6 closes three M6.2M residuals (boundary-verified)

F2-6 is the coder's fix for **three residuals the boundary line raised at M6.2M**, all re-executed and confirmed CLOSED:
- **F-EVID-1 duck variant** (boundary F2-6-1) — a duck `.recorded=True` + None fields → recomputed False → NOT_READY.
- **COMP-4 missing-attr crash** (F2-6-3) — missing attrs → `getattr(...,None)` → not recorded, no AttributeError.
- **N4/X2 smoke_id mislabel/leak** (F2-6-4) — `smoke_id` pinned to `spec.smoke_id`; a caller id carrying PII is discarded.
  So the F-SEC-2K-1/N4 **export-masking family shrinks** (the `smoke_id` slot is now closed). Plus the new import-scan
  gate (§1) is a security-positive no-egress-client control.

### 5.4 Residuals (armed-not-fired; none channel-reachable — no assembler/psid-seam channel caller, external_send=OFF)

- **M6-OD-003 (PRIMARY HARD forward gate; owner + exit judge).** §5.1 — real pepper provisioning + privacy/legal sign-off
  (+ the M5 `PSID_HASH_POLICY_M5_TMP` status) before any real psid_hash deploy/join/send. A **decision, not a code fix**.
- **F-SEC-2O-1 / F-SEC-2I-2 masking family (carried, SHRUNK; M6-OD-012).** B1 hashed the psid and F2-6 closed the
  `smoke_id` slot, leaving the live/comment/messenger **trace-join ids** (`messenger_thread_id` [most identifying] /
  `live_session_id` / `comment_id`) + `SmokeResult.status` (F-EVID-4, verbatim) still exporting raw → M6-OD-012.
- **F-EVID-6 (boundary N2, NEW; CODER).** No **trace↔smoke binding** — a genuine SMK-002 correlation/evidence trace can
  be mis-filed under the SMK-001 key (F2-6 pins `smoke_id` and kills the `.recorded`-lie, but nothing binds the *trace*
  to its smoke). The smoke-side analog of `_ref_binding`. Trusted-input. **Fix:** bind the trace to the smoke (or the
  `known_refs` registry covers it).
- **Carry-forwards:** **F-EVID-5** (readiness gates on `recorded`, not PASS/FAIL — add a `status=='PASS'` gate);
  **known_refs untyped param** robustness; **F-GROWTH-1 + reactivation N6** consent subject-bind; the **audit `detail`**
  unmasked sink (caller-discipline-defended today; a raw identity must never reach it once audit sinks are wired at
  M6-OD-011).

### 5.5 New owner decisions + housekeeping

- **M6-OD-003** is the load-bearing forward gate for B1 (§5.1). **M6-OD-012** governs the shrunk masking family.
- **Operator hygiene (non-blocking, now standing across M6.2L/M6.2M/M6.2O):** register **M6-OD-013** + **M6-OD-014** —
  and the **M5 `PSID_HASH_POLICY_M5_TMP` dependency** (M6-OD-003's input) — as `DECISION_REGISTER.md` rows; reconcile the
  stale ENTRY-004 row. These are referenced by slice specs / code but are not yet formal rows (a traceability gap).

### 5.6 Immutable posture & forward gates

`config.py` byte-identical to M6.2M (sha256 `911b3238…`); `global_gateway_state=BLOCKED`, `production_flag=OFF`,
`external_send=OFF`, `HASH_POLICY_RATIFIED=False`, all flags `False`, `live_migrations=false` — unchanged. **M6-P1000 +
M6-P1309 verdicts remain BLOCKED (not converted)**; the M6.2G/H/I/J + M6-OD-011/012 + **M6-OD-003** forward conditions
remain hard gates. Out of scope (untouched): any NEW code (this slice certifies the existing impl); the real per-M6
pepper secret_ref (owner, at deploy) + the cross-module psid_hash join (C7); DB/HTTP bind (M6-OD-011); any flag flip.

---

## 6. Changelog delta — *acceptance check 2*

| Kind | Delta this slice recorded/introduced |
|---|---|
| **Code (staged, carried/recorded)** | B1: `identity/psid_hash.py` (new), `models/attribution_context.py`, `attribution/resolver.py`, `funnel/funnel.py`, `funnel/models.py` (from M6.2N, unchanged). F2-6: `evidence/pack_assembler.py` `_smokes` (the one M6.2N→M6.2O app delta). |
| **Migration** | **+`0013_psid_to_psid_hash`** (B1; staged, never applied) — migrations now `0001–0013`; `0006` comment-only. First new migration since M6.2H's `0012`. |
| **Tests (staged, new)** | 2 coder regressions + 2 official smokes (SMK-026/027, 7 nodes) + the security import-scan gate (`test_no_http_client_import.py`, 2). Suite **575 → 593** (+9 verify artifacts on the 584 coder record-baseline). |
| **Config flag** | **none**; `config.py` byte-identical to M6.2M. |
| **New table** | none new beyond the `0013` psid_hash column migration (record-only certification). |
| **Contract** | CTR-025 DRAFT_LOCKED → satisfied; no new contract. |
| **Owner decisions** | **M6-OD-003** is the HARD forward gate for B1 (real pepper + privacy/legal + M5 `PSID_HASH_POLICY_M5_TMP`); **M6-OD-012** masking family (shrunk). M6-OD-013/014 + the M5 policy dependency still not DECISION_REGISTER rows (operator hygiene). |
| **Residuals closed** | F-EVID-1 duck variant + COMP-4 crash + N4/X2 smoke_id leak (all M6.2M, via F2-6) — boundary-verified. B1 = a FAIL-008 *reduction* (staged). **New:** F-EVID-6 (trace↔smoke binding). |
| **Governance verdicts** | `M6-P1000` + `M6-P1309` **remain BLOCKED** (not converted). Process debt (FAIL-009 class) closed on-ledger. |
| **Posture** | unchanged — `BLOCKED / OFF / OFF`, all flags `False`, `config.py` byte-identical. |
| **Readiness** | assembled pack still `OWNER_REVIEW_REQUIRED`; **B1 NOT certified production-safe** (M6-OD-003 forward). |

---

## 7. Handoff

- **Immediate next (JUDGE, fresh session): M6-P2309 `M6_2O_SLICE_GATE_JUDGE`.** Checks the 7 exit-gate legs (psid_hash
  B1, duck-coerce F2-6, SMK-026/027 recorded, every-prompt evidence, judge sign-off, rollback) **AND — per the entry
  judge's mandate — must weigh whether the internal HMAC/pepper scheme needs M6-OD-003 privacy/legal sign-off before B1
  is deemed closed.** Judges never modify what they judge. See §8.
- **OWNER (the load-bearing forward step):** **M6-OD-003** — decide the privacy/legal hash policy + provision the real
  `M6_PSID_HASH_PEPPER` secret_ref (a real deploy on the public mock pepper would be a FAIL-008 exposure; production
  fail-closes if unset) + resolve the M5 `PSID_HASH_POLICY_M5_TMP` temporary status, before any real psid_hash
  deploy / C7 cross-module join / external send. Plus **M6-OD-012** (the shrunk trace-join masking family) and the
  standing M6.2G/H/I/J + M6-OD-011 forward conditions.
- **CODER:** F-EVID-6 (bind the trace to its smoke); F-EVID-5 (`status=='PASS'` readiness gate); `known_refs` robustness;
  F-GROWTH-1 + reactivation N6 subject-bind; monitor the audit `detail` sink at the M6-OD-011 bind.
- **OPERATOR (doc-sync, non-blocking):** register **M6-OD-013** + **M6-OD-014** + the **M5 `PSID_HASH_POLICY_M5_TMP`**
  dependency in `DECISION_REGISTER.md`; reconcile the stale ENTRY-004 row.
- **Posture carried forward unchanged:** `BLOCKED / OFF / OFF`, all flags `False`; `M6-P1000` + `M6-P1309` BLOCKED.

---

## 8. Pointers for the slice-gate Judge (M6-P2309)

1. **Read order:** `M6_2O_EVIDENCE_INDEX.md` → the 7 band JSONs (M6-P2300…2306) → the two review reports
   (`M6.2O_boundary.md` incl. its §5 record-leg diff, `M6.2O_security.md` incl. its §5 M6-OD-003 gate) → `SMOKE_RESULTS.md`
   → `IMPLEMENTATION_NOTES.md` (record leg + rollback §6). The 7-leg exit-gate map is index §4; the residuals are index §5.
2. **What is proven (executed + boundary/security-verified):** B1 keeps **no raw PSID** on any durable/export surface
   (one-way HMAC, hashed at the seam, fail-closed in production; SMK-026 4/4) — a genuine **staged** FAIL-008 reduction;
   F2-6 coerces every smoke and never trusts `.recorded`, closing **three M6.2M residuals** (SMK-027 3/3). Full suite
   **593 passed**; boundary **0** FAIL-007/FAIL-008 breaches / 24 outcomes; security **0** raw PII/secrets / 258 files;
   `config.py` byte-identical; the record-leg diff confirms only the F2-6 one-file delta (no code smuggled).
3. **The finding to weigh hardest — M6-OD-003 (your explicit mandate):** B1 is a **staged mechanism proof, NOT
   production-safe** — the mock pepper is public/reversible, and legal sufficiency + the M5 `PSID_HASH_POLICY_M5_TMP`
   status are OPEN. Security **does not** certify B1 production-safe. Weigh whether the internal HMAC/pepper scheme needs
   M6-OD-003 sign-off before B1 is deemed closed; a real deploy on the mock pepper would be a FAIL-008 exposure.
4. **The process-debt honesty:** the off-ledger debt is a **FAIL-009 (gate-bypass)** class (the entry judge's "FAIL-008"
   label was a mislabel, corrected against the register); the record-leg byte-diff proves no code was smuggled under
   "record only"; the entry re-judgment (missing-spec BLOCKED → regenerated → PASS) shows the gate working as designed.
5. **What is NOT yet closed:** exit items **5 & 6** are PENDING only because this docs prompt (M6-P2308) and the judge
   (M6-P2309) are the last two to run. Legs 1–4 + 7 (rollback) are MET. New residual **F-EVID-6** (trace↔smoke binding)
   + the carried masking family (M6-OD-012) + F-EVID-5 are armed-not-fired, none channel-reachable.
6. **Boundary integrity of this docs prompt (M6-P2308):** `analysis_only` — it read the band evidence and wrote only this
   runbook + its evidence JSON. It touched no `04-artifacts/state/`, marked no ledger row, modified no file it documented,
   computed no verdict, declared no readiness, and did **not** certify B1 production-safe. `global_gateway_state=BLOCKED`,
   `production_flag=OFF`, `external_send=OFF` — untouched; `M6-P1000` + `M6-P1309` remain BLOCKED (not converted).
