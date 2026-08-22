"""M6-P1205 BOUNDARY ADVERSARY — executed attacks vs FROZEN staged M6.2C outbox/consent-egress pipeline.

Read-only: imports the staged package from 04-artifacts/impl/M6.2C and drives the real seams (conversions
endpoint, enqueue seams, both dispatcher workers, the Transport port, the consent gate). Writes NOTHING
(sys.dont_write_bytecode=True; run with -B). No network, no DB, no flag flip. One structured line per attack;
a SUMMARY last. No attacker/PII value is echoed — only ids, statuses, reason codes, booleans.

Status vocabulary:
  DEFENDED     attack blocked as required (no non-consented send; no direct send; bounded retry)
  BREACH       the IN-SCOPE fail gate M6-FAIL-002 (consent violation) is actually tripped  (expect 0)
  OPEN_NONGATE a real defect that does NOT trip M6-FAIL-002 (dispatcher robustness / lost-audit)
  CONTROL      non-vacuity control (the send path CAN reach the transport when consent+DQ are valid)
  NOTE         observation for the owner / routed to M6-P1206
"""
from __future__ import annotations

import sys
import os
import io
import tokenize
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

sys.dont_write_bytecode = True
IMPL = r"D:\M6\Module6-workspace\04-artifacts\impl\M6.2C"
sys.path.insert(0, IMPL)

from app import config as cfg
from app.measurement.audit import AuditLog
from app.measurement.consent.gate import ConsentGate
from app.measurement.registry.validator import EventValidator
from app.measurement.adapters.consent_reader import InMemoryConsentReader
from app.measurement.adapters.segment_reader import InMemorySegmentReader
from app.measurement.outbox.outbox_store import OutboxStore
from app.measurement.outbox.enqueue import enqueue_measurement, enqueue_audience_sync
from app.measurement.outbox.measurement_dispatcher import MeasurementDispatcher
from app.measurement.outbox.audience_dispatcher import AudienceDispatcher
from app.measurement.outbox.transport import StagedBlockedTransport, ExternalSendBlocked, attempt_delivery
from app.measurement.models.measurement_outbox import MeasurementOutboxItem, MeasurementPlatform, OutboxStatus
from app.measurement.models.audience_outbox import AudienceOutboxItem, AudiencePlatform, AudienceOperation
from app.measurement.models.conversion_event import ConversionEvent, DispatchState
from app.measurement.models.segments import ApprovalState, CustomerSegment, SegmentMember
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


# --- seed data / doubles --------------------------------------------------------------------------
REG = {
    "VIEW_LANDING": EventRegistryRow("VIEW_LANDING", RegistrationState.ACTIVE, owner="core.tracking",
                                     data_sensitivity=DataSensitivity.INTERNAL),
    "ORDER_VERIFIED": EventRegistryRow("ORDER_VERIFIED", RegistrationState.ACTIVE, owner="core.tracking",
                                       data_sensitivity=DataSensitivity.INTERNAL),
    "DEREG_SAMPLE": EventRegistryRow("DEREG_SAMPLE", RegistrationState.DEREGISTERED, owner="core.tracking"),
}
CONSENT = {
    "cs_valid": ConsentSnapshot("cs_valid", "guest_mapped_ok", ConsentState.VALID, TS,
                                frozenset({ConsentScope.EXTERNAL_MEASUREMENT, ConsentScope.AUDIENCE_SYNC})),
    "cs_meas_only": ConsentSnapshot("cs_meas_only", "guest_mapped_ok", ConsentState.VALID, TS,
                                    frozenset({ConsentScope.EXTERNAL_MEASUREMENT})),
    "cs_aud_only": ConsentSnapshot("cs_aud_only", "guest_mapped_ok", ConsentState.VALID, TS,
                                   frozenset({ConsentScope.AUDIENCE_SYNC})),
    "cs_missing": ConsentSnapshot("cs_missing", "guest_x", ConsentState.MISSING, TS, frozenset()),
    "cs_expired": ConsentSnapshot("cs_expired", "guest_x", ConsentState.EXPIRED, TS, frozenset()),
    "cs_optout": ConsentSnapshot("cs_optout", "guest_x", ConsentState.OPT_OUT, TS, frozenset()),
}
CUR_VALID = {"guest_mapped_ok": ConsentState.VALID}
CUR_LAPSED = {"guest_mapped_ok": ConsentState.MISSING}   # consent revoked before send


def reader(current=None, snaps=None):
    return InMemoryConsentReader(snapshots=snaps or CONSENT, current=current or CUR_VALID)


class RecordTransport:
    def __init__(self): self.delivered = []
    def deliver(self, item): self.delivered.append(item.outbox_id)


class FailTransport:
    def __init__(self): self.attempts = 0
    def deliver(self, item): self.attempts += 1; raise RuntimeError("simulated transient failure")


class CurrentStateRaises(InMemoryConsentReader):
    def current_state(self, subj): raise RuntimeError("consent store down at send-time")


