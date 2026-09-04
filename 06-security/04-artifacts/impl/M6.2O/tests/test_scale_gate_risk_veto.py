"""M6.2G leg 1 / M6-SMK-009: an active Risk-row lock (recall / sale lock / quality hold / complaint P0 / platform
spam flag / CRM suppression) forces the Scale Gate to FAIL/HOLD (RULE-017 hard veto) and the request cannot be
approved. "Recall/Sale Lock active -> Scale Gate FAIL/HOLD."
"""
from __future__ import annotations

import pytest

from app.measurement.models.measurement_event import DataQualityStatus
from app.measurement.scale.conditions import RISK_LOCKS, ScaleCondition, evaluate_conditions
from app.measurement.scale.scale_gate import ScaleGateViolation


@pytest.mark.parametrize("lock", list(RISK_LOCKS))
def test_any_active_risk_lock_forces_fail(make_scale_context, lock):
    ctx = make_scale_context(risk_flags={l: (l == lock) for l in RISK_LOCKS})
    results, overall = evaluate_conditions(ctx)
    risk = next(r for r in results if r.condition is ScaleCondition.RISK)
    assert risk.status is DataQualityStatus.FAIL       # hard veto (RULE-017)
    assert overall is DataQualityStatus.FAIL           # worst dominates


def test_risk_locked_request_cannot_be_approved(make_scale_context, scale_gate, scale_store, make_owner_decision):
    ctx = make_scale_context(risk_flags={l: (l == "recall") for l in RISK_LOCKS})
    req = scale_gate.propose("scr_risk", {"campaign_id": "c1"}, ctx,
                             budget_cap=1_000_000.0, rollback_condition="revert to pilot baseline")
    assert req.overall_status is DataQualityStatus.FAIL

    # owner attempts to approve while recall is active -> REFUSED (RULE-017 re-check at approval)
    with pytest.raises(ScaleGateViolation):
        scale_gate.record_owner_decision(
            "scr_risk", make_owner_decision("APPROVE"),
            current_risk_flags={l: (l == "recall") for l in RISK_LOCKS},
        )
    # the request stays PROPOSED — no approval, no scale
    assert scale_store.get("scr_risk").approval_state.value == "PROPOSED"
    assert scale_store.get("scr_risk").is_scale_authorized is False
