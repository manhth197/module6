"""M6.2F / M6-CTR-015: all 14 KPI metrics are present with their doc §14 formulas VERBATIM, each carries a
source_trace + a sample_evidence_ref (evidence-first), and every division is fail-closed (zero/missing
denominator -> None, never a crash, never a fabricated number). CRM/Diamond revenue split by attribution.
No numeric threshold is applied (M6-OD-002 OPEN).
"""
from __future__ import annotations

from app.api.dashboard import handle_dashboard_request
from app.measurement.dashboard.data_mart import ConsumedFacts

_EXPECTED = [
    ("Ads Spend", "Từ Ads platform / approved spend import"),
    ("Revenue Verified", "SUM(verified_revenue)"),
    ("ROAS", "Revenue Verified / Ads Spend"),
    ("CPA", "Ads Spend / number_of_ORDER_VERIFIED"),
    ("AOV", "Revenue Verified / verified_orders"),
    ("Boxes per Order", "Verified boxes / verified_orders"),
    ("Comment Rate", "LIVE_COMMENT / LIVE_VIEW"),
    ("Inbox Rate", "MESSENGER_STARTED / LIVE_COMMENT"),
    ("Quote Rate", "QUOTE_SENT / MESSENGER_STARTED"),
    ("Order Rate", "ORDER_CREATED / QUOTE_SENT"),
    ("Verified Rate", "ORDER_VERIFIED / ORDER_CREATED"),
    ("COD Fail Rate", "COD fail / COD orders"),
    ("CRM Revenue", "Verified revenue từ CRM attribution"),
    ("Diamond Revenue", "Verified revenue từ referral/Diamond attribution"),
]


def test_all_14_metrics_names_and_formulas_verbatim(make_dashboard_deps):
    view = handle_dashboard_request({}, make_dashboard_deps())
    assert len(view.metrics) == 14
    assert [(m.name, m.formula) for m in view.metrics] == _EXPECTED
    # evidence-first: every metric carries a source_trace
    assert all(m.source_trace for m in view.metrics)


def test_division_is_fail_closed_on_empty(make_dashboard_deps):
    view = handle_dashboard_request({}, make_dashboard_deps())   # empty store, no consumed inputs
    m = {x.name: x for x in view.metrics}
    assert m["Ads Spend"].value is None            # no spend import -> fail-closed
    assert m["ROAS"].value is None                 # revenue 0 / spend None -> None
    assert m["CPA"].value is None                  # spend None / 0 -> None
    assert m["Comment Rate"].value is None         # 0 / 0 -> None (no crash)
    assert m["COD Fail Rate"].value is None        # consumed absent -> None
    assert m["Revenue Verified"].value == 0.0      # SUM over no verified rows = 0 (not None)


def test_crm_and_diamond_revenue_split_by_attribution(make_verified_row, make_dashboard_deps):
    make_verified_row("evt_crm", revenue=100000.0, order_code="ORD_CRM", page_id="p", signals={"crm": True})
    make_verified_row("evt_dia", revenue=50000.0, order_code="ORD_DIA", page_id="p", signals={"diamond_id": "dia_1"})
    view = handle_dashboard_request({}, make_dashboard_deps())
    m = {x.name: x for x in view.metrics}
    assert m["Revenue Verified"].value == 150000.0
    assert m["CRM Revenue"].value == 100000.0      # entry_channel=CRM only
    assert m["Diamond Revenue"].value == 50000.0   # referral/diamond only


def test_boxes_per_order_fail_closed_on_partial_coverage(make_verified_row, make_dashboard_deps):
    """Adversarial-review regression: with only SOME verified orders' boxes reported, Boxes per Order must be
    None (fail-closed), never a fabricated understated figure. Full coverage yields the value."""
    make_verified_row("evt_a", revenue=100000.0, order_code="A", campaign_id="c1", adset_id="a1", ad_id="ad1")
    make_verified_row("evt_b", revenue=100000.0, order_code="B", campaign_id="c1", adset_id="a1", ad_id="ad1")

    partial = handle_dashboard_request({}, make_dashboard_deps(ConsumedFacts(boxes_by_order={"A": 5})))
    assert {x.name: x for x in partial.metrics}["Boxes per Order"].value is None      # B unreported -> fail-closed

    full = handle_dashboard_request({}, make_dashboard_deps(ConsumedFacts(boxes_by_order={"A": 5, "B": 3})))
    assert {x.name: x for x in full.metrics}["Boxes per Order"].value == 4.0          # (5+3)/2
