"""CONSUMED read-models for the audience chain — M6-CTR-009 customer_segments + M6-CTR-010 members.

CRM/Ads segmentation OWNS these; Module 6 only READS them (RULE-018, no write path). Audience sync is permitted
ONLY from an APPROVED segment (RULE-004). LOAD-BEARING (doc 13 L270): segment membership is read for AUDIENCE
SYNC ONLY — it must NEVER trigger a CRM/pricing/Diamond/scale action (RULE-012). `member_key` is PII-class
(masked on export, RULE-014/H02); a member with non-VALID consent is not synced (fail-closed, RULE-002).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ApprovalState(str, Enum):
    """The 'được duyệt' property (doc 13 L269). Sync permitted ONLY when APPROVED (fail-closed)."""

    APPROVED = "APPROVED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class CustomerSegment:
    """M6-CTR-009 (CONSUMED). M6 reads APPROVED segments to drive audience sync; it never authors criteria."""

    segment_id: str
    name: str
    approval_state: ApprovalState
    criteria_ref: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass(frozen=True)
class SegmentMember:
    """M6-CTR-010 (CONSUMED). Read for audience sync ONLY — NEVER a trigger owner (RULE-012)."""

    segment_id: str
    member_key: str                                 # PII (masked on export)
    consent_snapshot_id: str                        # opt-out/expired => not synced (fail-closed, RULE-002)
    added_at: Optional[datetime] = None
