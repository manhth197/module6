# M5 / Facebook Gateway — ASSERT-006: chống spam (rate / dedup / allowlist)

- **Entry:** M6-ENTRY-004 · **Assertion:** ASSERT-006 (M5 / Gateway) · **Grade: PARTIAL** (KHÔNG PROVEN — assertion YẾU NHẤT, có gap cấu trúc THẬT)
- **Author:** M5 Evidence Author (Nguyễn Đức Mạnh) · **Ngày:** 01/08/2026
- **Cách làm:** đã MỞ từng file thật trước khi trích; mỗi citation ghi kèm **branch@sha**.

## Provenance theo branch
- Đường **public** (spotlight) chỉ ở **`feat@0f7923e`** (chưa merge). **`main@87fad53` không có public egress** ⇒ trên canonical không có mặt "đường gửi ra kênh" để chống-spam theo nghĩa công khai. Các cơ chế foundation (idempotency / suppression) là canonical đã merge.

## Từng control — trạng thái THẬT (không tô hồng)

### (a) allowlist — ✅ ĐỦ (default-deny, fail-closed)
- Card spotlight: `feat@0f7923e` `src/outbound-guard/domain/spotlight-public-safe.ts` — `isNameAllowed:143` (name-whitelist rỗng ⇒ **deny-all**) + `isHostAllowed:152` (host-allowlist rỗng ⇒ deny). Đây là default-deny THẬT.
- Public template (đường PUBLIC_ACK cũ): `feat@0f7923e` `src/outbound-guard/outbound-dispatcher.ts:37,421` — `APPROVED_PUBLIC_TEMPLATES` chặn template ngoài danh sách.

### (b) dedup — 🟠 YẾU (per-instance, không cross-instance)
- Outbound idempotency key ghép `seed + subject + channel + class`, register tại `feat@0f7923e` `src/outbound-guard/outbound-dispatcher.ts:324` (`idempotency.register(...)`).
- **Nhưng** store = `InMemoryIdempotencyStore` — `main@87fad53` `src/foundation/idempotency/idempotency.module.ts:9` (`{ provide: IDEMPOTENCY_STORE, useClass: InMemoryIdempotencyStore }`); nội tại là `new Map<...>()` per-instance — `main@87fad53` `src/foundation/idempotency/in-memory-idempotency.store.ts:14`. **Không persistence, không cross-instance**: đa-instance hoặc restart ⇒ MẤT dedup; chỉ trùng đúng exact-key.

### (c) rate-limit — 🟠 KHÔNG ĐÚNG CHỖ (chỉ đọc throttle của Meta, không phải bộ đếm của M5)
- Trên đường outbound chỉ có **lớp đọc channel-throttle** trong suppression: `main@87fad53` `src/suppression/domain/suppression-policy.ts:24` (layer key `rate_limit`, `clean='OK' / active='THROTTLED'`), feed bởi mock `main@87fad53` `src/suppression/adapters/mock/mock-gateway-channel-state.ts:23-30` (chỉ THROTTLED cho 1 subject mock cụ thể). Tức "**tôn trọng throttle Meta**", KHÔNG phải bộ đếm send-rate do M5 tự áp.
- Bộ đếm rate THẬT (`RedisRateLimiter`) nằm ở **đường INBOUND moderation** (`main@87fad53` `src/rate-moderation/adapters/real/redis-rate-limiter.ts`, contract `moderation-handoff`), và **default MOCK** (`main@87fad53` `src/rate-moderation/rate-moderation.module.ts:16-19`, real chỉ khi `RATE_LIMITER_MODE=redis`). `grep RATE_LIMITER` trong `src/outbound-guard/` = **0 hit** ⇒ limiter này KHÔNG nằm trên đường outbound-to-channel.

### (phụ) handoff gửi NGOÀI chokepoint
- `main@87fad53` `src/comment-boundary/http/handoff.controller.ts:85` gọi `this.handoffSink.send(handoff)` **thẳng**, không qua `OutboundDispatcher`. Đây là **mock private handoff** (doc `:42-43`: "authorizes NO real outbound") — KHÔNG phải public egress, nhưng nằm NGOÀI chỗ gác chung (ghi nhận để minh bạch).

## Grade: **PARTIAL** — allowlist đủ; dedup + rate-limit có gap cấu trúc thật; chưa egress thật

## Vì sao CHƯA PROVEN
- Gốc chung (không-egress-thật): chưa post công khai thật (stub P4 + production hard-off).
- Cộng thêm **gap cấu trúc thật** (không chỉ "chưa có egress"): dedup per-instance; rate-limit outbound chỉ là đọc throttle Meta chứ không phải counter M5.

## Việc nợ (open_blockers liên quan 006)
- **DEBT-2:** thay dedup store → bản **persistent / cross-instance**.
- **DEBT-3:** thêm **bộ đếm send-rate outbound do M5 tự áp** trên đường public, HOẶC **ghi rõ (documented)** là dựa vào Meta channel-throttle + limiter inbound và risk-accept cho pilot. (Cân nhắc đưa `handoff.send` qua chokepoint chung, hoặc ghi rõ vì sao tách.)
