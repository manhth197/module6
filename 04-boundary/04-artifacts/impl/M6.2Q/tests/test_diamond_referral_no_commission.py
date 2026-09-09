"""M6.2J leg L2 / M6-SMK-014 (ADS-P0-014) / M6-RULE-019: "Diamond referral order verified" -> "Gắn referral
attribution, không tự tính commission". A verified Diamond referral order carries referral attribution
(referral_link_id + buyer identity); Diamond Revenue + commission-ready revenue are MEASURED (verified-only); NO
commission amount/rate/payout is computed (Finance owns). Buyer identity is masked on export.
"""
from __future__ import annotations

from app.measurement.growth.diamond import DiamondConsumed, DiamondReferralMeasurement

_FORBIDDEN_COMMISSION = (
    "commission", "compute_commission", "commission_amount", "commission_rate", "payout",
    "calculate_commission", "commission_value",
)


def test_referral_attribution_recorded_and_revenue_measured(make_verified_row, make_diamond_measurement):
    make_verified_row(
        "ev_d", revenue=500000.0, order_code="ord_d",
        signals={"referral_link_id": "ref_1", "diamond_id": "dia_1"},
    )
    m = make_diamond_measurement(DiamondConsumed(commission_eligible_orders={"ord_d": True}))
    attrs = m.referral_attributions()
    assert len(attrs) == 1
    assert attrs[0].referral_link_id == "ref_1" and attrs[0].order_code == "ord_d"
    assert m.diamond_revenue() == 500000.0                    # verified-only
    assert m.commission_ready_revenue() == 500000.0           # commission-ELIGIBLE verified revenue (a revenue figure)


def test_no_commission_is_computed(make_diamond_measurement):
    """RULE-019: the Diamond layer exposes NO method that computes a commission amount/rate/payout."""
    m = make_diamond_measurement()
    for verb in _FORBIDDEN_COMMISSION:
        assert not hasattr(m, verb), f"Diamond measurement exposes commission verb {verb!r} (RULE-019 breach)"


def test_commission_ready_is_zero_without_eligibility(make_verified_row, make_diamond_measurement):
    """commission-ready revenue counts ONLY commission-ELIGIBLE orders (consumed flag); absent ⇒ 0 (fail-closed).
    Diamond Revenue (verified-only) is still measured."""
    make_verified_row("ev_d2", revenue=400000.0, order_code="ord_d2", signals={"referral_link_id": "ref_2"})
    m = make_diamond_measurement()                             # no commission-eligibility wired
    assert m.diamond_revenue() == 400000.0
    assert m.commission_ready_revenue() == 0.0                 # fail-closed


def test_buyer_identity_masked_on_export(make_verified_row, make_diamond_measurement):
    make_verified_row("ev_d3", revenue=100000.0, order_code="ord_d3",
                      signals={"referral_link_id": "ref_3"}, customer_id="cust_diamond_9")
    attrs = make_diamond_measurement().referral_attributions()
    pub = attrs[0].to_public()
    assert pub["buyer_ref"] != "cust_diamond_9" and pub["buyer_ref"] is not None   # masked, not raw
    assert "cust_diamond_9" not in str(pub)


def test_diamond_lead_rate(make_measurement_event, make_diamond_measurement):
    make_measurement_event("l1", event_code="DIAMOND_LEAD_CREATED")
    make_measurement_event("l2", event_code="DIAMOND_LEAD_CREATED")
    make_measurement_event("v1", event_code="DIAMOND_REFERRAL_ORDER_VERIFIED")
    assert make_diamond_measurement().diamond_lead_rate() == 0.5   # 1 referral-verified / 2 leads
