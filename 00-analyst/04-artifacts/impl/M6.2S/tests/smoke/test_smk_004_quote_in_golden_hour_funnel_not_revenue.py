"""Official smoke — slice M6.2I — M6-SMK-004 (doc ADS-P0-004), Golden Hour funnel leg.

Authored by TESTER in M6-P1803 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1804. This is the
M6.2I Phase-2 conversion-machine leg of SMK-004 (the smoke binds M6.2F + M6.2I): the M6.2F carried smoke
(test_smk_004_quote_not_revenue.py) proves the DASHBOARD verified-only revenue; this file proves the Golden Hour
FUNNEL measures a quote as a funnel stage but never as revenue, using the SAME self-enforcing RULE-003 choke.
Governance is immutable: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below
flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 404):

    Kịch bản (verbatim):          "Quote được tạo nhưng chưa order"
    Kết quả phải đạt (verbatim):  "Không revenue, không ROAS"

A QUOTE_SENT is MEASURED in the Golden Hour funnel (it counts in the Quote stage / Quote Rate numerator) but
contributes ZERO verified revenue — only a set-once ORDER_VERIFIED revenue_value is revenue (RULE-003 / FAIL-001).
The choke is self-enforcing: even a quote force-carrying a revenue_value reports 0. No ROAS is derived from a
quote — the dashboard, reading the same store, shows Revenue Verified 0 and ROAS None. Reuses the shared conftest
fixtures (make_measurement_event, make_golden_hour_funnel, measurement_store, make_dashboard_deps). All ids
synthetic; no PII.
"""
from __future__ import annotations

from app.api.dashboard import handle_dashboard_request
from app.measurement.funnel.flow import FlowStage


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_004_quote_in_funnel_is_measured_but_not_revenue(make_measurement_event, make_golden_hour_funnel):
    """M6-SMK-004 "Quote được tạo nhưng chưa order" -> "Không revenue, không ROAS" (Golden Hour funnel leg)."""
    make_measurement_event("e_q", event_code="QUOTE_SENT", live_session_id="ls_q", page_id="p")
    make_measurement_event("e_msg", event_code="MESSENGER_STARTED", live_session_id="ls_q", page_id="p")
    v = make_golden_hour_funnel().view_for("ls_q")

    assert v.stage_count(FlowStage.MESSENGER_TO_QUOTE) == 1     # the quote IS measured (funnel stage)
    assert v.rate("Quote Rate").numerator == 1                 # QUOTE_SENT counts in the Quote Rate numerator
    assert v.verified_revenue == 0.0                           # ...but it is NOT revenue (RULE-003 / FAIL-001)


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_004_neg_order_created_not_verified_is_not_revenue(make_measurement_event, make_golden_hour_funnel):
    """An ORDER_CREATED (not yet verified) is a funnel stage (Quote→Order) but never verified revenue."""
    make_measurement_event("e_oc", event_code="ORDER_CREATED", live_session_id="ls_o", page_id="p", order_code="ord_9")
    v = make_golden_hour_funnel().view_for("ls_o")
    assert v.stage_count(FlowStage.QUOTE_TO_ORDER) == 1
    assert v.verified_revenue == 0.0                           # order-created is never verified revenue


def test_smk_004_neg_quote_carrying_revenue_is_still_zero(
    measurement_store, make_measurement_event, make_golden_hour_funnel
):
    """Defense-in-depth (self-enforcing RULE-003): even if a QUOTE_SENT row ILLEGITIMATELY carried a revenue_value
    (store/materializer misuse or a mismatched event<->conversion pairing), the funnel ANDs event_code ==
    ORDER_VERIFIED with revenue presence, so it reports 0 revenue for the quote — a quote is never revenue
    (FAIL-001)."""
    make_measurement_event("e_bad_q", event_code="QUOTE_SENT", live_session_id="ls_bad", page_id="p")
    measurement_store.materialize("e_bad_q", attribution_context={}, revenue_value=500000.0,
                                  order_code="ord_bad", verified=True)
    v = make_golden_hour_funnel().view_for("ls_bad")
    assert v.verified_revenue == 0.0


def test_smk_004_neg_no_roas_from_quote_same_choke_as_dashboard(
    make_measurement_event, make_golden_hour_funnel, make_dashboard_deps
):
    """"Không ROAS": with only a quote in the store, the funnel reports 0 verified revenue AND the M6.2F dashboard
    (reading the SAME store) reports Revenue Verified 0 with ROAS None — a quote yields no ROAS on either surface,
    the same single verified-only choke (RULE-003)."""
    make_measurement_event("e_q2", event_code="QUOTE_SENT", live_session_id="ls_q2", page_id="p")
    v = make_golden_hour_funnel().view_for("ls_q2")
    assert v.verified_revenue == 0.0                           # funnel: quote is not revenue

    dv = handle_dashboard_request({}, make_dashboard_deps())
    assert dv.metric("Revenue Verified").value == 0.0          # dashboard: same 0 revenue
    assert dv.metric("ROAS").value is None                     # no revenue + no spend -> no ROAS (không ROAS)
