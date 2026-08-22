"""BOUNDARY_ADVERSARY M6-P1005 — overreach lens attacks (run on a COPY under work/, never on impl/)."""
from datetime import datetime, timezone

from app import config
from app.measurement.audit import AuditLog
from app.measurement.consent.gate import ConsentGate
from app.measurement.ingest import IngestService
from app.measurement.logs.web_event_log_store import WebEventLogStore
from app.measurement.models.consumed import (
    ConsentScope, ConsentSnapshot, ConsentState, DataSensitivity,
    EventRegistryRow, RegistrationState,
)
from app.measurement.registry.validator import EventValidator

TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


class Reg:
    def __init__(s, rows): s.rows = rows
    def get(s, c): return s.rows.get(c)


class ConsentReaderD:
    def __init__(s, cur): s.cur = cur
    def get(s, i): return None
    def current_state(s, subj): return s.cur.get(subj, ConsentState.MISSING)


rows = {"VIEW_LANDING": EventRegistryRow(
    event_code="VIEW_LANDING", registration_state=RegistrationState.ACTIVE,
    owner="core.tracking", channel="web", data_sensitivity=DataSensitivity.INTERNAL,
    external_send_policy=None)}

cs_valid = ConsentSnapshot("cs_valid", "guest_mapped_ok", ConsentState.VALID, TS,
                           frozenset({ConsentScope.EXTERNAL_MEASUREMENT, ConsentScope.AUDIENCE_SYNC,
                                      ConsentScope.CRM}))

print("=== A1: ConsentGate.permits_send under STAGED posture (BLOCKED/OFF/OFF) ===")
print("posture:", config.GLOBAL_GATEWAY_STATE, config.PRODUCTION_FLAG, config.EXTERNAL_SEND)
audit = AuditLog()
gate = ConsentGate(audit)
reader = ConsentReaderD({"guest_mapped_ok": ConsentState.VALID})
for scope in (ConsentScope.EXTERNAL_MEASUREMENT, ConsentScope.AUDIENCE_SYNC, ConsentScope.CRM):
    print(f"  permits_send(cs_valid, {scope.value}) ->", gate.permits_send(cs_valid, scope, reader))
svc = IngestService(EventValidator(Reg(rows), audit), WebEventLogStore(), gate)
r = svc.ingest_event(event_code="VIEW_LANDING", page_id="p1", session_id="s1", source="web",
                     event_ts=TS, raw_event_hash="h", consent_snapshot=cs_valid)
print("  ingest egress_eligible for the SAME event ->", r.egress_eligible, r.notes)
import inspect
src = inspect.getsource(ConsentGate.permits_send)
print("  permits_send consults posture/policy?",
      any(t in src for t in ("EXTERNAL_SEND", "external_send_permitted", "GLOBAL_GATEWAY",
                             "PRODUCTION_FLAG", "permits_external_send", "is_external_send_enabled")))

print()
print("=== A2: is_external_send_enabled() — 'single choke point' claim ===")
print("  before:", config.is_external_send_enabled())
config.EXTERNAL_SEND = "ON"          # simulate later slice / bad config load / test monkeypatch
print("  after config.EXTERNAL_SEND='ON':", config.is_external_send_enabled())
config.EXTERNAL_SEND = "OFF"

print()
print("=== A3: session_id / page_id masking claim (PLAN.md C1) ===")
store = WebEventLogStore()
audit2 = AuditLog()
svc2 = IngestService(EventValidator(Reg(rows), audit2), store, ConsentGate(audit2))
svc2.ingest_event(event_code="VIEW_LANDING", page_id="/lp?sid=SUBJECT-IDENTIFIER-LONG",
                  session_id="SESSIONIDENTIFIERLONG", source="web", event_ts=TS,
                  raw_event_hash="h", consent_snapshot=cs_valid)
row = store.all()[0]
print("  stored session_id =", repr(row.session_id))
print("  stored page_id    =", repr(row.page_id))
print("  masked anywhere?  ", ("***" in row.session_id) or ("***" in row.page_id))

print()
print("=== A4: egress/order/revenue/CRM surface on public objects ===")
bad = ("send", "dispatch", "publish", "scale", "post", "order", "price", "pay",
       "revenue", "commission", "crm", "sync", "migrate", "apply", "connect")
for obj, name in ((svc, "IngestService"), (store, "WebEventLogStore"),
                  (gate, "ConsentGate"), (audit, "AuditLog")):
    hits = [a for a in dir(obj) if not a.startswith("_") and any(b in a.lower() for b in bad)]
    print(f"  {name}: {hits}")

print()
print("=== A5: rejected/HELD event — PLAN.md 'logged internally, never lost' ===")
store3 = WebEventLogStore()
audit3 = AuditLog()
svc3 = IngestService(EventValidator(Reg(rows), audit3), store3, ConsentGate(audit3))
res = svc3.ingest_event(event_code="UNKNOWN_X", page_id="p", session_id="s", source="web",
                        event_ts=TS, raw_event_hash="h")
print("  logged:", res.logged, "| rows in web_event_logs:", len(store3),
      "| audit records:", len(audit3))
