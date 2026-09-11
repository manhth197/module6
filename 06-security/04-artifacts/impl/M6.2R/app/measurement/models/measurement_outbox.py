"""M6-CTR-008 marketing_measurement_outbox — the transactional queue for Pixel/CAPI/Offline egress.

External measurement goes ONLY through this outbox + the dispatcher worker (M6-CTR-021), never directly from a
runtime request (RULE-004). One row per (conversion x platform), deduped UNIQUE on the LOCKED RULE-005 dedup_key.
Bounded retry -> dead-letter; no infinite retry, no silent loss (SMK-016). NO raw PII in the row or payload_ref
(the payload is built + hashed by the dispatcher at send, M6-OD-003/M6.2D).

Doc-named fields (error_log, next_retry_at — doc 12 L252) verbatim; the rest are [PACK] completions.
The item is MUTABLE by design: only the store / dispatcher worker transitions status + retry bookkeeping
(worker-only writes, RULE-004). Identity-derived fields are masked on export (O1, RULE-014/H02).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class MeasurementPlatform(str, Enum):
    """Doc-sourced measurement egress targets (doc 12 L248-250). Which connector runs first = M6-OD-004."""

    PIXEL = "PIXEL"
    CAPI = "CAPI"
    OFFLINE = "OFFLINE"        # dispatched ONLY after ORDER_VERIFIED or owner-approved (doc 12 L250)


class OutboxStatus(str, Enum):
    """SPEC 13 outbox item state machine: QUEUED -> SENT | RETRY(error_log,next_retry_at) -> DEAD_LETTER."""

    QUEUED = "QUEUED"
    SENT = "SENT"
    RETRY = "RETRY"
    DEAD_LETTER = "DEAD_LETTER"


@dataclass
class MeasurementOutboxItem:
    """One (conversion x platform) outbox row (M6-CTR-008). Mutable: transitions are worker/store-only."""

    outbox_id: str
    source_event_id: str                            # link to the conversion (M6-CTR-007)
    platform: MeasurementPlatform
    dedup_key: str                                  # LOCKED RULE-005; UNIQUE (one per conversion x platform)
    idempotency_key: str                            # LOCKED RULE-005; carried for platform-side dedup
    payload_ref: str                                # PII-SAFE reference; hashed payload built at dispatch (M6.2D)
    consent_snapshot_id: str                        # consent RE-VALIDATED at send (RULE-002)
    max_retries: int                                # bounded retry limit (value=config; the BOUND is doc-mandated)
    status: OutboxStatus = OutboxStatus.QUEUED
    retry_count: int = 0
    error_log: Optional[str] = None                 # doc 12 L252 verbatim — append log of failed attempts
    next_retry_at: Optional[datetime] = None        # doc 12 L252 verbatim — next bounded retry time
    created_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
