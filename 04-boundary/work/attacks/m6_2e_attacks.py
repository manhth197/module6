"""M6-P1405 BOUNDARY ADVERSARY — executed attacks vs FROZEN staged M6.2E attribution layer.

Read-only: imports the staged package from 04-artifacts/impl/M6.2E and drives the real seams (attribution
resolver + grading, materializer set-once + scale-evidence gating, adjustment path, the endpoint F-D bind,
platform_event_id F-E, safe_subject_ref F-F). Writes NOTHING (sys.dont_write_bytecode=True; run with -B). No
network, no DB, no persisted flag flip. One structured line per attack; a SUMMARY last. PII-shaped probes are
constructed programmatically and never echoed.

Status vocabulary:
  DEFENDED     attack blocked as required (LOW/HOLD never scale evidence; revenue verified-only + set-once; etc.)
  BREACH       an IN-SCOPE fail gate (M6-FAIL-001 / M6-FAIL-004) is actually tripped  (expect 0)
  OPEN_NONGATE a real defect that does NOT trip an in-scope fail gate
  CONTROL      non-vacuity control
  NOTE         observation for the owner / routed to M6-P1406
"""
from __future__ import annotations

import sys
import os
import io
import tokenize
from datetime import datetime, timezone

sys.dont_write_bytecode = True
IMPL = r"D:\M6\Module6-workspace\04-artifacts\impl\M6.2E"
sys.path.insert(0, IMPL)

from app import config as cfg
from app.measurement.audit import AuditLog
from app.measurement.attribution.resolver import AttributionResolver
from app.measurement.attribution.materializer import AttributionMaterializer
from app.measurement.attribution.adjustment import AdjustmentRecord, AdjustmentLog
from app.measurement.models.attribution_context import (
    AdsAttributionContext, EntryChannel, SourceConfidence, ConflictStatus,
)
from app.measurement.store.measurement_event_store import MeasurementEventStore, MeasurementStoreViolation
from app.measurement.models.measurement_event import AdsMeasurementEvent
from app.measurement.models.conversion_event import ConversionEvent
from app.measurement.integration.payload import platform_event_id
from app.measurement.outbox.transport import safe_subject_ref
from app.measurement.outbox.measurement_dispatcher import MeasurementDispatcher
from app.measurement.outbox.outbox_store import OutboxStore
from app.measurement.outbox.enqueue import enqueue_measurement
from app.measurement.integration.platform_transport import StagedPlatformTransport
from app.measurement.integration.result_log import PlatformResultLog
from app.measurement.consent.gate import ConsentGate
from app.measurement.registry.validator import EventValidator
from app.measurement.adapters.consent_reader import InMemoryConsentReader
from app.measurement.models.consumed import (
    ConsentScope, ConsentSnapshot, ConsentState, DataSensitivity, EventRegistryRow, RegistrationState,
)
from app.measurement.store.conversion_event_store import ConversionEventStore
from app.api.conversions import handle_conversions_request, ConversionDeps

TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
NOW = datetime(2026, 7, 30, 12, 0, 0, tzinfo=timezone.utc)
OUT = []


def rec(pid, status, gate, detail):
    OUT.append((pid, status, gate, detail))
    print(f"[{pid:<18}] {status:<12} gate={gate:<11} :: {detail}")


REG = {
    "VIEW_LANDING": EventRegistryRow("VIEW_LANDING", RegistrationState.ACTIVE, owner="core.tracking", data_sensitivity=DataSensitivity.INTERNAL),
    "ORDER_VERIFIED": EventRegistryRow("ORDER_VERIFIED", RegistrationState.ACTIVE, owner="core.tracking", data_sensitivity=DataSensitivity.INTERNAL),
    "PAYMENT_COMPLETED": EventRegistryRow("PAYMENT_COMPLETED", RegistrationState.ACTIVE, owner="core.tracking", data_sensitivity=DataSensitivity.INTERNAL),
}
class Reg:
    def get(self, code): return REG.get(code)


