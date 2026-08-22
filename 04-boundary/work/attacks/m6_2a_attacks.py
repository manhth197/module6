"""M6-P1005 BOUNDARY_ADVERSARY — executable attack fixtures against the STAGED slice M6.2A.

READ-ONLY against the implementation: this script imports the staged package and drives its public seams.
It writes nothing into 04-artifacts/impl/, applies no migration, opens no socket, flips no flag.

Every attack prints: ATTACK id | verdict | evidence
  HELD    = the defense held (attack failed)  -> good
  FINDING = the attack succeeded / a defect is demonstrated -> boundary finding

All identity-shaped values are SYNTHETIC and are built programmatically so that no PII-shaped literal
(phone/email) ever appears in this file or in any report generated from it.
"""
from __future__ import annotations

import sys
import pathlib
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

IMPL = pathlib.Path(__file__).resolve().parents[2] / "04-artifacts" / "impl" / "M6.2A"
sys.path.insert(0, str(IMPL))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from app import config                                                    # noqa: E402
from app.measurement.audit import AuditLog                                # noqa: E402
from app.measurement.consent.gate import ConsentGate                      # noqa: E402
from app.measurement.identity.resolver import Confidence, IdentityResolver  # noqa: E402
from app.measurement.ingest import IngestService                          # noqa: E402
from app.measurement.logs.idempotency import build_idempotency_key, normalize_ts  # noqa: E402
from app.measurement.logs.web_event_log_store import (                    # noqa: E402
    AppendOnlyViolation,
    WebEventLogStore,
)
from app.measurement.masking import mask                                  # noqa: E402
from app.measurement.models.consumed import (                             # noqa: E402
    ConsentScope,
    ConsentSnapshot,
    ConsentState,
    DataSensitivity,
    EventRegistryRow,
    GuestContact,
    RegistrationState,
)
from app.measurement.models.web_event_log import WebEventLog              # noqa: E402
from app.measurement.ports import (                                       # noqa: E402
    ConsentReader,
    CustomerRefReader,
    EventRegistryReader,
    GuestContactReader,
)
from app.measurement.registry.validator import (                          # noqa: E402
    EventDecision,
    EventValidator,
    permits_external_send,
)

NOW = datetime(2026, 7, 29, 10, 0, 0, tzinfo=timezone.utc)
RESULTS: list[tuple[str, str, str, str]] = []   # (id, area, verdict, evidence)


def rec(aid: str, area: str, held: bool, evidence: str) -> None:
    RESULTS.append((aid, area, "HELD" if held else "FINDING", evidence))


# ---------------------------------------------------------------- test doubles (read-only ports)
class FakeRegistry:
    def __init__(self, rows): self._rows = {r.event_code: r for r in rows}
    def get(self, event_code): return self._rows.get(event_code)


class FakeContacts:
    def __init__(self, rows): self._rows = {r.guest_id: r for r in rows}
    def get(self, guest_id): return self._rows.get(guest_id)


class FakeCustomers:
    def __init__(self, ids): self._ids = set(ids)
    def exists(self, customer_id): return customer_id in self._ids


class FakeConsentReader:
    def __init__(self, state): self._state = state
    def get(self, consent_snapshot_id): return None
    def current_state(self, subject_ref): return self._state


ACTIVE_EVENT = EventRegistryRow(
    event_code="ADS_PAGE_VIEW", registration_state=RegistrationState.ACTIVE,
    owner="core-event-governance", channel="web",
    data_sensitivity=DataSensitivity.INTERNAL, external_send_policy="ALLOW",
)
DEREG_EVENT = EventRegistryRow(
    event_code="ADS_OLD_EVENT", registration_state=RegistrationState.DEREGISTERED,
    owner="core-event-governance",
)
NO_OWNER_EVENT = EventRegistryRow(
    event_code="ADS_NO_OWNER", registration_state=RegistrationState.ACTIVE, owner=None,
)
REGISTRY = FakeRegistry([ACTIVE_EVENT, DEREG_EVENT, NO_OWNER_EVENT])

SYN_GUEST = "guest_" + "9" * 12          # synthetic, non-PII-shaped
SYN_CUST = "cust_" + "7" * 12


