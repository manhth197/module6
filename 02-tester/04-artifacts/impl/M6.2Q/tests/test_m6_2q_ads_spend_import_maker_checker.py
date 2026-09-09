"""M6.2Q leg 1 / M6-OD-016 / SMK-029 / RULE-015 / FAIL-007: ads_spend_import maker-checker + materialize worker.

An import enters PROPOSED; a DISTINCT checker (maker != checker) moves it to APPROVED; a self-approve /
single-actor / missing-checker approve is REFUSED (four-eyes); the worker materializes ONLY APPROVED imports (a
PROPOSED / REJECTED import materializes nothing); a second materialize is an idempotent no-op; and no raw PII from
the untrusted checker free-text reaches the audit trail. STAGED (mock CSV): no Meta network / Marketing API / new
secret; spend is campaign-level (campaign_id), not PII; posture BLOCKED/OFF/OFF unchanged.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.api.ads_spend_imports import (
    AdsSpendImportDeps,
    handle_import_create,
    handle_import_decision,
    handle_import_materialize,
)
from app.measurement.ads_spend.import_gate import AdsSpendImportGate, AdsSpendImportGateViolation
from app.measurement.ads_spend.materializer import AdsSpendMaterializer
from app.measurement.models.ads_spend_import import (
    AdsSpendImport,
    AdsSpendImportDecision,
    AdsSpendImportRow,
    AdsSpendImportState,
    ImportDecisionKind,
)
from app.measurement.store.ads_spend_import_store import AdsSpendImportStore
from app.measurement.store.ads_spend_record_store import AdsSpendRecordStore

D0 = datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc)
D1 = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)


def _import(import_id="asi_1", uploaded_by="maker_ops"):
    rows = (AdsSpendImportRow(campaign_id="camp_1", spend_value=100000.0, spend_date=D0),)
    return AdsSpendImport(import_id=import_id, rows=rows, window_start=D0, window_end=D1, uploaded_by=uploaded_by)


def _stack(audit=None):
    import_store = AdsSpendImportStore()
    record_store = AdsSpendRecordStore()
    gate = AdsSpendImportGate(import_store, audit)
    worker = AdsSpendMaterializer(import_store, record_store, audit)
    return import_store, record_store, gate, worker


def _decision(kind="APPROVE", actor="checker_ops"):
    return AdsSpendImportDecision(actor=actor, reason="pilot spend reviewed", audit_ref="aud_1",
                                  evidence_ref="ev_1", decision=ImportDecisionKind(kind))


# --- lifecycle: PROPOSED -> distinct checker APPROVES -> worker materializes -----------------------
def test_distinct_checker_approves_and_only_approved_materializes(audit):
    import_store, record_store, gate, worker = _stack(audit)
    imp = gate.propose(_import())
    assert imp.state is AdsSpendImportState.PROPOSED
    assert len(record_store) == 0                                  # nothing materialized while PROPOSED

    worker.run_once()
    assert len(record_store) == 0                                  # a PROPOSED import materializes NOTHING

    approved = gate.record_decision("asi_1", _decision("APPROVE", actor="checker_ops"))
    assert approved.state is AdsSpendImportState.APPROVED
    assert approved.decided_by == "checker_ops"

    done = worker.run_once()
    assert done == ["asi_1"]
    recs = record_store.all()
    assert len(recs) == 1
    assert recs[0].campaign_id == "camp_1" and recs[0].amount == 100000.0
    # campaign-level: adset/ad are None -> .mapped is False (leg-3 gates on the BINDING, never .mapped)
    assert recs[0].adset_id is None and recs[0].ad_id is None and recs[0].mapped is False
    assert recs[0].spend_date == D0

    # idempotent: a re-run materializes nothing new (set-once)
    assert worker.run_once() == []
    assert len(record_store.all()) == 1


# --- four-eyes: a self-approve / single-actor approve is REFUSED -----------------------------------
def test_self_approve_is_rejected(audit):
    import_store, record_store, gate, worker = _stack(audit)
    gate.propose(_import(uploaded_by="same_actor"))
    with pytest.raises(AdsSpendImportGateViolation):
        gate.record_decision("asi_1", _decision("APPROVE", actor="same_actor"))     # maker == checker
    assert import_store.get("asi_1").state is AdsSpendImportState.PROPOSED           # still not approved
    worker.run_once()
    assert len(record_store) == 0                                                    # never materializes


@pytest.mark.parametrize("checker", ["Maker_Ops", "maker_ops ", " maker_ops", "MAKER_OPS", "  "])
def test_self_approve_alias_is_rejected(audit, checker):
    """Adversarial red-team regression: the four-eyes distinctness test is CANONICALIZED (strip + casefold), so a
    case/whitespace alias of the maker's own ref cannot self-approve, and a whitespace-only checker is refused —
    the raw `==` guard previously let `Maker_Ops` / `maker_ops ` / ` ` reach APPROVED + materialize."""
    import_store, record_store, gate, worker = _stack(audit)
    gate.propose(_import(uploaded_by="maker_ops"))
    with pytest.raises(AdsSpendImportGateViolation):
        gate.record_decision("asi_1", _decision("APPROVE", actor=checker))
    assert import_store.get("asi_1").state is AdsSpendImportState.PROPOSED
    worker.run_once()
    assert len(record_store) == 0


def test_missing_checker_actor_is_rejected(audit):
    import_store, record_store, gate, worker = _stack(audit)
    gate.propose(_import(uploaded_by="maker_ops"))
    with pytest.raises(AdsSpendImportGateViolation):
        gate.record_decision("asi_1", _decision("APPROVE", actor=""))               # no checker
    assert import_store.get("asi_1").state is AdsSpendImportState.PROPOSED


def test_rejected_import_never_materializes(audit):
    import_store, record_store, gate, worker = _stack(audit)
    gate.propose(_import())
    rejected = gate.record_decision("asi_1", _decision("REJECT", actor="checker_ops"))
    assert rejected.state is AdsSpendImportState.REJECTED
    assert worker.run_once() == []
    assert len(record_store) == 0


def test_cannot_redecide_a_decided_import(audit):
    import_store, record_store, gate, worker = _stack(audit)
    gate.propose(_import())
    gate.record_decision("asi_1", _decision("APPROVE", actor="checker_ops"))
    with pytest.raises(AdsSpendImportGateViolation):
        gate.record_decision("asi_1", _decision("REJECT", actor="checker_ops"))


# --- API surface: create -> decide (self-approve refused) -> materialize ---------------------------
def test_api_create_decide_materialize(audit):
    import_store, record_store, gate, worker = _stack(audit)
    deps = AdsSpendImportDeps(gate=gate, materializer=worker, audit=audit)

    created = handle_import_create(
        {"uploaded_by": "maker_ops",
         "rows": [{"campaign_id": "camp_1", "spend_value": 100000.0, "spend_date": D0.isoformat()}]},
        deps,
    )
    assert created.status == "CREATED" and created.state == "PROPOSED"

    # a self-approve via the API is refused (maker == checker)
    refused = handle_import_decision(
        {"import_id": created.import_id, "decision": "APPROVE", "actor": "maker_ops",
         "reason": "self", "audit_ref": "a", "evidence_ref": "e"}, deps,
    )
    assert refused.error_code == "APPROVAL_REFUSED"

    # a decision missing fields is refused — never synthesized (RULE-015)
    incomplete = handle_import_decision({"import_id": created.import_id, "decision": "APPROVE"}, deps)
    assert incomplete.error_code == "OWNER_DECISION_INCOMPLETE"

    # a distinct checker approves -> DECIDED APPROVED -> worker materializes
    decided = handle_import_decision(
        {"import_id": created.import_id, "decision": "APPROVE", "actor": "checker_ops",
         "reason": "reviewed", "audit_ref": "a1", "evidence_ref": "e1"}, deps,
    )
    assert decided.status == "DECIDED" and decided.state == "APPROVED"
    materialized = handle_import_materialize({}, deps)
    assert materialized.status == "MATERIALIZED" and materialized.materialized == 1


# --- no raw PII from the untrusted checker free-text reaches the audit trail (FAIL-008) ------------
def test_no_raw_pii_from_checker_reaches_audit(audit):
    import_store, record_store, gate, worker = _stack(audit)
    gate.propose(_import(uploaded_by="maker_ops"))
    pii_phone = "0" + "9" + "12" + "345" + "678"          # a VN-phone-shaped value
    pii_id = "ord" + "_" + "100" + "001"                  # an order-id-shaped value
    gate.record_decision(
        "asi_1",
        AdsSpendImportDecision(actor="checker_ops", reason="call " + pii_phone, audit_ref=pii_id,
                               evidence_ref="e1", decision=ImportDecisionKind.APPROVE),
    )
    blob = " ".join(f"{r.action} {r.reason} {r.subject_masked} {r.detail}" for r in audit.records)
    assert pii_phone not in blob, "raw phone must never reach the audit trail"
    assert pii_id not in blob, "raw id-ref must never reach the audit trail"
    assert audit.find("ADS_SPEND_IMPORT_APPROVED")        # the decision was still audited (machine-safe)
