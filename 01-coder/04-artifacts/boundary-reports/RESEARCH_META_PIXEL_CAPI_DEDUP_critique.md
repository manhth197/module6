# BOUNDARY CRITIQUE — RESEARCH_META_PIXEL_CAPI_DEDUP.md

**Critic prompt**: M6-PC0204 (RESEARCH_META_PIXEL_CAPI_DEDUP_CRITIC) · **Role**: BOUNDARY_ADVERSARY · **Mode**: analysis_only
**Target**: `04-artifacts/analysis/research/RESEARCH_META_PIXEL_CAPI_DEDUP.md` (produced by M6-P0204)
**Author does not respond here.** Findings feed Phase-0 design, the producing prompt M6-P0705 (CTR-008), and the owner decisions M6-OD-003 / M6-OD-004.

> `global_gateway_state` stays **BLOCKED**, `production_flag` stays **OFF**. Nothing here flips a gate or a flag. Self-report; the runner gate decides PASS.

---

## 1. Entry gate (verified before review)

| Check | Result | Evidence |
|---|---|---|
| M6-PC0204 is RUNNING in the ledger | ✅ | `PROMPT_EXECUTION_LEDGER_LOCKED.csv` row 37 — `M6-PC0204 … BOUNDARY_ADVERSARY … RUNNING` |
| Dependency M6-P0204 is complete | ✅ | ledger row 36 — `M6-P0204 … PASS`; evidence `M6-P0204.json` status=PASS |
| Required inputs present | ✅ | brief, `RESEARCH_META_PIXEL_CAPI_DEDUP.md`, `M6-P0204.json` all read |

Entry gate holds; review proceeded.

## 2. Method

Direct citation verification plus an adversarial **find → refute-verify** pass: 5 finder lenses (citation-fidelity, **pii-platform-boundary**, **platform-fact-discipline**, owner-decisions, executability) surfaced candidates; each was handed to a separate verifier told to **try hard to refute it** and grade severity. **15 candidates verified; 6 confirmed (collapsing to 5 distinct issues), 9 refuted.**

**Hermetic-mode note (deliberate):** this critique did **not** web-verify Meta's API. The research responsibly quarantines every external Meta fact under a `[PLATFORM]` tag = "verify vs current Meta docs before implementation; not authoritative here"; neither the research nor this critique *asserts* those facts as settled truth, so the "verify-API-facts-before-asserting" discipline is satisfied by the tag + the impl-time verification requirement. The review therefore attacked the research's **soundness, boundary-safety, tagging discipline, and internal consistency**, not Meta's live behaviour. The stated mechanics are consistent with long-stable Meta CAPI behaviour, but **must still be re-verified at implementation** per the `[PLATFORM]` flags.

Severity rubric: **BLOCKER** = research unusable / raw PII to platform / M6 resolves an owner decision / hard-boundary breach; **MAJOR** = would cause a PII leak, boundary overreach, owner-decision resolution, or dropped dependency *if followed*, but mitigated; **MINOR** = citation/tagging precision, completeness, low-impact slip.

## 3. Overall verdict

**No BLOCKER, no MAJOR.** Clean, epistemically careful artifact. The three highest-stakes attacks were **refuted**:
- **PII is fail-closed and airtight.** Until M6-OD-003 exists, no PII-bearing CAPI field is sendable (§3 boundary lock L71–73); `external_id` is gated as PII by both the boundary lock and §5.1; Pixel stays public-safe; the "raw PII could leak" attacks failed.
- **OD-003/OD-004 are made *decidable*, not resolved.** §5/§6 enumerate the owner's questions ("each item is a question, not a proposed answer", L94); the "SHA-256"/permitted-field enumeration was refuted as *describing what must be decided*, not deciding it. No owner decision is resolved.
- **Platform-fact discipline holds.** The load-bearing "shared-event_id invariant" and §4 mapping are correctly `[PLATFORM]`/`[EXT]`-tagged and deferred to M6-P0705; the over-assertion attacks failed.

The confirmed defects are **5 MINOR** — citation/tagging precision and one cross-research consistency slip. Two are worth acting on (F1, F2).