class DuckNoStateReader:  # get returns a duck lacking consent_state -> evaluate raises AttributeError
    def get(self, cid): return SimpleNamespace(subject_ref="guest_x")
    def current_state(self, subj): return ConsentState.MISSING


def mob(cs_id, *, dedup="dk", max_retries=3, platform=MeasurementPlatform.PIXEL):
    return MeasurementOutboxItem(
        outbox_id="mob_" + dedup, source_event_id="conv_1", platform=platform, dedup_key=dedup,
        idempotency_key="idem_1", payload_ref="conversion:conv_1", consent_snapshot_id=cs_id,
        max_retries=max_retries,
    )


def dispatch_meas(cs_id, *, rdr, dq="PASS", transport=None, snap_reader=None):
    au = AuditLog(); store = OutboxStore(); store.enqueue(mob(cs_id))
    t = transport if transport is not None else RecordTransport()
    disp = MeasurementDispatcher(store, t, ConsentGate(au), snap_reader or rdr, au, dq_status=lambda i: dq)
    disp.run_once(now=NOW)
    return store.all()[0], t, au


print("=" * 104)
print("M6-P1205 — executed boundary attacks vs FROZEN M6.2C outbox pipeline (py", sys.version.split()[0], ")")
print("=" * 104)

# =================================================================================================
# GROUP CM — MEASUREMENT DISPATCH CONSENT (M6-FAIL-002 / RULE-002 checkpoint-2)
# =================================================================================================
for cs, why in [("cs_missing", "MISSING"), ("cs_expired", "EXPIRED"), ("cs_optout", "OPT_OUT")]:
    item, t, au = dispatch_meas(cs, rdr=reader())
    ok = (item.status is OutboxStatus.DEAD_LETTER and not t.delivered
          and any(x.reason == "SEND_BLOCKED_CONSENT" for x in au.records))
    rec(f"CM-{why}", "DEFENDED" if ok else "BREACH", "M6-FAIL-002",
        f"{why} consent -> status={item.status.value}, transport_called={bool(t.delivered)}, SEND_BLOCKED_CONSENT "
        f"(measurement_dispatcher.py:62-71)")

# absent snapshot (reader.get returns None for an unknown id)
item, t, au = dispatch_meas("cs_unknown_id", rdr=reader())
ok = item.status is OutboxStatus.DEAD_LETTER and not t.delivered
rec("CM-absent", "DEFENDED" if ok else "BREACH", "M6-FAIL-002",
    f"absent snapshot -> status={item.status.value}, transport_called={bool(t.delivered)} (gate.py:37 fail-closed)")

# scope isolation: audience-only consent must NOT authorize a MEASUREMENT send
item, t, au = dispatch_meas("cs_aud_only", rdr=reader())
ok = (item.status is OutboxStatus.DEAD_LETTER and not t.delivered
      and any(x.reason == "CONSENT_SCOPE_NOT_GRANTED" for x in au.records))
rec("CM-scope", "DEFENDED" if ok else "BREACH", "M6-FAIL-002",
    f"AUDIENCE_SYNC-only consent for a MEASUREMENT send -> status={item.status.value}, called={bool(t.delivered)}, "
    f"CONSENT_SCOPE_NOT_GRANTED (gate.py:68)")

# consent lapsed between enqueue and dispatch (valid snapshot, current_state now non-VALID)
item, t, au = dispatch_meas("cs_valid", rdr=reader(current=CUR_LAPSED))
ok = (item.status is OutboxStatus.DEAD_LETTER and not t.delivered
      and any(x.reason == "CONSENT_LAPSED_AT_SEND_TIME" for x in au.records))
rec("CM-lapsed", "DEFENDED" if ok else "BREACH", "M6-FAIL-002",
    f"valid snapshot but current_state revoked -> status={item.status.value}, called={bool(t.delivered)}, "
    f"CONSENT_LAPSED_AT_SEND_TIME (gate.py:91-97)")

# data_quality HOLD (staged default) must block even a fully-consented item
item, t, au = dispatch_meas("cs_valid", rdr=reader(), dq="HOLD")
ok = (item.status is OutboxStatus.DEAD_LETTER and not t.delivered
      and any(x.reason == "SEND_BLOCKED_DATA_QUALITY" for x in au.records))
rec("CM-dq-hold", "DEFENDED" if ok else "BREACH", "NONE",
    f"valid consent but dq=HOLD -> status={item.status.value}, called={bool(t.delivered)}, SEND_BLOCKED_DATA_QUALITY "
    f"(measurement_dispatcher.py:85; staged default HOLD until M6.2F)")

# F2 re-verify AT THE DISPATCHER: a ConsentSnapshot SUBCLASS with a raw-string scope must be denied
class _Unhardened(ConsentSnapshot):
    def __post_init__(self): pass
evil = _Unhardened("cs_evil", "guest_mapped_ok", ConsentState.VALID, TS, "external_measurement_granted")
item, t, au = dispatch_meas("cs_evil", rdr=reader(current=CUR_VALID, snaps={"cs_evil": evil}))
ok = (item.status is OutboxStatus.DEAD_LETTER and not t.delivered
      and any(x.reason == "CONSENT_SCOPE_UNTRUSTED_TYPE" for x in au.records))
