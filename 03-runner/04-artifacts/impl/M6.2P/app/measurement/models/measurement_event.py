"""M6-CTR-001 ads_measurement_event — the normalized measurement row (SPEC section 10.1, 20 DRAFT_LOCKED fields).

Binds to table ads_measurement_events (doc section 13). Module 6 owns & writes this normalized store serving
dashboard/ROAS. In M6.2B only **Zone A** (event-identity, write-once) is populated at INSERT, plus the INITIAL
data_quality_status. **Zone B** (attribution_context / revenue_value / order_code, set-once on the ORDER_VERIFIED
path, RULE-003/008) and **Zone C** (data_quality_status transitions, RULE-009) are the LATER enrichment workers'
duty (attribution_materializer M6-CTR-023 = M6.2E, data_quality_checker M6-CTR-024 = M6.2F) — NOT here.

All 20 doc fields are reproduced verbatim (name / type / optionality); the single physical addition is
ingested_at (changelog row 18). No doc field is renamed, removed, or retyped. `currency` is the locked constant
VND. Identity fields (customer_id / guest_id) are PII-class — masked before any log/evidence (RULE-014/H02).
`quote_snapshot_id` and `order_code` are REFERENCES only — M6 never writes QuoteSnapshot (M3) or order state (M8).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Optional

CURRENCY_VND = "VND"   # locked constant (SPEC section 10.1 'currency: VND'); not an enum, not variable


class DataQualityStatus(str, Enum):
    """SPEC section 10.1 data_quality_status enum (verbatim). Transitioned ONLY by data_quality_checker
    (M6-CTR-024, M6.2F). HOLD/FAIL rows are NEVER used as scale evidence (RULE-009)."""

    PASS = "PASS"
    HOLD = "HOLD"
    FAIL = "FAIL"


@dataclass(frozen=True)
class AdsMeasurementEvent:
    """One normalized measurement row (M6-CTR-001).

    Frozen: M6.2B inserts a Zone-A row once and never mutates it. Zone B/C enrichment is a later slice's
    controlled mechanism (a set-once/audited transition), NOT an in-place edit of this immutable row.
    """

    # --- Zone A: event identity / consent / trace / locked constant — write-once (RULE-007-like) ---
    event_id: str                                   # PRIMARY KEY
    event_code: str                                 # must be ACTIVE in event_registry (RULE-001, gated upstream)
    event_ts: datetime                              # business event time (source-supplied)
    idempotency_key: str                            # UNIQUE; locked RULE-005 formula (dedup, SMK-003)
    correlation_id: str                             # trace id for evidence linkage
    currency: str = CURRENCY_VND                    # locked constant VND (required; fixed at INSERT)
    ingested_at: Optional[datetime] = None          # physical persistence time (changelog row 18)
    customer_id: Optional[str] = None               # PII (at-event identity; masked in logs/evidence)
    guest_id: Optional[str] = None                  # PII
    page_id: Optional[str] = None
    live_session_id: Optional[str] = None
    campaign_id: Optional[str] = None
    adset_id: Optional[str] = None
    ad_id: Optional[str] = None
    sales_session_id: Optional[str] = None
    quote_snapshot_id: Optional[str] = None         # REFERENCE to M3 QuoteSnapshot; M6 never writes it
    consent_snapshot_id: Optional[str] = None       # REFERENCE to M6-CTR-006 (consent fail-closed upstream)
    # --- Zone B: verified-enrichment, set-once (LATER slices; ALWAYS unset at M6.2B) ---
    order_code: Optional[str] = None                # REFERENCE to Commerce/M8; never an order-state write
    revenue_value: Optional[float] = None           # ONLY from ORDER_VERIFIED (RULE-003); unset in M6.2B
    attribution_context: Mapping[str, Any] = field(default_factory=dict)  # materialized later (CTR-023)
    # --- Zone C: quality status, audited lifecycle (INITIAL here; transitions are CTR-024) ---
    data_quality_status: DataQualityStatus = DataQualityStatus.HOLD
