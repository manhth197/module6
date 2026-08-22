# M5 / Facebook Gateway — ASSERT-004: KHÔNG public giá cuối

- **Entry:** M6-ENTRY-004 · **Assertion:** ASSERT-004 (M5 / Gateway) · **Grade: PARTIAL** (KHÔNG PROVEN)
- **Author:** M5 Evidence Author (Nguyễn Đức Mạnh) · **Ngày:** 01/08/2026
- **Cách làm:** đã MỞ từng file thật trước khi trích; mỗi citation ghi kèm **branch@sha**. Trần grade = PARTIAL (không tự phong PROVEN/PASS).

## Provenance theo branch (điểm chịu lực — đọc trước)
- **`main@87fad53`** = canonical **ĐÃ MERGE**. **main KHÔNG có bất kỳ đường public-egress nào** — `git ls-tree -r 87fad53` = **0 hit** cho `spotlight.controller.ts` / `spotlight-public-safe.ts`. Canonical đang chạy đơn giản là **không có mặt egress công khai để rò giá**.
- **`feat/live-spotlight-endpoint@0f7923e`** = nhánh **CHƯA merge / CHƯA push** (local). Đây là **nơi DUY NHẤT** có đường public free-text (`LIVE_SPOTLIGHT`).
- ⇒ Toàn bộ cơ chế "chặn giá công khai" chỉ tồn tại ở nhánh chưa-merge. Sự thật này làm câu chuyện an toàn MẠNH hơn — không giấu.

## Cơ chế CÓ THẬT + wired ở đâu
1. **Đường public free-text duy nhất** — `feat@0f7923e` `src/outbound-guard/http/spotlight.controller.ts:56` (`@Post('spotlight')`, RBAC `GATEWAY_LIVE_SPOTLIGHT_SEND` `:58`). Controller KHÔNG tự gọi Graph; map sang `OutboundRequest` rồi route qua `OutboundDispatcher.dispatch()` chung.
2. **Guard default-deny trên card** — `feat@0f7923e` `src/outbound-guard/domain/spotlight-public-safe.ts:177` `evaluateSpotlight()`: `publicSafe = (reasonCodes.length === 0)` (`:185`). Chỉ PASS khi CẢ 3: (a) `productPublicName` ∈ name-whitelist owner — `isNameAllowed:143` (whitelist rỗng ⇒ **deny-all**); (b) host của `productLinkFb` ∈ host-allowlist — `isHostAllowed:152`; (c) card không chứa giá/link/cụm-cấm/PII — kiểm giá `hasPriceOrMoney:117`.
3. **Enforce tại chokepoint chung** — `feat@0f7923e` `src/outbound-guard/outbound-dispatcher.ts:195` gọi `spotlightGuard.evaluate(...)`; kết quả feed `authorizeSend` — `feat@0f7923e` `src/outbound-guard/domain/send-authorization.ts:51,56`: `publicSurfaceViolation = (replySurface===PUBLIC && !publicSafe)` ⇒ `sendAllowed=false`. `sink.send()` CHỈ chạy trong nhánh `if (sendAllowed)` (`dispatcher:313-324`).
4. **Chưa có egress THẬT (gated)** — `feat@0f7923e` `src/outbound-guard/adapters/real/graph-post-comment-sink.ts:18,22`: `tier='REAL'` nhưng `send()` **throw** `GRAPH_POST_COMMENT_SINK_NOT_IMPLEMENTED_P4`; default sink = `MockSpotlightSink` (tier MOCK). DEV-12 self-gate `dispatcher:314` từ chối REAL sink khi `!isProductionEnabled()`. Production **hard-off**: `main@87fad53` `src/foundation/feature-flag/feature-flag.service.ts:17` `PRODUCTION_ENABLED = false` (static, không set được qua env).

## Grade: **PARTIAL** — không tìm ra bypass khai thác được, nhưng KHÔNG PROVEN

## Vì sao CHƯA PROVEN
- **Gốc chung (không-egress-thật):** real Graph sink = stub P4 + production hard-off ⇒ "không rò giá ra kênh công khai THẬT" mới chỉ đúng **kiểu tầm thường** (hiện chưa post gì công khai cả). Guard-chặn-trước-gửi chỉ được chứng minh với **MOCK** sink, không phải Graph thật.
- **Kiểm giá = denylist/heuristic, tác giả code TỰ disclaim:** `feat@0f7923e` `spotlight-public-safe.ts:3-8` ghi nguyên văn rằng denylist trên free text *"cannot GUARANTEE the negative — Vietnamese word-form prices, teencode, homoglyphs…"*. ⇒ một biểu đạt giá đủ lắt léo vẫn có thể ⇒ `publicSafe=TRUE` ⇒ `authorizeSend` sẽ AUTHORIZE (chỉ nhờ MOCK sink nên chưa thành post thật).

## Việc nợ (open_blockers liên quan 004)
- **DEBT-1 (§4 default-deny template):** hiện thực ODR-002 §4 — template/allowlist owner-duyệt cho card text (thay heuristic best-effort). Đang PARK (owner + M7 Live).
- **DEBT-4 (real Graph sink):** hiện thực `graph-post-comment-sink` (P4) để certify phủ định end-to-end; gated bởi production.
- Guard-rail đã có (không phải remediation): `feat@0f7923e` `test/outbound-guard/spotlight-a1-tripwire.probe.ts` — chặn việc mở DTO nhận `spotlightTemplateId` TRƯỚC khi template registry land (đảo thứ tự A1).