def mk_event(event_id="evt_1", *, event_code="ORDER_VERIFIED", **f):
    return AdsMeasurementEvent(event_id=event_id, event_code=event_code, event_ts=TS,
                               idempotency_key=f.pop("idempotency_key", f"idem_{event_id}"),
                               correlation_id="corr_ame", ingested_at=TS, **f)


def mk_conv(event_code="ORDER_VERIFIED", *, revenue_value=None, order_code=None, src="evt_1", cust="cust_self", cs="cs_self"):
    return ConversionEvent(conversion_id=f"conv_{src}", event_code=event_code, source_event_id=src,
                           correlation_id="corr_c", customer_or_guest_key=cust, consent_snapshot_id=cs,
                           occurred_at=TS, idempotency_key=f"idem_conv_{src}", revenue_value=revenue_value, order_code=order_code)


def materialize(event, conv, *, signals=None):
    store = MeasurementEventStore(); store.insert(event)
    mat = AttributionMaterializer(store, AttributionResolver(), AuditLog())
    outcome = mat.materialize(event, conv, signals=signals)
    return outcome, store, mat


print("=" * 104)
print("M6-P1405 — executed boundary attacks vs FROZEN M6.2E attribution layer (py", sys.version.split()[0], ")")
print("=" * 104)

# =================================================================================================
# GROUP SE — LOW/HOLD/conflict never scale evidence (M6-FAIL-001 / RULE-009)
# =================================================================================================
# eligibility matrix: True ONLY for HIGH + NONE
eligible_true = []
for conf in SourceConfidence:
    for cflt in ConflictStatus:
        ctx = AdsAttributionContext(page_id="p", entry_channel=EntryChannel.FACEBOOK_AD,
                                    attribution_window="7d", source_confidence=conf, conflict_status=cflt)
        if ctx.is_scale_evidence_eligible():
            eligible_true.append((conf.value, cflt.value))
rec("SE-eligible-matrix", "DEFENDED" if eligible_true == [("HIGH", "NONE")] else "BREACH", "M6-FAIL-001",
    f"is_scale_evidence_eligible True combos = {eligible_true} (must be exactly [(HIGH,NONE)]; attribution_context.py:91-94)")

# while SCALE_MODEL_RATIFIED=False, EVEN a HIGH+NONE materialize -> scale_evidence False (doubly fail-closed)
ev = mk_event("evt_hi", campaign_id="camp_1", adset_id="ads_1", ad_id="ad_1")
oc, store, _ = materialize(ev, mk_conv(order_code="ORD_1", revenue_value=250000.0))
rec("SE-unratified-highnone", "DEFENDED" if (oc.scale_evidence_eligible is True and oc.scale_evidence is False) else "BREACH",
    "M6-FAIL-001", f"HIGH+NONE materialize: eligible={oc.scale_evidence_eligible}, scale_evidence={oc.scale_evidence} "
    f"(SCALE_MODEL_RATIFIED False -> never scale evidence; materializer.py:79-80)")

# a LOW (missing source) materialize -> never eligible, never scale evidence
ev2 = mk_event("evt_lo")   # no campaign/live -> MISSING_SOURCE/LOW
oc2, _, _ = materialize(ev2, mk_conv(src="evt_lo", order_code="ORD_2", revenue_value=99000.0))
rec("SE-materialize-low", "DEFENDED" if (oc2.context.source_confidence is SourceConfidence.LOW
    and oc2.scale_evidence_eligible is False and oc2.scale_evidence is False and oc2.revenue_value == 99000.0) else "BREACH",
    "M6-FAIL-001", f"missing-source verified: confidence={oc2.context.source_confidence.value}, "
    f"conflict={oc2.context.conflict_status.value}, eligible={oc2.scale_evidence_eligible}, scale_evidence={oc2.scale_evidence}, "
    f"revenue={oc2.revenue_value} (revenue stored, never scale evidence; SMK-007)")

