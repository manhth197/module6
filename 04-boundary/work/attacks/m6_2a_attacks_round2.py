"""M6-P1005 round 2 — first-hand re-execution of the CONSENT-PROVENANCE / FAIL-OPEN attacks.

Round 1 (m6_2a_attacks.py) attacked the gates with well-formed inputs. Round 2 attacks the SEAM CONTRACT:
what the gate trusts about the CONSUMED consent snapshot it is handed, and what the validator trusts about
the registry row it is handed. READ-ONLY: imports the staged package, writes nothing into 04-artifacts/impl/.
"""
from __future__ import annotations

import pathlib
import sys
from datetime import datetime, timezone

IMPL = pathlib.Path(__file__).resolve().parents[2] / "04-artifacts" / "impl" / "M6.2A"
sys.path.insert(0, str(IMPL))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from app.measurement.audit import AuditLog                                # noqa: E402
from app.measurement.consent.gate import ConsentGate                      # noqa: E402
from app.measurement.ingest import IngestService                          # noqa: E402
from app.measurement.logs.web_event_log_store import WebEventLogStore     # noqa: E402
from app.measurement.models.consumed import (                             # noqa: E402
    ConsentScope, ConsentSnapshot, ConsentState,
    DataSensitivity, EventRegistryRow, RegistrationState,
)
from app.measurement.models.web_event_log import WebEventLog              # noqa: E402
from app.measurement.registry.validator import EventDecision, EventValidator  # noqa: E402

NOW = datetime(2026, 7, 29, 10, 0, 0, tzinfo=timezone.utc)
OUT: list[tuple[str, str, str]] = []


def rec(aid, held, ev):
    OUT.append((aid, "HELD" if held else "FINDING", ev))


ACTIVE = EventRegistryRow("ADS_PAGE_VIEW", RegistrationState.ACTIVE, owner="core",
                          data_sensitivity=DataSensitivity.INTERNAL)


class Reg:
    def __init__(self, rows): self._r = {r.event_code: r for r in rows}
    def get(self, code): return self._r.get(code)


def stack():
    a = AuditLog(); s = WebEventLogStore(); g = ConsentGate(a)
    v = EventValidator(Reg([ACTIVE]), a)
    return a, s, g, v, IngestService(v, s, g)


# ---- N1: consent_scope delivered as a raw STRING -> `scope not in <str>` becomes SUBSTRING matching
def n1():
    _a, _s, gate, _v, _svc = stack()
    cases = {
        "crm:false": ConsentScope.CRM,                       # payload EXPLICITLY denies crm
        "no_crm": ConsentScope.CRM,
        "opt_out_of_crm": ConsentScope.CRM,
        '{"crm": false, "external_measurement": false}': ConsentScope.EXTERNAL_MEASUREMENT,
    }
    granted = {}
    for raw, scope in cases.items():
        snap = ConsentSnapshot("cs_str", "subj_000000", ConsentState.VALID, NOW,
                               consent_scope=raw)             # type: ignore[arg-type]
        granted[raw] = gate.evaluate(snap, scope)
    rec("N1", not any(granted.values()),
        f"consent_scope as raw str -> granted={granted} "
        f"(a payload that DENIES a scope must never grant it)")


# ---- N2: the seam trusts a caller-supplied snapshot object; no ConsentReader lookup, no provenance check
def n2():
    _a, store, gate, _v, svc = stack()
    forged = ConsentSnapshot("cs_NEVER_ISSUED_BY_CONSENT_SYSTEM", "subj_000000",
                             ConsentState.VALID, NOW, frozenset(ConsentScope))
    r = svc.ingest_event(event_code="ADS_PAGE_VIEW", page_id="p", session_id="s", source="web",
                         event_ts=NOW, raw_event_hash="h" * 8, consent_snapshot=forged)
    row = store.get(r.idempotency_key)
    persisted = row.consent_snapshot_id if row else None

    class Duck:                                              # not a ConsentSnapshot at all
        consent_snapshot_id = "cs_duck"
        subject_ref = "subj_000000"
        consent_state = ConsentState.VALID
        captured_at = NOW
        consent_scope = frozenset(ConsentScope)
    duck_ok = gate.evaluate(Duck(), ConsentScope.CRM)        # type: ignore[arg-type]
    has_reader = any("read" in a.lower() or "consent_reader" in a.lower()
                     for a in vars(svc).keys())
    rec("N2", (persisted is None) and (not duck_ok),
        f"unissued consent_snapshot_id persisted into append-only log as {persisted!r}; "
        f"duck-typed non-ConsentSnapshot granted={duck_ok}; IngestService deps={list(vars(svc).keys())} "
        f"(consent_reader wired={has_reader})")


