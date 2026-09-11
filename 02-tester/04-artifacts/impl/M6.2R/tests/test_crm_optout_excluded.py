"""M6.2J / M6-SMK-008 (ADS-P0-008): "CRM opt-out" -> "Không sync CRM audience/CRM event outbound". A CRM subject
with opt-out (or missing/expired) consent, or a failed suppression, is EXCLUDED from CRM revenue + reactivation
(fail-closed, RULE-002 / FAIL-002). The growth layer has NO CRM send surface.
"""
from __future__ import annotations

from app.measurement.growth.crm import CrmConsumed, CrmReorderMeasurement


def test_optout_consent_excludes_crm_revenue(make_verified_row, make_crm_measurement, make_crm_consent):
    make_verified_row("ev_o", revenue=250000.0, order_code="ord_o", signals={"crm": True})
    consumed = CrmConsumed(
        crm_eligible_orders={"ord_o": True},
        suppression_pass_orders={"ord_o": True},
        consent_by_order={"ord_o": make_crm_consent(state="OPT_OUT", scopes=())},   # opted out
    )
    assert make_crm_measurement(consumed).crm_revenue() == 0.0     # opt-out -> excluded (SMK-008)


def test_expired_or_missing_consent_excludes_crm_revenue(make_verified_row, make_crm_measurement, make_crm_consent):
    make_verified_row("ev_e", revenue=250000.0, order_code="ord_e", signals={"crm": True})
    expired = CrmConsumed(crm_eligible_orders={"ord_e": True}, suppression_pass_orders={"ord_e": True},
                          consent_by_order={"ord_e": make_crm_consent(state="EXPIRED", scopes=())})
    assert make_crm_measurement(expired).crm_revenue() == 0.0
    # missing snapshot entirely -> fail-closed
    missing = CrmConsumed(crm_eligible_orders={"ord_e": True}, suppression_pass_orders={"ord_e": True})
    assert make_crm_measurement(missing).crm_revenue() == 0.0


def test_consent_without_crm_scope_excludes(make_verified_row, make_crm_measurement, make_crm_consent):
    """VALID consent that grants only audience_sync (not crm) is not CRM-revenue eligible (scope not granted)."""
    make_verified_row("ev_s", revenue=250000.0, order_code="ord_s", signals={"crm": True})
    consumed = CrmConsumed(crm_eligible_orders={"ord_s": True}, suppression_pass_orders={"ord_s": True},
                           consent_by_order={"ord_s": make_crm_consent(scopes=("audience_sync",))})
    assert make_crm_measurement(consumed).crm_revenue() == 0.0


def test_crm_measurement_has_no_send_surface(make_crm_measurement):
    m = make_crm_measurement()
    for verb in ("send", "sync", "dispatch", "transport", "enqueue", "publish", "crm_send", "send_crm"):
        assert not hasattr(m, verb), f"CRM measurement exposes send verb {verb!r} (must be measure-only)"