# force SCALE_MODEL_RATIFIED=True -> HIGH+NONE becomes scale_evidence, but a LOW stays False (eligible False)
_orig = cfg.SCALE_MODEL_RATIFIED
try:
    cfg.SCALE_MODEL_RATIFIED = True
    evh = mk_event("evt_fh", campaign_id="c", adset_id="a", ad_id="d")
    och, _, _ = materialize(evh, mk_conv(src="evt_fh", order_code="O", revenue_value=1.0))
    evl = mk_event("evt_fl")
    ocl, _, _ = materialize(evl, mk_conv(src="evt_fl", order_code="O", revenue_value=1.0))
    forced_ok = (och.scale_evidence is True and ocl.scale_evidence is False)
finally:
    cfg.SCALE_MODEL_RATIFIED = _orig
rec("SE-force-ratified", "DEFENDED" if forced_ok else "BREACH", "M6-FAIL-001",
    f"force SCALE_MODEL_RATIFIED=True -> HIGH+NONE scale_evidence={och.scale_evidence}, LOW scale_evidence={ocl.scale_evidence} "
    f"(a LOW is never scale evidence even when ratified; eligible gate holds)")

# grading fail-closed: enumerate source shapes -> confidence/conflict
def grade(event, signals=None):
    ctx = AttributionResolver().resolve(event, mk_conv(src=event.event_id), signals=signals)
    return ctx.source_confidence.value, ctx.conflict_status.value

cases = {
    "missing": grade(mk_event("g1")),
    "complete_ad": grade(mk_event("g2", campaign_id="c", adset_id="a", ad_id="d")),
    "incomplete_ad": grade(mk_event("g3", campaign_id="c")),
    "multi_ad_live": grade(mk_event("g4", campaign_id="c", adset_id="a", ad_id="d", live_session_id="ls")),
    "dup_risk": grade(mk_event("g5", campaign_id="c", adset_id="a", ad_id="d"), {"duplicate_risk": True}),
    "live_session": grade(mk_event("g6", live_session_id="ls")),
    "live_comment_only": grade(mk_event("g7"), {"comment_id": "cm"}),
    "diamond": grade(mk_event("g8"), {"referral_link_id": "rl", "diamond_id": "dm"}),
    "crm_only": grade(mk_event("g9"), {"crm": True}),
    "inject_crm_degrades": grade(mk_event("g10", campaign_id="c", adset_id="a", ad_id="d"), {"crm": True}),
}
# expectation: only complete_ad / live_session / diamond -> HIGH+NONE; everything ambiguous/missing/conflict -> not HIGH
bad_grade = 0
if cases["missing"] != ("LOW", "MISSING_SOURCE"): bad_grade += 1
if cases["complete_ad"] != ("HIGH", "NONE"): bad_grade += 1
if cases["incomplete_ad"] != ("MEDIUM", "NONE"): bad_grade += 1
if cases["multi_ad_live"] != ("LOW", "MULTI_TOUCH"): bad_grade += 1
if cases["dup_risk"] != ("LOW", "DUPLICATE_RISK"): bad_grade += 1
if cases["live_session"] != ("HIGH", "NONE"): bad_grade += 1
if cases["live_comment_only"] != ("MEDIUM", "NONE"): bad_grade += 1
if cases["diamond"] != ("HIGH", "NONE"): bad_grade += 1
if cases["crm_only"] != ("MEDIUM", "NONE"): bad_grade += 1
if cases["inject_crm_degrades"] != ("LOW", "MULTI_TOUCH"): bad_grade += 1
rec("SE-grading", "DEFENDED" if bad_grade == 0 else "BREACH", "M6-FAIL-001",
    f"10 source shapes graded fail-closed, mismatches={bad_grade}; a missing/conflicting/multi source is never HIGH; "
    f"injecting a crm signal on a complete ad DEGRADES to MULTI_TOUCH/LOW (cannot inflate). cases={cases}")

# =================================================================================================
# GROUP REV — revenue only ORDER_VERIFIED + SET-ONCE (M6-FAIL-001 / RULE-003 / RULE-008)
# =================================================================================================
# non-ORDER_VERIFIED -> NO revenue
for code in ("VIEW_LANDING", "PAYMENT_COMPLETED"):
    ev = mk_event(f"evt_nv_{code}", event_code=code)
    oc, _, _ = materialize(ev, mk_conv(code, src=f"evt_nv_{code}", revenue_value=500000.0, order_code="ORD"))
    ok = oc.revenue_value is None
    rec(f"REV-nonverified-{code}", "DEFENDED" if ok else "BREACH", "M6-FAIL-001",
        f"{code} conversion (with a revenue_value on the conversion) -> materialized revenue={oc.revenue_value} "
        f"(revenue ONLY from ORDER_VERIFIED; materializer.py:65-67)")

