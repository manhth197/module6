"""M6.2C exit-gate leg 2 (SMK-016): bounded retry -> dead-letter, no infinite retry, no silent loss. A transient
transport failure is retried up to max_retries, then dead-lettered with a full trace (error_log). A successful
transport marks the row SENT. Exercised with INJECTED transports (test doubles) — no real platform call.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.measurement.models.measurement_outbox import OutboxStatus
from app.measurement.outbox.enqueue import enqueue_measurement
from app.measurement.outbox.measurement_dispatcher import MeasurementDispatcher

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def _dispatcher(store, transport, consent_gate, reader, audit):
    # dq_status PASS so the send_policy passes and the transport path (retry/success) is exercised.
    return MeasurementDispatcher(store, transport, consent_gate, reader, audit, dq_status=lambda item: "PASS")


def test_transient_failure_retries_then_dead_letters(
    make_conversion, measurement_outbox, consent_gate, app_consent_reader, audit, failing_transport
):
    conv = make_conversion("VIEW_LANDING", consent_snapshot_id="cs_valid", customer_or_guest_key="guest_mapped_ok")
    enqueue_measurement(conv, measurement_outbox, max_retries=3)   # 2 rows (PIXEL, CAPI)
    disp = _dispatcher(measurement_outbox, failing_transport, consent_gate, app_consent_reader, audit)

    # run repeatedly, advancing time past each next_retry_at
    for i in range(5):
        disp.run_once(now=_TS + timedelta(hours=i + 1))

    assert measurement_outbox.count_status(OutboxStatus.SENT) == 0
    assert measurement_outbox.count_status(OutboxStatus.DEAD_LETTER) == 2
    for row in measurement_outbox.all():
        assert row.retry_count == 3, "bounded at max_retries — no infinite retry"
        assert row.error_log and "SEND_FAILED" in row.error_log     # full trace, no silent loss
    assert audit.find("OUTBOX_RETRY") and audit.find("OUTBOX_DEAD_LETTER")


def test_successful_transport_marks_sent(
    make_conversion, measurement_outbox, consent_gate, app_consent_reader, audit, succeeding_transport
):
    conv = make_conversion("VIEW_LANDING", consent_snapshot_id="cs_valid", customer_or_guest_key="guest_mapped_ok")
    enqueue_measurement(conv, measurement_outbox, max_retries=3)
    disp = _dispatcher(measurement_outbox, succeeding_transport, consent_gate, app_consent_reader, audit)
    disp.run_once(now=_TS)
    assert measurement_outbox.count_status(OutboxStatus.SENT) == 2
    assert len(succeeding_transport.delivered) == 2


def test_dead_lettered_item_is_not_reprocessed(
    make_conversion, measurement_outbox, consent_gate, app_consent_reader, audit, failing_transport
):
    conv = make_conversion("VIEW_LANDING")
    enqueue_measurement(conv, measurement_outbox, max_retries=1)   # dead-letters on the first failure
    disp = _dispatcher(measurement_outbox, failing_transport, consent_gate, app_consent_reader, audit)
    disp.run_once(now=_TS)
    assert measurement_outbox.count_status(OutboxStatus.DEAD_LETTER) == 2
    attempts_after_first = failing_transport.attempts
    disp.run_once(now=_TS + timedelta(days=1))       # dead-lettered rows are not due -> not retried again
    assert failing_transport.attempts == attempts_after_first
