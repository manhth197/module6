"""Official smoke — slice M6.2J — M6-SMK-010 (doc ADS-P0-010) / M6-RULE-012 / M6-FAIL-005, growth leg.

Authored by TESTER in M6-P1903 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1904. This is the
M6.2J growth-machine leg of SMK-010 (the smoke binds M6.2F + M6.2J): the M6.2F carried smoke
(test_smk_010_data_mart_support_view_only.py) proves the dashboard side; this file proves the Phase 3 growth layer
READS the Data Mart but never turns it into a trigger. Governance is immutable: global_gateway_state=BLOCKED,
production_flag=OFF, external_send=OFF — nothing below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 410):

    Kịch bản (verbatim):          "Data Mart tạo trigger CRM/scale"
    Kết quả phải đạt (verbatim):  "Fail - Data Mart chỉ support view"

Neither the Data Mart nor the growth report builder exposes a CRM / pricing / Diamond / scale / commission /
order-state trigger — a CRM/scale trigger simply cannot be created; the growth report is read-only data, and
building it mutates nothing (RULE-012 / FAIL-005). Reuses the shared conftest fixtures (make_data_mart,
make_growth_builder, make_verified_row, measurement_store). All ids synthetic; no PII.
"""
from __future__ import annotations

_TRIGGER_VERBS = (
    "trigger", "send", "sync", "crm_send", "scale", "set_price", "write_price", "set_policy",
    "publish", "dispatch", "commission", "order_state", "write", "insert", "update", "delete",
)


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_010_data_mart_and_growth_expose_no_crm_or_scale_trigger(make_data_mart, make_growth_builder):
    """M6-SMK-010 "Data Mart tạo trigger CRM/scale" -> "Fail - Data Mart chỉ support view".

    The Data Mart is a support view and the growth builder only reads it — neither can create a CRM/scale trigger.
    """
    mart = make_data_mart()
    for verb in _TRIGGER_VERBS:
        assert not hasattr(mart, verb), f"DataMart must not expose trigger verb {verb!r} (RULE-012/FAIL-005)"

    builder = make_growth_builder()
    for verb in _TRIGGER_VERBS:
        assert not hasattr(builder, verb), f"GrowthReportBuilder must not expose trigger verb {verb!r}"
    report = builder.build()
    assert hasattr(report, "kpis") and not any(hasattr(report, v) for v in _TRIGGER_VERBS)


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_010_neg_growth_report_is_data_only(make_verified_row, make_growth_builder):
    """The growth report is plain read-only data — a dict of KPIs, with no trigger/send/scale handle."""
    make_verified_row("mv", revenue=100000.0, order_code="ord_m", signals={"crm": True})
    pub = make_growth_builder().build().to_public()
    assert isinstance(pub, dict) and isinstance(pub["kpis"], list)
    for verb in _TRIGGER_VERBS:
        assert verb not in pub, f"growth report export must not carry a {verb!r} handle"


def test_smk_010_neg_building_growth_report_does_not_mutate_store(
    make_verified_row, make_growth_builder, measurement_store
):
    """A support view only READS: building the growth report twice does not insert / mutate the measurement store
    (no trigger side effect)."""
    make_verified_row("mv2", revenue=120000.0, order_code="ord_m2", signals={"crm": True})
    builder = make_growth_builder()

    before = len(measurement_store.all())
    builder.build()
    builder.build()
    after = len(measurement_store.all())
    assert before == after, "building the growth report must not mutate the store (support view only)"
