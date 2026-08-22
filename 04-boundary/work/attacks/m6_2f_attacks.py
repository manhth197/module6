"""M6-P1505 BOUNDARY_ADVERSARY executed attack harness for slice M6.2F (KPI Dashboard + Data Quality Gate).

READ-ONLY adversary: this script IMPORTS the FROZEN staged M6.2F app and drives the REAL code paths. It never
modifies application code, never writes to 04-artifacts/state, never sends anything (external_send stays OFF).

In-scope fail gates ATTACKED: M6-FAIL-001 (revenue misuse) and M6-FAIL-005 (Data Mart used as a trigger owner).
In-scope rules: RULE-003 (revenue only ORDER_VERIFIED), RULE-012 (data mart is a support view only),
RULE-015 (nothing PASS without audit/evidence/trace), RULE-017 (suppression/risk locks reflected in gates).

Every claimed breach is EXECUTED here before it is recorded. Outcome classes:
  DEFENDED      - the invariant held; the attack was refused / degraded / fail-closed.
  OPEN_NONGATE  - a real weakness that does NOT trip an in-scope fail gate (armed-not-fired / DQ-caught / not
                  channel-reachable). Routed to CODER or the M6.2F security prompt (M6-P1506).
  NOTE          - an observation / robustness remark, no gate impact.
  BREACH        - an in-scope fail gate (FAIL-001/005) actually tripped. Any BREACH => evidence status FAIL.

Launcher: py -3.12 -B  (byte-clean; no __pycache__). PII-shaped probes are assembled at runtime, never echoed raw.
"""
from __future__ import annotations

import math
import sys
import tokenize
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path

# --- locate the FROZEN staged M6.2F app (read-only import) ------------------------------------------
HERE = Path(__file__).resolve()
PACK_ROOT = HERE.parents[3]                      # attacks -> work -> 04-boundary -> <pack root>
IMPL = PACK_ROOT / "04-artifacts" / "impl" / "M6.2F"
if not IMPL.exists():
    IMPL = Path(r"D:\M6\Module6-workspace\04-artifacts\impl\M6.2F")
sys.path.insert(0, str(IMPL))

from app import config
from app.measurement.audit import AuditLog
from app.measurement.attribution.materializer import AttributionMaterializer
from app.measurement.attribution.resolver import AttributionResolver
from app.measurement.dashboard.data_mart import AdsSpendRecord, ConsumedFacts, DataMart
from app.measurement.dashboard.kpi_metrics import compute_metrics
from app.measurement.dashboard.models import DashboardView, MetricResult
from app.api.dashboard import DashboardDeps, handle_dashboard_request
from app.measurement.masking import mask
from app.measurement.models.conversion_event import ConversionEvent
from app.measurement.models.measurement_event import AdsMeasurementEvent, DataQualityStatus
from app.measurement.quality.data_quality_check import (
    AdsDataQualityCheck,
    GateItem,
    GateStatus,
    worst_status,
)
from app.measurement.quality.data_quality_checker import DataQualityChecker, DQContext
from app.measurement.store.measurement_event_store import (
    MeasurementEventStore,
    MeasurementStoreViolation,
)

FIXED_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)

RESULTS = []            # list of (attack_id, gate, klass, detail)
BREACHES = []           # in-scope FAIL-001/005 breaches


def record(attack_id, gate, klass, detail):
    assert klass in ("DEFENDED", "OPEN_NONGATE", "NOTE", "BREACH"), klass
    RESULTS.append((attack_id, gate, klass, detail))
    if klass == "BREACH":
        BREACHES.append((attack_id, gate, detail))
    print(f"[{klass:12}] {attack_id:26} {gate:9} | {detail}")


# --- faithful factories (mirror tests/conftest.py: Zone-A insert -> materialize -> mart) -------------
def new_store():
    return MeasurementEventStore()


def insert_event(store, event_id, event_code="ORDER_VERIFIED", **over):
    base = dict(
        event_id=event_id, event_code=event_code, event_ts=FIXED_TS,
        idempotency_key=over.pop("idempotency_key", f"idem_{event_id}"),
        correlation_id=over.pop("correlation_id", "corr_ame"), ingested_at=FIXED_TS,
    )
    base.update(over)
    row = AdsMeasurementEvent(**base)
    store.insert(row)
    return row


def make_conversion(event_code, source_event_id, **over):
    base = dict(
        conversion_id=f"conv_{event_code}_{source_event_id}", event_code=event_code,
        source_event_id=source_event_id, correlation_id="corr_c",
        customer_or_guest_key="guest_mapped_ok", consent_snapshot_id="cs_valid",
        occurred_at=FIXED_TS, idempotency_key=f"idem_{event_code}_{source_event_id}",
    )
    base.update(over)
    return ConversionEvent(**base)


def verified_row(store, event_id, *, revenue, order_code, signals=None, event_code="ORDER_VERIFIED",
                 verified_codes=("ORDER_VERIFIED",), **event_over):
    """Seed Zone-A + materialize Zone-B verified revenue via the REAL CTR-023 materializer."""
    ev = insert_event(store, event_id, event_code=event_code, **event_over)
    conv = make_conversion(event_code, source_event_id=event_id,
                           revenue_value=float(revenue), currency="VND", order_code=order_code)
    mat = AttributionMaterializer(store, AttributionResolver(), AuditLog(),
                                  verified_event_codes=verified_codes)
    mat.materialize(ev, conv, signals=signals)
    return store.get_by_event_id(event_id)


def full_ad_signals():
    return {"campaign_name": "c-name", "adset_name": "a-name", "ad_name": "ad-name"}


