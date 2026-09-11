"""Generic transactional outbox store — shared by the measurement (M6-CTR-008) and audience (M6-CTR-011)
outboxes, whose row mechanics are identical (outbox_id, UNIQUE dedup_key, status, bounded-retry bookkeeping).

Runtime ENQUEUES rows (status=QUEUED) transactionally with the source; ONLY the dispatcher worker transitions
status / retry state (RULE-004, worker-only writes). `enqueue` is idempotent on the UNIQUE `dedup_key`: a
duplicate returns the existing row, created=False — no second row, no double send (RULE-005 / audience dedup).
In-memory backend for the staged slice; the physical transactional-outbox binding is the M6-OD-011 step.

Plan-delta (M6.2C PLAN C2/C3): the two per-domain stores are consolidated into this ONE generic store because
their mechanics are byte-identical; the measurement vs audience distinction lives in the ITEM type + dedup_key
formula, not in the store.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Generic, List, Optional, Tuple, TypeVar

from app.measurement.models.measurement_outbox import OutboxStatus

# A mutable outbox item exposing: outbox_id, dedup_key, status, next_retry_at (both CTR-008 and CTR-011 do).
T = TypeVar("T")


class OutboxStore(Generic[T]):
    def __init__(self) -> None:
        self._by_dedup: Dict[str, T] = {}
        self._by_id: Dict[str, T] = {}
        self._order: List[str] = []

    def enqueue(self, item: T) -> Tuple[T, bool]:
        """INSERT a QUEUED row. Idempotent on the UNIQUE dedup_key: a duplicate returns the existing row,
        created=False (no double send/count)."""
        existing = self._by_dedup.get(item.dedup_key)   # type: ignore[attr-defined]
        if existing is not None:
            return existing, False
        self._by_dedup[item.dedup_key] = item           # type: ignore[attr-defined]
        self._by_id[item.outbox_id] = item              # type: ignore[attr-defined]
        self._order.append(item.dedup_key)              # type: ignore[attr-defined]
        return item, True

    def get(self, dedup_key: str) -> Optional[T]:
        return self._by_dedup.get(dedup_key)

    def get_by_id(self, outbox_id: str) -> Optional[T]:
        return self._by_id.get(outbox_id)

    def all(self) -> Tuple[T, ...]:
        return tuple(self._by_dedup[k] for k in self._order)

    def due_items(self, now: datetime) -> List[T]:
        """Rows the worker may process: status in {QUEUED, RETRY} whose next_retry_at is due (or unset)."""
        due: List[T] = []
        for k in self._order:
            it = self._by_dedup[k]
            if it.status in (OutboxStatus.QUEUED, OutboxStatus.RETRY):   # type: ignore[attr-defined]
                nra = it.next_retry_at                                   # type: ignore[attr-defined]
                if nra is None or nra <= now:
                    due.append(it)
        return due

    def count_status(self, status: OutboxStatus) -> int:
        return sum(1 for k in self._order if self._by_dedup[k].status is status)   # type: ignore[attr-defined]

    def __len__(self) -> int:
        return len(self._order)
