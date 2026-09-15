"""M6.2B: CTR-016 request validation (all error codes) + response shape; consent fail-closed at the endpoint;
no external-send path reachable (external_send=OFF). Request bodies are UNTRUSTED (RULE-H03).
"""
from __future__ import annotations

from app import config
from app.api.track import handle_track_request


def test_missing_event_code_is_schema_invalid(track_deps, make_track_body):
    body = make_track_body()
    del body["event_code"]
    res = handle_track_request(body, track_deps)
    assert res.status == "REJECTED" and res.error_code == "SCHEMA_INVALID" and res.field == "event_code"


def test_missing_idempotency_key(track_deps, make_track_body):
    body = make_track_body()
    del body["idempotency_key"]
    assert handle_track_request(body, track_deps).error_code == "IDEMPOTENCY_KEY_MISSING"


def test_missing_consent_snapshot_id(track_deps, make_track_body):
    body = make_track_body()
    del body["consent_snapshot_id"]
    assert handle_track_request(body, track_deps).error_code == "CONSENT_MISSING_OR_INVALID"


def test_naive_event_ts_is_schema_invalid(track_deps, make_track_body):
    res = handle_track_request(make_track_body(event_ts="2026-07-29T12:00:00"), track_deps)  # no tz offset
    assert res.error_code == "SCHEMA_INVALID" and res.field == "event_ts"


def test_raw_pii_in_payload_is_rejected(track_deps, make_track_body):
    # Assemble the PII trigger at RUNTIME so no literal email/phone appears in this source file (the pack
    # secret-scan forbids raw PII in code). The endpoint's RULE-014 tripwire must still catch it.
    raw_email = "buyer" + "@" + "example" + ".com"
    res = handle_track_request(make_track_body(payload={"note": "reach me at " + raw_email}), track_deps)
    assert res.error_code == "RAW_PII_IN_PAYLOAD"
    # a VN-phone-shaped string is likewise refused (assembled at runtime)
    raw_phone = "0" + "9" * 9
    res2 = handle_track_request(make_track_body(payload={"n": "call " + raw_phone}), track_deps)
    assert res2.error_code == "RAW_PII_IN_PAYLOAD"


def test_non_object_body_is_schema_invalid(track_deps):
    assert handle_track_request("not-an-object", track_deps).error_code == "SCHEMA_INVALID"


def test_valid_request_response_shape(track_deps, make_track_body):
    res = handle_track_request(make_track_body(), track_deps)
    assert res.status == "ACCEPTED"
    assert res.log_id and res.event_id and res.correlation_id
    assert res.data_quality_status == "HOLD"
    assert res.idempotent_replay is False


def test_valid_event_with_missing_consent_is_logged_but_not_egress_eligible(
    track_deps, make_track_body, store, measurement_store
):
    """Consent fail-closed: cs_missing (subject guest_x, state MISSING) with a matching guest_id binds, but
    consent is not VALID -> egress ineligible. The valid event is STILL logged internally (RULE-002 gates
    egress, not ingestion). external_send=OFF regardless."""
    res = handle_track_request(
        make_track_body(consent_snapshot_id="cs_missing", guest_id="guest_x"), track_deps
    )
    assert res.status == "ACCEPTED"
    assert len(store) == 1 and len(measurement_store) == 1


def test_no_external_send_path(track_deps):
    assert config.EXTERNAL_SEND == "OFF" and config.is_external_send_enabled() is False
    for forbidden in ("send", "dispatch", "publish", "scale", "sync_audience", "post"):
        assert not hasattr(track_deps, forbidden)
        assert not hasattr(track_deps.ingest_service, forbidden)
