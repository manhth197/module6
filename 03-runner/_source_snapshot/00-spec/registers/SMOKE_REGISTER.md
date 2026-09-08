# SMOKE_REGISTER — Module 6

Doc smokes come first, mapped 1:1 to the owner document's P0 Smoke Test Matrix
(doc §21, extract lines 399–415). The owner's original IDs (ADS-P0-xxx) are
preserved as aliases; the pack ID scheme is M6-SMK-xxx. Proposed additions are
clearly labeled `proposed` and are `HARDENING — OWNER REVIEW`.

Slice bindings are machine-readable in `00-spec/slices/slice_definitions.json`
(that file is the single source for bindings; this register lists them for
human reading and the validator cross-checks both).

## Owner smokes (doc §21, verbatim scenario/expected)

| Smoke ID | Doc ID | Kịch bản (verbatim) | Kết quả phải đạt (verbatim) | Bound slices | Source |
|---|---|---|---|---|---|
| M6-SMK-001 | ADS-P0-001 | Event không có trong event_registry | Reject/HOLD, audit rõ | M6.2A, M6.2B, M6.2K | extract line 401 |
| M6-SMK-002 | ADS-P0-002 | Event hợp lệ nhưng thiếu consent | Không external measurement, không audience sync | M6.2A, M6.2C, M6.2K | extract line 402 |
| M6-SMK-003 | ADS-P0-003 | Duplicate Pixel/CAPI/Offline | Dedup, không double count | M6.2B, M6.2D, M6.2K | extract line 403 |
| M6-SMK-004 | ADS-P0-004 | Quote được tạo nhưng chưa order | Không revenue, không ROAS | M6.2F, M6.2I, M6.2K | extract line 404 |
| M6-SMK-005 | ADS-P0-005 | Order Draft / Order Created chưa verified | Không tính Revenue Verified | M6.2F, M6.2K | extract line 405 |
| M6-SMK-006 | ADS-P0-006 | ORDER_VERIFIED có campaign/adset/ad đầy đủ | ROAS/CPA/AOV dashboard cập nhật | M6.2E, M6.2F, M6.2K | extract line 406 |
| M6-SMK-007 | ADS-P0-007 | ORDER_VERIFIED thiếu source | Revenue vẫn lưu, attribution confidence LOW/HOLD | M6.2E, M6.2K | extract line 407 |
| M6-SMK-008 | ADS-P0-008 | CRM opt-out | Không sync CRM audience/CRM event outbound | M6.2J, M6.2K | extract line 408 |
| M6-SMK-009 | ADS-P0-009 | Recall/Sale Lock active | Scale Gate FAIL/HOLD | M6.2G, M6.2K | extract line 409 |
| M6-SMK-010 | ADS-P0-010 | Data Mart tạo trigger CRM/scale | Fail - Data Mart chỉ support view | M6.2F, M6.2J, M6.2K | extract line 410 |
| M6-SMK-011 | ADS-P0-011 | Learning candidate ngoài safe range | Hold review, không publish | M6.2H, M6.2K | extract line 411 |
| M6-SMK-012 | ADS-P0-012 | Scale request không owner approval | Không scale | M6.2G, M6.2K | extract line 412 |
| M6-SMK-013 | ADS-P0-013 | Live/Comment/Messenger chain | Trace được live_session_id, comment_id, messenger_thread_id | M6.2E, M6.2I, M6.2K | extract line 413 |
| M6-SMK-014 | ADS-P0-014 | Diamond referral order verified | Gắn referral attribution, không tự tính commission | M6.2J, M6.2K | extract line 414 |
| M6-SMK-015 | ADS-P0-015 | Dashboard hiển thị quote/order draft như revenue | Fail | M6.2F, M6.2K | extract line 415 |

## Proposed additions (proposed — HARDENING — OWNER REVIEW)

