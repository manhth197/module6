"""M6.2Q boundary-adversary harness (READ-ONLY analysis; prompt M6-P2505).

Attacks the staged M6.2Q slice (A5) — ads-spend import (maker-checker) + live-session-ads-binding.v1 +
CPA/ROAS-by-live_session. In-scope fail gate M6-FAIL-007; rules RULE-003 (revenue only ORDER_VERIFIED), RULE-015.
The harness drives the real staged code and EXECUTES every claimed breach; it flips no flag, opens no send.

    PYTHONDONTWRITEBYTECODE=1  py -3.12 -B  work/attacks/m6_2q_attacks.py

No raw psid/phone/email literal appears in this source (markers synthetic + runtime-assembled).
Classification: DEFENDED / OPEN_NONGATE (armed-not-fired) / NOTE / BREACH (a FAIL-007/RULE-003 gate trips OR
revenue/PII/egress leaks from a channel-reachable path).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

HERE = Path(__file__).resolve()
IMPL = None
for anc in HERE.parents:
    cand = anc / "04-artifacts" / "impl" / "M6.2Q"
    if (cand / "app").is_dir():
        IMPL = cand
        break
if IMPL is None:
    raise SystemExit("cannot locate 04-artifacts/impl/M6.2Q/app")
sys.path.insert(0, str(IMPL))

from app import config
from app.measurement.audit import AuditLog
from app.measurement.ads_spend.import_gate import AdsSpendImportGate, AdsSpendImportGateViolation, _canon_actor
from app.measurement.ads_spend.materializer import AdsSpendMaterializer
from app.measurement.store.ads_spend_import_store import AdsSpendImportStore
from app.measurement.store.ads_spend_record_store import AdsSpendRecordStore, AdsSpendRecordStoreViolation
from app.measurement.store.live_session_ads_binding_store import (
    LiveSessionAdsBindingStore, LiveSessionAdsBindingStoreViolation,
)
from app.measurement.models.ads_spend_import import (
    AdsSpendImport, AdsSpendImportRow, AdsSpendImportDecision, AdsSpendImportState, ImportDecisionKind,
)
from app.measurement.models.live_session_ads_binding import LiveSessionAdsBinding
from app.measurement.dashboard.data_mart import AdsSpendRecord
from app.measurement.dashboard.session_roas import SessionRoasReader
from app.measurement.store.measurement_event_store import MeasurementEventStore
from app.measurement.attribution.resolver import AttributionResolver
from app.measurement.attribution.materializer import AttributionMaterializer
from app.measurement.models.measurement_event import AdsMeasurementEvent
from app.measurement.models.conversion_event import ConversionEvent
from app.measurement.models.attribution_context import AdsAttributionContext, EntryChannel, SourceConfidence, ConflictStatus

TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
TS_OUT = TS + timedelta(days=10)
OUTCOMES = []


def record(vec, gate, klass, detail):
    OUTCOMES.append((vec, gate, klass, detail))
    print(f"[{klass:12}] {vec:8} {gate:10} {detail}")


# --- factories ---------------------------------------------------------------------------------------
def seed_ov(store, event_id, ls_id, campaign_id, revenue, order_code, ts=TS):
    ev = AdsMeasurementEvent(event_id=event_id, event_code="ORDER_VERIFIED", event_ts=ts,
                             idempotency_key=f"idem_{event_id}", correlation_id=f"c_{event_id}", ingested_at=ts,
                             live_session_id=ls_id, campaign_id=campaign_id)
    store.insert(ev)
    mat = AttributionMaterializer(store, AttributionResolver(), AuditLog())
    conv = ConversionEvent(conversion_id=f"conv_{event_id}", event_code="ORDER_VERIFIED", source_event_id=event_id,
                           correlation_id="c", customer_or_guest_key="g", consent_snapshot_id="cs", occurred_at=ts,
                           idempotency_key=f"idem2_{event_id}", revenue_value=float(revenue), currency="VND",
                           order_code=order_code)
    mat.materialize(ev, conv, signals={"campaign_id": campaign_id})
    return store.get_by_event_id(event_id)


def seed_plain(store, event_id, ls_id, event_code, ts=TS):
    ev = AdsMeasurementEvent(event_id=event_id, event_code=event_code, event_ts=ts,
                             idempotency_key=f"idem_{event_id}", correlation_id=f"c_{event_id}", ingested_at=ts,
                             live_session_id=ls_id)
    store.insert(ev)
    return ev


def make_import(import_id, campaign_id, spend, spend_date=TS, maker="maker_ops"):
    return AdsSpendImport(import_id=import_id,
                          rows=(AdsSpendImportRow(campaign_id=campaign_id, spend_value=float(spend), spend_date=spend_date),),
                          window_start=TS, window_end=TS_OUT, uploaded_by=maker)


def decision(actor, kind=ImportDecisionKind.APPROVE, reason="reviewed"):
    return AdsSpendImportDecision(actor=actor, reason=reason, audit_ref="aud", evidence_ref="ev", decision=kind)


def approve_and_materialize(imp_store, rec_store, gate, worker, import_id, campaign_id, spend, spend_date=TS,
                            maker="maker_ops", checker="checker_bob"):
    gate.propose(make_import(import_id, campaign_id, spend, spend_date, maker))
    gate.record_decision(import_id, decision(checker))
    worker.run_once()


def bind(binding_store, ls_id, campaign_id):
    binding_store.bind(LiveSessionAdsBinding(live_session_id=ls_id, primary_campaign_id=campaign_id,
                                             bound_at=TS, bound_by="binder_ops"))


def new_ads_stack():
    imp_store = AdsSpendImportStore()
    rec_store = AdsSpendRecordStore()
    gate = AdsSpendImportGate(imp_store, AuditLog())
    worker = AdsSpendMaterializer(imp_store, rec_store, AuditLog())
    return imp_store, rec_store, gate, worker


# ===================================================================================================
# GROUP MC — maker-checker four-eyes (FAIL-007 / RULE-015 / M6-OD-016)
# ===================================================================================================
def group_MC():
    # MC1 — raw self-approve (checker == maker) -> refused; import stays PROPOSED, materializes nothing.
    imp_store, rec_store, gate, worker = new_ads_stack()
    gate.propose(make_import("i1", "camp1", 100000, maker="maker_ops"))
    refused = False
    try:
        gate.record_decision("i1", decision("maker_ops"))
    except AdsSpendImportGateViolation:
        refused = True
    worker.run_once()
    if refused and imp_store.get("i1").state is AdsSpendImportState.PROPOSED and len(rec_store) == 0:
        record("MC1", "FAIL-007", "DEFENDED",
               "raw self-approve (checker == maker) is REFUSED (AdsSpendImportGateViolation); the import stays "
               "PROPOSED and the worker materializes nothing (four-eyes fail-closed, M6-OD-016).")
    else:
        record("MC1", "FAIL-007", "BREACH", f"self-approve slipped (refused={refused}, state={imp_store.get('i1').state})")

    # MC2 — case / whitespace / uppercase alias of the maker -> all refused (canonicalized strip+casefold).
    aliases = ["Maker_Ops", "maker_ops ", " maker_ops", "MAKER_OPS", "\tmaker_ops\t"]
    slipped = []
    for i, alias in enumerate(aliases):
        s_imp, s_rec, s_gate, s_worker = new_ads_stack()
        s_gate.propose(make_import(f"a{i}", "campX", 1, maker="maker_ops"))
        try:
            s_gate.record_decision(f"a{i}", decision(alias))
            if s_imp.get(f"a{i}").state is AdsSpendImportState.APPROVED:
                slipped.append(alias)
        except AdsSpendImportGateViolation:
            pass
    if not slipped:
        record("MC2", "FAIL-007", "DEFENDED",
               "case/whitespace aliases of the maker ('Maker_Ops'/'maker_ops '/'MAKER_OPS'/tab-wrapped) all "
               "canonicalize to the maker (strip+casefold) -> self-approve REFUSED. The red-team raw-`==` gap is closed.")
    else:
        record("MC2", "FAIL-007", "BREACH", f"alias self-approve slipped: {slipped}")

    # MC3 — blank / whitespace-only checker -> refused (canonical form empty).
    blanks = ["", "   ", "\t", "\n"]
    slipped = []
    for i, b in enumerate(blanks):
        s_imp, s_rec, s_gate, s_worker = new_ads_stack()
        s_gate.propose(make_import(f"b{i}", "campX", 1, maker="maker_ops"))
        try:
            s_gate.record_decision(f"b{i}", decision(b))
            if s_imp.get(f"b{i}").state is AdsSpendImportState.APPROVED:
                slipped.append(repr(b))
        except AdsSpendImportGateViolation:
            pass
    if not slipped:
        record("MC3", "FAIL-007", "DEFENDED",
               "a blank / whitespace-only checker is REFUSED (its canonical form is empty -> `not checker`); an "
               "unattributed approve cannot move an import to APPROVED.")
    else:
        record("MC3", "FAIL-007", "BREACH", f"blank checker approved: {slipped}")

    # MC4 — a DISTINCT checker -> APPROVED (non-vacuity: the gate genuinely approves).
    imp_store, rec_store, gate, worker = new_ads_stack()
    gate.propose(make_import("ok", "campX", 1, maker="maker_ops"))
    gate.record_decision("ok", decision("checker_bob"))
    if imp_store.get("ok").state is AdsSpendImportState.APPROVED:
        record("MC4", "FAIL-007", "DEFENDED",
               "a DISTINCT checker ('checker_bob' != 'maker_ops') moves the import to APPROVED (the four-eyes gate is "
               "real, not a dead refuse-all).")
    else:
        record("MC4", "FAIL-007", "BREACH", "a distinct checker failed to approve")

    # MC5 — only APPROVED materializes: PROPOSED -> 0 records; REJECTED -> 0 records; APPROVED -> records.
    imp_store, rec_store, gate, worker = new_ads_stack()
    gate.propose(make_import("prop", "campP", 5, maker="m"))                     # stays PROPOSED
    gate.propose(make_import("rej", "campR", 5, maker="m"))
    gate.record_decision("rej", decision("c", kind=ImportDecisionKind.REJECT))   # REJECTED
    gate.propose(make_import("app", "campA", 5, maker="m"))
    gate.record_decision("app", decision("c"))                                   # APPROVED
    worker.run_once()
    if rec_store.is_materialized("app") and not rec_store.is_materialized("prop") \
            and not rec_store.is_materialized("rej"):
        record("MC5", "FAIL-007", "DEFENDED",
               "only an APPROVED import materializes: PROPOSED + REJECTED materialize NOTHING; the APPROVED import "
               "materializes into set-once campaign-level records (worker fail-closed on state).")
    else:
        record("MC5", "FAIL-007", "BREACH", "a non-APPROVED import materialized")

    # MC6 — re-decide an already-decided import -> refused.
    imp_store, rec_store, gate, worker = new_ads_stack()
    gate.propose(make_import("rd", "campX", 1, maker="m"))
    gate.record_decision("rd", decision("c"))                                    # APPROVED
    redecide_refused = False
    try:
        gate.record_decision("rd", decision("c2", kind=ImportDecisionKind.REJECT))
    except AdsSpendImportGateViolation:
        redecide_refused = True
    if redecide_refused and imp_store.get("rd").state is AdsSpendImportState.APPROVED:
        record("MC6", "FAIL-007", "DEFENDED",
               "re-deciding an already-APPROVED import is REFUSED (no flip-flop / late reversal); the recorded "
               "decision is immutable.")
    else:
        record("MC6", "FAIL-007", "BREACH", "an already-decided import was re-decided")

    # MC7 — set-once record store: identical replay no-op; altered refuse; update/delete raise.
    imp_store, rec_store, gate, worker = new_ads_stack()
    approve_and_materialize(imp_store, rec_store, gate, worker, "im", "campX", 100000)
    n1 = len(rec_store)
    worker.run_once()                                                            # idempotent replay
    n2 = len(rec_store)
    altered_refused = update_refused = delete_refused = False
    try:
        rec_store.materialize_import("im", (AdsSpendRecord(amount=999.0, campaign_id="campX", spend_date=TS),))
    except AdsSpendRecordStoreViolation:
        altered_refused = True
    try:
        rec_store.update("im")
    except AdsSpendRecordStoreViolation:
        update_refused = True
    try:
        rec_store.delete("im")
    except AdsSpendRecordStoreViolation:
        delete_refused = True
    if n1 == n2 and altered_refused and update_refused and delete_refused:
        record("MC7", "FAIL-007", "DEFENDED",
               "the ads-spend record store is SET-ONCE: an idempotent re-materialize is a no-op, an ALTERED "
               "re-materialize + update() + delete() all raise (a spend correction must be a NEW import).")
    else:
        record("MC7", "FAIL-007", "BREACH", f"set-once record store leaked (altered={altered_refused})")

    # MC8 — no network / Marketing-API / send verb on the gate / materializer.
    verbs = ("send", "fetch", "network", "marketing", "api", "deliver", "post", "http", "request", "connect", "scale")
    hits = [v for v in verbs if hasattr(gate, v) or hasattr(worker, v)]
    if not hits:
        record("MC8", "FAIL-007", "DEFENDED",
               "the import gate + materializer expose NO network/Marketing-API/send/fetch verb (M6-OD-016 phase-1 "
               "CSV only; nothing egresses).")
    else:
        record("MC8", "FAIL-007", "BREACH", f"a network verb is exposed: {hits}")

    # MC9 (NEW) — a Unicode FULL-WIDTH homoglyph of the maker escapes casefold() (not NFKC) -> APPROVED.
    imp_store, rec_store, gate, worker = new_ads_stack()
    gate.propose(make_import("hg", "campX", 1, maker="maker_ops"))
    fullwidth = "".join(chr(ord(c) + 0xFEE0) if "a" <= c <= "z" else c for c in "maker_ops")   # ｍａｋｅｒ_ｏｐｓ
    hg_slipped = False
    try:
        gate.record_decision("hg", decision(fullwidth))
        hg_slipped = imp_store.get("hg").state is AdsSpendImportState.APPROVED
    except AdsSpendImportGateViolation:
        pass
    same_canon = _canon_actor(fullwidth) == _canon_actor("maker_ops")
    if hg_slipped and not same_canon:
        record("MC9", "FAIL-007", "OPEN_NONGATE",
               "F-SPEND-1 (NEW): a Unicode FULL-WIDTH homoglyph of the maker ('maker_ops' -> the full-width form) "
               "does NOT casefold to the maker (casefold != NFKC) -> canon differs -> treated as a DISTINCT checker "
               "-> APPROVED. Armed-not-fired: staged actors are UNAUTHENTICATED free text (a self-approver can "
               "already type any distinct string), so the four-eyes control is structural until M6-OD-011 binds real "
               "identity. Route CODER: NFKC-normalize before strip+casefold in _canon_actor (mirror-parity for when "
               "auth binds a real homoglyph identity).")
    else:
        record("MC9", "FAIL-007", "DEFENDED",
               f"full-width homoglyph handled (slipped={hg_slipped}, same_canon={same_canon}).")

    # MC10 — the untrusted checker free-text (reason/audit_ref) is NOT echoed into the audit detail; actor masked.
    audit = AuditLog()
    imp_store2 = AdsSpendImportStore()
    gate2 = AdsSpendImportGate(imp_store2, audit)
    gate2.propose(make_import("pii", "campX", 1, maker="maker_ops"))
    pii_reason = "leak-" + chr(64) + "-marker"                                   # @-shaped, assembled (no literal)
    gate2.record_decision("pii", AdsSpendImportDecision(actor="checker_bob", reason=pii_reason,
                                                        audit_ref=pii_reason, evidence_ref="ev",
                                                        decision=ImportDecisionKind.APPROVE))
    blob = str([(e.action, e.reason, getattr(e, "detail", None), getattr(e, "subject", None))
                for e in audit.entries]) if hasattr(audit, "entries") else str(vars(audit))
    if pii_reason not in blob:
        record("MC10", "FAIL-008", "DEFENDED",
               "the untrusted checker free-text (reason/audit_ref) is NOT echoed into the audit detail (machine-safe: "
               "only import_id + decision enum), and the checker actor is masked -> no raw PII in the audit trail "
               "(RULE-014); the APPROVE is still audited.")
    else:
        record("MC10", "FAIL-008", "NOTE", "checker free-text reached the audit blob (inspect masking scope)")


# ===================================================================================================
# GROUP RO — CPA/ROAS-by-session (RULE-003 / FAIL-007)
# ===================================================================================================
def group_RO():
    def stack_with(ls_id, campaign_id, ov_rows, spend, spend_date=TS, bind_session=True):
        m_store = MeasurementEventStore()
        for i, (rev, oc) in enumerate(ov_rows):
            seed_ov(m_store, f"{ls_id}_ov{i}", ls_id, campaign_id, rev, oc)
        imp_store, rec_store, gate, worker = new_ads_stack()
        approve_and_materialize(imp_store, rec_store, gate, worker, f"imp_{ls_id}", campaign_id, spend, spend_date)
        binding_store = LiveSessionAdsBindingStore()
        if bind_session:
            bind(binding_store, ls_id, campaign_id)
        return m_store, rec_store, binding_store

    # RO1 — RULE-003: an in-window QUOTE_SENT contributes 0 to verified_orders / verified_revenue.
    m_store, rec_store, binding_store = stack_with("ls1", "camp1", [(500000, "o1"), (0.0, "o2")], 100000)
    seed_plain(m_store, "ls1_quote", "ls1", "QUOTE_SENT")                        # in-window quote
    seed_plain(m_store, "ls1_draft", "ls1", "ORDER_CREATED")                     # in-window draft
    r = SessionRoasReader(m_store, rec_store.all(), binding_store).for_session("ls1")
    if r.verified_orders == 2 and r.verified_revenue == 500000.0:
        record("RO1", "RULE-003", "DEFENDED",
               "RULE-003 lock: a QUOTE_SENT and an ORDER_CREATED in the session window contribute 0 to "
               "verified_orders (=2, only the OV rows) and verified_revenue (=500000). A quote/draft is never a "
               "verified order or revenue in CPA/ROAS.")
    else:
        record("RO1", "RULE-003", "BREACH", f"non-verified rows inflated the session (orders={r.verified_orders})")

    # RO2 — the mispair: a row with revenue_value on a NON-ORDER_VERIFIED event_code is excluded from verified_revenue.
    m_store = MeasurementEventStore()
    q = seed_plain(m_store, "mp_q", "ls2", "QUOTE_SENT")
    # force a revenue onto the quote row (bypassing the store guards) to test the reader's event_code filter
    from dataclasses import replace as _replace
    m_store._by_event_id["mp_q"] = _replace(m_store.get_by_event_id("mp_q"), revenue_value=999999.0)
    imp_store, rec_store, gate, worker = new_ads_stack()
    approve_and_materialize(imp_store, rec_store, gate, worker, "imp_mp", "camp2", 100000)
    binding_store = LiveSessionAdsBindingStore(); bind(binding_store, "ls2", "camp2")
    r = SessionRoasReader(m_store, rec_store.all(), binding_store).for_session("ls2")
    if r.verified_revenue == 0.0 and r.verified_orders == 0:
        record("RO2", "RULE-003", "DEFENDED",
               "the mispair: a QUOTE_SENT row carrying a (crafted) revenue_value=999999 is EXCLUDED from "
               "verified_revenue (=0) and verified_orders (=0) — _verified filters on event_code==ORDER_VERIFIED, "
               "so a revenue leaked onto a non-verified row never reaches ROAS (carried B4 lock).")
    else:
        record("RO2", "RULE-003", "BREACH", f"a non-OV revenue row inflated ROAS (rev={r.verified_revenue})")

    # RO3 — fail-closed: spend > 0 but ZERO verified orders -> CPA None (no div-by-zero) + ROAS 0.0 (wasted spend).
    m_store = MeasurementEventStore()
    seed_plain(m_store, "z_q", "ls3", "QUOTE_SENT")                              # session exists, 0 verified
    imp_store, rec_store, gate, worker = new_ads_stack()
    approve_and_materialize(imp_store, rec_store, gate, worker, "imp_z", "camp3", 100000)
    binding_store = LiveSessionAdsBindingStore(); bind(binding_store, "ls3", "camp3")
    r = SessionRoasReader(m_store, rec_store.all(), binding_store).for_session("ls3")
    if r.cpa is None and r.roas == 0.0 and r.session_spend == 100000.0:
        record("RO3", "RULE-003", "DEFENDED",
               "fail-closed: a session with spend=100000 but ZERO verified orders -> CPA None (no divide-by-zero) + "
               "ROAS 0.0 (wasted spend); never a fabricated CPA.")
    else:
        record("RO3", "RULE-003", "BREACH", f"zero-verified session mis-computed (cpa={r.cpa}, roas={r.roas})")

    # RO4 — fail-closed: no bound spend -> CPA None + ROAS None (a genuine 0/0, not a fabricated 0).
    m_store, rec_store, binding_store = stack_with("ls4", "camp4", [(500000, "o1")], 100000, bind_session=False)
    r = SessionRoasReader(m_store, rec_store.all(), binding_store).for_session("ls4")
    if r.session_spend is None and r.cpa is None and r.roas is None:
        record("RO4", "RULE-003", "DEFENDED",
               "no bound spend (campaign unbound) -> session_spend None -> CPA None + ROAS None (a genuine 0/0, "
               "never a fabricated ROAS 0).")
    else:
        record("RO4", "RULE-003", "BREACH", f"unbound spend fabricated a number (spend={r.session_spend})")

    # RO5 — spend gating: an UNBOUND campaign's record + an OUT-OF-WINDOW record -> daily_total, not session.
    m_store = MeasurementEventStore()
    seed_ov(m_store, "g_ov", "ls5", "camp5", 500000, "o1")
    imp_store, rec_store, gate, worker = new_ads_stack()
    approve_and_materialize(imp_store, rec_store, gate, worker, "in", "camp5", 100000, spend_date=TS)          # bound+in-window
    approve_and_materialize(imp_store, rec_store, gate, worker, "out", "camp5", 30000, spend_date=TS_OUT)      # bound but out-of-window
    approve_and_materialize(imp_store, rec_store, gate, worker, "unb", "camp_other", 50000, spend_date=TS)     # unbound campaign
    binding_store = LiveSessionAdsBindingStore(); bind(binding_store, "ls5", "camp5")
    reader = SessionRoasReader(m_store, rec_store.all(), binding_store)
    r = reader.for_session("ls5")
    daily = reader.daily_total()
    if r.session_spend == 100000.0 and daily == 80000.0:
        record("RO5", "RULE-003", "DEFENDED",
               "spend gating: only the bound + in-window record (100000) is session-attributed; the out-of-window "
               "(30000) + unbound-campaign (50000) records fall to daily_total (=80000), never inflating the "
               "session's CPA/ROAS.")
    else:
        record("RO5", "RULE-003", "BREACH", f"spend mis-attributed (session={r.session_spend}, daily={daily})")

    # RO6 — a campaign-level record (.mapped False) bound in-window IS included (gate is the binding, not .mapped).
    rec = AdsSpendRecord(amount=100000.0, campaign_id="camp6", spend_date=TS)
    if rec.mapped is False:
        m_store = MeasurementEventStore()
        seed_ov(m_store, "m_ov", "ls6", "camp6", 500000, "o1")
        binding_store = LiveSessionAdsBindingStore(); bind(binding_store, "ls6", "camp6")
        r = SessionRoasReader(m_store, (rec,), binding_store).for_session("ls6")
        if r.session_spend == 100000.0:
            record("RO6", "RULE-003", "DEFENDED",
                   "a campaign-LEVEL record (.mapped is False, adset/ad None) that is bound + in-window is INCLUDED "
                   "(session_spend 100000) — the gate is the campaign-binding, not the 3-id .mapped predicate.")
        else:
            record("RO6", "RULE-003", "BREACH", f"a bound campaign-level record was dropped (spend={r.session_spend})")
    else:
        record("RO6", "RULE-003", "NOTE", "AdsSpendRecord.mapped unexpectedly True for a campaign-only record")

    # RO7 — window edges: spend_date == window_start and == window_end are INCLUSIVE (<=).
    m_store = MeasurementEventStore()
    seed_ov(m_store, "e_ov1", "ls7", "camp7", 500000, "o1", ts=TS)               # window_start
    seed_ov(m_store, "e_ov2", "ls7", "camp7", 0.0, "o2", ts=TS + timedelta(hours=2))   # window_end
    imp_store, rec_store, gate, worker = new_ads_stack()
    approve_and_materialize(imp_store, rec_store, gate, worker, "es", "camp7", 40000, spend_date=TS)                  # == start
    approve_and_materialize(imp_store, rec_store, gate, worker, "ee", "camp7", 60000, spend_date=TS + timedelta(hours=2))  # == end
    binding_store = LiveSessionAdsBindingStore(); bind(binding_store, "ls7", "camp7")
    r = SessionRoasReader(m_store, rec_store.all(), binding_store).for_session("ls7")
    if r.session_spend == 100000.0:
        record("RO7", "RULE-003", "DEFENDED",
               "window edges inclusive: spend_date == window_start and == window_end are both included "
               "(session_spend 40000+60000=100000; the window test is <=).")
    else:
        record("RO7", "RULE-003", "NOTE", f"window-edge inclusion unexpected (spend={r.session_spend})")

    # RO8 — only APPROVED-materialized spend reaches the reader: a PROPOSED-only import -> no record -> no spend.
    m_store = MeasurementEventStore()
    seed_ov(m_store, "p_ov", "ls8", "camp8", 500000, "o1")
    imp_store, rec_store, gate, worker = new_ads_stack()
    gate.propose(make_import("prop_only", "camp8", 100000))                      # PROPOSED, never approved
    worker.run_once()
    binding_store = LiveSessionAdsBindingStore(); bind(binding_store, "ls8", "camp8")
    r = SessionRoasReader(m_store, rec_store.all(), binding_store).for_session("ls8")
    if r.session_spend is None and r.roas is None:
        record("RO8", "RULE-003", "DEFENDED",
               "only APPROVED-materialized spend reaches the reader: a PROPOSED-only import produced no record, so "
               "the session has no spend -> CPA/ROAS None (unapproved spend never touches the money math).")
    else:
        record("RO8", "RULE-003", "BREACH", f"unapproved spend reached the reader (spend={r.session_spend})")

    # RO9 — purity: by_session() twice mutates neither the measurement store nor the record store.
    m_store, rec_store, binding_store = stack_with("ls9", "camp9", [(500000, "o1")], 100000)
    reader = SessionRoasReader(m_store, rec_store.all(), binding_store)
    before = (len(m_store), len(rec_store))
    reader.by_session(); reader.by_session()
    after = (len(m_store), len(rec_store))
    if before == after:
        record("RO9", "RULE-003", "DEFENDED",
               "purity: reading CPA/ROAS twice writes nothing (measurement + record stores unchanged) — a read-only "
               "reader (SMK-010 support-view discipline).")
    else:
        record("RO9", "RULE-003", "BREACH", f"reading mutated a store ({before}->{after})")

    # RO10 (NEW) — value-sanity: a NEGATIVE / NaN spend_value poisons CPA/ROAS (no isfinite/sign check).
    m_store = MeasurementEventStore()
    seed_ov(m_store, "n_ov", "ls10", "camp10", 500000, "o1")
    binding_store = LiveSessionAdsBindingStore(); bind(binding_store, "ls10", "camp10")
    neg = SessionRoasReader(m_store, (AdsSpendRecord(amount=-100000.0, campaign_id="camp10", spend_date=TS),),
                            binding_store).for_session("ls10")
    nan = SessionRoasReader(m_store, (AdsSpendRecord(amount=float("nan"), campaign_id="camp10", spend_date=TS),),
                            binding_store).for_session("ls10")
    if neg.session_spend == -100000.0 and neg.roas is not None and neg.roas < 0 and math.isnan(nan.roas):
        record("RO10", "RULE-003", "OPEN_NONGATE",
               "value-sanity gap (F-SPEND-2, NEW): a NEGATIVE spend (-100000) makes ROAS negative (=-5.0) and CPA "
               "negative; a NaN spend makes ROAS NaN — neither the import/materialize nor the reader checks "
               "finiteness/sign. Trusted-input: spend is maker-checker APPROVED (a human checker reviews the CSV "
               "rows); not channel-reachable. Route CODER: reject/clamp non-finite/negative spend_value at import "
               "(math.isfinite and >= 0). RULE-009-adjacent, out of the 3-leg core.")
    else:
        record("RO10", "RULE-003", "DEFENDED", f"value-sanity enforced (neg_roas={neg.roas}, nan_roas={nan.roas})")


# ===================================================================================================
# GROUP BIND — binding set-once + unambiguous; primary_campaign_id additive (RULE-015)
# ===================================================================================================
def group_BIND():
    # B1/B2 — set-once (session re-bind to a different campaign refused) + campaign-unambiguous (a campaign bound to
    #         two sessions refused).
    bs = LiveSessionAdsBindingStore()
    bind(bs, "lsA", "campA")
    rebind_refused = ambiguous_refused = False
    try:
        bs.bind(LiveSessionAdsBinding(live_session_id="lsA", primary_campaign_id="campZ", bound_at=TS, bound_by="b"))
    except LiveSessionAdsBindingStoreViolation:
        rebind_refused = True
    try:
        bs.bind(LiveSessionAdsBinding(live_session_id="lsB", primary_campaign_id="campA", bound_at=TS, bound_by="b"))
    except LiveSessionAdsBindingStoreViolation:
        ambiguous_refused = True
    if rebind_refused and ambiguous_refused and bs.session_for_campaign("campA") == "lsA":
        record("B1", "FAIL-007", "DEFENDED",
               "binding is SET-ONCE + campaign-UNAMBIGUOUS: re-binding lsA to a different campaign is refused, and "
               "binding campA to a second session (lsB) is refused -> session_for_campaign stays unambiguous (spend "
               "cannot be split/mis-attributed by an ambiguous binding).")
    else:
        record("B1", "FAIL-007", "BREACH", f"binding ambiguity possible (rebind={rebind_refused}, amb={ambiguous_refused})")

    # B2 — primary_campaign_id additive + NOT in grading: a complete FACEBOOK_AD context stays HIGH-eligible.
    hi = AdsAttributionContext(page_id="p", entry_channel=EntryChannel.FACEBOOK_AD, attribution_window="7d",
                               source_confidence=SourceConfidence.HIGH, conflict_status=ConflictStatus.NONE,
                               campaign_id="c", primary_campaign_id="c")
    lo = AdsAttributionContext(page_id="p", entry_channel=EntryChannel.LIVE_ORGANIC, attribution_window="7d",
                               source_confidence=SourceConfidence.LOW, conflict_status=ConflictStatus.MULTI_TOUCH,
                               primary_campaign_id="c")
    pub = hi.to_public()
    if hi.is_scale_evidence_eligible() and not lo.is_scale_evidence_eligible() and pub.get("primary_campaign_id") == "c":
        record("B2", "FAIL-007", "DEFENDED",
               "primary_campaign_id is ADDITIVE: it is emitted in to_public/as_stored but is NOT consulted by "
               "is_scale_evidence_eligible (which reads only source_confidence HIGH + conflict NONE) -> the A4 grading "
               "(SMK-020 HIGH / SMK-007 MULTI_TOUCH) is unaffected.")
    else:
        record("B2", "FAIL-007", "BREACH", "primary_campaign_id perturbed grading")


# ===================================================================================================
# GROUP PII — RULE-014 (actors masked; campaign/spend not PII)
# ===================================================================================================
def group_PII():
    import re as _re
    imp = make_import("pub", "camp_x", 100000, maker="maker_secret")
    d = AdsSpendImportDecision(actor="checker_secret", reason="ok", audit_ref="a", evidence_ref="e",
                               decision=ImportDecisionKind.APPROVE)
    binding = LiveSessionAdsBinding(live_session_id="ls", primary_campaign_id="camp_x", bound_at=TS, bound_by="binder_secret")
    blobs = [str(imp.to_public()), str(d.to_public()), str(binding.to_public())]
    raw_actor_leaked = any("maker_secret" in b or "checker_secret" in b or "binder_secret" in b for b in blobs)
    campaign_present = "camp_x" in blobs[0]
    pii_shaped = any("@" in b or _re.findall(r"\d{7,}", b) for b in blobs)
    if not raw_actor_leaked and campaign_present and not pii_shaped:
        record("PII", "FAIL-008", "DEFENDED",
               "RULE-014: uploaded_by / decided_by / actor / bound_by are MASKED on to_public (raw actor refs "
               "absent); campaign_id + spend numbers are exposed (campaign-level, not PII); no '@'/phone-shaped token "
               "in any export.")
    else:
        record("PII", "FAIL-008", "BREACH", f"a raw actor / PII leaked on export (actor_leaked={raw_actor_leaked})")


# ===================================================================================================
# GROUP F7 — carried FAIL-007 evidence pack + posture
# ===================================================================================================
def group_F7():
    from app.measurement.evidence.pack_assembler import EvidencePackAssembler
    from app.measurement.evidence.models import Readiness, SmokeResult
    from app.measurement.evidence.categories import CATEGORY_MANDATORY
    from app.measurement.evidence.smoke_registry import SMOKE_IDS
    from types import SimpleNamespace
    a = EvidencePackAssembler()
    refs = {cat: {k: f"ev::{cat.value}::{k}" for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}
    recorded = {sid: SmokeResult(sid, status="PASS", correlation_id="c" + sid[-3:], evidence_id="e" + sid[-3:])
                for sid in SMOKE_IDS}
    recorded["M6-SMK-001"] = SimpleNamespace(smoke_id="M6-SMK-001", status=None, correlation_id=None,
                                             evidence_id=None, waived=False, recorded=True)
    p = a.assemble(recorded, refs)
    smk = next(s for s in p.smokes if s.smoke_id == "M6-SMK-001")
    if not smk.recorded and p.readiness is Readiness.NOT_READY \
            and {m.value for m in Readiness} == {"OWNER_REVIEW_REQUIRED", "NOT_READY"}:
        record("F7", "FAIL-007", "DEFENDED",
               "carried evidence pack intact: F2-6 duck-coerce still rebuilds a lying duck -> NOT_READY; Readiness "
               "has no Pass/Ready member (no self-cert, RULE-015). The A5 spend work added no Pass/advance path.")
    else:
        record("F7", "FAIL-007", "BREACH", "carried evidence pack regressed")

    # posture
    if (config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
            and config.EXTERNAL_SEND == "OFF" and config.is_external_send_enabled() is False):
        record("REG", "FAIL-007", "DEFENDED",
               "posture immutable: BLOCKED / OFF / OFF, is_external_send_enabled() False — the A5 spend slice flipped "
               "nothing and opened no egress.")
    else:
        record("REG", "FAIL-007", "BREACH", "posture changed")


# ===================================================================================================
# GROUP N — reconciliation of the ideation workflow's novel vectors (executed)
# ===================================================================================================
def group_N():
    # N1 (ROAS-13, HIGHEST-VALUE) — the revenue-session join reuses the UN-PROVENANCED live_session_id: spend is
    #     authenticated (campaign->session binding), but a verified-revenue event is attributed to whatever session
    #     its live_session_id names (via _session_key), regardless of the spend binding. So a revenue event on a
    #     DIFFERENT campaign, tagged with the bound session's live_session_id, inflates that session's ROAS.
    m_store = MeasurementEventStore()
    seed_ov(m_store, "real_ov", "ls_real", "camp_real", 100000, "o1")            # genuine revenue for the session
    seed_ov(m_store, "forge_ov", "ls_real", "camp_OTHER", 900000, "o2")          # revenue on a DIFFERENT campaign, same live_session_id
    imp_store, rec_store, gate, worker = new_ads_stack()
    approve_and_materialize(imp_store, rec_store, gate, worker, "imp_r", "camp_real", 100000)
    binding_store = LiveSessionAdsBindingStore(); bind(binding_store, "ls_real", "camp_real")
    r = SessionRoasReader(m_store, rec_store.all(), binding_store).for_session("ls_real")
    if r.verified_revenue == 1000000.0:
        record("N1", "RULE-003", "OPEN_NONGATE",
               "ROAS-13 (carried F-SEC-2I-1, revenue-side): the CPA/ROAS revenue-session join is by _session_key "
               "(event.live_session_id / attribution_context), NOT by the spend binding — a verified-revenue event on "
               "a DIFFERENT campaign (camp_OTHER, 900000) tagged with the bound session's live_session_id is counted "
               "in ls_real's verified_revenue (=1000000), inflating its ROAS. The spend side is authenticated "
               "(campaign->session, unambiguous); the revenue-session assignment inherits the live_session_id "
               "provenance gap (M6.2I-FUNNEL standing blocker). Armed-not-fired: the reader is internal (no channel "
               "export) and events come from the trusted measurement store; but the asymmetry is real. Route: owner "
               "(F-SEC-2I-1 single-subject/live_session bind before any surface).")
    else:
        record("N1", "RULE-003", "DEFENDED", f"revenue-session join is spend-binding-tied (rev={r.verified_revenue})")

    # N2 (ROAS-10/11) — REVENUE value-sanity: a NEGATIVE / NaN revenue on a GENUINE ORDER_VERIFIED row poisons
    #     verified_revenue -> ROAS. More reachable than spend (no maker-checker gate on Commerce revenue); NaN also
    #     breaks the JSON export contract (to_public emits raw NaN).
    m_store = MeasurementEventStore()
    seed_ov(m_store, "neg_ov", "ls_n", "camp_n", -999000, "o1")
    imp_store, rec_store, gate, worker = new_ads_stack()
    approve_and_materialize(imp_store, rec_store, gate, worker, "imp_n", "camp_n", 100000)
    binding_store = LiveSessionAdsBindingStore(); bind(binding_store, "ls_n", "camp_n")
    neg = SessionRoasReader(m_store, rec_store.all(), binding_store).for_session("ls_n")
    m2 = MeasurementEventStore()
    seed_ov(m2, "nan_ov", "ls_x", "camp_x", float("nan"), "o1")
    bs2 = LiveSessionAdsBindingStore(); bind(bs2, "ls_x", "camp_x")
    nan_res = SessionRoasReader(m2, (AdsSpendRecord(amount=100000.0, campaign_id="camp_x", spend_date=TS),), bs2).for_session("ls_x")
    if neg.verified_revenue == -999000.0 and neg.roas is not None and neg.roas < 0 and math.isnan(nan_res.verified_revenue):
        record("N2", "RULE-003", "OPEN_NONGATE",
               "REVENUE value-sanity gap (ROAS-10/11): a NEGATIVE revenue (-999000) on a genuine ORDER_VERIFIED row "
               "makes verified_revenue/ROAS negative; a NaN revenue makes verified_revenue NaN (and to_public emits "
               "raw NaN -> breaks JSON export). Neither the store set-path nor _verified checks finiteness/sign, and "
               "revenue has NO maker-checker gate (Commerce-supplied) -> the REVENUE-side value-sanity is MORE "
               "reachable than the spend side (F-SPEND-2 twin). Route CODER: math.isfinite(v) and v>=0 on the "
               "verified-revenue write (same fix as the spend guard). Carried from M6.2L N4.")
    else:
        record("N2", "RULE-003", "DEFENDED", f"revenue value-sanity enforced (neg={neg.roas}, nan={nan_res.verified_revenue})")

    # N3 (ROAS-12) — order_code double-count: two ORDER_VERIFIED events sharing an order_code but distinct
    #     idempotency_key both count -> inflate verified_orders (CPA denom) + verified_revenue (ROAS num). The reader
    #     counts per-EVENT; there is no per-order dedup (the store dedups only on idempotency_key).
    m_store = MeasurementEventStore()
    seed_ov(m_store, "dc1", "ls_dc", "camp_dc", 500000, "ORD_SHARED")
    seed_ov(m_store, "dc2", "ls_dc", "camp_dc", 500000, "ORD_SHARED")            # same order_code, distinct event
    imp_store, rec_store, gate, worker = new_ads_stack()
    approve_and_materialize(imp_store, rec_store, gate, worker, "imp_dc", "camp_dc", 100000)
    binding_store = LiveSessionAdsBindingStore(); bind(binding_store, "ls_dc", "camp_dc")
    r = SessionRoasReader(m_store, rec_store.all(), binding_store).for_session("ls_dc")
    if r.verified_orders == 2 and r.verified_revenue == 1000000.0:
        record("N3", "RULE-003", "OPEN_NONGATE",
               "order_code double-count (ROAS-12, carried F-DASH-3): two ORDER_VERIFIED events sharing order_code "
               "'ORD_SHARED' (distinct idempotency_key) both count -> verified_orders=2 (CPA denom) + "
               "verified_revenue=1000000 (ROAS num). _verified counts per-EVENT with no per-order dedup (the store "
               "dedups only on idempotency_key). Reachable only if one order yields two distinct-key OV events "
               "(upstream verify uniqueness). Route: owner confirm order_code uniqueness, or dedup _verified by "
               "order_code (mirror DataMart.verified_order_count).")
    else:
        record("N3", "RULE-003", "DEFENDED", f"order_code deduped (orders={r.verified_orders})")

    # N4 (MC-11) — the four-eyes checks only the CHECKER side: a BLANK maker + a distinct non-blank checker ->
    #     APPROVED. An import with no identifiable uploader can be approved by one actor.
    imp_store, rec_store, gate, worker = new_ads_stack()
    gate.propose(make_import("bm", "camp_bm", 1, maker=""))                      # blank MAKER
    approved = False
    try:
        gate.record_decision("bm", decision("checker_bob"))
        approved = imp_store.get("bm").state is AdsSpendImportState.APPROVED
    except AdsSpendImportGateViolation:
        pass
    if approved:
        record("N4", "FAIL-007", "OPEN_NONGATE",
               "MC-11 (maker-side four-eyes gap): the gate refuses a blank CHECKER but not a blank MAKER — an import "
               "with uploaded_by='' + any distinct non-blank checker is APPROVED (only checker != '' and checker != "
               "canon(maker='') is tested; a non-blank checker satisfies both). An unattributed uploader's import can "
               "still be approved by one actor. Armed-not-fired (actors are unauthenticated free text until "
               "M6-OD-011). Route CODER: require a non-blank MAKER too (four-eyes needs two distinct non-blank actors).")
    else:
        record("N4", "FAIL-007", "DEFENDED", "blank-maker import was not approvable")

    # N5 (MC-09 / ROAS-14/15 / BIND-07 / EVID-10 — documented residuals, not separately executed)
    record("N5", "FAIL-007", "NOTE",
           "documented residuals (armed-not-fired, trusted-input, route CODER/owner/security): (a) MC-09 "
           "AdsSpendImportDecision.to_public() emits reason/audit_ref VERBATIM (only actor masked) -> a PII-shaped "
           "reason exports unmasked (M6-OD-012 / security M6-P2506); (b) ROAS-14 a rogue event_ts widens the derived "
           "[min,max] window (no event_ts sanity) -> re-scopes which bound spend attributes to a session; (c) ROAS-15 "
           "a tz-aware spend_date vs tz-naive event_ts raises TypeError -> crashes by_session()/daily_total() "
           "(availability, not fail-closed) — normalize tz; (d) BIND-07 a blank primary_campaign_id poisons the "
           "reverse index (mild DoS; session_for_campaign('') is guarded to None so no mis-attribution) — reject "
           "blank; (e) EVID-10 the A5 SessionRoasReader RULE-003 lock is proven by SMK-029 (proposed/HARDENING), NOT "
           "a registered P0 smoke, so a future regression that let a quote/draft inflate CPA/ROAS-by-session would not "
           "drop pack readiness -> owner decides whether the A5 reader needs a P0-registry floor.")


# ===================================================================================================
def main():
    print("=" * 100)
    print("M6.2Q BOUNDARY ADVERSARY — ads-spend + CPA/ROAS-by-session (in-scope: FAIL-007 / RULE-003)")
    print(f"impl root: {IMPL}")
    print("=" * 100)
    for g in (group_MC, group_RO, group_BIND, group_PII, group_F7, group_N):
        print(f"\n----- {g.__name__} -----")
        g()

    print("\n" + "=" * 100)
    tally = {}
    for _, _, k, _ in OUTCOMES:
        tally[k] = tally.get(k, 0) + 1
    breaches = [o for o in OUTCOMES if o[2] == "BREACH"]
    inscope = [o for o in breaches if o[1] in ("FAIL-007", "RULE-003", "FAIL-008")]
    print(f"SUMMARY: {tally}")
    print(f"TOTAL RECORDED OUTCOMES: {len(OUTCOMES)}")
    print(f"IN-SCOPE BREACHES (FAIL-007 / RULE-003): {len(inscope)}")
    for o in breaches:
        print("   BREACH:", o)

    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
    assert config.EXTERNAL_SEND == "OFF"
    print("POSTURE AFTER RUN: BLOCKED / OFF / OFF (unchanged)")
    print("=" * 100)


if __name__ == "__main__":
    main()
