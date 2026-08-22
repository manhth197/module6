"""M6-P1305 BOUNDARY ADVERSARY — executed attacks vs FROZEN staged M6.2D send-discipline layer.

Read-only: imports the staged package from 04-artifacts/impl/M6.2D and drives the real seams (hash policy,
payload builder, StagedPlatformTransport, PlatformResultLog, the consent dispatchers, the conversions endpoint).
Writes NOTHING (sys.dont_write_bytecode=True; run with -B). No network, no DB, no flag flip persists. One
structured line per attack; a SUMMARY last. No attacker/PII value is EVER echoed — PII-shaped probes are built
programmatically and only booleans/ids/hash-prefixes are printed.

Status vocabulary:
  DEFENDED     attack blocked as required (no raw PII; no offline/revenue misuse; consent/dedup hold)
  BREACH       an IN-SCOPE fail gate (M6-FAIL-001 / 002 / 008) is actually tripped  (expect 0)
  OPEN_NONGATE a real defect that does NOT trip an in-scope fail gate (armed-not-fired; needs hostile input)
  CONTROL      non-vacuity control
  NOTE         observation for the owner / routed to M6-P1306
"""
from __future__ import annotations

import sys
import os
import io
import tokenize
from datetime import datetime, timezone
from types import SimpleNamespace

sys.dont_write_bytecode = True
IMPL = r"D:\M6\Module6-workspace\04-artifacts\impl\M6.2D"
sys.path.insert(0, IMPL)

from app import config as cfg
from app.measurement.audit import AuditLog
from app.measurement.consent.gate import ConsentGate
from app.measurement.registry.validator import EventValidator
from app.measurement.adapters.consent_reader import InMemoryConsentReader
from app.measurement.outbox.outbox_store import OutboxStore
from app.measurement.outbox.enqueue import enqueue_measurement, enqueue_audience_sync
from app.measurement.outbox.measurement_dispatcher import MeasurementDispatcher
from app.measurement.outbox.audience_dispatcher import AudienceDispatcher
from app.measurement.outbox.transport import ExternalSendBlocked
from app.measurement.integration.hash_policy import to_public_safe, hash_identity
from app.measurement.integration.payload import build_platform_payload, platform_event_id, PlatformPayload
from app.measurement.integration.platform_transport import StagedPlatformTransport, OfflineNotVerified
from app.measurement.integration.result_log import PlatformResultLog, SendResult
from app.measurement.models.measurement_outbox import MeasurementOutboxItem, MeasurementPlatform, OutboxStatus
from app.measurement.models.audience_outbox import AudienceOperation, AudiencePlatform
from app.measurement.models.conversion_event import ConversionEvent
from app.measurement.models.segments import ApprovalState, CustomerSegment, SegmentMember
from app.measurement.adapters.segment_reader import InMemorySegmentReader
from app.measurement.models.consumed import (
    ConsentScope, ConsentSnapshot, ConsentState, DataSensitivity, EventRegistryRow, RegistrationState,
)
from app.measurement.store.conversion_event_store import ConversionEventStore
from app.api.conversions import handle_conversions_request, ConversionDeps

NOW = datetime(2026, 7, 30, 12, 0, 0, tzinfo=timezone.utc)
TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
OUT = []


def rec(pid, status, gate, detail):
    OUT.append((pid, status, gate, detail))
    print(f"[{pid:<18}] {status:<12} gate={gate:<11} :: {detail}")


REG = {
    "VIEW_LANDING": EventRegistryRow("VIEW_LANDING", RegistrationState.ACTIVE, owner="core.tracking",
                                     data_sensitivity=DataSensitivity.INTERNAL),
    "ORDER_VERIFIED": EventRegistryRow("ORDER_VERIFIED", RegistrationState.ACTIVE, owner="core.tracking",
                                       data_sensitivity=DataSensitivity.INTERNAL),
}
class Reg:
    def get(self, code): return REG.get(code)

