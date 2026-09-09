"""Golden Hour STATE measurement (doc §7/§8, extract L138) — MEASURE-ONLY, never a session controller.

`Golden Hour phải vận hành theo trạng thái PRE → LIVE → POST → CLOSED.` Module 6 MEASURES the observed state;
Gateway/Live OPERATES the session (RULE-013; operating live sessions is out of scope). This module is therefore a
pure projection: it LABELS an observed golden-hour signal into a validated `GoldenHourState`. It has NO
start / close / open / emit / transition method — nothing here drives a real session.

`GOLDEN_HOUR_START` / `GOLDEN_HOUR_REMINDER` are M6-OD-009 (OPEN): optional, disabled-by-default, Gateway/Live owns
their emission config. They are treated as OPTIONAL inputs, never required. Absent / unknown / malformed observed
state ⇒ `UNKNOWN` (fail-closed) — the funnel still measures the conversion chain regardless of golden-hour state.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

# The golden-hour signal event codes (doc §7 L134). M6-OD-009 OPEN → optional/disabled-by-default; Gateway/Live
# owns emission. Referenced as constants only; Module 6 never emits them (RULE-013) and never invents them.
GOLDEN_HOUR_START = "GOLDEN_HOUR_START"
GOLDEN_HOUR_REMINDER = "GOLDEN_HOUR_REMINDER"


class GoldenHourState(str, Enum):
    """The doc-mandated Golden Hour states (VERBATIM, extract L138) + a fail-closed UNKNOWN sentinel.

    UNKNOWN is NOT a doc state; it is the fail-closed default Module 6 uses when no golden-hour state was observed
    (M6-OD-009 optional signals absent) — never assume PRE/LIVE without an observed signal."""

    PRE = "PRE"
    LIVE = "LIVE"
    POST = "POST"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


# The four real (operated-by-Gateway/Live) states, in doc order — for a well-formed-signal check.
OPERATED_STATES = (GoldenHourState.PRE, GoldenHourState.LIVE, GoldenHourState.POST, GoldenHourState.CLOSED)


def observe_state(reported: Any) -> GoldenHourState:
    """Label an OBSERVED golden-hour signal (a consumed value Gateway/Live reports) into a `GoldenHourState`.

    Fail-closed and measure-only: a real `GoldenHourState`/valid token is returned; anything else — None, an
    unknown token, a non-string — degrades to `UNKNOWN` (never assumed active). This function OBSERVES; it never
    commands a transition (RULE-013 — Gateway/Live operates the session)."""
    if isinstance(reported, GoldenHourState):
        return reported
    if isinstance(reported, str):
        try:
            state = GoldenHourState(reported)
        except ValueError:
            return GoldenHourState.UNKNOWN
        # An explicit UNKNOWN token is honored as UNKNOWN; the four operated states pass through.
        return state
    return GoldenHourState.UNKNOWN
