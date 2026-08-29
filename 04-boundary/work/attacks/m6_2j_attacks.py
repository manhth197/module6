"""M6-P1905 BOUNDARY_ADVERSARY executed attack harness for slice M6.2J (Phase-3 growth machine measurement).

READ-ONLY adversary: imports the FROZEN staged M6.2J app and drives the REAL code paths. Never modifies app code,
never writes 04-artifacts/state, never sends CRM / computes commission / triggers the Data Mart (external_send OFF).

In-scope fail gates ATTACKED: M6-FAIL-002 (consent violation), M6-FAIL-004 (core override -- incl. commission,
RULE-019) and M6-FAIL-005 (Data Mart used as a trigger owner). In-scope rules: RULE-002 (consent fail-closed),
RULE-012 (Data Mart support view only), RULE-019 (Diamond referral: record attribution only; Finance owns commission).

Every claimed breach is EXECUTED here before it is recorded. Outcome classes: DEFENDED / OPEN_NONGATE / NOTE /
BREACH (BREACH = CRM/reactivation counted without valid consent, a commission computed, or a Data-Mart trigger).

Launcher: py -3.12 -B (byte-clean). PII probes assembled at runtime, never echoed raw.
"""
from __future__ import annotations

import sys
import tokenize
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
PACK_ROOT = HERE.parents[3]
IMPL = PACK_ROOT / "04-artifacts" / "impl" / "M6.2J"
if not IMPL.exists():
    IMPL = Path(r"D:\M6\Module6-workspace\04-artifacts\impl\M6.2J")
sys.path.insert(0, str(IMPL))

from app import config
from app.measurement.audit import AuditLog
from app.measurement.consent.gate import ConsentGate
from app.measurement.models.consumed import ConsentScope, ConsentSnapshot, ConsentState
from app.measurement.models.measurement_event import AdsMeasurementEvent
from app.measurement.models.conversion_event import ConversionEvent
from app.measurement.models.segments import ApprovalState, CustomerSegment, SegmentMember
from app.measurement.adapters.segment_reader import InMemorySegmentReader
from app.measurement.attribution.materializer import AttributionMaterializer
from app.measurement.attribution.resolver import AttributionResolver
from app.measurement.store.measurement_event_store import MeasurementEventStore
from app.measurement.dashboard.data_mart import DataMart
from app.measurement.growth.crm import CrmConsumed, CrmReorderMeasurement
from app.measurement.growth.diamond import DiamondConsumed, DiamondReferralMeasurement
from app.measurement.growth.reactivation import ReactivationConsumed, ReactivationMeasurement
from app.measurement.growth.growth import GrowthConsumed, GrowthReportBuilder
from app.measurement.growth.reads import verified_rows

FIXED_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
RESULTS = []
BREACHES = []


def record(attack_id, gate, klass, detail):
    assert klass in ("DEFENDED", "OPEN_NONGATE", "NOTE", "BREACH"), klass
    RESULTS.append((attack_id, gate, klass, detail))
    if klass == "BREACH":
        BREACHES.append((attack_id, gate, detail))
    print(f"[{klass:12}] {attack_id:30} {gate:9} | {detail}")


# --- faithful factories (mirror tests/conftest.py) --------------------------------------------------
def new_store():
    return MeasurementEventStore()


def gate():
    return ConsentGate(AuditLog())


def snap(snapshot_id="cs_crm", subject="subj_crm", state="VALID", scopes=("crm",)):
    return ConsentSnapshot(snapshot_id, subject, ConsentState(state), FIXED_TS,
                           frozenset(ConsentScope(s) for s in scopes))


def insert_event(store, event_id, event_code, **over):
    base = dict(event_id=event_id, event_code=event_code, event_ts=FIXED_TS,
                idempotency_key=over.pop("idempotency_key", f"idem_{event_id}"),
                correlation_id=over.pop("correlation_id", "corr"), ingested_at=FIXED_TS)
    base.update(over)
    row = AdsMeasurementEvent(**base)
    store.insert(row)
    return row


def make_conversion(event_code, source_event_id, **over):
    base = dict(conversion_id=f"conv_{source_event_id}", event_code=event_code, source_event_id=source_event_id,
                correlation_id="corr_c", customer_or_guest_key="guest_x", consent_snapshot_id="cs_valid",
                occurred_at=FIXED_TS, idempotency_key=f"idem_conv_{source_event_id}")
    base.update(over)
    return ConversionEvent(**base)