rec("CM-f2-subclass", "DEFENDED" if ok else "BREACH", "M6-FAIL-002",
    f"subclass raw-str scope at dispatch -> status={item.status.value}, called={bool(t.delivered)}, "
    f"CONSENT_SCOPE_UNTRUSTED_TYPE (gate.py:56-66) — F2 is load-bearing here")

# duck snapshot (VALID enum + real frozenset scope + subject) returned by reader: this IS valid consent, not a bypass
duck_valid = SimpleNamespace(consent_state=ConsentState.VALID, subject_ref="guest_mapped_ok",
                             consent_scope=frozenset({ConsentScope.EXTERNAL_MEASUREMENT}))
item, t, au = dispatch_meas("cs_duckvalid", rdr=reader(current=CUR_VALID),
                            snap_reader=InMemoryConsentReader(snapshots={}, current=CUR_VALID))
# override reader.get to return the duck
class _DuckValidReader(InMemoryConsentReader):
    def get(self, cid): return duck_valid
item, t, au = dispatch_meas("cs_duckvalid", rdr=_DuckValidReader(snapshots={}, current=CUR_VALID))
rec("CM-duck-valid", "NOTE", "NONE",
    f"a duck with VALID state + real frozenset scope + subject = genuine valid consent -> reaches transport "
    f"(called={bool(t.delivered)}); not a bypass (the object represents real consent); a duck with a RAW scope is "
    f"denied by CM-f2-subclass")

# CONTROL: everything valid + succeeding transport -> SENT (proves the block is consent/DQ-specific)
item, t, au = dispatch_meas("cs_valid", rdr=reader(), dq="PASS")
rec("CM-control", "CONTROL" if (item.status is OutboxStatus.SENT and t.delivered) else "BREACH", "NONE",
    f"valid consent+current+dq PASS+succeeding transport -> status={item.status.value}, sent={bool(t.delivered)} "
    f"(the M6.2D would-send path; block is consent-specific, not blanket)")

# STAGED transport hard-blocks even a fully-valid item (external_send=OFF)
item, t, au = dispatch_meas("cs_valid", rdr=reader(), dq="PASS", transport=StagedBlockedTransport())
ok = (item.status is OutboxStatus.QUEUED and any(x.reason == "EXTERNAL_SEND_OFF" for x in au.records))
rec("CM-staged-block", "DEFENDED" if ok else "BREACH", "M6-FAIL-002",
    f"valid item + StagedBlockedTransport -> status={item.status.value} (held, EXTERNAL_SEND_OFF), NOT sent "
    f"(transport.py:38-41,68-72); external_send=OFF is the hard backstop")

# =================================================================================================
# GROUP CA — AUDIENCE SYNC CONSENT (M6-FAIL-002 / RULE-002)
# =================================================================================================
def seg_reader():
    segs = {"seg_approved": CustomerSegment("seg_approved", "Approved", ApprovalState.APPROVED),
            "seg_pending": CustomerSegment("seg_pending", "Pending", ApprovalState.PENDING)}
    mems = {"seg_approved": [SegmentMember("seg_approved", "mem_consented", "cs_valid"),
                             SegmentMember("seg_approved", "mem_optout", "cs_optout"),
                             SegmentMember("seg_approved", "mem_measonly", "cs_meas_only")],
            "seg_pending": [SegmentMember("seg_pending", "mem_x", "cs_valid")]}
    return InMemorySegmentReader(segments=segs, members=mems)


def enqueue_aud(segment_id, *, current=None):
    au = AuditLog(); store = OutboxStore()
    rows = enqueue_audience_sync(segment_id, reader=seg_reader(), consent_reader=reader(current=current),
                                 consent_gate=ConsentGate(au), store=store, audit=au,
                                 platform=AudiencePlatform.META_AUDIENCE, max_retries=3)
    return rows, store, au


# non-APPROVED segment enqueues nothing
rows, store, au = enqueue_aud("seg_pending")
ok = len(rows) == 0 and len(store) == 0 and any(x.reason == "AUDIENCE_SEGMENT_NOT_APPROVED" for x in au.records)
rec("CA-notapproved", "DEFENDED" if ok else "BREACH", "M6-FAIL-002",
    f"PENDING segment -> enqueued={len(store)}, AUDIENCE_SEGMENT_NOT_APPROVED (enqueue.py:118-120)")

# per-member ADD/REMOVE by consent scope
rows, store, au = enqueue_aud("seg_approved")
ops = {it.member_key: it.operation for (it, created) in rows}
ok = (ops.get("mem_consented") is AudienceOperation.ADD
      and ops.get("mem_optout") is AudienceOperation.REMOVE
      and ops.get("mem_measonly") is AudienceOperation.REMOVE)
rec("CA-enqueue-ops", "DEFENDED" if ok else "BREACH", "M6-FAIL-002",
    f"APPROVED segment ops: consented={ops.get('mem_consented').value}, optout={ops.get('mem_optout').value}, "
    f"measurement-only-consent={ops.get('mem_measonly').value} (ADD only for AUDIENCE_SYNC-consented; enqueue.py:128-129)")

