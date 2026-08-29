"""M6-P1805 BOUNDARY_ADVERSARY executed attack harness for slice M6.2I (Phase-2 Golden-Hour funnel measurement).

READ-ONLY adversary: imports the FROZEN staged M6.2I app and drives the REAL code paths. Never modifies app code,
never writes 04-artifacts/state, never operates a session / sends / scales (external_send stays OFF).

In-scope fail gates ATTACKED: M6-FAIL-001 (revenue misuse) and M6-FAIL-010 (phase jump -- a Phase-2 measurement
must not perform a later-phase / live-op action). In-scope rules: RULE-003 (revenue only ORDER_VERIFIED),
RULE-013 (no Core override; live sessions are Gateway/Live's), RULE-016 (phase order locked), RULE-021 (order-
capture valid only when Commerce passed; M6 records, never validates).

Every claimed breach is EXECUTED here before it is recorded. Outcome classes: DEFENDED / OPEN_NONGATE / NOTE /
BREACH (BREACH = a non-verified value shown as revenue, OR the funnel performs a later-phase/live-op action).

Launcher: py -3.12 -B (byte-clean). psid/PII probes assembled at runtime, never echoed raw.
"""
from __future__ import annotations

import math
import sys
import tokenize
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
PACK_ROOT = HERE.parents[3]
IMPL = PACK_ROOT / "04-artifacts" / "impl" / "M6.2I"
if not IMPL.exists():
    IMPL = Path(r"D:\M6\Module6-workspace\04-artifacts\impl\M6.2I")
sys.path.insert(0, str(IMPL))

from app import config
from app.measurement.audit import AuditLog
from app.measurement.consent.gate import ConsentGate
from app.measurement.models.consumed import ConsentScope, ConsentSnapshot, ConsentState
from app.measurement.models.measurement_event import AdsMeasurementEvent, DataQualityStatus
from app.measurement.models.conversion_event import ConversionEvent
from app.measurement.attribution.materializer import AttributionMaterializer
from app.measurement.attribution.resolver import AttributionResolver
from app.measurement.store.measurement_event_store import MeasurementEventStore
from app.measurement.funnel.flow import CHAIN, FlowStage, REVENUE_VALID_EVENT, stage_for
from app.measurement.funnel.golden_hour import GoldenHourState, observe_state
from app.measurement.funnel.funnel import GoldenHourFunnel
from app.measurement.funnel.retargeting import RetargetingMeasurement, RETARGETING_SIGNAL_EVENTS

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


def insert_event(store, event_id, event_code, *, live_session_id=None, **over):
    base = dict(event_id=event_id, event_code=event_code, event_ts=FIXED_TS,
                idempotency_key=over.pop("idempotency_key", f"idem_{event_id}"),
                correlation_id=over.pop("correlation_id", "corr"), ingested_at=FIXED_TS,
                live_session_id=live_session_id)
    base.update(over)
    row = AdsMeasurementEvent(**base)
    store.insert(row)
    return row


def make_conversion(event_code, source_event_id, **over):
    base = dict(conversion_id=f"conv_{event_code}_{source_event_id}", event_code=event_code,
                source_event_id=source_event_id, correlation_id="corr_c",
                customer_or_guest_key="guest_mapped_ok", consent_snapshot_id="cs_valid",
                occurred_at=FIXED_TS, idempotency_key=f"idem_{event_code}_{source_event_id}")
    base.update(over)
    return ConversionEvent(**base)


def verified_row(store, event_id, *, revenue, order_code, live_session_id="ls_1", signals=None,
                 event_code="ORDER_VERIFIED", **over):
    ev = insert_event(store, event_id, event_code, live_session_id=live_session_id, **over)
    conv = make_conversion(event_code, source_event_id=event_id, revenue_value=float(revenue),
                           currency="VND", order_code=order_code)
    AttributionMaterializer(store, AttributionResolver(), AuditLog()).materialize(ev, conv, signals=signals)
    return store.get_by_event_id(event_id)


def force_revenue_on(store, event_id, *, revenue, order_code):
    """Force a Zone-B revenue_value onto whatever row `event_id` is (even a non-ORDER_VERIFIED one) via the store's
    materialize verified=True path -- the mispaired/misused revenue the funnel choke must still exclude."""
    store.materialize(event_id, attribution_context={"source_confidence": "LOW", "conflict_status": "NONE"},
                      revenue_value=float(revenue), order_code=order_code, verified=True)


