"""M6.2V / M6-OD-020 / E2 §3 — CODER test: the `not_sellable` sellability veto is TWO-DEEP.

M6.2U added the veto to conditions._risk (direct-feed channel). M6.2V wires it through the OTHER two paths that
reach the Scale Gate, so no route can lose it:

  * N1 — `recall_risk_contribution` PROPAGATES the veto into the merged map and returns it BEFORE the
    `risk_picture_complete` branch, so a not-sellable / unverified read can never fall to `{}`/HOLD nor be swallowed
    by a complete 6-lock no-active picture into a wrongful clear;
  * A2 — `scale_gate._assert_risk_clear_at_approval` refuses the approve when `current_risk_flags` carries
    `not_sellable` (mirrors conditions._risk), even on an otherwise-complete no-active read;
  * N5 — `map_risk_flags` uses `isinstance(decision, str) and decision == "SELLABLE"`, so a stray object's `__eq__`
    can never claim sellability.

Stricter / fail-closed ONLY: `not_sellable` is NOT a RISK_LOCK (the all-6 completeness is unchanged), and a
SELLABLE + no-active + complete-6 picture still clears exactly as in M6.2U (case e). STAGED; posture BLOCKED/OFF/OFF;
the mapper stays UNWIRED. Nothing here self-certifies (RULE-015).
"""
from __future__ import annotations

import pytest

from app.measurement.models.measurement_event import DataQualityStatus
from app.measurement.scale.conditions import (
    RISK_LOCKS,
    ScaleCondition,
    evaluate_conditions,
)
from app.measurement.scale.recall_risk_mapper import (
    RECALL_RISK_KEYS,
    OpsCoreAvailabilityResponse,
    map_pull_outcome,
    map_risk_flags,
    recall_risk_contribution,
)
from app.measurement.scale.scale_gate import ScaleGateViolation

_OTHER_LOCKS = ("complaint_p0", "platform_spam_flag", "crm_suppression")


def _risk_status(ctx):
    results, _ = evaluate_conditions(ctx)
    return next(r for r in results if r.condition is ScaleCondition.RISK).status


# ---- (a) contribution: a NOT_SELLABLE clean read -> merged carries not_sellable -> _risk FAIL + approve refused ---
def test_a_contribution_not_sellable_clean_read_fails_and_refuses_approve(
    make_scale_context, scale_gate, scale_store, make_owner_decision
):
    read = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=False, sale_lock=False, quality_hold=False, decision="NOT_SELLABLE"))
    merged = recall_risk_contribution(read, base_flags=None)
    assert merged.get("not_sellable") is True                    # N1: the veto reaches the merged map (not {})
    assert _risk_status(make_scale_context(risk_flags=merged)) is DataQualityStatus.FAIL

    scale_gate.propose("scr_v_a", {"campaign_id": "c1"}, make_scale_context(risk_flags=merged),
                       budget_cap=1.0, rollback_condition="r")
    with pytest.raises(ScaleGateViolation):                       # A2: approve refused on the sellability veto
        scale_gate.record_owner_decision("scr_v_a", make_owner_decision("APPROVE"), current_risk_flags=merged)
    assert scale_store.get("scr_v_a").approval_state.value == "PROPOSED"


# ---- (b) CRITICAL (N1): a COMPLETE 6-lock no-active merged picture + NOT_SELLABLE read -> still FAIL, never PASS ---
def test_b_complete_six_lock_plus_not_sellable_never_flips_to_pass(
    make_scale_context, scale_gate, scale_store, make_owner_decision
):
    """The chí-mạng case: base_flags supplies the other 3 locks (all clean) and the read supplies the 3 recall locks
    (all clean) -> the merged map is a COMPLETE 6-lock no-active picture that, pre-N1, `risk_picture_complete` would
    have swallowed into a clearing-eligible map. N1 propagates the veto and returns BEFORE that branch, so it stays
    FAIL; A2 refuses the approve. This proves the veto is never reversed into a PASS by completeness."""
    read = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=False, sale_lock=False, quality_hold=False, decision="NOT_SELLABLE"))
    merged = recall_risk_contribution(read, base_flags={lock: False for lock in _OTHER_LOCKS})
    assert all(lock in merged for lock in RISK_LOCKS)             # the merge IS complete on the 6 locks...
    assert not any(merged.get(lock) for lock in RISK_LOCKS)       # ...and no RISK_LOCK is active...
    assert merged.get("not_sellable") is True                    # ...but the veto is carried, so it must not clear
    assert _risk_status(make_scale_context(risk_flags=merged)) is DataQualityStatus.FAIL

    scale_gate.propose("scr_v_b", {"campaign_id": "c1"}, make_scale_context(risk_flags=merged),
                       budget_cap=1.0, rollback_condition="r")
    with pytest.raises(ScaleGateViolation):
        scale_gate.record_owner_decision("scr_v_b", make_owner_decision("APPROVE"), current_risk_flags=merged)
    assert scale_store.get("scr_v_b").approval_state.value == "PROPOSED"


