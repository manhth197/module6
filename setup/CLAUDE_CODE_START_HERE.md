# Claude Code — Module 6 start here

This pack is ready to start the governed workflow, not to bypass its gates.
Claude Code sessions must be opened in the exact role folders below.

## One-time machine setup

From the pack root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File setup\New-M6RoleVenvs.ps1
& .\.venv\Scripts\python.exe scripts\run_all_validators.py --report-only
& .\.venv\Scripts\python.exe scripts\validate_implementation_readiness.py --stage bootstrap
```

If Python is not discoverable, pass its full path:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File setup\New-M6RoleVenvs.ps1 -PythonExe C:\Path\To\python.exe
```

## Claude Code windows

| Window | Open project folder | Purpose |
|---|---|---|
| PM | pack root | BOOTSTRAP, orchestration, evidence collection |
| Judge | pack root, fresh session for every judgment | Evidence-only gate verdict |
| Analyst | `00-analyst` | DOC_LOCK, research, design, contract harmonization |
| Coder | `01-coder` | Plan and staged implementation |
| Tester | `02-tester` | Build/run tests; never repair implementation |
| Boundary | `04-boundary` | Adversarial boundary review |
| Security | `06-security` | PII/security review |
| Operator terminal | pack root | Only `scripts-win\*.ps1` state transitions |

Activate the role-local venv in each execution window. Do not open a Claude
session in `03-runner`; it is the human operator handoff folder.

## Start the workflow

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts-win\Get-NextPromptDetail.ps1 -CopyToClipboard -Open
```

Paste exactly that prompt into the indicated role window. After evidence is
written, run the machine gate, then the operator mark command described in
`setup/OPERATING_LOOP.md`.

## Inputs that remain owner-controlled

- Use `setup/templates/OWNER_DECISIONS_INTAKE.md` for M6-OD-001..012.
- Standardize cross-module evidence as
  `04-artifacts/evidence/entry/M6-ENTRY-001.json` ... `M6-ENTRY-004.json`
  using `setup/templates/ENTRY_EVIDENCE.template.json`.
- Lock M6-OD-011 with `setup/Set-M6ImplementationTarget.ps1` only after the
  repository and stack are actually selected.
- Before M6.2A, run:

```powershell
& .\.venv\Scripts\python.exe scripts\validate_implementation_readiness.py --stage slice-a-entry
```

The validator must remain BLOCKED until real owner decisions, real entry
evidence, approved contracts, and Judge sign-offs exist.
