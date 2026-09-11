"""M6.2G leg 1 / M6-RULE-010 / M6-FAIL-006: NO auto scale. The Scale-Gate layer, its handlers, its deps, and the
ads_scale_request are INERT — there is no code path that raises a budget, enables a campaign, opens audience scale,
sends, or publishes. Module 6 computes and proposes; the owner acts outside Module 6 (production_flag=OFF).
"""
from __future__ import annotations

from app import config

_FORBIDDEN = (
    "raise_budget", "increase_budget", "set_budget", "adjust_budget", "enable_campaign", "start_campaign",
    "open_audience", "scale", "scale_up", "execute", "apply", "act", "send", "publish", "dispatch", "transport",
    "trigger",
)


def test_no_executable_method_on_scale_layer(scale_gate, scale_store):
    for obj in (scale_gate, scale_store):
        for name in _FORBIDDEN:
            assert not hasattr(obj, name), f"{type(obj).__name__} exposes forbidden method {name!r}"


def test_scale_deps_are_inert(make_scale_context, make_scale_deps):
    deps = make_scale_deps(make_scale_context())
    # deps carry ONLY the inert gate + server-side context + audit — no transport/budget/execute handle
    assert set(vars(deps).keys()) == {"scale_gate", "context", "audit"}
    for name in ("transport", "send", "budget", "execute", "scale", "publish", "connector"):
        assert not hasattr(deps, name)


def test_scale_request_is_inert_data(make_scale_context, scale_gate):
    req = scale_gate.propose("scr_inert", {"campaign_id": "c1"}, make_scale_context(),
                             budget_cap=100.0, rollback_condition="r")
    for name in _FORBIDDEN:
        assert not hasattr(req, name)
    # budget_cap is a recorded FIELD, not an action
    assert req.budget_cap == 100.0 and req.approval_state.value == "PROPOSED"


def test_scale_execution_flag_is_false():
    assert config.SCALE_EXECUTION_ENABLED is False
    # immutable staged posture — never flipped here
    assert config.PRODUCTION_FLAG == "OFF" and config.GLOBAL_GATEWAY_STATE == "BLOCKED"
