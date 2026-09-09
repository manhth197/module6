"""M6.2J / doc §9 Dormant-Reactivation / M6-RULE-002: reactivation counts only dormant-segment members with
consent VALID (CRM scope) AND CRM eligibility pass; opt-out / expired / ineligible / absent ⇒ excluded
(fail-closed, FAIL-002). Measure-only (no CRM send).
"""
from __future__ import annotations


def _scenario(make_reactivation, make_crm_consent):
    mk = make_reactivation
    members = [
        mk.member("seg_dormant", "m_ok", "cs_ok"),        # VALID CRM + eligible + reactivated
        mk.member("seg_dormant", "m_out", "cs_out"),      # opt-out -> excluded
        mk.member("seg_dormant", "m_inel", "cs_inel"),    # VALID CRM but NOT crm-eligible -> excluded
    ]
    consent = {
        "cs_ok": make_crm_consent("cs_ok", "m_ok"),
        "cs_out": make_crm_consent("cs_out", "m_out", state="OPT_OUT", scopes=()),
        "cs_inel": make_crm_consent("cs_inel", "m_inel"),
    }
    return mk(members, consent, crm_eligible={"m_ok": True, "m_inel": False},
              reactivated={"m_ok"}, spend=90000.0)


def test_only_consent_valid_and_eligible_members_count(make_reactivation, make_crm_consent):
    meas, seg = _scenario(make_reactivation, make_crm_consent)
    eligible = meas.eligible_members(seg)
    keys = {m.member_key for m in eligible}
    assert keys == {"m_ok"}                               # opt-out + ineligible excluded (fail-closed)


def test_reactivation_rate_and_cpa(make_reactivation, make_crm_consent):
    meas, seg = _scenario(make_reactivation, make_crm_consent)
    assert meas.reactivated_count(seg) == 1
    assert meas.reactivation_rate(seg) == 1.0            # 1 reactivated / 1 eligible
    assert meas.cpa_reactivation(seg) == 90000.0         # spend / reactivated


def test_no_eligible_members_is_fail_closed(make_reactivation, make_crm_consent):
    mk = make_reactivation
    members = [mk.member("seg_dormant", "m_out", "cs_out")]
    consent = {"cs_out": make_crm_consent("cs_out", "m_out", state="OPT_OUT", scopes=())}
    meas, seg = mk(members, consent, crm_eligible={}, reactivated=set(), spend=50000.0)
    assert meas.eligible_members(seg) == []
    assert meas.reactivation_rate(seg) is None           # 0 eligible -> fail-closed None
    assert meas.cpa_reactivation(seg) is None            # 0 reactivated -> fail-closed None


def test_reactivation_has_no_send_surface(make_reactivation, make_crm_consent):
    meas, _seg = _scenario(make_reactivation, make_crm_consent)
    for verb in ("send", "sync", "dispatch", "crm_send", "enqueue", "publish"):
        assert not hasattr(meas, verb), f"reactivation exposes send verb {verb!r}"
