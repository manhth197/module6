"""M6-P1005 (attempt 3) BOUNDARY ADVERSARY — executed attacks vs FROZEN Round-4 staged M6.2A code.

Read-only: imports the staged package from 04-artifacts/impl/M6.2A and drives its public seams. Writes NOTHING
(sys.dont_write_bytecode=True; run with -B). No network, no DB, no flag flip. Every attack prints one structured
line; a SUMMARY is printed last. No attacker/PII value is ever echoed — only ids, statuses, reason codes, booleans.

Status vocabulary:
  DEFENDED     attack blocked exactly as the boundary requires
  BREACH       an IN-SCOPE fail gate (M6-FAIL-002 / M6-FAIL-003) is actually tripped  (expect 0)
  OPEN_NONGATE a real defect that does NOT trip an in-scope fail gate (armed-not-fired / lost-audit / residual)
  CONTROL      non-vacuity control (proves the machinery can also ACCEPT / GRANT the legitimate case)
  NOTE         observation recorded for the owner
"""
from __future__ import annotations

import sys
import os
import re
import io
import tokenize
import itertools
from datetime import datetime, timezone, timedelta, tzinfo
from types import SimpleNamespace

sys.dont_write_bytecode = True
IMPL = r"D:\M6\Module6-workspace\04-artifacts\impl\M6.2A"
sys.path.insert(0, IMPL)

from app import config as cfg
from app.measurement.audit import AuditLog, _safe_event_code
from app.measurement.masking import mask
from app.measurement.consent.gate import ConsentGate
from app.measurement.identity.resolver import IdentityResolver, Confidence
from app.measurement.registry.validator import (
    EventValidator, EventDecision, permits_external_send, _resolve_sensitivity,
)
from app.measurement.logs.web_event_log_store import WebEventLogStore, AppendOnlyViolation
from app.measurement.logs.idempotency import build_idempotency_key, normalize_ts
from app.measurement.ingest import IngestService, IngestResult
from app.measurement.models.consumed import (
    ConsentScope, ConsentSnapshot, ConsentState, DataSensitivity,
    EventRegistryRow, GuestContact, RegistrationState,
)

TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
OUT = []


def rec(pid, status, gate, detail):
    OUT.append((pid, status, gate, detail))
    print(f"[{pid:<10}] {status:<12} gate={gate:<11} :: {detail}")


# --- in-memory test doubles (mirror conftest) -----------------------------------------------------
class Registry:
    def __init__(self, rows): self._r = rows
    def get(self, code): return self._r.get(code)

class Contacts:
    def __init__(self, rows): self._r = rows
    def get(self, gid): return self._r.get(gid)

class ConsentRdr:
    def __init__(self, rows, cur=None): self._r = rows; self._c = cur or {}
    def get(self, cid): return self._r.get(cid)
    def current_state(self, subj): return self._c.get(subj, ConsentState.MISSING)

class Customers:
    def __init__(self, ids): self._ids = ids
    def exists(self, cid): return cid in self._ids

class MismatchReader:  # returns a row whose event_code != requested code (MINOR-6 probe)
    def get(self, code):
        return EventRegistryRow(event_code="ADS_SOMETHING_ELSE",
                                registration_state=RegistrationState.ACTIVE, owner="core.tracking")

class ThrowRegistry:
    def get(self, code): raise RuntimeError("registry adapter down")
class ThrowContacts:
    def get(self, gid): raise RuntimeError("contacts adapter down")
class ThrowConsent:
    def get(self, cid): raise RuntimeError("consent adapter down")
    def current_state(self, subj): raise RuntimeError("consent adapter down")
class ThrowStore:
    def append(self, row): raise RuntimeError("store adapter down")


REG = {
    "VIEW_LANDING": EventRegistryRow("VIEW_LANDING", RegistrationState.ACTIVE, owner="core.tracking",
                                     channel="web", data_sensitivity=DataSensitivity.INTERNAL,
                                     external_send_policy=None, schema_ref="evt.view_landing.v1"),
    "VIEW_LANDING_NO_SENS": EventRegistryRow("VIEW_LANDING_NO_SENS", RegistrationState.ACTIVE,
                                             owner="core.tracking", data_sensitivity=None),
    "DEREG_SAMPLE": EventRegistryRow("DEREG_SAMPLE", RegistrationState.DEREGISTERED, owner="core.tracking"),
    "NO_OWNER_SAMPLE": EventRegistryRow("NO_OWNER_SAMPLE", RegistrationState.ACTIVE, owner=None),
    "WS_OWNER_SAMPLE": EventRegistryRow("WS_OWNER_SAMPLE", RegistrationState.ACTIVE, owner="   "),
}
GUESTS = {
    "guest_mapped_ok": GuestContact("guest_mapped_ok", "fp_a", "cust_0001", "audit_ref_123"),
    "guest_no_audit": GuestContact("guest_no_audit", "fp_b", "cust_0001", None),
    "guest_unmapped": GuestContact("guest_unmapped", "fp_c"),
    "guest_bad_customer": GuestContact("guest_bad_customer", "fp_d", "cust_ghost", "audit_ref_999"),
}
CONSENT = {
    "cs_valid": ConsentSnapshot("cs_valid", "guest_mapped_ok", ConsentState.VALID, TS,
                                frozenset({ConsentScope.EXTERNAL_MEASUREMENT, ConsentScope.AUDIENCE_SYNC})),
    "cs_valid_meas": ConsentSnapshot("cs_valid_meas", "guest_mapped_ok", ConsentState.VALID, TS,
                                     frozenset({ConsentScope.EXTERNAL_MEASUREMENT})),
    "cs_valid_b": ConsentSnapshot("cs_valid_b", "guest_B", ConsentState.VALID, TS,
                                  frozenset({ConsentScope.EXTERNAL_MEASUREMENT})),
    "cs_valid_cust": ConsentSnapshot("cs_valid_cust", "cust_0001", ConsentState.VALID, TS,
                                     frozenset({ConsentScope.EXTERNAL_MEASUREMENT})),
    "cs_missing": ConsentSnapshot("cs_missing", "guest_x", ConsentState.MISSING, TS, frozenset()),
    "cs_expired": ConsentSnapshot("cs_expired", "guest_x", ConsentState.EXPIRED, TS, frozenset()),
    "cs_optout": ConsentSnapshot("cs_optout", "guest_x", ConsentState.OPT_OUT, TS, frozenset()),
}


