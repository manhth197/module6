"""Official smoke — slice M6.2U — M6-SMK-033 (recall E2 §3 conformance; M6-OD-020; chief list 2026-09-16 B3).

Authored by TESTER in M6-P2903 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P2904
(TESTER_RUN -> 04-artifacts/test-reports/M6.2U/SMOKE_RESULTS.md). Governance is immutable here and nothing below
flips a flag, opens egress, or wires the mapper: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF.
Leg 1 ADDS a FAIL to the recall path (a DISTINCT sellability no-scale veto + a pull-error/unverified FAIL) — it is
stricter/fail-closed only, opens no PASS branch, and loosens nothing. The mapper stays UNWIRED (wiring is the S1b /
server-bind seam, out of scope).

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (row M6-SMK-033):

    Scenario (verbatim):
        Recall E2 §3 conformance (M6.2U): (i) an availability response decision=NOT_SELLABLE with all
        recall/sale/quality flags false; (ii) decision unknown/missing; (iii) a pull error/timeout/429

    Expected (verbatim):
        (i)+(ii) decision not observed as SELLABLE → Scale-Gate Risk row FAIL (sellability no-scale, E2 §1/§3); the
        recall booleans are still NOT derived from decision (ops-core §4 preserved); (iii) pull error → Risk FAIL
        (not HOLD) + a running-campaign 'unverified' signal; a SELLABLE + no-active-flag response still clears as
        before (nothing loosened); no flag flip, no egress

The mapper (app.measurement.scale.recall_risk_mapper.map_risk_flags) derives the 3 recall booleans from the presence
booleans ONLY (never from decision), and — separately (M6-OD-020) — reads decision ONCE for a sellability veto:
decision != "SELLABLE" sets `not_sellable=True`, which the gate's distinct `conditions._risk` check FAILs (before
the all-6 completeness check; `not_sellable` is NOT a RISK_LOCK). A pull error / incomplete read is UNVERIFIED →
`not_sellable=True` + `unverified=True` → Risk FAIL (replacing the prior empty-{}/HOLD). Reuses the coder regression
patterns (`_full6` isolation helper, `_risk_status`) and the shared conftest fixture `make_scale_context`.
"""
from __future__ import annotations

import os

import pytest

from app import config
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
)


def _risk_status(ctx):
    results, _ = evaluate_conditions(ctx)
    return next(r for r in results if r.condition is ScaleCondition.RISK).status


def _full6(read):
    """Merge the mapper output onto a COMPLETE all-6-lock, no-active base — isolating the read from the M6.2T all-6
    completeness HOLD (an otherwise-clearing picture), so what moves the merged map off PASS is an active recall lock
    or the `not_sellable` sellability veto (never the completeness HOLD)."""
    flags = {lock: False for lock in RISK_LOCKS}
    flags.update(read.risk_flags)
    return flags


# ---- (i) decision=NOT_SELLABLE + all recall/sale/quality flags false -> Risk FAIL (sellability no-scale) --------
def test_smk_033_scenario_i_not_sellable_all_flags_false_fails_risk(make_scale_context):
    """SMK-033(i). A well-formed availability response with decision=NOT_SELLABLE and all recall/sale/quality flags
    false: the read is COMPLETE and the recall booleans are all False (NOT derived from decision), but the distinct
    sellability veto sets not_sellable=True. Fed to an otherwise-clearing full-6 no-active picture, the Scale-Gate
    Risk row is FAIL (sellability no-scale, E2 §1/§3)."""
    read = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=False, sale_lock=False, quality_hold=False, decision="NOT_SELLABLE"))
    assert read.complete is True and read.sellable is False
    assert read.risk_flags["recall"] is False and read.risk_flags["sale_lock"] is False \
        and read.risk_flags["quality_hold"] is False                # recall booleans NOT derived from decision
    assert read.risk_flags.get("not_sellable") is True              # the distinct sellability veto fires
    assert _risk_status(make_scale_context(risk_flags=_full6(read))) is DataQualityStatus.FAIL


# ---- (ii) decision unknown/missing -> Risk FAIL (not observed as SELLABLE) --------------------------------------
@pytest.mark.parametrize("decision", ["UNKNOWN", "sellable", None])   # unknown token / wrong-case / missing
def test_smk_033_scenario_ii_unknown_or_missing_decision_fails_risk(decision, make_scale_context):
    """SMK-033(ii). A decision not observed EXACTLY 'SELLABLE' (an unknown token, a wrong-case 'sellable', or a
    missing/None decision) sets not_sellable=True → the Scale-Gate Risk row FAILs, while the recall booleans stay
    False (decision drives no recall boolean)."""
    read = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=False, sale_lock=False, quality_hold=False, decision=decision))
    assert read.complete is True and read.sellable is False
    assert read.risk_flags.get("not_sellable") is True
    assert read.risk_flags["recall"] is False                       # ops-core §4 preserved
    assert _risk_status(make_scale_context(risk_flags=_full6(read))) is DataQualityStatus.FAIL


