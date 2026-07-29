# Hướng B — Owner Risk Acceptance: 3 gap Core Event Governance (ENTRY-003)

- **ACCEPTED:** 2026-07-22 · **bởi:** Nguyễn Đức Mạnh — **M6 program/business owner** (người chịu rủi ro đường-tới-tiền của M6).
- **Phạm vi chấp nhận:** 5 `open_blocker` của `M6-ENTRY-003.json` (2 PARTIAL + 3 GAP), **CHỈ để mở slice M6.2A** trên bằng chứng tầng-code.
- **KHÔNG đóng gap:** ENTRY-003 vẫn PARTIAL/GAP; đây là quyết định QUẢN TRỊ đặt lên trên bằng chứng, không sửa bằng chứng. Không tự phong PASS (verdict thuộc Judge M6-P1000).

## Đóng khung an toàn (bắt buộc — chặt hơn M3 vì đây là control privacy)
1. **`production` BLOCKED/OFF, `GLOBAL_GATEWAY` BLOCKED** — không đổi.
2. **Chỉ mở M6.2A** (định nghĩa event/tracking framework, staged). KHÔNG mở gửi dữ liệu thật.
3. **Rào privacy cứng (vì thiếu `data_sensitivity` + `external_send_policy`):** trong pilot, M6 **KHÔNG được gửi bất kỳ event data nào ra ad platform ngoài** dựa trên registry hiện tại. External-send giữ **OFF** cho tới khi Hướng A land. (Registry mặc định coi mọi event = chưa-phân-loại = cấm gửi.)
4. **Chọn nguồn Core (giải quyết Hướng C):** chấp nhận này đồng thời **chốt `business-platform` event_registry là nguồn Core event-gov của M6** (thay vì ops-core/Module-2). Nếu sau này xác định sai nguồn → phải re-gate.
5. **RE-GATE bắt buộc ở M6.2G Scale Gate:** trước BẤT KỲ ads-scale thật / external-send nào, Core PHẢI hoàn thành **Hướng A** (`_CORE_FIX_SPEC.md`: thêm `attribution_channel` + `data_sensitivity` + `external_send_policy` + siết owner + seed) và ENTRY-003 phải trích lại **PROVEN** + ký owner thật. Không có A → M6.2G BLOCKED.

## Điều kiện ràng buộc (A + B đi cùng)
Chấp nhận B **có hiệu lực kèm cam kết Hướng A**. B là **cầu tạm** để M6.2A không kẹt; A là **fix thật** phải xong trước scale. B đứng một mình (không A) = **vô hiệu**.

## Rủi ro còn lại (ghi rõ, owner đã biết)
- M6.2A chạy trên registry chưa phân loại độ nhạy/chính sách gửi → nếu ai đó bật external-send sớm (trái rào #3) có thể gửi dữ liệu nhạy cảm ra ngoài. Rào #3 + prod OFF là lớp chặn; trách nhiệm enforce thuộc owner/ops.
- owner runtime có thể = UNASSIGNED cho event tạo qua Admin API tới khi A siết.
