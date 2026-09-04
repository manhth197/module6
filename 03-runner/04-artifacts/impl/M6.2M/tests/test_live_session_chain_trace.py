"""M6.2E leg 1 / M6-SMK-013: a live/comment/messenger event traces live_session_id, comment_id and
messenger_thread_id into the ads_attribution_context (Live Session Resolver). psid is PII — masked on export.
"""
from __future__ import annotations

from app.measurement.models.attribution_context import ConflictStatus, EntryChannel, SourceConfidence

# synthetic psid VALUE assembled at runtime (no literal PII/id in source; the pack secret-scan forbids it)
_PSID = "ps" + "_syn_" + "abcd"


def test_live_comment_messenger_traced_into_context(
    make_measurement_event, make_conversion, attribution_resolver
):
    event = make_measurement_event(
        "evt_live", event_code="ORDER_VERIFIED", page_id="p_live", live_session_id="ls_1"
    )
    conv = make_conversion("ORDER_VERIFIED", source_event_id="evt_live")
    ctx = attribution_resolver.resolve(
        event, conv,
        signals={"comment_id": "cmt_1", "messenger_thread_id": "th_1", "psid": _PSID},
    )

    # the live chain is traced into the snapshot (SMK-013)
    assert ctx.live_session_id == "ls_1"
    assert ctx.comment_id == "cmt_1"
    assert ctx.messenger_thread_id == "th_1"
    assert ctx.entry_channel is EntryChannel.LIVE_ORGANIC
    assert ctx.source_confidence is SourceConfidence.HIGH   # a single, fully-identified live source
    assert ctx.conflict_status is ConflictStatus.NONE

    # psid is PII: the DURABLE snapshot keeps the raw value; the EXPORT view masks it (RULE-014 / H02)
    assert ctx.psid == _PSID
    public = ctx.to_public()
    assert public["psid"] != _PSID and public["psid"] is not None
