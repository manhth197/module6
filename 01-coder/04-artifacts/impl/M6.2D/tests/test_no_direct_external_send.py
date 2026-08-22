"""M6.2C exit-gate leg 1 (RULE-004): NO direct external send. Every external payload originates from an outbox
row processed by a worker, never from a runtime request. The runtime holds no Transport; the staged transport
refuses to send while external_send=OFF, so even the worker makes no real call.
"""
from __future__ import annotations

import pytest

from app import config
from app.api.conversions import ConversionDeps, handle_conversions_request
from app.measurement.models.measurement_outbox import OutboxStatus
from app.measurement.outbox.measurement_dispatcher import MeasurementDispatcher
from app.measurement.outbox.transport import ExternalSendBlocked


def test_conversion_deps_hold_no_transport(conversion_deps):
    for forbidden in ("transport", "send", "dispatch", "deliver", "sync"):
        assert not hasattr(conversion_deps, forbidden)
    # the deps container carries only stores + validator + audit (write-outbox-only, RULE-004)
    assert set(vars(conversion_deps).keys()) <= {
        "validator", "conversion_store", "measurement_outbox", "audit", "max_retries",
    }


def test_staged_transport_refuses_to_send(staged_transport):
    with pytest.raises(ExternalSendBlocked):
        staged_transport.deliver(object())
    assert config.EXTERNAL_SEND == "OFF" and config.is_external_send_enabled() is False


def test_dispatcher_with_staged_transport_never_sends(
    conversion_deps, make_conversion_body, measurement_outbox, consent_gate, app_consent_reader, audit,
    staged_transport,
):
    """Even when the send_policy would pass (consent VALID + dq PASS), the STAGED transport prevents any real
    send: items are HELD (QUEUED + EXTERNAL_SEND_OFF), never SENT, never lost."""
    res = handle_conversions_request(make_conversion_body(), conversion_deps)
    assert res.status == "CREATED"
    assert len(measurement_outbox) == 2   # PIXEL + CAPI enqueued; runtime sent nothing

    disp = MeasurementDispatcher(
        measurement_outbox, staged_transport, consent_gate, app_consent_reader, audit,
        dq_status=lambda item: "PASS",
    )
    disp.run_once()
    assert measurement_outbox.count_status(OutboxStatus.SENT) == 0     # NOTHING sent (external_send=OFF)
    assert audit.find("EXTERNAL_SEND_OFF")                             # held + audited (no silent loss)
