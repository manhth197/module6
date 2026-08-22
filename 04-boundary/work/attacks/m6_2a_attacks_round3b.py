"""M6-P1005 — Round-3 addendum probes (raise the reachability of F-2 from 'adapter down' to
'channel-origin data alone', and pin the SMK-001 expectation miss)."""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import pathlib
from datetime import datetime, timezone

IMPL = pathlib.Path(r"D:\M6\Module6-workspace\04-artifacts\impl\M6.2A")
sys.path.insert(0, str(IMPL))

from app.measurement.audit import AuditLog                             # noqa: E402
from app.measurement.consent.gate import ConsentGate                   # noqa: E402
from app.measurement.identity.resolver import IdentityResolver         # noqa: E402
from app.measurement.ingest import IngestService                       # noqa: E402
from app.measurement.logs.web_event_log_store import WebEventLogStore  # noqa: E402
from app.measurement.models.consumed import (                          # noqa: E402
    ConsentState, EventRegistryRow, GuestContact, RegistrationState,
)
from app.measurement.registry.validator import EventValidator          # noqa: E402

UTC = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


class Registry:
    def __init__(self, r):
        self._r = r

    def get(self, c):
        return self._r.get(c)


class Contacts:
    def __init__(self, r):
        self._r = r

    def get(self, g):
        return self._r.get(g)


class Customers:
    def exists(self, c):
        return c == "cust_0001"


class Reader:
    def get(self, i):
        return None

    def current_state(self, s):
        return ConsentState.MISSING


ROWS = {"VIEW_LANDING": EventRegistryRow("VIEW_LANDING", RegistrationState.ACTIVE, owner="core.tracking")}
GUESTS = {"guest_mapped_ok": GuestContact("guest_mapped_ok", "fp_a", "cust_0001", "audit_ref_123")}


def build():
    a = AuditLog()
    s = WebEventLogStore()
    return IngestService(
        EventValidator(Registry(ROWS), a), s, ConsentGate(a), Reader(), a,
        resolver=IdentityResolver(Contacts(GUESTS), Customers(), a),
    ), a, s


def probe(label, **kw):
    svc, audit, store = build()
    base = dict(event_code="VIEW_LANDING", page_id="p", session_id="s", source="web",
                event_ts=UTC, raw_event_hash="h")
    base.update(kw)
    try:
        res = svc.ingest_event(**base)
        print(f"[HELD   ] {label:<58} -> no raise; logged={res.logged} notes={res.notes} audits={len(audit)}")
        return False
    except BaseException as exc:  # noqa: BLE001
        print(f"[FINDING] {label:<58} -> ESCAPED {type(exc).__name__}: {exc} | audits written={len(audit)} "
              f"| rows={len(store)}")
        return True


print("=== G — channel-origin reachability of the unwrapped-port class (F-2) ===")
probe("guest_id = JSON array (channel-origin)", guest_id=["guest_mapped_ok"])
probe("guest_id = JSON object (channel-origin)", guest_id={"id": "guest_mapped_ok"})
probe("event_code = JSON array (channel-origin)", event_code=["VIEW_LANDING"])
probe("event_code = JSON number (channel-origin)", event_code=12345)
probe("event_code = None (absent key in JSON body)", event_code=None)
probe("page_id = JSON array (control: not a lookup key)", page_id=["p"])
probe("session_id = JSON number (control: not a lookup key)", session_id=7)
probe("raw_event_hash = None (control)", raw_event_hash=None)
probe("CONTROL: everything well-formed", guest_id="guest_mapped_ok")

print("\n=== H — SMK-001 expectation under the F-2 input class ===")
print("SMK-001 (ADS-P0-001): scenario 'Event khong co trong event_registry' -> expected 'Reject/HOLD, audit ro'")
for label, code in (("unknown, well-formed str", "TOTALLY_UNKNOWN_EVENT"),
                    ("unknown, JSON array", ["TOTALLY_UNKNOWN_EVENT"]),
                    ("unknown, JSON number", 987654)):
    svc, audit, store = build()
    try:
        res = svc.ingest_event(event_code=code, page_id="p", session_id="s", source="web",
                               event_ts=UTC, raw_event_hash="h")
        print(f"  {label:<28} decision={res.validation.decision.value:<6} logged={res.logged} "
              f"audit_records={len(audit)}  -> SMK-001 expectation MET")
    except BaseException as exc:  # noqa: BLE001
        print(f"  {label:<28} EXCEPTION {type(exc).__name__:<10} logged=n/a audit_records={len(audit)}  "
              f"-> SMK-001 expectation MISSED (neither Reject nor HOLD, and no audit)")