# verified set-once: a DIFFERENT revenue on re-materialize -> MeasurementStoreViolation
ev = mk_event("evt_so", campaign_id="c", adset_id="a", ad_id="d")
store = MeasurementEventStore(); store.insert(ev)
mat = AttributionMaterializer(store, AttributionResolver(), AuditLog())
mat.materialize(ev, mk_conv(src="evt_so", order_code="ORD", revenue_value=100000.0))
try:
    mat.materialize(ev, mk_conv(src="evt_so", order_code="ORD", revenue_value=999999.0))
    setonce = "no-raise"
except MeasurementStoreViolation:
    setonce = "raised"
same_noop = mat.materialize(ev, mk_conv(src="evt_so", order_code="ORD", revenue_value=100000.0)).changed
row_rev = store.get_by_event_id("evt_so").revenue_value
rec("REV-setonce", "DEFENDED" if (setonce == "raised" and same_noop is False and row_rev == 100000.0) else "BREACH",
    "M6-FAIL-001", f"verified revenue set-once: different-value re-materialize={setonce}, identical=no-op(changed={same_noop}), "
    f"row revenue stays {row_rev} (measurement_event_store.py:88-100, RULE-008)")

# revenue requires an order_code
ev = mk_event("evt_noord")
store = MeasurementEventStore(); store.insert(ev)
try:
    store.materialize("evt_noord", attribution_context={}, revenue_value=1.0, order_code=None, verified=True)
    noord = "no-raise"
except MeasurementStoreViolation:
    noord = "raised"
rec("REV-requires-order", "DEFENDED" if noord == "raised" else "BREACH", "M6-FAIL-001",
    f"revenue_value without order_code -> {noord} (measurement_event_store.py:85-86)")

# a revenue-bearing Zone-A insert -> violation; update/delete -> violation
viol = []
s2 = MeasurementEventStore()
try:
    s2.insert(AdsMeasurementEvent(event_id="e", event_code="ORDER_VERIFIED", event_ts=TS, idempotency_key="k",
                                  correlation_id="c", revenue_value=1.0))
    viol.append("zoneA-revenue=no-raise")
except MeasurementStoreViolation:
    pass
for op in ("update", "delete"):
    try:
        getattr(s2, op)(); viol.append(f"{op}=no-raise")
    except MeasurementStoreViolation:
        pass
rec("REV-store-guards", "DEFENDED" if not viol else "BREACH", "M6-FAIL-001",
    f"revenue-bearing Zone-A insert + update/delete all raise; leaks={viol or 'NONE'} (RULE-007/008)")

# =================================================================================================
# GROUP ADJ — immutability + adjustment path (M6-FAIL-004 / RULE-008, SMK-018)
# =================================================================================================
ev = mk_event("evt_adj", campaign_id="c", adset_id="a", ad_id="d")
store = MeasurementEventStore(); store.insert(ev)
mat = AttributionMaterializer(store, AttributionResolver(), AuditLog())
mat.materialize(ev, mk_conv(src="evt_adj", order_code="ORD", revenue_value=100000.0))
log = AdjustmentLog()
mat.request_adjustment("evt_adj", actor="op_1", reason="fix", audit_ref="a1", evidence_ref="e1",
                       proposed={"revenue_value": 300000.0}, adjustment_log=log)
row_after = store.get_by_event_id("evt_adj")
no_mutate = (row_after.revenue_value == 100000.0 and len(log) == 1)
rec("ADJ-no-mutate", "DEFENDED" if no_mutate else "BREACH", "M6-FAIL-004",
    f"request_adjustment(proposed revenue=300000) -> verified row revenue STILL {row_after.revenue_value}, "
    f"adjustment records={len(log)} (overlay, never mutates the row; materializer.py:103-134)")

