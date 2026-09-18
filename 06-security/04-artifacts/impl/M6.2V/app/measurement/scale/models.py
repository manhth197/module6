"""M6-CTR-013 ads_scale_request + M6-CTR-026 approval-flow models — INERT DATA (RULE-010).

An `AdsScaleRequest` is a PROPOSAL: it records the computed scale conditions + assembled evidence refs + a
`budget_cap` and a `rollback_condition` (both are request FIELDS / requirements, never actions) for OWNER review.
It carries NO method that raises a budget, enables a campaign, opens audience scale, sends, or publishes — those
are owner actions performed OUTSIDE Module 6, gated by production_flag=OFF (FAIL-006). `approval_state` transitions
only via an explicit `OwnerDecision` (SMK-012); the system never approves its own request (RULE-015). Identity in
the target/actor is masked on export (RULE-014). "Approved" is a recorded decision, not a trigger.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from app.measurement.masking import mask
from app.measurement.models.measurement_event import DataQualityStatus
from app.measurement.scale.conditions import ConditionResult


class ApprovalState(str, Enum):
    """CTR-026 lifecycle (SPEC §13): computed -> proposed -> owner approve/reject. No state executes anything."""

    COMPUTED = "COMPUTED"
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"          # a RECORDED owner decision — NOT an executed scale (RULE-010)
    REJECTED = "REJECTED"


class DecisionKind(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


@dataclass(frozen=True)
class OwnerDecision:
    """An explicit owner decision on a scale request (CTR-026). Requires actor + reason + audit + evidence — the
    system can never synthesize one (RULE-015). `actor` is masked on export (may be an operator id)."""

    actor: str
    reason: str
    audit_ref: str
    evidence_ref: str
    decision: DecisionKind
    at: Optional[datetime] = None

    def to_public(self) -> Dict[str, Any]:
        return {
            "actor": mask(self.actor),
            "reason": self.reason,
            "audit_ref": self.audit_ref,
            "evidence_ref": self.evidence_ref,
            "decision": self.decision.value,
            "at": self.at.isoformat() if self.at is not None else None,
        }


@dataclass(frozen=True)
class AdsScaleRequest:
    """One inert scale-request proposal (CTR-013). Frozen; a lifecycle transition produces a NEW record, never an
    executed action. `scale_target` is a reference (campaign/adset/ad ids) — recorded, never mutated."""

    request_id: str
    scale_target: Dict[str, Any]                       # {campaign_id, adset_id, ad_id} references (recorded only)
    budget_cap: Optional[float]                        # request field (a requirement / ceiling), NOT an action
    rollback_condition: Optional[str]                  # request field (a requirement), NOT an action
    evidence_refs: Tuple[str, ...]                     # masked evidence refs assembled for owner review
    condition_results: Tuple[ConditionResult, ...]     # the 8 doc §16 condition statuses
    overall_status: DataQualityStatus                  # worst of the conditions (PASS/HOLD/FAIL)
    approval_state: ApprovalState = ApprovalState.PROPOSED
    decision: Optional[OwnerDecision] = None
    created_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None

    @property
    def is_scale_authorized(self) -> bool:
        """A scale is authorized ONLY when BOTH hold: (a) an explicit owner APPROVE decision is recorded, AND
        (b) the computed conditions are a clean PASS (overall == PASS) with a budget cap + rollback condition.
        Owner approval alone is NOT enough — the evidence must support it (the Risk veto lives in the conditions).
        In the staged posture the overall is fail-closed HOLD (M6-OD-002 / M6-OD-005), so this is False even after
        an owner APPROVE — the honest truth that no scale is authorized yet. And even when True, NOTHING is executed
        here (RULE-010): it only reports that the owner authorized a scale THEY will perform outside Module 6."""
        return (
            self.approval_state is ApprovalState.APPROVED
            and self.decision is not None
            and self.decision.decision is DecisionKind.APPROVE
            and self.overall_status is DataQualityStatus.PASS
            and self.budget_cap is not None
            and bool(self.rollback_condition)
        )

    def to_public(self) -> Dict[str, Any]:
        """PII-safe export. `scale_target` ids are campaign/adset/ad refs (not PII); actor masked via the decision."""
        return {
            "request_id": self.request_id,
            "scale_target": dict(self.scale_target),
            "budget_cap": self.budget_cap,
            "rollback_condition": self.rollback_condition,
            "evidence_refs": list(self.evidence_refs),
            "conditions": [
                {"condition": c.condition.value, "status": c.status.value, "detail": c.detail,
                 "evidence_ref": c.evidence_ref}
                for c in self.condition_results
            ],
            "overall_status": self.overall_status.value,
            "approval_state": self.approval_state.value,
            "decision": self.decision.to_public() if self.decision is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "decided_at": self.decided_at.isoformat() if self.decided_at is not None else None,
        }
