# BOUNDARY CRITIQUE — RESEARCH_REPO_AUDIT_PLAN.md

**Critic prompt**: M6-PC0200 (RESEARCH_REPO_AUDIT_PLAN_CRITIC) · **Role**: BOUNDARY_ADVERSARY · **Mode**: analysis_only
**Target**: `04-artifacts/analysis/research/RESEARCH_REPO_AUDIT_PLAN.md` (produced by M6-P0200)
**Author does not respond here.** Findings feed Phase-0 design (M6-P0300+) and the CONTRACT_HARMONIZATION leg.

> `global_gateway_state` stays **BLOCKED**, `production_flag` stays **OFF**. Nothing in this critique flips a gate or a flag. This is a self-report; the runner gate decides PASS.

---

## 1. Entry gate (verified before review)

| Check | Result | Evidence |
|---|---|---|
| M6-PC0200 is RUNNING in the ledger | ✅ | `PROMPT_EXECUTION_LEDGER_LOCKED.csv` row 29 — `M6-PC0200 … BOUNDARY_ADVERSARY … RUNNING` |
| Dependency M6-P0200 is complete | ✅ | ledger row 28 — `M6-P0200 … PASS`; evidence `M6-P0200.json` status=PASS |
| Required inputs present | ✅ | brief, `RESEARCH_REPO_AUDIT_PLAN.md`, `M6-P0200.json` all read |
| Plan's own precondition premises are real (not assumed) | ✅ | `IMPLEMENTATION_TARGET_LOCKED.json`: `repository.mode=UNRESOLVED`, `owner_decision M6-OD-011=OPEN`, `status=DRAFT`, `workspace_mode=STAGED_ONLY`, all `safety.*=false` |

Entry gate holds; the review proceeded.

## 2. Method

Direct source grounding (plan + `CONTRACT_REGISTER`, `DECISION_REGISTER`, `RULES_LOCKED`, extract §7/§24/§25, ledger) followed by an adversarial **find → refute-verify** pass: 5 independent finder lenses (citation fidelity, contract-register consistency, owner-decision completeness, boundary/overreach, executability) surfaced candidates; each candidate was then handed to a separate verifier instructed to **try hard to refute it** and grade severity. 20 candidates verified. Only findings that survived refutation are reported below; six that did not are listed in §5 so the designer does not re-chase them.

Severity rubric (as applied by the verifiers): **BLOCKER** = plan unusable / unconditionally breaches a hard boundary / resolves an owner decision; **MAJOR** = would cause boundary overreach or a dropped owner dependency *if followed*, but is mitigated/contradicted elsewhere in the plan; **MINOR** = citation precision, wording, low-impact slip.

## 3. Overall verdict

**No BLOCKER.** The playbook is structurally sound as a boundary artifact: fail-closed preconditions (§1), strictly read-only on the target repo (§1.3/§7), respects operator-only state ownership (candidate stack facts go to the operator, not the coder — §2/§8.5), never resolves an owner decision (§6 "records intersections … never picks a value"), routes CONSUMED gaps to their owning module rather than building them in M6 (§4), and cross-references every MISSING contract to a real producing harmonization prompt (M6-P0700..0714 all exist in the ledger, rows 62–76). Gateway BLOCKED / production OFF are respected throughout.

The confirmed defects are **quality issues**, not boundary breaches that survive the plan's own mitigations: **2 MAJOR + 4 MINOR**. They should be corrected before the coder executes the playbook, but none blocks Phase-0 design from consuming the research.

