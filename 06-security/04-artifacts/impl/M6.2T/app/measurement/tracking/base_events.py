"""Locked Phase-1 base events (SPEC section 8.1, doc section 7 extract L123-134) — reproduced VERBATIM.

These nine event codes are the owner-LOCKED base-event vocabulary. Module 6 NEVER invents an event code
(RULE-001 / RULE-018): this set is copied from canon (00-spec/SPEC.md section 8.1), not authored here. The
frontend tracking hook (client layer) refuses to emit any code outside this set — the FIRST of the two
independent unknown-event layers; the backend independently re-validates against the Core event_registry
(M6-CTR-003) — the SECOND (M6.2B exit-gate leg 1).

GOLDEN_HOUR_START / _REMINDER (SPEC section 8.1 last row) are CONDITIONAL on M6-OD-009 (Golden Hour config,
OPEN) and are deliberately NOT in the locked Phase-1 set while that decision is OPEN — fail-closed (a
not-yet-ratified code is treated as unknown at the hook, never assumed active).
"""
from __future__ import annotations

from enum import Enum
from typing import FrozenSet


class BaseEvent(str, Enum):
    """The locked Phase-1 base events VIEW_LANDING..ORDER_VERIFIED (SPEC section 8.1, verbatim)."""

    VIEW_LANDING = "VIEW_LANDING"
    CLICK_CTA = "CLICK_CTA"
    SUBMIT_FORM = "SUBMIT_FORM"
    VIEW_ITEM = "VIEW_ITEM"
    ADD_TO_CART = "ADD_TO_CART"
    BEGIN_CHECKOUT = "BEGIN_CHECKOUT"
    ORDER_SUCCESS = "ORDER_SUCCESS"          # Core success signal; NOT a substitute for ORDER_VERIFIED
    USER_REGISTERED = "USER_REGISTERED"
    ORDER_VERIFIED = "ORDER_VERIFIED"        # the only revenue-valid event (RULE-003); revenue is a later slice


LOCKED_BASE_EVENTS: FrozenSet[str] = frozenset(e.value for e in BaseEvent)


def is_locked_base_event(event_code: object) -> bool:
    """True iff `event_code` is one of the owner-locked Phase-1 base events.

    Type-safe and fail-closed: a non-`str` is False (never coerced), so the client hook rejects hostile input
    exactly like the seam's type boundary. This is a CLIENT-side allow-list; the backend still re-validates
    against the live event_registry (a code can be a locked base event yet be DEREGISTERED in the registry).
    """
    return isinstance(event_code, str) and event_code in LOCKED_BASE_EVENTS
