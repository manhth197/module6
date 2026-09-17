"""Official smoke — slice M6.2A — M6-SMK-002 (doc ADS-P0-002).

Authored by TESTER in M6-P1003 (mode=build, "do not yet run"); it is EXECUTED and its result recorded in
M6-P1004 (TESTER_RUN -> 04-artifacts/test-reports/M6.2A/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 402):

    Kịch bản (verbatim):          "Event hợp lệ nhưng thiếu consent"
    Kết quả phải đạt (verbatim):  "Không external measurement, không audience sync"

The event is VALID (in event_registry) but consent is absent / MISSING / EXPIRED / OPT_OUT. Leg L2 evidence
is END-TO-END THROUGH THE INGEST SEAM (Round 3): the seam resolves the consent handle through the mandatory
`ConsentReader`, binds it to the event's subject, drives the fail-closed gate, and audits the denial. The
valid event is still durably logged internally (a measurement row), but egress is never eligible. We assert on
the SEAM's own audit trail — NOT on a side-channel `consent_gate.evaluate(...)` call — so the L2 leg has real
end-to-end proof. Prevents M6-FAIL-002 (consent violation). `subject_ref` is PII-class; the audit sink masks
it — these fixtures use synthetic ids only.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.measurement.ingest import IngestService
from app.measurement.models.consumed import ConsentScope

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)

# The two egress kinds the expected result names explicitly: "external measurement" and "audience sync".
_EGRESS_SCOPES = (ConsentScope.EXTERNAL_MEASUREMENT, ConsentScope.AUDIENCE_SYNC)


def _ingest_through_seam(
    validator, store, consent_gate, consent_reader, audit, resolver,
    *, consent_snapshot_id, guest_id, scope, session_id="sess_smk002",
):
    """Drive a VALID registry event through the real ingest seam, resolving consent by handle exactly as the
    M6.2B endpoint will. `guest_id` matches the snapshot's subject so Round-3 subject binding lets a
    legitimate snapshot through to the gate."""
    svc = IngestService(validator, store, consent_gate, consent_reader, audit, resolver=resolver)
    return svc.ingest_event(
        event_code="VIEW_LANDING",              # a VALID, ACTIVE registry event ("event hợp lệ")
        page_id="pg_smk002",
        session_id=session_id,                  # PII-pseudonymous synthetic id
        source="web",
        event_ts=_TS,
        raw_event_hash="rawhash_smk002",
        consent_snapshot_id=consent_snapshot_id,
        guest_id=guest_id,
        consent_scope=scope,
    )


# --- primary smoke: scenario verbatim, both named egress kinds, END-TO-END through the seam --------
@pytest.mark.parametrize("scope", list(_EGRESS_SCOPES))
def test_smk_002_valid_event_missing_consent_no_external_measurement_no_audience_sync(
    validator, store, consent_gate, consent_reader, audit, resolver, scope
):
    """M6-SMK-002 "Event hợp lệ nhưng thiếu consent" -> "Không external measurement, không audience sync".

    Driven through the ingest seam for BOTH egress kinds. A valid event with a MISSING-consent snapshot is
    durably logged, but the fail-closed gate the seam drives denies egress and audits the denial; end-to-end
    egress is never eligible. `cs_missing.subject_ref == "guest_x"`, so the event carries that guest_id.
    """
    res = _ingest_through_seam(
        validator, store, consent_gate, consent_reader, audit, resolver,
        consent_snapshot_id="cs_missing", guest_id="guest_x", scope=scope,
        session_id=f"sess_{scope.value}",
    )
    assert res.validation.accepted is True          # the event itself is valid ("event hợp lệ")
    assert res.logged is True                        # valid event is a durable internal measurement row
    assert res.egress_eligible is False              # no external measurement / audience sync without consent
    assert audit.find("CONSENT_MISSING"), "the seam must audit the consent denial end-to-end (not a side call)"


# --- negative / fail-closed companions: every non-valid consent state, ALSO through the seam -------
@pytest.mark.parametrize(
    "snap_id,expected_reason",
    [
        ("cs_missing", "CONSENT_MISSING"),
        ("cs_expired", "CONSENT_EXPIRED"),
        ("cs_optout", "CONSENT_OPT_OUT"),
    ],
)
def test_smk_002_neg_non_valid_consent_blocks_egress_through_the_seam(
    validator, store, consent_gate, consent_reader, audit, resolver, snap_id, expected_reason
):
    """Fail-closed across MISSING / EXPIRED / OPT_OUT, proven on the seam: egress ineligible, denial audited.
    (All three snapshots have subject_ref == "guest_x".)"""
    res = _ingest_through_seam(
        validator, store, consent_gate, consent_reader, audit, resolver,
        consent_snapshot_id=snap_id, guest_id="guest_x", scope=ConsentScope.EXTERNAL_MEASUREMENT,
        session_id=f"sess_{snap_id}",
    )
    assert res.egress_eligible is False
    assert audit.find(expected_reason), "each denial must be audited by the seam"


def test_smk_002_neg_absent_snapshot_is_fail_closed_through_the_seam(
    validator, store, consent_gate, consent_reader, audit, resolver
):
    """No consent handle at all -> the seam drives the gate to deny (never infer or upgrade consent)."""
    svc = IngestService(validator, store, consent_gate, consent_reader, audit, resolver=resolver)
    res = svc.ingest_event(
        event_code="VIEW_LANDING", page_id="pg_smk002", session_id="sess_absent", source="web",
        event_ts=_TS, raw_event_hash="rawhash_smk002",
        consent_scope=ConsentScope.EXTERNAL_MEASUREMENT,   # no consent_snapshot_id, no guest_id
    )
    assert res.egress_eligible is False
    assert audit.find("CONSENT_SNAPSHOT_ABSENT"), "an absent snapshot must be audited by the seam"


# --- positive control: proves it is the MISSING consent, not a blanket block, that denies egress --
def test_smk_002_control_valid_inscope_consent_is_egress_eligible_at_gate(consent_gate, consent_rows):
    """Control: VALID consent granted for both scopes IS eligible at the gate — proving the primary smoke
    denies because consent is missing, not because the gate denies everything. Actual send still stays
    framework-only at the seam (external_send=OFF, M6-OD-003 OPEN; see tests/test_ingest_measure_only.py)."""
    snap = consent_rows["cs_valid"]
    for scope in _EGRESS_SCOPES:
        assert consent_gate.evaluate(snap, scope) is True