| ID | Severity | Category | One-line |
|---|---|---|---|
| F1 | **MAJOR** | executability / boundary | MappingStatus vocabulary has no valid value for a CONSUMED contract that is *absent* from the repo |
| F2 | **MAJOR** | missing-owner-decision | §6/§10 "explicit … acceptance requirement" list omits M6-OD-006 (auto-publish safe-range) |
| F3 | MINOR | internal-inconsistency | "the 22 MISSING rows" wrongly equated with "M6-owned"; true M6-owned MISSING = 17 |
| F4 | MINOR | doc-citation | three citation-precision defects (`§10` tag, `463–466` range, elided L466 quote) |
| F5 | MINOR | internal-inconsistency | foreign-schema `EXISTS_EXTEND` routed to `(§5)` Conflict report; owner-capture is §6 |
| F6 | MINOR | internal-inconsistency | binary Owner column flattens CTR-007 `conversion_events` (register: joint `M6/Core`) |

---

## 4. Confirmed findings

### F1 — MAJOR — No MappingStatus value for a CONSUMED-but-absent contract
**Category**: executability / boundary-violation · **Verdict**: CONFIRMED (adversarial verifier upheld MAJOR after conceding the Owner-keyed mitigation)

**Exact claim (plan §3):**
- line 71: *"locate the corresponding target-repo artifact across four dimensions and assign one `MappingStatus`."*
- lines 78–80 vocabulary: `EXISTS_REUSE` / `EXISTS_EXTEND` / `MISSING_CREATE` ("**absent**; M6 creates it in staging … Expected for M6-owned tables/workers/APIs") / `CONFLICT`.
- lines 88–92: CONSUMED → "expect `EXISTS_REUSE` … If any is **absent**, that is a gap the owner module must fill — record as gap, do **not** create it in M6."
- §9 line 192: "Every `M6-CTR-001..026` has a `MappingStatus` (no unmapped contract)."

**Evidence:** `CONTRACT_REGISTER.md` line 21 — `CTR-005 guest_contacts | CONSUMED (Customer identity) | MISSING`; line 22 — `CTR-006 guest_marketing_consent_snapshot | CONSUMED (Consent)`. These CONSUMED objects are inside the mandatory `M6-CTR-001..026` set that §9 requires to carry a status.

**Defect:** The four-value vocabulary has exactly one "absent" value — `MISSING_CREATE` — and it is defined as "M6 creates it" and scoped to M6-owned objects. `EXISTS_REUSE` is scoped to CONSUMED but is false when the object is absent. So for an **absent CONSUMED** contract — a case the plan itself anticipates at §3 lines 91–92 — none of the four values is correct, yet §3 line 71 forces one and §9 line 192 requires it. A coder is left to either stall or stamp `MISSING_CREATE`, which files a Core/Identity/Consent/CRM object into the M6 build set.

**Why MAJOR not BLOCKER:** build-vs-route is ultimately **Owner-keyed**, not status-keyed — §4 lines 116–118 and §9 line 195 route "a gap on a CONSUMED object" to the owning module *regardless of MappingStatus*. So a mislabel would not, by itself, cause an actual M6 build. The gap is real (a mandatory column with no valid value for a plan-anticipated case) but its overreach is contained elsewhere → MAJOR.

**Fix:** add a fifth status (e.g. `MISSING_OWNER_FILL` / `CONSUMED_ABSENT` = "absent, route to owning module, M6 never creates"), or bind the MappingStatus rule explicitly to the Owner column so an absent CONSUMED object can never receive `MISSING_CREATE`.

---

### F2 — MAJOR — Owner-decision "acceptance requirement" list omits M6-OD-006
**Category**: missing-owner-decision · **Verdict**: CONFIRMED MAJOR (contested — see split below)

**Exact claim (plan):**
- §6 line 149: "**OPEN decisions the audit must respect but MUST NOT resolve**" — table lists only `M6-OD-011`, `M6-OD-002`, `M6-OD-003`, `M6-OD-004`, `M6-OD-005` (lines 153–157).
- §10 line 201: "## 10. Owner-decision dependencies (**explicit list — acceptance requirement**)"; line 205 repeats the OD-002/003/004/005 intersection set; lines 206–207 add only "New candidates: any EXISTS_EXTEND-on-foreign-schema / CONFLICT / reuse-ambiguity".

