# BOUNDARY CRITIQUE — RESEARCH_SCALE_GATE_WORKFLOW.md

**Critic prompt**: M6-PC0208 (RESEARCH_SCALE_GATE_WORKFLOW_CRITIC) · **Role**: BOUNDARY_ADVERSARY · **Mode**: analysis_only
**Target**: `04-artifacts/analysis/research/RESEARCH_SCALE_GATE_WORKFLOW.md` (produced by M6-P0208)
**Author does not respond here.** Findings feed Phase-0 design, the producing prompts M6-P0709/0712, and slice M6.2G.

> `global_gateway_state` stays **BLOCKED**, `production_flag` stays **OFF**. Nothing here grants a scale; an approved `ads_scale_request` is only data. Self-report; the runner gate decides PASS.

---

## 1. Entry gate (verified before review)

| Check | Result | Evidence |
|---|---|---|
| M6-PC0208 is RUNNING in the ledger | ✅ | `PROMPT_EXECUTION_LEDGER_LOCKED.csv` row 45 — `M6-PC0208 … BOUNDARY_ADVERSARY … RUNNING` |
| Dependency M6-P0208 is complete | ✅ | ledger row 44 — `M6-P0208 … PASS`; evidence `M6-P0208.json` status=PASS |
| Required inputs present | ✅ | brief, `RESEARCH_SCALE_GATE_WORKFLOW.md`, `M6-P0208.json` all read |
| §16 + M6.2G slice claims | ✅ | extract §16 L312–324 (banner + 8 conditions) and `slices/M6.2G.md` verified faithful; SMK-009 = "Recall/Sale Lock active → Scale Gate FAIL/HOLD" (locked) |

Entry gate holds; review proceeded.

## 2. Method

Direct citation/slice/smoke verification plus an adversarial **find → refute-verify** pass: 5 finder lenses (**auto-scale-boundary**, **risk-veto**, scale-evidence, citation-completeness, executability) surfaced candidates; each was handed to a separate verifier told to **try hard to refute it** and grade severity. **9 candidates verified; 5 confirmed (collapsing to 3 distinct issues), 4 refuted.** Hermetic mode (no web-fetch).

Severity rubric: **BLOCKER** = an executable scale/budget/rollback path in M6 / self-approval / weighted-not-hard risk veto / scale-on-LOW-HOLD / raw PII / resolves an owner decision; **MAJOR** = would cause such a breach *if followed* but mitigated; **MINOR** = citation/tagging precision, internal inconsistency, low-impact slip in the fail-closed direction.

## 3. Overall verdict

**No BLOCKER, no MAJOR.** A strong, boundary-tight artifact on the highest-risk axis. Every crux attack was **refuted**:
- **Auto-scale boundary — airtight.** M6 has no executable scale/budget path; the invariant is stated in the banner, §1, §5 L107 ("No transition inside M6 performs an external budget/campaign action"), and §6. The **rollback-execution attack failed** — §5 L107 already covers the `ROLLED_BACK` transition, and because a budget *revert* is itself a budget change, the invariant forbids M6 executing it symmetrically with scale-up (the explicit "[external]" marker would be redundant). The `ads_scale_request` stays inert data; no self-approval (§5).
- **Risk veto — hard and unbreakable.** The dedicated lens returned **zero findings**: the Risk row (recall/sale-lock/quality-hold/complaint-P0/spam-flag + CRM suppression) is a hard veto, re-checked at approval, and a rollback trigger — no way to soften or bypass it. All §16 citations (banner L312, 8 conditions, L323/L324) and SMK-009 verified faithful.

The confirmed defects are **3 MINOR** — all citation/precision.

| ID | Severity | Category | One-line |
|---|---|---|---|
| F1 | MINOR | scale-evidence-rule | §3/§8 state "Only PASS + **HIGH-confidence**" as scale evidence and stamp it `[REG RULE-009]` "owner-mandated", but RULE-009 bars only LOW/HOLD/conflict — **MEDIUM is explicitly valid** (SPEC L301) → over-restriction; **3rd pack-wide occurrence** (PC0206 F1 / PC0207 F2) |
| F2 | MINOR | citation precision | §6 header `[REG §18]` labels an owner-DOC boundary section as a register section (correct: `[BRIEF / DOC §18]`); pack-wide header nit |
| F3 | MINOR | internal-inconsistency | §1 attributes the exit-gate-**check-1** quote to "the M6.2G **done gate**", which actually reads only "No auto scale, owner approval required" |

---

## 4. Confirmed findings

### F1 — MINOR — "PASS + HIGH-confidence" over-restricts RULE-009 (excludes valid MEDIUM), mis-labeled owner-mandated
**Category**: scale-evidence-rule · **Verdict**: CONFIRMED MINOR (two verifiers) · **This is the actual Scale-Gate consumer of the recurring over-restriction**

**Exact claim:** §3 L78 "`[REG RULE-009]` **Only PASS + HIGH-confidence** evidence may support a scale case; any LOW/HOLD/conflicting input makes the request HOLD" — **reasserted §8 L142**: "Only PASS/HIGH-confidence is scale evidence | `[REG RULE-009]` — **owner-mandated**".

**Evidence:** `RULES_LOCKED` L18 / extract **L240** (RULE-009): "Missing source or conflicting attribution data ⇒ LOW confidence or HOLD; such data is never used as scale evidence" — bars only LOW/HOLD/conflict. Schema extract L233: `source_confidence: HIGH | MEDIUM | LOW`. **SPEC L301** makes it explicit: "HIGH / MEDIUM / LOW (**LOW/HOLD never scale evidence**)" — so **MEDIUM is a valid scale-evidence tier** RULE-009 does not exclude.

