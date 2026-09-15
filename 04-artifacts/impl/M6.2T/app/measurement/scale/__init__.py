"""Scale Gate layer (M6.2G): the doc §16 Scale Gate as an owner-decision workflow — compute the 8 scale
conditions, assemble evidence, PROPOSE an inert `ads_scale_request`; NEVER act.

RULE-010 / FAIL-006: Module 6 has NO executable scale path. It never raises a budget, enables a campaign, opens
audience scale, or publishes — those are OWNER actions performed outside Module 6, gated by production_flag=OFF.
`budget_cap` / `rollback_condition` are request FIELDS, not actions; "approved" is a recorded owner decision, not
a trigger. The Risk row is a HARD VETO (RULE-017), re-checked at approval. In the current staged posture the gate
is fail-closed (M6-OD-002 thresholds + M6-OD-005 scale model OPEN) — it can never compute a clean scale-ready PASS.
"""
