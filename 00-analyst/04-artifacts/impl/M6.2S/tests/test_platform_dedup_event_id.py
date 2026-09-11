"""M6.2D exit-gate leg 1 (SMK-003, FAIL-001): no double count. Pixel + CAPI of ONE source event build the SAME
platform event_id so the platform (Meta) collapses them; distinct source events get distinct event_ids; the
internal dedup_key stays UNIQUE per (conversion x platform). Proven via the PII-safe platform result log.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.api.conversions import handle_conversions_request
from app.measurement.integration.payload import build_platform_payload, platform_event_id
from app.measurement.models.measurement_outbox import MeasurementPlatform, OutboxStatus
from app.measurement.outbox.measurement_dispatcher import MeasurementDispatcher

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def _disp(store, transport, gate, reader, audit):
    return MeasurementDispatcher(store, transport, gate, reader, audit, dq_status=lambda item: "PASS")


def test_pixel_and_capi_share_event_id(
    conversion_deps, make_conversion_body, measurement_outbox, consent_gate, app_consent_reader, audit,
    platform_transport, platform_result_log,
):
    res = handle_conversions_request(make_conversion_body(), conversion_deps)   # VIEW_LANDING -> PIXEL + CAPI
    assert res.status == "CREATED"
    _disp(measurement_outbox, platform_transport, consent_gate, app_consent_reader, audit).run_once(now=_TS)
    assert len(platform_result_log) == 2
    platforms = {r.platform for r in platform_result_log.records}
    assert platforms == {"PIXEL", "CAPI"}
    event_ids = {r.event_id for r in platform_result_log.records}
    assert len(event_ids) == 1, "Pixel + CAPI of one source event MUST share event_id (platform dedup, FAIL-001)"


def test_distinct_source_events_get_distinct_event_ids():
    a = platform_event_id("evt_1", "VIEW_LANDING")
    b = platform_event_id("evt_2", "VIEW_LANDING")
    assert a != b
    assert platform_event_id("evt_1", "VIEW_LANDING") == a   # deterministic / stable


def test_build_payload_event_id_matches_helper(make_conversion):
    conv = make_conversion("VIEW_LANDING", source_event_id="evt_9")
    pix = build_platform_payload(conv, MeasurementPlatform.PIXEL)
    capi = build_platform_payload(conv, MeasurementPlatform.CAPI)
    assert pix.event_id == capi.event_id == platform_event_id("evt_9", "VIEW_LANDING")
    assert pix.platform == "PIXEL" and capi.platform == "CAPI"


def test_internal_dedup_key_unique_per_platform(
    conversion_deps, make_conversion_body, measurement_outbox
):
    handle_conversions_request(make_conversion_body(), conversion_deps)
    keys = {row.dedup_key for row in measurement_outbox.all()}
    assert len(keys) == len(measurement_outbox) == 2   # one row per platform, distinct internal dedup_key
