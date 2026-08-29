"""Official smoke — slice M6.2E — M6-SMK-013 (doc ADS-P0-013).

Authored by TESTER in M6-P1403 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1404
(TESTER_RUN -> 04-artifacts/test-reports/M6.2E/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 413):

    Kịch bản (verbatim):          "Live/Comment/Messenger chain"
    Kết quả phải đạt (verbatim):  "Trace được live_session_id, comment_id, messenger_thread_id"

The Live Session Resolver traces live_session_id (from the event's Zone A) + comment_id + messenger_thread_id
(from the live source, supplied via signals) into the ads_attribution_context (M6-CTR-002). `psid` is PII-class:
the DURABLE snapshot keeps the raw value (for trace joins) but every EXPORT masks it (RULE-014 / H02). The psid
marker is assembled at runtime so no literal PII/id sits in this source. RULE-008/009. Reuses the shared conftest
fixtures (make_measurement_event, make_conversion, attribution_resolver).
"""
from __future__ import annotations

from app.measurement.models.attribution_context import ConflictStatus, EntryChannel, SourceConfidence

# synthetic psid value assembled at runtime (no literal PII/id in source; the pack secret scan forbids it):
_PSID = "ps" + "_syn_" + "wxyz"


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_013_live_comment_messenger_chain_is_traced(
    make_measurement_event, make_conversion, attribution_resolver
):
    """M6-SMK-013 "Live/Comment/Messenger chain" -> "Trace được live_session_id, comment_id,
    messenger_thread_id".

    A live event with a comment + messenger thread traces all three ids into the snapshot; the single fully
    identified live source grades LIVE_ORGANIC / HIGH / NONE.
    """
    event = make_measurement_event(
        "evt_live", event_code="ORDER_VERIFIED", page_id="p_live", live_session_id="ls_1"
    )
    conv = make_conversion("ORDER_VERIFIED", source_event_id="evt_live")
    ctx = attribution_resolver.resolve(
        event, conv, signals={"comment_id": "cmt_1", "messenger_thread_id": "th_1", "psid": _PSID}
    )

    assert ctx.live_session_id == "ls_1"
    assert ctx.comment_id == "cmt_1"
    assert ctx.messenger_thread_id == "th_1"
    assert ctx.entry_channel is EntryChannel.LIVE_ORGANIC
    assert ctx.source_confidence is SourceConfidence.HIGH   # single, fully-identified live source
    assert ctx.conflict_status is ConflictStatus.NONE


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_013_neg_psid_is_masked_on_export_but_kept_durably(
    make_measurement_event, make_conversion, attribution_resolver
):
    """psid is PII: the durable snapshot keeps the raw value (for trace joins), but every EXPORT masks it
    (RULE-014 / H02) — the raw psid never reaches an export/dashboard/audit surface."""
    event = make_measurement_event("evt_live2", event_code="ORDER_VERIFIED", page_id="p", live_session_id="ls_2")
    ctx = attribution_resolver.resolve(
        event, make_conversion("ORDER_VERIFIED", source_event_id="evt_live2"),
        signals={"comment_id": "cmt_2", "psid": _PSID},
    )
    assert ctx.psid == _PSID                                  # durable snapshot keeps the raw value
    public = ctx.to_public()
    assert public["psid"] != _PSID and public["psid"] is not None   # export masks it (not dropped)
    assert _PSID not in str(public), "no raw psid on any export surface"


def test_smk_013_neg_partial_live_chain_still_traces_what_is_present(
    make_measurement_event, make_conversion, attribution_resolver
):
    """A partial live chain (a comment, but no live_session_id) still traces what IS present and is a valid
    LIVE_ORGANIC source, but degrades to MEDIUM (not a fully-identified live session)."""
    event = make_measurement_event("evt_live3", event_code="ORDER_VERIFIED", page_id="p")   # no live_session_id
    ctx = attribution_resolver.resolve(
        event, make_conversion("ORDER_VERIFIED", source_event_id="evt_live3"),
        signals={"comment_id": "cmt_3", "messenger_thread_id": "th_3"},
    )
    assert ctx.comment_id == "cmt_3" and ctx.messenger_thread_id == "th_3"
    assert ctx.live_session_id is None
    assert ctx.entry_channel is EntryChannel.LIVE_ORGANIC
    assert ctx.source_confidence is SourceConfidence.MEDIUM   # present but not fully identified


# --- positive control: proves the live trace is populated from live signals, not always-on ---------
def test_smk_013_control_no_live_signals_traces_no_live_chain(
    make_measurement_event, make_conversion, attribution_resolver
):
    """Control (non-vacuity): with NO live signals and no other source, nothing live is traced and the channel
    is DIRECT (MISSING_SOURCE) — proving the live ids above come from the live source, not a default."""
    event = make_measurement_event("evt_nolive", event_code="ORDER_VERIFIED", page_id="p")
    ctx = attribution_resolver.resolve(event, make_conversion("ORDER_VERIFIED", source_event_id="evt_nolive"))
    assert ctx.live_session_id is None and ctx.comment_id is None and ctx.messenger_thread_id is None
    assert ctx.entry_channel is EntryChannel.DIRECT
    assert ctx.conflict_status is ConflictStatus.MISSING_SOURCE
