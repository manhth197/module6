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
