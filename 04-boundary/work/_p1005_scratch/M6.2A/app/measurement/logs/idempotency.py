"""RULE-005 locked idempotency key.

The key components and their order are LOCKED and NOT altered:
    idempotency_key = event_code + page_id + session_id + raw_event_hash + normalized_ts

The five components are joined with a delimiter into a canonical string and hashed (sha256) into a compact,
collision-resistant key. Deduplication at ingest uses this key (RULE-005 / SMK-003 store-level invariant).
"""
from __future__ import annotations

import hashlib
from datetime import datetime

# Order is load-bearing (RULE-005). Do not reorder or add/remove components.
_KEY_COMPONENTS = ("event_code", "page_id", "session_id", "raw_event_hash", "normalized_ts")
_DELIM = "|"


def normalize_ts(event_ts: datetime) -> str:
    """Normalize an event timestamp to second precision in UTC ISO-8601 (stable across equal events)."""
    return event_ts.replace(microsecond=0).isoformat()


def build_idempotency_key(
    event_code: str,
    page_id: str,
    session_id: str,
    raw_event_hash: str,
    normalized_ts: str,
) -> str:
    """Return the locked RULE-005 idempotency key for one ingress event."""
    canonical = _DELIM.join(
        [event_code, page_id, session_id, raw_event_hash, normalized_ts]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
