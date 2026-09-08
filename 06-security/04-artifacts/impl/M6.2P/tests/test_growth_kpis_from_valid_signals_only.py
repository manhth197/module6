"""M6.2J / doc §9 growth KPIs: each of the five growth groups' KPIs computes ONLY from its listed valid signals;
fail-closed (0/None denominator or absent signal → None), verified-only revenue (RULE-003). commission-ready
revenue is a MEASURED revenue figure, never a commission (RULE-019).
"""
from __future__ import annotations

from app.measurement.growth.crm import CrmConsumed
from app.measurement.growth.diamond import DiamondConsumed
from app.measurement.growth.growth import GrowthConsumed
from app.measurement.growth.signals import GrowthGroup
from app.measurement.learning.candidate import ReviewState
from app.measurement.models.measurement_event import DataQualityStatus


def test_growth_report_kpis_and_failclosed(
    make_verified_row, make_measurement_event, make_crm_measurement, make_diamond_measurement,
    make_crm_consent, make_growth_builder, review_queue, make_candidate,
):
    # CRM verified reorder (gated pass) + reorder funnel events
    make_verified_row("gv_crm", revenue=300000.0, order_code="ord_crm", signals={"crm": True})
    make_measurement_event("gs1", event_code="CRM_REORDER_SENT")
    make_measurement_event("gc1", event_code="CRM_REORDER_ORDER_CREATED")
    crm = make_crm_measurement(CrmConsumed(crm_eligible_orders={"ord_crm": True},
                                           suppression_pass_orders={"ord_crm": True},
                                           consent_by_order={"ord_crm": make_crm_consent()}))
    # Diamond verified referral + lead events
    make_verified_row("gv_dia", revenue=500000.0, order_code="ord_dia", signals={"referral_link_id": "ref_1"})
    make_measurement_event("gl1", event_code="DIAMOND_LEAD_CREATED")
    make_measurement_event("gvr1", event_code="DIAMOND_REFERRAL_ORDER_VERIFIED")
    diamond = make_diamond_measurement(DiamondConsumed(commission_eligible_orders={"ord_dia": True}))
    # a DQ-FAIL row -> one drift violation
    make_measurement_event("gbad", event_code="LIVE_VIEW", data_quality_status=DataQualityStatus.FAIL)
    # learning candidates -> approval rate 1/2
    review_queue.enqueue(make_candidate("lc1", review_state=ReviewState.APPROVED))
    review_queue.enqueue(make_candidate("lc2", review_state=ReviewState.REJECTED))

    builder = make_growth_builder(crm=crm, diamond=diamond, review_queue=review_queue,
                                  consumed=GrowthConsumed())   # no dormant seg / cohort / value-opt signals
    r = builder.build()

    # Repeat / Reorder
    assert r.kpi("Repeat rate").value == 1.0                      # 1 created / 1 sent
    assert r.kpi("CRM Revenue").value == 300000.0                 # gated, verified-only
    # Diamond
    assert r.kpi("Diamond Revenue").value == 500000.0
    assert r.kpi("Diamond lead rate").value == 1.0               # 1 referral-verified / 1 lead
    assert r.kpi("commission-ready revenue").value == 500000.0   # eligible verified revenue (a revenue figure)
    # Learning Engine
    assert r.kpi("Candidate approval rate").value == 0.5
    assert r.kpi("drift violations").value == 1.0
    # fail-closed KPIs (no valid signals wired)
    assert r.group(GrowthGroup.DORMANT_REACTIVATION)[0].value is None   # Reactivation rate (no dormant seg)
    assert r.kpi("uplift").value is None
    assert r.kpi("CLV proxy").value is None
    assert r.kpi("ads ratio reduction").value is None
    # every KPI carries its doc §9 valid signals
    for k in r.kpis:
        assert k.source_signals, f"{k.name} missing source_signals"


def test_named_dormant_segment_without_reactivation_is_failclosed_not_crash(make_growth_builder):
    """Defense-in-depth (adversarial review): a named dormant segment but an UNWIRED reactivation measurement
    fails closed to None (mirrors the queue/store guards) rather than crashing."""
    from app.measurement.growth.growth import GrowthConsumed
    r = make_growth_builder(reactivation=None, consumed=GrowthConsumed(dormant_segment_id="seg_x")).build()
    react = r.group(GrowthGroup.DORMANT_REACTIVATION)
    assert all(k.value is None for k in react)                 # fail-closed None, no AttributeError
    assert any("not wired" in (k.note or "") for k in react)


def test_uplift_and_ads_ratio_from_consumed_cohorts(make_growth_builder):
    consumed = GrowthConsumed(uplift_treatment_revenue=1200.0, uplift_baseline_revenue=1000.0,
                              ads_ratio_current=0.2, ads_ratio_baseline=0.5, clv_proxy=800000.0)
    r = make_growth_builder(consumed=consumed).build()
    assert abs(r.kpi("uplift").value - 0.2) < 1e-9              # (1200-1000)/1000
    assert abs(r.kpi("ads ratio reduction").value - 0.6) < 1e-9  # (0.5-0.2)/0.5
    assert r.kpi("CLV proxy").value == 800000.0
