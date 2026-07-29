# BOUNDARY CRITIQUE — RESEARCH_LEARNING_ENGINE_GUARDRAILS.md

**Critic prompt**: M6-PC0209 (RESEARCH_LEARNING_ENGINE_GUARDRAILS_CRITIC) · **Role**: BOUNDARY_ADVERSARY · **Mode**: analysis_only
**Target**: `04-artifacts/analysis/research/RESEARCH_LEARNING_ENGINE_GUARDRAILS.md` (produced by M6-P0209)
**Author does not respond here.** Findings feed Phase-0 design, the producing prompt M6-P0710 (`ads_learning_candidate`) / M6-P0712 (API), and slice M6.2H.

> `global_gateway_state` stays **BLOCKED**, `production_flag` stays **OFF**. Nothing here publishes anything; an `ads_learning_candidate` is only data. Self-report; the runner gate decides PASS.

---

## 1. Entry gate (verified before review)

| Check | Result | Evidence |
|---|---|---|
| M6-PC0209 is RUNNING in the ledger | ✅ | `PROMPT_EXECUTION_LEDGER_LOCKED.csv` row 47 — `M6-PC0209 … BOUNDARY_ADVERSARY … RUNNING` |
| Dependency M6-P0209 is complete | ✅ | ledger row 46 — `M6-P0209 … PASS`; evidence `M6-P0209.json` status=PASS |
| Required inputs present | ✅ | brief, `RESEARCH_LEARNING_ENGINE_GUARDRAILS.md`, `M6-P0209.json` all read |
| §17 + §9 + registers + M6.2H slice claims | ✅ | extract §17 L326–353 (seed L328, learn-precondition L330, no-full-auto-publish L332, tie L334, lifecycle L349–353, guarded-auto-publish L353), §9 L177 KPIs, §4 L80 forbidden cell, RULE-011, LEX-006, SMK-011, OD-006/007, LEXICON banned-word table all verified faithful |

Entry gate holds; review proceeded.

## 2. Method

Direct citation/register/slice/smoke verification plus an adversarial **find → refute-verify** pass: 5 finder lenses (**full-auto-publish-path**, **learn-on-dirty/unseeded**, **safe-range-creep-and-execute**, **citation/tag precision**, **missing-owner-decision/completeness**) surfaced candidates; 5 lead-grounded seeds were merged in; each of the 10 candidates was handed to a separate verifier told to **try hard to refute it** and grade severity. **10 candidates verified; 2 confirmations collapsing to 2 distinct issues, 8 refuted.** Hermetic mode (no web-fetch).

Severity rubric: **BLOCKER** = an executable/live full-auto-publish path in M6 / softening RULE-011/LEX-006 into full auto-publish / learning on unclean-or-unseeded data / auto-publish while M6-OD-006 undefined / public ad copy while the banned-word table is MISSING / safe-range creeping into budget-scale / fabricating an owner requirement / raw PII; **MAJOR** = would cause such a breach *if a coder followed the text* but mitigated; **MINOR** = citation/tag precision, provenance slip, or a low-impact slip in the fail-closed (safer) direction.

## 3. Overall verdict

**No BLOCKER, no MAJOR.** A boundary-tight artifact on the pack's highest runaway-risk component. Every crux attack was **refuted**:

