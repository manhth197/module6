"""BOUNDARY_ADVERSARY M6-P1005 - part B: composite + residual probes (read-only)."""
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, r"D:\M6\Module6-workspace\04-boundary\04-artifacts\impl\M6.2A")

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
from app.measurement.registry.validator import (
    EventDecision, EventValidator, ValidationResult, permits_external_send,
)

TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def rep(n, d):
    print(f"[{n}] {d}")


audit = AuditLog()
gate = ConsentGate(audit)

# ---- B1. str scope param (uncoerced JSON) vs enum container --------------
snap_enum = ConsentSnapshot("cs1", "g", ConsentState.VALID, TS,
                            frozenset({ConsentScope.CRM}))
rep("B1-str-scope-arg", {"evaluate(snap, 'crm')": gate.evaluate(snap_enum, "crm")})

# ---- B2. EMPTY scope string vs str container -> always True --------------
snap_str = ConsentSnapshot("cs2", "g", ConsentState.VALID, TS, "external_measurement")
rep("B2-empty-scope", {
    "evaluate(snap_str, '')": gate.evaluate(snap_str, ""),
    "evaluate(snap_str,'measurement')(undefined scope)": gate.evaluate(snap_str, "measurement"),
})

# ---- B3. consent_scope missing entirely (None / field default) -----------
snap_none = ConsentSnapshot("cs3", "g", ConsentState.VALID, TS, None)
try:
    r = gate.evaluate(snap_none, ConsentScope.CRM)
    rep("B3-None-scope", f"returned {r}")
except Exception as e:
    rep("B3-None-scope", f"{type(e).__name__}: {e} (no audit written: "
                         f"{len(audit)} records so far)")
snap_default = ConsentSnapshot("cs4", "g", ConsentState.VALID, TS)   # default frozenset()
rep("B3-default-scope", gate.evaluate(snap_default, ConsentScope.CRM))

# ---- B4. GRANT path writes NO audit record ------------------------------
a2 = AuditLog()
g2 = ConsentGate(a2)
ok = g2.evaluate(ConsentSnapshot("cs_ok", "guest_secret", ConsentState.VALID, TS,
                                 frozenset({ConsentScope.CRM})), ConsentScope.CRM)
rep("B4-grant-audit", {"evaluate": ok, "audit_records_written": len(a2),
                       "reasons": [r.reason for r in a2.records]})


# ---- B5. composite: seam has no independent config choke-point -----------
class Reg:
    def get(self, c):
        return EventRegistryRow(event_code=c, registration_state=RegistrationState.ACTIVE,
                                owner="core.tracking", channel="web",
                                data_sensitivity=DataSensitivity.INTERNAL,
                                external_send_policy="ALLOW_EXTERNAL")


rep("B5-real-validator-lock", {
    "permits_external_send('ALLOW_EXTERNAL')": permits_external_send("ALLOW_EXTERNAL"),
    "config.EXTERNAL_SEND": config.EXTERNAL_SEND,
    "is_external_send_enabled()": config.is_external_send_enabled(),
})


class RatifiedValidator:
    """Stand-in for the post-M6-OD-003 validator: external_send_permitted becomes data-driven."""
    def validate(self, event_code):
        return ValidationResult(EventDecision.ACCEPT, event_code,
                                DataSensitivity.INTERNAL, True, None)


a3 = AuditLog()
store = WebEventLogStore()
svc = IngestService(RatifiedValidator(), store, ConsentGate(a3))
res = svc.ingest_event(
    event_code="VIEW_LANDING", page_id="p", session_id="s", source="web",
    event_ts=TS, raw_event_hash="h",
    # channel-supplied, never read through ConsentReader; scope is an uncoerced
    # JSON string that EXPLICITLY DENIES crm:
    consent_snapshot=ConsentSnapshot("cs_FORGED", "guest_x", ConsentState.VALID, TS,
                                     "{'crm': false, 'external_measurement': false}"),
    consent_scope=ConsentScope.CRM,
)
rep("B5-composite-egress", {
    "egress_eligible": res.egress_eligible,
    "notes": res.notes,
    "audit_records": [r.reason for r in a3.records],
    "seam ever calls config.is_external_send_enabled()?": False,
})

# ---- B6. does ingest.py reference the config choke point at all? --------
import inspect
import app.measurement.ingest as ing
src = inspect.getsource(ing)
rep("B6-choke-point-refs", {
    "'config' in ingest.py": "config" in src,
    "'is_external_send_enabled' in ingest.py": "is_external_send_enabled" in src,
    "'EXTERNAL_SEND' in ingest.py": "EXTERNAL_SEND" in src,
})
import app.measurement.consent.gate as gsrc
gs = inspect.getsource(gsrc)
rep("B6-gate-refs", {
    "'config' in gate.py": "config" in gs,
    "'captured_at' in gate.py": "captured_at" in gs,
    "'isinstance' in gate.py": "isinstance" in gs,
})