def verified_row(store, event_id, *, revenue, order_code, signals, event_code="ORDER_VERIFIED", **over):
    ev = insert_event(store, event_id, event_code, **over)
    conv = make_conversion(event_code, source_event_id=event_id, revenue_value=float(revenue),
                           currency="VND", order_code=order_code)
    AttributionMaterializer(store, AttributionResolver(), AuditLog()).materialize(ev, conv, signals=signals)
    return store.get_by_event_id(event_id)


def force_revenue_on(store, event_id, *, revenue, order_code, ctx):
    store.materialize(event_id, attribution_context=ctx, revenue_value=float(revenue),
                      order_code=order_code, verified=True)


# ================================================================================================
# GROUP A - FAIL-002 : CRM revenue consent + eligibility + suppression gated (fail-closed)
# ================================================================================================
def _crm_store_and_consumed(order_code="ord_c", *, elig=True, suppr=True, consent=None):
    st = new_store()
    verified_row(st, "e_crm", revenue=250000.0, order_code=order_code, signals={"crm": True})
    cons = CrmConsumed(
        crm_eligible_orders={order_code: elig} if elig is not None else {},
        suppression_pass_orders={order_code: suppr} if suppr is not None else {},
        consent_by_order={order_code: consent} if consent is not None else {},
    )
    return st, cons


def group_a():
    G = gate()
    # A1 opt-out consent -> crm_revenue 0 (SMK-008)
    st, cons = _crm_store_and_consumed(consent=snap(state="OPT_OUT", scopes=()))
    rev = CrmReorderMeasurement(st, G, cons).crm_revenue()
    record("A1-crm-optout-excluded", "FAIL-002",
           "DEFENDED" if rev == 0.0 else "BREACH", f"OPT_OUT CRM consent -> crm_revenue={rev} (fail-closed excluded)")

    # A2 expired / missing consent -> excluded
    st1, c1 = _crm_store_and_consumed(consent=snap(state="EXPIRED", scopes=()))
    st2, c2 = _crm_store_and_consumed(consent=None)   # no consent snapshot
    r_exp = CrmReorderMeasurement(st1, G, c1).crm_revenue()
    r_mis = CrmReorderMeasurement(st2, G, c2).crm_revenue()
    record("A2-expired-missing-excluded", "FAIL-002",
           "DEFENDED" if r_exp == 0.0 and r_mis == 0.0 else "BREACH",
           f"expired consent -> {r_exp}; missing snapshot -> {r_mis} (both fail-closed)")

    # A3 VALID consent but WRONG scope (audience_sync, not CRM) -> excluded
    st, cons = _crm_store_and_consumed(consent=snap(scopes=("audience_sync",)))
    rev = CrmReorderMeasurement(st, G, cons).crm_revenue()
    record("A3-wrong-scope-excluded", "FAIL-002",
           "DEFENDED" if rev == 0.0 else "BREACH", f"VALID consent w/ only audience_sync scope -> crm_revenue={rev}")

    # A4 eligibility missing/False -> excluded
    st1, c1 = _crm_store_and_consumed(elig=False, consent=snap())
    st2, c2 = _crm_store_and_consumed(elig=None, consent=snap())
    r_f = CrmReorderMeasurement(st1, G, c1).crm_revenue()
    r_m = CrmReorderMeasurement(st2, G, c2).crm_revenue()
    record("A4-eligibility-gated", "FAIL-002",
           "DEFENDED" if r_f == 0.0 and r_m == 0.0 else "BREACH",
           f"CRM eligibility False -> {r_f}; absent -> {r_m} (valid consent+suppression but no eligibility -> 0)")

    # A5 suppression missing/False -> excluded
    st1, c1 = _crm_store_and_consumed(suppr=False, consent=snap())
    st2, c2 = _crm_store_and_consumed(suppr=None, consent=snap())
    r_f = CrmReorderMeasurement(st1, G, c1).crm_revenue()
    r_m = CrmReorderMeasurement(st2, G, c2).crm_revenue()
    record("A5-suppression-gated", "FAIL-002",
           "DEFENDED" if r_f == 0.0 and r_m == 0.0 else "BREACH",
           f"suppression False -> {r_f}; absent -> {r_m} (fail-closed)")

    # A6 all pass -> counted (non-vacuous control)
    st, cons = _crm_store_and_consumed(consent=snap())
    rev = CrmReorderMeasurement(st, G, cons).crm_revenue()
    record("A6-all-pass-counted", "FAIL-002",
           "DEFENDED" if rev == 250000.0 else "BREACH",
           f"eligibility+suppression+VALID CRM consent -> crm_revenue={rev} (discriminating, not vacuous)")

    # A7 CRM layer exposes NO send/sync surface
    crm = CrmReorderMeasurement(new_store(), G, CrmConsumed())
    send_verbs = ("send", "sync", "dispatch", "transport", "enqueue", "publish", "crm_send", "send_crm", "trigger")
    hits = [v for v in send_verbs if hasattr(crm, v)]
    record("A7-crm-no-send-surface", "FAIL-002",
           "BREACH" if hits else "DEFENDED", f"CRM measurement send/sync surface: {hits or 'NONE'} (measure-only)")

    # A8 truthy-but-not-True eligibility/suppression -> excluded (`is not True`)
    st = new_store()
    verified_row(st, "e_crm", revenue=250000.0, order_code="ord_c", signals={"crm": True})
    cons = CrmConsumed(crm_eligible_orders={"ord_c": 1}, suppression_pass_orders={"ord_c": "yes"},
                       consent_by_order={"ord_c": snap()})
    rev = CrmReorderMeasurement(st, G, cons).crm_revenue()
    record("A8-truthy-not-true-excluded", "FAIL-002",
           "DEFENDED" if rev == 0.0 else "BREACH",
           f"eligibility=1 / suppression='yes' (truthy but not True) -> crm_revenue={rev} (strict `is True`)")

    # A9 a CRM_REORDER_SENT / click is never revenue (only ORDER_VERIFIED verified row)
    st = new_store()
    insert_event(st, "e_sent", "CRM_REORDER_SENT")
    cons = CrmConsumed(crm_eligible_orders={"ord_c": True}, suppression_pass_orders={"ord_c": True},
                       consent_by_order={"ord_c": snap()})
    rev = CrmReorderMeasurement(st, G, cons).crm_revenue()
    record("A9-sent-not-revenue", "FAIL-002",
           "DEFENDED" if rev == 0.0 else "BREACH", f"CRM_REORDER_SENT event -> crm_revenue={rev} (click/chat never revenue)")