def funnel(store, **kw):
    return GoldenHourFunnel(store, **kw)


# ================================================================================================
# GROUP A - FAIL-001 : funnel verified-only revenue, SELF-ENFORCING choke (event_code AND revenue)
# ================================================================================================
def group_a():
    # A1 a QUOTE_SENT counts in the funnel Quote stage but contributes 0 revenue (SMK-004)
    st = new_store()
    insert_event(st, "e_q", "QUOTE_SENT", live_session_id="ls_1")
    v = funnel(st).view_for("ls_1")
    record("A1-quote-not-revenue", "FAIL-001",
           "DEFENDED" if v.verified_revenue == 0.0 and v.stage_count(FlowStage.MESSENGER_TO_QUOTE) == 1 else "BREACH",
           f"QUOTE_SENT -> verified_revenue={v.verified_revenue}, MESSENGER_TO_QUOTE stage count="
           f"{v.stage_count(FlowStage.MESSENGER_TO_QUOTE)} (measured, never revenue)")

    # A2 ORDER_CREATED (draft) -> QUOTE_TO_ORDER stage, 0 revenue
    st = new_store()
    insert_event(st, "e_d", "ORDER_CREATED", live_session_id="ls_1")
    v = funnel(st).view_for("ls_1")
    record("A2-draft-not-revenue", "FAIL-001",
           "DEFENDED" if v.verified_revenue == 0.0 and v.stage_count(FlowStage.QUOTE_TO_ORDER) == 1 else "BREACH",
           f"ORDER_CREATED -> verified_revenue={v.verified_revenue}, QUOTE_TO_ORDER stage count="
           f"{v.stage_count(FlowStage.QUOTE_TO_ORDER)}")

    # A3 the full fail-gate taxonomy -> 0 revenue
    st = new_store()
    for i, code in enumerate(("QUOTE_SENT", "QUOTE_CART_CREATED", "ORDER_CREATED", "PAYMENT_WAITING", "COD_WAITING")):
        insert_event(st, f"e_nr_{i}", code, live_session_id="ls_1")
    v = funnel(st).view_for("ls_1")
    record("A3-nonrevenue-taxonomy", "FAIL-001",
           "DEFENDED" if v.verified_revenue == 0.0 else "BREACH",
           f"quote/cart/draft/payment-waiting/cod-waiting -> verified_revenue={v.verified_revenue}")

    # A4 (SELF-ENFORCING choke, closes the M6.2F F-DASH-1 gap) a QUOTE_SENT row FORCE-carrying a revenue_value on a
    #    non-verified event code STILL contributes 0 -- the funnel ANDs event_code==ORDER_VERIFIED with revenue.
    st = new_store()
    insert_event(st, "e_fq", "QUOTE_SENT", live_session_id="ls_1")
    force_revenue_on(st, "e_fq", revenue=999999.0, order_code="ord_bad")
    row = st.get_by_event_id("e_fq")
    v = funnel(st).view_for("ls_1")
    record("A4-self-enforcing-choke", "FAIL-001",
           "DEFENDED" if row.revenue_value == 999999.0 and v.verified_revenue == 0.0 else "BREACH",
           f"QUOTE_SENT row force-carrying revenue_value={row.revenue_value} -> funnel verified_revenue="
           f"{v.verified_revenue} (event_code!=ORDER_VERIFIED excluded; closes M6.2F F-DASH-1)")

    # A5 PAYMENT_COMPLETED force-carrying revenue -> 0 (only ORDER_VERIFIED is REVENUE_VALID_EVENT)
    st = new_store()
    insert_event(st, "e_pc", "PAYMENT_COMPLETED", live_session_id="ls_1")
    force_revenue_on(st, "e_pc", revenue=500000.0, order_code="ord_pc")
    v = funnel(st).view_for("ls_1")
    record("A5-payment-completed-not-revenue", "FAIL-001",
           "DEFENDED" if v.verified_revenue == 0.0 else "BREACH",
           f"PAYMENT_COMPLETED force-carrying revenue -> funnel verified_revenue={v.verified_revenue} "
           f"(REVENUE_VALID_EVENT={REVENUE_VALID_EVENT} only)")

    # A6 a genuine ORDER_VERIFIED row IS counted (non-vacuous control)
    st = new_store()
    verified_row(st, "e_ov", revenue=250000.0, order_code="ord_9", live_session_id="ls_1")
    v = funnel(st).view_for("ls_1")
    record("A6-verified-counted", "FAIL-001",
           "DEFENDED" if v.verified_revenue == 250000.0 else "BREACH",
           f"genuine ORDER_VERIFIED -> verified_revenue={v.verified_revenue} (discriminating, not vacuous)")

    # A7 cross-surface: funnel and the M6.2F dashboard (same store) agree 0 revenue / no ROAS for a quote-only store
    st = new_store()
    insert_event(st, "e_q2", "QUOTE_SENT", live_session_id="ls_1")
    fv = funnel(st).view_for("ls_1").verified_revenue
    from app.measurement.dashboard.data_mart import DataMart
    from app.measurement.dashboard.kpi_metrics import compute_metrics
    mart = DataMart(st)
    metrics = {m.name: m for m in compute_metrics(mart)}
    dash_rev = metrics["Revenue Verified"].value
    dash_roas = metrics["ROAS"].value
    record("A7-cross-surface-agreement", "FAIL-001",
           "DEFENDED" if fv == 0.0 and dash_rev == 0.0 and dash_roas is None else "BREACH",
           f"quote-only: funnel revenue={fv}, dashboard Revenue Verified={dash_rev}, ROAS={dash_roas} (both agree)")

    # A8 NaN/negative revenue on a verified row -> note (carried M6.2E O-5 / robustness, not inflation)
    st = new_store()
    insert_event(st, "e_nan", "ORDER_VERIFIED", live_session_id="ls_1")
    force_revenue_on(st, "e_nan", revenue=float("nan"), order_code="ord_nan")
    v = funnel(st).view_for("ls_1")
    record("A8-nan-revenue", "FAIL-001", "NOTE",
           f"NaN revenue on a verified row -> funnel verified_revenue={v.verified_revenue!r} (poisons the sum; "
           f"root cause is non-finite revenue at ingest -> DQ/robustness, M6-P1806; not a quote-as-revenue inflation)")


