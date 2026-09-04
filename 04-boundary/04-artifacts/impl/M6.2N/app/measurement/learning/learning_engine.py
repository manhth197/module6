"""M6.2H Learning Engine skeleton — Seed → Run → Learn → Review → Publish (doc §17), GUARDED (RULE-011).

`seed()` fills the libraries from canonical sources only (the store rejects fabricated origin, LEX-006). `run()`
is a skeleton that records an active mapping per sellable SKU (nothing actually runs). `learn()` runs ONLY after a
canonical seed exists AND consumes ONLY verified business signals that passed the Data Quality Gate (RULE-011),
scoring the 5 doc dims. `review()` puts a candidate into the review queue; a candidate not WITHIN the owner-ratified
safe range (UNKNOWN while M6-OD-006 is OPEN) is HELD (SMK-011). `record_review_decision()` records an explicit
owner approve/reject/hold. There is DELIBERATELY NO publish / auto-publish method — publish is owner-approval-only
and the guarded safe-range publish is BLOCKED (LEARNING_AUTOPUBLISH_ENABLED / LEARNING_SAFE_RANGE_RATIFIED False,
FAIL-006). The audit detail is machine-safe (no untrusted free-text). Nothing publishes; nothing runs for real.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from app import config
from app.measurement.learning.candidate import (
    AdsLearningCandidate,
    OwnerReviewDecision,
    ReviewState,
    SafeRangeStatus,
    TargetDim,
)
from app.measurement.learning.libraries import StrategyLibraryKind, StrategyLibraryStore
from app.measurement.learning.mapping import StrategyMapping
from app.measurement.learning.review_queue import ReviewQueue
from app.measurement.models.measurement_event import DataQualityStatus


class LearningPreconditionError(Exception):
    """Raised when Learn is asked to run before a canonical seed exists (RULE-011, fail-closed)."""


class LearningPublishBlocked(Exception):
    """Raised if a publish is attempted — there is no auto-publish path (RULE-011, LEX-006, FAIL-006)."""


@dataclass(frozen=True)
class VerifiedSignal:
    """One business signal fed to Learn. It is used ONLY if it passed the Data Quality Gate (dq_status == PASS)
    AND is verified (from ORDER_VERIFIED / verified revenue). `value` is a normalized effectiveness score input."""

    target_dim: TargetDim
    value: float
    dq_status: DataQualityStatus
    verified: bool

    @property
    def is_usable(self) -> bool:
        return self.dq_status is DataQualityStatus.PASS and self.verified


class LearningEngine:
    def __init__(self, library_store: StrategyLibraryStore, review_queue: ReviewQueue, audit: Any = None) -> None:
        # RULE-011/LEX-006: no publisher, no connector, no auto-publish — the engine holds only the library store
        # and the review queue.
        self._libraries = library_store
        self._queue = review_queue
        self._audit = audit
        self._active_mappings: List[StrategyMapping] = []

    # --- Seed --------------------------------------------------------------------------------------
    def seed(self, kind: StrategyLibraryKind, seed_source: str, *, entry_id: str, content: Optional[str] = None):
        """Fill a library from a canonical source. Delegates to the store, which rejects a non-canonical source or
        any fabricated content while content fill is BLOCKED (M6-OD-007)."""
        return self._libraries.seed(kind, seed_source, entry_id=entry_id, content=content)

    # --- Run (skeleton) ----------------------------------------------------------------------------
    def run(self, mapping: StrategyMapping) -> StrategyMapping:
        """Record an active mapping (anchored to a sellable SKU). This is a SKELETON — nothing actually runs an
        acquisition/retargeting campaign here (staged; production_flag=OFF)."""
        self._active_mappings.append(mapping)   # StrategyMapping.__post_init__ already enforced the SKU anchor
        return mapping

    @property
    def active_mappings(self) -> tuple:
        return tuple(self._active_mappings)

    # --- Learn -------------------------------------------------------------------------------------
    def learn(self, signals: Iterable[VerifiedSignal]) -> Dict[TargetDim, float]:
        """Score the 5 doc dims from effectiveness signals. PRECONDITION (RULE-011): a canonical seed MUST exist
        (else refuse, fail-closed); and ONLY verified signals that passed the Data Quality Gate are consumed —
        every HOLD/FAIL/unverified signal is excluded. Returns dim -> mean score over usable signals."""
        if not self._libraries.seeded_kinds():
            raise LearningPreconditionError(
                "Learn cannot run before a canonical seed exists (RULE-011: learn only after seed)"
            )
        usable = [s for s in signals if s.is_usable]     # DQ-passed + verified only (fail-closed exclusion)
        buckets: Dict[TargetDim, List[float]] = {}
        for s in usable:
            buckets.setdefault(s.target_dim, []).append(s.value)
        scores = {dim: sum(vals) / len(vals) for dim, vals in buckets.items()}
        if self._audit is not None:
            self._audit.record(
                "IDENTITY_RESOLVE", "LEARNING_SCORED",
                detail=f"usable_signals={len(usable)};dims={len(scores)}",
            )
        return scores

    # --- Review ------------------------------------------------------------------------------------
    def review(self, candidate: AdsLearningCandidate, *, now: Optional[datetime] = None) -> AdsLearningCandidate:
        """Put a candidate into the review queue. Its safe-range status is fail-closed: UNKNOWN while M6-OD-006 is
        OPEN (LEARNING_SAFE_RANGE_RATIFIED=False). A candidate NOT WITHIN the safe range is HELD (SMK-011) — it is
        never auto-published; it awaits an explicit owner decision."""
        safe = candidate.safe_range_status
        if not config.LEARNING_SAFE_RANGE_RATIFIED:
            safe = SafeRangeStatus.UNKNOWN               # no ratified safe range -> fail-closed UNKNOWN
        state = ReviewState.CANDIDATE if safe is SafeRangeStatus.WITHIN else ReviewState.HOLD
        queued = replace(candidate, safe_range_status=safe, review_state=state, created_at=now)
        self._queue.enqueue(queued)
        if self._audit is not None:
            self._audit.record(
                "HOLD" if state is ReviewState.HOLD else "IDENTITY_RESOLVE",
                f"LEARNING_CANDIDATE_{state.value}",
                detail=f"candidate={candidate.candidate_id};safe_range={safe.value};dim={candidate.target_dim.value}",
            )
        return queued

    def record_review_decision(
        self, candidate_id: str, decision: OwnerReviewDecision, *, now: Optional[datetime] = None
    ) -> AdsLearningCandidate:
        """Record an EXPLICIT owner/marketing review decision (approve/reject/hold). The system never synthesizes
        one (RULE-015). Even an APPROVED candidate is NOT publishable unless it is WITHIN a ratified safe range
        (UNKNOWN while M6-OD-006 OPEN -> is_publish_authorized stays False). Nothing is published here."""
        cand = self._queue.get(candidate_id)
        if cand is None:
            raise ReviewDecisionError(f"unknown candidate {candidate_id}")
        if cand.review_state in (ReviewState.APPROVED, ReviewState.REJECTED):
            raise ReviewDecisionError(f"candidate {candidate_id} already {cand.review_state.value}")
        updated = replace(cand, review_state=decision.new_state, decision=decision, decided_at=now)
        self._queue.update(updated)
        if self._audit is not None:
            # machine-safe detail: NO untrusted free-text reason/audit_ref (subject/actor masked by the sink).
            self._audit.record(
                "HOLD", f"LEARNING_REVIEW_{decision.new_state.value}", subject=decision.actor,
                detail=f"candidate={candidate_id};state={decision.new_state.value}",
            )
        return updated

    # --- Publish (BLOCKED — no auto-publish path) --------------------------------------------------
    @staticmethod
    def guarded_publish_blocked() -> bool:
        """The guarded auto-publish path is BLOCKED: LEARNING_AUTOPUBLISH_ENABLED is False and no owner-ratified
        safe range exists (M6-OD-006 OPEN). There is deliberately NO method that publishes a candidate (RULE-011,
        LEX-006, FAIL-006); this only reports that guarded publish is blocked."""
        return not (config.LEARNING_AUTOPUBLISH_ENABLED and config.LEARNING_SAFE_RANGE_RATIFIED)


class ReviewDecisionError(Exception):
    """Raised on an invalid review transition (unknown / already-decided candidate)."""
