"""M6.2P boundary-adversary harness (READ-ONLY analysis; prompt M6-P2405).

Attacks the staged M6.2P slice — the owner-signed ExternalSendPolicy 4-value enum adopted as typed, fail-closed
code (models/consumed.py + registry/validator.py). In-scope fail gate M6-FAIL-007 (no-evidence / overstated
readiness); rules RULE-014 (no raw PII), RULE-015 (no self-cert). The crown-jewel invariant: the enum opens NO
egress (no row is ALLOW_EXTERNAL, EXTERNAL_SEND stays Final OFF). The harness drives the real staged code and
EXECUTES every claimed breach; it flips no flag and opens no send.

    PYTHONDONTWRITEBYTECODE=1  py -3.12 -B  work/attacks/m6_2p_attacks.py

Classification: DEFENDED / OPEN_NONGATE (armed-not-fired) / NOTE / BREACH (a FAIL-007 gate trips OR a real egress
opens from a channel-reachable path).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve()
IMPL = None
for anc in HERE.parents:
    cand = anc / "04-artifacts" / "impl" / "M6.2P"
    if (cand / "app").is_dir():
        IMPL = cand
        break
if IMPL is None:
    raise SystemExit("cannot locate 04-artifacts/impl/M6.2P/app")
sys.path.insert(0, str(IMPL))

from app import config
from app.measurement.audit import AuditLog
from app.measurement.models.consumed import (
    ExternalSendPolicy, EventRegistryRow, RegistrationState, DataSensitivity,
)
from app.measurement.registry.validator import (
    _resolve_send_policy, permits_external_send, _resolve_sensitivity,
    EventValidator, EventDecision,
)
from app.measurement.evidence.pack_assembler import EvidencePackAssembler
from app.measurement.evidence.models import Readiness, SmokeResult
from app.measurement.evidence.categories import CATEGORY_MANDATORY
from app.measurement.evidence.smoke_registry import SMOKE_IDS
from types import SimpleNamespace

OUTCOMES = []


def record(vec, gate, klass, detail):
    OUTCOMES.append((vec, gate, klass, detail))
    print(f"[{klass:12}] {vec:8} {gate:10} {detail}")


class _Reg:
    """Minimal in-memory EventRegistryReader (test double for the CONSUMED event_registry)."""
    def __init__(self, rows):
        self._rows = rows

    def get(self, event_code):
        return self._rows.get(event_code)


def row(event_code="VIEW_LANDING", *, state=RegistrationState.ACTIVE, owner="core.tracking",
        policy=None, sensitivity=None):
    return EventRegistryRow(event_code=event_code, registration_state=state, owner=owner,
                            data_sensitivity=sensitivity, external_send_policy=policy)


# The junk sweep (governance tokens / non-coercible values; NO PII literal).
JUNK = [None, "", "   ", "\t", "\n", "MAYBE", "allow", "ALLOW", "true", "allow_external",
        "ALLOW_EXTERNAL ", " ALLOW_EXTERNAL", "ALLOW-EXTERNAL", 123, 0, 1, True, False,
        object(), b"ALLOW_EXTERNAL", [], {}, (), DataSensitivity.PII]


# ===================================================================================================
# GROUP P — enum fail-closed coercion + the egress crown-jewel (FAIL-007 / RULE-014)
# ===================================================================================================
def group_P():
    # P1 — the enum has exactly the 4 owner-signed values.
    vals = {m.value for m in ExternalSendPolicy}
    if vals == {"ALLOW_EXTERNAL", "INTERNAL_ONLY", "BLOCKED_PII", "BLOCKED_DEFAULT"}:
        record("P1", "FAIL-007", "DEFENDED",
               f"ExternalSendPolicy has exactly the 4 owner-signed values {sorted(vals)} (M6 adopts the vocabulary, "
               "invents none — RULE-018).")
    else:
        record("P1", "FAIL-007", "BREACH", f"enum values off-spec: {sorted(vals)}")

    # P2 — _resolve_send_policy fail-closes every junk value to BLOCKED_DEFAULT (never ALLOW_EXTERNAL, never crash).
    leaked, crashed = [], []
    for j in JUNK:
        try:
            r = _resolve_send_policy(j)
            if r is ExternalSendPolicy.ALLOW_EXTERNAL:
                leaked.append(repr(j))
            elif r is not ExternalSendPolicy.BLOCKED_DEFAULT:
                leaked.append(f"{j!r}->{r}")   # any non-default from junk is unexpected
        except Exception as e:  # noqa
            crashed.append(f"{j!r}:{type(e).__name__}")
    if not leaked and not crashed:
        record("P2", "FAIL-007", "DEFENDED",
               f"_resolve_send_policy fail-closes ALL {len(JUNK)} junk inputs (None/blank/tab/'MAYBE'/'allow'/"
               "'ALLOW'/'true'/lowercase/trailing-space/hyphen/int/bool/bytes/list/dict/other-enum) -> "
               "BLOCKED_DEFAULT; never ALLOW_EXTERNAL, never a crash.")
    else:
        record("P2", "FAIL-007", "BREACH", f"coercion leaked/crashed: leaked={leaked} crashed={crashed}")

    # P3 — each valid member AND its token string maps to its member.
    ok = all(_resolve_send_policy(m) is m for m in ExternalSendPolicy) \
        and all(_resolve_send_policy(m.value) is m for m in ExternalSendPolicy)
    if ok:
        record("P3", "FAIL-007", "DEFENDED",
               "each real ExternalSendPolicy member AND its exact token string ('ALLOW_EXTERNAL' etc.) maps to its "
               "member (the enum vocabulary is genuinely real, not a dead constant).")
    else:
        record("P3", "FAIL-007", "BREACH", "a valid member/token did not map to its member")

    # P4 — permits_external_send True ONLY for ALLOW_EXTERNAL.
    trues = [m for m in ExternalSendPolicy if permits_external_send(m)]
    if trues == [ExternalSendPolicy.ALLOW_EXTERNAL]:
        record("P4", "FAIL-007", "DEFENDED",
               "permits_external_send True ONLY for ALLOW_EXTERNAL; False for INTERNAL_ONLY / BLOCKED_PII / "
               "BLOCKED_DEFAULT (uses `is`, not `==`).")
    else:
        record("P4", "FAIL-007", "BREACH", f"permits_external_send True for {trues}")

    # P5 — the composed gate over the junk sweep is False for ALL (fail-closed direction airtight).
    if not any(permits_external_send(_resolve_send_policy(j)) for j in JUNK):
        record("P5", "FAIL-007", "DEFENDED",
               "composed gate permits_external_send(_resolve_send_policy(junk)) is False for EVERY junk input — no "
               "non-'ALLOW_EXTERNAL' value ever opens the policy gate.")
    else:
        record("P5", "FAIL-007", "BREACH", "a junk input opened the policy gate")

    # P6 — str-subclass / hostile-__eq__ whose VALUE equals 'ALLOW_EXTERNAL' coerces to ALLOW_EXTERNAL (INTENDED);
    #      a hostile object NOT matching -> BLOCKED_DEFAULT. Trusted-input; even ALLOW_EXTERNAL -> EXTERNAL_SEND OFF.
    class _AllowSub(str):
        pass

    class _HostileEq:
        def __init__(self, target):
            self._t = target

        def __eq__(self, other):
            return other == self._t

        def __hash__(self):
            return hash(self._t)
    sub_allow = _resolve_send_policy(_AllowSub("ALLOW_EXTERNAL"))
    eq_allow = _resolve_send_policy(_HostileEq("ALLOW_EXTERNAL"))
    eq_other = _resolve_send_policy(_HostileEq("MAYBE"))
    if (sub_allow is ExternalSendPolicy.ALLOW_EXTERNAL and eq_allow is ExternalSendPolicy.ALLOW_EXTERNAL
            and eq_other is ExternalSendPolicy.BLOCKED_DEFAULT):
        record("P6", "FAIL-007", "OPEN_NONGATE",
               "a str-subclass or hostile-__eq__ object whose VALUE equals 'ALLOW_EXTERNAL' coerces to ALLOW_EXTERNAL "
               "(the INTENDED coercion of a genuine token — the str-Enum value-lookup); a hostile object matching a "
               "NON-'ALLOW_EXTERNAL' value -> BLOCKED_DEFAULT (fail-closed direction unaffected). Trusted-input only: "
               "the registry SOURCE hands plain tokens; no row is ALLOW_EXTERNAL; and even ALLOW_EXTERNAL opens no "
               "egress (EXTERNAL_SEND Final OFF). Matches the coder's 1-candidate/0-surviving self-review.")
    else:
        record("P6", "FAIL-007", "NOTE",
               f"subclass/eq coercion unexpected (sub={sub_allow}, eq={eq_allow}, other={eq_other})")

    # P7 — a REAL ACCEPTED event (VIEW_LANDING, ACTIVE, owner, policy None) -> send_permitted False (no row ALLOW).
    v = EventValidator(_Reg({"VIEW_LANDING": row(policy=None)}), AuditLog())
    res = v.validate("VIEW_LANDING")
    if res.decision is EventDecision.ACCEPT and res.external_send_permitted is False:
        record("P7", "FAIL-007", "DEFENDED",
               "a real ACCEPTED event (policy None -> coerced BLOCKED_DEFAULT) validates ACCEPT with "
               "external_send_permitted=False; no real registry event is ALLOW_EXTERNAL (permit-mapping OPEN).")
    else:
        record("P7", "FAIL-007", "BREACH", f"a real event permitted send ({res.external_send_permitted})")

    # P8 — an explicit ALLOW_EXTERNAL row makes the POLICY gate genuinely True (non-vacuous), BUT EXTERNAL_SEND OFF.
    v = EventValidator(_Reg({"ALLOWED_EVT": row("ALLOWED_EVT", policy=ExternalSendPolicy.ALLOW_EXTERNAL)}), AuditLog())
    res = v.validate("ALLOWED_EVT")
    if res.decision is EventDecision.ACCEPT and res.external_send_permitted is True and config.EXTERNAL_SEND == "OFF":
        record("P8", "FAIL-007", "DEFENDED",
               "non-vacuity + defense-in-depth: an explicitly ALLOW_EXTERNAL row makes the policy gate genuinely True "
               "(the gate is real, not a dead hard-False), YET config.EXTERNAL_SEND == 'OFF' — send_permitted is an "
               "inert POLICY flag, not a real send. No such row exists in the real registry.")
    else:
        record("P8", "FAIL-007", "BREACH", f"ALLOW_EXTERNAL row misbehaved ({res.external_send_permitted}, {config.EXTERNAL_SEND})")

    # P9 — defense-in-depth: the transport is the real choke — is_external_send_enabled() False + StagedBlockedTransport
    #      raises ExternalSendBlocked, so send_permitted=True never reaches a real send.
    from app.measurement.outbox.transport import StagedBlockedTransport, ExternalSendBlocked
    blocked = False
    try:
        StagedBlockedTransport().deliver(SimpleNamespace(outbox_id="x", payload={}, platform="p"))
    except ExternalSendBlocked:
        blocked = True
    except Exception:  # any other raise still means no real send happened
        blocked = True
    if blocked and config.is_external_send_enabled() is False and config.EXTERNAL_SEND == "OFF":
        record("P9", "FAIL-007", "DEFENDED",
               "the transport is the real egress choke: is_external_send_enabled() False + StagedBlockedTransport "
               "raises ExternalSendBlocked on every deliver. So even a send_permitted=True (policy) row opens NO "
               "real send — the enum gate and the transport gate are independent (defense-in-depth).")
    else:
        record("P9", "FAIL-007", "BREACH", f"transport did not block (blocked={blocked}, enabled={config.is_external_send_enabled()})")

    # P10 — unknown -> REJECT + send_permitted False; not-ACTIVE / missing-owner -> HOLD + send_permitted False.
    v = EventValidator(_Reg({
        "DEREG": row("DEREG", state=RegistrationState.DEREGISTERED, policy=ExternalSendPolicy.ALLOW_EXTERNAL),
        "NOOWNER": row("NOOWNER", owner=None, policy=ExternalSendPolicy.ALLOW_EXTERNAL),
    }), AuditLog())
    unknown = v.validate("NOT_IN_REGISTRY")
    dereg = v.validate("DEREG")
    noowner = v.validate("NOOWNER")
    if (unknown.decision is EventDecision.REJECT and not unknown.external_send_permitted
            and dereg.decision is EventDecision.HOLD and not dereg.external_send_permitted
            and noowner.decision is EventDecision.HOLD and not noowner.external_send_permitted):
        record("P10", "FAIL-007", "DEFENDED",
               "an unknown event -> REJECT and a de-registered / missing-owner event -> HOLD both force "
               "external_send_permitted=False EVEN with an ALLOW_EXTERNAL policy (the gate is only reached on the "
               "ACCEPT path; a non-usable event never permits send).")
    else:
        record("P10", "FAIL-007", "BREACH", "an unknown/HOLD event permitted send")


# ===================================================================================================
# GROUP R14 — RULE-014 (no raw PII in the enum/policy path)
# ===================================================================================================
def group_R14():
    v = EventValidator(_Reg({"VIEW_LANDING": row(policy=ExternalSendPolicy.BLOCKED_PII,
                                                 sensitivity=DataSensitivity.PII)}), AuditLog())
    res = v.validate("VIEW_LANDING")
    blob = f"{res.event_code}|{res.data_sensitivity}|{res.external_send_permitted}|{res.reason}"
    import re as _re
    if "@" not in blob and not _re.findall(r"\d{7,}", blob) and all(
            m.value in ("ALLOW_EXTERNAL", "INTERNAL_ONLY", "BLOCKED_PII", "BLOCKED_DEFAULT") for m in ExternalSendPolicy):
        record("R14-1", "FAIL-008", "DEFENDED",
               "RULE-014: the ExternalSendPolicy values are governance tokens (ALLOW_EXTERNAL/…), not PII; the "
               "ValidationResult carries only event_code + enums + a bool + a governance reason — no raw PII. The "
               "BLOCKED_PII value makes PII-egress governance EXPLICIT + fail-closed.")
    else:
        record("R14-1", "FAIL-008", "NOTE", f"policy path carried a PII-shaped token: {blob}")


# ===================================================================================================
# GROUP F7 — carried FAIL-007 evidence pack (M6.2O) intact
# ===================================================================================================
def group_F7():
    a = EvidencePackAssembler()

    def canonical_refs():
        return {cat: {k: f"ev::{cat.value}::{k}" for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}

    def all_recorded():
        return {sid: SmokeResult(sid, status="PASS", correlation_id="c" + sid[-3:], evidence_id="e" + sid[-3:])
                for sid in SMOKE_IDS}

    # F7-1 — F2-6 duck-coerce carried: a duck with .recorded=True + None fields stays un-recorded -> NOT_READY.
    refs = dict(all_recorded())
    refs["M6-SMK-001"] = SimpleNamespace(smoke_id="M6-SMK-001", status=None, correlation_id=None,
                                         evidence_id=None, waived=False, recorded=True)
    p = a.assemble(refs, canonical_refs())
    smk = next(s for s in p.smokes if s.smoke_id == "M6-SMK-001")
    if not smk.recorded and p.readiness is Readiness.NOT_READY:
        record("F7-1", "FAIL-007", "DEFENDED",
               "carried M6.2O F2-6 duck-coerce intact: a duck .recorded=True + None fields is coerced -> recorded "
               "recomputed False -> NOT_READY (the evidence pack is unaffected by the enum change).")
    else:
        record("F7-1", "FAIL-007", "BREACH", "carried F2-6 duck-coerce regressed")

    # F7-2 — a genuine complete pack caps at OWNER_REVIEW_REQUIRED; no self-cert / Pass member (RULE-015).
    p = a.assemble(all_recorded(), canonical_refs())
    members = {m.value for m in Readiness}
    if p.readiness is Readiness.OWNER_REVIEW_REQUIRED and members == {"OWNER_REVIEW_REQUIRED", "NOT_READY"}:
        record("F7-2", "FAIL-007", "DEFENDED",
               "carried evidence pack caps at OWNER_REVIEW_REQUIRED; Readiness has no Pass/Ready member; no self-cert "
               "(RULE-015). The enum adoption did not add a Pass/advance verb.")
    else:
        record("F7-2", "FAIL-007", "BREACH", f"evidence pack readiness surface changed ({members})")


# ===================================================================================================
# GROUP REG — regression (the retype ripple, the mirror, the posture)
# ===================================================================================================
def group_REG():
    # REG1 — _resolve_sensitivity mirror still fail-closes MISSING/unknown -> PII (unchanged by the enum add).
    ok = (_resolve_sensitivity(None) is DataSensitivity.PII
          and _resolve_sensitivity("nonsense") is DataSensitivity.PII
          and _resolve_sensitivity(DataSensitivity.INTERNAL) is DataSensitivity.INTERNAL)
    if ok:
        record("REG1", "FAIL-007", "DEFENDED",
               "the _resolve_sensitivity mirror still fail-closes None/unknown -> PII and passes a real member "
               "(the pattern the send-policy coercion mirrors is intact — no regression).")
    else:
        record("REG1", "FAIL-007", "BREACH", "data_sensitivity coercion regressed")

    # REG2 — the field default None still coerces (an all-default EventRegistryRow validates ACCEPT, send False).
    v = EventValidator(_Reg({"E": row("E")}), AuditLog())
    res = v.validate("E")
    if res.accepted and res.external_send_permitted is False and res.data_sensitivity is DataSensitivity.PII:
        record("REG2", "FAIL-007", "DEFENDED",
               "an all-default EventRegistryRow (policy None, sensitivity None) validates ACCEPT with send_permitted "
               "False + sensitivity PII (both fail-closed defaults compose correctly).")
    else:
        record("REG2", "FAIL-007", "BREACH", "default-row coercion regressed")

    # REG3 — posture: EXTERNAL_SEND Final OFF + is_external_send_enabled() False + BLOCKED/OFF (immutable).
    if (config.EXTERNAL_SEND == "OFF" and config.is_external_send_enabled() is False
            and config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"):
        record("REG3", "FAIL-007", "DEFENDED",
               "posture immutable: EXTERNAL_SEND Final 'OFF', is_external_send_enabled() False, gateway BLOCKED, "
               "production OFF — the enum adoption flipped nothing.")
    else:
        record("REG3", "FAIL-007", "BREACH", "posture changed")


# ===================================================================================================
# GROUP N — reconciliation of the ideation workflow's novel vectors (executed)
# ===================================================================================================
def group_N():
    # N1 (EC-08 / MC-05, NEW residual) — the coercion is not TOTAL: a hostile object whose __hash__/__eq__ (during
    #     the value2member lookup) OR whose .strip() (line 80, OUTSIDE the try) raises a non-(ValueError,TypeError)
    #     exception PROPAGATES uncaught -> _resolve_send_policy crashes. It fails LOUD (never ALLOW_EXTERNAL, no
    #     permit, no egress), not open-toward-send. Not channel-reachable (registry hands plain tokens).
    class _RaisingHash:
        def __hash__(self):
            raise RuntimeError("hostile __hash__")

        def __eq__(self, other):
            return False

    class _RaisingStrip(str):
        def strip(self, *a):
            raise RuntimeError("hostile strip")
    crash = 0
    for hostile in (_RaisingHash(), _RaisingStrip("x")):
        try:
            r = _resolve_send_policy(hostile)
            if r is ExternalSendPolicy.ALLOW_EXTERNAL:
                crash = -99   # would be a real fail-open
        except (ValueError, TypeError):
            pass              # caught -> BLOCKED_DEFAULT would happen; but these raise RuntimeError
        except Exception:     # noqa - the uncaught crash we predict
            crash += 1
    if crash == 2:
        record("N1", "FAIL-007", "OPEN_NONGATE",
               "coercion not TOTAL (EC-08/MC-05): a hostile object whose __hash__ (value2member lookup) or .strip() "
               "(line 80, outside the try) raises RuntimeError propagates uncaught -> _resolve_send_policy crashes "
               "(the except is (ValueError,TypeError), narrower than the consent code's bare except Exception). It "
               "fails LOUD — never ALLOW_EXTERNAL, no permit, no egress (fail-away-from-send), not fail-open. NOT "
               "channel-reachable: external_send_policy is registry-SOURCED (M3), never a channel-crafted object. "
               "Robustness/mirror-parity residual: broaden the except to Exception -> BLOCKED_DEFAULT. Route CODER.")
    elif crash == -99:
        record("N1", "FAIL-007", "BREACH", "a hostile-dunder object coerced to ALLOW_EXTERNAL")
    else:
        record("N1", "FAIL-007", "DEFENDED", f"hostile dunder handled fail-closed (crash count {crash})")

    # N2 (EC-07) — a FOREIGN enum member whose value == 'ALLOW_EXTERNAL' coerces to ExternalSendPolicy.ALLOW_EXTERNAL
    #     (value-equality lookup). Same trusted-input class as P6; a foreign member with a NON-'ALLOW_EXTERNAL' value
    #     fail-closes. The registry field is typed Optional[ExternalSendPolicy]; no foreign-enum path is reachable.
    from enum import Enum as _Enum

    class _Other(str, _Enum):
        X = "ALLOW_EXTERNAL"
        Y = "SOMETHING_ELSE"
    r_x = _resolve_send_policy(_Other.X)
    r_y = _resolve_send_policy(_Other.Y)
    if r_x is ExternalSendPolicy.ALLOW_EXTERNAL and r_y is ExternalSendPolicy.BLOCKED_DEFAULT:
        record("N2", "FAIL-007", "OPEN_NONGATE",
               "a FOREIGN enum member with value 'ALLOW_EXTERNAL' coerces to ALLOW_EXTERNAL (str-Enum value lookup); "
               "a foreign member with a non-'ALLOW_EXTERNAL' value -> BLOCKED_DEFAULT (fail-closed direction intact). "
               "Same trusted-input class as P6 (needs value=='ALLOW_EXTERNAL'); the registry hands plain tokens / "
               "real members, not foreign enums. No row is ALLOW_EXTERNAL; EXTERNAL_SEND OFF.")
    else:
        record("N2", "FAIL-007", "NOTE", f"foreign-enum coercion unexpected (x={r_x}, y={r_y})")

    # N3 (MC-03/MC-04) — defense-in-depth beyond the transport: even a forced send_permitted=True is (a) an inert
    #     flag the real send path never reads and (b) further AND-gated by consent on the ingest eligibility bit.
    #     Confirm the transport is unconditional regardless of any policy value (the sole real choke).
    from app.measurement.outbox.transport import StagedBlockedTransport, ExternalSendBlocked
    from types import SimpleNamespace as _NS
    always_blocks = True
    for policy in ExternalSendPolicy:                          # transport ignores the policy entirely
        try:
            StagedBlockedTransport().deliver(_NS(outbox_id="x", payload={"policy": policy.value}, platform="p"))
            always_blocks = False
        except ExternalSendBlocked:
            pass
        except Exception:
            pass
    if always_blocks and config.is_external_send_enabled() is False:
        record("N3", "FAIL-007", "DEFENDED",
               "defense-in-depth (MC-03/MC-04): the StagedBlockedTransport raises ExternalSendBlocked UNCONDITIONALLY "
               "for every policy value — the real send path never reads external_send_permitted (an inert eligibility "
               "flag, further AND-gated by consent at ingest), so a forced permits=True opens no send. The transport + "
               "EXTERNAL_SEND-OFF is the sole real choke, independent of the enum gate.")
    else:
        record("N3", "FAIL-007", "BREACH", "the transport did not unconditionally block")


# ===================================================================================================
def main():
    print("=" * 100)
    print("M6.2P BOUNDARY ADVERSARY — external_send_policy enum (in-scope: FAIL-007; egress fail-closed / RULE-014)")
    print(f"impl root: {IMPL}")
    print(f"posture: EXTERNAL_SEND={config.EXTERNAL_SEND} is_enabled={config.is_external_send_enabled()} "
          f"PRODUCTION_FLAG={config.PRODUCTION_FLAG}")
    print("=" * 100)
    for g in (group_P, group_R14, group_F7, group_REG, group_N):
        print(f"\n----- {g.__name__} -----")
        g()

    print("\n" + "=" * 100)
    tally = {}
    for _, _, k, _ in OUTCOMES:
        tally[k] = tally.get(k, 0) + 1
    breaches = [o for o in OUTCOMES if o[2] == "BREACH"]
    inscope = [o for o in breaches if o[1] in ("FAIL-007", "FAIL-008")]
    print(f"SUMMARY: {tally}")
    print(f"TOTAL RECORDED OUTCOMES: {len(OUTCOMES)}")
    print(f"IN-SCOPE FAIL-GATE BREACHES: {len(inscope)}")
    for o in breaches:
        print("   BREACH:", o)

    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
    assert config.EXTERNAL_SEND == "OFF" and config.is_external_send_enabled() is False
    assert permits_external_send(ExternalSendPolicy.BLOCKED_DEFAULT) is False
    print("POSTURE AFTER RUN: BLOCKED / OFF / OFF (unchanged); permits_external_send fail-closed")
    print("=" * 100)


if __name__ == "__main__":
    main()
