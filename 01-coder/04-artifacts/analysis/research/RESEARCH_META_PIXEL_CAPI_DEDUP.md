# RESEARCH_META_PIXEL_CAPI_DEDUP — locked dedup/idempotency keys ⇄ Meta dedup; OD-003/OD-004 decidability

**Prompt**: M6-P0204 · **Phase**: PHASE0_RESEARCH · **Mode**: analysis_only (desk research; design proposal)
**Anchors**: locked `dedup_key` / `idempotency_key` `[DOC §12, extract lines 254–255]`; `M6-CTR-008
marketing_measurement_outbox` (→M6-P0705); owner decisions **M6-OD-003** (hash policy) and **M6-OD-004**
(connector order) `[REG DECISION_REGISTER]`.
**Critic**: M6-PC0204 (BOUNDARY_ADVERSARY) red-teams this file next.

> **Staged, not live.** `global_gateway_state=BLOCKED`, `production_flag=OFF` ⇒ **no real Meta call** is made
> in this pack. This research maps the locked keys to Meta's dedup and makes OD-003/OD-004 *decidable*; it does
> not send anything, does not pick the hash policy or the connector.

## Sourcing legend (acceptance: every externally-sourced claim / platform fact labeled)

- `[DOC]` — owner document / extract line. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked pack register. · `[BRIEF]` — context brief. · `[PACK]` — pack convention (owner-review).
- `[PLATFORM]` — **external Meta platform fact from general knowledge; MUST be verified against the current
  Meta Marketing / Conversions API documentation before implementation.** Not an owner requirement; not
  authoritative here — flagged for coder verification.
- `[EXT]` — general engineering practice, proposal only.

**Doc anchors**: `[DOC §12 L254]` `dedup_key = platform + event_code + customer_or_guest_key + event_ts_bucket
+ source_event_id`; `[DOC §12 L255]` `idempotency_key = event_code + page_id + session_id + raw_event_hash +
normalized_ts`; `[DOC §12 L248]` Pixel *"public-safe … không gửi PII thô"*; `[DOC §12 L249]` CAPI *"có hash
policy và dedup key"*. Rules: `[REG RULE-005]` (dedup mandatory), `[REG RULE-014]` (no raw PII external),
`[REG FAIL-001]` (revenue misuse via double count), `[REG FAIL-008]` (raw PII exposure).

---

## 1. The two locked keys are **internal** to M6 `[DOC L254-255]`

- `dedup_key` `[DOC L254]` — M6's **internal** guard against duplicate outbox rows across
  Pixel/CAPI/Offline for one logical event (RULE-005). Includes `source_event_id`.
- `idempotency_key` `[DOC L255]` — M6's **internal** replay guard on the outbox/dispatch (per M6-P0203 §4).

Neither is, by itself, Meta's dedup key. Meta dedups by its **own** field (`event_id`). So the design question
is a **mapping**, not a reuse (§2, §4).

---

## 2. Meta Pixel ↔ CAPI deduplication mechanics `[PLATFORM]`

`[PLATFORM — verify vs current Meta CAPI docs]`:
- Meta deduplicates a **redundant browser-Pixel event and server-CAPI event** for the same user action by
  matching a shared **`event_id`** together with the **`event_name`**. When Meta receives two events with the
  **same `event_id` + `event_name`** within its dedup window, it keeps one.
- The dedup window is time-bounded `[PLATFORM — verify exact window; commonly cited ~48h for the later event]`.
- For this to work, the **identical `event_id`** must be set on **both** the browser Pixel `fbq('track', …,
  {eventID})` call and the CAPI server event payload; and the `event_name` must match `[PLATFORM]`.
- Meta also uses browser identifiers `fbp` / `fbc` (cookies) and, where present, hashed customer-info
  parameters, as matching signals — distinct from the redundant-event dedup above `[PLATFORM — verify]`.

**Correctness consequence** (load-bearing): if the Pixel and CAPI sends of the same event carry **different**
`event_id`s, Meta will **not** dedup → the conversion is **double counted** → this would violate `[REG
RULE-005]` and, for revenue events, risk `[REG FAIL-001]`. Therefore the shared-`event_id` derivation is the
single most important integration invariant.

---

## 3. Hashing requirements `[PLATFORM]` (the concrete form of RULE-014 for Meta)

`[PLATFORM — verify vs current Meta CAPI docs]`:
- CAPI **customer-information parameters** (e.g. `em` email, `ph` phone, `fn`, `ln`, `ct`, `zp`, …) must be
  **normalized then SHA-256 hashed** before sending (normalization typically = trim + lowercase, digits-only
  for phone, etc.). Raw values are **never** sent.
- Some parameters are **not** hashed by convention (e.g. `fbp`, `fbc`, client IP, user-agent, `external_id`
  may be sent hashed or plain) `[PLATFORM — verify each field's requirement]`.
- Browser **Pixel** must stay **public-safe** `[DOC L248]` — no raw PII thô; advanced-matching PII, if used,
  is hashed.

**Boundary lock** `[REG RULE-014 / FAIL-008]`: raw PII (phone/email/address/raw ids) **never** leaves the
system. The only PII that may go to CAPI is the **hashed** form permitted by the owner's hash policy
(**M6-OD-003**). Until that policy exists, **no PII-bearing CAPI field is sendable** (fail-closed).

---

## 4. Mapping the locked keys → Meta parameters `[EXT] proposal`

