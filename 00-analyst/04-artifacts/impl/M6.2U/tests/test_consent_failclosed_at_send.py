"""M6.2C SMK-002 / FAIL-002: consent fail-closed at SEND (RULE-002 checkpoint 2). A consent-invalid item is
NEVER delivered (policy-block -> DEAD_LETTER, transport.deliver never called), audited. Consent that was valid
at event time but has lapsed by send time is also blocked (the send-time checkpoint).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.measurement.models.measurement_outbox import OutboxStatus
from app.measurement.outbox.enqueue import enqueue_measurement
from app.measurement.outbox.measurement_dispatcher import MeasurementDispatcher

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def _dispatcher(store, transport, consent_gate, reader, audit):
    return MeasurementDispatcher(store, transport, consent_gate, reader, audit, dq_status=lambda item: "PASS")


def test_missing_consent_is_never_sent(
    make_conversion, measurement_outbox, consent_gate, app_consent_reader, audit, succeeding_transport
):
    # cs_missing (state MISSING) -> permits_send False -> policy-block CONSENT -> DEAD_LETTER, NO delivery.
    conv = make_conversion("VIEW_LANDING", consent_snapshot_id="cs_missing", customer_or_guest_key="guest_x")
    enqueue_measurement(conv, measurement_outbox, max_retries=3)
    _dispatcher(measurement_outbox, succeeding_transport, consent_gate, app_consent_reader, audit).run_once(now=_TS)
    assert succeeding_transport.delivered == [], "a consent-invalid item must NEVER be delivered"
    assert measurement_outbox.count_status(OutboxStatus.SENT) == 0
    assert measurement_outbox.count_status(OutboxStatus.DEAD_LETTER) == 2
    assert audit.find("SEND_BLOCKED_CONSENT")


def test_consent_lapsed_at_send_is_blocked(
    make_conversion, measurement_outbox, consent_gate, app_consent_reader, audit, succeeding_transport
):
    # cs_valid_b is VALID at event time (subject guest_B) but current_state(guest_B) is not VALID at send
    # -> the send-time checkpoint (RULE-002 checkpoint 2) blocks it.
    conv = make_conversion("VIEW_LANDING", consent_snapshot_id="cs_valid_b", customer_or_guest_key="guest_B")
    enqueue_measurement(conv, measurement_outbox, max_retries=3)
    _dispatcher(measurement_outbox, succeeding_transport, consent_gate, app_consent_reader, audit).run_once(now=_TS)
    assert succeeding_transport.delivered == []
    assert audit.find("SEND_BLOCKED_CONSENT")


def test_consent_valid_at_send_would_deliver(
    make_conversion, measurement_outbox, consent_gate, app_consent_reader, audit, succeeding_transport
):
    """Control (do not over-block): cs_valid (subject guest_mapped_ok, current VALID) passes BOTH checkpoints,
    so with a succeeding (injected) transport it delivers."""
    conv = make_conversion("VIEW_LANDING", consent_snapshot_id="cs_valid", customer_or_guest_key="guest_mapped_ok")
    enqueue_measurement(conv, measurement_outbox, max_retries=3)
    _dispatcher(measurement_outbox, succeeding_transport, consent_gate, app_consent_reader, audit).run_once(now=_TS)
    assert measurement_outbox.count_status(OutboxStatus.SENT) == 2
