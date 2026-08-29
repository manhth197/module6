"""M6-CTR-004 web_event_logs — the ONE table Module 6 owns and writes in this slice.

Append-only ingress record (RULE-007): M6 inserts one immutable row per ingress event and never updates or
deletes it. The row object is `frozen` to encode that immutability at the application layer; the store
(app.measurement.logs.web_event_log_store) refuses UPDATE/DELETE and dedups on `idempotency_key` (RULE-005).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class WebEventLog:
    """One append-only ingress row.

    Doc-named fields (§7 L117): page_id, session_id, source, consent_snapshot_id, event_ts, idempotency_key.
    Completions (PACK): log_id (PK), event_code (registry lookup + idempotency component), ingested_at
    (append time, distinct from event_ts), correlation_id (trace). `session_id` is PII-pseudonymous — mask if
    it resolves to a person (M6-OD-012).
    """
    log_id: str
    event_code: str
    page_id: str
    session_id: str                          # PII-pseudonymous
    source: str                              # channel-origin value = untrusted DATA; no raw PII in it
    event_ts: datetime
    idempotency_key: str                     # unique; locked RULE-005 formula
    ingested_at: datetime
    consent_snapshot_id: Optional[str] = None
    correlation_id: Optional[str] = None