# ================================================================================================
# GROUP A - M6-FAIL-001 : revenue misuse (verified-only revenue, RULE-003)
# ================================================================================================
def group_a():
    # A1 quote created, never ordered -> not revenue, no ROAS (SMK-004)
    st = new_store()
    insert_event(st, "e_quote", event_code="QUOTE_SENT")
    mart = DataMart(st, ConsumedFacts(ads_spend=(AdsSpendRecord(100000.0, "c1", "a1", "ad1"),)))
    rv = mart.revenue_verified()
    metrics = {m.name: m for m in compute_metrics(mart)}
    roas = metrics["ROAS"].value
    quote_in_funnel = mart.event_count("QUOTE_SENT")
    # FAIL-001 invariant: the quote never becomes revenue. ROAS = 0.0 (0 verified revenue / real spend) is the
    # CORRECT, non-inflating result (tester SMK-004 asserts ROAS==0.0 with spend, None without) -- it is never a
    # positive/fabricated number. The breach would be revenue_verified>0 or ROAS>0.
    if rv == 0.0 and roas in (None, 0.0) and quote_in_funnel == 1:
        record("A1-quote-not-revenue", "FAIL-001", "DEFENDED",
               f"QUOTE_SENT+spend -> revenue_verified={rv}, ROAS={roas} (0 verified rev / spend), quote in funnel only")
    else:
        record("A1-quote-not-revenue", "FAIL-001", "BREACH",
               f"quote leaked into revenue: revenue={rv}, ROAS={roas}")

    # A2 order draft / created, not verified -> not Verified Revenue (SMK-005)
    st = new_store()
    insert_event(st, "e_draft", event_code="ORDER_CREATED")
    mart = DataMart(st)
    rv = mart.revenue_verified()
    record("A2-draft-not-revenue", "FAIL-001",
           "DEFENDED" if rv == 0.0 else "BREACH",
           f"ORDER_CREATED (draft) -> revenue_verified={rv} (verified_order_count={mart.verified_order_count()})")

    # A3 the exact fail-gate non-revenue states: quote/cart/order-draft/payment-waiting/COD-waiting
    st = new_store()
    for i, code in enumerate(("QUOTE_SENT", "CART_UPDATED", "ORDER_CREATED",
                              "PAYMENT_WAITING", "COD_WAITING")):
        insert_event(st, f"e_nr_{i}", event_code=code)
    mart = DataMart(st)
    rv = mart.revenue_verified()
    record("A3-nonrevenue-states", "FAIL-001",
           "DEFENDED" if rv == 0.0 else "BREACH",
           f"5 non-verified states (quote/cart/draft/payment-waiting/cod-waiting) -> revenue_verified={rv}")

    # A4 materializer fed a NON-ORDER_VERIFIED conversion carrying revenue -> books NOTHING (real caller)
    st = new_store()
    row = verified_row(st, "e_q999", revenue=999999.0, order_code="ORDQ",
                       event_code="QUOTE_SENT")   # verified_codes default ORDER_VERIFIED -> not verified
    mart = DataMart(st)
    if row.revenue_value is None and mart.revenue_verified() == 0.0:
        record("A4-materializer-quote-rev", "FAIL-001", "DEFENDED",
               f"QUOTE_SENT conversion w/ revenue 999999 -> row.revenue_value={row.revenue_value}, mart total=0.0")
    else:
        record("A4-materializer-quote-rev", "FAIL-001", "BREACH",
               f"materializer booked revenue on QUOTE_SENT: row.revenue_value={row.revenue_value}")

    # A5 (carried M6.2E O-4) a MIS-WIRED materializer (verified_event_codes includes QUOTE_SENT) WOULD book
    #    revenue on a quote -> mart would sum it. Is it (a) channel-reachable? no (default is the hardcoded
    #    ORDER_VERIFIED constant; no config knob). (b) caught downstream? yes: the DQ Verified-Revenue item
    #    FAILs the row (event_code != ORDER_VERIFIED). Classified armed-not-fired.
    st = new_store()
    row = verified_row(st, "e_mis", revenue=777000.0, order_code="ORDX",
                       event_code="QUOTE_SENT", verified_codes=("QUOTE_SENT",))
    mart = DataMart(st)
    dq = DataQualityChecker().check(store_row(st, "e_mis"))
    vr_item = dq.item(GateItem.VERIFIED_REVENUE)
    booked = mart.revenue_verified()
    if booked > 0.0 and vr_item.status is GateStatus.FAIL and dq.overall is GateStatus.FAIL:
        record("A5-miswire-verified-codes", "FAIL-001", "OPEN_NONGATE",
               f"mis-wired verified_event_codes=('QUOTE_SENT',) books {booked} BUT not channel-reachable "
               f"(default hardcoded ORDER_VERIFIED) AND DQ Verified-Revenue={vr_item.status.value}, "
               f"overall={dq.overall.value} -> row flagged, defense-in-depth (route CODER/M6-P1506)")
    else:
        record("A5-miswire-verified-codes", "FAIL-001", "NOTE",
               f"mis-wire booked={booked}, DQ verified_revenue={vr_item.status.value}, overall={dq.overall.value}")

    # A6 store.materialize trust boundary: it sets revenue on verified=True + order_code WITHOUT re-deriving
    #    event_code. A mis-wired caller could set revenue on a non-verified row; the ONLY caller (materializer)
    #    derives verified from event_code, and the DQ gate FAILs such a row.
    st = new_store()
    insert_event(st, "e_trust", event_code="QUOTE_SENT")
    st.materialize("e_trust", attribution_context={"source_confidence": "LOW", "conflict_status": "NONE"},
                   revenue_value=500000.0, order_code="ORDT", verified=True)
    mart = DataMart(st)
    dq = DataQualityChecker().check(store_row(st, "e_trust"))
    record("A6-store-verified-bool", "FAIL-001", "OPEN_NONGATE",
           f"store trusts caller 'verified' bool (event_code NOT re-checked): revenue set={mart.revenue_verified()} "
           f"on a QUOTE_SENT row; only caller (materializer) guards event_code; DQ overall={dq.overall.value} "
           f"(Verified-Revenue={dq.item(GateItem.VERIFIED_REVENUE).status.value}) -> armed-not-fired")

    # A7 frozen row: a dashboard consumer cannot mutate revenue_value on a row obtained via the mart
    st = new_store()
    verified_row(st, "e_fr", revenue=250000.0, order_code="ORDF",
                 signals=full_ad_signals(), campaign_id="c1", adset_id="a1", ad_id="ad1")
    mart = DataMart(st)
    r = mart.verified_rows()[0]
    try:
        r.revenue_value = 9_999_999.0   # type: ignore[misc]
        record("A7-frozen-row-mutate", "FAIL-001", "BREACH",
               f"mutated a verified row's revenue_value to {r.revenue_value}")
    except FrozenInstanceError:
        record("A7-frozen-row-mutate", "FAIL-001", "DEFENDED",
               "AdsMeasurementEvent is frozen -> revenue_value assignment raises FrozenInstanceError")

    # A8 DQ Verified-Revenue item: a non-verified figure presented as revenue -> FAIL (SMK-015)
    checker = DataQualityChecker()
    q_ev = AdsMeasurementEvent(event_id="dq_q", event_code="QUOTE_SENT", event_ts=FIXED_TS,
                               idempotency_key="ik_q", correlation_id="corr_q", revenue_value=123456.0)
    dq = checker.check(q_ev)
    ov_ev = AdsMeasurementEvent(event_id="dq_ov", event_code="ORDER_VERIFIED", event_ts=FIXED_TS,
                                idempotency_key="ik_ov", correlation_id="corr_v", revenue_value=200000.0,
                                order_code=None)   # verified code but NO order_code -> incomplete
    dq2 = checker.check(ov_ev)
    if (dq.item(GateItem.VERIFIED_REVENUE).status is GateStatus.FAIL and dq.overall is GateStatus.FAIL
            and dq2.item(GateItem.VERIFIED_REVENUE).status is GateStatus.FAIL):
        record("A8-dq-verified-revenue", "FAIL-001", "DEFENDED",
               "revenue on QUOTE_SENT -> DQ Verified-Revenue FAIL/overall FAIL; ORDER_VERIFIED w/o order_code -> FAIL")
    else:
        record("A8-dq-verified-revenue", "FAIL-001", "BREACH",
               f"DQ passed a non-verified revenue: quote={dq.item(GateItem.VERIFIED_REVENUE).status.value}")

    # A9 NaN revenue poison (carried M6.2E O-5): non-finite revenue poisons the total; set-once replay breaks.
    st = new_store()
    insert_event(st, "e_nan", event_code="ORDER_VERIFIED")
    st.materialize("e_nan", attribution_context={"source_confidence": "HIGH", "conflict_status": "NONE"},
                   revenue_value=float("nan"), order_code="ORDN", verified=True)
    mart = DataMart(st)
    total = mart.revenue_verified()
    replay_ok = True
    try:
        st.materialize("e_nan", attribution_context={"source_confidence": "HIGH", "conflict_status": "NONE"},
                       revenue_value=float("nan"), order_code="ORDN", verified=True)
    except MeasurementStoreViolation:
        replay_ok = False   # nan != nan -> identical replay wrongly raises
    record("A9-nan-revenue-poison", "FAIL-001", "NOTE",
           f"NaN revenue poisons revenue_verified={total!r} and breaks idempotent replay (raised={not replay_ok}); "
           f"root cause is non-finite revenue at ingest -> DQ/robustness (M6.2G DQ / M6-P1506); not inflation")

    # A10 negative revenue: store accepts it; understates (never inflates); no sign check anywhere
    st = new_store()
    insert_event(st, "e_neg", event_code="ORDER_VERIFIED")
    st.materialize("e_neg", attribution_context={"source_confidence": "HIGH", "conflict_status": "NONE"},
                   revenue_value=-100000.0, order_code="ORDG", verified=True)
    record("A10-negative-revenue", "FAIL-001", "NOTE",
           f"negative revenue accepted -> revenue_verified={DataMart(st).revenue_verified()} (understates, not a "
           f"FAIL-001 inflation); no >=0 check in store/DQ -> DQ hardening (M6-P1506)")

    # A11 crm/diamond revenue are verified-only SUBSETS, never added to Revenue Verified (no double count)
    st = new_store()
    verified_row(st, "e_crm", revenue=100000.0, order_code="ORDCRM", signals={"crm": True})
    verified_row(st, "e_dia", revenue=100000.0, order_code="ORDDIA", signals={"diamond_id": "d1"})
    verified_row(st, "e_ad", revenue=100000.0, order_code="ORDAD",
                 signals=full_ad_signals(), campaign_id="c1", adset_id="a1", ad_id="ad1")
    mart = DataMart(st)
    tot, crm, dia = mart.revenue_verified(), mart.crm_revenue(), mart.diamond_revenue()
    if tot == 300000.0 and crm <= tot and dia <= tot and crm == 100000.0 and dia == 100000.0:
        record("A11-crm-diamond-subset", "FAIL-001", "DEFENDED",
               f"Revenue Verified={tot}; CRM={crm} & Diamond={dia} are verified subsets, not summed into total")
    else:
        record("A11-crm-diamond-subset", "FAIL-001", "NOTE",
               f"total={tot}, crm={crm}, diamond={dia}")


