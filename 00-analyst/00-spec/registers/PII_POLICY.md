# PII_POLICY — Module 6

M6's handling of personal data + external-send policy. Canonical; consolidates the
PII-relevant owner decisions. Bất biến: `production_flag=OFF` · `global_gateway_state=BLOCKED`
· `external_send=OFF` — nothing leaves the system until go-live conditions are met.

## 1. psid (Messenger PSID)
- Stored/exported ONLY as a one-way salted hash: `psid_hash:` + base64url(HMAC-SHA256(pepper, psid)),
  M6-own pepper (env `M6_PSID_HASH_PEPPER`, secret_ref at deploy; dev mock is labeled non-secret).
  Raw psid never enters a durable row or an export surface (B1 / M6.2N-O; `identity/psid_hash.py`).
- **No cross-module join by psid_hash (M6-OD-015 / QĐ-3b):** M6 joins across modules by
  `live_session_id` / `comment_id` / `messenger_thread_id` (+ `attribution_id` when M3 emits it),
  never by psid_hash. A shared system-wide pepper (option a) would need privacy/legal (Sếp) +
  re-hash/drop of existing values — not adopted.

## 2. Raw PII never leaves the system
- No raw phone / email / address / raw user-or-guest id / bank / tax code in code, logs, evidence,
  or an external payload (RULE-014 / FAIL-008 / RULE-H02). PII masked as `abc***xy` in every file
  the pack produces (M6-OD-012).

## 3. external_send_policy (M6-OD-003)
- Typed enum VOCABULARY (owner-signed QĐ-1 2026-09-07): `{ALLOW_EXTERNAL, INTERNAL_ONLY,
  BLOCKED_PII, BLOCKED_DEFAULT}`, default `BLOCKED_DEFAULT`; `permits_external_send()` True ONLY for
  `ALLOW_EXTERNAL`. Unknown/blank token → `BLOCKED_DEFAULT` (fail-closed).
- **No event is classified `ALLOW_EXTERNAL`** — the per-event permit-mapping is OPEN (privacy/legal).
- **Stage-1 field policy (M6-OD-003 QĐ-A cách-1, 2026-09-08):** when an event is eventually opened,
  ONLY non-PII event-level fields may be sent (event_name, event_time, event_id, value, currency,
  content_ids/SKU, action_source). NO identifier field (em/ph/external_id) in stage-1.
- **Hash policy for a future identifier-field opening (RESERVED):** Meta-CAPI standard — normalize
  (lowercase, trim, phone E.164 without +) then SHA-256 hex; `external_id` = M6's `psid_hash`; never
  raw. Opening any identifier field to Meta is a SEPARATE future decision requiring privacy/legal (Sếp).

## 4. Consent gate
- External measurement / audience sync / CRM egress require consent VALID at both event-time snapshot
  and send-time re-validation (M6-CTR-006); MISSING/EXPIRED/OPT_OUT → no send.

## Sources
M6-OD-003 (+ enum / fields-hash-stage1 evidence), M6-OD-012, M6-OD-015; RULES_LOCKED
RULE-014 / RULE-H02; FAIL_GATE_REGISTER FAIL-008; CONTRACT_EVENT_REGISTRY.contract.yaml.