def new_stack():
    audit = AuditLog()
    store = WebEventLogStore()
    gate = ConsentGate(audit)
    validator = EventValidator(REGISTRY, audit)
    contacts = FakeContacts([
        GuestContact(guest_id=SYN_GUEST, contact_fingerprint="fp_" + "3" * 10,
                     mapped_customer_id=SYN_CUST, mapping_audit_ref="audit_ref_0001"),
        GuestContact(guest_id=SYN_GUEST + "_noaudit", contact_fingerprint="fp_" + "4" * 10,
                     mapped_customer_id=SYN_CUST, mapping_audit_ref=None),
    ])
    resolver = IdentityResolver(contacts, FakeCustomers([SYN_CUST]), audit)
    return audit, store, gate, validator, resolver, IngestService(validator, store, gate, resolver)


def snap(state, scopes, sid="cs_1"):
    return ConsentSnapshot(consent_snapshot_id=sid, subject_ref=SYN_GUEST,
                           consent_state=state, captured_at=NOW, consent_scope=frozenset(scopes))


def ingest(svc, **kw):
    base = dict(event_code="ADS_PAGE_VIEW", page_id="page_1", session_id="sess_1",
                source="web", event_ts=NOW, raw_event_hash="h" * 8)
    base.update(kw)
    return svc.ingest_event(**base)


