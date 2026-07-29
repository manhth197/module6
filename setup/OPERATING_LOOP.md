# OPERATING_LOOP — Sổ tay vận hành Build Pack Module 6 (dành cho Operator)

Pack này chạy theo mô hình: **nhiều phiên AI (mỗi phiên một vai) + một người vận hành (bạn) + gate máy giữa mọi bước**. AI không bao giờ tự chấm PASS — chỉ bạn chạy lệnh mark sau khi gate máy kiểm tra bằng chứng.

Trạng thái khóa: `global_gateway_state=BLOCKED`, `production_flag=OFF` — không prompt nào được đổi. Pack chỉ chứng minh năng lực bằng bằng chứng; ROAS Pass / Scale Ready là quyết định của Owner, ngoài pack.

---

## 1. Cài đặt một lần (one-time setup)

1. Giải nén / copy pack về máy, ví dụ `D:\M6\Module6-workspace`.
2. Mở PowerShell tại thư mục pack, chạy:
   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File setup\Initialize-M6RoleIsolatedDesktop.ps1
   ```
   Lệnh này tạo junction (00-spec, 04-artifacts, registry, scripts, scripts-win) vào từng thư mục vai, tạo bản chụp dự phòng `_source_snapshot\00-spec` (kèm manifest sha256), và tạo venv bằng Python 3 đã được tự dò ở gốc + từng vai thực thi. **05-judge KHÔNG có venv/CLAUDE.md/hooks — cố ý như vậy.** Thêm `-SkipVenv` nếu muốn tự tạo venv sau; nếu Python không nằm trong PATH, truyền `-PythonExe C:\Path\To\python.exe`.
2b. Tạo/kiểm tra venv HÀNG LOẠT (chạy được độc lập, idempotent, kể cả khi bước 2 đã bỏ qua venv):
   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File setup\New-M6RoleVenvs.ps1
   ```
   Script in bảng xác nhận từng thư mục (root + 6 vai = OK, 05-judge = NONE by design). Requirements theo cấu trúc **2 TẦNG**:
   - `requirements.txt` ở GỐC pack = baseline chung, **stdlib-only** (chỉ comment, không package);
   - `<vai>\requirements.txt` trong TỪNG thư mục vai = kế thừa baseline qua dòng `-r ../requirements.txt` + khu vực package RIÊNG CỦA VAI có gate: package của CODER/TESTER chỉ được thêm sau khi owner chốt M6-OD-011 (stack) và do OPERATOR ghi tay kèm dòng SCHEMA_CHANGELOG (AI executor bị hook chặn, không sửa được file này); ANALYST/RUNNER/BOUNDARY/SECURITY mặc định stdlib vĩnh viễn trừ khi có gate riêng.
   Mỗi venv cài từ đúng file CỦA VAI ĐÓ (gốc dùng baseline). Sau khi thêm package cho vai nào, chạy lại script — chỉ venv của vai đó nhận package mới. Kích hoạt là VIỆC TỪNG CỬA SỔ: trong mỗi cửa sổ vai chạy `& .\.venv\Scripts\Activate.ps1` (PowerShell) hoặc `.venv\Scripts\activate.bat` (cmd). Khi không kích hoạt, gọi trực tiếp `.venv\Scripts\python.exe`.
3. Chạy toàn bộ validator, phải PASS hết:
   ```
   & .\.venv\Scripts\python.exe scripts\run_all_validators.py
   ```
4. Kiểm tra readiness để bắt đầu BOOTSTRAP:
   ```
   & .\.venv\Scripts\python.exe scripts\validate_implementation_readiness.py --stage bootstrap
   ```

## 1b. Khóa repo/stack triển khai trước entry gate M6.2A

1. Owner điền `setup/templates/OWNER_DECISIONS_INTAKE.md`, đặc biệt M6-OD-011.
2. Operator ghi quyết định có ngày và evidence ref vào `DECISION_REGISTER.md`.
3. Operator khóa target bằng `setup/Set-M6ImplementationTarget.ps1`. Ví dụ:
   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File setup\Set-M6ImplementationTarget.ps1 -Mode Existing -TargetPath D:\path\to\repo -Language python -LanguageVersion 3.12 -Framework fastapi -Database postgresql -Queue redis -TestCommand "pytest -q" -RunCommand "uvicorn app.main:app" -DecisionEvidenceRef "04-artifacts/evidence/entry/M6-OD-011.json" -Lock
   ```
4. Chuẩn hóa evidence M6-ENTRY-001..004 từ `setup/templates/ENTRY_EVIDENCE.template.json`.
5. Trước M6-P1000, lệnh sau phải PASS:
   ```
   & .\.venv\Scripts\python.exe scripts\validate_implementation_readiness.py --stage slice-a-entry
   ```
5. **QUAN TRỌNG**: nếu sau này bạn di chuyển/copy pack sang chỗ khác, junction sẽ GÃY (junction lưu đường dẫn tuyệt đối). Chạy lại:
   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File setup\Repair-M6RoleJunctions.ps1
   ```

