"""Official smoke — slice M6.2E — M6-SMK-018 (proposed — HARDENING, owner review).

Authored by TESTER in M6-P1403 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1404
(TESTER_RUN -> 04-artifacts/test-reports/M6.2E/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (proposed additions row):

    Scenario (verbatim):   "Attribution correction attempted after ORDER_VERIFIED"
    Expected (verbatim):   "Direct mutation rejected; adjustment record created with actor, reason, audit,
                           evidence"

A materialized+verified Zone B is immutable (set-once, RULE-008): a DIRECT overwrite with a different value is
REJECTED by the store; the sanctioned correction is an audited AdjustmentRecord{actor, reason, audit_ref,
evidence_ref, proposed} appended to an append-only AdjustmentLog — the verified row is never silently
overwritten. `actor` is masked on export (RULE-014 / H02). `M6-SMK-018` is `proposed — HARDENING (owner
review)`; per the M6.2E done-gate leg 5 it is executed here (not waived). Reuses the shared conftest fixtures
(make_measurement_event, make_conversion, attribution_materializer, measurement_store, adjustment_log, audit).
"""
from __future__ import annotations

import pytest

from app.measurement.store.measurement_event_store import MeasurementStoreViolation


def _materialize_verified(make_measurement_event, make_conversion, materializer, event_id, revenue, order_code):
    event = make_measurement_event(
        event_id, event_code="ORDER_VERIFIED", page_id="p", campaign_id="c1", adset_id="a1", ad_id="ad1"
    )
    conv = make_conversion(
        "ORDER_VERIFIED", source_event_id=event_id, revenue_value=revenue, currency="VND", order_code=order_code
    )
    return materializer.materialize(event, conv)


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_018_post_verify_correction_is_adjustment_not_mutation(
    make_measurement_event, make_conversion, attribution_materializer, measurement_store, adjustment_log, audit
):
    """M6-SMK-018 "Attribution correction attempted after ORDER_VERIFIED" -> "Direct mutation rejected;
    adjustment record created with actor, reason, audit, evidence"."""
    _materialize_verified(make_measurement_event, make_conversion, attribution_materializer, "evt_ver", 250000.0, "ORD_9")
    assert measurement_store.get_by_event_id("evt_ver").revenue_value == 250000.0

    # (a) a DIRECT Zone-B overwrite with a DIFFERENT revenue is REJECTED (set-once, RULE-008)
    with pytest.raises(MeasurementStoreViolation):
        measurement_store.materialize(
            "evt_ver", attribution_context={"page_id": "p"}, revenue_value=300000.0,
            order_code="ORD_9", verified=True,
        )
    assert measurement_store.get_by_event_id("evt_ver").revenue_value == 250000.0   # untouched

    # (b) the sanctioned correction is an audited AdjustmentRecord — actor, reason, audit_ref, evidence_ref
    rec = attribution_materializer.request_adjustment(
        "evt_ver", actor="ops_admin", reason="late_refund_reconciliation",
        audit_ref="aud_1", evidence_ref="ev_1", proposed={"revenue_value": 300000.0},
        adjustment_log=adjustment_log,
    )
    assert rec.event_id == "evt_ver"
    assert (rec.actor, rec.reason, rec.audit_ref, rec.evidence_ref) == (
        "ops_admin", "late_refund_reconciliation", "aud_1", "ev_1"
    )
    assert rec.proposed["revenue_value"] == 300000.0
    assert len(adjustment_log) == 1
    assert adjustment_log.for_event("evt_ver")[0].reason == "late_refund_reconciliation"
    assert audit.find("ATTRIBUTION_ADJUSTMENT_RECORDED")

    # the verified row is STILL unchanged after the adjustment (never overwritten) ...
    assert measurement_store.get_by_event_id("evt_ver").revenue_value == 250000.0
    # ... and the exported adjustment masks the actor (RULE-014 / H02)
    assert rec.to_public()["actor"] != "ops_admin"


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_018_neg_adjustment_log_is_append_only(
    make_measurement_event, make_conversion, attribution_materializer, adjustment_log
):
    """The AdjustmentLog is append-only: a second correction for the same event APPENDS a new record — it never
    edits the first (a later correction is another appended overlay)."""
    _materialize_verified(make_measurement_event, make_conversion, attribution_materializer, "evt_two", 100000.0, "ORD_T")
    attribution_materializer.request_adjustment(
        "evt_two", actor="a1", reason="first", audit_ref="au1", evidence_ref="e1",
        proposed={"revenue_value": 110000.0}, adjustment_log=adjustment_log,
    )
    attribution_materializer.request_adjustment(
        "evt_two", actor="a2", reason="second", audit_ref="au2", evidence_ref="e2",
        proposed={"revenue_value": 120000.0}, adjustment_log=adjustment_log,
    )
    recs = adjustment_log.for_event("evt_two")
    assert len(recs) == 2
    assert recs[0].reason == "first" and recs[1].reason == "second"   # first untouched, second appended


def test_smk_018_neg_re_materialize_same_inputs_is_idempotent_no_op(
    make_measurement_event, make_conversion, attribution_materializer, measurement_store
):
    """Set-once permits an idempotent REPLAY: re-materializing the SAME verified inputs is a no-op (changed
    False) and leaves the revenue unchanged — it is a DIFFERENT value that the set-once guard rejects, not a
    re-run."""
    first = _materialize_verified(make_measurement_event, make_conversion, attribution_materializer, "evt_idem", 77000.0, "ORD_I")
    assert first.changed is True
    # re-materialize the SAME event_id with the SAME inputs -> idempotent no-op (deterministic resolver + store)
    second = _materialize_verified(make_measurement_event, make_conversion, attribution_materializer, "evt_idem", 77000.0, "ORD_I")
    assert second.changed is False, "a same-input re-materialize is an idempotent no-op (set-once replay-safe)"
    assert measurement_store.get_by_event_id("evt_idem").revenue_value == 77000.0


# --- positive control: proves set-once is PER-ROW (the store is not globally frozen) --------------
def test_smk_018_control_set_once_is_per_row(
    make_measurement_event, make_conversion, attribution_materializer, measurement_store
):
    """Control (non-vacuity): materializing a DIFFERENT verified event succeeds and does not touch the first —
    the set-once guard protects each verified row, it does not freeze the whole store."""
    _materialize_verified(make_measurement_event, make_conversion, attribution_materializer, "evt_a", 10000.0, "ORD_A")
    _materialize_verified(make_measurement_event, make_conversion, attribution_materializer, "evt_b", 20000.0, "ORD_B")
    assert measurement_store.get_by_event_id("evt_a").revenue_value == 10000.0
    assert measurement_store.get_by_event_id("evt_b").revenue_value == 20000.0
