"""M6-P3002 BOUNDARY_FULL_PASS — pack-wide CROSS-SLICE seam harness (READ-ONLY analysis).

The PR/PILOT pack-wide adversarial pass over the integrated M6.2K tree (which carries every slice A..K byte-
identical). Attacks the FOUR named cross-slice seams — evidence tampering, gate bypass, revenue misuse through
slice seams, data-mart triggering across F/J — plus dedup / consent / commission seams. Every claimed breach is
EXECUTED against the real staged code before it is recorded. Nothing is written to the app; no posture flips.

    PYTHONDONTWRITEBYTECODE=1  py -3.12 -B  work/attacks/pack_wide_attacks.py

Classification: DEFENDED / OPEN_NONGATE (armed-not-fired: in-process code-exec-only, trusted-input-only, or not
channel-reachable) / NOTE / BREACH (a fail gate trips from a CHANNEL-reachable path). Target in-scope breaches: 0.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve()
IMPL = None
for anc in HERE.parents:
    cand = anc / "04-artifacts" / "impl" / "M6.2K"
    if (cand / "app").is_dir():
        IMPL = cand
        break
if IMPL is None:
    raise SystemExit("cannot locate 04-artifacts/impl/M6.2K/app")
sys.path.insert(0, str(IMPL))

from datetime import datetime, timezone

from app import config
from app.measurement.masking import mask

from app.measurement.store.measurement_event_store import (
    MeasurementEventStore, MeasurementStoreViolation,
)
from app.measurement.attribution.resolver import AttributionResolver
from app.measurement.attribution.materializer import AttributionMaterializer
from app.measurement.models.measurement_event import AdsMeasurementEvent
from app.measurement.models.conversion_event import ConversionEvent
from app.measurement.models.consumed import ConsentScope, ConsentSnapshot, ConsentState
from app.measurement.consent.gate import ConsentGate
from app.measurement.audit import AuditLog

from app.measurement.dashboard.data_mart import DataMart, ConsumedFacts
from app.measurement.dashboard.kpi_metrics import compute_metrics
from app.measurement.growth.reads import verified_rows
from app.measurement.growth.crm import CrmReorderMeasurement, CrmConsumed
from app.measurement.growth.diamond import DiamondReferralMeasurement, DiamondConsumed
from app.measurement.growth.growth import GrowthReportBuilder, GrowthConsumed

from app.measurement.evidence.pack_assembler import EvidencePackAssembler
from app.measurement.evidence.models import Readiness, GapKind
from app.measurement.evidence.gap_blockers import STANDING_BLOCKER_IDS

FIXED_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
OUTCOMES = []


def record(vec, gate, klass, detail):
    OUTCOMES.append((vec, gate, klass, detail))
    print(f"[{klass:12}] {vec:8} {gate:10} {detail}")


# --- factories --------------------------------------------------------------------------------------
def new_store():
    return MeasurementEventStore()


def insert_event(store, event_id, event_code, idem=None):
    ev = AdsMeasurementEvent(event_id=event_id, event_code=event_code, event_ts=FIXED_TS,
                             idempotency_key=idem or f"idem_{event_id}", correlation_id=f"corr_{event_id}",
                             ingested_at=FIXED_TS)
    store.insert(ev)
    return ev


def materialize(store, ev, *, event_code_conv, revenue, order_code, signals=None):
    """Drive the CTR-023 materializer: revenue is written iff the CONVERSION event_code is ORDER_VERIFIED."""
    mat = AttributionMaterializer(store, AttributionResolver(), AuditLog())
    conv = ConversionEvent(conversion_id=f"conv_{ev.event_id}", event_code=event_code_conv,
                           source_event_id=ev.event_id, correlation_id="corr_c",
                           customer_or_guest_key="guest_mapped_ok", consent_snapshot_id="cs_valid",
                           occurred_at=FIXED_TS, idempotency_key=f"idem2_{ev.event_id}",
                           revenue_value=(float(revenue) if revenue is not None else None),
                           currency="VND", order_code=order_code)
    return mat.materialize(ev, conv, signals=signals)


def snap(state, scopes, subject="subj_a"):
    return ConsentSnapshot("cs_x", subject, ConsentState(state), FIXED_TS,
                           frozenset(ConsentScope(s) for s in scopes))


# ===================================================================================================
# SEAM A — REVENUE MISUSE THROUGH THE E->F->J SEAM (FAIL-001 / RULE-003)
# ===================================================================================================
def seam_A():
    # A1 — the MISPAIR: a QUOTE_SENT measurement event + an ORDER_VERIFIED conversion (w/ revenue+order_code).
    #      The materializer keys 'verified' on the CONVERSION code, and the store only checks the verified flag
    #      (not the event's own code), so revenue lands on the QUOTE row and flows E->F->J.
    store = new_store()
    quote_ev = insert_event(store, "q_mis", "QUOTE_SENT")
    out = materialize(store, quote_ev, event_code_conv="ORDER_VERIFIED", revenue=650000,
                      order_code="ord_mis", signals={"entry_channel": "CRM"})
    row = store.get_by_event_id("q_mis")
    dm = DataMart(store)
    dash_rev = dm.revenue_verified()
    dash_crm = dm.crm_revenue()
    grow_rows = verified_rows(store)
    if (row.revenue_value == 650000.0 and row.event_code == "QUOTE_SENT"
            and dash_rev == 650000.0 and dash_crm == 650000.0 and len(grow_rows) == 1):
        record("A1", "FAIL-001", "OPEN_NONGATE",
               "MISPAIR seam (F-DASH-1/F-GROWTH-3): materialize(QUOTE_SENT event, ORDER_VERIFIED conversion) "
               "stamps 650000 revenue onto a QUOTE_SENT row (materializer keys 'verified' on the CONVERSION code; "
               "the store checks only the verified flag + order_code, never the event's own event_code). It then "
               "flows into DataMart.revenue_verified()=650000 and growth verified_rows. In-process/trusted-input "
               "ONLY — the materializer has NO channel caller pairing arbitrary event+conversion (the conversions "
               "endpoint enqueues to outbox, never materializes). Fix: AND event.event_code=='ORDER_VERIFIED'.")
    else:
        record("A1", "FAIL-001", "NOTE",
               f"mispair result unexpected (rev={row.revenue_value}, dash={dash_rev}, crm={dash_crm})")

    # A2 — the DEFENDED baseline: a QUOTE_SENT event + a QUOTE_SENT (non-verified) conversion -> NO revenue.
    store = new_store()
    q2 = insert_event(store, "q_ok", "QUOTE_SENT")
    materialize(store, q2, event_code_conv="QUOTE_SENT", revenue=500000, order_code="ord_ok")
    row = store.get_by_event_id("q_ok")
    if row.revenue_value is None and DataMart(store).revenue_verified() == 0.0 and len(verified_rows(store)) == 0:
        record("A2", "FAIL-001", "DEFENDED",
               "baseline: a non-verified (QUOTE_SENT) conversion materializes attribution with NO revenue and NO "
               "order_code (RULE-003); dashboard revenue 0, growth verified_rows empty. Quote is never revenue.")
    else:
        record("A2", "FAIL-001", "BREACH", f"a non-verified conversion carried revenue (rev={row.revenue_value})")

    # A3 — the STORE chokes: revenue-bearing Zone-A insert, revenue w/o verified, revenue w/o order_code all raise.
    chokes = 0
    store = new_store()
    try:
        store.insert(AdsMeasurementEvent(event_id="rz", event_code="ORDER_VERIFIED", event_ts=FIXED_TS,
                                         idempotency_key="idem_rz", correlation_id="c", ingested_at=FIXED_TS,
                                         revenue_value=1.0))
    except MeasurementStoreViolation:
        chokes += 1
    insert_event(store, "vv", "ORDER_VERIFIED")
    try:
        store.materialize("vv", attribution_context={}, revenue_value=1.0, order_code="o", verified=False)
    except MeasurementStoreViolation:
        chokes += 1
    try:
        store.materialize("vv", attribution_context={}, revenue_value=1.0, order_code=None, verified=True)
    except MeasurementStoreViolation:
        chokes += 1
    if chokes == 3:
        record("A3", "FAIL-001", "DEFENDED",
               "store guards fire loudly: a revenue-bearing Zone-A insert, revenue without verified, and revenue "
               "without an order_code all raise MeasurementStoreViolation (RULE-003). Revenue cannot enter Zone A.")
    else:
        record("A3", "FAIL-001", "BREACH", f"only {chokes}/3 store revenue guards fired")

    # A4 — set-once immutability across the seam: a differing re-materialize on a verified row raises;
    #      Zone-A update/delete raise -> no in-place revenue rewrite feeds F/J a changed figure.
    store = new_store()
    v = insert_event(store, "sv", "ORDER_VERIFIED")
    materialize(store, v, event_code_conv="ORDER_VERIFIED", revenue=100000, order_code="ord_sv")
    setonce = 0
    try:
        store.materialize("sv", attribution_context={"x": 1}, revenue_value=999999.0, order_code="ord_other",
                          verified=True)
    except MeasurementStoreViolation:
        setonce += 1
    for op in (store.update, store.delete):
        try:
            op("sv")
        except MeasurementStoreViolation:
            setonce += 1
    if setonce == 3 and store.get_by_event_id("sv").revenue_value == 100000.0:
        record("A4", "FAIL-001", "DEFENDED",
               "set-once verified revenue: a differing re-materialize + Zone-A update/delete all raise; the stored "
               "100000 is immutable. The figure F/J read cannot be rewritten in place (RULE-008).")
    else:
        record("A4", "FAIL-001", "BREACH", f"set-once/immutability guards incomplete ({setonce}/3)")


# ===================================================================================================
# SEAM B — DATA-MART TRIGGERING ACROSS F/J (RULE-012 / FAIL-005)
# ===================================================================================================
def seam_B():
    store = new_store()
    dm = DataMart(store)

    # B1 — the DataMart exposes NO trigger/send/scale/write verb (support view only), across F and J reuse.
    trigger_verbs = ("trigger", "send", "sync", "crm_send", "scale", "set_price", "publish", "commission",
                     "order_state", "write", "insert", "update", "delete", "enqueue", "dispatch")
    dm_hits = [v for v in trigger_verbs if hasattr(dm, v)]
    if not dm_hits:
        record("B1", "FAIL-005", "DEFENDED",
               "DataMart exposes only read/aggregate methods; no trigger/send/scale/write verb (RULE-012). It "
               "cannot become a trigger owner in F or when reused by the J GrowthReportBuilder.")
    else:
        record("B1", "FAIL-005", "BREACH", f"DataMart exposes a trigger verb: {dm_hits}")

    # B2 — building the growth report over the shared store is side-effect-free (no store mutation, no trigger).
    store = new_store()
    v = insert_event(store, "gb", "ORDER_VERIFIED")
    materialize(store, v, event_code_conv="ORDER_VERIFIED", revenue=200000, order_code="ord_gb",
                signals={"entry_channel": "CRM"})
    builder = GrowthReportBuilder(DataMart(store), CrmReorderMeasurement(store, ConsentGate(AuditLog()), None),
                                  DiamondReferralMeasurement(store, None), None,
                                  measurement_store=store, consumed=GrowthConsumed())
    before = len(store)
    r1 = builder.build()
    r2 = builder.build()
    after = len(store)
    is_dict = isinstance(r1, dict) or hasattr(r1, "to_public")
    if before == after and is_dict:
        record("B2", "FAIL-005", "DEFENDED",
               "GrowthReportBuilder.build() over the shared store is a read-only assembly: building twice does not "
               "mutate the store and returns a data report (no trigger handle).")
    else:
        record("B2", "FAIL-005", "BREACH", f"growth build mutated the store ({before}->{after})")

    # B3 — F-GROWTH-2: the UNGATED DataMart.crm_revenue twin vs the GATED growth crm_revenue on an OPT-OUT row.
    #      The dashboard (support-view) number includes opt-out CRM revenue; the Finance-facing growth number
    #      excludes it. This is a display-vs-Finance consistency gap, NOT a send (no FAIL-002/005 trip).
    store = new_store()
    v = insert_event(store, "co", "ORDER_VERIFIED")
    materialize(store, v, event_code_conv="ORDER_VERIFIED", revenue=300000, order_code="ord_co",
                signals={"entry_channel": "CRM"})
    dash_crm = DataMart(store).crm_revenue()                      # ungated
    optout = ConsentSnapshot("cs_o", "subj", ConsentState.OPT_OUT, FIXED_TS, frozenset())
    consumed = CrmConsumed(crm_eligible_orders={"ord_co": True}, suppression_pass_orders={"ord_co": True},
                           consent_by_order={"ord_co": optout})
    grow_crm = CrmReorderMeasurement(store, ConsentGate(AuditLog()), consumed).crm_revenue()  # gated
    if dash_crm == 300000.0 and grow_crm == 0.0:
        record("B3", "FAIL-002", "OPEN_NONGATE",
               "F-GROWTH-2: DataMart.crm_revenue() (dashboard support view) is UNGATED and counts 300000 for a "
               "CRM-attributed opt-out row, while the Finance-facing growth CrmReorderMeasurement.crm_revenue() is "
               "consent+eligibility+suppression GATED and returns 0. The DataMart is read-only (no send), so this "
               "is a display-vs-Finance consistency gap, not a FAIL-002 send / FAIL-005 trigger. Route: CODER "
               "(name/gate the dashboard CRM twin consistently).")
    else:
        record("B3", "FAIL-002", "NOTE", f"crm twin behaviour unexpected (dash={dash_crm}, grow={grow_crm})")


# ===================================================================================================
# SEAM C — CONSENT ACROSS SLICE SEAMS (FAIL-002 / RULE-002)
# ===================================================================================================
def seam_C():
    # C1 — opt-out / expired / missing consent fail-closed excluded from the Finance-facing growth CRM revenue.
    store = new_store()
    v = insert_event(store, "cc", "ORDER_VERIFIED")
    materialize(store, v, event_code_conv="ORDER_VERIFIED", revenue=400000, order_code="ord_cc",
                signals={"entry_channel": "CRM"})
    gate = ConsentGate(AuditLog())
    bad = 0
    for state in ("OPT_OUT", "EXPIRED", "MISSING"):
        cons = CrmConsumed(crm_eligible_orders={"ord_cc": True}, suppression_pass_orders={"ord_cc": True},
                           consent_by_order={"ord_cc": ConsentSnapshot("c", "s", ConsentState(state), FIXED_TS,
                                                                       frozenset())})
        if CrmReorderMeasurement(store, gate, cons).crm_revenue() == 0.0:
            bad += 1
    # and no consumed facts at all
    if CrmReorderMeasurement(store, gate, None).crm_revenue() == 0.0 and bad == 3:
        record("C1", "FAIL-002", "DEFENDED",
               "growth CRM revenue is fail-closed 0 for opt-out / expired / missing consent AND with no consumed "
               "facts (consent+eligibility+suppression gate, SMK-008). Consent holds across the E->J seam.")
    else:
        record("C1", "FAIL-002", "BREACH", f"consent leak in growth CRM revenue (bad={bad})")

    # C2 — F-GROWTH-1: borrowed consent — the CRM gate evaluates a consent snapshot keyed by order_code but never
    #      binds snapshot.subject_ref to the row's buyer, so subject_B's VALID CRM consent authorizes the buyer's
    #      CRM revenue. Trusted-input only (consent_by_order is a consumed Consent/CRM map, not channel input).
    store = new_store()
    v = insert_event(store, "cb", "ORDER_VERIFIED")
    materialize(store, v, event_code_conv="ORDER_VERIFIED", revenue=650000, order_code="ord_cb",
                signals={"entry_channel": "CRM"})
    other = ConsentSnapshot("cs_b", "subject_B_totally_different", ConsentState.VALID, FIXED_TS,
                            frozenset({ConsentScope.CRM}))
    consumed = CrmConsumed(crm_eligible_orders={"ord_cb": True}, suppression_pass_orders={"ord_cb": True},
                           consent_by_order={"ord_cb": other})
    rev = CrmReorderMeasurement(store, ConsentGate(AuditLog()), consumed).crm_revenue()
    if rev == 650000.0:
        record("C2", "FAIL-002", "OPEN_NONGATE",
               "F-GROWTH-1: the CRM growth gate counts 650000 using subject_B's VALID CRM consent for the buyer's "
               "order — snapshot.subject_ref is never bound to the row's buyer. Trusted-input only: consent_by_order "
               "is a consumed Consent/CRM map, not channel input; the M6.2E conversions seam already enforces this "
               "bind. Route: CODER (mirror the M6.2E F-D subject bind). Disclosed standing blocker.")
    else:
        record("C2", "FAIL-002", "DEFENDED", f"borrowed consent did not count (rev={rev}) — bind already present")


# ===================================================================================================
# SEAM D — EVIDENCE TAMPERING + GATE BYPASS (FAIL-007 / RULE-015) — pack-wide integrity
# ===================================================================================================
def seam_D():
    a = EvidencePackAssembler()

    # D1 — the evidence pack is fail-closed and cannot be forged to a Pass (no Pass/Ready enum member).
    members = {m.value for m in Readiness}
    empty = a.assemble()
    if members == {"OWNER_REVIEW_REQUIRED", "NOT_READY"} and empty.readiness is Readiness.NOT_READY:
        record("D1", "FAIL-007", "DEFENDED",
               "the M6.2K evidence pack has no Pass/Ready readiness member and an empty pack is NOT_READY; the "
               "evidence-tampering surface cannot forge a Pass verdict (fail-closed, RULE-015).")
    else:
        record("D1", "FAIL-007", "BREACH", f"pack readiness surface not fail-closed ({members})")

    # D2 — the pack ALWAYS discloses the 8 standing blockers (incl. the two BLOCKED override verdicts) — gate
    #      state is carried honestly, never silently converted.
    complete_refs = {c: {k: "ev" for k in ks} for c, ks in __import__(
        "app.measurement.evidence.categories", fromlist=["CATEGORY_MANDATORY"]).CATEGORY_MANDATORY.items()}
    from app.measurement.evidence.models import SmokeResult
    from app.measurement.evidence.smoke_registry import SMOKE_IDS
    smokes = {s: SmokeResult(s, status="PASS", correlation_id="c", evidence_id="e") for s in SMOKE_IDS}
    pack = a.assemble(smokes, complete_refs)
    standing = {g.id for g in pack.gap_blockers if g.kind is GapKind.STANDING_BLOCKER}
    overrides_carried = {"M6-P1000", "M6-P1309"} <= standing
    if standing == set(STANDING_BLOCKER_IDS) and overrides_carried and pack.readiness is Readiness.OWNER_REVIEW_REQUIRED:
        record("D2", "FAIL-007", "DEFENDED",
               "even a fully-complete pack (OWNER_REVIEW_REQUIRED) discloses all 8 standing blockers incl. the "
               "M6-P1000/M6-P1309 BLOCKED override verdicts — no gate is silently converted or bypassed.")
    else:
        record("D2", "FAIL-007", "BREACH", f"standing/override disclosure incomplete ({sorted(standing)})")

    # D3 — no code path in the integrated tree flips a governance flag; the enabling flags read False, and the
    #      external-send choke is hard-closed.
    flags_off = (config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
                 and config.EXTERNAL_SEND == "OFF" and config.SCALE_EXECUTION_ENABLED is False
                 and config.LEARNING_AUTOPUBLISH_ENABLED is False and config.HASH_POLICY_RATIFIED is False
                 and config.SCALE_MODEL_RATIFIED is False and config.is_external_send_enabled() is False)
    if flags_off:
        record("D3", "FAIL-006", "DEFENDED",
               "governance flags immutable/OFF (gateway BLOCKED, production OFF, external_send OFF, scale/learning/"
               "hash all False); is_external_send_enabled() hard-returns False. No self-advance path enables scale/"
               "publish/send across the pack.")
    else:
        record("D3", "FAIL-006", "BREACH", "a governance flag is in an enabling state")


# ===================================================================================================
# SEAM E — DEDUP ACROSS INGEST->GROWTH (FAIL-003 / RULE-005) + the F-DASH-3 order_code double-count
# ===================================================================================================
def seam_E():
    # E1 — a duplicate idempotency_key insert returns the existing row (created=False) — no second row, no double
    #      count downstream (SMK-003 seam).
    store = new_store()
    insert_event(store, "d1", "ORDER_VERIFIED", idem="same_key")
    r = store.insert(AdsMeasurementEvent(event_id="d2", event_code="ORDER_VERIFIED", event_ts=FIXED_TS,
                                         idempotency_key="same_key", correlation_id="c", ingested_at=FIXED_TS))
    if r.created is False and len(store) == 1:
        record("E1", "FAIL-003", "DEFENDED",
               "duplicate idempotency_key insert returns the existing row (created=False); one measurement row, no "
               "double count across the ingest->growth chain (RULE-005 / SMK-003).")
    else:
        record("E1", "FAIL-003", "BREACH", f"dedup failed (created={r.created}, len={len(store)})")

    # E2 — F-DASH-3: two verified rows sharing an order_code double-count revenue_verified (per-row sum) while
    #      verified_order_count dedups by order_code. Trusted-input/data-quality, not channel-reachable.
    store = new_store()
    for i in (1, 2):
        v = insert_event(store, f"o{i}", "ORDER_VERIFIED")
        materialize(store, v, event_code_conv="ORDER_VERIFIED", revenue=100000, order_code="ord_shared")
    dm = DataMart(store)
    if dm.revenue_verified() == 200000.0 and dm.verified_order_count() == 1:
        record("E2", "FAIL-001", "OPEN_NONGATE",
               "F-DASH-3: two verified rows sharing order_code 'ord_shared' -> revenue_verified sums per-row "
               "(200000) while verified_order_count dedups by order_code (1), double-counting Revenue Verified + "
               "AOV. Trusted-input/data-quality, not channel-reachable; does not trip FAIL-001 from a channel. "
               "Route: CODER (dedup revenue by order_code). Disclosed dashboard residual.")
    else:
        record("E2", "FAIL-001", "DEFENDED",
               f"order_code double-count not reproduced (rev={dm.revenue_verified()}, n={dm.verified_order_count()})")


# ===================================================================================================
# SEAM F — DIAMOND COMMISSION + KPI REVENUE HONESTY (FAIL-004 / RULE-019)
# ===================================================================================================
def seam_F():
    # F1 — no commission amount/rate/payout method anywhere on the Diamond path across the integrated tree.
    d = DiamondReferralMeasurement(new_store(), None)
    meths = [v for v in dir(d) if not v.startswith("__") and callable(getattr(d, v))]
    comm = [v for v in meths if "commission" in v.lower() and v != "commission_ready_revenue"]
    payout = [v for v in meths if any(t in v.lower() for t in ("payout", "commission_amount", "commission_rate"))]
    if not comm and not payout:
        record("F1", "FAIL-004", "DEFENDED",
               "Diamond exposes no commission amount/rate/payout method (only commission_ready_revenue, a "
               "fail-closed verified-revenue subset). Finance owns commission (RULE-019 / SMK-014).")
    else:
        record("F1", "FAIL-004", "BREACH", f"Diamond exposes a commission-computing method: {comm + payout}")

    # F2 — the 14 dashboard KPIs source revenue ONLY from verified Zone-B rows; a quote-only store yields 0
    #      revenue / None ROAS (no fabricated revenue).
    store = new_store()
    insert_event(store, "qz", "QUOTE_SENT")
    mets = {m.name: m.value for m in compute_metrics(DataMart(store, ConsumedFacts()))}
    if mets["Revenue Verified"] == 0.0 and mets["ROAS"] is None and mets["CRM Revenue"] == 0.0:
        record("F2", "FAIL-001", "DEFENDED",
               "compute_metrics over a quote-only store: Revenue Verified 0, ROAS None (fail-closed division), CRM "
               "Revenue 0 — no revenue fabricated from a non-verified funnel (RULE-003).")
    else:
        record("F2", "FAIL-001", "BREACH", f"KPIs fabricated revenue from a quote-only store: {mets}")


# ===================================================================================================
# SEAM N — reconciliation of the cross-slice ideation workflow's NOVEL seams (executed)
# ===================================================================================================
def seam_N():
    from app.measurement.models.measurement_event import DataQualityStatus
    from app.measurement.funnel.funnel import GoldenHourFunnel
    from app.measurement.growth.reactivation import ReactivationMeasurement, ReactivationConsumed
    from app.measurement.learning.review_queue import ReviewQueue
    from app.measurement.learning.candidate import (
        AdsLearningCandidate, LearningCandidateKind, TargetDim, ReviewState,
    )
    from app.measurement.adapters.segment_reader import InMemorySegmentReader
    from app.measurement.models.segments import ApprovalState, CustomerSegment, SegmentMember
    from app.measurement.evidence.models import SmokeResult
    from app.measurement.evidence.smoke_registry import SMOKE_IDS
    from app.measurement.evidence.categories import CATEGORY_MANDATORY

    # N1 (CRIT-DIVERGE-01) — ONE store, THREE verified-revenue predicates: the M6.2I funnel already ANDs
    #     event_code==ORDER_VERIFIED (self-enforcing, returns 0 for the mispair) while F and J key on revenue
    #     presence alone. The correct fix ALREADY ships in-repo (the funnel) — F/J just diverge from it.
    store = new_store()
    q = insert_event(store, "dv", "QUOTE_SENT")
    materialize(store, q, event_code_conv="ORDER_VERIFIED", revenue=500000, order_code="ord_dv")
    funnel_rev = sum(v.verified_revenue for v in GoldenHourFunnel(store).assemble())
    f_rev = DataMart(store).revenue_verified()
    j_rows = verified_rows(store)
    if funnel_rev == 0.0 and f_rev == 500000.0 and len(j_rows) == 1:
        record("N1", "FAIL-001", "OPEN_NONGATE",
               "predicate divergence (F-DASH-1/F-GROWTH-3, sharpened): on the mispaired store the M6.2I funnel "
               "_verified_revenue returns 0 (it ANDs event_code==ORDER_VERIFIED with revenue — the shipped "
               "self-enforcing choke), while F DataMart.revenue_verified()=500000 and J verified_rows count it. "
               "One store, three answers; the fix is to bring F/J to the funnel's already-shipped predicate. "
               "In-process only (materializer unwired). Route: CODER.")
    else:
        record("N1", "FAIL-001", "NOTE", f"divergence unexpected (I={funnel_rev}, F={f_rev}, J={len(j_rows)})")

    # N2 (NS-06) — order_code fan-out: ONE consumed CRM-eligibility decision keyed by order_code authorizes N
    #     verified rows sharing that order_code (distinct from F-DASH-3's revenue sum — this multiplies a CRM/
    #     Finance/Commerce fact across rows).
    store = new_store()
    for i in (1, 2):
        v = insert_event(store, f"fo{i}", "ORDER_VERIFIED")
        materialize(store, v, event_code_conv="ORDER_VERIFIED", revenue=100000, order_code="ORD1",
                    signals={"entry_channel": "CRM"})
    consumed = CrmConsumed(crm_eligible_orders={"ORD1": True}, suppression_pass_orders={"ORD1": True},
                           consent_by_order={"ORD1": ConsentSnapshot("c", "s", ConsentState.VALID, FIXED_TS,
                                                                     frozenset({ConsentScope.CRM}))})
    crm = CrmReorderMeasurement(store, ConsentGate(AuditLog()), consumed)
    rows = crm.crm_revenue_rows()
    if len(rows) == 2 and crm.crm_revenue() == 200000.0:
        record("N2", "FAIL-002", "OPEN_NONGATE",
               "order_code fan-out (NS-06): ONE consumed CRM decision for order_code 'ORD1' (eligible+suppression+"
               "consent) authorizes BOTH verified rows sharing it -> crm_revenue counts 200000 from a single "
               "per-order fact. Every growth/dashboard/funnel consumed map is order_code-keyed, so one Finance/CRM/"
               "Commerce decision multiplies across duplicate-order_code rows. Trusted-input + in-process order_code "
               "collision; not channel-reachable. Route: CODER (bind a per-order fact to one row / dedup by order).")
    else:
        record("N2", "FAIL-002", "NOTE", f"fan-out unexpected (rows={len(rows)}, rev={crm.crm_revenue()})")

    # N3 (EV-T-03) — a RECORDED smoke with status='FAIL' does NOT drop pack readiness (recorded != passed):
    #     readiness only tests s.recorded (run+evidenced), never the pass/fail of the status.
    a = EvidencePackAssembler()
    refs = {c: {k: "ev" for k in ks} for c, ks in CATEGORY_MANDATORY.items()}
    all_fail = {s: SmokeResult(s, status="FAIL", correlation_id="c", evidence_id="e") for s in SMOKE_IDS}
    pack = a.assemble(all_fail, refs)
    if pack.readiness is Readiness.OWNER_REVIEW_REQUIRED and all(s.recorded for s in pack.smokes):
        record("N3", "FAIL-007", "OPEN_NONGATE",
               "recorded != passed (EV-T-03): a pack where all 18 P0 smokes are RECORDED with status='FAIL' still "
               "reaches OWNER_REVIEW_REQUIRED — _readiness tests only s.recorded (run+evidenced), never whether the "
               "status is PASS. The FAIL status IS surfaced in the smoke list for the owner, but a failing P0 matrix "
               "presents as review-ready. Trusted-input only (TESTER records PASS); caps at OWNER_REVIEW_REQUIRED, "
               "never a Pass. Route: CODER (drop readiness to NOT_READY on any recorded FAIL/HOLD). New evidence "
               "residual F-EVID-5.")
    else:
        record("N3", "FAIL-007", "DEFENDED", "recorded FAIL smoke dropped readiness (already gated).")

    # N4 (CRIT-DQ-J-01) — a DQ-FAIL verified row still BANKS its revenue in F/J while the SAME growth report
    #     flags it as a drift violation (the verified-revenue predicate ignores data_quality_status).
    store = new_store()
    v = insert_event(store, "dq", "ORDER_VERIFIED")
    materialize(store, v, event_code_conv="ORDER_VERIFIED", revenue=300000, order_code="ord_dq",
                signals={"entry_channel": "CRM"})
    store.set_data_quality_status("dq", DataQualityStatus.FAIL, actor="dq_worker", reason="drift")
    dash_rev = DataMart(store).revenue_verified()
    builder = GrowthReportBuilder(DataMart(store), CrmReorderMeasurement(store, ConsentGate(AuditLog()), None),
                                  DiamondReferralMeasurement(store, None), None,
                                  measurement_store=store, consumed=GrowthConsumed())
    kpis = {k.name: k.value for k in builder.build().kpis}
    if dash_rev == 300000.0 and kpis.get("drift violations") == 1.0:
        record("N4", "FAIL-001", "OPEN_NONGATE",
               "quality-signal dropped across the F->J revenue seam (CRIT-DQ-J-01): a verified row marked "
               "data_quality_status=FAIL still banks 300000 in DataMart.revenue_verified() (verified_rows filters "
               "only on revenue presence, never DQ status), while the SAME growth report flags 'drift violations'=1 "
               "-- one artifact both flags the row as failed and counts its revenue. RULE-009 bars HOLD/FAIL only as "
               "SCALE evidence (the report is not scale evidence), so no gate trips; in-process (DQ worker + "
               "materializer unwired). Route: CODER (gate verified_rows on DQ status, or reconcile the report).")
    else:
        record("N4", "FAIL-001", "NOTE", f"DQ-fail revenue path unexpected (rev={dash_rev}, drift={kpis.get('drift violations')})")

    # N5 (CRIT-LEARN-J-01) — H->J compose: the learning review_state (set by the admin endpoint, whose authN is
    #     the OPEN M6-OD-011) drives the J growth report's 'Candidate approval rate' KPI. Executed J-side; the KPI
    #     is display-only -- is_publish_authorized stays False (M6-OD-006 OPEN), so NOTHING publishes/scales/sends.
    queue = ReviewQueue()
    queue.enqueue(AdsLearningCandidate("lc_ok", LearningCandidateKind.OPTIMIZATION, TargetDim.PERSONA, 0.8,
                                       "SKU_1", review_state=ReviewState.APPROVED))
    queue.enqueue(AdsLearningCandidate("lc_pend", LearningCandidateKind.OPTIMIZATION, TargetDim.PERSONA, 0.5,
                                       "SKU_2", review_state=ReviewState.CANDIDATE))
    store = new_store()
    builder = GrowthReportBuilder(DataMart(store), CrmReorderMeasurement(store, ConsentGate(AuditLog()), None),
                                  DiamondReferralMeasurement(store, None), None,
                                  review_queue=queue, measurement_store=store, consumed=GrowthConsumed())
    kpis = {k.name: k.value for k in builder.build().kpis}
    approved = queue.get("lc_ok")
    if kpis.get("Candidate approval rate") == 0.5 and approved.is_publish_authorized is False:
        record("N5", "FAIL-006", "OPEN_NONGATE",
               "H->J compose (CRIT-LEARN-J-01): an APPROVED learning review_state drives the J growth report's "
               "'Candidate approval rate' KPI (=0.5 here). The learning-review admin endpoint's authN is the OPEN "
               "M6-OD-011 (a disclosed standing blocker), so this is channel-reachable ACCEPTANCE — an "
               "unauthenticated approve moves a J KPI. BUT armed-not-fired: the KPI is display-only; "
               "is_publish_authorized stays False (M6-OD-006 OPEN) so nothing publishes/scales/sends -> no gate "
               "trips. Closed by the M6-OD-011 admin-authN owner decision before any surface.")
    else:
        record("N5", "FAIL-006", "NOTE",
               f"learning->growth KPI unexpected (rate={kpis.get('Candidate approval rate')}, "
               f"publish={approved.is_publish_authorized})")

    # N6 (CRIT-REACT-02) — reactivation borrowed consent: _member_eligible evaluates the member's
    #     consent_snapshot_id but never binds snapshot.subject_ref == member.member_key, so a member carrying
    #     another subject's VALID CRM consent is reactivation-eligible (the F-GROWTH-1 class on the J reactivation
    #     surface, previously unexamined).
    seg_id = "seg_dormant"
    members = [SegmentMember(seg_id, "member_A", "cs_borrowed")]
    reader = InMemorySegmentReader(segments={seg_id: CustomerSegment(seg_id, "Dormant", ApprovalState.APPROVED)},
                                   members={seg_id: members})

    class _CMap:
        def get(self, sid):
            # the snapshot's subject is a DIFFERENT person, not member_A
            return ConsentSnapshot(sid, "subject_B_not_member_A", ConsentState.VALID, FIXED_TS,
                                   frozenset({ConsentScope.CRM})) if sid == "cs_borrowed" else None
    consumed = ReactivationConsumed(crm_eligible_members={"member_A": True},
                                    reactivated_member_keys=frozenset({"member_A"}), reactivation_spend=1000.0)
    react = ReactivationMeasurement(reader, _CMap(), ConsentGate(AuditLog()), consumed)
    elig = react.eligible_members(seg_id)
    if len(elig) == 1:
        record("N6", "FAIL-002", "OPEN_NONGATE",
               "reactivation borrowed consent (CRIT-REACT-02): member_A is reactivation-ELIGIBLE using subject_B's "
               "VALID CRM consent -- _member_eligible never binds snapshot.subject_ref==member.member_key (the "
               "F-GROWTH-1 class on the J reactivation surface the per-slice review did not examine). Trusted-input "
               "only (segment members + consent map are CRM/Member-owned, not channel); measure-only (no CRM send). "
               "Route: CODER (mirror the audience-sync subject bind). Same owner routing as F-GROWTH-1.")
    else:
        record("N6", "FAIL-002", "DEFENDED", f"reactivation bound subject (elig={len(elig)}) -- bind already present")


# ===================================================================================================
def main():
    print("=" * 100)
    print("M6-P3002 BOUNDARY_FULL_PASS — pack-wide CROSS-SLICE seam attacks over the integrated M6.2K tree")
    print(f"impl root: {IMPL}")
    print("=" * 100)
    for s in (seam_A, seam_B, seam_C, seam_D, seam_E, seam_F, seam_N):
        print(f"\n----- {s.__name__} -----")
        s()

    print("\n" + "=" * 100)
    tally = {}
    for _, _, k, _ in OUTCOMES:
        tally[k] = tally.get(k, 0) + 1
    breaches = [o for o in OUTCOMES if o[2] == "BREACH"]
    # a "channel-reachable breach" is the only thing that trips a gate for this pass; OPEN_NONGATE are armed-not-fired
    print(f"SUMMARY: {tally}")
    print(f"TOTAL RECORDED OUTCOMES: {len(OUTCOMES)}")
    print(f"CHANNEL-REACHABLE FAIL-GATE BREACHES: {len(breaches)}")
    if breaches:
        for o in breaches:
            print("   BREACH:", o)

    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
    assert config.EXTERNAL_SEND == "OFF"
    assert {m.value for m in Readiness} == {"OWNER_REVIEW_REQUIRED", "NOT_READY"}
    print("POSTURE AFTER RUN: BLOCKED / OFF / OFF (unchanged); Readiness has no Pass/Ready member")
    print("=" * 100)


if __name__ == "__main__":
    main()
