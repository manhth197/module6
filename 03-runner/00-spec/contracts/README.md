# 00-spec/contracts — operator-applied contract schemas

This folder starts EMPTY by design. It is filled by the OPERATOR (never by an
AI executor — all execution roles are denied writes to `00-spec/`) after the
CONTRACT_HARMONIZATION gate judge (M6-P0715) signs off:

1. Copy each approved `*.contract.yaml` from `04-artifacts/analysis/contracts/`
   into this folder.
2. Flip the matching row in `../registers/CONTRACT_REGISTER.md` from
   `MISSING / OWNER_DECISION_REQUIRED` to `DRAFT_LOCKED`, citing the judge
   sign-off file.
3. Append a row to `../registers/SCHEMA_CHANGELOG.md` per contract.
4. Run `setup\Repair-M6RoleJunctions.ps1` to refresh role snapshots.

Tie-break rule: if a file here ever disagrees with an approved harmonization
output or the SPEC's locked YAML contracts, raise a Conflict Matrix row —
`00-spec/` canon is corrected only via the operator with a changelog entry,
never silently.
