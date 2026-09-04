# Hướng dẫn AI kiểm tra (AI CHECK) — Module 6 build pack

> **Dành cho:** một trợ lý AI (Claude / GPT / …) được giao clone repo này và **kiểm tra độc lập**.
> **Nguyên tắc số 1:** hãy **tự kiểm và báo cáo đúng những gì bạn tìm thấy**. File này chỉ tay
> tới đâu để kiểm — **không** phải để bạn lặp lại một kết luận có sẵn. Nếu bạn phát hiện mâu thuẫn,
> PASS giả, cờ production bị bật, evidence trống, hay một lỗ chưa được escalate đúng, **hãy nêu ra**.
> (File chủ động chỉ bạn tới **một fix và một residual** ở §4 để bạn tự tái hiện + xác nhận.)

## 1. Pack này là gì
Bộ build pack cho **Module 6 — Đo lường Quảng cáo / Attribution / ROAS** của Ginsengfood, dựng theo
**gated, evidence-driven**: mỗi bước có bằng chứng, **không role nào tự chấm PASS**; bằng chứng
cross-module kiểm bằng **bốn-mắt** (author ≠ adversary ≠ judge), pin theo **commit SHA** repo mã nguồn.

**Trạng thái khoá là CHỦ Ý:** `global_gateway_state = BLOCKED`, `production_flag = OFF`,
`external_send = OFF`. Pack **build xong end-to-end** nhưng **chưa bật production** — quyết định
scale/production thuộc **owner**. Thấy "BLOCKED/OFF" là **fail-closed đúng thiết kế**, không phải thất bại.

## 2. Trạng thái hiện tại (2026-09-03) — đọc ledger, đừng tin tóm tắt
`04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv`: **218 prompt terminal — 186 PASS, 29 SIGNED,
3 SKIPPED**; không còn TODO/RUNNING/BLOCKED. Pack (BOOTSTRAP → M6.2A…M6.2K → PR_PILOT → **M6.2L → M6.2M**) đã chạy.
- **M6.2G Scale Gate (`M6-P1600`) = SIGNED** — mở bằng phiên Judge tươi, **không owner override**. Kiểm `04-artifacts/evidence/judge/M6-P1600_JUDGE_FINAL_SIGN_OFF.json`.
- **M6.2L** (fix-slice post-pilot, `M6-P2100..2109`, judge `M6-P2109` SIGNED): đóng 5 lỗ audit — xem §4.
- **M6.2M** (mini-slice, `M6-P2200..2209`, judge `M6-P2209` SIGNED): đóng smoke-side M6-OD-013 — xem §4(B).
- **B1/F2-6 out-of-band** (impl `M6.2N`/`M6.2O`, **không** ledger row): psid_hash + duck-coerce, verify-clean nhưng off-ledger — xem §4(C).
- **3 SKIPPED** (`M6-P1000/1306/1309`): override phải là **SKIPPED** (không PASS/SIGNED), judge verdict giữ **BLOCKED**, có decision file trong `04-artifacts/evidence/decisions/`. Xác nhận không evidence nào ghi `production_flag=ON` / gateway mở.

## 3. Bằng chứng entry — đọc verdict file
- **ENTRY-001** (verified revenue): `04-artifacts/evidence/entry/M6-ENTRY-001.json` + `_REJUDGE_VERDICT_*.json`. **PROVEN** (doanh thu chỉ từ `ORDER_VERIFIED`); surefire XML **sha256 khớp** (tự tính lại); owner M3 đã ký.
- **ENTRY-003** (event governance): **PROVEN** — 3 chiều fail-closed (external_send_policy DEFAULT BLOCKED + data_sensitivity DEFAULT SENSITIVE + attribution_channel) V190/V191, 2 adversary xác nhận.
- **ENTRY-004** (M4+M5): M4 **PROVEN** (`safetyBoundary` fix @9f7e3dc8); M5 **PARTIAL — risk-accepted RATIFIED** cho pilot OFF, DEBT-1..4 là điều kiện cứng trước real send.
- **ENTRY-002** clean.