# ================================================================================================
# GROUP B - FAIL-010 / RULE-016 / RULE-013 : measure-only; no later-phase / live-op action
# ================================================================================================
_LIVEOP_ATTRS = ("start", "close", "open", "emit", "transition", "operate", "start_session", "close_session",
                 "go_live", "publish", "scale", "send", "dispatch", "enqueue", "write", "order_state",
                 "set_state", "advance", "run_live")


def group_b():
    st = new_store()
    verified_row(st, "e_b", revenue=250000.0, order_code="ord_9", live_session_id="ls_1")
    gf = funnel(st)
    ret = RetargetingMeasurement(ConsentGate(AuditLog()))

    # B1 GoldenHourFunnel / retargeting expose NO live-op / later-phase verb
    surfaces = {"GoldenHourFunnel": gf, "RetargetingMeasurement": ret}
    present = {n: [a for a in _LIVEOP_ATTRS if hasattr(o, a)] for n, o in surfaces.items()}
    any_liveop = any(present.values())
    record("B1-no-liveop-verb", "FAIL-010",
           "BREACH" if any_liveop else "DEFENDED",
           f"live-op/later-phase attrs on funnel/retargeting: {present if any_liveop else 'NONE'}")

    # B2 golden_hour module: observe_state only; NO session controller (start/close/transition/emit)
    import app.measurement.funnel.golden_hour as gh
    gh_funcs = [n for n in dir(gh) if not n.startswith("_") and callable(getattr(gh, n))]
    controller = [n for n in gh_funcs if any(v in n.lower() for v in
                  ("start", "close", "open", "emit", "transition", "operate", "drive"))]
    record("B2-golden-hour-measure-only", "FAIL-013" if False else "RULE-013",
           "BREACH" if controller else "DEFENDED",
           f"golden_hour public callables={gh_funcs}; session-controller verbs={controller or 'NONE'} (observe-only)")

    # B3 assemble()/view_for() mutate nothing (read-only projection)
    st2 = new_store()
    verified_row(st2, "e_b3", revenue=100000.0, order_code="ord_b3", live_session_id="ls_1")
    before = st2.all()
    gf2 = funnel(st2)
    gf2.assemble(); gf2.assemble()
    after = st2.all()
    record("B3-read-only-no-mutation", "FAIL-010",
           "DEFENDED" if before == after and len(before) == len(after) else "BREACH",
           f"two assemble() calls mutated nothing (store rows stable={len(after)})")

    # B4 the funnel package imports NO scale/learning/publish/outbox/dispatcher execution path (no phase-jump)
    later_phase = ("scale", "learning", "outbox", "dispatcher", "transport")
    hits = []
    for p in (IMPL / "app" / "measurement" / "funnel").glob("*.py"):
        txt = p.read_text(encoding="utf-8")
        for mod in later_phase:
            if f"import {mod}" in txt or f"measurement.{mod}" in txt:
                hits.append(f"{p.name}:{mod}")
    record("B4-no-later-phase-import", "FAIL-010",
           "DEFENDED" if not hits else "BREACH",
           f"funnel package imports of scale/learning/outbox/dispatcher/transport: {hits or 'NONE'} (measure-only)")

    # B5 observe_state fail-closed: malformed / None / unknown -> UNKNOWN; never assumes PRE/LIVE; a real state passes
    cases = {
        "None": observe_state(None), "unknown": observe_state("ACTIVE_NOW"), "int": observe_state(3),
        "obj": observe_state(object()), "PRE": observe_state("PRE"), "enum": observe_state(GoldenHourState.LIVE),
    }
    ok = (cases["None"] is GoldenHourState.UNKNOWN and cases["unknown"] is GoldenHourState.UNKNOWN
          and cases["int"] is GoldenHourState.UNKNOWN and cases["obj"] is GoldenHourState.UNKNOWN
          and cases["PRE"] is GoldenHourState.PRE and cases["enum"] is GoldenHourState.LIVE)
    record("B5-observe-fail-closed", "RULE-013",
           "DEFENDED" if ok else "BREACH",
           f"observe_state: None/unknown/int/obj -> UNKNOWN; 'PRE'->PRE; enum passes -> {{k:v.value for...}}="
           f"{ {k: v.value for k, v in cases.items()} }")