CONSENT = {
    "cs_valid": ConsentSnapshot("cs_valid", "guest_mapped_ok", ConsentState.VALID, TS,
                                frozenset({ConsentScope.EXTERNAL_MEASUREMENT, ConsentScope.AUDIENCE_SYNC})),
    "cs_missing": ConsentSnapshot("cs_missing", "guest_x", ConsentState.MISSING, TS, frozenset()),
    "cs_optout": ConsentSnapshot("cs_optout", "guest_x", ConsentState.OPT_OUT, TS, frozenset()),
    "cs_mem_consented": ConsentSnapshot("cs_mem_consented", "mem_consented", ConsentState.VALID, TS,
                                        frozenset({ConsentScope.AUDIENCE_SYNC})),
    "cs_mem_optout": ConsentSnapshot("cs_mem_optout", "mem_optout", ConsentState.OPT_OUT, TS, frozenset()),
}
CUR = {"guest_mapped_ok": ConsentState.VALID, "mem_consented": ConsentState.VALID}


def reader(current=None, snaps=None):
    return InMemoryConsentReader(snapshots=snaps or CONSENT, current=current or CUR)


def mk_conv(event_code="VIEW_LANDING", *, cs="cs_valid", cust="guest_mapped_ok", src="evt_src"):
    return ConversionEvent(conversion_id=f"conv_{event_code}_{src}", event_code=event_code, source_event_id=src,
                           correlation_id="corr_c", customer_or_guest_key=cust, consent_snapshot_id=cs,
                           occurred_at=TS, idempotency_key=f"idem_{event_code}_{src}")


# PII-shaped probes constructed programmatically (never a literal; never echoed)
PHONE = "0" + "".join(str((i * 7 + 3) % 10) for i in range(9))          # VN mobile shape
EMAIL = "u" + chr(64) + "h" + "." + "xx"                                 # email shape
RAWID = "psid_" + "".join(str((i * 3) % 10) for i in range(12))          # raw platform id shape
PII_PROBES = {"phone": PHONE, "email": EMAIL, "psid": RAWID}


def dispatch_conv(conv, *, rdr, dq="PASS", platforms=None):
    au = AuditLog(); cstore = ConversionEventStore(); cstore.create(conv)
    outbox = OutboxStore(); enqueue_measurement(conv, outbox, max_retries=3, platforms=platforms)
    rlog = PlatformResultLog(); transport = StagedPlatformTransport(cstore, rlog)
    MeasurementDispatcher(outbox, transport, ConsentGate(au), rdr, au, dq_status=lambda i: dq).run_once(now=NOW)
    return outbox, rlog, au, cstore


print("=" * 104)
print("M6-P1305 — executed boundary attacks vs FROZEN M6.2D send-discipline (py", sys.version.split()[0], ")")
print("=" * 104)

# =================================================================================================
# GROUP PII — RAW PII in the payload / result log (M6-FAIL-008 / RULE-014, SMK-017)
# =================================================================================================
# every raw-PII identity is HASHED in the payload; the raw value never appears
leaks = 0
for shape, probe in PII_PROBES.items():
    payload = build_platform_payload(mk_conv(cust=probe), MeasurementPlatform.PIXEL)
    ident = payload.user_data.get("identity", "")
    raw_present = (probe in ident) or (probe in payload.event_id) or (probe in str(payload.platform))
    if not ident.startswith("h_") or raw_present:
        leaks += 1
rec("PII-payload-hash", "DEFENDED" if leaks == 0 else "BREACH", "M6-FAIL-008",
    f"3 PII shapes (phone/email/psid) as customer_or_guest_key -> user_data hashed (h_), raw absent; leaks={leaks}/3 "
    f"(payload.py:39 -> hash_policy.to_public_safe)")

# force HASH_POLICY_RATIFIED=True -> to_public_safe STILL hashes (empty _RAW_ALLOWED_FIELDS): doubly fail-closed
_orig_ratified = cfg.HASH_POLICY_RATIFIED
try:
    cfg.HASH_POLICY_RATIFIED = True
    out = to_public_safe({"identity": PHONE, "email": EMAIL})
    still_hashed = all(v.startswith("h_") for v in out.values()) and PHONE not in str(out) and EMAIL not in str(out)
finally:
    cfg.HASH_POLICY_RATIFIED = _orig_ratified
