"""M6.2B: the ads_measurement_events store (M6-CTR-001) — Zone-A append + UNIQUE dedup + forbidden-op
rejection. Backs the store-level half of SMK-003 and the CTR-001 immutability contract (RULE-005/007/008/003).
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.measurement.models.measurement_event import AdsMeasurementEvent, DataQualityStatus
from app.measurement.store.measurement_event_store import (
    MeasurementEventStore,
    MeasurementStoreViolation,
)

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def _row(key="k1", event_id="evt_1", **over):
    base = dict(
        event_id=event_id, event_code="VIEW_LANDING", event_ts=_TS,
        idempotency_key=key, correlation_id="corr_1",
    )
    base.update(over)
    return AdsMeasurementEvent(**base)


def test_insert_creates_zone_a_row_with_locked_defaults():
    store = MeasurementEventStore()
    r = store.insert(_row())
    assert r.created is True and len(store) == 1
    assert r.row.currency == "VND"                                  # locked constant
    assert r.row.data_quality_status is DataQualityStatus.HOLD      # initial, fail-closed
    assert r.row.revenue_value is None and r.row.order_code is None # Zone B unset in M6.2B
    assert dict(r.row.attribution_context) == {}                   # empty-initial (materialized later)


def test_duplicate_idempotency_key_is_deduped():
    store = MeasurementEventStore()
    store.insert(_row(key="dup", event_id="evt_a"))
    r2 = store.insert(_row(key="dup", event_id="evt_b"))
    assert r2.created is False                    # dedup: no second row (SMK-003)
    assert r2.row.event_id == "evt_a"             # the EXISTING row is returned
    assert len(store) == 1


def test_update_and_delete_are_forbidden():
    store = MeasurementEventStore()
    store.insert(_row())
    with pytest.raises(MeasurementStoreViolation):
        store.update()
    with pytest.raises(MeasurementStoreViolation):
        store.delete()


def test_revenue_bearing_insert_is_rejected_in_this_slice():
    """M6.2B inserts Zone A only; revenue is set later on the ORDER_VERIFIED path (RULE-003), never at ingest."""
    store = MeasurementEventStore()
    with pytest.raises(MeasurementStoreViolation):
        store.insert(_row(revenue_value=100000.0, order_code="ord_1"))
