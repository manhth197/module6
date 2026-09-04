"""M6.2I leg L2 / M6-SMK-004 / M6-RULE-003 / M6-FAIL-001: "Quote được tạo nhưng chưa order" -> "Không revenue".
A QUOTE_SENT is MEASURED in the funnel (it counts in the Quote stage / Quote Rate) but contributes ZERO verified
revenue — only a set-once ORDER_VERIFIED revenue_value is revenue.
"""
from __future__ import annotations

from app.measurement.funnel.flow import FlowStage


def test_quote_counts_in_funnel_but_is_not_revenue(make_measurement_event, make_golden_hour_funnel):
    make_measurement_event("e_q", event_code="QUOTE_SENT", live_session_id="ls_q", page_id="p")
    make_measurement_event("e_msg", event_code="MESSENGER_STARTED", live_session_id="ls_q", page_id="p")
    v = make_golden_hour_funnel().view_for("ls_q")

    assert v.stage_count(FlowStage.MESSENGER_TO_QUOTE) == 1     # the quote IS measured (funnel stage)
    assert v.rate("Quote Rate").numerator == 1                 # QUOTE_SENT counts in the Quote Rate numerator
    assert v.verified_revenue == 0.0                           # ...but it is NOT revenue (RULE-003 / FAIL-001)


def test_order_created_without_verify_is_still_not_revenue(make_measurement_event, make_golden_hour_funnel):
    """SMK-005-adjacent inside the funnel: an ORDER_CREATED (not yet verified) is a funnel stage, never revenue."""
    make_measurement_event("e_oc", event_code="ORDER_CREATED", live_session_id="ls_o", page_id="p", order_code="ord_9")
    v = make_golden_hour_funnel().view_for("ls_o")
    assert v.stage_count(FlowStage.QUOTE_TO_ORDER) == 1
    assert v.verified_revenue == 0.0                           # order-created is never verified revenue


def test_quote_carrying_revenue_is_still_zero_in_funnel(measurement_store, make_measurement_event, make_golden_hour_funnel):
    """Defense-in-depth (adversarial review): even if a QUOTE_SENT row ILLEGITIMATELY carried a revenue_value
    (store/materializer misuse, or a mismatched event↔conversion pairing), the funnel's self-enforcing RULE-003
    choke — ANDing event_code == ORDER_VERIFIED with revenue presence — reports 0 revenue for it (never a quote)."""
    make_measurement_event("e_bad_q", event_code="QUOTE_SENT", live_session_id="ls_bad", page_id="p")
    # bypass the normal ORDER_VERIFIED materialize path and force revenue onto the QUOTE_SENT row
    measurement_store.materialize("e_bad_q", attribution_context={}, revenue_value=500000.0,
                                  order_code="ord_bad", verified=True)
    v = make_golden_hour_funnel().view_for("ls_bad")
    assert v.verified_revenue == 0.0        # a quote is NEVER revenue, even carrying a (bad) revenue_value (RULE-003)


def test_quote_in_funnel_matches_dashboard_smk_004(make_measurement_event, make_dashboard_deps, make_golden_hour_funnel):
    """Cross-check: the funnel's verified-only rule is the SAME single choke the M6.2F dashboard uses — a quote is
    0 revenue on BOTH surfaces (no divergence between the funnel and the KPI dashboard), both reading the same
    measurement store."""
    from app.api.dashboard import handle_dashboard_request
    make_measurement_event("e_q2", event_code="QUOTE_SENT", live_session_id="ls_q2", page_id="p")
    dv = handle_dashboard_request({}, make_dashboard_deps())
    assert dv.metric("Revenue Verified").value == 0.0          # dashboard (M6.2F): quote is not revenue
    v = make_golden_hour_funnel().view_for("ls_q2")
    assert v.verified_revenue == 0.0                           # funnel (M6.2I): same choke, same answer
