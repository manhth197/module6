# STATUS — Module 6 (Đo lường Quảng cáo / Attribution / ROAS)

**Cập nhật:** 2026-09-04
**Khoá an toàn (chủ ý, không phải lỗi):** `production_flag = OFF` · `global_gateway_state = BLOCKED` · `external_send = OFF` — pack là công trình **dựng + thẩm định bằng chứng**, **chưa bật production**. Các cờ này bất biến với mọi role.

> Đọc `_AI_CHECK_GUIDE.md` ở gốc repo để **tự kiểm độc lập** từng mục dưới — kể cả để **tái hiện phần debt** ở §4.

## 1. Toàn pack đã build xong (end-to-end) + fix-slice M6.2L/M6.2M

Ledger `04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv`: **218 prompt đều terminal** — **186 PASS + 29 SIGNED + 3 SKIPPED**. Không còn prompt nào TODO/RUNNING/BLOCKED.

| Giai đoạn | Prompt | Trạng thái |
|---|---|---|
| BOOTSTRAP · DOC_LOCK · PHASE0 · HARMONIZATION | 76 | PASS |
| M6.2A → M6.2K (11 slice build) | 110 | PASS/SIGNED (mỗi slice có JUDGE_GATE SIGNED) |
| PR_PILOT (pilot production-OFF) | 12 | PASS/SIGNED — M6-P3011 SIGNED |
| **M6.2L (fix-slice post-pilot, M6-P2100-2109)** | 10 | PASS/SIGNED — judge M6-P2109 SIGNED |
| **M6.2M (mini-slice OD-013 smoke-side, M6-P2200-2209)** | 10 | PASS/SIGNED — judge M6-P2209 SIGNED |

**Ngoài ledger (out-of-band):** B1 (psid_hash) + F2-6 (duck-coerce) dựng trong impl `M6.2N`/`M6.2O` theo chỉ đạo operator, **verify bốn-mắt sạch nhưng chưa có ledger row / slice-spec** — xem §4. Đây là **staged-ready, chưa production-ready**.

**3 SKIPPED là minh bạch, không phải PASS giả:** `M6-P1000` (M6.2A), `M6-P1306` + `M6-P1309` (M6.2D) — override transparent, judge verdict giữ **BLOCKED**, có decision file; cũng là *standing blocker* mà evidence-pack M6.2K disclose thẳng.

## 2. Scale Gate M6.2G đã mở (đúng quy trình, không override)

`M6-P1600` (M6.2G Scale Gate) = **SIGNED** bằng phiên Judge tươi trên bằng chứng entry thật — **không** owner override, không bỏ bước. 4 entry-evidence proven/judged bốn-mắt:

| Entry | Trạng thái | Ghi chú |
|---|---|---|
| ENTRY-001 (verified revenue chỉ từ `ORDER_VERIFIED`) | **PROVEN** + owner M3 ký | runtime proof (surefire XML) sha256 khớp; adversary không phá được ranh giới doanh thu |
| ENTRY-002 (channel identity M5) | **clean** | |
| ENTRY-003 (event governance fail-closed) | **PROVEN** | V190 schema + V191 classify + enforce trên `origin/dev`; residual owner-runtime create (đúng posture OFF) |
| ENTRY-004 (M4+M5) | M4 **PROVEN** · M5 **PARTIAL — risk-accepted (RATIFIED)** | M4 `safetyBoundary` fix @9f7e3dc8; M5 PARTIAL cho pilot OFF |

## 3. Pack readiness = OWNER_REVIEW_REQUIRED (không tự phong Pass/Scale-Ready)

Enum `Readiness` **không có** member Pass/Ready/Scale-Ready — trần cấu trúc là `OWNER_REVIEW_REQUIRED`; pack **không thể** tự tuyên bố "ROAS Pass" / "Scale Ready" (owner-only, doc §23). 8 *standing blocker* luôn disclose kể cả khi pack đầy đủ.

## 4. Đóng nợ evidence-assembler + doanh-thu-lock + PII — verify độc lập

**M6.2L (on-ledger, M6-P2100-2109, judge M6-P2109 SIGNED)** — chief-auditor @5f09894 nêu 5 lỗi M6 tự đóng được → fix-slice gated, chạy trọn loop, re-judge độc lập (soi M6.2L vs M6.2K từng dòng) **5/5 thật**:
- **B2 forgery đóng thật:** `pack_assembler` thêm uniqueness đếm pack-wide + binding (category,key) → 1 ref copy-paste cả 10 category = mọi category MISSING (không phải fix hẹp cũ).
- **B3 collision đóng thật:** floor `standing_floor_ok` = mỗi standing-id đúng 1 lần + pin (kind,description) → dup/shadow M6-P1000/M6-P1309 = FAIL (không còn set-subset).
- **B4 ROAS-lock:** `verified_rows()` lọc `event_code==ORDER_VERIFIED` + `materialize()` tự kiểm event_code (bỏ boolean caller) + choke thứ 3 (growth). QUOTE_SENT+verified=True → Revenue=0/ROAS=0.
- **A3** attribution_id thành khóa trace first-class; **A4** intake nhận đủ campaign/adset/ad/live_session → resolver HIGH.

