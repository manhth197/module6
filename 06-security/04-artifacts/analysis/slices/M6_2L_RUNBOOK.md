# M6.2L — Slice Runbook — Post-Pilot Audit Fix Batch (A3 / A4 / B2 / B3 / B4)

> **Status: STAGED — a remediation slice that proves 5 audit fixes with regression evidence; it flips nothing.**
> M6.2L closes the **5 M6-self-doable** defects from the 2026-09-03 chief-auditor audit (against commit `5f09894`), as a
> cumulative superset of M6.2K under `04-artifacts/impl/M6.2L/`. Three of the five close residuals the pack's **own**
> boundary/security lines had raised — **B4** closes F-DASH-1 / F-GROWTH-3 (the M6.2K/M6-P3002 revenue mispair),
> **B2** closes F-EVID-2, **B3** closes F-EVID-3 — and the M6.2L boundary adversary **re-executed the old attacks and
> confirmed all three CLOSED**, with **0** in-scope FAIL-001/FAIL-007 breaches.
>
> Posture immutable and untouched: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all
> scale/hash/learning flags `False`, `live_migrations=false`, **`config.py` byte-identical to M6.2K**. No new
> table/migration/flag (migrations stay `0001–0012`). The assembled pack still tops at `OWNER_REVIEW_REQUIRED`;
> `M6-P1000` + `M6-P1309` verdicts remain **BLOCKED (not converted)**. This slice declares no ROAS Pass / Scale Ready
> (owner-only, doc §23).
>
> Evidence at a glance: full staged suite **561 passed / 0 failed / 0 skipped / 0 error, rc 0**; all **5** official
> smokes SMK-019…023 PASS (17/17 nodes), each with a masked `correlation_id` + `evidence_id`; boundary **0** in-scope
> breaches across 30 executed outcomes; security **0** raw PII / **0** secrets across 244 files. Next: slice-gate Judge
> **M6-P2109**.

| Field | Value |
|---|---|
| Slice | **M6.2L** — Post-Pilot Audit Fix Batch (post-pilot; depends on M6.2K; the audit closed against commit `5f09894`) |
| Prompt (this doc) | **M6-P2108** — `M6_2L_DOCS` (ANALYST_ARCHITECT, `analysis_only`, EVIDENCE_GATE) |
| Doc scope | chief-auditor audit 2026-09-03 (`manh-viec-can-lam-m6`): the 5 M6-self-doable items **A3 / A4 / B2 / B3 / B4** |
| Rules in scope | **RULE-003** (revenue only ORDER_VERIFIED) · **RULE-009** (LOW/HOLD never scale evidence) · **RULE-014** (no raw PII) · **RULE-015** (no self-cert) |
| Fail gates in scope | **FAIL-001** (revenue misuse — B4) · **FAIL-007** (no-evidence / overstated readiness — B2/B3) |
| Contracts | CTR-002 DRAFT_LOCKED (A3) · CTR-016 MISSING but harmonization M6-P0711 PASS → resolved-for-entry (A4 HTTP/authN = OPEN M6-OD-011) · CTR-025 DRAFT_LOCKED (B2/B3) |

---

## 1. What this slice built (staged under `04-artifacts/impl/M6.2L/`)