# ================================================================================================
# GROUP C - RULE-021 : order-capture recorded (fail-closed), never validated/owned
# ================================================================================================
def group_c():
    st = new_store()
    verified_row(st, "e_c", revenue=250000.0, order_code="ord_9", live_session_id="ls_1")

    # C1 capture_gate_passed fail-closed across the map states
    matrix = {}
    for label, capmap in (("absent", None), ("empty", {}), ("false", {"ord_9": False}),
                          ("truthy_1", {"ord_9": 1}), ("truthy_yes", {"ord_9": "yes"}), ("true", {"ord_9": True})):
        v = funnel(st, capture_gate_passed_by_order=capmap).view_for("ls_1")
        matrix[label] = v.capture_gate_passed
    # only an explicit True (identity) clears; 1/'yes' are NOT True (fail-closed on `is True`)
    ok = (matrix["absent"] is False and matrix["empty"] is False and matrix["false"] is False
          and matrix["truthy_1"] is False and matrix["truthy_yes"] is False and matrix["true"] is True)
    record("C1-capture-fail-closed", "RULE-021",
           "DEFENDED" if ok else "BREACH",
           f"capture_gate_passed by map: {matrix} (only explicit True clears; truthy 1/'yes' do NOT)")

    # C2 a session with an order but the OTHER order's flag True -> still False (every order must pass)
    st2 = new_store()
    verified_row(st2, "e_c2a", revenue=100000.0, order_code="ord_A", live_session_id="ls_1")
    insert_event(st2, "e_c2b", "ORDER_CREATED", live_session_id="ls_1", order_code="ord_B")
    v = funnel(st2, capture_gate_passed_by_order={"ord_A": True}).view_for("ls_1")
    record("C2-every-order-must-pass", "RULE-021",
           "DEFENDED" if v.capture_gate_passed is False else "BREACH",
           f"one order flagged True, another (ord_B) absent -> capture_gate_passed={v.capture_gate_passed} (all-or-fail)")

    # C3 M6 records, never validates: capture flag is a CONSUMED constructor input; funnel has no validation method
    validate_verbs = ("validate", "check_stock", "fulfillment", "trust", "confirm_order", "own_order", "gate_order")
    gf = funnel(st)
    hits = [v for v in validate_verbs if hasattr(gf, v)]
    record("C3-records-not-validates", "RULE-021",
           "BREACH" if hits else "DEFENDED",
           f"funnel Commerce-validation methods: {hits or 'NONE'} (capture flag is CONSUMED, injected at ctor; RULE-021)")


