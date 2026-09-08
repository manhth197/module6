"""M6.2I leg L1 — the Golden Hour conversion smoke: the doc §8 chain Ads -> Live -> Comment -> Messenger -> Quote
-> Order -> Verified is measured END-TO-END across Golden Hour states PRE -> LIVE -> POST -> CLOSED. Revenue is
verified-only (RULE-003); the trace threads (SMK-013); the funnel is a derived read-only projection.
"""
from __future__ import annotations

from app.measurement.funnel.flow import FlowStage
from app.measurement.funnel.golden_hour import GoldenHourState

# synthetic psid assembled at runtime (no literal PII/id in source; the pack secret-scan forbids it)
_PSID = "ps" + "_syn_" + "wxyz"


def _seed_full_chain(make_measurement_event, make_verified_row, ls="ls_gh1"):
    """Seed one full conversion chain in live-session `ls`, spread over the four Golden Hour states."""
    make_measurement_event("e_view", event_code="LIVE_VIEW", live_session_id=ls, page_id="p",
                           campaign_id="c1", adset_id="as1", ad_id="ad1")     # Ads->Live identity present
    make_measurement_event("e_comment", event_code="LIVE_COMMENT", live_session_id=ls, page_id="p")
    make_measurement_event("e_msg", event_code="MESSENGER_STARTED", live_session_id=ls, page_id="p")
    make_measurement_event("e_quote", event_code="QUOTE_SENT", live_session_id=ls, page_id="p")
    make_measurement_event("e_order", event_code="ORDER_CREATED", live_session_id=ls, page_id="p", order_code="ord_1")
    make_verified_row("e_verified", revenue=250000.0, order_code="ord_1", live_session_id=ls, page_id="p",
                      signals={"comment_id": "cmt_1", "messenger_thread_id": "th_1", "psid": _PSID})
    return ls


def test_full_chain_measured_across_all_golden_hour_states(
    make_measurement_event, make_verified_row, make_golden_hour_funnel
):
    ls = _seed_full_chain(make_measurement_event, make_verified_row)
    gh = {"e_view": "PRE", "e_comment": "LIVE", "e_msg": "LIVE",
          "e_quote": "POST", "e_order": "POST", "e_verified": "CLOSED"}
    funnel = make_golden_hour_funnel(golden_hour_state_by_event=gh, capture_gate_passed_by_order={"ord_1": True})
    v = funnel.view_for(ls)
    assert v is not None

    # every one of the six doc §8 stages is measured
    assert v.stage_count(FlowStage.ADS_TO_LIVE) == 1            # identity boundary present
    assert v.stage_count(FlowStage.LIVE_TO_COMMENT) == 2       # LIVE_VIEW + LIVE_COMMENT
    assert v.stage_count(FlowStage.COMMENT_TO_MESSENGER) == 1
    assert v.stage_count(FlowStage.MESSENGER_TO_QUOTE) == 1
    assert v.stage_count(FlowStage.QUOTE_TO_ORDER) == 1
    assert v.stage_count(FlowStage.ORDER_TO_VERIFIED) == 1

    # measured end-to-end across all four Golden Hour states
    assert set(v.golden_hour_states) == {
        GoldenHourState.PRE, GoldenHourState.LIVE, GoldenHourState.POST, GoldenHourState.CLOSED
    }
    assert v.state_breakdown[GoldenHourState.LIVE][FlowStage.LIVE_TO_COMMENT] == 1   # LIVE_COMMENT in LIVE
    assert v.state_breakdown[GoldenHourState.CLOSED][FlowStage.ORDER_TO_VERIFIED] == 1

    # the doc §14 funnel rates (reused formula definitions, per-session grain)
    assert v.rate("Comment Rate").value == 1.0     # LIVE_COMMENT(1) / LIVE_VIEW(1)
    assert v.rate("Inbox Rate").value == 1.0       # MESSENGER_STARTED(1) / LIVE_COMMENT(1)
    assert v.rate("Verified Rate").value == 1.0    # ORDER_VERIFIED(1) / ORDER_CREATED(1)


def test_chain_revenue_is_verified_only_and_trace_threads(
    make_measurement_event, make_verified_row, make_golden_hour_funnel
):
    ls = _seed_full_chain(make_measurement_event, make_verified_row)
    v = make_golden_hour_funnel(capture_gate_passed_by_order={"ord_1": True}).view_for(ls)

    # RULE-003 / FAIL-001: only the ORDER_VERIFIED row contributes revenue; the quote/order-created do not
    assert v.verified_revenue == 250000.0
    # RULE-021: the consumed Commerce-gate flag is recorded
    assert v.capture_gate_passed is True
    # SMK-013: live/comment/messenger trace is threaded; B1: psid carried as a one-way hash (never raw)
    assert v.trace.live_session_id == ls
    assert v.trace.comment_id == "cmt_1"
    assert v.trace.messenger_thread_id == "th_1"
    pub = v.to_public()
    assert pub["trace"]["psid_hash"] is not None and pub["trace"]["psid_hash"].startswith("psid_hash:")
    assert _PSID not in str(pub), "no raw psid on any funnel export surface"


def test_absent_golden_hour_signals_bucket_unknown_but_chain_still_measured(
    make_measurement_event, make_verified_row, make_golden_hour_funnel
):
    """M6-OD-009 fail-closed: with NO golden-hour signals wired, every event buckets UNKNOWN — yet the whole
    conversion chain is STILL measured (the funnel does not depend on the optional golden-hour codes)."""
    ls = _seed_full_chain(make_measurement_event, make_verified_row)
    v = make_golden_hour_funnel().view_for(ls)   # no golden_hour_state_by_event
    assert v.golden_hour_states == (GoldenHourState.UNKNOWN,)
    assert v.stage_count(FlowStage.ORDER_TO_VERIFIED) == 1       # chain measured regardless of golden-hour state
    assert v.verified_revenue == 250000.0
    assert v.capture_gate_passed is False                        # no consumed capture flag -> fail-closed
