# ASSERT-004 — Verified Revenue chỉ tính từ ORDER_VERIFIED

- **Nguồn:** Module 3 @ f90152d2 (nhánh `PhucApu`, chưa merge).
- **Grade sau verify + refute:** 🟠 **PARTIAL** (verify PARTIAL → refute CONFIRMED PARTIAL; hostile read KHÔNG hạ được xuống GAP — mọi lệch đều nghiêng về UNDER-count, không có rò tiền chưa verified).
- Người trích: AI (chỉ đọc code). `supplied_by` chờ owner M3.

## Claim
Doanh thu verified được cộng **chỉ** từ order `VERIFIED + DELIVERED + PAID + verified_at IS NOT NULL` — không bao giờ từ quote/draft/order chưa verified. Bộ lọc còn **chặt hơn** cả checkpoint ORDER_VERIFIED.

## Artifact thật (file:line @ f90152d2)

**1. `report/repository/AdminRevenueReportJdbcRepository.java:447-455`** — bộ lọc doanh thu (lặp lại y hệt ở CTE detail 577-582, SKU 113-118, invoice 360-365):
```sql
WHERE o.verified_at IS NOT NULL
  AND o.verification_status = 'VERIFIED'
  AND o.order_status = 'DELIVERED'
  AND o.payment_status IN ('PAID','PARTIALLY_REFUNDED')
  AND o.program_type IN ('24_7','GOLDEN_HOUR')
```
Quote/draft ở bảng riêng, report KHÔNG bao giờ đụng.

**2. `AdminRevenueReportJdbcRepository.java:386-402`** — pricing_breakdown lấy từ LEFT JOIN `quote_snapshot_items`; miss join → discount NULL, `pricing_breakdown_available=false`.

**3. `resources/db/migration/V110__...sql:245-246`** — cột linkage `order_items.quote_snapshot_item_id` **tạo nhưng KHÔNG producer nào ghi** (grep toàn `back-end/src/main`: chỉ migration + report reader tham chiếu).

**4. `report/service/impl/AdminRevenueReportServiceImpl.java:270-274`** — degrade trung thực: không snapshot → `pricingBreakdownAvailable=false` + note "không tự suy luận số giảm giá".

**5. Product Analytics (surface M6 hay dùng hơn):** `ProductAnalyticsJdbcRepository.java:589-595` + `OrderLifecycleEventListener.java:44-51` — `verified_revenue_amount` chỉ tăng bởi `AggregateDelta.verified()` bắn từ checkpoint ORDER_VERIFIED; path ORDER_SUCCESS/PAID mang `verifiedRevenueAmount=ZERO`.

## Chứng minh được
Không có code path nào cộng quote/draft/order chưa verified vào doanh thu. Cả 2 surface (AdminRevenueReport + ProductAnalytics) đều strict-gated. Amount thật (`order_items.line_total` NOT NULL, khác cột `quote_snapshot_item_id` phantom). Mọi sai lệch nghiêng UNDER-count, không over-count.

## KHÔNG chứng minh được (fail-closed)
- **0 test loại-trừ-theo-amount runtime:** test Postgres thật duy nhất chỉ đụng gián tiếp `verified_at IS NOT NULL` (seed order verified_at=NULL, assert businessDate non-null); không cover status≠VERIFIED / TRUSTED-only / verified-nhưng-chưa-DELIVERED / quote-draft, không assert amount bị loại. Các assert "verified filter" mạnh nhất là **string SQL trên jdbcTemplate mock**.
- **Semantic subset:** checkpoint coi verified = `VERIFIED||TRUSTED` nhưng report chỉ đếm `VERIFIED` + đòi DELIVERED+PAID → "chỉ từ ORDER_VERIFIED" thực ra là "từ **tập con chặt** của ORDER_VERIFIED" (bảo thủ, không over-count; và TRUSTED không có producer nên tập loại ra rỗng trên thực tế).
- **Degradation LIVE đã xác nhận:** thiếu QuoteSnapshot producer → `pricing_breakdown_available` **luôn false**, discount program/member **luôn NULL** → Finance chưa đối soát được tách giảm giá. (Chỉ hỏng **hiển thị breakdown**; KHÔNG ảnh hưởng amount tổng gross/VAT/net hay gate verified.)
