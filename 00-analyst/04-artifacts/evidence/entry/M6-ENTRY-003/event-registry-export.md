# M6-ENTRY-003 · Core Event Governance — event_registry export & governance evidence

- **Đơn:** M6-ENTRY-003 (Core Event Governance → Module 6). Yêu cầu: event_registry tồn tại + mỗi event có **owner / channel / data-sensitivity / external-send policy**.
- **Nguồn (provenance):** repo `PhucApu/ginsengfood-business-platform` @ **f90152d2** (nhánh `PhucApu`, chưa merge) — đây là repo platform/Commerce (owner chọn làm nguồn Core event-gov). Trích verify+refute 8 agent (ASSERT-005 verify lỗi tool → verify trực tiếp).
- **PII/secret:** không có; toàn bộ là DDL/seed/code + file:line.
- **Overall:** 🟠🟠🔴🔴🔴 — **2 PARTIAL + 3 GAP**. Registry tồn tại + governed + owner/source seed thật; nhưng **thiếu channel-attribution, data-sensitivity, external-send-policy**, và **không phải "Core"-owned**.

---

## E1 — event_registry TỒN TẠI (DDL gốc)
`back-end/src/main/resources/db/migration/V1__foundation_baseline.sql:248-262`
```sql
CREATE TABLE event_registry (
  event_code VARCHAR(64) PRIMARY KEY,
  event_group VARCHAR(64) NOT NULL,
  domain VARCHAR(64) NOT NULL,
  event_description TEXT,
  event_source_allowed JSONB NOT NULL DEFAULT '[]'::JSONB,   -- emitter allowlist (KHÔNG phải attribution channel)
  is_crm_trigger BOOLEAN NOT NULL DEFAULT FALSE,
  is_ads_conversion BOOLEAN NOT NULL DEFAULT FALSE,           -- tín hiệu external-send DUY NHẤT; FALSE mọi row seed
  is_active BOOLEAN NOT NULL DEFAULT TRUE, created_at ..., updated_at ...
);
```

## E2 — Governance (V26 thêm owner/lifecycle/approval)
`V26__p0_06_governance_registry_seed_support.sql:8-52`
```sql
ADD COLUMN owner_flow VARCHAR(32) NOT NULL DEFAULT 'FLOW_UNASSIGNED';   -- sentinel default, KHÔNG có CHECK cấm
ADD COLUMN owner_service VARCHAR(128) NOT NULL DEFAULT 'UNASSIGNED';
ADD COLUMN payload_contract_version ...; required_fields_json ...;
ADD COLUMN deprecated_at/by/reason; replacement_event_code (self-FK); approval_request_id;
```
Runtime governance: `event/api/AdminEventRegistryController.java:40-118` (`/api/v1/admin/event/registry` CRUD + activate/deactivate).

## E3 — Owner/source SEED THẬT (không phải default)
`seed/EventRegistryDataSeeder.java:581-599` (INSERT 12 cột) · `:800-811` `ownerServiceFor()` · test `EventRegistryDataSeederTest.java:257-273` `allSatisfy` ép 91 event có owner thật.
`V57__p3_08...sql:20-41` seed FLOW_04 (`ORDER_LIFECYCLE`/`PAYMENT_FINANCE`/`ORDER_FULFILLMENT`); `V36_1__p1_02...sql:19-60` seed FLOW_02/`GUEST_CONTACT`. `event_source_allowed` validate non-empty vs `event/domain/EventSourceCatalog.java` (throw nếu rỗng).

---

## Map 5 assertion → thực tế

### ASSERT-001 registry tồn tại — 🟠 PARTIAL
CHỨNG MINH: table tồn tại (E1) + governed (E2) + owner/source seed thật (E3).
KHÔNG: `EventSourceCatalog.java:7` tự ghi **"Platform-owned"**; seeder `:24-25` = "Phase-0 governance baseline"; seed trải FLOW_01..09 (identity/catalog/inventory/shipping/golden-hour/governance) → **registry PLATFORM/phase-wide, KHÔNG phải Module-3 "Core"-owned**. M6 phải coi là shared platform registry.

### ASSERT-002 OWNER per event — 🟠 PARTIAL
CHỨNG MINH: `owner_flow`+`owner_service` seed thật per-event, test-enforced (E3); 0 row seed mang sentinel.
KHÔNG: (1) không schema-invariant — NOT NULL nhưng DEFAULT sentinel, **không CHECK** cấm `UNASSIGNED`; (2) runtime `CreateEventRegistryRequest.java:11-18` **KHÔNG có field owner** + entity không map cột owner → event tạo qua Admin API lúc chạy = `UNASSIGNED`. "MỖI event có owner" đúng cho seed corpus, **sai** cho event tạo runtime.

### ASSERT-003 CHANNEL per event — 🔴 GAP
KHÔNG có cột `channel`. `event_source_allowed` (JSONB) seed thật nhưng là **allowlist EMITTER** (SYSTEM/ADMIN/ORDER/PAYMENT/CUSTOMER/…) — WHO được phép phát event, **không phải attribution-channel** (FB Ads/Messenger/Live/organic) mà M6 Ads cần. Occurrence-channel (nếu có) ở `p6_event_logs.event_source` — vẫn là emitter. Token CHANNEL duy nhất trong package = pg NOTIFY channel name (plumbing).

### ASSERT-004 DATA-SENSITIVITY per event — 🔴 GAP
KHÔNG có cột/enum/annotation/config phân loại sensitivity per-event **ở đâu cả** (grep `data_sensitivity|privacy_class|pii_level|data_classification` = 0). `data_class` chỉ tồn tại trên **bảng log runtime** (`event_packages` V31:25, `audit_logs` V32:32,38, `system_events`) — phân loại bản-ghi-đã-log lúc chạy, KHÔNG phải định nghĩa registry. `data_class` trong seeder chỉ là **payload field của 4 event SENSITIVE_EXPORT_*** (`:227-246`), không phải chiều registry.

### ASSERT-005 EXTERNAL-SEND POLICY per event — 🔴 GAP
KHÔNG có cột send/outbound/external/egress policy per-event (grep `send_policy|outbound_policy|external_send|is_external` = 0). Tín hiệu external-send DUY NHẤT là `is_ads_conversion` (boolean) — và **FALSE trên MỌI row seed** (E1 seed V57/V36_1 + baseline factory hardcode false) → không phân biệt được event nào được gửi ra ngoài. Với module Ads (có thể đẩy dữ liệu ra ad platform) đây là **thiếu control an toàn cốt lõi**.

---

### Kết luận ENTRY-003 — 2 PARTIAL + 3 GAP
Core event_registry **tồn tại và được governed thật**, owner/source seed đầy đủ — nhưng **thiếu 3/5 chiều governance** (attribution-channel · data-sensitivity · external-send-policy) và **không phải "Core"-owned**. Nộp trung thực → Judge M6-P1000 **BLOCKED** cho ENTRY-003. Đây là **gap schema Core thật**, không phải lỗi trích.