# ================================================================================================
# GROUP D - retargeting: consent-valid (AUDIENCE_SYNC)-only; measure-only, no send
# ================================================================================================
def _snap(state=ConsentState.VALID, scopes=frozenset({ConsentScope.AUDIENCE_SYNC})):
    return ConsentSnapshot("cs", "guest_x", state, FIXED_TS, scopes)


def group_d():
    ret = RetargetingMeasurement(ConsentGate(AuditLog()))

    # D1 eligible ONLY on a recognized signal + VALID AUDIENCE_SYNC consent
    good = ret.is_eligible("LIVE_COMMENT", _snap())
    states = {
        "missing": ret.is_eligible("LIVE_COMMENT", _snap(ConsentState.MISSING, frozenset())),
        "expired": ret.is_eligible("LIVE_COMMENT", _snap(ConsentState.EXPIRED, frozenset())),
        "optout": ret.is_eligible("LIVE_COMMENT", _snap(ConsentState.OPT_OUT, frozenset())),
        "absent": ret.is_eligible("LIVE_COMMENT", None),
        "wrong_scope": ret.is_eligible("LIVE_COMMENT", _snap(ConsentState.VALID, frozenset({ConsentScope.EXTERNAL_MEASUREMENT}))),
    }
    ok = good is True and not any(states.values())
    record("D1-consent-valid-only", "FAIL-001" if False else "RULE-002",
           "DEFENDED" if ok else "BREACH",
           f"recognized+VALID+AUDIENCE_SYNC eligible={good}; missing/expired/optout/absent/wrong-scope eligible="
           f"{states} (all fail-closed)")

    # D2 an unrecognized / order-state code is NEVER eligible even with valid consent (fail-closed)
    bad_codes = {c: ret.is_eligible(c, _snap()) for c in ("ORDER_VERIFIED", "ORDER_CREATED", "PAYMENT_COMPLETED",
                                                          "NOT_A_REAL_EVENT", "", 123)}
    record("D2-unrecognized-not-eligible", "RULE-002",
           "DEFENDED" if not any(bad_codes.values()) else "BREACH",
           f"non-engagement / order-state / unknown codes eligible={bad_codes} (verified/order codes excluded)")

    # D3 measure-only: no send/enqueue/transport surface; measure() returns counts only
    send_verbs = ("send", "enqueue", "dispatch", "transport", "sync_audience", "push", "publish")
    hits = [v for v in send_verbs if hasattr(ret, v)]
    reach = ret.measure([("LIVE_COMMENT", _snap()), ("ORDER_VERIFIED", _snap()), ("LIVE_VIEW", None)])
    record("D3-measure-only-no-send", "RULE-013",
           "BREACH" if hits else "DEFENDED",
           f"retargeting send verbs={hits or 'NONE'}; measure() -> eligible={reach.eligible}/considered={reach.considered} "
           f"(counts only, never an audience/send list)")

    # D4 consent scope hardening: ConsentGate coerces the requested scope via ConsentScope(scope). The EXACT enum
    #    value ('audience_sync') coerces to the member and passes; the NAME string ('AUDIENCE_SYNC') and a bogus
    #    substring ('audience') are NOT valid values -> denied as malformed (fail-closed, no substring fail-open).
    gate = ConsentGate(AuditLog())
    val = gate.evaluate(_snap(), ConsentScope.AUDIENCE_SYNC.value)  # 'audience_sync' -> coerces -> True
    name = gate.evaluate(_snap(), "AUDIENCE_SYNC")                  # the NAME, not a value -> denied (malformed)
    substr = gate.evaluate(_snap(), "audience")                    # substring of the value -> denied (no substring)
    record("D4-scope-hardening", "RULE-002",
           "DEFENDED" if val is True and name is False and substr is False else "NOTE",
           f"ConsentGate.evaluate: exact value 'audience_sync'->{val} (coerced+passes); NAME 'AUDIENCE_SYNC'->{name} "
           f"and substring 'audience'->{substr} (denied as malformed, no substring fail-open)")


