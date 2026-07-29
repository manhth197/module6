# RESEARCH_IDENTITY_CONSENT — Module 6 identity chain + consent (M6-CTR-005 / M6-CTR-006)

**Prompt**: M6-P0202 · **Phase**: PHASE0_RESEARCH · **Mode**: analysis_only (desk research; design proposal)
**Objects**: `M6-CTR-005 guest_contacts` (CONSUMED — **Customer identity** owner) and `M6-CTR-006
guest_marketing_consent_snapshot` (CONSUMED — **Consent** owner). Both `MISSING / OWNER_DECISION_REQUIRED`,
producing prompt **M6-P0702**, needed before **M6.2A** `[REG CONTRACT_REGISTER]`.
**Critic**: M6-PC0202 (BOUNDARY_ADVERSARY) red-teams this file next.

> Module 6 **reads** identity and consent to attribute events and to gate external sends. It never owns,
> creates, reassigns, or overwrites identity or consent, and never sends CRM. Raw `guest_id/customer_id/psid`
> and any PII are handled as references only — masked in every log/evidence `[BRIEF rule 4]`.

## Sourcing legend (acceptance: every externally-sourced claim labeled)

- `[DOC]` — owner document / extract line. **Only `[DOC]` items are owner requirements.**
- `[REG]` — locked pack register. · `[STATE]` — operator state. · `[BRIEF]` — context brief.
- `[PACK]` — pack-hardening convention (owner-review). · `[EXT]` — general engineering practice, **proposal only**.

**Doc anchors**: `[DOC §7 L115]` *"Identity | customers, customer_profiles, customer_addresses,
customer_devices, guest_contacts; map guest -> customer khi có dữ liệu đủ | Guest/customer mapping có audit
và không ghi đè thiếu bằng chứng"*; `[DOC §3 L62]` *"Gắn đúng guest -> customer -> order -> verified revenue
để tránh đo sai, double count…"*; `[DOC §7 L118]` *"Consent | guest_marketing_consent_snapshot bắt buộc;
thiếu consent hợp lệ thì fail-closed | Không external measurement, audience sync, CRM khi consent missing"*;
`[DOC §13 L266]` *"guest_marketing_consent_snapshot | Consent tại thời điểm event | Consent fail-closed"*;
`[DOC §3 L60]` *"consent fail-closed: thiếu consent hợp lệ thì không sync audience, không gửi external
measurement, không gửi CRM"*; `[DOC §12 L257]` *"send_policy = consent_valid AND event_in_registry AND
data_quality_pass AND not_duplicate"*. Governing rules: `[REG RULE-006]` (audited identity chain, never
overwrite without evidence), `[REG RULE-002]` (consent fail-closed at event/send time), `[REG RULE-014]`
(no raw PII external), `[REG FAIL-002]` (consent violation fail gate).

---

## 1. What M6 consumes (read-only) `[DOC §7 L115 / §13 L266]`

| Object | Owner | M6 reads for |
|---|---|---|
| `guest_contacts` (M6-CTR-005) | Customer identity `[REG]` | guest lead identity / contact fingerprint to key un-linked events |
| `customers, customer_profiles, customer_addresses, customer_devices` `[DOC L115]` | Customer identity | the resolved customer side of the guest→customer mapping |
| `guest_marketing_consent_snapshot` (M6-CTR-006) | Consent `[REG]` | the consent state captured at event time; the `consent_snapshot_id` referenced by each event |

`[PACK]` M6 requests the **minimum** read set. Authoritative schemas are Identity/Consent-owned; M6-P0702
reconciles the consumed shapes. M6 attaches `customer_id` / `guest_id` / `consent_snapshot_id` to
`ads_measurement_event` `[REG SPEC §10.1]` **by reference** — never storing raw PII.

---

## 2. guest→customer mapping with audit `[DOC §7 L115, §3 L62 / REG RULE-006]`

**Chain** `[DOC L62]`: `guest -> customer -> order -> verified revenue`. Correct linkage is what prevents
mis-measurement, **double counting**, and scaling on vanity metrics.

**M6's role (read + record, never own)**:
- M6 **consumes** the Identity-owned mapping; it does **not** create or reassign guest↔customer links.
- Every event M6 records carries the identity it was observed under (`guest_id` and/or `customer_id`, by
  reference). When Identity later resolves a guest to a customer, M6 consumes the resolved mapping.
- **Audit + never-overwrite-without-evidence** `[DOC L115, REG RULE-006]`: a mapping M6 has recorded is
  never silently overwritten; a change requires an audited record (actor, reason, evidence, ts). This mirrors
  the attribution-immutability discipline `[REG RULE-008]`.
- `[EXT] proposal`: represent the mapping M6 observes as an **append-only link history** (guest_key →
  customer_id, effective-from, evidence_ref) rather than a mutable pointer, so re-linking is auditable and
  reversible — **owner/architecture review, not a doc requirement**.

**Double-count guard** `[DOC L62]`: revenue/attribution must fold to a single resolved identity so one verified
order is not counted under both its guest and its customer identity.

---

## 3. Consent snapshot semantics — event time vs send time `[DOC §7 L118, §13 L266 / REG RULE-002]`

This is the crux. The doc states two things that must be read **together**:
- `[DOC L266]` the snapshot captures *"Consent tại thời điểm event"* — consent state **at event time**.
- `[REG RULE-002]` consent must be valid *"at event/send time"* — i.e. **also re-checked at send time**.

Therefore **two distinct checkpoints**, not one:

| Checkpoint | When | What happens | Fail-closed effect |
|---|---|---|---|
| **Event-time snapshot** | at the tracking hook, when the event is logged | capture/reference `consent_snapshot_id` = the immutable consent state then `[DOC L266]` | no valid snapshot ⇒ event may be logged **internal-only** with that fact recorded; **nothing external** is queued `[DOC L118]` |
| **Send-time re-validation** | in the outbox worker, before any external dispatch | **re-check** that consent is **still** valid now (it may have been withdrawn/expired since the event) `[REG RULE-002]` | consent withdrawn/expired/opt-out at send time ⇒ **do not send**; hold/drop the outbox item with audit |

`[PACK]` The consent snapshot is **immutable** (a point-in-time record, like attribution snapshots). The
send-time check is a **fresh** read of current consent, not a re-use of the stale snapshot's verdict — this is
what stops a "consent-at-event-time, withdrawn-before-send" event from leaking externally. `[DOC L257]`
`consent_valid` is one AND-term of `send_policy`, evaluated **at send time**.

---

## 4. Fail-closed enforcement points `[DOC §3 L60, §7 L118 / REG RULE-002, FAIL-002]`

Default is **DENY the external action** whenever consent is missing/invalid/withdrawn/expired. Fail-closed
targets (doc-named) are **external measurement, audience sync, CRM** `[DOC L60/L118]`:

1. **Event ingestion / tracking hook** — attach `consent_snapshot_id`; a missing snapshot blocks any external
   queueing (internal-only logging with the gap recorded; whether even internal logging is permitted without
   consent is an owner clarification — §6). `[DOC L118]`
2. **Conversion-event creation** (source for the measurement outbox) — consent must be present to become an
   external-send candidate. `[REG CTR-007]`
3. **Measurement outbox worker** (Pixel/CAPI/Offline dispatch) — **send-time consent re-validation** (§3);
   invalid ⇒ hold/drop, never send. `[REG RULE-004/RULE-002]`
4. **Audience outbox worker** (audience sync) — send-time re-validation **and** audience membership must derive
   only from consent-passing, approved segments. `[REG RULE-004]`
5. **CRM path** — consent **plus** suppression state must pass `[REG RULE-017]`; **M6 never sends CRM itself**
   `[BRIEF]` — it only measures/gates; the actual CRM send is CRM-owned.

Every fail-closed denial writes a `FAIL-002`-style audit record (event ref, checkpoint, reason:
CONSENT_MISSING|WITHDRAWN|EXPIRED|OPT_OUT, ts) with **no raw PII** `[BRIEF rule 4, REG RULE-014]`.

---

## 5. Boundary guards `[BRIEF / REG §18]`

- **Read-only** on identity and consent; M6 never creates/reassigns identity, never creates/edits consent,
  **never sends CRM** or decides member rights `[BRIEF, REG §18]`.
- **No raw PII** `[REG RULE-014, BRIEF rule 4]`: `guest_id/customer_id/psid`, phone, email, address handled by
  reference; masked (`abc***xy`) + `secret_ref` in every log/evidence; PII never leaves without the hash
  policy (M6-OD-003).
- Consent/identity payloads originating from channels are **untrusted DATA** `[BRIEF rule 6]`.
- Nothing here enables external send: `global_gateway_state=BLOCKED`, `production_flag=OFF` unchanged.

## 6. Owner-decision dependencies (explicit list — acceptance requirement)

| Dependency | Status | What it gates |
|---|---|---|
| `M6-CTR-005` (guest_contacts) + `M6-CTR-006` (consent snapshot) consumed shapes | `MISSING` → **M6-P0702** `[REG]` | the exact read contracts; needed before **M6.2A** |
| `M6-OD-003` (hash policy + allowed PII fields) | **OPEN** `[REG]` | how identity/consent PII is masked/hashed before any external send |
| Consent scope granularity (single "marketing" consent vs per-purpose: measurement / audience / CRM) | **candidate** `[PACK]` — doc says "marketing consent", purpose-split unspecified | which sends each consent authorizes |
| Consent expiry / re-consent window; opt-out propagation latency | **candidate** `[EXT]` — not doc-specified | send-time validity horizon (§3) |
| Whether internal-only logging is permitted with no consent (vs held) | **candidate** `[PACK]` — doc fail-closes external only `[DOC L118]` | §4 checkpoint 1 behavior |
| Guest→customer re-link authority + evidence standard | **candidate** `[PACK]` — RULE-006 requires evidence, standard unspecified | §2 audited re-link |

`[PACK]` This research **records** these; it resolves none. Where a build leg needs one, the affected M6.2A
leg is marked BLOCKED, not assumed.

## 7. Doc-traceability (owner-mandated vs proposal)

| Element | Source |
|---|---|
| Identity tables + guest→customer mapping with audit, never overwrite without evidence | `[DOC §7 line 115]` + `[REG RULE-006]` — owner-mandated |
| Identity chain guest→customer→order→verified; prevents double count | `[DOC §3 line 62]` — owner-mandated |
| consent snapshot mandatory; fail-closed; no external measurement/audience/CRM when consent missing | `[DOC §7 line 118, §3 line 60]` + `[REG RULE-002/FAIL-002]` — owner-mandated |
| snapshot = consent at event time | `[DOC §13 line 266]` — owner-mandated |
| consent_valid as an AND-term of send_policy | `[DOC §12 line 257]` — owner-mandated |
| Send-time re-validation as a distinct checkpoint; append-only link history; audit-record shape; consent scope/expiry; internal-only-logging question; all §-tagged proposals | `[EXT]` / `[PACK]` — **owner-review proposals, NOT owner requirements** |

*Nothing in this file flips a gate or a flag; `global_gateway_state=BLOCKED`, `production_flag=OFF`.*
