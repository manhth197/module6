"""Official smoke — slice M6.2J — M6-SMK-008 (doc ADS-P0-008).

Authored by TESTER in M6-P1903 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1904. Governance is
immutable here: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag
and nothing is ever sent.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 408):

    Kịch bản (verbatim):          "CRM opt-out"
    Kết quả phải đạt (verbatim):  "Không sync CRM audience/CRM event outbound"

A CRM subject with opt-out (or missing / expired / scope-not-granted) consent is EXCLUDED from CRM revenue
(fail-closed, RULE-002 / FAIL-002); and the growth CRM layer has NO send / sync / dispatch surface at all — there
is no CRM audience or CRM event outbound path. Reuses the shared conftest growth fixtures (make_verified_row,
make_crm_measurement, make_crm_consent). All ids synthetic; no PII.
"""
from __future__ import annotations

from app.measurement.growth.crm import CrmConsumed


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_008_crm_optout_excluded_and_no_sync_surface(
    make_verified_row, make_crm_measurement, make_crm_consent
):
    """M6-SMK-008 "CRM opt-out" -> "Không sync CRM audience/CRM event outbound"."""
    make_verified_row("ev_o", revenue=250000.0, order_code="ord_o", signals={"crm": True})
    consumed = CrmConsumed(
        crm_eligible_orders={"ord_o": True},
        suppression_pass_orders={"ord_o": True},
        consent_by_order={"ord_o": make_crm_consent(state="OPT_OUT", scopes=())},   # opted out
    )
    m = make_crm_measurement(consumed)

    assert m.crm_revenue() == 0.0            # opt-out subject excluded from CRM revenue (fail-closed)
    # ...and there is NO CRM audience / event outbound surface at all (không sync)
    for verb in ("send", "sync", "dispatch", "transport", "enqueue", "publish", "crm_send", "send_crm"):
        assert not hasattr(m, verb), f"CRM measurement must not expose an outbound verb {verb!r}"


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_008_neg_expired_or_missing_consent_excluded(
    make_verified_row, make_crm_measurement, make_crm_consent
):
    """Expired consent — and a missing snapshot entirely — are fail-closed excluded from CRM revenue (RULE-002)."""
    make_verified_row("ev_e", revenue=250000.0, order_code="ord_e", signals={"crm": True})
    expired = CrmConsumed(crm_eligible_orders={"ord_e": True}, suppression_pass_orders={"ord_e": True},
                          consent_by_order={"ord_e": make_crm_consent(state="EXPIRED", scopes=())})
    assert make_crm_measurement(expired).crm_revenue() == 0.0
    missing = CrmConsumed(crm_eligible_orders={"ord_e": True}, suppression_pass_orders={"ord_e": True})
    assert make_crm_measurement(missing).crm_revenue() == 0.0   # no snapshot -> fail-closed


def test_smk_008_neg_consent_without_crm_scope_excluded(
    make_verified_row, make_crm_measurement, make_crm_consent
):
    """VALID consent that grants only audience_sync (not the CRM scope) is not CRM-revenue eligible (fail-closed)."""
    make_verified_row("ev_s", revenue=250000.0, order_code="ord_s", signals={"crm": True})
    consumed = CrmConsumed(crm_eligible_orders={"ord_s": True}, suppression_pass_orders={"ord_s": True},
                           consent_by_order={"ord_s": make_crm_consent(scopes=("audience_sync",))})
    assert make_crm_measurement(consumed).crm_revenue() == 0.0


def test_smk_008_control_valid_crm_consent_is_counted(
    make_verified_row, make_crm_measurement, make_crm_consent
):
    """Control (non-vacuous): the SAME measurement DOES count a verified CRM order when consent is VALID for the
    CRM scope AND eligibility + suppression pass — proving the exclusions above are consent/suppression-caused,
    not a measurement that always returns 0."""
    make_verified_row("ev_v", revenue=250000.0, order_code="ord_v", signals={"crm": True})
    consumed = CrmConsumed(crm_eligible_orders={"ord_v": True}, suppression_pass_orders={"ord_v": True},
                           consent_by_order={"ord_v": make_crm_consent(state="VALID", scopes=("crm",))})
    assert make_crm_measurement(consumed).crm_revenue() == 250000.0