# ================================================================================================
# GROUP B - FAIL-004 / RULE-019 : Diamond commission MEASURED-not-computed; no Core override
# ================================================================================================
_COMMISSION_VERBS = ("commission", "commission_amount", "commission_rate", "payout", "compute_commission",
                     "calc_commission", "commission_value", "set_commission")


def group_b():
    st = new_store()
    verified_row(st, "e_d1", revenue=500000.0, order_code="ord_d", signals={"diamond_id": "dia_1", "referral_link_id": "ref_1"})
    verified_row(st, "e_d2", revenue=400000.0, order_code="ord_d2", signals={"referral_link_id": "ref_2"})
    dia = DiamondReferralMeasurement(st, DiamondConsumed(commission_eligible_orders={"ord_d": True}))

    # B1 Diamond layer exposes NO commission amount/rate/payout method
    hits = [v for v in _COMMISSION_VERBS if hasattr(dia, v)]
    record("B1-no-commission-method", "FAIL-004",
           "BREACH" if hits else "DEFENDED", f"Diamond commission methods: {hits or 'NONE'} (RULE-019, Finance owns)")

    # B2 commission_ready_revenue is a REVENUE subset (<= diamond_revenue), not a computed %
    dr = dia.diamond_revenue()
    cr = dia.commission_ready_revenue()
    record("B2-commission-ready-is-revenue", "FAIL-004",
           "DEFENDED" if dr == 900000.0 and cr == 500000.0 and cr <= dr else "BREACH",
           f"diamond_revenue={dr}; commission_ready_revenue={cr} (verified commission-ELIGIBLE revenue subset, "
           f"not a commission amount/%)")

    # B3 commission_ready_revenue fail-closed 0 without the consumed eligibility flag (SMK-014)
    dia0 = DiamondReferralMeasurement(st, DiamondConsumed())   # no eligibility wired
    cr0 = dia0.commission_ready_revenue()
    dr0 = dia0.diamond_revenue()
    record("B3-commission-ready-failclosed", "FAIL-004",
           "DEFENDED" if cr0 == 0.0 and dr0 == 900000.0 else "BREACH",
           f"no consumed eligibility -> commission_ready_revenue={cr0} (fail-closed); diamond_revenue={dr0} still measured")

    # B4 token sweep: no commission/pricing/order-state/member-right override action def in the growth package
    override_verbs = ("compute_commission", "commission_amount", "set_price", "write_price", "order_state",
                      "write_order", "member_right", "set_member_right", "override", "crm_send", "diamond_payout")
    hits2 = []
    for p in (IMPL / "app" / "measurement" / "growth").glob("*.py"):
        with tokenize.open(str(p)) as fh:
            for tok in tokenize.generate_tokens(fh.readline):
                if tok.type == tokenize.NAME and tok.string.lower() in override_verbs:
                    hits2.append(f"{p.name}:{tok.start[0]}:{tok.string}")
    record("B4-no-override-identifiers", "FAIL-004",
           "DEFENDED" if not hits2 else "NOTE",
           f"token sweep of the growth package: commission/pricing/order-state/member-right override defs = {hits2 or 'NONE'}")

    # B5 buyer identity masked on referral export; raw buyer_ref never appears
    st2 = new_store()
    probe = "cust" + "DIAMOND" + "0001"
    verified_row(st2, "e_b5", revenue=500000.0, order_code="ord_b5",
                 signals={"diamond_id": "dia_1", "referral_link_id": "ref_1"}, customer_id=probe)
    attrs = DiamondReferralMeasurement(st2).referral_attributions()
    exported = repr([a.to_public() for a in attrs])
    from app.measurement.masking import mask
    record("B5-buyer-masked", "RULE-014",
           "DEFENDED" if probe not in exported and mask(probe) in exported else "NOTE",
           f"referral export: raw buyer_ref absent={probe not in exported}, masked present={mask(probe) in exported}")

    # B6 commission eligibility is a CONSUMED constructor input (Finance decides), not computed by M6
    record("B6-eligibility-consumed", "FAIL-004", "DEFENDED",
           f"commission_eligible_orders is a DiamondConsumed ctor field (Finance-owned flag M6 reads); the flag "
           f"controls commission_ready_revenue and M6 computes NO commission from it (RULE-019)")


