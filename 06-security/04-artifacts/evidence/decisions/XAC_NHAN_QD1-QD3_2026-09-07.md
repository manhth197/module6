# Xác nhận của chief auditor / Tech Lead về ba quyết định PM M6 trình (QĐ-1, QĐ-2, QĐ-3)

Ngày lập: 07/09/2026 · Người lập: chief auditor (phiên D:\9 module) cho anh Nguyễn Đức Mạnh (Tech Lead) · Gửi: PM M6, dev M6, và phần trình Sếp/Owner.

## 0. Kết luận nhanh — ký được gì, phải trình gì

| Quyết định | Anh Mạnh ký được ngay | Phải trình Sếp / Owner (không ký thay) |
|---|---|---|
| QĐ-1 Hash policy Pixel/CAPI | Phần kỹ thuật fail-closed: adopt enum `external_send_policy` 4 giá trị, mặc định `BLOCKED_DEFAULT`, **không event/field nào là `ALLOW_EXTERNAL` tới khi Sếp phân loại** (đã ký OD-003 ngày 04/09 — xác nhận lại). | (a) danh sách trường được gửi Pixel/CAPI/Offline; (b) cách hash từng trường. Đây là dữ liệu cá nhân rời hệ thống → Sếp + pháp chế. Chief kèm đề xuất kỹ thuật ở mục 2.1 để Sếp chọn. |
| QĐ-2 Nhánh governance registry + M3 thêm cột | (1) Lệnh kỹ thuật cho M3 (Phúc): thêm 2 cột `data_sensitivity`, `external_send_policy` vào `event_registry` = ENTRY-003, enum theo OD-003, số migration **V221**; (2) lệnh M3 cấp change-feed/version endpoint cho registry (tên tạm do chief phát hành). | (a) nhánh registry canonical — quyết định cross-team đụng nhánh của Phúc (PhucApu) và Tài (dev). Chief trình đề xuất ở mục 2.2; Sếp/Owner ký, hoặc anh Mạnh ký nếu Sếp đã ủy quyền Tech Lead quyết định kỹ thuật cross-team (ghi rõ căn cứ ủy quyền khi ký). |
| QĐ-3 psid_hash pepper (C7) | Phương án **(b)**: M6 không join theo psid; join theo `live_session_id` / `comment_id` / `messenger_thread_id`. Đây là phương án không mở rộng khả năng tái định danh → thuộc thẩm quyền chief/Tech Lead. | Phương án (a) shared pepper toàn hệ chỉ mở khi Sếp/pháp chế yêu cầu join danh tính xuyên module (tăng khả năng tái định danh) — nếu chọn (a) thì phải trình. |

Ba dòng "Ký (Sếp)" / "Ký (Sếp/Owner)" trong đề bài của PM M6 là đúng vị trí; chỉ dòng "Ký (Owner/chief)" của QĐ-3 anh ký được ngay với phương án (b).

## 1. Kiểm ba "dữ kiện đã verify" của PM M6 (chief đọc lại trên code M3, 07/09)