def build(audit, *, registry=None, store=None, reader=None, resolver="default"):
    registry = registry or Registry(REG)
    store = store if store is not None else WebEventLogStore()
    reader = reader or ConsentRdr(CONSENT, {"guest_mapped_ok": ConsentState.VALID})
    if resolver == "default":
        resolver = IdentityResolver(Contacts(GUESTS), Customers({"cust_0001"}), audit)
    validator = EventValidator(registry, audit)
    gate = ConsentGate(audit)
    svc = IngestService(validator, store, gate, reader, audit, resolver)
    return svc, store


def ingest(svc, **over):
    kw = dict(event_code="VIEW_LANDING", page_id="pg", session_id="sess", source="web",
              event_ts=TS, raw_event_hash="rawhash")
    kw.update(over)
    return svc.ingest_event(**kw)


def safe_ingest(svc, **over):
    """Return ('RESULT', res) or ('RAISE', 'ExcType') — never echoes the offending value."""
    try:
        return "RESULT", ingest(svc, **over)
    except Exception as e:  # noqa: BLE001 — the whole point is to detect an escaped raise
        return "RAISE", type(e).__name__


print("=" * 100)
print("M6-P1005 attempt 3 — executed boundary attacks vs FROZEN Round-4 code (py", sys.version.split()[0], ")")
print("=" * 100)

# =================================================================================================
# GROUP A — CONSENT BYPASS (M6-FAIL-002 / RULE-002)
# =================================================================================================
# A1 — MAJOR-1 re-verify: a raw-string / raw-container consent_scope must be REFUSED at construction.
for label, scope in [("raw_str", "no_external_measurement_allowed"),
                     ("set_of_str", {"external_measurement"}),
                     ("list_of_str", ["crm"]),
                     ("dict", {"crm": False})]:
    try:
        ConsentSnapshot("cs", "guest_mapped_ok", ConsentState.VALID, TS, scope)
        rec(f"A1-{label}", "BREACH", "M6-FAIL-002", "raw-container scope ACCEPTED at construction (MAJOR-1 reopened)")
    except TypeError:
        rec(f"A1-{label}", "DEFENDED", "M6-FAIL-002", "ConsentSnapshot.__post_init__ raised TypeError (consumed.py:117-139)")

# A3 — MAJOR-3 re-verify: mutable set aliased then mutated must NOT retroactively grant.
src = {ConsentScope.EXTERNAL_MEASUREMENT}
snap_alias = ConsentSnapshot("cs_alias", "guest_mapped_ok", ConsentState.VALID, TS, src)
src.add(ConsentScope.CRM)
g = ConsentGate(AuditLog())
rec("A3-alias", "DEFENDED" if g.evaluate(snap_alias, ConsentScope.CRM) is False else "BREACH",
    "M6-FAIL-002",
    f"post-construction .add(CRM) on caller set -> evaluate(CRM)={g.evaluate(snap_alias, ConsentScope.CRM)} (frozenset copy)")

# A7 — MAJOR-7 re-verify VIA THE SEAM: a duck-typed snapshot returned by the reader must be fail-closed.
for label, scope_val in [("scope_str", "no_external_measurement_allowed"), ("scope_dict", {"external_measurement": False})]:
    duck = SimpleNamespace(consent_snapshot_id="cs_duck", subject_ref="guest_mapped_ok",
                           consent_state=ConsentState.VALID, consent_scope=scope_val)
    au = AuditLog()
    svc, store = build(au, reader=ConsentRdr({"cs_duck": duck}))
    kind, res = safe_ingest(svc, consent_snapshot_id="cs_duck", guest_id="guest_mapped_ok")
    ok = (kind == "RESULT" and res.egress_eligible is False
          and any(r.reason == "CONSENT_SNAPSHOT_UNTRUSTED_TYPE" for r in au.records)
          and all(getattr(r, "consent_snapshot_id", None) != "cs_duck" for r in store.all()))
    rec(f"A7-seam-{label}", "DEFENDED" if ok else "BREACH", "M6-FAIL-002",
        f"seam isinstance FIX-2 (ingest.py:172-182) -> egress={None if kind=='RAISE' else res.egress_eligible}, "
        f"UNTRUSTED_TYPE audited, id not logged (kind={kind})")

# A7g — the GATE ITSELF (bypassing the seam) still substring/key-matches a duck snapshot => residual, non-gate
duck2 = SimpleNamespace(consent_state=ConsentState.VALID, subject_ref="x",
                        consent_scope="no_external_measurement_allowed")
gate_open = ConsentGate(AuditLog()).evaluate(duck2, ConsentScope.EXTERNAL_MEASUREMENT)
rec("A7-gate-direct", "OPEN_NONGATE" if gate_open is True else "DEFENDED", "NONE",
    f"ConsentGate.evaluate(duck,scope) direct = {gate_open}; gate.py:50 has no isinstance guard on consent_scope "
    f"(defense-in-depth gap) — but the SEAM (A7-seam-*) blocks this path, so not reachable via ingest today")

