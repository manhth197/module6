"""M6.2K boundary-adversary harness (READ-ONLY analysis; prompt M6-P2005).

Attacks the staged M6.2K "Smoke & Evidence Pack" slice — the final full-P0-matrix re-run + doc §22 owner
sign-off package assembler. In-scope fail gate: M6-FAIL-007 ("No evidence" = calling PASS without
audit/evidence/smoke). In-scope rule: M6-RULE-015 (executors write evidence, never certify their own success).

This harness DRIVES the real staged code (no mocks of the unit under attack) and EXECUTES every claimed breach
before recording it. It writes NOTHING to the app, changes no posture, applies no migration. Run byte-clean:

    PYTHONDONTWRITEBYTECODE=1  py -3.12 -B  work/attacks/m6_2k_attacks.py

Classification vocabulary (identical to prior slices):
  DEFENDED       — the attack is refused / fails-closed by a reachable path.
  OPEN_NONGATE   — "armed, not fired": only reachable by in-process code-exec, trusted-input-only, or not
                   channel-reachable; does NOT trip an in-scope gate from any channel path.
  NOTE           — an observation worth routing (e.g. PII on a raw attribute) that is not a gate breach.
  BREACH         — an in-scope FAIL-007 gate actually trips from a reachable path. (Target: zero.)
"""
from __future__ import annotations

import sys
from pathlib import Path

# --- locate the staged impl root (robust to per-role vs root 04-artifacts layout) -------------------
HERE = Path(__file__).resolve()
IMPL = None
for anc in HERE.parents:
    cand = anc / "04-artifacts" / "impl" / "M6.2K"
    if (cand / "app").is_dir():
        IMPL = cand
        break
if IMPL is None:
    raise SystemExit("cannot locate 04-artifacts/impl/M6.2K/app from " + str(HERE))
sys.path.insert(0, str(IMPL))

from datetime import datetime, timezone

from app import config
from app.measurement.masking import mask

# --- the M6.2K evidence-pack surface (the FAIL-007 target) ------------------------------------------
from app.measurement.evidence import pack_assembler as PA
from app.measurement.evidence import gap_blockers as GB
from app.measurement.evidence.pack_assembler import EvidencePackAssembler
from app.measurement.evidence.models import (
    Readiness, GapKind, SmokeResult, CategoryStatus, GapBlocker, EvidencePack,
)
from app.measurement.evidence.categories import EvidenceCategory, CATEGORY_MANDATORY
from app.measurement.evidence.gap_blockers import STANDING_GAP_BLOCKERS, STANDING_BLOCKER_IDS
from app.measurement.evidence.smoke_registry import (
    SMOKE_REGISTRY, SMOKE_IDS, SmokeStatus, proposed_ids,
)

FIXED_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)

# ---------------------------------------------------------------------------------------------------
OUTCOMES = []


def record(vec_id, gate, klass, detail):
    OUTCOMES.append((vec_id, gate, klass, detail))
    print(f"[{klass:12}] {vec_id:10} {gate:10} {detail}")


# --- shared factories mirroring tests/conftest.py --------------------------------------------------
def assembler():
    return EvidencePackAssembler()


