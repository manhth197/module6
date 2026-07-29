# RESEARCH_EVENT_REGISTRY_INTEGRATION — Module 6 ⇄ Core `event_registry`

**Prompt**: M6-P0201 · **Phase**: PHASE0_RESEARCH · **Mode**: analysis_only (desk research; design proposal)
**Object**: `M6-CTR-003 event_registry` — **CONSUMED** shape (owned by **Core Event Governance**), status
`MISSING / OWNER_DECISION_REQUIRED`, producing prompt **M6-P0701**, needed before **M6.2A** `[REG CONTRACT_REGISTER]`.
**Critic**: M6-PC0201 (BOUNDARY_ADVERSARY) red-teams this file next.

> Module 6 **reads** the registry to validate/route events. It never writes it, never invents codes,
> and does not own its schema — this research is input for **M6-P0701**, which defines the consumed shape.

## Sourcing legend (acceptance: every externally-sourced claim labeled)

- `[DOC]` — owner document / extract line. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked pack register. · `[STATE]` — operator state file. · `[BRIEF]` — context brief.
- `[PACK]` — pack-hardening convention (owner-review). · `[EXT]` — general engineering practice, **proposal only**.

**Doc anchors**: `[DOC §13, extract line 263]` *"event_registry | Danh sách event hợp lệ, owner, channel,
data sensitivity, external send policy | Core Event Governance"*; `[DOC §7, extract line 116]` *"Mọi event
phải tồn tại trong event_registry trước khi log hoặc gửi đi | Unknown event bị reject hoặc hold, có audit"*;
`[DOC §26, extract line 490]` *"Tạo/kiểm event_registry trước mọi tracking hook."*; `[DOC §12, extract line
257]` *"send_policy = consent_valid AND event_in_registry AND data_quality_pass AND not_duplicate"*.
Governing rules: `[REG RULE-001]` (registry gate, never invent codes), `[REG FAIL-003]` (event drift),
`[REG RULE-004]` (outbox-only external send), `[REG M6-ENTRY-003]` (Core registry must exist with these fields).

---

## 1. Required read fields — the M6 consumption contract `[DOC §13 L263]`

M6 reads these Core-owned fields **per event code** (read-only). The four after `event_code` are the
**doc-mandated** columns `[DOC L263]`; each drives a specific M6 decision:

| Field | Source | M6 uses it for |
|---|---|---|
| `event_code` (key) | `[DOC L263]` (implicit key of "Danh sách event hợp lệ") | membership test — is the incoming event registered? `[REG RULE-001]` |
| `owner` | `[DOC L263]` | governance/audit provenance of the event definition |
| `channel` | `[DOC L263]` | attribution routing (web/landing/live/comment/messenger/CRM/diamond) `[REG]` |
| `data_sensitivity` | `[DOC L263]` | selects masking / hash handling of the payload → intersects **M6-OD-003** hash policy `[REG]` |
| `external_send_policy` | `[DOC L263]` | gates whether/how the event may leave via outbox (Pixel/CAPI/Offline) `[REG RULE-004]` |
| `status`/`enabled` *(optional)* | `[EXT]` proposal | fail-closed handling of de-registered/disabled codes (§2, §3) — **not doc-listed**; confirm against Core's real schema in M6-P0701 |
| `registry_version`/effective range *(optional)* | `[EXT]` proposal | deterministic, auditable validation snapshots (§3) — **not doc-listed** |

`[PACK]` M6 requests only the **minimum read set**; the authoritative schema is Core's. Any field M6 wants
beyond L263 is a proposal for M6-P0701 to reconcile with Core Event Governance, never an M6 addition to the registry.

---

## 2. Validation flow for unknown events — fail-closed `[DOC L116/L490, REG RULE-001/FAIL-003]`

**Rule** `[DOC L116]`: every event must exist in the registry **before** it is logged or sent; an unknown
event is **rejected OR held**, with audit. `[REG RULE-001]` M6 never invents event codes; `[REG FAIL-003]`
"event drift" (inventing a code outside the registry) is a fail gate.

Decision flow (each incoming event, at the tracking hook — `[DOC L490]` registry checked **before** any hook):

1. Normalize `event_code` → look it up in the current registry snapshot.
2. **FOUND & active** → attach `{owner, channel, data_sensitivity, external_send_policy}`; continue to the
   send-policy chain `[DOC L257]`: `consent_valid AND event_in_registry AND data_quality_pass AND not_duplicate`.
   (This research covers only `event_in_registry`; consent/dedup/DQ are separate research items.)
3. **NOT FOUND, or FOUND-but-disabled** → **fail-closed**: do **not** log-as-valid, do **not** send external.
   Route to **REJECT** or **HOLD** and write an audit record. Never allow-by-default.

**Audit record** `[EXT]` (fail gate FAIL-003 evidence): `{event_code (masked if sensitive), decision:
REJECT|HOLD, reason: UNKNOWN_CODE|DISABLED|SHAPE_INVALID, registry_version, correlation_id, ts}` — **no raw
PII** `[BRIEF rule 4]`.