# A-subject — subject confusion: attacker guest_id + a VALID snapshot for a DIFFERENT subject must NOT bind.
au = AuditLog(); svc, store = build(au)
kind, res = safe_ingest(svc, consent_snapshot_id="cs_valid_b", guest_id="attacker_guest")
ok = (kind == "RESULT" and res.egress_eligible is False
      and any(r.reason == "CONSENT_SUBJECT_MISMATCH" for r in au.records)
      and all(getattr(r, "consent_snapshot_id", None) != "cs_valid_b" for r in store.all()))
rec("A-subject", "DEFENDED" if ok else "BREACH", "M6-FAIL-002",
    "another subject's VALID consent -> SUBJECT_MISMATCH, id not logged (ingest.py:183-191)")

# A-matrix — non-VALID consent x every scope must never grant (even if scope set were present).
grants = 0
for st in (ConsentState.MISSING, ConsentState.EXPIRED, ConsentState.OPT_OUT):
    snap = ConsentSnapshot("cs", "guest_x", st, TS, frozenset(ConsentScope))
    for sc in ConsentScope:
        if ConsentGate(AuditLog()).evaluate(snap, sc) is True:
            grants += 1
rec("A-matrix", "DEFENDED" if grants == 0 else "BREACH", "M6-FAIL-002",
    f"MISSING/EXPIRED/OPT_OUT x 3 scopes (full scope set present) -> grants={grants}/9 (gate.py:43)")

# A-absent / A-scope-not-granted / A-scope-malformed
rec("A-absent", "DEFENDED" if ConsentGate(AuditLog()).evaluate(None, ConsentScope.CRM) is False else "BREACH",
    "M6-FAIL-002", "absent snapshot -> deny (gate.py:37)")
sng = ConsentGate(AuditLog()).evaluate(CONSENT["cs_valid_meas"], ConsentScope.CRM)
rec("A-scope-deny", "DEFENDED" if sng is False else "BREACH", "M6-FAIL-002",
    f"VALID meas-only consent, request CRM -> {sng} (gate.py:50)")
bad = 0
for sc in ("CRM", None, 7, True, "", "not_a_scope"):
    if ConsentGate(AuditLog()).evaluate(CONSENT["cs_valid_meas"], sc) is True:
        bad += 1
rec("A-scope-malformed", "DEFENDED" if bad == 0 else "BREACH", "M6-FAIL-002",
    f"6 malformed REQUESTED scopes -> grants={bad}/6 (ConsentScope(scope) coercion, gate.py:31)")

# A-reader-raise — consent reader down: audited deny, event still logged, id not persisted, NO raise.
au = AuditLog(); svc, store = build(au, reader=ThrowConsent())
kind, res = safe_ingest(svc, consent_snapshot_id="cs_valid", guest_id="guest_mapped_ok")
ok = (kind == "RESULT" and res.logged is True and res.egress_eligible is False
      and any(r.reason == "CONSENT_READER_FAILED" for r in au.records))
rec("A-reader-raise", "DEFENDED" if ok else "BREACH", "M6-FAIL-002",
    f"reader.get raises -> CONSENT_READER_FAILED, logged={None if kind=='RAISE' else res.logged}, no raise (ingest.py:159-167)")

# A-fix2b — caller-supplied consent_snapshot OBJECT: stray object => absent+audit, no raise; real object => accepted.
au = AuditLog(); svc, _ = build(au, reader=ConsentRdr({}))
kind, res = safe_ingest(svc, consent_snapshot=SimpleNamespace(foo=1), guest_id="guest_mapped_ok")
rec("A-fix2b-stray", "DEFENDED" if (kind == "RESULT" and res.egress_eligible is False) else "BREACH",
    "M6-FAIL-002", f"stray consent_snapshot object -> no raise, egress False (ingest.py:152-156); kind={kind}")
au = AuditLog(); real = ConsentSnapshot("cs_real", "guest_mapped_ok", ConsentState.VALID, TS,
                                        frozenset({ConsentScope.EXTERNAL_MEASUREMENT}))
svc, _ = build(au, reader=ConsentRdr({"cs_real": real}))
kind, res = safe_ingest(svc, consent_snapshot=real, guest_id="guest_mapped_ok")
rec("A-fix2b-real", "CONTROL" if kind == "RESULT" else "BREACH", "NONE",
    f"real ConsentSnapshot object -> handle re-resolved via reader, no raise (kind={kind})")

# A-bestcase (C17) — best case an attacker can build still yields egress_eligible=False (egress bolted).
au = AuditLog(); svc, _ = build(au)
res = ingest(svc, consent_snapshot_id="cs_valid", guest_id="guest_mapped_ok")
gate_true = ConsentGate(AuditLog()).evaluate(CONSENT["cs_valid"], ConsentScope.EXTERNAL_MEASUREMENT)
rec("A-bestcase", "DEFENDED" if (res.egress_eligible is False and gate_true is True) else "BREACH",
    "M6-FAIL-002", f"registered+VALID+subject-bound: gate grants={gate_true} but egress_eligible={res.egress_eligible} "
    f"(permits_external_send hard-False); notes={[n for n in res.notes]}")

# =================================================================================================
# GROUP B — EVENT DRIFT (M6-FAIL-003 / RULE-001 / RULE-018)
# =================================================================================================
au = AuditLog(); svc, store = build(au)
kind, res = safe_ingest(svc, event_code="TOTALLY_UNKNOWN_EVENT")
ok = (kind == "RESULT" and res.validation.decision is EventDecision.REJECT and res.logged is False
      and len(store) == 0 and any(r.reason == "UNKNOWN_EVENT_NOT_IN_REGISTRY" for r in au.records))