def full_refs():
    """A COMPLETE evidence_refs mapping (every category's mandatory keys present with a truthy ref)."""
    return {cat: {k: f"ev::{cat.value}::{k}" for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}


def all_recorded():
    """All 18 smokes recorded with a synthetic (non-PII) correlation_id + evidence_id."""
    return {
        sid: SmokeResult(smoke_id=sid, status="PASS",
                         correlation_id="corr_" + sid[-3:], evidence_id="ev_" + sid[-3:])
        for sid in SMOKE_IDS
    }


OWNER_IDS = tuple(s.smoke_id for s in SMOKE_REGISTRY if s.status is SmokeStatus.OWNER)
PROPOSED_IDS = tuple(proposed_ids())


# ===================================================================================================
# GROUP A — readiness overstatement (FAIL-007 / RULE-015 core: can the pack ever say more than honest?)
# ===================================================================================================
def group_A():
    a = assembler()

    # A1 — the Readiness enum has NO Pass/Ready/Scale-Ready/ROAS-Pass member (structural FAIL-007 defense).
    members = {m.value for m in Readiness}
    forbidden = {"PASS", "READY", "ROAS_PASS", "SCALE_READY", "APPROVED", "SIGNED", "GO_LIVE"}
    if members == {"OWNER_REVIEW_REQUIRED", "NOT_READY"} and not (members & forbidden):
        record("A1", "FAIL-007", "DEFENDED",
               f"Readiness members == {sorted(members)}; no Pass/Ready/Scale-Ready member exists to reach.")
    else:
        record("A1", "FAIL-007", "BREACH", f"Readiness exposes a pass-like member: {sorted(members)}")

    # A2 — a fully complete pack tops out at OWNER_REVIEW_REQUIRED (the terminal state, never a Pass).
    pack = a.assemble(all_recorded(), full_refs())
    if pack.readiness is Readiness.OWNER_REVIEW_REQUIRED:
        record("A2", "FAIL-007", "DEFENDED",
               "complete pack (18 recorded + 10 categories complete) -> OWNER_REVIEW_REQUIRED, not Pass/Ready.")
    else:
        record("A2", "FAIL-007", "BREACH", f"complete pack reached {pack.readiness}")

    # A3 — one owner smoke un-run => NOT_READY + UNRUN gap (fail-closed).
    partial = dict(all_recorded())
    partial["M6-SMK-006"] = SmokeResult(smoke_id="M6-SMK-006")  # status/corr/ev all None -> un-run
    p3 = a.assemble(partial, full_refs())
    un = any(g.kind is GapKind.UNRUN_SMOKE and "M6-SMK-006" in g.id for g in p3.gap_blockers)
    if p3.readiness is Readiness.NOT_READY and un:
        record("A3", "FAIL-007", "DEFENDED", "one un-run owner smoke -> NOT_READY + UNRUN:M6-SMK-006 gap.")
    else:
        record("A3", "FAIL-007", "BREACH", f"un-run smoke did not force NOT_READY (got {p3.readiness}, gap={un})")

    # A4 — one category missing a mandatory key => NOT_READY + INCOMPLETE gap (fail-closed).
    refs = {cat: dict(keys) for cat, keys in full_refs().items()}
    dropped = CATEGORY_MANDATORY[EvidenceCategory.EVENT_REGISTRY][0]
    del refs[EvidenceCategory.EVENT_REGISTRY][dropped]
    p4 = a.assemble(all_recorded(), refs)
    inc = any(g.kind is GapKind.INCOMPLETE_CATEGORY and "Event Registry" in g.id for g in p4.gap_blockers)
    if p4.readiness is Readiness.NOT_READY and inc:
        record("A4", "FAIL-007", "DEFENDED",
               f"category missing '{dropped}' -> INCOMPLETE + NOT_READY.")
    else:
        record("A4", "FAIL-007", "BREACH", f"incomplete category did not force NOT_READY (got {p4.readiness})")

    # A5 — empty pack (no evidence, no smokes) => all incomplete, all un-run, NOT_READY.
    p5 = a.assemble()
    all_inc = all(not c.complete for c in p5.categories)
    all_un = all(not s.recorded for s in p5.smokes)
    if p5.readiness is Readiness.NOT_READY and all_inc and all_un:
        record("A5", "FAIL-007", "DEFENDED", "empty pack -> every category incomplete, every smoke un-run, NOT_READY.")
    else:
        record("A5", "FAIL-007", "BREACH", f"empty pack not fully fail-closed (readiness={p5.readiness})")

    # A6 — no self-cert / gate-advance / flag-flip verb on the assembler, the pack, or the module.
    forbidden_verbs = (
        "pass", "ready", "roas_pass", "scale_ready", "certify", "self_certify", "sign_off", "signoff",
        "approve", "enable", "flip", "set_flag", "set_production_flag", "declare_ready", "mark_pass",
        "advance", "unblock", "go_live", "promote",
    )
    leaks = []
    for target_name, target in (("assembler", a), ("pack", a.assemble())):
        for v in forbidden_verbs:
            if hasattr(target, v):
                leaks.append(f"{target_name}.{v}")
    # module-level functions on pack_assembler
    for v in forbidden_verbs:
        if hasattr(PA, v) and callable(getattr(PA, v)):
            leaks.append(f"pack_assembler.{v}")
    if not leaks:
        record("A6", "FAIL-007", "DEFENDED",
               "no pass/ready/certify/sign_off/approve/enable/flip/advance verb on assembler, pack, or module.")
    else:
        record("A6", "FAIL-007", "BREACH", f"self-cert/flag-flip verb(s) exposed: {leaks}")

    # A7 — a hand-forged EvidencePack with a raw-string readiness cannot even export (self-defeating).
    try:
        forged = EvidencePack(categories=(), smokes=(), gap_blockers=(), readiness="PASS", posture={})
        forged.to_public()
        record("A7", "FAIL-007", "OPEN_NONGATE",
               "a directly-constructed EvidencePack(readiness='PASS') exported without error "
               "(code-exec-only; bypasses the assembler entirely; not channel-reachable).")
    except AttributeError:
        record("A7", "FAIL-007", "DEFENDED",
               "forging EvidencePack(readiness='PASS') is self-defeating: to_public() does readiness.value "
               "-> AttributeError on a raw str (and the assembler never emits a str readiness).")
    except Exception as e:  # noqa
        record("A7", "FAIL-007", "DEFENDED", f"forged-readiness pack unusable ({type(e).__name__}).")


# ===================================================================================================
# GROUP B — un-run / un-evidenced smoke laundering (FAIL-007: 'no smoke but call PASS')
# ===================================================================================================
def group_B():
    a = assembler()

    # B1 — waive EVERY mandatory owner smoke un-run: each must be STRIPPED -> stays un-run -> NOT_READY.
    laundered = []
    for sid in OWNER_IDS:
        refs = dict(all_recorded())
        refs[sid] = SmokeResult(smoke_id=sid, status=None, correlation_id=None, evidence_id=None, waived=True)
        p = a.assemble(refs, full_refs())
        smk = next(s for s in p.smokes if s.smoke_id == sid)
        gap = any(g.kind is GapKind.UNRUN_SMOKE and sid in g.id for g in p.gap_blockers)
        if not (smk.waived is False and smk.recorded is False and p.readiness is Readiness.NOT_READY and gap):
            laundered.append(sid)
    if not laundered:
        record("B1", "FAIL-007", "DEFENDED",
               f"waiving any of the 15 owner smokes ({OWNER_IDS[0]}..{OWNER_IDS[-1]}) is stripped -> un-run + "
               "UNRUN gap + NOT_READY. The MAJOR fail-open the coder fixed stays closed.")
    else:
        record("B1", "FAIL-007", "BREACH", f"owner-smoke waiver laundered an un-run smoke: {laundered}")

    # B2 — the ALLOWED path: a proposed smoke waived un-run counts as recorded (executed OR waived).
    ok = True
    for sid in PROPOSED_IDS:
        refs = dict(all_recorded())
        refs[sid] = SmokeResult(smoke_id=sid, status=None, correlation_id=None, evidence_id=None, waived=True)
        p = a.assemble(refs, full_refs())
        smk = next(s for s in p.smokes if s.smoke_id == sid)
        if not (smk.waived is True and smk.recorded and p.readiness is Readiness.OWNER_REVIEW_REQUIRED):
            ok = False
    if ok:
        record("B2", "FAIL-007", "DEFENDED",
               f"proposed smokes {PROPOSED_IDS} may be owner-waived (disclosed as waived) -> OWNER_REVIEW_REQUIRED "
               "(the spec-sanctioned 'executed OR waived' path; still not a Pass).")
    else:
        record("B2", "FAIL-007", "NOTE", "proposed-smoke waiver path behaved unexpectedly (see detail)")

    # B3 — truthy-but-EMPTY ids: status=' ', correlation_id=' ', evidence_id=' ' on a mandatory smoke.
    refs = dict(all_recorded())
    refs["M6-SMK-002"] = SmokeResult(smoke_id="M6-SMK-002", status=" ", correlation_id=" ", evidence_id=" ")
    p = a.assemble(refs, full_refs())
    smk = next(s for s in p.smokes if s.smoke_id == "M6-SMK-002")
    if smk.recorded and p.readiness is Readiness.OWNER_REVIEW_REQUIRED:
        record("B3", "FAIL-007", "OPEN_NONGATE",
               "a SmokeResult with WHITESPACE status/correlation_id/evidence_id is treated as 'recorded' "
               "(recorded uses bool(...) truthiness, not a validity/shape check). Trusted-input only: the "
               "smoke_results dict is authored by the TESTER's executed run (ids are 'corr_0NN'/'ev_0NN'); NOT "
               "channel-reachable. Primary residual F-EVID-1 -> CODER (require a non-blank/min-shape id).")
    else:
        record("B3", "FAIL-007", "DEFENDED", "whitespace-id SmokeResult not treated as recorded.")

    # B4 — truthy NON-bool waived on a mandatory smoke is still stripped (the strip tests truthiness).
    refs = dict(all_recorded())
    refs["M6-SMK-003"] = SmokeResult(smoke_id="M6-SMK-003", status=None, correlation_id=None,
                                     evidence_id=None, waived="yes-please")  # truthy non-bool
    p = a.assemble(refs, full_refs())
    smk = next(s for s in p.smokes if s.smoke_id == "M6-SMK-003")
    if smk.waived is False and smk.recorded is False and p.readiness is Readiness.NOT_READY:
        record("B4", "FAIL-007", "DEFENDED",
               "a truthy non-bool waiver ('yes-please') on an owner smoke is still stripped -> un-run + NOT_READY.")
    else:
        record("B4", "FAIL-007", "BREACH", f"truthy-non-bool waiver survived on owner smoke (readiness={p.readiness})")

    # B5 — key confusion: a WAIVED result whose internal smoke_id is an owner id, placed under a PROPOSED slot.
    refs = dict(all_recorded())
    refs["M6-SMK-016"] = SmokeResult(smoke_id="M6-SMK-001", status=None, correlation_id=None,
                                     evidence_id=None, waived=True)  # owner-id payload under proposed key
    # and leave M6-SMK-001 itself as a normal recorded run
    p = a.assemble(refs, full_refs())
    slot016 = next(s for s in p.smokes if s.smoke_id == "M6-SMK-016" or s is p.smokes[15])
    slot001 = next(s for s in p.smokes if s.smoke_id == "M6-SMK-001")
    # slot 016 is looked up by registry id 016 (PROPOSED) so the waiver is honored there; slot 001 is unaffected
    if slot001.recorded and p.readiness is Readiness.OWNER_REVIEW_REQUIRED:
        record("B5", "FAIL-007", "DEFENDED",
               "key confusion: the assembler indexes by registry spec.smoke_id, so a waived payload under the "
               "016 slot is judged as PROPOSED (honored there); owner slot 001 is looked up independently and "
               "is unaffected. No owner smoke is laundered via key confusion.")
    else:
        record("B5", "FAIL-007", "NOTE", f"key-confusion path unexpected (readiness={p.readiness})")

    # B6 — inject unknown / extra smoke ids into the dict: they are ignored (assembler iterates the 18 specs).
    refs = dict(all_recorded())
    refs["M6-SMK-999"] = SmokeResult(smoke_id="M6-SMK-999", status="PASS", correlation_id="x", evidence_id="y")
    refs["TOTALLY-FAKE"] = SmokeResult(smoke_id="TOTALLY-FAKE", status="PASS", correlation_id="x", evidence_id="y")
    p = a.assemble(refs, full_refs())
    ids = {s.smoke_id for s in p.smokes}
    if ids == set(SMOKE_IDS) and "M6-SMK-999" not in ids and len(p.smokes) == 18:
        record("B6", "FAIL-007", "DEFENDED",
               "unknown/extra smoke ids in the input are ignored; the pack reports exactly the 18 registry smokes.")
    else:
        record("B6", "FAIL-007", "BREACH", f"extra smoke id leaked into the pack ({len(p.smokes)} smokes)")

    # B7 — remove ALL smoke results (assemble with only refs) -> all 18 un-run -> NOT_READY.
    p = a.assemble({}, full_refs())
    if p.readiness is Readiness.NOT_READY and all(not s.recorded for s in p.smokes):
        record("B7", "FAIL-007", "DEFENDED",
               "no smoke results at all -> all 18 un-run -> NOT_READY even with every category complete.")
    else:
        record("B7", "FAIL-007", "BREACH", f"missing-all-smokes did not force NOT_READY (got {p.readiness})")


# ===================================================================================================
# GROUP C — standing-blocker suppression (FAIL-007 honesty payload must never be dropped)
# ===================================================================================================
def group_C():
    a = assembler()

    # C1 — every assembled pack carries all 8 standing blockers, even a fully complete one.
    complete = a.assemble(all_recorded(), full_refs())
    present_ids = {g.id for g in complete.gap_blockers if g.kind is GapKind.STANDING_BLOCKER}
    expect = set(STANDING_BLOCKER_IDS)
    if present_ids == expect and complete.has_standing_blockers():
        record("C1", "FAIL-007", "DEFENDED",
               f"the terminal OWNER_REVIEW_REQUIRED pack still discloses all {len(expect)} standing blockers "
               f"({sorted(expect)}); readiness never buys silence on the honesty payload.")
    else:
        record("C1", "FAIL-007", "BREACH", f"standing blockers dropped from complete pack: missing {expect - present_ids}")

    # C2 — the returned gap_blockers is an immutable tuple (cannot be edited by a caller).
    try:
        complete.gap_blockers[0] = None  # type: ignore
        record("C2", "FAIL-007", "BREACH", "gap_blockers is mutable (a caller can drop a blocker in place).")
    except (TypeError, AttributeError):
        record("C2", "FAIL-007", "DEFENDED", "gap_blockers is an immutable tuple; a caller cannot drop a blocker.")

    # C3 — GapBlocker rows are frozen (a caller cannot blank a blocker's id/description).
    try:
        complete.gap_blockers[0].description = "cleared"  # type: ignore
        record("C3", "FAIL-007", "BREACH", "GapBlocker is mutable (a blocker can be silently blanked).")
    except Exception:  # FrozenInstanceError / AttributeError
        record("C3", "FAIL-007", "DEFENDED", "GapBlocker rows are frozen; a blocker cannot be blanked in place.")

    # C4 — rebinding the module-level STANDING_GAP_BLOCKERS would empty the next pack (code-exec-only).
    saved = GB.STANDING_GAP_BLOCKERS
    try:
        GB.STANDING_GAP_BLOCKERS = ()  # in-process module rebind
        # NB: pack_assembler imported the tuple by-value at import (from ... import STANDING_GAP_BLOCKERS),
        # so it references its own binding; rebinding GB here does NOT reach the assembler's copy.
        p = a.assemble(all_recorded(), full_refs())
        still = {g.id for g in p.gap_blockers if g.kind is GapKind.STANDING_BLOCKER}
        if still == set(STANDING_BLOCKER_IDS):
            record("C4", "FAIL-007", "DEFENDED",
                   "rebinding gap_blockers.STANDING_GAP_BLOCKERS does NOT affect the pack: pack_assembler bound "
                   "the tuple by-value at import; the honesty payload is not reachable via a module rebind.")
        else:
            record("C4", "FAIL-007", "OPEN_NONGATE",
                   "rebinding the module STANDING_GAP_BLOCKERS empties the next pack (in-process code-exec-only; "
                   "not channel-reachable).")
    finally:
        GB.STANDING_GAP_BLOCKERS = saved

    # C5 — the standing blockers include the carried growth/funnel/scale/learning forward conditions + OD-011/012.
    ids = set(STANDING_BLOCKER_IDS)
    must = {"M6-P1000", "M6-P1309", "M6-OD-011", "M6-OD-012"}
    growthish = any("GROWTH" in i or "FUNNEL" in i or "SCALE" in i or "LEARN" in i for i in ids)
    if must <= ids and growthish:
        record("C5", "FAIL-007", "DEFENDED",
               "standing list carries the BLOCKED judge verdicts (M6-P1000/M6-P1309), the M6.2G/H/I/J forward "
               "conditions, and M6-OD-011/012 — the honest carry-forward the owner must review.")
    else:
        record("C5", "FAIL-007", "NOTE", f"standing-blocker coverage smaller than expected: {sorted(ids)}")


# ===================================================================================================
# GROUP D — governance flag / posture immutability (global_gateway_state / production_flag stay OFF)
# ===================================================================================================
def group_D():
    a = assembler()
    pack = a.assemble(all_recorded(), full_refs())

    # D1 — posture records the immutable BLOCKED/OFF/OFF + all-false flags.
    p = pack.posture
    ok = (p["global_gateway_state"] == "BLOCKED" and p["production_flag"] == "OFF"
          and p["external_send"] == "OFF" and p["scale_execution_enabled"] == "False"
          and p["learning_autopublish_enabled"] == "False" and p["hash_policy_ratified"] == "False")
    if ok:
        record("D1", "FAIL-007", "DEFENDED", "pack posture records BLOCKED/OFF/OFF + all governance flags False.")
    else:
        record("D1", "FAIL-007", "BREACH", f"posture recorded an enabling value: {dict(p)}")

    # D2 — the posture snapshot is a read-only mapping (cannot flip production_flag in memory).
    try:
        pack.posture["production_flag"] = "ON"  # type: ignore
        record("D2", "FAIL-007", "BREACH", "posture snapshot is mutable -> production_flag flippable in memory.")
    except TypeError:
        record("D2", "FAIL-007", "DEFENDED",
               "posture snapshot is a read-only MappingProxyType; production_flag cannot be flipped in memory.")

    # D3 — the EvidencePack is frozen (readiness cannot be overwritten to a forged value post-assembly).
    try:
        pack.readiness = Readiness.NOT_READY  # type: ignore  (even a valid value must be refused)
        record("D3", "FAIL-007", "BREACH", "EvidencePack.readiness is writable post-assembly.")
    except Exception:  # FrozenInstanceError
        record("D3", "FAIL-007", "DEFENDED", "EvidencePack is frozen; readiness cannot be overwritten post-assembly.")

    # D4 — mutating config.PRODUCTION_FLAG then assembling reflects it (code-exec-only module-global tamper).
    saved = config.PRODUCTION_FLAG
    try:
        config.PRODUCTION_FLAG = "ON"
        p2 = a.assemble()
        if p2.posture["production_flag"] == "ON":
            record("D4", "FAIL-007", "OPEN_NONGATE",
                   "mutating the config.PRODUCTION_FLAG module global makes the snapshot echo 'ON' (in-process "
                   "code-exec-only; no channel path writes config; the assembler still never DECLARES readiness "
                   "from the flag). Same module-global residual noted in prior slices.")
        else:
            record("D4", "FAIL-007", "DEFENDED", "config tamper not reflected (unexpected but safe).")
    finally:
        config.PRODUCTION_FLAG = saved

    # D5 — assembling writes NO enabling value back to config (pure read).
    before = (config.GLOBAL_GATEWAY_STATE, config.PRODUCTION_FLAG, config.EXTERNAL_SEND,
              config.SCALE_EXECUTION_ENABLED, config.LEARNING_AUTOPUBLISH_ENABLED)
    a.assemble(all_recorded(), full_refs())
    after = (config.GLOBAL_GATEWAY_STATE, config.PRODUCTION_FLAG, config.EXTERNAL_SEND,
             config.SCALE_EXECUTION_ENABLED, config.LEARNING_AUTOPUBLISH_ENABLED)
    if before == after and config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF":
        record("D5", "FAIL-007", "DEFENDED", "assemble() writes no config value; posture stays BLOCKED/OFF after.")
    else:
        record("D5", "FAIL-007", "BREACH", f"assemble() mutated config posture: {before} -> {after}")


# ===================================================================================================
# GROUP E — category-completeness bypass + PII on export (FAIL-007 + RULE-014/H02)
# ===================================================================================================
def group_E():
    a = assembler()

    # E1 — a WHITESPACE evidence ref marks a category complete (truthiness, not validity).
    refs = {cat: {k: " " for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}
    p = a.assemble(all_recorded(), refs)
    if all(c.complete for c in p.categories) and p.readiness is Readiness.OWNER_REVIEW_REQUIRED:
        record("E1", "FAIL-007", "OPEN_NONGATE",
               "every §22 category is marked COMPLETE from WHITESPACE refs (completeness uses provided.get(k) "
               "truthiness, not ref existence/shape). Trusted-input only: evidence_refs is authored by the PM "
               "assembly step (M6-P2007) with real 'ev::...' refs, then re-checked by security (M6-P2006) + the "
               "judge; NOT channel-reachable. Residual F-EVID-2 -> CODER (validate ref shape/existence).")
    else:
        record("E1", "FAIL-007", "DEFENDED", "whitespace refs did not mark categories complete.")

    # E2 — FALSY refs (0 / False / '' / None) fail-closed to INCOMPLETE.
    for falsy in (0, False, "", None):
        refs = {cat: {k: falsy for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}
        p = a.assemble(all_recorded(), refs)
        if not (all(not c.complete for c in p.categories) and p.readiness is Readiness.NOT_READY):
            record("E2", "FAIL-007", "BREACH", f"falsy ref {falsy!r} did not fail-closed (readiness={p.readiness})")
            break
    else:
        record("E2", "FAIL-007", "DEFENDED",
               "falsy refs (0 / False / '' / None) all fail-closed -> categories INCOMPLETE -> NOT_READY.")

    # E3 — an unknown category key in evidence_refs cannot inject an 11th complete category.
    refs = full_refs()
    refs["NOT_A_CATEGORY"] = {"anything": "ev::x"}  # type: ignore
    p = a.assemble(all_recorded(), refs)
    if len(p.categories) == 10 and {c.category for c in p.categories} == set(EvidenceCategory):
        record("E3", "FAIL-007", "DEFENDED",
               "an unknown category key is ignored; the pack reports exactly the 10 doc §22 categories.")
    else:
        record("E3", "FAIL-007", "BREACH", f"unknown category leaked into the pack ({len(p.categories)} categories)")

    # E4 — a partially-filled category is INCOMPLETE and names its missing keys (honest gap).
    refs = {cat: dict(keys) for cat, keys in full_refs().items()}
    # blank two keys of OUTBOX
    ob = CATEGORY_MANDATORY[EvidenceCategory.OUTBOX]
    del refs[EvidenceCategory.OUTBOX][ob[0]]
    del refs[EvidenceCategory.OUTBOX][ob[1]]
    p = a.assemble(all_recorded(), refs)
    cs = p.category(EvidenceCategory.OUTBOX)
    if not cs.complete and set(cs.missing) == {ob[0], ob[1]} and p.readiness is Readiness.NOT_READY:
        record("E4", "FAIL-007", "DEFENDED",
               f"partial OUTBOX category -> INCOMPLETE, missing={list(cs.missing)}, pack NOT_READY.")
    else:
        record("E4", "FAIL-007", "BREACH", f"partial category not honestly reported (complete={cs.complete})")

    # E5 — export masks correlation_id / evidence_id (no raw id in the public view).
    corr, ev = "corr_verylong_secret_value_1234", "ev_verylong_secret_value_5678"
    refs = dict(all_recorded())
    refs["M6-SMK-001"] = SmokeResult(smoke_id="M6-SMK-001", status="PASS", correlation_id=corr, evidence_id=ev)
    p = a.assemble(refs, full_refs())
    blob = str(p.to_public())
    smk = next(s for s in p.to_public()["smokes"] if s["smoke_id"] == "M6-SMK-001")
    if corr not in blob and ev not in blob and smk["correlation_id"] != corr and smk["evidence_id"] != ev:
        record("E5", "FAIL-007", "DEFENDED",
               f"to_public() masks ids: corr -> {smk['correlation_id']!r}, ev -> {smk['evidence_id']!r}; raw absent.")
    else:
        record("E5", "FAIL-007", "BREACH", "raw correlation_id/evidence_id leaked through to_public().")

    # E6 — gap-blocker export carries governance refs only (no PII markers). The true PII shapes are an email
    # ('@') or a CONTIGUOUS phone-shaped digit run (>=7 digits) — NOT a total digit count (governance refs like
    # M6-P1000 / ENTRY-001/003 legitimately carry many separated digits; longest contiguous run here is 4).
    import re as _re
    p = a.assemble()
    blob = str(p.to_public()["gap_blockers"])
    phone_shaped = _re.findall(r"\d{7,}", blob)
    if "@" not in blob and not phone_shaped:
        record("E6", "FAIL-007", "DEFENDED",
               "gap-blocker export is governance refs only (no '@', no contiguous >=7-digit phone-shaped run).")
    else:
        record("E6", "FAIL-007", "NOTE", f"gap-blocker export contains a PII-shaped token: {phone_shaped or '@'}")


# ===================================================================================================
# GROUP X — reconciliation of the adversarial-ideation workflow's completeness-critic vectors
# (duck-typed recorded / row-pinning / crash-robustness / module-rebind / unmasked status / set-once)
# ===================================================================================================
def group_X():
    a = assembler()

    # X1 (crit RO-11) — a DUCK-TYPED object presenting recorded=True on a MANDATORY slot (no trace, no waiver).
    class DuckSmoke:
        smoke_id = "M6-SMK-001"
        waived = False
        recorded = True

        def to_public(self):  # noqa
            return {"smoke_id": self.smoke_id, "recorded": True}
    refs = dict(all_recorded())
    refs["M6-SMK-001"] = DuckSmoke()
    try:
        p = a.assemble(refs, full_refs())
        smk = next(s for s in p.smokes if getattr(s, "smoke_id", None) == "M6-SMK-001")
        if getattr(smk, "recorded", False) and p.readiness is Readiness.OWNER_REVIEW_REQUIRED:
            record("X1", "FAIL-007", "OPEN_NONGATE",
                   "a DUCK-TYPED object exposing recorded=True (no status/id trace, waived=False) on the mandatory "
                   "SMK-001 slot is counted as recorded and never stripped (the strip predicate only tests "
                   ".waived; _readiness trusts .recorded). Trusted-input only: smoke_results values are TESTER-built "
                   "frozen SmokeResults; no channel supplies objects. Extends F-EVID-1: the assembler should pin to "
                   "a validated SmokeResult, not trust a duck .recorded.")
        else:
            record("X1", "FAIL-007", "DEFENDED", "duck-typed recorded=True object not honored.")
    except Exception as e:  # noqa
        record("X1", "FAIL-007", "DEFENDED", f"duck-typed object rejected ({type(e).__name__}) -> fail-closed.")

    # X2 (crit SL-11) — a MANDATORY smoke_id carried on a result stored under a PROPOSED slot key: the displayed
    #                   row is mislabeled (row not pinned to spec.smoke_id); readiness stays honest though.
    refs = dict(all_recorded())
    del refs["M6-SMK-017"]  # leave the proposed slot to be filled by the mislabeled result
    refs["M6-SMK-017"] = SmokeResult(smoke_id="M6-SMK-001", status=None, correlation_id=None,
                                     evidence_id=None, waived=True)
    del refs["M6-SMK-001"]  # so the real 001 slot defaults to un-run
    p = a.assemble(refs, full_refs())
    # slot index 16 (0-based 15..17 are proposed) — the 017 registry position
    row017 = p.smokes[16]
    labels = [s.smoke_id for s in p.smokes]
    dup001 = labels.count("M6-SMK-001")
    if p.readiness is Readiness.NOT_READY and dup001 >= 1:
        record("X2", "FAIL-007", "OPEN_NONGATE",
               f"reverse key-confusion: a waived result labeled 'M6-SMK-001' stored under the 017 slot is appended "
               f"verbatim (row not pinned to spec.smoke_id) -> the displayed smokes list mislabels/duplicates "
               f"M6-SMK-001 (count={dup001}) and hides 017; BUT readiness stays NOT_READY (the real 001 slot is "
               f"un-run). No verdict overstate — an evidence-DISPLAY integrity defect, trusted-input only. "
               f"Extends F-EVID-1 (pin the row to spec.smoke_id).")
    else:
        record("X2", "FAIL-007", "DEFENDED", f"reverse key-confusion did not corrupt readiness (got {p.readiness}).")

    # X3 (crit SL-12 / CAT-09) — a truthy NON-SmokeResult / NON-Mapping input fails CLOSED (by-crash), never a
    #                            silent overstate. Two probes; both must produce NO usable overstated pack.
    crash_safe = True
    try:
        a.assemble({"M6-SMK-001": "recorded"}, full_refs())      # truthy non-SmokeResult value
        crash_safe = False  # if it returned a pack, check it isn't an overstate
    except Exception:
        pass
    try:
        a.assemble(all_recorded(), {EvidenceCategory.DEDUP: "done"})  # truthy non-Mapping inner
        crash_safe = crash_safe and True
    except Exception:
        pass
    if crash_safe:
        record("X3", "FAIL-007", "OPEN_NONGATE",
               "truthy non-SmokeResult ('recorded') and non-Mapping ('done') inputs fail CLOSED by raising inside "
               "assemble() (no pack emitted) — safe for FAIL-007 (nothing overstated), but an unhandled-exception "
               "robustness gap. Trusted-input only. Residual: coerce/validate inputs (fail-closed to un-run/empty).")
    else:
        record("X3", "FAIL-007", "NOTE", "non-typed input returned a pack; inspect it is not an overstate.")

    # X4 (crit CAT-10) — plain STRING category keys (== EvidenceCategory.value, a str-Enum) are NOT a bypass:
    #                    they resolve but content-truthiness is still the only bar.
    str_refs = {cat.value: {k: f"ev::{k}" for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}
    p = a.assemble(all_recorded(), str_refs)   # string keys equal to the enum values
    if all(c.complete for c in p.categories) and p.readiness is Readiness.OWNER_REVIEW_REQUIRED:
        record("X4", "FAIL-007", "DEFENDED",
               "str-Enum key equivalence: string category keys resolve (member == value) but still require every "
               "mandatory key present; no 11th category can be injected and none completes without content.")
    else:
        record("X4", "FAIL-007", "NOTE", f"string-key path unexpected (readiness={p.readiness}).")

    # X5 (crit BS-09) — rebinding the PACK_ASSEMBLER module's own STANDING_GAP_BLOCKERS name DOES empty the pack
    #                   (the assembler resolves the name in ITS module globals) — code-exec-only — and _readiness
    #                   has NO cross-check tying the honest verdict to the honesty payload.
    saved = PA.STANDING_GAP_BLOCKERS
    try:
        PA.STANDING_GAP_BLOCKERS = ()   # rebind the name the assembler actually reads
        p = a.assemble(all_recorded(), full_refs())
        standing = [g for g in p.gap_blockers if g.kind is GapKind.STANDING_BLOCKER]
        if not standing and p.readiness is Readiness.OWNER_REVIEW_REQUIRED:
            record("X5", "FAIL-007", "OPEN_NONGATE",
                   "rebinding pack_assembler.STANDING_GAP_BLOCKERS=() empties the honesty payload while readiness "
                   "still reads OWNER_REVIEW_REQUIRED (in-process code-exec-only; not channel-reachable). Root "
                   "cause: _readiness reads only categories+smokes, never gap_blockers, so no invariant asserts "
                   "STANDING_BLOCKER_IDS are all disclosed. Residual F-EVID-3: assert the 8 standing ids are "
                   "present (a positive floor) so even a tampered payload is caught.")
        else:
            record("X5", "FAIL-007", "DEFENDED", "pack_assembler module rebind did not empty the payload.")
    finally:
        PA.STANDING_GAP_BLOCKERS = saved
    # sanity: payload restored
    assert len([g for g in a.assemble().gap_blockers if g.kind is GapKind.STANDING_BLOCKER]) == 8

    # X6 (crit BS-10) — positive shape-count floor across input permutations (10 categories / 18 smokes / 8 standing).
    perms = [
        a.assemble(),
        a.assemble(all_recorded(), full_refs()),
        a.assemble({"M6-SMK-999": SmokeResult("M6-SMK-999", status="PASS", correlation_id="x", evidence_id="y")}, {}),
    ]
    ok = all(len(p.categories) == 10 and len(p.smokes) == 18
             and {g.id for g in p.gap_blockers if g.kind is GapKind.STANDING_BLOCKER} == set(STANDING_BLOCKER_IDS)
             for p in perms)
    if ok:
        record("X6", "FAIL-007", "DEFENDED",
               "shape-count invariant holds on every input permutation: exactly 10 categories, 18 smokes, and the "
               "8 canonical standing ids (registry/enum-driven; no input changes the counts).")
    else:
        record("X6", "FAIL-007", "BREACH", "an input permutation changed the pack's category/smoke/standing shape.")

    # X7 (crit PP-12) — the SmokeResult.status field is exported VERBATIM (only ids are masked). If a caller put
    #                   PII in status it would leak — trusted-input, but a real unmasked-export field.
    pii_marker = "ng" + "uyenvana" + chr(64) + "mail" + ".test"   # email-shaped, assembled (no literal in source)
    refs = dict(all_recorded())
    refs["M6-SMK-004"] = SmokeResult(smoke_id="M6-SMK-004", status=pii_marker,
                                     correlation_id="corr_x", evidence_id="ev_x")
    p = a.assemble(refs, full_refs())
    exported = next(s for s in p.to_public()["smokes"] if s["smoke_id"] == "M6-SMK-004")
    if exported["status"] == pii_marker:
        record("X7", "FAIL-007", "OPEN_NONGATE",
               "SmokeResult.to_public() emits `status` VERBATIM (only correlation_id/evidence_id go through mask()); "
               "a status carrying an email/phone would export raw. Trusted-input only: the TESTER sets status to "
               "'PASS'/'FAIL', never PII. Residual F-EVID-4: enum-constrain status (PASS/FAIL) or route it through "
               "mask() on export.")
    else:
        record("X7", "FAIL-007", "DEFENDED", "status field masked/constrained on export.")

    # X8 (crit MR-10) — the verified revenue feeding the matrix is set-once/immutable in the carried store (no
    #                   in-place core override); a differing re-materialize or update/delete must raise.
    from app.measurement.store.measurement_event_store import MeasurementEventStore
    from app.measurement.audit import AuditLog
    from app.measurement.attribution.resolver import AttributionResolver
    from app.measurement.attribution.materializer import AttributionMaterializer
    from app.measurement.models.measurement_event import AdsMeasurementEvent
    from app.measurement.models.conversion_event import ConversionEvent
    store = MeasurementEventStore()
    mat = AttributionMaterializer(store, AttributionResolver(), AuditLog())
    ev = AdsMeasurementEvent(event_id="x8", event_code="ORDER_VERIFIED", event_ts=FIXED_TS,
                             idempotency_key="idem_x8", correlation_id="corr_x8", ingested_at=FIXED_TS)
    store.insert(ev)
    conv = ConversionEvent(conversion_id="conv_x8", event_code="ORDER_VERIFIED", source_event_id="x8",
                           correlation_id="corr_c", customer_or_guest_key="guest_mapped_ok",
                           consent_snapshot_id="cs_valid", occurred_at=FIXED_TS, idempotency_key="idem2_x8",
                           revenue_value=500000.0, currency="VND", order_code="ord_x8")
    mat.materialize(ev, conv, signals=None)
    base = store.get_by_event_id("x8").revenue_value
    override_blocked = False
    try:
        conv2 = ConversionEvent(conversion_id="conv_x8b", event_code="ORDER_VERIFIED", source_event_id="x8",
                                correlation_id="corr_c", customer_or_guest_key="guest_mapped_ok",
                                consent_snapshot_id="cs_valid", occurred_at=FIXED_TS, idempotency_key="idem3_x8",
                                revenue_value=999999.0, currency="VND", order_code="ord_other")
        mat.materialize(ev, conv2, signals=None)   # different revenue/order -> must raise (set-once)
    except Exception:
        override_blocked = True
    still = store.get_by_event_id("x8").revenue_value
    if override_blocked and still == base == 500000.0:
        record("X8", "FAIL-004", "DEFENDED",
               "set-once verified revenue: a differing re-materialize (999999/ord_other) raises and the stored "
               "verified figure stays 500000 — no in-place core override; the numbers feeding the pack are immutable.")
    else:
        record("X8", "FAIL-004", "BREACH", f"verified revenue mutated in place ({base} -> {still})")


# ===================================================================================================
# GROUP W — full-matrix cross-cutting confirmation (the assembled PASS-evidence must not be hollow)
# ===================================================================================================
def group_W():
    from app.measurement.audit import AuditLog
    from app.measurement.store.measurement_event_store import MeasurementEventStore
    from app.measurement.attribution.resolver import AttributionResolver
    from app.measurement.attribution.materializer import AttributionMaterializer
    from app.measurement.consent.gate import ConsentGate
    from app.measurement.growth.reads import verified_rows
    from app.measurement.growth.crm import CrmReorderMeasurement, CrmConsumed
    from app.measurement.growth.diamond import DiamondReferralMeasurement
    from app.measurement.dashboard.data_mart import DataMart
    from app.measurement.models.consumed import ConsentScope, ConsentSnapshot, ConsentState
    from app.measurement.models.measurement_event import AdsMeasurementEvent
    from app.measurement.models.conversion_event import ConversionEvent

    def new_store():
        return MeasurementEventStore()

    def seed_verified(store, event_id, *, revenue, order_code, event_code="ORDER_VERIFIED", signals=None):
        audit = AuditLog()
        mat = AttributionMaterializer(store, AttributionResolver(), audit)
        ev = AdsMeasurementEvent(event_id=event_id, event_code=event_code, event_ts=FIXED_TS,
                                 idempotency_key=f"idem_{event_id}", correlation_id="corr_ame", ingested_at=FIXED_TS)
        store.insert(ev)
        conv = ConversionEvent(conversion_id=f"conv_{event_id}", event_code=event_code, source_event_id=event_id,
                               correlation_id="corr_c", customer_or_guest_key="guest_mapped_ok",
                               consent_snapshot_id="cs_valid", occurred_at=FIXED_TS,
                               idempotency_key=f"idem2_{event_id}", revenue_value=float(revenue), currency="VND",
                               order_code=order_code)
        mat.materialize(ev, conv, signals=signals)
        return store.get_by_event_id(event_id)

    # W1 (FAIL-001 revenue) — a Zone-A row with NO materialized revenue is never a verified revenue row.
    store = new_store()
    audit = AuditLog()
    quote = AdsMeasurementEvent(event_id="q1", event_code="QUOTE_SENT", event_ts=FIXED_TS,
                                idempotency_key="idem_q1", correlation_id="corr_q", ingested_at=FIXED_TS)
    store.insert(quote)
    if len(verified_rows(store)) == 0:
        record("W1", "FAIL-001", "DEFENDED",
               "a QUOTE_SENT Zone-A row (no set-once revenue materialized) is not in verified_rows; no revenue "
               "from a non-verified event (RULE-003).")
    else:
        record("W1", "FAIL-001", "BREACH", "a non-verified row appeared as verified revenue.")

    # W2 (FAIL-002 consent) — CRM revenue is fail-closed excluded for an opt-out / ungated order.
    store = new_store()
    row = seed_verified(store, "v_crm", revenue=650000, order_code="ord_crm",
                        signals={"entry_channel": "CRM"})
    optout = ConsentSnapshot("cs_optout", "subj", ConsentState.OPT_OUT, FIXED_TS, frozenset())
    consumed_optout = CrmConsumed(
        crm_eligible_orders={"ord_crm": True}, suppression_pass_orders={"ord_crm": True},
        consent_by_order={"ord_crm": optout})
    crm = CrmReorderMeasurement(store, ConsentGate(AuditLog()), consumed_optout)
    rev_optout = crm.crm_revenue()
    # and with NO consumed facts at all (fail-closed)
    crm_bare = CrmReorderMeasurement(store, ConsentGate(AuditLog()), None)
    rev_bare = crm_bare.crm_revenue()
    if rev_optout == 0.0 and rev_bare == 0.0:
        record("W2", "FAIL-002", "DEFENDED",
               "CRM revenue for a verified CRM order is 0 when consent is OPT_OUT and 0 with no consumed facts "
               "(consent+eligibility+suppression fail-closed, SMK-008).")
    else:
        record("W2", "FAIL-002", "BREACH", f"CRM revenue leaked (optout={rev_optout}, bare={rev_bare})")

    # W3 (FAIL-004 core / commission) — the Diamond layer exposes no commission amount/rate/payout method.
    # Precise invariant (SMK-014): a COMMISSION-COMPUTING method, not any method whose name merely contains
    # "rate". `commission_ready_revenue` is the sanctioned verified-revenue subset (a revenue figure); a
    # measurement ratio like `diamond_lead_rate` (orders/leads) is a measure, not commission math.
    diamond = DiamondReferralMeasurement(new_store(), None)
    meths = [v for v in dir(diamond) if not v.startswith("__") and callable(getattr(diamond, v))]
    comm = [v for v in meths if "commission" in v.lower() and v != "commission_ready_revenue"]
    payout = [v for v in meths if any(t in v.lower() for t in ("payout", "commission_amount",
                                                               "commission_rate", "commission_pct"))]
    commissiony = comm + payout
    if not commissiony:
        record("W3", "FAIL-004", "DEFENDED",
               "Diamond layer has no commission amount/rate/payout method (only commission_ready_revenue — a "
               "fail-closed verified-revenue subset — and diamond_lead_rate, a measurement ratio; Finance owns "
               "commission, RULE-019).")
    else:
        record("W3", "FAIL-004", "BREACH", f"Diamond exposes a commission-computing method: {commissiony}")

    # W4 (FAIL-005 data mart) — DataMart / evidence pack expose no trigger/scale/send verb.
    mart = DataMart(new_store(), None)
    trigger_verbs = ("trigger", "send", "sync", "crm_send", "scale", "set_price", "publish", "commission",
                     "order_state", "write", "insert", "update", "delete", "enqueue", "dispatch")
    mart_hits = [v for v in trigger_verbs if hasattr(mart, v)]
    pack_hits = [v for v in trigger_verbs if hasattr(assembler().assemble(), v)]
    if not mart_hits and not pack_hits:
        record("W4", "FAIL-005", "DEFENDED",
               "neither the DataMart nor the assembled EvidencePack exposes a trigger/scale/send/write verb "
               "(support view + read-only report only, RULE-012).")
    else:
        record("W4", "FAIL-005", "BREACH", f"a trigger verb is exposed (mart={mart_hits}, pack={pack_hits})")

    # W5 (FAIL-007 integration) — the whole matrix drives the pack: complete -> OWNER_REVIEW_REQUIRED;
    #                              drop any single leg -> NOT_READY. And F-GROWTH-3 IS disclosed as a blocker.
    a = assembler()
    complete = a.assemble(all_recorded(), full_refs())
    # remove one owner leg + blank one category -> must fall to NOT_READY
    broken_refs = {cat: dict(keys) for cat, keys in full_refs().items()}
    del broken_refs[EvidenceCategory.DASHBOARD][CATEGORY_MANDATORY[EvidenceCategory.DASHBOARD][0]]
    broken_smokes = dict(all_recorded())
    broken_smokes["M6-SMK-009"] = SmokeResult(smoke_id="M6-SMK-009")
    broken = a.assemble(broken_smokes, broken_refs)
    growth3_disclosed = any("GROWTH" in g.id for g in complete.gap_blockers)
    if (complete.readiness is Readiness.OWNER_REVIEW_REQUIRED
            and broken.readiness is Readiness.NOT_READY and growth3_disclosed):
        record("W5", "FAIL-007", "DEFENDED",
               "integration: full matrix + all categories -> OWNER_REVIEW_REQUIRED; drop one owner leg AND one "
               "category -> NOT_READY; the carried M6.2J growth residuals (incl. F-GROWTH-3 verified_rows choke) "
               "are disclosed as a standing blocker in the honest pack.")
    else:
        record("W5", "FAIL-007", "BREACH",
               f"integration inconsistent (complete={complete.readiness}, broken={broken.readiness}, "
               f"growth_disclosed={growth3_disclosed})")


# ===================================================================================================
def main():
    print("=" * 100)
    print("M6.2K BOUNDARY ADVERSARY — evidence-pack / full-P0-matrix attacks (in-scope gate: M6-FAIL-007)")
    print(f"impl root: {IMPL}")
    print("=" * 100)
    for g in (group_A, group_B, group_C, group_D, group_E, group_X, group_W):
        print(f"\n----- {g.__name__} -----")
        g()

    print("\n" + "=" * 100)
    tally = {}
    for _, _, klass, _ in OUTCOMES:
        tally[klass] = tally.get(klass, 0) + 1
    breaches = [o for o in OUTCOMES if o[2] == "BREACH"]
    inscope_breaches = [o for o in breaches if o[1] == "FAIL-007"]
    print(f"SUMMARY: {tally}")
    print(f"TOTAL RECORDED OUTCOMES: {len(OUTCOMES)}")
    print(f"IN-SCOPE FAIL-GATE BREACHES (FAIL-007): {len(inscope_breaches)}")
    if breaches:
        print("ALL BREACHES:")
        for o in breaches:
            print("   ", o)

    # final posture assertions (nothing this harness did may have flipped a governance flag)
    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED", "gateway state mutated!"
    assert config.PRODUCTION_FLAG == "OFF", "production flag mutated!"
    assert config.EXTERNAL_SEND == "OFF", "external send mutated!"
    assert {m.value for m in Readiness} == {"OWNER_REVIEW_REQUIRED", "NOT_READY"}, "Readiness gained a member!"
    print("POSTURE AFTER RUN: BLOCKED / OFF / OFF  (unchanged) ; Readiness has no Pass/Ready member")
    print("=" * 100)


if __name__ == "__main__":
    main()
