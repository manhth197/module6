"""Official smoke — slice M6.2F — M6-SMK-015 (doc ADS-P0-015) / M6-FAIL-001.

Authored by TESTER in M6-P1503 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1504. Governance is
immutable: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 415):

    Kịch bản (verbatim):          "Dashboard hiển thị quote/order draft như revenue"
    Kết quả phải đạt (verbatim):  "Fail"

Dashboard revenue is verified-only BY CONSTRUCTION (RULE-003 / FAIL-001): a quote / order-draft adds 0 to any
revenue metric. And if a non-verified figure were ever presented as revenue, the Data Quality Verified-Revenue
gate returns FAIL (the worst-status overall is FAIL). Reuses shared conftest fixtures. All ids synthetic; no PII.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.api.dashboard import handle_dashboard_request
from app.measurement.dashboard.data_mart import AdsSpendRecord, ConsumedFacts
from app.measurement.models.measurement_event import AdsMeasurementEvent, DataQualityStatus
from app.measurement.quality.data_quality_check import GateItem
from app.measurement.quality.data_quality_checker import DataQualityChecker, DQContext

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def _clean_ctx(**over):
    """A clean per-signal DQ context (every fail-closed signal satisfied) so an item under test is the ONLY
    non-PASS contributor. Mirrors the coder's reference helper (test_data_quality_checker.py)."""
    base = dict(
        event_registered=True, event_owner_known=True, consent_valid=True, no_duplicate=True,
        identity_mapped=True, suppression_active=False, dashboard_has_trace=True,
    )
    base.update(over)
    return DQContext(**base)


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_015_dashboard_revenue_is_verified_only(
    make_verified_row, make_measurement_event, make_dashboard_deps
):
    """M6-SMK-015 "Dashboard hiển thị quote/order draft như revenue" -> "Fail".

    Construction guard: with one verified order + a quote + an order-draft in the same window, Revenue Verified
    counts ONLY the verified order — the quote/draft can never surface as revenue.
    """
    make_verified_row("evt_v", revenue=200000.0, order_code="ORD_9", campaign_id="c1", adset_id="a1", ad_id="ad1")
    make_measurement_event("evt_q", event_code="QUOTE_SENT")
    make_measurement_event("evt_d", event_code="ORDER_CREATED")
    consumed = ConsumedFacts(ads_spend=(AdsSpendRecord(100000.0, "c1", "a1", "ad1"),))
    view = handle_dashboard_request({}, make_dashboard_deps(consumed))
    m = {x.name: x for x in view.metrics}

    assert m["Revenue Verified"].value == 200000.0     # ONLY the verified order — never the quote/draft
    assert view.overall_data_quality == "PASS"         # every displayed figure is verified + trace-backed


def test_smk_015_dq_fails_quote_shown_as_revenue():
    """The Data Quality Verified-Revenue gate returns FAIL for a quote presented as revenue (FAIL-001)."""
    quote_as_revenue = AdsMeasurementEvent(
        event_id="q_as_rev", event_code="QUOTE_SENT", event_ts=_TS,
        idempotency_key="k_q", correlation_id="corr_q", order_code=None, revenue_value=999000.0,
    )
    res = DataQualityChecker().check(quote_as_revenue, _clean_ctx())
    assert res.item(GateItem.VERIFIED_REVENUE).status is DataQualityStatus.FAIL
    assert res.overall is DataQualityStatus.FAIL


def test_smk_015_dq_fails_order_draft_shown_as_revenue():
    """The gate equally FAILs an order-draft (ORDER_CREATED, even with an order_code) presented as revenue —
    only ORDER_VERIFIED is revenue (FAIL-001)."""
    draft_as_revenue = AdsMeasurementEvent(
        event_id="d_as_rev", event_code="ORDER_CREATED", event_ts=_TS,
        idempotency_key="k_d", correlation_id="corr_d", order_code="ORD_DRAFT", revenue_value=500000.0,
    )
    res = DataQualityChecker().check(draft_as_revenue, _clean_ctx())
    assert res.item(GateItem.VERIFIED_REVENUE).status is DataQualityStatus.FAIL
    assert res.overall is DataQualityStatus.FAIL


def test_smk_015_control_verified_revenue_item_passes():
    """Positive control (non-vacuous): a genuine ORDER_VERIFIED carrying an order_code + revenue PASSES the
    Verified-Revenue gate — so the FAILs above are discriminating, not a gate that always fails."""
    verified = AdsMeasurementEvent(
        event_id="ok_rev", event_code="ORDER_VERIFIED", event_ts=_TS,
        idempotency_key="k_v", correlation_id="corr_v", order_code="ORD_OK", revenue_value=250000.0,
    )
    res = DataQualityChecker().check(verified, _clean_ctx())
    assert res.item(GateItem.VERIFIED_REVENUE).status is DataQualityStatus.PASS