# ================================================================ A. CONSENT (M6-FAIL-002 / RULE-002)
def attack_consent():
    audit, store, gate, _v, _r, svc = new_stack()
    all_scopes = list(ConsentScope)

    # A1 absent snapshot -> every scope denied
    denied = [gate.evaluate(None, s) for s in all_scopes]
    rec("A1", "consent", not any(denied), f"absent snapshot -> evaluate={denied} (all must be False)")

    # A2 non-VALID states denied on every scope
    bad = []
    for st in (ConsentState.MISSING, ConsentState.EXPIRED, ConsentState.OPT_OUT):
        for s in all_scopes:
            if gate.evaluate(snap(st, all_scopes), s):
                bad.append((st.value, s.value))
    rec("A2", "consent", not bad, f"MISSING/EXPIRED/OPT_OUT on all scopes -> granted={bad} (must be empty)")

    # A3 VALID but scope not granted
    only_ext = snap(ConsentState.VALID, [ConsentScope.EXTERNAL_MEASUREMENT])
    leaked = [s.value for s in (ConsentScope.AUDIENCE_SYNC, ConsentScope.CRM) if gate.evaluate(only_ext, s)]
    rec("A3", "consent", not leaked, f"VALID(external only) -> other scopes granted={leaked} (must be empty)")

    # A4 empty scope set with VALID state
    rec("A4", "consent", not gate.evaluate(snap(ConsentState.VALID, []), ConsentScope.CRM),
        "VALID with empty consent_scope -> CRM must be denied")

    # A5 state forgery via raw string (JSON/duck-typed deserialization)
    forged = ConsentSnapshot(consent_snapshot_id="cs_forge", subject_ref=SYN_GUEST,
                             consent_state="VALID", captured_at=NOW,           # type: ignore[arg-type]
                             consent_scope=frozenset(all_scopes))
    a5_audit_before = len(audit)
    try:
        granted = gate.evaluate(forged, ConsentScope.EXTERNAL_MEASUREMENT)
        rec("A5", "consent", not granted,
            f"raw-string consent_state='VALID' -> granted={granted} (must be False, fail-closed)")
    except Exception as exc:                      # noqa: BLE001 — the crash IS the observation
        rec("A5", "consent/robustness", False,
            f"raw-string consent_state crashed the gate: {type(exc).__name__}: {exc} "
            f"(no consent granted, but the denial is NOT audited: records added="
            f"{len(audit) - a5_audit_before}) — deny-by-exception at gate.py:36")

    # A5b same duck-typed state on the NON-valid side (e.g. 'OPT_OUT' as a raw string)
    forged2 = ConsentSnapshot(consent_snapshot_id="cs_forge2", subject_ref=SYN_GUEST,
                              consent_state="OPT_OUT", captured_at=NOW,        # type: ignore[arg-type]
                              consent_scope=frozenset(all_scopes))
    try:
        g2 = gate.evaluate(forged2, ConsentScope.EXTERNAL_MEASUREMENT)
        rec("A5b", "consent", not g2, f"raw-string consent_state='OPT_OUT' -> granted={g2}")
    except Exception as exc:                      # noqa: BLE001
        rec("A5b", "consent/robustness", False,
            f"raw-string consent_state='OPT_OUT' crashed the gate: {type(exc).__name__}: {exc}")

    # A5c the same malformed consumed snapshot arriving through the real ingest seam
    try:
        r5 = ingest(svc, consent_snapshot=forged, session_id="sess_forged")
        rec("A5c", "consent", not r5.egress_eligible,
            f"malformed snapshot via ingest -> egress_eligible={r5.egress_eligible}")
    except Exception as exc:                      # noqa: BLE001
        rec("A5c", "consent/robustness", False,
            f"malformed consumed snapshot propagates out of IngestService.ingest_event: "
            f"{type(exc).__name__}: {exc} (ingest of that event is aborted, nothing sent)")

    # A6 mutate a frozen snapshot to upgrade consent
    s = snap(ConsentState.OPT_OUT, all_scopes)
    try:
        s.consent_state = ConsentState.VALID          # type: ignore[misc]
        held6, ev6 = False, "frozen snapshot was MUTATED to VALID"
    except FrozenInstanceError:
        held6, ev6 = True, "FrozenInstanceError — consent snapshot is immutable"
    rec("A6", "consent", held6, ev6)

    # A7 full ingest with NO consent: logged internally, but egress must be blocked + denial audited
    r = ingest(svc, consent_snapshot=None)
    audited = bool(audit.find("CONSENT_SNAPSHOT_ABSENT"))
    rec("A7", "consent", (r.logged and not r.egress_eligible and audited),
        f"no-consent ingest -> logged={r.logged} egress_eligible={r.egress_eligible} "
        f"denial_audited={audited} notes={r.notes}")

    # A8 gate bypass: flip the staged posture constant at runtime, then re-attack
    original = config.EXTERNAL_SEND
    try:
        config.EXTERNAL_SEND = "ON"                    # attacker flips the module constant
        r2 = ingest(svc, consent_snapshot=None, session_id="sess_flip")
        held8 = (not r2.egress_eligible) and (permits_external_send("ALLOW") is False)
        ev8 = (f"config.EXTERNAL_SEND forced to 'ON' -> egress_eligible={r2.egress_eligible}; "
               f"permits_external_send('ALLOW')={permits_external_send('ALLOW')} "
               f"(second, independent lock)")
    finally:
        config.EXTERNAL_SEND = original
    rec("A8", "consent/gate-bypass", held8, ev8)

    # A9 send-time checkpoint: event-time VALID but consent lapsed at send time
    valid = snap(ConsentState.VALID, all_scopes)
    lapsed = gate.permits_send(valid, ConsentScope.EXTERNAL_MEASUREMENT, FakeConsentReader(ConsentState.OPT_OUT))
    still = gate.permits_send(valid, ConsentScope.EXTERNAL_MEASUREMENT, FakeConsentReader(ConsentState.VALID))
    rec("A9", "consent", (not lapsed) and still,
        f"permits_send: lapsed-at-send={lapsed} (must be False), still-valid={still} (must be True)")


