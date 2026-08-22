"""M6-P1105 BOUNDARY ADVERSARY — executed attacks vs FROZEN staged M6.2B tracking pipeline.

Read-only: imports the staged package from 04-artifacts/impl/M6.2B and drives its public seams (the
POST /api/ads/events/track handler, the frontend hook, both append-only stores, the hardened seam). Writes
NOTHING (sys.dont_write_bytecode=True; run with -B). No network, no DB, no flag flip. One structured line per
attack; a SUMMARY last. No attacker/PII value is ever echoed — only ids, statuses, reason codes, booleans.

Status vocabulary:
  DEFENDED     attack blocked as required
  BREACH       the IN-SCOPE fail gate M6-FAIL-003 (event drift) is actually tripped  (expect 0)
  OPEN_NONGATE a real defect that does NOT trip M6-FAIL-003 (robustness / dedup nuance / needs-hostile-adapter)
  CONTROL      non-vacuity control (the pipeline can also ACCEPT the legitimate case)
  NOTE         observation for the owner / routed to M6-P1106
"""
from __future__ import annotations

import sys
import os
import io
import re
import tokenize
import itertools
from datetime import datetime, timezone, timedelta, tzinfo
from types import SimpleNamespace

sys.dont_write_bytecode = True
IMPL = r"D:\M6\Module6-workspace\04-artifacts\impl\M6.2B"
sys.path.insert(0, IMPL)

from app import config as cfg
from app.api.track import handle_track_request, TrackDeps, _raw_event_hash, _contains_raw_pii
from app.measurement.audit import AuditLog, _safe_event_code, _looks_like_identifier
from app.measurement.masking import mask
from app.measurement.ingest import IngestService
from app.measurement.consent.gate import ConsentGate
from app.measurement.identity.resolver import IdentityResolver
from app.measurement.registry.validator import EventValidator, EventDecision, permits_external_send
from app.measurement.logs.web_event_log_store import WebEventLogStore, AppendOnlyViolation
from app.measurement.logs.idempotency import build_idempotency_key, normalize_ts
from app.measurement.store.measurement_event_store import MeasurementEventStore, MeasurementStoreViolation
from app.measurement.models.measurement_event import AdsMeasurementEvent, DataQualityStatus
from app.measurement.models.consumed import (
    ConsentScope, ConsentSnapshot, ConsentState, DataSensitivity,
    EventRegistryRow, GuestContact, RegistrationState,
)
from app.measurement.adapters.consent_reader import InMemoryConsentReader
from app.measurement.tracking.hooks import TrackingHook
from app.measurement.tracking.base_events import is_locked_base_event, LOCKED_BASE_EVENTS

TS_STR = "2026-07-29T12:00:00+00:00"
OUT = []


def rec(pid, status, gate, detail):
    OUT.append((pid, status, gate, detail))
    print(f"[{pid:<16}] {status:<12} gate={gate:<11} :: {detail}")


# --- test doubles (mirror conftest) ---------------------------------------------------------------
class Registry:
    def __init__(self, rows): self._r = rows
    def get(self, code): return self._r.get(code)

class MismatchRegistry:  # returns an ACTIVE row whose event_code != requested (MINOR-6)
    def get(self, code):
        return EventRegistryRow(event_code="ADS_SOMETHING_ELSE",
                                registration_state=RegistrationState.ACTIVE, owner="core.tracking")

class Contacts:
    def __init__(self, rows): self._r = rows
    def get(self, gid): return self._r.get(gid)

class Customers:
    def __init__(self, ids): self._ids = ids
    def exists(self, cid): return cid in self._ids

class ThrowRegistry:
    def get(self, code): raise RuntimeError("registry adapter down")
class ThrowContacts:
    def get(self, gid): raise RuntimeError("contacts adapter down")
class ThrowReader:
    def get(self, cid): raise RuntimeError("consent adapter down")
    def current_state(self, subj): raise RuntimeError("down")
class ThrowStore(WebEventLogStore):
    def append(self, row): raise RuntimeError("store adapter down")


REG = {
    "VIEW_LANDING": EventRegistryRow("VIEW_LANDING", RegistrationState.ACTIVE, owner="core.tracking",
                                     channel="web", data_sensitivity=DataSensitivity.INTERNAL,
                                     external_send_policy=None, schema_ref="evt.view_landing.v1"),
    "DEREG_SAMPLE": EventRegistryRow("DEREG_SAMPLE", RegistrationState.DEREGISTERED, owner="core.tracking"),
    "NO_OWNER_SAMPLE": EventRegistryRow("NO_OWNER_SAMPLE", RegistrationState.ACTIVE, owner=None),
}
GUESTS = {
    "guest_mapped_ok": GuestContact("guest_mapped_ok", "fp_a", "cust_0001", "audit_ref_123"),
}
CONSENT = {
    "cs_valid": ConsentSnapshot("cs_valid", "guest_mapped_ok", ConsentState.VALID, datetime(2026, 7, 29, 12, tzinfo=timezone.utc),
                                frozenset({ConsentScope.EXTERNAL_MEASUREMENT, ConsentScope.AUDIENCE_SYNC})),
}


