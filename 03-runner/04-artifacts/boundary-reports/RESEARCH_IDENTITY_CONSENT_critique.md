# BOUNDARY CRITIQUE — RESEARCH_IDENTITY_CONSENT.md

**Critic prompt**: M6-PC0202 (RESEARCH_IDENTITY_CONSENT_CRITIC) · **Role**: BOUNDARY_ADVERSARY · **Mode**: analysis_only
**Target**: `04-artifacts/analysis/research/RESEARCH_IDENTITY_CONSENT.md` (produced by M6-P0202)
**Author does not respond here.** Findings feed Phase-0 design and the producing prompt M6-P0702 (CONTRACT_IDENTITY_CONSENT).

> `global_gateway_state` stays **BLOCKED**, `production_flag` stays **OFF**. Nothing here flips a gate or a flag. Self-report; the runner gate decides PASS.

---

## 1. Entry gate (verified before review)

| Check | Result | Evidence |
|---|---|---|
| M6-PC0202 is RUNNING in the ledger | ✅ | `PROMPT_EXECUTION_LEDGER_LOCKED.csv` row 33 — `M6-PC0202 … BOUNDARY_ADVERSARY … RUNNING` |
| Dependency M6-P0202 is complete | ✅ | ledger row 32 — `M6-P0202 … PASS`; evidence `M6-P0202.json` status=PASS |
| Required inputs present | ✅ | brief, `RESEARCH_IDENTITY_CONSENT.md`, `M6-P0202.json` all read |

Entry gate holds; review proceeded.

## 2. Method

Direct citation verification (every `[DOC]`/`[REG]` anchor re-opened) plus an adversarial **find → refute-verify** pass: 5 finder lenses (citation-fidelity, boundary-overreach, **pii-exposure**, **consent-fail-closed**, owner-decisions/executability) surfaced candidates; each was handed to a separate verifier told to **try hard to refute it** and grade severity. **15 candidates verified; only 1 survived.** The 14 dismissed are summarized in §5.

Severity rubric: **BLOCKER** = research unusable / unconditional hard-boundary breach / M6 owns-or-edits identity/consent / sends CRM / resolves an owner decision / a consent-fail-OPEN external send; **MAJOR** = would cause boundary overreach, PII leak, dropped owner dependency, or a fail-open design *if followed*, but mitigated elsewhere; **MINOR** = citation precision / completeness / low-impact slip.

## 3. Overall verdict

**No BLOCKER, no MAJOR — the cleanest of the Phase-0 research artifacts reviewed so far.** Every `[DOC]`/`[REG]` anchor verified faithful and correctly section-tagged (L115/§7, L118/§7, L266/§13, L62/§3, L60/§3, L257/§12; the `[REG SPEC §10.1]` field claim also checks out — `ads_measurement_event` genuinely carries `customer_id`, `guest_id`, `consent_snapshot_id`, all `optional string`, extract L191–211).

Two structural strengths worth recording for the judge:
- **Consent fail-closed is correct.** The §3 two-checkpoint model (event-time immutable snapshot **+** a *fresh* send-time re-read of current consent) faithfully implements RULE-002's "at event/send time", and the 5 enforcement points (§4) all default-DENY. This research **gets right the send-time re-validation gate that the M6-PC0201 event-registry research missed** — a notable consistency win.
- **Boundary is clean.** Read-only on identity/consent; M6 never creates/reassigns identity, never edits consent, never sends CRM or decides member rights (§5, §4 checkpoint 5). The adversarial boundary, PII-exposure, and consent-fail-open attacks all failed (§5).

The single confirmed defect is **1 MINOR** citation-precision slip.

| ID | Severity | Category | One-line |
|---|---|---|---|
| F1 | MINOR | unsupported-claim | §4 checkpoint 5 cites `[REG RULE-017]` for the CRM **consent** gate, but RULE-017 has no consent term |

---

## 4. Confirmed finding

### F1 — MINOR — CRM-path consent clause mis-cited to RULE-017 (which has no consent element)
**Category**: unsupported-claim / citation-precision · **Verdict**: CONFIRMED MINOR (finder proposed MAJOR; verifier downgraded to MINOR after confirming no fail-open follows)

**Exact claim (research §4 checkpoint 5, L102):** "**CRM path** — consent **plus** suppression state must pass `[REG RULE-017]`; **M6 never sends CRM itself** `[BRIEF]` — it only measures/gates; the actual CRM send is CRM-owned."

