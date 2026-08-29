"""Frontend tracking-hook guard (client layer) — M6.2B exit-gate leg 1, layer 1.

The STAGED Python representation of the "frontend tracking hooks for locked base events" (slice M6.2B). The real
browser/JS SDK binding is an owner-controlled integration step (M6-OD-011); the CONTRACT it must honor lives
here: a tracking hook emits an event ONLY if the event_code is one of the LOCKED base events (SPEC section 8.1).
An unknown / hostile code is refused at the client and audited — the FIRST of the two independent unknown-event
layers. Client validation is NEVER trusted alone (RULE-H03): the backend event_registry gate re-checks.

Channel-origin fields are untrusted DATA (RULE-H03); the hook builds a payload but interprets nothing in it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.measurement.audit import AuditLog
from app.measurement.tracking.base_events import is_locked_base_event


@dataclass(frozen=True)
class HookResult:
    emitted: bool
    event_code: str
    reason: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)


class TrackingHook:
    """Client-side emit guard. `emit()` returns a payload ONLY for a locked base event; otherwise it refuses
    (audited) and emits nothing — nothing reaches the transport for an unknown code."""

    def __init__(self, audit: AuditLog) -> None:
        self._audit = audit

    def emit(self, event_code: object, **fields: Any) -> HookResult:
        if not is_locked_base_event(event_code):
            # Unknown / hostile code refused at the CLIENT layer (leg-1 layer 1). Audited; nothing emitted.
            # A non-str code is never handed to the audit sink (would break its shape check) -> event_code=None.
            self._audit.record(
                "REJECT", "HOOK_UNKNOWN_EVENT",
                event_code=event_code if isinstance(event_code, str) else None,
            )
            safe = event_code if isinstance(event_code, str) else ""
            return HookResult(emitted=False, event_code=safe, reason="HOOK_UNKNOWN_EVENT")
        return HookResult(emitted=True, event_code=str(event_code), payload=dict(fields))