| ID | Severity | Category | One-line |
|---|---|---|---|
| F1 | MINOR | unsupported-claim | `[REG FAIL-001]` mis-cited for a double-count; the L26 anchor even *redefines* FAIL-001 as "revenue misuse via double count" (a locked gate it never states) — pack-wide recurring slip (cf. M6-PC0203 F2) |
| F2 | MINOR | internal-inconsistency | `idempotency_key`'s role **contradicts** sibling M6-P0203 §4, yet §4/§1 cite "(ties to M6-P0203 §4)" as if they agree — an inverted cross-reference on a locked key both feed into CTR-008 |
| F3 | MINOR | platform-fact-discipline | §1 L36 states a Meta platform fact (`Meta dedups by … event_id`) **untagged**, breaching the file's own `[PLATFORM]` labeling rule |
| F4 | MINOR | citation precision | §6.3 tags secret-handling `[REG RULE-014]`, but RULE-014 governs raw **PII**, not secrets/tokens — the secret_ref mandate is RULE-H02 (+FAIL-008) |
| F5 | MINOR | citation precision | §7 header `[BRIEF / REG §18]` labels a **DOC** section as a register section (correct tag `[DOC §18]`); pack-wide header convention nit |

---

## 4. Confirmed findings

### F1 — MINOR — `[REG FAIL-001]` mis-cited (and re-defined) for the double-count case
**Verdict**: CONFIRMED MINOR (two verifiers)

**Exact claim:** §2 L53–56 "the conversion is **double counted** → this would violate `[REG RULE-005]` and, for revenue events, risk `[REG FAIL-001]`."; **and, more firmly, the anchor gloss L26** "`[REG FAIL-001]` (revenue misuse via **double count**)".

**Evidence:** `FAIL_GATE_REGISTER` L13 — FAIL-001 trips **only** when "Quote/cart/order draft/payment waiting/COD waiting **bị tính revenue**" (a non-verified *state* counted as revenue). A Meta dedup miss double-counts a genuine **ORDER_VERIFIED** conversion (over-counting *real* revenue) — a dedup failure governed by **RULE-005** ("No double count", co-cited) and the Data-Quality dedup gate (extract L303), not FAIL-001.

**Defect:** the §2 "risk FAIL-001" is a citation-precision slip; worse, the L26 anchor **redefines** the locked, owner-1:1 fail gate as "revenue misuse via double count" — a mechanism the register never states, which could propagate a wrong `fail_gate_tripped` classification into downstream evidence (M6-P0705). Low behavioural impact (RULE-005 co-cited and correct). **Fix:** drop the FAIL-001 attribution (both L26 and L55); cite RULE-005 / the DQ dedup gate for double-count. *Note:* the identical FAIL-001-for-double-count mis-fit was confirmed in the sibling outbox research (**M6-PC0203 F2**) — a **pack-wide recurring slip** worth a single coordinated fix.

### F2 — MINOR — `idempotency_key`'s role contradicts sibling M6-P0203, with a false "ties to" cross-reference
**Verdict**: CONFIRMED MINOR (executability lens; not analyst-seeded — surfaced by the workflow)

**Exact claim (this research):** §4 L82 "`idempotency_key` `[DOC L255]` | M6 outbox replay guard | **keep internal**; a crash-retry reuses the **same** `event_id`, so Meta still dedups **(ties to M6-P0203 §4)**"; reinforced §1 L34 (`idempotency_key` = "M6's **internal** replay guard").

**Evidence:** sibling `RESEARCH_OUTBOX_WORKER_PATTERNS.md` (M6-P0203) §4 L87–94 says the **opposite**: "`idempotency_key` … **carried on the external dispatch** so the **platform** collapses duplicates … the `idempotency_key` makes the platform dedup".

**Defect:** the two Phase-0 researches that both feed CTR-008 (M6-P0705) describe the same locked key oppositely — P0204: `idempotency_key` stays **internal**, the external Meta dedup rides on a **derived `event_id`**; P0203: `idempotency_key` is **carried externally** and *is* the platform-dedup field. P0204's "(ties to M6-P0203 §4)" claims agreement where they invert. (P0204's Meta-specific model — dedup by shared `event_id` — is the technically-accurate one for Meta; but the contradiction and false cross-reference are the defect.) MINOR because both are `[EXT]` proposals explicitly deferred to M6-P0705. **Fix:** reconcile the `idempotency_key` vs `event_id` external-dedup mapping in the CTR-008 contract (M6-P0705), and correct the cross-reference so it does not assert agreement.

### F3 — MINOR — §1 states a Meta platform fact untagged
**Verdict**: CONFIRMED MINOR

**Exact claim (§1 L36):** "Neither is, by itself, Meta's dedup key. **Meta dedups by its own field (`event_id`).** So the design question is a mapping, not a reuse (§2, §4)."

**Evidence:** the file's legend (L13) makes "every externally-sourced claim / platform fact labeled" an acceptance rule, and (L17–19) defines `[PLATFORM]`. §1 sits under a `[DOC L254-255]` header; the sentence carries no `[PLATFORM]` tag, though the identical fact **is** tagged `[PLATFORM]` in §2 (L43/L46) and classified `[PLATFORM]` in the §9 traceability table.

