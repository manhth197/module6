# VĂN BẢN CHẤP NHẬN RỦI RO — GAP MODULE 3 (đính kèm M6-ENTRY-001)

- **Ngày:** 2026-07-22
- **Người chấp nhận:** Nguyễn Đức Mạnh — Owner chương trình / chủ doanh nghiệp (Ginsengfood)
- **Quyết định:** CHO PHÉP slice **M6.2A** đi tiếp trên bằng chứng tầng-code của M6-ENTRY-001; **CHẤP NHẬN 4 gap M3** dưới đây; **rủi ro thuộc owner**.
- **KHÔNG thay đổi nội dung kỹ thuật** của M6-ENTRY-001: vẫn `overall=PARTIAL`, 4 `open_blocker` giữ nguyên. Đây là quyết định **quản trị chồng lên trên** bằng chứng, không sửa bằng chứng.

## Bối cảnh
M6-ENTRY-001 (bằng chứng P3/Commerce cho M6.2A) do Tech Lead nộp, trích verbatim code M3 @ `f90152d2`, đã verify+refute 8 agent. Kết quả trung thực: 4 assertion PARTIAL; owner M3 (Phúc) chưa xác nhận độc lập. Owner M3 chậm → owner chương trình quyết proceed để không chặn tiến độ đo lường. Đây KHÔNG phải phủ nhận gap — mà là chấp nhận có kiểm soát.

## 4 GAP M3 ĐƯỢC CHẤP NHẬN (ghi rõ, không giấu)
1. **NO_RUNTIME_PROOF** — chưa có integration/e2e đẩy 1 order thật tới ORDER_VERIFIED; test toàn mock/static.
2. **FAIL_OPEN_RECALL (cỡ-BLOCKER)** — `SellableGateAdminServiceImpl:805`: khi WMS snapshot null → bỏ qua recall/sale_lock/quality_hold → SKU đang thu hồi vẫn resolve SELLABLE (test xác nhận). **Rủi ro:** đơn cho SKU đang thu hồi có thể lọt và về sau bị tính vào verified revenue.
3. **PREPAID→VERIFIED_NO_E2E** — prepaid chỉ e2e tới PAID, không tới VERIFIED.
4. **QUOTESNAPSHOT_PRODUCER_MISSING** — không producer nào ghi quote_snapshot → revenue `pricing_breakdown` luôn false, discount NULL (hỏng hiển thị tách giảm giá; **không** sai amount tổng).

## ĐIỀU KIỆN KÈM THEO (để chấp nhận này AN TOÀN)
1. Chấp nhận **CHỈ để mở M6.2A** (nền móng đo lường, staged). `global_gateway_state=BLOCKED`, `production_flag=OFF` **giữ nguyên** — không đồng tiền thật nào chạy qua đường này.
2. **KHÔNG đóng** defect M3. M6-ENTRY-001 vẫn PARTIAL; 4 gap vẫn mở.
3. **RE-GATE BẮT BUỘC tại M6.2G Scale Gate.** Theo `ENTRY_EVIDENCE_REGISTER`, M6-ENTRY-001 được kiểm lại ở Scale Gate. **Trước KHI scale thật**, M3 owner (Phúc) PHẢI: (a) fix fail-open recall, (b) thêm ≥1 e2e order→VERIFIED, (c) ký xác nhận owner. Thiếu → Scale Gate chặn. ⇒ **rủi ro fail-open không thể lọt ra production** dù M6.2A đã mở.
4. Owner giao Phúc remediate 4 gap; theo dõi tới mốc Scale Gate.

## PHẠM VI (đọc kỹ)
Văn bản này mở **đúng một cửa**: xây M6.2A (đo lường) với production khoá. Nó **KHÔNG** là chấp nhận cho production, cho scale, hay cho việc để đơn SKU-thu-hồi thành doanh thu thật. Mọi thứ đó vẫn bị chặn bởi `production_flag=OFF` và Scale Gate.

## CHỮ KÝ
- **Owner chương trình:** Nguyễn Đức Mạnh — 2026-07-22
- **Cam kết:** "Tôi chấp nhận 4 gap M3 nêu trên, rủi ro thuộc tôi, cho M6.2A đi tiếp trên bằng chứng tầng-code; production/scale giữ BLOCKED/OFF tới khi M3 được fix và re-gate tại M6.2G."
- *(Ghi theo chỉ đạo trực tiếp của owner trong phiên 2026-07-22; owner rà lại câu chữ trước khi coi là bản cuối.)*
