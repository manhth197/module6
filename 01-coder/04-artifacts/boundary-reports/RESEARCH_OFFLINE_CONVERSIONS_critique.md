# BOUNDARY CRITIQUE — RESEARCH_OFFLINE_CONVERSIONS.md

**Critic prompt**: M6-PC0205 (RESEARCH_OFFLINE_CONVERSIONS_CRITIC) · **Role**: BOUNDARY_ADVERSARY · **Mode**: analysis_only
**Target**: `04-artifacts/analysis/research/RESEARCH_OFFLINE_CONVERSIONS.md` (produced by M6-P0205)
**Author does not respond here.** Findings feed Phase-0 design, the producing prompt M6-P0705 (CTR-008), and slice M6.2D.

> `global_gateway_state` stays **BLOCKED**, `production_flag` stays **OFF**. Nothing here flips a gate or a flag. Self-report; the runner gate decides PASS.

---

## 1. Entry gate (verified before review)

| Check | Result | Evidence |
|---|---|---|
| M6-PC0205 is RUNNING in the ledger | ✅ | `PROMPT_EXECUTION_LEDGER_LOCKED.csv` row 39 — `M6-PC0205 … BOUNDARY_ADVERSARY … RUNNING` |
| Dependency M6-P0205 is complete | ✅ | ledger row 38 — `M6-P0205 … PASS`; evidence `M6-P0205.json` status=PASS |
| Required inputs present | ✅ | brief, `RESEARCH_OFFLINE_CONVERSIONS.md`, `M6-P0205.json` all read |
| M6.2D slice claims | ✅ | `slices/M6.2D.md` — done-gate "No double count, no PII thô"; scope incl. "platform result logs" + "offline conversion after ORDER_VERIFIED or owner-approved event" |

Entry gate holds; review proceeded.

## 2. Method

Direct citation/slice verification plus an adversarial **find → refute-verify** pass: 5 finder lenses (**revenue-trigger-boundary**, **consent-pii-boundary**, platform-fact-discipline, owner-decisions, citation/executability) surfaced candidates; each was handed to a separate verifier told to **try hard to refute it** and grade severity. **15 candidates verified; 8 confirmed (collapsing to 3 distinct issues), 7 refuted.** Hermetic mode: no web-fetch (platform facts are `[PLATFORM]`-quarantined and impl-time verified).

Severity rubric: **BLOCKER** = pre-verified-revenue upload path / consent bypass / raw PII to platform / M6 resolves an owner decision; **MAJOR** = would cause such a breach *if followed* but mitigated; **MINOR** = enumeration/citation/tagging completeness, low-impact slip.

## 3. Overall verdict

**No BLOCKER, no MAJOR.** This is the strongest revenue-boundary artifact in the Phase-0 set. The two crux attacks were **refuted**:
- **Revenue trigger is airtight.** §2 emits an offline conversion **only** on the `ORDER_VERIFIED` transition (a fail-closed *creation-time* trigger, not a post-filter); the never-list (quote/cart/draft/payment_waiting/COD_waiting) is explicit; M6 consumes Commerce Verified Revenue and never creates revenue/confirms payment/sets order state. Every "pre-verified-revenue upload" attack failed. It also uses **FAIL-001 in its correct scope** (unlike the sibling PC0203/PC0204 mis-cites) and **includes M6-ENTRY-001** in §7 (which PC0203 omitted).
- **OD-003 is not resolved.** §4 explicitly refuses the match-rate/hash tradeoff ("choosing send more PII for a higher match rate is an owner/privacy-legal decision, not one this research makes"; fail-closed until decided). The "§4 resolves OD-003 permissively" attack failed — the non-PII/click-id reading aligns with the locked RULE-014, and the offline field set is MISSING→M6-P0705, so no pre-OD-003 upload path is buildable.

The confirmed defects are **3 MINOR** — the notable one is a consent under-enumeration.

