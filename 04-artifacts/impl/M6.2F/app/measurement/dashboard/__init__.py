"""Dashboard layer (M6.2F): the KPI data mart (support view), the 14 CTR-015 metrics (formulas verbatim, doc §14),
and the read-only GET /api/admin/ads/dashboard (CTR-018).

Revenue-bearing metrics are VERIFIED-ONLY (RULE-003): they read only the set-once Zone-B `revenue_value` M6.2E
populates on the ORDER_VERIFIED path — quote / order-draft / payment-waiting are never revenue (FAIL-001,
SMK-004/005/015). The data mart is a SUPPORT VIEW ONLY: it never writes, never triggers CRM / pricing / Diamond /
scale (RULE-012, FAIL-005, SMK-010). Alert thresholds are M6-OD-002 (OPEN) — none are invented here.
"""