# ---- (iii) a pull error / timeout / 429 / incomplete -> Risk FAIL (not HOLD) + an 'unverified' signal -----------
@pytest.mark.parametrize("read", [
    map_pull_outcome(error="HTTP_429"),
    map_pull_outcome(error="TIMEOUT"),
    map_pull_outcome(error="CONNECTION_ERROR"),
    map_pull_outcome(response=None),
    map_pull_outcome({"recall_hold": True}),                        # malformed (missing sale_lock/quality_hold)
])
def test_smk_033_scenario_iii_pull_error_unverified_fails_risk(read, make_scale_context):
    """SMK-033(iii). A pull error / timeout / 429 / absent / malformed read is UNVERIFIED: the ops-core recall locks
    are left unobserved and the mapper sets not_sellable=True + unverified=True, so the Scale-Gate Risk row is FAIL
    (not HOLD — the M6.2U conformance; the prior empty-{}/HOLD is replaced) and the running-campaign 'unverified'
    signal is surfaced."""
    assert read.complete is False and read.unverified is True       # the 'unverified' running-campaign signal
    assert read.risk_flags == {"not_sellable": True}                # recall booleans UNOBSERVED; only the veto is set
    assert _risk_status(make_scale_context(risk_flags=read.risk_flags)) is DataQualityStatus.FAIL   # FAIL, not HOLD
    assert _risk_status(make_scale_context(risk_flags=_full6(read))) is DataQualityStatus.FAIL      # even merged full-6


# ---- the recall booleans are NOT derived from decision (ops-core §4 preserved) ---------------------------------
def test_smk_033_recall_booleans_not_derived_from_decision(make_scale_context):
    """ops-core §4 preserved: a present recall lock FAILs even when decision=SELLABLE (the recall boolean comes from
    the presence boolean, not the decision, and SELLABLE adds no veto); and a clean lot with decision=NOT_SELLABLE
    keeps recall False (decision drives no recall boolean) while setting the sellability veto."""
    locked = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=True, sale_lock=False, quality_hold=False, decision="SELLABLE"))
    assert locked.risk_flags["recall"] is True
    assert "not_sellable" not in locked.risk_flags                  # SELLABLE adds no veto; the recall lock is what FAILs
    assert _risk_status(make_scale_context(risk_flags=_full6(locked))) is DataQualityStatus.FAIL

    clean = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=False, sale_lock=False, quality_hold=False, decision="NOT_SELLABLE"))
    assert clean.risk_flags["recall"] is False                      # decision does not fabricate a recall boolean
    assert clean.risk_flags.get("not_sellable") is True


# ---- clear-path PRESERVED: a SELLABLE + no-active-flag response still clears as before (nothing loosened) -------
def test_smk_033_sellable_no_active_still_clears(make_scale_context):
    """A SELLABLE + no-active-flag response still clears exactly as before: the mapper output is the exact-3-key
    recall map with NO not_sellable veto, and a COMPLETE all-6 no-active picture reaches Risk PASS (non-vacuous —
    the FAILs above are veto-caused, not a gate that always FAILs). The M6.2T all-6 completeness still holds: a
    partial SELLABLE 3-of-6 map → HOLD, never PASS."""
    clean = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=False, sale_lock=False, quality_hold=False, decision="SELLABLE"))
    assert clean.risk_flags == {"recall": False, "sale_lock": False, "quality_hold": False}   # exact-3-key, no veto
    assert clean.sellable is True
    assert _risk_status(make_scale_context(risk_flags=_full6(clean))) is DataQualityStatus.PASS   # clear-path unchanged
    assert _risk_status(make_scale_context(risk_flags=dict(clean.risk_flags))) is DataQualityStatus.HOLD  # 3-of-6 -> HOLD


# ---- the sellability veto is a DISTINCT key, not a 7th RISK_LOCK (non-mapper contexts unchanged) ----------------
def test_smk_033_not_sellable_distinct_from_risk_locks(make_scale_context):
    """`not_sellable` is a distinct sellability signal, NOT a RISK_LOCK / RECALL_RISK_KEY — so the all-6 completeness
    and every non-mapper scale context (which carry no not_sellable key) are unchanged."""
    assert "not_sellable" not in RISK_LOCKS
    assert "not_sellable" not in RECALL_RISK_KEYS
    # a complete all-6 no-active context with no not_sellable key still PASSes (unchanged); active lock still FAILs
    assert _risk_status(make_scale_context(risk_flags={lock: False for lock in RISK_LOCKS})) is DataQualityStatus.PASS
    assert _risk_status(make_scale_context(
        risk_flags={l: (l == "recall") for l in RISK_LOCKS})) is DataQualityStatus.FAIL


# ---- boundary: the mapper is UNWIRED (no app runtime import) -> no egress ---------------------------------------
def test_smk_033_mapper_unwired_no_egress():
    """No egress: the mapper is UNWIRED — no app runtime module imports `recall_risk_mapper` (staged; the S1b live
    pull is the go-live seam). Reuses the coder regression's walk."""
    import app
    app_root = os.path.dirname(os.path.abspath(app.__file__))
    mapper_tail = os.path.join("measurement", "scale", "recall_risk_mapper.py")
    offenders = []
    for dirpath, _dirs, files in os.walk(app_root):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            full = os.path.join(dirpath, fn)
            if full.endswith(mapper_tail):
                continue                                            # the mapper module itself is not a wiring
            if "recall_risk_mapper" in open(full, encoding="utf-8").read():
                offenders.append(os.path.relpath(full, app_root))
    assert offenders == [], f"mapper must stay UNWIRED (staged); imported by: {offenders}"


# ---- posture: no flag flip ------------------------------------------------------------------------------------
def test_smk_033_posture_immutable_no_flag_flip():
    """The governance posture is immutable (the expected tail: 'no flag flip, no egress')."""
    assert config.EXTERNAL_SEND == "OFF"
    assert config.PRODUCTION_FLAG == "OFF"
    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED"
