"""M6.2I leg L1 / M6-RULE-021: order-capture signals are measured, but an order is "commerce-gate-passed" ONLY
when a CONSUMED Commerce signal says its stock/fulfillment/trust/policy + customer-confirmation gate passed BEFORE
send-to-Core. Absent -> not-validated (fail-closed). Module 6 RECORDS the flag; it never performs/owns/bypasses
that validation.
"""
from __future__ import annotations


def _seed_order_session(make_measurement_event, make_verified_row, ls="ls_r21", order="ord_r21"):
    make_measurement_event("e_oc", event_code="ORDER_CREATED", live_session_id=ls, page_id="p", order_code=order)
    make_verified_row("e_ov", revenue=120000.0, order_code=order, live_session_id=ls, page_id="p")
    return ls, order


def test_capture_gate_passed_only_with_consumed_flag(make_measurement_event, make_verified_row, make_golden_hour_funnel):
    ls, order = _seed_order_session(make_measurement_event, make_verified_row)
    v = make_golden_hour_funnel(capture_gate_passed_by_order={order: True}).view_for(ls)
    assert v.capture_gate_passed is True          # consumed Commerce-gate flag present + True


def test_capture_gate_absent_is_fail_closed(make_measurement_event, make_verified_row, make_golden_hour_funnel):
    ls, _order = _seed_order_session(make_measurement_event, make_verified_row)
    v = make_golden_hour_funnel().view_for(ls)     # no consumed capture flag wired
    assert v.capture_gate_passed is False          # fail-closed: not-validated


def test_capture_gate_explicit_false_is_not_passed(make_measurement_event, make_verified_row, make_golden_hour_funnel):
    ls, order = _seed_order_session(make_measurement_event, make_verified_row)
    v = make_golden_hour_funnel(capture_gate_passed_by_order={order: False}).view_for(ls)
    assert v.capture_gate_passed is False


def test_funnel_never_performs_commerce_validation(make_golden_hour_funnel):
    """RULE-021: the funnel only RECORDS the consumed flag; it exposes no verb that would validate an order or
    change order state (that is Commerce/M8-owned)."""
    funnel = make_golden_hour_funnel()
    for verb in ("validate_order", "validate", "send_to_core", "set_order_state", "confirm_order",
                 "capture_order", "create_order", "order_state"):
        assert not hasattr(funnel, verb), f"funnel exposes order-ownership verb {verb!r} (RULE-021 breach)"
