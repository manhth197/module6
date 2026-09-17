"""M6.2R / M6-OD-017 / SMK-030 / RULE-017 / RULE-015 / FAIL-006: recall-risk mapper -> existing Scale Gate.

The mapper turns an ops-core availability response (value object / dict — NO live HTTP) into the three
ops-core-sourced risk_flags (recall = recall_hold OR recall_case_open, sale_lock, quality_hold), reading the
presence booleans ONLY. Feeding a present lock to the EXISTING Scale Gate FAILs the Risk row EVEN when
decision==SELLABLE. M6.2U (M6-OD-020): a pull error / timeout / 429 / None / malformed is an UNVERIFIED read that
is now `not_sellable=True` -> Risk FAIL (fail-closed, stricter than the prior empty-{}/HOLD); a decision not observed
SELLABLE also sets `not_sellable` -> FAIL — a DISTINCT sellability veto, separate from the recall booleans (which are
STILL derived from the presence booleans only, never from decision). The mapper's 3 recall keys are a strict SUBSET
of RISK_LOCKS — a PARTIAL contribution, never a standalone clearing map. No PASS branch opened; STAGED; posture
BLOCKED/OFF/OFF unchanged.
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
    risk_picture_complete,
)
from app.measurement.scale.scale_gate import ScaleGateViolation

_OTHER_LOCKS = ("complaint_p0", "platform_spam_flag", "crm_suppression")


def _risk_status(ctx):
    results, _ = evaluate_conditions(ctx)
    return next(r for r in results if r.condition is ScaleCondition.RISK).status


# ---- LEG 1: the E2 mapping (M6-OD-017) — booleans only, additive recall_case_open, no fabricated lock ----
def test_recall_hold_maps_to_recall():
    # RULE A (M6.2U): decision="SELLABLE" isolates the boolean mapping under test — a sellable lot adds NO
    # `not_sellable` veto key, so the exact-3-key recall map is what this test asserts. recall_hold=True -> recall.
    read = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=True, sale_lock=False, quality_hold=False,
                                                      decision="SELLABLE"))
    assert read.complete is True
    assert read.risk_flags == {"recall": True, "sale_lock": False, "quality_hold": False}


def test_recall_case_open_is_additive():
    # recall_case_open TRUE alone (recall_hold False) -> recall True
    r1 = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=False, sale_lock=False, quality_hold=False,
                                                    recall_case_open=True))
    assert r1.risk_flags["recall"] is True
    # recall_case_open ABSENT -> treated False; recall follows recall_hold only
    r2 = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=False, sale_lock=False, quality_hold=False))
    assert r2.risk_flags["recall"] is False


def test_sale_lock_and_quality_hold_map_through():
    read = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=False, sale_lock=True, quality_hold=True))
    assert read.risk_flags["sale_lock"] is True and read.risk_flags["quality_hold"] is True
    assert read.risk_flags["recall"] is False


def test_output_keys_are_exactly_the_three_ops_core_locks():
    # RULE A (M6.2U): decision="SELLABLE" adds no `not_sellable` key, so the output key-set stays exactly the 3
    # ops-core recall locks — the invariant this test guards (no OTHER lock fabricated).
    read = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=True, sale_lock=True, quality_hold=True,
                                                      recall_case_open=True, decision="SELLABLE"))
    assert set(read.risk_flags.keys()) == set(RECALL_RISK_KEYS)     # no other lock fabricated


def test_mapper_never_derives_recall_booleans_from_decision(make_scale_context):
    # M6.2U (M6-OD-020): `decision` is read ONLY for the sellability veto; the recall booleans are STILL derived from
    # the presence booleans (ops-core §4), NEVER from decision. This replaces the old `never_reads_decision` framing
    # (the mapper now DOES read decision — but only for the DISTINCT sellability veto, never for a recall boolean).
    # (a) a SELLABLE clean lot with recall_hold=True -> recall STILL True (a present lock, not derived from SELLABLE)
    sellable_locked = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=True, sale_lock=False, quality_hold=False,
                                                                 decision="SELLABLE", block_reasons=("stale",)))
    assert sellable_locked.risk_flags["recall"] is True
    assert "not_sellable" not in sellable_locked.risk_flags        # a SELLABLE lot adds NO veto key
    # (b) a decision literally "RECALL" with recall_hold=False -> the recall BOOLEAN stays False (decision drives no
    # recall boolean) while not_sellable=True fires the DISTINCT sellability veto -> Risk FAIL.
    recall_decision_clean = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=False, sale_lock=False,
                                                                       quality_hold=False, decision="RECALL"))
    assert recall_decision_clean.risk_flags["recall"] is False
    assert recall_decision_clean.risk_flags.get("not_sellable") is True
    assert _risk_status(make_scale_context(risk_flags=recall_decision_clean.risk_flags)) is DataQualityStatus.FAIL


def test_from_mapping_dict_path_and_malformed_is_failclosed():
    ok = map_pull_outcome({"recall_hold": True, "sale_lock": False, "quality_hold": False, "decision": "SELLABLE"})
    assert ok.complete is True and ok.risk_flags["recall"] is True
    # RULE B (M6.2U): a MISSING required presence flag -> malformed -> UNVERIFIED -> not_sellable veto (fail-closed)
    miss = map_pull_outcome({"recall_hold": True, "sale_lock": False})            # quality_hold missing
    assert miss.complete is False and miss.risk_flags == {"not_sellable": True}
    # a NON-BOOL required flag ("true" string) -> malformed -> UNVERIFIED (never bool()-coerced to a truthy clear)
    coerce = map_pull_outcome({"recall_hold": "true", "sale_lock": False, "quality_hold": False})
    assert coerce.complete is False and coerce.risk_flags == {"not_sellable": True}


# ---- LEG 2: present lock -> existing Scale-Gate Risk FAIL + approve REFUSED, EVEN when SELLABLE ----
@pytest.mark.parametrize("kwargs", [
    {"recall_hold": True},                                   # SMK-030(i)
    {"recall_hold": False, "recall_case_open": True},        # SMK-030(ii)
])
def test_present_lock_fails_gate_even_when_sellable(kwargs, scale_gate, make_scale_context, make_owner_decision):
    resp = OpsCoreAvailabilityResponse(sale_lock=False, quality_hold=False, decision="SELLABLE", **{
        "recall_hold": kwargs.get("recall_hold", False),
        "recall_case_open": kwargs.get("recall_case_open", False),
    })
    read = map_risk_flags(resp)
    assert read.risk_flags["recall"] is True
    ctx = make_scale_context(risk_flags=read.risk_flags)           # feed ONLY the mapper output
    assert _risk_status(ctx) is DataQualityStatus.FAIL             # Risk row FAIL despite decision=SELLABLE

    scale_gate.propose("scr_leg2", {"campaign_id": "c1"}, ctx, budget_cap=1000.0, rollback_condition="revert")
    with pytest.raises(ScaleGateViolation):                        # RULE-017 re-check refuses the approve
        scale_gate.record_owner_decision("scr_leg2", make_owner_decision("APPROVE"),
                                         current_risk_flags=read.risk_flags)


# ---- LEG 3: pull error/timeout/429/None/malformed -> UNVERIFIED -> not_sellable -> gate FAILs (fail-closed) ----
@pytest.mark.parametrize("read", [
    map_pull_outcome(error="TIMEOUT"),
    map_pull_outcome(error="HTTP_429"),
    map_pull_outcome(error="CONNECTION_ERROR"),
    map_pull_outcome(response=None),
    map_pull_outcome({"recall_hold": True}),                  # malformed (missing sale_lock/quality_hold)
])
def test_pull_error_is_incomplete_and_gate_does_not_clear(read, scale_gate, make_scale_context, make_owner_decision):
    # RULE B (M6.2U): an unverified read is now not_sellable=True -> Risk FAIL (stricter than the prior empty-{}/HOLD);
    # the "does not clear" guarantee is PRESERVED and strengthened (FAIL also refuses the approve). Never a fabricated
    # recall True, never a False false-clear — the recall booleans stay UNOBSERVED (absent).
    assert read.complete is False and read.risk_flags == {"not_sellable": True} and read.unverified is True
    ctx = make_scale_context(risk_flags=read.risk_flags)          # unverified read -> sellability veto
    assert _risk_status(ctx) is DataQualityStatus.FAIL           # unverified -> not_sellable -> FAIL (fail-closed)

    scale_gate.propose("scr_leg3", {"campaign_id": "c1"}, ctx, budget_cap=1000.0, rollback_condition="revert")
    with pytest.raises(ScaleGateViolation):                       # unverified read -> approval REFUSED (does not clear)
        scale_gate.record_owner_decision("scr_leg3", make_owner_decision("APPROVE"),
                                         current_risk_flags=read.risk_flags)


# ---- Partial-contribution safety (impl red-team fix): the merge is fail-closed BY CONSTRUCTION ----
def test_clean_bare_merge_collapses_to_empty_and_does_not_clear(scale_gate, make_scale_context, make_owner_decision):
    """The mapper's clean 3-of-6 output is structurally NEVER a standalone clearing map: a bare merge (no other
    lock sources) collapses to {} -> the gate reads HOLD and REFUSES the approve. Feeds the REAL gate to prove it."""
    assert set(RECALL_RISK_KEYS) < set(RISK_LOCKS)               # strict subset: 3 of 6
    clean = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=False, sale_lock=False, quality_hold=False))
    bare = recall_risk_contribution(clean, base_flags=None)
    assert bare == {}                                           # incomplete + no active -> fail-closed empty
    assert risk_picture_complete(bare) is False

    ctx = make_scale_context(risk_flags=bare)
    assert _risk_status(ctx) is DataQualityStatus.HOLD          # {} -> HOLD (never a false PASS)
    scale_gate.propose("scr_bare", {"campaign_id": "c1"}, ctx, budget_cap=1000.0, rollback_condition="revert")
    with pytest.raises(ScaleGateViolation):
        scale_gate.record_owner_decision("scr_bare", make_owner_decision("APPROVE"), current_risk_flags=bare)


def test_full_six_lock_picture_is_clearing_eligible_and_fail_direction_holds():
    clean = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=False, sale_lock=False, quality_hold=False))
    # merged with the OTHER three lock observations -> a COMPLETE 6-lock picture (no active) -> clearing-eligible
    full = recall_risk_contribution(clean, base_flags={k: False for k in _OTHER_LOCKS})
    assert risk_picture_complete(full) is True and set(full.keys()) == set(RISK_LOCKS)
    # FAIL direction: a present recall lock surfaces in the merged map (even bare) so the gate FAILs
    locked = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=True, sale_lock=False, quality_hold=False))
    assert recall_risk_contribution(locked)["recall"] is True
    # a present lock in the base is preserved too (any active lock reaches the gate)
    base_active = recall_risk_contribution(clean, base_flags={"complaint_p0": True})
    assert base_active.get("complaint_p0") is True
    # an incomplete (pull-error) read -> {} (fail-closed)
    assert recall_risk_contribution(map_pull_outcome(error="TIMEOUT"), base_flags=None) == {}


def test_value_object_nonbool_presence_flag_is_failclosed():
    """Impl red-team fix (finding 2): map_risk_flags is the SINGLE strict-bool choke, so a directly-constructed
    value object (the S1b seam's first-class path) with a non-bool / None presence flag fails closed to an
    INCOMPLETE read -- never an 'unknown coerced to a clean clear'. bool() is NOT used to coerce the fields."""
    # RULE B (M6.2U): a non-bool presence flag is an UNVERIFIED read -> not_sellable veto (fail-closed), never an
    # 'unknown coerced to a clean clear'. bool() is NOT used to coerce the fields.
    for bad in (None, 0, 1, "", "false", "true", (), []):
        r = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=bad, sale_lock=False, quality_hold=False))
        assert r.complete is False and r.risk_flags == {"not_sellable": True}, f"non-bool recall_hold={bad!r} must fail closed"
    # a non-bool recall_case_open is fail-closed too (additive default False stays a real bool and is fine)
    r2 = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=False, sale_lock=False, quality_hold=False,
                                                    recall_case_open="true"))
    assert r2.complete is False and r2.risk_flags == {"not_sellable": True}
    # map_pull_outcome forwards a prebuilt value object through the same strict choke
    assert map_pull_outcome(OpsCoreAvailabilityResponse(recall_hold=None, sale_lock=None,
                                                        quality_hold=None)).complete is False
