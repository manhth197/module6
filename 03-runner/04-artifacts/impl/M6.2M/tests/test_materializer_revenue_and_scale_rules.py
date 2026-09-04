"""M6.2E leg 1: the materializer's load-bearing rules — revenue ONLY from ORDER_VERIFIED (RULE-003, FAIL-001);
LOW/HOLD (or any conflict) NEVER scale evidence (RULE-009); NO commission is computed (RULE-019, FAIL-004);
a re-materialize is idempotent.
"""
from __future__ import annotations

from app.measurement.models.attribution_context import ConflictStatus, EntryChannel, SourceConfidence


def test_revenue_only_from_order_verified(
    make_measurement_event, make_conversion, attribution_materializer, measurement_store
):
    event = make_measurement_event(
        "evt_nonrev", event_code="VIEW_LANDING", page_id="p",
        campaign_id="c1", adset_id="a1", ad_id="ad1",
    )
    # a conversion that (wrongly) carries revenue on a NON-verified event -> revenue must NOT be recorded
    conv = make_conversion(
        "VIEW_LANDING", source_event_id="evt_nonrev", revenue_value=500000.0,
        currency="VND", order_code="ORD_X",
    )
    outcome = attribution_materializer.materialize(event, conv)
    assert outcome.revenue_value is None
    assert measurement_store.get_by_event_id("evt_nonrev").revenue_value is None
    assert measurement_store.get_by_event_id("evt_nonrev").order_code is None


def test_multi_touch_conflict_is_low_and_not_scale(
    make_measurement_event, make_conversion, attribution_materializer
):
    event = make_measurement_event(
        "evt_multi", event_code="ORDER_VERIFIED", page_id="p",
        campaign_id="c1", adset_id="a1", ad_id="ad1",
    )
    conv = make_conversion(
        "ORDER_VERIFIED", source_event_id="evt_multi", revenue_value=100000.0,
        currency="VND", order_code="ORD_M",
    )
    # a competing DIAMOND_LINK source alongside the ad source -> ambiguous -> MULTI_TOUCH
    outcome = attribution_materializer.materialize(event, conv, signals={"diamond_id": "dia_1"})
    assert outcome.context.conflict_status is ConflictStatus.MULTI_TOUCH
    assert outcome.context.source_confidence is SourceConfidence.LOW
    assert outcome.scale_evidence_eligible is False and outcome.scale_evidence is False


def test_no_commission_recorded_for_diamond_referral(
    make_measurement_event, make_conversion, attribution_resolver
):
    event = make_measurement_event("evt_ref", event_code="ORDER_VERIFIED", page_id="p")
    conv = make_conversion("ORDER_VERIFIED", source_event_id="evt_ref")
    ctx = attribution_resolver.resolve(
        event, conv, signals={"referral_link_id": "ref_1", "diamond_id": "dia_9"}
    )
    # referral attribution is RECORDED ...
    assert ctx.referral_link_id == "ref_1" and ctx.diamond_id == "dia_9"
    assert ctx.entry_channel is EntryChannel.DIAMOND_LINK
    # ... but Module 6 NEVER computes a commission (RULE-019; Finance owns / FAIL-004)
    assert not hasattr(ctx, "commission")
    assert "commission" not in ctx.to_public()


def test_rematerialize_is_idempotent(
    make_measurement_event, make_conversion, attribution_materializer, measurement_store
):
    event = make_measurement_event(
        "evt_idem", event_code="ORDER_VERIFIED", page_id="p",
        campaign_id="c1", adset_id="a1", ad_id="ad1",
    )
    conv = make_conversion(
        "ORDER_VERIFIED", source_event_id="evt_idem", revenue_value=120000.0,
        currency="VND", order_code="ORD_I",
    )
    first = attribution_materializer.materialize(event, conv)
    second = attribution_materializer.materialize(event, conv)   # same inputs -> no overwrite
    assert first.changed is True and second.changed is False
    assert measurement_store.get_by_event_id("evt_idem").revenue_value == 120000.0
