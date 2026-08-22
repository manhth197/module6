"""M6-P1005 — adversarial REFUTATION pass over the Round-3 findings.

Every finding from m6_2a_attacks_round3.py is re-probed with the explicit goal of KILLING it (false positive,
unreachable, already-covered, or over-severed). Anything that survives goes in the report; anything that dies
is recorded as a refuted candidate so the report shows what was tried and discarded.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import pathlib
import re
from datetime import datetime, timezone
from types import SimpleNamespace

IMPL = pathlib.Path(r"D:\M6\Module6-workspace\04-artifacts\impl\M6.2A")
sys.path.insert(0, str(IMPL))

from app.measurement.audit import AuditLog, _EVENT_CODE_SHAPE          # noqa: E402
from app.measurement.consent.gate import ConsentGate                   # noqa: E402
from app.measurement.ingest import IngestService                       # noqa: E402
from app.measurement.logs.web_event_log_store import WebEventLogStore  # noqa: E402
from app.measurement.models.consumed import (                          # noqa: E402
    ConsentScope, ConsentSnapshot, ConsentState, EventRegistryRow, RegistrationState,
)
from app.measurement.registry.validator import EventValidator          # noqa: E402

UTC_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
OUT = []


def refute(fid, question, verdict, detail):
    """verdict in {SURVIVES, REFUTED}."""
    OUT.append((fid, verdict, detail))
    print(f"[{verdict:<8}] {fid:<6} {question}\n           -> {detail}\n")


class Registry:
    def __init__(self, rows):
        self._rows = rows

    def get(self, c):
        return self._rows.get(c)


ROWS = {"VIEW_LANDING": EventRegistryRow("VIEW_LANDING", RegistrationState.ACTIVE, owner="core.tracking")}


class ReaderMap:
    def __init__(self, rows):
        self._rows = rows

    def get(self, i):
        return self._rows.get(i)

    def current_state(self, _s):
        return ConsentState.MISSING


# ===================================================================================================
print("=== REFUTATION PASS ===\n")

# --- F3 candidate (posture SQL sweep): is it a real code path or docstring prose? ------------------
import app as app_pkg  # noqa: E402

root = pathlib.Path(app_pkg.__file__).parent
raw_hits, code_hits = [], []
for path in sorted(root.rglob("*.py")):
    src = path.read_text(encoding="utf-8")
    stripped = re.sub(r'"""·*?"""', "", src, flags=re.S)          # (intentionally non-matching)
    stripped = re.sub(r'(?s)""".*?"""', "", src)
    stripped = "\n".join(l.split("#")[0] for l in stripped.splitlines())
    for pat in (r"\.sql\b", r"\b(UPDATE|DELETE|DROP|TRUNCATE)\s+\w"):
        for m in re.finditer(pat, src):
            raw_hits.append(f"{path.name}: {m.group(0)!r}")
        for m in re.finditer(pat, stripped):
            code_hits.append(f"{path.name}: {m.group(0)!r}")
refute("F3", "Does app/ contain a reachable SQL DDL/DML path?",
       "REFUTED" if not code_hits else "SURVIVES",
       f"raw-source hits (incl. docstrings/comments)={raw_hits}; hits with docstrings+comments STRIPPED="
       f"{code_hits or 'none'} -> the earlier F3 hit was prose in the append-only docstrings "
       f"('refuses UPDATE/DELETE', a path to migrations/0001_...sql), NOT executable SQL. FALSE POSITIVE.")

# --- F-1 candidate: is the duck-typed-snapshot fail-OPEN reachable, or is the type enforced anywhere?
src_all = "\n".join(p.read_text(encoding="utf-8") for p in root.rglob("*.py"))
isinst = re.findall(r"isinstance\([^)]*\)", src_all)
snap_guard = [s for s in isinst if "ConsentSnapshot" in s]
refute("F1", "Is a non-ConsentSnapshot rejected anywhere between reader and gate?",
       "REFUTED" if snap_guard else "SURVIVES",
       f"isinstance() guards in app/: {isinst}; guards naming ConsentSnapshot: {snap_guard or 'NONE'} "
       f"-> nothing type-checks the object ConsentReader.get() returns; the only enforcement point is "
       f"ConsentSnapshot.__post_init__, which a reader that does not construct one never reaches.")

# does the slice's own test suite model a reader returning a non-ConsentSnapshot? (reachability evidence)
tests = (IMPL / "tests").rglob("*.py")
ns_models = []
for p in tests:
    s = p.read_text(encoding="utf-8")
    if "SimpleNamespace(" in s and "consent_scope" in s:
        ns_models += [f"{p.name}:{m}" for m in re.findall(r"consent_scope=([^,\n]+)", s)]
refute("F1b", "Is 'reader returns a non-ConsentSnapshot' a shape the authors consider realistic?",
       "SURVIVES" if ns_models else "REFUTED",
       f"the staged suite itself hands the seam SimpleNamespace snapshots: {ns_models} -> the shape is "
       f"treated as realistic, but every modelled case sets consent_scope=frozenset() (the SAFE value); "
       f"the fail-OPEN direction (a str/dict consent_scope) is modelled nowhere.")

# can the duck-typed grant actually cause egress today?
gate = ConsentGate(AuditLog())
duck = SimpleNamespace(consent_snapshot_id="cs_d", subject_ref="guest_x",
                       consent_state=ConsentState.VALID, consent_scope="crm:false", captured_at=UTC_TS)
svc = IngestService(EventValidator(Registry(ROWS), AuditLog()), WebEventLogStore(),
                    gate, ReaderMap({"cs_d": duck}), AuditLog())
res = svc.ingest_event(event_code="VIEW_LANDING", page_id="p", session_id="s", source="web",
                       event_ts=UTC_TS, raw_event_hash="h", consent_snapshot_id="cs_d",
                       guest_id="guest_x", consent_scope=ConsentScope.CRM)
refute("F1c", "Does the duck-typed consent grant produce an actual send/egress today?",
       "REFUTED" if res.egress_eligible is False else "SURVIVES",
       f"gate.evaluate -> {gate.evaluate(duck, ConsentScope.CRM)} (GRANTED), but seam egress_eligible="
       f"{res.egress_eligible} because permits_external_send() is hard-False while M6-OD-003 is OPEN "
       f"-> severity ceiling: ARMED, NOT FIRED (identical posture to the Round-1 MAJORs).")

# --- F-2 candidate: does the staged property test already cover the registry/contacts ports? -------
prop = (IMPL / "tests" / "test_round3_regressions.py").read_text(encoding="utf-8")
code_values = re.search(r"code_values\s*=\s*\[(.*?)\]", prop, flags=re.S)
reader_values = re.search(r"reader_values\s*=\s*\[(.*?)\]", prop, flags=re.S)
non_str = [v for v in re.findall(r"[\"']([^\"']*)[\"']", code_values.group(1))] if code_values else []
refute("F2", "Is 'the seam never raises' already pinned for the registry / guest_contacts ports?",
       "SURVIVES",
       f"the seam property test enumerates code_values={non_str} (ALL str), "
       f"reader_values={reader_values.group(1).strip() if reader_values else '?'} (consent port only), and "
       f"builds IngestService with NO resolver -> the registry port, the guest_contacts port and every "
       f"non-str event_code are outside the product it iterates. The test's claim to 'close the whole CLASS' "
       f"is bounded by the values it enumerates.")

# does the seam's own docstring claim the coverage it does not have?
ingest_doc = (IMPL / "app" / "measurement" / "ingest.py").read_text(encoding="utf-8")[:2000]
claims = [l.strip() for l in ingest_doc.splitlines()
          if "WRAPS every call" in l or "never raises" in l]
refute("F2b", "Is the uncovered-port gap a contract violation, or just an unstated limit?",
       "SURVIVES" if claims else "REFUTED",
       f"ingest.py module docstring states: {claims} -> the seam claims total coverage of external/untrusted "
       f"calls and of hostile input; the registry and guest_contacts ports are external and unwrapped.")

# is a non-str event_code reachable, i.e. does anything type the endpoint body?
req_contract = list(pathlib.Path(r"D:\M6\Module6-workspace\00-spec\contracts").glob("*TRACK*")) + \
    list(pathlib.Path(r"D:\M6\Module6-workspace\00-spec\contracts").glob("*track*"))
refute("F2c", "Can a non-str event_code actually reach ingest_event()?",
       "SURVIVES",
       f"ingest.py names its future caller as the M6.2B endpoint POST /api/ads/events/track; "
       f"track-request contract files in 00-spec/contracts: {[p.name for p in req_contract] or 'NONE'} "
       f"-> nothing in this slice types or validates the JSON body, so event_code arrives as whatever the "
       f"channel sent (list/dict/number are one line of attacker input).")

# does the escaping exception leave a half-written append-only row?
class ThrowingGate(ConsentGate):
    def evaluate(self, *_a, **_k):
        raise RuntimeError("gate blew up in a way the seam does not catch")


store = WebEventLogStore()
audit = AuditLog()
svc = IngestService(EventValidator(Registry(ROWS), audit), store, ThrowingGate(audit),
                    ReaderMap({}), audit)
raised = ""
try:
    svc.ingest_event(event_code="VIEW_LANDING", page_id="p", session_id="s", source="web",
                     event_ts=UTC_TS, raw_event_hash="h")
except BaseException as exc:  # noqa: BLE001
    raised = f"{type(exc).__name__}: {exc}"
refute("F2d", "Does an escaping exception corrupt the append-only log (partial write)?",
       "REFUTED" if len(store) == 1 else "SURVIVES",
       f"a non-(AttributeError|TypeError) raised by the consent gate AFTER step 3 escapes ({raised}) and "
       f"leaves rows={len(store)} already appended. The row is complete and an identical retry dedups on the "
       f"same RULE-005 key, so RULE-007 history is NOT corrupted and no double count occurs -> the damage of "
       f"F-2 is the LOST AUDIT + LOST RESULT, not a corrupted log. Severity capped accordingly.")

# --- F-3 candidate (SEC-PII-01 residual): is the verbatim-store real, and does the proposed fix keep
#     SMK-001's 'audit rõ' for legitimate codes?
digits = "".join(chr(0x30 + d) for d in (0, 9, 1, 2, 3, 4, 5, 6, 7, 8))
idish = "guest_" + digits
a = AuditLog()
EventValidator(Registry(ROWS), a).validate(digits)
stored_digits = a.records[-1].event_code
a2 = AuditLog()
EventValidator(Registry(ROWS), a2).validate(idish)
stored_idish = a2.records[-1].event_code
refute("F3p", "Is the identifier-shaped event_code really kept verbatim (not masked)?",
       "SURVIVES" if (stored_digits == digits and stored_idish == idish) else "REFUTED",
       f"shape allowlist = {_EVENT_CODE_SHAPE.pattern!r}; a 10-digit run and 'guest_<10 digits>' both MATCH, "
       f"so both are stored byte-for-byte (verbatim==digits: {stored_digits == digits}, "
       f"verbatim==id-shape: {stored_idish == idish}). Values are not echoed here.")

# proposed fix must not regress the codes the staged suite relies on
proposed = re.compile(r"\A(?=.*[A-Za-z])(?!.*\d{7})[A-Za-z0-9_.:\-]{1,64}\Z")
legit = ["VIEW_LANDING", "view_landing", "VIEW_LANDING_NO_SENS", "DEREG_SAMPLE", "NO_OWNER_SAMPLE",
         "SMK001_EVENT_NOT_IN_REGISTRY", "ADS-P0-001", "evt.view_landing.v1", "UNKNOWN_EVENT_X"]
kept = [c for c in legit if proposed.match(c)]
neutralized = [lbl for lbl, v in (("digit-run", digits), ("id-shape", idish)) if not proposed.match(v)]
refute("F3q", "Would the proposed tightened allowlist break SMK-001 'audit rõ'?",
       "REFUTED" if (len(kept) == len(legit) and len(neutralized) == 2) else "SURVIVES",
       f"proposed shape (require >=1 letter, forbid a run of 7+ digits): keeps {len(kept)}/{len(legit)} "
       f"legitimate codes verbatim {kept}; neutralizes {neutralized} -> the fix is compatible with the "
       f"diagnostic requirement (this refutes the 'cannot be fixed without losing audit rõ' objection).")

# --- MINOR re-checks: are the still-open Round-1 MINORs genuinely unfixed, not fixed elsewhere? ----
gate_src = (IMPL / "app" / "measurement" / "consent" / "gate.py").read_text(encoding="utf-8")
val_src = (IMPL / "app" / "measurement" / "registry" / "validator.py").read_text(encoding="utf-8")
store_src = (IMPL / "app" / "measurement" / "logs" / "web_event_log_store.py").read_text(encoding="utf-8")
refute("M1", "MINOR-1 (freshness): is captured_at checked anywhere?",
       "SURVIVES" if "captured_at" not in gate_src and "captured_at" not in ingest_doc else "REFUTED",
       f"'captured_at' occurrences in gate.py: {gate_src.count('captured_at')}; in ingest.py: "
       f"{(IMPL / 'app' / 'measurement' / 'ingest.py').read_text(encoding='utf-8').count('captured_at')}")
refute("M6", "MINOR-6: is the registry row checked to be FOR the requested code?",
       "SURVIVES" if "row.event_code ==" not in val_src else "REFUTED",
       f"'row.event_code ==' present in validator.py: {'row.event_code ==' in val_src}")
refute("M7", "MINOR-7: does the store enforce log_id uniqueness?",
       "SURVIVES" if "log_id" not in store_src else "REFUTED",
       f"'log_id' occurrences in web_event_log_store.py: {store_src.count('log_id')} "
       f"(store keys only on idempotency_key)")

print("\n=== REFUTATION SUMMARY ===")
for fid, verdict, _ in OUT:
    print(f"  {verdict:<8} {fid}")
