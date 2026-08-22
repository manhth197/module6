"""BOUNDARY_ADVERSARY probes - RULE-007 store + RULE-015 audit. READ-ONLY: imports impl, modifies nothing."""
from datetime import datetime, timezone, timedelta

from app.measurement.audit import AuditLog
from app.measurement.consent.gate import ConsentGate
from app.measurement.logs.web_event_log_store import WebEventLogStore
from app.measurement.logs.idempotency import build_idempotency_key, normalize_ts
from app.measurement.models.web_event_log import WebEventLog
from app.measurement.models.consumed import EventRegistryRow, RegistrationState, DataSensitivity
from app.measurement.registry.validator import EventValidator
from app.measurement.ingest import IngestService

TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


class Reg:
    def __init__(self, rows): self._r = rows
    def get(self, code): return self._r.get(code)


ROWS = {"VIEW_LANDING": EventRegistryRow("VIEW_LANDING", RegistrationState.ACTIVE,
                                         owner="core.tracking", channel="web",
                                         data_sensitivity=DataSensitivity.INTERNAL)}


def seam():
    a = AuditLog()
    s = WebEventLogStore()
    return IngestService(EventValidator(Reg(ROWS), a), s, ConsentGate(a)), s, a


print("=" * 78)
print("B1  log_id PRIMARY KEY (DDL L12) vs store: no uniqueness check on log_id")
print("=" * 78)
s = WebEventLogStore()
k1 = build_idempotency_key("VIEW_LANDING", "p1", "s1", "h1", normalize_ts(TS))
k2 = build_idempotency_key("VIEW_LANDING", "p2", "s2", "h2", normalize_ts(TS))
r1 = WebEventLog("log_COLLIDE00000", "VIEW_LANDING", "p1", "s1", "web", TS, k1, TS)
r2 = WebEventLog("log_COLLIDE00000", "VIEW_LANDING", "p2", "s2", "web", TS, k2, TS)
a1, a2 = s.append(r1), s.append(r2)
print("  created:", a1.created, a2.created, "| rows in store:", len(s))
print("  distinct log_id values:", len({r.log_id for r in s.all()}), "of", len(s), "rows")
print("  log_id = 'log_' + key[:16] = 64 bits of sha256 over attacker-supplied page/session/hash")
print("  sample:", "log_" + k1[:16])

print()
print("=" * 78)
print("B3  dedup collision: store never compares the colliding row, never audits the drop")
print("=" * 78)
s = WebEventLogStore()
key = build_idempotency_key("VIEW_LANDING", "p1", "s1", "h", normalize_ts(TS))
orig = WebEventLog("log_a", "VIEW_LANDING", "p1", "s1", "web", TS, key, TS,
                   consent_snapshot_id="cs_valid", correlation_id="corr_1")
s.append(orig)
other = WebEventLog("log_b", "OTHER_EVENT", "pX", "sX", "mobile", TS + timedelta(days=99),
                    key, TS, consent_snapshot_id="cs_other", correlation_id="corr_2")
res = s.append(other)
print("  rows differ in every field?", orig != other)
print("  append() created =", res.created, "; returned row IS the original:", res.row is orig)
print("  store size:", len(s), "-> 2nd distinct event GONE: no exception, no comparison")

svc, store2, aud = seam()
before = len(aud)
svc.ingest_event(event_code="VIEW_LANDING", page_id="p1", session_id="s1",
                 source="web", event_ts=TS, raw_event_hash="h")
r_b = svc.ingest_event(event_code="VIEW_LANDING", page_id="p1", session_id="s1",
                       source="web", event_ts=TS, raw_event_hash="h")
print("  via seam, 2nd call: logged =", r_b.logged, "| log_created =", r_b.log_created,
      "| notes =", r_b.notes)
print("  audit records for the dropped event:", len(aud) - before)
print("  IngestService ctor params:", IngestService.__init__.__code__.co_varnames[1:5])

print()
print("=" * 78)
print("B5  DDL 'source TEXT NOT NULL' (L16) vs code: zero validation, reachable via seam")
print("=" * 78)
svc, store3, aud3 = seam()
r = svc.ingest_event(event_code="VIEW_LANDING", page_id="p1", session_id="s1",
                     source=None, event_ts=TS, raw_event_hash="h")
row = store3.all()[0]
print("  accepted source=None -> logged:", r.logged, "| stored row.source =", repr(row.source))
try:
    build_idempotency_key("VIEW_LANDING", None, "s1", "h", normalize_ts(TS))
except TypeError as e:
    print("  contrast: page_id=None DOES raise ->", type(e).__name__)

print()
print("=" * 78)
print("B6  audit sink: unbounded, pre-registry, attacker-driven, no dedup")
print("=" * 78)
svc, store4, aud4 = seam()
for i in range(5000):
    svc.ingest_event(event_code="EVIL_%d" % i, page_id="p", session_id="s",
                     source="web", event_ts=TS, raw_event_hash="h")
print("  5000 unknown event_codes ->", len(store4), "web_event_logs rows (correctly none)")
print("     but", len(aud4), "AuditRecords, each holding the RAW attacker string")
print("     last audit event_code:", repr(aud4.records[-1].event_code))
svc, _, aud5 = seam()
for _ in range(3):
    svc.ingest_event(event_code="EVIL", page_id="p", session_id="s", source="web",
                     event_ts=TS, raw_event_hash="h")
print("  same unknown code 3x -> audit records =", len(aud5), "(no dedup / no cap)")

print()
print("=" * 78)
print("B7  AuditRecord timestamp is caller-supplied and unvalidated (single field)")
print("=" * 78)
a = AuditLog()
a.record("HOLD", "CONSENT_MISSING", at=datetime(1999, 1, 1, tzinfo=timezone.utc))
a.record("HOLD", "CONSENT_MISSING", at=datetime(2999, 1, 1, tzinfo=timezone.utc))
print("  accepted years:", [rec.at.year for rec in a.records])
print("  AuditRecord fields:", list(a.records[0].__dataclass_fields__))
print("  WebEventLog time fields:", [f for f in WebEventLog.__dataclass_fields__
                                     if f in ("event_ts", "ingested_at")])

print()
print("=" * 78)
print("control: audit sink public API really is append-only (nothing mutating to call)")
print("=" * 78)
a = AuditLog()
a.record("HOLD", "X")
print("  public methods:", [m for m in dir(a) if not m.startswith("_")])
print("  records property is a copy:", a.records is not a._records, type(a.records).__name__)
