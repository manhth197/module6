# _OWNER_RISK_ACCEPTANCE (NHÁP) — M6-ENTRY-004, phần M5 / Gateway

> **Trạng thái: DRAFT** — do M5 Evidence Author soạn để Owner cân nhắc ký. **Chưa có hiệu lực tới khi Owner ratify.**
> **Entry:** M6-ENTRY-004 · **Module:** M5 (Facebook Gateway) · **Ngày soạn:** 01/08/2026 · Mẫu theo ENTRY-003.

## 1. Điều được risk-accept
3 assertion M5 của M6-ENTRY-004 đạt **PARTIAL (KHÔNG PROVEN)** — chấp nhận rủi ro ở mức PARTIAL này **CHỈ cho PILOT**, KHÔNG cho bật egress công khai thật:
- **ASSERT-004** (không public giá cuối) — PARTIAL.
- **ASSERT-005** (không leak PII) — PARTIAL.
- **ASSERT-006** (chống spam) — PARTIAL (có gap cấu trúc thật: dedup per-instance; rate-limit outbound chỉ đọc Meta throttle).

## 2. Vì sao risk-accept được cho pilot (các chốt chặn phải CÒN NGUYÊN)
- **External-send OFF (P4 chưa bật):** real Graph sink là **stub ném lỗi** — `feat@0f7923e src/outbound-guard/adapters/real/graph-post-comment-sink.ts:22` (`GRAPH_POST_COMMENT_SINK_NOT_IMPLEMENTED_P4`); default sink = MOCK. ⇒ **không post gì ra Meta thật.**
- **Production OFF (hard-locked):** `main@87fad53 src/foundation/feature-flag/feature-flag.service.ts:17` `PRODUCTION_ENABLED = false` (static, không set qua env) + `GLOBAL_GATEWAY` BLOCKED. DEV-12 self-gate (`dispatcher:314`) từ chối REAL sink khi production OFF.
- **Chưa merge:** đường public (spotlight) chỉ ở nhánh `feat/live-spotlight-endpoint@0f7923e` — **CHƯA merge, CHƯA push**. Canonical `main@87fad53` **không có public egress**.
⇒ Trong khung này, "không rò giá/PII/spam ra kênh công khai" là đúng theo nghĩa **chưa có đường công khai nào hoạt động**; guard-chặn-trước-gửi đã chứng minh với MOCK sink.

## 3. Điều KHÔNG được risk-accept (ranh giới cứng)
- KHÔNG chấp nhận **PROVEN/PASS** — trần là PARTIAL.
- KHÔNG chấp nhận **bật P4 / real posting / production ON** dựa trên memo này.
- KHÔNG chấp nhận merge/push nhánh spotlight khi 4 blocker chưa đóng.

## 4. Điều kiện BẮT BUỘC trước khi bật egress công khai thật (P4) — đóng 4 blocker
1. **DEBT-1:** ODR-002 §4 default-deny TEMPLATE/allowlist owner-duyệt cho card text (đóng 004 + 005). *(Đang PARK — owner + M7.)*
2. **DEBT-2:** dedup store **persistent/cross-instance**.
3. **DEBT-3:** bộ đếm send-rate outbound do M5 tự áp trên đường public, HOẶC document rõ + risk-accept riêng.
4. **DEBT-4:** hiện thực real Graph sink (P4).
- **RE-GATE M6.2G BẮT BUỘC:** sau khi 4 blocker đóng, phải re-run Scale Gate M6.2G + adversarial trên build P4 (assert posted==scanned, structural A/B/C/D) TRƯỚC khi cho phép real posting. Guard-rail đảo-thứ-tự đã có: `feat@0f7923e test/outbound-guard/spotlight-a1-tripwire.probe.ts`.

## 5. Phạm vi pilot chấp nhận
- Pilot **external-send OFF**, **production OFF**, `GLOBAL_GATEWAY` BLOCKED. Không có post công khai thật ra Meta.

## 6. Ký (chờ Owner)
- **Owner (M5 / Gateway):** Nguyễn Đức Mạnh — [ ] chấp nhận rủi ro PARTIAL cho pilot theo điều kiện trên · Ngày: ______
- **Ghi chú:** memo này chỉ có hiệu lực khi Owner ký; joint dossier M6-ENTRY-004 còn cần nửa M4 (AI Advisor). Thiếu 1 bên hoặc còn open_blocker ⇒ M6.2G BLOCKED (trung thực).