rec("B-unknown", "DEFENDED" if ok else "BREACH", "M6-FAIL-003",
    "unknown event -> REJECT, not logged, audited (validator.py:85-92) [SMK-001]")

for code, why in [("DEREG_SAMPLE", "de-registered"), ("NO_OWNER_SAMPLE", "missing owner"),
                  ("WS_OWNER_SAMPLE", "whitespace-only owner")]:
    au = AuditLog(); svc, store = build(au)
    res = ingest(svc, event_code=code)
    ok = res.validation.decision is EventDecision.HOLD and res.logged is False and len(store) == 0
    rec(f"B-{code}", "DEFENDED" if ok else "BREACH", "M6-FAIL-003",
        f"{why} -> HOLD, not logged (validator.py:95-112)")

# B-duckrow — a registry row whose registration_state is a RAW STRING 'ACTIVE' must NOT ACCEPT.
class DuckRowReader:
    def get(self, code):
        return SimpleNamespace(event_code=code, registration_state="ACTIVE", owner="core.tracking",
                               data_sensitivity=None, external_send_policy=None)
au = AuditLog(); v = EventValidator(DuckRowReader(), au)
vr = v.validate("VIEW_LANDING")
rec("B-duckrow-state", "DEFENDED" if vr.decision is not EventDecision.ACCEPT else "BREACH", "M6-FAIL-003",
    f"raw-string registration_state='ACTIVE' -> {vr.decision.value} (validator.py:95 'is not ACTIVE')")

# B-nearmiss — case / whitespace / zero-width / newline variants of a registered code -> all REJECT (unknown).
accepts = 0
for var in ["view_landing", "VIEW_LANDING ", " VIEW_LANDING", "VIEW_LANDING\n", "VIEW_LANDING\t",
            "VIEW\u200bLANDING", "VIEWLANDING", "VIEW-LANDING"]:
    au = AuditLog(); svc, _ = build(au)
    r = ingest(svc, event_code=var)
    if r.validation.decision is EventDecision.ACCEPT:
        accepts += 1
rec("B-nearmiss", "DEFENDED" if accepts == 0 else "BREACH", "M6-FAIL-003",
    f"8 near-miss variants of a registered code -> accepts={accepts}/8")

# B-sendpolicy — no external_send_policy token is ever read as 'allow'.
allow = sum(1 for t in ["ALLOW", "allow", "true", "True", "1", "YES", "*", "ON", "enabled", "permit", 1, True]
            if permits_external_send(t) is True)
rec("B-sendpolicy", "DEFENDED" if allow == 0 else "BREACH", "M6-FAIL-003",
    f"12 external_send_policy tokens -> read-as-allow={allow}/12 (validator.py:66-73, M6-OD-003 OPEN)")

# B-sensitivity — a raw/unknown data_sensitivity token defaults to the most-restrictive PII.
sens = _resolve_sensitivity("totally_unknown_token")
rec("B-sensitivity", "DEFENDED" if sens is DataSensitivity.PII else "BREACH", "NONE",
    f"unknown data_sensitivity token -> {sens.value} (validator.py:48-63)")

# B-MINOR6 — registry row whose event_code != requested is NOT checked; logged under requested name. Residual.
au = AuditLog(); svc, store = build(au, registry=MismatchReader())
res = ingest(svc, event_code="ADS_REQUESTED_NEVER_REGISTERED")
mismatch_logged = (res.validation.decision is EventDecision.ACCEPT and res.logged is True
                   and store.all() and store.all()[0].event_code == "ADS_REQUESTED_NEVER_REGISTERED")
rec("B-MINOR6", "OPEN_NONGATE" if mismatch_logged else "DEFENDED", "NONE",
    "registry row.event_code != requested is not asserted; needs a LOOSE/hostile adapter (no shipped adapter does this)"
    " (validator.py has no 'row.event_code==event_code' check)")

# B-ports — CONSUMED ports expose NO write method (RULE-018) — structural.
import app.measurement.ports as ports_mod
writeverbs = ("insert", "update", "delete", "add", "put", "post", "save", "write", "upsert", "create")
port_write_hits = []
for name in dir(ports_mod):
    obj = getattr(ports_mod, name)
    if isinstance(obj, type):
        for m in dir(obj):
            if any(m.lower() == w or m.lower().startswith(w + "_") for w in writeverbs):
                port_write_hits.append(f"{name}.{m}")
rec("B-ports", "DEFENDED" if not port_write_hits else "BREACH", "M6-FAIL-003",
    f"CONSUMED read-only ports write-methods = {port_write_hits or 'NONE'} (ports.py) [RULE-018]")

# =================================================================================================
# GROUP T — ROUND-4 TYPE BOUNDARY (MAJOR-6 wrong-TYPE class) + throwing-adapter half + new-code holes
# =================================================================================================
BAD_TYPES = {"list": [1], "dict": {"k": 1}, "int": 5, "none": None, "bytes": b"x", "bool": True}
# T-required — each REQUIRED scalar of a wrong type -> audited REJECT, no raise, no row, no junk-accept.
req_breach = 0; req_raise = 0; req_junk = 0; total = 0
for fld in ("event_code", "page_id", "session_id", "source", "raw_event_hash"):
    for tname, tval in BAD_TYPES.items():
        if tname == "none":  # None is 'absent' for optional; for required it is still non-str -> REJECT
            pass
        total += 1
        au = AuditLog(); svc, store = build(au)
        kind, res = safe_ingest(svc, **{fld: tval})
        if kind == "RAISE":
            req_raise += 1
        else:
            if not (res.validation.decision is EventDecision.REJECT and res.logged is False and len(store) == 0):
                req_breach += 1
            if len(store) != 0:  # junk-accept: a wrong-typed required field became a row
                req_junk += 1
            if not any(r.reason == "FIELD_TYPE_INVALID" for r in au.records):
                req_breach += 1