# ================================================================================================
# GROUP E - belt sweeps: no action identifiers; PII masking on export
# ================================================================================================
def group_e():
    action_verbs = ("start_session", "close_session", "emit", "go_live", "publish", "scale_now", "raise_budget",
                    "enable_campaign", "order_state", "write_order", "crm_send", "set_price", "commission",
                    "sync_audience", "audience_send")
    targets = list((IMPL / "app" / "measurement" / "funnel").glob("*.py"))
    hits = []
    for p in targets:
        with tokenize.open(str(p)) as fh:
            for tok in tokenize.generate_tokens(fh.readline):
                if tok.type == tokenize.NAME and tok.string.lower() in action_verbs:
                    hits.append(f"{p.name}:{tok.start[0]}:{tok.string}")
    record("E1-no-action-identifiers", "RULE-013",
           "DEFENDED" if not hits else "NOTE",
           f"token sweep of the funnel package: session/send/scale/publish/order-state action defs = {hits or 'NONE'}")

    # E2 masking: a distinctive psid in attribution_context is masked on the funnel export; raw never appears
    st = new_store()
    probe = "psid" + "ZZZ" + "abcdefgh"
    verified_row(st, "e_mask", revenue=250000.0, order_code="ord_9", live_session_id="ls_1",
                 signals={"psid": probe, "comment_id": "cmt_1", "messenger_thread_id": "th_1",
                          "campaign_id": "c1", "adset_id": "a1", "ad_id": "ad1"},
                 campaign_id="c1", adset_id="a1", ad_id="ad1")
    v = funnel(st).view_for("ls_1")
    exported = repr(v.to_public())
    from app.measurement.masking import mask
    masked = mask(probe)
    record("E2-psid-masking", "RULE-014",
           "DEFENDED" if probe not in exported and masked in exported else "NOTE",
           f"raw psid absent from funnel export={probe not in exported}; masked present={masked in exported} "
           f"(comment_id/messenger_thread_id/live_session_id exported raw as trace ids); belt -> M6-P1806")