rec("PII-force-ratified", "DEFENDED" if still_hashed else "BREACH", "M6-FAIL-008",
    f"force HASH_POLICY_RATIFIED=True -> every field still hashed={still_hashed} (empty allow-list; hash_policy.py:33)")

# the platform RESULT LOG stores NO raw PII (no user_data field at all)
outbox, rlog, au, cstore = dispatch_conv(mk_conv(cust=PHONE), rdr=reader())
rlog_raw = any(PHONE in str(vars(r)) for r in rlog.records)
has_userdata = any(hasattr(r, "user_data") for r in rlog.records)
rec("PII-resultlog-safe", "DEFENDED" if (not rlog_raw and not has_userdata) else "BREACH", "M6-FAIL-008",
    f"result log records ({len(rlog)}) contain raw PII={rlog_raw}, expose user_data={has_userdata} "
    f"(result_log.py:22-29: platform/event_id/event_name/dedup_key/result only)")

# hash properties: deterministic, one-way (out != in), distinct -> distinct
h1 = hash_identity(PHONE); h2 = hash_identity(PHONE); h3 = hash_identity(EMAIL)
rec("PII-hash-props", "DEFENDED" if (h1 == h2 and h1 != h3 and PHONE not in h1) else "BREACH", "NONE",
    f"hash_identity deterministic={h1==h2}, distinct-inputs-distinct={h1!=h3}, one-way(out!=in)={PHONE not in h1}")

# payload has only {platform, event_name(registry), event_id(hash), user_data(hashed)} -- enumerate
p = build_platform_payload(mk_conv(cust=PHONE), MeasurementPlatform.CAPI)
fields = set(PlatformPayload.__dataclass_fields__.keys())
rec("PII-payload-fields", "DEFENDED" if (fields == {"platform", "event_name", "event_id", "user_data"}
    and p.event_name == "VIEW_LANDING" and all(v.startswith("h_") for v in p.user_data.values())) else "BREACH",
    "M6-FAIL-008", f"PlatformPayload fields={sorted(fields)}; event_name={p.event_name} (registry code, not PII); "
    f"user_data all hashed")

# NOTE: unsalted sha256 hash of a low-entropy identity is brute-forceable, but (a) it is the Meta CAPI matching
# standard and (b) the result log never stores user_data (only the ephemeral payload carries the hash).
rec("PII-unsalted-note", "NOTE", "NONE",
    f"hash_identity is UNSALTED sha256 (config.MEASUREMENT_HASH_ALGO); reversible for low-entropy PII by brute force, "
    f"but that is the platform-matching standard and the result log stores no user_data -> M6-P1306 / M6-OD-003 scope")

# =================================================================================================
# GROUP OFF — OFFLINE / REVENUE only after ORDER_VERIFIED (M6-FAIL-001 / RULE-003)
# =================================================================================================
st_vl = OutboxStore(); rows_vl = enqueue_measurement(mk_conv("VIEW_LANDING"), st_vl, max_retries=3)
st_ov = OutboxStore(); rows_ov = enqueue_measurement(mk_conv("ORDER_VERIFIED", src="evt_ov"), st_ov, max_retries=3)
plat_vl = {it.platform for (it, c) in rows_vl}; plat_ov = {it.platform for (it, c) in rows_ov}
ok = (MeasurementPlatform.OFFLINE not in plat_vl and MeasurementPlatform.OFFLINE in plat_ov)
rec("OFF-fanout", "DEFENDED" if ok else "BREACH", "M6-FAIL-001",
    f"VIEW_LANDING platforms={sorted(x.value for x in plat_vl)} (no OFFLINE); ORDER_VERIFIED={sorted(x.value for x in plat_ov)} "
    f"(OFFLINE only after ORDER_VERIFIED; enqueue.py:80-81)")

# defense-in-depth: force an OFFLINE outbox item for a VIEW_LANDING conversion -> transport raises OfflineNotVerified
conv_vl = mk_conv("VIEW_LANDING", src="evt_forced")
cstore = ConversionEventStore(); cstore.create(conv_vl)
offline_item = MeasurementOutboxItem(outbox_id="mob_x", source_event_id=conv_vl.conversion_id,
                                     platform=MeasurementPlatform.OFFLINE, dedup_key="dkx", idempotency_key="ik",
                                     payload_ref="p", consent_snapshot_id="cs_valid", max_retries=3)