# a 2nd adjustment appends; the 1st is untouched (append-only)
mat.request_adjustment("evt_adj", actor="op_2", reason="fix2", audit_ref="a2", evidence_ref="e2", proposed={}, adjustment_log=log)
rec("ADJ-append-only", "DEFENDED" if (len(log) == 2 and log.records[0].actor == "op_1") else "BREACH", "NONE",
    f"2nd adjustment -> log len={len(log)}, first record untouched (actor={log.records[0].actor}); AdjustmentLog append-only")

# actor masked on export
r0 = log.records[0]
rec("ADJ-actor-masked", "DEFENDED" if r0.to_public()["actor"] != r0.actor else "BREACH", "M6-FAIL-008",
    f"AdjustmentRecord.to_public masks actor (raw!={r0.to_public()['actor']}) (adjustment.py:32-43; -> M6-P1406)")

# EMPTY required fields accepted (no non-empty validation) -> accountability gap, not a mutation
log2 = AdjustmentLog()
mat.request_adjustment("evt_adj", actor="", reason="", audit_ref="", evidence_ref="", proposed={}, adjustment_log=log2)
row_after2 = store.get_by_event_id("evt_adj").revenue_value
rec("ADJ-empty-fields", "OPEN_NONGATE" if len(log2) == 1 else "DEFENDED", "NONE",
    f"request_adjustment with EMPTY actor/reason/audit_ref/evidence_ref -> recorded={len(log2) == 1}; no non-empty "
    f"validation (materializer.py:118-127) -> a vacuous accountability record (RULE-008 nominally 'has' the fields). "
    f"Row still immutable (revenue={row_after2}) so NOT a FAIL-004 override; a DQ/accountability gap. Fix: require non-empty.")

# =================================================================================================
# GROUP COMM — no commission / no core override (M6-FAIL-004 / RULE-019 / RULE-018)
# =================================================================================================
# diamond/referral RECORDED into the attribution context, NO commission computed/field
ctx = AttributionResolver().resolve(mk_event("evt_dia"), mk_conv(src="evt_dia"),
                                    signals={"referral_link_id": "rl_1", "diamond_id": "dm_1"})
pub = ctx.to_public()
has_commission = any("commission" in k.lower() for k in pub) or hasattr(ctx, "commission_value")
rec("COMM-diamond-recorded", "DEFENDED" if (pub.get("referral_link_id") == "rl_1" and pub.get("diamond_id") == "dm_1"
    and not has_commission) else "BREACH", "M6-FAIL-004",
    f"referral/diamond recorded (referral={pub.get('referral_link_id')}, diamond={pub.get('diamond_id')}); commission field/computation={has_commission} "
    f"(RULE-019: recorded only, Finance owns commission)")

# proposed can carry a caller-supplied commission-ish key -> RECORDED (echoed) but NOT computed/applied
log3 = AdjustmentLog()
mat.request_adjustment("evt_adj", actor="op", reason="r", audit_ref="a", evidence_ref="e",
                       proposed={"commission_value": 5000}, adjustment_log=log3)
rec("COMM-proposed-echo", "NOTE", "NONE",
    f"request_adjustment(proposed={{commission_value:5000}}) -> stored in the record's proposed={dict(log3.records[0].proposed)} "
    f"but NEVER computed/applied to any row; the module records a caller ASSERTION, it does not compute commission "
    f"(RULE-019 holds). proposed has no field allow-list -> M6-P1406 hardening note.")

# sweep the attribution modules + store for commission / order-state / quote / CRM / pricing / network primitives
FORBIDDEN = {"commission", "socket", "requests", "urllib", "httpx", "psycopg", "sqlalchemy", "cursor", "execute", "executemany"}
# actual override/commission ACTION verbs (NOT the fail-closed check `is_scale_evidence_eligible`, which merely
# GATES scale evidence and is the defence, not an action).
DEF_DANGER = ("commission", "order_state", "write_order", "quote_snapshot", "crm_send", "set_price",
              "raise_budget", "enable_campaign", "publish_optim", "golden_hour_override")
