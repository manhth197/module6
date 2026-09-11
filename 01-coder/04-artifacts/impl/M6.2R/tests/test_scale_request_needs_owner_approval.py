"""M6.2G leg 2 / M6-SMK-012: a scale request WITHOUT an explicit owner approval never scales — it stays PROPOSED,
and the system cannot approve its own request (RULE-015). "Scale request không owner approval -> Không scale."
"""
from __future__ import annotations


def test_proposed_request_stays_proposed_without_owner(make_scale_context, scale_gate, scale_store):
    ctx = make_scale_context(budget_cap=1_000_000.0, rollback_condition="revert")
    req = scale_gate.propose("scr_1", {"campaign_id": "c1"}, ctx,
                             budget_cap=1_000_000.0, rollback_condition="revert to baseline")
    assert req.approval_state.value == "PROPOSED"
    assert req.is_scale_authorized is False           # no owner decision -> not authorized -> no scale
    assert scale_store.get("scr_1").approval_state.value == "PROPOSED"


def test_scale_gate_cannot_self_approve(scale_gate):
    # there is NO auto-approve / self-approve entry point (RULE-015): approval requires an explicit OwnerDecision
    for name in ("approve", "auto_approve", "self_approve", "approve_all", "authorize"):
        assert not hasattr(scale_gate, name)