**Evidence:**
- `RULES_LOCKED` L26 (**RULE-017**): "Suppression and risk locks must be reflected in measurement and gates … plus CRM suppression (doc §15). **No scale while ANY of these is active.**" — its normative clause is a **Scale-Gate** rule; it contains **zero consent language**.
- The consent authority is `RULES_LOCKED` L11 (**RULE-002**): "…without valid consent at event/send time there is … **NO CRM send**."
- The precise CRM consent+suppression doc anchor is **extract §10 L188**: "CRM | CRM_REORDER_SENT, CRM_REORDER_ORDER_CREATED | **CRM chỉ khi suppression/consent pass**" (and §9 L165 "CRM revenue phải xuất phát từ CRM eligibility, **suppression pass** và order verified").

**Defect:** Checkpoint 5 attaches "**consent** … must pass" to RULE-017 alone, but RULE-017 carries no consent term and its verb is *scale*, not *send*. A coder tracing the CRM-send consent gate to RULE-017 lands on a rule with no consent and a Scale-Gate effect — a broken trace that misplaces the check at the Scale Gate rather than the CRM send path. RULE-017 legitimately owns only the **suppression** half.

**Why MINOR (not the proposed MAJOR):** no fail-open or boundary harm follows under verbatim consumption — the §4 section header (L88) already cites `[REG RULE-002]` as governing the whole fail-closed block, and the same checkpoint preserves "M6 never sends CRM itself … CRM-owned". CRM consent fail-closed is therefore redundantly and correctly established elsewhere; the residual is purely citation precision.

**Fix:** cite **RULE-002** (and ideally **extract §10 L188 / §9 L165**) for the *consent* clause; keep RULE-017 only for the *suppression*/scale-reflection half.

---

## 5. Attacked and dismissed (did not survive adversarial verification)

The research was attacked hard across boundary, PII, consent-fail-open, and owner-decision axes; 14 candidates were refuted. Grouped:

1. **§6 owner-decision list omits M6-OD-012 (evidence masking format).** DISMISSED — OD-012 is a **pack-execution, hook-enforced evidence-format** decision (Blocks = "evidence format"), not a dependency of the CTR-005/006 read contract this research designs. §5's `abc***xy` usage is faithful application of the already-locked masking rule; nothing is resolved by assumption.
2. **§2 `[EXT]` append-only guest→customer link history = M6 shadow identity-resolution store.** DISMISSED — foreclosed on multiple levels: the proposal records "the mapping M6 **observes**", never resolves/reassigns (L52–55), consumes the Identity-owned resolution, and is labeled owner-review `[EXT]`.
3. **§3 send-time re-validation could re-use the stale snapshot / fail-open.** DISMISSED — the text mandates a **fresh** read of current consent (L82–83); the measurement outbox worker is M6-owned and genuinely evaluates `consent_valid` at send time (send_policy L257; DQ-Gate extract L302 "valid tại thời điểm event/external send"); §4 default is DENY. No fail-open window.
4. **§7 traceability row "demotes send-time re-validation to a proposal".** DISMISSED — the row scopes "send-time re-validation **as a distinct checkpoint**" as `[PACK]` (the *checkpoint framing* is pack-added); the underlying consent-at-send-time requirement is RULE-002/owner-mandated and cited in §3/§4. No contradiction.
5. **`[REG RULE-017]` doesn't govern the CRM path at all** (broader framing of F1). DISMISSED at that breadth — RULE-017 *does* own the CRM-**suppression** half; only the **consent** attribution is wrong (retained as F1 MINOR).
6. **§6 omits event_registry / M6-CTR-003 / M6-ENTRY-003 and M6-ENTRY-001 (verified-revenue chain) and M6-ENTRY-002 (Gateway psid).** DISMISSED (three separate candidates) — §6 is **subject-scoped to identity/consent owner-decisions** for M6-P0702, not a full upstream-contract sweep; those dependencies are tracked and enforced independently by CONTRACT_REGISTER, ENTRY_EVIDENCE_REGISTER, and the M6.2A entry gate (registry Invariant 1). The §2 chain is cited as the doc's *rationale*, not a build instruction; §1 keys off `guest_contacts` (Customer identity), not `psid`.
7. **`[REG CTR-007]` cited as the consent authority at conversion-event creation; `[REG §18]` dangling.** DISMISSED — §4's header establishes the normative consent rule (RULE-002 / DOC L118); CTR-007 is an object reference, not the authority. `§18` resolves to `ENTRY_EVIDENCE_REGISTER` L21 "Consumed-boundary reference (doc §18…)".

## 6. Acceptance-check trace

- [x] Every finding cites the exact claim and its evidence (research section/line + source file line/row).
- [x] Verdict per finding: BLOCKER/MAJOR/MINOR — 0 BLOCKER, 0 MAJOR, 1 MINOR (F1).
- [x] No raw secret or unmasked PII (only register/extract/research text quoted; no channel-origin data present).
- [x] Nothing self-certified PASS; `04-artifacts/state/` untouched; gateway BLOCKED / production OFF unchanged.