## 2. Mô hình cửa sổ (window model)

- **Terminal (bạn — operator)**: mở tại gốc pack, chỉ chạy các script `scripts-win\`. Không phải phiên Claude.
- **Mỗi vai một cửa sổ Claude Code Desktop**:
  - `00-analyst`, `01-coder`, `02-tester`, `04-boundary`, `06-security`: mở ĐÚNG thư mục vai đó làm project.
  - **PM** và **JUDGE**: mở GỐC PACK làm project (hai phiên riêng biệt).
  - **JUDGE luôn là phiên MỚI TINH cho mỗi lần chấm** — để phán quyết dựa trên file bằng chứng, không dựa trên trí nhớ hội thoại.
- `03-runner` là thư mục của bạn (handoff files); không mở phiên Claude ở đó.

## 3. Vòng lặp mỗi prompt (per-prompt loop)

```
powershell -NoProfile -ExecutionPolicy Bypass -File scripts-win\Get-NextPromptDetail.ps1 -CopyToClipboard -Open
```
1. Lệnh trên: chọn prompt kế tiếp (theo Order + dependency), đánh dấu RUNNING, copy toàn bộ prompt vào clipboard, tạo file handoff `03-runner\handoff\NEXT_<id>_<Role>_<ts>.md`, và TẠO SẴN file judge `JUDGE_AFTER_RUNNER_<id>_<ts>.md` cho gate judge cùng band.
2. Dán prompt vào đúng cửa sổ vai (xem cột Role in ra màn hình).
3. Executor làm việc và tự ghi bằng chứng `04-artifacts/evidence/prompts/<id>.json` (hook chặn "done" nếu thiếu). Executor KHÔNG tự mark.
4. Bạn chạy gate máy:
   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File scripts-win\Check-PromptGateLocked.ps1 -PromptId <id>
   ```
   Exit 0 = đạt; exit 2 = in rõ lý do (thiếu file, evidence sai schema, PII, blocker...).
5. Đạt thì mark (lệnh này TỰ chạy lại gate trước khi ghi):
   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File scripts-win\Mark-PromptPassLocked.ps1 -PromptId <id>
   ```
6. Lặp lại. Xem prompt kế tiếp bất kỳ lúc nào: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts-win\Get-NextPromptLocked.ps1`.

Trạng thái khác (không bao giờ PASS/SIGNED bằng tay):
```
powershell -NoProfile -ExecutionPolicy Bypass -File scripts-win\Set-PromptStatusLocked.ps1 -PromptId <id> -Status BLOCKED|FAIL|TODO|RUNNING -Note "..."
```
`SKIPPED` bắt buộc `-Note "SKIP_APPROVED:<mã quyết định owner>"` và KHÔNG BAO GIỜ áp dụng được cho hàng JUDGE_GATE.

## 4. Bước có Judge (JUDGE_GATE)