def make_deps(*, registry=None, reader=None, resolver="default", store=None, mstore=None):
    audit = AuditLog()
    registry = registry or Registry(REG)
    store = store if store is not None else WebEventLogStore()
    mstore = mstore if mstore is not None else MeasurementEventStore()
    reader = reader or InMemoryConsentReader(snapshots=CONSENT, current={"guest_mapped_ok": ConsentState.VALID})
    if resolver == "default":
        resolver = IdentityResolver(Contacts(GUESTS), Customers({"cust_0001"}), audit)
    validator = EventValidator(registry, audit)
    gate = ConsentGate(audit)
    ingest = IngestService(validator, store, gate, reader, audit, resolver=resolver)
    deps = TrackDeps(ingest_service=ingest, web_store=store, measurement_store=mstore, audit=audit)
    return deps, store, mstore, audit


def body(**over):
    b = {"event_code": "VIEW_LANDING", "page_id": "p1", "session_id": "s1", "source": "web",
         "consent_snapshot_id": "cs_valid", "event_ts": TS_STR,
         "idempotency_key": "client-ignored", "correlation_id": "corr_test"}
    b.update(over)
    return b


def post(deps, b):
    return handle_track_request(b, deps)


def safe_post(deps, b):
    try:
        return "RESULT", handle_track_request(b, deps)
    except Exception as e:  # noqa: BLE001 — detecting an escaped raise IS the test
        return "RAISE", type(e).__name__


print("=" * 104)
print("M6-P1105 — executed boundary attacks vs FROZEN M6.2B tracking pipeline (py", sys.version.split()[0], ")")
print("=" * 104)

# =================================================================================================
# GROUP TR — EVENT DRIFT via the endpoint (M6-FAIL-003 / RULE-001) + two-layer independence
# =================================================================================================
d, ws, ms, au = make_deps()
r = post(d, body(event_code="TOTALLY_UNKNOWN_EVENT"))
ok = (r.status == "REJECTED" and r.error_code == "UNKNOWN_EVENT" and len(ws) == 0 and len(ms) == 0
      and any(x.reason == "UNKNOWN_EVENT_NOT_IN_REGISTRY" for x in au.records))
rec("TR-unknown", "DEFENDED" if ok else "BREACH", "M6-FAIL-003",
    f"unknown event -> {r.status}/{r.error_code}, web={len(ws)} meas={len(ms)}, audited (track.py:150-158) [SMK-001 layer-2]")

for code, why in [("DEREG_SAMPLE", "de-registered"), ("NO_OWNER_SAMPLE", "missing-owner")]:
    d, ws, ms, au = make_deps()
    r = post(d, body(event_code=code))
    ok = r.status == "REJECTED" and len(ws) == 0 and len(ms) == 0
    rec(f"TR-{code}", "DEFENDED" if ok else "BREACH", "M6-FAIL-003",
        f"{why} -> {r.status}/{r.error_code}, web={len(ws)} meas={len(ms)} (HOLD not logged)")

# Two-layer independence: CLICK_CTA passes the CLIENT hook (locked base event) but is NOT active in the registry.
d, ws, ms, au = make_deps()
r = post(d, body(event_code="CLICK_CTA"))
hook_ok = is_locked_base_event("CLICK_CTA")   # client layer would allow it
ok = hook_ok and r.status == "REJECTED" and r.error_code == "UNKNOWN_EVENT" and len(ws) == 0 and len(ms) == 0
rec("TR-2layer", "DEFENDED" if ok else "BREACH", "M6-FAIL-003",
    f"CLICK_CTA passes client hook ({hook_ok}) but backend registry REJECTS -> {r.status}/{r.error_code}, "
    f"web={len(ws)} meas={len(ms)} (layers independent) [leg-1]")

accepts = 0
for var in ["view_landing", "VIEW_LANDING ", " VIEW_LANDING", "VIEW\u200bLANDING", "VIEWLANDING"]:
    d, ws, ms, au = make_deps()
    r = post(d, body(event_code=var))
    if r.status != "REJECTED" or len(ws) or len(ms):
        accepts += 1
rec("TR-nearmiss", "DEFENDED" if accepts == 0 else "BREACH", "M6-FAIL-003",
    f"5 registry near-miss variants -> non-rejected/logged={accepts}/5")

# Non-str event_code at the endpoint (server re-validates; client never trusted alone).
raises = 0; bad = 0
for badval in [["x"], {"k": 1}, 123, None, True]:
    d, ws, ms, au = make_deps()
    k, r = safe_post(d, body(event_code=badval))
    if k == "RAISE":
        raises += 1
    elif not (r.status == "REJECTED" and r.error_code == "SCHEMA_INVALID" and len(ws) == 0 and len(ms) == 0):
        bad += 1
rec("TR-nonstr-code", "DEFENDED" if (raises == 0 and bad == 0) else "BREACH", "M6-FAIL-003",
    f"5 non-str event_code -> raises={raises}, non-fail-closed={bad} (track.py:84-86)")

# Control: a valid registered event is ACCEPTED end-to-end, exactly one row in EACH store.
d, ws, ms, au = make_deps()
r = post(d, body(guest_id="guest_mapped_ok"))
ok = (r.status == "ACCEPTED" and r.event_id and r.log_id and r.data_quality_status == "HOLD"
      and len(ws) == 1 and len(ms) == 1)
