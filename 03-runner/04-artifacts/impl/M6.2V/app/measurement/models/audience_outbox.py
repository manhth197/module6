"""M6-CTR-011 marketing_audience_outbox — the transactional queue for audience sync.

Audience sync goes ONLY from APPROVED customer_segments + this outbox + consent pass (doc 12 L251); NEVER from
an ad-hoc query / data mart (RULE-012), NEVER direct from a runtime request (RULE-004). Consent fail-closed:
opt-out => REMOVE / not-ADD (RULE-002). Bounded retry -> dead-letter, mirroring the measurement outbox.
The audience dedup_key is DISTINCT from the RULE-005 measurement formula. NO raw PII in the row / payload_ref.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

# Reuse the shared outbox state machine.
from app.measurement.models.measurement_outbox import OutboxStatus


class AudiencePlatform(str, Enum):
    """Audience platform targets (doc 13 L271). Which connector runs first = M6-OD-004."""

    META_AUDIENCE = "META_AUDIENCE"
    GOOGLE_AUDIENCE = "GOOGLE_AUDIENCE"


class AudienceOperation(str, Enum):
    """Membership add/remove. A member opting out => REMOVE / not-ADD (fail-closed, RULE-002)."""

    ADD = "ADD"
    REMOVE = "REMOVE"


@dataclass
class AudienceOutboxItem:
    """One (segment x member x platform x operation) audience-sync row (M6-CTR-011). Mutable: worker/store-only."""

    outbox_id: str
    segment_id: str                                 # FK to an APPROVED customer_segments (M6-CTR-009)
    member_key: str                                 # PII (masked on export); payload hashed at dispatch
    platform: AudiencePlatform
    operation: AudienceOperation
    dedup_key: str                                  # audience dedup: segment_id+member_key+platform+operation (UNIQUE)
    payload_ref: str                                # PII-SAFE reference; hashed at dispatch (M6-OD-003/M6.2D)
    consent_snapshot_id: str                        # consent RE-VALIDATED at send (RULE-002)
    max_retries: int
    status: OutboxStatus = OutboxStatus.QUEUED
    retry_count: int = 0
    error_log: Optional[str] = None
    next_retry_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