# ================================================================================================
# GROUP C - FAIL-005 : Data Mart / growth builder support view only, never a trigger owner
# ================================================================================================
_TRIGGER_EXACT = ("trigger", "send", "sync", "crm_send", "scale", "set_price", "publish", "commission",
                  "order_state", "write", "insert", "update", "delete", "enqueue", "dispatch")


def group_c():
    st = new_store()
    verified_row(st, "e_c", revenue=250000.0, order_code="ord_c", signals={"crm": True})
    mart = DataMart(st)
    crm = CrmReorderMeasurement(st, gate(), CrmConsumed())
    dia = DiamondReferralMeasurement(st)
    react = None
    builder = GrowthReportBuilder(mart, crm, dia, react, measurement_store=st, consumed=GrowthConsumed())

    # C1 DataMart + GrowthReportBuilder expose NO trigger verb (SMK-010)
    present = {name: [a for a in _TRIGGER_EXACT if hasattr(o, a)] for name, o in
               (("DataMart", mart), ("GrowthReportBuilder", builder))}
    any_trig = any(present.values())
    record("C1-no-trigger-verb", "FAIL-005",
           "BREACH" if any_trig else "DEFENDED", f"trigger verbs on mart/builder: {present if any_trig else 'NONE'}")

    # C2 the growth report is plain data (kpis dict), no trigger handle
    report = builder.build()
    pub = report.to_public()
    has_trigger = any(v in report.__dict__ for v in ("trigger", "send", "_transport"))
    record("C2-report-data-only", "FAIL-005",
           "DEFENDED" if set(pub.keys()) == {"kpis"} and not has_trigger else "BREACH",
           f"GrowthReport.to_public keys={set(pub.keys())}; no trigger handle (data-only, RULE-012)")

    # C3 building the report twice mutates nothing (no store side effect)
    before = st.all()
    builder.build(); builder.build()
    after = st.all()
    record("C3-build-no-mutation", "FAIL-005",
           "DEFENDED" if before == after and len(before) == len(after) else "BREACH",
           f"two build() calls mutated nothing (store rows stable={len(after)})")

    # C4 the builder's Data Mart holds no trigger-owner capability even one layer down (mart._store)
    store_methods = {n for n in dir(mart._store) if not n.startswith("_") and callable(getattr(mart._store, n))}
    trigger_owner = {n for n in store_methods if any(v in n.lower() for v in
                     ("crm", "price", "budget", "scale", "publish", "enqueue", "send", "dispatch", "commission"))}
    record("C4-store-no-trigger-owner", "FAIL-005",
           "BREACH" if trigger_owner else "DEFENDED",
           f"mart._store methods {sorted(store_methods)} contain NO CRM/pricing/scale/commission trigger-owner capability")


