# ASSERT-003 — Không tạo order khi chưa xác nhận; tạo sớm bị chặn

- **Nguồn:** Module 3 @ f90152d2 (nhánh `PhucApu`, chưa merge).
- **Grade sau verify + refute:** 🟠 **PARTIAL** (verify PARTIAL → refute CONFIRMED PARTIAL).
- Người trích: AI (chỉ đọc code). `supplied_by` chờ owner M3.

## Claim (nêu ĐÚNG cả phần đúng lẫn phần sai literal)
KHÔNG có order **CONFIRMED/PAID/VERIFIED** (revenue-bearing) nào tồn tại trước khi qua transition confirm có gác — điều này **code-proven đa lớp**. NHƯNG câu chữ "không tạo order khi chưa xác nhận" **sai literal**: một row `CONFIRMING` VẪN được ghi trước khi khách xác nhận (không có state DRAFT).

## Artifact thật (file:line @ f90152d2)

**1. `order/service/impl/OrderCreateServiceImpl.java:515-546,872-878`** — order tạo thẳng ở `CONFIRMING` (không DRAFT); state log đầu `from=null → CONFIRMING "Order created"`.

**2. `order/domain/enums/OrderStatus.java:14-22`** — **không có DRAFT**; lifecycle bắt đầu `CONFIRMING`.

**3. `sellablegate/service/impl/SellableGateAdminServiceImpl.java:805-816`** — **NHÁNH FAIL-OPEN**:
```java
if (wms != null) { unknownBlocked = evaluateWms(wms, policy, resolvedAt, blockers) || unknownBlocked; }
// wms == null -> KHÔNG có blocker bù -> blockers rỗng -> SELLABLE_BASE
SellableGateBaseStatus baseStatus = unknownBlocked ? UNKNOWN_BLOCKED
        : blockers.isEmpty() ? SELLABLE_BASE : NOT_SELLABLE;
```

**4. `SellableGateAdminServiceImpl.java:931-939,1303-1311`** — recall/sale_lock/quality_hold **chỉ** nằm trong `evaluateWms` (unreachable khi `wms==null`); `isClearHold(null)` trả CLEAR (fail-open thứ 2 khi field null).

**5. `test/.../SellableGateAdminServiceImplTest.java:97-116`** — test đang PASS **chứng minh fail-open**: WMS `Optional.empty` + catalog fresh → `SELLABLE_BASE`, blockers rỗng.

## Chứng minh được
- Không có DRAFT; chỉ 1 constructor order, luôn `CONFIRMING`.
- `CONFIRMED` chỉ được ghi bởi transition có gác `applyOnlinePaymentSuccess`/`applyIvrConfirm` (đều `rejectIfNot(CONFIRMING)`); `ORDER_VERIFIED` đòi DELIVERED+PAID. → không order nào tới trạng thái revenue-bearing/official mà không qua confirm tường minh. Đây là phần boundary M6 cần, và nó **sống sót hostile read**.
- Fail-open recall **tồn tại thật** (test xác nhận).

## KHÔNG chứng minh được (fail-closed)
- Claim **sai literal**: row `CONFIRMING` persisted trước confirm.
- Phần "tạo sớm bị chặn" **không kín**: (a) gate tạo 24/7 đọc `resolve()` live, **fail-open khi WMS null** (recall/sale_lock/quality_hold bị bỏ; catalog-side fail-closed nhưng WMS-side fail-open); (b) path **Golden Hour bỏ hẳn gate lúc tạo** — chỉ check ở `reserve()` bằng cùng port fail-open, KHÔNG check lại lúc confirm/bind order.
- **0 runtime proof:** test reject order-create **mock** port trả NOT_SELLABLE; test real-logic duy nhất lại cho ra **fail-open** (ngược claim).
- Mức khai thác thật của fail-open phụ thuộc **giả định cross-module CHƯA verify** (SKU đang recall mà row WMS null) — không kiểm được từ repo Commerce một mình. → cần Owner+Phúc+Toàn chốt nguồn sellable (ops-core `availability-sellable.v1`).
