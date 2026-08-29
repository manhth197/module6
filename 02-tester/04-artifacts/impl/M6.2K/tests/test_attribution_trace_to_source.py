"""M6.2E leg 1 / M6-SMK-006: an ORDER_VERIFIED with a full campaign/adset/ad + page traces back to source; the
ads_attribution_context is populated; confidence HIGH, conflict NONE; revenue is materialized into Zone B
(ORDER_VERIFIED only, RULE-003). Fail-gate FAIL-001 (revenue misuse) is the guard.
"""
from __future__ import annotations

from app.measurement.models.attribution_context import (
    ConflictStatus,
    EntryChannel,
    SourceConfidence,
)


def test_order_verified_full_source_traces_high_none(
    make_measurement_event, make_conversion, attribution_materializer, measurement_store
):
    event = make_measurement_event(
        "evt_full", event_code="ORDER_VERIFIED", page_id="p_home",
        campaign_id="camp_1", adset_id="ads_1", ad_id="ad_1", customer_id="cust_0001",
    )
    conv = make_conversion(
        "ORDER_VERIFIED", source_event_id="evt_full", revenue_value=250000.0,
        currency="VND", order_code="ORD_1",
    )
    outcome = attribution_materializer.materialize(
        event, conv, signals={"campaign_name": "C", "adset_name": "A", "ad_name": "D"}
    )
    ctx = outcome.context

    # full source resolved, unambiguous
    assert ctx.entry_channel is EntryChannel.FACEBOOK_AD
    assert ctx.source_confidence is SourceConfidence.HIGH
    assert ctx.conflict_status is ConflictStatus.NONE
    assert (ctx.campaign_id, ctx.adset_id, ctx.ad_id) == ("camp_1", "ads_1", "ad_1")
    assert (ctx.campaign_name, ctx.adset_name, ctx.ad_name) == ("C", "A", "D")
    # multi-model touches BOTH recorded (M6-OD-005 OPEN)
    assert ctx.first_touch_event_id == "evt_full" and ctx.last_touch_event_id == "evt_full"

    # trace to source: revenue materialized into Zone B (ORDER_VERIFIED, RULE-003)
    row = measurement_store.get_by_event_id("evt_full")
    assert row.revenue_value == 250000.0 and row.order_code == "ORD_1"
    assert row.attribution_context["campaign_id"] == "camp_1"
    assert outcome.changed is True

    # HIGH + NONE clears the RULE-009 data-quality bar, but is STILL not scale evidence: no model is
    # scale-authoritative while M6-OD-005 is OPEN (fail-closed).
    assert outcome.scale_evidence_eligible is True
    assert outcome.scale_evidence is False