hits = []; def_hits = []
for rel in ("measurement/attribution/resolver.py", "measurement/attribution/materializer.py",
            "measurement/attribution/adjustment.py", "measurement/models/attribution_context.py",
            "measurement/store/measurement_event_store.py"):
    with open(os.path.join(IMPL, "app", rel), "r", encoding="utf-8") as f:
        src = f.read()
    names = set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.NAME:
                names.add(tok.string)
    except tokenize.TokenError:
        pass
    for h in names & FORBIDDEN:
        hits.append(f"{os.path.basename(rel)}:{h}")
    import re as _re
    for m in _re.finditer(r"^\s*def\s+(\w+)", src, _re.M):
        if any(d in m.group(1).lower() for d in DEF_DANGER):
            def_hits.append(f"{os.path.basename(rel)}:{m.group(1)}")
rec("COMM-sweep", "DEFENDED" if not hits and not def_hits else "BREACH", "M6-FAIL-004",
    f"attribution-layer code identifiers in {{commission/order/quote/crm/pricing/network/db}} = {hits or 'NONE'}; "
    f"danger def names = {def_hits or 'NONE'} (no commission math, no Core/order/quote/CRM write)")

# =================================================================================================
# GROUP FF — RE-VERIFY F-D / F-E / F-F (carried; claimed closed Round 2)
# =================================================================================================
CONSENT = {
    "cs_self": ConsentSnapshot("cs_self", "cust_self", ConsentState.VALID, TS, frozenset({ConsentScope.EXTERNAL_MEASUREMENT})),
    "cs_other": ConsentSnapshot("cs_other", "someone_else", ConsentState.VALID, TS, frozenset({ConsentScope.EXTERNAL_MEASUREMENT})),
}
def conv_deps(reader):
    return ConversionDeps(validator=EventValidator(Reg(), AuditLog()), conversion_store=ConversionEventStore(),
                          measurement_outbox=OutboxStore(), audit=AuditLog(), max_retries=3, consent_reader=reader)
def conv_body(**over):
    b = {"event_code": "ORDER_VERIFIED", "source_event_id": "e", "customer_or_guest_key": "cust_self",
         "consent_snapshot_id": "cs_self", "occurred_at": "2026-07-29T12:00:00+00:00", "idempotency_key": "k",
         "correlation_id": "c", "order_code": "ORD"}
    b.update(over); return b
rdr = InMemoryConsentReader(snapshots=CONSENT, current={"cust_self": ConsentState.VALID})
# borrowed: customer=cust_self but consent subject someone_else -> REJECTED
r_borrow = handle_conversions_request(conv_body(consent_snapshot_id="cs_other"), conv_deps(rdr))
# matching -> CREATED
r_match = handle_conversions_request(conv_body(), conv_deps(rdr))
# None reader -> REJECTED (fails closed)
r_noread = handle_conversions_request(conv_body(), conv_deps(None))
fd_ok = (r_borrow.status == "REJECTED" and r_borrow.error_code == "CONSENT_MISSING_OR_INVALID"
         and r_match.status == "CREATED" and r_noread.status == "REJECTED")
rec("FF-F-D-borrowed", "DEFENDED" if fd_ok else "BREACH", "M6-FAIL-002",
    f"borrowed consent -> {r_borrow.status}/{r_borrow.error_code}; matching -> {r_match.status}; None reader -> {r_noread.status} "
    f"(conversions.py:96-108 mandatory bind) — F-D CLOSED")

# F-E: platform_event_id now injective (escapes the join)
fe_ok = platform_event_id("a", "b|c") != platform_event_id("a|b", "c")
rec("FF-F-E-injective", "DEFENDED" if fe_ok else "BREACH", "M6-FAIL-001",
    f"platform_event_id('a','b|c') != ('a|b','c') = {fe_ok} (payload.py escapes the join) — F-E CLOSED (M6.2A MAJOR-5 class)")

# F-F: safe_subject_ref survives a raising subject_ref property + a str-subclass; dispatcher run_once does not crash
class _RaiseSubj:
    consent_state = ConsentState.VALID
    @property
    def subject_ref(self): raise RuntimeError("hostile subject_ref")