- **Full-auto-publish path — none.** The full-auto-publish lens returned an **empty list**. `[REG RULE-011]` itself *permits* "guarded auto-publish inside the owner-approved safe range, with rollback and audit" — the research keeps that faithful **and** gated: `M6-OD-006` OPEN ⇒ auto-publish **BLOCKED entirely** (§4 L82–83), `production_flag=OFF` ⇒ staged (§7 L123). Default path is review-queue-only (§3, `[DOC L332]`). No softening of RULE-011/LEX-006.
- **Learn only on seeded, clean data — held.** §2/§5 restate `[DOC L330]` / RULE-011 faithfully: no seed ⇒ no learn; unclean/unverified ⇒ excluded; provenance without a canonical `seed_source_ref` is **rejected**, not "flagged". DQ whitelist intact.
- **Auto-rollback / auto-pause are not a rogue execute path.** `[DOC §17 L353]` + RULE-011 **mandate** "có rollback"; "pause auto-publish" on repeated drift is fail-closed and moot while publish is already BLOCKED/OFF — it restricts, never executes.
- **Safe range does not creep into budget/scale.** §6.1 (L110–111) explicitly excludes budget/scale ("never the learning safe range"); §7 L124 "learning ≠ scale". §8's "links M6-OD-002 family" is a numeric-relatedness cross-reference, not ownership of the scale action.
- **No fabricated owner requirement.** §9 traceability stamps only genuine `[DOC]`/`[REG]` rows "owner-mandated" and correctly marks candidate-lifecycle / provenance / drift-threshold / safe-range parameterization as `[EXT]/[PACK]` **owner-review proposals, NOT owner requirements**. *(This file does **not** carry the "HIGH-confidence over-restriction stamped owner-mandated" defect seen in PC0206 F1 / PC0207 F2 / PC0208 F1 — that pattern was not force-fit here.)*

The confirmed defects are **2 MINOR** — both citation/tag precision, fail-safe.

| ID | Severity | Category | One-line |
|---|---|---|---|
| F1 | MINOR | tag precision | §7 header L118 `[BRIEF / REG §18]` and §7 body L124 `[REG §18]` tag DOC section §18 (module-boundary table, extract L355) as a **register** — correct `[DOC §18]` / `[BRIEF/DOC §18]`; **6th pack-wide occurrence** (PC0204 F5 / PC0205 F2 / PC0206 F2 / PC0207 F1 / PC0208 F2) |
| F2 | MINOR | citation precision | header L4 anchor `[DOC §17 extract lines 325–353]` starts one line early — §17 heading is at extract **L326**; L325 is the boundary line after §16's Approval row. Correct: **326–353** |

---

## 4. Confirmed findings

### F1 — MINOR — `[REG §18]` tags a DOC module-boundary section as a locked register (recurring)
**Category**: tag precision · **Verdict**: CONFIRMED MINOR (two verifiers)

**Exact claim:** §7 header L118 "## 7. Boundary & safety guards `[BRIEF / REG §18]`"; reasserted §7 body L124 "No pricing/order/CRM/commission side effects; no scale action (learning ≠ scale) `[REG §18]`".

**Evidence:** extract **L355** "## 18. Tích hợp với Module 3, 4, 5, 7, 8" is a **DOC** section — the module-integration boundary table with the "Module 6 không được làm gì" column (L357–362) — surfaced in `ENTRY_EVIDENCE_REGISTER` as "Consumed-boundary reference (doc §18)". The file's own legend (L17) reserves `[REG]` for locked pack registers (ID-keyed) and cites every real register by ID (RULE-011 / LEX-006 / CTR-014 / SMK-011 / OD-006), using bare "§N" only for DOC sections (`[DOC §17]`, `[DOC §9]`, `[DOC §4]`). So "§18" cannot resolve to a register.