# ---- N3: consent_scope annotated FrozenSet but never coerced -> caller keeps an alias and mutates it
def n3():
    audit, _s, gate, _v, _svc = stack()
    live = {ConsentScope.EXTERNAL_MEASUREMENT}               # a MUTABLE set the caller retains
    snap = ConsentSnapshot("cs_alias", "subj_000000", ConsentState.VALID, NOW,
                           consent_scope=live)               # type: ignore[arg-type]
    before = gate.evaluate(snap, ConsentScope.CRM)
    live.add(ConsentScope.CRM)                               # retroactive upgrade, same snapshot id
    after = gate.evaluate(snap, ConsentScope.CRM)
    rec("N3", not (before is False and after is True),
        f"same snapshot id 'cs_alias': CRM before={before} -> after caller mutated the aliased set={after} "
        f"(point-in-time record must be immutable); denial audited earlier={bool(audit.find('CONSENT_SCOPE_NOT_GRANTED'))}")


# ---- N4: captured_at is never compared to event time (stale + post-dated consent both grant)
def n4():
    _a, _s, gate, _v, _svc = stack()
    stale = ConsentSnapshot("cs_2019", "subj_000000", ConsentState.VALID,
                            datetime(2019, 1, 1, tzinfo=timezone.utc), frozenset(ConsentScope))
    future = ConsentSnapshot("cs_2099", "subj_000000", ConsentState.VALID,
                             datetime(2099, 1, 1, tzinfo=timezone.utc), frozenset(ConsentScope))
    rec("N4", not (gate.evaluate(stale, ConsentScope.CRM) and gate.evaluate(future, ConsentScope.CRM)),
        f"captured_at ignored -> 2019 snapshot granted={gate.evaluate(stale, ConsentScope.CRM)}, "
        f"post-dated 2099 snapshot granted={gate.evaluate(future, ConsentScope.CRM)}")


# ---- N6: the GRANT path writes no audit record (only denials are audited)
def n6():
    audit, _s, gate, _v, _svc = stack()
    ok = ConsentSnapshot("cs_ok", "subj_000000", ConsentState.VALID, NOW, frozenset(ConsentScope))
    before = len(audit)
    granted = gate.evaluate(ok, ConsentScope.EXTERNAL_MEASUREMENT)
    rec("N6", (len(audit) - before) > 0,
        f"consent GRANT (result={granted}) wrote {len(audit) - before} audit records "
        f"(denials are audited; a grant leaves no trace)")


# ---- G1: the validator never checks that the row the adapter returned is FOR the requested event_code
def g1():
    audit = AuditLog()
    mismatched = Reg([ACTIVE])
    mismatched._r = {"ADS_REQUESTED": EventRegistryRow(          # row is for a DIFFERENT code
        "ADS_SOMETHING_ELSE", RegistrationState.ACTIVE, owner="core")}
    v = EventValidator(mismatched, audit)
    res = v.validate("ADS_REQUESTED")
    rec("G1", res.decision is not EventDecision.ACCEPT,
        f"registry row.event_code='ADS_SOMETHING_ELSE' returned for requested 'ADS_REQUESTED' -> "
        f"decision={res.decision.value}, result.event_code={res.event_code!r} "
        f"(row identity is never re-checked against the request)")


# ---- G2: log_id is the DDL PRIMARY KEY but the store only enforces idempotency_key
def g2():
    store = WebEventLogStore()
    a = WebEventLog("log_SAME", "ADS_PAGE_VIEW", "p", "s", "web", NOW, "key_A", NOW)
    b = WebEventLog("log_SAME", "ADS_PAGE_VIEW", "p2", "s2", "web", NOW, "key_B", NOW)
    store.append(a); store.append(b)
    ids = [r.log_id for r in store.all()]
    rec("G2", len(set(ids)) == len(ids),
        f"two rows accepted with duplicate log_id={ids} while migrations DDL declares "
        f"log_id TEXT NOT NULL PRIMARY KEY (staged store would break the physical PK)")


def main():
    for fn in (n1, n2, n3, n4, n6, g1, g2):
        try:
            fn()
        except Exception as exc:                              # noqa: BLE001
            rec(fn.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print("=" * 100)
    for aid, verdict, ev in OUT:
        print(f"{aid.ljust(4)} | {verdict.ljust(7)} | {ev}")
    print("=" * 100)
    print(f"TOTAL {len(OUT)} | HELD {sum(1 for o in OUT if o[1] == 'HELD')} | "
          f"FINDINGS {sum(1 for o in OUT if o[1] == 'FINDING')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
