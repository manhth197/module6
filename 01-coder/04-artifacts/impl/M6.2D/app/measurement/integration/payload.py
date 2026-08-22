"""Platform payload builder (M6.2D) — PII-safe, with the SHARED platform event_id for cross-platform dedup.

`event_id = hash(source_event_id + event_code)` is **shared** across PIXEL / CAPI / OFFLINE of ONE source event,
so the platform (Meta) collapses them -> no double count (FAIL-001, SMK-003). The internal `dedup_key` stays
per-platform (one outbox row per conversion x platform, M6.2C). No raw PII in the payload (RULE-014, FAIL-008):
every identity field is hashed via the hash-policy mechanism. Nothing here sends; the payload is what the staged
transport WOULD hand a connector once M6-OD-003/004 + the M6.2G re-gate open a real send.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict

from app.measurement.integration.hash_policy import to_public_safe


def platform_event_id(source_event_id: str, event_code: str) -> str:
    """The platform-facing dedup id — SHARED across platforms for one source event (the Meta shared event_id).
    A DIFFERENT id per platform would double-count on the platform side (FAIL-001)."""
    return "mev_" + hashlib.sha256(f"{source_event_id}|{event_code}".encode("utf-8")).hexdigest()[:24]


@dataclass(frozen=True)
class PlatformPayload:
    platform: str
    event_name: str                                   # = event_code (doc taxonomy)
    event_id: str                                     # shared across platforms of one source event
    user_data: Dict[str, str] = field(default_factory=dict)   # ALL hashed — never raw PII


def build_platform_payload(conversion: Any, platform: Any) -> PlatformPayload:
    """Build a PII-safe payload for one (conversion, platform). Identity is hashed; the event_id is shared so
    Pixel/CAPI/Offline of the same source event dedup on the platform side."""
    return PlatformPayload(
        platform=getattr(platform, "value", str(platform)),
        event_name=conversion.event_code,
        event_id=platform_event_id(conversion.source_event_id, conversion.event_code),
        user_data=to_public_safe({"identity": conversion.customer_or_guest_key}),
    )
