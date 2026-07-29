# BOUNDARY CRITIQUE — RESEARCH_ATTRIBUTION_MODELS.md

**Critic prompt**: M6-PC0206 (RESEARCH_ATTRIBUTION_MODELS_CRITIC) · **Role**: BOUNDARY_ADVERSARY · **Mode**: analysis_only
**Target**: `04-artifacts/analysis/research/RESEARCH_ATTRIBUTION_MODELS.md` (produced by M6-P0206)
**Author does not respond here.** Findings feed Phase-0 design, the owner decision M6-OD-005, and slice M6.2E.

> `global_gateway_state` stays **BLOCKED**, `production_flag` stays **OFF**. Nothing here flips a gate or a flag, and it selects no model. Self-report; the runner gate decides PASS.

---

## 1. Entry gate (verified before review)

| Check | Result | Evidence |
|---|---|---|
| M6-PC0206 is RUNNING in the ledger | ✅ | `PROMPT_EXECUTION_LEDGER_LOCKED.csv` row 41 — `M6-PC0206 … BOUNDARY_ADVERSARY … RUNNING` |
| Dependency M6-P0206 is complete | ✅ | ledger row 40 — `M6-P0206 … PASS`; evidence `M6-P0206.json` status=PASS |
| Required inputs present | ✅ | brief, `RESEARCH_ATTRIBUTION_MODELS.md`, `M6-P0206.json` all read |

Entry gate holds; review proceeded.

## 2. Method

Direct citation/schema verification plus an adversarial **find → refute-verify** pass: 5 finder lenses (**model-neutrality**, **scale-evidence-fidelity**, boundary, citation/executability, owner-decisions) surfaced candidates; each was handed to a separate verifier told to **try hard to refute it** and grade severity. **12 candidates verified; 7 confirmed (collapsing to 2 distinct issues), 5 refuted.** Hermetic mode (no web-fetch).

Severity rubric: **BLOCKER** = briefing picks the OD-005 model / computes commission / auto-scales / scale-on-low-confidence / raw PII / resolves an owner decision; **MAJOR** = would cause such a breach or a soft model-recommendation *if followed*, but mitigated; **MINOR** = internal inconsistency, citation/tagging precision, low-impact soft-resolution.

## 3. Overall verdict

**No BLOCKER, no MAJOR.** A clean, disciplined briefing. Every crux attack was **refuted**:
- **OD-005 neutrality holds.** The briefing genuinely compares models without picking one; the "§3 readiness asymmetry (first/last cheap ✅, weighted/cohort data-gap) soft-steers toward the cheaper models" attack was refuted — the asymmetry is factually true, `✅` appears only on clean-YES rows, and the disclaimers (header, §3 L65–67, §7 L118) hold. M6-OD-005 stays OPEN (§6 L102).
- **Boundary is tight.** Diamond/referral attribution is recorded but commission is Finance-owned (RULE-019); no cohort/LTV output computes commission; attribution feeds a scale *proposal*, never auto-scales (RULE-010); the "budget shifts toward acquisition/retargeting" language correctly explains *why the owner decides*, not M6 allocating budget. RULE-008 immutability and citations (`[DOC §25 L482]`, `[DOC §11 L236]`, the 19-field schema) are faithful.

The confirmed defects are **2 MINOR**.

| ID | Severity | Category | One-line |
|---|---|---|---|
| F1 | MINOR | scale-evidence-rule / internal-inconsistency | §1/§4 assert "**only `source_confidence=HIGH`**" as scale-evidence, tagged `[REG RULE-009]` — but RULE-009 only excludes missing/conflict (silent on MEDIUM), and §6 lists the confidence threshold as owner-pending → unsupported cite + soft-resolution (fail-closed-safe) |
| F2 | MINOR | citation precision | §5 header `[REG §18]` labels an owner-DOC section as a register section (correct: `[DOC §18]`); pack-wide header nit |

---

## 4. Confirmed findings

### F1 — MINOR — `HIGH-only` scale-evidence threshold: unsupported `[REG RULE-009]` citation + internal inconsistency with §6
**Category**: scale-evidence-rule / internal-inconsistency · **Verdict**: CONFIRMED MINOR (≈5 verifiers; one finder proposed MAJOR, all verifiers landed MINOR)

**Exact claim (research):**
- §4 L79–80: "Only attributions with **`source_confidence = HIGH`** and `conflict_status = NONE` may count as scale evidence `[REG RULE-009]`; LOW/HOLD/conflicting attributions are excluded."
- §1 L38 (same assertion): "`[REG RULE-009]` only **HIGH-confidence**, non-conflicting attribution counts as scale evidence."

