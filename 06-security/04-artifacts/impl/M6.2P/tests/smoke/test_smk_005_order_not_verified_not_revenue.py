"""Official smoke — slice M6.2F — M6-SMK-005 (doc ADS-P0-005).

Authored by TESTER in M6-P1503 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1504
(TESTER_RUN -> 04-artifacts/test-reports/M6.2F/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 405):

    Kịch bản (verbatim):          "Order Draft / Order Created chưa verified"
    Kết quả phải đạt (verbatim):  "Không tính Revenue Verified"

An ORDER_CREATED / order-draft that is NOT verified is never counted as Revenue Verified (RULE-003 / FAIL-001):
revenue is materialized ONLY on the ORDER_VERIFIED path (set-once Zone-B). The draft is MEASURED in the funnel
denominator only. Reuses shared conftest fixtures. All ids synthetic; no PII.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.api.dashboard import handle_dashboard_request
from app.measurement.models.measurement_event import AdsMeasurementEvent, DataQualityStatus
from app.measurement.quality.data_quality_check import GateItem
from app.measurement.quality.data_quality_checker import DataQualityChecker, DQContext

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_005_order_created_not_counted_as_verified_revenue(make_measurement_event, make_dashboard_deps):
    """M6-SMK-005 "Order Draft / Order Created chưa verified" -> "Không tính Revenue Verified"."""
    make_measurement_event("evt_oc", event_code="ORDER_CREATED")   # created, NOT verified -> no revenue
    view = handle_dashboard_request({}, make_dashboard_deps())
    m = {x.name: x for x in view.metrics}

    assert m["Revenue Verified"].value == 0.0                       # draft/created is NOT revenue
    assert m["Verified Rate"].value == 0.0                          # ORDER_VERIFIED(0) / ORDER_CREATED(1)
    assert m["Verified Rate"].source_trace == "ORDER_VERIFIED=0 / ORDER_CREATED=1"


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_005_neg_draft_conversion_materializes_no_revenue(
    make_measurement_event, make_conversion, attribution_materializer, measurement_store
):
    """The set-once Zone-B revenue writer fires ONLY for ORDER_VERIFIED: an ORDER_CREATED conversion that even
    carries a revenue_value records attribution but NO revenue / order_code (RULE-003 / FAIL-001)."""
    event = make_measurement_event("evt_draft", event_code="ORDER_CREATED", page_id="p", campaign_id="camp_1")
    conv = make_conversion(
        "ORDER_CREATED", source_event_id="evt_draft", revenue_value=250000.0, currency="VND", order_code="ORD_D"
    )
    attribution_materializer.materialize(event, conv)
    row = measurement_store.get_by_event_id("evt_draft")
    assert row.revenue_value is None, "an unverified order-draft never carries revenue (FAIL-001)"
    assert row.order_code is None


def test_smk_005_neg_draft_carrying_revenue_is_dq_fail():
    """A (fabricated) ORDER_CREATED row carrying a revenue figure FAILs the Data Quality Verified-Revenue gate —
    an order-draft counted as revenue is FAIL-001. The store would never persist it; the checker catches it."""
    draft_with_revenue = AdsMeasurementEvent(
        event_id="bad_draft", event_code="ORDER_CREATED", event_ts=_TS,
        idempotency_key="k_d", correlation_id="corr_d", order_code=None, revenue_value=250000.0,
    )
    res = DataQualityChecker().check(
        draft_with_revenue,
        DQContext(event_registered=True, event_owner_known=True, consent_valid=True,
                  no_duplicate=True, identity_mapped=True, suppression_active=False, dashboard_has_trace=True),
    )
    assert res.item(GateItem.VERIFIED_REVENUE).status is DataQualityStatus.FAIL
    assert res.overall is DataQualityStatus.FAIL


def test_smk_005_control_verified_order_is_counted(make_verified_row, make_dashboard_deps):
    """Positive control (non-vacuous): the SAME dashboard DOES count a genuine ORDER_VERIFIED as revenue, so the
    'not counted' assertions above are discriminating, not a dead dashboard."""
    make_verified_row("evt_v", revenue=180000.0, order_code="ORD_V", campaign_id="c1", adset_id="a1", ad_id="ad1")
    view = handle_dashboard_request({}, make_dashboard_deps())
    m = {x.name: x for x in view.metrics}
    assert m["Revenue Verified"].value == 180000.0                 # a verified order IS revenue
