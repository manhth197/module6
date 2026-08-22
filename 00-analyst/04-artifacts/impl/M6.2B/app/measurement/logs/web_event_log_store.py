"""RULE-007 append-only web_event_logs store (M6-OWNED).

INSERT only. UPDATE and DELETE are not implemented and are actively rejected — history is never rewritten. A
duplicate `idempotency_key` does NOT create a second row and does not double-count (RULE-005). In-memory backend
for the staged slice; the physical DB binding (with DB-level append-only enforcement) is the M6-OD-011
integration step — see migrations/0001_create_web_event_logs.sql.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.measurement.models.web_event_log import WebEventLog


class AppendOnlyViolation(Exception):
    """Raised on any attempt to update or delete a web_event_logs row (RULE-007)."""


@dataclass(frozen=True)
class AppendResult:
    row: WebEventLog
    created: bool          # False when an existing row with the same idempotency_key was returned (dedup)


class WebEventLogStore:
    def __init__(self) -> None:
        self._by_key: Dict[str, WebEventLog] = {}
        self._order: List[str] = []

    def append(self, log: WebEventLog) -> AppendResult:
        """Insert one row. Idempotent on `idempotency_key`: a duplicate returns the existing row, created=False."""
        existing = self._by_key.get(log.idempotency_key)
        if existing is not None:
            return AppendResult(existing, created=False)
        self._by_key[log.idempotency_key] = log
        self._order.append(log.idempotency_key)
        return AppendResult(log, created=True)

    def get(self, idempotency_key: str) -> Optional[WebEventLog]:
        return self._by_key.get(idempotency_key)

    def all(self) -> Tuple[WebEventLog, ...]:
        return tuple(self._by_key[k] for k in self._order)

    def __len__(self) -> int:
        return len(self._order)

    # --- append-only guards (RULE-007): present so a mutation attempt fails loudly, not silently -----
    def update(self, *args, **kwargs):
        raise AppendOnlyViolation("web_event_logs is append-only (RULE-007): UPDATE is forbidden")

    def delete(self, *args, **kwargs):
        raise AppendOnlyViolation("web_event_logs is append-only (RULE-007): DELETE is forbidden")
