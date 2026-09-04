"""M6.2J / M6-SMK-010 (ADS-P0-010) / M6-RULE-012 / M6-FAIL-005: "Data Mart tạo trigger CRM/scale" -> "Fail - Data
Mart chỉ support view". The growth layer READS the Data Mart but never turns it into a trigger; neither the Data
Mart nor the growth report builder exposes a CRM/pricing/Diamond/scale trigger.
"""
from __future__ import annotations

from app.measurement.dashboard.data_mart import DataMart

_TRIGGER_VERBS = (
    "trigger", "send", "sync", "crm_send", "scale", "set_price", "write_price", "set_policy",
    "publish", "dispatch", "commission", "order_state", "write", "insert", "update", "delete",
)


def test_data_mart_exposes_no_trigger(make_data_mart):
    mart = make_data_mart()
    for verb in _TRIGGER_VERBS:
        assert not hasattr(mart, verb), f"DataMart exposes trigger verb {verb!r} (RULE-012/FAIL-005)"


def test_growth_builder_reads_mart_without_becoming_a_trigger(make_growth_builder):
    builder = make_growth_builder()
    for verb in _TRIGGER_VERBS:
        assert not hasattr(builder, verb), f"GrowthReportBuilder exposes trigger verb {verb!r} (RULE-012)"
    # it only builds a read-only report
    report = builder.build()
    assert hasattr(report, "kpis") and not any(hasattr(report, v) for v in _TRIGGER_VERBS)


def test_growth_report_is_data_only(make_verified_row, make_growth_builder):
    make_verified_row("mv", revenue=100000.0, order_code="ord_m", signals={"crm": True})
    pub = make_growth_builder().build().to_public()
    assert isinstance(pub, dict) and isinstance(pub["kpis"], list)     # plain data, no trigger handle
