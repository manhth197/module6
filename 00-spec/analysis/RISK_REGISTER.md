# RISK_REGISTER — Module 6 build pack

| Risk ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| M6-RISK-001 | Executor conflates ORDER_SUCCESS with ORDER_VERIFIED and counts unverified revenue | Medium | Critical (M6-FAIL-001) | Rule M6-RULE-003 in every revenue-adjacent prompt; smokes M6-SMK-004/005/015; boundary adversary tries it explicitly |
| M6-RISK-002 | Direct external send slips in during M6.2B (before outbox exists) | Medium | High (M6-FAIL-002/consent) | M6.2B out-of-scope list forbids external sends; security prompt greps for platform SDK calls outside workers |
| M6-RISK-003 | OPEN owner decisions (M6-OD-002/003/005/006) stall slice exits | High | Medium | Decision "Blocks" column limits blast radius; prompts mark BLOCKED narrowly, plan legs proceed |
| M6-RISK-004 | Junctions break after the pack is moved/copied | High | Medium | `Repair-M6RoleJunctions.ps1` + `_source_snapshot/00-spec/` fallback with sha256 manifest |
| M6-RISK-005 | Prompt index and prompt XML entry gates drift | Medium | High (gate bypass) | Single generator emits both; validator cross-checks every prompt |
| M6-RISK-006 | PII/token leaks into evidence (Vietnamese phone formats) | Medium | High (M6-FAIL-008) | Two-pattern phone scan in hooks + gate + whole-repo scan; PII/trap batteries prove behavior |
| M6-RISK-007 | Judge session judges from memory instead of evidence | Medium | High | Operating loop mandates FRESH judge session; judge prompts enumerate exact evidence files to open |
| M6-RISK-008 | Executor edits the state ledger to self-advance | Low | Critical (M6-FAIL-009) | Every role (incl. runner role folder) denies `04-artifacts/state/`; hooks block; gate validates transitions |
| M6-RISK-009 | Cross-module entry evidence never arrives (M6-ENTRY-001..003) | Medium | High | Checked at BOOTSTRAP readiness + M6.2A entry judge; slices stay BLOCKED, fail-closed |
| M6-RISK-010 | Learning/creative prompts generate public copy without the claim/lexicon lock | Low | High (brand/claim risk) | LEXICON_REGISTER missing-row rule: framework only until M6-OD-007 resolves |
