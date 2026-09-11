"""Official smoke — slice M6.2G — M6-SMK-012 (doc ADS-P0-012).

Authored by TESTER in M6-P1603 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1604
(TESTER_RUN -> 04-artifacts/test-reports/M6.2G/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF, SCALE_EXECUTION_ENABLED=False,
SCALE_MODEL_RATIFIED=False — nothing below flips a flag and nothing is ever scaled.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 412):

    Kịch bản (verbatim):          "Scale request không owner approval"
    Kết quả phải đạt (verbatim):  "Không scale"

A scale request without an explicit owner APPROVE never authorizes a scale: it stays PROPOSED and
`is_scale_authorized` is False (RULE-015 — the system never approves its own request). And even a RECORDED owner
APPROVE does not authorize a scale in the staged posture, because the computed conditions roll up to HOLD
(SCALE_MODEL_RATIFIED=False, M6-OD-005) — the honest fail-closed truth. Reuses the shared conftest scale fixtures
(make_scale_context, scale_gate, scale_store, make_owner_decision). All ids synthetic; no PII.
"""
from __future__ import annotations

from app import config


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_012_no_owner_approval_means_not_scale_authorized(make_scale_context, scale_gate, scale_store):
    """M6-SMK-012 "Scale request không owner approval" -> "Không scale".

    A proposed request with a budget cap + rollback but NO owner decision stays PROPOSED and is not authorized.
    """
    req = scale_gate.propose("scr_1", {"campaign_id": "c1"}, make_scale_context(),
                             budget_cap=1_000_000.0, rollback_condition="revert to baseline")
    assert req.approval_state.value == "PROPOSED"
    assert req.is_scale_authorized is False               # no owner decision -> not authorized -> no scale
    assert scale_store.get("scr_1").approval_state.value == "PROPOSED"


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_012_neg_gate_cannot_self_approve(scale_gate):
    """RULE-015: there is NO auto/self-approve entry point — an approval requires an explicit OwnerDecision — and
    the module ships no scale-execution path (SCALE_EXECUTION_ENABLED=False), so nothing can scale itself."""
    for name in ("approve", "auto_approve", "self_approve", "approve_all", "authorize",
                 "scale", "execute", "raise_budget", "enable_campaign"):
        assert not hasattr(scale_gate, name), f"scale gate must not expose {name!r}"
    assert config.SCALE_EXECUTION_ENABLED is False
    assert config.PRODUCTION_FLAG == "OFF" and config.GLOBAL_GATEWAY_STATE == "BLOCKED"


def test_smk_012_neg_recorded_owner_approve_still_not_scale_in_staged_posture(
    make_scale_context, scale_gate, scale_store, make_owner_decision
):
    """Even a RECORDED explicit owner APPROVE (clean risk, budget cap + rollback) does NOT authorize a scale while
    the attribution model is unratified (overall HOLD, M6-OD-005 / SCALE_MODEL_RATIFIED=False): approval_state
    becomes APPROVED but is_scale_authorized stays False — "không scale". Nothing is executed (RULE-010)."""
    scale_gate.propose("scr_appr", {"campaign_id": "c1"}, make_scale_context(),
                       budget_cap=1_000_000.0, rollback_condition="revert to baseline")
    new = scale_gate.record_owner_decision("scr_appr", make_owner_decision("APPROVE"))

    assert new.approval_state.value == "APPROVED"          # the CTR-026 transition is recorded ...
    assert new.is_scale_authorized is False                # ... but no scale is authorized (overall HOLD)
    assert config.SCALE_MODEL_RATIFIED is False            # the forward gate that keeps it HOLD
    assert scale_store.get("scr_appr").is_scale_authorized is False


def test_smk_012_control_owner_reject_is_recorded_no_scale(
    make_scale_context, scale_gate, scale_store, make_owner_decision
):
    """Control (non-vacuous): an explicit owner REJECT is recorded as a lifecycle decision (REJECTED) and is never
    a scale — proving the lifecycle records decisions but never executes one."""
    scale_gate.propose("scr_rej", {"campaign_id": "c1"}, make_scale_context(),
                       budget_cap=1_000_000.0, rollback_condition="revert")
    new = scale_gate.record_owner_decision("scr_rej", make_owner_decision("REJECT"))

    assert new.approval_state.value == "REJECTED"
    assert new.is_scale_authorized is False
    assert scale_store.get("scr_rej").approval_state.value == "REJECTED"
