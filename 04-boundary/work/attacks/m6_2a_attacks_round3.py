"""M6-P1005 BOUNDARY_ADVERSARY — attack harness, ROUND 3 (attempt 2).

Target: the STAGED implementation at 04-artifacts/impl/M6.2A (Round-3 / post-fix code).
Mode: analysis_only. READ-ONLY import of the staged package; nothing under 04-artifacts/impl is written
(sys.dont_write_bytecode = True, so no __pycache__ lands in a root this role may not write).

Purpose (per the ledger note on M6-P1005 attempt 2: "evidence describes pre-fix code; re-verify MAJOR-1..5
are closed"):
  1. RE-ATTACK every Round-1 finding (MAJOR-1..5, MINOR-1..7) against the CURRENT code and record
     CLOSED / STILL-OPEN as an executed outcome, not a reading of the diff.
  2. Attack the NEW Round-3 surface: the "strict callee, forgiving seam" contract, consent provenance via
     ConsentReader, subject binding, the escaped/normalized RULE-005 key, and the audit sanitizers.

Governance: this harness performs NO egress, NO migration, NO flag write. It only calls the staged package's
public seams in memory. All probe values are synthetic; PII-shaped probes are CONSTRUCTED PROGRAMMATICALLY so
no phone/email-shaped literal exists in this file or in the boundary report.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # never dirty the staged tree (04-artifacts/impl is not a boundary write root)

import copy
import itertools
import pathlib
import random
import re
import traceback
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

IMPL = pathlib.Path(r"D:\M6\Module6-workspace\04-artifacts\impl\M6.2A")
sys.path.insert(0, str(IMPL))

from app import config                                                     # noqa: E402
from app.measurement.audit import AuditLog                                 # noqa: E402
from app.measurement.consent.gate import ConsentGate                       # noqa: E402
from app.measurement.identity.resolver import Confidence, IdentityResolver  # noqa: E402
from app.measurement.ingest import IngestResult, IngestService             # noqa: E402
from app.measurement.logs.idempotency import build_idempotency_key, normalize_ts  # noqa: E402
from app.measurement.logs.web_event_log_store import (                     # noqa: E402
    AppendOnlyViolation,
    WebEventLogStore,
)
from app.measurement.models.consumed import (                              # noqa: E402
    ConsentScope,
    ConsentSnapshot,
    ConsentState,
    DataSensitivity,
    EventRegistryRow,
    GuestContact,
    RegistrationState,
)
from app.measurement.models.web_event_log import WebEventLog               # noqa: E402
from app.measurement.registry.validator import (                           # noqa: E402
    EventDecision,
    EventValidator,
    permits_external_send,
)

UTC_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)

# ---------------------------------------------------------------------------------------------------
# result recorder
# ---------------------------------------------------------------------------------------------------
RESULTS: list[tuple[str, str, str, str]] = []


def rec(aid: str, area: str, verdict: str, detail: str) -> None:
    """verdict in {HELD, FINDING, CLOSED, OPEN, INFO}."""
    RESULTS.append((aid, area, verdict, detail))
    print(f"[{verdict:<7}] {aid:<6} {area:<22} {detail}")


# ---------------------------------------------------------------------------------------------------
# test doubles (adapters the slice CONSUMES — owned by other modules in reality)
# ---------------------------------------------------------------------------------------------------
class Registry:
    def __init__(self, rows):
        self._rows = rows

    def get(self, event_code):
        return self._rows.get(event_code)


class ThrowingRegistry:
    """Core's event_registry is DOWN / the adapter blows up (someone else's system)."""

    def get(self, event_code):
        raise RuntimeError("event_registry unreachable")


class WrongRowRegistry:
    """A loose adapter that returns a row for a DIFFERENT event_code than the one requested."""

    def __init__(self, row):
        self._row = row

    def get(self, _event_code):
        return self._row


class Contacts:
    def __init__(self, rows):
        self._rows = rows

    def get(self, guest_id):
        return self._rows.get(guest_id)


class ThrowingContacts:
    """guest_contacts (Customer identity) is DOWN."""

    def get(self, _guest_id):
        raise RuntimeError("guest_contacts unreachable")


class Customers:
    def __init__(self, ids):
        self._ids = ids

    def exists(self, customer_id):
        return customer_id in self._ids


class ConsentReaderMap:
    def __init__(self, rows, current=None):
        self._rows = rows
        self._current = current or {}

    def get(self, consent_snapshot_id):
        return self._rows.get(consent_snapshot_id)

    def current_state(self, subject_ref):
        return self._current.get(subject_ref, ConsentState.MISSING)


class ThrowingConsentReader:
    def get(self, _id):
        raise RuntimeError("consent store unreachable")

    def current_state(self, _s):
        raise RuntimeError("consent store unreachable")


REG_ROWS = {
    "VIEW_LANDING": EventRegistryRow(
        "VIEW_LANDING", RegistrationState.ACTIVE, owner="core.tracking", channel="web",
        data_sensitivity=DataSensitivity.INTERNAL, external_send_policy=None,
    ),
    "DEREG_SAMPLE": EventRegistryRow("DEREG_SAMPLE", RegistrationState.DEREGISTERED, owner="core.tracking"),
    "NO_OWNER_SAMPLE": EventRegistryRow("NO_OWNER_SAMPLE", RegistrationState.ACTIVE, owner=None),
    "WS_OWNER_SAMPLE": EventRegistryRow("WS_OWNER_SAMPLE", RegistrationState.ACTIVE, owner="   "),
}

GUEST_ROWS = {
    "guest_mapped_ok": GuestContact("guest_mapped_ok", "fp_aaaaaaaa", "cust_0001", "audit_ref_123"),
    "guest_no_audit": GuestContact("guest_no_audit", "fp_bbbbbbbb", "cust_0001", None),
    "guest_unmapped": GuestContact("guest_unmapped", "fp_cccccccc"),
}


def mk_svc(*, registry=None, reader=None, contacts=None, with_resolver=False, audit=None, store=None):
    audit = audit if audit is not None else AuditLog()
    store = store if store is not None else WebEventLogStore()
    registry = registry if registry is not None else Registry(REG_ROWS)
    reader = reader if reader is not None else ConsentReaderMap({})
    resolver = None
    if with_resolver:
        contacts = contacts if contacts is not None else Contacts(GUEST_ROWS)
        resolver = IdentityResolver(contacts, Customers({"cust_0001"}), audit)
    svc = IngestService(
        EventValidator(registry, audit), store, ConsentGate(audit), reader, audit, resolver=resolver
    )
    return svc, audit, store


def ingest(svc, **over):
    kw = dict(
        event_code="VIEW_LANDING", page_id="p", session_id="s", source="web",
        event_ts=UTC_TS, raw_event_hash="h",
    )
    kw.update(over)
    return svc.ingest_event(**kw)


def seam_raises(svc, **over):
    """Return (raised: bool, exc_repr: str, result)."""
    try:
        return False, "", ingest(svc, **over)
    except BaseException as exc:  # noqa: BLE001 — the whole point is to see WHAT escapes
        return True, f"{type(exc).__name__}: {exc}", None


# ===================================================================================================
# GROUP A — re-attack the Round-1 MAJOR findings against the CURRENT (Round-3) code
# ===================================================================================================
def group_a_major_reattack():
    print("\n=== GROUP A — Round-1 MAJOR re-attack (closed or still open?) ===")

    # --- MAJOR-1: raw-string consent_scope => substring membership => fail-OPEN -------------------
    fail_open = []
    for raw in ("crm:false", "no_crm", "opt_out_of_crm", '{"crm": false, "external_measurement": false}'):
        try:
            ConsentSnapshot("cs_a1", "subjX", ConsentState.VALID, UTC_TS, raw)  # type: ignore[arg-type]
            fail_open.append(raw)
        except TypeError:
            pass
    if fail_open:
        rec("A1", "consent/MAJOR-1", "OPEN", f"raw-string scope still constructs: {fail_open}")
    else:
        rec("A1", "consent/MAJOR-1", "CLOSED",
            "ConsentSnapshot.__post_init__ raises TypeError on every raw-string consent_scope "
            "(4/4 probes) -> substring fail-OPEN unreachable via construction")

    # non-ConsentScope element must also be refused
    for bad in ([{"crm"}], [["crm"]], [{"crm": False}]):
        try:
            ConsentSnapshot("cs_a1b", "subjX", ConsentState.VALID, UTC_TS, bad[0])  # type: ignore[arg-type]
            rec("A1b", "consent/MAJOR-1", "OPEN", f"non-ConsentScope element accepted: {bad[0]!r}")
            break
        except TypeError:
            continue
    else:
        rec("A1b", "consent/MAJOR-1", "CLOSED",
            "set/list/dict of raw strings refused at construction (element type enforced)")

    # --- MAJOR-1 RESIDUAL: the same fail-OPEN through a READER-returned duck-typed snapshot ------
    gate_audit = AuditLog()
    gate = ConsentGate(gate_audit)
    duck_str = SimpleNamespace(
        consent_snapshot_id="cs_duck_str", subject_ref="guest_x",
        consent_state=ConsentState.VALID, consent_scope="crm:false", captured_at=UTC_TS,
    )
    duck_dict = SimpleNamespace(
        consent_snapshot_id="cs_duck_dict", subject_ref="guest_x",
        consent_state=ConsentState.VALID, consent_scope={"crm": False, "audience_sync": False},
        captured_at=UTC_TS,
    )
    duck_deny_str = SimpleNamespace(
        consent_snapshot_id="cs_duck_deny", subject_ref="guest_x",
        consent_state=ConsentState.VALID, consent_scope="no_external_measurement_allowed",
        captured_at=UTC_TS,
    )
    hits = []
    for label, duck, scope in (
        ("str 'crm:false' -> CRM", duck_str, ConsentScope.CRM),
        ("dict {'crm': False} -> CRM", duck_dict, ConsentScope.CRM),
        ("dict {'audience_sync': False} -> AUDIENCE_SYNC", duck_dict, ConsentScope.AUDIENCE_SYNC),
        ("str 'no_external_measurement_allowed' -> EXTERNAL_MEASUREMENT", duck_deny_str,
         ConsentScope.EXTERNAL_MEASUREMENT),
    ):
        try:
            if gate.evaluate(duck, scope) is True:  # type: ignore[arg-type]
                hits.append(label)
        except Exception as exc:  # noqa: BLE001
            rec("A1c", "consent/MAJOR-1", "INFO", f"{label} raised {type(exc).__name__}")
    if hits:
        rec("A1c", "consent/MAJOR-1r", "FINDING",
            f"gate GRANTS a reader-returned duck snapshot whose consent_scope literally DENIES: {hits}")
    else:
        rec("A1c", "consent/MAJOR-1r", "HELD", "duck-typed consent_scope denied at the gate")

    # is the duck-typed snapshot rejected anywhere in the seam? (isinstance check present?)
    svc, audit, store = mk_svc(reader=ConsentReaderMap({"cs_duck_str": duck_str}))
    res = ingest(svc, consent_snapshot_id="cs_duck_str", guest_id="guest_x",
                 consent_scope=ConsentScope.CRM)
    row = store.get(res.idempotency_key)
    rec("A1d", "consent/MAJOR-1r", "FINDING" if row and row.consent_snapshot_id == "cs_duck_str" else "HELD",
        f"seam has no isinstance(ConsentSnapshot) check: duck snapshot accepted as provenance -> "
        f"persisted consent_snapshot_id={row.consent_snapshot_id!r}, notes={res.notes}, "
        f"egress_eligible={res.egress_eligible}")

    # --- MAJOR-2: consent provenance ------------------------------------------------------------
    try:
        IngestService(EventValidator(Registry(REG_ROWS), AuditLog()), WebEventLogStore(),
                      ConsentGate(AuditLog()))  # type: ignore[call-arg]
        rec("A2", "consent/MAJOR-2", "OPEN", "IngestService still constructible without a ConsentReader")
    except TypeError:
        rec("A2", "consent/MAJOR-2", "CLOSED", "ConsentReader + audit sink are now REQUIRED ctor args")

    # caller-supplied snapshot with an id the consent system never issued
    svc, audit, store = mk_svc(reader=ConsentReaderMap({}))
    forged = ConsentSnapshot(
        "cs_NEVER_ISSUED_BY_CONSENT_SYSTEM", "guest_x", ConsentState.VALID, UTC_TS,
        frozenset({ConsentScope.CRM, ConsentScope.EXTERNAL_MEASUREMENT, ConsentScope.AUDIENCE_SYNC}),
    )
    res = ingest(svc, consent_snapshot=forged, guest_id="guest_x", consent_scope=ConsentScope.CRM)
    row = store.get(res.idempotency_key)
    ok = (row is not None and row.consent_snapshot_id is None and res.egress_eligible is False
          and "CONSENT_SNAPSHOT_UNRESOLVED" in res.notes and bool(audit.find("CONSENT_SNAPSHOT_UNRESOLVED")))
    rec("A2b", "consent/MAJOR-2", "CLOSED" if ok else "OPEN",
        f"caller-supplied forged snapshot: only its id is taken and re-resolved -> "
        f"unresolved, audited, persisted id={row.consent_snapshot_id!r}, notes={res.notes}")

    # a caller-supplied VALID snapshot object whose id IS issued but for another subject
    real_b = ConsentSnapshot("cs_valid_b", "guest_B", ConsentState.VALID, UTC_TS,
                             frozenset({ConsentScope.CRM}))
    svc, audit, store = mk_svc(reader=ConsentReaderMap({"cs_valid_b": real_b}), with_resolver=True)
    res = ingest(svc, consent_snapshot_id="cs_valid_b", guest_id="guest_mapped_ok",
                 consent_scope=ConsentScope.CRM)
    row = store.get(res.idempotency_key)
    ok = row.consent_snapshot_id is None and "CONSENT_SUBJECT_MISMATCH" in res.notes
    rec("A2c", "consent/MAJOR-2", "HELD" if ok else "FINDING",
        f"issued-but-other-subject consent refused: notes={res.notes}, persisted id={row.consent_snapshot_id!r}")

    # --- MAJOR-3: container aliasing / retroactive grant ----------------------------------------
    live = {ConsentScope.EXTERNAL_MEASUREMENT}
    snap = ConsentSnapshot("cs_alias", "guest_x", ConsentState.VALID, UTC_TS, live)  # type: ignore[arg-type]
    g_audit = AuditLog()
    g = ConsentGate(g_audit)
    before = g.evaluate(snap, ConsentScope.CRM)
    live.add(ConsentScope.CRM)
    after = g.evaluate(snap, ConsentScope.CRM)
    rec("A3", "consent/MAJOR-3", "CLOSED" if (before is False and after is False) else "OPEN",
        f"caller mutates its own set after construction: evaluate(CRM) before={before} after={after} "
        f"(snapshot holds a frozenset COPY: {type(snap.consent_scope).__name__})")

    try:
        snap.consent_scope.add(ConsentScope.CRM)  # type: ignore[attr-defined]
        rec("A3b", "consent/MAJOR-3", "OPEN", "snapshot.consent_scope is mutable in place")
    except AttributeError:
        rec("A3b", "consent/MAJOR-3", "CLOSED", "snapshot.consent_scope is a frozenset (no .add)")

    # --- MAJOR-4: timezone normalization --------------------------------------------------------
    same_instant = [
        datetime(2026, 7, 29, 10, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 7, 29, 17, 0, 0, tzinfo=timezone(timedelta(hours=7))),
        datetime(2026, 7, 29, 5, 0, 0, tzinfo=timezone(timedelta(hours=-5))),
    ]
    keys = {build_idempotency_key("E", "P", "S", "H", normalize_ts(t)) for t in same_instant}
    svc, audit, store = mk_svc()
    for t in same_instant:
        ingest(svc, event_ts=t, page_id="p4", session_id="s4", raw_event_hash="h4")
    rec("A4", "dedup/MAJOR-4", "CLOSED" if (len(keys) == 1 and len(store) == 1) else "OPEN",
        f"same instant in 3 notations -> distinct keys={len(keys)}, rows in web_event_logs={len(store)}")

    # naive datetime: rejected by the callee, audited by the seam, but the VALID event gets NO row
    svc, audit, store = mk_svc()
    raised, exc, res = seam_raises(svc, event_ts=datetime(2026, 7, 29, 10, 0, 0))
    rec("A4b", "dedup/MAJOR-4", "CLOSED" if (not raised and res.logged is False
                                             and bool(audit.find("TS_NOT_TZ_AWARE"))) else "OPEN",
        f"naive event_ts: seam raised={raised}, logged={res.logged if res else None}, "
        f"notes={res.notes if res else None}, audited=TS_NOT_TZ_AWARE:{len(audit.find('TS_NOT_TZ_AWARE'))} "
        f"-> a REGISTRY-VALID event produces NO measurement row (audited under-count, see report N4)")

    # --- MAJOR-5: delimiter ambiguity in the RULE-005 key ---------------------------------------
    k1 = build_idempotency_key("E", "P|X", "Y", "H", "T")
    k2 = build_idempotency_key("E", "P", "X|Y", "H", "T")
    svc, audit, store = mk_svc()
    ingest(svc, page_id="P|X", session_id="Y", raw_event_hash="h5")
    r2 = ingest(svc, page_id="P", session_id="X|Y", raw_event_hash="h5")
    rec("A5", "dedup/MAJOR-5", "CLOSED" if (k1 != k2 and len(store) == 2) else "OPEN",
        f"pipe-ambiguous split: keys equal={k1 == k2}, rows={len(store)}, "
        f"second notes={r2.notes}")

    # injectivity fuzz over the escape function
    rng = random.Random(20260729)
    alphabet = ["a", "b", "|", "\\", "", "\\|", "||", "\\\\", "None"]
    seen: dict[str, tuple] = {}
    collisions = []
    for _ in range(20000):
        comps = tuple(rng.choice(alphabet) for _ in range(5))
        k = build_idempotency_key(*comps)
        if k in seen and seen[k] != comps:
            collisions.append((seen[k], comps))
        seen[k] = comps
    # absent (None) component vs the literal "None"
    k_absent = build_idempotency_key("E", None, "s", "h", "t")  # type: ignore[arg-type]
    k_literal = build_idempotency_key("E", "None", "s", "h", "t")
    rec("A5b", "dedup/MAJOR-5", "CLOSED" if (not collisions and k_absent != k_literal) else "OPEN",
        f"20000-sample escape fuzz over {{a,b,|,\\,'',\\|,||,\\\\,None}}^5: collisions={len(collisions)}; "
        f"None-sentinel distinct from literal 'None'={k_absent != k_literal}")


# ===================================================================================================
# GROUP B — M6-FAIL-003 (event drift)
# ===================================================================================================
def group_b_event_drift():
    print("\n=== GROUP B — M6-FAIL-003 event drift ===")

    svc, audit, store = mk_svc()
    res = ingest(svc, event_code="UNKNOWN_EVENT_NOT_IN_REGISTRY_B1")
    ok = (res.validation.decision is EventDecision.REJECT and res.logged is False and len(store) == 0
          and res.egress_eligible is False and bool(audit.find("UNKNOWN_EVENT_NOT_IN_REGISTRY")))
    rec("B1", "drift/RULE-001", "HELD" if ok else "FINDING",
        f"unknown event -> {res.validation.decision.value}, logged={res.logged}, rows={len(store)}, "
        f"audited={len(audit.find('UNKNOWN_EVENT_NOT_IN_REGISTRY'))}")

    for aid, code, want in (("B2", "DEREG_SAMPLE", "REGISTRATION_STATE_NOT_ACTIVE"),
                            ("B3", "NO_OWNER_SAMPLE", "MISSING_OWNER"),
                            ("B3b", "WS_OWNER_SAMPLE", "MISSING_OWNER")):
        svc, audit, store = mk_svc()
        res = ingest(svc, event_code=code)
        ok = (res.validation.decision is EventDecision.HOLD and res.logged is False
              and bool(audit.find(want)))
        rec(aid, "drift/RULE-001", "HELD" if ok else "FINDING",
            f"{code} -> {res.validation.decision.value}/{res.validation.reason}, logged={res.logged}")

    # raw-string registration_state must not false-ALLOW
    reg = Registry({"RAW_STATE": EventRegistryRow("RAW_STATE", "ACTIVE", owner="core.tracking")})  # type: ignore[arg-type]
    svc, audit, store = mk_svc(registry=reg)
    res = ingest(svc, event_code="RAW_STATE")
    rec("B4", "drift/RULE-001", "HELD" if res.validation.decision is EventDecision.HOLD else "FINDING",
        f"raw-string registration_state='ACTIVE' -> {res.validation.decision.value} (fail-closed duck-typing)")

    near = ["view_landing", "VIEW_LANDING ", " VIEW_LANDING", "VIEW_LANDING\n", "VIEW\u200bLANDING",
            "View_Landing", "VIEW-LANDING", "VIEW_LANDING\t", "VIEW_LANDING\x00"]
    accepted = []
    for code in near:
        svc, audit, store = mk_svc()
        res = ingest(svc, event_code=code)
        if res.validation.accepted:
            accepted.append(code)
    rec("B5", "drift/RULE-001", "HELD" if not accepted else "FINDING",
        f"{len(near)} case/space/zero-width/control near-misses of a registered code -> "
        f"{len(accepted)} accepted (no silent normalization)")

    tokens = [None, "ALLOW", "allow", "true", "1", "YES", "*", "ENABLED", "ON", "PERMIT", "external_ok"]
    permitted = [t for t in tokens if permits_external_send(t)]
    rec("B6", "drift/egress", "HELD" if not permitted else "FINDING",
        f"{len(tokens)} external_send_policy tokens -> {len(permitted)} read as allow (M6-OD-003 OPEN)")

    from app.measurement import ports as ports_mod
    writeish = []
    for name in dir(ports_mod):
        obj = getattr(ports_mod, name)
        if isinstance(obj, type) and name.endswith("Reader") or name == "CustomerRefReader":
            for m in dir(obj):
                if m.startswith("_"):
                    continue
                if any(v in m.lower() for v in ("insert", "update", "delete", "write", "save", "set",
                                                "create", "upsert", "merge", "put", "add", "remove")):
                    writeish.append(f"{name}.{m}")
    rec("B7", "drift/ownership", "HELD" if not writeish else "FINDING",
        f"CONSUMED ports expose {len(writeish)} write-ish methods -> M6 structurally cannot mutate a "
        f"table it does not own (RULE-018)")

    # MINOR-6 re-attack: is the returned row checked to be FOR the requested code?
    wrong = WrongRowRegistry(EventRegistryRow("ADS_SOMETHING_ELSE", RegistrationState.ACTIVE,
                                              owner="core.tracking"))
    svc, audit, store = mk_svc(registry=wrong)
    res = ingest(svc, event_code="ADS_REQUESTED_BUT_NEVER_REGISTERED")
    row = store.get(res.idempotency_key)
    ok_open = res.validation.accepted and row is not None and row.event_code == "ADS_REQUESTED_BUT_NEVER_REGISTERED"
    rec("B8", "drift/MINOR-6", "OPEN" if ok_open else "CLOSED",
        f"registry row for a DIFFERENT code -> decision={res.validation.decision.value}; "
        f"row logged under the REQUESTED name={row.event_code if row else None!r} "
        f"(no row.event_code == event_code assertion in validator.validate)")

    # NEW: Core's registry adapter raises -> does the seam survive?
    svc, audit, store = mk_svc(registry=ThrowingRegistry())
    raised, exc, res = seam_raises(svc)
    rec("B9", "drift/seam", "FINDING" if raised else "HELD",
        f"event_registry adapter raises: seam raised={raised} ({exc}); audit records written={len(audit)} "
        f"-> the seam's 'never raise / always audit' contract does NOT cover the registry port")

    # NEW: a non-string event_code (JSON array/object body) against a dict-backed registry adapter
    for aid, code in (("B10", ["VIEW_LANDING"]), ("B10b", {"code": "VIEW_LANDING"})):
        svc, audit, store = mk_svc()
        raised, exc, res = seam_raises(svc, event_code=code)
        rec(aid, "drift/seam", "FINDING" if raised else "HELD",
            f"event_code={type(code).__name__} (unhashable, channel-origin JSON body): seam raised={raised} "
            f"({exc}); audit records={len(audit)}")

    # NEW: a non-string but HASHABLE event_code -> reaches the audit sanitizer
    svc, audit, store = mk_svc()
    raised, exc, res = seam_raises(svc, event_code=12345)
    rec("B11", "drift/seam", "FINDING" if raised else "HELD",
        f"event_code=int (hashable, unknown): seam raised={raised} ({exc}); audit records={len(audit)}")


# ===================================================================================================
# GROUP C — M6-FAIL-002 (consent violation)
# ===================================================================================================
def group_c_consent():
    print("\n=== GROUP C — M6-FAIL-002 consent ===")
    scopes = list(ConsentScope)

    a = AuditLog()
    g = ConsentGate(a)
    rec("C1", "consent/RULE-002",
        "HELD" if all(g.evaluate(None, s) is False for s in scopes) else "FINDING",
        f"absent snapshot denied on all {len(scopes)} scopes; audited="
        f"{len(a.find('CONSENT_SNAPSHOT_ABSENT'))}")

    grants = []
    a = AuditLog()
    g = ConsentGate(a)
    for state in (ConsentState.MISSING, ConsentState.EXPIRED, ConsentState.OPT_OUT):
        snap = ConsentSnapshot(f"cs_{state.value}", "guest_x", state, UTC_TS, frozenset(scopes))
        for s in scopes:
            if g.evaluate(snap, s) is True:
                grants.append((state.value, s.value))
    rec("C2", "consent/RULE-002", "HELD" if not grants else "FINDING",
        f"MISSING/EXPIRED/OPT_OUT x 3 scopes (9 probes, each with ALL scopes granted in the snapshot) -> "
        f"{len(grants)} granted")

    a = AuditLog()
    g = ConsentGate(a)
    meas_only = ConsentSnapshot("cs_meas", "guest_x", ConsentState.VALID, UTC_TS,
                                frozenset({ConsentScope.EXTERNAL_MEASUREMENT}))
    leak = [s.value for s in (ConsentScope.AUDIENCE_SYNC, ConsentScope.CRM) if g.evaluate(meas_only, s)]
    rec("C3", "consent/RULE-002", "HELD" if not leak else "FINDING",
        f"measurement-only consent leaking into other scopes: {leak or 'none'} "
        f"(control: EXTERNAL_MEASUREMENT={g.evaluate(meas_only, ConsentScope.EXTERNAL_MEASUREMENT)})")

    empty = ConsentSnapshot("cs_empty", "guest_x", ConsentState.VALID, UTC_TS, frozenset())
    a = AuditLog()
    g = ConsentGate(a)
    rec("C4", "consent/RULE-002",
        "HELD" if all(g.evaluate(empty, s) is False for s in scopes) else "FINDING",
        f"VALID with an EMPTY scope set denied on all scopes; audited="
        f"{len(a.find('CONSENT_SCOPE_NOT_GRANTED'))}")

    # subject binding matrix through the seam
    rows = {
        "cs_x": ConsentSnapshot("cs_x", "guest_x", ConsentState.VALID, UTC_TS, frozenset(scopes)),
        "cs_b": ConsentSnapshot("cs_b", "guest_B", ConsentState.VALID, UTC_TS, frozenset(scopes)),
        "cs_cust": ConsentSnapshot("cs_cust", "cust_0001", ConsentState.VALID, UTC_TS, frozenset(scopes)),
    }
    for aid, cid, gid, want_bound in (
        ("C5", "cs_b", "guest_mapped_ok", False),      # someone else's consent
        ("C6", "cs_x", None, False),                   # nothing to verify against
        ("C6b", "cs_cust", "guest_mapped_ok", True),   # trusted mapping (control: must NOT over-deny)
        ("C6c", "cs_cust", "guest_no_audit", False),   # mapping without audit -> not trusted (RULE-006)
        ("C6d", "cs_cust", "guest_unmapped", False),   # unmapped guest
    ):
        svc, audit, store = mk_svc(reader=ConsentReaderMap(rows), with_resolver=True)
        res = ingest(svc, consent_snapshot_id=cid, guest_id=gid, consent_scope=ConsentScope.CRM,
                     page_id=f"p_{aid}", session_id=f"s_{aid}")
        row = store.get(res.idempotency_key)
        bound = row is not None and row.consent_snapshot_id == cid
        ok = bound == want_bound
        rec(aid, "consent/subject", "HELD" if ok else "FINDING",
            f"consent {cid} for guest_id={gid!r}: bound={bound} (expected {want_bound}); "
            f"persisted id={row.consent_snapshot_id if row else None!r}; notes={res.notes}")

    svc, audit, store = mk_svc(reader=ThrowingConsentReader())
    raised, exc, res = seam_raises(svc, consent_snapshot_id="cs_any", guest_id="guest_x")
    row = store.get(res.idempotency_key) if res else None
    ok = (not raised and res.egress_eligible is False and row.consent_snapshot_id is None
          and bool(audit.find("CONSENT_READER_FAILED")))
    rec("C7", "consent/seam", "HELD" if ok else "FINDING",
        f"consent store DOWN: raised={raised}, egress={res.egress_eligible if res else None}, "
        f"persisted id={row.consent_snapshot_id if row else None!r}, audited=CONSENT_READER_FAILED")

    svc, audit, store = mk_svc(reader=ConsentReaderMap({}))
    res = ingest(svc, consent_snapshot_id="cs_never_issued", guest_id="guest_x")
    row = store.get(res.idempotency_key)
    rec("C8", "consent/seam",
        "HELD" if (row.consent_snapshot_id is None and bool(audit.find("CONSENT_SNAPSHOT_UNRESOLVED")))
        else "FINDING",
        f"unresolved consent id: persisted={row.consent_snapshot_id!r}, notes={res.notes}")

    # MINOR-1 re-attack: freshness / captured_at
    a = AuditLog()
    g = ConsentGate(a)
    stale = ConsentSnapshot("cs_2019", "guest_x", ConsentState.VALID,
                            datetime(2019, 1, 1, tzinfo=timezone.utc), frozenset(scopes))
    future = ConsentSnapshot("cs_2099", "guest_x", ConsentState.VALID,
                             datetime(2099, 1, 1, tzinfo=timezone.utc), frozenset(scopes))
    rec("C9", "consent/MINOR-1",
        "OPEN" if (g.evaluate(stale, ConsentScope.CRM) and g.evaluate(future, ConsentScope.CRM)) else "CLOSED",
        f"captured_at never compared to event time: 2019 snapshot grants="
        f"{g.evaluate(stale, ConsentScope.CRM)}, POST-DATED 2099 snapshot grants="
        f"{g.evaluate(future, ConsentScope.CRM)}")

    # MINOR-4 re-attack: is a GRANT audited?
    a = AuditLog()
    g = ConsentGate(a)
    ok_snap = ConsentSnapshot("cs_ok", "guest_x", ConsentState.VALID, UTC_TS, frozenset(scopes))
    n_before = len(a)
    granted = g.evaluate(ok_snap, ConsentScope.CRM)
    rec("C10", "consent/MINOR-4", "OPEN" if (granted and len(a) == n_before) else "CLOSED",
        f"consent GRANT wrote {len(a) - n_before} audit records (denials are all audited)")

    # MINOR-2 re-attack: malformed consent_state
    try:
        ConsentSnapshot("cs_raw", "guest_x", "VALID", UTC_TS, frozenset(scopes))  # type: ignore[arg-type]
        rec("C11", "consent/MINOR-2", "OPEN", "raw-string consent_state still constructs")
    except TypeError:
        rec("C11", "consent/MINOR-2", "CLOSED", "raw-string consent_state refused at construction")

    junk = SimpleNamespace(consent_snapshot_id="cs_junk", subject_ref="guest_x",
                           consent_state="MISSING", consent_scope=frozenset(), captured_at=UTC_TS)
    svc, audit, store = mk_svc(reader=ConsentReaderMap({"cs_junk": junk}))
    raised, exc, res = seam_raises(svc, consent_snapshot_id="cs_junk", guest_id="guest_x")
    rec("C11b", "consent/MINOR-2", "CLOSED" if (not raised and bool(audit.find("CONSENT_STATE_MALFORMED")))
        else "OPEN",
        f"reader hands back a junk consent_state: seam raised={raised}, "
        f"audited=CONSENT_STATE_MALFORMED:{len(audit.find('CONSENT_STATE_MALFORMED'))}, notes={res.notes if res else None}")

    a = AuditLog()
    g = ConsentGate(a)
    bad_scopes = ["not_a_real_scope", "CRM", None, 7, True, ""]
    granted_bad = [s for s in bad_scopes if g.evaluate(ok_snap, s) is True]  # type: ignore[arg-type]
    rec("C12", "consent/scope", "HELD" if not granted_bad else "FINDING",
        f"{len(bad_scopes)} malformed REQUESTED scopes -> {len(granted_bad)} granted; "
        f"audited=CONSENT_SCOPE_MALFORMED:{len(a.find('CONSENT_SCOPE_MALFORMED'))}")

    # MINOR-5 re-attack: is the evaluated scope carried on the result / the row?
    svc, audit, store = mk_svc(reader=ConsentReaderMap(rows), with_resolver=True)
    res = ingest(svc, consent_snapshot_id="cs_x", guest_id="guest_x", consent_scope=ConsentScope.CRM)
    row = store.get(res.idempotency_key)
    has_scope = any("scope" in f for f in res.__dataclass_fields__) or any(
        "scope" in f for f in row.__dataclass_fields__)
    rec("C13", "consent/MINOR-5", "OPEN" if not has_scope else "CLOSED",
        f"IngestResult fields={list(res.__dataclass_fields__)}; WebEventLog fields carry no evaluated "
        f"consent scope -> egress_eligible stays a scope-agnostic boolean")

    # NEW: guest_contacts adapter raises, reached via the resolver (step 0) and subject_matches (step 1)
    svc, audit, store = mk_svc(with_resolver=True, contacts=ThrowingContacts())
    raised, exc, res = seam_raises(svc, guest_id="guest_x", page_id="p_c14", session_id="s_c14")
    rec("C14", "consent/seam", "FINDING" if raised else "HELD",
        f"guest_contacts adapter raises at identity step 0: seam raised={raised} ({exc}); "
        f"audit records={len(audit)}")

    class HalfThrowingContacts:
        """resolve() works (guest found), but the later subject_matches lookup raises."""

        def __init__(self):
            self._n = 0

        def get(self, guest_id):
            self._n += 1
            if self._n == 1:
                return GUEST_ROWS["guest_mapped_ok"]
            raise RuntimeError("guest_contacts unreachable")

    svc, audit, store = mk_svc(with_resolver=True, contacts=HalfThrowingContacts(),
                               reader=ConsentReaderMap(rows))
    raised, exc, res = seam_raises(svc, consent_snapshot_id="cs_cust", guest_id="guest_mapped_ok",
                                   page_id="p_c15", session_id="s_c15")
    rec("C15", "consent/seam", "FINDING" if raised else "HELD",
        f"guest_contacts raises inside subject_matches (consent binding, step 1): seam raised={raised} "
        f"({exc}); audit records={len(audit)}")

    # gate bypass: force the posture flag ON at runtime
    original = config.EXTERNAL_SEND
    try:
        config.EXTERNAL_SEND = "ON"  # runtime probe only; never written to a file
        svc, audit, store = mk_svc(reader=ConsentReaderMap(rows), with_resolver=True)
        res = ingest(svc, consent_snapshot_id="cs_cust", guest_id="guest_mapped_ok",
                     consent_scope=ConsentScope.EXTERNAL_MEASUREMENT, page_id="p_c16", session_id="s_c16")
        rec("C16", "gate bypass", "HELD" if res.egress_eligible is False else "FINDING",
            f"config.EXTERNAL_SEND forced 'ON' at runtime: egress_eligible={res.egress_eligible}, "
            f"notes={res.notes} (permits_external_send() is an independent second lock)")
    finally:
        config.EXTERNAL_SEND = original

    # best case an attacker can construct: registered + VALID + all scopes + subject bound
    svc, audit, store = mk_svc(reader=ConsentReaderMap(rows), with_resolver=True)
    best = []
    for s in scopes:
        res = ingest(svc, consent_snapshot_id="cs_cust", guest_id="guest_mapped_ok", consent_scope=s,
                     page_id=f"p_c17_{s.value}", session_id=f"s_c17_{s.value}")
        best.append((s.value, res.egress_eligible))
    rec("C17", "gate bypass", "HELD" if not any(e for _, e in best) else "FINDING",
        f"BEST CASE (registered event + reader-issued VALID consent + all scopes + subject bound): "
        f"egress_eligible per scope = {best}")

    # dispatcher / sender sweep
    import app.measurement as pkg
    senders = []
    for path in sorted(pathlib.Path(pkg.__file__).parent.rglob("*.py")):
        src = path.read_text(encoding="utf-8")
        for pat in (r"\bimport\s+requests\b", r"\bimport\s+httpx\b", r"\bimport\s+urllib\b",
                    r"\bimport\s+socket\b", r"\bimport\s+http\b", r"\bsmtplib\b", r"\bboto3\b",
                    r"\bdef\s+send\b", r"\bdef\s+dispatch\b", r"\bdef\s+publish\b", r"\bdef\s+emit\b"):
            if re.search(pat, src):
                senders.append(f"{path.name}:{pat}")
    rec("C18", "gate bypass", "HELD" if not senders else "FINDING",
        f"dispatcher/network primitive sweep over app/measurement/**: {len(senders)} hits "
        f"-> there is no code path that can send anything")


# ===================================================================================================
# GROUP D — RULE-007 append-only / RULE-005 dedup semantics
# ===================================================================================================
def group_d_append_only():
    print("\n=== GROUP D — RULE-007 append-only ===")
    store = WebEventLogStore()
    row = WebEventLog("log_1", "VIEW_LANDING", "p", "s", "web", UTC_TS, "key_1", UTC_TS)
    store.append(row)

    blocked = 0
    for fn in (store.update, store.delete):
        try:
            fn(row)
        except AppendOnlyViolation:
            blocked += 1
    rec("D1", "append-only", "HELD" if blocked == 2 else "FINDING",
        f"store.update()/store.delete() -> {blocked}/2 raised AppendOnlyViolation")

    got = store.get("key_1")
    try:
        got.event_code = "MUTATED"  # type: ignore[misc]
        rec("D2", "append-only", "FINDING", "a stored row is mutable in place")
    except FrozenInstanceError:
        rec("D2", "append-only", "HELD", "a stored row is frozen (FrozenInstanceError on field write)")

    overwrite = WebEventLog("log_evil", "EVIL", "p2", "s2", "web", UTC_TS, "key_1", UTC_TS)
    result = store.append(overwrite)
    survived = store.get("key_1").event_code == "VIEW_LANDING"
    rec("D3", "append-only", "HELD" if (survived and result.created is False) else "FINDING",
        f"re-append a DIFFERENT row under an existing key: created={result.created}, "
        f"original survived={survived}, rows={len(store)}")

    # MINOR-7 re-attack: log_id uniqueness (DDL says PRIMARY KEY)
    store2 = WebEventLogStore()
    store2.append(WebEventLog("log_SAME", "A", "p", "s", "web", UTC_TS, "key_a", UTC_TS))
    store2.append(WebEventLog("log_SAME", "B", "p", "s", "web", UTC_TS, "key_b", UTC_TS))
    ids = [r.log_id for r in store2.all()]
    rec("D4", "append-only/MINOR-7", "OPEN" if len(set(ids)) < len(ids) else "CLOSED",
        f"two rows with duplicate log_id accepted in memory ({ids}) while migration 0001 declares "
        f"log_id ... PRIMARY KEY -> staged store does not enforce an invariant the physical table will")

    # NEW: dedup vs the persisted consent binding (RULE-005 key excludes consent_snapshot_id)
    rows = {"cs_x": ConsentSnapshot("cs_x", "guest_x", ConsentState.VALID, UTC_TS,
                                    frozenset({ConsentScope.EXTERNAL_MEASUREMENT}))}
    svc, audit, store3 = mk_svc(reader=ConsentReaderMap(rows))
    r1 = ingest(svc, page_id="pd5", session_id="sd5", raw_event_hash="hd5")            # no consent
    r2 = ingest(svc, page_id="pd5", session_id="sd5", raw_event_hash="hd5",
                consent_snapshot_id="cs_x", guest_id="guest_x")                        # same event + consent
    stored = store3.get(r1.idempotency_key)
    rec("D5", "dedup/consent", "INFO",
        f"identical RULE-005 components, different consent binding: rows={len(store3)}, "
        f"log_created(second)={r2.log_created}, persisted consent_snapshot_id={stored.consent_snapshot_id!r}, "
        f"second-call egress decision recomputed live (egress_eligible={r2.egress_eligible}) "
        f"-> first-write-wins on the row (consistent with RULE-007), eligibility is never cached")


# ===================================================================================================
# GROUP E — PII / audit hygiene (RULE-014 / H02; routes to M6-P1006)
# ===================================================================================================
def group_e_pii():
    print("\n=== GROUP E — PII / audit hygiene ===")
    from app.measurement.masking import mask

    svc, audit, store = mk_svc(with_resolver=True)
    res = ingest(svc, guest_id="guest_mapped_ok", page_id="pe1", session_id="se1")
    raw_hits = [r for r in audit.records if r.subject_masked in ("guest_mapped_ok", "cust_0001")]
    rec("E1", "PII/RULE-014", "HELD" if not raw_hits else "FINDING",
        f"identity through the seam: {len(raw_hits)} raw identity values in the audit sink; "
        f"resolution={res.identity.confidence.value}, masked guest={res.identity.guest_id_masked!r}, "
        f"masked customer={res.identity.mapped_customer_id_masked!r}")

    shorts = {v: mask(v) for v in ("a", "ab", "abcde", "abcdef")}
    leak = [v for v, m in shorts.items() if len(v) <= 5 and m != "***"]
    rec("E2", "PII/RULE-014", "HELD" if not leak else "FINDING",
        f"mask() on short values {shorts} -> {len(leak)} partial-reveal leaks")

    # PII-shaped unknown event_code probes, CONSTRUCTED programmatically (no literal in this file)
    digits = "".join(chr(0x30 + d) for d in (0, 9, 1, 2, 3, 4, 5, 6, 7, 8))          # 10-digit VN-mobile shape
    at = chr(0x40)
    dot = chr(0x2E)
    emailish = "user" + at + "example" + dot + "com"
    idish = "guest_" + digits
    probes = {
        "vn-mobile-shaped (digits only)": digits,
        "email-shaped (contains @)": emailish,
        "raw-guest-id-shaped": idish,
        "oversize (300 chars)": "X" * 300,
        "newline-bearing": "VIEW_LANDING" + chr(10) + "INJECTED",
        "null-byte-bearing": "VIEW" + chr(0) + "LANDING",
    }
    verbatim = []
    for label, value in probes.items():
        a = AuditLog()
        EventValidator(Registry(REG_ROWS), a).validate(value)
        stored = a.records[-1].event_code
        if stored == value:
            verbatim.append(label)
    rec("E3", "PII/SEC-PII-01", "FINDING" if verbatim else "HELD",
        f"unknown (attacker-shaped) event_code stored VERBATIM in AuditRecord.event_code for: "
        f"{verbatim or 'none'} — the shape allowlist [A-Za-z0-9_.:-]{{1,64}} admits a bare digit run and an "
        f"underscore-joined id, so an identifier-shaped payload survives the SEC-PII-01 sanitizer "
        f"(wrapped correctly for: {[k for k in probes if k not in verbatim]})")

    a = AuditLog()
    a.record("HOLD", "X", detail="D" * 500)
    a.record("A" * 200, "R" * 200)
    a.record("HOLD", "Y", subject="gu" + chr(0) + "st" + chr(10) + "_more")
    bounded = (len(a.records[0].detail) <= 140 and len(a.records[1].action) <= 80
               and chr(10) not in (a.records[2].subject_masked or ""))
    rec("E4", "PII/audit", "HELD" if bounded else "FINDING",
        f"detail bounded={len(a.records[0].detail)} chars, action bounded={len(a.records[1].action)}, "
        f"control chars stripped from masked subject")

    # NEW: a non-string event_code reaching the sanitizer
    a = AuditLog()
    try:
        a.record("REJECT", "UNKNOWN_EVENT_NOT_IN_REGISTRY", event_code=12345)  # type: ignore[arg-type]
        rec("E5", "PII/audit", "HELD", "non-string event_code handled by the sanitizer")
    except Exception as exc:  # noqa: BLE001
        rec("E5", "PII/audit", "FINDING",
            f"AuditLog.record(event_code=int) raises {type(exc).__name__}: {exc} "
            f"-> _safe_event_code assumes str; a non-string channel value crashes the audit sink itself")

    # does any PII-shaped value reach the append-only row?
    svc, audit, store = mk_svc(with_resolver=True)
    res = ingest(svc, guest_id="guest_mapped_ok", session_id=digits, page_id="pe6")
    row = store.get(res.idempotency_key)
    rec("E6", "PII/row", "INFO",
        f"web_event_logs.session_id is stored RAW as supplied (declared PII-pseudonymous, "
        f"'mask if it resolves to a person', M6-OD-012 OPEN): stored len={len(row.session_id)} — "
        f"no masking is applied at the store layer; consent_snapshot_id={row.consent_snapshot_id!r}")


# ===================================================================================================
# GROUP F — overreach / posture / data-mart
# ===================================================================================================
def group_f_overreach():
    print("\n=== GROUP F — overreach & posture ===")
    import app as app_pkg
    root = pathlib.Path(app_pkg.__file__).parent
    files = sorted(root.rglob("*.py"))

    forbidden = {
        "pricing/quote": r"\b(price|pricing|quote|quotesnapshot|discount|tariff)\b",
        "order/payment": r"\b(order_verified|create_order|place_order|payment|checkout|cod_)\b",
        "revenue write": r"\b(revenue|gmv|invoice|refund)\s*=",
        "CRM send": r"\b(crm_send|send_crm|zalo|messenger_send|push_message)\b",
        "commission": r"\b(commission|payout|affiliate_fee)\b",
        "budget/scale": r"\b(scale_budget|raise_budget|set_budget|budget\s*=|autoscale)\b",
        "publish/optimize": r"\b(publish_optimization|auto_publish|apply_optimization)\b",
        "data mart trigger": r"\b(data_mart|datamart)\b.*\b(trigger|owner|fire)\b",
        "network": r"\b(requests|httpx|urllib|socket|aiohttp|smtplib|boto3)\b",
        "db apply": r"\b(execute|executemany|cursor|psycopg|sqlalchemy|create_engine)\b",
    }
    hits: dict[str, list[str]] = {}
    for path in files:
        src = path.read_text(encoding="utf-8")
        # strip comments/docstrings crudely so prose about what M6 must NOT do is not counted as a code path
        code = "\n".join(l.split("#")[0] for l in src.splitlines())
        code = re.sub(r'""".*?"""', "", code, flags=re.S)
        for label, pat in forbidden.items():
            for m in re.finditer(pat, code, flags=re.I):
                hits.setdefault(label, []).append(f"{path.name}:{m.group(0)}")
    rec("F1", "overreach", "HELD" if not hits else "FINDING",
        f"symbol sweep over {len(files)} app/ files for pricing/order/payment/revenue/CRM/commission/"
        f"budget/publish/data-mart-trigger/network/db-apply -> {hits or 'no hit'}")

    posture = (config.GLOBAL_GATEWAY_STATE, config.PRODUCTION_FLAG, config.EXTERNAL_SEND,
               config.is_external_send_enabled())
    rec("F2", "posture", "HELD" if posture == ("BLOCKED", "OFF", "OFF", False) else "FINDING",
        f"(GLOBAL_GATEWAY_STATE, PRODUCTION_FLAG, EXTERNAL_SEND, is_external_send_enabled()) = {posture}")

    # RULE-007: is there any DDL/DML in the slice that could be applied by this code?
    sql_files = sorted((root.parent / "migrations").glob("*.sql"))
    applied = []
    for path in files:
        src = path.read_text(encoding="utf-8")
        if re.search(r"\.sql\b", src) or re.search(r"\b(UPDATE|DELETE|DROP|TRUNCATE)\s+\w", src):
            applied.append(path.name)
    rec("F3", "posture", "HELD" if not applied else "FINDING",
        f"{len(sql_files)} staged .sql file(s) exist; app/ files that reference/execute SQL DDL/DML: "
        f"{applied or 'none'} -> the migration is staged text, not reachable from code")


def main() -> int:
    for fn in (group_a_major_reattack, group_b_event_drift, group_c_consent,
               group_d_append_only, group_e_pii, group_f_overreach):
        try:
            fn()
        except Exception:  # noqa: BLE001
            print(f"!! harness error in {fn.__name__}")
            traceback.print_exc()
    print("\n=== SUMMARY ===")
    from collections import Counter
    counts = Counter(v for _, _, v, _ in RESULTS)
    print(f"total attacks recorded: {len(RESULTS)}  {dict(counts)}")
    for verdict in ("FINDING", "OPEN"):
        for aid, area, v, detail in RESULTS:
            if v == verdict:
                print(f"  {verdict:<7} {aid:<6} {area:<22} {detail[:150]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
