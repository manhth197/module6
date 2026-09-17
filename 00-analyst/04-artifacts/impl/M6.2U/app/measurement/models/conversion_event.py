"""M6-CTR-007 conversion_events — the internal conversion source that FEEDS the measurement outbox.

Created (before any external measurement is sent) by POST /api/ads/conversions (M6-CTR-017). External
measurement goes ONLY through marketing_measurement_outbox + the dispatcher worker, never directly from a
runtime request (RULE-004). Core policy governs which events qualify as a revenue conversion (M6-OD-008);
revenue is recorded ONLY from ORDER_VERIFIED (RULE-003) — M6 never computes it. Identity is PII-class
(masked on export, RULE-014/H02).

The doc names conversion_events by role only (no field-level schema) — every field is a [PACK] completion
anchored to a locked rule/contract. `idempotency_key` is a [PACK] completion (CTR-017 request field) used for
conversion-level replay dedup; the per-platform RULE-005 dedup_key lives on the outbox row (M6-CTR-008).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Optional

CURRENCY_VND = "VND"   # locked constant (CTR-001, doc 10.1)


class DispatchState(str, Enum):
    """CTR-007 lifecycle. conversion_events itself NEVER sends externally (RULE-004)."""

    CREATED = "CREATED"
    QUEUED = "QUEUED"          # enqueued to marketing_measurement_outbox
    DISPATCHED = "DISPATCHED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ConversionEvent:
    """One internal conversion row (M6-CTR-007). Frozen: the identity/consent/trace facts are write-once;
    dispatch progress is tracked on the OUTBOX rows, not by mutating this source row."""

    conversion_id: str
    event_code: str                                 # must be ACTIVE in event_registry (RULE-001)
    source_event_id: str                            # the ads_measurement_event / web_event_log it derives from
    correlation_id: str                             # trace linkage (evidence)
    customer_or_guest_key: str                      # PII (masked on export); a dedup_key component
    consent_snapshot_id: str                        # consent gate ref (RULE-002); egress only if VALID
    occurred_at: datetime                           # conversion event time; event_ts_bucket component
    idempotency_key: str                            # [PACK] conversion-level replay dedup (server-derived)
    attribution_context_ref: Optional[str] = None   # link to CTR-002 (materialized later, M6.2E)
    revenue_value: Optional[float] = None           # ONLY from ORDER_VERIFIED (RULE-003); else absent
    currency: Optional[str] = None                  # VND whenever revenue_value present
    order_code: Optional[str] = None                # REFERENCE to Commerce/M8; M6 never writes order state
    dedup_inputs: Mapping[str, Any] = field(default_factory=dict)   # platform-agnostic dedup components
    dispatch_state: DispatchState = DispatchState.CREATED
    created_at: Optional[datetime] = None