class _SubStr(str): pass
class _SubclassSnap:
    consent_state = ConsentState.VALID
    subject_ref = _SubStr("x")
r1 = safe_subject_ref(_RaiseSubj()); r2 = safe_subject_ref(_SubclassSnap())
class _RaiseReader:
    def get(self, cid): return _RaiseSubj()
    def current_state(self, s): return ConsentState.VALID
au = AuditLog(); cstore = ConversionEventStore()
conv = ConversionEvent(conversion_id="c1", event_code="ORDER_VERIFIED", source_event_id="s", correlation_id="c",
                       customer_or_guest_key="cust_self", consent_snapshot_id="cs_x", occurred_at=TS, idempotency_key="ik")
cstore.create(conv); outbox = OutboxStore(); enqueue_measurement(conv, outbox, max_retries=3)
try:
    MeasurementDispatcher(outbox, StagedPlatformTransport(cstore, PlatformResultLog()), ConsentGate(au),
                          _RaiseReader(), au, dq_status=lambda i: "PASS").run_once(now=NOW)
    disp = ("RESULT", outbox.all()[0].status.value)
except Exception as e:  # noqa: BLE001
    disp = ("RAISE", type(e).__name__)
ff_ok = (r1 is None and r2 is None and disp[0] == "RESULT")
rec("FF-F-F-safesubj", "DEFENDED" if ff_ok else "BREACH", "M6-FAIL-002",
    f"safe_subject_ref(raising-property)={r1}, (str-subclass)={r2}; dispatcher run_once with a hostile snapshot -> {disp} "
    f"(transport.safe_subject_ref type() is str; measurement_dispatcher.py:84) — F-F CLOSED")

# =================================================================================================
# GROUP OVR — posture / PII observation
# =================================================================================================
posture = (cfg.GLOBAL_GATEWAY_STATE == "BLOCKED" and cfg.PRODUCTION_FLAG == "OFF" and cfg.EXTERNAL_SEND == "OFF"
           and cfg.HASH_POLICY_RATIFIED is False and cfg.SCALE_MODEL_RATIFIED is False)
rec("OVR-posture", "DEFENDED" if posture else "BREACH", "M6-FAIL-004",
    f"(gateway,prod,ext_send,hash_ratified,scale_ratified)=({cfg.GLOBAL_GATEWAY_STATE},{cfg.PRODUCTION_FLAG},"
    f"{cfg.EXTERNAL_SEND},{cfg.HASH_POLICY_RATIFIED},{cfg.SCALE_MODEL_RATIFIED})")

# psid masked on export, raw kept durably in as_stored
ctx = AttributionResolver().resolve(mk_event("evt_ps", live_session_id="ls"), mk_conv(src="evt_ps"),
                                    signals={"psid": "psid_" + "".join(str((i * 3) % 10) for i in range(10))})
pub_psid = ctx.to_public()["psid"]; stored_psid = ctx.as_stored()["psid"]
rec("OVR-psid", "NOTE", "NONE",
    f"psid masked on export (to_public psid != raw = {pub_psid != ctx.psid}); as_stored keeps raw ({stored_psid == ctx.psid}) "
    f"for durable trace joins -> PII-in-durable-store is M6-P1406 / M6-OD-012 scope, not FAIL-001/004")

# =================================================================================================
# GROUP W — vectors surfaced by the adversarial-ideation workflow (executed to confirm/refute)
# =================================================================================================
# W-ADJ2: request_adjustment does NOT check the event exists / is verified -> a record against an unknown event
log_u = AdjustmentLog()
mat_u = AttributionMaterializer(MeasurementEventStore(), AttributionResolver(), AuditLog())
mat_u.request_adjustment("no_such_event", actor="op", reason="r", audit_ref="a", evidence_ref="e",
                         proposed={"revenue_value": 1.0}, adjustment_log=log_u)
rec("W-ADJ2-noexist", "OPEN_NONGATE" if len(log_u) == 1 else "DEFENDED", "NONE",
    f"request_adjustment('no_such_event',...) -> recorded={len(log_u) == 1}; the adjustment path never checks the "
    f"event exists or is verified (materializer.py:103-134). No mutation (there is no row) -> not a FAIL-004 override; "
    f"same accountability-gap class as F-G. Fix: assert the target row exists AND is verified before recording.")

