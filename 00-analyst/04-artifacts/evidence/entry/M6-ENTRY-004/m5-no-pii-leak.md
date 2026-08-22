# M5 / Facebook Gateway — ASSERT-005: KHÔNG leak PII (chỉ hashed/masked)

- **Entry:** M6-ENTRY-004 · **Assertion:** ASSERT-005 (M5 / Gateway) · **Grade: PARTIAL** (KHÔNG PROVEN)
- **Author:** M5 Evidence Author (Nguyễn Đức Mạnh) · **Ngày:** 01/08/2026 · **pii_handling:** MASKED_OR_NONE (artifact này KHÔNG chứa PII thô — chỉ mô tả cơ chế + tên nhãn + `secret_ref`).
- **Cách làm:** đã MỞ từng file thật trước khi trích; mỗi citation ghi kèm **branch@sha**.

## Provenance theo branch
- Cơ chế mask/hash PII là **canonical, đã merge ở `main@87fad53`** (dùng cho toàn bộ inbound + đường private). Đường **public** (spotlight) chỉ ở **`feat@0f7923e`** (chưa merge) — và **`main` không có public egress** nên trên canonical không có mặt kênh công khai để rò PSID/phone/email.

## Cơ chế CÓ THẬT + wired ở đâu
1. **Masker thật (deny-shape):** `main@87fad53` `src/foundation/evidence/masking.ts` — `MIN_DIGIT_RUN = 10` (`:24`) ⇒ mọi **chuỗi ≥10 chữ số** (phone / PSID / Meta-object-id) bị mask; bộ `STRING_PATTERNS` (`:28`) gồm nhãn **FB_TOKEN** (EAA-prefixed, `:29`) và **EMAIL** (`:30`). `containsSensitive()` (`:103`) = kiểm shape; `deepMask()` (`:129`) deep-mask payload trước khi ghi evidence.
2. **containsSensitive gác ở nhiều điểm:**
   - Endpoint private `delivery/send`: `main@87fad53` `src/outbound-guard/http/delivery.controller.ts:67` → ném `400 RAW_PII_REJECTED` nếu body mang PII thô.
   - Card spotlight (public): `feat@0f7923e` `src/outbound-guard/domain/spotlight-public-safe.ts:138` — `evaluateSpotlightText()` gọi `containsSensitive(text)` ⇒ reason `TEXT_PII` (M4 lớp PII trong guard).
3. **PSID KHÔNG bao giờ đi ra thô:** `recipientRef` là **cust_ref đã hash** (từ M5.2B, không phải PSID thô). Cho spotlight, subject công khai thay bằng **`pub_subj:` + sha256b64(liveVideoRef)** — `feat@0f7923e` `src/outbound-guard/outbound-dispatcher.ts:90` (không kèm PSID/recipient).
4. **Evidence + read đều masked, fail-closed:** `EvidenceService` deep-mask trước khi ghi (fail-closed nếu còn shape nhạy cảm); admin read chỉ trả **`maskedPayload`** — `main@87fad53` `src/admin/admin-read.controller.ts:25,40` (RBAC deny-by-default `:22,31`).

## Grade: **PARTIAL** — cơ chế mask/hash chắc theo cấu trúc, nhưng KHÔNG PROVEN cho kênh công khai

## Vì sao CHƯA PROVEN
- **Gốc chung (không-egress-thật):** chưa có real Graph sink (stub P4) + production hard-off (`main@87fad53` `feature-flag.service.ts:17` `PRODUCTION_ENABLED=false`) ⇒ "không rò PII ra comment/message công khai THẬT" mới đúng kiểu tầm thường (chưa post gì công khai).
- **Card free-text = detector-based:** với `publicSpotlightText` verbatim, lớp PII là `containsSensitive` (detector), **không** default-deny cấu trúc. Header code tự disclaim (`feat@0f7923e` `spotlight-public-safe.ts:3-8`): denylist trên free text không guarantee được phủ định. Certify "không PII trên card công khai" cần chung fix ODR-002 §4 (template owner-duyệt) như 004.

## Việc nợ (open_blockers liên quan 005)
- **DEBT-1 (§4 default-deny template):** dùng CHUNG với 004 — template owner-duyệt + slot đã kiểm ⇒ certify được cả price-safe LẪN PII-safe cho card.
- **DEBT-4 (real Graph sink):** để chứng minh phủ định end-to-end trên egress thật.
