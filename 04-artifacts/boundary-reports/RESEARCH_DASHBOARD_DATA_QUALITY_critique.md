# BOUNDARY CRITIQUE — RESEARCH_DASHBOARD_DATA_QUALITY.md

**Critic prompt**: M6-PC0207 (RESEARCH_DASHBOARD_DATA_QUALITY_CRITIC) · **Role**: BOUNDARY_ADVERSARY · **Mode**: analysis_only
**Target**: `04-artifacts/analysis/research/RESEARCH_DASHBOARD_DATA_QUALITY.md` (produced by M6-P0207)
**Author does not respond here.** Findings feed Phase-0 design, the producing prompts M6-P0708/0712/0713, and slice M6.2F.

> `global_gateway_state` stays **BLOCKED**, `production_flag` stays **OFF**. The dashboard flips no gate and triggers nothing. Self-report; the runner gate decides PASS.

---

## 1. Entry gate (verified before review)

| Check | Result | Evidence |
|---|---|---|
| M6-PC0207 is RUNNING in the ledger | ✅ | `PROMPT_EXECUTION_LEDGER_LOCKED.csv` row 43 — `M6-PC0207 … BOUNDARY_ADVERSARY … RUNNING` |
| Dependency M6-P0207 is complete | ✅ | ledger row 42 — `M6-P0207 … PASS`; evidence `M6-P0207.json` status=PASS |
| Required inputs present | ✅ | brief, `RESEARCH_DASHBOARD_DATA_QUALITY.md`, `M6-P0207.json` all read |

Entry gate holds; review proceeded.

## 2. Method

Direct citation/schema verification plus an adversarial **find → refute-verify** pass: 5 finder lenses (**revenue-datamart-boundary**, **dq-propagation**, owner-decisions, citation-fidelity, executability) surfaced candidates; each was handed to a separate verifier told to **try hard to refute it** and grade severity. **9 candidates verified; 5 confirmed (collapsing to 3 distinct issues), 4 refuted.** Hermetic mode (no web-fetch).

Severity rubric: **BLOCKER** = dashboard shows unverified revenue / Data Mart as trigger owner / auto-scales / invents a threshold / raw PII / resolves an owner decision; **MAJOR** = would cause such a breach *if followed* but mitigated; **MINOR** = citation/tagging precision, internal inconsistency, low-impact slip.

## 3. Overall verdict

**No BLOCKER, no MAJOR.** A clean, boundary-tight artifact. All citations verified faithful — §14 has exactly **14 KPI metrics** (`ROAS = Revenue Verified / Ads Spend`, L284; `Revenue Verified = SUM(verified_revenue), Chỉ ORDER_VERIFIED`, L283), §15 has exactly the **8 gate items** the research lists, and the L308 dashboard-DQ-gate quote is exact. The two highest-stakes attack lenses returned **zero findings**:
- **Revenue + Data-Mart boundary — clean.** No path to show non-`ORDER_VERIFIED` revenue (FAIL-001), no Data-Mart-as-trigger-owner (FAIL-005), no auto-scale (RULE-010); §4's worst-status propagation (FAIL▸HOLD▸PASS) genuinely blocks "làm đẹp dashboard bằng dữ liệu chưa verified"; the dashboard stays read-only.
- **Executability — clean.** M6-P0708/0712/0713 and M6.2F can consume the evidence-bundle (§3) and propagation rule (§4) without guessing; no scope leak.
- **Owner-decision handling — clean.** Alert thresholds are **not** invented (§5: `MISSING → M6-OD-002`); the OD-008 and OD-005 "omission" attacks were **refuted** — the dashboard reads a *pre-classified, pre-attributed* support view, its revenue is fixed to `ORDER_VERIFIED` by locked RULE-003 + the §14 formula, and OD-005's register note explicitly *permits* multi-model dashboard display while blocking only M6.2E/M6.2G.

The confirmed defects are **3 MINOR** — all citation/tagging precision (one is a propagated over-restriction).

| ID | Severity | Category | One-line |
|---|---|---|---|
| F1 | MINOR | citation precision | §5 header `[REG §18]` labels a DOC section as a register section (correct: `[BRIEF / DOC §18]`); pack-wide header nit |
| F2 | MINOR | unsupported-claim | §4 attributes "only **HIGH-confidence** may feed the Scale Gate" to `[REG RULE-009]`, but RULE-009 only bars LOW/HOLD/conflict (silent on MEDIUM) — over-restriction, propagated from M6-PC0206 F1 |
| F3 | MINOR | citation precision | §4 `[REG FAIL-001 / §4 boundary]` folds a genuine **DOC §4** quote under the `[REG]` class (correct: `[REG FAIL-001 / DOC §4 L78]`) |

---

## 4. Confirmed findings

### F1 — MINOR — `[REG §18]` labels a DOC section as a register section
**Verdict**: CONFIRMED MINOR (one verifier MINOR; a second verifier judged it defensible/below-MINOR)

**Exact claim:** §5 header L92 "## 5. Boundary & safety guards `[BRIEF / REG §18]`".

**Evidence:** the file's legend (L16–17) reserves `[REG]` for locked pack registers (ID-keyed); no register carries a numbered "§18". "§18" is an owner-**DOC** section (extract L355 "## 18. Tích hợp với Module 3, 4, 5, 7, 8"; also surfaced in `ENTRY_EVIDENCE_REGISTER` "Consumed-boundary reference (doc §18)"). Correct tag: `[BRIEF / DOC §18]`.

