import math
from decimal import Decimal
from datetime import datetime, timezone

from app.measurement.store.measurement_event_store import MeasurementEventStore
from app.measurement.models.measurement_event import AdsMeasurementEvent
from app.measurement.dashboard.data_mart import DataMart, ConsumedFacts, AdsSpendRecord
from app.measurement.dashboard.kpi_metrics import compute_metrics
from app.api.dashboard import DashboardDeps, handle_dashboard_request
from app.measurement.quality.data_quality_checker import DataQualityChecker, DQContext

TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)

def zoneA(store, event_id, code="ORDER_VERIFIED", key=None):
    row = AdsMeasurementEvent(
        event_id=event_id, event_code=code, event_ts=TS,
        idempotency_key=key or ("idem_" + event_id), correlation_id="corr_" + event_id,
        ingested_at=TS,
    )
    store.insert(row)
    return row

def book(store, event_id, revenue, order_code="ORD", code="ORDER_VERIFIED"):
    zoneA(store, event_id, code=code)
    return store.materialize(event_id, attribution_context={"conflict_status":"NONE","source_confidence":"HIGH"},
                             revenue_value=revenue, order_code=order_code, verified=True)

def full_ctx():
    return DQContext(event_registered=True, event_owner_known=True, consent_valid=True,
                     no_duplicate=True, identity_mapped=True, suppression_active=False,
                     dashboard_has_trace=True)

def sep(t): print("\n===== " + t + " =====")

sep("V1 NaN revenue")
s = MeasurementEventStore()
r = book(s, "e_nan", float("nan"), order_code="ORD_NAN")
print("stored revenue_value:", r.row.revenue_value)
m = DataMart(s)
print("verified_rows count:", len(m.verified_rows()))
print("revenue_verified():", m.revenue_verified(), "isnan:", math.isnan(m.revenue_verified()))
row = s.get_by_event_id("e_nan")
dq = DataQualityChecker().check(row, full_ctx())
print("per-row Verified Revenue DQ + overall:",
      [it.status.value for it in dq.items if it.item.value == "Verified Revenue"], dq.overall.value)

sep("V2 +Inf revenue, ROAS")
s = MeasurementEventStore()
book(s, "e_inf", float("inf"), order_code="ORD_INF")
cf = ConsumedFacts(ads_spend=(AdsSpendRecord(1000.0, "c", "a", "ad"),))
m = DataMart(s, cf)
mets = {x.name: x.value for x in compute_metrics(m)}
print("Revenue Verified:", mets["Revenue Verified"], "ROAS:", mets["ROAS"], "CPA:", mets["CPA"])

sep("V3 negative revenue")
s = MeasurementEventStore()
book(s, "e_neg", -500000.0, order_code="ORD_NEG")
m = DataMart(s)
print("revenue_verified():", m.revenue_verified())
row = s.get_by_event_id("e_neg")
dq = DataQualityChecker().check(row, full_ctx())
print("Verified Revenue DQ:", [it.status.value for it in dq.items if it.item.value == "Verified Revenue"],
      "overall:", dq.overall.value)

sep("V4 bool True revenue")
s = MeasurementEventStore()
r = book(s, "e_bool", True, order_code="ORD_BOOL")
print("stored:", repr(r.row.revenue_value))
m = DataMart(s)
print("revenue_verified():", m.revenue_verified())

sep("V5 Decimal+float mix crash")
s = MeasurementEventStore()
book(s, "e_dec", Decimal("100000"), order_code="ORD_DEC")
book(s, "e_flt", 250000.0, order_code="ORD_FLT")
m = DataMart(s)
try:
    print("revenue_verified():", m.revenue_verified())
except Exception as ex:
    print("CRASH revenue_verified:", type(ex).__name__, ex)
try:
    handle_dashboard_request({}, DashboardDeps(mart=m))
    print("dashboard OK")
except Exception as ex:
    print("CRASH handle_dashboard_request:", type(ex).__name__, ex)

sep("V6 NaN mapped spend")
s = MeasurementEventStore()
book(s, "e_ok", 300000.0, order_code="ORD_OK")
cf = ConsumedFacts(ads_spend=(AdsSpendRecord(float("nan"), "c", "a", "ad"),))
m = DataMart(s, cf)
mets = {x.name: x.value for x in compute_metrics(m)}
print("ads_spend:", m.ads_spend(), "ROAS:", mets["ROAS"], "CPA:", mets["CPA"])

sep("V7 empty store")
s = MeasurementEventStore()
m = DataMart(s)
view = handle_dashboard_request({}, DashboardDeps(mart=m))
rv = view.metric("Revenue Verified")
print("Revenue Verified value:", rv.value, "evidence_ref:", rv.sample_evidence_ref,
      "has_trace_and_evidence:", rv.has_trace_and_evidence)
print("overall_data_quality:", view.overall_data_quality)

sep("V8 store trusts verified flag on QUOTE_SENT row")
s = MeasurementEventStore()
zoneA(s, "e_quote", code="QUOTE_SENT")
res = s.materialize("e_quote", attribution_context={"conflict_status":"NONE","source_confidence":"HIGH"},
                    revenue_value=9_999_999_999.0, order_code="ORD_QUOTE", verified=True)
print("stored revenue on QUOTE_SENT row:", res.row.revenue_value, "event_code:", res.row.event_code)
m = DataMart(s)
print("dashboard revenue_verified():", m.revenue_verified())
row = s.get_by_event_id("e_quote")
dq = DataQualityChecker().check(row, full_ctx())
print("per-row Verified Revenue DQ:", [it.status.value for it in dq.items if it.item.value == "Verified Revenue"])

sep("V9 overflow to inf")
s = MeasurementEventStore()
book(s, "e_big1", 1e308, order_code="ORD_B1")
book(s, "e_big2", 1e308, order_code="ORD_B2")
m = DataMart(s)
print("revenue_verified():", m.revenue_verified(), "isinf:", math.isinf(m.revenue_verified()))

sep("V10 boxes value not sanity-checked")
s = MeasurementEventStore()
book(s, "b1", 100.0, order_code="ORD1")
book(s, "b2", 100.0, order_code="ORD2")
cf = ConsumedFacts(boxes_by_order={"ORD1": True, "ORD2": -5})
m = DataMart(s, cf)
print("verified_boxes():", m.verified_boxes())
mets = {x.name: x.value for x in compute_metrics(m)}
print("Boxes per Order:", mets["Boxes per Order"])