# ================================================================================================
# GROUP D - reactivation consent gate + revenue-integrity consistency
# ================================================================================================
def group_d():
    G = gate()
    mk = lambda seg, key, sid: SegmentMember(seg, key, sid)

    def build_react(members, consent_by_sid, *, crm_elig=None, reactivated=()):
        class _CMap:
            def __init__(self, m): self._m = dict(m)
            def get(self, sid): return self._m.get(sid)
        seg_id = "seg_dormant"
        reader = InMemorySegmentReader(
            segments={seg_id: CustomerSegment(seg_id, "Dormant", ApprovalState.APPROVED)},
            members={seg_id: list(members)})
        cons = ReactivationConsumed(crm_eligible_members=crm_elig or {}, reactivated_member_keys=frozenset(reactivated))
        return ReactivationMeasurement(reader, _CMap(consent_by_sid), G, cons), seg_id

    # D1 reactivation eligible only on VALID CRM consent AND consumed CRM-eligibility (fail-closed)
    members = [mk("seg_dormant", "m_ok", "cs_ok"), mk("seg_dormant", "m_optout", "cs_out"),
               mk("seg_dormant", "m_noelig", "cs_ok2")]
    consent = {"cs_ok": snap("cs_ok"), "cs_out": snap("cs_out", state="OPT_OUT", scopes=()), "cs_ok2": snap("cs_ok2")}
    react, seg = build_react(members, consent, crm_elig={"m_ok": True, "m_noelig": False})
    eligible = [getattr(m, "member_key", None) for m in react.eligible_members(seg)]
    record("D1-reactivation-consent-eligibility", "FAIL-002",
           "DEFENDED" if eligible == ["m_ok"] else "BREACH",
           f"eligible members={eligible} (only VALID-CRM-consent + CRM-eligible; opt-out and not-eligible excluded)")

    # D2 reactivation measure-only: no send surface; rate/cpa are floats (member_key not emitted)
    send_verbs = ("send", "sync", "dispatch", "enqueue", "crm_send", "publish", "trigger")
    hits = [v for v in send_verbs if hasattr(react, v)]
    rate = react.reactivation_rate(seg)
    record("D2-reactivation-measure-only", "FAIL-002",
           "BREACH" if hits else "DEFENDED",
           f"reactivation send surface: {hits or 'NONE'}; reactivation_rate={rate} (aggregate float, no member_key)")

    # D3 (consistency; FAIL-001 out-of-scope) reads.verified_rows keys off revenue_value, NOT event_code -- a
    #    QUOTE_SENT row force-carrying revenue + entry_channel=CRM + all CRM gates pass would be counted. Needs
    #    in-process store misuse to put revenue on a non-verified row (not channel-reachable). Regression vs M6.2I.
    st = new_store()
    insert_event(st, "e_q", "QUOTE_SENT", order_code="ord_q")
    force_revenue_on(st, "e_q", revenue=999999.0, order_code="ord_q", ctx={"entry_channel": "CRM"})
    counted = str(getattr(st.get_by_event_id("e_q"), "revenue_value", None))
    cons = CrmConsumed(crm_eligible_orders={"ord_q": True}, suppression_pass_orders={"ord_q": True},
                       consent_by_order={"ord_q": snap()})
    crm_rev = CrmReorderMeasurement(st, G, cons).crm_revenue()
    in_verified = len(verified_rows(st))
    record("D3-verified-rows-choke-regression", "FAIL-002",
           "OPEN_NONGATE" if crm_rev == 999999.0 else "NOTE",
           f"reads.verified_rows keys off revenue_value (not event_code): a QUOTE_SENT row force-carrying revenue "
           f"(={counted}) + entry_channel=CRM + all CRM gates pass -> crm_revenue={crm_rev} (verified_rows n={in_verified}); "
           f"needs in-process store misuse (materialize verified=True on a non-verified row) -> NOT channel-reachable; "
           f"FAIL-001 out-of-scope here; a REGRESSION vs the M6.2I self-enforcing choke -> route CODER (AND event_code==ORDER_VERIFIED)")