def store_row(store, event_id):
    return store.get_by_event_id(event_id)


# ================================================================================================
# GROUP B - M6-FAIL-005 : Data Mart used as a trigger owner (RULE-012, support view only)
# ================================================================================================
def group_b():
    st = new_store()
    verified_row(st, "e_b", revenue=250000.0, order_code="ORDB",
                 signals=full_ad_signals(), campaign_id="c1", adset_id="a1", ad_id="ad1")
    mart = DataMart(st)

    # B1 DataMart public surface is read/aggregate only; NO trigger/write ATTRIBUTE exists.
    #    (Exact-name check mirroring the SMK-010 test -- `crm_revenue`/`diamond_revenue` are READ aggregates in
    #    the allow-list; a substring scan would false-match "crm" inside "crm_revenue".)
    public = {n for n in dir(mart) if not n.startswith("_") and callable(getattr(mart, n))}
    allow = {"verified_rows", "revenue_verified", "verified_order_count", "crm_revenue", "diamond_revenue",
             "verified_boxes", "event_count", "ads_spend", "cod_orders", "cod_fail",
             "sample_verified_correlation"}
    extra = public - allow
    forbidden_exact = ("write", "insert", "update", "delete", "trigger", "send", "dispatch", "scale",
                       "publish", "enqueue", "create_crm", "crm", "price", "budget", "commission",
                       "order_state", "sync")
    present = [f for f in forbidden_exact if hasattr(mart, f)]
    if not extra and not present:
        record("B1-mart-public-surface", "FAIL-005", "DEFENDED",
               f"DataMart public methods {sorted(public)} subset read-only allow-list; 0 trigger/write attribute "
               f"(exact-name check: none of {list(forbidden_exact)} present)")
    else:
        record("B1-mart-public-surface", "FAIL-005", "BREACH",
               f"unexpected mart surface: extra={extra}, trigger_attr={present}")

    # B2 DashboardDeps carry ONLY the read-only mart (no writer/transport/trigger/crm/scale)
    deps = DashboardDeps(mart=mart)
    fields = set(vars(deps).keys())
    bad_attr = [v for v in ("transport", "send", "dispatch", "scale", "store", "writer", "trigger", "crm")
                if hasattr(deps, v)]
    if fields == {"mart"} and not bad_attr:
        record("B2-deps-only-mart", "FAIL-005", "DEFENDED",
               "DashboardDeps fields == {mart}; no store-writer/transport/trigger/crm/scale handle")
    else:
        record("B2-deps-only-mart", "FAIL-005", "BREACH", f"deps fields={fields}, bad={bad_attr}")

    # B3 handle_dashboard_request has NO side effect (reading twice does not mutate the store)
    before = st.all()
    v1 = handle_dashboard_request({}, deps)
    v2 = handle_dashboard_request({}, deps)
    after = st.all()
    if (isinstance(v1, DashboardView) and isinstance(v2, DashboardView) and before == after
            and len(before) == len(after)):
        record("B3-endpoint-no-sideeffect", "FAIL-005", "DEFENDED",
               f"two dashboard reads mutated nothing (store rows stable={len(after)}); returns a view only")
    else:
        record("B3-endpoint-no-sideeffect", "FAIL-005", "BREACH", "dashboard read mutated the store")

    # B4 malicious untrusted `query` is DATA (discarded) -> no execution, output identical to empty query
    executed = {"hit": False}

    class _Evil:
        def __getitem__(self, k):
            executed["hit"] = True
            raise KeyError(k)

    evil = {"trigger": "scale_now", "scale": lambda: executed.__setitem__("hit", True),
            "__class__": "x", "crm_send": True, "sql": "DROP TABLE ads;"}
    v_evil = handle_dashboard_request(evil, deps)
    v_empty = handle_dashboard_request({}, deps)
    same = ([ (m.name, m.value) for m in v_evil.metrics ] == [ (m.name, m.value) for m in v_empty.metrics ]
            and v_evil.overall_data_quality == v_empty.overall_data_quality)
    _ = handle_dashboard_request(_Evil(), deps)   # non-Mapping -> coerced to {}; __getitem__ never called
    if same and not executed["hit"]:
        record("B4-query-is-data", "FAIL-005", "DEFENDED",
               "malicious query (trigger/scale/crm_send/sql/callable) ignored; no execution; output unchanged")
    else:
        record("B4-query-is-data", "FAIL-005", "BREACH",
               f"query influenced behaviour or executed: hit={executed['hit']}, same={same}")

    # B5 reach-around: mart._store is the measurement store. Even reaching it yields NO trigger-owner capability
    #    (no CRM/pricing/Diamond/budget/scale/publish/enqueue/send method exists on the store either).
    store_methods = {n for n in dir(mart._store) if not n.startswith("_") and callable(getattr(mart._store, n))}
    trigger_owner = {n for n in store_methods
                     if any(v in n.lower() for v in
                            ("crm", "price", "budget", "scale", "publish", "enqueue", "send", "dispatch",
                             "trigger", "commission", "order_state", "sync"))}
    if not trigger_owner:
        record("B5-store-no-trigger-owner", "FAIL-005", "DEFENDED",
               f"mart._store methods {sorted(store_methods)} contain NO CRM/pricing/Diamond/budget/scale/"
               f"publish/send trigger-owner capability; update/delete raise; set-once revenue only")
    else:
        record("B5-store-no-trigger-owner", "FAIL-005", "BREACH",
               f"store exposes trigger-owner method(s): {trigger_owner}")

    # B6 DQ check_and_record writes ONLY Zone-C data_quality_status (audited); no CRM/scale emission; revenue/
    #    attribution untouched; DQ PASS is not scale evidence by itself.
    st2 = new_store()
    verified_row(st2, "e_dq", revenue=250000.0, order_code="ORDDQ",
                 signals=full_ad_signals(), campaign_id="c1", adset_id="a1", ad_id="ad1")
    row_before = store_row(st2, "e_dq")
    checker = DataQualityChecker(st2, AuditLog())
    ctx = DQContext(event_registered=True, event_owner_known=True, consent_valid=True, no_duplicate=True,
                    identity_mapped=True, suppression_active=False, dashboard_has_trace=True)
    res = checker.check_and_record(row_before, ctx)
    row_after = store_row(st2, "e_dq")
    ok = (row_after.revenue_value == row_before.revenue_value
          and dict(row_after.attribution_context) == dict(row_before.attribution_context)
          and len(st2.dq_transitions) == 1
          and st2.dq_transitions[0].actor == "data_quality_checker")
    record("B6-dq-record-no-trigger", "FAIL-005",
           "DEFENDED" if ok else "BREACH",
           f"check_and_record: overall={res.overall.value}; revenue/attribution unchanged; only Zone-C status + 1 "
           f"audited transition (actor={st2.dq_transitions[0].actor}); no CRM/scale/publish emitted")