# ================================================================ B. EVENT DRIFT (M6-FAIL-003 / RULE-001/018)
def attack_event_drift():
    audit, store, gate, validator, _r, svc = new_stack()

    # B1 unknown event -> REJECT, not logged, audited
    r = ingest(svc, event_code="ADS_TOTALLY_MADE_UP")
    held1 = (r.validation.decision is EventDecision.REJECT and not r.logged
             and len(store) == 0 and bool(audit.find("UNKNOWN_EVENT_NOT_IN_REGISTRY")))
    rec("B1", "event-drift", held1,
        f"unknown event -> decision={r.validation.decision.value} logged={r.logged} "
        f"rows={len(store)} audited={bool(audit.find('UNKNOWN_EVENT_NOT_IN_REGISTRY'))}")

    # B2 de-registered -> HOLD, not logged
    r = ingest(svc, event_code="ADS_OLD_EVENT")
    rec("B2", "event-drift", r.validation.decision is EventDecision.HOLD and not r.logged,
        f"de-registered -> decision={r.validation.decision.value} logged={r.logged} (never false-ALLOW)")

    # B3 missing owner -> HOLD, not logged
    r = ingest(svc, event_code="ADS_NO_OWNER")
    rec("B3", "event-drift", r.validation.decision is EventDecision.HOLD and not r.logged,
        f"missing owner -> decision={r.validation.decision.value} logged={r.logged}")

    # B4 registration_state forged as a raw string
    forged_reg = FakeRegistry([EventRegistryRow(event_code="ADS_FORGED",
                                                registration_state="ACTIVE",   # type: ignore[arg-type]
                                                owner="x")])
    v2 = EventValidator(forged_reg, AuditLog())
    d = v2.validate("ADS_FORGED").decision
    rec("B4", "event-drift", d is not EventDecision.ACCEPT,
        f"raw-string registration_state='ACTIVE' -> decision={d.value} (must not ACCEPT)")

    # B5 near-miss / case / whitespace variants must NOT fuzzy-match a registered code
    variants = ["ads_page_view", "ADS_PAGE_VIEW ", " ADS_PAGE_VIEW", "ADS_PAGE_VIEW\n", "ADS_PAGE_VIEW​"]
    accepted = [v for v in variants if validator.validate(v).decision is EventDecision.ACCEPT]
    rec("B5", "event-drift", not accepted,
        f"case/whitespace/zero-width variants accepted={len(accepted)} (must be 0 — no silent normalization)")

    # B6 external_send_policy tokens must never mean "allow" while M6-OD-003 is OPEN
    tokens = ["ALLOW", "allow", "true", "1", "YES", "ENABLED", "*", None]
    allowed = [t for t in tokens if permits_external_send(t)]
    rec("B6", "event-drift/egress", not allowed,
        f"external_send_policy tokens treated as allow={allowed} (must be empty; M6-OD-003 OPEN)")

    # B7 structural: the CONSUMED ports expose no write method (M6 cannot insert an event code)
    writes = []
    for proto in (EventRegistryReader, GuestContactReader, ConsentReader, CustomerRefReader):
        for name in dir(proto):
            if name.startswith("_"):
                continue
            if any(name.lower().startswith(p) for p in
                   ("add", "insert", "update", "upsert", "delete", "set", "write", "save", "create")):
                writes.append(f"{proto.__name__}.{name}")
    rec("B7", "boundary/ownership", not writes,
        f"write-ish methods on CONSUMED ports={writes} (must be empty — read-only ports)")


