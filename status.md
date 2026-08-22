# STATUS — Module 6 (Đo lường Quảng cáo / Attribution / ROAS)

**Cập nhật:** 2026-08-11
**Khoá an toàn (chủ ý, KHÔNG phải lỗi):** `production_flag = OFF` · `global_gateway_state = BLOCKED` — pack đang ở giai đoạn dựng + thẩm định bằng chứng, **chưa bật production**.
**Cổng hiện tại:** M6.2G Scale Gate (`M6-P1600`) — **BLOCKED** (fail-closed, chờ đủ bằng chứng entry). Đây là gate đang chờ, **không phải PASS giả**.

> Đọc `_AI_CHECK_GUIDE.md` ở gốc repo để biết cách **tự kiểm độc lập** từng mục dưới đây.

## Bằng chứng entry (điều kiện vào Scale Gate)

| Entry | Nội dung | Trạng thái | File bằng chứng |
|---|---|---|---|
| **ENTRY-001** | Verified revenue — doanh thu chỉ đếm từ `ORDER_VERIFIED`, fail-closed | ✅ **PROVEN** (judge độc lập + đối kháng) · chờ chữ ký owner M3 | `04-artifacts/evidence/entry/M6-ENTRY-001.json` + `M6-ENTRY-001/_REJUDGE_VERDICT_2026-08-11.json` + surefire XML (sha256 khớp) |
| **ENTRY-002** | Channel identity (M5 Gateway) | ✅ clean | `04-artifacts/evidence/entry/M6-ENTRY-002.json` |
| **ENTRY-003** | Event governance (event_registry: external_send / data_sensitivity / channel) | 🔴 **đang build** (schema + reseed + enforce) | (spec ở repo mã nguồn, chưa nộp) |
| **ENTRY-004** | M4 + M5: không public giá cuối / không leak PII / không spam ra kênh công khai | 🟡 **cả 2 nửa đã judge độc lập**; nửa M4 = **ACCEPTED_PARTIAL** + 1 defect ghi thẳng (`safetyBoundary` chưa được PII guard quét) | `04-artifacts/evidence/entry/M6-ENTRY-004.json` + `M6-ENTRY-004/_M4_JUDGE_VERDICT_2026-08-11.json` |
| DEFER-FBC | Consent fail-open (F-A…F-F) | ✅ đã đóng + nộp | `04-artifacts/evidence/decisions/M6-DEFER-FBC-M6.2D.json` |

## Đã thẩm định thế nào (không tự chấm)
- **Bốn-mắt:** author ≠ adversary ≠ judge; mọi verdict pin theo **commit SHA** repo mã nguồn (`a3aad246`, `97cc82bc`).
- **ENTRY-001:** test tích hợp thật (Testcontainers PostgreSQL) chạy **xanh**, surefire XML + **sha256 khớp** (tự tính lại mà kiểm); adversary cố phá ranh giới doanh thu → **không phá được**.
- **ENTRY-004 (M4):** ASSERT-001 (giá) + ASSERT-003 (spam) **PROVEN**; ASSERT-002 (PII) **PARTIAL** + đối kháng tìm ra lỗ `safetyBoundary` — **ghi thẳng, chưa che**.

## Còn lại để mở M6.2G
1. **Phúc (M3):** ký owner ENTRY-001 + build ENTRY-003 (3 lớp).
2. **Tài (M4):** fix `safetyBoundary` + ký owner M4.
3. **Re-run `M6-P1600`** khi bằng chứng đủ — **không override, không bỏ qua bước nào**.

## Điểm trung thực (dấu hiệu tốt)
- Mọi dossier liệt kê `open_blockers` thẳng, không tô hồng.
- Override (nếu có) đều transparent: judge giữ BLOCKED, ledger ghi SKIPPED (không PASS), có decision file.
- Lỗi (`safetyBoundary`) được ghi vào verdict, **không giấu**.

**Một câu:** bằng chứng thật · thẩm định thật · lỗi ghi thẳng · không có gì làm giả · production vẫn OFF.