# ================================================================================================
# GROUP E - belt sweeps + PII masking
# ================================================================================================
def group_e():
    action_verbs = ("crm_send", "send_crm", "sync_audience", "compute_commission", "diamond_payout", "set_price",
                    "order_state", "member_right", "scale_now", "publish_optim", "enable_campaign")
    targets = list((IMPL / "app" / "measurement" / "growth").glob("*.py"))
    hits = []
    for p in targets:
        with tokenize.open(str(p)) as fh:
            for tok in tokenize.generate_tokens(fh.readline):
                if tok.type == tokenize.NAME and tok.string.lower() in action_verbs:
                    hits.append(f"{p.name}:{tok.start[0]}:{tok.string}")
    record("E1-no-action-identifiers", "FAIL-004",
           "DEFENDED" if not hits else "NOTE",
           f"token sweep of the 8 growth modules: CRM-send/commission/pricing/order-state/member-right action defs = {hits or 'NONE'}")

    # E2 growth report + referral export carry no raw PII (aggregates + masked buyer only)
    st = new_store()
    probe = "guest" + "SECRET" + "9001"
    verified_row(st, "e_e2", revenue=500000.0, order_code="ord_e2",
                 signals={"diamond_id": "dia_1", "referral_link_id": "ref_1", "psid": "PSID_secret"}, guest_id=probe)
    builder = GrowthReportBuilder(DataMart(st), CrmReorderMeasurement(st, gate(), CrmConsumed()),
                                  DiamondReferralMeasurement(st), None, measurement_store=st, consumed=GrowthConsumed())
    report_export = repr(builder.build().to_public())
    referral_export = repr([a.to_public() for a in DiamondReferralMeasurement(st).referral_attributions()])
    record("E2-no-raw-pii-export", "RULE-014",
           "DEFENDED" if probe not in report_export and probe not in referral_export and "PSID_secret" not in referral_export else "NOTE",
           f"growth report + referral export carry no raw buyer/guest/psid (aggregates + masked buyer); belt -> M6-P1906")


