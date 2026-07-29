# BOUNDARY CRITIQUE — RESEARCH_EVENT_REGISTRY_INTEGRATION.md

**Critic prompt**: M6-PC0201 (RESEARCH_EVENT_REGISTRY_INTEGRATION_CRITIC) · **Role**: BOUNDARY_ADVERSARY · **Mode**: analysis_only
**Target**: `04-artifacts/analysis/research/RESEARCH_EVENT_REGISTRY_INTEGRATION.md` (produced by M6-P0201)
**Author does not respond here.** Findings feed Phase-0 design and the producing prompt M6-P0701 (CONTRACT_EVENT_REGISTRY).

> `global_gateway_state` stays **BLOCKED**, `production_flag` stays **OFF**. Nothing here flips a gate or a flag. Self-report; the runner gate decides PASS.

---

## 1. Entry gate (verified before review)

| Check | Result | Evidence |
|---|---|---|
| M6-PC0201 is RUNNING in the ledger | ✅ | `PROMPT_EXECUTION_LEDGER_LOCKED.csv` row 31 — `M6-PC0201 … BOUNDARY_ADVERSARY … RUNNING` |
| Dependency M6-P0201 is complete | ✅ | ledger row 30 — `M6-P0201 … PASS`; evidence `M6-P0201.json` status=PASS |
| Required inputs present | ✅ | brief, `RESEARCH_EVENT_REGISTRY_INTEGRATION.md`, `M6-P0201.json` all read |

Entry gate holds; review proceeded.

## 2. Method

Direct citation verification (every `[DOC]`/`[REG]` anchor re-opened against the extract and registers) plus an adversarial **find → refute-verify** pass: 5 finder lenses (citation-fidelity, boundary-overreach, owner-decisions, fail-closed-caching, executability) surfaced candidates; each was handed to a separate verifier told to **try hard to refute it** and grade severity. 11 candidates verified; only survivors are reported. Six dismissed candidates are listed in §5.

Severity rubric: **BLOCKER** = research unusable / unconditional hard-boundary breach / M6 writes-or-invents the registry / resolves an owner decision; **MAJOR** = would cause boundary overreach, a dropped owner dependency, or a fail-closed-unsafe design *if followed*, but mitigated elsewhere; **MINOR** = citation precision / completeness / low-impact slip.

## 3. Overall verdict

**No BLOCKER.** This is a high-quality, boundary-careful artifact. **All six DOC anchors are faithful and correctly section-tagged** — verified directly:

| Anchor | Verified against extract | Status |
|---|---|---|
| `[DOC §13 L263]` event_registry fields owner/channel/data_sensitivity/external_send_policy | extract L263 (under `## 13`) — exact | ✅ |
| `[DOC §12 L257]` `send_policy = consent_valid AND event_in_registry AND data_quality_pass AND not_duplicate` | extract L257 (under `## 12`) — exact | ✅ |
| `[DOC §7 L116]` registry gate, unknown → reject/hold + audit | extract L116 (under `## 7`) — exact | ✅ |
| `[DOC §26 L490]` registry checked before every tracking hook | extract L490 (under `## 26`) — exact | ✅ |
| `[REG FAIL-003]` Event drift (invent code outside registry) | FAIL_GATE_REGISTER L15 — exact | ✅ |
| `[REG M6-ENTRY-003]` Core registry exists w/ those fields (OPEN) | ENTRY_EVIDENCE_REGISTER L18 — exact | ✅ |

Boundary handling is explicit and clean (read-only; never writes/invents the registry; CONSUMED shape deferred to Core via M6-P0701; PII masked; external send not enabled). Owner-decision dependencies are recorded in §5. The confirmed defects are **1 MAJOR + 1 MINOR**.

| ID | Severity | Category | One-line |
|---|---|---|---|
| F1 | **MAJOR** | fail-closed-correctness | `event_in_registry` validated once at the tracking hook; no send-time re-check → async-outbox false-ALLOW window for a de-registered code |
| F2 | MINOR | unsupported-claim | `channel` value-set `(web/landing/…/diamond)` tagged `[REG]` but enumerated in no locked register |