rec("TR-control", "CONTROL" if ok else "BREACH", "NONE",
    f"valid VIEW_LANDING -> {r.status}, event_id set={bool(r.event_id)}, dq={r.data_quality_status}, "
    f"web={len(ws)} meas={len(ms)}")

# =================================================================================================
# GROUP HOOK — frontend client layer (leg-1 layer-1, RULE-001)
# =================================================================================================
au = AuditLog(); hook = TrackingHook(au)
h = hook.emit("TOTALLY_UNKNOWN_EVENT")
rec("HOOK-unknown", "DEFENDED" if (not h.emitted and h.reason == "HOOK_UNKNOWN_EVENT") else "BREACH",
    "M6-FAIL-003", f"unknown code at hook -> emitted={h.emitted}, audited HOOK_UNKNOWN_EVENT (hooks.py:36-44)")
nonstr_emit = 0
for bad in [["x"], 123, None, {"k": 1}]:
    hh = hook.emit(bad)
    if hh.emitted:
        nonstr_emit += 1
rec("HOOK-nonstr", "DEFENDED" if nonstr_emit == 0 else "BREACH", "M6-FAIL-003",
    f"4 non-str codes at hook -> emitted={nonstr_emit}/4 (is_locked_base_event type-safe, base_events.py:43)")
golden = hook.emit("GOLDEN_HOUR_START")   # conditional on M6-OD-009 (OPEN) -> NOT in locked set
rec("HOOK-golden", "DEFENDED" if not golden.emitted else "BREACH", "M6-FAIL-003",
    f"GOLDEN_HOUR_START (M6-OD-009 OPEN) -> emitted={golden.emitted} (fail-closed, not-yet-ratified)")
base_ok = all(hook.emit(c).emitted for c in ["VIEW_LANDING", "ORDER_VERIFIED", "ADD_TO_CART"])
rec("HOOK-base", "CONTROL" if base_ok else "BREACH", "NONE",
    f"3 locked base events at hook -> all emitted={base_ok} (non-vacuity)")

# =================================================================================================
# GROUP DEDUP — RULE-005 / RULE-007 / SMK-003 (double count / silent loss / append-only)
# =================================================================================================
# Exact replay (different correlation_id) -> DUPLICATE, same event_id, ONE row in EACH store.
d, ws, ms, au = make_deps()
r1 = post(d, body(correlation_id="corr_A"))
r2 = post(d, body(correlation_id="corr_B"))
ok = (r1.status == "ACCEPTED" and r2.status == "DUPLICATE" and r2.idempotent_replay
      and r1.event_id == r2.event_id and len(ws) == 1 and len(ms) == 1)
rec("DEDUP-replay", "DEFENDED" if ok else "BREACH", "M6-FAIL-003",
    f"exact replay (diff corr) -> {r1.status}/{r2.status}, same event_id={r1.event_id == r2.event_id}, "
    f"web={len(ws)} meas={len(ms)} [SMK-003]")

# Client-supplied idempotency_key must be IGNORED (server recomputes).
d, ws, ms, au = make_deps()
post(d, body(idempotency_key="attacker-key-1"))
r = post(d, body(idempotency_key="attacker-key-2"))
rec("DEDUP-clientkey", "DEFENDED" if (r.status == "DUPLICATE" and len(ws) == 1 and len(ms) == 1) else "BREACH",
    "M6-FAIL-003", f"replay with different client idempotency_key -> {r.status}, web={len(ws)} meas={len(ms)} "
    f"(server-derived key, track.py:92-98,127)")

# Distinct events (different page_id) must NOT dedup.
d, ws, ms, au = make_deps()
post(d, body(page_id="p1"))
post(d, body(page_id="p2"))
rec("DEDUP-distinct", "DEFENDED" if (len(ws) == 2 and len(ms) == 2) else "BREACH", "M6-FAIL-003",
    f"two distinct page_ids -> web={len(ws)} meas={len(ms)} (dedup discriminates)")

# Cross-store consistency: the two append-only stores never disagree on row count.
d, ws, ms, au = make_deps()
for i in range(3):
    post(d, body(correlation_id=f"c{i}"))            # 3 exact replays
post(d, body(page_id="pX"))                           # + 1 distinct
rec("DEDUP-consistency", "DEFENDED" if len(ws) == len(ms) == 2 else "BREACH", "M6-FAIL-003",
    f"3 replays + 1 distinct -> web={len(ws)} meas={len(ms)} (stores agree)")

# Append-only guards on BOTH stores.
viol = []
mstore = MeasurementEventStore()
for op in ("update", "delete"):
    try:
        getattr(mstore, op)()
        viol.append(f"meas.{op}=no-raise")
    except MeasurementStoreViolation:
        pass
wstore = WebEventLogStore()
for op in ("update", "delete"):
    try:
        getattr(wstore, op)()
        viol.append(f"web.{op}=no-raise")
    except AppendOnlyViolation:
        pass
rec("DEDUP-appendonly", "DEFENDED" if not viol else "BREACH", "NONE",
    f"update/delete on both stores raise; leaks={viol or 'NONE'} (RULE-007)")

