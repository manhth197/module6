"""Official smoke — slice M6.2A — M6-SMK-002 (doc ADS-P0-002).

Authored by TESTER in M6-P1003 (mode=build, "do not yet run"); it is EXECUTED and its result recorded in
M6-P1004 (TESTER_RUN -> 04-artifacts/test-reports/M6.2A/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 402):

    Kịch bản (verbatim):          "Event hợp lệ nhưng thiếu consent"
    Kết quả phải đạt (verbatim):  "Không external measurement, không audience sync"

The event is VALID (in event_registry) but consent is absent / MISSING / EXPIRED / OPT_OUT. The consent gate is
fail-closed (RULE-002): it denies BOTH external_measurement AND audience_sync, and each denial is audited. The
valid event is still durably logged internally (a measurement row), but egress is never eligible. Prevents
M6-FAIL-002 (consent violation); exit-gate leg L2. Exercised through the ingest seam, reusing the shared
conftest fixtures. `subject_ref` is PII-class; the audit sink masks it — these fixtures use synthetic ids only.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.measurement.ingest import IngestService
from app.measurement.models.consumed import ConsentScope

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)

# The two egress kinds the expected result names explicitly: "external measurement" and "audience sync".
_EGRESS_SCOPES = (ConsentScope.EXTERNAL_MEASUREMENT, ConsentScope.AUDIENCE_SYNC)


def _ingest_valid_event(validator, store, consent_gate, resolver, snapshot, scope):
    """Drive a VALID registry event through the real ingest seam with the given consent snapshot/scope."""
    svc = IngestService(validator, store, consent_gate, resolver)
    return svc.ingest_event(
        event_code="VIEW_LANDING",              # a VALID, ACTIVE registry event ("event hợp lệ")
        page_id="pg_smk002",
        session_id="sess_smk002",               # PII-pseudonymous synthetic id
        source="web",
        event_ts=_TS,
        raw_event_hash="rawhash_smk002",
        consent_snapshot=snapshot,
        consent_scope=scope,
    )


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_002_valid_event_missing_consent_no_external_measurement_no_audience_sync(
    validator, store, consent_gate, resolver, consent_rows, audit
):
    """M6-SMK-002 "Event hợp lệ nhưng thiếu consent" -> "Không external measurement, không audience sync".

    A valid event with a MISSING-consent snapshot is durably logged, but the fail-closed consent gate denies
    every egress scope and audits the denial; end-to-end egress is never eligible.
    """
    snap = consent_rows["cs_missing"]

    # Fail-closed consent decision: neither external measurement nor audience sync is permitted.
    for scope in _EGRESS_SCOPES:
        assert consent_gate.evaluate(snap, scope) is False

    # ...and end-to-end through the ingest seam: the valid event is logged, but egress stays ineligible.
    res = _ingest_valid_event(
        validator, store, consent_gate, resolver, snap, ConsentScope.EXTERNAL_MEASUREMENT
    )
    assert res.validation.accepted is True          # the event itself is valid ("event hợp lệ")
    assert res.logged is True                        # valid event is a durable internal measurement row
    assert res.egress_eligible is False              # no external measurement without valid consent
    assert audit.find("CONSENT_MISSING"), "the consent denial must be audited"


# --- negative / fail-closed companions: every non-valid consent state -----------------------------
@pytest.mark.parametrize(
    "snap_key,expected_reason",
    [
        ("cs_missing", "CONSENT_MISSING"),
        ("cs_expired", "CONSENT_EXPIRED"),
        ("cs_optout", "CONSENT_OPT_OUT"),
    ],
)
def test_smk_002_neg_non_valid_consent_blocks_every_egress_scope(
    consent_gate, consent_rows, snap_key, expected_reason, audit
):
    """Fail-closed across MISSING / EXPIRED / OPT_OUT: no external measurement, no audience sync; each audited."""
    snap = consent_rows[snap_key]
    for scope in _EGRESS_SCOPES:
        assert consent_gate.evaluate(snap, scope) is False
    assert audit.find(expected_reason), "each denial must be audited"


def test_smk_002_neg_absent_snapshot_is_fail_closed(consent_gate, audit):
    """No snapshot at all -> deny every egress scope (never infer or upgrade consent)."""
    for scope in _EGRESS_SCOPES:
        assert consent_gate.evaluate(None, scope) is False
    assert audit.find("CONSENT_SNAPSHOT_ABSENT"), "absent snapshot must be audited"


# --- positive control: proves it is the MISSING consent, not a blanket block, that denies egress --
def test_smk_002_control_valid_inscope_consent_is_egress_eligible_at_gate(consent_gate, consent_rows):
    """Control: VALID consent granted for both scopes IS eligible at the gate — proving the primary smoke
    denies because consent is missing, not because the gate denies everything. Actual send still stays
    framework-only at the seam (external_send=OFF, M6-OD-003 OPEN)."""
    snap = consent_rows["cs_valid"]
    for scope in _EGRESS_SCOPES:
        assert consent_gate.evaluate(snap, scope) is True
