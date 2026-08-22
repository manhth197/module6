"""BOUNDARY_ADVERSARY M6-P1005 - consent-bypass attacks vs slice M6.2A (read-only)."""
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, r"D:\M6\Module6-workspace\04-boundary\04-artifacts\impl\M6.2A")

from datetime import datetime, timezone
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


def rep(name, detail):
    print(f"[{name}] {detail}")


# ---- 0. enum hashing/equality ground truth --------------------------------
rep("A0-hash", {
    "hash(CRM)==hash('crm')": hash(ConsentScope.CRM) == hash("crm"),
    "hash(CRM)==hash('CRM')": hash(ConsentScope.CRM) == hash("CRM"),
    "CRM=='crm'": ConsentScope.CRM == "crm",
    "'crm' in frozenset({CRM})": "crm" in frozenset({ConsentScope.CRM}),
    "CRM in frozenset({'crm'})": ConsentScope.CRM in frozenset({"crm"}),
})

audit = AuditLog()
gate = ConsentGate(audit)

# ---- A1. consent_scope arrives as a plain STRING (uncoerced JSON scalar) ---
for raw in ["crm:false", "no_crm", "crm_denied", "external_measurement=DENIED",
            "{'crm': False, 'external_measurement': False}", "opt_out_of_crm"]:
    snap = ConsentSnapshot("cs_str", "guest_x", ConsentState.VALID, TS, raw)
    rep("A1-substring", {
        "consent_scope_raw": raw,
        "evaluate(CRM)": gate.evaluate(snap, ConsentScope.CRM),
        "evaluate(EXT_MEAS)": gate.evaluate(snap, ConsentScope.EXTERNAL_MEASUREMENT),
    })

# ---- A2. consent_scope arrives as list/set/dict of plain strings ----------
for cont in [["crm"], {"crm"}, frozenset({"crm"}), ("crm",), {"crm": False}]:
    snap = ConsentSnapshot("cs_c", "guest_x", ConsentState.VALID, TS, cont)
    rep("A2-untyped-container", {
        "container": repr(cont),
        "evaluate(CRM)": gate.evaluate(snap, ConsentScope.CRM),
    })

# ---- A3. frozen dataclass + MUTABLE aliased scope set ---------------------
live = set()                       # attacker keeps the reference
snap = ConsentSnapshot("cs_alias", "guest_x", ConsentState.VALID, TS, live)
before = gate.evaluate(snap, ConsentScope.CRM)
try:
    snap.consent_state = ConsentState.OPT_OUT
    direct = "MUTATED"
except Exception as e:
    direct = f"blocked: {type(e).__name__}"
live.add(ConsentScope.CRM)         # mutate the aliased container AFTER "freeze"
after = gate.evaluate(snap, ConsentScope.CRM)
rep("A3-alias-mutation", {
    "direct_attr_write": direct,
    "evaluate(CRM) before": before,
    "evaluate(CRM) after set.add": after,
    "snapshot_id_unchanged": snap.consent_snapshot_id,
})

# ---- A4. stale / post-dated snapshot: captured_at never checked -----------
old = ConsentSnapshot("cs_2019", "guest_x", ConsentState.VALID,
                      datetime(2019, 1, 1, tzinfo=timezone.utc),
                      frozenset({ConsentScope.CRM, ConsentScope.EXTERNAL_MEASUREMENT}))
future = ConsentSnapshot("cs_2099", "guest_x", ConsentState.VALID,
                         datetime(2099, 1, 1, tzinfo=timezone.utc),
                         frozenset({ConsentScope.CRM}))
rep("A4-freshness", {
    "captured_at=2019 evaluate(CRM)": gate.evaluate(old, ConsentScope.CRM),
    "captured_at=2099 evaluate(CRM)": gate.evaluate(future, ConsentScope.CRM),
})

# ---- A5. duck-typed / fabricated snapshot object (no isinstance check) ----
class Forged:
    consent_snapshot_id = "cs_FORGED"
    subject_ref = "guest_x"
    consent_state = ConsentState.VALID
    captured_at = TS
    consent_scope = frozenset({ConsentScope.CRM, ConsentScope.EXTERNAL_MEASUREMENT,
                               ConsentScope.AUDIENCE_SYNC})


rep("A5-forged-object", {"evaluate(CRM)": gate.evaluate(Forged(), ConsentScope.CRM)})


# ---- A6. seam-level: ingest never reads the ConsentReader port ------------
class Reg:
    def get(self, c):
        if c == "VIEW_LANDING":
            return EventRegistryRow(event_code="VIEW_LANDING",
                                    registration_state=RegistrationState.ACTIVE,
                                    owner="core.tracking", channel="web",
                                    data_sensitivity=DataSensitivity.INTERNAL)
        return None


audit2 = AuditLog()
store = WebEventLogStore()
svc = IngestService(EventValidator(Reg(), audit2), store, ConsentGate(audit2))
rep("A6-ingest-ctor-attrs", list(svc.__dict__.keys()))
res = svc.ingest_event(
    event_code="VIEW_LANDING", page_id="p1", session_id="s1", source="web",
    event_ts=TS, raw_event_hash="h1",
    consent_snapshot=ConsentSnapshot("cs_NEVER_ISSUED", "guest_x",
                                     ConsentState.VALID, TS,
                                     frozenset({ConsentScope.EXTERNAL_MEASUREMENT})),
)
rep("A6-fabricated-snapshot", {
    "notes": res.notes,
    "egress_eligible": res.egress_eligible,
    "store_methods": [m for m in dir(store) if not m.startswith("_")],
    "audit_reasons": [r.reason for r in audit2.records],
})
rep("A6-store-contents", [(r.log_id, r.consent_snapshot_id) for r in store.all()]
    if hasattr(store, "all") else "n/a")

# ---- A7. scope-agnostic egress_eligible in the seam -----------------------
res2 = svc.ingest_event(
    event_code="VIEW_LANDING", page_id="p2", session_id="s2", source="web",
    event_ts=TS, raw_event_hash="h2",
    consent_snapshot=ConsentSnapshot("cs_meas_only", "guest_x", ConsentState.VALID, TS,
                                     frozenset({ConsentScope.EXTERNAL_MEASUREMENT})),
)
rep("A7-scope-not-carried", {
    "IngestResult fields": list(res2.__dataclass_fields__),
    "scope recorded?": any("scope" in f for f in res2.__dataclass_fields__),
})


# ---- A8. permits_send robustness -----------------------------------------
class ReaderStr:
    def get(self, i): return None
    def current_state(self, s): return "VALID"          # raw str, not enum


class ReaderRaise:
    def get(self, i): return None
    def current_state(self, s): raise RuntimeError("consent service down")


good = ConsentSnapshot("cs_ok", "guest_x", ConsentState.VALID, TS,
                       frozenset({ConsentScope.CRM}))
rep("A8-permits_send-str", gate.permits_send(good, ConsentScope.CRM, ReaderStr()))
try:
    gate.permits_send(good, ConsentScope.CRM, ReaderRaise())
    rep("A8-reader-raises", "returned without exception")
except Exception as e:
    rep("A8-reader-raises", f"{type(e).__name__}: {e} -> propagates, no deny audit")

print("\n--- audit reasons on main gate:", [r.reason for r in audit.records])
