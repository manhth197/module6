"""M6.2F leg 1 / M6-SMK-015 / M6-FAIL-001: a quote / order-draft can NEVER appear as a revenue figure. Dashboard
revenue == verified-only; the Data Quality Verified-Revenue item FAILs if a non-verified figure is counted as
revenue. "Dashboard hiển thị quote/order draft như revenue -> Fail."
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.api.dashboard import handle_dashboard_request
from app.measurement.dashboard.data_mart import AdsSpendRecord, ConsumedFacts
from app.measurement.models.measurement_event import AdsMeasurementEvent, DataQualityStatus
from app.measurement.quality.data_quality_check import GateItem
from app.measurement.quality.data_quality_checker import DataQualityChecker, DQContext

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def test_dashboard_revenue_counts_only_verified(make_verified_row, make_measurement_event, make_dashboard_deps):
    # one verified order + a quote + an order-draft, same window
    make_verified_row("evt_v", revenue=200000.0, order_code="ORD_9", campaign_id="c1", adset_id="a1", ad_id="ad1")
    make_measurement_event("evt_q", event_code="QUOTE_SENT")
    make_measurement_event("evt_d", event_code="ORDER_CREATED")
    consumed = ConsumedFacts(ads_spend=(AdsSpendRecord(100000.0, "c1", "a1", "ad1"),))
    view = handle_dashboard_request({}, make_dashboard_deps(consumed))
    m = {x.name: x for x in view.metrics}

    assert m["Revenue Verified"].value == 200000.0     # ONLY the verified order — never the quote/draft
    assert view.overall_data_quality == "PASS"         # every displayed figure is verified + trace-backed


def test_dq_verified_revenue_item_fails_on_unverified_revenue():
    # a (fabricated) row that carries revenue on a NON-verified event — the DQ Verified-Revenue item FAILs,
    # and the worst-status overall is FAIL (FAIL-001). The store would never persist this; the checker catches it.
    bad = AdsMeasurementEvent(
        event_id="bad_rev", event_code="QUOTE_SENT", event_ts=_TS,
        idempotency_key="k_bad", correlation_id="corr_bad", order_code=None, revenue_value=999000.0,
    )
    res = DataQualityChecker().check(
        bad, DQContext(event_registered=True, event_owner_known=True, consent_valid=True,
                       no_duplicate=True, identity_mapped=True, dashboard_has_trace=True)
    )
    assert res.item(GateItem.VERIFIED_REVENUE).status is DataQualityStatus.FAIL
    assert res.overall is DataQualityStatus.FAIL
