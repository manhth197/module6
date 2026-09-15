"""Official smoke — slice M6.2L — M6-SMK-020 (proposed — HARDENING, owner review).

Authored by TESTER in M6-P2103 (mode=build, "do not yet run"); EXECUTED and its result recorded in M6-P2104
(TESTER_RUN -> 04-artifacts/test-reports/M6.2L/SMOKE_RESULTS.md). Closes audit item A4 (FIX_M6 2026-09-03).
Governance is immutable here: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below
flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (proposed additions row M6-SMK-020):

    Scenario (verbatim):   "POST /api/ads/events/track for a FACEBOOK_AD event carrying campaign/adset/ad/live_session"
    Expected (verbatim):   "intake + normalize persist the 4 ad-hierarchy ids; resolver reaches HIGH source confidence
                           via the real API path"

The 4 ad-hierarchy ids are M6-owned (M6's own ad link / UTM), read + validated at the real track intake and
persisted through normalize to Zone A. Untrusted (RULE-H03): a present-but-non-string id is a fail-closed
SCHEMA_INVALID reject. A COMPLETE FACEBOOK_AD path carrying a live_session grades single-channel FACEBOOK_AD/HIGH
(the live_session stays a downstream trace, not a competing entry channel); an INCOMPLETE ad path + a live_session
stays a genuine MULTI_TOUCH ambiguity (preserves carried SMK-007). Reuses the coder's A4 leg pattern + the shared
conftest fixtures (track_deps, make_track_body, measurement_store, make_conversion, attribution_resolver).
"""
from __future__ import annotations

from app.api.track import handle_track_request
from app.measurement.models.attribution_context import (
    ConflictStatus,
    EntryChannel,
    SourceConfidence,
)


# --- primary smoke: scenario verbatim, END-TO-END through the real API path -----------------------
def test_smk_020_track_persists_four_ad_ids_and_resolver_reaches_high(
    track_deps, make_track_body, measurement_store, make_conversion, attribution_resolver
):
    """M6-SMK-020 "POST /api/ads/events/track for a FACEBOOK_AD event carrying campaign/adset/ad/live_session" ->
    "intake + normalize persist the 4 ad-hierarchy ids; resolver reaches HIGH source confidence via the real API path".

    A track request carrying all 4 ad-hierarchy ids is ACCEPTED; intake + normalize persist them on the Zone-A row;
    the resolver, over that real-API-path row, reaches FACEBOOK_AD / HIGH / NONE with the live_session still traced.
    """
    body = make_track_body(
        event_code="VIEW_LANDING", guest_id="guest_mapped_ok",
        campaign_id="camp_1", adset_id="ads_1", ad_id="ad_1", live_session_id="ls_1",
    )
    res = handle_track_request(body, track_deps)
    assert res.status == "ACCEPTED"

    row = measurement_store.get_by_event_id(res.event_id)
    assert (row.campaign_id, row.adset_id, row.ad_id, row.live_session_id) == ("camp_1", "ads_1", "ad_1", "ls_1")

    ctx = attribution_resolver.resolve(row, make_conversion("VIEW_LANDING", source_event_id=res.event_id))
    assert ctx.entry_channel is EntryChannel.FACEBOOK_AD
    assert ctx.source_confidence is SourceConfidence.HIGH        # HIGH via the real API path
    assert ctx.conflict_status is ConflictStatus.NONE
    assert ctx.live_session_id == "ls_1"                         # still traced, not a competing entry channel


# --- negative / fail-closed: a present-but-non-string ad id is a SCHEMA_INVALID reject (RULE-H03) --
def test_smk_020_neg_non_string_ad_id_is_fail_closed_reject(track_deps, make_track_body):
    """Untrusted-input fail-closed (RULE-H03): a present-but-non-string ad-hierarchy id is REJECTED with
    SCHEMA_INVALID naming the offending field — never silently coerced or persisted."""
    res = handle_track_request(make_track_body(event_code="VIEW_LANDING", campaign_id=123), track_deps)
    assert res.status == "REJECTED"
    assert res.error_code == "SCHEMA_INVALID" and res.field == "campaign_id"


# --- negative / narrow-rule control: incomplete ad path + live stays MULTI_TOUCH (preserves SMK-007) --
def test_smk_020_neg_incomplete_ad_path_plus_live_stays_multi_touch(
    track_deps, make_track_body, measurement_store, make_conversion, attribution_resolver
):
    """The A4 narrow rule must NOT over-dominate: campaign-only (incomplete ad path) + a live_session is a genuine
    MULTI_TOUCH / LOW ambiguity — the FACEBOOK_AD/HIGH grade is reserved for a COMPLETE ad path."""
    body = make_track_body(
        event_code="VIEW_LANDING", guest_id="guest_mapped_ok", campaign_id="camp_only", live_session_id="ls_x",
    )
    res = handle_track_request(body, track_deps)
    assert res.status == "ACCEPTED"
    row = measurement_store.get_by_event_id(res.event_id)
    ctx = attribution_resolver.resolve(row, make_conversion("VIEW_LANDING", source_event_id=res.event_id))
    assert ctx.conflict_status is ConflictStatus.MULTI_TOUCH
    assert ctx.source_confidence is SourceConfidence.LOW
