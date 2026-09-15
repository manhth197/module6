"""RULE-002 consent fail-closed — exit-gate leg L2, smoke M6-SMK-002, prevents FAIL-002."""
from __future__ import annotations

import pytest

from app.measurement.models.consumed import ConsentScope


def test_valid_consent_in_scope_is_eligible(consent_gate, consent_rows):
    assert consent_gate.evaluate(consent_rows["cs_valid"], ConsentScope.EXTERNAL_MEASUREMENT) is True
    assert consent_gate.evaluate(consent_rows["cs_valid"], ConsentScope.AUDIENCE_SYNC) is True


@pytest.mark.parametrize("snap_key", ["cs_missing", "cs_expired", "cs_optout"])
def test_smk_002_non_valid_consent_blocks_egress(consent_gate, consent_rows, snap_key, audit):
    """M6-SMK-002: valid event but consent missing/expired/opt-out -> no external measurement, no audience sync."""
    snap = consent_rows[snap_key]
    assert consent_gate.evaluate(snap, ConsentScope.EXTERNAL_MEASUREMENT) is False
    assert consent_gate.evaluate(snap, ConsentScope.AUDIENCE_SYNC) is False
    assert len(audit) >= 1, "each denial must be audited"


def test_absent_snapshot_is_fail_closed(consent_gate, audit):
    """No snapshot at all -> deny (never infer/upgrade consent)."""
    assert consent_gate.evaluate(None, ConsentScope.EXTERNAL_MEASUREMENT) is False
    assert audit.find("CONSENT_SNAPSHOT_ABSENT"), "absent snapshot must be audited"


def test_scope_not_granted_is_denied(consent_gate, consent_rows):
    """Consent VALID for measurement only -> CRM egress denied (scope fail-closed)."""
    snap = consent_rows["cs_valid_meas_only"]
    assert consent_gate.evaluate(snap, ConsentScope.EXTERNAL_MEASUREMENT) is True
    assert consent_gate.evaluate(snap, ConsentScope.CRM) is False