# ================================================================================================
# GROUP C - RULE-017 : suppression / risk locks reflected in the DQ gate (never PASS while active+unreflected)
# ================================================================================================
def _neutral_all_pass_ctx(**over):
    base = dict(event_registered=True, event_owner_known=True, consent_valid=True, no_duplicate=True,
                identity_mapped=True, suppression_active=False, suppression_reflected=None,
                dashboard_has_trace=True)
    base.update(over)
    return DQContext(**base)


def group_c():
    checker = DataQualityChecker()
    # a verified, fully-attributed row so ATTRIBUTION + VERIFIED_REVENUE items are PASS on their own
    st = new_store()
    verified_row(st, "e_sup", revenue=250000.0, order_code="ORDS",
                 signals=full_ad_signals(), campaign_id="c1", adset_id="a1", ad_id="ad1")
    row = store_row(st, "e_sup")

    combos = [
        (None, None), (None, False), (None, True),
        (False, None), (False, False), (False, True),
        (True, None), (True, False), (True, True),
    ]
    sup_map = {}
    bad = []
    for active, reflected in combos:
        ctx = _neutral_all_pass_ctx(suppression_active=active, suppression_reflected=reflected)
        dq = checker.check(row, ctx)
        item = dq.item(GateItem.SUPPRESSION).status
        sup_map[(active, reflected)] = (item, dq.overall)
        # the forbidden outcome: suppression ACTIVE and NOT reflected, yet the item/overall reads PASS
        if active is True and reflected is not True and (item is GateStatus.PASS or dq.overall is GateStatus.PASS):
            bad.append((active, reflected, item.value, dq.overall.value))

    # expected: active True+reflected False -> FAIL; True+None -> HOLD; True+True -> PASS; None-> HOLD; False-> PASS
    exp_ok = (
        sup_map[(True, False)][0] is GateStatus.FAIL
        and sup_map[(True, None)][0] is GateStatus.HOLD
        and sup_map[(True, True)][0] is GateStatus.PASS
        and sup_map[(None, None)][0] is GateStatus.HOLD
        and sup_map[(False, None)][0] is GateStatus.PASS
    )
    if not bad and exp_ok:
        record("C1-suppression-matrix", "RULE-017", "DEFENDED",
               "all 9 active x reflected combos: active+unreflected never PASS "
               "(True/False->FAIL, True/None->HOLD, True/True->PASS, None->HOLD, False->PASS)")
    else:
        record("C1-suppression-matrix", "RULE-017", "BREACH",
               f"suppression bypass combos={bad}; matrix={ {k: (a.value,b.value) for k,(a,b) in sup_map.items()} }")

    # C2 active-unreflected suppression dominates the overall roll-up to FAIL even with all else PASS
    ctx = _neutral_all_pass_ctx(suppression_active=True, suppression_reflected=False)
    dq = checker.check(row, ctx)
    record("C2-active-suppression-overall", "RULE-017",
           "DEFENDED" if dq.overall is GateStatus.FAIL else "BREACH",
           f"active+unreflected suppression -> overall={dq.overall.value} (worst dominates; not scale evidence)")