1. Chỉ sau khi evidence của các prompt trong band đã có và gate máy đã pass chúng.
2. Mở phiên Judge MỚI (gốc pack), dán nội dung file `JUDGE_AFTER_RUNNER_*.md` đã tạo sẵn.
3. Judge đọc từng file bằng chứng, ghi evidence + sign-off `04-artifacts/evidence/judge/<id>_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS/FAIL/BLOCKED).
4. Bạn chạy hai script với `powershell -NoProfile -ExecutionPolicy Bypass -File`: `Check-PromptGateLocked.ps1 -PromptId <id>` (kiểm cả sign-off), rồi `Mark-PromptPassLocked.ps1` → hàng judge thành SIGNED.

## 5. Việc riêng của operator trong luồng

- **M6-P0008**: prompt sẽ yêu cầu bạn chạy `Get-FileHash D:\M6\source-archive\MODULE_6_ADS_MEASUREMENT_ROAS_V0.3_CLEAN_FINAL.docx -Algorithm SHA256` và dán kết quả vào phiên PM.
- **Entry evidence (M6-ENTRY-001..004)**: khi có bằng chứng từ Module 3/5/Core, đặt file vào `04-artifacts/evidence/entry/` trước entry-gate của slice M6.2A.
- **Sau HARMONIZATION judge (M6-P0715)**: bạn (không phải AI) copy các contract đã duyệt từ `04-artifacts/analysis/contracts/` vào `00-spec/contracts/`, đổi status trong `CONTRACT_REGISTER.md` (MISSING → DRAFT_LOCKED) và thêm dòng `SCHEMA_CHANGELOG.md` — vì mọi vai AI đều bị cấm ghi `00-spec/`. Sau đó chạy `setup\Repair-M6RoleJunctions.ps1` để làm mới snapshot.
- **Quyết định owner (M6-OD-xxx)**: ghi ngày + quyết định vào `DECISION_REGISTER.md` (bạn sửa tay), kèm ghi chú vào evidence note.

## 6. Xử lý sự cố (troubleshooting)

| Hiện tượng | Nguyên nhân / cách xử lý |
|---|---|
| Gate fail "required output missing" | Executor chưa ghi đủ file trong `<required_outputs>`. Dán lại yêu cầu, executor bổ sung. |
| Gate fail "secret/PII scan hit" | Evidence chứa số điện thoại/email/token thô. Executor phải che (`abc***xy`, `secret_ref`) rồi ghi lại. |
| Gate fail "files_changed outside role allowlist" | Executor khai đã sửa file ngoài quyền. Xem lại thay đổi; nếu sai vai → revert. |
| Hook chặn "ROLE_PRE_TOOL_GUARD BLOCK" | Executor cố ghi ngoài allowlist / cụm nguy hiểm (production_flag ON, token...). Đây là hành vi đúng của hook. |
| Hook chặn "STOP_ROLE_EVIDENCE_GUARD" | Executor định kết thúc mà chưa ghi evidence cho prompt RUNNING. Yêu cầu ghi evidence. |
| Junction gãy (mở 00-spec trong thư mục vai bị lỗi) | Pack vừa bị move/copy → chạy `setup\Repair-M6RoleJunctions.ps1`. Trong lúc chưa sửa, executor đọc tạm `_source_snapshot\00-spec\` (chỉ đọc). |
| `validate_roles` báo "snapshot STALE" | 00-spec đã thay đổi sau lần chụp → chạy Repair để làm mới snapshot. |
| `validate_release_clean` FAIL khi đang chạy | **Bình thường** — validator này chỉ PASS khi pack còn nguyên trạng chưa chạy (dùng trước khi bàn giao/re-zip). Không phải lỗi. |
| Hai prompt cùng RUNNING | Không thể qua script; nếu ai sửa tay ledger → `Set-PromptStatusLocked -Status TODO` cho hàng thừa. |
| PowerShell báo lỗi encoding tiếng Việt | Script pack đều ASCII; file dữ liệu là UTF-8 no-BOM. Luôn dùng `Get-Content -Raw -Encoding UTF8` khi tự xem file. |

## 7. Chọn model cho từng vai

| Vai | Khuyến nghị |
|---|---|
| JUDGE, BOUNDARY_ADVERSARY, SECURITY_PII | Model mạnh nhất đang có (chấm gate, tấn công biên, soát PII — không được tiếc). |
| ANALYST_ARCHITECT (DOC_LOCK, HARMONIZATION) | Model mạnh. |
| CODER, TESTER | Model mạnh hoặc trung. |
| PM_ORCHESTRATOR (bootstrap, evidence-collect, docs) | Model nhanh/tiết kiệm là đủ. |
| Tuyệt đối không | Dùng model nhanh để judge. |

## 8. Thứ tự tổng thể

BOOTSTRAP (12) → DOC_LOCK (14) → PHASE0_RESEARCH + CRITIC (24) → PHASE0 design (10) → CONTRACT_HARMONIZATION (16) → 11 slice bands M6.2A→K (110) → PR/PILOT (12). Tổng 198 prompt, 27 judge gate. Slice chạy TUẦN TỰ (M6-OD-010). Lệnh đầu tiên của bạn:

```
powershell -NoProfile -ExecutionPolicy Bypass -File scripts-win\Get-NextPromptDetail.ps1 -CopyToClipboard -Open
```
