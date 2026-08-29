"""M6.2J boundary — the growth modules are MEASURE-ONLY: read-only projections that expose NO CRM-send /
commission / member-rights / scale / publish / order-state / trigger verb (RULE-012 / 019; FAIL-002 / 004 / 005;
module boundary). A growth measurement layer that could act would breach the Module 6 boundary.
"""
from __future__ import annotations

_FORBIDDEN = (
    "send", "crm_send", "send_crm", "sync", "dispatch", "transport", "enqueue", "publish",
    "commission", "compute_commission", "payout", "commission_rate",
    "scale", "set_price", "set_policy", "override", "member_right", "set_member_right",
    "order_state", "set_order_state", "create_order", "trigger", "write", "insert", "update", "delete",
)


def test_crm_measurement_measure_only(make_crm_measurement):
    m = make_crm_measurement()
    for verb in _FORBIDDEN:
        assert not hasattr(m, verb), f"CrmReorderMeasurement exposes forbidden verb {verb!r}"


def test_diamond_measurement_measure_only(make_diamond_measurement):
    m = make_diamond_measurement()
    for verb in _FORBIDDEN:
        assert not hasattr(m, verb), f"DiamondReferralMeasurement exposes forbidden verb {verb!r}"


def test_reactivation_measurement_measure_only(make_reactivation, make_crm_consent):
    meas, _seg = make_reactivation([], {})
    for verb in _FORBIDDEN:
        assert not hasattr(meas, verb), f"ReactivationMeasurement exposes forbidden verb {verb!r}"


def test_growth_builder_measure_only(make_growth_builder):
    b = make_growth_builder()
    for verb in _FORBIDDEN:
        assert not hasattr(b, verb), f"GrowthReportBuilder exposes forbidden verb {verb!r}"
    # public surface is measurement only
    assert callable(getattr(b, "build"))