| ID | Severity | Category | One-line |
|---|---|---|---|
| F1 | MINOR* | consent-enumeration | §2/§6/§7 enumerate the revenue and PII boundaries but omit the **consent** gate (RULE-002/FAIL-002) for the offline upload, and §7 omits the `M6-CTR-006` consent-snapshot dependency — *one verifier rated this MAJOR* |
| F2 | MINOR | citation precision | §6 header `[REG §18]` labels an owner-DOC section as a register section (correct: `[DOC §18]`); pack-wide header nit |
| F3 | MINOR | internal-inconsistency | §3 ties offline batch window/size to the "**M6-OD-002 family**", but OD-002 is CPA/ROAS/AOV thresholds — and it contradicts §7, which correctly leaves batch cadence as `[PLATFORM]` verify-at-impl |

---

## 4. Confirmed findings

### F1 — MINOR (one verifier: MAJOR) — the consent gate is absent from the offline boundary enumeration
**Category**: consent-enumeration · **Verdict**: CONFIRMED (five verifiers: 4× MINOR, 1× MAJOR)

**Exact claim (research):**
- §2 (L37–48) "**The load-bearing boundary of this whole flow**" lists **only** the `ORDER_VERIFIED`/owner-approved (revenue) trigger.
- §6 "Boundary & safety guards" (L97–105) lists: no-real-upload, ORDER_VERIFIED derivation, no-raw-PII (with a dedicated `M6-OD-003` guard), secret_ref, no-CRM — **no consent gate**.
- §7 "explicit list — acceptance requirement" (L107–119) lists OD-003, owner-approved events, OD-004, CTR-008, ENTRY-001, `[PLATFORM]` timing — **no consent scope, and no `M6-CTR-006` consent-snapshot dependency**.
- The **only** consent mention in the whole file is §4 L79 "(consent-gated)", scoped to the non-PII click-id-matching sub-case.

**Evidence:** `RULES_LOCKED` L11 (**RULE-002**): "Consent is fail-closed: without valid consent at event/send time there is **NO external measurement**…"; `FAIL_GATE_REGISTER` L14 (**FAIL-002**) consent violation; `slices/M6.2D.md` L23 puts `send_policy = consent_valid AND …` in scope and L44 lists **FAIL-002** among the slice's in-scope fail gates. An offline upload **is** external measurement (§1 "uploaded to the ad platform").

**Defect:** consent is a co-equal fail-closed boundary for an offline upload, but the research's *own* enumerated boundary surface (§6) and acceptance-requirement dependency list (§7) surface only the revenue and PII boundaries — each of which gets a dedicated guard/dependency row — while consent gets neither. A verified order from a customer who did **not** consent to marketing measurement must not be uploaded; that rule is present only *implicitly* (inherited from the M6-P0203 outbox send-gate) and in one §4 parenthetical.

**Severity — MINOR, with a noted MAJOR dissent:** graded **MINOR** because it is **not a shippable bypass** — offline is explicitly "one channel of `marketing_measurement_outbox` … via the outbox pattern (M6-P0203)" whose send-gate re-validates consent, and the M6.2D exit-gate requires the full `send_policy` conjunction (consent_valid first) with FAIL-002 in scope, so a slice-faithful coder cannot ship a consent-bypassing path. One verifier rated it **MAJOR** on the ground that §6/§7 are *billed as* the enumerated boundary/acceptance surface, so omitting consent there (plus the `M6-CTR-006` dependency) while exhaustively listing revenue+PII is a substantive gap a coder treating §6/§7 as the checklist would inherit. **Fix (the most actionable item):** add the consent gate (RULE-002/FAIL-002, send-time re-validation) as an explicit co-boundary in §2/§6, and add `M6-CTR-006` (consent snapshot, →M6-P0702) + consent scope to the §7 dependency list.

### F2 — MINOR — `[REG §18]` labels a DOC section as a register section
**Verdict**: CONFIRMED MINOR (two verifiers)

**Exact claim:** §6 header L97 "## 6. Boundary & safety guards `[BRIEF / REG §18]`" (and L101 "`[REG §18, RULE-003]`").