# ---- (c) contribution: an UNVERIFIED (pull-error) read -> merged carries the veto (never {}/HOLD) -> FAIL ---------
def test_c_contribution_unverified_pull_error_does_not_collapse_to_empty(make_scale_context):
    read = map_pull_outcome(error="HTTP_429")
    assert read.unverified is True and read.complete is False
    merged = recall_risk_contribution(read, base_flags=None)
    assert merged == {"not_sellable": True}                      # N1: NOT {} — the unverified read carries the veto
    assert _risk_status(make_scale_context(risk_flags=merged)) is DataQualityStatus.FAIL


# ---- (d) approval (A2): current_risk_flags with not_sellable -> refuse, even a complete-6 no-active map -----------
def test_d_approval_refuses_on_not_sellable_flag(
    make_scale_context, scale_gate, scale_store, make_owner_decision
):
    scale_gate.propose("scr_v_d", {"campaign_id": "c1"}, make_scale_context(risk_flags={}),
                       budget_cap=1.0, rollback_condition="r")
    flags = {lock: False for lock in RISK_LOCKS}                  # complete 6-lock, none active...
    flags["not_sellable"] = True                                 # ...plus the sellability veto
    with pytest.raises(ScaleGateViolation):                       # A2 refuses before the completeness clear
        scale_gate.record_owner_decision("scr_v_d", make_owner_decision("APPROVE"), current_risk_flags=flags)
    assert scale_store.get("scr_v_d").approval_state.value == "PROPOSED"


# ---- (e) non-vacuity / stricter-only: SELLABLE + no-active + complete-6 -> PASS & approve clears (as M6.2U) -------
def test_e_sellable_complete_six_lock_still_clears_unchanged(
    make_scale_context, scale_gate, scale_store, make_owner_decision
):
    read = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=False, sale_lock=False, quality_hold=False, decision="SELLABLE"))
    merged = recall_risk_contribution(read, base_flags={lock: False for lock in _OTHER_LOCKS})
    assert "not_sellable" not in merged and set(merged) == set(RISK_LOCKS)   # SELLABLE -> no veto, exact 6-lock map
    assert _risk_status(make_scale_context(risk_flags=merged)) is DataQualityStatus.PASS  # clears as before

    # a context with NO not_sellable key behaves identically to M6.2U: a complete-6 no-active fresh read clears
    scale_gate.propose("scr_v_e", {"campaign_id": "c1"}, make_scale_context(risk_flags={}),
                       budget_cap=1.0, rollback_condition="r")
    res = scale_gate.record_owner_decision("scr_v_e", make_owner_decision("APPROVE"),
                                           current_risk_flags={lock: False for lock in RISK_LOCKS})
    assert res.approval_state.value == "APPROVED"


# ---- (f) N5: a non-str decision (incl. a hostile __eq__) -> fail-closed not_sellable veto ------------------------
class _HostileDecision:
    """A crafted object whose __eq__ claims to equal ANY value — pre-N5 this would coerce `decision == "SELLABLE"`
    to True and false-clear sellability. N5's isinstance(str) guard short-circuits before dispatching __eq__."""
    def __eq__(self, other):  # noqa: D401 - intentionally hostile
        return True
    def __hash__(self):
        return 0


def test_f_non_str_decision_is_failclosed_not_sellable(make_scale_context):
    hostile = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=False, sale_lock=False, quality_hold=False, decision=_HostileDecision()))
    assert hostile.sellable is False                             # N5: isinstance(str) guard wins over __eq__
    assert hostile.risk_flags.get("not_sellable") is True
    assert _risk_status(make_scale_context(risk_flags=hostile.risk_flags)) is DataQualityStatus.FAIL

    # a plain non-str (int) is fail-closed too
    numeric = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=False, sale_lock=False, quality_hold=False, decision=123))
    assert numeric.sellable is False and numeric.risk_flags.get("not_sellable") is True

    # a genuine SELLABLE str is unaffected (the wire feed): sellable, no veto, exact-3-key
    ok = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=False, sale_lock=False, quality_hold=False, decision="SELLABLE"))
    assert ok.sellable is True and set(ok.risk_flags) == set(RECALL_RISK_KEYS)
