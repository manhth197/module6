"""BOUNDARY_ADVERSARY M6-P1005 - event-drift attack battery (read-only against impl)."""
from datetime import datetime, timezone

from app.measurement.audit import AuditLog
from app.measurement.consent.gate import ConsentGate
from app.measurement.ingest import IngestService
from app.measurement.logs.web_event_log_store import WebEventLogStore
from app.measurement.models.consumed import (
    ConsentScope, ConsentSnapshot, ConsentState, DataSensitivity,
    EventRegistryRow, RegistrationState,
)
from app.measurement.models.web_event_log import WebEventLog
from app.measurement.registry.validator import EventValidator

TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)

ROW_OK = EventRegistryRow(
    event_code="VIEW_LANDING", registration_state=RegistrationState.ACTIVE,
    owner="core.tracking", channel="web", data_sensitivity=DataSensitivity.INTERNAL,
)


class DictRegistry:
    """Exactly the conftest test double."""
    def __init__(self, rows): self._rows = rows
    def get(self, event_code): return self._rows.get(event_code)


class CollationRegistry:
    """Realistic SQL adapter: MySQL utf8mb4_general_ci / PAD SPACE, or Postgres citext.
    `WHERE event_code = %s` matches case-insensitively and ignores trailing spaces."""
    def __init__(self, rows): self._rows = rows
    def get(self, event_code):
        probe = str(event_code).strip().upper()
        for k, v in self._rows.items():
            if k.upper() == probe:
                return v          # returns the CANONICAL row for a non-canonical probe
        return None


def svc(registry):
    a = AuditLog()
    s = WebEventLogStore()
    return IngestService(EventValidator(registry, a), s, ConsentGate(a)), s, a


print("=" * 78)
print("A1  registry adapter returns canonical row for a NON-CANONICAL probe")
print("=" * 78)
sv, store, aud = svc(CollationRegistry({"VIEW_LANDING": ROW_OK}))
for probe in ("view_landing", "VIEW_LANDING ", "View_Landing"):
    r = sv.ingest_event(event_code=probe, page_id="p1", session_id="s1", source="web",
                        event_ts=TS, raw_event_hash="h")
    print("  probe=%-18r decision=%-7s logged=%s created=%s"
          % (probe, r.validation.decision.value, r.logged, r.log_created))
print("  rows in web_event_logs = %d" % len(store))
print("  persisted event_code values:", [repr(x.event_code) for x in store.all()])
print("  registry ACTIVE codes      : ['VIEW_LANDING']")
print("  audit records              :", len(aud))
print("  >> codes written NOT in event_registry:",
      [repr(x.event_code) for x in store.all() if x.event_code != "VIEW_LANDING"])

print()
print("=" * 78)
print("A2  same missing reconciliation, against the UNMODIFIED conftest double")
print("=" * 78)


class Spoof(str):
    """A str whose hash/eq impersonate a registered code but whose VALUE is a new code."""
    def __hash__(self): return hash("VIEW_LANDING")
    def __eq__(self, other): return other == "VIEW_LANDING"
    def __ne__(self, other): return not self.__eq__(other)


sv, store, aud = svc(DictRegistry({"VIEW_LANDING": ROW_OK}))
spoof = Spoof("M6_INVENTED_EVENT")
r = sv.ingest_event(event_code=spoof, page_id="p1", session_id="s1", source="web",
                    event_ts=TS, raw_event_hash="h")
print("  decision=%s logged=%s created=%s" % (r.validation.decision.value, r.logged, r.log_created))
row = store.all()[0]
print("  row.event_code as written   =", repr(str(row.event_code)))
print("  ValidationResult.event_code =", repr(str(r.validation.event_code)))
print("  registry row.event_code     = 'VIEW_LANDING'  <- never compared by validator")
print("  audit records               = %d  (no reject/hold, no drift alarm)" % len(aud))

