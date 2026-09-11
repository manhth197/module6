"""M6-CTR-019 POST /api/admin/ads/scale-requests — framework-neutral, INERT request handlers (M6.2G).

`handle_scale_request_create(body, deps)` creates an inert PROPOSED `ads_scale_request` (compute conditions +
assemble evidence + propose); `handle_scale_decision(body, deps)` records an explicit owner APPROVE/REJECT. NEITHER
acts: `ScaleRequestDeps` holds only the `ScaleGate` (over the inert request store) + the server-assembled
`ScaleContext` + audit — no Transport, no budget/campaign/audience API, no connector (RULE-010, FAIL-006). The
scale CONDITIONS are computed from server-side state (deps.context), NOT from the untrusted admin body (RULE-H03),
so a request body can never fake a condition PASS. Owner-decision fields (actor/reason/audit/evidence) must all be
present — the system never synthesizes an approval (RULE-015). PII masked. HTTP mapping binds at M6-OD-011.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Optional

from app.measurement.scale.conditions import ScaleContext
from app.measurement.scale.models import DecisionKind, OwnerDecision
from app.measurement.scale.scale_gate import ScaleGate, ScaleGateViolation


@dataclass
class ScaleRequestDeps:
    """Read/create-only deps. Holds ONLY the inert ScaleGate + the server-assembled ScaleContext + audit — no
    Transport, no budget/campaign/audience handle (RULE-010/012). The absence is asserted by a test (FAIL-006)."""

    scale_gate: ScaleGate
    context: ScaleContext
    audit: Any = None


@dataclass(frozen=True)
class ScaleResponse:
    status: str                                 # CREATED | DECIDED | REJECTED_INPUT
    request_id: Optional[str] = None
    approval_state: Optional[str] = None
    overall_status: Optional[str] = None
    error_code: Optional[str] = None
    message: Optional[str] = None


def _str(body: Mapping[str, Any], key: str) -> Optional[str]:
    v = body.get(key)
    return v if isinstance(v, str) and v else None


def handle_scale_request_create(body: Any, deps: ScaleRequestDeps) -> ScaleResponse:
    if not isinstance(body, Mapping):
        return ScaleResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID", message="body must be an object")
    # scale_target references (campaign/adset/ad) — recorded only, never mutated. At least one is required.
    target = {k: _str(body, k) for k in ("campaign_id", "adset_id", "ad_id")}
    if not any(target.values()):
        return ScaleResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID",
                             message="a scale_target (campaign_id/adset_id/ad_id) is required")
    budget_cap = body.get("budget_cap")
    if budget_cap is not None and (isinstance(budget_cap, bool) or not isinstance(budget_cap, (int, float))):
        return ScaleResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID", message="budget_cap must be a number")
    rollback_condition = _str(body, "rollback_condition")

    request_id = "scr_" + hashlib.sha256(
        (str(sorted((k, v) for k, v in target.items() if v)) + "|" + uuid.uuid4().hex).encode("utf-8")
    ).hexdigest()[:24]

    # Conditions come from deps.context (server-side), NOT the untrusted body.
    request = deps.scale_gate.propose(
        request_id, target, deps.context,
        budget_cap=float(budget_cap) if budget_cap is not None else None,
        rollback_condition=rollback_condition,
    )
    return ScaleResponse(
        status="CREATED", request_id=request.request_id,
        approval_state=request.approval_state.value, overall_status=request.overall_status.value,
    )


def handle_scale_decision(body: Any, deps: ScaleRequestDeps, *, now: Optional[datetime] = None) -> ScaleResponse:
    if not isinstance(body, Mapping):
        return ScaleResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID", message="body must be an object")
    request_id = _str(body, "request_id")
    if not request_id:
        return ScaleResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID", message="request_id is required")
    kind = _str(body, "decision")
    if kind not in ("APPROVE", "REJECT"):
        return ScaleResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID",
                             message="decision must be APPROVE or REJECT")
    # An owner decision requires ALL of actor/reason/audit_ref/evidence_ref — the system never synthesizes one.
    fields = {k: _str(body, k) for k in ("actor", "reason", "audit_ref", "evidence_ref")}
    missing = [k for k, v in fields.items() if not v]
    if missing:
        return ScaleResponse(status="REJECTED_INPUT", error_code="OWNER_DECISION_INCOMPLETE",
                             message=f"owner decision missing: {','.join(missing)}")

    decision = OwnerDecision(
        actor=fields["actor"], reason=fields["reason"], audit_ref=fields["audit_ref"],
        evidence_ref=fields["evidence_ref"], decision=DecisionKind(kind), at=now,
    )
    try:
        result = deps.scale_gate.record_owner_decision(
            request_id, decision, current_risk_flags=deps.context.risk_flags, now=now,
        )
    except ScaleGateViolation as exc:
        # fail-closed: an approval refused by the Risk veto / missing cap / FAIL request is NOT an error to hide;
        # it is the gate working. Report it as a refusal (no scale happened).
        return ScaleResponse(status="REJECTED_INPUT", request_id=request_id,
                             error_code="APPROVAL_REFUSED", message=str(exc))
    return ScaleResponse(
        status="DECIDED", request_id=result.request_id,
        approval_state=result.approval_state.value, overall_status=result.overall_status.value,
    )
