"""M6.2F / M6-SMK-005: an ORDER_CREATED / order-draft that is NOT verified is never counted as Verified Revenue
(RULE-003, FAIL-001). "Order Draft / Order Created chưa verified -> Không tính Revenue Verified."
"""
from __future__ import annotations

from app.api.dashboard import handle_dashboard_request


def test_order_created_not_verified_is_not_revenue(make_measurement_event, make_dashboard_deps):
    make_measurement_event("evt_oc", event_code="ORDER_CREATED")   # created, NOT verified -> no revenue
    view = handle_dashboard_request({}, make_dashboard_deps())
    m = {x.name: x for x in view.metrics}

    assert m["Revenue Verified"].value == 0.0                       # draft/created is not revenue
    # it counts in the funnel denominator only
    assert m["Verified Rate"].value == 0.0                          # ORDER_VERIFIED(0) / ORDER_CREATED(1)
    assert m["Verified Rate"].source_trace == "ORDER_VERIFIED=0 / ORDER_CREATED=1"