# audience DISPATCH: an ADD whose consent LAPSED before send -> blocked (never synced)
rows, store, au2 = enqueue_aud("seg_approved")             # enqueue with valid consent
t = RecordTransport()
AudienceDispatcher(store, t, ConsentGate(au2), reader(current=CUR_LAPSED), au2).run_once(now=NOW)
add_item = next(it for (it, c) in rows if it.operation is AudienceOperation.ADD)
add_blocked = (add_item.status is OutboxStatus.DEAD_LETTER and add_item.outbox_id not in t.delivered
               and any(x.reason == "SYNC_BLOCKED_CONSENT" for x in au2.records))
rec("CA-add-lapsed", "DEFENDED" if add_blocked else "BREACH", "M6-FAIL-002",
    f"ADD row, consent revoked before dispatch -> status={add_item.status.value}, synced={add_item.outbox_id in t.delivered}, "
    f"SYNC_BLOCKED_CONSENT (audience_dispatcher.py:75-76)")

# audience DISPATCH: a REMOVE always proceeds (privacy-protective; correct, not a bypass)
rows, store, au3 = enqueue_aud("seg_approved")
t2 = RecordTransport()
AudienceDispatcher(store, t2, ConsentGate(au3), reader(current=CUR_LAPSED), au3).run_once(now=NOW)
remove_items = [it for (it, c) in rows if it.operation is AudienceOperation.REMOVE]
removes_sent = all(it.status is OutboxStatus.SENT for it in remove_items)
rec("CA-remove-always", "CONTROL" if removes_sent else "BREACH", "NONE",
    f"REMOVE rows -> all SENT regardless of consent = {removes_sent} (removal needs no consent; audience_dispatcher.py:74-77)")

# audience DISPATCH control: ADD with valid current consent + succeeding transport -> SENT
rows, store, au4 = enqueue_aud("seg_approved")
t3 = RecordTransport()
AudienceDispatcher(store, t3, ConsentGate(au4), reader(current=CUR_VALID), au4).run_once(now=NOW)
add_item2 = next(it for (it, c) in rows if it.operation is AudienceOperation.ADD)
rec("CA-add-control", "CONTROL" if add_item2.status is OutboxStatus.SENT else "BREACH", "NONE",
    f"ADD row, consent still VALID at send -> status={add_item2.status.value}, synced={add_item2.outbox_id in t3.delivered}")

# =================================================================================================
# GROUP R4 — NO DIRECT EXTERNAL SEND (RULE-004) + StagedBlockedTransport lock
# =================================================================================================
# the conversions endpoint holds NO transport; it only enqueues
conv_fields = set(ConversionDeps.__dataclass_fields__.keys())
rec("R4-no-transport", "DEFENDED" if "transport" not in conv_fields else "BREACH", "M6-FAIL-002",
    f"ConversionDeps fields={sorted(conv_fields)}; holds a Transport={('transport' in conv_fields)} (endpoint cannot send)")

# a valid conversion -> CREATED + enqueues QUEUED outbox rows, nothing sent
au = AuditLog(); cstore = ConversionEventStore(); outbox = OutboxStore()
deps = ConversionDeps(validator=EventValidator(Registry := type("R", (), {"get": staticmethod(lambda c: REG.get(c))})(), audit=au),
                      conversion_store=cstore, measurement_outbox=outbox, audit=au, max_retries=3)
body = {"event_code": "VIEW_LANDING", "source_event_id": "evt_src_1", "customer_or_guest_key": "guest_mapped_ok",
        "consent_snapshot_id": "cs_missing", "occurred_at": "2026-07-29T12:00:00+00:00", "idempotency_key": "k1",
        "correlation_id": "corr_conv"}
r = handle_conversions_request(body, deps)
ok = (r.status == "CREATED" and len(outbox) >= 1 and all(it.status is OutboxStatus.QUEUED for it in outbox.all()))
rec("R4-enqueue-only", "DEFENDED" if ok else "BREACH", "M6-FAIL-002",
    f"conversion with cs_missing consent -> {r.status}, outbox_rows={len(outbox)} all QUEUED={ok}; consent gated at "
    f"SEND not creation (conversions.py:141-146) — the row is internal, never externally sent without consent")

# force config.EXTERNAL_SEND=ON at runtime -> StagedBlockedTransport STILL refuses
_orig = cfg.EXTERNAL_SEND
try:
    cfg.EXTERNAL_SEND = "ON"
    try:
        StagedBlockedTransport().deliver(mob("cs_valid")); forced = "no-raise"
    except ExternalSendBlocked:
        forced = "blocked"
finally:
    cfg.EXTERNAL_SEND = _orig
rec("R4-force-on", "DEFENDED" if forced == "blocked" else "BREACH", "M6-FAIL-002",
    f"config.EXTERNAL_SEND forced ON -> StagedBlockedTransport.deliver={forced} (transport.py:38-41 hardcoded raise)")