**Evidence:** `DECISION_REGISTER.md` line 18 — `M6-OD-006 | Safe range cho guarded auto-publish là gì? | Cần trước khi bật learning engine publish | OPEN | M6.2H publish leg`. Plan §3 lines 96/99 place `CTR-013 ads_scale_request`, `CTR-014 ads_learning_candidate` and `CTR-015/025/026` (scale-flow) **inside the audit's mapping scope**. `CONTRACT_REGISTER.md` line 30 — `CTR-014 … Needed before M6.2H`.

**Defect:** The plan's own inclusion criterion for the listed decisions is *"a value that plugs into a contract the audit maps"* — OD-002 is listed because it plugs thresholds into mapped `CTR-015/026` (§6 line 154). **OD-006 has the identical structure**: it plugs an auto-publish safe-range into mapped `CTR-013/014/026` (M6.2H). Yet it is absent, leaving Module 6's **auto-publish boundary the only value-plug boundary with no owner-decision flag** in a list explicitly billed as an acceptance requirement. A coder handed a "where it intersects" pointer for four decisions and none for the auto-publish path is steered to treat the list as the intersection set.

**Verifier split (disclosed for the judge):** 1 verifier CONFIRMED MAJOR on the OD-002⇄OD-006 symmetry; 3 verifiers REJECTED the *broad* framing, arguing the list is a curated subset and later-leg decisions are backstopped by §5(b), §6 "BLOCKED not assumed", and hard rule 3. **Adjudication:** I side with MAJOR **specifically for OD-006**, because the rejecters' "later implement leg ⇒ omit" rule does not actually separate it from the listed decisions — OD-002 (M6.2F/G exit) and OD-005 (M6.2E/M6.2G) are *also* later-leg yet listed. The distinguishing criterion the plan really uses (value-plugs-into-a-mapped-contract) covers OD-006. Mitigations make it MAJOR, not BLOCKER.

**Sub-notes (MINOR, weaker):** `M6-OD-008` (does PAYMENT_COMPLETED count as revenue-adjacent — `DECISION_REGISTER` line 25; extract line 187) and `M6-OD-009` (GOLDEN_HOUR codes — line 26) are also unlisted, but each is independently backstopped for a *read-only, analysis-only* audit: §5(b) routes any revenue/order-state ownership collision to CONFLICT, the §4 gap report carries an "Owner decision? (Y/N + id)" column, §3 line 102 routes ambiguous event codes to owner/Core-governance, and `CTR-007` already carries `OWNER_DECISION_REQUIRED` status. The audit computes no revenue, so it cannot breach "only ORDER_VERIFIED is revenue." Their omission is lower-risk than OD-006's.

**Fix:** add `M6-OD-006` to §6/§10 with its `CTR-013/014/026` (M6.2H) insertion point; optionally note OD-008/OD-009 as audit-adjacent decisions to keep the "acceptance" list honest.

---

### F3 — MINOR — "the 22 MISSING rows" equated with "M6-owned"
**Category**: internal-inconsistency · **Verdict**: CONFIRMED (4/4 verifiers; severity 3×MINOR, 1×MAJOR — MINOR adopted)

**Exact claim (plan §3 lines 78–79):** "`MISSING_CREATE` — absent; M6 creates it in staging … Expected for **M6-owned** tables/workers/APIs (**the 22 `MISSING` CONTRACT_REGISTER rows**)."

**Evidence:** `CONTRACT_REGISTER.md` — 22 rows carry status `MISSING / OWNER_DECISION_REQUIRED`, but **5 are Owner=CONSUMED**: line 19 CTR-003 `event_registry` (Core), line 21 CTR-005 `guest_contacts` (Identity), line 22 CTR-006 `guest_marketing_consent_snapshot` (Consent), lines 25–26 CTR-009/010 `customer_segments`/`_members` (CRM). So **M6-owned MISSING = 17, not 22**. The equation also fails the other way: CTR-001/002 are M6-owned but `DRAFT_LOCKED` (lines 17–18), i.e. *not* among the 22, yet lines 93–94 list them as expected `MISSING_CREATE`. It further conflates two orthogonal axes — the register's `MISSING` = "no field-level schema in doc" vs the plan's `MISSING_CREATE` = "absent from repo".

