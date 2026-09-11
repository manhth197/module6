"""Official smoke — slice M6.2R — M6-SMK-030 (chief E2_BLOCK_REASON_V1 2026-09-10 §3/§5; recall-lock M6-OD-017).

Authored by TESTER in M6-P2603 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P2604
(TESTER_RUN -> 04-artifacts/test-reports/M6.2R/SMOKE_RESULTS.md). Governance is immutable here and nothing below
flips a flag, opens egress, or calls a real network: global_gateway_state=BLOCKED, production_flag=OFF,
external_send=OFF, SCALE_MODEL_RATIFIED=False. The ops-core availability response is a value object / dict built
in the test (STAGED) — the live HTTP client is the S1b seam / go-live and is not built or called here.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (row M6-SMK-030):

    Scenario (verbatim):
        Ops-core availability responses fed to the M6 recall mapper: (i) decision=SELLABLE + recall_hold=true
        (clean-lot); (ii) recall_case_open=true (additive); (iii) a pull error/timeout/429

    Expected (verbatim):
        mapper sets risk_flags['recall']=recall_hold OR recall_case_open, sale_lock, quality_hold; Scale-Gate Risk
        row FAILs on any presence-flag true EVEN when decision=SELLABLE; the mapper never reads
        decision/block_reasons; a pull error → incomplete/unknown risk read → gate FAIL (fail-closed, RULE-017);
        no PII, external_send OFF

The mapper (app.measurement.scale.recall_risk_mapper) turns an ops-core /v1/availability/check response into the
three ops-core-sourced risk_flags (recall = recall_hold OR recall_case_open, sale_lock, quality_hold), reading the
presence booleans only — never decision / block_reasons (M6 does not own the recall decision, RULE-018). Feeding a
present lock to the EXISTING Scale Gate (no gate-logic change) fails the Risk row (RULE-017 hard veto) and refuses
an owner approve, even when decision == SELLABLE. A pull error / timeout / 429 / None / malformed is an incomplete
read (empty) that leaves the locks unobserved, so the gate is fail-closed HOLD and the approve is refused — never a
false-clear. Reuses the shared conftest scale fixtures (make_scale_context, scale_gate, scale_store,
make_owner_decision) and the mapper's public surface. All ids synthetic; refs are campaign/SKU refs, not PII.
"""
from __future__ import annotations

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
    recall_risk_contribution,
    risk_picture_complete,
)
from app.measurement.scale.scale_gate import ScaleGateViolation


def _risk_status(ctx):
    results, _ = evaluate_conditions(ctx)
    return next(r for r in results if r.condition is ScaleCondition.RISK).status


# ---- Scenario (i): decision=SELLABLE + recall_hold=true (clean-lot) -> recall True; gate FAIL EVEN when SELLABLE
def test_smk_030_scenario_i_recall_hold_maps_and_gate_fails_even_when_sellable(
    make_scale_context, scale_gate, scale_store, make_owner_decision
):
    """SMK-030(i). A clean-lot response (decision=SELLABLE) with recall_hold=true maps to risk_flags['recall']=True
    (the mapper reads the presence boolean, not the decision); sale_lock / quality_hold map through unchanged.
    Feeding ONLY the mapper output to the existing Scale Gate fails the Risk row despite decision=SELLABLE, and an
    owner APPROVE is refused (RULE-017 re-check) — the request stays PROPOSED and nothing is scaled."""
    resp = OpsCoreAvailabilityResponse(
        recall_hold=True, sale_lock=False, quality_hold=False, decision="SELLABLE",
    )
    read = map_risk_flags(resp)
    assert read.complete is True
    assert read.risk_flags == {"recall": True, "sale_lock": False, "quality_hold": False}

    ctx = make_scale_context(risk_flags=read.risk_flags)          # feed ONLY the mapped ops-core locks
    assert _risk_status(ctx) is DataQualityStatus.FAIL            # Risk FAIL despite decision=SELLABLE (RULE-017)

    req = scale_gate.propose("scr_smk030_i", {"campaign_id": "c1"}, ctx,
                             budget_cap=1_000_000.0, rollback_condition="revert to pilot baseline")
    assert req.overall_status is DataQualityStatus.FAIL
    with pytest.raises(ScaleGateViolation):                       # approve refused: active recall lock at approval
        scale_gate.record_owner_decision("scr_smk030_i", make_owner_decision("APPROVE"),
                                         current_risk_flags=read.risk_flags)
    assert scale_store.get("scr_smk030_i").approval_state.value == "PROPOSED"
    assert scale_store.get("scr_smk030_i").is_scale_authorized is False


