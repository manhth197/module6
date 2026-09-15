"""Official smoke — slice M6.2T — M6-SMK-032 (pre-wiring hardening; M6-OD-019; M6.2R P2609 + M6.2S P2709 findings).

Authored by TESTER in M6-P2803 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P2804
(TESTER_RUN -> 04-artifacts/test-reports/M6.2T/SMOKE_RESULTS.md). Governance is immutable here and nothing below
flips a flag, opens egress, or wires the mapper/reader: global_gateway_state=BLOCKED, production_flag=OFF,
external_send=OFF. All four legs are stricter/fail-closed-direction ONLY (leg 1 can only HOLD more, never clear
more; it opens no PASS branch). The mapper + reader stay UNWIRED (wiring is the S1b / server-bind seam, out of scope).

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (row M6-SMK-032):

    Scenario (verbatim):
        Pre-wiring hardening (M6.2T): (i) a propose with a partial no-active risk map (only the 3 ops-core locks) +
        a falsy-non-bool lock value at approval; (ii) a monkeypatched PASS branch on _funnel/_dashboard; (iii) a feed
        row with an email/phone-shaped governance field; (iv) base_flags carrying a RECALL_RISK_KEY + a non-iterable
        block_reasons

    Expected (verbatim):
        (i) conditions._risk → HOLD not PASS (all-6 required); approval does NOT clear on a falsy-non-bool lock
        (bool-ness validated); (ii) the HOLD-floor regression FAILs loudly (structural unreachability pinned); (iii)
        reader rejects fail-closed (feed_error, input-side PII-shape); (iv) recall_risk_contribution rejects the
        base-key overwrite + from_mapping fail-closed-loud on non-iterable; all stricter/fail-closed, no certified
        behavior loosened, no flag flip, no egress

Reuses the shared conftest scale fixtures (make_scale_context, scale_gate, scale_store, make_owner_decision) and the
CODER's M6.2T regression patterns. PII-shaped test values are assembled at runtime (no literal PII in source).
"""
from __future__ import annotations

import pytest

from app import config
from app.measurement.models.consumed import DataSensitivity, ExternalSendPolicy
from app.measurement.models.measurement_event import DataQualityStatus
from app.measurement.scale import conditions
from app.measurement.scale.conditions import (
    ConditionResult,
    RISK_LOCKS,
    ScaleCondition,
    evaluate_conditions,
)
from app.measurement.scale.recall_risk_mapper import (
    OpsCoreAvailabilityResponse,
    RecallRiskContributionError,
    map_pull_outcome,
    map_risk_flags,
    recall_risk_contribution,
)
from app.measurement.scale.scale_gate import ScaleGateViolation
from app.measurement.adapters.registry_feed_reader import RegistryFeedReader

# PII shapes assembled at runtime (no literal PII in source; mirrors the coder regression):
_EMAIL = "u" + chr(64) + "x" + "." + "yz"       # an email shape
_PHONE = "0" + "9" * 9                            # a VN-phone shape (0 + 9 digits)
_LONGID = "1" * 12                                # a long digit run (id/phone-like)


def _risk_status(ctx):
    results, _ = evaluate_conditions(ctx)
    return next(r for r in results if r.condition is ScaleCondition.RISK).status


# ---- LEG (i): conditions._risk requires all-6 to PASS; a partial no-active map -> HOLD, not PASS ---------------
def test_smk_032_leg_i_partial_no_active_risk_map_holds_not_pass(make_scale_context):
    """SMK-032(i)-a. A partial no-active risk map (only the 3 ops-core locks observed) → Risk HOLD, not PASS (all 6
    RISK_LOCKS required to clear — an unobserved lock could be active). Non-vacuous: a COMPLETE all-6 no-active map
    still reaches PASS (the gate CAN clear the Risk row with a complete read); {} → HOLD and an active lock → FAIL
    are unchanged (certified M6.2G behavior preserved)."""
    partial = make_scale_context(risk_flags={"recall": False, "sale_lock": False, "quality_hold": False})
    assert _risk_status(partial) is DataQualityStatus.HOLD                       # partial no-active -> HOLD (M6.2T)
    full = make_scale_context(risk_flags={lock: False for lock in RISK_LOCKS})
    assert _risk_status(full) is DataQualityStatus.PASS                          # complete no-active -> PASS (non-vacuous)
    assert _risk_status(make_scale_context(risk_flags={})) is DataQualityStatus.HOLD                     # unchanged
    assert _risk_status(make_scale_context(risk_flags={l: (l == "recall") for l in RISK_LOCKS})) is DataQualityStatus.FAIL