# sweep: only the dispatchers hold/call the transport; the endpoint + enqueue reference no send primitive IN CODE
# (tokenize NAME tokens only, so a docstring mention of "Transport" is excluded).
def code_names(rel):
    with open(os.path.join(IMPL, "app", rel), "r", encoding="utf-8") as f:
        s = f.read()
    names = set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(s).readline):
            if tok.type == tokenize.NAME:
                names.add(tok.string)
    except tokenize.TokenError:
        pass
    return names
SEND_NAMES = {"attempt_delivery", "deliver", "StagedBlockedTransport", "ExternalSendBlocked", "Transport"}
ep_send = code_names("api/conversions.py") & SEND_NAMES
enq_send = code_names("measurement/outbox/enqueue.py") & SEND_NAMES
rec("R4-runtime-no-send", "DEFENDED" if not (ep_send or enq_send) else "BREACH", "M6-FAIL-002",
    f"send-primitive code names in endpoint={ep_send or 'NONE'}, in enqueue={enq_send or 'NONE'} "
    f"(runtime holds no transport; only the workers call attempt_delivery)")

# =================================================================================================
# GROUP RT — BOUNDED RETRY / DEAD-LETTER / NO SILENT LOSS (RULE-004, SMK-016)
# =================================================================================================
# failing transport + max_retries=3 -> RETRY x2 then DEAD_LETTER (bounded, trace retained)
au = AuditLog(); store = OutboxStore(); store.enqueue(mob("cs_valid", max_retries=3))
ft = FailTransport()
disp = MeasurementDispatcher(store, ft, ConsentGate(au), reader(), au, dq_status=lambda i: "PASS", backoff_base_seconds=60)
states = []
t_now = NOW
for _ in range(5):
    disp.run_once(now=t_now)
    it = store.all()[0]
    states.append((it.status.value, it.retry_count))
    t_now = t_now + timedelta(seconds=10000)   # advance past next_retry_at
final = store.all()[0]
bounded = (final.status is OutboxStatus.DEAD_LETTER and final.retry_count == 3
           and ft.attempts == 3 and final.error_log and "SEND_FAILED" in final.error_log)
rec("RT-retry-deadletter", "DEFENDED" if bounded else "BREACH", "NONE",
    f"failing transport max_retries=3 -> states={states}, attempts={ft.attempts}, error_log_has_trace={bool(final.error_log)} "
    f"(bounded, no infinite retry, no silent loss; transport.py:73-86) [SMK-016]")

# dead-lettered item is NOT reprocessed
before = ft.attempts
disp.run_once(now=t_now + timedelta(seconds=99999))
rec("RT-deadletter-frozen", "DEFENDED" if ft.attempts == before else "BREACH", "NONE",
    f"post-dead-letter run_once -> transport attempts {before}->{ft.attempts} (due_items excludes DEAD_LETTER; outbox_store.py:50-59)")

# ExternalSendBlocked -> held QUEUED, retry_count NOT incremented, not lost
au = AuditLog(); store = OutboxStore(); store.enqueue(mob("cs_valid"))
disp = MeasurementDispatcher(store, StagedBlockedTransport(), ConsentGate(au), reader(), au, dq_status=lambda i: "PASS")
disp.run_once(now=NOW); disp.run_once(now=NOW)   # drained twice
it = store.all()[0]
rec("RT-external-held", "DEFENDED" if (it.status is OutboxStatus.QUEUED and it.retry_count == 0) else "BREACH", "NONE",
    f"StagedBlockedTransport -> status={it.status.value}, retry_count={it.retry_count} (held, not lost, not a retry loop; transport.py:68-72)")

# consent policy-block is a distinct terminal (attempts==0, never reaches transport)
item, t, au = dispatch_meas("cs_missing", rdr=reader(), transport=FailTransport())
rec("RT-consent-terminal", "DEFENDED" if (item.status is OutboxStatus.DEAD_LETTER and t.attempts == 0) else "BREACH",
    "M6-FAIL-002", f"consent block -> DEAD_LETTER, transport.attempts={t.attempts} (distinct terminal, not a retry loop)")

# =================================================================================================
# GROUP DD — DEDUP / FAN-OUT (RULE-005)
# =================================================================================================
def mk_conv(event_code="VIEW_LANDING", *, source_event_id="evt_src", cs="cs_valid"):
    return ConversionEvent(conversion_id=f"conv_{event_code}_{source_event_id}", event_code=event_code,
                           source_event_id=source_event_id, correlation_id="corr_c",
                           customer_or_guest_key="guest_mapped_ok", consent_snapshot_id=cs, occurred_at=TS,
                           idempotency_key=f"idem_{event_code}_{source_event_id}")

# VIEW_LANDING fans out to PIXEL+CAPI (no OFFLINE); ORDER_VERIFIED adds OFFLINE
st1 = OutboxStore(); rows_vl = enqueue_measurement(mk_conv("VIEW_LANDING"), st1, max_retries=3)
st2 = OutboxStore(); rows_ov = enqueue_measurement(mk_conv("ORDER_VERIFIED"), st2, max_retries=3)
plat_vl = {it.platform for (it, c) in rows_vl}
plat_ov = {it.platform for (it, c) in rows_ov}
ok = (plat_vl == {MeasurementPlatform.PIXEL, MeasurementPlatform.CAPI}
      and plat_ov == {MeasurementPlatform.PIXEL, MeasurementPlatform.CAPI, MeasurementPlatform.OFFLINE})