**Why MINOR:** the parenthetical is a non-operative gloss inside a term *definition*; the operative "Expected buckets" block 8 lines later (lines 88–102) names the exact 5 CONSUMED contracts as `EXISTS_REUSE` / "do not create it in M6", reinforced by §4 lines 116–118 and the §9 checklist. A coder executing the *whole* of §3 never assigns `MISSING_CREATE` to a CONSUMED object. Realized harm is negligible; this compounds F1 (same root risk) but is itself a precision slip.

**Fix:** change "the 22 MISSING rows" → "the 17 M6-owned MISSING rows", or drop the parenthetical.

---

### F4 — MINOR — Three DOC-citation precision defects
**Category**: doc-citation fidelity · **Verdict**: CONFIRMED (all MINOR; substance faithful in each case)

**(a) `§10` section tag on base event codes — plan §3 line 100.** `[DOC §10, extract lines 123–134]`. Extract lines 123–134 (the "Event nền bắt buộc" table) sit under heading **`## 7. Phase 1`** (extract line 108); `## 10` is at extract line 179 (Event Taxonomy), and `CONTRACT_REGISTER` line 17 uses "doc §10" for extract lines 191–211. By the plan's own convention (§N = extract heading N, holds for §24→452 and §25→474), the tag should read **§7**. The co-cited line range 123–134 is correct and the requirement is redundantly anchored to line 468 / RULE-001, so a verbatim coder still reads the right lines.

**(b) Working-mode range excludes the line it quotes — plan sourcing legend lines 22–24.** Quotes `[DOC §24, extract lines 463–466]` but the final quoted sentence "*Do not invent event codes outside Core event_registry*" is **extract line 468**, outside 463–466. The plan's own §11 line 214 cites it correctly as "**463–466, 468**".

**(c) Elided quoted fragment — plan §2 line 60.** `[DOC §24 L466 "reuse existing test patterns"]`. Extract L466 reads "*Reuse existing conventions and test patterns.*"; the quoted fragment silently drops "conventions and" with no ellipsis (contrast plan line 68, whose quote *is* a contiguous substring of L459).

**Fix:** (a) `§10`→`§7`; (b) extend range to "463–466, 468"; (c) quote L466 verbatim or add an ellipsis.

---

### F5 — MINOR — Foreign-schema `EXISTS_EXTEND` routed to the wrong section
**Category**: internal-inconsistency · **Verdict**: CONFIRMED MINOR

**Exact claim (plan §3 lines 76–77):** "`EXISTS_EXTEND` — a related artifact exists that M6 must extend … If the extension touches **another module's** schema → **owner decision required** (**§5**)."

**Evidence:** §5 (line 124) is "## 5. Step 4 — **Conflict report**", "one row per `CONFLICT`" (line 126) — and `EXISTS_EXTEND` is a *distinct* MappingStatus from `CONFLICT` (§3 vocabulary). Owner-decision capture is **§6**, whose line 143 names "every `EXISTS_EXTEND` that touches another module's schema" as its first trigger; §10 lines 206–207 corroborate.

**Defect:** the pointer sends a foreign-schema `EXISTS_EXTEND` to the Conflict report, where it has no valid row, instead of (or in addition to) the §6 owner-decision candidate. The owner dependency is **not dropped** (§6/§10 independently capture it), but a coder could misfile the row. **Fix:** change "(§5)" → "(§6)".

---

### F6 — MINOR — Binary Owner column flattens CTR-007's joint ownership
**Category**: internal-inconsistency · **Verdict**: CONFIRMED MINOR

