"""M6.2T LEG 2 / M6-OD-019 / SMK-032(ii) / FAIL-006: HOLD-floor lock (is_scale_authorized structurally unreachable).

Pins that `AdsScaleRequest.is_scale_authorized` is structurally UNREACHABLE while M6-OD-002/005 are OPEN -- even
with BOTH config floors (DASHBOARD_ALERT_THRESHOLDS_DEFINED, SCALE_MODEL_RATIFIED) monkeypatched True and the
best-achievable ScaleContext + a recorded owner APPROVE, `_funnel`/`_dashboard` have NO PASS branch, so overall
stays HOLD and no scale is authorized. A future PASS-branch refactor FAILs this regression loudly.
"""
from __future__ import annotations

from app import config
from app.measurement.models.measurement_event import DataQualityStatus
from app.measurement.scale.conditions import RISK_LOCKS


def test_is_scale_authorized_unreachable_even_with_both_floors_true(
    monkeypatch, make_scale_context, scale_gate, scale_store, make_owner_decision
):
    # monkeypatch BOTH M6-OD-002 (funnel thresholds) + M6-OD-005 (scale model) floors True -- the best-case future
    monkeypatch.setattr(config, "DASHBOARD_ALERT_THRESHOLDS_DEFINED", True)
    monkeypatch.setattr(config, "SCALE_MODEL_RATIFIED", True)

    # best achievable context: entry evidence present, boundaries True, dq PASS, AOV>=2, all-6 risk False, budget+rollback
    ctx = make_scale_context(
        quote_order_ok=True, public_privacy_ok=True, boxes_per_order=3.0,
        dq_overall=DataQualityStatus.PASS, risk_flags={l: False for l in RISK_LOCKS},
    )
    req = scale_gate.propose("scr_floor", {"campaign_id": "c1"}, ctx,
                             budget_cap=1_000_000.0, rollback_condition="revert")
    # even with both floors True, _funnel/_dashboard return HOLD (no PASS branch) -> overall HOLD
    assert req.overall_status is DataQualityStatus.HOLD

    # a recorded owner APPROVE (all-6 real-bool fresh read clears the RISK re-check) still yields NO authorized scale
    res = scale_gate.record_owner_decision("scr_floor", make_owner_decision("APPROVE"),
                                           current_risk_flags=ctx.risk_flags)
    assert res.approval_state.value == "APPROVED"
    assert res.is_scale_authorized is False        # structurally unreachable while the model is unratified (FAIL-006)
    assert scale_store.get("scr_floor").is_scale_authorized is False