rec("DD-fanout-offline", "DEFENDED" if ok else "BREACH", "NONE",
    f"VIEW_LANDING platforms={sorted(p.value for p in plat_vl)}; ORDER_VERIFIED={sorted(p.value for p in plat_ov)} "
    f"(OFFLINE only after ORDER_VERIFIED; enqueue.py:80-81)")

# re-enqueue the same conversion -> dedup (created=False), no double rows
st3 = OutboxStore(); enqueue_measurement(mk_conv("VIEW_LANDING"), st3, max_retries=3)
rows2 = enqueue_measurement(mk_conv("VIEW_LANDING"), st3, max_retries=3)
ok = all(created is False for (it, created) in rows2) and len(st3) == 2
rec("DD-dedup", "DEFENDED" if ok else "BREACH", "NONE",
    f"re-enqueue same conversion -> created={[c for (i,c) in rows2]}, rows={len(st3)} (UNIQUE dedup_key; outbox_store.py:30-39)")

# conversion endpoint replay -> DUPLICATE, no re-enqueue
au = AuditLog(); cstore = ConversionEventStore(); outbox = OutboxStore()
deps = ConversionDeps(validator=EventValidator(type("R", (), {"get": staticmethod(lambda c: REG.get(c))})(), audit=au),
                      conversion_store=cstore, measurement_outbox=outbox, audit=au, max_retries=3)
b = {"event_code": "VIEW_LANDING", "source_event_id": "evt_1", "customer_or_guest_key": "guest_mapped_ok",
     "consent_snapshot_id": "cs_valid", "occurred_at": "2026-07-29T12:00:00+00:00", "idempotency_key": "k",
     "correlation_id": "corr"}
r1 = handle_conversions_request(b, deps); n_after_first = len(outbox)
r2 = handle_conversions_request(dict(b, correlation_id="other"), deps)
ok = (r1.status == "CREATED" and r2.status == "DUPLICATE" and len(outbox) == n_after_first)
rec("DD-conv-replay", "DEFENDED" if ok else "BREACH", "NONE",
    f"conversion replay -> {r1.status}/{r2.status}, outbox stayed {n_after_first} (no re-enqueue; conversions.py:134-139)")

# =================================================================================================
# GROUP OVR — REVENUE / DATA-MART / POSTURE (FAIL-001 / FAIL-005 / FAIL-009, RULE-012/018)
# =================================================================================================
# revenue only from ORDER_VERIFIED
au = AuditLog(); deps = ConversionDeps(validator=EventValidator(type("R", (), {"get": staticmethod(lambda c: REG.get(c))})(), audit=au),
                                       conversion_store=ConversionEventStore(), measurement_outbox=OutboxStore(), audit=au, max_retries=3)
r_nonrev = handle_conversions_request({"event_code": "VIEW_LANDING", "source_event_id": "e", "customer_or_guest_key": "guest_mapped_ok",
                                       "consent_snapshot_id": "cs_valid", "occurred_at": "2026-07-29T12:00:00+00:00",
                                       "idempotency_key": "kk", "correlation_id": "c", "revenue_value": 100}, deps)
ok = r_nonrev.status == "REJECTED" and r_nonrev.error_code == "REVENUE_NOT_VERIFIED"
rec("OVR-revenue", "DEFENDED" if ok else "BREACH", "M6-FAIL-001",
    f"revenue_value on non-ORDER_VERIFIED -> {r_nonrev.status}/{r_nonrev.error_code} (conversions.py:102-107; only ORDER_VERIFIED)")

# segment reader is read-only (RULE-018) + audience read for sync only, no trigger (RULE-012)
seg_write = [m for m in dir(InMemorySegmentReader) if any(m.lower().startswith(w) for w in ("insert", "update", "delete", "add", "put", "save", "write", "trigger", "publish"))]
rec("OVR-datamart", "DEFENDED" if not seg_write else "BREACH", "M6-FAIL-005",
    f"SegmentReader write/trigger methods = {seg_write or 'NONE'} (read-only: get_segment/members; RULE-012/018)")

# posture immutable
posture = (cfg.GLOBAL_GATEWAY_STATE == "BLOCKED" and cfg.PRODUCTION_FLAG == "OFF" and cfg.EXTERNAL_SEND == "OFF"
           and cfg.is_external_send_enabled() is False)
rec("OVR-posture", "DEFENDED" if posture else "BREACH", "M6-FAIL-009",
    f"(gateway,prod,ext_send,enabled)=({cfg.GLOBAL_GATEWAY_STATE},{cfg.PRODUCTION_FLAG},{cfg.EXTERNAL_SEND},{cfg.is_external_send_enabled()})")

