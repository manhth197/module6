"""M6.2P leg 1 / M6-SMK-028 / RULE-014 / FAIL-007: external_send_policy is the owner-signed `ExternalSendPolicy`
enum {ALLOW_EXTERNAL, INTERNAL_ONLY, BLOCKED_PII, BLOCKED_DEFAULT}, coerced fail-closed to BLOCKED_DEFAULT on a
None / blank / unknown / raw token (mirroring `_resolve_sensitivity`), and `permits_external_send()` is True ONLY for
ALLOW_EXTERNAL. No registry row is ALLOW_EXTERNAL, so every real ACCEPTED event stays send_permitted=False; and even
an explicitly ALLOW_EXTERNAL row opens NO real egress because EXTERNAL_SEND is Final OFF (defense-in-depth). The
slice adds vocabulary; it opens no egress.
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
    """Minimal EventRegistryReader stub (`.get(event_code)`) — a tiny in-memory registry for the control case."""

    def __init__(self, rows):
        self._rows = {r.event_code: r for r in rows}

    def get(self, event_code):
        return self._rows.get(event_code)


def test_the_four_enum_values_exist():
    assert {p.value for p in ExternalSendPolicy} == {
        "ALLOW_EXTERNAL", "INTERNAL_ONLY", "BLOCKED_PII", "BLOCKED_DEFAULT"
    }


def test_resolve_send_policy_maps_each_value_to_itself():
    for p in ExternalSendPolicy:
        assert _resolve_send_policy(p) is p          # a real member -> itself
        assert _resolve_send_policy(p.value) is p    # its token string -> the member


def test_resolve_send_policy_fail_closed_on_none_blank_unknown_raw():
    # None / blank / unknown token / non-coercible junk all resolve to BLOCKED_DEFAULT — never crash, never auto-allow
    for bad in (None, "", "   ", "\t", "MAYBE", "allow", "true", "ALLOW", 123, 0, object(), b"ALLOW_EXTERNAL"):
        assert _resolve_send_policy(bad) is ExternalSendPolicy.BLOCKED_DEFAULT


def test_permits_external_send_true_only_for_allow_external():
    assert permits_external_send(ExternalSendPolicy.ALLOW_EXTERNAL) is True
    for p in (ExternalSendPolicy.INTERNAL_ONLY, ExternalSendPolicy.BLOCKED_PII, ExternalSendPolicy.BLOCKED_DEFAULT):
        assert permits_external_send(p) is False
    assert permits_external_send(_resolve_send_policy(None)) is False          # a coerced default is False
    assert permits_external_send(_resolve_send_policy("nonsense")) is False     # an unknown token is False


def test_real_accepted_event_stays_send_permitted_false(validator):
    # VIEW_LANDING (conftest): ACTIVE + owner + external_send_policy=None -> coerced BLOCKED_DEFAULT -> False
    result = validator.validate("VIEW_LANDING")
    assert result.accepted is True
    assert result.external_send_permitted is False


def test_allow_external_row_gates_true_but_opens_no_real_egress():
    # Non-vacuity + defense-in-depth: an explicitly ALLOW_EXTERNAL row makes the POLICY gate genuinely True (the
    # gate is real, not a dead hard-False) ... yet NO real egress opens because EXTERNAL_SEND stays Final OFF.
    row = EventRegistryRow(
        event_code="FB_ALLOW", registration_state=RegistrationState.ACTIVE, owner="core.tracking",
        external_send_policy=ExternalSendPolicy.ALLOW_EXTERNAL,
    )
    result = EventValidator(_Reg([row]), AuditLog()).validate("FB_ALLOW")
    assert result.accepted is True
    assert result.external_send_permitted is True              # the policy layer permits ALLOW_EXTERNAL
    assert config.EXTERNAL_SEND == "OFF"                       # independent second gate: no real send in this slice