# Measurement store revenue-bearing insert is a fail-closed violation (RULE-003 scope guard).
mstore = MeasurementEventStore()
rev_row = AdsMeasurementEvent(event_id="e", event_code="VIEW_LANDING",
                              event_ts=datetime(2026, 7, 29, tzinfo=timezone.utc),
                              idempotency_key="k", correlation_id="c", revenue_value=1.0)
try:
    mstore.insert(rev_row); rev_guard = "no-raise"
except MeasurementStoreViolation:
    rev_guard = "raised"
rec("DEDUP-revenue-guard", "DEFENDED" if rev_guard == "raised" else "BREACH", "M6-FAIL-001",
    f"revenue-bearing insert -> {rev_guard} (measurement_event_store.py:45-48; M6.2B never sets revenue)")

# build_idempotency_key injectivity (carried MAJOR-5) + endpoint hash is sha256 (distinct bodies distinct hash).
alpha = ["a", "|", "\\", "\\|", "", None]
seen = {}; coll = 0
for combo in itertools.product(alpha, repeat=5):
    k = build_idempotency_key(*combo)
    if k in seen and seen[k] != combo:
        coll += 1
    seen[k] = combo
h1 = _raw_event_hash(body(page_id="p1")); h2 = _raw_event_hash(body(page_id="p2"))
rec("DEDUP-injective", "DEFENDED" if (coll == 0 and h1 != h2) else "BREACH", "M6-FAIL-003",
    f"key fuzz 6^5 collisions={coll}; distinct bodies -> distinct raw_event_hash={h1 != h2} (idempotency.py + sha256)")

# OBSERVATION: same instant, two tz notations -> server raw_event_hash differs -> TWO rows (over-count).
d, ws, ms, au = make_deps()
post(d, body(event_ts="2026-07-29T12:00:00+07:00"))
post(d, body(event_ts="2026-07-29T05:00:00+00:00"))   # SAME instant, different notation
same_instant_rows = len(ws)
rec("DEDUP-tznotation", "OPEN_NONGATE" if same_instant_rows == 2 else "DEFENDED", "NONE",
    f"same instant in +07:00 vs +00:00 -> web={len(ws)} meas={len(ms)} rows; raw_event_hash includes the RAW ts "
    f"string (track.py:251) so normalize_ts canonicalization (MAJOR-4) is not effective in the key for the "
    f"endpoint path -> potential OVER-count on a non-exact-replay. NOT an exact-replay (SMK-003 holds), NOT event "
    f"drift -> no FAIL-003. Fix: drop event_ts from the raw_event_hash canon (normalized_ts already carries it).")

# =================================================================================================
# GROUP FF — FIX-FIRST RE-VERIFY (F1 / F2 / MINOR-9 / O1)
# =================================================================================================
# F1 — the endpoint NEVER raises on a throwing adapter; each becomes an audited deny.
f1 = []
d, ws, ms, au = make_deps(registry=ThrowRegistry(), resolver=None)
k, r = safe_post(d, body())
f1.append(("registry", k, r.status if k == "RESULT" else None, any(x.reason == "VALIDATION_FAILED" for x in au.records)))
d, ws, ms, au = make_deps(store=ThrowStore(), resolver=None)
k, r = safe_post(d, body())
f1.append(("store", k, r.status if k == "RESULT" else None, any(x.reason == "STORE_APPEND_FAILED" for x in au.records)))
d, ws, ms, au = make_deps(reader=ThrowReader(), resolver=None)
k, r = safe_post(d, body())
f1.append(("reader", k, r.status if k == "RESULT" else None, any(x.reason == "CONSENT_READER_FAILED" for x in au.records)))
d, ws, ms, au = make_deps(resolver=IdentityResolver(ThrowContacts(), Customers(set()), AuditLog()))
k, r = safe_post(d, body(guest_id="guest_mapped_ok"))
f1.append(("resolver", k, r.status if k == "RESULT" else None, None))
raised = [name for (name, k, st, a) in f1 if k == "RAISE"]
rec("FF-F1-adapters", "DEFENDED" if not raised else "OPEN_NONGATE", "NONE",
    f"throwing registry/store/reader/resolver via endpoint -> raises={raised or 'NONE'}; "
    f"{[(n, st, ('audit' if a else '')) for (n, k, st, a) in f1]} (ingest.py F1 wraps hold end-to-end)")

# F1(b) — extreme-year event_ts (OverflowError) via the endpoint -> audited TS_NORMALIZE_FAILED, no raise.
d, ws, ms, au = make_deps()
k, r = safe_post(d, body(event_ts="9999-12-31T20:00:00-14:00"))
ok = (k == "RESULT" and r.status == "REJECTED" and len(ws) == 0
      and any(x.reason == "TS_NORMALIZE_FAILED" for x in au.records))
rec("FF-F1-tsoverflow", "DEFENDED" if ok else ("OPEN_NONGATE" if k == "RAISE" else "BREACH"), "NONE",
    f"year-9999 @ -14:00 (OverflowError in tz math) via endpoint -> kind={k}, status={r.status if k=='RESULT' else None}, "
    f"TS_NORMALIZE_FAILED audited (ingest.py:230-236 except Exception)")

# F1(b) — hostile tzinfo at the seam (not reachable from JSON, but proves the except Exception catches it).
class _HostileTZ(tzinfo):
    def utcoffset(self, dt): raise RuntimeError("hostile tz")
    def tzname(self, dt): return "X"
    def dst(self, dt): return None
