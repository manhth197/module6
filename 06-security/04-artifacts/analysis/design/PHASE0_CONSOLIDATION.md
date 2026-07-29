# PHASE0_CONSOLIDATION — design-set cross-check + summary for the judge

**Prompt**: M6-P0308 · **Phase**: PHASE0 (design) · **Mode**: plan_only (no code, no call) · **Feeds**: JUDGE
**M6-P0309** (order 59), then CONTRACT_HARMONIZATION (M6-P0700+).
**Scope**: cross-check the Phase-0 design band (M6-P0300..0307) against each other and against every BLOCKER
critic finding; produce the design summary the judge rules from. **Anchors**: the eight design deliverables in
`04-artifacts/analysis/design/`; the critic/verification record in `04-artifacts/evidence/prompts/`.

> **Count note (verify-before-assert).** The prompt says *"seven design outputs"*; the design band M6-P0300..0307
> produced **eight** deliverables — the seven `*_DESIGN/BASELINE` docs **plus** `TEST_STRATEGY.md`. All eight are
> cross-checked here (including one more than stated is complete, not under-scoped). Surfaced for the judge, not
> silently reconciled. `global_gateway_state=BLOCKED`, `production_flag=OFF`.

## Sourcing legend

- `[DOC]` — owner doc / extract line. **Only `[DOC]` items are owner requirements.** · `[REG]` — locked
  register. · `[PACK]` — pack convention (owner-review). · `[EXT]` — general practice, proposal only.

---

## 1. The Phase-0 design set (inventory) `[REG evidence/prompts]`

| # | Deliverable | Prompt | Evidence | Covers |
|---|---|---|---|---|
| 1 | `ARCH_BASELINE.md` | M6-P0300 | PASS/0-blk | 9-layer §5 architecture; all 26 CTR placed; cross-cutting invariants |
| 2 | `DATA_MODEL_BASELINE.md` | M6-P0301 | PASS/0-blk | 9 owned / 5 consumed objects; 2 locked schemas; append-only + immutability |
| 3 | `EVENT_FLOW_DESIGN.md` | M6-P0302 | PASS/0-blk | ingest→egress pipeline; send_policy; fail-closed branches; 2 consent checkpoints |
| 4 | `ATTRIBUTION_DESIGN.md` | M6-P0303 | PASS/0-blk | resolver chain; confidence/conflict; immutability; multi-model (M6-OD-005) |
| 5 | `DASHBOARD_DESIGN.md` | M6-P0304 | PASS/0-blk | 14 KPIs; verified-only revenue at query layer; DQ propagation; data-mart read-only |
| 6 | `SCALE_LEARNING_DESIGN.md` | M6-P0305 | PASS/0-blk | scale-request workflow; learning skeleton; orthogonality seam |
| 7 | `TEST_STRATEGY.md` | M6-P0306 | PASS/0-blk | 18 smokes build/run (staged); fixtures; correlation_id+evidence_id; contract gating |
| 8 | `SECURITY_PRIVACY_DESIGN.md` | M6-P0307 | PASS/0-blk | consent/hash/secret_ref/PII/untrusted-input; admin-API + worker + evidence access |

Every deliverable is `plan_only`, cites rules/contracts by ID, and pre-empts no owner decision (verified per
its own evidence).

---

## 2. Cross-cutting invariant consistency (the contradiction cross-check) `[PACK]`

Each spine invariant must be stated **consistently** (never contradicted) across the docs that touch it:

| Invariant | Authority | Asserted consistently in | Consistent? |
|---|---|---|---|
| Revenue only from `ORDER_VERIFIED`; quote/draft/unpaid never revenue | RULE-003 | DATA_MODEL §5 · ATTRIBUTION §1 · DASHBOARD §2 · EVENT_FLOW §2 (Stage 4) · SCALE_LEARNING §2.2 | ✅ |
| Consent fail-closed at **event + send time** (two checkpoints) | RULE-002 / §15 L302 | EVENT_FLOW §5 · SECURITY §1 | ✅ |
| Attribution immutable after `ORDER_VERIFIED`; correction = adjustment record `{actor, reason, audit, evidence}` | RULE-008 / §11 L242 | DATA_MODEL §5 · ATTRIBUTION §4 | ✅ (identical field set) |
| Status-transition audit `{actor, from→to, reason, evidence_ref, ts}` is `[PACK]`, **distinct** from the doc-locked adjustment record | `[PACK]` (RULE-008 governs the adjustment record, not this) | SCALE_LEARNING §2.1 (canonical) · DATA_MODEL §4 (referenced) | ⚠ minor phrasing divergence → §6.5 |
| No executable scale path; compute & propose only | RULE-010 / FAIL-006 | ARCH §1.7/§3 · SCALE_LEARNING §1/§2 · DASHBOARD §4 | ✅ |
| Guarded learning; no full-auto-publish; **safe-range ≠ budget/scale** | RULE-011 / LEX-006 | ARCH §1.8 · SCALE_LEARNING §3/§4 | ✅ (orthogonality seam) |
| Data mart = read-only support view; never a trigger | RULE-012 | ARCH §1.6 · DASHBOARD §4 | ✅ |
| Every event registered before log/send; unknown → reject/HOLD | RULE-001 | ARCH §1.1 · EVENT_FLOW §2.1 · TEST_STRATEGY (SMK-001) | ✅ |
| `dedup_key`/`idempotency_key` locked formulas; no double count | RULE-005 | DATA_MODEL §7 · EVENT_FLOW §2/§3 · TEST_STRATEGY §3 | ✅ (identical formulas) |
| No raw PII/secret; `secret_ref` + `abc***xy` masking | RULE-014/H02 | every doc's boundary § + SECURITY §3/§4 | ✅ |
| Staged: `global_gateway_state=BLOCKED`, `production_flag=OFF` | RULE-H01 | every doc footer | ✅ |
| Channel-origin text = untrusted DATA | RULE-H03 | every doc's boundary § + SECURITY §5 | ✅ |

**No contradiction on any spine invariant** across the eight docs. The doc-locked **adjustment record**
`{actor, reason, audit, evidence}` (row 3) is aligned identically in DATA_MODEL §5 and ATTRIBUTION §4 (the
P0301 fix). The `[PACK]` **status-transition audit** (row 4) carries a residual **minor phrasing divergence** —
canonical `{actor, from→to, reason, evidence_ref, ts}` in SCALE_LEARNING §2.1 vs an "adds"-phrasing in
DATA_MODEL §4 — which does **not** relax immutability and is carried to §6.5 for the harmonization band to
reconcile into one canonical shape.

---

## 3. Contract inventory consistency `[REG CONTRACT_REGISTER]`

- **All 26 `M6-CTR`** placed once in ARCH §2 (contract→layer) and reflected in DATA_MODEL §1 (9 owned + 5
  consumed as row-storage; APIs/workers/evidence-pack are the remaining 12). No CTR dropped or double-owned.
- **DRAFT_LOCKED set consistent** across docs: CTR-001 (measurement, 20 fields), CTR-002 (attribution, 19
  fields), CTR-015 (dashboard formulas), CTR-025 (evidence-pack content). Everything else **MISSING** with the
  same producing prompt (M6-P0701..0714) cited identically in ARCH §2, DATA_MODEL §6, EVENT_FLOW §8,
  TEST_STRATEGY §5, SCALE_LEARNING §6, SECURITY §9.
- **TEST_STRATEGY buildable/BLOCKED split** is consistent with the DRAFT_LOCKED/MISSING statuses (smokes on
  MISSING contracts are BLOCKED, not faked).

---

## 4. Critic-finding & verification ledger — all BLOCKER findings addressed/escalated `[REG evidence]`

The acceptance check *"BLOCKER critic findings addressed or escalated"* is satisfied by record:

- **Research critics** `M6-PC0200..0211`: all **PASS**, **fail_gate=false**, **open_blockers=0** (re-verified
  mechanically this prompt). **Zero BLOCKER** entering the design band.
