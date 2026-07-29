# METHODOLOGY — Module 6 delivery process (condensed from the owner document)

Source: doc §6 (phase flow), §24 (handoff playbook), §22 (evidence plan),
§2 (ADS Execution Playbook rhythm). Read policy: governance / analysis_only
prompts.

## 1. Delivery rhythm (locked)

NHỊP THI CÔNG BẮT BUỘC (verbatim, extract line 454): "Mỗi phase chạy 3 prompt
riêng: Audit Prompt -> Implementation Prompt -> Verify/Gate Prompt. Không dùng
một prompt làm hết. Không nhảy Phase 2 nếu Phase 1 chưa pass. Không nhảy
Phase 3 nếu Phase 2 chưa pass."

The pack encodes this as: per slice — entry-gate judge -> coder PLAN only ->
coder IMPLEMENT -> tester build -> tester run -> boundary adversary ->
security review -> evidence collect -> docs -> slice-gate judge.

## 2. Step requirements (doc §24, extract lines 457–461)

| Bước | Yêu cầu output |
|---|---|
| Audit | Đọc repo hiện tại, mapping file/table/service/test, gap report, conflict report, owner decision required |
| Implementation | Liệt kê exact files, migrations, configs, workers, services, tests; thay đổi tối thiểu đúng phase |
| Verify/Gate | Chạy test, output PASS/FAIL từng item, evidence, rollback, không mark done nếu thiếu acceptance |

## 3. Working mode for dev / AI agents (verbatim, extract lines 463–472)

- Do not guess.
- Read the current repository structure first.
- Reuse existing conventions and test patterns.
- Keep owner and boundary aligned with ADS phase lock.
- Do not invent event codes outside Core event_registry.
- Do not invent pricing or policy outside Core policy resolver.
- Do not override Core, AI Runtime, CRM Messaging, Golden Hour, 24/7 or Diamond.
- Do not jump ahead to future phase scope except safe extension seams.
- Output required: repo summary, files touched, code/migration/config/jobs/tests,
  commands, PASS/FAIL checklist, rollback steps.

## 4. Evidence discipline

Every prompt writes evidence JSON (schema embedded in each prompt); smokes
record correlation_id + evidence_id (doc §22 line 430); machine gates check
evidence before any status changes; judges review evidence in fresh sessions;
the human operator is the only party who marks PASS/SIGNED, via
`scripts-win/Mark-PromptPassLocked.ps1`.

## 5. Fail-closed defaults

Missing evidence, unknown state, contradiction, or an OPEN owner decision in
scope ⇒ status BLOCKED, never assumed PASS (pack principle + doc fail gate
M6-FAIL-007). `global_gateway_state=BLOCKED`, `production_flag=OFF` at all
times during this pack's execution.