au = AuditLog(); ing = IngestService(EventValidator(Registry(REG), au), WebEventLogStore(),
                                     ConsentGate(au), InMemoryConsentReader(CONSENT), au)
try:
    ing.ingest_event(event_code="VIEW_LANDING", page_id="p", session_id="s", source="web",
                     event_ts=datetime(2026, 7, 29, 12, tzinfo=_HostileTZ()), raw_event_hash="h")
    seam_ts = ("RESULT", any(x.reason == "TS_NORMALIZE_FAILED" for x in au.records))
except Exception as e:  # noqa: BLE001
    seam_ts = ("RAISE", type(e).__name__)
rec("FF-F1-hostiletz", "DEFENDED" if seam_ts[0] == "RESULT" and seam_ts[1] else "OPEN_NONGATE", "NONE",
    f"hostile tzinfo at seam -> {seam_ts} (ingest.py:230 except Exception)")

# F2 — a ConsentSnapshot SUBCLASS skipping __post_init__ + raw-string scope is now DENIED at the gate.
class _UnhardenedSnap(ConsentSnapshot):
    def __post_init__(self):  # skip hardening
        pass
evil = _UnhardenedSnap("cs_evil", "guest_mapped_ok", ConsentState.VALID,
                       datetime(2026, 7, 29, tzinfo=timezone.utc), "external_measurement_granted")
au = AuditLog()
g_sub = ConsentGate(au).evaluate(evil, ConsentScope.EXTERNAL_MEASUREMENT)
evil_dict = _UnhardenedSnap("cs_evil2", "g", ConsentState.VALID, datetime(2026, 7, 29, tzinfo=timezone.utc),
                            {"external_measurement": False})
g_dict = ConsentGate(AuditLog()).evaluate(evil_dict, ConsentScope.EXTERNAL_MEASUREMENT)
ok = (g_sub is False and g_dict is False and any(x.reason == "CONSENT_SCOPE_UNTRUSTED_TYPE" for x in au.records))
rec("FF-F2-subclass", "DEFENDED" if ok else "BREACH", "M6-FAIL-002",
    f"subclass raw-str scope -> gate.evaluate={g_sub}; dict scope -> {g_dict}; CONSENT_SCOPE_UNTRUSTED_TYPE "
    f"(gate.py:56-66) — the M6.2A F2 residual is CLOSED")

# F2 — duck-typed reader snapshot still fail-closed at the seam.
duck = SimpleNamespace(consent_snapshot_id="cs_d", subject_ref="guest_mapped_ok",
                       consent_state=ConsentState.VALID, consent_scope="no_external_measurement_allowed")
d, ws, ms, au = make_deps(reader=InMemoryConsentReader({"cs_d": None}))
# reader returns None for cs_d in this build; instead drive the seam directly with a duck reader:
class DuckReader:
    def get(self, cid): return duck
    def current_state(self, s): return ConsentState.MISSING
au = AuditLog(); ing = IngestService(EventValidator(Registry(REG), au), WebEventLogStore(), ConsentGate(au),
                                     DuckReader(), au)
res = ing.ingest_event(event_code="VIEW_LANDING", page_id="p", session_id="s", source="web",
                       event_ts=datetime(2026, 7, 29, 12, tzinfo=timezone.utc), raw_event_hash="h",
                       consent_snapshot_id="cs_d", guest_id="guest_mapped_ok")
ok = (res.egress_eligible is False and any(x.reason == "CONSENT_SNAPSHOT_UNTRUSTED_TYPE" for x in au.records)
      and all(getattr(x, "consent_snapshot_id", None) != "cs_d" for x in ws.all()) if False else
      any(x.reason == "CONSENT_SNAPSHOT_UNTRUSTED_TYPE" for x in au.records) and res.egress_eligible is False)
rec("FF-F2-ducktype", "DEFENDED" if ok else "BREACH", "M6-FAIL-002",
    f"duck reader snapshot -> UNTRUSTED_TYPE, egress={res.egress_eligible} (ingest.py:184-194)")

# MINOR-9 — identifier-shaped event_code is WRAPPED in the audit sink; a genuine code stays verbatim.
digit_run = "".join(str((i * 3 + 1) % 10) for i in range(8))       # 8-digit run; no literal
cust_id = "cust_" + "".join(str((i * 7) % 10) for i in range(5))   # cust_ prefix + digits; no literal
guest_pfx = "guest_" + "".join(str((i * 3) % 10) for i in range(5))
wrapped = all(_safe_event_code(v).startswith("INVALID_EVENT_CODE[") for v in (digit_run, cust_id, guest_pfx))
verbatim_ok = _safe_event_code("VIEW_LANDING") == "VIEW_LANDING" and _safe_event_code("view_landing") == "view_landing"
rec("FF-MINOR9", "DEFENDED" if (wrapped and verbatim_ok) else "OPEN_NONGATE", "NONE",
    f"identifier-shaped event_code wrapped={wrapped}; genuine code stays verbatim={verbatim_ok} "
    f"(audit.py:31-52 _looks_like_identifier) — the M6.2A SEC-PII-01 residual is CLOSED")

