"""M6.2Q leg 3 / M6-CTR-015 / SMK-029 / RULE-003 / FAIL-007: CPA/ROAS-by-live_session.

Per live_session, from APPROVED imported spend only:
  * a CAMPAIGN-LEVEL approved spend record BOUND to a session (session_for_campaign) with spend_date in the derived
    window IS included (CPA/ROAS non-None) — the sum gates on the binding, NOT AdsSpendRecord.mapped;
  * CPA = spend / count(ORDER_VERIFIED in session); ROAS = verified_revenue / spend (RULE-003 lock — a quote in the
    window contributes 0);
  * spend OUTSIDE the window or on an UNBOUND campaign -> daily_total(), not session-attributed;
  * a session with spend + ZERO verified orders -> CPA None (no divide-by-zero) + ROAS 0.0 (wasted spend);
  * a session with NO bound spend -> CPA None + ROAS None (never a fabricated 0);
  * reading writes nothing (SMK-010 purity).
It is a STANDALONE reader (not a DataMart method, not a 15th metric), so the pinned allow-set + 14-metric tests stay
green (asserted by test_data_mart_support_view_only + test_kpi_formulas_verbatim, carried).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.measurement.dashboard.data_mart import AdsSpendRecord
from app.measurement.dashboard.session_roas import SessionRoasReader
from app.measurement.models.live_session_ads_binding import LiveSessionAdsBinding
from app.measurement.store.live_session_ads_binding_store import LiveSessionAdsBindingStore

T0 = datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc)     # ls_1 window start
TQ = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)    # quote + spend, inside ls_1 window
T1 = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)    # ls_1 window end
T2 = datetime(2026, 9, 2, 9, 0, 0, tzinfo=timezone.utc)     # ls_2 (zero-verified) single point
T3 = datetime(2026, 9, 3, 9, 0, 0, tzinfo=timezone.utc)     # ls_3 (no bound spend)
TOUT = datetime(2026, 9, 5, 9, 0, 0, tzinfo=timezone.utc)   # outside every window


def _binding_store():
    store = LiveSessionAdsBindingStore()
    store.bind(LiveSessionAdsBinding(live_session_id="ls_1", primary_campaign_id="camp_1"))
    store.bind(LiveSessionAdsBinding(live_session_id="ls_2", primary_campaign_id="camp_2"))
    return store


def _seed_sessions(measurement_store, make_verified_row, make_measurement_event):
    # ls_1: two ORDER_VERIFIED (revenue 250k each) + a QUOTE_SENT in-window (contributes 0, RULE-003)
    make_verified_row("evt_v1", revenue=250000.0, order_code="ORD1", live_session_id="ls_1", event_ts=T0)
    make_verified_row("evt_v2", revenue=250000.0, order_code="ORD2", live_session_id="ls_1", event_ts=T1)
    make_measurement_event("evt_q1", event_code="QUOTE_SENT", live_session_id="ls_1", event_ts=TQ)
    # ls_2: a QUOTE_SENT only -> ZERO verified orders (spend but no verified order)
    make_measurement_event("evt_q2", event_code="QUOTE_SENT", live_session_id="ls_2", event_ts=T2)
    # ls_3: a verified order but NO bound spend
    make_verified_row("evt_v3", revenue=90000.0, order_code="ORD3", live_session_id="ls_3", event_ts=T3)


def _spend_records():
    return [
        AdsSpendRecord(amount=100000.0, campaign_id="camp_1", spend_date=TQ),        # in ls_1 window -> attributed
        AdsSpendRecord(amount=60000.0, campaign_id="camp_2", spend_date=T2),         # in ls_2 window -> attributed
        AdsSpendRecord(amount=50000.0, campaign_id="camp_1", spend_date=TOUT),       # camp_1 bound but OUT of window
        AdsSpendRecord(amount=30000.0, campaign_id="camp_unbound", spend_date=TQ),   # unbound campaign
    ]


def test_campaign_level_bound_spend_is_included_not_gated_on_mapped(
    measurement_store, make_verified_row, make_measurement_event
):
    _seed_sessions(measurement_store, make_verified_row, make_measurement_event)
    records = _spend_records()
    # the ls_1 spend record is CAMPAIGN-LEVEL: adset/ad None -> .mapped is False, yet it MUST be included
    assert records[0].mapped is False
    reader = SessionRoasReader(measurement_store, records, _binding_store())

    s1 = reader.for_session("ls_1")
    assert s1.session_spend == 100000.0            # bound + in-window (NOT dropped by .mapped)
    assert s1.verified_orders == 2                 # the in-window QUOTE_SENT contributes 0 (RULE-003)
    assert s1.verified_revenue == 500000.0
    assert s1.cpa == 50000.0                        # 100000 / 2
    assert s1.roas == 5.0                           # 500000 / 100000


def test_zero_verified_session_is_cpa_none_roas_zero(
    measurement_store, make_verified_row, make_measurement_event
):
    _seed_sessions(measurement_store, make_verified_row, make_measurement_event)
    reader = SessionRoasReader(measurement_store, _spend_records(), _binding_store())
    s2 = reader.for_session("ls_2")
    assert s2.session_spend == 60000.0
    assert s2.verified_orders == 0
    assert s2.cpa is None                           # fail-closed: spend / 0 -> None (no divide-by-zero)
    assert s2.roas == 0.0                           # wasted spend: 0.0 revenue / spend>0 -> 0.0


def test_no_bound_spend_session_is_cpa_none_roas_none(
    measurement_store, make_verified_row, make_measurement_event
):
    _seed_sessions(measurement_store, make_verified_row, make_measurement_event)
    reader = SessionRoasReader(measurement_store, _spend_records(), _binding_store())
    s3 = reader.for_session("ls_3")
    assert s3.session_spend is None                 # no bound spend -> None, never a fabricated 0
    assert s3.cpa is None
    assert s3.roas is None                          # genuine 0/0 -> None (not 0.0)


def test_spend_outside_window_or_unbound_goes_to_daily_total(
    measurement_store, make_verified_row, make_measurement_event
):
    _seed_sessions(measurement_store, make_verified_row, make_measurement_event)
    reader = SessionRoasReader(measurement_store, _spend_records(), _binding_store())
    # camp_1 out-of-window (50000) + unbound camp (30000) = 80000; the two in-window records are session-attributed
    assert reader.daily_total() == 80000.0


def test_reading_writes_nothing(measurement_store, make_verified_row, make_measurement_event):
    _seed_sessions(measurement_store, make_verified_row, make_measurement_event)
    before = len(measurement_store.all())
    reader = SessionRoasReader(measurement_store, _spend_records(), _binding_store())
    reader.by_session()
    reader.daily_total()
    assert len(measurement_store.all()) == before   # SMK-010 purity: the reader mutates no store
