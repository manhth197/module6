"""Official smoke — slice M6.2L — M6-SMK-019 (proposed — HARDENING, owner review).

Authored by TESTER in M6-P2103 (mode=build, "do not yet run"); EXECUTED and its result recorded in M6-P2104
(TESTER_RUN -> 04-artifacts/test-reports/M6.2L/SMOKE_RESULTS.md). Closes audit item A3 (FIX_M6 2026-09-03).
Governance is immutable here: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below
flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (proposed additions row M6-SMK-019):

    Scenario (verbatim):   "ORDER_VERIFIED with a resolved ad source"
    Expected (verbatim):   "attribution_id present as a first-class key of AdsAttributionContext + handoff payload;
                           ORDER_VERIFIED traces attribution_id -> campaign"

attribution_id is the CTR-002 surrogate id (migration 0006) derived deterministically 1:1 from the measurement
event_id (no clock / randomness) — a re-materialize is a no-op. It is a governance ref, NOT PII, so it is not masked
(RULE-014); Module 6 still exposes no commission field (RULE-019). Reuses the shared conftest fixtures
(make_measurement_event, make_conversion, attribution_resolver, make_verified_row) and the coder's A3 leg pattern.
"""
from __future__ import annotations


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_019_attribution_id_first_class_and_traces_to_campaign(
    make_measurement_event, make_conversion, attribution_resolver, make_verified_row
):
    """M6-SMK-019 "ORDER_VERIFIED with a resolved ad source" -> "attribution_id present as a first-class key of
    AdsAttributionContext + handoff payload; ORDER_VERIFIED traces attribution_id -> campaign".

    An ORDER_VERIFIED event with a resolved ad source resolves to an AdsAttributionContext whose attribution_id is a
    first-class field present on BOTH handoff surfaces (to_public / as_stored); a materialized ORDER_VERIFIED row
    carries the attribution_id and its campaign together, so attribution_id traces to campaign.
    """
    event = make_measurement_event(
        "evt_smk019", event_code="ORDER_VERIFIED", page_id="p", campaign_id="camp_1", adset_id="a1", ad_id="ad1"
    )
    conv = make_conversion("ORDER_VERIFIED", source_event_id="evt_smk019")
    ctx = attribution_resolver.resolve(event, conv, signals={"campaign_name": "C", "adset_name": "A", "ad_name": "D"})

    assert ctx.attribution_id is not None and ctx.attribution_id.startswith("attr_")   # first-class field
    assert ctx.to_public()["attribution_id"] == ctx.attribution_id                     # on the public handoff
    assert ctx.as_stored()["attribution_id"] == ctx.attribution_id                     # on the stored handoff
    assert ctx.as_stored()["campaign_id"] == "camp_1"                                  # id and campaign travel together

    row = make_verified_row(
        "evt_smk019v", revenue=100000.0, order_code="ORD_SMK019",
        signals={"campaign_name": "C", "adset_name": "A", "ad_name": "D"},
        campaign_id="camp_9", adset_id="ads_9", ad_id="ad_9",
    )
    trace = row.attribution_context
    assert trace["attribution_id"] is not None            # the materialized ORDER_VERIFIED row carries the trace key
    assert trace["campaign_id"] == "camp_9"               # attribution_id -> row -> campaign


# --- negative / fail-closed: the trace key is deterministic (a re-materialize cannot fork it) -----
def test_smk_019_neg_attribution_id_is_deterministic_rematerialize_stable(
    make_measurement_event, make_conversion, attribution_resolver
):
    """Fail-closed idempotence: attribution_id is a pure derivation of the event_id (no clock / randomness), so
    resolving the same event twice yields the SAME id — a re-materialize cannot fork or duplicate the trace."""
    event = make_measurement_event(
        "evt_smk019det", event_code="ORDER_VERIFIED", page_id="p", campaign_id="c", adset_id="a", ad_id="d"
    )
    conv = make_conversion("ORDER_VERIFIED", source_event_id="evt_smk019det")
    first = attribution_resolver.resolve(event, conv).attribution_id
    second = attribution_resolver.resolve(event, conv).attribution_id
    assert first is not None and first == second


# --- negative / boundary: attribution_id is a governance ref (not PII, not masked); no commission --
def test_smk_019_neg_attribution_id_is_governance_ref_not_pii_and_no_commission(
    make_measurement_event, make_conversion, attribution_resolver
):
    """The attribution_id is a governance ref, NOT PII — it appears UNMASKED on the public handoff (equal to the raw
    id), and the payload still exposes no commission field (RULE-019). No raw phone/email/user-id anywhere."""
    event = make_measurement_event(
        "evt_smk019pii", event_code="ORDER_VERIFIED", page_id="p", campaign_id="c", adset_id="a", ad_id="d"
    )
    ctx = attribution_resolver.resolve(event, make_conversion("ORDER_VERIFIED", source_event_id="evt_smk019pii"))
    pub = ctx.to_public()
    assert pub["attribution_id"] == ctx.attribution_id     # governance ref -> not masked (RULE-014 scope)
    assert "commission" not in pub                         # RULE-019: Module 6 never computes commission