**Defect:** a tagging-precision slip against the file's own legend. No boundary harm — every §5 guard is independently re-cited (RULE-003/010/012/014, FAIL-005, CTR-018, OD-002). *(Honest note: one verifier rejected this as "defensible / below MINOR" on the ground that the §18 boundary content is itself register-locked via RULE-018/019, so `[REG]` is arguably acceptable.)* **Fix (pack-wide):** retag `[BRIEF / DOC §18]` — this header form recurs across the Phase-0 research files (same as **M6-PC0204 F5 / PC0205 F2 / PC0206 F2**); normalize once.

### F2 — MINOR — `HIGH-confidence` scale-evidence over-restriction mis-attributed to RULE-009
**Verdict**: CONFIRMED MINOR (two verifiers)

**Exact claim (§4 L86–87):** "**Scale-evidence link** `[REG RULE-009]`: only metrics that are **PASS** (and, for attribution, **HIGH-confidence** / non-conflicting) may feed the Scale Gate; HOLD/FAIL metrics are **never** scale evidence."

**Evidence:** `RULES_LOCKED` L18 / extract **L240** (RULE-009): "Missing source or conflicting attribution data ⇒ LOW confidence or HOLD; such data is never used as scale evidence" — bars only LOW/HOLD/conflict, **silent on MEDIUM**. Schema extract L233: `source_confidence: HIGH | MEDIUM | LOW`.

**Defect:** the "HIGH-confidence" clause narrows RULE-009's exclusion (LOW/HOLD/conflict out) into a positive "HIGH-only" inclusion threshold that **also excludes MEDIUM**, and mis-attributes this stricter rule to `[REG RULE-009]`. A coder implementing the CTR-024 (M6-P0713) scale-readiness filter verbatim could encode `source_confidence == HIGH` and discard valid MEDIUM-confidence rows the spec allows. **Fail-closed-safe** (it excludes data from scale, never enables unverified revenue or auto-scale), and out of the read-only dashboard's own action scope, so MINOR. This is the **same over-restriction confirmed in the sibling attribution critique (M6-PC0206 F1)** — a coordinated fix in the attribution rule/CTR-024 contract resolves both. **Fix:** state as RULE-009's actual mandate (exclude missing-source/conflict → LOW/HOLD) and defer the exact usable-confidence cutoff (MEDIUM?) to the owner.

### F3 — MINOR — `[REG FAIL-001 / §4 boundary]` folds a DOC quote under the register class
**Verdict**: CONFIRMED MINOR

**Exact claim (§4 L82):** "This is exactly what blocks *'làm đẹp dashboard bằng dữ liệu chưa verified'* `[REG FAIL-001 / §4 boundary]`."

**Evidence:** the quoted phrase is a **genuine verbatim owner-doc quote** from extract **§4 Boundary Lock L78** (verified) — so per the file's legend (L16, "[DOC] = owner document / extract line") it must carry `[DOC §4 L78]`; "§4 boundary" is a doc section, not a register key. The `[REG FAIL-001]` half is a valid register cite.

**Defect:** the tag folds a DOC-§4 pointer under `[REG]` without a `[DOC]` token — precise form `[REG FAIL-001 / DOC §4 L78]`. No boundary harm (the constraint stays mandatory; the quote is real). **Fix:** split the source classes. *(The sibling `[DOC CTR-018 "Chỉ đọc data mart/support view"]` pointer-format at §2 L49/§5 L94 was tested and **dismissed as cosmetic** — the `[DOC]` class is correct and `CTR-018` resolves one hop to extract §19 L373; optionally tighten to `[DOC §19 L373]`.)*

---

## 5. Attacked and dismissed (did not survive adversarial verification)

1. **Revenue / Data-Mart / auto-scale boundary breach.** DISMISSED (lens returned zero findings) — no path to display non-`ORDER_VERIFIED` revenue, use the Data Mart as a trigger owner, or auto-scale; §2/§4/§5 hold.
2. **Executability gap.** DISMISSED (lens returned zero findings) — the design is consumable by M6-P0708/0712/0713 without guessing.
3. **§6 omits M6-OD-008 (PAYMENT_COMPLETED revenue-adjacency).** DISMISSED — OD-008's Blocks column is M6.2E/M6.2F **edge handling** (the event-ingestion/classification edge), not the read-only dashboard; the dashboard aggregates *already-classified* verified revenue, fixed to `ORDER_VERIFIED` by RULE-003 + the §14 formula, and OD-008 resolves the same way in both branches — orthogonal to the dashboard.
4. **§6 omits M6-OD-005 (attribution model).** DISMISSED — OD-005's Blocks column targets M6.2E/M6.2G (attribution is materialized upstream; the dashboard reads the pre-attributed view), and its register note explicitly *permits* the dashboard to show multiple models. The dashboard never picks a model, so OD-005 is not an M6.2F acceptance dependency.

## 6. Acceptance-check trace

- [x] Every finding cites the exact claim and its evidence (research section/line + source file line/row).
- [x] Verdict per finding: BLOCKER/MAJOR/MINOR — 0 BLOCKER, 0 MAJOR, 3 MINOR (F1–F3); F1's one-verifier dissent recorded.
- [x] No raw secret or unmasked PII (only register/extract/research text quoted; no channel-origin data present).
- [x] Nothing self-certified PASS; `04-artifacts/state/` untouched; gateway BLOCKED / production OFF unchanged; dashboard flips no gate.