- **Design band** M6-P0300..0307: the ledger routes each design prompt directly to the next with **no
  `M6-PC03xx` critic**; per pack discipline each ran an **independent 2–3-lens verification pass** (contract
  placement, rule-citation fidelity, owner-decision preemption, no-PII, cross-doc where relevant). Outcomes:
  | Prompt | Verification outcome |
  |---|---|
  | P0300 | 1 MAJOR (§9→§19 mislabel) + 1 MINOR — **fixed** |
  | P0301 | 1 MINOR (adjustment-record shape) — **fixed** |
  | P0302 | 1 MINOR (RULE-005/007 over-cite) — **fixed** |
  | P0303 | 3 MINOR (verbatim word, citation scope, RULE-021 label) — **fixed** |
  | P0304 | 1 MINOR + 1 informational — **fixed** |
  | P0305 | 2 MINOR (SPEC-core vs [PACK], RULE-009 scope) — **fixed** |
  | P0306 | 6 MINOR (verbatim proposed rows, buildable/BLOCKED split) — **fixed** |
  | P0307 | 0 findings (both lenses CLEAN) |
- **No BLOCKER or MAJOR-unresolved finding survives.** Every finding was MINOR (one MAJOR at P0300, fixed);
  all folded into the deliverables and recorded in each prompt's evidence. **Nothing outstanding to escalate as
  a blocker.**

---

## 5. Consolidated open owner decisions (surfaced, none resolved) `[REG DECISION_REGISTER]`

| Decision | Status | Gated design(s) |
|---|---|---|
| M6-OD-001 (Hero SKU lock) | OPEN | SCALE_LEARNING (Landing/CTA seed), pilot |
| M6-OD-002 (CPA/ROAS/AOV/verified-rate thresholds) | OPEN | DASHBOARD (alerts), SCALE_LEARNING (Funnel/Dashboard conditions) |
| M6-OD-003 (hash policy / allowed fields) | OPEN | EVENT_FLOW, SECURITY (CAPI payload) |
| M6-OD-004 (Meta/Google connector first) | OPEN | EVENT_FLOW (platform target) |
| M6-OD-005 (primary attribution model) | OPEN | ATTRIBUTION §5, DASHBOARD, SCALE_LEARNING (scale ROAS) |
| M6-OD-006 (learning safe range) | OPEN | SCALE_LEARNING (auto-publish BLOCKED) |
| M6-OD-007 (persona/keyword/hook content fill) | OPEN | SCALE_LEARNING (framework only) |
| M6-OD-008 (PAYMENT_COMPLETED as revenue?) | OPEN | DATA_MODEL, ATTRIBUTION, DASHBOARD (non-revenue default) |
| M6-OD-009 (GOLDEN_HOUR_START/REMINDER event config) | OPEN | not design-band-gating; M6.2I event set (default disabled) |
| M6-OD-010 (slice execution model sequential vs parallel) | OPEN | not design-band-gating; prompt DAG (sequential default) |
| M6-OD-011 (target repo/stack) | OPEN | ALL — staging = `04-artifacts/impl/`, stdlib-only |
| M6-OD-012 (evidence masking format) | OPEN (pack-recommended `abc***xy`) | SECURITY §4 |
| M6-ENTRY-001..004 | OPEN | ARCH/EVENT_FLOW (Source inputs), Scale Gate |

The design set makes each **decidable** (it briefs what the owner must fix) and **resolves none**.

## 6. Carried-forward non-blocking gaps (for owner/registry — not blockers) `[PACK]`

1. **Negative-test coverage gap** — 4/7 cross-module boundaries (M4/M5/M7/M8) are RULE-covered but lack a
   dedicated P0 boundary smoke (`[[RESEARCH_CROSS_MODULE_CONTRACTS]]` §2.1); proposed smokes are owner-review.
2. **SCHEMA_CHANGELOG gap** — no dedicated changelog row for hardening rules H01/H02/H03 (flagged M6-P0112).
3. **Behavior / Negative-Keyword scoring** not in the doc's 5-dim Learn list — `[EXT]` candidate, owner-review
   (`[[RESEARCH_STRATEGY_LIBRARIES]]`).
4. **Proposed smokes M6-SMK-016/017/018** remain HARDENING pending owner ratification.
5. **Status-transition audit record shape** — a `[PACK]` proposal (not doc-locked, distinct from the immutable
   adjustment record which is aligned) expressed as a distinct 5-field `{actor, from→to, reason, evidence_ref,
   ts}` in SCALE_LEARNING §2.1 but via an "adds" phrasing in DATA_MODEL §4; reconcile to one canonical shape
   when the audit/request/candidate schemas finalize (CTR-013/014 → M6-P0709/0710). Non-blocking; neither
   relaxes immutability.