# W-ADJ6: AdjustmentRecord is frozen but its `proposed` is a plain mutable dict -> post-hoc mutable after append
log_m = AdjustmentLog()
mat_u.request_adjustment("evt_adj", actor="op", reason="r", audit_ref="a", evidence_ref="e", proposed={"revenue_value": 1.0}, adjustment_log=log_m)
log_m.records[0].proposed["injected"] = 999
mutated = "injected" in log_m.records[0].proposed
rec("W-ADJ6-mutable", "OPEN_NONGATE" if mutated else "DEFENDED", "NONE",
    f"AdjustmentRecord is frozen but proposed is a plain dict -> post-append mutation of records[0].proposed succeeded={mutated} "
    f"(adjustment.py:29). The append-only LOG is immutable but a record's `proposed` contents are not (frozen guards the "
    f"field binding, not the dict). No row is mutated -> not FAIL-004; an immutability-completeness gap. Fix: store a MappingProxyType / re-copy on read.")

# W-REV7: the materializer trusts its `verified_event_codes` ctor arg; a MIS-WIRED instance books non-verified revenue
ev = mk_event("evt_mw", event_code="VIEW_LANDING")
store = MeasurementEventStore(); store.insert(ev)
mat_mw = AttributionMaterializer(store, AttributionResolver(), AuditLog(), verified_event_codes=("VIEW_LANDING",))
oc_mw = mat_mw.materialize(ev, mk_conv("VIEW_LANDING", src="evt_mw", revenue_value=500000.0, order_code="ORD"))
rec("W-REV7-miswire", "NOTE", "NONE",
    f"materializer(verified_event_codes=('VIEW_LANDING',)) books revenue for VIEW_LANDING -> revenue={oc_mw.revenue_value}; "
    f"the DEFAULT is ('ORDER_VERIFIED',) (materializer.py:47) which is correct. verified_event_codes is a CONSTRUCTOR arg "
    f"(not channel input) -> a mis-wired assembler could book non-verified revenue: an assembly/wiring risk, not "
    f"channel-reachable -> not a live FAIL-001; owner/CODER wiring discipline note.")

# W-REV8: NaN revenue breaks the set-once idempotent replay (NaN != NaN -> an honest replay RAISES instead of no-op)
ev = mk_event("evt_nan", campaign_id="c", adset_id="a", ad_id="d")
store = MeasurementEventStore(); store.insert(ev)
mat_n = AttributionMaterializer(store, AttributionResolver(), AuditLog())
mat_n.materialize(ev, mk_conv(src="evt_nan", order_code="ORD", revenue_value=float("nan")))
try:
    mat_n.materialize(ev, mk_conv(src="evt_nan", order_code="ORD", revenue_value=float("nan")))
    nan_replay = "no-op"
except MeasurementStoreViolation:
    nan_replay = "raised"
rec("W-REV8-nan", "NOTE", "NONE",
    f"a verified NaN revenue re-materialized identically -> {nan_replay} (NaN != NaN, so the set-once 'same?' check "
    f"(measurement_event_store.py:90-96) treats an honest replay as a DIFFERENT value and raises). Root cause is NaN/Inf "
    f"revenue itself (the M6.2D O-4 DQ gap) -> M6.2F DQ checker / M6-P1406 should reject non-finite revenue; not a FAIL-001 over-count.")

# =================================================================================================
# SUMMARY
# =================================================================================================
from collections import Counter
cnt = Counter(s for _, s, _, _ in OUT)
breaches = [pid for pid, s, g, d in OUT if s == "BREACH"]
opens = [pid for pid, s, g, d in OUT if s == "OPEN_NONGATE"]
print("=" * 104)
print("SUMMARY:", dict(cnt))
print("IN-SCOPE FAIL-GATE BREACHES (FAIL-001/004):", breaches or "NONE")
print("OPEN (real defect, does NOT trip an in-scope fail gate):", opens or "NONE")
print("TOTAL RECORDED OUTCOMES:", len(OUT))
print("=" * 104)