rlog = PlatformResultLog()
try:
    StagedPlatformTransport(cstore, rlog).deliver(offline_item); off_guard = "no-raise"
except OfflineNotVerified:
    off_guard = "OfflineNotVerified"
except ExternalSendBlocked:
    off_guard = "sent-then-blocked"
rec("OFF-transport-guard", "DEFENDED" if off_guard == "OfflineNotVerified" else "BREACH", "M6-FAIL-001",
    f"forced OFFLINE item for a VIEW_LANDING conversion -> {off_guard}, result-log records={len(rlog)} "
    f"(platform_transport.py:41-42 defense-in-depth)")

# revenue only from ORDER_VERIFIED (endpoint)
au = AuditLog(); deps = ConversionDeps(validator=EventValidator(Reg(), au), conversion_store=ConversionEventStore(),
                                       measurement_outbox=OutboxStore(), audit=au, max_retries=3)
r_rev = handle_conversions_request({"event_code": "VIEW_LANDING", "source_event_id": "e", "customer_or_guest_key": "guest_mapped_ok",
                                    "consent_snapshot_id": "cs_valid", "occurred_at": "2026-07-29T12:00:00+00:00",
                                    "idempotency_key": "k", "correlation_id": "c", "revenue_value": 500}, deps)
rec("OFF-revenue", "DEFENDED" if (r_rev.status == "REJECTED" and r_rev.error_code == "REVENUE_NOT_VERIFIED") else "BREACH",
    "M6-FAIL-001", f"revenue on non-ORDER_VERIFIED -> {r_rev.status}/{r_rev.error_code} (conversions.py:102-107)")

# payload carries no revenue field
rec("OFF-no-revenue-payload", "DEFENDED" if not (set(PlatformPayload.__dataclass_fields__) & {"revenue", "revenue_value", "value", "amount"}) else "BREACH",
    "M6-FAIL-001", "PlatformPayload has no revenue/value field (payload.py:24-29)")

# =================================================================================================
# GROUP DD — CROSS-SOURCE DEDUP / no double count (RULE-005 / SMK-003)
# =================================================================================================
conv = mk_conv("ORDER_VERIFIED", src="evt_ov2")
ids = {plat: build_platform_payload(conv, plat).event_id for plat in
       (MeasurementPlatform.PIXEL, MeasurementPlatform.CAPI, MeasurementPlatform.OFFLINE)}
shared = len(set(ids.values())) == 1
rec("DD-shared-eventid", "DEFENDED" if shared else "BREACH", "M6-FAIL-001",
    f"PIXEL/CAPI/OFFLINE of one conversion share event_id={shared} (payload.platform_event_id: no per-platform id -> no platform double count)")

id_a = platform_event_id("srcA", "VIEW_LANDING"); id_b = platform_event_id("srcB", "VIEW_LANDING")
rec("DD-distinct-source", "DEFENDED" if id_a != id_b else "BREACH", "NONE",
    f"distinct source_event_id -> distinct event_id={id_a != id_b}")

# dispatch PIXEL+CAPI of one conversion -> result log has 2 records SHARING one event_id; outbox 2 distinct dedup_key
outbox, rlog, au, cstore = dispatch_conv(mk_conv("VIEW_LANDING", src="evt_dd"), rdr=reader())
recs = rlog.records
one_event = len({r.event_id for r in recs}) == 1 and len(recs) == 2
distinct_internal = len({it.dedup_key for it in outbox.all()}) == 2
rec("DD-resultlog", "DEFENDED" if (one_event and distinct_internal) else "BREACH", "M6-FAIL-001",
    f"dispatch PIXEL+CAPI -> {len(recs)} result records sharing one event_id={one_event}; outbox distinct dedup_key={distinct_internal} "
    f"(platform-side dedup, no double count)")