**Exact claim (plan §3):** mapping-table column "`Owner (M6 / CONSUMED)`" (line 84); "Expected buckets" M6-OWNED list (lines 93–94) names `CTR-007 conversion_events` as pure M6.

**Evidence:** `CONTRACT_REGISTER.md` line 23 — `M6-CTR-007 | conversion_events | **M6/Core** | MISSING / OWNER_DECISION_REQUIRED | … | M6-P0704`. The binary "M6 / CONSUMED" column cannot represent the register's joint `M6/Core` ownership, so CTR-007 is recorded as pure M6, dropping the Core co-ownership nuance.

**Why MINOR:** building `conversion_events` in staging is within M6's measurement mandate (extract line 267: "Source chuyển đổi nội bộ trước khi gửi measurement"); the register and producing prompt `M6-P0704` still govern the M6-vs-Core split, and §3 lines 100–102 handle the Core event-governance dimension separately. Low-impact, but connects to F2's OD-008 (CTR-007 is where the PAYMENT_COMPLETED revenue-adjacency question lives). **Fix:** allow `M6/Core` in the Owner column, or annotate CTR-007's split as owner-pending (M6-P0704 / OD-008-adjacent).

---

## 5. Attacked and dismissed (did not survive adversarial verification)

Listed so the designer does not re-chase them. Each was raised as a candidate and refuted.

1. **"CONSUMED `EXISTS_REUSE` silently drops the harmonization/owner-decision dependency."** DISMISSED — `CONTRACT_REGISTER` Invariant 1 + the M6.2A entry gate machine-enforce the producing-prompt dependency (M6-P0701/0702/0706) in the DAG, independent of the read-only, non-resolving audit map. Stamping `EXISTS_REUSE` cannot unblock that gate.
2. **"`(CTR-008, M6.2D)` contradicts register `Needed before M6.2C`."** DISMISSED — §6's second column is "Where the *decision* intersects", and OD-003 Blocks "M6.2D exit"; the gap-row slice is read from §4/register (CTR-008→M6.2C), not from §6. Both tokens are individually correct.
3. **"OD-008 / OD-009 omission is a standalone MAJOR/BLOCKER."** DISMISSED as standalone (retained only as MINOR sub-notes under F2) — the audit is analysis-only with no revenue-classification or emit step, and OD-008/009 are independently backstopped (§5(b), §4 owner-decision column, §3 line 102, CTR-007 status). Only OD-006 survived, via the OD-002 symmetry.
4. **"Owner-decision candidate format ≠ DECISION_REGISTER discovered-decision shape (adds Options, drops Status, renames Blocks→Blast radius)."** DISMISSED — the coder emits the one explicit column list deterministically; §8.4 routes candidates through a separate owner-decision prompt, never a direct register append, so no column misalignment reaches the register.
5. **"CTR-007 bucketed as M6-OWNED resolves OD-008 by code."** DISMISSED — `MISSING_CREATE` is register-correct for CTR-007 (its status *is* MISSING); §4 routes it to producing prompt M6-P0704; OD-008 gates M6.2E/F edge handling, not the read-only audit; a staging build resolves nothing.
6. **"§9 exit checklist doesn't re-verify §8.4 owner-decision candidates / §8.5 stack handoff."** DISMISSED — §6/§2 are mandatory steps and §8 enumerates every required output; §9 is a labeled self-check, not a claimed-exhaustive superset, and the active-prompt protocol binds the coder to §8's full output list.

## 6. Acceptance-check trace

- [x] Every finding cites the exact claim and its evidence (plan section/line + source file line/row).
- [x] Verdict per finding: BLOCKER/MAJOR/MINOR — 0 BLOCKER, 2 MAJOR (F1, F2), 4 MINOR (F3–F6).
- [x] No raw secret or unmasked PII (only register/plan text quoted; no channel-origin data present).
- [x] Nothing self-certified PASS; `04-artifacts/state/` untouched; gateway BLOCKED / production OFF unchanged.
