"""Official smoke — slice M6.2L — M6-SMK-023 (proposed — HARDENING, owner review).

Authored by TESTER in M6-P2103 (mode=build, "do not yet run"); EXECUTED and its result recorded in M6-P2104
(TESTER_RUN -> 04-artifacts/test-reports/M6.2L/SMOKE_RESULTS.md). Closes audit item B4 (FIX_M6 2026-09-03).
Governance is immutable here: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below
flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (proposed additions row M6-SMK-023):

    Scenario (verbatim):   "In-process QUOTE_SENT row + store.materialize(revenue_value>0, verified=True)"
    Expected (verbatim):   "no revenue set (event_code enforced at materialize); dashboard Revenue Verified = 0 and
                           ROAS = 0 (event_code filter at verified_rows)"

Only ORDER_VERIFIED is revenue (RULE-003 / FAIL-001). The lock holds at BOTH choke points: store.materialize()
self-checks the STORED row's OWN event_code (not a caller boolean) and fail-closed DROPS illegitimate revenue
WITHOUT raising; data_mart.verified_rows() + growth.reads.verified_rows() apply an event_code==ORDER_VERIFIED filter.

TESTER note on "ROAS = 0" (verbatim expected vs frozen code): with zero verified revenue AND no ads spend, ROAS is
`safe_div(0, None) -> None` (fail-closed, RULE-003) — this is the register's "ROAS = 0" realized as the fail-closed
None (no revenue, no spend => no ROAS). The assertion below matches the frozen code (`ROAS is None`); the register
wording is flagged as a non-blocking operator-hygiene reword in the evidence. Reuses the coder's B4 leg pattern +
the shared conftest fixtures (measurement_store, make_measurement_event, make_dashboard_deps, make_verified_row).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.api.dashboard import handle_dashboard_request
from app.measurement.dashboard.data_mart import DataMart
from app.measurement.growth.reads import verified_rows as growth_verified_rows
from app.measurement.models.measurement_event import AdsMeasurementEvent

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_023_quote_materialized_verified_sets_no_revenue_and_zero_dashboard(
    measurement_store, make_measurement_event, make_dashboard_deps
):
    """M6-SMK-023 "In-process QUOTE_SENT row + store.materialize(revenue_value>0, verified=True)" -> "no revenue set
    (event_code enforced at materialize); dashboard Revenue Verified = 0 and ROAS = 0 (event_code filter at
    verified_rows)".

    A caller LIES with verified=True + a positive revenue on a QUOTE_SENT row (the audit hole). materialize()
    self-checks the STORED event_code and fail-closed DROPS the revenue WITHOUT raising; the dashboard reads
    Revenue Verified = 0.0 and ROAS = None (no revenue + no spend -> the fail-closed form of "ROAS = 0").
    """
    make_measurement_event("e_smk023q", event_code="QUOTE_SENT")
    res = measurement_store.materialize(
        "e_smk023q", attribution_context={}, revenue_value=500000.0, order_code="ord_bad", verified=True
    )
    row = measurement_store.get_by_event_id("e_smk023q")
    assert row.revenue_value is None            # event_code self-check dropped the illegitimate revenue ...
    assert row.order_code is None
    assert res.row.revenue_value is None        # ... WITHOUT raising (the store returned a revenue-less row)

    dv = handle_dashboard_request({}, make_dashboard_deps())
    assert dv.metric("Revenue Verified").value == 0.0
    assert dv.metric("ROAS").value is None      # no verified revenue + no spend -> no ROAS (RULE-003 fail-closed)


# --- negative / fail-closed: BOTH verified_rows choke points exclude a leaked QUOTE_SENT row ------
def test_smk_023_neg_verified_rows_filter_excludes_leaked_quote_row_both_choke_points():
    """Even if a QUOTE_SENT row somehow held a revenue_value (built directly, bypassing the store), BOTH
    verified_rows choke points exclude it by the event_code filter -> Revenue Verified stays 0."""
    leaked = AdsMeasurementEvent(
        event_id="bad_smk023", event_code="QUOTE_SENT", event_ts=_TS, idempotency_key="k",
        correlation_id="c", revenue_value=999000.0, order_code="o",
    )

    class _Store:
        def all(self):
            return (leaked,)

    assert DataMart(_Store()).verified_rows() == ()          # data_mart choke point
    assert DataMart(_Store()).revenue_verified() == 0.0
    assert growth_verified_rows(_Store()) == []              # growth.reads choke point


# --- positive control: a genuine ORDER_VERIFIED order IS counted (non-vacuous) --------------------
def test_smk_023_control_genuine_order_verified_still_counts(make_verified_row, make_dashboard_deps):
    """Non-vacuity control: a real verified order IS revenue — so the lock excludes quotes, not everything."""
    make_verified_row("e_smk023v", revenue=180000.0, order_code="ORD_SMK023", campaign_id="c", adset_id="a", ad_id="d")
    dv = handle_dashboard_request({}, make_dashboard_deps())
    assert dv.metric("Revenue Verified").value == 180000.0
