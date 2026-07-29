# BOUNDARY CRITIQUE — RESEARCH_CROSS_MODULE_CONTRACTS.md

**Critic prompt**: M6-PC0210 (RESEARCH_CROSS_MODULE_CONTRACTS_CRITIC) · **Role**: BOUNDARY_ADVERSARY · **Mode**: analysis_only
**Target**: `04-artifacts/analysis/research/RESEARCH_CROSS_MODULE_CONTRACTS.md` (produced by M6-P0210)
**Author does not respond here.** Findings feed Phase-0 design, the CONTRACT_HARMONIZATION prompts M6-P0701/0702/0706 (consumed shapes), and the M6.2A/M6.2I entry gates.

> `global_gateway_state` stays **BLOCKED**, `production_flag` stays **OFF**. Nothing here consumes anything live or writes into another module. Self-report; the runner gate decides PASS.

---

## 1. Entry gate (verified before review)

| Check | Result | Evidence |
|---|---|---|
| M6-PC0210 is RUNNING in the ledger | ✅ | `PROMPT_EXECUTION_LEDGER_LOCKED.csv` row 49 — `M6-PC0210 … BOUNDARY_ADVERSARY … RUNNING` |
| Dependency M6-P0210 is complete | ✅ | ledger row 48 — `M6-P0210 … PASS`; evidence `M6-P0210.json` status=PASS |
| Required inputs present | ✅ | brief, `RESEARCH_CROSS_MODULE_CONTRACTS.md`, `M6-P0210.json` all read |
| §18 table + registers + entry evidence claims | ✅ | extract §18 L355–365 (all **7** rows verbatim incl. M8/CRM/Finance), §26 L488 P3+P5, RULE-001/002/003/013/017/019/020/021/H02/H03, SMK-001..015 + proposed 016/017/018, ENTRY-001..004 (all OPEN), CTR-003/004/005/006/009/010, OD-008/011 all verified faithful |

Entry gate holds; review proceeded.

## 2. Method

Direct citation/register/slice/smoke verification plus an adversarial **find → refute-verify** pass: 5 finder lenses (**producer-path-reframing**, **doc-fidelity/fabricated-rows**, **smoke-count/coverage-gap**, **citation/tag precision**, **missing-owner-decision/entry-gate**) surfaced candidates; 5 lead-grounded seeds were merged in; each of the 10 candidates was handed to a separate verifier told to **try hard to refute it** and grade severity. **10 candidates verified; 1 confirmed defect, the rest refuted (2 finders' primary lenses returned empty; one verifier confirmed §2.1 is clean, not a defect).** Hermetic mode (no web-fetch).

Severity rubric: **BLOCKER** = a consume-interface reframed as a **producer** path (M6 pricing/order-state/CRM-send/commission/advisory/public-reply/live-as-revenue) / a must-not-do stripped of its RULE anchor / an OPEN entry row treated as satisfied / a fabricated owner-mandated row / using the §2.1 gap to actually create smokes in read-only 00-spec / raw PII; **MAJOR** = would cause such a breach *if a coder followed the text* but mitigated; **MINOR** = citation/tag precision, internal inconsistency, or a slip that errs fail-closed.

## 3. Overall verdict

**No BLOCKER, no MAJOR.** The cleanest artifact in the Phase-0 series — a defensively-written, self-critical consume-only map. Every crux attack was **refuted**:

- **Producer-path boundary — airtight (the crux axis).** No §18 row is reframed as a write-back. §4 (L119–127) states the direction discipline explicitly: M6 **produces only its own** objects (`ads_measurement_event`, `ads_attribution_context`, outboxes, scale/learning candidates) and "even those never reach into another module's domain (outbox worker sends to Meta/Google, not to CRM/Commerce/Finance)." Every write-verb in §1 targets an **M6-owned** sink (`web_event_logs`/CTR-004). The Finance row's "referral fields **recorded by** M6" is the verbatim concept of `[REG RULE-019]` (records-only into M6's own attribution context; Finance decides commission) — **not** a write into the Finance ledger.
- **Doc fidelity — verbatim.** All **7** §18 rows (consume + must-not-do cells) verify cell-by-cell against extract L359–365; the scope note (heading names "3,4,5,7,8" but the table carries 7 rows incl. CRM/Member + Finance/Diamond, no Module-6 row) is **accurate, not an over-claim**. No fabricated/extra/dropped row.
- **Smoke coverage — count accurate, gap honestly hedged.** "3 of 7 have a direct owner P0 smoke" (M3=SMK-004/005/015, CRM=SMK-002/008/010, Finance=SMK-014) is correct; M4/M5/M7/M8 have no dedicated boundary smoke (SMK-013 is a positive **trace** test, not a prohibition assertion — the research says exactly this). §2.1 is labelled `[PACK]`, **non-blocking**, "does not create smokes" — read-only 00-spec is respected.
- **Entry evidence — all OPEN, treated as gates.** ENTRY-001..004 are marked OPEN in §3/§5, matching the register; every §1 backing-evidence reference points at an OPEN row **as a gate**, never as satisfied.
- **Dependencies — principled scope.** The CTR-004 and OD-009 "omissions" from §5 were **refuted**: CTR-004 is **M6-owned** (not a CONSUMED cross-module shape → correctly excluded from the consumed-shape list, consistent with §1 L46/L52–54), and OD-009 is disabled-by-default / Gateway-owned / scoped to M6.2I event-set (not a revenue-boundary edge like OD-008).