| Smoke ID | Status | Scenario | Expected | Bound slices | Derivation |
|---|---|---|---|---|---|
| M6-SMK-016 | proposed | Outbox item fails to send N times | Bounded retry with error_log + next_retry_at, then dead-letter; no infinite retry, no silent loss | M6.2C, M6.2K | doc §12 line 252, M6.2C done gate line 387 (retry/dead-letter named in doc but absent from P0 matrix) |
| M6-SMK-017 | proposed | External payload (CAPI/Offline) built from an event containing raw PII | Hash policy applied per M6-OD-003; no raw phone/email/user-id in the outbound payload or platform result log | M6.2D, M6.2K | doc §12 line 248, §22 line 429, M6.2D done gate line 388 ("no PII thô" named in doc but absent from P0 matrix) |
| M6-SMK-018 | proposed | Attribution correction attempted after ORDER_VERIFIED | Direct mutation rejected; adjustment record created with actor, reason, audit, evidence | M6.2E, M6.2K | doc §11 line 242 (immutability rule named in doc but absent from P0 matrix) |
| M6-SMK-019 | proposed | ORDER_VERIFIED with a resolved ad source | attribution_id present as a first-class key of AdsAttributionContext + handoff payload; ORDER_VERIFIED traces attribution_id -> campaign | M6.2L | FIX_M6 audit 2026-09-03 item A3; M6.md:195-214 |
| M6-SMK-020 | proposed | POST /api/ads/events/track for a FACEBOOK_AD event carrying campaign/adset/ad/live_session | intake + normalize persist the 4 ad-hierarchy ids; resolver reaches HIGH source confidence via the real API path | M6.2L | FIX_M6 audit 2026-09-03 item A4; M6.md:139,180-184,361 |
| M6-SMK-021 | proposed | Evidence pack assembled with a fake-but-nonblank ref, or one valid ref copy-pasted across all mandatory keys of all 10 categories | categories read MISSING (never COMPLETE); ref existence + uniqueness + category-binding enforced, not raw truthiness | M6.2L | FIX_M6 audit 2026-09-03 item B2 / M6-OD-013; status.md §4b |
| M6-SMK-022 | proposed | Gap-blocker list carries a duplicated/shadowing standing-blocker id (M6-P1000/M6-P1309) | the floor detects the duplicate and FAILs (membership count, not set-subset) | M6.2L | FIX_M6 audit 2026-09-03 item B3 / M6-OD-014; status.md §4b |
| M6-SMK-023 | proposed | In-process QUOTE_SENT row + store.materialize(revenue_value>0, verified=True) | no revenue set (event_code enforced at materialize); dashboard Revenue Verified = 0 and ROAS = 0 (event_code filter at verified_rows) | M6.2L | FIX_M6 audit 2026-09-03 item B4; M6.md ROAS-on-ORDER_VERIFIED |
| M6-SMK-024 | proposed | Evidence pack assembled with a known-refs allowlist + a ref that is shape-valid, uniquely used, correctly (category,key)-bound, but NOT in the allowlist (canonical-string reconstruction) | that category reads MISSING (authenticity, not just slot-correctness); with no allowlist the M6.2L slot-correctness bar still holds (no regression) | M6.2M | M6-OD-013 ref-side authenticity residual (M6.2L re-judge 2026-09-03) |
| M6-SMK-025 | proposed | SmokeResult for a mandatory owner smoke carries whitespace / fake-but-nonblank status/correlation_id/evidence_id | recorded() is False (stripped-non-blank required, not raw truthiness); the mandatory smoke stays un-recorded → pack NOT_READY | M6.2M | M6-OD-013 smoke-side twin (doc B2 Ghi chú 'vá cả hai một lượt') |
| M6-SMK-026 | proposed | A raw PSID supplied at the resolve seam is stored/exported (B1 psid_hash) | no raw psid on any durable/export surface — as_stored() carries only a one-way `psid_hash:` HMAC value (deterministic per pepper, collision-sensitive); production with the pepper env unset fails closed (PsidHashPolicyError) | M6.2O | out-of-band B1 (impl M6.2N psid_hash); chief-auditor 2026-09-07 item B4 |
| M6-SMK-027 | proposed | A duck smoke object with a fake .recorded=True + blank status/correlation_id/evidence_id for a mandatory owner smoke (F2-6) | _smokes coerces it to a canonical SmokeResult, recomputes recorded=False → UNRUN_SMOKE gap → pack NOT_READY (caller .recorded never trusted) | M6.2O | out-of-band F2-6 (impl M6.2O duck-coerce); chief-auditor 2026-09-07 item B4 |
| M6-SMK-028 | proposed | event_registry row with external_send_policy = each of ALLOW_EXTERNAL / INTERNAL_ONLY / BLOCKED_PII / BLOCKED_DEFAULT + a None/blank/unknown token (B5) | typed ExternalSendPolicy enum; permits_external_send() True ONLY for ALLOW_EXTERNAL; None/blank/unknown coerces fail-closed to BLOCKED_DEFAULT (no crash, no auto-allow); every real ACCEPTED event still send_permitted=False (no event is ALLOW_EXTERNAL) and EXTERNAL_SEND stays OFF | M6.2P | chief-auditor 2026-09-07 item B5; M6-OD-003 enum half signed (QĐ-1) |
