# BOUNDARY CRITIQUE — RESEARCH_STRATEGY_LIBRARIES.md

**Critic prompt**: M6-PC0211 (RESEARCH_STRATEGY_LIBRARIES_CRITIC) · **Role**: BOUNDARY_ADVERSARY · **Mode**: analysis_only
**Target**: `04-artifacts/analysis/research/RESEARCH_STRATEGY_LIBRARIES.md` (produced by M6-P0211 — the last Phase-0 research prompt)
**Author does not respond here.** Findings feed Phase-0 design, the producing prompt M6-P0710 (`ads_learning_candidate`), and slice M6.2H.

> `global_gateway_state` stays **BLOCKED**, `production_flag` stays **OFF**. This file invents no seed, publishes nothing, flips no flag. Self-report; the runner gate decides PASS.

---

## 1. Entry gate (verified before review)

| Check | Result | Evidence |
|---|---|---|
| M6-PC0211 is RUNNING in the ledger | ✅ | `PROMPT_EXECUTION_LEDGER_LOCKED.csv` row 51 — `M6-PC0211 … BOUNDARY_ADVERSARY … RUNNING` |
| Dependency M6-P0211 is complete | ✅ | ledger row 50 — `M6-P0211 … PASS`; evidence `M6-P0211.json` status=PASS |
| Required inputs present | ✅ | brief, `RESEARCH_STRATEGY_LIBRARIES.md`, `M6-P0211.json` all read |
| §17 six-library + mapping + registers | ✅ | extract §17 L338–345 (six libraries verbatim), L336 (mapping chain), L351 (Learn 5 dims), L330/L349; OD-001 (L478)/OD-006/OD-007 (L484), LEX-001/002/005/006, CTR-003/014/020/001/002, SMK-011, RULE-011 all verified faithful; owner-decision table §25 tag verified correct |

Entry gate holds; review proceeded.

## 2. Method

Direct citation/register/slice verification plus an adversarial **find → refute-verify** pass: 5 finder lenses (**invented-seed**, **seed-source verbatim fidelity**, **proposal-vs-owner-requirement**, **citation/tag precision**, **missing-owner-decision/boundary**) surfaced candidates; 6 lead-grounded seeds were merged in; each candidate was handed to a separate verifier told to **try hard to refute it** and grade. **11 candidates verified; 3 confirmed distinct defects, the rest refuted** (the invented-seed and seed-source lenses returned empty). Hermetic mode (no web-fetch).

Severity rubric: **BLOCKER** = an **invented seed** (a concrete persona/keyword/hook/landing/CTA presented as content = the LEX-006 forbidden cell) / softened LEX-006/RULE-011 into full-auto-publish / a mapping node scale-eligible without a registered `event_code` or `verified_revenue_binding` / a `[PACK]`/`[EXT]` proposal stamped owner-mandated / public copy while the banned-word table is MISSING / safe-range creep into budget-scale / raw PII; **MAJOR** = would cause such a breach *if a coder followed the text* but mitigated; **MINOR** = citation/tag precision, dependency-list completeness, or a slip that errs fail-closed.

## 3. Overall verdict

**No BLOCKER, no MAJOR.** A disciplined "three razor-apart layers" artifact (LOCKED / SCHEMA-proposal / CONTENT-BLOCKED). The crux attacks were **refuted**:

- **Invented-seed — none (the crux axis).** The dedicated lens returned **empty**. §1's six-library table is verbatim from extract L338–345; §2's enum values (`content_block_sku`, `spam|troll|low_intent|fake_order`, `hero_sku|golden_hour|diamond|crm_reorder`, `acquisition|intent`) are **structural echoes of the doc's seed-SOURCE column**, not fabricated seeds; §5 marks every CONTENT cell **BLOCKED**. "Golden Hour Tri Ân" / "Hero SKU" / "Diamond" appear only inside verbatim seed-SOURCE / LEX-002 quotes (owner program-source names), never as machine-authored copy. The `[REG LEX-006]` "no fabricated origin strategy" boundary holds.
- **Proposals correctly quarantined.** The per-library schema (§2), mapping record (§3), and score fields (§4) are consistently tagged `[PACK]`/`[EXT]`; §8 L214 lists all five as "owner-review proposals, **NOT owner requirements**." Only the verbatim owner-mandated chain **order** (L336) stays `[DOC]`.
- **Mapping fail-closed.** §3 L124–127: a node with an unregistered `event_code` (RULE-001) or absent `verified_revenue_binding` is "unmeasurable ⇒ **not scale-eligible** — fail-closed." Behavior/Negative-Keyword scoring is flagged `[EXT]` candidate (not in the doc's 5-dim Learn list), "flagged for the owner rather than silently added."
- **§25 owner-decision tag verified correct.** The `[DOC §25 L478/L484]` citations for OD-001/OD-007 are accurate in both section number and line numbers.

The confirmed defects are **3 MINOR** — all citation/precision or completeness, fail-safe.

| ID | Severity | Category | One-line |
|---|---|---|---|
| F1 | MINOR | tag precision | §7 header L192 `[BRIEF / REG §18]` and §7 body L200 `[REG §18]` tag DOC section §18 as a register — correct `[DOC §18]`; **8th pack-wide occurrence**, two hits in this file |
| F2 | MINOR | citation precision | intro L18 quotes *"machine tự bịa chiến lược gốc"* tagged `[REG LEX-006]`, but that exact phrase is the **§17 L349** Seed-stage wording; LEX-006's actual cell (doc §4 L80) reads *"bịa persona/keyword/hook gốc"* |
| F3 | MINOR (borderline) | completeness | §6, self-billed "explicit list — acceptance requirement," omits `M6-CTR-003` (event_registry, MISSING→P0701) that §3's mapping Event node depends on — counter-argument: principled scope (see below) |

---

## 4. Confirmed findings

### F1 — MINOR — `[REG §18]` tags a DOC section as a register (recurring, two occurrences)
**Category**: tag precision · **Verdict**: CONFIRMED MINOR (three verifiers)

**Exact claim:** §7 header L192 "## 7. Boundary & safety guards `[BRIEF / REG §18]`"; §7 body L200 "…learning ≠ scale (safe range excludes budget/scale — that is the Scale Gate + M6-OD-002) `[REG §18]`".

**Evidence:** extract **L355** "## 18. Tích hợp với Module 3, 4, 5, 7, 8" is a **DOC** module-boundary section; no locked register is numbered "§18" (registers are ID-scoped: OD/LEX/RULE/CTR). The file's own legend (L23–26) reserves `[REG]` for locked registers.

**Defect:** citation hygiene — mislabels a DOC section as a register (over-attributes authority; fail-safe). The §7 claims (learning ≠ scale, safe range excludes budget/scale, no full-auto-publish) are independently backed by RULE-011/LEX-006/M6-OD-002. **Fix (pack-wide):** retag `[DOC §18]`. This is the **8th occurrence** of the identical nit (PC0204 F5 / PC0205 F2 / PC0206 F2 / PC0207 F1 / PC0208 F2 / PC0209 F1 / PC0210 F1) — normalize once.

### F2 — MINOR — the L18 "forbidden cell" quote is the §17 L349 Seed-stage wording, not LEX-006's text
**Category**: citation precision · **Verdict**: CONFIRMED MINOR (surfaced by the invented-seed + citation lenses)

**Exact claim (intro blockquote L18):** "Inventing a seed is exactly *'machine tự bịa chiến lược gốc'* — the doc's FORBIDDEN cell `[REG LEX-006]`."

**Evidence:** the quoted phrase *"…machine tự bịa chiến lược gốc"* is the **Seed-stage** row at extract **§17 L349** ("Fill thư viện… không để machine tự bịa **chiến lược gốc**"). LEX-006's actual cell (doc §4 L80, LEXICON_REGISTER L15) reads *"Cho machine tự publish toàn quyền hoặc bịa **persona/keyword/hook gốc**"* — a different phrasing.

**Defect:** the exact quoted words are attributed to the wrong source line — they belong to L349, while LEX-006 is the *semantically equivalent* register cell (both = no fabricated origin strategy). **Substance is correct** (LEX-006 does forbid this), only the quote↔citation pairing is imprecise. **Fix:** attribute the quote to `[DOC §17 L349]` (Seed stage) and keep `[REG LEX-006]` as the normative register anchor, or quote LEX-006's own words.

### F3 — MINOR (borderline) — §6 "explicit list" omits the CTR-003 the mapping Event node depends on
**Category**: dependency-list completeness · **Verdict**: SPLIT — one verifier CONFIRMED MINOR, one REFUTED as principled scope

**Exact claim:** §6 header L178 "## 6. Owner-decision & contract dependencies (**explicit list — acceptance requirement**)" lists CTR-014→P0710 and CTR-020→P0712 but **not** `M6-CTR-003` (event_registry).

**Evidence:** §3 L118 ("`event_code` → Core `event_registry` (RULE-001; must be registered)") and L126 make the mapping's Event node depend on the registered `event_registry`, whose consumed shape is `M6-CTR-003` (CONTRACT_REGISTER L19: CONSUMED, **MISSING**, →M6-P0701).

**Why borderline / counter-argument:** the omission errs **fail-closed** and is defensibly **principled scope** — CTR-003 is a **CONSUMED, cross-cutting** shape gated **upstream at M6.2A** (before this file's slice M6.2H), produced by a different prompt (P0701), and already tracked in `[[RESEARCH_CROSS_MODULE_CONTRACTS]]` §5 / `[[RESEARCH_EVENT_REGISTRY_INTEGRATION]]`; §6 deliberately scopes to the **M6-owned** contracts that block M6.2H (CTR-014/020), and CTR-001/002 (also §3-referenced, DRAFT_LOCKED) are likewise excluded. The dependency is **surfaced and fail-closed-gated in §3**, so nothing is loosened. **What tips it to worth-noting:** §6's own "explicit list — acceptance requirement" framing invites completeness. **Fix (optional):** add a one-line cross-reference in §6 ("mapping Event node also depends on CTR-003 event_registry, gated upstream at M6.2A — see [[RESEARCH_CROSS_MODULE_CONTRACTS]]"), or narrow §6's header to "M6-owned M6.2H-blocking contracts." Advisory, not blocking.

---

## 5. Attacked and dismissed (did not survive adversarial verification)

1. **An invented seed appears somewhere (crux).** DISMISSED (two verifiers, lens empty) — every concrete string is a verbatim seed-SOURCE cell, a structural enum echo of it, or an explicit BLOCKED placeholder; "invents zero seeds" holds.
2. **A six-library cell is paraphrased / a library is fabricated.** DISMISSED — §1 L46–51 verify cell-by-cell against extract L340–345; the "source constraint not content list" framing is correct.
3. **A `[PACK]`/`[EXT]` proposal is presented as an owner requirement.** DISMISSED — schema/mapping/score are consistently proposal-tagged; §8 L214 quarantines all five as "NOT owner requirements."
4. **A mapping node is scale-eligible without event/revenue binding, or Behavior/Neg-keyword scoring is doc-mandated.** DISMISSED — §3 L124–127 is fail-closed; §4 L146–149 flags the extra scoring as `[EXT]` candidate.
5. **The `[DOC §25]` owner-decision tag has the wrong section number.** DISMISSED — verified: the owner-decision table is doc §25; section and line numbers both accurate.
6. **The banned-word table / public-copy gate is loosened.** DISMISSED — §2/§4/§7 hard-gate Creative Hook public copy behind the MISSING banned-word table (M6-OD-007); framework-only until locked.

## 6. Acceptance-check trace

- [x] Every finding cites the exact claim and its evidence (research section/line + source file line/id).
- [x] Verdict per finding: BLOCKER/MAJOR/MINOR — 0 BLOCKER, 0 MAJOR, 3 MINOR (F1–F3; F3 flagged borderline with its counter-argument).
- [x] No raw secret or unmasked PII (only register/extract/research text quoted; no channel-origin data present).
- [x] Nothing self-certified PASS; `04-artifacts/state/` untouched; gateway BLOCKED / production OFF unchanged; no seed invented, no owner decision resolved.
