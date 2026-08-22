"""M6.2E leg 1 / M6-SMK-007: an ORDER_VERIFIED whose source is MISSING still records revenue (Zone B), but the
snapshot degrades to source_confidence=LOW / conflict=MISSING_SOURCE and is flagged NOT scale evidence (RULE-009).
Revenue is never dropped for a verified order; it is simply not usable as scale evidence.
"""
from __future__ import annotations

from app.measurement.models.attribution_context import (
    ConflictStatus,
    EntryChannel,
    SourceConfidence,
)


def test_missing_source_still_stores_revenue_but_low_not_scale(
    make_measurement_event, make_conversion, attribution_materializer, measurement_store
):
    # verified order with NO campaign / live / referral source and no page attribution
    event = make_measurement_event("evt_nosrc", event_code="ORDER_VERIFIED", page_id="")
    conv = make_conversion(
        "ORDER_VERIFIED", source_event_id="evt_nosrc", revenue_value=99000.0,
        currency="VND", order_code="ORD_2",
    )
    outcome = attribution_materializer.materialize(event, conv)
    ctx = outcome.context

    assert ctx.conflict_status is ConflictStatus.MISSING_SOURCE
    assert ctx.source_confidence is SourceConfidence.LOW
    assert ctx.entry_channel is EntryChannel.DIRECT

    # revenue is STILL stored (a verified order is never dropped) ...
    row = measurement_store.get_by_event_id("evt_nosrc")
    assert row.revenue_value == 99000.0 and row.order_code == "ORD_2"

    # ... but the row is NEVER scale evidence (RULE-009) — on BOTH the data-quality bar and the ratified-model gate
    assert ctx.is_scale_evidence_eligible() is False
    assert outcome.scale_evidence_eligible is False
    assert outcome.scale_evidence is False
