"""M6.2I leg L1 (retargeting) / doc §8 L143 / M6-RULE-002: "Retargeting chỉ dựa trên event hợp lệ và consent hợp
lệ." The measure-only classifier marks an engagement event retargeting-eligible ONLY when consent is VALID for
AUDIENCE_SYNC; missing/expired/opt-out/scope-not-granted -> not eligible (fail-closed). It never sends.
"""
from __future__ import annotations

from app.measurement.funnel.retargeting import RetargetingMeasurement

# a retargeting sender would push an audience/external payload — the measure-only classifier must expose no such verb
_FORBIDDEN_SEND = ("send", "dispatch", "transport", "enqueue", "sync", "publish", "push", "deliver", "connector")


def test_engagement_event_with_valid_audience_consent_is_eligible(retargeting_measurement, consent_rows):
    assert retargeting_measurement.is_eligible("LIVE_COMMENT", consent_rows["cs_valid"]) is True   # has AUDIENCE_SYNC


def test_consent_missing_or_optout_is_not_eligible(retargeting_measurement, consent_rows):
    assert retargeting_measurement.is_eligible("LIVE_COMMENT", None) is False                      # no snapshot
    assert retargeting_measurement.is_eligible("LIVE_COMMENT", consent_rows["cs_optout"]) is False # opt-out
    assert retargeting_measurement.is_eligible("LIVE_COMMENT", consent_rows["cs_expired"]) is False # expired


def test_valid_state_but_scope_not_granted_is_not_eligible(retargeting_measurement, consent_rows):
    """VALID consent that grants ONLY external_measurement (not audience_sync) is NOT retargeting-eligible."""
    assert retargeting_measurement.is_eligible("LIVE_COMMENT", consent_rows["cs_valid_meas_only"]) is False


def test_unrecognized_event_is_not_eligible(retargeting_measurement, consent_rows):
    """A non-engagement / unrecognized code is never eligible even with valid consent (fail-closed, RULE-001-aligned)."""
    assert retargeting_measurement.is_eligible("ORDER_VERIFIED", consent_rows["cs_valid"]) is False
    assert retargeting_measurement.is_eligible("NOT_A_REAL_EVENT", consent_rows["cs_valid"]) is False
    assert retargeting_measurement.is_eligible(None, consent_rows["cs_valid"]) is False


def test_measure_counts_only_consent_valid_eligibles(retargeting_measurement, consent_rows):
    pairs = [
        ("LIVE_COMMENT", consent_rows["cs_valid"]),        # eligible
        ("MESSENGER_STARTED", consent_rows["cs_valid"]),   # eligible
        ("LIVE_VIEW", consent_rows["cs_optout"]),          # ineligible (opt-out)
        ("QUOTE_SENT", None),                              # ineligible (no consent)
        ("ORDER_VERIFIED", consent_rows["cs_valid"]),      # ineligible (not an engagement signal)
    ]
    reach = retargeting_measurement.measure(pairs)
    assert reach.eligible == 2
    assert reach.ineligible == 3
    assert reach.considered == 5


def test_retargeting_measurement_has_no_send_surface(retargeting_measurement):
    for verb in _FORBIDDEN_SEND:
        assert not hasattr(retargeting_measurement, verb), f"retargeting exposes send verb {verb!r} (must be measure-only)"
