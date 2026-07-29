# Module 6 — Owner decision intake

Copy the final answer for each decision into `00-spec/registers/DECISION_REGISTER.md`
as a dated operator edit and attach an evidence note. Never replace an unknown with
a guessed value.

| Decision | Owner input required | Answer | Evidence ref | Decided at |
|---|---|---|---|---|
| M6-OD-001 | Official Phase-1 Hero SKU list |  |  |  |
| M6-OD-002 | CPA/ROAS/AOV/Verified Rate thresholds by stage |  |  |  |
| M6-OD-003 | Hash policy and fields allowed for Pixel/CAPI/Offline |  |  |  |
| M6-OD-004 | First pilot connector: Meta, Google, or both |  |  |  |
| M6-OD-005 | Primary attribution model for the Scale Gate |  |  |  |
| M6-OD-006 | Safe range for guarded auto-publish |  |  |  |
| M6-OD-007 | Locked persona/keyword/hook source list |  |  |  |
| M6-OD-008 | Core handling of PAYMENT_COMPLETED |  |  |  |
| M6-OD-009 | Golden Hour optional event configuration and owner |  |  |  |
| M6-OD-010 | Sequential/parallel slice execution approval |  |  |  |
| M6-OD-011 | Target repository and implementation stack |  |  |  |
| M6-OD-012 | Evidence masking policy |  |  |  |

For M6-OD-011, use `setup/Set-M6ImplementationTarget.ps1` after recording the
decision. The script refuses to lock a target without a language, test command,
and decision evidence reference.
