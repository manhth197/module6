"""Adjustment-record path (RULE-008, SMK-018) — how a VERIFIED attribution/revenue is corrected.

A materialized+verified Zone B is immutable (set-once). A post-verify correction is therefore NEVER an in-place
row rewrite (the store refuses it) — it is an `AdjustmentRecord{actor, reason, audit_ref, evidence_ref}` capturing
WHO changed WHAT and WHY, appended to an append-only `AdjustmentLog`. The original verified row is preserved; the
correction is an auditable overlay, not a mutation. Identity in the record is masked on export (RULE-014 / H02).
No commission is ever recorded here (RULE-019).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Tuple

from app.measurement.masking import mask


@dataclass(frozen=True)
class AdjustmentRecord:
    """One audited post-verify correction request. `proposed` holds the requested change (e.g.
    {'revenue_value': 300000}) — attribution/revenue values, never a commission (RULE-019). `actor` is masked on
    export (it may be an operator/user id). `at` is caller-supplied (staged code takes no clock)."""

    event_id: str
    actor: str
    reason: str
    audit_ref: str
    evidence_ref: str
    proposed: Mapping[str, Any] = field(default_factory=dict)
    at: Optional[datetime] = None

    def to_public(self) -> Dict[str, Any]:
        """Export view — `actor` masked (RULE-014 / H02). `proposed` is echoed as-is (attribution/revenue only —
        callers must not place PII there; if they do, mask at the call site)."""
        return {
            "event_id": self.event_id,
            "actor": mask(self.actor),
            "reason": self.reason,
            "audit_ref": self.audit_ref,
            "evidence_ref": self.evidence_ref,
            "proposed": dict(self.proposed),
            "at": self.at.isoformat() if self.at is not None else None,
        }


class AdjustmentLog:
    """Append-only log of adjustment records (RULE-007-like). No update / delete — a later correction is another
    appended record, never an edit of an earlier one."""

    def __init__(self) -> None:
        self._records: List[AdjustmentRecord] = []

    def append(self, record: AdjustmentRecord) -> AdjustmentRecord:
        self._records.append(record)
        return record

    @property
    def records(self) -> Tuple[AdjustmentRecord, ...]:
        return tuple(self._records)

    def for_event(self, event_id: str) -> Tuple[AdjustmentRecord, ...]:
        return tuple(r for r in self._records if r.event_id == event_id)

    def __len__(self) -> int:
        return len(self._records)
