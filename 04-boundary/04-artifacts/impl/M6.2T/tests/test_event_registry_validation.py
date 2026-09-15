"""RULE-001 event-registry validation — exit-gate leg L1, smoke M6-SMK-001, prevents FAIL-003."""
from __future__ import annotations

from app.measurement.models.consumed import DataSensitivity
from app.measurement.registry.validator import EventDecision


def test_smk_001_unknown_event_rejected_with_audit(validator, audit):
    """M6-SMK-001: an event NOT in event_registry -> Reject/HOLD, audit clear."""
    result = validator.validate("TOTALLY_UNKNOWN_EVENT")
    assert result.decision is EventDecision.REJECT
    assert result.reason == "UNKNOWN_EVENT_NOT_IN_REGISTRY"
    assert result.external_send_permitted is False
    assert audit.find("UNKNOWN_EVENT_NOT_IN_REGISTRY"), "reject must be audited (never silently dropped)"


def test_deregistered_event_held_not_false_allowed(validator, audit):
    result = validator.validate("DEREG_SAMPLE")
    assert result.decision is EventDecision.HOLD
    assert result.reason == "REGISTRATION_STATE_NOT_ACTIVE"
    assert result.external_send_permitted is False
    assert audit.find("REGISTRATION_STATE_NOT_ACTIVE")


def test_missing_owner_event_held(validator, audit):
    """DQ item 1: an event without an owner fails -> HOLD (fail-closed)."""
    result = validator.validate("NO_OWNER_SAMPLE")
    assert result.decision is EventDecision.HOLD
    assert result.reason == "MISSING_OWNER"
    assert audit.find("MISSING_OWNER")


def test_valid_active_event_accepted_but_egress_fail_closed(validator):
    """Valid ACTIVE event is accepted; egress stays fail-closed while M6-OD-003 is OPEN."""
    result = validator.validate("VIEW_LANDING")
    assert result.decision is EventDecision.ACCEPT
    assert result.accepted is True
    assert result.data_sensitivity is DataSensitivity.INTERNAL
    assert result.external_send_permitted is False   # ENTRY-003 fail-closed default


def test_missing_data_sensitivity_defaults_to_pii(validator):
    """ENTRY-003 fail-closed default: MISSING data_sensitivity -> treat as PII (mask downstream)."""
    result = validator.validate("VIEW_LANDING_NO_SENS")
    assert result.decision is EventDecision.ACCEPT
    assert result.data_sensitivity is DataSensitivity.PII


def test_module6_never_invents_event_codes(registry):
    """RULE-001/018: the read-only registry port exposes no write path (M6 cannot insert an event code)."""
    for forbidden in ("insert", "add", "create", "update", "delete", "put"):
        assert not hasattr(registry, forbidden)