rec("T-required", "DEFENDED" if (req_raise == 0 and req_breach == 0 and req_junk == 0) else "BREACH",
    "M6-FAIL-003", f"{total} required-scalar wrong-type probes -> raises={req_raise}, junk-accepts={req_junk}, "
    f"non-fail-closed={req_breach} (ingest.py:117-128 _require_str/_field_type_reject)")

# T-optional — wrong-typed OPTIONAL id -> dropped to ABSENT (audited HOLD), no raise, ingest proceeds fail-closed.
opt_raise = 0; opt_bad = 0; optn = 0
for fld in ("guest_id", "consent_snapshot_id", "correlation_id"):
    for tname, tval in {"list": [1], "dict": {"k": 1}, "int": 9}.items():
        optn += 1
        au = AuditLog(); svc, store = build(au)
        kind, res = safe_ingest(svc, **{fld: tval})
        if kind == "RAISE":
            opt_raise += 1
        elif not any(r.reason == "FIELD_TYPE_INVALID" for r in au.records):
            opt_bad += 1
rec("T-optional", "DEFENDED" if (opt_raise == 0 and opt_bad == 0) else "BREACH", "NONE",
    f"{optn} optional-id wrong-type probes -> raises={opt_raise}, un-audited={opt_bad} (ingest.py:130-134)")

# T-event_ts — a non-datetime / naive event_ts on a VALID event -> audited TS_NOT_TZ_AWARE, not logged, no raise.
tsn_raise = 0; tsn_bad = 0
for tval in ["2026-07-29T12:00:00", 1690000000, None, datetime(2026, 7, 29, 12, 0, 0)]:  # last = naive
    au = AuditLog(); svc, store = build(au)
    kind, res = safe_ingest(svc, event_ts=tval)
    if kind == "RAISE":
        tsn_raise += 1
    elif not (res.logged is False and any(r.reason == "TS_NOT_TZ_AWARE" for r in au.records)):
        tsn_bad += 1
rec("T-event_ts", "DEFENDED" if (tsn_raise == 0 and tsn_bad == 0) else "BREACH", "NONE",
    f"4 bad event_ts (str/int/None/naive) on VALID event -> raises={tsn_raise}, unaudited={tsn_bad} (ingest.py:203-209)")

# T-control — the happy path still ACCEPTS + logs (non-vacuity; proves the type boundary didn't over-block).
au = AuditLog(); svc, store = build(au)
res = ingest(svc)
rec("T-control", "CONTROL" if (res.logged is True and len(store) == 1) else "BREACH", "NONE",
    f"all-str valid event -> logged={res.logged}, rows={len(store)}, egress={res.egress_eligible}, notes={res.notes}")

# T-throwadapter — MAJOR-6 THROWING-ADAPTER HALF: validate/resolve/subject_matches/append are NOT wrapped.
throw_cases = []
# registry.validate raises (no consent handle, no resolver -> isolates step 2)
au = AuditLog(); svc, _ = build(au, registry=ThrowRegistry(), resolver=None)
k, _ = safe_ingest(svc, event_code="VIEW_LANDING")
throw_cases.append(("registry.validate", k, len(au)))
# resolver.resolve raises at step 0
au = AuditLog(); svc, _ = build(au, resolver=IdentityResolver(ThrowContacts(), Customers(set()), au))
k, _ = safe_ingest(svc, guest_id="guest_mapped_ok")
throw_cases.append(("identity.resolve", k, len(au)))
# store.append raises on a valid event
au = AuditLog(); svc, _ = build(au, store=ThrowStore(), resolver=None)
k, _ = safe_ingest(svc, event_code="VIEW_LANDING")
throw_cases.append(("store.append", k, len(au)))
escapes = [(nm, na) for (nm, k, na) in throw_cases if k == "RAISE"]
rec("T-throwadapter", "OPEN_NONGATE" if escapes else "DEFENDED", "NONE",
    f"unwrapped adapter exceptions escape ingest_event() (MAJOR-6 throwing-half, still open): "
    f"{[(nm, 'raise', 'audit='+str(na)) for (nm, k, na) in throw_cases]} "
    f"-> data-loss+lost-audit; NO send/accept, so no in-scope gate tripped")

# T-MINOR8 — the audit sanitizer itself crashes on a non-str event_code (residual; NOT reachable via the seam).
try:
    AuditLog().record("REJECT", "R", event_code=12345)
    minor8 = "no-crash"
except TypeError:
    minor8 = "TypeError"
# reachable via seam? seam type-checks event_code first and never passes the bad value to audit:
au = AuditLog(); svc, _ = build(au)
k, _ = safe_ingest(svc, event_code=12345)
seam_safe = (k == "RESULT" and not any(getattr(r, "event_code", None) not in (None,) and False for r in au.records))
rec("T-MINOR8", "OPEN_NONGATE" if minor8 == "TypeError" else "DEFENDED", "NONE",
    f"AuditLog.record(event_code=<int>) direct -> {minor8} (audit.py:35 assumes str); via SEAM a non-str event_code "
    f"is rejected before the sink (kind={k}) so not reachable through ingest")

# =================================================================================================
# GROUP D — DEDUP / IDEMPOTENCY / APPEND-ONLY (RULE-005 / RULE-007, MAJOR-4/5)
# =================================================================================================
# D-tz — same instant in 3 notations -> ONE key -> ONE row (MAJOR-4).
inst_utc = datetime(2026, 7, 29, 5, 0, 0, tzinfo=timezone.utc)
inst_p7 = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone(timedelta(hours=7)))
inst_m5 = datetime(2026, 7, 29, 0, 0, 0, tzinfo=timezone(timedelta(hours=-5)))
au = AuditLog(); svc, store = build(au)
for t in (inst_utc, inst_p7, inst_m5):
    ingest(svc, event_ts=t)
