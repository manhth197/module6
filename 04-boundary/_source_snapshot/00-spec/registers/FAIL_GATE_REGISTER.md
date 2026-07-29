# FAIL_GATE_REGISTER — Module 6

1:1 with the owner document's Fail Gate table (doc §23, extract lines 442–450).
A tripped fail gate blocks immediately: the affected prompt/slice is marked
FAIL or BLOCKED, `fail_gate_tripped=true` goes into evidence, and work stops
until the operator/owner resolves it. Extensions beyond the document are
explicitly marked `HARDENING — OWNER REVIEW`.

## Owner fail gates (verbatim scope)

| Fail Gate ID | Name | Chặn ngay nếu (verbatim) | Source |
|---|---|---|---|
| M6-FAIL-001 | Revenue misuse | Quote/cart/order draft/payment waiting/COD waiting bị tính revenue | doc §23, extract line 444 |
| M6-FAIL-002 | Consent violation | External measurement hoặc audience sync khi thiếu consent | doc §23, extract line 445 |
| M6-FAIL-003 | Event drift | Tự phát minh event ngoài event_registry | doc §23, extract line 446 |
| M6-FAIL-004 | Core override | Override pricing/policy/Golden Hour/24-7/Diamond/CRM owner | doc §23, extract line 447 |
| M6-FAIL-005 | Data Mart abuse | Dùng Data Mart làm trigger owner | doc §23, extract line 448 |
| M6-FAIL-006 | Auto scale | Tự tăng ngân sách hoặc publish optimization không approval | doc §23, extract line 449 |
| M6-FAIL-007 | No evidence | Không có audit/evidence/smoke mà gọi PASS | doc §23, extract line 450 |

## Pack extensions (HARDENING — OWNER REVIEW)

| Fail Gate ID | Name | Trips when | Derivation |
|---|---|---|---|
| M6-FAIL-008 | Raw PII exposure | Raw PII (phone, email, address, raw user/guest id, bank account, tax code) or a raw secret/token appears in code, prompt, log, evidence or an external payload without the hash policy | Extension of doc §12 line 248, §16 line 319, §22 line 429 into gate form |
| M6-FAIL-009 | Gate bypass | An executor marks its own work PASS/SIGNED, edits the runner state ledger, or a JUDGE_GATE row is skipped | Pack mechanics only; no doc source |
| M6-FAIL-010 | Phase jump | Work starts on a later ADS phase/slice while an earlier phase's gate is not passed | Extension of doc §6 line 100 ("Không được nhảy phase") and §24 line 454 into gate form |
