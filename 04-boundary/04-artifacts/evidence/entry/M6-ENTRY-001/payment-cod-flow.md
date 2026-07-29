# ASSERT-002 — Luồng Payment/COD/Order-Verified chạy đúng end-to-end (prepaid + COD)

- **Nguồn:** Module 3 @ f90152d2 (nhánh `PhucApu`, chưa merge).
- **Grade sau verify + refute:** 🟠 **PARTIAL** (verify PARTIAL → refute CONFIRMED PARTIAL; hostile read KHÔNG tìm thấy lỗi correctness để hạ xuống GAP).
- Người trích: AI (chỉ đọc code). `supplied_by` chờ owner M3.

## Claim (thu hẹp đúng thứ chứng minh được)
Cả prepaid (VNPAY HMAC thật) và COD (IVR→CONFIRMED, proof→PAID) đều **được cài thật, tách bạch**, và hội tụ về **một gate ORDER_VERIFIED fail-closed** (DELIVERED+PAID). Không có mock/stub/TODO trên critical path.

## Artifact thật (file:line @ f90152d2)

**1. `order/service/impl/VnpayGatewayAdapter.java:126-150`** — HMAC-SHA512 **thật**, không stub:
```java
public boolean verifyResponse(Map<String,String> params) {
    String secureHash = params.get("vnp_SecureHash");
    if (secureHash == null || secureHash.isBlank()) return false;
    ... return secureHash.equalsIgnoreCase(sign(signedParams)); // Mac HmacSHA512
}
```

**2. `order/service/impl/DevMockPaymentWebhookVerifier.java:33-50`** — mock verifier fail-closed, **loại trừ VNPAY** (prepaid luôn dùng verifier thật):
```java
@ConditionalOnProperty(name="payment.mock.enabled", havingValue="true", matchIfMissing=false)
public boolean supports(String providerCode) { return !VnpayGatewayAdapter.PROVIDER_CODE.equalsIgnoreCase(providerCode); }
```

**3. `order/service/impl/OrderStateMachineImpl.java:70-87,139-161`** — prepaid vs COD tách bạch:
```java
applyOnlinePaymentSuccess: rejectIfNot(order, CONFIRMING); order.setOrderStatus(CONFIRMED); order.setPaymentStatus(PAID); order.setPaidAt(now);
applyIvrConfirm: if (paymentMethodSnapshot != COD) throw 422; // IVR confirm -> CONFIRMED, KHÔNG PAID
```

**4. `order/service/impl/CodReconciliationServiceImpl.java:232-237`** — COD chỉ PAID sau khi có proof thu tiền.

**5. `order/service/impl/OrderVerificationCheckpointServiceImpl.java:242-245`** — gate ORDER_VERIFIED method-agnostic, fail-closed DELIVERED+PAID.

## Chứng minh được
Parser webhook là thật; COD/prepaid tách bạch; gate verified fail-closed trên MỌI path (kể cả legacy markVerified và override — override chỉ đổi idempotency/metadata, không đổi gate). E2e COD full-chain create→confirm→deliver→pay→VERIFIED có viết, gọi **endpoint admin thật** (`affiliate-invite-link.real.spec.ts` → `POST /api/v1/admin/orders/{id}/verification/checkpoints`).

## KHÔNG chứng minh được (fail-closed)
- **0 bằng chứng chạy thật ở f90152d2:** report e2e committed (`front-end/playwright-report-real/index.html`) giải nén ra **đúng 1 test** — `sellable-gate-last-unit.real.spec.ts` — KHÔNG có test payment/COD/verified nào. Runtime proof cho ASSERT-002 **vắng mặt hẳn**, không phải "mờ".
- **prepaid→VERIFIED = 0 e2e:** `vnpay-provider.real.spec.ts` dừng ở `paymentStatus=PAID`, không đi tiếp DELIVERED/VERIFIED, lại triple env-gated (`VNPAY_PROVIDER_E2E_ENABLED` + public HTTPS IPN + hash secret). `order.real.spec.ts` prepaid chỉ mở trang `/payment/result?vnp_ResponseCode=00`, KHÔNG POST IPN thật → chưa tới cả PAID.
- **Cả package `order` không có integration test:** không `@SpringBootTest`/`@DataJpaTest`/Testcontainers; mọi test là Mockito/`@WebMvcTest` (DB, PaymentStateService, OrderStateMachine, verification repo đều mock). Chuỗi webhook→state→statemachine→verified chưa bao giờ wired với DB thật.
- Test "acceptance" Java (`Phase3OrderPaymentRefundAcceptanceTest`) là **string-grep** đọc source test khác + assert tồn tại tên method — không chạy flow.
- Một số assertion "VERIFIED" trong e2e cưỡi lên **state terminal seed thẳng** (`GuestCheckoutMembershipRealE2eDataSeeder.java:737-768` ghi raw SQL DELIVERED/PAID/VERIFIED/COLLECTED).
