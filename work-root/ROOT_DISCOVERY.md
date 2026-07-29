# ROOT_DISCOVERY — Module 6 build pack

**Prompt**: M6-P0002 (ROOT_DISCOVERY) · Role: PM_ORCHESTRATOR · Mode: analysis_only
**Recorded**: 2026-07-20 · Read-only discovery; nothing modified except this note and the evidence JSON.

## 1. Absolute pack root

```
D:\M6\Module6-workspace
```

This is the `PM_ORCHESTRATOR,JUDGE` pack-root session folder. Its `00-spec`,
`04-artifacts`, `registry`, `scripts`, `scripts-win` are **real directories**
(the junction *sources*), not reparse points — confirmed `00-spec`
`isReparsePoint=False` at root.

## 2. Top-level layout

Directories at pack root (none are reparse points):

`.claude`, `.venv`, `00-analyst`, `00-spec`, `01-coder`, `02-tester`,
`03-runner`, `04-artifacts`, `04-boundary`, `05-judge`, `06-security`,
`registry`, `scripts`, `scripts-win`, `setup`, `work-root`

## 3. Role folders

| Folder | Kind | own CLAUDE.md | own .claude | _source_snapshot | Junctions |
|---|---|---|---|---|---|
| 00-analyst | role-session | yes | yes | yes | 5 |
| 01-coder | role-session | yes | yes | yes | 5 |
| 02-tester | role-session | yes | yes | yes | 5 |
| 03-runner | role-session | yes | yes | yes | 5 |
| 04-boundary | role-session | yes | yes | yes | 5 |
| 06-security | role-session | yes | yes | yes | 5 |
| 05-judge | judge-output (not a session) | no | no | n/a | 0 |

**05-judge note**: not a junction-based role-session folder — it holds
`README.md` only, is not a reparse point, and has no `CLAUDE.md`/`.claude`.
This is expected: JUDGE runs from the **pack root** under the combined
`PM_ORCHESTRATOR,JUDGE` role, and `05-judge/` is a write-target for judge
sign-offs (it is in this role's allowed write roots). Its absence of junctions
is by design, not a broken link.

## 4. Role junctions and targets

Each of the 6 role-session folders contains an identical set of 5 junctions
(`dir /AL` equivalent via `Get-Item` `LinkType=Junction`). Canonical set (same
for every role-session folder `<ROLE>`):

| Junction | LinkType | Target | Resolves | Under pack root |
|---|---|---|---|---|
| `<ROLE>\00-spec` | Junction | `D:\M6\Module6-workspace\00-spec` | yes | yes |
| `<ROLE>\04-artifacts` | Junction | `D:\M6\Module6-workspace\04-artifacts` | yes | yes |
| `<ROLE>\registry` | Junction | `D:\M6\Module6-workspace\registry` | yes | yes |
| `<ROLE>\scripts` | Junction | `D:\M6\Module6-workspace\scripts` | yes | yes |
| `<ROLE>\scripts-win` | Junction | `D:\M6\Module6-workspace\scripts-win` | yes | yes |

Applied across `00-analyst, 01-coder, 02-tester, 03-runner, 04-boundary,
06-security` = **30 junctions total**.

## 5. Resolution verdict

- **TOTAL_JUNCTIONS = 30**
- **ALL_RESOLVE = True** (every junction target passes `Test-Path`)
- **ALL_UNDER_ROOT = True** (every target begins with `D:\M6\Module6-workspace`)

Every role junction resolves to the **current** pack root. No dangling
junction, no target pointing outside the current root (i.e. no stale
target from a moved/copied pack). Fallback `_source_snapshot/` is present in
each role-session folder for the broken-junction case, but is not needed here.

## 6. Method (read-only)

- `(Get-Item .).FullName` — pack root
- `Get-ChildItem -Directory -Force` + `ReparsePoint` attribute test — top-level layout
- Per role: `Get-ChildItem -Force | ? {ReparsePoint}` → `.Name`, `.LinkType`,
  `.Target`; then `Test-Path` on target and prefix-match against pack root
- No junction was created, repaired, or removed.
