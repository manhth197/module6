-- Migration 0008 — create ads_dashboard_kpi_source (M6-CTR-018/015 read path) as a READ-ONLY SUPPORT VIEW
-- STAGED per 04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json (live_migrations=false): NEVER applied here.
--
-- RULE-012 / FAIL-005 (SMK-010): the Data Mart / dashboard read path is a SUPPORT VIEW ONLY. It is a VIEW (not a
-- table, not a materialized trigger) so it can never become a trigger owner for CRM / pricing / Diamond / budget
-- scale — it only reads ads_measurement_events. RULE-003 / FAIL-001 (SMK-004/005/015): VERIFIED-ONLY revenue —
-- verified revenue is `revenue_value` and is non-NULL ONLY on the ORDER_VERIFIED path (Zone-B set-once); a quote /
-- order-draft (revenue_value IS NULL) contributes ZERO revenue. Alert thresholds are M6-OD-002 (OPEN) — none here.
-- Applies AFTER 0002 (and 0006). At the M6-OD-011 integration step the owner grants SELECT-only on this view.

-- ============================================================ UP
CREATE VIEW ads_dashboard_kpi_source AS
SELECT
    event_id,
    event_code,
    campaign_id,
    adset_id,
    ad_id,
    page_id,
    live_session_id,
    order_code,
    -- VERIFIED-ONLY revenue: non-NULL ONLY when the row was materialized on the ORDER_VERIFIED path (RULE-003).
    -- A quote / order-draft row has revenue_value IS NULL here, so it can never be summed as revenue (FAIL-001).
    revenue_value            AS verified_revenue,
    attribution_context,
    data_quality_status
FROM ads_measurement_events
WHERE revenue_value IS NULL OR order_code IS NOT NULL;   -- defense-in-depth: revenue only alongside an order_code

-- Illustrative access control at integration time (NOT executed here): the dashboard role gets SELECT only.
--   GRANT SELECT ON ads_dashboard_kpi_source TO ads_dashboard_reader;
--   -- no INSERT/UPDATE/DELETE and no trigger is ever attached (support view only, RULE-012).

-- ============================================================ DOWN (rollback)
-- Staged now => documented, not executed.
-- DROP VIEW ads_dashboard_kpi_source;
