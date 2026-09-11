"""Platform result log (M6.2D, staged in-memory) — a PII-safe record of each (staged) send attempt.

Records ONLY hashed / PII-safe fields (platform, event_id, event_name, dedup_key, result) — NEVER raw PII
(RULE-014, FAIL-008, SMK-017). Proves single delivery per (conversion x platform) and event_id CONSISTENCY
across platforms of one source event (SMK-003). Physical binding is the M6-OD-011 integration step.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple


class SendResult(str, Enum):
    WOULD_SEND = "WOULD_SEND"                              # payload built + policy passed (real send only if ON)
    BLOCKED_EXTERNAL_SEND_OFF = "BLOCKED_EXTERNAL_SEND_OFF"   # staged: external_send=OFF -> no real send
    DUPLICATE = "DUPLICATE"
    FAILED = "FAILED"


@dataclass(frozen=True)
class PlatformResultRecord:
    platform: str
    event_id: str
    event_name: str
    dedup_key: str
    result: SendResult
    at: Optional[datetime] = None


class PlatformResultLog:
    """Append-only PII-safe log of (staged) platform send attempts."""

    def __init__(self) -> None:
        self._records: List[PlatformResultRecord] = []

    def record(self, rec: PlatformResultRecord) -> None:
        self._records.append(rec)

    @property
    def records(self) -> Tuple[PlatformResultRecord, ...]:
        return tuple(self._records)

    def for_event(self, event_id: str) -> Tuple[PlatformResultRecord, ...]:
        return tuple(r for r in self._records if r.event_id == event_id)

    def __len__(self) -> int:
        return len(self._records)