**Defect:** the research converts RULE-009's *exclusion* (LOW/HOLD out) into a positive "**HIGH-only**" inclusion rule that **also drops MEDIUM**, and (worse than the sibling occurrences) **stamps it "owner-mandated" in §8 L142** — a fidelity error the file's own acceptance criterion ("only `[DOC]` items are owner requirements") forbids. A coder building the CTR-024 scale-readiness filter (M6-P0713) verbatim would encode `source_confidence == 'HIGH'` and silently drop valid MEDIUM-confidence rows. **Fail-closed-safe** (fewer things qualify for scale — opens no budget/scale path), hence MINOR. **This is the 3rd pack-wide occurrence** (M6-PC0206 F1 attribution, M6-PC0207 F2 dashboard, here the Scale Gate itself). **Fix (one coordinated pack-wide change):** state the rule as "**not LOW, not HOLD, not conflicting**" (per RULE-009), not "HIGH only", and drop the "owner-mandated" label; defer the exact usable-confidence cutoff (whether MEDIUM counts for scale) to the owner. Anchor the fix in the attribution rule / CTR-024 worker contract.

### F2 — MINOR — `[REG §18]` labels an owner-DOC boundary section as a register section
**Verdict**: CONFIRMED MINOR (two verifiers)

**Exact claim:** §6 header L109 "## 6. Boundary & safety guards `[BRIEF / REG §18]`".

**Evidence:** the file's legend (L17) reserves `[REG]` for locked pack registers (ID-keyed); "§18" is an owner-**DOC** section (the "Module 6 không được làm gì" consumed-boundary table, extract L355; surfaced in `ENTRY_EVIDENCE_REGISTER` "Consumed-boundary reference (doc §18)"). Correct tag: `[BRIEF / DOC §18]`.

**Defect:** a citation-precision slip (it also demotes an owner-mandated boundary to a mere register reference). No boundary harm — every §6 guard is independently re-cited (RULE-010/FAIL-006 at L111, RULE-014 at L116, BRIEF rule 6 at L117). **Fix (pack-wide):** retag `[BRIEF / DOC §18]` — this recurs across the Phase-0 research files (5th occurrence: **PC0204 F5 / PC0205 F2 / PC0206 F2 / PC0207 F1**); normalize once.

### F3 — MINOR — the "done gate" quote is actually the exit-gate check, not the done-gate column
**Verdict**: CONFIRMED MINOR

**Exact claim (§1 L40–42):** "the M6.2G **done gate** states exactly this (*'the system can compute and propose but has no code path that raises budget, enables campaigns or opens audience scale'*)".

**Evidence:** that verbatim sentence is **exit-gate CHECK 1** (`slices/M6.2G.md` line 57), an itemization of the done gate. The done-gate **column** (M6.2G.md line 9) reads only "**No auto scale, owner approval required**" — which the research itself renders correctly at its own L6. So the label "done gate" is bound to two different strings.

**Defect:** a provenance/precision slip — the quote is real and faithful (from the slice's exit-gate checks) but attributed to the wrong field ("done gate" column vs exit-gate check). Substance is boundary-correct; no wrong action follows. **Fix:** attribute the longer quote to "the M6.2G exit-gate check 1" (or "done-gate leg"), reserving "done gate" for the terse column text.

---

## 5. Attacked and dismissed (did not survive adversarial verification)

1. **Rollback execution is an M6 budget-mutation path (asymmetry vs scale-up's explicit `[external]`).** DISMISSED (two verifiers) — §5 L107 ("No transition inside M6 performs an external budget/campaign action") sits in the same section and explicitly covers the `ROLLED_BACK` transition; a budget *revert* is itself a budget change the banner/§1/§6 invariant forbids M6 to execute symmetrically; "reverts the scale" defines the stored `rollback_condition`'s semantics (M6's in-scope detection), not who executes. The explicit "[external]" marker would be redundant with L107.
2. **Risk-veto softening/bypass.** DISMISSED (lens returned zero findings) — the hard veto holds.
3. **§4 cites only SMK-009; the M6.2G slice binds SMK-009 AND SMK-012.** DISMISSED — smoke bindings are authoritatively sourced from the slice/register (which names both) and the exit-gate checks 3&4 enforce both; the desk research is not the smoke-binding artifact, and it makes no false/exhaustiveness claim (SMK-009 correctly ties to the §4 risk veto). The no-approval→no-scale concept is fully covered in prose (§1, §5).
4. **§5 lifecycle string puts `REJECTED | HOLD` on the same arrow into `[external scale by owner]`.** DISMISSED — the scale node is explicitly external to M6 (not an M6 state, so no in-M6 transition to mis-wire), and §1/§3 L78/§4/§6/RULE-009 preclude HOLD/LOW/REJECTED advancing; the `|` is ordinary verdict-alternation. A branching diagram would be cleaner but is cosmetic.

## 6. Acceptance-check trace

- [x] Every finding cites the exact claim and its evidence (research section/line + source file line/row).
- [x] Verdict per finding: BLOCKER/MAJOR/MINOR — 0 BLOCKER, 0 MAJOR, 3 MINOR (F1–F3).
- [x] No raw secret or unmasked PII (only register/extract/research text quoted; no channel-origin data present).
- [x] Nothing self-certified PASS; `04-artifacts/state/` untouched; gateway BLOCKED / production OFF unchanged; no scale granted, no owner decision resolved.
