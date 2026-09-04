"""M6-CTR-007 conversion_events store (M6-OWNED internal conversion source).

Append + idempotent on `idempotency_key` (RULE-005 replay dedup): a repeat returns the EXISTING conversion,
created=False — no double conversion. conversion_events NEVER sends externally (RULE-004); it is drained into the
measurement outbox by the enqueue seam. In-memory backend for the staged slice; DB binding = M6-OD-011.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.measurement.models.conversion_event import ConversionEvent


@dataclass(frozen=True)
class ConversionInsertResult:
    row: ConversionEvent
    created: bool          # False when an existing row with the same idempotency_key was returned (dedup)


class ConversionEventStore:
    def __init__(self) -> None:
        self._by_key: Dict[str, ConversionEvent] = {}
        self._by_id: Dict[str, ConversionEvent] = {}
        self._order: List[str] = []

    def create(self, row: ConversionEvent) -> ConversionInsertResult:
        existing = self._by_key.get(row.idempotency_key)
        if existing is not None:
            return ConversionInsertResult(existing, created=False)
        self._by_key[row.idempotency_key] = row
        self._by_id[row.conversion_id] = row
        self._order.append(row.idempotency_key)
        return ConversionInsertResult(row, created=True)

    def get(self, idempotency_key: str) -> Optional[ConversionEvent]:
        return self._by_key.get(idempotency_key)

    def get_by_id(self, conversion_id: str) -> Optional[ConversionEvent]:
        return self._by_id.get(conversion_id)

    def all(self) -> Tuple[ConversionEvent, ...]:
        return tuple(self._by_key[k] for k in self._order)

    def __len__(self) -> int:
        return len(self._order)