# ================================================================================================
# GROUP D - RULE-015 : nothing PASS without full evidence/trace (fail-closed roll-up)
# ================================================================================================
def group_d():
    # D1 empty gate item set -> HOLD, never PASS
    ws = worst_status([])
    empty = AdsDataQualityCheck.from_items([])
    record("D1-empty-gate-hold", "RULE-015",
           "DEFENDED" if ws is GateStatus.HOLD and empty.overall is GateStatus.HOLD else "BREACH",
           f"worst_status([])={ws.value}; from_items([]).overall={empty.overall.value} (fail-closed, not PASS)")

    # D2 a displayed metric value with NO trace / NO evidence -> dashboard overall FAIL
    no_trace = MetricResult(name="X", formula="f", value=123.0, unit="VND", source_trace="",
                            sample_evidence_ref="ev")
    no_ev = MetricResult(name="Y", formula="f", value=123.0, unit="VND", source_trace="t",
                         sample_evidence_ref=None)
    good = MetricResult(name="Z", formula="f", value=1.0, unit="ratio", source_trace="t",
                        sample_evidence_ref="ev")
    from app.api.dashboard import _dashboard_data_quality
    dq_no_trace = _dashboard_data_quality([good, no_trace])
    dq_no_ev = _dashboard_data_quality([good, no_ev])
    dq_good = _dashboard_data_quality([good])
    if dq_no_trace == "FAIL" and dq_no_ev == "FAIL" and dq_good == "PASS":
        record("D2-visual-only-fail", "RULE-015", "DEFENDED",
               "metric value w/o trace->FAIL; value w/o evidence->FAIL; fully-traced->PASS (has_trace_and_evidence)")
    else:
        record("D2-visual-only-fail", "RULE-015", "BREACH",
               f"visual-only slipped: no_trace={dq_no_trace}, no_ev={dq_no_ev}, good={dq_good}")

    # D3 DQ overall PASS requires ALL 8 items PASS; a single HOLD/FAIL dominates
    checker = DataQualityChecker()
    st = new_store()
    verified_row(st, "e_d3", revenue=250000.0, order_code="ORDD3",
                 signals=full_ad_signals(), campaign_id="c1", adset_id="a1", ad_id="ad1")
    row = store_row(st, "e_d3")
    all_pass = _neutral_all_pass_ctx(suppression_active=False)
    ov_pass = checker.check(row, all_pass).overall
    ov_hold = checker.check(row, _neutral_all_pass_ctx(suppression_active=False, identity_mapped=None)).overall
    ov_fail = checker.check(row, _neutral_all_pass_ctx(suppression_active=False, consent_valid=False)).overall
    if ov_pass is GateStatus.PASS and ov_hold is GateStatus.HOLD and ov_fail is GateStatus.FAIL:
        record("D3-overall-requires-all", "RULE-015", "DEFENDED",
               "all-8-PASS->PASS (non-vacuous); one missing signal->HOLD; one violation->FAIL")
    else:
        record("D3-overall-requires-all", "RULE-015", "NOTE",
               f"pass={ov_pass.value}, hold={ov_hold.value}, fail={ov_fail.value}")

    # D4 check_and_record leaves an append-only audited transition (RULE-015 audit)
    st = new_store()
    verified_row(st, "e_d4", revenue=250000.0, order_code="ORDD4",
                 signals=full_ad_signals(), campaign_id="c1", adset_id="a1", ad_id="ad1")
    ch = DataQualityChecker(st, AuditLog())
    ch.check_and_record(store_row(st, "e_d4"), _neutral_all_pass_ctx(suppression_active=False))
    tr = st.dq_transitions
    record("D4-audited-transition", "RULE-015",
           "DEFENDED" if len(tr) == 1 and tr[0].actor == "data_quality_checker" and tr[0].reason else "BREACH",
           f"Zone-C transition appended (n={len(tr)}, actor={tr[0].actor}, reason={tr[0].reason!r})")

    # D5 empty store dashboard is fail-closed (an evidence-less 0 revenue is NOT silently PASS)
    mart = DataMart(new_store())
    view = handle_dashboard_request({}, DashboardDeps(mart=mart))
    rev = view.metric("Revenue Verified")
    record("D5-empty-dashboard-failclosed", "RULE-015", "NOTE",
           f"empty store -> Revenue Verified value={rev.value}, evidence={rev.sample_evidence_ref!r}, "
           f"overall={view.overall_data_quality} (fail-closed: no evidence -> not PASS)")


