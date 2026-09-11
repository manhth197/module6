"""M6-CTR-014 ads_learning_candidate — INERT proposal for owner/marketing review (M6.2H).

The Learn stage produces candidates (delta / safe-range / optimization) targeting one of the 5 doc §17 Learn
dims (persona / keyword / hook / landing / CTA). A candidate is INERT DATA: it lands in a review queue and can be
approved / rejected / held by an owner — it NEVER publishes. A candidate outside (or, while M6-OD-006 is OPEN,
UNKNOWN) the safe range is HELD, never published (SMK-011). There is no auto-publish path (RULE-011, LEX-006,
FAIL-006). Identity/actor masked on export (RULE-014).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from app.measurement.masking import mask


class LearningCandidateKind(str, Enum):
    """Permitted learning outputs (RULE-011): candidate / delta recommendation / safe-range optimization."""

    DELTA = "DELTA"
    SAFE_RANGE = "SAFE_RANGE"
    OPTIMIZATION = "OPTIMIZATION"


class TargetDim(str, Enum):
    """The 5 doc §17 Learn-scoring dims (extract 351)."""

    PERSONA = "persona"
    KEYWORD = "keyword"
    HOOK = "hook"
    LANDING = "landing"
    CTA = "cta"


class ReviewState(str, Enum):
    """Review-queue lifecycle. No state publishes — publish is owner-approval-only, outside this module."""

    CANDIDATE = "CANDIDATE"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    HOLD = "HOLD"


class SafeRangeStatus(str, Enum):
    """Whether a candidate is within the owner-approved safe range. UNKNOWN while M6-OD-006 is OPEN (fail-closed)."""

    WITHIN = "WITHIN"
    OUTSIDE = "OUTSIDE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class OwnerReviewDecision:
    """An explicit owner/marketing review decision (approve/reject/hold). Requires actor + reason + audit +
    evidence — the system never synthesizes one (RULE-015). `actor` masked on export."""

    actor: str
    reason: str
    audit_ref: str
    evidence_ref: str
    new_state: ReviewState
    at: Optional[datetime] = None

    def to_public(self) -> Dict[str, Any]:
        return {
            "actor": mask(self.actor),
            "reason": self.reason,
            "audit_ref": self.audit_ref,
            "evidence_ref": self.evidence_ref,
            "new_state": self.new_state.value,
            "at": self.at.isoformat() if self.at is not None else None,
        }


@dataclass(frozen=True)
class AdsLearningCandidate:
    """One inert learning candidate (CTR-014). Frozen; a review transition produces a NEW record, never a publish."""

    candidate_id: str
    kind: LearningCandidateKind
    target_dim: TargetDim
    score: float
    sku_ref: str                                    # anchored to a sellable SKU (LEX-005)
    evidence_refs: Tuple[str, ...] = ()
    review_state: ReviewState = ReviewState.CANDIDATE
    safe_range_status: SafeRangeStatus = SafeRangeStatus.UNKNOWN   # fail-closed (M6-OD-006 OPEN)
    decision: Optional[OwnerReviewDecision] = None
    created_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None

    @property
    def is_publish_authorized(self) -> bool:
        """A publish is authorized ONLY when an owner APPROVED the candidate AND it is within the owner-ratified
        safe range. While M6-OD-006 is OPEN the safe range is UNKNOWN, so this is False — no candidate is
        publishable. Even when True, NOTHING is auto-published here (RULE-011, LEX-006): the owner publishes it,
        guarded, outside Module 6."""
        return (
            self.review_state is ReviewState.APPROVED
            and self.safe_range_status is SafeRangeStatus.WITHIN
        )

    def to_public(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "kind": self.kind.value,
            "target_dim": self.target_dim.value,
            "score": self.score,
            "sku_ref": self.sku_ref,
            "evidence_refs": list(self.evidence_refs),
            "review_state": self.review_state.value,
            "safe_range_status": self.safe_range_status.value,
            "decision": self.decision.to_public() if self.decision is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "decided_at": self.decided_at.isoformat() if self.decided_at is not None else None,
        }
