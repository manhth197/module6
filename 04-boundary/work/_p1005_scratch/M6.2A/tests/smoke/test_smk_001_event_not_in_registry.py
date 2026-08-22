"""Official smoke — slice M6.2A — M6-SMK-001 (doc ADS-P0-001).

Authored by TESTER in M6-P1003 (mode=build, "do not yet run"); it is EXECUTED and its result recorded in
M6-P1004 (TESTER_RUN -> 04-artifacts/test-reports/M6.2A/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 401):

    Kịch bản (verbatim):          "Event không có trong event_registry"
    Kết quả phải đạt (verbatim):  "Reject/HOLD, audit rõ"

Exercised end-to-end through the ingest seam (app.measurement.ingest.IngestService), reusing the shared
conftest fixtures (in-memory TEST DOUBLES for the CONSUMED event_registry). RULE-001 / RULE-018; prevents
M6-FAIL-003 (event drift); exit-gate leg L1. An `event_code` is channel-origin, untrusted DATA — these
fixtures use synthetic codes only; no raw PII.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.measurement.ingest import IngestService
from app.measurement.registry.validator import EventDecision

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def _ingest(validator, store, consent_gate, resolver, event_code):
    """Drive one event through the real ingest seam (validate -> append -> consent-eligibility)."""
    svc = IngestService(validator, store, consent_gate, resolver)
    return svc.ingest_event(
        event_code=event_code,
        page_id="pg_smk001",
        session_id="sess_smk001",          # PII-pseudonymous synthetic id
        source="web",
        event_ts=_TS,
        raw_event_hash="rawhash_smk001",
    )


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_001_event_not_in_event_registry_is_rejected_with_audit(
    validator, store, consent_gate, resolver, audit
):
    """M6-SMK-001 "Event không có trong event_registry" -> "Reject/HOLD, audit rõ".

    An event code absent from event_registry is REJECTed, never written to web_event_logs, and never
    egress-eligible; the rejection is clearly audited (audit rõ), never silently dropped.
    """
    res = _ingest(validator, store, consent_gate, resolver, "SMK001_EVENT_NOT_IN_REGISTRY")

    assert res.validation.decision is EventDecision.REJECT            # Reject
    assert res.validation.reason == "UNKNOWN_EVENT_NOT_IN_REGISTRY"
    assert res.logged is False                                        # not counted as a measurement row
    assert len(store) == 0
    assert res.egress_eligible is False                              # no external send off an unknown event
    assert audit.find("UNKNOWN_EVENT_NOT_IN_REGISTRY"), "reject must be audited clearly (audit ro)"


# --- negative / fail-closed companions: the HOLD arm of "Reject/HOLD" ------------------------------
def test_smk_001_neg_deregistered_event_is_held_not_false_allowed(
    validator, store, consent_gate, resolver, audit
):
    """Fail-closed: a registered-but-DEREGISTERED event is HELD (not accepted), audited, and not logged."""
    res = _ingest(validator, store, consent_gate, resolver, "DEREG_SAMPLE")

    assert res.validation.decision is EventDecision.HOLD
    assert res.validation.reason == "REGISTRATION_STATE_NOT_ACTIVE"
    assert res.logged is False
    assert res.egress_eligible is False
    assert audit.find("REGISTRATION_STATE_NOT_ACTIVE"), "hold must be audited"


def test_smk_001_neg_registered_but_missing_owner_is_held(
    validator, store, consent_gate, resolver, audit
):
    """Fail-closed: an ACTIVE event with no owner fails data-quality and is HELD (not accepted)."""
    res = _ingest(validator, store, consent_gate, resolver, "NO_OWNER_SAMPLE")

    assert res.validation.decision is EventDecision.HOLD
    assert res.validation.reason == "MISSING_OWNER"
    assert res.logged is False
    assert audit.find("MISSING_OWNER"), "hold must be audited"


# --- positive control: proves the smoke discriminates (it does not reject everything) -------------
def test_smk_001_control_known_active_event_is_accepted_and_logged(
    validator, store, consent_gate, resolver
):
    """Control: a known ACTIVE registry event IS accepted and logged, so the smoke is not vacuous."""
    res = _ingest(validator, store, consent_gate, resolver, "VIEW_LANDING")

    assert res.validation.decision is EventDecision.ACCEPT
    assert res.logged is True
    assert len(store) == 1
