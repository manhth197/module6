"""Read-only adversarial verification of F1 (tz normalization / dedup). Modifies nothing."""
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, r"D:/M6/Module6-workspace/04-boundary/04-artifacts/impl/M6.2A")

from app.measurement.audit import AuditLog
from app.measurement.consent.gate import ConsentGate
from app.measurement.logs.idempotency import build_idempotency_key, normalize_ts
from app.measurement.logs.web_event_log_store import WebEventLogStore
from app.measurement.models.consumed import (
    DataSensitivity, EventRegistryRow, RegistrationState,
)
from app.measurement.registry.validator import EventValidator
from app.measurement.ingest import IngestService


class Reg:
    def __init__(self, rows): self._rows = rows
    def get(self, code): return self._rows.get(code)


rows = {
    "VIEW_LANDING": EventRegistryRow(
        event_code="VIEW_LANDING",
        registration_state=RegistrationState.ACTIVE,
        owner="core.tracking",
        channel="web",
        data_sensitivity=DataSensitivity.INTERNAL,
        external_send_policy=None,
        schema_ref="evt.view_landing.v1",
    ),
}

audit = AuditLog()
store = WebEventLogStore()
svc = IngestService(EventValidator(Reg(rows), audit), store, ConsentGate(audit))

t_utc = datetime(2026, 7, 29, 10, 0, 0, tzinfo=timezone.utc)
t_naive = datetime(2026, 7, 29, 10, 0, 0)
t_ict = datetime(2026, 7, 29, 17, 0, 0, tzinfo=timezone(timedelta(hours=7)))

print("aware-UTC == +07:00 (same instant)?", t_utc == t_ict)
for label, t in (("aware-UTC", t_utc), ("naive   ", t_naive), ("+07:00  ", t_ict)):
    print(f"  normalize_ts({label}) = {normalize_ts(t)!r}")

keys = []
for label, t in (("aware-UTC", t_utc), ("naive   ", t_naive), ("+07:00  ", t_ict)):
    r = svc.ingest_event(
        event_code="VIEW_LANDING", page_id="p1", session_id="s1", source="web",
        event_ts=t, raw_event_hash="SAME_RAW_HASH",
        ingested_at=t_utc,
    )
    keys.append(r.idempotency_key)
    print(f"  ingest {label}: created={r.log_created} key={r.idempotency_key[:16]} notes={r.notes}")

print("distinct keys:", len(set(keys)))
print("rows in web_event_logs:", len(store))
print("stored event_ts:", [row.event_ts.isoformat() for row in store.all()])

import inspect
src = inspect.getsource(svc.ingest_event)
print("seam has tz guard (astimezone/utcoffset/tzinfo):",
      any(tok in src for tok in ("astimezone", "utcoffset", "tzinfo")))
print("normalize_ts source:", inspect.getsource(normalize_ts).strip().splitlines()[-1].strip())
