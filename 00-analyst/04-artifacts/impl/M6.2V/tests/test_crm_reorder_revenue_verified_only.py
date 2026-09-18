"""M6.2J leg L1 / M6-RULE-002/003 / M6-FAIL-001/002: CRM Revenue counts ONLY verified revenue on CRM-attributed
ORDER_VERIFIED rows where CRM-eligibility + suppression + consent ALL pass. A click/chat / CRM_REORDER_SENT is
never revenue; any missing/failing gate ⇒ excluded (fail-closed).
"""
from __future__ import annotations

from app.measurement.growth.crm import CrmConsumed


def _all_pass_consumed(make_crm_consent, order="ord_crm"):
    return CrmConsumed(
        crm_eligible_orders={order: True},
        suppression_pass_orders={order: True},
        consent_by_order={order: make_crm_consent()},          # VALID + CRM scope
    )


def test_crm_revenue_counts_only_when_all_gates_pass(make_verified_row, make_crm_measurement, make_crm_consent):
    make_verified_row("ev_crm", revenue=300000.0, order_code="ord_crm", signals={"crm": True})   # CRM-attributed
    m = make_crm_measurement(_all_pass_consumed(make_crm_consent))
    assert m.crm_revenue() == 300000.0


def test_crm_revenue_excludes_ineligible_or_unsuppressed(make_verified_row, make_crm_measurement, make_crm_consent):
    make_verified_row("ev_crm2", revenue=300000.0, order_code="ord_crm", signals={"crm": True})
    # eligibility fails
    m1 = make_crm_measurement(CrmConsumed(crm_eligible_orders={"ord_crm": False},
                                          suppression_pass_orders={"ord_crm": True},
                                          consent_by_order={"ord_crm": make_crm_consent()}))
    assert m1.crm_revenue() == 0.0
    # suppression not cleared (absent) -> fail-closed
    m2 = make_crm_measurement(CrmConsumed(crm_eligible_orders={"ord_crm": True},
                                          consent_by_order={"ord_crm": make_crm_consent()}))
    assert m2.crm_revenue() == 0.0


def test_crm_revenue_excludes_when_no_consumed_facts(make_verified_row, make_crm_measurement):
    """Fail-closed: a CRM verified row with NO consumed eligibility/suppression/consent contributes 0."""
    make_verified_row("ev_crm3", revenue=300000.0, order_code="ord_crm", signals={"crm": True})
    assert make_crm_measurement().crm_revenue() == 0.0


def test_crm_reorder_sent_event_is_not_revenue(make_measurement_event, make_crm_measurement, make_crm_consent):
    """A CRM_REORDER_SENT engagement event carries no revenue_value and is never counted as CRM Revenue."""
    make_measurement_event("ev_sent", event_code="CRM_REORDER_SENT")   # Zone-A, no revenue
    m = make_crm_measurement(_all_pass_consumed(make_crm_consent))
    assert m.crm_revenue() == 0.0


def test_repeat_rate_from_reorder_events(make_measurement_event, make_crm_measurement):
    make_measurement_event("s1", event_code="CRM_REORDER_SENT")
    make_measurement_event("s2", event_code="CRM_REORDER_SENT")
    make_measurement_event("c1", event_code="CRM_REORDER_ORDER_CREATED")
    assert make_crm_measurement().repeat_rate() == 0.5      # 1 created / 2 sent
