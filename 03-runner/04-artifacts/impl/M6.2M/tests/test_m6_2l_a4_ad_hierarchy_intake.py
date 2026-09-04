"""M6.2L leg 2 / M6-SMK-020 / RULE-014: POST /api/ads/events/track + normalize persist the 4 M6-owned ad-hierarchy
ids (campaign/adset/ad/live_session); a COMPLETE-ad FACEBOOK_AD event carrying them reaches HIGH source confidence
via the REAL API path. Untrusted (RULE-H03): a present-but-non-string id is a fail-closed SCHEMA_INVALID reject.
Narrow-rule control: an INCOMPLETE ad path + a live_session stays a genuine MULTI_TOUCH ambiguity (SMK-007).
"""
from __future__ import annotations

from app.api.track import handle_track_request
from app.measurement.models.attribution_context import (
    ConflictStatus,
    EntryChannel,
    SourceConfidence,
)


def test_track_persists_four_ad_ids_and_resolver_reaches_high(
    track_deps, make_track_body, measurement_store, make_conversion, attribution_resolver
):
    body = make_track_body(
        event_code="VIEW_LANDING", guest_id="guest_mapped_ok",
        campaign_id="camp_1", adset_id="ads_1", ad_id="ad_1", live_session_id="ls_1",
    )
    res = handle_track_request(body, track_deps)
    assert res.status == "ACCEPTED"

    # intake + normalize persisted all 4 ad-hierarchy ids onto the Zone-A row (the real API path)
    row = measurement_store.get_by_event_id(res.event_id)
    assert (row.campaign_id, row.adset_id, row.ad_id, row.live_session_id) == ("camp_1", "ads_1", "ad_1", "ls_1")

    # a COMPLETE FACEBOOK_AD path carrying a live_session grades single-channel HIGH/NONE (live = downstream trace)
    ctx = attribution_resolver.resolve(row, make_conversion("VIEW_LANDING", source_event_id=res.event_id))
    assert ctx.entry_channel is EntryChannel.FACEBOOK_AD
    assert ctx.source_confidence is SourceConfidence.HIGH
    assert ctx.conflict_status is ConflictStatus.NONE
    assert ctx.live_session_id == "ls_1"                 # still traced, just not a competing entry channel


def test_track_rejects_non_string_ad_id_fail_closed(track_deps, make_track_body):
    body = make_track_body(event_code="VIEW_LANDING", campaign_id=123)     # non-string untrusted value
    res = handle_track_request(body, track_deps)
    assert res.status == "REJECTED"
    assert res.error_code == "SCHEMA_INVALID" and res.field == "campaign_id"


def test_incomplete_ad_path_plus_live_stays_multi_touch(
    track_deps, make_track_body, measurement_store, make_conversion, attribution_resolver
):
    # campaign only (incomplete ad path) + a live_session -> the narrow rule does NOT dominate -> MULTI_TOUCH/LOW
    body = make_track_body(
        event_code="VIEW_LANDING", guest_id="guest_mapped_ok",
        campaign_id="camp_only", live_session_id="ls_x",
    )
    res = handle_track_request(body, track_deps)
    assert res.status == "ACCEPTED"
    row = measurement_store.get_by_event_id(res.event_id)
    ctx = attribution_resolver.resolve(row, make_conversion("VIEW_LANDING", source_event_id=res.event_id))
    assert ctx.conflict_status is ConflictStatus.MULTI_TOUCH
    assert ctx.source_confidence is SourceConfidence.LOW