# tokenizer sweep: no network/db primitives across M6.2C app/
NET_DB = {"socket", "requests", "urllib", "httpx", "aiohttp", "smtplib", "websocket", "boto3", "kafka",
          "psycopg", "psycopg2", "pymysql", "sqlalchemy", "create_engine", "executemany", "cursor"}
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
rec("OVR-sweep-net", "DEFENDED" if not net_hits else "BREACH", "M6-FAIL-002",
    f"network/db code identifiers across M6.2C app/ = {net_hits or 'NONE'}")

# =================================================================================================
# GROUP F1 — DISPATCHER ROBUSTNESS (permits_send / current_state / duck attr unwrapped in _policy_block)
# =================================================================================================
# reader.get raises -> _policy_block wraps it -> snap=None -> consent deny (DEFENDED)
au = AuditLog(); store = OutboxStore(); store.enqueue(mob("cs_valid"))
class GetRaises(InMemoryConsentReader):
    def get(self, cid): raise RuntimeError("consent get down")
try:
    MeasurementDispatcher(store, RecordTransport(), ConsentGate(au), GetRaises(snapshots=CONSENT, current=CUR_VALID), au, dq_status=lambda i: "PASS").run_once(now=NOW)
    getraise = ("RESULT", store.all()[0].status.value)
except Exception as e:  # noqa: BLE001
    getraise = ("RAISE", type(e).__name__)
rec("F1-get-raises", "DEFENDED" if getraise[0] == "RESULT" and getraise[1] == "DEAD_LETTER" else "OPEN_NONGATE",
    "NONE", f"reader.get raises -> {getraise} (measurement_dispatcher.py:78-81 wraps get -> consent deny)")

# current_state raises -> permits_send NOT wrapped -> escapes the dispatcher run_once
au = AuditLog(); store = OutboxStore(); store.enqueue(mob("cs_valid"))
try:
    MeasurementDispatcher(store, RecordTransport(), ConsentGate(au), CurrentStateRaises(snapshots=CONSENT, current=CUR_VALID), au, dq_status=lambda i: "PASS").run_once(now=NOW)
    csr = ("RESULT", store.all()[0].status.value)
except Exception as e:  # noqa: BLE001
    csr = ("RAISE", type(e).__name__)
rec("F1-currentstate-raises", "OPEN_NONGATE" if csr[0] == "RAISE" else "DEFENDED", "NONE",
    f"consent_reader.current_state raises -> run_once {csr}; permits_send (gate.py:91) is NOT wrapped in "
    f"_policy_block -> escapes run_once, aborting the drain batch. No send occurs (fail-closed in send) -> not FAIL-002; "
    f"robustness/lost-audit; needs a hostile consent adapter.")

# duck snapshot lacking consent_state -> evaluate raises AttributeError -> escapes run_once
au = AuditLog(); store = OutboxStore(); store.enqueue(mob("cs_duck"))
try:
    MeasurementDispatcher(store, RecordTransport(), ConsentGate(au), DuckNoStateReader(), au, dq_status=lambda i: "PASS").run_once(now=NOW)
    dcr = ("RESULT", store.all()[0].status.value)
except Exception as e:  # noqa: BLE001
    dcr = ("RAISE", type(e).__name__)
rec("F1-duck-attr-raises", "OPEN_NONGATE" if dcr[0] == "RAISE" else "DEFENDED", "NONE",
    f"reader.get returns a duck lacking consent_state -> evaluate (gate.py:43) AttributeError -> run_once {dcr}; "
    f"same unwrapped-callee class as F1; no send -> not FAIL-002.")

# =================================================================================================
# GROUP W — vectors surfaced by the adversarial-ideation workflow (executed to confirm/refute)
# =================================================================================================
# W-MDC01 — a set SUBCLASS consent_scope with a lying __contains__ defeats the F2 guard (fail-OPEN residual).
class _LyingSet(set):
    def __contains__(self, x): return True   # empty backing (vacuous all()) but claims every scope is granted
lie = _Unhardened("cs_lie", "guest_mapped_ok", ConsentState.VALID, TS, _LyingSet())
item, t, au = dispatch_meas("cs_lie", rdr=InMemoryConsentReader(snapshots={"cs_lie": lie}, current=CUR_VALID))
fail_open = (item.status is OutboxStatus.SENT and bool(t.delivered))
rec("W-MDC01-lyingset", "OPEN_NONGATE" if fail_open else "DEFENDED", "NONE",
    f"set-subclass consent_scope w/ lying __contains__ (empty backing) -> status={item.status.value}, "
    f"transport_called={bool(t.delivered)}. F2 (gate.py:56-66) checks container type + element types but the grant "
    f"uses `scope not in scopes` (gate.py:68) which trusts __contains__ -> a scope never in the set reads as granted. "
    f"Armed-not-fired: the STAGED transport blocks the real send, and it needs a COMPROMISED consent adapter returning "
    f"a booby-trapped ConsentSnapshot subclass -> not a FAIL-002 trip today. Fix: `scope in frozenset(snapshot.consent_scope)` "
    f"(materialise the elements; bypass __contains__).")