---

## 4. Confirmed findings

### F1 — MAJOR — No send-time re-validation of `event_in_registry` (async-outbox false-ALLOW window)
**Category**: fail-closed-correctness · **Verdict**: CONFIRMED MAJOR (verifier upheld after conceding a competent worker *might* re-check)

**Exact claim (research):**
- §2 step 2 (L56–57): "**FOUND & active** → attach `{owner, channel, data_sensitivity, external_send_policy}`; **continue to the send-policy chain** `[DOC L257]`: `consent_valid AND event_in_registry AND data_quality_pass AND not_duplicate`." — the whole flow is scoped "at the tracking hook" (L53).
- §3 versioned snapshots (L86–87): "validate against a pinned `registry_version` and **record which version validated each event**."
- §2 L58 scopes out only consent/dedup/DQ ("This research covers only `event_in_registry`"), i.e. `event_in_registry` is treated as **settled at the hook**.

**Evidence:** `RULES_LOCKED` L13 (**RULE-004**): external measurement/audience sync "go through outbox + worker … **never directly from a runtime request**" — so send is asynchronous, creating a **hook → enqueue → drain** time gap. `[DOC §12 L257]`: `event_in_registry` is a **send-time** AND-term (it lives in the §12 Pixel/CAPI/Offline **send** section). Research L38: `external_send_policy` "gates whether/how the event may leave via outbox".

**Defect:** The research evaluates the send-policy chain **at the hook** and §3 pins a **single** hook-time validation (recording the version used), but nowhere requires `event_in_registry` (or the full L257 chain) to be **re-evaluated against the live registry at outbox drain**. If Core de-registers/disables a code during the gap, a worker draining on the pinned hook-time decision **false-ALLOWs an external send** of a now-invalid code — the exact removal false-ALLOW §3's own invariant forbids. Critically, **§3's removal remedies are all cache-lookup-time** (fast invalidation refreshes the *next* lookup); they do nothing for an outbox item whose decision was already pinned at hook time. Only §3's abstract "never false-ALLOW removals" invariant catches it — the prescribed *mechanisms* do not.

**Why MAJOR not BLOCKER:** the research *states* the never-false-ALLOW-removals invariant (§3), so it does not unconditionally breach — a careful architect would catch the tension. Why **not MINOR**: the consequence is an **external send of a de-registered event on the outbox/Pixel/CAPI path** (RULE-004 / RULE-002 / FAIL-003 territory), the most sensitive action, not a completeness slip.

**Fix:** state explicitly that `event_in_registry` (and the full L257 send_policy chain) must be **re-evaluated against the current registry snapshot at outbox-send time**; the tracking hook only gates *eligibility-to-enqueue*, and the pinned `registry_version` is **audit metadata, not send authorization**. This belongs jointly to this research and to `M6-P0203` (RESEARCH_OUTBOX_WORKER_PATTERNS) — flag the hand-off so the send-time gate is not lost between the two.

---

### F2 — MINOR — `channel` value-set tagged `[REG]` with no locked-register anchor
**Category**: unsupported-claim · **Verdict**: CONFIRMED MINOR (two independent verifiers, both MINOR)

**Exact claim (research §1 L36):** "| `channel` | `[DOC L263]` | attribution routing **(web/landing/live/comment/messenger/CRM/diamond)** `[REG]` |"

**Evidence:** the file's own sourcing legend (L14) defines `[REG]` = "locked pack register". **No locked register enumerates that value list as event_registry channel codes**: the closest, `ENTRY_EVIDENCE_REGISTER` L17 (M6-ENTRY-002), lists only "page, live, comment, messenger" — it omits web/landing/CRM/diamond, and the research in turn omits page. The **only** locked channel enum is the *disjoint*, M6-owned `M6-CTR-002 entry_channel` (`FACEBOOK_AD | LIVE_ORGANIC | DIAMOND_LINK | CRM | DIRECT`, extract L229). Unlike its sibling rows (L34/37/38, anchored to RULE-001 / M6-OD-003 / RULE-004), line 36's `[REG]` has **no resolvable register anchor**; and `channel` is a **Core-owned field of the CONSUMED `M6-CTR-003`**, so its value-domain is Core's to define.

