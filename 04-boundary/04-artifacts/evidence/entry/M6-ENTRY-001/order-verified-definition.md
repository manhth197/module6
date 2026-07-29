# ASSERT-001 — ORDER_VERIFIED có định nghĩa chính thức

- **Nguồn:** Module 3 Commerce Runtime, repo `PhucApu/ginsengfood-business-platform` @ commit **f90152d2** (nhánh `PhucApu`, nhánh cá nhân CHƯA merge vào `dev`).
- **Grade sau verify + refute đối kháng:** 🟠 **PARTIAL** (verify chấm PROVEN → refute HẠ xuống PARTIAL).
- **Người trích:** AI assistant (chỉ đọc code, KHÔNG ký thay owner). `supplied_by` chờ Commerce/M3 owner xác nhận.

## Claim (thu hẹp đúng thứ code chứng minh được)
ORDER_VERIFIED có định nghĩa **chính thức, DB-authoritative, fail-closed** ở tầng CODE: điều kiện chuyển trạng thái được mã hoá cứng, có DB CHECK constraint, có seeded policy, có RBAC gate, và được đánh dấu là nguồn doanh thu thật cho Ads.

## Artifact thật (file:line @ f90152d2)

**1. `back-end/.../order/domain/enums/OrderCheckpoint.java:14-25`** — enum checkpoint; ORDER_VERIFIED tách biệt ORDER_SUCCESS/PAID.
```java
public enum OrderCheckpoint {
    ORDER_SUCCESS,
    ORDER_VERIFIED;
    /** Guard: chỉ ORDER_VERIFIED cho phép mở post-purchase lifecycle. */
    public boolean opensPostPurchaseLifecycle() { return this == ORDER_VERIFIED; }
}
```

**2. `back-end/.../order/service/impl/OrderVerificationCheckpointServiceImpl.java:235-285,497-502`** — guard chuyển trạng thái, fail-closed:
```java
if (!"DELIVERED".equals(order.orderStatus()) || !"PAID".equals(order.paymentStatus()))
    throw new AppException(UNPROCESSABLE_ENTITY, "ORDER_VERIFIED requires order_status=DELIVERED and payment_status=PAID");
if (!order.hasRequiredSnapshotRefs()) { updateOrderVerificationState(...,"BLOCKED",...); throw ...MISSING_SNAPSHOT_REFS; }
if (isBlocked(order)) { insertCheckpoint(order,"SKIPPED","BLOCKED",...); } // no event
// isBlocked: riskBlocked = !(CLEAR||OVERRIDE_APPROVED); afterSalesBlocked = !CLEAR
```

**3. `back-end/.../order/api/OrderTransitionController.java:105-117`** — endpoint + RBAC `ORDER.VERIFY`:
```java
private static final String PERM_VERIFY = "ORDER.VERIFY";
@PostMapping("/{id}/verification/verified")
public ... markVerified(@PathVariable Long id, Authentication auth) {
    requirePermission(requireActorId(auth), PERM_VERIFY);
    ... verificationCheckpointService.markVerified(id, actorId);
}
```

**4. `back-end/.../resources/db/migration/V56__p3_07_order_verification_commission_eligibility.sql`** — DB CHECK pin state set + policy + event_registry:
```sql
ADD CONSTRAINT chk_orders_verification_status CHECK (verification_status IN ('PENDING','VERIFIED','REVOKED','BLOCKED'))
-- policy: requires_delivered/requires_paid/requires_order_snapshot_id = true;
--   risk_status_allowlist ['CLEAR','OVERRIDE_APPROVED']; after_sales_block_allowlist ['CLEAR']
-- event_registry ORDER_VERIFIED: is_ads_conversion=TRUE, 'revenue truth source'  <-- ranh giới M6/Ads
```

**5. `back-end/.../seed/RbacDataSeeder.java:331-332`** — permission `ORDER.VERIFY` seeded thật.

## Chứng minh được
Định nghĩa ORDER_VERIFIED tồn tại thật, nhất quán ở tầng DB: DB CHECK + seeded policy (DELIVERED+PAID+snapshot+risk/after-sales) + guard fail-closed + RBAC + cờ `is_ads_conversion=TRUE` = nguồn doanh thu thật M6 phải đọc.

## KHÔNG chứng minh được (khai báo trung thực — fail-closed)
- **0 runtime proof:** mọi test là Mockito/`@WebMvcTest`/static; test Postgres duy nhất **seed thẳng** `verification_status='VERIFIED'`, KHÔNG chạy producer. Không có Testcontainers test đẩy 1 order thật tới VERIFIED + bắn event.
- **Dead code:** `OrderCheckpoint.opensPostPurchaseLifecycle()` **0 call site** (grep toàn repo) — định nghĩa "canonical" thật nằm ở DB policy/guard, không ở method này.
- **Drift định nghĩa:** javadoc + `VerificationStatus.canOpenPostPurchaseLifecycle()` coi verified = `VERIFIED || TRUSTED` (javadoc còn bỏ điều kiện DELIVERED), nhưng DB CHECK **cấm lưu TRUSTED** → nhánh TRUSTED unreachable; định nghĩa chưa đơn nhất/nhất quán giữa các nguồn.
- **Legacy mislabel:** `markVerified()` trả `OrderDetailResponse.from(order, ORDER_VERIFIED)` **vô điều kiện**; đơn risk-held/blocked vẫn bị dán nhãn ORDER_VERIFIED ở HTTP response dù `verification_status=BLOCKED` và KHÔNG có event (boundary event/revenue vẫn nguyên, nhưng nhãn response sai).