**Evidence:**
- `RULES_LOCKED` L18 / extract **L240** (RULE-009's actual text): "Missing source or conflicting attribution data ⇒ mark **LOW confidence or HOLD**; such data is **never** used as scale evidence." — it mandates only that *missing-source OR conflict* be excluded; it contains **no "HIGH-only" language** and is **silent on MEDIUM**.
- Schema extract **L233**: `source_confidence: HIGH | MEDIUM | LOW` — a `MEDIUM` / `conflict_status=NONE` attribution is neither missing-source nor conflicting, so RULE-009 does not force it out.
- §6 L104 (the file's own dependency list): "`attribution_window` value + **confidence thresholds for scale eligibility** | **candidate** `[PACK]` — links M6-OD-002 | RULE-009 scale-evidence gating (§4)" — i.e. the confidence threshold is **owner-pending**, and §6 L108 says the file "resolves nothing".

**Defect:** §4 (and §1) recast RULE-009's fail-closed *exclusion* rule (missing/conflict → LOW/HOLD → excluded) into a positive *inclusion* threshold ("only HIGH may count"), which (a) **silently excludes all MEDIUM-confidence attributions** that RULE-009 would not exclude; (b) **mis-attributes** this stricter threshold to the locked `[REG RULE-009]`, which contains no such rule; and (c) is **internally inconsistent** with §6 L104, which lists the confidence threshold as an owner-pending candidate — so the briefing simultaneously *asserts* (§1/§4) and *defers* (§6) the same threshold, soft-resolving the MEDIUM-eligibility question a briefing is meant to leave open.

**Why MINOR (not the proposed MAJOR):** the picked direction is **fail-closed** (excluding MEDIUM is stricter/conservative) so it cannot cause scale-on-low-confidence, and it recommends no model — it is under-inclusion + an unsupported-citation/consistency slip. **Fix:** state §4/§1 as RULE-009's actual mandate ("missing-source or conflicting ⇒ LOW/HOLD ⇒ excluded"), and defer the exact usable-confidence cutoff (whether `MEDIUM` counts) to the owner per §6 — do not assert `HIGH`-only as register-locked.

### F2 — MINOR — `[REG §18]` labels a DOC section as a register section
**Verdict**: CONFIRMED MINOR (two verifiers)

**Exact claim:** §5 header L89 "## 5. Boundary guards `[BRIEF / REG §18]`".

**Evidence:** the file's own legend (L18) defines `[REG]` = "locked pack register" (ID-keyed: RULE-/CTR-/OD-NNN — no numbered sections); "§18" is an owner-**DOC** section (extract **L355** "## 18. Tích hợp với Module 3, 4, 5, 7, 8"; also surfaced in `ENTRY_EVIDENCE_REGISTER` "Consumed-boundary reference (doc §18)"). The file writes SPEC refs explicitly as `[REG SPEC §10.2]` (L27/L56), so the bare `§18` under `[REG]` is malformed.

**Defect:** a citation/tagging-precision slip; every substantive §5 guard is independently and correctly re-cited (RULE-008/009/010/019/014, BRIEF rule 6), so no wrong action follows. **Fix (pack-wide):** retag as `[BRIEF / DOC §18]` (this `[… / REG §18]` header recurs across the Phase-0 research files — normalize once; same as **M6-PC0204 F5** / **M6-PC0205 F2**).

---

## 5. Attacked and dismissed (did not survive adversarial verification)

1. **§3 readiness asymmetry (first/last "lowest data cost ✅"; weighted/cohort "data GAP") soft-recommends the cheaper models.** DISMISSED (two verifiers) — the asymmetry is factually true against the 19-field schema, `✅` appears only on clean-YES rows, and the research explicitly disclaims it as "not a recommendation" and reaffirms the owner's choice (header, §3 L65–67, §7 L118). Data cost is a legitimate input the owner needs; no model is picked.
2. **§4's `conflict_status=NONE` requirement nullifies the weighted model** (because a multi-touch model's attributions are `MULTI_TOUCH`). DISMISSED (two verifiers) — `MULTI_TOUCH` is a **value of `conflict_status`** by schema design (extract L234), and nothing links model=weighted to `conflict_status=MULTI_TOUCH` on every record; scale-eligibility gating is orthogonal to model selection, so no OD-005 option is foreclosed. (Speculative reinterpretation not supported by the sources.)
3. **§6 mis-scopes M6-OD-002 / omits the real OD-002 threshold dependency.** DISMISSED — OD-002 **is** named in the §6 list; the row's "what it gates" column correctly routes confidence gating to RULE-009, and OD-002's numeric Scale-Gate role is authoritatively held in DECISION_REGISTER and echoed at §4 L81. Only the loose word "confidence" in one grab-bag row — cosmetic.

## 6. Acceptance-check trace

- [x] Every finding cites the exact claim and its evidence (research section/line + source file line/row).
- [x] Verdict per finding: BLOCKER/MAJOR/MINOR — 0 BLOCKER, 0 MAJOR, 2 MINOR (F1, F2); F1's proposed-MAJOR downgraded to MINOR with rationale.
- [x] No raw secret or unmasked PII (only register/extract/research text quoted; no channel-origin data present).
- [x] Nothing self-certified PASS; `04-artifacts/state/` untouched; gateway BLOCKED / production OFF unchanged; no model selected on M6's behalf.