**Defect:** a literal breach of the file's own labeling discipline at the point of use. Fully mitigated (the sentence forwards to §2's bold `[PLATFORM]` gate; §8/§9 re-classify it "verify … NOT owner requirements"; the fact is correct) — no coder treats it as owner-mandated or skips verification. **Fix:** add `[PLATFORM]` to L36.

### F4 — MINOR — secret-handling tagged `[REG RULE-014]` (a raw-PII rule), not the secret rule
**Verdict**: CONFIRMED MINOR

**Exact claim (§6.3 L116–117):** "Credentials/config as `secret_ref` only: `pixel_id`/dataset_id, CAPI `access_token`, ad-account ids — never in code/logs/evidence `[BRIEF, REG RULE-014]`."

**Evidence:** `RULES_LOCKED` L23 — **RULE-014** governs "no raw **PII** in code, logs or evidence" and says nothing about secrets/tokens/credentials. The rule that mandates `secret_ref` is **RULE-H02** ("Secret values exist only as `secret_ref`…"), with **FAIL-008** as the exposure gate. `access_token`/`pixel_id`/`dataset_id`/ad-account ids are secrets/config, not PII.

**Defect:** the `[REG RULE-014]` tag mis-states which register rule requires `secret_ref`. Low impact — `[BRIEF]` is co-cited and a verbatim consumer still uses `secret_ref` (correct). **Fix:** cite **RULE-H02** (and FAIL-008) for secret handling; keep RULE-014 for the raw-PII fields.

### F5 — MINOR — `[REG §18]` labels a DOC section as a register section
**Verdict**: CONFIRMED MINOR (cosmetic / pack-wide convention)

**Exact claim (§7 header L121):** "## 7. Boundary & safety guards `[BRIEF / REG §18]`"

**Evidence:** the file's own legend (L16) defines `[REG]` = "locked pack register"; no register has a numbered "§18" section (RULES_LOCKED/FAIL_GATE are ID-keyed). "§18" is an **owner-doc** section (the consumed-boundary block, surfaced in `ENTRY_EVIDENCE_REGISTER` "Consumed-boundary reference (doc §18)"; also RULE-013/RULE-018). Correct tag: `[DOC §18]`.

**Defect:** a mis-scoped/imprecise citation prefix. Lowest-priority — the §7 boundary content is real and independently re-cited, and this `[… / REG §18]` header form recurs across the Phase-0 research files, so it is a **pack-wide header convention** to normalize rather than a defect unique to this artifact. **Fix (pack-wide):** retag as `[DOC §18]` (or `[REG §18 boundary]` pointing explicitly at ENTRY_EVIDENCE_REGISTER's consumed-boundary reference).

---

## 5. Attacked and dismissed (did not survive adversarial verification)

1. **`external_id` "may be sent hashed or plain" (§3 L66–67) → raw-id leak.** DISMISSED (two verifiers) — the bullet is a `[PLATFORM — verify each field]` description of Meta's convention, not an M6 directive; the same-section boundary lock (L71–73) and §5.1 independently gate `external_id` as OD-003-pending PII, so verbatim consumption fail-closes it.
2. **§2 "load-bearing" consequence over-asserted on an unverified premise.** DISMISSED — the consequence sits under the §2 `[PLATFORM]` header and inherits the verify-before-implementation gate.
3. **§4 shared-`event_id` derivation stated without a tag.** DISMISSED — §9 L149 classifies §4 as `[EXT]/[PLATFORM]` proposal.
4. **§5 enumerating permitted-PII fields = resolving OD-003.** DISMISSED — enumerating the *candidate* fields as the owner's question ("which fields may be sent… a privacy/legal scope decision") is making the decision *decidable*, not deciding it; OD-003's discretion (which/whether) is left to the owner.
5. **§3 boundary lock is CAPI-only, leaving Pixel advanced-matching PII ungated.** DISMISSED — OD-003 governs Pixel/CAPI/Offline; §3 keeps Pixel public-safe and the fail-closed default covers it.

## 6. Acceptance-check trace

- [x] Every finding cites the exact claim and its evidence (research section/line + source file line/row).
- [x] Verdict per finding: BLOCKER/MAJOR/MINOR — 0 BLOCKER, 0 MAJOR, 5 MINOR (F1–F5).
- [x] No raw secret or unmasked PII (only register/extract/research text quoted; no channel-origin data present).
- [x] Nothing self-certified PASS; `04-artifacts/state/` untouched; gateway BLOCKED / production OFF unchanged.