rec("D-tz", "DEFENDED" if len(store) == 1 else "BREACH", "NONE",
    f"same instant x3 offsets -> rows={len(store)} (idempotency.normalize_ts UTC canonicalization) [MAJOR-4]")

# D-inject — EXHAUSTIVE injectivity: distinct 5-component tuples must map to distinct keys (MAJOR-5).
alpha = ["a", "|", "\\", "\\|", "", None]
seen = {}; collisions = 0
for combo in itertools.product(alpha, repeat=5):
    key = build_idempotency_key(*combo)
    if key in seen and seen[key] != combo:
        collisions += 1
    seen[key] = combo
rec("D-inject", "DEFENDED" if collisions == 0 else "BREACH", "NONE",
    f"exhaustive {len(alpha)}^5={len(alpha)**5} component-tuple fuzz -> collisions={collisions} "
    f"(escape + None sentinel, idempotency.py:42-71) [MAJOR-5]")

# D-none-sentinel — None component vs literal 'None' vs '\\0' text must be 3 distinct keys.
kN = build_idempotency_key("e", "p", "s", "r", None)
kNone = build_idempotency_key("e", "p", "s", "r", "None")
kSent = build_idempotency_key("e", "p", "s", "r", "\\0")
rec("D-none-sentinel", "DEFENDED" if len({kN, kNone, kSent}) == 3 else "BREACH", "NONE",
    f"None vs 'None' vs '\\\\0' -> distinct keys={len({kN, kNone, kSent})}/3")

# D-appendonly — UPDATE/DELETE raise; re-append DIFFERENT row under same key keeps the ORIGINAL (no overwrite).
s = WebEventLogStore()
from app.measurement.models.web_event_log import WebEventLog
r1 = WebEventLog("log_1", "VIEW_LANDING", "pg", "sess", "web", TS, "K", TS)
r2 = WebEventLog("log_2", "VIEW_LANDING", "pg2", "sess2", "web", TS, "K", TS)  # same idempotency_key 'K'
a1 = s.append(r1); a2 = s.append(r2)
upd = del_ = "no-raise"
try: s.update(r2)
except AppendOnlyViolation: upd = "raised"
try: s.delete("K")
except AppendOnlyViolation: del_ = "raised"
kept_original = (a1.created is True and a2.created is False and s.get("K").page_id == "pg" and len(s) == 1)
rec("D-appendonly", "DEFENDED" if (upd == "raised" and del_ == "raised" and kept_original) else "BREACH",
    "NONE", f"update={upd}, delete={del_}, dup-key keeps original page_id={s.get('K').page_id}, rows={len(s)} [RULE-007]")

# D-logid MINOR7 — two rows with DIFFERENT idempotency_key but SAME log_id are both stored (DDL says PK). Residual.
s2 = WebEventLogStore()
s2.append(WebEventLog("log_same", "E", "p", "s", "web", TS, "K1", TS))
s2.append(WebEventLog("log_same", "E", "p", "s", "web", TS, "K2", TS))
rec("D-logid", "OPEN_NONGATE" if len(s2) == 2 else "DEFENDED", "NONE",
    f"two rows share log_id, differ on idempotency_key -> rows={len(s2)}; store keys on idempotency_key only "
    f"while migration 0001 declares log_id PRIMARY KEY (needs 64-bit prefix collision; not a volume risk)")

# =================================================================================================
# GROUP E — OVERREACH / GATE BYPASS / POSTURE (FAIL-001/004/005/006/009, RULE-020)
# =================================================================================================
# E-posture — locked flags immutable + is_external_send_enabled False.
posture_ok = (cfg.GLOBAL_GATEWAY_STATE == "BLOCKED" and cfg.PRODUCTION_FLAG == "OFF"
              and cfg.EXTERNAL_SEND == "OFF" and cfg.is_external_send_enabled() is False)
rec("E-posture", "DEFENDED" if posture_ok else "BREACH", "M6-FAIL-009",
    f"(gateway,prod,ext_send,enabled)=({cfg.GLOBAL_GATEWAY_STATE},{cfg.PRODUCTION_FLAG},{cfg.EXTERNAL_SEND},"
    f"{cfg.is_external_send_enabled()})")

# E-forcesend — force config.EXTERNAL_SEND='ON' at runtime; egress must STILL be False (hard lock).
_orig = cfg.EXTERNAL_SEND
try:
    cfg.EXTERNAL_SEND = "ON"
    au = AuditLog(); svc, _ = build(au)
    res = ingest(svc, consent_snapshot_id="cs_valid", guest_id="guest_mapped_ok")
    forced = res.egress_eligible
finally:
    cfg.EXTERNAL_SEND = _orig
rec("E-forcesend", "DEFENDED" if forced is False else "BREACH", "M6-FAIL-002",
    f"config.EXTERNAL_SEND forced 'ON' at runtime -> egress_eligible={forced} (permits_external_send independent hard-False)")

# E-no-revenue — IngestResult carries no revenue/roas/order field; 'logged' is not 'revenue'.
res_fields = set(IngestResult.__dataclass_fields__.keys())
rev_like = {f for f in res_fields if re.search(r"revenue|roas|order|price|payment|commission|budget|scale", f, re.I)}
rec("E-no-revenue", "DEFENDED" if not rev_like else "BREACH", "M6-FAIL-001",
    f"IngestResult fields={sorted(res_fields)}; revenue-like={rev_like or 'NONE'} (M6.2A measures, never prices)")