# ================================================================================================
# GROUP W - workflow-harvested vectors (6-agent adversarial ideation + completeness critic; 50 vectors).
#           Every claimed breach EXECUTED here before recording; reachability checked against the real wiring.
# ================================================================================================
def group_w():
    # W1 (CC-01, sharpest) revenue-choke TYPE-CONFUSION: a str-subclass event_code with a spoofed __eq__ defeats the
    #    `event_code == 'ORDER_VERIFIED'` equality (the same class the code hardened for CONSENT SCOPE but NOT the
    #    revenue path). Needs (a) a str-subclass event_code (ingest yields plain str, RULE-001) AND (b) object.
    #    __setattr__ to slip revenue past the store guard -> BOTH require in-process code exec; not channel-reachable.
    class SpoofCode(str):
        def __eq__(self, other):
            return True

        def __hash__(self):
            return hash("ORDER_VERIFIED")

    st = new_store()
    ev = AdsMeasurementEvent(event_id="evtS", event_code=SpoofCode("QUOTE_SENT"), event_ts=FIXED_TS,
                             idempotency_key="idemS", correlation_id="c", ingested_at=FIXED_TS, live_session_id="lsS")
    st.insert(ev)                                              # store sees revenue_value=None -> OK
    object.__setattr__(ev, "revenue_value", 9_000_000.0)      # frozen bypass; row CONTENT is still 'QUOTE_SENT'
    v = funnel(st).view_for("lsS")
    spoofed = v.verified_revenue == 9_000_000.0
    record("W1-revenue-choke-typeconfusion", "FAIL-001",
           "OPEN_NONGATE" if spoofed else "DEFENDED",
           f"str-subclass event_code w/ spoofed __eq__ + object.__setattr__ revenue -> funnel verified_revenue="
           f"{v.verified_revenue} (a QUOTE_SENT-content row counted as verified); needs in-process code exec x2 "
           f"(str-subclass NOT from ingest + frozen bypass) -> NOT channel-reachable; the code hardened consent-scope "
           f"membership but not the revenue event_code equality -> route CODER (compare via type(x) is str AND ==)")

    # W2 (CC-02) a hostile Mapping.get on the UN-COPIED attribution_context drives a REAL Zone-B write during
    #    assemble(): the funnel dict()-copies its two consumed maps but reads each event's attribution_context LIVE.
    #    In-process only (building+injecting WriteCtx already has store capability); a defense-in-depth inconsistency.
    st = new_store()
    holder = {"store": st}

    class WriteCtx(dict):
        _fired = False

        def get(self, k, d=None):
            if not WriteCtx._fired:
                WriteCtx._fired = True
                holder["store"].materialize("victim", attribution_context={"x": 1}, revenue_value=1.0,
                                            order_code="o", verified=True)
            return dict.get(self, k, d)

    insert_event(st, "victim", "ORDER_VERIFIED", live_session_id="lsV", order_code="o")
    st.insert(AdsMeasurementEvent(event_id="drv", event_code="LIVE_VIEW", event_ts=FIXED_TS, idempotency_key="kd",
                                  correlation_id="c", ingested_at=FIXED_TS, live_session_id="lsV",
                                  attribution_context=WriteCtx({"comment_id": "x"})))
    before_rev = st.get_by_event_id("victim").revenue_value
    funnel(st).view_for("lsV")
    after_rev = st.get_by_event_id("victim").revenue_value
    record("W2-mutable-ctx-drives-write", "FAIL-010",
           "OPEN_NONGATE" if before_rev is None and after_rev == 1.0 else "DEFENDED",
           f"a hostile attribution_context.get() runs INSIDE assemble() and drove a Zone-B write "
           f"(victim revenue {before_rev}->{after_rev}); the funnel dict()-copies its 2 consumed maps but reads the "
           f"event ctx LIVE; in-process only (injector already has store capability) -> route CODER (snapshot dict(ctx))")

    # W3 (CC-03) benign twin: a PLAIN mutable ctx shared with the store row makes the projection non-deterministic
    #    (TOCTOU) -- mutating it between assemble() calls changes the session grouping. Measurement drift, not a gate.
    st = new_store()
    ctx = {"live_session_id": "lsA"}
    st.insert(AdsMeasurementEvent(event_id="e4", event_code="LIVE_VIEW", event_ts=FIXED_TS, idempotency_key="k4",
                                  correlation_id="c", ingested_at=FIXED_TS, live_session_id=None,
                                  attribution_context=ctx))
    gf = funnel(st)
    k1 = gf.assemble()[0].live_session_id
    ctx["live_session_id"] = "lsB"
    k2 = gf.assemble()[0].live_session_id
    record("W3-mutable-ctx-toctou", "FAIL-001",
           "OPEN_NONGATE" if k1 == "lsA" and k2 == "lsB" else "DEFENDED",
           f"same store, same funnel, a shared mutable ctx mutated between reads -> session grouping {k1}->{k2} "
           f"(measurement drift / non-repeatable evidence; revenue/capture unaffected -- they key off row fields) "
           f"-> route CODER (snapshot dict(ctx)); NOT a boundary gate")

    # W4 (CC-05) decisive FAIL-010 negative: the funnel's TRANSITIVE import graph pulls the dashboard package (via
    #    kpi_metrics._safe_div) but ZERO Phase-3 (scale/learning/outbox/dispatcher/transport) module -- phase order
    #    not crossed at import time. (Closes B4's top-level-only check.)
    taint = ("scale", "learning", "outbox", "dispatch", "transport")
    loaded = [m for m in sys.modules if m.startswith("app.measurement.")]
    tainted = [m for m in loaded if any(t in m for t in taint)]
    dashboard_pulled = any("dashboard" in m for m in loaded)
    record("W4-no-phase3-transitive-import", "FAIL-010",
           "DEFENDED" if not tainted else "BREACH",
           f"funnel transitive import graph: Phase-3 (scale/learning/outbox/dispatcher/transport) modules loaded="
           f"{tainted or 'NONE'}; dashboard pulled (via kpi_metrics)={dashboard_pulled} (a Phase-2 sibling, not tainted)")

    # W5 (V-PII-07) the _trace per-field `or`-fold stitches comment_id / messenger_thread_id / psid from DIFFERENT
    #    events sharing one live_session_id -> a fabricated cross-person linkage in an evidence artifact (even with
    #    psid masked, a false association between two identifiable people). Attribution-integrity + PII, non-gate.
    st = new_store()
    st.insert(AdsMeasurementEvent(event_id="a", event_code="LIVE_COMMENT", event_ts=FIXED_TS, idempotency_key="ka",
                                  correlation_id="c", ingested_at=FIXED_TS, live_session_id="LSX",
                                  attribution_context={"comment_id": "cmt_personA"}))
    st.insert(AdsMeasurementEvent(event_id="b", event_code="MESSENGER_STARTED", event_ts=FIXED_TS, idempotency_key="kb",
                                  correlation_id="c", ingested_at=FIXED_TS, live_session_id="LSX",
                                  attribution_context={"messenger_thread_id": "thr_personB", "psid": "PSID_personB"}))
    tr = funnel(st).view_for("LSX").to_public()["trace"]
    stitched = tr["comment_id"] == "cmt_personA" and tr["messenger_thread_id"] == "thr_personB"
    record("W5-trace-cross-person-stitch", "FAIL-001",
           "OPEN_NONGATE" if stitched else "DEFENDED",
           f"two subjects sharing one live_session_id -> _trace `or`-fold stitches personA.comment_id + personB."
           f"messenger_thread_id into ONE trace={tr}; a fabricated cross-person linkage (psid masked but the "
           f"association is asserted); no subject/consent binding -> route CODER/M6-P1806 (bind trace to one subject)")

    # W6 (CC-04) frozen-view object.__setattr__ forges verified_revenue onto a produced view -> rides to_public();
    #    requires an in-process handle to the already-produced view (post-measurement tampering), generic to every
    #    frozen dataclass -> a process-integrity note, not a measurement-logic failure (the choke computed 0.0).
    st = new_store()
    insert_event(st, "e1", "LIVE_VIEW", live_session_id="ls")
    view = funnel(st).view_for("ls")
    computed = view.verified_revenue
    try:
        view.verified_revenue = 5_000_000.0
        forged = "plain-assign-succeeded"
    except FrozenInstanceError:
        object.__setattr__(view, "verified_revenue", 5_000_000.0)
        forged = f"object.__setattr__ -> {view.to_public()['verified_revenue']}"
    record("W6-frozen-view-setattr", "FAIL-001", "NOTE",
           f"the funnel computed verified_revenue={computed} correctly; a post-measurement object.__setattr__ forges "
           f"{forged} through to_public() -- frozen is a typo-guard, not a tamper boundary; needs an in-process handle "
           f"to the produced view -> evidence serializers must not treat a view's immutability as tamper-evidence")