# OBSERVATION: event_id excludes customer_or_guest_key -> same source_event_id+event_code, different customer, collide
id_c1 = build_platform_payload(mk_conv("VIEW_LANDING", cust="custA", src="shared_src"), MeasurementPlatform.PIXEL).event_id
id_c2 = build_platform_payload(mk_conv("VIEW_LANDING", cust="custB", src="shared_src"), MeasurementPlatform.PIXEL).event_id
rec("DD-source-collision", "NOTE", "NONE",
    f"same source_event_id+event_code, DIFFERENT customer -> same event_id={id_c1 == id_c2}; platform would collapse two "
    f"distinct customers -> UNDER-count (DQ, not FAIL-001 over-count); needs a reused source_event_id -> M6-P1306/DQ")

# =================================================================================================
# GROUP FF — FIX-FIRST RE-VERIFY (F-A / F-B / F-C)
# =================================================================================================
class CurrentStateRaises(InMemoryConsentReader):
    def current_state(self, subj): raise RuntimeError("consent store down at send")

# F-A measurement: current_state raises -> CONSENT deny, no crash, batch not aborted (2 items both processed)
au = AuditLog(); cstore = ConversionEventStore()
c1 = mk_conv("VIEW_LANDING", src="a"); c2 = mk_conv("VIEW_LANDING", src="b")
cstore.create(c1); cstore.create(c2)
outbox = OutboxStore(); enqueue_measurement(c1, outbox, max_retries=3); enqueue_measurement(c2, outbox, max_retries=3)
rlog = PlatformResultLog()
try:
    MeasurementDispatcher(outbox, StagedPlatformTransport(cstore, rlog), ConsentGate(au),
                          CurrentStateRaises(snapshots=CONSENT, current=CUR), au, dq_status=lambda i: "PASS").run_once(now=NOW)
    fa = ("RESULT", sum(1 for it in outbox.all() if it.status is OutboxStatus.DEAD_LETTER), len(rlog))
except Exception as e:  # noqa: BLE001
    fa = ("RAISE", type(e).__name__)
rec("FF-F-A-meas", "DEFENDED" if fa[0] == "RESULT" and fa[1] == 4 and fa[2] == 0 else "BREACH", "M6-FAIL-002",
    f"current_state raises on a 4-item batch -> {fa} (all DEAD_LETTER, 0 payloads); permits_send wrapped "
    f"(measurement_dispatcher.py:84-89) — F-A closed, batch not aborted")

# F-A audience: current_state raises on an ADD -> CONSENT deny, no crash
au = AuditLog(); store = OutboxStore()
segs = {"seg": CustomerSegment("seg", "S", ApprovalState.APPROVED)}
mems = {"seg": [SegmentMember("seg", "mem_consented", "cs_mem_consented")]}
enqueue_audience_sync("seg", reader=InMemorySegmentReader(segments=segs, members=mems), consent_reader=reader(),
                      consent_gate=ConsentGate(au), store=store, audit=au, platform=AudiencePlatform.META_AUDIENCE, max_retries=3)
try:
    AudienceDispatcher(store, StagedPlatformTransport(ConversionEventStore(), PlatformResultLog()), ConsentGate(au),
                       CurrentStateRaises(snapshots=CONSENT, current=CUR), au).run_once(now=NOW)
    faa = ("RESULT", store.all()[0].status.value)
except Exception as e:  # noqa: BLE001
    faa = ("RAISE", type(e).__name__)
rec("FF-F-A-aud", "DEFENDED" if faa[0] == "RESULT" else "BREACH", "M6-FAIL-002",
    f"audience current_state raises -> {faa} (audience_dispatcher.py:82-88 wraps permits_send) — F-A closed")

# F-B: a lying set-subclass consent_scope -> gate.evaluate now False (frozenset materialization)
class _LyingSet(set):
    def __contains__(self, x): return True
class _Unhardened(ConsentSnapshot):
    def __post_init__(self): pass
evil = _Unhardened("cs_lie", "guest_mapped_ok", ConsentState.VALID, TS, _LyingSet())
g_lie = ConsentGate(AuditLog()).evaluate(evil, ConsentScope.EXTERNAL_MEASUREMENT)
rec("FF-F-B-lyingset", "DEFENDED" if g_lie is False else "BREACH", "M6-FAIL-002",
    f"lying set-subclass consent_scope -> gate.evaluate={g_lie} (gate.py:73 frozenset membership) — F-B closed")

