"""Official smoke — slice M6.2Q — M6-SMK-029 (proposed — HARDENING, owner review): ads-spend maker-checker +
live-session binding + CPA/ROAS-by-session (A5).

Authored by TESTER in M6-P2503 (mode=build, "do not yet run"); EXECUTED + recorded in M6-P2504
(-> 04-artifacts/test-reports/M6.2Q/SMOKE_RESULTS.md). Governance is immutable here: global_gateway_state=BLOCKED,
production_flag=OFF, external_send=OFF — nothing below flips a flag, calls no real Meta network / Marketing API, and
uses only mock in-test spend. Spend is campaign-level (campaign_id), NOT PII; actors are masked on export.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (proposed additions row M6-SMK-029):

    Scenario (verbatim):   "A spend import (mock CSV rows keyed by campaign_id) approved by a DISTINCT checker + a
                           live-session-ads-binding; a self-approved import; a live_session with spend but no verified
                           order (A5)"
    Expected (verbatim):   "maker-checker enforced (self-approve rejected; only APPROVED imports materialize);
                           CPA-by-live_session = spend / verified-order-count + ROAS = verified-revenue / spend
                           computed per session from approved spend; spend outside a session window → daily total (not
                           attributed to a session); no verified order → CPA fail-closed (no div-by-zero), ROAS=0; no
                           PII, external_send OFF"

RULE-003 (revenue only from ORDER_VERIFIED) / RULE-015 (no self-cert); FAIL-007. Reuses the coder's M6.2Q leg
patterns (import gate/materializer, binding store, SessionRoasReader) + the shared conftest fixtures (audit,
measurement_store, make_verified_row, make_measurement_event). All ids synthetic; PII markers assembled at runtime.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app import config
from app.measurement.ads_spend.import_gate import AdsSpendImportGate, AdsSpendImportGateViolation
from app.measurement.ads_spend.materializer import AdsSpendMaterializer
from app.measurement.dashboard.session_roas import SessionRoasReader
from app.measurement.models.ads_spend_import import (
    AdsSpendImport,
    AdsSpendImportDecision,
    AdsSpendImportRow,
    AdsSpendImportState,
    ImportDecisionKind,
)
from app.measurement.models.live_session_ads_binding import LiveSessionAdsBinding
from app.measurement.store.ads_spend_import_store import AdsSpendImportStore
from app.measurement.store.ads_spend_record_store import AdsSpendRecordStore
from app.measurement.store.live_session_ads_binding_store import LiveSessionAdsBindingStore

# ls_1 window: derived [min,max event_ts]; the in-window spend/quote sit between the two verified orders.
T0 = datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc)     # ls_1 window start (verified order 1)
TQ = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)    # in-window quote + spend_date
T1 = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)    # ls_1 window end (verified order 2)
T2 = datetime(2026, 9, 2, 9, 0, 0, tzinfo=timezone.utc)     # ls_2 (zero-verified) single point
TOUT = datetime(2026, 9, 5, 9, 0, 0, tzinfo=timezone.utc)   # outside every session window


def _stack(audit):
    import_store = AdsSpendImportStore()
    record_store = AdsSpendRecordStore()
    gate = AdsSpendImportGate(import_store, audit)
    worker = AdsSpendMaterializer(import_store, record_store, audit)
    return import_store, record_store, gate, worker


def _import(import_id="asi_1", *, campaign_id="camp_1", spend=100000.0, spend_date=TQ, uploaded_by="maker_ops"):
    rows = (AdsSpendImportRow(campaign_id=campaign_id, spend_value=spend, spend_date=spend_date),)
    return AdsSpendImport(import_id=import_id, rows=rows, window_start=T0, window_end=T1, uploaded_by=uploaded_by)


def _decision(kind="APPROVE", actor="checker_ops"):
    return AdsSpendImportDecision(actor=actor, reason="pilot spend reviewed", audit_ref="aud_1",
                                  evidence_ref="ev_1", decision=ImportDecisionKind(kind))


# --- primary smoke: scenario verbatim, END-TO-END (distinct-checker approve -> materialize -> bind -> CPA/ROAS) ---
def test_smk_029_distinct_checker_approve_materialize_bind_session_cpa_roas(
    audit, measurement_store, make_verified_row, make_measurement_event
):
    """M6-SMK-029 "A spend import (mock CSV rows keyed by campaign_id) approved by a DISTINCT checker + a
    live-session-ads-binding; ..." -> "maker-checker enforced (... only APPROVED imports materialize); CPA-by-
    live_session = spend / verified-order-count + ROAS = verified-revenue / spend computed per session ...".

    A mock-CSV spend import for camp_1 enters PROPOSED; a DISTINCT checker approves it; the worker materializes ONLY
    the APPROVED import into a campaign-level spend record; a binding maps camp_1 -> ls_1; and SessionRoasReader
    computes CPA = spend / verified-order-count and ROAS = verified-revenue / spend for ls_1 from that approved spend.
    The record is campaign-level (adset/ad None -> .mapped False) yet IS included — the sum gates on the binding.
    """
    import_store, record_store, gate, worker = _stack(audit)
    imp = gate.propose(_import(campaign_id="camp_1", spend=100000.0, spend_date=TQ, uploaded_by="maker_ops"))
    assert imp.state is AdsSpendImportState.PROPOSED
    assert worker.run_once() == [] and len(record_store) == 0             # nothing materializes while PROPOSED

    approved = gate.record_decision("asi_1", _decision("APPROVE", actor="checker_ops"))   # maker != checker
    assert approved.state is AdsSpendImportState.APPROVED
    assert worker.run_once() == ["asi_1"]                                # ONLY the APPROVED import materializes
    rec = record_store.all()[0]
    assert rec.campaign_id == "camp_1" and rec.amount == 100000.0 and rec.mapped is False   # campaign-level

    binding = LiveSessionAdsBindingStore()
    binding.bind(LiveSessionAdsBinding(live_session_id="ls_1", primary_campaign_id="camp_1"))

    make_verified_row("evt_v1", revenue=250000.0, order_code="ORD1", live_session_id="ls_1", event_ts=T0)
    make_verified_row("evt_v2", revenue=250000.0, order_code="ORD2", live_session_id="ls_1", event_ts=T1)
    make_measurement_event("evt_q1", event_code="QUOTE_SENT", live_session_id="ls_1", event_ts=TQ)   # RULE-003: 0

    s1 = SessionRoasReader(measurement_store, record_store.all(), binding).for_session("ls_1")
    assert s1.session_spend == 100000.0            # bound + in-window campaign-level spend included (not .mapped-gated)
    assert s1.verified_orders == 2                 # the in-window QUOTE_SENT contributes 0 (RULE-003 lock)
    assert s1.verified_revenue == 500000.0
    assert s1.cpa == 50000.0                        # 100000 / 2
    assert s1.roas == 5.0                           # 500000 / 100000
    assert config.EXTERNAL_SEND == "OFF"            # no egress opened by this slice


# --- negative / four-eyes: a self-approved import is REFUSED and never materializes ----------------
def test_smk_029_neg_self_approve_rejected_never_materializes(audit):
    """"maker-checker enforced (self-approve rejected ...)": an APPROVE whose checker equals the maker (same actor)
    raises AdsSpendImportGateViolation, the import stays PROPOSED, and the worker materializes nothing."""
    import_store, record_store, gate, worker = _stack(audit)
    gate.propose(_import(uploaded_by="maker_ops"))
    with pytest.raises(AdsSpendImportGateViolation):
        gate.record_decision("asi_1", _decision("APPROVE", actor="maker_ops"))   # maker == checker
    assert import_store.get("asi_1").state is AdsSpendImportState.PROPOSED
    assert worker.run_once() == [] and len(record_store) == 0


# --- negative / fail-closed: a session with spend but ZERO verified orders -> CPA None, ROAS 0.0 ---
def test_smk_029_neg_zero_verified_session_cpa_failclosed_roas_zero(
    audit, measurement_store, make_verified_row, make_measurement_event
):
    """"no verified order → CPA fail-closed (no div-by-zero), ROAS=0": camp_2 approved spend bound to ls_2, whose
    only event is a QUOTE_SENT (zero ORDER_VERIFIED) -> CPA is None (spend / 0 guarded, no divide-by-zero) and ROAS
    is 0.0 (wasted spend: 0 verified revenue / spend>0)."""
    import_store, record_store, gate, worker = _stack(audit)
    gate.propose(_import("asi_2", campaign_id="camp_2", spend=60000.0, spend_date=T2, uploaded_by="maker_ops"))
    gate.record_decision("asi_2", _decision("APPROVE", actor="checker_ops"))
    worker.run_once()

    binding = LiveSessionAdsBindingStore()
    binding.bind(LiveSessionAdsBinding(live_session_id="ls_2", primary_campaign_id="camp_2"))
    make_measurement_event("evt_q2", event_code="QUOTE_SENT", live_session_id="ls_2", event_ts=T2)   # 0 verified

    s2 = SessionRoasReader(measurement_store, record_store.all(), binding).for_session("ls_2")
    assert s2.session_spend == 60000.0
    assert s2.verified_orders == 0
    assert s2.cpa is None                           # fail-closed: spend / 0 -> None (no divide-by-zero)
    assert s2.roas == 0.0                           # 0.0 verified revenue / spend>0 -> 0.0


# --- negative: spend outside a session window / on an unbound campaign -> daily total --------------
def test_smk_029_neg_spend_outside_window_or_unbound_goes_to_daily_total(
    audit, measurement_store, make_verified_row, make_measurement_event
):
    """"spend outside a session window → daily total (not attributed to a session)": a camp_1 spend record whose
    spend_date is OUTSIDE the ls_1 window, plus an UNBOUND-campaign record, are excluded from any session and land in
    daily_total() instead."""
    from app.measurement.dashboard.data_mart import AdsSpendRecord
    make_verified_row("evt_v1", revenue=250000.0, order_code="ORD1", live_session_id="ls_1", event_ts=T0)
    make_verified_row("evt_v2", revenue=250000.0, order_code="ORD2", live_session_id="ls_1", event_ts=T1)
    binding = LiveSessionAdsBindingStore()
    binding.bind(LiveSessionAdsBinding(live_session_id="ls_1", primary_campaign_id="camp_1"))
    records = [
        AdsSpendRecord(amount=100000.0, campaign_id="camp_1", spend_date=TQ),      # in ls_1 window -> session
        AdsSpendRecord(amount=50000.0, campaign_id="camp_1", spend_date=TOUT),     # camp_1 bound but OUT of window
        AdsSpendRecord(amount=30000.0, campaign_id="camp_unbound", spend_date=TQ), # unbound campaign
    ]
    reader = SessionRoasReader(measurement_store, records, binding)
    assert reader.for_session("ls_1").session_spend == 100000.0    # only the in-window record is session-attributed
    assert reader.daily_total() == 80000.0                          # 50000 out-of-window + 30000 unbound


# --- negative / PII-safe: no raw PII from the untrusted checker free-text reaches the audit trail --
def test_smk_029_neg_no_raw_pii_from_checker_reaches_audit(audit):
    """"no PII": the checker's free-text reason / audit_ref is untrusted; a PII-shaped value in it never reaches the
    audit trail raw, yet the decision is still audited (machine-safe). PII markers assembled at runtime."""
    import_store, record_store, gate, worker = _stack(audit)
    gate.propose(_import(uploaded_by="maker_ops"))
    pii_phone = "0" + "9" + "12" + "345" + "678"          # a VN-phone-shaped value (synthetic, runtime-assembled)
    pii_id = "ord" + "_" + "100" + "001"                  # an order-id-shaped value
    gate.record_decision(
        "asi_1",
        AdsSpendImportDecision(actor="checker_ops", reason="call " + pii_phone, audit_ref=pii_id,
                               evidence_ref="e1", decision=ImportDecisionKind.APPROVE),
    )
    blob = " ".join(f"{r.action} {r.reason} {r.subject_masked} {r.detail}" for r in audit.records)
    assert pii_phone not in blob, "raw phone must never reach the audit trail"
    assert pii_id not in blob, "raw id-ref must never reach the audit trail"
    assert audit.find("ADS_SPEND_IMPORT_APPROVED")        # the decision was still audited