**Why MINOR:** the boundary-overreach reading is refuted — M6 never validates against this list (it reads `channel` from Core), and the surrounding text keeps `channel` firmly Core-owned (L42–43, L100–101). What survives is a **citation-label slip**: an illustrative M6-side list wears register authority it does not have. Low-impact, but a coder feeding M6-P0701 could carry the invented value-set forward as "register-backed truth about Core's schema", or wire M6.2A attribution through the registry `channel` instead of `M6-CTR-002 entry_channel`.

**Fix:** retag the parenthetical as `[EXT]`/illustrative (or anchor to a real register), and mark the channel value-domain as **Core-owned, to be reconciled in M6-P0701**; keep it distinct from the M6-owned `M6-CTR-002 entry_channel` enum.

---

## 5. Attacked and dismissed (did not survive adversarial verification)

Listed so the designer does not re-chase them.

1. **§5 owner-decision list omits M6-OD-009 (GOLDEN_HOUR / disabled-by-default codes).** DISMISSED — OD-009 governs event **emission/enablement** (which codes are disabled-by-default, who owns the config), blast radius **M6.2I**, a different band from this pre-M6.2A read/validate contract. The research's disabled-code handling is **generic and outcome-invariant** (fail-closed either way) and the `enabled`/`status` field is explicitly deferred to Core via M6-P0701, so no OD-009 value is resolved or assumed. (Same conclusion the PC0200 review reached on OD-009.)
2. **Cache TTL fallback is not fail-closed for removals.** DISMISSED — §3 is explicitly `[EXT]` owner-review proposal; the actual detection layer is §2 step 3 ("NOT FOUND, or FOUND-but-disabled → fail-closed"), independent of the cache; and §5 records the change-feed as an **OPEN integration dependency that BLOCKS the affected leg**. (Note: this is a *different* mechanism from the confirmed F1 — F1 is the async-outbox gap, not cache staleness.)
3. **Proposing `status`/`enabled`/`registry_version` read fields dictates Core's CONSUMED schema.** DISMISSED — the research frames them as read-set *requests* deferred to Core via M6-P0701, "never an M6 addition to the registry" (L42–43, L100–101, L130); reading a field ≠ owning the schema.
4. **`record which version validated each event` bolts `registry_version` onto M6-owned `web_event_logs` (CTR-004) without routing through M6-P0703.** DISMISSED — "aligns with RULE-007" is a design-*principle* citation (append-only/immutability), not a schema-modification instruction; the field's stated home is the §2 audit record, not `web_event_logs`; and M6-P0701 does not define `web_event_logs`.
5. **§2's "FOUND-but-disabled" branch is unimplementable / contradicts §1 and §3.** DISMISSED — §1 explicitly tags `status`/`enabled` as an unconfirmed `[EXT]` proposal and cross-links §2/§3; §2 **unions** FOUND-but-disabled with NOT-FOUND (same fail-closed outcome); §3's absence=reject fallback covers the no-status-field case. (Cosmetic slip only: §2 step 2 is L56, not L57.)

## 6. Acceptance-check trace

- [x] Every finding cites the exact claim and its evidence (research section/line + source file line/row).
- [x] Verdict per finding: BLOCKER/MAJOR/MINOR — 0 BLOCKER, 1 MAJOR (F1), 1 MINOR (F2).
- [x] No raw secret or unmasked PII (only register/extract/research text quoted; no channel-origin data present).
- [x] Nothing self-certified PASS; `04-artifacts/state/` untouched; gateway BLOCKED / production OFF unchanged.