## 4. Fix M6.2L + residual còn mở — HÃY TỰ TÁI HIỆN (bài kiểm thật)
M6.2K từng để judge **ký đè** 2 lỗ evidence-assembler bằng fix hẹp. Slice **M6.2L** dựng để đóng thật.
Nhiệm vụ của bạn: xác nhận **fix đã landing** VÀ **residual được khai trung thực** (không phải rủi ro
production — cờ OFF/BLOCKED, không channel-reachable).

**(A) Fix đã đóng thật — verify trên code M6.2L (so với M6.2K):**
- Forgery: `04-artifacts/impl/M6.2L/app/measurement/evidence/pack_assembler.py` — completeness giờ có **uniqueness đếm pack-wide** (`counts[...] != 1`, ~dòng 74/134-139) + **binding (category,key)** (`_ref_binding`, ~dòng 40-54/78), không còn raw truthiness. So với M6.2K dòng 83 (`provided.get(k)`). Test `tests/test_m6_2l_b2_evidence_ref_forgery.py`: 1 ref copy-paste cả 10 category → **tất cả MISSING / NOT_READY**.
- Collision: `.../evidence/gap_blockers.py` — `standing_floor_ok` (~dòng 55-72): mỗi standing-id **đúng 1 lần** + pin `(kind,description)` → dup/shadow M6-P1000/M6-P1309 = FAIL. M6.2K **không có floor** (chỉ set-subset trong test). Test `tests/test_m6_2l_b3_gap_floor_membership.py`.
- ROAS-lock: `.../dashboard/data_mart.py` `verified_rows()` lọc `event_code==ORDER_VERIFIED` + `.../store/measurement_event_store.py` `materialize()` tự kiểm event_code (bỏ boolean caller). Test `tests/test_m6_2l_b4_verified_lock.py`: QUOTE_SENT+`materialize(verified=True)` → Revenue=0/ROAS=0.

**(B) Residual authenticity M6-OD-013 — smoke-side đã đóng (M6.2M), ref-side còn mở:**
- smoke-side (twin): M6.2M sửa `04-artifacts/impl/M6.2M/app/measurement/evidence/models.py` — `SmokeResult.recorded` bỏ raw truthiness, thêm `_nonblank` (isinstance str + `strip()!=""`); `_smokes` chuẩn hoá. Test `tests/test_m6_2m_smoke_authenticity.py` + smoke `test_smk_025_*`. Re-judge độc lập: **smoke-side thật**.
- ref-side: **chưa đóng** — oracle `known_refs` (seam `pack_assembler.py`) chỉ chặn khi caller truyền allowlist; M6.2M thêm test SMK-024 + docstring nhưng **enforcement byte-identical M6.2L**, không caller production nào truyền → đường mặc định vẫn nhận ref dựng-lại canonical `ev::{cat}::{key}`. Đóng thật = **owner-integration** (registry issued-refs wire vào mọi caller `assemble()`), cap `OWNER_REVIEW_REQUIRED`.
- Kết luận: M6.2L/M6.2M là **fix sâu thật** (không ký đè lần nữa), ref-side còn là **owner-integration đã disclose**, không lật cờ nào. Xem `status.md §4`.