# ================================================================ C. DEDUP (RULE-005)
def attack_dedup():
    _a, store, _g, _v, _r, svc = new_stack()

    # C1 exact duplicate -> one row only
    r1 = ingest(svc)
    r2 = ingest(svc)
    rec("C1", "dedup", (r1.log_created and not r2.log_created and len(store) == 1),
        f"same event twice -> created={r1.log_created}/{r2.log_created} rows={len(store)} notes={r2.notes}")

    # C2 sub-second jitter must still dedup
    r3 = ingest(svc, event_ts=NOW + timedelta(microseconds=999999))
    rec("C2", "dedup", not r3.log_created,
        f"same event +999999us -> created={r3.log_created} (normalize_ts drops microseconds)")

    # C3 DELIMITER INJECTION: two DIFFERENT (page_id, session_id) pairs -> same canonical string?
    k_a = build_idempotency_key("E", "P|X", "Y", "H", "T")
    k_b = build_idempotency_key("E", "P", "X|Y", "H", "T")
    rec("C3", "dedup", k_a != k_b,
        "delimiter injection: key(page='P|X',sess='Y') vs key(page='P',sess='X|Y') -> "
        f"{'COLLISION (identical key)' if k_a == k_b else 'distinct keys'}")

    # C3b same collision driven through the real ingest seam -> does a distinct event get swallowed?
    _a2, store2, _g2, _v2, _r2, svc2 = new_stack()
    e1 = svc2.ingest_event(event_code="ADS_PAGE_VIEW", page_id="p1|s1", session_id="s2",
                           source="web", event_ts=NOW, raw_event_hash="h" * 8)
    e2 = svc2.ingest_event(event_code="ADS_PAGE_VIEW", page_id="p1", session_id="s1|s2",
                           source="web", event_ts=NOW, raw_event_hash="h" * 8)
    swallowed = (e1.idempotency_key == e2.idempotency_key) and not e2.log_created
    rec("C3b", "dedup", not swallowed,
        f"two DISTINCT (page,session) events via ingest -> same_key={e1.idempotency_key == e2.idempotency_key}, "
        f"second_created={e2.log_created}, rows={len(store2)} "
        f"({'distinct event silently swallowed as a duplicate' if swallowed else 'both preserved'})")

    # C4 TIMEZONE normalization: the same instant expressed three ways must dedup to ONE row
    _a3, store3, _g3, _v3, _r3, svc3 = new_stack()
    aware_utc = datetime(2026, 7, 29, 10, 0, 0, tzinfo=timezone.utc)
    naive_same = datetime(2026, 7, 29, 10, 0, 0)                                  # same wall clock, no tz
    other_off = datetime(2026, 7, 29, 17, 0, 0, tzinfo=timezone(timedelta(hours=7)))  # SAME instant, +07:00
    keys = [normalize_ts(t) for t in (aware_utc, naive_same, other_off)]
    for i, t in enumerate((aware_utc, naive_same, other_off)):
        svc3.ingest_event(event_code="ADS_PAGE_VIEW", page_id="p", session_id="s",
                          source="web", event_ts=t, raw_event_hash="h" * 8)
    rec("C4", "dedup", len(store3) == 1,
        f"same instant as aware-UTC / naive / +07:00 -> normalize_ts={keys} rows={len(store3)} "
        f"(docstring claims 'in UTC'; {'double-logged' if len(store3) > 1 else 'deduped'})")


# ================================================================ D. APPEND-ONLY (RULE-007)
def attack_append_only():
    _a, store, _g, _v, _r, svc = new_stack()
    r = ingest(svc)
    key = r.idempotency_key

    # D1 explicit update/delete
    for name in ("update", "delete"):
        try:
            getattr(store, name)(key)
            rec("D1_" + name, "append-only", False, f"store.{name}() succeeded — history is rewritable")
        except AppendOnlyViolation as exc:
            rec("D1_" + name, "append-only", True, f"store.{name}() raised AppendOnlyViolation: {exc}")

    # D2 mutate a row obtained through the read path
    row = store.get(key)
    try:
        row.event_code = "ADS_SOMETHING_ELSE"      # type: ignore[misc]
        rec("D2", "append-only", False, "row returned by store.get() was MUTATED in place")
    except FrozenInstanceError:
        rec("D2", "append-only", True, "FrozenInstanceError — stored row is immutable via the read path")

    # D3 history rewrite by re-appending a DIFFERENT row under the same idempotency_key
    before = store.get(key)
    attacker_row = WebEventLog(
        log_id="log_attacker", event_code="ADS_PAGE_VIEW", page_id="ATTACKER_PAGE",
        session_id="ATTACKER_SESSION", source="attacker", event_ts=NOW,
        idempotency_key=key, ingested_at=NOW, consent_snapshot_id=None, correlation_id=None,
    )
    res = store.append(attacker_row)
    after = store.get(key)
    rec("D3", "append-only", (not res.created) and after is before and after.page_id != "ATTACKER_PAGE",
        f"re-append under an existing key -> created={res.created}, stored page_id={after.page_id!r} "
        f"(original must survive), rows={len(store)}")


