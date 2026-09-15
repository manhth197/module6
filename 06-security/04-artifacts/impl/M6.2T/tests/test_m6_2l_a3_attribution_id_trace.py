"""M6.2L leg 1 / M6-SMK-019 / RULE-014: `attribution_id` (A3) is a first-class key of AdsAttributionContext and its
handoff payload (to_public / as_stored); an ORDER_VERIFIED row traces attribution_id -> campaign; the id is
DETERMINISTIC (1:1 with the measurement event_id — migration 0006 surrogate), so a re-materialize is a no-op.
attribution_id is a governance ref (NOT PII) -> it is not masked, and there is still no commission field (RULE-019).
"""
from __future__ import annotations


def test_attribution_id_is_first_class_and_in_handoff_payload(
    make_measurement_event, make_conversion, attribution_resolver
):
    event = make_measurement_event(
        "evt_a3", event_code="ORDER_VERIFIED", page_id="p", campaign_id="camp_1", adset_id="a1", ad_id="ad1"
    )
    conv = make_conversion("ORDER_VERIFIED", source_event_id="evt_a3")
    ctx = attribution_resolver.resolve(event, conv, signals={"campaign_name": "C", "adset_name": "A", "ad_name": "D"})

    # first-class field + present on BOTH handoff surfaces
    assert ctx.attribution_id is not None and ctx.attribution_id.startswith("attr_")
    assert ctx.to_public()["attribution_id"] == ctx.attribution_id
    assert ctx.as_stored()["attribution_id"] == ctx.attribution_id
    # trace: the id and its campaign travel together on the payload -> id -> campaign
    assert ctx.as_stored()["campaign_id"] == "camp_1"
    # governance ref, not PII (not masked); no commission leak (RULE-019)
    assert "commission" not in ctx.to_public()


def test_order_verified_row_traces_attribution_id_to_campaign(make_verified_row):
    row = make_verified_row(
        "evt_a3v", revenue=100000.0, order_code="ORD_A3",
        signals={"campaign_name": "C", "adset_name": "A", "ad_name": "D"},
        campaign_id="camp_9", adset_id="ads_9", ad_id="ad_9",
    )
    ctx = row.attribution_context
    assert ctx["attribution_id"] is not None            # materialized ORDER_VERIFIED row carries the trace key
    assert ctx["campaign_id"] == "camp_9"               # attribution_id -> row -> campaign


def test_attribution_id_is_deterministic_so_rematerialize_is_stable(
    make_measurement_event, make_conversion, attribution_resolver
):
    event = make_measurement_event(
        "evt_det", event_code="ORDER_VERIFIED", page_id="p", campaign_id="c", adset_id="a", ad_id="d"
    )
    conv = make_conversion("ORDER_VERIFIED", source_event_id="evt_det")
    first = attribution_resolver.resolve(event, conv).attribution_id
    second = attribution_resolver.resolve(event, conv).attribution_id
    assert first is not None and first == second        # pure derivation (no clock / randomness)