print()
print("=" * 78)
print("A3  store.append() is an UNGUARDED write surface (no registry check, no audit)")
print("=" * 78)
s2 = WebEventLogStore()
forged = WebEventLog(
    log_id="log_forged", event_code="PURCHASE_CONFIRMED_INVENTED_BY_M6",
    page_id="p", session_id="s", source="web", event_ts=TS,
    idempotency_key="not-even-a-sha256", ingested_at=TS,
)
res = s2.append(forged)
print("  created=%s  len(store)=%d" % (res.created, len(s2)))
print("  event_code in web_event_logs =", repr(s2.all()[0].event_code))
print("  idempotency_key stored       =", repr(s2.all()[0].idempotency_key),
      " (never recomputed/verified)")
print("  store public methods:", [m for m in dir(s2) if not m.startswith('_')])

print()
print("=" * 78)
print("A4  log_id = key[:16] (64-bit) vs DDL 'log_id TEXT PRIMARY KEY'")
print("=" * 78)
s3 = WebEventLogStore()
s3.append(WebEventLog("log_dead0000beef00", "E", "p", "s", "web", TS, "KEY_A", TS))
s3.append(WebEventLog("log_dead0000beef00", "E", "p", "s2", "web", TS, "KEY_B", TS))
print("  in-memory rows sharing one log_id = %d  log_ids=%s"
      % (len(s3), [x.log_id for x in s3.all()]))
print("  >> DDL PRIMARY KEY(log_id) would reject the 2nd INSERT")

print()
print("=" * 78)
print("A5  whitespace-only owner passes the 'must have an owner' check")
print("=" * 78)
ws = EventRegistryRow(event_code="WS_OWNER", registration_state=RegistrationState.ACTIVE,
                      owner="   ", data_sensitivity=DataSensitivity.INTERNAL)
sv, store, aud = svc(DictRegistry({"WS_OWNER": ws}))
r = sv.ingest_event(event_code="WS_OWNER", page_id="p", session_id="s", source="web",
                    event_ts=TS, raw_event_hash="h")
print("  owner=%r decision=%s logged=%s audit=%d"
      % (ws.owner, r.validation.decision.value, r.logged, len(aud)))
print("  control owner='' ->",
      EventValidator(DictRegistry({"E": EventRegistryRow(
          "E", RegistrationState.ACTIVE, owner="")}), AuditLog()).validate("E").decision.value)

print()
print("=" * 78)
print("A6  consent_scope is a DEFAULTED security parameter")
print("=" * 78)
snap = ConsentSnapshot("cs1", "guest_1", ConsentState.VALID, TS,
                       frozenset({ConsentScope.EXTERNAL_MEASUREMENT}))
sv, store, aud = svc(DictRegistry({"VIEW_LANDING": ROW_OK}))
r = sv.ingest_event(event_code="VIEW_LANDING", page_id="p", session_id="s", source="web",
                    event_ts=TS, raw_event_hash="h", consent_snapshot=snap)
gate = ConsentGate(AuditLog())
print("  omitted scope -> evaluated as EXTERNAL_MEASUREMENT ->",
      gate.evaluate(snap, ConsentScope.EXTERNAL_MEASUREMENT))
print("  scope the caller actually meant (CRM)              ->",
      gate.evaluate(snap, ConsentScope.CRM))
print("  ingest notes =", r.notes)
print("  IngestResult fields =", list(type(r).__dataclass_fields__))

print()
print("=" * 78)
print("A7  raw-string consent_scope from JSON passes `in` (loose) while consent_state")
print("    uses `is` (strict) - asymmetric coercion discipline")
print("=" * 78)
raw = ConsentSnapshot("cs2", "guest_2", ConsentState.VALID, TS, frozenset({"crm"}))
print("  scope set =", set(raw.consent_scope), " gate.evaluate(CRM) =",
      gate.evaluate(raw, ConsentScope.CRM))