# ---- Scenario (ii): recall_case_open=true (additive) -> recall True; gate FAIL EVEN when SELLABLE ---------------
def test_smk_030_scenario_ii_recall_case_open_additive_and_gate_fails(
    make_scale_context, scale_gate, scale_store, make_owner_decision
):
    """SMK-030(ii). recall_case_open=true with recall_hold=false still maps to risk_flags['recall']=True
    (recall = recall_hold OR recall_case_open — additive); the other flags are unaffected. The mapped lock fails
    the Scale-Gate Risk row despite decision=SELLABLE and the approve is refused. Also proves the additive default:
    recall_case_open ABSENT is treated false, so recall then follows recall_hold only."""
    resp = OpsCoreAvailabilityResponse(
        recall_hold=False, sale_lock=False, quality_hold=False, recall_case_open=True, decision="SELLABLE",
    )
    read = map_risk_flags(resp)
    assert read.risk_flags["recall"] is True                     # additive OR: recall_case_open alone -> recall
    assert read.risk_flags["sale_lock"] is False and read.risk_flags["quality_hold"] is False

    ctx = make_scale_context(risk_flags=read.risk_flags)
    assert _risk_status(ctx) is DataQualityStatus.FAIL           # FAIL despite SELLABLE (clean-lot recall case)
    scale_gate.propose("scr_smk030_ii", {"campaign_id": "c1"}, ctx,
                       budget_cap=1_000_000.0, rollback_condition="revert")
    with pytest.raises(ScaleGateViolation):
        scale_gate.record_owner_decision("scr_smk030_ii", make_owner_decision("APPROVE"),
                                         current_risk_flags=read.risk_flags)
    assert scale_store.get("scr_smk030_ii").approval_state.value == "PROPOSED"

    # additive default (absent -> false): recall follows recall_hold only, other flags unaffected
    absent = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=False, sale_lock=False, quality_hold=False))
    assert absent.risk_flags["recall"] is False


# ---- Scenario (iii): pull error/timeout/429 (or None/malformed) -> incomplete/unknown -> gate does not clear ----
@pytest.mark.parametrize("read", [
    map_pull_outcome(error="TIMEOUT"),                            # (iii) timeout
    map_pull_outcome(error="HTTP_429"),                           # (iii) 429
    map_pull_outcome(error="CONNECTION_ERROR"),                   # (iii) pull error
    map_pull_outcome(response=None),                              # absent response
    map_pull_outcome({"recall_hold": True}),                      # malformed (missing sale_lock/quality_hold)
])
def test_smk_030_scenario_iii_pull_error_incomplete_gate_does_not_clear(
    read, make_scale_context, scale_gate, scale_store, make_owner_decision
):
    """SMK-030(iii). A pull error / timeout / 429 (or a None / malformed response) is an INCOMPLETE risk read: the
    ops-core locks are left unobserved (empty risk_flags) — never a False false-clear, never a fabricated True.
    Fed to the existing Scale Gate the Risk row is fail-closed HOLD (not PASS, RULE-017), and an owner APPROVE is
    refused because the risk state was not fully re-checked — the gate does not clear."""
    assert read.complete is False and read.risk_flags == {}      # unknown -> empty (fail-closed), no false-clear
    ctx = make_scale_context(risk_flags=read.risk_flags)
    assert _risk_status(ctx) is DataQualityStatus.HOLD           # unobserved -> HOLD, never PASS

    scale_gate.propose("scr_smk030_iii", {"campaign_id": "c1"}, ctx,
                       budget_cap=1_000_000.0, rollback_condition="revert")
    with pytest.raises(ScaleGateViolation):                      # incomplete read -> approve refused (does not clear)
        scale_gate.record_owner_decision("scr_smk030_iii", make_owner_decision("APPROVE"),
                                         current_risk_flags=read.risk_flags)
    assert scale_store.get("scr_smk030_iii").approval_state.value == "PROPOSED"