# F-C audience: a member whose consent subject != member_key -> REMOVE at enqueue
au = AuditLog(); store = OutboxStore()
mems_bad = {"seg": [SegmentMember("seg", "mem_victim", "cs_valid")]}   # cs_valid.subject_ref=guest_mapped_ok != mem_victim
rows = enqueue_audience_sync("seg", reader=InMemorySegmentReader(segments=segs, members=mems_bad), consent_reader=reader(),
                             consent_gate=ConsentGate(au), store=store, audit=au, platform=AudiencePlatform.META_AUDIENCE, max_retries=3)
fc = rows[0][0].operation is AudienceOperation.REMOVE
rec("FF-F-C-audience", "DEFENDED" if fc else "BREACH", "M6-FAIL-002",
    f"audience member bound to ANOTHER subject's consent -> operation={rows[0][0].operation.value} "
    f"(enqueue.py:131-135 subject_ref==member_key) — F-C closed (borrowed-consent audience fixed)")

# =================================================================================================
# GROUP MBC — MEASUREMENT-PATH BORROWED CONSENT (coder-flagged sec.4.3; confirm open)
# =================================================================================================
# POST a conversion: customer = a NON-consented victim, consent ref = ANOTHER subject's VALID consent
au = AuditLog(); cstore = ConversionEventStore(); outbox = OutboxStore()
deps = ConversionDeps(validator=EventValidator(Reg(), au), conversion_store=cstore, measurement_outbox=outbox, audit=au, max_retries=3)
body = {"event_code": "VIEW_LANDING", "source_event_id": "evt_borrow", "customer_or_guest_key": "victim_no_consent",
        "consent_snapshot_id": "cs_valid", "occurred_at": "2026-07-29T12:00:00+00:00", "idempotency_key": "kb", "correlation_id": "cb"}
res = handle_conversions_request(body, deps)
rlog = PlatformResultLog()
MeasurementDispatcher(outbox, StagedPlatformTransport(cstore, rlog), ConsentGate(au), reader(current=CUR),
                      au, dq_status=lambda i: "PASS").run_once(now=NOW)
borrowed = (res.status == "CREATED" and len(rlog) >= 1)   # rlog record only if the item passed the consent gate
rec("MBC-endpoint", "OPEN_NONGATE" if borrowed else "DEFENDED", "NONE",
    f"conversion customer='victim' + consent_snapshot_id=ANOTHER subject's VALID consent -> {res.status}, "
    f"payloads built + result-log records={len(rlog)} (BORROWED consent: the victim's measurement reached the payload "
    f"build on someone else's consent). conversions.py:82-123 + measurement_dispatcher.py:76-92 never bind "
    f"customer_or_guest_key to snap.subject_ref (the F-C audience fix was NOT applied to the measurement path; "
    f"coder-flagged sec.4.3). Armed-not-fired: StagedPlatformTransport blocks the real send. REACHABLE from the "
    f"untrusted conversions body. Fix: bind customer_or_guest_key to snap.subject_ref (mirror F-C).")

# control: a genuinely non-consented conversion -> SEND_BLOCKED_CONSENT, NO payload/result-log record
au = AuditLog(); cstore = ConversionEventStore(); outbox = OutboxStore()
deps = ConversionDeps(validator=EventValidator(Reg(), au), conversion_store=cstore, measurement_outbox=outbox, audit=au, max_retries=3)
handle_conversions_request(dict(body, consent_snapshot_id="cs_missing", customer_or_guest_key="guest_x", source_event_id="evt_nc", idempotency_key="knc"), deps)
rlog2 = PlatformResultLog()
MeasurementDispatcher(outbox, StagedPlatformTransport(cstore, rlog2), ConsentGate(au), reader(current=CUR),
                      au, dq_status=lambda i: "PASS").run_once(now=NOW)
blocked = (len(rlog2) == 0 and all(it.status is OutboxStatus.DEAD_LETTER for it in outbox.all())
           and any(x.reason == "SEND_BLOCKED_CONSENT" for x in au.records))
