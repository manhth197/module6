"""Official smoke — slice M6.2F — M6-SMK-006 (doc ADS-P0-006), dashboard-render leg.

Authored by TESTER in M6-P1503 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1504. This is the
M6.2F DASHBOARD leg of SMK-006 (the smoke binds M6.2E + M6.2F): the M6.2E carried smoke
(test_smk_006_order_verified_full_source.py) proves the attribution + verified-revenue INPUT; this file proves
the ROAS/CPA/AOV dashboard READS that input and updates. Governance is immutable:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 406):

    Kịch bản (verbatim):          "ORDER_VERIFIED có campaign/adset/ad đầy đủ"
    Kết quả phải đạt (verbatim):  "ROAS/CPA/AOV dashboard cập nhật"

Revenue is the set-once Zone-B value the M6.2E materializer wrote on the ORDER_VERIFIED path; the dashboard's
revenue metrics are verified-only (RULE-003 / FAIL-001). Every division is fail-closed (missing denominator ->
None, never fabricated). Reuses shared conftest fixtures (make_verified_row, make_dashboard_deps). All ids
synthetic; no PII.
"""
from __future__ import annotations

from app.api.dashboard import handle_dashboard_request
from app.measurement.dashboard.data_mart import AdsSpendRecord, ConsumedFacts


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_006_verified_order_updates_roas_cpa_aov(make_verified_row, make_dashboard_deps):
    """M6-SMK-006 "ORDER_VERIFIED có campaign/adset/ad đầy đủ" -> "ROAS/CPA/AOV dashboard cập nhật"."""
    make_verified_row(
        "evt_v1", revenue=250000.0, order_code="ORD_1", page_id="p_home",
        campaign_id="c1", adset_id="a1", ad_id="ad1",
    )
    consumed = ConsumedFacts(ads_spend=(AdsSpendRecord(100000.0, "c1", "a1", "ad1"),))
    view = handle_dashboard_request({}, make_dashboard_deps(consumed))
    m = {x.name: x for x in view.metrics}

    assert m["Revenue Verified"].value == 250000.0
    assert m["Ads Spend"].value == 100000.0
    assert m["ROAS"].value == 2.5           # 250000 / 100000
    assert m["CPA"].value == 100000.0       # spend / number_of_ORDER_VERIFIED(1)
    assert m["AOV"].value == 250000.0       # revenue / verified_orders(1)
    # evidence-first: the revenue metrics carry a source trace + a (masked) sample evidence ref
    assert m["Revenue Verified"].has_trace_and_evidence
    assert m["ROAS"].has_trace_and_evidence
    assert view.overall_data_quality == "PASS"


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_006_neg_absent_spend_fail_closed_roas(make_verified_row, make_dashboard_deps):
    """A verified order with NO ads-spend import: ROAS / CPA are fail-closed None (denominator absent, never
    fabricated), while Revenue Verified and AOV — which do not need spend — still update."""
    make_verified_row("evt_v2", revenue=250000.0, order_code="ORD_2", campaign_id="c1", adset_id="a1", ad_id="ad1")
    view = handle_dashboard_request({}, make_dashboard_deps())   # no consumed spend
    m = {x.name: x for x in view.metrics}

    assert m["Revenue Verified"].value == 250000.0
    assert m["AOV"].value == 250000.0
    assert m["Ads Spend"].value is None
    assert m["ROAS"].value is None          # verified revenue / None spend -> fail-closed
    assert m["CPA"].value is None           # None spend / count -> fail-closed


def test_smk_006_neg_unmapped_spend_excluded(make_verified_row, make_dashboard_deps):
    """Only spend mapped to campaign/adset/ad counts (doc §14 note): an unmapped spend record is excluded, so
    Ads Spend is fail-closed None and ROAS cannot be computed from unmapped spend."""
    make_verified_row("evt_v3", revenue=250000.0, order_code="ORD_3", campaign_id="c1", adset_id="a1", ad_id="ad1")
    consumed = ConsumedFacts(ads_spend=(AdsSpendRecord(100000.0),))   # no campaign/adset/ad -> unmapped
    view = handle_dashboard_request({}, make_dashboard_deps(consumed))
    m = {x.name: x for x in view.metrics}

    assert m["Ads Spend"].value is None     # unmapped spend excluded -> fail-closed
    assert m["ROAS"].value is None


def test_smk_006_dashboard_updates_as_more_orders_verify(make_verified_row, make_dashboard_deps):
    """The dashboard aggregates update (cập nhật) as more verified orders arrive: two verified orders move CPA and
    AOV to reflect the new count / total, sourced from verified revenue only."""
    make_verified_row("evt_a", revenue=200000.0, order_code="ORD_A", campaign_id="c1", adset_id="a1", ad_id="ad1")
    make_verified_row("evt_b", revenue=100000.0, order_code="ORD_B", campaign_id="c1", adset_id="a1", ad_id="ad1")
    consumed = ConsumedFacts(ads_spend=(AdsSpendRecord(150000.0, "c1", "a1", "ad1"),))
    view = handle_dashboard_request({}, make_dashboard_deps(consumed))
    m = {x.name: x for x in view.metrics}

    assert m["Revenue Verified"].value == 300000.0     # 200000 + 100000 (verified only)
    assert m["CPA"].value == 75000.0                   # 150000 spend / 2 ORDER_VERIFIED
    assert m["AOV"].value == 150000.0                  # 300000 / 2 verified orders
    assert m["ROAS"].value == 2.0                      # 300000 / 150000