# ---- Expected clause: "the mapper never reads decision/block_reasons" ------------------------------------------
def test_smk_030_neg_mapper_never_reads_decision_or_block_reasons(make_scale_context):
    """The mapper reads presence booleans only. decision=SELLABLE with block_reasons present does NOT clear a
    present recall_hold (recall stays True); and a clean lot (no presence flag) with decision/block_reasons present
    does NOT fabricate a lock (recall stays False). So block_reasons / decision never move the mapped risk_flags —
    only the presence booleans do."""
    locked = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=True, sale_lock=False, quality_hold=False,
        decision="SELLABLE", block_reasons=("clean_lot", "stale_reason"),
    ))
    assert locked.risk_flags["recall"] is True                   # decision=SELLABLE cannot clear a present lock

    clean = map_risk_flags(OpsCoreAvailabilityResponse(
        recall_hold=False, sale_lock=False, quality_hold=False,
        decision="RECALL", block_reasons=("some_reason",),        # a scary decision string is still never read
    ))
    assert clean.risk_flags == {"recall": False, "sale_lock": False, "quality_hold": False}
    assert set(clean.risk_flags.keys()) == set(RECALL_RISK_KEYS)  # no other lock fabricated from block_reasons
    assert _risk_status(make_scale_context(risk_flags=clean.risk_flags)) is DataQualityStatus.PASS  # non-vacuous


# ---- Fail-closed non-vacuity: a missing / non-bool presence flag never coerces to a clear ----------------------
def test_smk_030_neg_malformed_or_nonbool_presence_flag_is_failclosed(make_scale_context):
    """Reinforces the fail-closed direction: a missing presence key (dict path) or a non-bool value (the value-object
    path — the S1b seam's first-class construction) is an INCOMPLETE read (empty), never bool()-coerced to a truthy
    clear or lock. The empty read is fail-closed HOLD at the gate."""
    # dict path: a non-bool "true" string is malformed -> incomplete empty (not coerced to a clear)
    coerced = map_pull_outcome({"recall_hold": "true", "sale_lock": False, "quality_hold": False})
    assert coerced.complete is False and coerced.risk_flags == {}
    # value-object path: None / int / string presence flags all fail closed through the single strict-bool choke
    for bad in (None, 0, 1, "false", "true", (), []):
        r = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=bad, sale_lock=False, quality_hold=False))
        assert r.complete is False and r.risk_flags == {}, f"non-bool recall_hold={bad!r} must fail closed"
    assert _risk_status(make_scale_context(risk_flags={})) is DataQualityStatus.HOLD  # empty -> HOLD (not PASS)


# ---- Non-vacuous control: a clean COMPLETE read maps (recall False), so the empties above are error-caused ------
def test_smk_030_control_clean_complete_read_maps_non_empty(make_scale_context):
    """Control (non-vacuous): a clean, well-formed response (all presence booleans real, no lock) is a COMPLETE
    read whose risk_flags is the non-empty {recall:False, sale_lock:False, quality_hold:False} — proving the empty
    reads in the fail-closed cases are caused by the pull error / non-bool, not a mapper that always yields empty.
    The mapper's 3-of-6 output is a strict subset of RISK_LOCKS (a partial contribution), so recall_risk_contribution
    collapses this bare clean map to {} rather than a standalone clearing map (fail-closed by construction)."""
    clean = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=False, sale_lock=False, quality_hold=False))
    assert clean.complete is True
    assert clean.risk_flags == {"recall": False, "sale_lock": False, "quality_hold": False}
    assert set(RECALL_RISK_KEYS) < set(RISK_LOCKS)               # strict subset: 3 of 6 locks
    bare = recall_risk_contribution(clean, base_flags=None)
    assert bare == {} and risk_picture_complete(bare) is False   # partial + no active -> fail-closed, never clears


# ---- Expected clause: "no PII, external_send OFF" (+ posture immutable, no egress / live client) ---------------
def test_smk_030_no_pii_external_send_off_and_posture_unchanged():
    """The governance posture is immutable and nothing in this slice flips it or opens egress. The mapper module
    imports no HTTP client / transport (the S1b live client is not built), a campaign/SKU ref is provenance-only and
    never enters risk_flags, and the response carries no raw PII."""
    assert config.EXTERNAL_SEND == "OFF"
    assert config.PRODUCTION_FLAG == "OFF"
    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED"

    # the mapper is pure/read-only over a value object — no live HTTP / transport surface (S1b seam not built here)
    import inspect

    import app.measurement.scale.recall_risk_mapper as mod
    module_src = inspect.getsource(mod)
    for forbidden in ("import requests", "import httpx", "urllib.request", "http.client", "socket."):
        assert forbidden not in module_src, f"mapper must not open a network surface: {forbidden}"

    # sku_ref / decision / block_reasons are provenance only — never read into the mapped risk_flags
    resp = OpsCoreAvailabilityResponse(
        recall_hold=True, sale_lock=False, quality_hold=False, sku_ref="SKU_HERO_1", decision="SELLABLE",
    )
    read = map_risk_flags(resp)
    assert set(read.risk_flags.keys()) == set(RECALL_RISK_KEYS)  # only the three ops-core locks; no ref leaks in
