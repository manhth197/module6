"""M6.2I boundary — the funnel / retargeting / dashboard-section are MEASURE-ONLY: read-only projections that
expose NO write / send / scale / publish / order-state / pricing / commission verb (RULE-012 / 013 / 018; module
boundary). A measurement layer that could act would breach the Module 6 boundary.
"""
from __future__ import annotations

from app.measurement.funnel.funnel import GoldenHourFunnel
from app.measurement.funnel.models import GoldenHourFunnelView
from app.measurement.funnel.retargeting import RetargetingMeasurement

_FORBIDDEN = (
    "write", "insert", "update", "delete", "send", "dispatch", "transport", "enqueue", "sync",
    "publish", "scale", "set_price", "write_price", "set_policy", "override", "commission",
    "order_state", "set_order_state", "send_to_core", "create_order", "trigger",
)


def test_funnel_exposes_no_mutating_or_sending_verb(make_golden_hour_funnel):
    funnel = make_golden_hour_funnel()
    for verb in _FORBIDDEN:
        assert not hasattr(funnel, verb), f"GoldenHourFunnel exposes forbidden verb {verb!r}"
    # its public surface is measurement only
    assert callable(getattr(funnel, "assemble"))
    assert callable(getattr(funnel, "view_for"))


def test_funnel_view_is_data_only(make_verified_row, make_golden_hour_funnel):
    make_verified_row("e_b", revenue=50000.0, order_code="ord_b", live_session_id="ls_b", page_id="p")
    v = make_golden_hour_funnel().view_for("ls_b")
    assert isinstance(v, GoldenHourFunnelView)
    for verb in _FORBIDDEN:
        assert not hasattr(v, verb), f"GoldenHourFunnelView exposes forbidden verb {verb!r}"
    # export is a plain data mapping (verified-only revenue; no trigger handle)
    pub = v.to_public()
    assert set(pub.keys()) >= {"live_session_id", "stage_counts", "rates", "verified_revenue", "capture_gate_passed", "trace"}


def test_retargeting_is_measure_only(retargeting_measurement):
    for verb in _FORBIDDEN:
        assert not hasattr(retargeting_measurement, verb), f"retargeting exposes forbidden verb {verb!r}"
