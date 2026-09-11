"""M6.2D: OFFLINE conversion only after ORDER_VERIFIED (RULE-003, FAIL-001). The staged platform transport
refuses to build an OFFLINE payload for a non-ORDER_VERIFIED source (defense-in-depth over the M6.2C fan-out
guard, which already enqueues OFFLINE rows only for ORDER_VERIFIED).
"""
from __future__ import annotations

import pytest

from app.measurement.integration.platform_transport import OfflineNotVerified, StagedPlatformTransport
from app.measurement.models.measurement_outbox import MeasurementOutboxItem, MeasurementPlatform
from app.measurement.outbox.transport import ExternalSendBlocked


def _offline_item(conversion_id):
    return MeasurementOutboxItem(
        outbox_id="ob_offline", source_event_id=conversion_id, platform=MeasurementPlatform.OFFLINE,
        dedup_key="dk_off", idempotency_key="ik_off", payload_ref="p", consent_snapshot_id="cs_valid",
        max_retries=3,
    )


def test_offline_refused_for_non_verified_source(make_conversion, conversion_store, platform_result_log):
    conv = make_conversion("VIEW_LANDING", source_event_id="evt_nv")   # NOT ORDER_VERIFIED
    conversion_store.create(conv)
    transport = StagedPlatformTransport(conversion_store, platform_result_log)
    with pytest.raises(OfflineNotVerified):
        transport.deliver(_offline_item(conv.conversion_id))
    assert len(platform_result_log) == 0   # refused before any payload/log


def test_offline_allowed_for_verified_source_but_still_blocked_staged(make_conversion, conversion_store, platform_result_log):
    conv = make_conversion("ORDER_VERIFIED", source_event_id="evt_ov")
    conversion_store.create(conv)
    transport = StagedPlatformTransport(conversion_store, platform_result_log)
    with pytest.raises(ExternalSendBlocked):   # builds the payload + logs, then blocks (external_send=OFF)
        transport.deliver(_offline_item(conv.conversion_id))
    assert len(platform_result_log) == 1       # payload was built + logged (PII-safe) before the staged block
