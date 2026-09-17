"""M6.2U / M6-OD-020 / E2_BLOCK_REASON_V1 §3 — CODER regression for the recall sellability conformance.

Leg 1 adds a DISTINCT sellability no-scale veto to the recall path (STRICTER / fail-closed ONLY, opens no PASS
branch). This regression pins the exact M6-OD-020 semantics against the REAL gate + mapper:

  * decision not observed SELLABLE (NOT_SELLABLE / unknown / missing) -> `not_sellable=True` -> Scale-Gate Risk FAIL,
    a signal DISTINCT from the recall booleans and NOT a RISK_LOCK;
  * a pull error / 429 / incomplete read -> UNVERIFIED -> `not_sellable=True` + `unverified` -> Risk FAIL;
  * the recall booleans are STILL derived from the presence booleans ONLY (never from decision): a present recall
    lock FAILs even when decision=SELLABLE, and a clean lot's booleans stay False whatever the decision says;
  * the certified clear-path is PRESERVED: a SELLABLE + no-active + COMPLETE all-6 picture still reaches Risk PASS;
  * the mapper is UNWIRED — no app runtime module imports it (staged; the S1b live pull is the go-live seam).

Nothing here flips a flag, wires the mapper, opens egress, or self-certifies (RULE-015). Posture BLOCKED/OFF/OFF.
"""
from __future__ import annotations

import os

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
)

_OTHER_LOCKS = ("complaint_p0", "platform_spam_flag", "crm_suppression")


def _risk_status(ctx):
    results, _ = evaluate_conditions(ctx)
    return next(r for r in results if r.condition is ScaleCondition.RISK).status


def _full6(read):
    """Merge the mapper output into a COMPLETE all-6-lock, no-active base so the sellability veto is isolated from
    the M6.2T all-6 completeness HOLD (an otherwise-clearing picture): only `not_sellable` can move it off PASS."""
    flags = {lock: False for lock in RISK_LOCKS}
    flags.update(read.risk_flags)
    return flags


# ---- The veto is a DISTINCT key, not a 7th RISK_LOCK -----------------------------------------------------------
def test_not_sellable_is_distinct_from_risk_locks():
    assert "not_sellable" not in RISK_LOCKS                       # not a lock -> all-6 completeness unchanged
    assert "not_sellable" not in RECALL_RISK_KEYS                 # not an ops-core recall key -> no merge into the 6


# ---- decision not observed SELLABLE -> Risk FAIL (even on an otherwise-clearing full-6 picture) -----------------
@pytest.mark.parametrize("decision", ["NOT_SELLABLE", "UNKNOWN", None])
def test_decision_not_sellable_fails_risk(decision, make_scale_context):
    read = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=False, sale_lock=False, quality_hold=False, decision=decision))
    assert read.complete is True                                 # a well-formed read: the booleans ARE observed
    assert read.risk_flags.get("not_sellable") is True           # ...but the sellability veto fires
    assert read.sellable is False
    ctx = make_scale_context(risk_flags=_full6(read))            # full-6 no-active -> would clear but for the veto
    assert _risk_status(ctx) is DataQualityStatus.FAIL           # sellability no-scale (E2 §3), DISTINCT veto


# ---- pull error / 429 / incomplete -> UNVERIFIED -> Risk FAIL + `unverified` ------------------------------------
@pytest.mark.parametrize("read", [
    map_pull_outcome(error="HTTP_429"),
    map_pull_outcome(error="TIMEOUT"),
    map_pull_outcome(response=None),
    map_pull_outcome({"recall_hold": True}),                     # malformed (missing sale_lock/quality_hold)
])
def test_pull_error_unverified_fails_risk(read, make_scale_context):
    assert read.complete is False and read.unverified is True
    assert read.risk_flags == {"not_sellable": True}            # recall booleans UNOBSERVED; only the veto is set
    assert _risk_status(make_scale_context(risk_flags=_full6(read))) is DataQualityStatus.FAIL


# ---- the recall booleans are NOT derived from decision (ops-core §4 preserved) ---------------------------------
def test_recall_booleans_not_derived_from_decision(make_scale_context):
    # a present recall lock FAILs even when decision=SELLABLE (recall from presence boolean, not decision)
    locked = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=True, sale_lock=False, quality_hold=False, decision="SELLABLE"))
    assert locked.risk_flags["recall"] is True
    assert "not_sellable" not in locked.risk_flags               # SELLABLE adds no veto; the recall lock is what FAILs
    assert _risk_status(make_scale_context(risk_flags=_full6(locked))) is DataQualityStatus.FAIL

    # a clean lot with decision=NOT_SELLABLE keeps recall False (decision drives no recall boolean) but sets the veto
    clean = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=False, sale_lock=False, quality_hold=False, decision="NOT_SELLABLE"))
    assert clean.risk_flags["recall"] is False
    assert clean.risk_flags.get("not_sellable") is True


# ---- clear-path PRESERVED: SELLABLE + no-active + COMPLETE all-6 -> Risk PASS (nothing loosened) ----------------
def test_sellable_no_active_full6_still_clears(make_scale_context):
    clean = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=False, sale_lock=False, quality_hold=False, decision="SELLABLE"))
    assert clean.risk_flags == {"recall": False, "sale_lock": False, "quality_hold": False}  # exact-3-key, no veto
    ctx = make_scale_context(risk_flags=_full6(clean))           # complete, no-active, no veto
    assert _risk_status(ctx) is DataQualityStatus.PASS           # certified clear-path unchanged (opens no NEW pass)
    # and the M6.2T all-6 completeness still holds: a PARTIAL SELLABLE map (3-of-6, no veto) -> HOLD, never PASS
    assert _risk_status(make_scale_context(risk_flags=dict(clean.risk_flags))) is DataQualityStatus.HOLD


# ---- the mapper is UNWIRED: no app runtime module imports it ----------------------------------------------------
def test_mapper_is_unwired_no_app_import():
    import app
    app_root = os.path.dirname(os.path.abspath(app.__file__))
    mapper_path = os.path.join("measurement", "scale", "recall_risk_mapper.py")
    offenders = []
    for dirpath, _dirs, files in os.walk(app_root):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            full = os.path.join(dirpath, fn)
            if full.endswith(mapper_path):
                continue                                         # the mapper module itself is not a wiring
            src = open(full, encoding="utf-8").read()
            if "recall_risk_mapper" in src:
                offenders.append(os.path.relpath(full, app_root))
    assert offenders == [], f"mapper must stay UNWIRED (staged); imported by: {offenders}"
