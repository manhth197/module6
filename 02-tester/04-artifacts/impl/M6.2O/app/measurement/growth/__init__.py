"""M6.2J Phase-3 growth-machine measurement (doc §9) — a DERIVED, READ-ONLY projection.

MEASURES the growth machine (repeat/reorder, dormant reactivation, Diamond referral, value optimization) over the
existing `ads_measurement_events` (CTR-001) + `ads_attribution_context` (CTR-002) + the Data Mart support view +
CONSUMED `customer_segments` / consent snapshots. It owns NO new table (doc §13 defines none — RULE-018), sends NO
CRM (CRM Messaging owns), computes NO commission (RULE-019 — Finance owns), decides NO member right, and never turns
the Data Mart into a trigger (RULE-012 / FAIL-005). CRM revenue is verified-only AND consent/eligibility/suppression
gated (RULE-002 / FAIL-002). Everything here is fail-closed and measure-only.
"""