None blocks the design band; all are recorded for the owner/registry, none silently resolved (00-spec is
read-only to this role).

## 7. Design summary for the judge `[PACK]`

- **Coverage**: the eight deliverables map 1:1 to the doc's operating surface — §5 architecture, §10/§11 data
  model, §7/§12/§19 event pipeline, §11 attribution, §14/§15 dashboard+DQ, §16/§17 scale+learning, §21/§22
  test+security. Nothing in the doc's Module-6 scope is unaddressed.
- **Fail-closed spine intact**: registry-gate, consent (2 checkpoints), verified-only revenue, outbox-not-
  direct, dedup, no-executable-scale, guarded-learning-orthogonal-to-scale, data-mart-read-only, no-raw-PII,
  staged-BLOCKED/OFF, untrusted-input — all present and mutually consistent (§2).
- **Boundary preserved**: no design prices/orders/confirms-payment (M3), writes advisory (M4), processes raw
  webhook / public-replies (M5), uses live-signal-as-revenue (M7), changes order-state (M8), sends CRM, or
  computes commission (Finance).
- **Buildability**: what is DRAFT_LOCKED (CTR-001/002/015/025) is buildable; everything MISSING is routed to a
  named CONTRACT_HARMONIZATION prompt (M6-P0700..0714) — the design set is the **input** to that band.
- **Owner decisions**: all **12** ODs (M6-OD-001..012) + entry evidence remain OPEN; each is briefed to
  decidability, none resolved. OD-009/010 do not gate the design band (event config / slice ordering) but are
  listed for a complete inventory. The implement legs the ODs gate stay BLOCKED until the owner decides
  (fail-closed).
- **Verification**: 0 outstanding BLOCKER findings (§4); the one MAJOR (P0300) was fixed; all else MINOR and
  folded.

**Recommended judge focus** `[PACK]`: (a) confirm no owner decision was pre-empted anywhere; (b) confirm the
orthogonality seam (learning safe-range ≠ scale) and the no-executable-scale invariant; (c) confirm the
seven-vs-eight count note and the carried-forward gaps (§6) are acceptable as non-blocking.

## 8. Verification pass (consolidation cross-check) `[PACK]`

This consolidation feeds JUDGE M6-P0309, so an **independent cross-document contradiction hunt** was run over
the eight deliverables: (A) spine-invariant consistency (no invariant stated inconsistently/contradicted); (B)
contract-inventory + owner-decision consistency (26 CTR consistent; no OD resolved in one doc yet OPEN in
another). Findings folded above. The mechanical finding-ledger (§4) was re-scanned this prompt: all research
critics + design prompts PASS/0-blocker.

## 9. Boundary & safety guards `[BRIEF / REG §18]`

- **Plan-only consolidation**: reads and summarizes; writes no code, resolves no decision, flips no flag.
- **No raw PII/secrets** — references field names only, masked/`secret_ref` `[REG RULE-014 / H02]`.
- **No self-certify** — this summary is evidence; the **judge** (M6-P0309) renders the verdict `[REG RULE-015]`.
- **Staged**: `global_gateway_state=BLOCKED`, `production_flag=OFF` — unchanged.

## 10. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| The eight design deliverables and their doc-section coverage | `[DOC §5/§7/§10–22]` via each prompt — owner-mandated scope |
| Spine invariants (revenue/consent/immutability/no-scale/learning/data-mart/PII/registry/dedup) | `[REG RULES_LOCKED]` — owner-mandated |
| Contract inventory (26 CTR, DRAFT_LOCKED vs MISSING) | `[REG CONTRACT_REGISTER]` — owner-mandated |
| Open owner decisions (OD-001..012 + entry evidence) | `[REG DECISION_REGISTER]` — owner-mandated (statuses) |
| Cross-check matrix; finding-ledger framing; judge-focus recommendation; carried-forward gaps | `[PACK]` / `[EXT]` — owner/judge-review, NOT owner requirements |

*This consolidation is plan-only: it cross-checks and summarizes the design band for the judge, resolves no
owner decision, marks its own count discrepancy and non-blocking gaps openly, and flips no flag;
`global_gateway_state=BLOCKED`, `production_flag=OFF`.*
