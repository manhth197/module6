"""M6.2G / M6-CTR-013: the 8 doc §16 scale conditions evaluate; Funnel (M6-OD-002 thresholds) and Dashboard-as-
scale-evidence (M6-OD-005 / SCALE_MODEL_RATIFIED=False) are fail-closed HOLD, so the overall gate can NEVER be a
clean scale-ready PASS in the staged posture; Quality mirrors the M6.2F Data Quality Gate; Risk is a hard veto;
worst-status roll-up.
"""
from __future__ import annotations

from app.measurement.models.measurement_event import DataQualityStatus
from app.measurement.scale.conditions import ScaleCondition, evaluate_conditions


def test_eight_conditions_with_failclosed_holds(make_scale_context):
    results, overall = evaluate_conditions(make_scale_context())
    assert len(results) == 8
    by = {r.condition: r.status for r in results}
    # fail-closed HOLDs while the owner decisions are OPEN
    assert by[ScaleCondition.FUNNEL] is DataQualityStatus.HOLD          # M6-OD-002 thresholds
    assert by[ScaleCondition.DASHBOARD] is DataQualityStatus.HOLD       # M6-OD-005 scale model
    assert by[ScaleCondition.APPROVAL] is DataQualityStatus.HOLD        # not approved at propose
    # satisfiable conditions PASS
    assert by[ScaleCondition.P3_P5_P6_EVIDENCE] is DataQualityStatus.PASS
    assert by[ScaleCondition.QUALITY] is DataQualityStatus.PASS         # dq_overall PASS
    assert by[ScaleCondition.RISK] is DataQualityStatus.PASS            # no locks
    # the gate can never be a clean scale-ready PASS in the staged posture
    assert overall is DataQualityStatus.HOLD


def test_missing_entry_evidence_is_hold(make_scale_context):
    ctx = make_scale_context(entry_evidence_refs={"ENTRY-001": "e1"})   # 002/003/004 missing
    by = {r.condition: r.status for r in evaluate_conditions(ctx)[0]}
    assert by[ScaleCondition.P3_P5_P6_EVIDENCE] is DataQualityStatus.HOLD


def test_dq_fail_makes_quality_and_overall_fail(make_scale_context):
    results, overall = evaluate_conditions(make_scale_context(dq_overall=DataQualityStatus.FAIL))
    by = {r.condition: r.status for r in results}
    assert by[ScaleCondition.QUALITY] is DataQualityStatus.FAIL
    assert overall is DataQualityStatus.FAIL


def test_never_clean_pass_even_when_everything_attestable(make_scale_context):
    # even with owner approval + budget + rollback + all attestations, Funnel/Dashboard keep the gate off PASS
    ctx = make_scale_context(owner_approved=True, budget_cap=1.0, rollback_condition="r")
    _results, overall = evaluate_conditions(ctx)
    assert overall is not DataQualityStatus.PASS