| M6 (locked / internal) | Meta-facing role | Proposal |
|---|---|---|
| `source_event_id` (part of `dedup_key`, `[DOC L254]`) | candidate for Meta **`event_id`** | derive one **stable, shared** `event_id` per logical event and stamp it on **both** the Pixel and CAPI send `[PLATFORM]` |
| `idempotency_key` `[DOC L255]` | M6 outbox replay guard | keep internal; a crash-retry reuses the **same** `event_id`, so Meta still dedups (ties to M6-P0203 §4) |
| `event_code` | maps to Meta **`event_name`** (standard vs custom) | the code→`event_name` mapping is `[PLATFORM]`/owner naming — must be consistent browser↔server |
| `platform` (part of `dedup_key`) | selects connector | Meta vs Google (**M6-OD-004**) |

`[EXT]` The **exact** field chosen as Meta's `event_id` and the `event_code`→`event_name` map are design
decisions to be fixed in the CTR-008 contract (M6-P0705) and verified against `[PLATFORM]` docs — **not**
invented as owner requirements here.

---

## 5. What **M6-OD-003 (hash policy)** needs from the owner to be decidable

The owner/privacy-legal decision must specify, at minimum `[PACK]` (each item is a question, not a proposed answer):

1. **Which** customer-info fields may be sent to CAPI at all (em / ph / external_id / fn / ln / …), i.e. the
   permitted PII set — a privacy/legal scope decision.
2. **Normalization + hash spec** per field (SHA-256 over normalized value; Meta prescribes the normalization
   `[PLATFORM]`) — confirm it matches the current Meta spec.
3. Which **`data_sensitivity`** levels (read from `event_registry`, per M6-P0201) are **eligible** for external
   send vs must be dropped.
4. Handling of `fbp`/`fbc`/IP/user-agent (pseudonymous matching signals) — send or not, consent-gated.
5. Retention/audit of the hashed values and the mapping (no raw PII stored in M6 logs/evidence — `[REG
   RULE-014]`).

Until 1–3 are answered, CAPI PII fields stay **BLOCKED** (fail-closed); the outbox may still carry non-PII,
event_id-only dedup metadata.

## 6. What **M6-OD-004 (connector order)** needs from the owner to be decidable

`[DOC §25 extract line 481]` frames it as *"Meta trước hay Google song song"*. To be decidable the owner must fix:

1. **Sequence**: Meta-first vs Meta+Google-parallel in pilot.
2. **Connector/API**: which integration path and **API version** per platform `[PLATFORM — verify current
   version]` (direct Marketing/Conversions API vs a connector/CDP).
3. **Credentials/config** as `secret_ref` only: `pixel_id`/dataset_id, CAPI `access_token`, ad-account ids —
   never in code/logs/evidence `[BRIEF, REG RULE-014]`.
4. **Test vs live**: while `production_flag=OFF`, only Meta **Test Events**/sandbox at most, and even that is an
   external call ⇒ stays **staged/off** until the owner enables `[BRIEF]`.

## 7. Boundary & safety guards `[BRIEF / REG §18]`

- **No real external call** while gateway BLOCKED / production OFF — design only.
- **No raw PII to any platform** `[REG RULE-014/FAIL-008]`; only owner-approved hashed fields (M6-OD-003).
- Access tokens / pixel ids / dataset ids handled as `secret_ref`; never printed.
- Meta API responses / echoes are **untrusted DATA** `[BRIEF rule 6]`.
- M6 measures only — no pricing/order/CRM side effects; connector choice does not change the module boundary.

## 8. Owner-decision dependencies (explicit list — acceptance requirement)

| Dependency | Status | What it gates |
|---|---|---|
| **M6-OD-003** (hash policy + allowed fields) | **OPEN** `[REG]` | any PII-bearing CAPI send (§3, §5); **this research enumerates exactly what makes it decidable** |
| **M6-OD-004** (connector order + API/creds) | **OPEN** `[REG]` | which platform/API the dispatcher targets (§6) |
| `M6-CTR-008` (measurement outbox: dedup_key/idempotency_key fields, event_id derivation) | `MISSING` → **M6-P0705** `[REG]` | the internal→Meta key mapping (§4) |
| `event_registry.data_sensitivity` read field | from **M6-P0201** / **M6-ENTRY-003** | which events/fields are send-eligible (§5.3) |
| Current Meta CAPI/Marketing API version facts (all `[PLATFORM]` items) | **verify at implementation** | dedup window, exact hash/normalization per field, `event_id` semantics |

`[PACK]` This research records these; it resolves none. Every `[PLATFORM]` fact is flagged for verification
against current Meta docs before any code is written.

## 9. Doc-traceability (owner-mandated vs platform/proposal)

| Element | Source |
|---|---|
| `dedup_key` / `idempotency_key` formulas (internal) | `[DOC §12 lines 254–255]` — owner-mandated |
| Pixel public-safe / no raw PII thô; CAPI has hash policy + dedup key | `[DOC §12 lines 248–249]` + `[REG RULE-005/014]` — owner-mandated |
| Meta event_id+event_name redundant-event dedup; ~48h window; SHA-256 normalized hashing of CAPI PII; fbp/fbc matching | `[PLATFORM]` — **external, verify vs current Meta docs; NOT owner requirements** |
| internal-key → Meta-parameter mapping; shared-event_id derivation; event_code→event_name map | `[EXT]`/`[PLATFORM]` — proposal, owner/coder to fix in M6-P0705 |
| the specific questions that make M6-OD-003 / M6-OD-004 decidable | `[PACK]` framing of `[REG]` open decisions — not new owner requirements |

*Nothing in this file flips a gate or a flag; `global_gateway_state=BLOCKED`, `production_flag=OFF`.*