# W-AUD02 — enqueue_audience_sync never binds member_key to the consent snapshot's subject_ref (borrowed consent).
segs = {"seg_borrow": CustomerSegment("seg_borrow", "Borrow", ApprovalState.APPROVED)}
# mem_victim's consent ref points at cs_valid, whose subject_ref is 'guest_mapped_ok' (a DIFFERENT subject)
mems = {"seg_borrow": [SegmentMember("seg_borrow", "mem_victim", "cs_valid")]}
au = AuditLog(); store = OutboxStore()
rows = enqueue_audience_sync("seg_borrow", reader=InMemorySegmentReader(segments=segs, members=mems),
                             consent_reader=reader(current=CUR_VALID), consent_gate=ConsentGate(au), store=store,
                             audit=au, platform=AudiencePlatform.META_AUDIENCE, max_retries=3)
borrowed = bool(rows) and rows[0][0].operation is AudienceOperation.ADD
rec("W-AUD02-borrowed", "OPEN_NONGATE" if borrowed else "DEFENDED", "NONE",
    f"member 'mem_victim' whose consent ref resolves to a DIFFERENT subject's VALID consent -> operation="
    f"{rows[0][0].operation.value if rows else 'none'} (ADD = borrowed consent). enqueue.py:122-129 never asserts "
    f"snap.subject_ref corresponds to member.member_key (the M6.2A ingest MAJOR-2 subject-binding was not applied to "
    f"the audience path); the dispatcher's permits_send checks current_state(snap.subject_ref) = the OTHER subject too. "
    f"Armed-not-fired: staged transport blocks; needs a MISPOINTED CRM membership (consumed) -> not a FAIL-002 trip today. "
    f"Fix: bind member_key to snap.subject_ref (or a trusted mapping) before ADD.")

# W-R5 — enqueue_audience_sync wraps consent_reader.get but NOT consent_gate.evaluate; a duck snap raises mid-loop.
class _DuckGetReader:
    def get(self, cid): return SimpleNamespace(subject_ref="x")     # no consent_state -> evaluate raises
    def current_state(self, s): return ConsentState.MISSING
segs2 = {"seg_d": CustomerSegment("seg_d", "D", ApprovalState.APPROVED)}
mems2 = {"seg_d": [SegmentMember("seg_d", "mem_d", "cs_duck")]}
au = AuditLog(); store = OutboxStore()
try:
    enqueue_audience_sync("seg_d", reader=InMemorySegmentReader(segments=segs2, members=mems2),
                          consent_reader=_DuckGetReader(), consent_gate=ConsentGate(au), store=store, audit=au,
                          platform=AudiencePlatform.META_AUDIENCE, max_retries=3)
    r5 = ("RESULT", len(store))
except Exception as e:  # noqa: BLE001
    r5 = ("RAISE", type(e).__name__)
rec("W-R5-enqueue-duck", "OPEN_NONGATE" if r5[0] == "RAISE" else "DEFENDED", "NONE",
    f"duck snapshot at enqueue -> {r5}; enqueue.py:124-128 wraps consent_reader.get but NOT consent_gate.evaluate, so a "
    f"duck lacking consent_state raises AttributeError mid-loop -> partial/unaudited enqueue. Same unwrapped-callee class "
    f"as F-A; no send -> not FAIL-002; needs a hostile consent adapter.")

# W-REV3 — NaN/Inf revenue on a genuine ORDER_VERIFIED passes the number check (data-quality, not a fail gate).
au = AuditLog(); deps = ConversionDeps(validator=EventValidator(type("R", (), {"get": staticmethod(lambda c: REG.get(c))})(), audit=au),
                                       conversion_store=ConversionEventStore(), measurement_outbox=OutboxStore(), audit=au, max_retries=3)
r_inf = handle_conversions_request({"event_code": "ORDER_VERIFIED", "source_event_id": "e", "customer_or_guest_key": "guest_mapped_ok",
                                    "consent_snapshot_id": "cs_valid", "occurred_at": "2026-07-29T12:00:00+00:00",
                                    "idempotency_key": "kinf", "correlation_id": "c", "revenue_value": float("inf")}, deps)
rec("W-REV3-naninf", "NOTE", "NONE",
    f"revenue_value=inf on ORDER_VERIFIED -> {r_inf.status} (accepted; NaN/Inf is a data-quality gap, not FAIL-001/FAIL-002; "
    f"the DQ checker at M6.2F / M6-P1206 should reject non-finite revenue). Not in-scope for this prompt.")

# =================================================================================================
# SUMMARY
# =================================================================================================
from collections import Counter
cnt = Counter(s for _, s, _, _ in OUT)
breaches = [pid for pid, s, g, d in OUT if s == "BREACH"]
opens = [pid for pid, s, g, d in OUT if s == "OPEN_NONGATE"]
print("=" * 104)
print("SUMMARY:", dict(cnt))
print("IN-SCOPE FAIL-GATE BREACHES (M6-FAIL-002):", breaches or "NONE")
print("OPEN (real defect, does NOT trip M6-FAIL-002):", opens or "NONE")
print("TOTAL RECORDED OUTCOMES:", len(OUT))
print("=" * 104)