1. **Đúng.** `V1__foundation_baseline.sql` tạo `event_registry` với 10 cột (event_code, event_group, domain, event_description, event_source_allowed, is_crm_trigger, is_ads_conversion, is_active, created_at, updated_at) — không có `data_sensitivity` lẫn `external_send_policy` trên `origin/PhucApu` @a47366ba. Hai cột này hiện tồn tại ở **hai nơi chưa hòa**: `origin/dev` V190 + V191 (enum `CHECK (external_send_policy IN ('BLOCKED','ALLOWED'))`, `data_sensitivity` {SENSITIVE, INTERNAL}) và working tree PhucApu `V207__event_registry_governance_external_send.sql` (untracked ngày thứ 9, trùng số với V207 golden-hour đã commit). Cả hai đều là enum 2 giá trị, **không khớp OD-003 4 giá trị**.
2. **Đúng một phần — sửa câu chữ của chief.** `V56__p3_07_order_verification_commission_eligibility.sql` không định nghĩa registry; nó là một trong 27 migration `INSERT INTO event_registry` (seed dòng ORDER_VERIFIED / COMMISSION_ELIGIBLE, `:141-161`). Câu "registry canonical = V56" trong TRA_LOI_BRIEF 04/09 phải đọc là: **registry canonical = bảng `event_registry` (V1) + các dòng seed trong migration mainline, trong đó V56 là dòng ORDER_VERIFIED/COMMISSION mà M6 tiêu thụ**. Chief nhận lỗi câu chữ này.
3. **Đúng.** Id `E-M6-003` không có trong pack M6. Nó là dòng escalation trong ma trận seam của chief: `D:\9 module\9MODULE_SEAM_MATRIX.md` dòng 477 ("Governance event_registry đã có shape hai phía nhưng lệch enum và chưa vào nhánh… Owner + chief (nhánh đích, enum) + M3"). Đề xuất: PM M6 tạo một row register trong pack M6 với id riêng của M6 và trường `ref = 9MODULE_SEAM_MATRIX.md §12 E-M6-003` để theo dõi được hai chiều; chief giữ id E-M6-003 phía ma trận.

Ghi chú: con số "policy ~79 event trên origin/dev vs seeder ~93 event" là số PM M6 đếm; chief chưa đếm lại (đang giả định, chưa verify) — không ảnh hưởng kết luận ký.

## 2. Nội dung ký / trình từng quyết định

### 2.1 QĐ-1 — Hash policy Pixel/CAPI (M6-OD-003 phần privacy/legal)

**Anh Mạnh ký (kỹ thuật, fail-closed):**
> Adopt enum `external_send_policy = {ALLOW_EXTERNAL, INTERNAL_ONLY, BLOCKED_PII, BLOCKED_DEFAULT}`, mặc định `BLOCKED_DEFAULT`; `permits_external_send()` chỉ trả True với `ALLOW_EXTERNAL`; **không event/field nào được gán `ALLOW_EXTERNAL` cho tới khi Sếp ký phân loại**. Không raw PII rời hệ; psid chỉ ở dạng HMAC-SHA256 một chiều (B1). Hiện trạng code đúng như PM mô tả: `app/measurement/registry/validator.py:66-73` luôn trả False.

**Trình Sếp + pháp chế (chief đề xuất để Sếp chọn, không tự chốt):**
- (a) Trường được gửi: đề xuất giai đoạn 1 **không gửi trường định danh nào** — chỉ event-level (event_name, event_time, event_id, value, currency, content_ids/SKU, action_source). Chỉ khi cần match-rate thì mở tối đa `em`, `ph`, `external_id`.
- (b) Cách hash: theo chuẩn Meta CAPI — chuẩn hóa (lowercase, bỏ khoảng trắng, phone dạng E.164 không dấu +) rồi SHA-256 hex; `external_id` = `psid_hash` hiện có của M6 (HMAC-SHA256 + pepper M6) — không dùng psid thô, không dùng email/phone thô. Offline conversion: cùng quy tắc, chỉ khi Sếp ký.
- Đường lùi: mọi trường mở đều gắn `data_sensitivity` + `external_send_policy` trong registry; đóng lại bằng cách đổi policy về `BLOCKED_PII`, không cần deploy code.

### 2.2 QĐ-2 — Nhánh đích governance registry + M3 thêm cột

