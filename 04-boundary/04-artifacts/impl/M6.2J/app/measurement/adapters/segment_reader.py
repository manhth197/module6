"""Staged in-memory SegmentReader adapter (M6.2C).

Read-only view of the CONSUMED audience chain (customer_segments M6-CTR-009 + members M6-CTR-010). Seeded for
the staged slice; the CRM-owned source binds at the owner integration step (M6-OD-011). No write path — Module 6
never mutates a CRM-owned segment/membership (RULE-018); membership is read for audience sync ONLY (RULE-012).
"""
from __future__ import annotations

from typing import Dict, List, Optional

from app.measurement.models.segments import CustomerSegment, SegmentMember


class InMemorySegmentReader:
    """Satisfies the SegmentReader port (get_segment + members)."""

    def __init__(
        self,
        segments: Optional[Dict[str, CustomerSegment]] = None,
        members: Optional[Dict[str, List[SegmentMember]]] = None,
    ) -> None:
        self._segments: Dict[str, CustomerSegment] = dict(segments or {})
        self._members: Dict[str, List[SegmentMember]] = {k: list(v) for k, v in (members or {}).items()}

    def get_segment(self, segment_id: str) -> Optional[CustomerSegment]:
        return self._segments.get(segment_id)

    def members(self, segment_id: str) -> List[SegmentMember]:
        return list(self._members.get(segment_id, ()))   # copy; caller cannot mutate the consumed source