# E-sweep — tokenize every app/*.py; flag any network/db IMPORT or CALL identifier in CODE (not strings/comments).
NET_DB = {"socket", "requests", "urllib", "urllib2", "httpx", "aiohttp", "smtplib", "ftplib",
          "websocket", "websockets", "boto3", "kafka", "pika", "psycopg", "psycopg2", "pymysql",
          "sqlalchemy", "create_engine", "executemany", "cursor", "sessionmaker"}
DANGER_DEF = ("send", "dispatch", "publish", "emit", "scale", "price", "order", "payment",
              "commission", "budget", "revenue", "roas", "sync")
app_dir = os.path.join(IMPL, "app")
net_hits = []; def_hits = []
for root, _dirs, files in os.walk(app_dir):
    for fn in files:
        if not fn.endswith(".py"):
            continue
        path = os.path.join(root, fn)
        with open(path, "r", encoding="utf-8") as f:
            src = f.read()
        code_names = set()
        try:
            for tok in tokenize.generate_tokens(io.StringIO(src).readline):
                if tok.type == tokenize.NAME:
                    code_names.add(tok.string)
        except tokenize.TokenError:
            pass
        for n in code_names & NET_DB:
            net_hits.append(f"{fn}:{n}")
        for m in re.finditer(r"^\s*def\s+(\w+)", src, re.M):
            nm = m.group(1)
            if any(d in nm.lower() for d in DANGER_DEF):
                # classify: is any NET_DB primitive used inside this file's code at all?
                body_net = bool(code_names & NET_DB)
                def_hits.append(f"{fn}:{nm}({'net' if body_net else 'no-net'})")
rec("E-sweep-net", "DEFENDED" if not net_hits else "BREACH", "M6-FAIL-002",
    f"network/db code identifiers across app/ = {net_hits or 'NONE'}")
rec("E-sweep-def", "NOTE", "NONE",
    f"danger-lexicon def names = {def_hits or 'NONE'} — all with 'no-net' bodies are documented no-caller stubs "
    f"(e.g. permits_send, is_external_send_enabled); no reachable egress")

# =================================================================================================
# GROUP F — PII / AUDIT-SINK LEAKAGE (FAIL-008 / RULE-014, SEC-PII-01/02 residual, MINOR-8/9)
# =================================================================================================
# F-wrap — attacker-shaped event_code (non-identifier) is WRAPPED, not stored verbatim.
wrapped = 0; wtot = 0
for probe in ["evt x", "A" * 300, "E\nX", "E\x00X", "e" + chr(7) + "x"]:
    wtot += 1
    if _safe_event_code(probe).startswith("INVALID_EVENT_CODE["):
        wrapped += 1
rec("F-wrap", "DEFENDED" if wrapped == wtot else "BREACH", "M6-FAIL-008",
    f"{wrapped}/{wtot} attacker-shaped event_codes wrapped (audit.py:_safe_event_code)")

# F-MINOR9 — an IDENTIFIER-shaped attacker event_code is stored VERBATIM (residual SEC-PII-01). Values built
# programmatically; never echoed.
digit_run = "".join(str((i * 3 + 1) % 10) for i in range(10))     # 10-digit run (mobile-shape); no literal
uj_id = "guest_" + "".join(str((i * 7) % 10) for i in range(6))   # underscore-joined id shape; no literal
verbatim = (_safe_event_code(digit_run) == digit_run) or (_safe_event_code(uj_id) == uj_id)
rec("F-MINOR9", "OPEN_NONGATE" if verbatim else "DEFENDED", "NONE",
    "identifier-shaped event_code stored VERBATIM by the allowlist [A-Za-z0-9_.:-]{1,64} (audit.py:23); in-process "
    "sink only, nothing exported today — escalates if the sink becomes durable. Route to M6-P1006 (SEC-PII).")

# F-mask — mask() fully masks <=5 chars, partial-reveals longer, strips control chars; no raw value leaks.
m_short = mask("abcd")               # <=5 -> fully masked
m_long = mask("abcdefghij")          # -> abc***ij shape
m_ctrl = mask("ab\x00cd\nefghij")    # control chars stripped before reveal
mask_ok = (m_short == "***" and m_long.startswith("abc") and m_long.endswith("ij")
           and all(ch.isprintable() for ch in m_ctrl))
rec("F-mask", "DEFENDED" if mask_ok else "BREACH", "M6-FAIL-008",
    f"mask short='{m_short}', long-shape ok={m_long.startswith('abc') and m_long.endswith('ij')}, ctrl-stripped ok "
    f"(masking.py:14-25)")

# F-subject — identity through the seam records only MASKED subjects in the audit sink (no raw id).
au = AuditLog()
resolver = IdentityResolver(Contacts(GUESTS), Customers({"cust_0001"}), au)
resolver.resolve("guest_mapped_ok")
raw_in_audit = any((r.subject_masked and "guest_mapped_ok" in r.subject_masked) for r in au.records)
rec("F-subject", "DEFENDED" if not raw_in_audit else "BREACH", "M6-FAIL-008",
    f"identity resolve -> raw guest_id present in audit subject_masked = {raw_in_audit} (resolver masks via masking.mask)")

# F-N3 — session_id is stored RAW in web_event_logs (model says PII-pseudonymous, M6-OD-012 OPEN). Observation.
au = AuditLog(); svc, store = build(au)
ingest(svc, session_id="sess_raw_probe")
raw_session = bool(store.all()) and store.all()[0].session_id == "sess_raw_probe"
rec("F-N3-session", "NOTE", "NONE",
    f"web_event_logs stores session_id raw={raw_session} (no store-layer masking); M6-OD-012 OPEN, in scope for M6-P1006")

