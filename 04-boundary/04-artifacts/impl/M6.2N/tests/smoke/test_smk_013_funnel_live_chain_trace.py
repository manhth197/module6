"""Official smoke — slice M6.2I — M6-SMK-013 (doc ADS-P0-013), Golden Hour funnel leg.

Authored by TESTER in M6-P1803 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1804. This is the
M6.2I Phase-2 conversion-machine leg of SMK-013 (the smoke binds M6.2E + M6.2I): the M6.2E carried smoke
(test_smk_013_live_chain_trace.py) proves the ATTRIBUTION resolver threads the chain; this file proves the Golden
Hour FUNNEL surfaces live_session_id + comment_id + messenger_thread_id from the materialized
ads_attribution_context, with psid masked on export. Governance is immutable: global_gateway_state=BLOCKED,
production_flag=OFF, external_send=OFF — nothing below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 413):

    Kịch bản (verbatim):          "Live/Comment/Messenger chain"
    Kết quả phải đạt (verbatim):  "Trace được live_session_id, comment_id, messenger_thread_id"

psid is PII and is masked on every export (RULE-014 / H02); the marker is assembled at runtime so no literal id
sits in this source. Reuses the shared conftest fixtures (make_verified_row, make_measurement_event,
make_golden_hour_funnel). All ids synthetic; no PII.
"""
from __future__ import annotations

_PSID = "ps" + "_syn_" + "wxyz"    # synthetic psid marker, assembled at runtime (no literal PII in source)


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_013_funnel_threads_live_comment_messenger_trace(make_verified_row, make_golden_hour_funnel):
    """M6-SMK-013 "Live/Comment/Messenger chain" -> "Trace được live_session_id, comment_id, messenger_thread_id"
    — the Golden Hour funnel threads all three ids from the materialized attribution_context."""
    make_verified_row(
        "e_live", revenue=180000.0, order_code="ord_live", live_session_id="ls_1", page_id="p_live",
        signals={"comment_id": "cmt_1", "messenger_thread_id": "th_1", "psid": _PSID},
    )
    v = make_golden_hour_funnel().view_for("ls_1")
    assert v.trace.live_session_id == "ls_1"
    assert v.trace.comment_id == "cmt_1"
    assert v.trace.messenger_thread_id == "th_1"


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_013_neg_psid_masked_on_export(make_verified_row, make_golden_hour_funnel):
    """B1 (M5 PSID policy) UPDATED CONTRACT: the funnel trace carries only a ONE-WAY salted hash (`psid_hash`), never
    a raw psid — the raw value reaches no funnel export surface. (SMK-013 psid companion realigned by the
    operator-directed B1 patch; the live-chain-trace assertions are unchanged — the TESTER should re-bless.)"""
    make_verified_row(
        "e_live2", revenue=90000.0, order_code="ord_live2", live_session_id="ls_2", page_id="p",
        signals={"comment_id": "cmt_2", "messenger_thread_id": "th_2", "psid": _PSID},
    )
    pub = make_golden_hour_funnel().view_for("ls_2").to_public()
    assert pub["trace"]["psid_hash"] is not None and pub["trace"]["psid_hash"].startswith("psid_hash:")
    assert _PSID not in str(pub), "raw psid must never reach a funnel export surface"


def test_smk_013_neg_partial_chain_traces_what_is_present(make_verified_row, make_golden_hour_funnel):
    """A partial chain (a comment but no messenger thread) still traces what IS present — comment_id is threaded,
    messenger_thread_id stays None (never fabricated)."""
    make_verified_row(
        "e_live3", revenue=50000.0, order_code="ord_live3", live_session_id="ls_p", page_id="p",
        signals={"comment_id": "cmt_only"},
    )
    v = make_golden_hour_funnel().view_for("ls_p")
    assert v.trace.live_session_id == "ls_p"
    assert v.trace.comment_id == "cmt_only"
    assert v.trace.messenger_thread_id is None


def test_smk_013_control_no_live_chain_traces_none(make_measurement_event, make_golden_hour_funnel):
    """Control (non-vacuity): a session with no live/comment/messenger source (a plain event, no attribution
    signals) traces none of the comment/messenger ids — proving the ids come from the chain, not a default; the
    session key itself is still traced."""
    make_measurement_event("e_plain", event_code="LIVE_COMMENT", live_session_id="ls_3", page_id="p")
    v = make_golden_hour_funnel().view_for("ls_3")
    assert v.trace.comment_id is None and v.trace.messenger_thread_id is None
    assert v.trace.live_session_id == "ls_3"   # the session key itself is still traced
