"""M6.2Q leg 2 / M6-OD-011 / SMK-029 / RULE-015: primary_campaign_id first-class + live-session-ads-binding.v1.

primary_campaign_id is a first-class attribution field, present in to_public()/as_stored(), deterministic on
replay, and NOT wired into the grading (.complete/_grade) — so a complete FACEBOOK_AD path still grades HIGH
(SMK-020) and an incomplete-ad + live still grades MULTI_TOUCH (SMK-007). The binding maps campaign_id ->
live_session_id via session_for_campaign (the spend->session join hook), set-once and unambiguous.
"""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.measurement.attribution.resolver import AttributionResolver
from app.measurement.models.attribution_context import ConflictStatus, SourceConfidence
from app.measurement.models.live_session_ads_binding import LiveSessionAdsBinding
from app.measurement.store.live_session_ads_binding_store import (
    LiveSessionAdsBindingStore,
    LiveSessionAdsBindingStoreViolation,
)

D0 = datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc)


def _event(**over):
    base = dict(event_id="evt_1", campaign_id=None, adset_id=None, ad_id=None, live_session_id=None, page_id="p")
    base.update(over)
    return SimpleNamespace(**base)


def _conv(source_event_id="evt_1"):
    return SimpleNamespace(source_event_id=source_event_id)


# --- primary_campaign_id is first-class + deterministic -------------------------------------------
def test_primary_campaign_id_is_first_class_and_in_exports():
    ctx = AttributionResolver().resolve(
        _event(campaign_id="camp_1", adset_id="a1", ad_id="ad1"), _conv(),
        signals={"campaign_name": "C", "adset_name": "A", "ad_name": "D"},
    )
    assert ctx.primary_campaign_id == "camp_1"
    assert ctx.to_public()["primary_campaign_id"] == "camp_1"
    assert ctx.as_stored()["primary_campaign_id"] == "camp_1"


def test_primary_campaign_id_from_signal_when_event_lacks_it():
    ctx = AttributionResolver().resolve(
        _event(campaign_id=None, live_session_id="ls_1"), _conv(),
        signals={"primary_campaign_id": "camp_sig", "live_session_id": "ls_1"},
    )
    assert ctx.primary_campaign_id == "camp_sig"


def test_primary_campaign_id_is_deterministic_on_replay():
    ev = _event(campaign_id="camp_1", adset_id="a1", ad_id="ad1")
    a = AttributionResolver().resolve(ev, _conv())
    b = AttributionResolver().resolve(ev, _conv())
    assert a.primary_campaign_id == b.primary_campaign_id == "camp_1"
    assert a.as_stored() == b.as_stored()                       # additive field does not break replay idempotency


# --- NOT wired into grading: SMK-020 (complete ad -> HIGH) + SMK-007 (incomplete + live -> MULTI) --
def test_primary_campaign_id_does_not_change_grading():
    complete = AttributionResolver().resolve(
        _event(campaign_id="camp_1", adset_id="a1", ad_id="ad1", live_session_id="ls_1"), _conv(),
        signals={"campaign_name": "C", "adset_name": "A", "ad_name": "D"},
    )
    assert complete.source_confidence is SourceConfidence.HIGH        # SMK-020 unaffected
    assert complete.conflict_status is ConflictStatus.NONE
    assert complete.primary_campaign_id == "camp_1"

    incomplete = AttributionResolver().resolve(
        _event(campaign_id="camp_1", live_session_id="ls_1"), _conv(),      # ad path incomplete + a live session
        signals={"live_session_id": "ls_1"},
    )
    assert incomplete.conflict_status is ConflictStatus.MULTI_TOUCH   # SMK-007 unaffected
    assert incomplete.source_confidence is SourceConfidence.LOW
    assert incomplete.primary_campaign_id == "camp_1"


# --- binding.v1 maps campaign -> live_session (session_for_campaign) -------------------------------
def test_binding_maps_campaign_to_session():
    store = LiveSessionAdsBindingStore()
    store.bind(LiveSessionAdsBinding(live_session_id="ls_1", primary_campaign_id="camp_1", bound_at=D0,
                                     bound_by="ops"))
    assert store.session_for_campaign("camp_1") == "ls_1"
    assert store.session_for_campaign("camp_unbound") is None
    # bound_by masked on export (RULE-014); campaign id is not PII
    assert store.get("ls_1").to_public()["bound_by"] != "ops"
    assert store.get("ls_1").to_public()["primary_campaign_id"] == "camp_1"


def test_binding_is_set_once_and_unambiguous():
    store = LiveSessionAdsBindingStore()
    store.bind(LiveSessionAdsBinding(live_session_id="ls_1", primary_campaign_id="camp_1"))
    store.bind(LiveSessionAdsBinding(live_session_id="ls_1", primary_campaign_id="camp_1"))  # identical -> no-op
    with pytest.raises(LiveSessionAdsBindingStoreViolation):
        store.bind(LiveSessionAdsBinding(live_session_id="ls_1", primary_campaign_id="camp_2"))  # re-bind session
    with pytest.raises(LiveSessionAdsBindingStoreViolation):
        store.bind(LiveSessionAdsBinding(live_session_id="ls_2", primary_campaign_id="camp_1"))  # campaign reused
