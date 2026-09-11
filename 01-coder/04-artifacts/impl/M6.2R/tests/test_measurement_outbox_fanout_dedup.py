"""M6.2C: the measurement-outbox fan-out + dedup (RULE-005). One conversion -> one QUEUED row per platform,
UNIQUE dedup_key; OFFLINE only for ORDER_VERIFIED; a re-enqueue of the same conversion is deduped (no double
send). The dedup_key is HASHED so no raw PII sits in the key (O1).
"""
from __future__ import annotations

from app.measurement.models.measurement_outbox import MeasurementPlatform
from app.measurement.outbox.enqueue import enqueue_measurement


def test_fanout_two_platforms_for_non_verified(make_conversion, measurement_outbox):
    conv = make_conversion("VIEW_LANDING")
    results = enqueue_measurement(conv, measurement_outbox, max_retries=3)
    platforms = {row.platform for row, _created in results}
    assert MeasurementPlatform.OFFLINE not in platforms
    assert platforms == {MeasurementPlatform.PIXEL, MeasurementPlatform.CAPI}
    assert len(measurement_outbox) == 2


def test_offline_only_for_order_verified(make_conversion, measurement_outbox):
    conv = make_conversion("ORDER_VERIFIED")
    results = enqueue_measurement(conv, measurement_outbox, max_retries=3)
    assert MeasurementPlatform.OFFLINE in {row.platform for row, _created in results}
    assert len(measurement_outbox) == 3


def test_reenqueue_same_conversion_is_deduped(make_conversion, measurement_outbox):
    conv = make_conversion("VIEW_LANDING")
    enqueue_measurement(conv, measurement_outbox, max_retries=3)
    second = enqueue_measurement(conv, measurement_outbox, max_retries=3)
    assert all(created is False for _row, created in second)   # dedup: no new rows (RULE-005 UNIQUE dedup_key)
    assert len(measurement_outbox) == 2


def test_dedup_key_contains_no_raw_pii(make_conversion, measurement_outbox):
    conv = make_conversion("VIEW_LANDING", customer_or_guest_key="guest_pii_marker")
    results = enqueue_measurement(conv, measurement_outbox, max_retries=3)
    for row, _created in results:
        assert "guest_pii_marker" not in row.dedup_key      # hashed => no raw PII in the key
        assert "guest_pii_marker" not in row.payload_ref    # payload_ref is PII-safe
