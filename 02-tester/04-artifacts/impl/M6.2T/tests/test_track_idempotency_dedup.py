"""M6.2B exit-gate leg 2 (SMK-003): a replayed track request is deduped END-TO-END — no double count in
either the raw web_event_logs store or the normalized ads_measurement_events store (RULE-005/007).
"""
from __future__ import annotations

from app.api.track import handle_track_request


def test_first_request_accepted_creates_one_row_each(track_deps, make_track_body, store, measurement_store):
    res = handle_track_request(make_track_body(), track_deps)
    assert res.status == "ACCEPTED"
    assert res.idempotent_replay is False
    assert res.event_id is not None and res.log_id is not None
    assert res.data_quality_status == "HOLD"               # initial, fail-closed (no DQ check in M6.2B)
    assert len(store) == 1 and len(measurement_store) == 1


def test_replayed_request_is_deduped_no_double_count(track_deps, make_track_body, store, measurement_store):
    body = make_track_body()
    first = handle_track_request(body, track_deps)
    second = handle_track_request(dict(body), track_deps)   # identical body replayed
    assert first.status == "ACCEPTED" and second.status == "DUPLICATE"
    assert second.idempotent_replay is True
    assert second.event_id == first.event_id               # SAME normalized event, not a new one
    assert len(store) == 1, "no second web_event_logs row (RULE-005/007)"
    assert len(measurement_store) == 1, "no second ads_measurement_events row (RULE-005, SMK-003)"


def test_replay_survives_a_different_correlation_id(track_deps, make_track_body, store, measurement_store):
    """correlation_id is EXCLUDED from raw_event_hash, so a replay with a fresh correlation_id still dedups
    (the same underlying event maps to the same locked RULE-005 key)."""
    handle_track_request(make_track_body(correlation_id="corr_A"), track_deps)
    second = handle_track_request(make_track_body(correlation_id="corr_B"), track_deps)
    assert second.status == "DUPLICATE" and second.idempotent_replay is True
    assert len(store) == 1 and len(measurement_store) == 1


def test_different_event_is_not_deduped(track_deps, make_track_body, store, measurement_store):
    handle_track_request(make_track_body(), track_deps)                       # VIEW_LANDING p1/s1
    other = handle_track_request(make_track_body(page_id="p2"), track_deps)   # different page -> different key
    assert other.status == "ACCEPTED" and other.idempotent_replay is False
    assert len(store) == 2 and len(measurement_store) == 2
