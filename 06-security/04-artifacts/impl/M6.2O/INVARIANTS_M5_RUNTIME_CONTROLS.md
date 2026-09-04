# INVARIANT — M5 runtime controls before real public egress (C7)

**Kind**: governance invariant (documentation; **no code**). **Source**: M5 `DAP-M5-cho-M6.md` (M5-confirmed:
3/4 controls un-gate + 1 ready — nothing new to build; M6's part is to **record the invariant**). **Governance
placement (flag)**: the canonical home of this invariant is the **Scale-Gate / go-live checklist** +
`_OWNER_RISK_ACCEPTANCE.md` (mapping `ENTRY-004 DEBT-1..4`), which are **owner/analyst/judge-owned** artifacts
outside the coder write scope — the ANALYST/PM should merge this record into them. This file is the coder-side
durable capture so the invariant is not lost.

## The invariant (HARD condition, fail-closed)

> **Do NOT enable `external_send` / a real Graph sink until ALL FOUR M5 runtime controls below are closed AND the
> owner signs.** Real public egress (posting a comment/CAPI to a live platform) is gated on these; none may be
> skipped.

## M6 side — already enforced fail-closed (M6-verified @ `04-artifacts/impl/M6.2O/`)

M6 already refuses real egress structurally, so this invariant holds by construction in the staged build:

- `config.EXTERNAL_SEND` is an immutable `Final = "OFF"` (`app/config.py:13`); the `EXTERNAL_SEND == "ON"` helper
  (`config.py:79`) returns **False**.
- every send attempt raises **`ExternalSendBlocked`** — `outbox/transport.py:19,39` (`StagedBlockedTransport`) and
  `integration/platform_transport.py:55` — so the outbox is drained but **no real platform call** occurs (the item
  is HELD, not sent, `transport.py:91-95`).
- `registry/validator.permits_external_send(policy)` (`validator.py:66`) is the per-event send-policy gate; with the
  posture OFF nothing is permitted.
- `global_gateway_state=BLOCKED`, `production_flag=OFF` are immutable. **Nothing in M6 flips these.**

This matches the operator's statement (`EXTERNAL_SEND=OFF` immutable · `ExternalSendBlocked` · `permits_external_send()=False`).

## The four M5 runtime controls (status as **M5-reported**, per `DAP-M5-cho-M6.md` — not M6-verified)

| # | Control | M5-reported status | Owner / debt |
|---|---|---|---|
| 1 | allowlist template | ✅ present (`public-safe-templates.ts` + `spotlight-render.guard`) | M5 — done |
| 2 | dedup cross-instance | ⚠️ default in-memory; cross-instance only when `IDEMPOTENCY_STORE=prisma/redis` | M5 — **B5** |
| 3 | send-rate | ✅ present (Redis rate limiter + 429 backoff), pending Redis infra | M5 — Redis infra |
| 4 | real Graph sink | ✅ present (`graph-post-comment-sink` + `http-graph-client`), pending go-live | M5 — **B11** |

> The rows 1/3/4 status is **cross-module DATA reported by M5** (transcribed by the operator); M6 does not and cannot
> verify M5's source tree. M6 records it verbatim for the checklist; the M5 team owns its accuracy.

## Ownership of the 4 debts (owner/chief action, NOT M6)

M5 asks the chief to move the 4 debts into **FIX_M5**: allowlist = done · dedup = **B5** · rate = **Redis** ·
sink = **B11**. This is an **owner/chief action** — not a Module-6 build item.

## M6's action items for this invariant (what THIS record commits M6 to)

1. **Keep the invariant in the Scale-Gate / go-live checklist**, mapped to `ENTRY-004 DEBT-1..4` and
   `_OWNER_RISK_ACCEPTANCE.md` — ANALYST/PM to merge (this file is the coder-side capture).
2. **Re-gate M6.2G + an adversarial pass on the build's P4** before any real posting.
3. **Never enable `external_send`** until the four controls are closed **and the owner has signed**. (M6 has no code
   path that flips `external_send`; this is a governance commitment layered on the structural fail-closed above.)

*This is documentation only: no application code, no migration, no flag change. `global_gateway_state=BLOCKED`,
`production_flag=OFF`, `external_send=OFF` remain immutable and unflipped.*
