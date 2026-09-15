"""Official smoke — slice M6.2G — M6-SMK-009 (doc ADS-P0-009).

Authored by TESTER in M6-P1603 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1604
(TESTER_RUN -> 04-artifacts/test-reports/M6.2G/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF, SCALE_EXECUTION_ENABLED=False,
SCALE_MODEL_RATIFIED=False — nothing below flips a flag and nothing is ever scaled.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 409):

    Kịch bản (verbatim):          "Recall/Sale Lock active"
    Kết quả phải đạt (verbatim):  "Scale Gate FAIL/HOLD"

The Risk row is a HARD VETO (RULE-017): any active recall / sale-lock / quality-hold / complaint-P0 /
platform-spam-flag / CRM-suppression forces the Risk condition to FAIL and the whole gate to FAIL; an UNOBSERVED
risk state is fail-closed HOLD (never PASS). The veto is RE-CHECKED at owner-approval time, so a lock that
appears after a clean proposal still refuses the approval. Reuses the shared conftest scale fixtures
(make_scale_context, scale_gate, scale_store, make_owner_decision). All ids synthetic; no PII.
"""
from __future__ import annotations

import pytest

from app.measurement.models.measurement_event import DataQualityStatus
from app.measurement.scale.conditions import RISK_LOCKS, ScaleCondition, evaluate_conditions
from app.measurement.scale.scale_gate import ScaleGateViolation


# --- primary smoke: scenario verbatim (the full Risk row, doc §16 line 323) -----------------------
@pytest.mark.parametrize("lock", list(RISK_LOCKS))
def test_smk_009_active_risk_lock_forces_scale_gate_fail(make_scale_context, lock):
    """M6-SMK-009 "Recall/Sale Lock active" -> "Scale Gate FAIL/HOLD".

    recall and sale_lock (and every other Risk-row lock) each force Risk = FAIL and the overall gate to FAIL.
    """
    ctx = make_scale_context(risk_flags={l: (l == lock) for l in RISK_LOCKS})
    results, overall = evaluate_conditions(ctx)
    risk = next(r for r in results if r.condition is ScaleCondition.RISK)
    assert risk.status is DataQualityStatus.FAIL       # hard veto (RULE-017)
    assert overall is DataQualityStatus.FAIL           # worst-status dominates -> Scale Gate FAIL


def test_smk_009_recall_locked_request_cannot_be_approved(
    make_scale_context, scale_gate, scale_store, make_owner_decision
):
    """A recall-locked proposal is overall FAIL and an owner APPROVE with recall active is REFUSED (RULE-017
    re-check) — the request stays PROPOSED and is never authorized. Nothing is scaled."""
    ctx = make_scale_context(risk_flags={l: (l == "recall") for l in RISK_LOCKS})
    req = scale_gate.propose("scr_recall", {"campaign_id": "c1"}, ctx,
                             budget_cap=1_000_000.0, rollback_condition="revert to pilot baseline")
    assert req.overall_status is DataQualityStatus.FAIL

    with pytest.raises(ScaleGateViolation):
        scale_gate.record_owner_decision(
            "scr_recall", make_owner_decision("APPROVE"),
            current_risk_flags={l: (l == "recall") for l in RISK_LOCKS},
        )
    assert scale_store.get("scr_recall").approval_state.value == "PROPOSED"
    assert scale_store.get("scr_recall").is_scale_authorized is False


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_009_neg_unobserved_risk_is_hold_not_pass(make_scale_context):
    """The HOLD half of "FAIL/HOLD": when the risk/suppression state was never observed (empty risk_flags), Risk
    is fail-closed HOLD (never PASS) and the overall gate is HOLD — never a clean scale-ready PASS."""
    ctx = make_scale_context(risk_flags={})
    results, overall = evaluate_conditions(ctx)
    risk = next(r for r in results if r.condition is ScaleCondition.RISK)
    assert risk.status is DataQualityStatus.HOLD       # not checked -> fail-closed HOLD
    assert overall is DataQualityStatus.HOLD           # gate is HOLD, not PASS


def test_smk_009_neg_risk_recheck_catches_lock_after_clean_proposal(
    make_scale_context, scale_gate, make_owner_decision
):
    """RULE-017 is re-checked at approval: a proposal computed while risk was clean (overall HOLD) still cannot be
    approved if a sale_lock is active at approval time — the fresh read vetoes it (fail-closed)."""
    req = scale_gate.propose("scr_clean", {"campaign_id": "c1"}, make_scale_context(),
                             budget_cap=1_000_000.0, rollback_condition="revert")
    assert req.overall_status is DataQualityStatus.HOLD      # clean proposal is HOLD (staged), not FAIL

    with pytest.raises(ScaleGateViolation):
        scale_gate.record_owner_decision(
            "scr_clean", make_owner_decision("APPROVE"),
            current_risk_flags={l: (l == "sale_lock") for l in RISK_LOCKS},   # lock appears at approval
        )


# --- positive control: proves the FAIL is lock-caused, not blanket --------------------------------
def test_smk_009_control_no_active_locks_risk_passes(make_scale_context):
    """Control (non-vacuous): with the full risk row observed and NO lock active, Risk is PASS (not FAIL) — so the
    FAILs above are caused by the active lock, not a gate that always fails. The overall is still HOLD in the
    staged posture (Funnel M6-OD-002 / Dashboard M6-OD-005 fail-closed), never a scale-ready PASS."""
    results, overall = evaluate_conditions(make_scale_context())
    risk = next(r for r in results if r.condition is ScaleCondition.RISK)
    assert risk.status is DataQualityStatus.PASS
    assert overall is DataQualityStatus.HOLD           # never a clean PASS in the staged posture