# O1 — the audit EXPORT surface masks correlation_id (raw never appears in an audit detail).
d, ws, ms, au = make_deps()
CORR = "corr_secrettrace_xyz"
post(d, body(event_code="TOTALLY_UNKNOWN", correlation_id=CORR))
raw_in_audit = any(CORR in (x.detail or "") for x in au.records)
masked_present = any(mask(CORR) in (x.detail or "") for x in au.records)
rec("FF-O1-mask", "DEFENDED" if (not raw_in_audit and masked_present) else "OPEN_NONGATE", "NONE",
    f"correlation_id raw-in-audit={raw_in_audit}, masked-present={masked_present} (track.py:195-197 _corr masks on export)")

# =================================================================================================
# GROUP RB — ENDPOINT ROBUSTNESS / NEVER-RAISES / SCHEMA
# =================================================================================================
# Malformed bodies -> REJECTED with the right code, never a raise, no rows.
schema_raises = 0; schema_bad = 0; n = 0
cases = [
    (None, "SCHEMA_INVALID"), (["x"], "SCHEMA_INVALID"), (123, "SCHEMA_INVALID"), ("str", "SCHEMA_INVALID"),
]
for bd, exp in cases:
    n += 1
    d, ws, ms, au = make_deps()
    k, r = safe_post(d, bd)
    if k == "RAISE":
        schema_raises += 1
    elif not (r.status == "REJECTED" and len(ws) == 0):
        schema_bad += 1
# missing required fields
for missing, exp in [("event_code", "SCHEMA_INVALID"), ("page_id", "SCHEMA_INVALID"),
                     ("idempotency_key", "IDEMPOTENCY_KEY_MISSING"),
                     ("consent_snapshot_id", "CONSENT_MISSING_OR_INVALID")]:
    n += 1
    d, ws, ms, au = make_deps()
    b = body(); del b[missing]
    k, r = safe_post(d, b)
    if k == "RAISE":
        schema_raises += 1
    elif not (r.status == "REJECTED" and r.error_code == exp and len(ws) == 0 and len(ms) == 0):
        schema_bad += 1
# bad event_ts (naive / bad string)
for badts in ["2026-07-29T12:00:00", "not-a-date", 12345, None]:
    n += 1
    d, ws, ms, au = make_deps()
    k, r = safe_post(d, body(event_ts=badts))
    if k == "RAISE":
        schema_raises += 1
    elif not (r.status == "REJECTED" and r.error_code == "SCHEMA_INVALID"):
        schema_bad += 1
rec("RB-schema", "DEFENDED" if (schema_raises == 0 and schema_bad == 0) else "BREACH", "NONE",
    f"{n} malformed bodies -> raises={schema_raises}, wrong-outcome={schema_bad} (track.py:80-124)")

# RAW_PII tripwire refuses an email/VN-phone in the payload (constructed programmatically; never echoed).
email_probe = "u" + chr(64) + "h" + ".xy"          # email-shaped probe built via chr(64); no literal in this file
phone_probe = "0" + "".join(str((i * 7) % 10) for i in range(9))   # 0 + 9 digits = VN mobile shape
pii_refused = 0
for probe in (email_probe, phone_probe):
    d, ws, ms, au = make_deps()
    r = post(d, body(payload={"note": probe}))
    if r.status == "REJECTED" and r.error_code == "RAW_PII_IN_PAYLOAD":
        pii_refused += 1
rec("RB-pii-tripwire", "DEFENDED" if pii_refused == 2 else "OPEN_NONGATE", "M6-FAIL-008",
    f"email/phone-shaped payload refused={pii_refused}/2 (track.py:121-124 RAW_PII tripwire)")

# NOVEL: a deeply-nested (valid JSON) payload makes the UNWRAPPED recursive walk RAISE out of the handler.
deep = leaf = {}
for _ in range(4000):
    nxt = {}
    leaf["k"] = nxt
    leaf = nxt
leaf["v"] = "x"
d, ws, ms, au = make_deps()
k, r = safe_post(d, body(payload=deep))
rec("RB-deepnest", "OPEN_NONGATE" if k == "RAISE" else "DEFENDED", "NONE",
    f"4000-deep JSON payload -> handler kind={k} ({r if k=='RAISE' else r.status}); _contains_raw_pii "
    f"(_iter_strings, track.py:225-241) and _raw_event_hash (json.dumps, track.py:244-253) are UNWRAPPED "
    f"recursive walks -> RecursionError escapes the 'never-raises' handler (unaudited). REACHABLE from a real "
    f"nested JSON body -> DoS/robustness + lost-audit; NOT event drift -> no FAIL-003. Fix: bound payload depth "
    f"or wrap step-6/step-7 in the audited-deny pattern.")

# =================================================================================================
# GROUP OVR — OVERREACH / POSTURE / MINOR-6 / DATA-MART
# =================================================================================================
posture_ok = (cfg.GLOBAL_GATEWAY_STATE == "BLOCKED" and cfg.PRODUCTION_FLAG == "OFF"
              and cfg.EXTERNAL_SEND == "OFF" and cfg.is_external_send_enabled() is False)
rec("OVR-posture", "DEFENDED" if posture_ok else "BREACH", "M6-FAIL-009",
    f"(gateway,prod,ext_send,enabled)=({cfg.GLOBAL_GATEWAY_STATE},{cfg.PRODUCTION_FLAG},{cfg.EXTERNAL_SEND},"
    f"{cfg.is_external_send_enabled()})")