def main():
    print("=" * 100)
    print("M6-P1805 BOUNDARY_ADVERSARY - executed attacks vs FROZEN staged M6.2I (Phase-2 Golden-Hour funnel)")
    print(f"impl root: {IMPL}")
    print(f"posture: gateway={config.GLOBAL_GATEWAY_STATE} prod={config.PRODUCTION_FLAG} "
          f"external_send={config.EXTERNAL_SEND} SCALE_EXECUTION_ENABLED={config.SCALE_EXECUTION_ENABLED} "
          f"LEARNING_AUTOPUBLISH_ENABLED={config.LEARNING_AUTOPUBLISH_ENABLED}")
    print("=" * 100)
    for grp in (group_a, group_b, group_c, group_d, group_e, group_w):
        print(f"\n----- {grp.__name__} -----")
        grp()

    from collections import Counter
    tally = Counter(k for _, _, k, _ in RESULTS)
    print("\n" + "=" * 100)
    print(f"SUMMARY: {dict(tally)}")
    print(f"TOTAL RECORDED OUTCOMES: {len(RESULTS)}")
    print(f"IN-SCOPE FAIL-GATE BREACHES (FAIL-001 / FAIL-010): {len(BREACHES)}")
    for b in BREACHES:
        print(f"   !!! BREACH {b}")
    print("=" * 100)
    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
    assert config.EXTERNAL_SEND == "OFF"


if __name__ == "__main__":
    main()
