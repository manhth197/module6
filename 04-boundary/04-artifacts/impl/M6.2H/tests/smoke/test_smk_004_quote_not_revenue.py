"""Official smoke — slice M6.2F — M6-SMK-004 (doc ADS-P0-004).

Authored by TESTER in M6-P1503 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1504
(TESTER_RUN -> 04-artifacts/test-reports/M6.2F/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 404):

    Kịch bản (verbatim):          "Quote được tạo nhưng chưa order"
    Kết quả phải đạt (verbatim):  "Không revenue, không ROAS"

A QUOTE_SENT with no verified order contributes ZERO to Revenue Verified and yields NO ROAS from the quote
(RULE-003 / FAIL-001 — only the set-once Zone-B revenue of an ORDER_VERIFIED is revenue). The quote is still
MEASURED (it counts in the funnel), it is just never revenue. Reuses shared conftest fixtures
(make_measurement_event, make_dashboard_deps). All ids synthetic; no PII.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.api.dashboard import handle_dashboard_request
from app.measurement.dashboard.data_mart import AdsSpendRecord, ConsumedFacts
from app.measurement.models.measurement_event import AdsMeasurementEvent, DataQualityStatus
from app.measurement.quality.data_quality_check import GateItem
from app.measurement.quality.data_quality_checker import DataQualityChecker, DQContext

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_004_quote_is_not_revenue_and_no_roas(make_measurement_event, make_dashboard_deps):
    """M6-SMK-004 "Quote được tạo nhưng chưa order" -> "Không revenue, không ROAS".

    A QUOTE_SENT event, with real ads spend present, still yields 0 Revenue Verified and no ROAS from the quote.
    """
    make_measurement_event("evt_q", event_code="QUOTE_SENT")   # a quote; never materialized as revenue
    consumed = ConsumedFacts(ads_spend=(AdsSpendRecord(100000.0, "c1", "a1", "ad1"),))
    view = handle_dashboard_request({}, make_dashboard_deps(consumed))
    m = {x.name: x for x in view.metrics}

    assert m["Revenue Verified"].value == 0.0          # the quote is NOT revenue
    assert m["ROAS"].value == 0.0                      # 0 verified revenue / spend -> no ROAS from the quote
    assert m["AOV"].value is None                      # no verified orders -> fail-closed (0 denominator)
    # the quote IS measured — it counts in the funnel (Quote Rate numerator), just never as revenue
    assert m["Quote Rate"].source_trace.startswith("QUOTE_SENT=1")


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_004_neg_no_spend_roas_is_fail_closed(make_measurement_event, make_dashboard_deps):
    """No ads-spend import + only a quote: ROAS is fail-closed None (0 revenue / None spend), never fabricated,
    and Revenue Verified stays 0.0 (a quote is measured but is not revenue)."""
    make_measurement_event("evt_q2", event_code="QUOTE_SENT")
    view = handle_dashboard_request({}, make_dashboard_deps())   # no consumed spend
    m = {x.name: x for x in view.metrics}

    assert m["Revenue Verified"].value == 0.0
    assert m["ROAS"].value is None                     # denominator absent -> fail-closed (no ROAS)


def test_smk_004_neg_quote_carrying_revenue_is_dq_fail():
    """Defense-in-depth: a (fabricated) QUOTE_SENT row that carries a revenue figure is caught by the Data
    Quality Verified-Revenue gate as FAIL (a quote can never be counted as revenue, RULE-003 / FAIL-001). The
    store would never persist this; the checker catches it."""
    quote_with_revenue = AdsMeasurementEvent(
        event_id="bad_quote", event_code="QUOTE_SENT", event_ts=_TS,
        idempotency_key="k_q", correlation_id="corr_q", order_code=None, revenue_value=250000.0,
    )
    res = DataQualityChecker().check(
        quote_with_revenue,
        DQContext(event_registered=True, event_owner_known=True, consent_valid=True,
                  no_duplicate=True, identity_mapped=True, suppression_active=False, dashboard_has_trace=True),
    )
    assert res.item(GateItem.VERIFIED_REVENUE).status is DataQualityStatus.FAIL
    assert res.overall is DataQualityStatus.FAIL      # worst-status dominates -> the display is a FAIL
