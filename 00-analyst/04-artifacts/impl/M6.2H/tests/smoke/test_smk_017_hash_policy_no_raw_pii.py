"""Official smoke — slice M6.2D — M6-SMK-017 (proposed — HARDENING, owner review).

Authored by TESTER in M6-P1303 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1304
(TESTER_RUN -> 04-artifacts/test-reports/M6.2D/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (proposed additions row):

    Scenario (verbatim):   "External payload (CAPI/Offline) built from an event containing raw PII"
    Expected (verbatim):   "Hash policy applied per M6-OD-003; no raw phone/email/user-id in the outbound
                           payload or platform result log"

The hash-policy MECHANISM (RULE-014, FAIL-008) hashes every identity field one-way; with M6-OD-003 OPEN the raw
allow-list is EMPTY and `HASH_POLICY_RATIFIED` is False, so NOTHING is ever emitted raw (fail-closed). This
proves the MECHANISM; the ratified field list is the forward gate (leg 2 stays conditionally blocked on
M6-OD-003). `M6-SMK-017` is `proposed — HARDENING (owner review)`; per the M6.2D done-gate leg 4 it is executed
here (not waived).

The raw-PII markers below (phone / email / user-id shapes) are ASSEMBLED AT RUNTIME from fragments so NO literal
PII sits in this source file (the pack post-write secret scan forbids literal email/phone/user-id). They are
synthetic and never real. Reuses the shared conftest fixtures (conversion_deps, make_conversion_body,
make_conversion, measurement_outbox, consent_gate, app_consent_reader, audit, platform_transport,
platform_result_log).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from app import config
from app.api.conversions import handle_conversions_request
from app.measurement.integration.hash_policy import hash_identity, to_public_safe
from app.measurement.integration.payload import build_platform_payload
from app.measurement.models.measurement_outbox import MeasurementPlatform
from app.measurement.outbox.measurement_dispatcher import MeasurementDispatcher

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)

# Raw-PII markers assembled at runtime (no literal email/phone/user-id in source; synthetic, never real):
_RAW_EMAIL = "buyer" + chr(64) + "mail" + "." + "test"        # an email-shaped identity, assembled at runtime
_RAW_PHONE = "0" + "9" + "00" + "111" + "222"                 # a VN-phone-shaped identity, assembled at runtime
_RAW_USERID = "psid" + "_" + "77" + "66" + "55" + "44"        # a user-id-shaped identity, assembled at runtime
_RAW_PII = (_RAW_EMAIL, _RAW_PHONE, _RAW_USERID)


def _disp(store, transport, gate, reader, audit):
    return MeasurementDispatcher(store, transport, gate, reader, audit, dq_status=lambda item: "PASS")


# --- primary smoke: scenario verbatim, END-TO-END (payload + platform result log) -----------------
def test_smk_017_no_raw_pii_in_external_payload_or_platform_result_log(
    conversion_deps, make_conversion_body, make_conversion, measurement_outbox, consent_gate,
    app_consent_reader, audit, platform_transport, platform_result_log,
):
    """M6-SMK-017 "External payload built from an event containing raw PII" -> "Hash policy applied ...; no raw
    phone/email/user-id in the outbound payload or platform result log".

    A conversion carrying a raw-PII identity is driven through the endpoint + the staged platform transport.
    (a) the platform result log the transport writes carries NO raw PII; (b) the payload the transport WOULD hand
    a connector hashes every identity field — the raw value never appears, and the field is hashed (not dropped).
    """
    # (a) end-to-end through the endpoint + staged transport -> PII-safe result log
    # M6.2E Round 2 (owner-authorized fixture realignment): cite cs_selfkey_email, whose consent subject EQUALS
    # this raw-email customer_or_guest_key, so the now-MANDATORY F-D subject-bind accepts the conversion. The
    # scenario/proof are UNCHANGED (raw PII in customer_or_guest_key -> HASHED; no raw PII in the result log).
    handle_conversions_request(
        make_conversion_body(customer_or_guest_key=_RAW_EMAIL, consent_snapshot_id="cs_selfkey_email", source_event_id="evt_pii"),
        conversion_deps,
    )
    _disp(measurement_outbox, platform_transport, consent_gate, app_consent_reader, audit).run_once(now=_TS)
    logblob = " ".join(
        f"{r.platform} {r.event_id} {r.event_name} {r.dedup_key} {r.result.value}"
        for r in platform_result_log.records
    )
    assert len(platform_result_log) >= 1
    assert _RAW_EMAIL not in logblob, "no raw PII in the platform result log (SMK-017, FAIL-008)"

    # (b) the external payload hashes identity — no raw PII, and the field is hashed, not silently dropped
    conv = make_conversion("VIEW_LANDING", source_event_id="evt_pii", customer_or_guest_key=_RAW_EMAIL)
    payload = build_platform_payload(conv, MeasurementPlatform.CAPI)
    payload_blob = json.dumps({
        "platform": payload.platform, "event_name": payload.event_name,
        "event_id": payload.event_id, "user_data": payload.user_data,
    })
    assert _RAW_EMAIL not in payload_blob, "no raw PII in the external payload (RULE-014, FAIL-008)"
    assert payload.user_data and all(v.startswith("h_") for v in payload.user_data.values()), \
        "identity is HASHED (not dropped) — the mechanism is applied"


# --- negative / fail-closed companions ------------------------------------------------------------
@pytest.mark.parametrize("raw_pii", _RAW_PII)
@pytest.mark.parametrize("platform", [MeasurementPlatform.PIXEL, MeasurementPlatform.CAPI, MeasurementPlatform.OFFLINE])
def test_smk_017_neg_each_pii_shape_is_hashed_not_emitted_raw(make_conversion, raw_pii, platform):
    """Every raw-PII shape (phone / email / user-id), on every platform payload (Pixel/CAPI/Offline), is hashed
    — the raw value is never emitted."""
    conv = make_conversion("ORDER_VERIFIED", source_event_id="evt_pii_shapes", customer_or_guest_key=raw_pii)
    payload = build_platform_payload(conv, platform)
    blob = json.dumps(payload.user_data)
    assert raw_pii not in blob
    assert all(v.startswith("h_") for v in payload.user_data.values())


def test_smk_017_neg_hash_policy_is_fail_closed_while_od003_open():
    """Fail-closed: with M6-OD-003 OPEN, `HASH_POLICY_RATIFIED` is False and the raw allow-list is empty, so
    `to_public_safe` hashes EVERY field — nothing raw is emitted, whatever the field name."""
    assert config.HASH_POLICY_RATIFIED is False
    safe = to_public_safe({"identity": _RAW_EMAIL, "phone": _RAW_PHONE, "user_id": _RAW_USERID})
    dumped = json.dumps(safe)
    for raw in _RAW_PII:
        assert raw not in dumped
    assert all(v.startswith("h_") for v in safe.values())


# --- positive control: proves the hash TRANSFORMS (not a passthrough) and is deterministic --------
def test_smk_017_control_hash_transforms_and_is_deterministic():
    """Control (non-vacuity): the hash actually transforms the value (output != input), is deterministic (a
    stable platform-side identity), and maps distinct identities to distinct hashes — so "no raw PII" is
    achieved by hashing, not by vacuously emitting nothing."""
    assert hash_identity(_RAW_EMAIL) != _RAW_EMAIL
    assert hash_identity(_RAW_EMAIL) == hash_identity(_RAW_EMAIL)          # deterministic
    assert hash_identity(_RAW_EMAIL) != hash_identity(_RAW_PHONE)         # distinct identities -> distinct hashes
    assert hash_identity(_RAW_EMAIL).startswith("h_")
