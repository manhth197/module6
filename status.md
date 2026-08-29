# STATUS — Module 6 (Đo lường Quảng cáo / Attribution / ROAS)

**Cập nhật:** 2026-08-29
**Khoá an toàn (chủ ý, KHÔNG phải lỗi):** `production_flag = OFF` · `global_gateway_state = BLOCKED` · `external_send = OFF` — pack là công trình **dựng + thẩm định bằng chứng**, **chưa bật production**. Các cờ này bất biến với mọi role.

> Đọc `_AI_CHECK_GUIDE.md` ở gốc repo để **tự kiểm độc lập** từng mục dưới — kể cả để **tái hiện phần debt** nêu ở §4.

## 1. Toàn pack đã build xong (end-to-end)

Ledger `04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv`: **198 prompt đều terminal** — **170 PASS + 25 SIGNED + 3 SKIPPED**. Không còn prompt nào TODO/RUNNING/BLOCKED.

| Giai đoạn | Prompt | Trạng thái |
|---|---|---|
| BOOTSTRAP · DOC_LOCK · PHASE0 · HARMONIZATION | 76 | PASS |
| M6.2A → M6.2K (11 slice build) | 110 | PASS/SIGNED (mỗi slice có JUDGE_GATE SIGNED) |
| PR_PILOT (pilot production-OFF) | 12 | PASS/SIGNED — row cuối M6-P3011 SIGNED |

**3 SKIPPED là minh bạch, KHÔNG phải PASS giả:** `M6-P1000` (M6.2A), `M6-P1306` + `M6-P1309` (M6.2D) — override transparent, judge verdict giữ **BLOCKED**, có decision file; đây cũng là các *standing blocker* mà evidence-pack M6.2K disclose thẳng.

## 2. Scale Gate M6.2G đã mở (đúng quy trình, không override)

`M6-P1600` (M6.2G Scale Gate) = **SIGNED** bằng phiên Judge tươi trên bằng chứng entry thật — **không dùng owner override**, không bỏ qua bước nào. Cả 4 entry-evidence đã proven/judged độc lập bốn-mắt:

| Entry | Trạng thái | Ghi chú |
|---|---|---|
| ENTRY-001 (verified revenue chỉ từ `ORDER_VERIFIED`) | **PROVEN** + owner M3 ký | runtime proof (surefire XML) sha256 khớp; adversary không phá được ranh giới doanh thu |
| ENTRY-002 (channel identity M5) | **clean** | |
| ENTRY-003 (event governance: external_send/data_sensitivity/channel fail-closed) | **PROVEN** | build trên `origin/dev` (V190 schema + V191 classify + enforce), judge độc lập; residual: owner-runtime create + enforce chưa wire egress (đúng posture production OFF) |
| ENTRY-004 (M4+M5: không public giá / không leak PII / không spam) | M4 **PROVEN** · M5 **PARTIAL — risk-accepted (RATIFIED)** | M4 defect `safetyBoundary` đã fix (SAFE-003 @9f7e3dc8, RED→GREEN); M5 giữ PARTIAL cho pilot production-OFF |

## 3. Pack readiness = OWNER_REVIEW_REQUIRED (không tự phong Pass/Scale-Ready)

Evidence-pack cuối (M6.2K) lắp gói owner-sign-off. Enum `Readiness` **không có member Pass/Ready/Scale-Ready** — trần cấu trúc là `OWNER_REVIEW_REQUIRED`; pack **không thể tự tuyên bố** "ROAS Pass" hay "Scale Ready" (quyết định đó thuộc owner, theo doc §23). 8 *standing blocker* luôn được disclose kể cả khi pack đầy đủ.

## 4. Nợ kỹ thuật còn mở — ghi thẳng, KHÔNG che (không phải rủi ro production)

Hai loại forward-debt đã biết. **Không cái nào là rủi ro production** (cờ vẫn OFF/BLOCKED, các đường egress thật chưa bật/không reachable từ kênh):

**(a) M5 runtime controls trước real external send** (ENTRY-004 DEBT-1..4): allowlist template, dedup cross-instance, send-rate outbound, real Graph sink — điều kiện **cứng trước bất kỳ post công khai thật nào**; đã owner risk-accept cho pilot production-OFF (`M6-ENTRY-004/_OWNER_RISK_ACCEPTANCE.md`).

**(b) Lỗ trong evidence-assembler M6.2K — phát hiện bởi re-judge độc lập post-close, đã bị "ký đè" bằng fix hẹp, CHƯA thành owner-debt.** Ghi thẳng ở đây:
- **Category-content forgery:** `app/measurement/evidence/pack_assembler.py:83` đánh dấu category COMPLETE bằng `provided.get(k)` *truthiness*. Một ref giả-đúng-dạng, hoặc **1 ref hợp lệ copy-paste vào cả 10 category**, làm mọi category COMPLETE ⇒ readiness `OWNER_REVIEW_REQUIRED` với **zero bằng chứng thật**. Nó **sống sót qua fix hẹp `stripped-non-blank`** đã carry. Cần: validate ref **tồn-tại + duy-nhất + buộc-đúng-category**.
- **Collision / shadow:** floor kiểm gap-id là **set-subset** (`tests/test_gap_blocker_list_carries_standing_blockers.py`) → collapse duplicate → **không phát hiện id trùng/shadow** một standing-blocker chuẩn (M6-P1000/M6-P1309). Cần: pin/de-dup gap id.
- **Đề xuất track:** `M6-OD-013` (forgery) + `M6-OD-014` (collision/shadow), đóng **trước khi pack được đưa ra bất kỳ endpoint thật nào**. Judge M6-P2009 sign-off **sound về cơ học** (verdict PASS, `open_blockers=[]`) nhưng đã reduce 2 lỗ này thành "coder hardening non-blocking" thay vì escalate lên owner-debt — nay ghi lại để không trôi.

## 5. Điểm trung thực (dấu hiệu tốt)
- Mọi dossier liệt kê `open_blockers`/residual thẳng, không tô hồng.
- Override đều transparent: judge giữ BLOCKED, ledger SKIPPED (không PASS), có decision file.
- Defect (`safetyBoundary`) và cả lỗ evidence-assembler (§4b) **ghi thẳng, không giấu** — kể cả khi nó lộ ra rằng một bước judge trước đó chưa vét kiệt.

**Một câu:** pack build xong end-to-end, thẩm định thật bốn-mắt, production vẫn OFF; hai nợ forward (M5 runtime + evidence-assembler forgery/collision) **ghi thẳng, chưa đóng, không phải rủi ro production** — đóng trước khi chạm endpoint thật.
