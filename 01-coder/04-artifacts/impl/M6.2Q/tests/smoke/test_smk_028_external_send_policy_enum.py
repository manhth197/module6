"""Official smoke — slice M6.2P — M6-SMK-028 (proposed — HARDENING, owner review): external_send_policy enum (B5).

Authored by TESTER in M6-P2403 (mode=build, "do not yet run"); EXECUTED + recorded in M6-P2404
(-> 04-artifacts/test-reports/M6.2P/SMOKE_RESULTS.md). Adopts the owner-signed (QĐ-1, 2026-09-07) ExternalSendPolicy
enum as typed, fail-closed code. Governance is immutable here: global_gateway_state=BLOCKED, production_flag=OFF,
external_send=OFF — nothing below flips a flag or opens egress; this slice makes the vocabulary real + fail-closed
only (no event is ALLOW_EXTERNAL; EXTERNAL_SEND stays Final OFF).

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (proposed additions row M6-SMK-028):

    Scenario (verbatim):   "event_registry row with external_send_policy = each of ALLOW_EXTERNAL / INTERNAL_ONLY /
                           BLOCKED_PII / BLOCKED_DEFAULT + a None/blank/unknown token (B5)"
    Expected (verbatim):   "typed ExternalSendPolicy enum; permits_external_send() True ONLY for ALLOW_EXTERNAL;
                           None/blank/unknown coerces fail-closed to BLOCKED_DEFAULT (no crash, no auto-allow); every
                           real ACCEPTED event still send_permitted=False (no event is ALLOW_EXTERNAL) and
                           EXTERNAL_SEND stays OFF"

RULE-014 (PII-egress governance, explicit + fail-closed) / RULE-015 (no self-cert); FAIL-007. Reuses the coder's
M6.2P leg pattern + the shared conftest `validator` fixture; all event codes are synthetic.
"""
from __future__ import annotations

from app import config
from app.measurement.audit import AuditLog
from app.measurement.models.consumed import EventRegistryRow, ExternalSendPolicy, RegistrationState
from app.measurement.registry.validator import (
    EventValidator,
    _resolve_send_policy,
    permits_external_send,
)


class _Reg:
    """Minimal EventRegistryReader stub (`.get(event_code)`) — a tiny in-memory registry seeded with the row(s)."""

    def __init__(self, rows):
        self._rows = {r.event_code: r for r in rows}

    def get(self, event_code):
        return self._rows.get(event_code)


def _validate(row):
    return EventValidator(_Reg([row]), AuditLog()).validate(row.event_code)


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_028_each_policy_value_gates_permits_only_allow_external():
    """M6-SMK-028 "event_registry row with external_send_policy = each of ALLOW_EXTERNAL / INTERNAL_ONLY /
    BLOCKED_PII / BLOCKED_DEFAULT + a None/blank/unknown token (B5)" -> "typed ExternalSendPolicy enum;
    permits_external_send() True ONLY for ALLOW_EXTERNAL; ...".

    The enum has exactly the 4 owner-signed values; an event_registry row carrying EACH value validates ACCEPTED and
    its resolved external_send_permitted is True iff the policy is ALLOW_EXTERNAL (permits_external_send agrees).
    """
    assert {p.value for p in ExternalSendPolicy} == {
        "ALLOW_EXTERNAL", "INTERNAL_ONLY", "BLOCKED_PII", "BLOCKED_DEFAULT"
    }
    for policy in ExternalSendPolicy:
        row = EventRegistryRow(
            event_code=f"EVT_{policy.name}", registration_state=RegistrationState.ACTIVE,
            owner="core.tracking", external_send_policy=policy,
        )
        result = _validate(row)
        assert result.accepted is True
        assert result.external_send_permitted is (policy is ExternalSendPolicy.ALLOW_EXTERNAL)
        assert permits_external_send(policy) is (policy is ExternalSendPolicy.ALLOW_EXTERNAL)


# --- negative / fail-closed: a None/blank/unknown token coerces to BLOCKED_DEFAULT (no crash, no auto-allow) ---
def test_smk_028_neg_none_blank_unknown_token_is_failclosed_blocked_default():
    """"None/blank/unknown coerces fail-closed to BLOCKED_DEFAULT (no crash, no auto-allow)": _resolve_send_policy
    maps None / blank / whitespace / an unknown token / non-coercible junk to BLOCKED_DEFAULT; a registry row
    carrying such a token still validates ACCEPTED but with external_send_permitted False (never auto-allow)."""
    for bad in (None, "", "   ", "\t", "MAYBE", "allow", "ALLOW", "true", 123, 0, object(), b"ALLOW_EXTERNAL"):
        assert _resolve_send_policy(bad) is ExternalSendPolicy.BLOCKED_DEFAULT     # fail-closed, never crashes
        assert permits_external_send(_resolve_send_policy(bad)) is False           # never auto-allow
    for i, bad in enumerate((None, "", "   ", "MAYBE")):
        row = EventRegistryRow(
            event_code=f"EVT_BAD_{i}", registration_state=RegistrationState.ACTIVE,
            owner="core.tracking", external_send_policy=bad,
        )
        result = _validate(row)
        assert result.accepted is True
        assert result.external_send_permitted is False        # coerced BLOCKED_DEFAULT -> not permitted


# --- negative / real-world: every real ACCEPTED event stays send_permitted=False ------------------
def test_smk_028_neg_real_accepted_event_stays_send_permitted_false(validator):
    """"every real ACCEPTED event still send_permitted=False (no event is ALLOW_EXTERNAL)": the conftest VIEW_LANDING
    row (ACTIVE + owner + external_send_policy=None) validates ACCEPTED with external_send_permitted False — no real
    registry row is classified ALLOW_EXTERNAL (the permit-mapping is the OPEN M6-OD-003 privacy/legal half)."""
    result = validator.validate("VIEW_LANDING")
    assert result.accepted is True
    assert result.external_send_permitted is False


# --- positive control + defense-in-depth: the gate is REAL, yet EXTERNAL_SEND stays OFF -----------
def test_smk_028_control_allow_external_gates_true_but_external_send_off():
    """Non-vacuity + defense-in-depth ("and EXTERNAL_SEND stays OFF"): an explicitly ALLOW_EXTERNAL row makes the
    POLICY gate genuinely True (proving the gate is real, not a dead hard-False) — yet NO real egress opens because
    `config.EXTERNAL_SEND` is Final "OFF" (an independent second gate). This slice classifies no real event
    ALLOW_EXTERNAL and flips no flag."""
    row = EventRegistryRow(
        event_code="FB_ALLOW_SMK028", registration_state=RegistrationState.ACTIVE,
        owner="core.tracking", external_send_policy=ExternalSendPolicy.ALLOW_EXTERNAL,
    )
    result = _validate(row)
    assert result.accepted is True
    assert result.external_send_permitted is True             # the policy layer permits ALLOW_EXTERNAL (real gate)
    assert config.EXTERNAL_SEND == "OFF"                      # independent second gate: no real send in this slice
