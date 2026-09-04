"""M6.2L leg 5 / M6-SMK-023 / RULE-003 / FAIL-001: verified revenue counts ONLY from ORDER_VERIFIED — at BOTH
store.materialize() (self-checks the STORED row's own event_code, not a caller boolean; drops illegitimate revenue
fail-closed WITHOUT raising) AND verified_rows() (data_mart + growth.reads event_code filter). An in-process
QUOTE_SENT row + materialize(revenue>0, verified=True) sets no revenue; dashboard Revenue Verified = 0 and ROAS is
None. A genuine ORDER_VERIFIED order is still counted (non-vacuous control).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.api.dashboard import handle_dashboard_request
from app.measurement.dashboard.data_mart import DataMart
from app.measurement.growth.reads import verified_rows as growth_verified_rows
from app.measurement.models.measurement_event import AdsMeasurementEvent

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def test_materialize_drops_revenue_on_non_order_verified_row_without_raising(measurement_store, make_measurement_event):
    make_measurement_event("e_q", event_code="QUOTE_SENT")
    # a direct caller LIES with verified=True on a QUOTE_SENT row (the audit hole) -> revenue is fail-closed dropped
    res = measurement_store.materialize(
        "e_q", attribution_context={}, revenue_value=500000.0, order_code="ord_bad", verified=True
    )
    row = measurement_store.get_by_event_id("e_q")
    assert row.revenue_value is None          # self-check on the STORED event_code dropped the illegitimate revenue
    assert row.order_code is None
    assert res.row.revenue_value is None      # no raise; the store returned a row without revenue


def test_quote_row_is_zero_on_dashboard(measurement_store, make_measurement_event, make_dashboard_deps):
    make_measurement_event("e_q2", event_code="QUOTE_SENT")
    measurement_store.materialize(
        "e_q2", attribution_context={}, revenue_value=500000.0, order_code="ord_y", verified=True
    )
    dv = handle_dashboard_request({}, make_dashboard_deps())
    assert dv.metric("Revenue Verified").value == 0.0
    assert dv.metric("ROAS").value is None     # no revenue + no spend -> no ROAS


def test_verified_rows_filter_excludes_a_leaked_quote_row_both_choke_points():
    # even if a QUOTE_SENT row somehow held a revenue_value (built directly, bypassing the store), BOTH verified_rows
    # choke points exclude it by the event_code filter (data_mart + growth.reads) — Revenue Verified stays 0.
    leaked = AdsMeasurementEvent(
        event_id="bad", event_code="QUOTE_SENT", event_ts=_TS, idempotency_key="k",
        correlation_id="c", revenue_value=999000.0, order_code="o",
    )

    class _Store:
        def all(self):
            return (leaked,)

    assert DataMart(_Store()).verified_rows() == ()
    assert DataMart(_Store()).revenue_verified() == 0.0
    assert growth_verified_rows(_Store()) == []


def test_genuine_order_verified_still_counts(make_verified_row, make_dashboard_deps):
    make_verified_row("e_v", revenue=180000.0, order_code="ORD_V", campaign_id="c", adset_id="a", ad_id="d")
    dv = handle_dashboard_request({}, make_dashboard_deps())
    assert dv.metric("Revenue Verified").value == 180000.0    # non-vacuous: a real verified order IS revenue
