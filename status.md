# STATUS — Module 6 (Đo lường Quảng cáo / Attribution / ROAS)

**Cập nhật:** 2026-09-03
**Khoá an toàn (chủ ý, KHÔNG phải lỗi):** `production_flag = OFF` · `global_gateway_state = BLOCKED` · `external_send = OFF` — pack là công trình **dựng + thẩm định bằng chứng**, **chưa bật production**. Các cờ này bất biến với mọi role.

> Đọc `_AI_CHECK_GUIDE.md` ở gốc repo để **tự kiểm độc lập** từng mục dưới — kể cả để **tái hiện phần debt** ở §4.

## 1. Toàn pack đã build xong (end-to-end) + fix-slice M6.2L

Ledger `04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv`: **208 prompt đều terminal** — **178 PASS + 27 SIGNED + 3 SKIPPED**. Không còn prompt nào TODO/RUNNING/BLOCKED.

| Giai đoạn | Prompt | Trạng thái |
|---|---|---|
| BOOTSTRAP · DOC_LOCK · PHASE0 · HARMONIZATION | 76 | PASS |
| M6.2A → M6.2K (11 slice build) | 110 | PASS/SIGNED (mỗi slice có JUDGE_GATE SIGNED) |
| PR_PILOT (pilot production-OFF) | 12 | PASS/SIGNED — M6-P3011 SIGNED |
| **M6.2L (fix-slice post-pilot, M6-P2100-2109)** | 10 | PASS/SIGNED — judge M6-P2109 SIGNED |

**3 SKIPPED là minh bạch, KHÔNG phải PASS giả:** `M6-P1000` (M6.2A), `M6-P1306` + `M6-P1309` (M6.2D) — override transparent, judge verdict giữ **BLOCKED**, có decision file; cũng là *standing blocker* mà evidence-pack M6.2K disclose thẳng.

## 2. Scale Gate M6.2G đã mở (đúng quy trình, không override)

`M6-P1600` (M6.2G Scale Gate) = **SIGNED** bằng phiên Judge tươi trên bằng chứng entry thật — **không owner override**, không bỏ bước. 4 entry-evidence proven/judged bốn-mắt:

| Entry | Trạng thái | Ghi chú |
|---|---|---|
| ENTRY-001 (verified revenue chỉ từ `ORDER_VERIFIED`) | **PROVEN** + owner M3 ký | runtime proof (surefire XML) sha256 khớp; adversary không phá được ranh giới doanh thu |
| ENTRY-002 (channel identity M5) | **clean** | |
| ENTRY-003 (event governance fail-closed) | **PROVEN** | V190 schema + V191 classify + enforce trên `origin/dev`; residual owner-runtime create (đúng posture OFF) |
| ENTRY-004 (M4+M5) | M4 **PROVEN** · M5 **PARTIAL — risk-accepted (RATIFIED)** | M4 `safetyBoundary` fix @9f7e3dc8; M5 PARTIAL cho pilot OFF |

## 3. Pack readiness = OWNER_REVIEW_REQUIRED (không tự phong Pass/Scale-Ready)

Enum `Readiness` **không có member Pass/Ready/Scale-Ready** — trần cấu trúc là `OWNER_REVIEW_REQUIRED`; pack **không thể tự tuyên bố** "ROAS Pass" / "Scale Ready" (owner-only, doc §23). 8 *standing blocker* luôn disclose kể cả khi pack đầy đủ.

## 4. M6.2L đã đóng nợ evidence-assembler + doanh-thu-lock — verify độc lập

Audit chief-auditor @5f09894 nêu 5 lỗi M6 tự đóng được → dựng **fix-slice gated M6.2L**, chạy trọn loop, judge SIGNED, và **re-judge độc lập (soi code M6.2L vs M6.2K từng dòng) xác nhận 5/5 REAL**:
- **B2 forgery ĐÓNG THẬT:** `pack_assembler` thêm uniqueness đếm pack-wide + binding (category,key) → 1 ref copy-paste cả 10 category = mọi category MISSING (không phải fix hẹp cũ).
- **B3 collision ĐÓNG THẬT:** floor `standing_floor_ok` = mỗi standing-id đúng 1 lần + pin (kind,description) → dup/shadow M6-P1000/M6-P1309 = FAIL (không còn set-subset).
- **B4 ROAS-lock:** `verified_rows()` lọc `event_code==ORDER_VERIFIED` + `materialize()` tự kiểm event_code (bỏ boolean caller) + choke thứ 3 (growth). QUOTE_SENT+verified=True → Revenue=0/ROAS=0.
- **A3** attribution_id thành khóa trace first-class; **A4** intake nhận đủ campaign/adset/ad/live_session → resolver HIGH.

**Nợ forward còn mở (ghi thẳng — KHÔNG phải rủi ro production; cờ vẫn OFF/BLOCKED):**
- **(a) M5 runtime controls trước real external send** (ENTRY-004 DEBT-1..4): allowlist template, dedup cross-instance, send-rate, real Graph sink — điều kiện cứng trước post công khai thật; owner đã risk-accept cho pilot OFF (`M6-ENTRY-004/_OWNER_RISK_ACCEPTANCE.md`).
- **(b) M6-OD-013 — authenticity của evidence pack** (code-exec-only, cap `OWNER_REVIEW_REQUIRED`, đóng trước real owner sign-off): B2 mới chứng minh *slot-correctness* chưa *authenticity* — (i) ref-side: kẻ dựng lại đúng chuỗi canonical `ev::{cat}::{key}` riêng từng slot vẫn lọt (oracle `known_refs` đã code seam); (ii) smoke-side: `models.py` `SmokeResult.recorded` còn dùng raw truthiness (`bool(status) and ...`) — cùng lớp, doc đòi "vá cả hai một lượt" nhưng M6.2L mới vá ref-side. Cả hai gộp vào M6-OD-013.
- **M6-OD-014** (gap-id collision floor): code-side **đã đóng** bởi B3; owner còn review canon standing-blocker.

## 5. Điểm trung thực (dấu hiệu tốt)
- Mọi dossier liệt kê `open_blockers`/residual thẳng, không tô hồng.
- Override đều transparent: judge giữ BLOCKED, ledger SKIPPED (không PASS), có decision file.
- Lỗ evidence-assembler từng bị judge M6.2K **ký đè bằng fix hẹp** → được nêu thẳng, dựng slice fix M6.2L đóng thật, rồi re-verify độc lập. Residual còn lại (§4b) khai rõ, không giấu.
- **Finding pre-existing (không do M6.2L):** `validate_input_consumption` báo 33 mục "declared but not consumed" khắp M6.2A-K (role session khai `RequiredInputs` nhưng không ghi vào `files_read`, đa số `IMPLEMENTATION_TARGET_LOCKED` cho tester / brief cho judge). Nghĩa là full validator suite chưa từng xanh post-execution (operator chỉ chạy per-prompt gate). Đây là evidence-hygiene, không phải sai correctness; **không** được "làm xanh" bằng cách sửa evidence.

**Một câu:** pack build xong end-to-end + fix-slice M6.2L đóng thật nợ forgery/collision/ROAS-lock (verify độc lập 5/5 REAL), production vẫn OFF; residual còn lại = M5 runtime + M6-OD-013 authenticity (code-exec-only) — ghi thẳng, đóng trước khi chạm endpoint thật.