**M6.2M (on-ledger, M6-P2200-2209, judge M6-P2209 SIGNED)** — đóng **smoke-side** của M6-OD-013: `models.py` `SmokeResult.recorded` bỏ raw truthiness, dùng `_nonblank` (isinstance str + `strip() != ""`) → một `SmokeResult` whitespace/fake-nonblank cho owner-smoke bắt buộc = `recorded=False` → UNRUN → NOT_READY; `_smokes` chuẩn hoá defense-in-depth. Re-judge độc lập: smoke-side **thật**; ref-side chỉ thêm test SMK-024 + docstring (enforcement byte-identical M6.2L) → **ref-side OD-013 chưa đóng** (xem §4 nợ (b)).

**B1 + F2-6 (out-of-band — operator-directed, không on-ledger)** — verify bốn-mắt độc lập, sạch, nhưng **chưa có** ledger row / slice-spec / entry-judge (ledger dừng ở M6-P2209):
- **B1 psid_hash (impl M6.2N→O):** đóng surface raw-PSID cuối trên đường attribution/live — raw psid **không còn** lưu ở đâu (kể cả durable); một chiều HMAC-SHA256(pepper, psid) prefix `psid_hash:`; production **fail-close** khi pepper env chưa set. Pepper là **secret** — hiện chỉ có mock dev-only (labeled non-secret); **pepper thật = secret_ref owner cấp khi deploy**.
- **F2-6 duck-coerce (impl M6.2O):** `_smokes` dựng lại canonical `SmokeResult` từ field, **không tin** `.recorded` của caller → đóng twin code-exec của smoke-side (duck `.recorded=True` + field rỗng không mark được owner-smoke).
- **Gate bốn-mắt (2026-09-04):** boundary giữ (0 dòng app do tester), 2 smoke chính thức assert thật (fail-closed dùng argument, **không** lật flag), 2 SMK-013 + 3 test coder re-point đều **strengthen, 0 nerf**, no leak; tự chạy lại 4 file → 15 passed; full suite 591 passed. Đây là **verify-clean self-report**, **không** advance ledger/readiness.

**Nợ forward còn mở (ghi thẳng — không phải rủi ro production; cờ vẫn OFF/BLOCKED):**
- **(a) M5 runtime controls trước real external send** (ENTRY-004 DEBT-1..4): allowlist template, dedup cross-instance, send-rate, real Graph sink — điều kiện cứng trước post công khai thật; owner đã risk-accept cho pilot OFF (`M6-ENTRY-004/_OWNER_RISK_ACCEPTANCE.md`).
- **(b) M6-OD-013 ref-side authenticity** (code-exec-only, cap `OWNER_REVIEW_REQUIRED`): oracle `known_refs` mới **opt-in**, **chưa** caller production nào truyền → đường mặc định vẫn nhận ref dựng-lại canonical `ev::{cat}::{key}`. Đóng thật = **owner-integration** (dựng registry issued-refs + wire vào mọi caller `assemble()`). Smoke-side twin **đã đóng** bởi M6.2M.
- **(c) Governance out-of-band:** M6.2N/M6.2O cần owner/analyst đăng ký (slice_definitions + ledger + entry-judge) nếu muốn bắt vào flow gate chính thức; + quyết pepper cross-module M6↔M3/M7 (owner + chief).
- **M6-OD-014** (gap-id collision floor): code-side **đã đóng** bởi B3; owner còn review canon standing-blocker.

## 5. Điểm trung thực (dấu hiệu tốt)
- Mọi dossier liệt kê `open_blockers`/residual thẳng, không tô hồng.
- Override đều transparent: judge giữ BLOCKED, ledger SKIPPED (không PASS), có decision file.
- Lỗ evidence-assembler từng bị judge M6.2K **ký đè bằng fix hẹp** → nêu thẳng, dựng slice fix M6.2L đóng thật, rồi re-verify độc lập; smoke-side twin đóng nốt bằng M6.2M. Residual còn lại (§4b) khai rõ, không giấu.
- **Out-of-band khai thẳng:** B1/F2-6 làm ngoài ledger; tester **không** ghi evidence id `M6-Pxxxx` giả (để ở `04-artifacts/test-reports/M6.2O/`) để tránh lừa EVIDENCE_GATE — trạng thái off-ledger nói rõ, không nguỵ trang thành prompt đã chạy.
- **Finding pre-existing (không do M6.2L/M):** `validate_input_consumption` báo các mục "declared but not consumed" khắp M6.2A-M (role session khai `RequiredInputs` nhưng không ghi vào `files_read`). Đây là evidence-hygiene, không phải sai correctness; **không** được "làm xanh" bằng cách sửa evidence.

**Một câu:** pack build xong end-to-end + M6.2L/M6.2M đóng thật nợ forgery/collision/ROAS-lock/smoke-authenticity (verify độc lập thật); B1/F2-6 đóng raw-PSID + duck-coerce **out-of-band, verify-clean nhưng chưa on-ledger**; production vẫn OFF; residual còn lại = M5 runtime + ref-side OD-013 (owner-integration) — ghi thẳng, đóng trước khi chạm endpoint thật.
