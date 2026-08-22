"""M6-CTR-001 ads_measurement_events store (M6-OWNED normalized store).

INSERT appends one Zone-A row keyed UNIQUE on `idempotency_key` (RULE-005): a duplicate returns the EXISTING
row with created=False — no second measurement row, no double count (SMK-003). Forbidden ops fail LOUDLY
(`MeasurementStoreViolation`), never silently: Zone-A UPDATE, DELETE / history-rewrite, and — as a fail-closed
guard for this slice's scope — inserting a row that already carries `revenue_value` (revenue is set later, only
on the ORDER_VERIFIED path, RULE-003; M6.2B never sets it). Zone B/C enrichment (attribution/revenue set-once,
DQ transitions) is a LATER slice's mechanism and is not implemented here.

In-memory backend for the staged slice; the physical DB binding is the M6-OD-011 integration step — see
migrations/0002_create_ads_measurement_events.sql.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.measurement.models.measurement_event import AdsMeasurementEvent


class MeasurementStoreViolation(Exception):
    """Raised on a forbidden op: Zone-A update, delete/history-rewrite, or a revenue-bearing insert in M6.2B."""


@dataclass(frozen=True)
class InsertResult:
    row: AdsMeasurementEvent
    created: bool          # False when an existing row with the same idempotency_key was returned (dedup)


class MeasurementEventStore:
    def __init__(self) -> None:
        self._by_key: Dict[str, AdsMeasurementEvent] = {}
        self._by_event_id: Dict[str, AdsMeasurementEvent] = {}
        self._order: List[str] = []

    def insert(self, row: AdsMeasurementEvent) -> InsertResult:
        """Insert one normalized row. Idempotent on `idempotency_key` (RULE-005): a duplicate returns the
        existing row, created=False — no second measurement row, no double count (SMK-003)."""
        existing = self._by_key.get(row.idempotency_key)
        if existing is not None:
            return InsertResult(existing, created=False)
        # Scope guard (RULE-003): M6.2B inserts Zone A only. revenue_value is set later on the ORDER_VERIFIED
        # path (M6.2E), never at ingest — a revenue-bearing insert here is a fail-closed violation.
        if row.revenue_value is not None:
            raise MeasurementStoreViolation(
                "M6.2B inserts Zone A only; revenue_value is set later on the ORDER_VERIFIED path (RULE-003)"
            )
        self._by_key[row.idempotency_key] = row
        self._by_event_id[row.event_id] = row
        self._order.append(row.idempotency_key)
        return InsertResult(row, created=True)

    def get(self, idempotency_key: str) -> Optional[AdsMeasurementEvent]:
        return self._by_key.get(idempotency_key)

    def get_by_event_id(self, event_id: str) -> Optional[AdsMeasurementEvent]:
        return self._by_event_id.get(event_id)

    def all(self) -> Tuple[AdsMeasurementEvent, ...]:
        return tuple(self._by_key[k] for k in self._order)

    def __len__(self) -> int:
        return len(self._order)

    # --- forbidden-op guards (RULE-007/008 immutability) — fail loudly, never silently ---------------
    def update(self, *args, **kwargs):
        raise MeasurementStoreViolation(
            "ads_measurement_events Zone-A is write-once (RULE-007/008): UPDATE is forbidden in M6.2B"
        )

    def delete(self, *args, **kwargs):
        raise MeasurementStoreViolation(
            "ads_measurement_events forbids DELETE / history rewrite (RULE-007/008)"
        )
