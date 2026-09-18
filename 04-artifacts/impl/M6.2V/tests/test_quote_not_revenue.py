"""M6.2F / M6-SMK-004: a QUOTE_SENT with no verified order contributes NO revenue and NO ROAS (RULE-003,
FAIL-001). "Quote được tạo nhưng chưa order -> Không revenue, không ROAS."
"""
from __future__ import annotations

from app.api.dashboard import handle_dashboard_request
from app.measurement.dashboard.data_mart import AdsSpendRecord, ConsumedFacts


def test_quote_contributes_no_revenue_no_roas(make_measurement_event, make_dashboard_deps):
    make_measurement_event("evt_q", event_code="QUOTE_SENT")   # a quote; never materialized as revenue
    consumed = ConsumedFacts(ads_spend=(AdsSpendRecord(50000.0, "c1", "a1", "ad1"),))
    view = handle_dashboard_request({}, make_dashboard_deps(consumed))
    m = {x.name: x for x in view.metrics}

    assert m["Revenue Verified"].value == 0.0          # the quote is NOT revenue
    assert m["ROAS"].value == 0.0                      # 0 revenue / spend -> no ROAS from the quote
    assert m["AOV"].value is None                      # no verified orders -> fail-closed (0 denominator)
    # the quote DOES count in the funnel (Quote Rate numerator) — measured, just never revenue
    assert m["Quote Rate"].source_trace.startswith("QUOTE_SENT=1")
