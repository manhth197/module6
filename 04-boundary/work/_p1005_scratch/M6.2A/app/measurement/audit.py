"""Audit trail for reject/hold and identity-mapping decisions (RULE-001 / RULE-006 / RULE-015).

Every rejected/held ingress and every identity resolution is recorded here so nothing is silently lost. Subjects
are masked at the boundary (RULE-014/H02) — a raw identity value never enters an AuditRecord. In-memory sink;
durable persistence is bound at the M6-OD-011 integration step.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple

from app.measurement.masking import mask


@dataclass(frozen=True)
class AuditRecord:
    action: str                       # e.g. REJECT / HOLD / IDENTITY_RESOLVE
    reason: str                       # machine reason code, e.g. UNKNOWN_EVENT_NOT_IN_REGISTRY
    at: datetime
    event_code: Optional[str] = None
    subject_masked: Optional[str] = None   # already masked; never a raw identity value
    detail: Optional[str] = None


class AuditLog:
    """Append-only in-memory audit sink."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def record(
        self,
        action: str,
        reason: str,
        *,
        event_code: Optional[str] = None,
        subject: Optional[str] = None,
        detail: Optional[str] = None,
        at: Optional[datetime] = None,
    ) -> AuditRecord:
        """Record one audited decision. `subject` is masked here so callers cannot leak raw PII by accident."""
        rec = AuditRecord(
            action=action,
            reason=reason,
            at=at or datetime.now(timezone.utc),
            event_code=event_code,
            subject_masked=mask(subject),
            detail=detail,
        )
        self._records.append(rec)
        return rec

    @property
    def records(self) -> Tuple[AuditRecord, ...]:
        return tuple(self._records)

    def find(self, reason: str) -> Tuple[AuditRecord, ...]:
        return tuple(r for r in self._records if r.reason == reason)

    def __len__(self) -> int:
        return len(self._records)