**(C) B1 + F2-6 — out-of-band, verify-clean nhưng không on-ledger (tự soi):**
- **B1 psid_hash:** `04-artifacts/impl/M6.2O/app/measurement/identity/psid_hash.py` — `hash_psid` một chiều HMAC-SHA256(pepper, psid) prefix `psid_hash:`; `resolve_pepper(production=True)` raise `PsidHashPolicyError` khi env `M6_PSID_HASH_PEPPER` chưa set (fail-close). `.../models/attribution_context.py` `as_stored()` chỉ mang `psid_hash`, **không** raw psid. Smoke `tests/smoke/test_b1_psid_hash_smoke.py` (4/4). Pepper thật là **secret_ref owner cấp khi deploy**; repo chỉ có mock dev-only labeled non-secret.
- **F2-6 duck-coerce:** `.../evidence/pack_assembler.py` `_smokes` dựng lại canonical `SmokeResult` từ field (không tin `.recorded` caller). Smoke `tests/smoke/test_f2_6_duck_recorded_coerced.py` (3/3).
- **Tình trạng governance:** ledger dừng ở `M6-P2209`; M6.2N/M6.2O **chưa có** slice-spec / ledger row / entry-judge. Evidence để ở `04-artifacts/test-reports/M6.2O/` (không phải `evidence/prompts/` với id giả). Đây là **staged-ready**, chưa production-ready; muốn on-ledger cần owner/analyst đăng ký slice.

## 5. Finding pre-existing — chạy validator suite rồi tự đánh giá
Chạy `.venv\Scripts\python.exe scripts\run_all_validators.py`. Bạn sẽ thấy **8 validator PASS** (registry,
roles, gate_hardening, registers, implementation_readiness, four_eyes, secret_scan, scanner_battery) +
2 đỏ: `release_clean` **FAIL by-design** (pack in-flight, không pristine) và `validate_input_consumption`
**FAIL (40)**. Đừng vội gọi đó là lỗi correctness: cả 40 cùng **một pattern** khắp M6.2A-M (role session
khai `RequiredInputs` nhưng không ghi vào `files_read` — đa số `IMPLEMENTATION_TARGET_LOCKED` cho tester,
brief cho judge). Đây là **evidence-hygiene** (full suite chưa từng chạy post-execution, operator chỉ chạy
per-prompt gate), **không** phải PASS giả và pack **không** được "làm xanh" bằng cách sửa evidence. Nêu nó
như một finding, không phải một tố cáo giả mạo.

## 6. Giới hạn — cái bạn KHÔNG kiểm được chỉ từ repo này (hãy nói rõ)
- Repo này **KHÔNG chứa mã nguồn** business-platform (M3/M4/M5). Claim về code kiểm tại **commit SHA cụ thể** ghi trong verdict file; muốn re-verify tầng đó cần clone repo business-platform riêng. Phân biệt **"đã đọc verdict"** vs **"đã tự chạy lại trên mã nguồn"**.
- `_*JUDGE_VERDICT_*.json` là **thẩm định bốn-mắt đã ghi lại**, dẫn chiếu file:line + SHA.

## 7. Kết luận trung thực mà một lần kiểm đúng sẽ ra
- Pack **build xong end-to-end, evidence-driven, không PASS giả**; production/gateway/external_send **OFF/BLOCKED**; readiness trần **OWNER_REVIEW_REQUIRED**.
- 4 entry proven/judged; M6.2G mở đúng quy trình; **M6.2L đóng thật** 5 lỗ audit (forgery/collision/ROAS-lock + attribution_id + ad-hierarchy) verify độc lập 5/5 thật; **M6.2M** đóng nốt smoke-side M6-OD-013.
- **B1/F2-6 (psid_hash + duck-coerce)** làm out-of-band, verify bốn-mắt sạch nhưng **chưa on-ledger** (§4C) — staged-ready, chưa production-ready.
- **Còn nợ forward, ghi thẳng:** M5 runtime controls (ENTRY-004 DEBT-1..4) + **ref-side** M6-OD-013 authenticity (canonical-reconstruction, đóng bằng owner-integration registry issued-refs) — **code-exec-only, không rủi ro production**, đóng trước khi chạm endpoint thật.
- Finding pre-existing `validate_input_consumption` (§5) — evidence-hygiene, không phải giả mạo.

Tóm một câu: **bằng chứng thật, thẩm định thật, lỗi/nợ ghi thẳng, không có gì bị làm giả — pack tự chỉ ra chỗ đã đóng, chỗ chưa vét kiệt, và chỗ hygiene chưa hoàn hảo để bạn kiểm lại.** Thấy khác → nêu ra.
