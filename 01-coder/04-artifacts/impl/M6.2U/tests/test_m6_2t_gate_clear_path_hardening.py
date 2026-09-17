"""M6.2T LEG 1 / M6-OD-019 / SMK-032(i) / RULE-017: shared Scale-Gate clear-path hardening (stricter/fail-closed).

conditions._risk PASSes ONLY a COMPLETE read (all 6 RISK_LOCKS present AND none active) -- a partial no-active map
-> HOLD (was PASS). scale_gate._assert_risk_clear_at_approval additionally validates BOOL-NESS: a falsy non-bool
lock value (0/''/None) does NOT clear via the fresh-read path. Stricter/fail-closed only; NO PASS branch opened, NO
clear loosened; the certified M6.2G behaviors (active->FAIL, all-6-real-bool->clear) are UNCHANGED.
"""
from __future__ import annotations

import pytest

from app.measurement.models.measurement_event import DataQualityStatus
from app.measurement.scale.conditions import RISK_LOCKS, ScaleCondition, evaluate_conditions
from app.measurement.scale.scale_gate import ScaleGateViolation


def _risk_status(ctx):
    results, _ = evaluate_conditions(ctx)
    return next(r for r in results if r.condition is ScaleCondition.RISK).status


def test_partial_no_active_map_holds_full_six_passes(make_scale_context):
    # a partial (3-of-6 ops-core locks) no-active map -> HOLD (all 6 required to PASS; an unobserved lock could be active)
    partial = make_scale_context(risk_flags={"recall": False, "sale_lock": False, "quality_hold": False})
    assert _risk_status(partial) is DataQualityStatus.HOLD
    # a COMPLETE all-6 no-active map -> PASS (non-vacuous: the gate CAN reach PASS with a complete read)
    full = make_scale_context(risk_flags={l: False for l in RISK_LOCKS})
    assert _risk_status(full) is DataQualityStatus.PASS
    # {} -> HOLD (unchanged); an active lock -> FAIL (unchanged)
    assert _risk_status(make_scale_context(risk_flags={})) is DataQualityStatus.HOLD
    assert _risk_status(make_scale_context(risk_flags={l: (l == "recall") for l in RISK_LOCKS})) is DataQualityStatus.FAIL


def test_all_six_real_bool_fresh_read_clears_at_approval(make_scale_context, scale_gate, scale_store, make_owner_decision):
    # control (certified behavior unchanged): a COMPLETE all-6 REAL-bool no-active fresh read clears the approval
    scale_gate.propose("scr_ok", {"campaign_id": "c1"}, make_scale_context(risk_flags={}), budget_cap=1.0, rollback_condition="r")
    res = scale_gate.record_owner_decision("scr_ok", make_owner_decision("APPROVE"),
                                           current_risk_flags={l: False for l in RISK_LOCKS})
    assert res.approval_state.value == "APPROVED"


@pytest.mark.parametrize("bad", [0, "", None])
def test_falsy_non_bool_lock_does_not_clear_at_approval(bad, make_scale_context, scale_gate, scale_store, make_owner_decision):
    # a falsy NON-bool lock value (0/''/None-as-value) does NOT clear via the fresh-read path (bool-ness) -> falls
    # back to the proposal's Risk (HOLD, proposed with {}), so the approval is REFUSED (fail-closed).
    rid = f"scr_bad_{bad!r}"
    scale_gate.propose(rid, {"campaign_id": "c1"}, make_scale_context(risk_flags={}), budget_cap=1.0, rollback_condition="r")
    flags = {l: False for l in RISK_LOCKS}
    flags["recall"] = bad                                   # one lock is a falsy non-bool (all 6 keys present)
    with pytest.raises(ScaleGateViolation):
        scale_gate.record_owner_decision(rid, make_owner_decision("APPROVE"), current_risk_flags=flags)
    assert scale_store.get(rid).approval_state.value == "PROPOSED"
