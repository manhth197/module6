"""Official smoke — slice M6.2E — M6-SMK-007 (doc ADS-P0-007).

Authored by TESTER in M6-P1403 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1404
(TESTER_RUN -> 04-artifacts/test-reports/M6.2E/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF, SCALE_MODEL_RATIFIED=False.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 407):

    Kịch bản (verbatim):          "ORDER_VERIFIED thiếu source"
    Kết quả phải đạt (verbatim):  "Revenue vẫn lưu, attribution confidence LOW/HOLD"

A verified order whose source is missing (or conflicting) STILL records revenue (a verified order is never
dropped), but the snapshot degrades to source_confidence=LOW and a non-NONE conflict_status, and is flagged
NEVER scale evidence (RULE-009). RULE-008/009, guards FAIL-001. All ids synthetic. Reuses the shared conftest
fixtures (make_measurement_event, make_conversion, attribution_materializer, measurement_store).
"""
from __future__ import annotations

from app.measurement.models.attribution_context import (
    ConflictStatus,
    EntryChannel,
    SourceConfidence,
)


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_007_missing_source_stores_revenue_but_low_hold_not_scale(
    make_measurement_event, make_conversion, attribution_materializer, measurement_store
):
    """M6-SMK-007 "ORDER_VERIFIED thiếu source" -> "Revenue vẫn lưu, attribution confidence LOW/HOLD".

    A verified order with NO source resolves conflict=MISSING_SOURCE / confidence=LOW / channel=DIRECT; revenue
    is still stored, but the row is never scale evidence.
    """
    event = make_measurement_event("evt_nosrc", event_code="ORDER_VERIFIED", page_id="")
    conv = make_conversion(
        "ORDER_VERIFIED", source_event_id="evt_nosrc", revenue_value=99000.0, currency="VND", order_code="ORD_2"
    )
    outcome = attribution_materializer.materialize(event, conv)
    ctx = outcome.context

    assert ctx.conflict_status is ConflictStatus.MISSING_SOURCE
    assert ctx.source_confidence is SourceConfidence.LOW
    assert ctx.entry_channel is EntryChannel.DIRECT

    # revenue is STILL stored (never dropped for a verified order) ...
    row = measurement_store.get_by_event_id("evt_nosrc")
    assert row.revenue_value == 99000.0 and row.order_code == "ORD_2"

    # ... but NEVER scale evidence (RULE-009), on BOTH the data-quality bar and the ratified-model gate
    assert ctx.is_scale_evidence_eligible() is False
    assert outcome.scale_evidence_eligible is False
    assert outcome.scale_evidence is False


# --- negative / fail-closed companions: "conflicting sources degrade to LOW/HOLD" ------------------
def test_smk_007_neg_conflicting_multi_touch_is_low_not_scale(
    make_measurement_event, make_conversion, attribution_materializer, measurement_store
):
    """More than one entry channel (an ad AND a live source) is a MULTI_TOUCH conflict -> LOW, not scale
    evidence; revenue is still stored."""
    event = make_measurement_event(
        "evt_multi", event_code="ORDER_VERIFIED", page_id="p", campaign_id="camp_1", live_session_id="ls_1"
    )
    conv = make_conversion(
        "ORDER_VERIFIED", source_event_id="evt_multi", revenue_value=120000.0, currency="VND", order_code="ORD_M"
    )
    outcome = attribution_materializer.materialize(event, conv)
    assert outcome.context.conflict_status is ConflictStatus.MULTI_TOUCH
    assert outcome.context.source_confidence is SourceConfidence.LOW
    assert outcome.scale_evidence_eligible is False
    assert measurement_store.get_by_event_id("evt_multi").revenue_value == 120000.0


def test_smk_007_neg_duplicate_risk_signal_is_low_not_scale(
    make_measurement_event, make_conversion, attribution_materializer
):
    """An explicit duplicate-risk signal fails closed -> conflict=DUPLICATE_RISK, confidence=LOW, not scale
    evidence (a possible double count is never HIGH evidence, FAIL-001)."""
    event = make_measurement_event(
        "evt_dup", event_code="ORDER_VERIFIED", page_id="p", campaign_id="c", adset_id="a", ad_id="d"
    )
    conv = make_conversion(
        "ORDER_VERIFIED", source_event_id="evt_dup", revenue_value=10000.0, currency="VND", order_code="ORD_D"
    )
    outcome = attribution_materializer.materialize(event, conv, signals={"duplicate_risk": True})
    assert outcome.context.conflict_status is ConflictStatus.DUPLICATE_RISK
    assert outcome.context.source_confidence is SourceConfidence.LOW
    assert outcome.scale_evidence_eligible is False


# --- positive control: proves LOW is source-caused, not a blanket refusal --------------------------
def test_smk_007_control_clean_full_source_is_eligible(
    make_measurement_event, make_conversion, attribution_materializer
):
    """Control (non-vacuity): a clean full single-source order IS eligible (HIGH/NONE) — proving the LOW verdict
    above is caused by the missing/conflicting source, not by everything being held."""
    event = make_measurement_event(
        "evt_clean", event_code="ORDER_VERIFIED", page_id="p", campaign_id="c", adset_id="a", ad_id="d"
    )
    conv = make_conversion(
        "ORDER_VERIFIED", source_event_id="evt_clean", revenue_value=10000.0, currency="VND", order_code="ORD_C"
    )
    outcome = attribution_materializer.materialize(
        event, conv, signals={"campaign_name": "C", "adset_name": "A", "ad_name": "D"}
    )
    assert outcome.scale_evidence_eligible is True
