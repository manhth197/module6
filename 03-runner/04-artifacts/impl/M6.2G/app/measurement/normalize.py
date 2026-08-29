"""Normalize an ACCEPTED ingress event into the M6-CTR-001 ads_measurement_event (Zone-A insert, M6.2B).

Called by the track endpoint AFTER `ingest_event()` has ACCEPTED + logged the raw event. Builds the Zone-A
event-identity row: a deterministic `event_id` (derived from the locked idempotency_key so a replay maps to the
SAME event_id — dedup-consistent, SMK-003), the locked idempotency_key, currency=VND, an INITIAL
`data_quality_status = HOLD` (fail-closed — no DQ check has run; only M6-CTR-024 may transition it), and an
EMPTY attribution_context (materialized later by M6-CTR-023, M6.2E). Zone B (revenue / order / attribution) is
left unset. No enrichment, no revenue, no attribution resolution happens here (all later slices).
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional

from app.measurement.models.measurement_event import AdsMeasurementEvent, DataQualityStatus


def event_id_for(idempotency_key: str) -> str:
    """Stable `event_id` derived from the locked idempotency_key so a replayed event maps to the SAME
    event_id (dedup-consistent, SMK-003). Deterministic; no randomness, no wall-clock."""
    return "evt_" + hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()[:24]


def normalize_to_measurement_event(
    *,
    event_code: str,
    idempotency_key: str,
    event_ts: datetime,
    correlation_id: str,
    page_id: Optional[str] = None,
    consent_snapshot_id: Optional[str] = None,
    guest_id: Optional[str] = None,
    ingested_at: Optional[datetime] = None,
) -> AdsMeasurementEvent:
    """Build the Zone-A ads_measurement_event for an accepted, logged event. Zone B/C stay at their
    fail-closed defaults (no revenue, empty attribution_context, data_quality_status=HOLD)."""
    return AdsMeasurementEvent(
        event_id=event_id_for(idempotency_key),
        event_code=event_code,
        event_ts=event_ts,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        ingested_at=ingested_at or datetime.now(timezone.utc),
        page_id=page_id,
        guest_id=guest_id,
        consent_snapshot_id=consent_snapshot_id,
        data_quality_status=DataQualityStatus.HOLD,   # INITIAL; transitions are M6-CTR-024 (M6.2F)
        # Zone B intentionally unset: revenue_value=None, order_code=None, attribution_context={} (M6.2E)
    )
