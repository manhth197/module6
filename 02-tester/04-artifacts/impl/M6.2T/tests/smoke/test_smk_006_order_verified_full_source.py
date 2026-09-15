"""Official smoke — slice M6.2E — M6-SMK-006 (doc ADS-P0-006).

Authored by TESTER in M6-P1403 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1404
(TESTER_RUN -> 04-artifacts/test-reports/M6.2E/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF, SCALE_MODEL_RATIFIED=False — nothing
below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 406):

    Kịch bản (verbatim):          "ORDER_VERIFIED có campaign/adset/ad đầy đủ"
    Kết quả phải đạt (verbatim):  "ROAS/CPA/AOV dashboard cập nhật"

A fully-sourced ORDER_VERIFIED resolves to a HIGH-confidence, no-conflict attribution snapshot and materializes
revenue + full ad hierarchy into Zone B — the exact data the ROAS/CPA/AOV dashboard reads (the dashboard RENDER
is M6.2F; M6.2E proves the attribution + revenue input that updates it). Revenue is materialized ONLY for an
ORDER_VERIFIED (RULE-003, guards FAIL-001). RULE-008/009. All ids synthetic; psid (when present) masked on
export. Reuses the shared conftest fixtures (make_measurement_event, make_conversion, attribution_materializer,
measurement_store).
"""
from __future__ import annotations

from app import config
from app.measurement.models.attribution_context import (
    ConflictStatus,
    EntryChannel,
    SourceConfidence,
)


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_006_order_verified_full_source_traces_and_feeds_dashboard(
    make_measurement_event, make_conversion, attribution_materializer, measurement_store
):
    """M6-SMK-006 "ORDER_VERIFIED có campaign/adset/ad đầy đủ" -> "ROAS/CPA/AOV dashboard cập nhật".

    A full campaign/adset/ad + page resolves HIGH / NONE and materializes revenue + the full ad hierarchy into
    Zone B — the ROAS/CPA/AOV dashboard input.
    """
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

    assert ctx.entry_channel is EntryChannel.FACEBOOK_AD
    assert ctx.source_confidence is SourceConfidence.HIGH
    assert ctx.conflict_status is ConflictStatus.NONE
    assert (ctx.campaign_id, ctx.adset_id, ctx.ad_id) == ("camp_1", "ads_1", "ad_1")
    assert (ctx.campaign_name, ctx.adset_name, ctx.ad_name) == ("C", "A", "D")

    # revenue + full attribution materialized into Zone B -> the ROAS/CPA/AOV dashboard input
    row = measurement_store.get_by_event_id("evt_full")
    assert row.revenue_value == 250000.0 and row.order_code == "ORD_1"
    assert row.attribution_context["campaign_id"] == "camp_1"
    assert row.attribution_context["adset_id"] == "ads_1"
    assert row.attribution_context["ad_id"] == "ad_1"
    assert outcome.changed is True


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_006_neg_incomplete_ad_path_is_medium_not_high(
    make_measurement_event, make_conversion, attribution_materializer, measurement_store
):
    """A single FACEBOOK_AD channel that is NOT fully identified (campaign only, no adset/ad) grades MEDIUM, not
    HIGH -> not scale-eligible; revenue is still stored (a verified order is never dropped)."""
    event = make_measurement_event("evt_partial", event_code="ORDER_VERIFIED", page_id="p", campaign_id="camp_1")
    conv = make_conversion(
        "ORDER_VERIFIED", source_event_id="evt_partial", revenue_value=50000.0, currency="VND", order_code="ORD_P"
    )
    outcome = attribution_materializer.materialize(event, conv)
    assert outcome.context.entry_channel is EntryChannel.FACEBOOK_AD
    assert outcome.context.source_confidence is SourceConfidence.MEDIUM
    assert outcome.context.conflict_status is ConflictStatus.NONE
    assert outcome.scale_evidence_eligible is False              # MEDIUM never clears the RULE-009 bar
    assert measurement_store.get_by_event_id("evt_partial").revenue_value == 50000.0


def test_smk_006_neg_non_verified_conversion_records_no_revenue(
    make_measurement_event, make_conversion, attribution_materializer, measurement_store
):
    """Revenue is materialized ONLY for ORDER_VERIFIED (RULE-003, FAIL-001): a non-verified conversion (even one
    carrying a revenue_value) records attribution but NO revenue / order_code."""
    event = make_measurement_event(
        "evt_nonver", event_code="VIEW_LANDING", page_id="p", campaign_id="camp_1", adset_id="ads_1", ad_id="ad_1"
    )
    conv = make_conversion(
        "VIEW_LANDING", source_event_id="evt_nonver", revenue_value=250000.0, currency="VND", order_code="ORD_X"
    )
    attribution_materializer.materialize(event, conv)
    row = measurement_store.get_by_event_id("evt_nonver")
    assert row.revenue_value is None, "quote/cart/non-verified never carries revenue (FAIL-001)"
    assert row.order_code is None


# --- positive control: proves the fail-closed forward gate (not vacuous) --------------------------
def test_smk_006_control_full_source_eligible_but_not_scale_evidence_while_model_open(
    make_measurement_event, make_conversion, attribution_materializer
):
    """Fail-closed forward gate: a full-source HIGH/NONE row CLEARS the RULE-009 data-quality bar (eligible) but
    is STILL not scale evidence while no attribution model is owner-ratified (M6-OD-005 OPEN ->
    SCALE_MODEL_RATIFIED False). Eligibility is necessary, not sufficient."""
    event = make_measurement_event(
        "evt_scale", event_code="ORDER_VERIFIED", page_id="p", campaign_id="c", adset_id="a", ad_id="d"
    )
    conv = make_conversion(
        "ORDER_VERIFIED", source_event_id="evt_scale", revenue_value=10000.0, currency="VND", order_code="ORD_S"
    )
    outcome = attribution_materializer.materialize(
        event, conv, signals={"campaign_name": "C", "adset_name": "A", "ad_name": "D"}
    )
    assert outcome.scale_evidence_eligible is True
    assert outcome.scale_evidence is False
    assert config.SCALE_MODEL_RATIFIED is False
