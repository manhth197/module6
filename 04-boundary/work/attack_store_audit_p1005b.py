"""Refinement of B3: exactly which audit records surround a dedup drop. READ-ONLY."""
from datetime import datetime, timezone

from app.measurement.audit import AuditLog
from app.measurement.consent.gate import ConsentGate
from app.measurement.logs.web_event_log_store import WebEventLogStore
from app.measurement.models.consumed import (EventRegistryRow, RegistrationState,
                                             DataSensitivity, ConsentScope, ConsentSnapshot,
                                             ConsentState)
from app.measurement.registry.validator import EventValidator
from app.measurement.ingest import IngestService

TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


class Reg:
    def __init__(self, rows): self._r = rows
    def get(self, code): return self._r.get(code)


ROWS = {"VIEW_LANDING": EventRegistryRow("VIEW_LANDING", RegistrationState.ACTIVE,
                                         owner="core.tracking", channel="web",
                                         data_sensitivity=DataSensitivity.INTERNAL)}
CS = ConsentSnapshot("cs_valid", "guest_1", ConsentState.VALID, TS,
                     frozenset({ConsentScope.EXTERNAL_MEASUREMENT}))

aud = AuditLog()
store = WebEventLogStore()
svc = IngestService(EventValidator(Reg(ROWS), aud), store, ConsentGate(aud))

# fully valid + consented event, twice with the SAME idempotency inputs
svc.ingest_event(event_code="VIEW_LANDING", page_id="p1", session_id="s1", source="web",
                 event_ts=TS, raw_event_hash="h", consent_snapshot=CS)
n_before_2nd = len(aud)
r2 = svc.ingest_event(event_code="VIEW_LANDING", page_id="p1", session_id="s1", source="web",
                      event_ts=TS, raw_event_hash="h", consent_snapshot=CS)

print("audit records written during the 2nd (deduped) call:", len(aud) - n_before_2nd)
print("all audit reasons ever written:", [r.reason for r in aud.records])
print("any audit reason mentioning dedup/drop/collision:",
      [r.reason for r in aud.records if "DEDUP" in r.reason or "DROP" in r.reason])
print("2nd call result: logged=%s log_created=%s notes=%s" % (r2.logged, r2.log_created, r2.notes))
print("store size:", len(store))
print()
print("-> the ONLY trace of the dropped event is the ephemeral in-process notes list on")
print("   IngestResult; nothing durable records that an ingress event was discarded.")
print()
print("store.append() source lines (no row comparison):")
import inspect
from app.measurement.logs import web_event_log_store as m
src = inspect.getsource(m.WebEventLogStore.append)
print(src)
