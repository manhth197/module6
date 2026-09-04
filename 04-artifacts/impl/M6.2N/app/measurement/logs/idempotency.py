"""RULE-005 locked idempotency key.

The key components and their order are LOCKED and NOT altered:
    idempotency_key = event_code + page_id + session_id + raw_event_hash + normalized_ts

The five components are joined with a delimiter into a canonical string and hashed (sha256) into a compact,
collision-resistant key. Deduplication at ingest uses this key (RULE-005 / SMK-003 store-level invariant).
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

# Order is load-bearing (RULE-005). Do not reorder or add/remove components.
_KEY_COMPONENTS = ("event_code", "page_id", "session_id", "raw_event_hash", "normalized_ts")
_DELIM = "|"
# Sentinel for a MISSING (None) component. A lone backslash + "0" can never be produced by escaping real
# data (a real backslash is doubled to "\\", so an unescaped lone backslash never appears), so an ABSENT
# component and the literal string "None" can never collide onto one key.
_NONE_SENTINEL = "\\0"


def normalize_ts(event_ts: datetime) -> str:
    """Normalize an event timestamp to UTC, second precision, ISO-8601.

    RULE-005 is UNCHANGED — this canonicalizes only the VALUE of the ``normalized_ts`` component so the
    SAME instant always maps to ONE string. Without this, the same moment expressed at ``+07:00`` and at
    UTC (or naive vs aware) produced two different strings -> two idempotency keys -> the same event
    counted twice (revenue double-count; MAJOR-4).

    A NAIVE (tz-unaware) datetime is REJECTED: an ambiguous wall-clock time must never silently collapse
    two different instants — or split one — into the wrong key. Callers must pass a timezone-aware
    ``event_ts`` (the ingest contract already does).
    """
    if event_ts.tzinfo is None or event_ts.tzinfo.utcoffset(event_ts) is None:
        raise ValueError(
            "event_ts must be timezone-aware (RULE-005 normalization); a naive datetime is ambiguous"
        )
    return event_ts.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _escape(component: str) -> str:
    """Make the RULE-005 component join injective.

    Escape the escape char first, then the delimiter, so no combination of component contents can forge
    a false component boundary. Without this, an id containing ``|`` (``page_id``/``session_id`` are
    channel-origin) could make two DIFFERENT events serialize to ONE canonical string -> ONE key -> the
    second event silently swallowed and mislabelled as de-duplication (data loss disguised as dedup;
    MAJOR-5). The order and count of the five RULE-005 components are unchanged; only the serialization
    of each component is made unambiguous.

    A ``None`` (absent) component maps to a dedicated sentinel — NOT ``str(None) == "None"`` — so an absent
    component and the literal string ``"None"`` never collapse onto the same key (they are different events).
    """
    if component is None:
        return _NONE_SENTINEL
    return str(component).replace("\\", "\\\\").replace(_DELIM, "\\" + _DELIM)


def build_idempotency_key(
    event_code: str,
    page_id: str,
    session_id: str,
    raw_event_hash: str,
    normalized_ts: str,
) -> str:
    """Return the locked RULE-005 idempotency key for one ingress event."""
    canonical = _DELIM.join(
        _escape(c) for c in (event_code, page_id, session_id, raw_event_hash, normalized_ts)
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