# Best-case egress via the seam is still False (permits_external_send hard-False).
au = AuditLog(); ing = IngestService(EventValidator(Registry(REG), au), WebEventLogStore(), ConsentGate(au),
                                     InMemoryConsentReader(CONSENT, {"guest_mapped_ok": ConsentState.VALID}), au,
                                     resolver=IdentityResolver(Contacts(GUESTS), Customers({"cust_0001"}), au))
best = ing.ingest_event(event_code="VIEW_LANDING", page_id="p", session_id="s", source="web",
                        event_ts=datetime(2026, 7, 29, 12, tzinfo=timezone.utc), raw_event_hash="h",
                        consent_snapshot_id="cs_valid", guest_id="guest_mapped_ok")
rec("OVR-egress", "DEFENDED" if best.egress_eligible is False else "BREACH", "M6-FAIL-002",
    f"best case (registered+VALID+bound) -> egress_eligible={best.egress_eligible}; permits_external_send={permits_external_send('ALLOW')}")

# No revenue in the M6.2B path.
mev = AdsMeasurementEvent(event_id="e", event_code="VIEW_LANDING",
                          event_ts=datetime(2026, 7, 29, tzinfo=timezone.utc), idempotency_key="k",
                          correlation_id="c")
rec("OVR-no-revenue", "DEFENDED" if (mev.revenue_value is None and mev.order_code is None
    and dict(mev.attribution_context) == {} and mev.data_quality_status is DataQualityStatus.HOLD) else "BREACH",
    "M6-FAIL-001", f"normalized Zone-A row: revenue={mev.revenue_value}, order={mev.order_code}, dq={mev.data_quality_status.value}")

# Tokenizer sweep for network/db/egress primitives across the M6.2B app tree.
NET_DB = {"socket", "requests", "urllib", "httpx", "aiohttp", "smtplib", "websocket", "websockets",
          "boto3", "kafka", "pika", "psycopg", "psycopg2", "pymysql", "sqlalchemy", "create_engine",
          "executemany", "cursor", "sessionmaker", "execute"}
app_dir = os.path.join(IMPL, "app")
net_hits = []
for root, _dd, files in os.walk(app_dir):
    for fn in files:
        if not fn.endswith(".py"):
            continue
        with open(os.path.join(root, fn), "r", encoding="utf-8") as f:
            src = f.read()
        names = set()
        try:
            for tok in tokenize.generate_tokens(io.StringIO(src).readline):
                if tok.type == tokenize.NAME:
                    names.add(tok.string)
        except tokenize.TokenError:
            pass
        for hit in names & NET_DB:
            net_hits.append(f"{fn}:{hit}")
rec("OVR-sweep-net", "DEFENDED" if not net_hits else "BREACH", "M6-FAIL-002",
    f"network/db code identifiers across M6.2B app/ = {net_hits or 'NONE'}")

# MINOR-6 via the endpoint: a loose registry returns a row for a DIFFERENT code -> unregistered code logged.
d, ws, ms, au = make_deps(registry=MismatchRegistry())
r = post(d, body(event_code="ADS_REQUESTED_NEVER_REGISTERED"))
minor6 = (r.status == "ACCEPTED" and len(ws) == 1 and ws.all()[0].event_code == "ADS_REQUESTED_NEVER_REGISTERED"
          and len(ms) == 1 and ms.all()[0].event_code == "ADS_REQUESTED_NEVER_REGISTERED")
rec("OVR-MINOR6", "OPEN_NONGATE" if minor6 else "DEFENDED", "NONE",
    f"loose registry (row.event_code != requested) -> requested unregistered code logged under its own name "
    f"in both stores={minor6}; needs a NORMALIZING adapter (no shipped adapter does this). validator has no "
    f"row.event_code==event_code assertion (validator.py:82). Same as M6.2A MINOR-6.")

# PII in session_id bypasses the payload-only tripwire -> stored raw in the durable row (masked on export).
d, ws, ms, au = make_deps()
post(d, body(session_id=phone_probe))
raw_sess = bool(ws.all()) and ws.all()[0].session_id == phone_probe
rec("OVR-pii-nonpayload", "NOTE", "NONE",
    f"phone-shaped session_id bypasses the payload-only RAW_PII tripwire, stored raw in web_event_logs={raw_sess} "
    f"(masked on export/audit per O1). FAIL-008 / M6-P1106 scope, not FAIL-003.")

# =================================================================================================
# GROUP W — vectors surfaced by the adversarial-ideation workflow (executed to confirm/refute)
# =================================================================================================
# W-subsecond — sub-second precision in event_ts forks the key (normalized_ts drops us; raw_event_hash keeps it).
d, ws, ms, au = make_deps()
post(d, body(event_ts="2026-07-29T12:00:00+00:00"))
post(d, body(event_ts="2026-07-29T12:00:00.500000+00:00"))   # same second, sub-second differs
rec("W-subsecond", "OPEN_NONGATE" if len(ws) == 2 else "DEFENDED", "NONE",
    f"same-second ts differing only in microseconds -> web={len(ws)} meas={len(ms)}; normalized_ts drops microseconds "
    f"(idempotency.py:39) but raw_event_hash keeps the raw ts (track.py:251) -> 2 keys -> over-count. Not exact-replay "
    f"(SMK-003 holds), not FAIL-003. Same root as DEDUP-tznotation.")