**Defect:** a citation-precision slip that also demotes an owner-**DOC** boundary to a mere register reference. No boundary harm — the §7 guards are independently re-grounded (RULE-011/LEX-006 at L120, RULE-014 at L125, BRIEF rule 6 at L126, and the boundary content itself maps to §18's DOC table). Fail-safe (if anything it **under**-claims owner-requirement status). **Fix (pack-wide):** retag `[DOC §18]` (header `[BRIEF / DOC §18]`); this is the **6th occurrence** of the identical nit across the Phase-0 research files — normalize once.

> Note: the lead's seed prose mislocated the second occurrence as "§5 L124"; a verifier corrected it — L124 sits in **§7** (§5 = Drift detection, L93–104). The mis-tag on both L118 and L124 is real; the section label is corrected here.

### F2 — MINOR — the §17 anchor range starts one line before the section heading
**Category**: citation precision · **Verdict**: CONFIRMED MINOR (one verifier)

**Exact claim:** header L4 "**Anchors**: `[DOC §17 extract lines 325–353]` ADS Strategy Input Pack & Learning Engine".

**Evidence:** in `M6_FULL_DETAIL_EXTRACT.md` the §17 heading "## 17. ADS Strategy Input Pack và Learning Engine" is at **L326**; **L325** is the boundary line immediately after §16's "| Approval | Owner duyệt scale request… |" row (L324). So §17's content spans **326–353**, and the anchor's start line "325" pulls in one extraneous boundary line.

**Defect:** a trivial off-by-one in the outer summary anchor only — **every inner citation is correct** (L328/L330/L332/L334/L349–353 all verified faithful). No substance affected; nothing a coder would mis-build. **Fix:** state the anchor as "extract lines 326–353".

---

## 5. Attacked and dismissed (did not survive adversarial verification)

1. **Full-auto-publish / softened RULE-011.** DISMISSED (lens returned empty) — guarded auto-publish is the doc/register-permitted capability (RULE-011), kept BLOCKED (OD-006 OPEN) and staged (production OFF); review-queue is the default.
2. **`banned-word/claim table MISSING → OD-007 → no public copy` conflates OD-007 with a fabricated LEXICON table.** DISMISSED — `LEXICON_REGISTER` L21–25 ("## Missing banned-word table") **explicitly** declares the banned-word/claim blacklist MISSING / OWNER_DECISION_REQUIRED, **links it to M6-OD-007**, and states "until supplied, learning/creative prompts stop at framework level and never generate public copy." The research is register-grounded and faithful.
3. **Auto-rollback / auto-pause is an M6 execute path.** DISMISSED (two lenses) — `[DOC L353]`/RULE-011 mandate "có rollback"; "pause auto-publish" is fail-closed and moot while publish is BLOCKED/OFF; nothing fires live.
4. **§2's `L334` tie (sellable SKU/program/policy/public claim/brand) is unsatisfiable while OD-007 OPEN, leaving a publish gap.** DISMISSED — auto-publish is BLOCKED entirely (OD-006 OPEN) and public copy is blocked (banned-word table MISSING), so no candidate can publish without the tie; §2 L56 makes the un-anchored optimization **invalid** by construction.
5. **§8 omits M6-OD-004 (connector) / M6-OD-005 (attribution) / M6-OD-001 (Hero SKU).** DISMISSED — `DECISION_REGISTER` scopes those to **other** slices (OD-004→M6.2D, OD-005→M6.2E/G scale evidence, OD-001→M6.2A pilot config); slice M6.2H references **only** OD-006 and OD-007, both of which §8 lists. Importing OD-005 would re-entangle the scale/learning domains the doc deliberately separates (§6.1). §8 is faithful and complete for its declared M6.2H scope; the footer already marks any needing leg BLOCKED.
6. **§8 "links M6-OD-002 family" couples the learning safe range to the scale-threshold decision.** DISMISSED — it is a numeric-relatedness cross-reference for drift/uplift alert thresholds, not an ownership/control coupling to the scale action; §6.1 (L111) and §8's own "What it gates" = "§5 rollback triggers" keep the scale-action boundary intact.
7. **Provenance enforcement is merely "flagged" / learn could run on dirty data.** DISMISSED — §2 states an entry lacking canonical provenance is **rejected** (fail-closed) and Learn consumes **only** DQ-passed verified signals; faithful to L330 / RULE-011.

## 6. Acceptance-check trace

- [x] Every finding cites the exact claim and its evidence (research section/line + source file line/id).
- [x] Verdict per finding: BLOCKER/MAJOR/MINOR — 0 BLOCKER, 0 MAJOR, 2 MINOR (F1–F2).
- [x] No raw secret or unmasked PII (only register/extract/research text quoted; no channel-origin data present).
- [x] Nothing self-certified PASS; `04-artifacts/state/` untouched; gateway BLOCKED / production OFF unchanged; nothing published, no owner decision resolved.
