"""M6.2F leg 1 / M6-SMK-006: an ORDER_VERIFIED with full campaign/adset/ad → the dashboard's ROAS / CPA / AOV
update from VERIFIED revenue only (RULE-003, FAIL-001). The revenue is the set-once Zone-B value the M6.2E
materializer wrote on the ORDER_VERIFIED path.
"""
from __future__ import annotations

from app.api.dashboard import handle_dashboard_request
from app.measurement.dashboard.data_mart import AdsSpendRecord, ConsumedFacts


def test_verified_order_updates_roas_cpa_aov(make_verified_row, make_dashboard_deps):
    make_verified_row(
        "evt_v1", revenue=250000.0, order_code="ORD_1", page_id="p_home",
        campaign_id="c1", adset_id="a1", ad_id="ad1",
    )
    consumed = ConsumedFacts(ads_spend=(AdsSpendRecord(100000.0, "c1", "a1", "ad1"),))
    view = handle_dashboard_request({}, make_dashboard_deps(consumed))
    m = {x.name: x for x in view.metrics}

    assert m["Revenue Verified"].value == 250000.0
    assert m["Ads Spend"].value == 100000.0
    assert m["ROAS"].value == 2.5           # 250000 / 100000
    assert m["CPA"].value == 100000.0       # spend / number_of_ORDER_VERIFIED(1)
    assert m["AOV"].value == 250000.0       # revenue / verified_orders(1)
    # evidence-first: revenue metrics carry a trace + a (masked) sample evidence ref
    assert m["Revenue Verified"].has_trace_and_evidence
    assert view.overall_data_quality == "PASS"
