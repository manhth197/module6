"""M6.2E leg 1 / M6-SMK-018 (proposed): a post-verify correction is NOT a direct Zone-B mutation. The store's
set-once guard REJECTS an overwrite of verified revenue (RULE-008); the sanctioned correction is an audited
AdjustmentRecord{actor, reason, audit_ref, evidence_ref}. Verified revenue is never silently overwritten.
"""
from __future__ import annotations

import pytest

from app.measurement.store.measurement_event_store import MeasurementStoreViolation


def test_post_verify_correction_is_adjustment_not_mutation(
    make_measurement_event, make_conversion, attribution_materializer, measurement_store, adjustment_log, audit
):
    event = make_measurement_event(
        "evt_ver", event_code="ORDER_VERIFIED", page_id="p",
        campaign_id="c1", adset_id="a1", ad_id="ad1",
    )
    conv = make_conversion(
        "ORDER_VERIFIED", source_event_id="evt_ver", revenue_value=250000.0,
        currency="VND", order_code="ORD_9",
    )
    attribution_materializer.materialize(event, conv)
    assert measurement_store.get_by_event_id("evt_ver").revenue_value == 250000.0

    # (a) a DIRECT Zone-B overwrite with a DIFFERENT revenue is rejected by the store (set-once, RULE-008)
    with pytest.raises(MeasurementStoreViolation):
        measurement_store.materialize(
            "evt_ver", attribution_context={"page_id": "p"}, revenue_value=300000.0,
            order_code="ORD_9", verified=True,
        )
    assert measurement_store.get_by_event_id("evt_ver").revenue_value == 250000.0   # untouched

    # (b) the sanctioned correction is an AdjustmentRecord (audited), never a mutation
    rec = attribution_materializer.request_adjustment(
        "evt_ver", actor="ops_admin", reason="late_refund_reconciliation",
        audit_ref="aud_1", evidence_ref="ev_1", proposed={"revenue_value": 300000.0},
        adjustment_log=adjustment_log,
    )
    assert rec.event_id == "evt_ver" and rec.proposed["revenue_value"] == 300000.0
    assert len(adjustment_log) == 1
    assert adjustment_log.for_event("evt_ver")[0].reason == "late_refund_reconciliation"
    assert audit.find("ATTRIBUTION_ADJUSTMENT_RECORDED")

    # the verified row is STILL unchanged after the adjustment (never overwritten)
    assert measurement_store.get_by_event_id("evt_ver").revenue_value == 250000.0

    # the exported adjustment masks the actor (RULE-014 / H02)
    assert rec.to_public()["actor"] != "ops_admin"