**Evidence:** the file's own legend (L16) defines `[REG]` = "locked pack register" and (L15) `[DOC]` = "owner document / extract line". No register is §-keyed (they are ID-keyed: RULE-/FAIL-/ENTRY-/OD-NNN); "§18" is an owner-**DOC** section (the consumed-boundary block, extract ~L355/359, reproduced in `ENTRY_EVIDENCE_REGISTER` "Consumed-boundary reference (doc §18)"). The file itself uses `[DOC §12 …]` correctly.

**Defect:** a citation/tagging-precision slip; the boundary content is real and independently re-cited (RULE-003, RULE-014/FAIL-008), so no wrong action follows. **Fix (pack-wide):** retag as `[DOC §18]` (this `[… / REG §18]` header recurs across the Phase-0 research files — normalize once; same as **M6-PC0204 F5**).

### F3 — MINOR — offline batch cadence wrongly tied to the "M6-OD-002 family", contradicting §7
**Verdict**: CONFIRMED MINOR

**Exact claim (§3 L58):** "**Batch window / size** … the window is config → ops/owner (**M6-OD-002 family**)."

**Evidence:** `DECISION_REGISTER` — **M6-OD-002** governs "Ngưỡng CPA/ROAS/AOV/Verified Rate" for the Scale Gate and dashboard alerts (blocks CTR-015/026, M6.2G exit) — nothing about offline upload cadence; **no** owner decision covers batch cadence. The same file's **§7 L116** correctly lists "Batch window/size, attribution-window timing (all `[PLATFORM]`) | verify at implementation" with no owner-decision id.

**Defect:** §3 invents an unsupported governance tie (batch cadence ⇄ OD-002) and contradicts §7's correct `[PLATFORM]`-verify treatment. Low impact (a coder following §7 does the right thing). **Fix:** drop "(M6-OD-002 family)" in §3; treat batch window/size as a `[PLATFORM]`/ops-config item consistent with §7 (or, if an owner threshold genuinely applies, name the correct decision).

---

## 5. Attacked and dismissed (did not survive adversarial verification)

1. **§7 omits M6-OD-008 (PAYMENT_COMPLETED as an owner-approved offline trigger).** DISMISSED (three verifiers) — OD-008's Blocks column is M6.2E/M6.2F, not this M6.2D slice; the "owner-approved event (**default none**)" escape hatch is fail-closed by construction; §2 is a fail-closed creation-time trigger, so no coder emits an offline conversion on PAYMENT_COMPLETED without an explicit owner approval that routes through the decision. (Same conclusion as the sibling PC0203 review.)
2. **§1's illustrative examples ("COD confirmed later, phone/live order") could be read as triggers / platform fact untagged.** DISMISSED — §1 is `[EXT]`-tagged and §2 clamps the actual trigger to `ORDER_VERIFIED`; the match-rate/attribution mechanics are `[PLATFORM]`-tagged in §3/§4 and the §8 traceability table.
3. **§4 "at most non-PII click-id matching" resolves OD-003 permissively (pre-OD-003 click-id upload).** DISMISSED (two verifiers) — the non-PII reading aligns with the locked RULE-014 ("Hash policy fields require M6-OD-003"; Pixel public-safe), the offline field set is MISSING→M6-P0705, connector is OPEN (OD-004), and the whole flow is staged "design only" — no pre-OD-003 upload path is buildable and nothing is resolved.

## 6. Acceptance-check trace

- [x] Every finding cites the exact claim and its evidence (research section/line + source file line/row).
- [x] Verdict per finding: BLOCKER/MAJOR/MINOR — 0 BLOCKER, 0 MAJOR, 3 MINOR (F1–F3); F1's MAJOR dissent recorded.
- [x] No raw secret or unmasked PII (only register/extract/research text quoted; no channel-origin data present).
- [x] Nothing self-certified PASS; `04-artifacts/state/` untouched; gateway BLOCKED / production OFF unchanged.
