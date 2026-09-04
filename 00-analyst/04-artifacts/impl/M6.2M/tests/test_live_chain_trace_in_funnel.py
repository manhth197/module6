"""M6.2I leg L3 / M6-SMK-013: "Live/Comment/Messenger chain" -> "Trace được live_session_id, comment_id,
messenger_thread_id". The funnel threads the three ids from the ads_attribution_context (M6.2E resolver); psid is
PII and masked on every export (RULE-014 / H02).
"""
from __future__ import annotations

_PSID = "ps" + "_syn_" + "abcd"


def test_funnel_threads_live_comment_messenger_trace(make_verified_row, make_golden_hour_funnel):
    make_verified_row(
        "e_live", revenue=180000.0, order_code="ord_live", live_session_id="ls_1", page_id="p_live",
        signals={"comment_id": "cmt_1", "messenger_thread_id": "th_1", "psid": _PSID},
    )
    v = make_golden_hour_funnel().view_for("ls_1")
    assert v.trace.live_session_id == "ls_1"
    assert v.trace.comment_id == "cmt_1"
    assert v.trace.messenger_thread_id == "th_1"


def test_funnel_masks_psid_on_export(make_verified_row, make_golden_hour_funnel):
    make_verified_row(
        "e_live2", revenue=90000.0, order_code="ord_live2", live_session_id="ls_2", page_id="p",
        signals={"comment_id": "cmt_2", "messenger_thread_id": "th_2", "psid": _PSID},
    )
    v = make_golden_hour_funnel().view_for("ls_2")
    pub = v.to_public()
    assert pub["trace"]["psid"] != _PSID and pub["trace"]["psid"] is not None   # masked, not dropped
    assert _PSID not in str(pub), "raw psid must never reach a funnel export surface"


def test_funnel_trace_empty_when_no_live_chain(make_measurement_event, make_golden_hour_funnel):
    """Control (non-vacuity): a session with no live/comment/messenger source traces none of the three ids."""
    make_measurement_event("e_plain", event_code="LIVE_COMMENT", live_session_id="ls_3", page_id="p")
    v = make_golden_hour_funnel().view_for("ls_3")
    assert v.trace.comment_id is None and v.trace.messenger_thread_id is None
    assert v.trace.live_session_id == "ls_3"   # the session key itself is still traced
