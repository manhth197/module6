"""Official smoke — slice M6.2F — M6-SMK-010 (doc ADS-P0-010) / M6-FAIL-005.

Authored by TESTER in M6-P1503 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1504. Governance is
immutable: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 410):

    Kịch bản (verbatim):          "Data Mart tạo trigger CRM/scale"
    Kết quả phải đạt (verbatim):  "Fail - Data Mart chỉ support view"

The Data Mart is a SUPPORT VIEW ONLY (RULE-012 / FAIL-005): it exposes ONLY read/aggregate methods — there is NO
write / CRM / pricing / Diamond / budget-scale / trigger / send / publish surface, so a CRM/scale trigger simply
cannot be created from it (it can never become a trigger owner). The dashboard deps + view carry no
writer/transport/trigger handle either, and reading the dashboard mutates nothing. Reuses shared conftest
fixtures. All ids synthetic; no PII.
"""
from __future__ import annotations

from app.api.dashboard import handle_dashboard_request

_READ_ONLY_ALLOWED = {
    "verified_rows", "revenue_verified", "verified_order_count", "crm_revenue", "diamond_revenue",
    "verified_boxes", "event_count", "ads_spend", "cod_orders", "cod_fail", "sample_verified_correlation",
}
_FORBIDDEN_VERBS = (
    "write", "insert", "update", "delete", "trigger", "send", "dispatch", "scale", "publish", "enqueue",
    "crm", "create_crm", "price", "budget",
)


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_010_data_mart_exposes_only_read_aggregate_methods(make_data_mart):
    """M6-SMK-010 "Data Mart tạo trigger CRM/scale" -> "Fail - Data Mart chỉ support view".

    There is NO trigger/write surface to create a CRM/scale trigger with — the mart is read-only aggregates.
    """
    mart = make_data_mart()
    public = {n for n in dir(mart) if not n.startswith("_") and callable(getattr(mart, n))}
    assert public <= _READ_ONLY_ALLOWED, f"unexpected (non-read-only) method(s): {public - _READ_ONLY_ALLOWED}"
    # no CRM/scale/trigger/write verb exists AT ALL (RULE-012, FAIL-005) — the trigger cannot be created
    for forbidden in _FORBIDDEN_VERBS:
        assert not hasattr(mart, forbidden), f"support view must not expose {forbidden!r}"


def test_smk_010_dashboard_deps_and_view_carry_no_trigger_handle(make_dashboard_deps):
    """The dashboard dependency container holds ONLY the read-only mart (no store-writer / transport / trigger),
    and the returned view carries no write/trigger handle."""
    deps = make_dashboard_deps()
    assert set(vars(deps).keys()) == {"mart"}
    for forbidden in ("transport", "send", "dispatch", "scale", "store", "writer", "trigger", "crm"):
        assert not hasattr(deps, forbidden)

    view = handle_dashboard_request({}, deps)
    for forbidden in ("trigger", "send", "dispatch", "scale", "publish", "enqueue", "write", "crm"):
        assert not hasattr(view, forbidden), f"dashboard view must not expose {forbidden!r}"


def test_smk_010_neg_reading_dashboard_does_not_mutate_store(
    make_verified_row, make_dashboard_deps, measurement_store
):
    """A support view only READS: computing the dashboard twice does not insert, transition, or otherwise mutate
    the measurement store (no trigger side effect)."""
    make_verified_row("evt_v", revenue=120000.0, order_code="ORD_1", campaign_id="c1", adset_id="a1", ad_id="ad1")
    deps = make_dashboard_deps()

    before = len(measurement_store.all())
    handle_dashboard_request({}, deps)
    handle_dashboard_request({}, deps)
    after = len(measurement_store.all())
    assert before == after, "reading the dashboard must not mutate the store (support view only)"