@pytest.mark.parametrize("bad", [0, "", None])
def test_smk_032_leg_i_falsy_non_bool_lock_does_not_clear_at_approval(
    bad, make_scale_context, scale_gate, scale_store, make_owner_decision
):
    """SMK-032(i)-b. A falsy non-bool lock value (0 / '' / None-as-value) at approval does NOT clear via the
    fresh-read path (bool-ness validated) — it falls back to the proposal's Risk (HOLD, proposed with {}), so the
    APPROVE is refused (ScaleGateViolation) and the request stays PROPOSED."""
    rid = f"scr_smk032_bad_{bad!r}"
    scale_gate.propose(rid, {"campaign_id": "c1"}, make_scale_context(risk_flags={}),
                       budget_cap=1.0, rollback_condition="r")
    flags = {lock: False for lock in RISK_LOCKS}
    flags["recall"] = bad                                                        # all 6 keys present; one falsy non-bool
    with pytest.raises(ScaleGateViolation):
        scale_gate.record_owner_decision(rid, make_owner_decision("APPROVE"), current_risk_flags=flags)
    assert scale_store.get(rid).approval_state.value == "PROPOSED"


def test_smk_032_leg_i_control_all_six_real_bool_fresh_read_clears(
    make_scale_context, scale_gate, scale_store, make_owner_decision
):
    """Non-vacuous control (certified behavior UNCHANGED): a COMPLETE all-6 REAL-bool no-active fresh read still
    clears the RULE-017 approval re-check — so the refusals above are caused by the partial/bool-ness fail-closed
    path, not a gate that can never clear."""
    scale_gate.propose("scr_smk032_ok", {"campaign_id": "c1"}, make_scale_context(risk_flags={}),
                       budget_cap=1.0, rollback_condition="r")
    res = scale_gate.record_owner_decision("scr_smk032_ok", make_owner_decision("APPROVE"),
                                           current_risk_flags={lock: False for lock in RISK_LOCKS})
    assert res.approval_state.value == "APPROVED"


# ---- LEG (ii): HOLD-floor lock — is_scale_authorized structurally unreachable; a PASS branch would fail it loudly
def test_smk_032_leg_ii_hold_floor_regression_pins_unreachability(
    monkeypatch, make_scale_context, scale_gate, scale_store, make_owner_decision
):
    """SMK-032(ii). The HOLD-floor regression pins is_scale_authorized structurally unreachable: even with BOTH
    config floors (DASHBOARD_ALERT_THRESHOLDS_DEFINED, SCALE_MODEL_RATIFIED) monkeypatched True + a best context + a
    recorded owner APPROVE, `_funnel`/`_dashboard` have no PASS branch, so overall stays HOLD and no scale is
    authorized. Then simulating a PASS branch on `_funnel`/`_dashboard` (monkeypatching the functions) lifts the ONLY
    remaining floor — overall reaches PASS — which is exactly what the regression pins: a real PASS-branch would
    flip is_scale_authorized and make the regression's `assert ... is False` FAIL loudly."""
    monkeypatch.setattr(config, "DASHBOARD_ALERT_THRESHOLDS_DEFINED", True)
    monkeypatch.setattr(config, "SCALE_MODEL_RATIFIED", True)
    best = dict(quote_order_ok=True, public_privacy_ok=True, boxes_per_order=3.0,
                dq_overall=DataQualityStatus.PASS, risk_flags={lock: False for lock in RISK_LOCKS})

    # (a) real code: both config floors True + best context + owner APPROVE -> still NOT authorized (overall HOLD)
    ctx = make_scale_context(**best)
    req = scale_gate.propose("scr_smk032_floor", {"campaign_id": "c1"}, ctx,
                             budget_cap=1_000_000.0, rollback_condition="revert")
    assert req.overall_status is DataQualityStatus.HOLD                          # _funnel/_dashboard have no PASS branch
    res = scale_gate.record_owner_decision("scr_smk032_floor", make_owner_decision("APPROVE"),
                                           current_risk_flags=ctx.risk_flags)
    assert res.approval_state.value == "APPROVED"
    assert res.is_scale_authorized is False                                      # HOLD floor holds (FAIL-006)
    assert scale_store.get("scr_smk032_floor").is_scale_authorized is False

    # (b) simulate the guarded PASS-branch refactor -> the HOLD floor lifts -> the regression would FAIL loudly
    monkeypatch.setattr(conditions, "_funnel",
                        lambda c: ConditionResult(ScaleCondition.FUNNEL, DataQualityStatus.PASS, "patched-pass-branch"))
    monkeypatch.setattr(conditions, "_dashboard",
                        lambda c: ConditionResult(ScaleCondition.DASHBOARD, DataQualityStatus.PASS, "patched-pass-branch"))
    approved_ctx = make_scale_context(owner_approved=True, budget_cap=1.0, rollback_condition="r", **best)
    _, overall = evaluate_conditions(approved_ctx)
    assert overall is DataQualityStatus.PASS      # _funnel/_dashboard were the sole HOLD floor -> unreachability pinned


# ---- LEG (iii): reader rejects a PII-shaped governance field fail-closed (input-side, state unchanged) --------
@pytest.mark.parametrize("field,val", [
    ("event_code", _EMAIL), ("event_group", _PHONE), ("domain", _LONGID),
])
def test_smk_032_leg_iii_pii_shape_in_governance_field_rejected(field, val):
    """SMK-032(iii). A feed row whose governance metadata (event_code / event_group / domain) carries a customer-PII
    shape (email / phone / long-digit) is rejected fail-closed at parse (feed_error:pii_shape_in_governance_field),
    leaving version + rows UNCHANGED — an input-side reject, never stored or exported (NOT export masking)."""
    r = RegistryFeedReader()
    r.apply({"registry_version": 1, "events": [{"event_code": "SEED"}]})         # seed version 1
    res = r.apply({"registry_version": 2, "events": [dict({"event_code": "E"}, **{field: val})]})
    assert res.applied is False and res.reason == "feed_error:pii_shape_in_governance_field"
    assert r.current_registry_version() == 1 and r.get("E") is None              # state unchanged


