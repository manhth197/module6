"""Official smoke — slice M6.2J — M6-SMK-014 (doc ADS-P0-014) / M6-RULE-019.

Authored by TESTER in M6-P1903 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1904. Governance is
immutable here: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag
and no commission is ever computed.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 414):

    Kịch bản (verbatim):          "Diamond referral order verified"
    Kết quả phải đạt (verbatim):  "Gắn referral attribution, không tự tính commission"

A verified Diamond referral order carries referral attribution (referral_link_id + buyer identity + order_code);
Diamond Revenue and commission-READY revenue are MEASURED (verified-only) — but NO commission amount / rate /
payout is computed (Finance owns, RULE-019). Buyer identity is PII, masked on export. Reuses the shared conftest
growth fixtures (make_verified_row, make_diamond_measurement). All ids synthetic; no PII.
"""
from __future__ import annotations

from app.measurement.growth.diamond import DiamondConsumed

_FORBIDDEN_COMMISSION = (
    "commission", "compute_commission", "commission_amount", "commission_rate", "payout",
    "calculate_commission", "commission_value",
)


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_014_verified_referral_records_attribution_and_measures_revenue(
    make_verified_row, make_diamond_measurement
):
    """M6-SMK-014 "Diamond referral order verified" -> "Gắn referral attribution, không tự tính commission"."""
    make_verified_row(
        "ev_d", revenue=500000.0, order_code="ord_d",
        signals={"referral_link_id": "ref_1", "diamond_id": "dia_1"},
    )
    m = make_diamond_measurement(DiamondConsumed(commission_eligible_orders={"ord_d": True}))
    attrs = m.referral_attributions()

    assert len(attrs) == 1
    assert attrs[0].referral_link_id == "ref_1" and attrs[0].order_code == "ord_d"   # referral attribution attached
    assert m.diamond_revenue() == 500000.0                    # verified-only revenue MEASURED
    assert m.commission_ready_revenue() == 500000.0           # commission-ELIGIBLE verified revenue (a revenue figure)
    # ...but NO commission amount / rate / payout is computed (RULE-019)
    for verb in _FORBIDDEN_COMMISSION:
        assert not hasattr(m, verb), f"Diamond measurement must not compute a commission ({verb!r}, RULE-019)"


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_014_neg_no_commission_method_anywhere(make_diamond_measurement):
    """RULE-019: the Diamond layer exposes NO method that computes a commission amount / rate / payout — even with
    no data wired (the surface itself is absent, not merely data-empty)."""
    m = make_diamond_measurement()
    for verb in _FORBIDDEN_COMMISSION:
        assert not hasattr(m, verb), f"Diamond measurement exposes commission verb {verb!r} (RULE-019 breach)"


def test_smk_014_neg_commission_ready_zero_without_eligibility(make_verified_row, make_diamond_measurement):
    """Commission-READY revenue counts ONLY commission-ELIGIBLE orders (a CONSUMED Finance flag); absent ⇒ 0
    (fail-closed). Diamond Revenue (verified-only) is still measured — Module 6 measures the source, never the
    commission."""
    make_verified_row("ev_d2", revenue=400000.0, order_code="ord_d2", signals={"referral_link_id": "ref_2"})
    m = make_diamond_measurement()                            # no commission-eligibility wired
    assert m.diamond_revenue() == 400000.0
    assert m.commission_ready_revenue() == 0.0               # fail-closed


def test_smk_014_neg_buyer_identity_masked_on_export(make_verified_row, make_diamond_measurement):
    """Buyer identity is PII — masked on every referral-attribution export; the raw id never reaches the surface
    (RULE-014 / H02)."""
    make_verified_row("ev_d3", revenue=100000.0, order_code="ord_d3",
                      signals={"referral_link_id": "ref_3"}, customer_id="cust_dia_smk14")
    pub = make_diamond_measurement().referral_attributions()[0].to_public()
    assert pub["buyer_ref"] != "cust_dia_smk14" and pub["buyer_ref"] is not None   # masked, not raw
    assert "cust_dia_smk14" not in str(pub)
