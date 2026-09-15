"""M6.2G leg 2 / M6-CTR-013 / CTR-026: an ads_scale_request carries evidence refs + budget cap + rollback
condition, and transitions COMPUTED->PROPOSED->APPROVED (or REJECTED) ONLY via an explicit owner decision
{actor, reason, audit, evidence}. Even an APPROVED request is inert (no scale executes; RULE-010).
"""
from __future__ import annotations

from app.api.scale_requests import handle_scale_decision, handle_scale_request_create


def test_request_carries_evidence_budget_rollback(make_scale_context, scale_gate):
    req = scale_gate.propose(
        "scr_l", {"campaign_id": "c1", "adset_id": "a1"}, make_scale_context(),
        budget_cap=500_000.0, rollback_condition="pause + revert to pilot baseline",
    )
    assert req.budget_cap == 500_000.0
    assert req.rollback_condition == "pause + revert to pilot baseline"
    assert req.evidence_refs                       # entry evidence + dq assembled
    assert len(req.condition_results) == 8
    assert req.approval_state.value == "PROPOSED"


def test_owner_approve_is_recorded_but_inert(make_scale_context, scale_gate, audit, make_owner_decision):
    ctx = make_scale_context()                     # no risk; overall HOLD (staged fail-closed)
    scale_gate.propose("scr_a", {"campaign_id": "c1"}, ctx, budget_cap=500_000.0, rollback_condition="revert")
    res = scale_gate.record_owner_decision("scr_a", make_owner_decision("APPROVE"), current_risk_flags=ctx.risk_flags)

    assert res.approval_state.value == "APPROVED"
    assert res.decision is not None and res.decision.decision.value == "APPROVE"
    assert audit.find("SCALE_REQUEST_APPROVED")
    assert res.decision.to_public()["actor"] != "owner_ops"     # actor masked (RULE-014)
    # NO scale is authorized: overall is HOLD (M6-OD-002/005), even after owner approval — honest fail-closed
    assert res.overall_status.value == "HOLD"
    assert res.is_scale_authorized is False


def test_owner_reject_is_recorded(make_scale_context, scale_gate, audit, make_owner_decision):
    scale_gate.propose("scr_r", {"campaign_id": "c1"}, make_scale_context(), budget_cap=1.0, rollback_condition="r")
    res = scale_gate.record_owner_decision("scr_r", make_owner_decision("REJECT"))
    assert res.approval_state.value == "REJECTED"
    assert audit.find("SCALE_REQUEST_REJECTED")


def test_api_create_then_owner_decide(make_scale_context, make_scale_deps):
    deps = make_scale_deps(make_scale_context())
    created = handle_scale_request_create(
        {"campaign_id": "c1", "budget_cap": 500_000, "rollback_condition": "revert"}, deps
    )
    assert created.status == "CREATED" and created.approval_state == "PROPOSED"

    # an owner decision missing fields is refused — the system never synthesizes an approval (RULE-015)
    incomplete = handle_scale_decision({"request_id": created.request_id, "decision": "APPROVE"}, deps)
    assert incomplete.error_code == "OWNER_DECISION_INCOMPLETE"

    # a complete explicit owner decision -> recorded APPROVED (still inert)
    decided = handle_scale_decision(
        {"request_id": created.request_id, "decision": "APPROVE", "actor": "owner_ops",
         "reason": "pilot reviewed", "audit_ref": "a1", "evidence_ref": "e1"}, deps
    )
    assert decided.status == "DECIDED" and decided.approval_state == "APPROVED"


def test_no_raw_pii_from_owner_decision_reaches_audit(make_scale_context, make_scale_deps, audit):
    """Adversarial-review regression: untrusted owner-decision free-text (reason / audit_ref) must NOT reach the
    audit trail raw. The audit `detail` is machine-safe (request id + decision enum); actor is masked. PII markers
    assembled at runtime (no literal PII in source)."""
    deps = make_scale_deps(make_scale_context())          # full risk map -> approvable in the workflow
    created = handle_scale_request_create({"campaign_id": "c1", "budget_cap": 1000, "rollback_condition": "revert"}, deps)
    pii_phone = "0" + "9" + "12" + "345" + "678"          # a VN-phone-shaped value
    pii_id = "ord" + "_" + "100" + "001"                  # an order-id-shaped value
    handle_scale_decision(
        {"request_id": created.request_id, "decision": "APPROVE", "actor": "owner_ops",
         "reason": "call " + pii_phone, "audit_ref": pii_id, "evidence_ref": "e1"}, deps
    )
    blob = " ".join(
        f"{r.action} {r.reason} {r.subject_masked} {r.detail}" for r in audit.records
    )
    assert pii_phone not in blob, "raw phone must never reach the audit trail"
    assert pii_id not in blob, "raw id-ref must never reach the audit trail"
    assert audit.find("SCALE_REQUEST_APPROVED")          # the decision was still audited (machine-safe)