**Anh Mạnh ký (lệnh kỹ thuật cho M3, Phúc thực thi — additive, fail-closed):**
> ENTRY-003: M3 thêm vào `event_registry` hai cột `data_sensitivity` (SENSITIVE | INTERNAL, mặc định SENSITIVE) và `external_send_policy` (4 giá trị theo OD-003, mặc định `BLOCKED_DEFAULT`), migration đánh số **V221** (số trống kế tiếp sau V220; V207 governance trong working tree PhucApu phải đánh số lại), kèm guard `requireExternalSendAllowed` fail-closed đã viết. M3 cấp cho M6 một endpoint đọc registry có version/change-feed (tên tạm `event-registry-feed.v1`, ví dụ `GET /api/v1/internal/event-registry?since_version=…` trả `registry_version` + danh sách event kèm hai cột trên) — tên/shape cuối do chief phát hành, M6 dựng reader theo tên tạm + TODO.

**Trình Sếp/Owner (chief đề xuất):**
- (a) Nhánh registry canonical = **PhucApu** (nhánh mang runtime mới nhất, V220), governance commit thành V221 với enum 4 giá trị; bản governance trên `origin/dev` (V190/V191, enum 2 giá trị) được hòa khi merge dev ↔ PhucApu theo thứ tự chief chốt (map `BLOCKED → BLOCKED_DEFAULT`, `ALLOWED → ALLOW_EXTERNAL`; mọi dòng chưa phân loại về `BLOCKED_DEFAULT`). Lý do cần Sếp/Owner: đổi nhánh và enum của cả Phúc lẫn Tài.
- (b) Change-feed/version endpoint: lệnh kỹ thuật ở trên đã đủ; Sếp chỉ xác nhận M3 nhận việc này trong tuần.

### 2.3 QĐ-3 — psid_hash cross-module pepper (C7)

**Anh Mạnh ký (phương án b):**
> M6 không join dữ liệu theo `psid_hash` với M5/M3/M7. Khóa join xuyên module là `live_session_id`, `comment_id`, `messenger_thread_id` (và `attribution_id` khi M3 phát). `psid_hash` của M6 chỉ dùng nội bộ M6 (pepper M6 riêng, `identity/psid_hash.py:9-10`). Ghi vào registry PII policy của M6.

**Nếu sau này cần phương án (a)** (shared pepper toàn hệ qua `secret_ref`, M5 own, M6 đọc): phải trình Sếp + pháp chế vì tăng khả năng tái định danh xuyên module; khi đó dữ liệu psid_hash cũ của M6 phải re-hash hoặc bỏ.

## 3. Ký

- QĐ-1 phần kỹ thuật (adopt enum, fail-closed, chưa mở trường nào): Ký: Nguyễn Đức Mạnh — ngày ____/09/2026
- QĐ-1 (a) danh sách trường + (b) cách hash: Trình Sếp + pháp chế — Ký (Sếp): ______________________ ngày ____/09/2026
- QĐ-2 lệnh kỹ thuật ENTRY-003 (2 cột, enum OD-003, V221) + change-feed endpoint: Ký: Nguyễn Đức Mạnh — ngày ____/09/2026
- QĐ-2 (a) nhánh canonical = PhucApu + hòa dev V190/V191: Trình Sếp/Owner — Ký: ______________________ ngày ____/09/2026 (hoặc Tech Lead ký nếu có ủy quyền: căn cứ ______________)
- QĐ-3 phương án (b) không join theo psid: Ký: Nguyễn Đức Mạnh — ngày ____/09/2026

## 4. Việc kế tiếp sau khi ký (ai làm gì)

- Chief: cấp bản này vào `M6/_SPEC` và `M3/_SPEC`; sửa câu "registry canonical = V56" trong tài liệu chief thành câu ở mục 1.2; phát hành tên tạm `event-registry-feed.v1` và ghi ma trận seam S6b/E-M6-003.
- PM M6: tạo row register trỏ về E-M6-003; ghi QĐ-3(b) vào registry PII policy; giữ `permits_external_send()` trả False tới khi Sếp ký QĐ-1 (a)(b).
- Phúc (M3): đánh số lại V207 governance → V221, enum 4 giá trị, commit + push; dựng endpoint registry version/change-feed theo tên tạm.
- Sếp/pháp chế: QĐ-1 (a)(b) và QĐ-2 (a).
