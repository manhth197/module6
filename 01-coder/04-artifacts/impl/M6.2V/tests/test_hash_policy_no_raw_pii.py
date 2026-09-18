"""M6.2D exit-gate leg 2 (SMK-017, FAIL-008): no raw PII in any external payload or platform result log. Every
identity field is hashed (hash-policy mechanism); with M6-OD-003 OPEN the raw allow-list is empty -> fail-closed,
nothing raw is ever emitted. Leg 2 stays conditionally blocked on M6-OD-003 for the ratified field list; the
MECHANISM is what this proves. The PII marker is assembled at runtime (no literal PII in source).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from app import config
from app.api.conversions import handle_conversions_request
from app.measurement.integration.hash_policy import to_public_safe
from app.measurement.integration.payload import build_platform_payload
from app.measurement.models.measurement_outbox import MeasurementPlatform
from app.measurement.outbox.measurement_dispatcher import MeasurementDispatcher

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
_PII = "guest" + "_IDMARKER_" + "abc"   # a distinctive identity marker; no @/phone shape; assembled at runtime


def test_hash_policy_is_fail_closed_and_ratified_false():
    assert config.HASH_POLICY_RATIFIED is False           # M6-OD-003 OPEN -> nothing raw
    safe = to_public_safe({"identity": _PII, "phone": _PII})
    assert _PII not in json.dumps(safe)                    # every value hashed
    assert all(v.startswith("h_") for v in safe.values())


def test_built_payload_has_no_raw_pii(make_conversion):
    conv = make_conversion("VIEW_LANDING", source_event_id="evt_pii", customer_or_guest_key=_PII)
    payload = build_platform_payload(conv, MeasurementPlatform.PIXEL)
    blob = json.dumps({
        "platform": payload.platform, "event_name": payload.event_name,
        "event_id": payload.event_id, "user_data": payload.user_data,
    })
    assert _PII not in blob, "raw identity must not appear in the external payload (RULE-014, FAIL-008)"
    assert any(v.startswith("h_") for v in payload.user_data.values())


def test_result_log_has_no_raw_pii(
    conversion_deps, make_conversion_body, measurement_outbox, conversion_store, consent_gate,
    app_consent_reader, audit, platform_transport, platform_result_log,
):
    # M6.2E Round 2 (owner-authorized): cite the self-key consent whose subject == _PII so the now-MANDATORY
    # F-D bind accepts this conversion. The proof is unchanged — a raw-PII customer_or_guest_key must be HASHED
    # (no raw PII in the result log); only the cited consent's subject was realigned to the same key.
    handle_conversions_request(
        make_conversion_body(customer_or_guest_key=_PII, consent_snapshot_id="cs_selfkey_pii", source_event_id="evt_pii2"),
        conversion_deps,
    )
    MeasurementDispatcher(
        measurement_outbox, platform_transport, consent_gate, app_consent_reader, audit,
        dq_status=lambda item: "PASS",
    ).run_once(now=_TS)
    logblob = " ".join(
        f"{r.platform} {r.event_id} {r.event_name} {r.dedup_key} {r.result.value}"
        for r in platform_result_log.records
    )
    assert _PII not in logblob, "raw identity must not appear in the platform result log (SMK-017)"
    assert len(platform_result_log) >= 1
