"""M6-CTR-020 POST /api/admin/ads/learning-candidates — framework-neutral, INERT request handlers (M6.2H).

`handle_learning_candidate_create(body, deps)` creates an inert learning candidate and puts it in the review
queue (it is HELD while the safe range is unratified, M6-OD-006). `handle_learning_review_decision(body, deps)`
records an explicit owner/marketing approve/reject/hold. NEITHER publishes: `LearningDeps` holds only the inert
`LearningEngine` (library store + review queue) + audit — no publisher / Transport / auto-publish handle
(RULE-011, LEX-006, FAIL-006). The untrusted admin body is DATA (RULE-H03); a candidate is a proposal for review,
never published. Owner-decision fields (actor/reason/audit/evidence) must all be present (RULE-015). PII masked.
The HTTP mapping binds at the owner integration step (M6-OD-011).
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Optional

from app.measurement.learning.candidate import (
    AdsLearningCandidate,
    LearningCandidateKind,
    OwnerReviewDecision,
    ReviewState,
    TargetDim,
)
from app.measurement.learning.learning_engine import LearningEngine, ReviewDecisionError

_DECISION_STATE = {"APPROVE": ReviewState.APPROVED, "REJECT": ReviewState.REJECTED, "HOLD": ReviewState.HOLD}


@dataclass
class LearningDeps:
    """Read/create-only deps. Holds ONLY the inert LearningEngine + audit — no publisher / Transport / auto-publish
    handle (RULE-011, FAIL-006). The absence is asserted by a test."""

    engine: LearningEngine
    audit: Any = None


@dataclass(frozen=True)
class LearningResponse:
    status: str                                 # CREATED | DECIDED | REJECTED_INPUT
    candidate_id: Optional[str] = None
    review_state: Optional[str] = None
    safe_range_status: Optional[str] = None
    error_code: Optional[str] = None
    message: Optional[str] = None


def _str(body: Mapping[str, Any], key: str) -> Optional[str]:
    v = body.get(key)
    return v if isinstance(v, str) and v else None


def handle_learning_candidate_create(body: Any, deps: LearningDeps, *, now: Optional[datetime] = None) -> LearningResponse:
    if not isinstance(body, Mapping):
        return LearningResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID", message="body must be an object")
    dim = _str(body, "target_dim")
    if dim not in {d.value for d in TargetDim}:
        return LearningResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID",
                                message="target_dim must be one of persona/keyword/hook/landing/cta")
    kind = _str(body, "kind") or LearningCandidateKind.OPTIMIZATION.value
    if kind not in {k.value for k in LearningCandidateKind}:
        return LearningResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID", message="invalid candidate kind")
    sku_ref = _str(body, "sku_ref")
    if not sku_ref:
        return LearningResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID",
                                message="sku_ref (sellable SKU) is required (LEX-005)")
    score = body.get("score")
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return LearningResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID", message="score must be a number")

    candidate_id = "lc_" + hashlib.sha256(
        (dim + "|" + sku_ref + "|" + uuid.uuid4().hex).encode("utf-8")
    ).hexdigest()[:24]
    candidate = AdsLearningCandidate(
        candidate_id=candidate_id, kind=LearningCandidateKind(kind), target_dim=TargetDim(dim),
        score=float(score), sku_ref=sku_ref,
    )
    queued = deps.engine.review(candidate, now=now)   # -> review queue; HELD (safe range unratified, M6-OD-006)
    return LearningResponse(
        status="CREATED", candidate_id=queued.candidate_id,
        review_state=queued.review_state.value, safe_range_status=queued.safe_range_status.value,
    )


def handle_learning_review_decision(body: Any, deps: LearningDeps, *, now: Optional[datetime] = None) -> LearningResponse:
    if not isinstance(body, Mapping):
        return LearningResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID", message="body must be an object")
    candidate_id = _str(body, "candidate_id")
    if not candidate_id:
        return LearningResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID", message="candidate_id is required")
    kind = _str(body, "decision")
    if kind not in _DECISION_STATE:
        return LearningResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID",
                                message="decision must be APPROVE, REJECT or HOLD")
    fields = {k: _str(body, k) for k in ("actor", "reason", "audit_ref", "evidence_ref")}
    missing = [k for k, v in fields.items() if not v]
    if missing:
        return LearningResponse(status="REJECTED_INPUT", error_code="OWNER_DECISION_INCOMPLETE",
                                message=f"owner decision missing: {','.join(missing)}")

    decision = OwnerReviewDecision(
        actor=fields["actor"], reason=fields["reason"], audit_ref=fields["audit_ref"],
        evidence_ref=fields["evidence_ref"], new_state=_DECISION_STATE[kind], at=now,
    )
    try:
        result = deps.engine.record_review_decision(candidate_id, decision, now=now)
    except ReviewDecisionError as exc:
        return LearningResponse(status="REJECTED_INPUT", candidate_id=candidate_id,
                                error_code="REVIEW_DECISION_REFUSED", message=str(exc))
    return LearningResponse(
        status="DECIDED", candidate_id=result.candidate_id,
        review_state=result.review_state.value, safe_range_status=result.safe_range_status.value,
    )
