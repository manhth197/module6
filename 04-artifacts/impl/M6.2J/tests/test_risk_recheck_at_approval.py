"""M6.2G / M6-RULE-017: the Risk row is re-checked AT APPROVAL time, not only at propose. A request proposed while
risk was clear is REFUSED approval if a lock becomes active at approval; and an approval with no fresh risk read is
fail-closed (only a PASS Risk condition on the proposal clears).
"""
from __future__ import annotations

import pytest

from app.measurement.scale.scale_gate import ScaleGateViolation


def test_risk_active_at_approval_refuses(make_scale_context, scale_gate, scale_store, make_owner_decision):
    # proposed while clear -> overall HOLD (approvable in principle)
    scale_gate.propose("scr_t6", {"campaign_id": "c1"}, make_scale_context(), budget_cap=1.0, rollback_condition="r")
    # a recall is now active at approval time -> re-check refuses (RULE-017)
    with pytest.raises(ScaleGateViolation):
        scale_gate.record_owner_decision("scr_t6", make_owner_decision("APPROVE"), current_risk_flags={"recall": True})
    assert scale_store.get("scr_t6").approval_state.value == "PROPOSED"       # not approved -> no scale


def test_approval_without_fresh_risk_read_is_failclosed(make_scale_context, scale_gate, scale_store, make_owner_decision):
    # proposed with risk NEVER checked (empty risk_flags) -> Risk condition HOLD
    scale_gate.propose("scr_t6b", {"campaign_id": "c1"}, make_scale_context(risk_flags={}),
                       budget_cap=1.0, rollback_condition="r")
    # approving with no fresh risk read falls back to the proposal's Risk (HOLD, not PASS) -> refused
    with pytest.raises(ScaleGateViolation):
        scale_gate.record_owner_decision("scr_t6b", make_owner_decision("APPROVE"))
    assert scale_store.get("scr_t6b").approval_state.value == "PROPOSED"


def test_empty_or_partial_fresh_risk_read_is_failclosed(make_scale_context, scale_gate, scale_store, make_owner_decision):
    """Adversarial-review regression: a fresh risk read must be COMPLETE (all 6 locks observed) to clear. An
    empty {} or a partial map (some locks unobserved) does NOT clear — an unobserved lock could be active."""
    # empty fresh read (as the API handler forwards for a context whose risk was never observed)
    scale_gate.propose("scr_empty", {"campaign_id": "c1"}, make_scale_context(risk_flags={}), budget_cap=1.0, rollback_condition="r")
    with pytest.raises(ScaleGateViolation):
        scale_gate.record_owner_decision("scr_empty", make_owner_decision("APPROVE"), current_risk_flags={})
    assert scale_store.get("scr_empty").approval_state.value == "PROPOSED"

    # partial fresh read (only 1 of 6 locks observed) -> fail-closed
    scale_gate.propose("scr_partial", {"campaign_id": "c1"}, make_scale_context(risk_flags={}), budget_cap=1.0, rollback_condition="r")
    with pytest.raises(ScaleGateViolation):
        scale_gate.record_owner_decision("scr_partial", make_owner_decision("APPROVE"), current_risk_flags={"recall": False})
    assert scale_store.get("scr_partial").approval_state.value == "PROPOSED"


def test_api_approval_with_unobserved_risk_is_refused(make_scale_context, make_scale_deps):
    """The API path forwards deps.context.risk_flags; when risk was never observed ({}), approval is refused
    fail-closed (the exact path the adversarial review flagged)."""
    from app.api.scale_requests import handle_scale_decision, handle_scale_request_create
    deps = make_scale_deps(make_scale_context(risk_flags={}))
    created = handle_scale_request_create({"campaign_id": "c1", "budget_cap": 1000, "rollback_condition": "revert"}, deps)
    decided = handle_scale_decision(
        {"request_id": created.request_id, "decision": "APPROVE", "actor": "owner_ops",
         "reason": "reviewed", "audit_ref": "a1", "evidence_ref": "e1"}, deps
    )
    assert decided.error_code == "APPROVAL_REFUSED"      # fail-closed: risk not fully observed