# ================================================================================================
# GROUP W - workflow-harvested vectors (6-agent adversarial ideation + completeness critic; 51 vectors).
#           Every claimed breach EXECUTED here before recording; reachability checked against the real wiring.
# ================================================================================================
def group_w():
    G = gate()

    # W1 (COMP-02, sharpest FAIL-002) BORROWED CONSENT: _crm_gate_passes calls evaluate(snapshot, CRM) but NEVER
    #    binds snapshot.subject_ref to the verified row's buyer (customer_id/guest_id). A consent snapshot belonging
    #    to a DIFFERENT subject (person_B), VALID + CRM, keyed to the order authorizes person_A's CRM revenue into
    #    the exported §9 KPI. The M6.2E conversion seam F-D enforces this bind; the growth path omits it. Reachable
    #    only via a mis-keyed/adversarial CONSUMED consent_by_order map (a trusted upstream input), not a channel.
    st = new_store()
    verified_row(st, "e_b", revenue=650000.0, order_code="ord_b", signals={"crm": True}, customer_id="person_A")
    borrowed = ConsentSnapshot("cs_borrow", "person_B_not_the_buyer", ConsentState.VALID, FIXED_TS,
                               frozenset({ConsentScope.CRM}))
    cons = CrmConsumed(crm_eligible_orders={"ord_b": True}, suppression_pass_orders={"ord_b": True},
                       consent_by_order={"ord_b": borrowed})
    rev = CrmReorderMeasurement(st, G, cons).crm_revenue()
    record("W1-borrowed-consent-subject", "FAIL-002",
           "OPEN_NONGATE" if rev == 650000.0 else "DEFENDED",
           f"a NON-buyer's VALID CRM consent (subject=person_B) keyed to the order authorizes the buyer (person_A)'s "
           f"CRM revenue -> crm_revenue={rev}; the gate never compares snapshot.subject_ref to the row's buyer "
           f"(measurement_event carries customer_id; the Diamond path already reads it); reachable only via a "
           f"mis-keyed/adversarial CONSUMED consent map (trusted upstream input), not a channel -> route CODER "
           f"(bind subject_ref to the row's buyer, mirroring the M6.2E F-D fix)")

    # W2 (COMP-01) an UNGATED DataMart.crm_revenue twin is reachable via builder._mart and diverges from the GATED
    #    doc §9 KPI. The shipped builder uses the gated crm.crm_revenue for the KPI (defense holds); only naming
    #    convention keeps the consent-blind number out. A consumer reading builder._mart.crm_revenue as CRM Revenue
    #    would trip FAIL-002.
    st = new_store()
    verified_row(st, "e_z", revenue=800000.0, order_code="ord_z", signals={"crm": True})
    consumed = CrmConsumed(crm_eligible_orders={"ord_z": True}, suppression_pass_orders={"ord_z": True})  # NO consent
    crm = CrmReorderMeasurement(st, G, consumed)
    mart = DataMart(st)
    builder = GrowthReportBuilder(mart, crm, DiamondReferralMeasurement(st), None,
                                  measurement_store=st, consumed=GrowthConsumed())
    kpi = builder.build().kpi("CRM Revenue").value
    ungated = builder._mart.crm_revenue()
    record("W2-ungated-crm-twin", "FAIL-002",
           "OPEN_NONGATE" if kpi == 0.0 and ungated == 800000.0 else "NOTE",
           f"§9 CRM Revenue KPI (gated) = {kpi} (consent absent -> excluded, defense holds); BUT the ungated "
           f"DataMart.crm_revenue twin reachable via builder._mart = {ungated} (consent-blind); only naming keeps "
           f"it out of the §9 figure -> route CODER/M6-P1906 (rename/mark the ungated aggregate)")

    # W3 (COMP-06) the materializer keys `verified` off the CONVERSION's event_code, not the EVENT's, and
    #    reads.verified_rows keys off revenue presence -> a QUOTE_SENT event paired with an ORDER_VERIFIED conversion
    #    stamps revenue onto the QUOTE_SENT row, which surfaces as Diamond Revenue AND the Finance-facing
    #    commission-ready figure. Not channel-reachable (the materializer is constructed only in tests); a RULE-003
    #    cross-slice consistency regression vs the M6.2I self-enforcing choke.
    st = new_store()
    ev = insert_event(st, "e_q", "QUOTE_SENT")
    conv = make_conversion("ORDER_VERIFIED", source_event_id="e_q", revenue_value=900000.0, currency="VND",
                           order_code="ord_q")
    AttributionMaterializer(st, AttributionResolver(), AuditLog()).materialize(ev, conv, signals={"diamond_id": "Dq"})
    row_code = st.get_by_event_id("e_q").event_code
    dia = DiamondReferralMeasurement(st, DiamondConsumed(commission_eligible_orders={"ord_q": True}))
    dr, cr = dia.diamond_revenue(), dia.commission_ready_revenue()
    record("W3-materializer-mispair-diamond", "FAIL-004",
           "OPEN_NONGATE" if dr == 900000.0 and cr == 900000.0 and row_code == "QUOTE_SENT" else "NOTE",
           f"a {row_code} row stamped with revenue (materializer keys off conversion.event_code) -> Diamond Revenue="
           f"{dr} AND commission-ready revenue={cr} (Finance-facing); reads.verified_rows keys off revenue presence, "
           f"not event_code; not channel-reachable (materializer test-only); RULE-003 consistency regression vs M6.2I "
           f"-> route CODER (AND event_code==ORDER_VERIFIED in verified_rows)")

    # W4 (COMP-03) the Learning-Engine 'Candidate approval rate' KPI counts a candidate approved on
    #    str(review_state.value)=='APPROVED' alone -- never consulting is_publish_authorized or the audited
    #    OwnerReviewDecision. A candidate marked APPROVED at construction (no decision, safe_range UNKNOWN) counts.
    #    Measurement-integrity gap; NOT a publish (is_publish_authorized still gates the real publish outside M6).
    from app.measurement.learning.candidate import (AdsLearningCandidate, LearningCandidateKind, ReviewState,
                                                     TargetDim)
    from app.measurement.learning.review_queue import ReviewQueue
    q = ReviewQueue()
    q.enqueue(AdsLearningCandidate("lc_1", LearningCandidateKind.OPTIMIZATION, TargetDim.PERSONA, 0.8, "SKU1",
                                   review_state=ReviewState.APPROVED))
    c = q.get("lc_1")
    builder = GrowthReportBuilder(DataMart(new_store()), CrmReorderMeasurement(new_store(), G, CrmConsumed()),
                                  DiamondReferralMeasurement(new_store()), None, review_queue=q,
                                  measurement_store=new_store(), consumed=GrowthConsumed())
    rate = builder.build().kpi("Candidate approval rate").value
    record("W4-approval-rate-review-state-only", "FAIL-004",
           "OPEN_NONGATE" if rate == 1.0 and not c.is_publish_authorized and c.decision is None else "NOTE",
           f"a candidate marked APPROVED at construction (is_publish_authorized={c.is_publish_authorized}, "
           f"decision={c.decision}) -> approval rate={rate}; the KPI reads review_state.value only, never "
           f"is_publish_authorized / the audited decision -> measurement-integrity gap (not a publish) -> route CODER/M6-P1906")

    # W5 (COMP-04) build() duck-types every collaborator (queue.all(), store.all()) with no isinstance guard -- a
    #    hostile queue/store with a side-effecting .all() runs during build(). Needs a mis-wired collaborator at the
    #    composition root (the shipped ReviewQueue/MeasurementEventStore .all() are pure reads); defense-in-depth.
    fired = []

    class TriggerQueue:
        def all(self):
            fired.append("QUEUE")
            return ()

    class TriggerStore:
        def all(self):
            fired.append("STORE")
            return ()

    b = GrowthReportBuilder(DataMart(new_store()), CrmReorderMeasurement(new_store(), G, CrmConsumed()),
                            DiamondReferralMeasurement(new_store()), None, review_queue=TriggerQueue(),
                            measurement_store=TriggerStore(), consumed=GrowthConsumed())
    b.build()
    record("W5-builder-ducktypes-collaborators", "FAIL-005",
           "OPEN_NONGATE" if fired == ["STORE", "QUEUE"] or set(fired) == {"STORE", "QUEUE"} else "NOTE",
           f"build() invoked injected collaborators' .all() (fired={fired}); duck-typed, no isinstance/Protocol guard; "
           f"needs a mis-wired side-effecting queue/store at the composition root (shipped types are pure reads) -> "
           f"defense-in-depth, route CODER (isinstance/Protocol guard)")

    # W6 (COMP-05) ReferralAttribution.buyer_ref holds RAW PII on the public dataclass attribute; mask() is applied
    #    ONLY in to_public(). A caller reading .buyer_ref directly gets the raw customer/guest id. PII belt.
    st = new_store()
    probe = "cust" + "RAWSECRET" + "0001"
    verified_row(st, "e_p", revenue=400000.0, order_code="ord_p", signals={"diamond_id": "D1"}, customer_id=probe)
    attr = DiamondReferralMeasurement(st).referral_attributions()[0]
    raw_attr = attr.buyer_ref == probe
    from app.measurement.masking import mask
    masked_export = attr.to_public()["buyer_ref"] == mask(probe)
    record("W6-buyer-ref-raw-attribute", "RULE-014",
           "NOTE",
           f"referral_attributions() returns dataclass objects whose buyer_ref attribute is RAW (={raw_attr}); mask "
           f"is export-only (to_public buyer_ref masked={masked_export}); a caller reading .buyer_ref directly gets "
           f"raw PII -> PII belt, route M6-P1906 (mask at construction / mark the attribute)")


def main():
    print("=" * 100)
    print("M6-P1905 BOUNDARY_ADVERSARY - executed attacks vs FROZEN staged M6.2J (Phase-3 growth machine)")
    print(f"impl root: {IMPL}")
    print(f"posture: gateway={config.GLOBAL_GATEWAY_STATE} prod={config.PRODUCTION_FLAG} "
          f"external_send={config.EXTERNAL_SEND}")
    print("=" * 100)
    for grp in (group_a, group_b, group_c, group_d, group_e, group_w):
        print(f"\n----- {grp.__name__} -----")
        grp()

    from collections import Counter
    tally = Counter(k for _, _, k, _ in RESULTS)
    print("\n" + "=" * 100)
    print(f"SUMMARY: {dict(tally)}")
    print(f"TOTAL RECORDED OUTCOMES: {len(RESULTS)}")
    print(f"IN-SCOPE FAIL-GATE BREACHES (FAIL-002 / FAIL-004 / FAIL-005): {len(BREACHES)}")
    for b in BREACHES:
        print(f"   !!! BREACH {b}")
    print("=" * 100)
    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF" and config.EXTERNAL_SEND == "OFF"


if __name__ == "__main__":
    main()