# ================================================================================================
# GROUP E - belt sweeps: core-boundary (RULE-012/013/019) + PII masking (RULE-014; M6-P1506 owns gate)
# ================================================================================================
def group_e():
    # E1 token sweep: no override/commission/order-state/CRM/pricing/scale ACTION identifier in the M6.2F surface
    action_verbs = ("commission", "order_state", "write_order", "quote_snapshot_write", "crm_send",
                    "set_price", "raise_budget", "enable_campaign", "publish_optim", "scale_now",
                    "golden_hour_override")
    targets = [
        IMPL / "app" / "measurement" / "dashboard" / "data_mart.py",
        IMPL / "app" / "measurement" / "dashboard" / "kpi_metrics.py",
        IMPL / "app" / "measurement" / "dashboard" / "models.py",
        IMPL / "app" / "api" / "dashboard.py",
        IMPL / "app" / "measurement" / "quality" / "data_quality_check.py",
        IMPL / "app" / "measurement" / "quality" / "data_quality_checker.py",
    ]
    hits = []
    for p in targets:
        with tokenize.open(str(p)) as fh:   # NAME tokens only -> excludes docstrings/comments
            for tok in tokenize.generate_tokens(fh.readline):
                if tok.type == tokenize.NAME and tok.string.lower() in action_verbs:
                    hits.append(f"{p.name}:{tok.start[0]}:{tok.string}")
    record("E1-no-action-identifiers", "RULE-012/019",
           "DEFENDED" if not hits else "NOTE",
           f"token sweep of 6 M6.2F modules: override/commission/order-state/CRM/pricing/scale action defs = "
           f"{hits or 'NONE'}")

    # E2 masking: a distinctive correlation id reaches a metric's sample_evidence_ref MASKED, never raw
    st = new_store()
    probe = "corr" + "ZZZ" + "abcdefgh"
    verified_row(st, "e_mask", revenue=250000.0, order_code="ORDM", correlation_id=probe,
                 signals=full_ad_signals(), campaign_id="c1", adset_id="a1", ad_id="ad1")
    view = handle_dashboard_request({}, DashboardDeps(mart=DataMart(st)))
    exported = repr(view.to_public())
    masked = mask(probe)
    if probe not in exported and masked in exported:
        record("E2-dashboard-masking", "RULE-014", "DEFENDED",
               f"raw correlation_id absent from dashboard export; masked form present ({masked})")
    else:
        record("E2-dashboard-masking", "RULE-014", "NOTE",
               f"raw-in-export={probe in exported}; masked-present={masked in exported} (route M6-P1506)")