rec("MBC-control-blocked", "DEFENDED" if blocked else "BREACH", "M6-FAIL-002",
    f"genuinely non-consented (cs_missing) -> DEAD_LETTER, result-log records={len(rlog2)}, SEND_BLOCKED_CONSENT "
    f"(consent-blocked item builds NO payload) — the borrowed-consent bypass is cross-subject VALID consent, not a blanket pass")

# =================================================================================================
# GROUP OVR — STAGED NO-REAL-SEND / POSTURE
# =================================================================================================
posture = (cfg.GLOBAL_GATEWAY_STATE == "BLOCKED" and cfg.PRODUCTION_FLAG == "OFF" and cfg.EXTERNAL_SEND == "OFF"
           and cfg.is_external_send_enabled() is False)
rec("OVR-posture", "DEFENDED" if posture else "BREACH", "M6-FAIL-009",
    f"(gateway,prod,ext_send,enabled)=({cfg.GLOBAL_GATEWAY_STATE},{cfg.PRODUCTION_FLAG},{cfg.EXTERNAL_SEND},{cfg.is_external_send_enabled()})")

# consent-blocked item builds NO payload (ties FAIL-002 to no external artifact) — already in MBC-control; also missing directly
outbox, rlog, au, cstore = dispatch_conv(mk_conv(cs="cs_optout", cust="guest_x", src="evt_oo"), rdr=reader())
rec("OVR-consent-no-payload", "DEFENDED" if len(rlog) == 0 else "BREACH", "M6-FAIL-002",
    f"opt-out consent -> result-log records={len(rlog)} (transport never called; no payload built)")

# force EXTERNAL_SEND=ON -> transport records WOULD_SEND + returns (no raise) BUT there is no connector/network code
_orig = cfg.EXTERNAL_SEND
try:
    cfg.EXTERNAL_SEND = "ON"
    cstore = ConversionEventStore(); cstore.create(mk_conv(src="evt_on")); rlog = PlatformResultLog()
    item = enqueue_measurement(mk_conv(src="evt_on"), OutboxStore(), max_retries=3)[0][0]
    try:
        StagedPlatformTransport(cstore, rlog).deliver(item); forced = "returned"
    except ExternalSendBlocked:
        forced = "blocked"
    would = rlog.records[0].result if rlog.records else None
finally:
    cfg.EXTERNAL_SEND = _orig
rec("OVR-force-on", "NOTE", "NONE",
    f"force EXTERNAL_SEND=ON -> transport {forced}, result={would.value if would else None} (marks WOULD_SEND, no raise); "
    f"but NO connector/network code exists (line 56 is a comment) -> nothing is actually transmitted. The real hard lock "
    f"is the connector absence (M6-OD-004), verified by the sweep below.")

# tokenizer sweep: no network/db primitives across M6.2D app (incl. the integration layer)
NET_DB = {"socket", "requests", "urllib", "httpx", "aiohttp", "smtplib", "websocket", "boto3", "kafka",
          "psycopg", "psycopg2", "pymysql", "sqlalchemy", "create_engine", "executemany", "cursor", "urlopen"}
net_hits = []
for root, _dd, files in os.walk(os.path.join(IMPL, "app")):
    for fn in files:
        if not fn.endswith(".py"):
            continue
        with open(os.path.join(root, fn), "r", encoding="utf-8") as f:
            s = f.read()
        names = set()
        try:
            for tok in tokenize.generate_tokens(io.StringIO(s).readline):
                if tok.type == tokenize.NAME:
                    names.add(tok.string)
        except tokenize.TokenError:
            pass
        for hit in names & NET_DB:
            net_hits.append(f"{fn}:{hit}")
rec("OVR-sweep-net", "DEFENDED" if not net_hits else "BREACH", "M6-FAIL-008",
    f"network/db code identifiers across M6.2D app/ = {net_hits or 'NONE'} (no real send exists even if the flag flips)")