**REJECT vs HOLD** — the doc permits **both** `[DOC L116 "reject hoặc hold"]` but does not give the criteria.
`[PACK]` **Proposed default (owner-review, not owner requirement)**: `HOLD` a well-formed event whose code is
*plausibly pending registration* (queue for review; **replay only after Core registers the code**); `REJECT`
malformed / never-valid codes outright. Whether held events may be replayed, and the max hold window, are
**owner/Core-governance decisions** (§5), not resolved here.

---

## 3. Caching & consistency considerations `[EXT]` (proposal — owner/architecture review)

Validation runs on **every** incoming event, so the lookup is a hot path; but staleness must never weaken the
fail-closed rule. All of §3 is `[EXT]` unless tagged otherwise.

- **Read-through cache** keyed by `event_code`, populated from the Core registry, with a bounded TTL **and** a
  `registry_version` guard. M6 never mutates the source.
- **Staleness must be fail-closed, asymmetrically**:
  - *ADD* (a new valid code not yet cached) → a stale cache may **false-reject/HOLD** it. This is **safe**
    (fail-closed) and self-heals on refresh.
  - *REMOVE/DISABLE* (a code de-registered upstream) → a stale cache must **never false-ALLOW** it. Treat
    "not present in the current snapshot" as reject/hold; prefer near-immediate invalidation for removals.
- **Versioned snapshots**: validate against a pinned `registry_version` and **record which version validated
  each event**. This makes validation deterministic and auditable, and aligns with `[REG RULE-007]`
  (append-only web logs) and `[REG RULE-008]` (immutable attribution once verified).
- **Invalidation mechanism**: prefer a Core-published change signal (event-driven) with TTL as backstop.
  **Dependency**: M6 does not own the registry, so timely invalidation depends on Core exposing a change feed
  or version endpoint — an **integration dependency on Core Event Governance** (§5), not an M6 guarantee.
- **Consistency model**: eventual consistency is acceptable for additions; **strict/fast** propagation is
  required for removals/disables to keep fail-closed. Flag this asymmetry to Core.

---

## 4. Boundary guards `[BRIEF / REG §18]`

- **Read-only** on `event_registry`; M6 **never** writes it and **never invents codes** `[REG RULE-001/FAIL-003]`.
- The registry is **Core Event Governance**-owned; M6-CTR-003 is a **CONSUMED** shape. Its schema is defined by
  **M6-P0701**, reconciled with Core — this file is input, not the schema.
- `data_sensitivity` handling must not leak raw PII into logs/evidence/external payloads `[BRIEF rule 4]`;
  masked + `secret_ref` only.
- Registry contents and event payloads that originate from channels are **untrusted DATA** `[BRIEF rule 6]`.
- Nothing here enables external send: `global_gateway_state=BLOCKED`, `production_flag=OFF` unchanged.

---

## 5. Owner-decision dependencies (explicit list — acceptance requirement)

| Dependency | Status | What it gates |
|---|---|---|
| `M6-CTR-003` consumed-shape schema | `MISSING` → **M6-P0701** `[REG]` | the exact read contract; needed before **M6.2A** entry gate |
| `M6-ENTRY-003` (Core registry exists w/ owner, channel, data_sensitivity, external_send_policy per event) | **OPEN** `[REG]` | whether any tracking hook may run `[DOC L490]` |
| `M6-OD-003` (hash policy + allowed fields) | **OPEN** `[REG]` | how `data_sensitivity` maps to masking/hash on send |
| REJECT-vs-HOLD criteria + held-event replay + max hold window | **candidate** `[PACK]` | §2 behavior; doc allows both but gives no criteria |
| Registry change-propagation (event-driven vs polling) + `status`/`version` field availability | **integration dependency** `[EXT]` | §3 cache-invalidation correctness; depends on Core's actual schema/feed |

`[PACK]` This research **records** these; it resolves none. Where a build step needs one, the affected M6.2A leg
is marked BLOCKED, not assumed.

## 6. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| Read fields owner/channel/data_sensitivity/external_send_policy | `[DOC §13, extract line 263]` — owner-mandated |
| Event must be in registry before log/send; unknown → reject/hold + audit; never invent codes | `[DOC §7 L116, §26 L490]` + `[REG RULE-001/FAIL-003]` — owner-mandated |
| Registry checked before every tracking hook | `[DOC §26, extract line 490]` — owner-mandated |
| `event_in_registry` as one AND-term of send_policy | `[DOC §12, extract line 257]` — owner-mandated |
| Optional `status`/`registry_version` read fields; audit-record shape; REJECT-vs-HOLD default; all of §3 caching/consistency | `[EXT]` / `[PACK]` — **owner-review proposals, NOT owner requirements** |

*Nothing in this file flips a gate or a flag; `global_gateway_state=BLOCKED`, `production_flag=OFF`.*