M6.2L carries the **entire M6.2K tree byte-identical** (app + 12 migrations `0001–0012` + full carried suite; baseline
verified green **before any patch: 523 passed**, byte-parity with M6.2K) and applies **5 fix sites** across **9 distinct
carried files** (each a fix's named site; `resolver.py` and `pack_assembler.py` each host two fixes in distinct regions).
**No new migration, no new config flag, no new table** (attribution_id pre-exists in `0006`; ad-hierarchy columns in
`0002` — RULE-018). Nothing acts, sends, or flips.

| Fix | Audit | What it does | Files | Gate/rule |
|---|---|---|---|---|
| **A3** | attribution_id trace | `attribution_id` becomes a **first-class** field on `AdsAttributionContext` (the CTR-002 surrogate already declared in migration `0006`) + exposed in `to_public`/`as_stored`; `derive_attribution_id()` = deterministic `attr_`+sha256(**event_id**)[:24], 1:1 with the row, idempotent. An ORDER_VERIFIED traces `attribution_id → campaign`. A governance ref rooted in a non-PII event id — **not masked**, no commission field. | `models/attribution_context.py`, `attribution/resolver.py` | trace; RULE-014/019 |
| **A4** | ad-hierarchy intake | `POST /api/ads/events/track` reads + **type-validates** 4 optional M6-owned ad-hierarchy ids (`campaign/adset/ad/live_session`; present-but-non-string ⇒ fail-closed `SCHEMA_INVALID`, RULE-H03); `normalize` persists them to Zone A; the resolver appends `LIVE_ORGANIC` **only when `live.present AND NOT ads.complete`** (a complete ad path dominates a co-present live_session). A FACEBOOK_AD event → **HIGH** via the real API path; an incomplete-ad+live path stays **MULTI_TOUCH** (preserves carried SMK-007). | `api/track.py`, `normalize.py`, `attribution/resolver.py` | attribution; CTR-016 |
| **B2** | evidence forgery (M6-OD-013) | `pack_assembler` category-completeness now validates ref **existence(well-formed) + (category,key)-binding + pack-wide uniqueness** (not raw truthiness), with an optional `known_refs` authenticity oracle. Defeats both named forgeries (junk ref; one ref copy-pasted across all mandatory keys of all 10 categories) + wrong-category/wrong-key. **Closes F-EVID-2.** | `evidence/pack_assembler.py` | FAIL-007; RULE-015 |
| **B3** | gap-id floor (M6-OD-014) | `gap_blockers.standing_floor_ok()` is a **membership-count** floor (a duplicated / shadowing / missing standing id ⇒ FAIL, where a naive set-subset would pass), with a **defensive floor call in `assemble`** ⇒ `NOT_READY` if the emitted list fails the floor. **Closes F-EVID-3.** | `evidence/gap_blockers.py`, `evidence/pack_assembler.py` | FAIL-007; RULE-015 |
| **B4** | ROAS verified-lock | `store.materialize()` self-checks the **stored row's own** `event_code` and **drops** non-ORDER_VERIFIED revenue+order_code fail-closed **without raising** — the drop-not-raise applies **only to non-OV rows**; a differing re-materialize of a genuine ORDER_VERIFIED row still **raises** (set-once **RULE-008** / SMK-018 preserved, boundary B4-5). `data_mart.verified_rows()` **and** `growth.reads.verified_rows()` add the `event_code == ORDER_VERIFIED` filter. A QUOTE_SENT row + `materialize(verified=True)` ⇒ Revenue Verified `0.0`, ROAS `None` (no spend); a genuine ORDER_VERIFIED counts. **Closes F-DASH-1 / F-GROWTH-3 — the mispair now yields 0 across all four revenue readers** (store, data_mart, growth, funnel; B4 patches the first three, the funnel already carried the filter → CRIT-DIVERGE-01 resolved). | `store/measurement_event_store.py`, `dashboard/data_mart.py`, `growth/reads.py` | **FAIL-001**; RULE-003 |

> **Cite-note (for the Judge):** the band evidence headlines "**8** patched files"; enumerating the distinct sites gives
> **9** (`resolver.py` + `pack_assembler.py` each host two fixes). This runbook lists all **9** so §4 rollback covers
> every change. Non-gating; a headline-count nuance, not a defect.

---

## 2. Operate

M6.2L is measure/record-only; there is no new operational action. What changes at the staged level:

1. **A3/A4 record more, act on nothing.** `attribution_id` and the 4 ad-hierarchy ids are **recorded** attribution
   fields; they are never priced, ordered, sent, or turned into commission. A4's intake is on the channel-facing track
   endpoint but its HTTP routing/authN is the OPEN **M6-OD-011** owner-integration step — the handler is
   framework-neutral (untrusted-input discipline: server re-validates, derives `raw_event_hash` server-side, type-checks
   the new ids fail-closed).
2. **B2/B3 make the evidence pack harder to fool.** The assembler now rejects forged/duplicate/whitespace refs and a
   tampered/emptied standing-blocker payload — it still tops at `OWNER_REVIEW_REQUIRED`, never a Pass.
3. **B4 makes verified revenue self-enforcing.** Revenue is booked only from a stored ORDER_VERIFIED row, at the write
   (`materialize`, drop-not-raise) and at both read choke points; a leaked/mispaired non-OV row contributes 0.
4. **What stays impossible:** flipping a flag, sending externally, scaling, self-certifying. `config.py` is byte-identical
   to M6.2K; nothing here is wired to an endpoint that acts.

---

## 3. Verify

### 3.1 The 5 official smokes (each proven by its smoke AND its coder regression)

All 5 bound smokes **PASS** (17/17 nodes = 3+3+4+4+3), each recorded with a masked `correlation_id` + `evidence_id`
(`SMOKE_RESULTS.md`, M6-P2104), executed (not owner-waived):

- **SMK-019 (A3)** 3/3 — attribution_id first-class + traces to campaign; deterministic/idempotent; governance ref, not PII.
- **SMK-020 (A4)** 3/3 — 4 ids persist via the real track path → FACEBOOK_AD/HIGH; non-string → fail-closed SCHEMA_INVALID; incomplete-ad+live stays MULTI_TOUCH.
- **SMK-021 (B2)** 4/4 — both named forgeries → MISSING/NOT_READY; wrong-category/wrong-key MISSING; honest refs all-COMPLETE.
- **SMK-022 (B3)** 4/4 — duplicate/shadow/missing standing id → floor FAIL; canonical list passes + carries all 8 standing blockers.
- **SMK-023 (B4)** 3/3 — QUOTE_SENT + `materialize(verified=True)` → Revenue Verified `0.0`, **ROAS `None`** (no spend); both `verified_rows` exclude a leaked quote row; genuine OV counts `180000.0`.

### 3.2 Full staged suite (count discipline)

```
# from 04-artifacts/impl/M6.2L/  (venv: 02-tester/.venv, python 3.12.13, pytest 8.4.2; cache-free, no shell redirection)
python -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider'])>"   # -> RC 0 ; 561 passed / 0 failed
python -c "<tally; pytest.main([the 5 tests/smoke/test_smk_019..023 files])>"          # -> RC 0 ; 17 passed
```

**Reconciliation: 561 = 523 carried (M6.2K) + 21 coder M6.2L regressions (19 initial + 2 review-driven B2, → 544
baseline) + 17 official-smoke nodes (3+3+4+4+3).** Coder baseline before any patch was 523 (byte-parity with M6.2K); the
isolated 5-leg run independently confirms 17 passed. *(pytest's terminal summary is unreliable in this harness for a long
run, so totals came from an in-process `pytest_runtest_logreport` tally with `pytest.main() RC=0` — see SMOKE_RESULTS.md
"On counting".)*

### 3.3 The in-scope fail gates — NOT tripped (boundary-verified)

- **FAIL-001 (revenue misuse) — B4:** QUOTE_SENT never became revenue at any of the four readers (store-drop + data_mart
  + growth + funnel). Boundary Group B4 6/6 DEFENDED; the M6.2K/M6-P3002 mispair (F-DASH-1/F-GROWTH-3) **CLOSED**, and
  the funnel-vs-F/J divergence (M6-P3002 **CRIT-DIVERGE-01**) **RESOLVED** — all four readers now agree on the mispair.
- **FAIL-007 (no-evidence / overstated readiness) — B2/B3:** forged/duplicate refs → categories MISSING; a
  tampered/emptied standing payload → NOT_READY (F-EVID-3 **CLOSED**; the readiness↔standing cross-check now exists).
  Boundary Group B2 6/8 DEFENDED (2 documented residuals, below), Group B3 4/4 DEFENDED.
- Boundary total: **30 executed outcomes (20 DEFENDED / 9 OPEN_NONGATE / 1 NOTE), 0 in-scope breaches**. Security:
  **0** raw PII / **0** secrets across 244 files.

---

## 4. Rollback (every change this slice made) — *acceptance check 1*

Staged-only and non-destructive: nothing live, no migration applied, no flag flipped. Baseline rollback = **delete the
`04-artifacts/impl/M6.2L/` tree** (M6.2K untouched, carried byte-identical). Per change:

| Change | Rollback |
|---|---|
| **A3** `models/attribution_context.py` (+`attribution_id` field + `to_public`/`as_stored`) | revert to M6.2K bytes |
| **A3** `attribution/resolver.py` — `derive_attribution_id()` + field-set region | **scoped partial revert** of only the A3 region (dual-fix file) |
| **A4** `api/track.py` (+4 ad-hierarchy id intake + validate) | revert to M6.2K bytes |
| **A4** `normalize.py` (+4 optional params → Zone-A) | revert to M6.2K bytes |
| **A4** `attribution/resolver.py` — `_entry_channels` LIVE_ORGANIC rule | **scoped partial revert** of only the A4 region (dual-fix file) |
| **B2** `evidence/pack_assembler.py` — `_categories`/`_ref_valid`/`_ref_binding` region | **scoped partial revert** of only the B2 region (dual-fix file) |
| **B3** `evidence/gap_blockers.py` (+`standing_floor_ok()`) | revert to M6.2K bytes |
| **B3** `evidence/pack_assembler.py` — defensive floor call in `assemble` | **scoped partial revert** of only the B3 region (dual-fix file) |
| **B4** `store/measurement_event_store.py` (materialize event_code self-check, drop-not-raise) | revert to M6.2K bytes |
| **B4** `dashboard/data_mart.py` (+`event_code==ORDER_VERIFIED` filter) | revert to M6.2K bytes |
| **B4** `growth/reads.py` (+`event_code==ORDER_VERIFIED` filter) | revert to M6.2K bytes |
| **New tests** — 5 coder regressions `tests/test_m6_2l_{a3,a4,b2,b3,b4}_*.py` + 5 official smokes `tests/smoke/test_smk_019…023_*.py` + `tests/TEST_MANIFEST.md` | delete the files |
| **Migration** | **none added** (attribution_id in `0006`, ad-hierarchy in `0002`; migrations stay `0001–0012`) — nothing to unwind |
| **Config flag** | **none** — `config.py` byte-identical to M6.2K |
| **Boundary / security analysis-only writes** (`M6.2L_boundary.md`, `M6.2L_security.md`, harness/scanner scripts) | delete; both recorded "no source modified" |

Every change is additive or a fail-closed tightening, so a revert restores exact prior behavior. No posture value was
ever written — nothing to revert on `global_gateway_state` / `production_flag` / `external_send`.

---

## 5. Decision deltas & governance

### 5.1 Coder self-fixes (M6-P2101/2102 §5) — 2 pre-code corrections + 3 impl-level minors

- **Plan-level (12-agent, before any code):** two load-bearing corrections were forced into the plan — **(a) B4 must
  drop, not raise** (four carried tests call `store.materialize` directly, two un-wrapped on a QUOTE_SENT row — a raise
  would break them), and **(b) A4 must include a resolver rule** reconciling SMK-007 (incomplete-ad+live = MULTI_TOUCH)
  with SMK-020 (complete-ad+live = HIGH). Both implemented; no OPEN owner decision was resolved (the pack's own smokes
  uniquely determine the rule).
- **Impl-level (7-agent, against the running code):** **0 CRITICAL/MAJOR**; 3 minors — **(B2, fixed)** existence was
  convention-shape-only in the default (a right-category/bogus-key ref completed a category) → binding is now on
  **(category, key)**, regression-added; **(SMK-023 wording, documented)** "ROAS = 0" is fail-closed `None` under
  no-spend; **(A4 ad-id PII, documented)** ad-hierarchy ids are non-PII platform ids, routed to security + M6-OD-012.

### 5.2 The remediation win — three of the pack's own residuals CLOSED, boundary-verified

This is the point of the slice, and it is honestly verified (top-0.1% lens): the M6.2L boundary adversary **re-executed
its own prior attacks** and confirmed:
- **B4 → F-DASH-1 / F-GROWTH-3 CLOSED** — the M6.2K/M6-P3002 revenue mispair is dropped at the write and excluded at all
  four readers; **CRIT-DIVERGE-01 RESOLVED** (store/data_mart/growth/funnel now agree).
- **B2 → F-EVID-2 CLOSED** — whitespace/junk/duplicate refs can no longer mark a category complete.
- **B3 → F-EVID-3 CLOSED** — a rebind of `STANDING_GAP_BLOCKERS` to `()` now trips the defensive floor → NOT_READY (in
  M6.2K it yielded OWNER_REVIEW_REQUIRED).

**No regression in the contested carried areas** (coder §4, boundary B4-5): the two un-wrapped QUOTE_SENT funnel tests
(**SMK-004**) and the incomplete-ad+live resolver test (**SMK-007**) re-verified green under B4/A4, and the set-once
RULE-008 immutability (**SMK-018** — a differing re-materialize of a genuine ORDER_VERIFIED row) still **raises** — B4's
drop-not-raise is scoped to non-OV rows only, so no prior guarantee was weakened.

### 5.3 The two sharp findings — the fixes are real but bounded (surfaced, not buried)

- **B4 trust-shift (boundary §5, CMP-02):** B4 makes the **stored row's `event_code == ORDER_VERIFIED`** the sole revenue
  authority — which is exactly what RULE-003/FAIL-001 permit. But B4 does not (and is not meant to) validate that the OV
  **label itself** is genuine; the defense against a self-minted OV label is **endpoint authN/authZ (M6-OD-011) +
  Commerce-ownership of verification**, not B4. Armed-not-fired today: the materialize/CTR-023 worker is **un-wired** (no
  `app/api/*` endpoint calls it) and M6-OD-011 is OPEN. Stated plainly so the owner sees where the revenue-trust burden
  now sits.
- **B2 authenticity residual (M6-OD-013):** the B2 default path proves **slot-correctness** (well-formed + (category,key)
  bind + uniqueness), **not authenticity** — a forger reconstructing the exact canonical `ev::{category}::{key}` string
  still passes without the injected `known_refs` issued-refs oracle (the forward M6-OD-013 seam, exercised by a
  regression; boundary B2-1 OPEN_NONGATE). It **compounds with F-EVID-5** (boundary **N3** capstone): canonical-
  reconstructed refs + all-`FAIL` recorded smokes still reach `OWNER_REVIEW_REQUIRED` (caps there, never a Pass, still
  discloses the 8 standing blockers). Trusted-input (PM authors refs); the oracle must be a real `set`/`frozenset`, not a
  hostile always-True container (boundary B2-7).

### 5.4 Slice-owned + carried residuals (armed-not-fired; none channel-reachable while export unwired + external_send=OFF)

- **F-SEC-2L-1 (primary security; M6-OD-012 + CODER).** A4 lets a **channel-supplied** value populate the ad-hierarchy /
  trace-join ids, which are type-validated but **not** run through the RULE-014 payload tripwire and **export unmasked**
  (`to_public()` masks only `psid`; the export predates A4). Security adjudicated **campaign/adset/ad as non-PII platform
  ids** (masking them would be wrong; a phone/digit scan false-positives legitimate numeric ids), and routed
  `live_session_id` + `comment_id`/`messenger_thread_id` (`messenger_thread_id` most identifying) to the OPEN
  **M6-OD-012** masking-scope decision — the **same family** as F-SEC-2I-2 / F-SEC-2J-2 / F-SEC-2K-1. **Fix:** M6-OD-012,
  plus an **email-only** intake reject as false-positive-safe defense-in-depth (a phone/digit reject is **not** safe).
- **Carry-forwards (out of the 5-fix scope; CODER/owner):** **F-EVID-5** (add a `status=='PASS'` gate so a recorded-FAIL
  smoke drops to `NOT_READY`); **F-EVID-1 / F-EVID-4** (smoke truthiness / unmasked `status` export); **F-GROWTH-1 + N6
  reactivation borrowed-consent** (bind `snapshot.subject_ref` to the row's buyer/member — disclosed in M6.2J-GROWTH);
  **RULE-009 value-sanity (N4)** (`math.isfinite(v) and v>=0` on the verified-revenue write); **N5 scale-evidence**
  (A4 ad-id laundering — **neutralized** by `SCALE_MODEL_RATIFIED=False`, M6-OD-005); **B4 silent-drop audit-trail /
  idempotency** (RN-01/RN-04 — the drop leaves no audit line; a future hardening pass emits one; B4 still holds FAIL-001).

### 5.5 New owner decisions this slice references + housekeeping

- **M6-OD-013** (evidence-ref authenticity, B2) and **M6-OD-014** (gap-id floor, B3) are **referenced by the slice spec as
  fix-decision-ids but are not yet rows in `DECISION_REGISTER.md`** — a doc-sync gap (operator hygiene, flagged by the
  entry judge + coder + tester), analogous to the stale **ENTRY-004** row carried from M6-P3011.
- **R5 housekeeping (boundary R5 / security §11):** the **M6.2J-GROWTH** standing-blocker text still lists **F-GROWTH-3**
  as a forward condition even though **B4 closed it**, and the B3 membership floor now **locks that text by value** → a
  future slice must update the disclosure **floor-aware**. Over-disclosure (safe/honest-conservative), not a leak.
- **Operator hygiene (non-blocking):** register M6-OD-013 + M6-OD-014; reword the SMK-023 SMOKE_REGISTER "ROAS = 0" line
  to the fail-closed `None`; reconcile the stale ENTRY-004 register row.

### 5.6 Immutable posture & forward gates

`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `HASH_POLICY_RATIFIED=False`,
`SCALE_MODEL_RATIFIED=False`, all learning flags `False`, `live_migrations=false` — unchanged; `config.py` byte-identical
to M6.2K. **M6-P1000 + M6-P1309 verdicts remain BLOCKED (not converted)** and are carried in the assembled pack; the
M6.2G/H/I/J + M6-OD-011/012 + owner-gated forward conditions from the M6-P3011 readiness package remain hard gates.
Out of scope (owner/cross-module, untouched): B1 psid_hash (M6-OD-003), A1/A2 (M3), A6/B5 (registry+M3/M5/M7),
A5/B6/B8 (M6-OD-011/owner), the C-band cross-module seams, M5 DEBT-1..4.

---

## 6. Changelog delta — *acceptance check 2*

| Kind | Delta this slice introduced |
|---|---|
| **Code (staged, patched)** | 9 distinct carried files across the 5 fixes (A3: `attribution_context.py`, `resolver.py`; A4: `track.py`, `normalize.py`, `resolver.py`; B2: `pack_assembler.py`; B3: `gap_blockers.py`, `pack_assembler.py`; B4: `measurement_event_store.py`, `data_mart.py`, `reads.py`). All additive or fail-closed tightening. |
| **Tests (staged, new)** | 5 coder regressions + 5 official smokes (SMK-019…023, 17 nodes). Suite total **523 → 561** (+21 coder, +17 smoke nodes). |
| **Migration** | **none** (RULE-018 — attribution_id in `0006`, ad-hierarchy in `0002`; migrations stay `0001–0012`). |
| **Config flag** | **none**; `config.py` byte-identical to M6.2K. |
| **New table** | **none** (measure/record-only). |
| **Contracts** | CTR-002 DRAFT_LOCKED (A3 surfaces the pre-existing surrogate) · CTR-016 MISSING but harmonization M6-P0711 PASS → resolved-for-entry · CTR-025 DRAFT_LOCKED (B2/B3 harden the assembler). No new contract. |
| **Owner decisions** | references **M6-OD-013** (B2 authenticity) + **M6-OD-014** (B3 floor) — not yet DECISION_REGISTER rows (operator hygiene); the F-SEC-2L-1 masking family routes to the OPEN **M6-OD-012**. |
| **Residuals closed** | **F-DASH-1 / F-GROWTH-3** (B4), **F-EVID-2** (B2), **F-EVID-3** (B3) — boundary re-verified. |
| **Governance verdicts** | `M6-P1000` + `M6-P1309` **remain BLOCKED** (not converted), carried in the pack. |
| **Posture** | unchanged — `BLOCKED / OFF / OFF`, all flags `False`, `config.py` byte-identical. |
| **Readiness** | assembled pack still `OWNER_REVIEW_REQUIRED` (no Pass/Ready). |

---

## 7. Handoff

- **Immediate next (JUDGE, fresh session): M6-P2109 `M6_2L_SLICE_GATE_JUDGE`.** Reads the evidence index + the band and
  checks the 13 exit-gate legs: the 5 fixes proven by regression (items 1–5), SMK-019…023 recorded (6–10), every-prompt
  evidence (11), judge sign-off (12), rollback (13). Judges never modify what they judge. See §8.
- **CODER (hardening before any real surface):** F-SEC-2L-1 email-only intake reject; F-EVID-5 `status=='PASS'` gate;
  F-EVID-1/4; F-GROWTH-1 + N6 consent subject-bind; RULE-009 value-sanity (`math.isfinite`); the B4 silent-drop audit
  line; wire the B2 `known_refs` oracle as a real set at the M6-OD-013 step.
- **OWNER:** M6-OD-012 (masking scope for the trace-join ids — the F-SEC-2I-2/2J-2/2K-1/2L-1 family); M6-OD-013 (evidence
  authenticity oracle); M6-OD-014 (gap-id floor); the standing M6-OD-011 (admin/track authN — B4's revenue-trust and A4's
  endpoint both lean on it) and the M6.2G/H/I/J forward conditions.
- **OPERATOR (doc-sync, non-blocking):** register M6-OD-013 + M6-OD-014 in `DECISION_REGISTER.md`; reword SMK-023
  "ROAS = 0" → fail-closed `None`; reconcile the stale ENTRY-004 row; a future slice updates the M6.2J-GROWTH
  standing-blocker text floor-aware (F-GROWTH-3 now closed).
- **Posture carried forward unchanged:** `BLOCKED / OFF / OFF`, all flags `False`; `M6-P1000` + `M6-P1309` BLOCKED.

---

## 8. Pointers for the slice-gate Judge (M6-P2109)

1. **Read order:** `M6_2L_EVIDENCE_INDEX.md` → the 7 band JSONs (M6-P2100…2106) → the two review reports
   (`M6.2L_boundary.md`, `M6.2L_security.md`) → `SMOKE_RESULTS.md` → `IMPLEMENTATION_NOTES.md` (rollback §7). The
   13-leg exit-gate map is index §4; the residuals are index §5.
2. **What is proven (executed + boundary-verified):** all 5 M6-self-doable fixes hold — A3 (attribution_id first-class +
   traces to campaign), A4 (4 ids persist via the real track path → HIGH; non-string fail-closed; carried SMK-007
   preserved), B2 (existence+uniqueness+(category,key)-binding defeats both named forgeries), B3 (membership floor FAILs
   duplicate/shadow/missing), B4 (verified-revenue event_code lock at `materialize` + both `verified_rows`, drop-not-raise,
   all four readers agree). Full suite **561 passed / 0 failed**; smokes **17/17**; boundary **0** in-scope breaches and
   **F-DASH-1/F-GROWTH-3, F-EVID-2, F-EVID-3 confirmed CLOSED**; security **0** raw PII/secrets across 244 files;
   `config.py` byte-identical to M6.2K.
3. **What is NOT yet closed:** exit items **11 & 12** are PENDING only because this docs prompt (M6-P2108) and the judge
   (M6-P2109) are the last two to run — not a defect. Every fix leg (1–5), smoke leg (6–10), and rollback (13) is MET.
4. **The findings to weigh hardest:** the two **bounded-ness** points (§5.3) — **B4** locks revenue to the stored OV
   label but does not authenticate the label (that is M6-OD-011 authN + Commerce-ownership; armed-not-fired, materialize
   unwired), and **B2** proves slot-correctness not authenticity (M6-OD-013; compounds with F-EVID-5 via boundary N3).
   Plus **F-SEC-2L-1** (A4 channel-supplied trace-join ids export unmasked → M6-OD-012). All armed-not-fired, none
   channel-reachable while export surfaces are unwired and `external_send=OFF`.
5. **One evidence-count nuance (not a defect):** the band evidence headlines "8 patched files"; 9 distinct files are
   actually patched (`resolver.py` + `pack_assembler.py` each host two fixes) — this runbook §1/§4/§6 lists all 9 for
   rollback completeness.
6. **Boundary integrity of this docs prompt (M6-P2108):** `analysis_only` — it read the band evidence and wrote only this
   runbook + its evidence JSON. It touched no `04-artifacts/state/`, marked no ledger row, modified no file it documented,
   computed no verdict, and declared no readiness. `global_gateway_state=BLOCKED`, `production_flag=OFF`,
   `external_send=OFF` — untouched; `M6-P1000` + `M6-P1309` remain BLOCKED (not converted).