# =================================================================================================
# GROUP W — vectors surfaced by the adversarial-ideation workflow (executed to confirm/refute)
# =================================================================================================
# W-eventid-inject: platform_event_id joins with a raw '|' and does NOT escape (unlike enqueue._hash_key)
c1 = platform_event_id("a", "b|c"); c2 = platform_event_id("a|b", "c")
rec("W-eventid-inject", "OPEN_NONGATE" if c1 == c2 else "DEFENDED", "NONE",
    f"platform_event_id('a','b|c')==('a|b','c') -> collision={c1 == c2} (payload.py:21 raw f-string join, no escape, "
    f"unlike enqueue._hash_key which escapes). NOT reachable via the endpoint (event_code is registry-constrained, no "
    f"'|'; a distinct valid (source_event_id,event_code) split cannot be forged) -> latent defense-in-depth "
    f"inconsistency in a key-like formula (the M6.2A MAJOR-5 class), not FAIL-001. Fix: escape/canonicalize like _hash_key.")

# W-subjectref-raise: getattr(snap,'subject_ref',None) at measurement_dispatcher.py:82 is unwrapped for non-AttributeError
class _RaisingSubjSnap:
    consent_state = ConsentState.VALID
    @property
    def subject_ref(self): raise RuntimeError("hostile subject_ref property")
class _RaiseSubjReader:
    def get(self, cid): return _RaisingSubjSnap()
    def current_state(self, s): return ConsentState.VALID
au = AuditLog(); cstore = ConversionEventStore(); conv = mk_conv(src="evt_sr"); cstore.create(conv)
outbox = OutboxStore(); enqueue_measurement(conv, outbox, max_retries=3)
try:
    MeasurementDispatcher(outbox, StagedPlatformTransport(cstore, PlatformResultLog()), ConsentGate(au),
                          _RaiseSubjReader(), au, dq_status=lambda i: "PASS").run_once(now=NOW)
    sr = ("RESULT", outbox.all()[0].status.value)
except Exception as e:  # noqa: BLE001
    sr = ("RAISE", type(e).__name__)
rec("W-subjectref-raise", "OPEN_NONGATE" if sr[0] == "RAISE" else "DEFENDED", "NONE",
    f"snapshot with a subject_ref PROPERTY that raises RuntimeError -> run_once {sr}; getattr(snap,'subject_ref',None) "
    f"(measurement_dispatcher.py:82) only catches AttributeError, so a non-AttributeError escapes (residual F-A nick, "
    f"unwrapped, before the permits_send try/except). No send -> not FAIL-002; needs a hostile consent adapter. Fix: wrap line 82.")

# W-heldlog-growth: a held (ExternalSendBlocked) item is re-drained each run_once, appending a new BLOCKED record
au = AuditLog(); cstore = ConversionEventStore(); conv = mk_conv(src="evt_held"); cstore.create(conv)
outbox = OutboxStore(); enqueue_measurement(conv, outbox, max_retries=3)
rlog = PlatformResultLog()
disp = MeasurementDispatcher(outbox, StagedPlatformTransport(cstore, rlog), ConsentGate(au), reader(), au, dq_status=lambda i: "PASS")
disp.run_once(now=NOW); n1 = len(rlog); disp.run_once(now=NOW); n2 = len(rlog)
rec("W-heldlog-growth", "NOTE", "NONE",
    f"held (ExternalSendBlocked) items re-drained: result-log records {n1}->{n2} over 2 run_once (each drain re-builds the "
    f"PII-safe payload + appends a BLOCKED record). Staged-only (an ON item would SEND, not hold); unbounded growth of "
    f"BLOCKED records is an operational note (result-log/DQ) -> M6.2F/owner, not a gate trip or PII leak.")

# =================================================================================================
# SUMMARY
# =================================================================================================
from collections import Counter
cnt = Counter(s for _, s, _, _ in OUT)
breaches = [pid for pid, s, g, d in OUT if s == "BREACH"]
opens = [pid for pid, s, g, d in OUT if s == "OPEN_NONGATE"]
print("=" * 104)
print("SUMMARY:", dict(cnt))
print("IN-SCOPE FAIL-GATE BREACHES (FAIL-001/002/008):", breaches or "NONE")
print("OPEN (real defect, does NOT trip an in-scope fail gate):", opens or "NONE")
print("TOTAL RECORDED OUTCOMES:", len(OUT))
print("=" * 104)
