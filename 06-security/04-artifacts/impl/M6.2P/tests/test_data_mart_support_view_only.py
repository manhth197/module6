"""M6.2F leg 1 / M6-SMK-010 / M6-FAIL-005: the Data Mart is a SUPPORT VIEW ONLY (RULE-012). It exposes ONLY
read/aggregate methods — there is NO write / CRM / pricing / Diamond / scale / trigger surface, so it can never
become a trigger owner. "Data Mart tạo trigger CRM/scale -> Fail - Data Mart chỉ support view."
"""
from __future__ import annotations


def test_data_mart_exposes_only_read_aggregate_methods(make_data_mart):
    mart = make_data_mart()
    public = {n for n in dir(mart) if not n.startswith("_") and callable(getattr(mart, n))}
    read_only_allowed = {
        "verified_rows", "revenue_verified", "verified_order_count", "crm_revenue", "diamond_revenue",
        "verified_boxes", "event_count", "ads_spend", "cod_orders", "cod_fail", "sample_verified_correlation",
    }
    assert public <= read_only_allowed, f"unexpected (non-read-only) method(s): {public - read_only_allowed}"
    # no trigger/write verb exists at all (RULE-012, FAIL-005)
    for forbidden in ("write", "insert", "update", "delete", "trigger", "send", "scale", "publish",
                      "enqueue", "create_crm", "crm", "price", "budget"):
        assert not hasattr(mart, forbidden)


def test_dashboard_deps_carry_only_the_read_only_mart(make_dashboard_deps):
    deps = make_dashboard_deps()
    assert set(vars(deps).keys()) == {"mart"}          # no store-writer / transport / trigger handle
    for forbidden in ("transport", "send", "dispatch", "scale", "store", "writer", "trigger", "crm"):
        assert not hasattr(deps, forbidden)