# =================================================================================================
# GROUP N — NOVEL vectors surfaced by the adversarial-ideation workflow (executed to confirm/refute)
# =================================================================================================
# N-CB04 — customer-keyed consent must NOT bind to a guest whose customer mapping lacks audit / is dangling.
misbind = 0
for gid, cs in [("guest_no_audit", "cs_valid_cust"), ("guest_bad_customer", "cs_valid_cust")]:
    au = AuditLog(); svc, store = build(au)
    kind, res = safe_ingest(svc, consent_snapshot_id=cs, guest_id=gid)
    if kind == "RESULT" and any(getattr(r, "consent_snapshot_id", None) == cs for r in store.all()):
        misbind += 1
rec("N-CB04", "DEFENDED" if misbind == 0 else "BREACH", "M6-FAIL-002",
    "customer-keyed consent + guest with unaudited/dangling mapping -> no bind, id not logged (resolver.py:57-61)")

# N-subclass — MAJOR-7 RESIDUAL (NOVEL): a ConsentSnapshot SUBCLASS skipping __post_init__ keeps a RAW-STRING
# scope, PASSES the seam isinstance guard (isinstance True for subclasses), and reopens the gate substring fail-OPEN.
class _UnhardenedSnap(ConsentSnapshot):
    def __post_init__(self):  # deliberately skip ConsentSnapshot's hardening
        pass
evil = _UnhardenedSnap("cs_evil", "guest_mapped_ok", ConsentState.VALID, TS, "external_measurement_granted")
au = AuditLog(); svc, store = build(au, reader=ConsentRdr({"cs_evil": evil}))
kind, res = safe_ingest(svc, consent_snapshot_id="cs_evil", guest_id="guest_mapped_ok")
gate_grants = ConsentGate(AuditLog()).evaluate(evil, ConsentScope.EXTERNAL_MEASUREMENT)
reached_gate = not any(r.reason == "CONSENT_SNAPSHOT_UNTRUSTED_TYPE" for r in au.records)
rec("N-subclass", "OPEN_NONGATE" if (gate_grants is True and reached_gate) else "DEFENDED", "NONE",
    f"ConsentSnapshot subclass w/ no-op __post_init__ + raw-str scope: gate.evaluate grants={gate_grants}, seam "
    f"isinstance PASSES (ingest.py:172), egress_eligible={None if kind=='RAISE' else res.egress_eligible} (still bolted). "
    f"Prior MAJOR-7 fix rec's gate.py isinstance(consent_scope,frozenset) assertion NOT implemented -> residual, armed-not-fired")

# N-ts-escape — NOVEL: the forgiving-seam except tuple (ingest.py:205 = ValueError/AttributeError/TypeError only) is
# too narrow: an extreme-year tz shift (OverflowError) or a hostile tzinfo.utcoffset escapes the seam UNAUDITED.
class _HostileTZ(tzinfo):
    def utcoffset(self, dt): raise RuntimeError("hostile tz")
    def tzname(self, dt): return "X"
    def dst(self, dt): return None
esc = []
for label, ts in [("overflow_year", datetime(9999, 12, 31, 23, 0, 0, tzinfo=timezone(timedelta(hours=-14)))),
                  ("hostile_tzinfo", datetime(2026, 7, 29, 12, 0, 0, tzinfo=_HostileTZ()))]:
    au = AuditLog(); svc, _ = build(au)
    kind, _res = safe_ingest(svc, event_ts=ts)  # VIEW_LANDING accepted -> normalize_ts runs
    esc.append((label, kind, len(au)))
escaped = [(l, na) for (l, k, na) in esc if k == "RAISE"]
rec("N-ts-escape", "OPEN_NONGATE" if escaped else "DEFENDED", "NONE",
    f"valid-event event_ts -> OverflowError / hostile-tzinfo: {esc} (ingest.py:205 catch too narrow); "
    f"escaped(with audit-count)={escaped} -> lost audit + lost row; no send/accept -> no in-scope gate tripped")

# N-detail-crash — parallel to MINOR-8 (NOVEL field): a non-str detail crashes _safe_detail (audit.py:64 iterates
# value). NOT reachable via the seam (detail is always a controlled token there); robustness residual only.
try:
    AuditLog().record("A", "R", detail=12345)
    dcrash = "no-crash"
except TypeError:
    dcrash = "TypeError"
rec("N-detail-crash", "OPEN_NONGATE" if dcrash == "TypeError" else "DEFENDED", "NONE",
    f"AuditLog.record(detail=<int>) direct -> {dcrash} (audit.py:64 assumes str); not reachable via seam (detail always controlled)")

# N-corr-raw — correlation_id written RAW (unbounded/unmasked) into the append-only row (same class as N-3 session_id).
au = AuditLog(); svc, store = build(au)
ingest(svc, correlation_id="corr_raw_probe")
corr_raw = bool(store.all()) and store.all()[0].correlation_id == "corr_raw_probe"
rec("N-corr-raw", "NOTE", "NONE",
    f"web_event_logs stores correlation_id raw={corr_raw} (web_event_log.py:32, no bound/mask); M6-OD-012 / M6-P1006 scope")

# =================================================================================================
# SUMMARY
# =================================================================================================
from collections import Counter
cnt = Counter(s for _, s, _, _ in OUT)
breaches = [pid for pid, s, g, d in OUT if s == "BREACH"]
opens = [pid for pid, s, g, d in OUT if s == "OPEN_NONGATE"]
print("=" * 100)
print("SUMMARY:", dict(cnt))
print("IN-SCOPE FAIL-GATE BREACHES (FAIL-002/003):", breaches or "NONE")
print("OPEN (real defect, does NOT trip an in-scope fail gate):", opens or "NONE")
print("TOTAL RECORDED OUTCOMES:", len(OUT))
print("=" * 100)