# ================================================================================================
# GROUP W - workflow-harvested vectors (6-agent adversarial ideation + completeness critic).
#           Every claimed breach EXECUTED here before recording; reachability checked against the
#           real wiring (store.materialize's ONLY caller is AttributionMaterializer.materialize, which
#           is constructed ONLY in tests -- no app endpoint wires it).
# ================================================================================================
def group_w():
    # W1 (sharpest FAIL-001 candidate) materializer books revenue onto event.event_id while deriving
    #    `verified` from conversion.event_code -- it never asserts the measurement EVENT's own event_code is
    #    ORDER_VERIFIED. A mispaired (ORDER_VERIFIED conversion, ORDER_CREATED/PAYMENT_WAITING/COD_WAITING event)
    #    call books revenue onto the pre-verified row. Uses the DEFAULT materializer + DEFAULT config.
    booked_states = {}
    for code in ("ORDER_CREATED", "PAYMENT_WAITING", "COD_WAITING"):
        st = new_store()
        eid = f"w_{code.lower()}"
        insert_event(st, eid, event_code=code, correlation_id="corr_w")
        conv = make_conversion("ORDER_VERIFIED", source_event_id=eid,
                               revenue_value=500000.0, currency="VND", order_code=f"ORD_{eid}")
        AttributionMaterializer(st, AttributionResolver(), AuditLog()).materialize(store_row(st, eid), conv)
        mart = DataMart(st)
        view = handle_dashboard_request({}, DashboardDeps(mart=mart))
        dq = DataQualityChecker().check(store_row(st, eid))
        booked_states[code] = (mart.revenue_verified(), view.metric("Revenue Verified").value,
                               view.overall_data_quality, dq.item(GateItem.VERIFIED_REVENUE).status.value,
                               dq.overall.value)
    all_booked = all(v[0] == 500000.0 for v in booked_states.values())
    all_dq_fail = all(v[3] == "FAIL" and v[4] == "FAIL" for v in booked_states.values())
    dash_pass = all(v[2] == "PASS" for v in booked_states.values())
    if all_booked and all_dq_fail:
        record("W1-materializer-eventcode-gap", "FAIL-001", "OPEN_NONGATE",
               f"DEFAULT materializer books 500000 onto ORDER_CREATED/PAYMENT_WAITING/COD_WAITING rows (event.event_code "
               f"never asserted ==ORDER_VERIFIED); NOT channel-reachable (materializer constructed only in tests, sole "
               f"store.materialize caller); per-row DQ Verified-Revenue=FAIL/overall=FAIL on each; BUT dashboard "
               f"overall={ 'PASS' if dash_pass else 'mixed' } (endpoint runs no per-row DQ) -> primary residual, route "
               f"CODER (assert event.event_code==ORDER_VERIFIED) + M6-P1506/M6.2G")
    else:
        record("W1-materializer-eventcode-gap", "FAIL-001", "NOTE",
               f"unexpected: booked={all_booked}, dq_fail={all_dq_fail}, states={booked_states}")

    # W2 attribution_context is stored as a PLAIN MUTABLE dict; frozen=True freezes the binding, not the dict.
    #    In-place mutation (no object.__setattr__ needed) upgrades an ambiguous row's DQ Attribution HOLD->PASS
    #    and re-routes revenue between the CRM / Diamond breakdowns. Evidence-integrity gap (RULE-008/009).
    st = new_store()
    insert_event(st, "w_amb", event_code="ORDER_VERIFIED")
    st.materialize("w_amb", attribution_context={"conflict_status": "MULTI_TOUCH", "source_confidence": "LOW"},
                   revenue_value=1000000.0, order_code="ORDAMB", verified=True)
    row = store_row(st, "w_amb")
    before = DataQualityChecker().check(row).item(GateItem.ATTRIBUTION).status.value
    crm_before = DataMart(st).crm_revenue()
    row.attribution_context["conflict_status"] = "NONE"        # frozen row, but the dict is mutable
    row.attribution_context["source_confidence"] = "HIGH"
    row.attribution_context["entry_channel"] = "CRM"
    after = DataQualityChecker().check(row).item(GateItem.ATTRIBUTION).status.value
    crm_after = DataMart(st).crm_revenue()
    if before == "HOLD" and after == "PASS" and crm_before == 0.0 and crm_after == 1000000.0:
        record("W2-mutable-attrctx-dict", "FAIL-005", "OPEN_NONGATE",
               f"attribution_context is a mutable dict inside a frozen row: in-place edit upgrades DQ Attribution "
               f"{before}->{after} and re-routes CRM breakdown {crm_before}->{crm_after}; total revenue_verified "
               f"unchanged (not FAIL-001); set-once/immutability not enforced on the contained dict -> route CODER "
               f"(store MappingProxyType/copy-on-read) + M6-P1506")
    else:
        record("W2-mutable-attrctx-dict", "FAIL-005", "NOTE",
               f"attr={before}->{after}, crm={crm_before}->{crm_after}")

    # W3 frozen=True is not a hard barrier: object.__setattr__ forges revenue on a quote row and inflates a
    #    verified row past the store's set-once guard. Requires ARBITRARY in-process code execution (at which point
    #    every in-memory invariant is moot) -> defense-in-depth limit, not a channel-reachable gate.
    st = new_store()
    insert_event(st, "w_q", event_code="QUOTE_SENT")
    qrow = store_row(st, "w_q")
    object.__setattr__(qrow, "revenue_value", 9_000_000.0)
    forged = DataMart(st).revenue_verified()
    record("W3-frozen-setattr-bypass", "FAIL-001", "NOTE",
           f"object.__setattr__ forges revenue on a QUOTE_SENT row -> mart={forged} (frozen guard bypassed); requires "
           f"arbitrary in-process code exec (all in-memory invariants moot) -> defense-in-depth limit, not "
           f"channel-reachable; hardening: defensive copy on read / re-check event_code in verified_rows")

    # W4 same order_code across two DISTINCT verified measurement rows: revenue_verified() sums per-ROW while
    #    verified_order_count() dedups by order_code -> Revenue Verified + AOV double-count one order.
    st = new_store()
    for eid, key in (("w_o1", "k1"), ("w_o2", "k2")):
        insert_event(st, eid, event_code="ORDER_VERIFIED", idempotency_key=key)
        st.materialize(eid, attribution_context={"source_confidence": "HIGH", "conflict_status": "NONE"},
                       revenue_value=1000000.0, order_code="ORD-SAME", verified=True)
    mart = DataMart(st)
    rv, voc = mart.revenue_verified(), mart.verified_order_count()
    metrics = {m.name: m for m in compute_metrics(mart)}
    aov = metrics["AOV"].value
    record("W4-same-order-doublecount", "FAIL-001", "OPEN_NONGATE",
           f"two distinct ORDER_VERIFIED rows sharing order_code ORD-SAME -> Revenue Verified={rv} but "
           f"verified_order_count={voc} -> AOV={aov} double-counts one order; both rows genuinely verified (not the "
           f"quote-as-revenue class); revenue_verified sums per-row, no dedup-by-order (DQ Dedup item is the intended "
           f"per-row backstop) -> route CODER/DQ dedup (M6-P1506/M6.2G)")

    # W5 is_scale_evidence_eligible checks ONLY attribution (HIGH+NONE); it never consults the 8-item DQ overall,
    #    so a row that DQ-FAILs (active suppression unreflected, RULE-017 / missing consent) is still 'scale
    #    eligible'. Armed-not-fired: nothing in-slice consumes scale_evidence, and it is AND-gated by
    #    SCALE_MODEL_RATIFIED=False. (The flag is a bare module attr -> in-process mutable, W3-class caveat.)
    st = new_store()
    insert_event(st, "w_se", event_code="ORDER_VERIFIED", campaign_id="c1", adset_id="a1", ad_id="ad1")
    conv = make_conversion("ORDER_VERIFIED", source_event_id="w_se", revenue_value=500000.0,
                           currency="VND", order_code="ORDSE")
    out = AttributionMaterializer(st, AttributionResolver(), AuditLog()).materialize(
        store_row(st, "w_se"), conv, signals=full_ad_signals())
    dq_fail = DataQualityChecker().check(
        store_row(st, "w_se"),
        DQContext(event_registered=True, event_owner_known=True, consent_valid=False, no_duplicate=True,
                  identity_mapped=True, suppression_active=True, suppression_reflected=False,
                  dashboard_has_trace=True)).overall.value
    record("W5-scale-eligible-ignores-dq", "FAIL-005", "OPEN_NONGATE",
           f"scale_evidence_eligible={out.scale_evidence_eligible} (attribution HIGH+NONE) while the SAME row's DQ "
           f"overall={dq_fail} (consent-missing + suppression-unreflected); eligibility never consults the DQ gate; "
           f"scale_evidence={out.scale_evidence} (AND-gated by SCALE_MODEL_RATIFIED=False); armed-not-fired (no "
           f"in-slice scale consumer) -> route M6.2G scale-gate (M6-P1600) + CODER")

    # W6 mask() reveals first3+last2; for a 6-char id that is 5/6 chars (sanctioned M6-OD-012 default but a near-
    #    full reveal for short order/guest codes). PII belt -> M6-P1506 owns the gate.
    sample6 = "OD" + "1234"
    m6 = mask(sample6)
    record("W6-mask-short-reveal", "RULE-014", "NOTE",
           f"mask({sample6!r})={m6!r} reveals 5/6 chars (sanctioned abc***xy default; near-full reveal for 6-char "
           f"order/guest codes routed to a dashboard sample_evidence_ref) -> PII hardening, M6-P1506")


