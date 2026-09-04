"""M6.2I leg L1 / M6-RULE-013 / M6-OD-009: the Golden Hour state is a MEASUREMENT observation, never a session
controller. Module 6 labels an observed state; Gateway/Live operates the session. GOLDEN_HOUR_START/REMINDER are
optional (M6-OD-009 OPEN) -> absent/unknown observed state degrades to UNKNOWN (fail-closed).
"""
from __future__ import annotations

from app.measurement.funnel import golden_hour as gh_mod
from app.measurement.funnel.funnel import GoldenHourFunnel
from app.measurement.funnel.golden_hour import GoldenHourState, observe_state

# a session controller would DRIVE a live session — Module 6 must expose no such verb (RULE-013)
_CONTROLLER_VERBS = (
    "start", "close", "open", "emit", "transition", "advance", "operate", "run",
    "start_session", "close_session", "set_state",
)


def test_observe_state_coerces_valid_tokens():
    assert observe_state("PRE") is GoldenHourState.PRE
    assert observe_state("LIVE") is GoldenHourState.LIVE
    assert observe_state("POST") is GoldenHourState.POST
    assert observe_state("CLOSED") is GoldenHourState.CLOSED
    assert observe_state(GoldenHourState.LIVE) is GoldenHourState.LIVE   # already-typed passes through


def test_observe_state_is_fail_closed_to_unknown():
    assert observe_state(None) is GoldenHourState.UNKNOWN               # no signal (M6-OD-009 optional)
    assert observe_state("bogus") is GoldenHourState.UNKNOWN            # unknown token
    assert observe_state(123) is GoldenHourState.UNKNOWN               # non-string
    assert observe_state("live") is GoldenHourState.UNKNOWN            # case-sensitive; not a valid token


def test_golden_hour_layer_has_no_session_controller():
    """RULE-013: neither the module nor the funnel exposes a verb that would OPERATE a live session."""
    for verb in _CONTROLLER_VERBS:
        assert not hasattr(gh_mod, verb), f"golden_hour module exposes controller verb {verb!r}"
        assert not hasattr(GoldenHourFunnel, verb), f"GoldenHourFunnel exposes controller verb {verb!r}"


def test_funnel_buckets_unknown_when_no_signal(make_measurement_event, make_golden_hour_funnel):
    make_measurement_event("e1", event_code="LIVE_COMMENT", live_session_id="ls_x", page_id="p")
    v = make_golden_hour_funnel().view_for("ls_x")    # no golden-hour annotation
    assert v.golden_hour_states == (GoldenHourState.UNKNOWN,)
