"""Official smoke — slice M6.2D — M6-SMK-003 (doc ADS-P0-003), platform (Pixel/CAPI/Offline) dedup flavor.

Authored by TESTER in M6-P1303 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1304
(TESTER_RUN -> 04-artifacts/test-reports/M6.2D/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 403):

    Kịch bản (verbatim):          "Duplicate Pixel/CAPI/Offline"
    Kết quả phải đạt (verbatim):  "Dedup, không double count"

M6.2D binds SMK-003 to PLATFORM send discipline: PIXEL + CAPI (+ OFFLINE for ORDER_VERIFIED) of ONE source
event build the SAME platform `event_id` (`hash(source_event_id + event_code)`), so the platform (Meta)
collapses them — one conversion is counted once, not once per platform (FAIL-001, no double count). The internal
`dedup_key` stays UNIQUE per (conversion x platform). Proven end-to-end via the PII-safe `PlatformResultLog`
that the staged transport writes (it builds + logs, then blocks — external_send=OFF, no real send). RULE-005 /
RULE-003. All ids synthetic; identity hashed in payloads, masked on export. Reuses the shared conftest fixtures
(conversion_deps, make_conversion_body, make_conversion, measurement_outbox, consent_gate, app_consent_reader,
audit, platform_transport, platform_result_log).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.api.conversions import handle_conversions_request
from app.measurement.integration.payload import build_platform_payload, platform_event_id
from app.measurement.models.measurement_outbox import MeasurementPlatform
from app.measurement.outbox.measurement_dispatcher import MeasurementDispatcher

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def _disp(store, transport, gate, reader, audit):
    return MeasurementDispatcher(store, transport, gate, reader, audit, dq_status=lambda item: "PASS")


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_003_pixel_and_capi_of_one_event_dedup_no_double_count(
    conversion_deps, make_conversion_body, measurement_outbox, consent_gate, app_consent_reader, audit,
    platform_transport, platform_result_log,
):
    """M6-SMK-003 "Duplicate Pixel/CAPI/Offline" -> "Dedup, không double count".

    One source conversion fans out to PIXEL + CAPI; both build the SAME platform event_id, so the platform
    collapses them — the same event is not double counted. The internal dedup_key stays unique per platform.
    """
    res = handle_conversions_request(make_conversion_body(), conversion_deps)   # VIEW_LANDING -> PIXEL + CAPI
    assert res.status == "CREATED"
    _disp(measurement_outbox, platform_transport, consent_gate, app_consent_reader, audit).run_once(now=_TS)

    assert len(platform_result_log) == 2
    assert {r.platform for r in platform_result_log.records} == {"PIXEL", "CAPI"}
    event_ids = {r.event_id for r in platform_result_log.records}
    assert len(event_ids) == 1, "Pixel + CAPI of one source event share event_id -> platform dedup, no double count"
    dedup_keys = {row.dedup_key for row in measurement_outbox.all()}
    assert len(dedup_keys) == 2, "internal dedup_key stays unique per platform (one row per conversion x platform)"


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_003_neg_offline_for_order_verified_shares_the_same_event_id(make_conversion):
    """The Offline arm of "Pixel/CAPI/Offline": for an ORDER_VERIFIED source, PIXEL, CAPI and OFFLINE all build
    the SAME shared event_id — all three platforms dedup to one platform-side event (no triple count)."""
    conv = make_conversion("ORDER_VERIFIED", source_event_id="evt_ov")
    pix = build_platform_payload(conv, MeasurementPlatform.PIXEL)
    capi = build_platform_payload(conv, MeasurementPlatform.CAPI)
    offline = build_platform_payload(conv, MeasurementPlatform.OFFLINE)
    assert pix.event_id == capi.event_id == offline.event_id == platform_event_id("evt_ov", "ORDER_VERIFIED")


def test_smk_003_neg_replayed_conversion_is_not_re_enqueued(
    conversion_deps, make_conversion_body, measurement_outbox
):
    """A replayed identical conversion is deduped at the endpoint (server-derived key) — DUPLICATE, no new
    outbox rows, so no double count downstream (RULE-005)."""
    first = handle_conversions_request(make_conversion_body(), conversion_deps)
    second = handle_conversions_request(make_conversion_body(), conversion_deps)   # identical replay
    assert first.status == "CREATED" and second.status == "DUPLICATE"
    assert second.idempotent_replay is True
    assert len(measurement_outbox) == 2, "a replayed conversion never re-enqueues (no double count)"


# --- positive control: proves the dedup DISCRIMINATES (does not collapse distinct events) ----------
def test_smk_003_control_distinct_source_events_get_distinct_event_ids():
    """Control (non-vacuity): two DIFFERENT source events get DIFFERENT platform event_ids (deterministic and
    stable), so the shared-id dedup collapses true duplicates only — it does not merge unrelated conversions."""
    a = platform_event_id("evt_1", "VIEW_LANDING")
    b = platform_event_id("evt_2", "VIEW_LANDING")
    assert a != b
    assert platform_event_id("evt_1", "VIEW_LANDING") == a   # deterministic / stable across calls
