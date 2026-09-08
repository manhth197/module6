# M6.2O PLAN — Out-of-band Backfill: psid_hash (B1) + duck-coerce (F2-6) (STAGED, plan-only)

**Prompt**: M6-P2301 (`M6_2O_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code) · **Gate**: EVIDENCE_GATE
**Slice**: M6.2O — **retroactive ledger/judge certification** of two already-shipped, self-disclosed **off-ledger**
changes (chief-auditor 2026-09-07 item B4): **B1** (raw PSID → one-way `psid_hash`, per the M5 PSID policy; landed in
`impl/M6.2N`, carried forward) and **F2-6** (`_smokes` coerces any smoke object to a canonical `SmokeResult`, never
trusting a caller `.recorded`; landed in `impl/M6.2O`). **The impl ALREADY EXISTS and is verified-clean — this coder
leg RECORDS the shipped code (points at `04-artifacts/impl/M6.2O/`); there is NO re-implementation and NO new code**
(the slice adds no features). Cumulative superset of M6.2M.

> **Posture (immutable, this slice flips nothing):** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
> `external_send=OFF`, `live_migrations=false`; `config.py` sha256 **911b3238…** byte-identical to M6.2M. Status here
> is **coder self-reported**; the runner gate + JUDGE (M6-P2309) decide (RULE-015).

Ledger verified: **M6-P2301 = RUNNING** (row 221), dependency **M6-P2300 = SIGNED** (entry gate PASS). Target
**LOCKED**, **M6-OD-011 DECIDED**. Single in-scope contract **M6-CTR-025** (Evidence package) = DRAFT_LOCKED. Doc
working mode (extract L463–472): *do not guess; read the repo first; reuse conventions; minimal change; output
files-touched + tests + commands + PASS/FAIL + rollback*.

## 0. Hard forward condition (from the M6-P2300 entry judge — flagged, not a blocker)

**M6-OD-003** (privacy/legal hash-policy review; hash policy + fields allowed to be SENT to Pixel/CAPI/Offline) is
**OPEN** and is a **hard forward condition**: it must be **DECIDED before any REAL psid_hash deployment** — real
pepper provisioning, the cross-module `psid_hash` join (C7), or any external send of hashed data. The in-scope B1
here is **internal PII-minimization only** (raw PSID never stored on any durable/export surface; only a one-way
HMAC; pepper is a `secret_ref`; `external_send` immutably OFF) — strictly *more* protective, enables/sends nothing —
so M6-OD-003 does not block this backfill. Per the entry judge, **the exit judge M6-P2309 must scrutinize whether
the internal HMAC/pepper scheme itself needs M6-OD-003 sign-off before B1 is deemed closed.** This plan records that
condition; it resolves no owner decision.

## 1. What this slice is (a certification of existing code, not a build)

The two fixes were shipped off-ledger and self-disclosed in `impl/M6.2N` + `impl/M6.2O` IMPLEMENTATION_NOTES. This
slice brings them **onto the ledger** with a judge sign-off, closing the **FAIL-008-adjacent process debt** (an
off-ledger change with no slice-spec/row/gate). Leg roles:

- **coder plan (this, M6-P2301) + coder implement (M6-P2302)**: **RECORD** the shipped code — point at
  `04-artifacts/impl/M6.2O/`, re-verify it is green + clean, write the notes; **no re-implementation**.
- **tester (M6-P2303/2304)**: author + run the official smokes **SMK-026** (B1) + **SMK-027** (F2-6), record
  correlation_id + evidence_id.
- **boundary (M6-P2305) / security-PII (M6-P2306) / judge (M6-P2309)**: verify the PII-minimization + evidence-
  authenticity substance (M6-P2306 is the natural home to scrutinize the psid_hash/pepper surface + M6-OD-003).

## 2. The shipped change-set → exit-gate leg + smoke (RECORD; rollback per item)

Legend: **Leg** = M6.2O.md "Exit gate checks" number · **Smoke** = SMOKE_REGISTER id · file:anchor are M6.2O-current.

### LEG 1 — B1 psid_hash → **SMK-026 · RULE-014 · FAIL-008**

- **SMK-026 (verbatim)**: *a raw PSID supplied at the resolve seam is stored/exported → no raw psid on any durable/
  export surface; `as_stored()` carries only a one-way `psid_hash:` HMAC value (deterministic per pepper, collision-
  sensitive); production with the pepper env unset fails closed (`PsidHashPolicyError`).*
- **Shipped (verified-clean)** — files + rollback per item:

| File : anchor | What shipped | Rollback (staged) |
|---|---|---|
| `app/measurement/identity/psid_hash.py` (new) | `hash_psid` (:53, `psid_hash:`+base64url(HMAC-SHA256(**pepper=key**, psid)); None for None/blank; coerces non-str); `resolve_pepper` (:37, env `M6_PSID_HASH_PEPPER` secret_ref; **fail-closed production** when unset → `PsidHashPolicyError` :33); labelled **non-secret dev** `_MOCK_PEPPER` (:30) | delete the file |
| `app/measurement/models/attribution_context.py` | field `psid`→`psid_hash` (:77); `to_public()` emits the hash as-is (:116, no mask); `as_stored()`=`dict(to_public())` (:133, no raw-keep); dropped unused `mask` import | revert to M6.2M bytes |
| `app/measurement/attribution/resolver.py` | `import hash_psid` (:26); `LiveContext.psid`→`psid_hash` (:75); **hash at ingest** (:104, raw psid in RAM only); `resolve()` threads `psid_hash` (:151) | revert to M6.2M bytes |
| `app/measurement/funnel/funnel.py` + `funnel/models.py` | `_trace` reads `ctx["psid_hash"]` + `FunnelTrace.psid_hash` (funnel.py:180-182; models.py:36,43, no mask) | revert to M6.2M bytes |
| `migrations/0013_psid_to_psid_hash.sql` (new) | staged `ALTER … RENAME COLUMN psid TO psid_hash` (:13, append-only) | delete (do NOT run its DOWN rename — a raw-psid column is a privacy regression) |
| `migrations/0006_…sql` | **comment-only** (forward-note to `psid_hash`; mask() insufficient) | revert the 2 comment lines |

- **Verified (this record)**: `grep app/` for a raw `.psid` field/`["psid"]` key (excl `psid_hash`) ⇒ **NONE**;
  `as_stored()`/`to_public()` carry `psid_hash` and no `psid` key; the hash is one-way + deterministic (pepper as
  the HMAC key); `resolve_pepper(production=True)` with the env unset **raises**; the only pepper literal is the
  labelled non-secret dev mock. **No raw PSID/pepper** on any surface (RULE-014 / FAIL-008 satisfied).

### LEG 2 — F2-6 duck-coerce → **SMK-027 · RULE-015 · FAIL-007**

- **SMK-027 (verbatim)**: *a duck smoke object with a fake `.recorded=True` + blank status/correlation_id/
  evidence_id for a mandatory owner smoke → `_smokes` coerces it to a canonical `SmokeResult`, recomputes
  `recorded=False` → `UNRUN_SMOKE` gap → pack `NOT_READY` (caller `.recorded` never trusted).*
- **Shipped (verified-clean)**:

| File : anchor | What shipped | Rollback (staged) |
|---|---|---|
| `app/measurement/evidence/pack_assembler.py` | `_smokes` (:157–170) **coerces** every provided object to a canonical frozen `SmokeResult` from its fields (`smoke_id`=registry; `status`/`correlation_id`/`evidence_id`/`waived` via `getattr`), so `recorded` is recomputed by `SmokeResult.recorded` (fail-closed); strip-waiver + whitespace-normalize run after, unchanged. **`models.py` NOT changed** | revert `_smokes` to M6.2M bytes |
| `tests/test_duck_smoke_recorded.py` (new) | duck ⇒ `recorded=False` + `UNRUN` gap + `NOT_READY`; isolating flip; non-vacuity | delete the file |

- **Verified**: only `_smokes` changed in `pack_assembler.py` (16 changed lines; **no** `_ref_valid`/`_ref_binding`/
  `_categories`/`standing_floor_ok`/`known_refs` line touched — B2/B3 intact). Code-exec-only, not channel-reachable,
  no production risk.

### LEGS 3–7 (other roles)

3–4 SMK-026/027 executed-or-waived (**TESTER** M6-P2303/2304). 5 all evidence schema-valid. 6 judge PASS
(M6-P2309). 7 rollback documented (this §2 + §5). The coder legs never self-run/self-certify the smokes (RULE-015).

## 3. Minimal-change & scope integrity (VERIFIED — this backfill certifies, adds nothing)

- `config.py` sha256 **911b3238…** identical to M6.2M (posture untouched).
- **B2/B3/B4 fix-logic files whole-file byte-identical to M6.2M**: `gap_blockers.py` (B3), `data_mart.py` +
  `measurement_event_store.py` + `growth/reads.py` (B4), `evidence/models.py` (B2/B3), `evidence/categories.py` (B2).
- The **A3/A4/B2/B3 fix LOGIC is unchanged** inside the files B1/F2-6 touched (diff-verified: no A3/A4 marker in
  `attribution_context.py`/`resolver.py`; no B2/B3 marker in `pack_assembler.py`).
- Migrations `0001–0013` (0013 the only add; 0006 comment-only). Full suite **584 passed** (`PYTHONDONTWRITEBYTECODE=1
  python -B`), no skips, no regress.

## 4. Rules / fail gates in scope

- **RULE-014 + FAIL-008** (raw PII / raw secret exposure): B1 removes the raw PSID from every durable/export surface
  and applies the hash policy (one-way HMAC; pepper as `secret_ref`) — the slice **closes** this exposure, tripping
  neither.
- **RULE-015 + FAIL-007** (no self-cert / no-evidence): F2-6 hardens the evidence pack against a forged
  `.recorded` (fail-closed to NOT_READY); the coder legs write evidence and self-certify nothing.
- **RULE-009** (missing source → LOW/HOLD, never fabricated): honored — a missing/blank PSID hashes to `None`
  (fail-closed), nothing is fabricated; no data-quality grading is changed by this slice.

## 5. Scope & governance boundary

- **In scope (recorded here)**: exactly the shipped B1 (`identity/psid_hash.py` + `attribution_context` psid→psid_hash
  + migration 0013) and F2-6 (`pack_assembler._smokes` duck-coerce). **No NEW code.**
- **Out of scope (untouched)**: the real per-M6 pepper `secret_ref` (owner-provisioned at deploy) + the cross-module
  `psid_hash` join (C7, owner+chief); DB/HTTP bind (M6-OD-011); registry runtime (B5); any flag flip —
  `production_flag`/`global_gateway_state`/`external_send` stay OFF/BLOCKED/OFF. **M6-OD-003** governs the real
  send/join (forward condition §0).
- **Boundary intact**: measure/record-only; no pricing/order-state/CRM-send/commission; `M6-P1000`/`M6-P1309` stay
  BLOCKED. No raw secrets/PII in code or evidence (pepper `secret_ref` only; raw PSID nowhere).

## 6. What M6-P2302 (implement leg) will do — RECORD, not re-implement

Write `IMPLEMENTATION_NOTES.md` pointing at the shipped `04-artifacts/impl/M6.2O/` code (the change-set of §2),
re-verify the suite is green (`584 passed`, no regress) + the acceptance greps (0 raw psid; fail-closed pepper;
`_smokes` coerce; config sha256 identical; migrations 0001–0013), and confirm **no code is changed** by the record
step. The C7 invariant doc (`INVARIANTS_M5_RUNTIME_CONTROLS.md`) is already present in the tree.

## 7. Rollback (per item §2, + baseline)

Staged only — baseline rollback = delete the `04-artifacts/impl/M6.2O/` tree (M6.2N + M6.2M untouched). Per item:
the §2 tables. No live migration to unwind (`live_migrations=false`). Every change is a privacy tightening (B1) or a
fail-closed tightening (F2-6); a revert restores the prior (raw-psid / duck-trusting) behaviour — a deliberate
regression, not a routine undo.

---

*Plan-only: this document writes no application code, adds no migration/flag, resolves no owner decision, and flips
no flag. It RECORDS already-shipped, verified-clean code. `global_gateway_state=BLOCKED`, `production_flag=OFF`,
`external_send=OFF`. The runner gate + JUDGE decide (RULE-015).*
