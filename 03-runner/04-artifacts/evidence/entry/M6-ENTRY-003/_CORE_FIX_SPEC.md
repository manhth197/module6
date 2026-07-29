# Hướng A — Core fix spec: bổ sung 3 chiều governance vào `event_registry`

> Mục tiêu: đóng 3 GAP (channel-attribution · data-sensitivity · external-send-policy) + siết owner, để ENTRY-003 trích lại **PROVEN**. Đây là **spec dev cho platform/Core**, không phải AI tự sửa code.

## 1. Thêm cột (migration mới, ví dụ `Vxxx__p6_event_registry_m6_governance.sql`)
```sql
ALTER TABLE event_registry
  -- 003: attribution channel per-event (KHÁC event_source_allowed = emitter)
  ADD COLUMN IF NOT EXISTS attribution_channel VARCHAR(32) NOT NULL DEFAULT 'NONE'
    CHECK (attribution_channel IN ('NONE','FB_ADS','MESSENGER','LIVE','ORGANIC','MULTI')),
  -- 004: phân loại độ nhạy dữ liệu per-event
  ADD COLUMN IF NOT EXISTS data_sensitivity VARCHAR(16) NOT NULL DEFAULT 'INTERNAL'
    CHECK (data_sensitivity IN ('PUBLIC','INTERNAL','PII','SENSITIVE')),
  -- 005: chính sách gửi ra ngoài per-event — DEFAULT fail-closed
  ADD COLUMN IF NOT EXISTS external_send_policy VARCHAR(24) NOT NULL DEFAULT 'BLOCKED'
    CHECK (external_send_policy IN ('BLOCKED','ALLOWED_AGGREGATE','ALLOWED_HASHED','ALLOWED'));
```
**Fail-closed:** `external_send_policy` default = `BLOCKED` (event chưa phân loại thì KHÔNG được gửi ra ngoài). Đây là điểm mấu chốt cho module Ads.

## 2. Siết OWNER (đóng 002 PARTIAL)
- Thêm CHECK cấm sentinel: `CHECK (owner_flow <> 'FLOW_UNASSIGNED' AND owner_service <> 'UNASSIGNED')` **sau khi** đã seed hết; và/hoặc
- Thêm `ownerFlow/ownerService` (+ 3 cột mới) vào `CreateEventRegistryRequest` + entity + service create/update, để event tạo runtime KHÔNG rơi về default.

## 3. Seed per-event 3 cột mới
Cập nhật `EventRegistryDataSeeder.java` + các migration seed (V36_1/V39/V57/…) đặt giá trị thật cho từng event: sự kiện conversion → `attribution_channel`, `external_send_policy=ALLOWED_AGGREGATE`; event chứa PII → `data_sensitivity=PII|SENSITIVE` + `external_send_policy=BLOCKED`.

## 4. Nghiệm thu
Trích lại ENTRY-003 (workflow `m6-entry-003-core-eventgov-verify`): 5/5 PROVEN → gỡ `owner_risk_acceptance` tạm, ký owner thật.

**Chủ trì:** owner của event_registry (platform governance / trong repo Phúc). Ước lượng: 1 migration + seed + sửa DTO/entity/service create — gọn.