# ================================================================ E. PII / channel-origin (RULE-014 / H02)
def attack_pii():
    audit, _s, gate, _v, resolver, svc = new_stack()

    # E1 identity subject masked in the audit trail
    resolver.resolve(SYN_GUEST)
    leaked = [r for r in audit.records if r.subject_masked and SYN_GUEST in str(r.subject_masked)]
    sample = [r.subject_masked for r in audit.records if r.subject_masked][:1]
    rec("E1", "pii", not leaked, f"identity audit subject_masked sample={sample} raw_leaks={len(leaked)}")

    # E2 masked identity is never returned raw by the resolver
    res = resolver.resolve(SYN_GUEST)
    rec("E2", "pii", SYN_GUEST not in res.guest_id_masked and (res.mapped_customer_id_masked or "") != SYN_CUST,
        f"resolution exposes guest={res.guest_id_masked} customer={res.mapped_customer_id_masked} "
        f"confidence={res.confidence.value}")

    # E3 channel-origin event_code is attacker-controlled: does a PII-shaped unknown code land RAW in audit?
    #    Built programmatically so no PII-shaped literal exists in this file.
    pii_shaped = "0" + "9" * 9                      # 10-digit VN-mobile-shaped synthetic string
    at_shaped = "abc" + chr(64) + "example.test"    # email-shaped synthetic string
    a2 = AuditLog()
    v2 = EventValidator(REGISTRY, a2)
    v2.validate(pii_shaped)
    v2.validate(at_shaped)
    raw_in_audit = [r.event_code for r in a2.records if r.event_code in (pii_shaped, at_shaped)]
    rec("E3", "pii", not raw_in_audit,
        f"unknown channel-origin event_code stored in audit unmasked count={len(raw_in_audit)} "
        f"(field=AuditRecord.event_code; masked_form_would_be={mask(pii_shaped)!r})")

    # E4 mask() must not reveal too much of a short value
    shorts = {v: mask(v) for v in ("a", "ab", "abcde", "abcdef")}
    bad = [v for v, m in shorts.items() if len(v) <= 5 and m != "***"]
    rec("E4", "pii", not bad, f"mask() on short values={shorts} leaky={bad}")

    # E5 identity mapping without audit evidence must not be trusted (RULE-006)
    res2 = resolver.resolve(SYN_GUEST + "_noaudit")
    rec("E5", "identity", res2.confidence is Confidence.HOLD,
        f"mapping without mapping_audit_ref -> confidence={res2.confidence.value} (must be HOLD)")

    # E6 unknown guest must not be guessed into a customer
    res3 = resolver.resolve("guest_does_not_exist")
    rec("E6", "identity", res3.confidence is Confidence.HOLD and res3.mapped_customer_id_masked is None,
        f"unknown guest -> confidence={res3.confidence.value} mapped={res3.mapped_customer_id_masked}")


# ================================================================ F. staged posture
def attack_posture():
    rec("F1", "posture", config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF",
        f"GLOBAL_GATEWAY_STATE={config.GLOBAL_GATEWAY_STATE} PRODUCTION_FLAG={config.PRODUCTION_FLAG}")
    _a, _s, _g, _v, _r, svc = new_stack()
    valid = snap(ConsentState.VALID, list(ConsentScope))
    r = ingest(svc, consent_snapshot=valid)
    rec("F2", "posture", not r.egress_eligible,
        f"BEST CASE for the attacker (registered event + VALID consent + all scopes) -> "
        f"egress_eligible={r.egress_eligible} notes={r.notes}")


def main() -> int:
    for fn in (attack_consent, attack_event_drift, attack_dedup,
               attack_append_only, attack_pii, attack_posture):
        try:
            fn()
        except Exception as exc:                  # noqa: BLE001 — never let one crash hide the rest
            rec(fn.__name__, "harness", False, f"attack group aborted: {type(exc).__name__}: {exc}")
    width = max(len(a) for a, _, _, _ in RESULTS)
    print("=" * 100)
    print(f"{'ATTACK'.ljust(width)} | {'AREA'.ljust(20)} | VERDICT | EVIDENCE")
    print("=" * 100)
    for aid, area, verdict, ev in RESULTS:
        print(f"{aid.ljust(width)} | {area.ljust(20)} | {verdict.ljust(7)} | {ev}")
    findings = [r for r in RESULTS if r[2] == "FINDING"]
    print("=" * 100)
    print(f"TOTAL {len(RESULTS)} attacks | HELD {len(RESULTS) - len(findings)} | FINDINGS {len(findings)}")
    for aid, area, _v, ev in findings:
        print(f"  FINDING {aid} [{area}] {ev}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
