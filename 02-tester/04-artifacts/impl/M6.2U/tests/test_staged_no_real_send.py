"""M6.2D: the staged platform transport builds + logs but NEVER sends (external_send=OFF, H01). The item is held
(never SENT), the result log records BLOCKED_EXTERNAL_SEND_OFF — no real platform call ever happens.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app import config
from app.api.conversions import handle_conversions_request
from app.measurement.integration.result_log import SendResult
from app.measurement.models.measurement_outbox import OutboxStatus
from app.measurement.outbox.measurement_dispatcher import MeasurementDispatcher

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def test_staged_transport_builds_logs_but_never_sends(
    conversion_deps, make_conversion_body, measurement_outbox, consent_gate, app_consent_reader, audit,
    platform_transport, platform_result_log,
):
    handle_conversions_request(make_conversion_body(), conversion_deps)
    MeasurementDispatcher(
        measurement_outbox, platform_transport, consent_gate, app_consent_reader, audit,
        dq_status=lambda item: "PASS",
    ).run_once(now=_TS)

    # nothing SENT (external_send=OFF); the item is held, the discipline (payload+log) still ran
    assert measurement_outbox.count_status(OutboxStatus.SENT) == 0
    assert len(platform_result_log) == 2
    assert all(r.result is SendResult.BLOCKED_EXTERNAL_SEND_OFF for r in platform_result_log.records)
    assert config.is_external_send_enabled() is False
    assert audit.find("EXTERNAL_SEND_OFF")   # the dispatcher held the item (no silent loss)