# W-junkkey — an extra ignored top-level body field forks raw_event_hash (canon = every non-volatile key).
d, ws, ms, au = make_deps()
post(d, body())
post(d, {**body(), "_nonce": "1"})
rec("W-junkkey", "OPEN_NONGATE" if len(ws) == 2 else "DEFENDED", "NONE",
    f"replay + one extra ignored body key -> web={len(ws)} meas={len(ms)}; raw_event_hash canons EVERY non-volatile "
    f"key (track.py:250-251), so a non-semantic field forks the RULE-005 key. MINOR dedup-robustness; not FAIL-003.")

# W-mixedkeys — a body with mixed-type keys makes json.dumps(sort_keys=True) raise OUT of the handler (non-JSON).
d, ws, ms, au = make_deps()
b = body(); b[5] = "y"   # int key alongside str keys
k, r = safe_post(d, b)
rec("W-mixedkeys", "OPEN_NONGATE" if k == "RAISE" else "DEFENDED", "NONE",
    f"mixed-type body keys -> handler kind={k}; sorted()/json.dumps(sort_keys=True) at track.py:251 raises, UNWRAPPED "
    f"(track.py:127). NOT reachable from a JSON body (JSON keys are str); needs a non-JSON caller.")

# W-hostiletz-datetime — event_ts as a datetime with a hostile tzinfo raises in _raw_event_hash BEFORE the seam.
d, ws, ms, au = make_deps()
k, r = safe_post(d, body(event_ts=datetime(2026, 7, 29, 12, tzinfo=_HostileTZ())))
rec("W-hostiletz-ep", "OPEN_NONGATE" if k == "RAISE" else "DEFENDED", "NONE",
    f"event_ts=datetime(hostile tzinfo) -> handler kind={k}; str(datetime) in _raw_event_hash (track.py:252 default=str) "
    f"raises BEFORE the seam's F1 guard runs. NOT reachable from JSON (ts is a string there); direct-driver only.")

# W-circular — a circular payload raises RecursionError in _contains_raw_pii (unwrapped). Non-JSON only.
d, ws, ms, au = make_deps()
cyc = {}; cyc["self"] = cyc
k, r = safe_post(d, body(payload=cyc))
rec("W-circular", "OPEN_NONGATE" if k == "RAISE" else "DEFENDED", "NONE",
    f"circular payload -> handler kind={k}; _iter_strings (track.py:225-233) recurses a cycle unbounded. NOT reachable "
    f"from JSON (no cycles); the REACHABLE instance of this unwrapped-walk class is RB-deepnest (deep JSON).")

# W-minor9-residual — a 5-digit / unlisted-prefix id still stores verbatim (digit-run threshold is >=6).
five = "".join(str((i * 3 + 1) % 10) for i in range(5))            # 5-digit run; below the digit-run threshold
sess_pfx = "sess_" + "".join(str((i * 7) % 10) for i in range(4))  # 'sess' not in the id-prefix list
resid = (_safe_event_code(five) == five) or (_safe_event_code(sess_pfx) == sess_pfx)
rec("W-minor9-residual", "OPEN_NONGATE" if resid else "DEFENDED", "NONE",
    f"5-digit run / unlisted-prefix id stored verbatim in audit={resid}; the digit-run regex requires >=6 and the "
    f"id-prefix list is finite (audit.py:31-32). Low-severity PII residual -> M6-P1106 scope, not FAIL-003.")

# W-store-guard — the measurement-store scope guard blocks revenue_value only; order_code is NOT guarded (not
# reachable via the endpoint's normalize, which never sets it). Defense-in-depth completeness note.
mstore = MeasurementEventStore()
ordered = AdsMeasurementEvent(event_id="e2", event_code="VIEW_LANDING",
                              event_ts=datetime(2026, 7, 29, tzinfo=timezone.utc), idempotency_key="k2",
                              correlation_id="c", order_code="ORD_ref_123")
try:
    mstore.insert(ordered); guard = "inserted"
except MeasurementStoreViolation:
    guard = "raised"
rec("W-store-guard", "NOTE", "NONE",
    f"direct insert of a row with order_code set -> {guard}; the store scope guard checks revenue_value only "
    f"(measurement_event_store.py:45). NOT reachable via the endpoint (normalize never sets Zone-B). Completeness note.")

# =================================================================================================
# SUMMARY
# =================================================================================================
from collections import Counter
cnt = Counter(s for _, s, _, _ in OUT)
breaches = [pid for pid, s, g, d0 in OUT if s == "BREACH"]
opens = [pid for pid, s, g, d0 in OUT if s == "OPEN_NONGATE"]
print("=" * 104)
print("SUMMARY:", dict(cnt))
print("IN-SCOPE FAIL-GATE BREACHES (M6-FAIL-003):", breaches or "NONE")
print("OPEN (real defect, does NOT trip M6-FAIL-003):", opens or "NONE")
print("TOTAL RECORDED OUTCOMES:", len(OUT))
print("=" * 104)