def main():
    print("=" * 100)
    print("M6-P1505 BOUNDARY_ADVERSARY - executed attacks vs FROZEN staged M6.2F (dashboard + data quality)")
    print(f"impl root: {IMPL}")
    print(f"posture: gateway={config.GLOBAL_GATEWAY_STATE} prod={config.PRODUCTION_FLAG} "
          f"external_send={config.EXTERNAL_SEND} SCALE_MODEL_RATIFIED={config.SCALE_MODEL_RATIFIED} "
          f"HASH_POLICY_RATIFIED={config.HASH_POLICY_RATIFIED}")
    print("=" * 100)
    for grp in (group_a, group_b, group_c, group_d, group_e, group_w):
        print(f"\n----- {grp.__name__} -----")
        grp()

    from collections import Counter
    tally = Counter(k for _, _, k, _ in RESULTS)
    print("\n" + "=" * 100)
    print(f"SUMMARY: {dict(tally)}")
    print(f"TOTAL RECORDED OUTCOMES: {len(RESULTS)}")
    print(f"IN-SCOPE FAIL-GATE BREACHES (FAIL-001 / FAIL-005): {len(BREACHES)}")
    for b in BREACHES:
        print(f"   !!! BREACH {b}")
    print("=" * 100)
    # posture must be unchanged by anything we did
    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
    assert config.EXTERNAL_SEND == "OFF" and config.SCALE_MODEL_RATIFIED is False


if __name__ == "__main__":
    main()