The confirmed defect is **1 MINOR** — a single citation/tag slip.

| ID | Severity | Category | One-line |
|---|---|---|---|
| F1 | MINOR | tag precision / internal inconsistency | §6 header L146 `[BRIEF / REG §18]` tags DOC section §18 (module-boundary table, extract L355) as a **register** — correct `[DOC §18]`; **7th pack-wide occurrence**, and internally inconsistent with this file's own ~10 correct `[DOC §18]` citations |

---

## 4. Confirmed finding

### F1 — MINOR — the lone `[REG §18]` tag mislabels a DOC section (internally inconsistent)
**Category**: tag precision / internal inconsistency · **Verdict**: CONFIRMED MINOR (three verifiers)

**Exact claim:** §6 header L146 "## 6. Boundary & safety guards `[BRIEF / REG §18]`".

**Evidence:** extract **L355** "## 18. Tích hợp với Module 3, 4, 5, 7, 8" is a **DOC** section (the module-integration boundary table), not a locked pack register; no register is organized as "§18". The file's own legend (L18–19) reserves `[REG]` for locked pack registers and `[DOC]` for the owner document, and **every other §18 reference in the same file uses `[DOC §18]`** (L4, L22, L23, L37, L56, L63, L150, L163–166) — L146 is the sole `[REG §18]`. The file's own body even writes the correct compound form at §6 L150: "`[DOC §18 / REG RULE-003/013/017/019/021/H03]`".

**Defect:** a citation-precision slip that mislabels an owner-DOC boundary as a register. No boundary harm — if anything it **over**-attributes normative weight (reads as *more* binding), and the §6 guards are independently re-grounded (RULE-003/013/017/019/021/H03, BLOCKED/OFF). Fail-safe. **Fix (pack-wide):** retag `[DOC §18]` (header `[BRIEF / DOC §18]`); this is the **7th occurrence** of the identical nit (PC0204 F5 / PC0205 F2 / PC0206 F2 / PC0207 F1 / PC0208 F2 / PC0209 F1) — normalize once.

> **Self-correction (adversary caught a lead over-count):** the lead's initial note also suspected `[REG §18]` on the anchor line L6. Verification refuted that — **L6 lists only RULE IDs** (`RULE-001/002/003/013/017/019/021` + `RULE-H03`), no `§18`. The **only** `[REG §18]` slip is L146.

---

## 5. Attacked and dismissed (did not survive adversarial verification)

1. **A §18 row is reframed as a producer/write-back path.** DISMISSED (two verifiers) — §4 direction discipline holds; every M6 write targets an M6-owned object; "referral fields recorded by M6" is RULE-019 records-only into M6's own attribution context, under a column literally headed "Consumed contract shape". No producer path.
2. **The "seven rows" scope note over-claims §18 (heading names only 5 modules).** DISMISSED — extract L359–365 carries all 7 rows verbatim incl. M8 (L363), CRM/Member (L364), Finance/Diamond (L365); the note is faithful.
3. **§2.1 coverage-gap finding is overstated/blocking or smuggles new smokes into read-only 00-spec.** DISMISSED (two verifiers) — the 3-of-7 count is accurate, the finding is explicitly `[PACK]`, non-blocking, rule-covered, and "does not create smokes"; a *proposal* recorded for the owner, not an edit.
4. **A CTR/OD/ENTRY/SMK citation or harmonization-prompt number is wrong.** DISMISSED — CTR-003→P0701, CTR-005/006→P0702, CTR-009/010→P0706, the CTR-010 "no owner-trigger" caveat, OD-008/011 OPEN, and ENTRY-001..004 all OPEN are faithful to the registers.
5. **CTR-004 (`web_event_logs`) and OD-009 (GOLDEN_HOUR config) are omitted from the §5 dependency list.** DISMISSED — CTR-004 is **M6-owned** (harmonized by M6-P0703), not a CONSUMED cross-module shape, so §5's consumed-shape list correctly excludes it (consistent with §1's own treatment); OD-009 defaults disabled / Gateway-owned / scoped to M6.2I event-set, not the revenue-adjacency edge OD-008 that this file centers on. Both are principled scope choices, not internal inconsistencies; each errs fail-closed and opens no producer path.
6. **An OPEN entry-evidence row is treated as satisfied.** DISMISSED — all four ENTRY rows are consistently OPEN and used only as gates (BLOCKED), matching the register verbatim.

## 6. Acceptance-check trace

- [x] Every finding cites the exact claim and its evidence (research section/line + source file line/id).
- [x] Verdict per finding: BLOCKER/MAJOR/MINOR — 0 BLOCKER, 0 MAJOR, 1 MINOR (F1).
- [x] No raw secret or unmasked PII (only register/extract/research text quoted; no channel-origin data present).
- [x] Nothing self-certified PASS; `04-artifacts/state/` untouched; gateway BLOCKED / production OFF unchanged; nothing consumed live, no owner decision resolved, no smoke created.
