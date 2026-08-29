# M6.2K IMPLEMENTATION PLAN — Smoke & Evidence Pack (STAGED, plan-only)

**Prompt**: M6-P2001 (`M6_2K_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code this prompt)
**Slice**: M6.2K — the FINAL build slice: re-run the full P0 smoke matrix (SMK-001..018) and assemble the doc §22
evidence plan into an **owner sign-off package** with an honest gap/blocker list. Depends on M6.2J. **Done gate**:
*Evidence pack ready for review.*
**Posture (immutable)**: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
`SCALE_MODEL_RATIFIED=False`, `SCALE_EXECUTION_ENABLED=False`, `HASH_POLICY_RATIFIED=False`,
`LEARNING_AUTOPUBLISH_ENABLED=False`, `LEARNING_CONTENT_FILL_ENABLED=False`, `LEARNING_SAFE_RANGE_RATIFIED=False`,
`live_migrations=false`. This plan writes no code, applies no migration, flips no flag, and — decisively for THIS
slice — **never declares ROAS Pass or Scale Ready** (owner-only, doc §23) and **never self-certifies** (RULE-015).

> **Top-0.1% design lens (load-bearing — it CHANGED the design, not a label).** The dominant failure mode of an
> evidence-pack slice is a pack that **overstates readiness** — declaring ROAS Pass / Scale Ready, marking the pack
> "PASS", or silently dropping a standing blocker (FAIL-007 "No evidence → called PASS"; RULE-015 no self-certify).
> That reframed the whole build:
> 1. **The assembler has NO Pass / Ready / certify / flag-flip method.** Pack readiness tops out at
>    `OWNER_REVIEW_REQUIRED` — the owner decides Pass/Ready at PR/PILOT, not this code (doc §23).
> 2. **A category is COMPLETE only with its mandatory doc §22 content present; else INCOMPLETE (fail-closed).** The
>    ONE readiness rule (§4.4): readiness is `NOT_READY` iff any category is INCOMPLETE OR any of the 18 smokes
>    lacks a recorded result (a proposed smoke: a result OR a recorded owner waiver); otherwise `OWNER_REVIEW_REQUIRED`
>    — never silently "ready", never Pass/Ready.
> 3. **The gap/blocker list is MANDATORY and canonical.** It MUST carry the standing BLOCKED verdicts (M6-P1000,
>    M6-P1309) + every G/H/I/J forward condition + M6-OD-011/012 (§4.3). These standing blockers are ALWAYS
>    DISCLOSED but do NOT by themselves gate readiness (production stays BLOCKED regardless — that IS what the owner
>    reviews); the assembler cannot emit a pack that omits them.
> 4. **No new table (RULE-018).** Doc §13 defines no evidence-pack table; the pack is an ASSEMBLED artifact (the
>    Evidence layer's "evidence item / smoke report / release review", ARCH §1.9) over the existing smoke suite +
>    recorded evidence — no migration, no CTR beyond CTR-025 (already DRAFT_LOCKED, content-level).
> 5. **No raw PII / secrets in the pack (RULE-014/H02).** Evidence carries refs + correlation_id/evidence_id only;
>    PII masked. The pack is a governance artifact, not a data dump.
> This slice is the honesty test of the whole pack — its correctness IS its refusal to overstate.

---

## 1. Entry-gate verification

| Precondition | Source | Result |
|---|---|---|
| This prompt RUNNING | ledger (order 177) | **M6-P2001 = RUNNING** ✓ |
| Dependency resolved | ledger | **M6-P2000 = SIGNED** (M6.2K entry judge PASS, opens the slice STAGED) ✓; M6.2J exit **M6-P1909 = SIGNED** (all build slices A..J closed) ✓ |
| Target LOCKED + M6-OD-011 | `04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json` | `status=LOCKED`, `STAGED_ONLY`, safety all false; **M6-OD-011 DECIDED** 2026-07-23 ✓ |
| Slice contract | slice §Contract-checklist + M6-P2000 | sole contract **CTR-025** (Evidence package / owner review pack) **DRAFT_LOCKED** content-level (doc §22 / SPEC §19); file format = pack hardening — resolved-for-entry ✓ |
| OPEN owner decisions vs scope | DECISION_REGISTER (M6.2K sweep) + M6-P2000 | **ZERO** owner decisions name M6.2K (OD-002..007/011/012 remain OPEN globally and MUST surface in the pack's gap/blocker list) ✓ |
| Full P0 smoke suite present | `04-artifacts/impl/M6.2J/tests/smoke/` | all 18 smoke ids (SMK-001..015 owner + 016/017/018 proposed) have bound test files carried forward ✓ |
| Flags | manifest/brief | BLOCKED/OFF/OFF + all posture flags unchanged; `live_migrations=false` ✓ |

**Conclusion**: open for **STAGED** M6.2K. Build a smoke registry + an evidence-pack assembler that re-runs the P0
matrix (TESTER executes), assembles the 10 doc §22 categories fail-closed, carries the honest gap/blocker list, and
**never declares Pass/Ready or flips a flag**.

---

## 2. Working mode, conventions & staging model

Reuse the M6.2A–J baseline verbatim (pytest, frozen dataclasses, pure functions, mask-on-export, fail-closed
everywhere). The whole **M6.2J** tree (414 tests, all 18 smokes present) is carried forward **byte-identical** into
`04-artifacts/impl/M6.2K/`; M6.2K **adds** an `evidence/` assembly package + tests only. The change set (§5) is the
diff. **No new migration; no new config flag; no new contract beyond CTR-025; no carried-forward file patched** (the
smoke suite is executed as-is by the TESTER). `production_flag=OFF` immutable.

---

## 3. Scope lock (anchored strictly to `00-spec/slices/M6.2K.md`)

**In scope:**
1. **Full P0 smoke re-run** — a canonical registry of all 18 smoke ids (scenario/expected/bound-files/owner-vs-
   proposed) so the TESTER re-runs the complete matrix and records a `correlation_id` + `evidence_id` per smoke
   (doc §22 Smoke Report). SMK-016/017/018 are proposed → executed OR explicitly owner-waived (recorded as a waiver).
2. **Evidence registry completion (all 10 doc §22 categories)** — an assembler that gathers each category's
   mandatory content (§4.2); a category missing its content is **INCOMPLETE** (fail-closed, FAIL-007).
3. **Owner review package assembly** — a pack that bundles the 10 categories + the smoke report + the gap/blocker
   list; readiness is a FIXED `OWNER_REVIEW_REQUIRED` (never Pass/Ready — doc §23; RULE-015).
4. **Gap/blocker list for owner** — the MANDATORY honest list (§4.3): the standing BLOCKED verdicts + every G/H/I/J
   forward condition + OD-011/012 + any incomplete category / un-run smoke. The pack cannot be emitted without it.

**Out of scope (explicit — owner-only / other-owner):**
- **Flipping any gate/flag** (RULE-H01) — nothing enables production/gateway/external_send/scale/publish.
- **Declaring ROAS Pass or Scale Ready** (owner-only, doc §23) — the assembler has NO such method; readiness stays
  `OWNER_REVIEW_REQUIRED`.
- **Self-certifying PASS** (RULE-015 / FAIL-007) — the assembler certifies nothing; it records honest status only.
- **Re-authoring / re-executing the smokes** (that is the TESTER's, M6-P2003/2004), pricing (M3), consult (M4),
  public reply (M5), live-ops (M7), order-state (M8), CRM send, commission (Finance). No new API/table/flag.

---

## 4. Locked doc content (build to the exact spec)

### 4.1 The 18 P0 smokes (SMOKE_REGISTER, doc §21 + proposed hardening)

`SMK-001` event-not-in-registry → reject/HOLD · `SMK-002` valid event missing consent → no external/audience ·
`SMK-003` duplicate Pixel/CAPI/Offline → dedup · `SMK-004` quote not order → no revenue/ROAS · `SMK-005` order
draft/created not verified → not revenue · `SMK-006` ORDER_VERIFIED full source → dashboard updates · `SMK-007`
ORDER_VERIFIED missing source → revenue stored, attribution LOW/HOLD · `SMK-008` CRM opt-out → no CRM sync ·
`SMK-009` recall/sale-lock → Scale Gate FAIL/HOLD · `SMK-010` Data Mart trigger → FAIL (support view only) ·
`SMK-011` learning candidate outside safe range → hold, no publish · `SMK-012` scale request no owner approval →
no scale · `SMK-013` live/comment/messenger chain → trace ids · `SMK-014` Diamond referral verified → referral
attribution, no self-commission · `SMK-015` dashboard shows quote/draft as revenue → FAIL · **`SMK-016`** (proposed)
outbox retry → dead-letter · **`SMK-017`** (proposed) hash policy no raw PII · **`SMK-018`** (proposed) attribution
immutable after verify → adjustment record. Proposed = executed OR owner-waived (recorded).

### 4.2 The 10 doc §22 evidence categories + mandatory content (English gloss of extract L419–430; category names/keys faithful, cells translated)

| # | Category | Mandatory content (doc §22 "Nội dung bắt buộc", glossed) |
|---|---|---|
| 1 | **Event Registry** | Screenshot/API/DB record proving event codes, owner, policy |
| 2 | **Consent** | consent pass / fail-closed cases, opt-out handling |
| 3 | **Outbox** | conversion/audience outbox queued, sent, retry, error, dead-letter |
| 4 | **Dedup** | Pixel/CAPI/Offline duplicate handled correctly |
| 5 | **Attribution** | ORDER_VERIFIED traced back campaign/adset/ad/page/live/comment/Messenger |
| 6 | **Dashboard** | Revenue Verified / ROAS / CPA / AOV from correct sources |
| 7 | **Scale Gate** | PASS/HOLD/FAIL with owner approval flow |
| 8 | **Learning** | candidate → review → approve/reject/hold → rollback |
| 9 | **Security/Privacy** | no raw PII, consent, hash policy, access control |
| 10 | **Smoke Report** | P0 smoke result with correlation_id + evidence_id |

### 4.3 The MANDATORY gap/blocker list (canonical honesty payload — RULE-015 / FAIL-007)

The pack MUST carry (never drop): standing BLOCKED judge verdicts **M6-P1000** (M6.2A entry) + **M6-P1309** (M6.2D
exit); **M6.2G** scale forward conditions (ENTRY-001/003 real-scale, four M6-P1600 attestation true-ups, ENTRY-004
M5 DEBT-1..4 + P4 re-gate, ACCESS-1/F-SCALE-*, OD-002/003/004/005); **M6.2H** learning (OD-006 safe range, OD-007
content fill, F-LEARN-*); **M6.2I** funnel (F-FUNNEL-4 single-subject trace bind, F-SEC-2I-2); **M6.2J** growth
(F-GROWTH-1 CRM subject-bind, F-GROWTH-3 verified_rows ORDER_VERIFIED choke, F-SEC-2J-*); **M6-OD-011** admin-endpoint
authN/authZ + **M6-OD-012** masking scope; plus any INCOMPLETE category / un-run-or-un-waived smoke. This is encoded
canonically so the assembler cannot emit a pack that omits it.

### 4.4 The ONE readiness rule (reconciled — no other definition governs)

`readiness = NOT_READY` **iff** (any of the 10 categories is INCOMPLETE) **OR** (any of the 18 smokes lacks a
recorded result — a proposed smoke SMK-016/017/018: a result OR a recorded owner waiver); **else**
`OWNER_REVIEW_REQUIRED`. There is **no** Pass/Ready state (owner-only at PR/PILOT, doc §23). The
`STANDING_GAP_BLOCKERS` (§4.3) are **always disclosed** in the pack's gap/blocker list but **do NOT by themselves
gate readiness** — production stays BLOCKED regardless of readiness, and reviewing those standing blockers IS the
owner's job. So a fully-assembled pack (all categories complete, all smokes recorded/waived) reaches the terminal
`OWNER_REVIEW_REQUIRED` **while still disclosing** every standing blocker — the honest hand-off state. This rule
supersedes any looser "open blocker" phrasing elsewhere in this plan.

---

## 5. Minimal change set (all target-relative, staged under `04-artifacts/impl/M6.2K/`)

Legend: **Leg** = M6.2K exit-gate leg — **L1** = *evidence pack ready for review* (P0 re-run + 10 §22 categories +
owner package + gap/blocker list). Rollback: new files → delete (no carried-forward file is patched).

### 5.1 New — the `evidence/` assembly package (read-only, no self-cert)

| # | Target file (new) | Purpose | Contract/Rule | Leg | Smoke |
|---|---|---|---|---|---|
| C1 | `app/measurement/evidence/__init__.py` | package marker (assembly-only; no self-cert; no flag flip; no new table). | — | — | — |
| C2 | `app/measurement/evidence/smoke_registry.py` | the canonical 18 smoke ids (SMK-001..018) + scenario/expected (verbatim doc §21) + bound test-file refs + `owner`/`proposed` status. A proposed smoke needs EITHER an executed result OR a recorded owner waiver. | RULE-015 | **L1** | all 18 |
| C3 | `app/measurement/evidence/categories.py` | the 10 doc §22 evidence categories + each category's mandatory-content requirement keys (per §4.2; category-1 keeps the "Screenshot/API/DB record" proof-form to match the slice exit-gate). | CTR-025 | **L1** | — |
| C4 | `app/measurement/evidence/models.py` | frozen `SmokeResult{smoke_id, status, correlation_id, evidence_id, waived}` + `CategoryStatus{category, complete, present, missing}` + `GapBlocker{id, kind, description, owner}` + `EvidencePack{categories, smokes, gap_blockers, readiness, posture}`. `to_public()` masks any PII; readiness enum has NO "PASS/READY" member (only `OWNER_REVIEW_REQUIRED` / `NOT_READY`). | CTR-025; RULE-014/015 | **L1** | — |
| C5 | `app/measurement/evidence/gap_blockers.py` | the canonical `STANDING_GAP_BLOCKERS` list (§4.3) — the BLOCKED verdicts + G/H/I/J forward conditions + OD-011/012 — encoded so the pack always carries them. | RULE-015/FAIL-007 | **L1** | — |
| C6 | `app/measurement/evidence/pack_assembler.py` | `EvidencePackAssembler.assemble(smoke_results, evidence_refs)` → `EvidencePack`: marks each category COMPLETE only when its mandatory content is present (else INCOMPLETE, fail-closed); builds the smoke report (correlation_id + evidence_id per smoke; a proposed smoke un-run AND un-waived ⇒ a gap); ALWAYS merges `STANDING_GAP_BLOCKERS` (disclosed, never dropped) + derived gaps; sets readiness per the ONE rule (§4.4): `NOT_READY` iff any category INCOMPLETE OR any of the 18 smokes lacks a recorded result/waiver, else `OWNER_REVIEW_REQUIRED` — the standing blockers are disclosed but do NOT by themselves gate readiness (production stays BLOCKED regardless; NEVER Pass/Ready); records the immutable posture (BLOCKED/OFF/OFF). **NO** `pass`/`ready`/`certify`/`sign_off`/`enable`/flag-flip method (RULE-015; doc §23). | **CTR-025**; **RULE-015/FAIL-007** | **L1** | — |

### 5.2 Migrations & config

**None.** No new table (doc §13 defines no evidence-pack table — inventing one breaches RULE-018; the pack is an
assembled artifact over the existing smoke suite + recorded evidence). No new config flag (assembly-only; the
posture flags already fence everything). Both omissions are deliberate minimal-change calls.

---

## 6. Test plan → done-gate / smoke mapping (`pytest -q`; TESTER re-runs the P0 matrix + records results)

Fixtures extend `conftest.py` with an `EvidencePackAssembler`, sample smoke-result + evidence-ref builders (all
synthetic; no raw PII). Carried-forward M6.2J tests + the full 18-smoke suite stay green. PII markers assembled at
runtime.

| # | Target test (new) | Proves | Leg | Fail-gate |
|---|---|---|---|---|
| T1 | `tests/test_evidence_ten_categories_mandatory_content.py` | all 10 doc §22 categories present; a category missing its mandatory content is **INCOMPLETE** (fail-closed) → the pack is `NOT_READY` (FAIL-007). | **L1** | **FAIL-007** |
| T2 | `tests/test_smoke_registry_complete_18.py` | the registry lists all 18 smoke ids with scenario/expected/bound-files; SMK-016/017/018 are `proposed` and require an executed result OR a recorded owner waiver. | L1 | — |
| T3 | `tests/test_gap_blocker_list_carries_standing_blockers.py` | the pack ALWAYS carries the canonical gap/blocker list (M6-P1000 + M6-P1309 BLOCKED, G/H/I/J forward conditions, OD-011/012); the assembler cannot emit a pack that omits them; **the standing blockers are disclosed but do NOT force `NOT_READY`** (§4.4). | **L1** | **FAIL-007** |
| T4 | `tests/test_pack_never_declares_pass_or_ready.py` | the readiness enum has no PASS/READY member; per §4.4 a fully-complete pack (all categories complete, all smokes recorded/waived) reaches `OWNER_REVIEW_REQUIRED` **while still disclosing** the standing blockers, and any incomplete category / un-recorded smoke ⇒ `NOT_READY`; the assembler exposes NO pass/ready/certify/sign_off/enable/flag-flip method (RULE-015; doc §23). | **L1** | — |
| T5 | `tests/test_pack_posture_immutable_and_pii_safe.py` | the pack records the immutable posture (BLOCKED/OFF/OFF + all flags) and exposes no method to change it; every export is PII-safe (correlation_id/evidence_id masked; no raw PII). | L1 | — |
| T6 | `tests/test_full_p0_matrix_runs_green.py` | a meta-check that the carried 18-smoke suite collects + runs (a coder-level smoke-suite sanity check; the OFFICIAL P0 re-run + recorded results is the TESTER's, RULE-015). | L1 | — |

**Smoke → test binding**: the OFFICIAL P0 re-run (all 18, recorded correlation_id + evidence_id) + the completed
owner-review package is the TESTER's (M6-P2003 build / M6-P2004 run → `04-artifacts/test-reports/M6.2K/`) and the
PM evidence-collect's (M6-P2007). The CODER provides the registry + assembler + the fail-closed/no-self-cert
discipline. No self-run / self-certify (RULE-015).

---

## 7. Master traceability matrix

| Item | Files | Contract | Rule(s) | Leg | Fail-gate | Rollback |
|---|---|---|---|---|---|---|
| Smoke registry (18) | C2 | — | RULE-015 | **L1** | — | delete |
| 10 §22 categories | C3 | CTR-025 | — | **L1** | FAIL-007 | delete |
| Pack result models (no PASS/READY) | C4 | CTR-025 | RULE-014/015 | **L1** | — | delete |
| Canonical gap/blocker list | C5 | — | RULE-015/FAIL-007 | **L1** | FAIL-007 | delete |
| Pack assembler (fail-closed, no self-cert) | C6 | **CTR-025** | **RULE-015/FAIL-007** | **L1** | FAIL-007 | delete |
| Tests | T1–T6 | — | — | L1 | FAIL-007 | delete |

**Legs**: L1 (evidence pack ready for review — the 10 categories + smoke registry + gap/blocker list + no-self-cert,
T1–T6) ✓. The 18 smoke-execution legs + the completed owner package are the TESTER's (M6-P2003/2004) + PM's
(M6-P2007); judge (M6-P2009), docs (M6-P2008) are downstream process legs.

---

## 8. Rollback strategy (global)

1. **Nothing declared / nothing flipped.** Staged under `04-artifacts/impl/M6.2K/`; no migration (none added), no
   flag written, no Pass/Ready declared. Baseline rollback = delete the M6.2K tree (M6.2J untouched).
2. **Per-item** (§5): new `evidence/` files → delete; **no carried-forward file is patched** (the smoke suite runs
   as-is).
3. **The assembler is pure** — it reads smoke results + evidence refs and returns a report object; it writes nothing
   to any store and changes no posture. Removing it leaves the carried tree exactly as M6.2J left it.

---

## 9. Plan-deltas & notes

- **No self-certification, no Pass/Ready (RULE-015 / FAIL-007 / doc §23)** — the load-bearing constraint. The
  assembler certifies nothing; readiness is `OWNER_REVIEW_REQUIRED`/`NOT_READY`; there is no pass/ready/certify/
  flag-flip method. The owner declares ROAS Pass / Scale Ready at PR/PILOT, not this code.
- **Fail-closed evidence + the ONE readiness rule (§4.4, FAIL-007)** — readiness is `NOT_READY` iff any category is
  INCOMPLETE OR any of the 18 smokes lacks a recorded result/waiver; else `OWNER_REVIEW_REQUIRED` (never Pass/Ready).
  The pack never overstates readiness.
- **Mandatory honest gap/blocker list (§4.3)** — encoded canonically (M6-P1000 + M6-P1309 BLOCKED, G/H/I/J forward
  conditions, OD-011/012); ALWAYS disclosed but NOT a readiness gate (§4.4 — production stays BLOCKED regardless);
  the assembler cannot emit a pack that drops it.
- **No new table / migration / CTR / config flag (RULE-018)** — the pack is an assembled artifact (Evidence layer,
  ARCH §1.9) over the existing smoke suite + recorded evidence; doc §13 defines no evidence-pack table.
- **No raw PII / secrets (RULE-014/H02)** — the pack carries refs + correlation_id/evidence_id only; PII masked.
- **Module boundary intact** — no smoke re-authoring (TESTER), no pricing/consult/reply/live-ops/order-state/CRM
  send/commission; assembly-only.
- **Governance unchanged** — `M6-P1000` + `M6-P1309` verdicts stay BLOCKED (not converted) and appear IN the pack;
  the G/H/I/J forward conditions remain hard gates and appear IN the pack; production/gateway/external_send stay
  immutably OFF through M6.2K and into PR/PILOT.
- **Ultracode note** — this plan was reviewed by an independent adversarial design red-team (§ below) driving the
  claims against the real M6.2J tree + registers before finalizing.

---

## 10. Acceptance self-map

1. *Every item → leg or smoke* → §5–§7. ✓  2. *Rollback per item* → §5/§8. ✓  3. *No scope beyond the slice* →
§3 (no flag flip / Pass-Ready declaration / smoke re-authoring; assembly-only). ✓  4. *Target LOCKED + M6-OD-011
decided* → §1. ✓  5. *Reuse conventions / test patterns from the locked target* → §2 (M6.2J baseline; the carried
18-smoke suite). ✓  Plus the **load-bearing invariants**: no self-certify / no Pass-Ready (RULE-015/FAIL-007, T4),
fail-closed evidence (FAIL-007, T1/T3), mandatory honest gap/blocker list (T3), no invented schema (RULE-018),
PII-safe (T5) — each with a test and the M6.2J suite (incl. all 18 smokes) staying green.

*Plan-only: no code, no migration, no flag flipped, no Pass/Ready declared, no self-certification;
`global_gateway_state=BLOCKED`, `production_flag=OFF`.*
