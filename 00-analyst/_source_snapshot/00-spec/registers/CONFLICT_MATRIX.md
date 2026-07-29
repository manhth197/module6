# CONFLICT_MATRIX — Module 6

Contradictions and ambiguities found in the owner document (or between the
document and pack mechanics). Per M6-RULE-018, conflicts are NEVER resolved
silently by code — each row carries the pack's recommendation for the owner to
ratify. Status OPEN until the owner decides (some rows delegate to a
DECISION_REGISTER id).

| Conflict ID | Where | The tension | Pack recommendation | Status | Source |
|---|---|---|---|---|---|
| M6-CONF-001 | doc §10 vs §13 | §10 defines contract `ads_measurement_event` (singular); §13 lists table `ads_measurement_events` (plural). Same thing or two artifacts? | Read the singular as the row contract of the plural storage table; no rename anywhere; recorded in SCHEMA_CHANGELOG as naming observation. | OPEN (low risk; pack proceeds with recommendation) | extract lines 191, 273 |
| M6-CONF-002 | doc §8 line 157, §10 line 187 | "PAYMENT_COMPLETED nếu có / nếu Core policy cho phép" — conditional revenue signal with the governing Core policy not included in this document. | Treat PAYMENT_COMPLETED as non-revenue telemetry until Core policy evidence arrives; ORDER_VERIFIED remains sole revenue source. | OPEN -> M6-OD-008 | extract lines 157, 187 |
| M6-CONF-003 | doc §6 line 104 vs §20 line 393 | Phase 1 core output includes "Retargeting Engine cơ bản", while retargeting measurement is scoped to slice M6.2I (Phase 2 band). Potential double implementation / scope gap. | Slices M6.2A–D build the retargeting data foundation (events, consent, audience outbox) only; M6.2I owns retargeting funnel measurement. No retargeting logic before M6.2I. | OPEN (pack proceeds with recommendation) | extract lines 104, 393 |
| M6-CONF-004 | doc §7 line 134 | GOLDEN_HOUR_START / REMINDER is "Tùy cấu hình" — optional events with no configuration owner stated. | Register both codes as optional/disabled by default; Gateway/Live owns emission config. | OPEN -> M6-OD-009 | extract line 134 |
| M6-CONF-005 | doc §1 line 22 vs §20/§24 | Document Control says the deliverable is NOT "Code, migration, dashboard production…", yet slices M6.2A–K and the handoff playbook prescribe implementation work. | No real conflict: line 22 describes the DOCUMENT's own nature; the slices govern future implementation executed through this pack's gated prompts. Recorded for transparency only. | RESOLVED-BY-READING (owner may veto) | extract lines 22, 384–395, 452–472 |
| M6-CONF-006 | doc §24 line 470 vs §4 line 81 | "24/7" appears as "24-7" in the §23 fail-gate row and "24/7" elsewhere. Same policy entity, two spellings. | Treat as one entity ("24/7 policy"); keep verbatim spellings in quotes; no normalization in registers. | RESOLVED-BY-READING (cosmetic) | extract lines 447, 470 |
| M6-CONF-007 | doc §16 line 317 | Scale-condition row requires "P3/P5/P6 evidence" — P6 is Module 6's own phase; the row makes Module 6 evidence an entry to its own scale gate (self-referencing). | Read P6 evidence = Module 6's event-identity evidence produced by slices M6.2A/B and re-checked at the Scale Gate; not an external dependency. ENTRY_EVIDENCE M6-ENTRY-003 covers the Core registry part. | OPEN (pack proceeds with recommendation) | extract line 317 |
