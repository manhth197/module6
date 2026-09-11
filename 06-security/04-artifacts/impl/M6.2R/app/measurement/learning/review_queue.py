"""Inert review queue for ads_learning_candidate (M6.2H, CTR-014/020).

Candidates land here for owner/marketing review; a review decision REPLACES the record and appends to an
append-only history — it is data, never a published action (RULE-011). This queue has NO publish / auto-publish /
send method. The physical DB binding is the M6-OD-011 integration step.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from app.measurement.learning.candidate import AdsLearningCandidate


class ReviewQueueViolation(Exception):
    """Raised on a forbidden op (duplicate enqueue / unknown update)."""


class ReviewQueue:
    def __init__(self) -> None:
        self._by_id: Dict[str, AdsLearningCandidate] = {}
        self._order: List[str] = []
        self._history: List[AdsLearningCandidate] = []

    def enqueue(self, candidate: AdsLearningCandidate) -> AdsLearningCandidate:
        if candidate.candidate_id in self._by_id:
            raise ReviewQueueViolation(f"candidate {candidate.candidate_id} already queued")
        self._by_id[candidate.candidate_id] = candidate
        self._order.append(candidate.candidate_id)
        self._history.append(candidate)
        return candidate

    def update(self, candidate: AdsLearningCandidate) -> AdsLearningCandidate:
        """Persist a review transition (a NEW frozen record with the same candidate_id). Append-only history."""
        if candidate.candidate_id not in self._by_id:
            raise ReviewQueueViolation(f"cannot update unknown candidate {candidate.candidate_id}")
        self._by_id[candidate.candidate_id] = candidate
        self._history.append(candidate)
        return candidate

    def get(self, candidate_id: str) -> Optional[AdsLearningCandidate]:
        return self._by_id.get(candidate_id)

    def all(self) -> Tuple[AdsLearningCandidate, ...]:
        return tuple(self._by_id[i] for i in self._order)

    @property
    def history(self) -> Tuple[AdsLearningCandidate, ...]:
        return tuple(self._history)

    def __len__(self) -> int:
        return len(self._order)
