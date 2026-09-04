"""M6.2F / M6-CTR-024 + CTR-012: the data_quality_checker evaluates the 8 doc §15 gate items and outputs ONLY
PASS/HOLD/FAIL with a worst-status roll-up (FAIL > HOLD > PASS); it transitions the row's Zone-C
data_quality_status via the store's audited setter (RULE-015). HOLD/FAIL never scale evidence (RULE-009).
"""
from __future__ import annotations

from app.measurement.models.measurement_event import DataQualityStatus
from app.measurement.quality.data_quality_check import GateItem
from app.measurement.quality.data_quality_checker import DQContext

_ALL_STATES = (DataQualityStatus.PASS, DataQualityStatus.HOLD, DataQualityStatus.FAIL)


def _clean_ctx(**over):
    base = dict(
        event_registered=True, event_owner_known=True, consent_valid=True, no_duplicate=True,
        identity_mapped=True, suppression_active=False, dashboard_has_trace=True,
    )
    base.update(over)
    return DQContext(**base)


def test_all_items_pass_transitions_zone_c_audited(make_verified_row, dq_checker, measurement_store, audit):
    row = make_verified_row("evt_ok", revenue=100000.0, order_code="ORD_A",
                            campaign_id="c1", adset_id="a1", ad_id="ad1")   # full campaign -> attribution HIGH/NONE
    res = dq_checker.check_and_record(row, _clean_ctx())

    assert res.overall is DataQualityStatus.PASS
    assert all(i.status is DataQualityStatus.PASS for i in res.items)
    assert len(res.items) == 8
    # Zone-C transitioned + audited (the store is the only writer; the checker its only caller)
    assert measurement_store.get_by_event_id("evt_ok").data_quality_status is DataQualityStatus.PASS
    assert measurement_store.dq_transitions[-1].to_status is DataQualityStatus.PASS
    assert measurement_store.dq_transitions[-1].actor == "data_quality_checker"
    assert audit.find("DATA_QUALITY_PASS")


def test_worst_status_fail_dominates(make_verified_row, dq_checker):
    row = make_verified_row("evt_bad", revenue=100000.0, order_code="ORD_B",
                            campaign_id="c1", adset_id="a1", ad_id="ad1")
    res = dq_checker.check(row, _clean_ctx(consent_valid=False))          # consent FAIL
    assert res.item(GateItem.CONSENT).status is DataQualityStatus.FAIL
    assert res.overall is DataQualityStatus.FAIL                          # worst dominates
    assert all(i.status in _ALL_STATES for i in res.items)               # NOTHING beyond PASS/HOLD/FAIL


def test_missing_signal_is_hold_not_pass(make_verified_row, dq_checker):
    row = make_verified_row("evt_hold", revenue=100000.0, order_code="ORD_C",
                            campaign_id="c1", adset_id="a1", ad_id="ad1")
    res = dq_checker.check(row, _clean_ctx(dashboard_has_trace=None))     # unknown -> HOLD (fail-closed)
    assert res.item(GateItem.DASHBOARD).status is DataQualityStatus.HOLD
    assert res.overall is DataQualityStatus.HOLD                          # no FAIL, but not PASS


def test_active_suppression_not_reflected_fails(make_verified_row, dq_checker):
    row = make_verified_row("evt_supp", revenue=100000.0, order_code="ORD_D",
                            campaign_id="c1", adset_id="a1", ad_id="ad1")
    res = dq_checker.check(row, _clean_ctx(suppression_active=True, suppression_reflected=False))
    assert res.item(GateItem.SUPPRESSION).status is DataQualityStatus.FAIL   # RULE-017
    assert res.overall is DataQualityStatus.FAIL


def test_unobserved_suppression_is_hold_not_pass(make_verified_row, dq_checker):
    """Adversarial-review regression: an UNOBSERVED suppression signal (suppression_active left unset/None) must
    be fail-closed HOLD, never PASS — otherwise a row could roll up to PASS with suppression never verified
    (RULE-017 / RULE-009 false-ALLOW)."""
    row = make_verified_row("evt_sup_unk", revenue=100000.0, order_code="ORD_U",
                            campaign_id="c1", adset_id="a1", ad_id="ad1")
    res = dq_checker.check(row, _clean_ctx(suppression_active=None))   # suppression not checked
    assert res.item(GateItem.SUPPRESSION).status is DataQualityStatus.HOLD
    assert res.overall is DataQualityStatus.HOLD                        # not PASS