def test_smk_032_leg_iii_control_legit_governance_codes_do_not_trip():
    """Non-vacuous control: a legitimate governance code (ORDER_VERIFIED / ads.core / ads) does NOT trip the PII
    reject — so the rejects above are caused by the PII shape, not a reader that rejects everything."""
    r = RegistryFeedReader()
    ok = r.apply({"registry_version": 1, "events": [
        {"event_code": "ORDER_VERIFIED", "event_group": "ads.core", "domain": "ads", "data_sensitivity": "INTERNAL"},
    ]})
    assert ok.applied is True and r.get("ORDER_VERIFIED") is not None


# ---- LEG (iv): in-process residuals — base-key overwrite reject + non-iterable block_reasons fail-closed -------
def test_smk_032_leg_iv_recall_contribution_rejects_base_recall_key():
    """SMK-032(iv)-a. recall_risk_contribution rejects a base_flags carrying any mapper-owned RECALL_RISK_KEY
    (recall / sale_lock / quality_hold) — a silent overwrite would hide a lock, so it raises
    RecallRiskContributionError (fail-closed). A base carrying only the OTHER lock sources is accepted."""
    read = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=False, sale_lock=False, quality_hold=False))
    for key in ("recall", "sale_lock", "quality_hold"):
        with pytest.raises(RecallRiskContributionError):
            recall_risk_contribution(read, base_flags={key: False, "complaint_p0": False})
    out = recall_risk_contribution(read, base_flags={"complaint_p0": False, "platform_spam_flag": False,
                                                     "crm_suppression": False})
    # no clash -> accepted; the merged clean 6-lock picture is returned (all 6 keys present, none active)
    assert set(out.keys()) == set(RISK_LOCKS) and not any(out.values())


def test_smk_032_leg_iv_from_mapping_non_iterable_block_reasons_failclosed():
    """SMK-032(iv)-b. OpsCoreAvailabilityResponse.from_mapping is fail-closed-loud on a non-iterable / bare-string
    block_reasons (which would crash tuple(...) on untrusted input): it returns None (an INCOMPLETE read), and
    map_pull_outcome surfaces it as complete=False. A valid list/tuple / absent block_reasons still parses."""
    base = {"recall_hold": False, "sale_lock": False, "quality_hold": False}
    assert OpsCoreAvailabilityResponse.from_mapping(dict(base, block_reasons=5)) is None          # int -> None
    assert OpsCoreAvailabilityResponse.from_mapping(dict(base, block_reasons="oops")) is None      # bare str -> None
    assert map_pull_outcome(dict(base, block_reasons=5)).complete is False                         # surfaced incomplete
    ok = OpsCoreAvailabilityResponse.from_mapping(dict(base, block_reasons=["a", "b"]))
    assert ok is not None and ok.block_reasons == ("a", "b")                                       # valid list parses
    assert OpsCoreAvailabilityResponse.from_mapping(base) is not None                              # absent -> ()


def test_smk_032_leg_iv_non_str_enum_sibling_failclosed_and_observable():
    """SMK-032(iv) residual (N5/N6): a non-str enum sibling (data_sensitivity / external_send_policy) resolves to its
    fail-closed default (PII / BLOCKED_DEFAULT) and is counted in malformed_fields (observability); a well-formed
    feed carries no malformed sibling."""
    r = RegistryFeedReader()
    res = r.apply({"registry_version": 1, "events": [
        {"event_code": "E", "data_sensitivity": 123, "external_send_policy": {"x": 1}},   # both non-str
    ]})
    assert res.applied is True and res.malformed_fields == 2                     # N6 observable
    row = r.get("E")
    assert row.data_sensitivity is DataSensitivity.PII                           # N5 non-str -> PII (fail-closed)
    assert row.external_send_policy is ExternalSendPolicy.BLOCKED_DEFAULT         # N5 non-str -> BLOCKED_DEFAULT
    r2 = RegistryFeedReader()
    ok = r2.apply({"registry_version": 1, "events": [
        {"event_code": "E", "data_sensitivity": "INTERNAL", "external_send_policy": "INTERNAL_ONLY"},
    ]})
    assert ok.malformed_fields == 0 and ok.reason == "applied"                   # well-formed -> no malformed sibling


# ---- posture: stricter/fail-closed only, no flag flip, no egress ---------------------------------------------
def test_smk_032_posture_immutable_no_flag_flip_no_egress():
    """The governance posture is immutable and nothing in this slice flips it or opens egress (the tail of the
    expected clause: 'no flag flip, no egress')."""
    assert config.EXTERNAL_SEND == "OFF"
    assert config.PRODUCTION_FLAG == "OFF"
    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED"
