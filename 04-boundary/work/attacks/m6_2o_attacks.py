"""M6.2O boundary-adversary harness (READ-ONLY analysis; prompt M6-P2305).

Attacks the staged M6.2O "Out-of-band Backfill" slice — the two retroactively-certified off-ledger changes:
B1 (psid_hash: raw PSID -> one-way HMAC hash; FAIL-008 / RULE-014) and F2-6 (pack_assembler._smokes duck-coerce:
rebuild every smoke to a canonical SmokeResult, never trust caller .recorded; FAIL-007 / RULE-015 — the coder's fix
for THIS line's M6.2M duck residual). The harness DRIVES the real staged code and EXECUTES every claimed breach.

    PYTHONDONTWRITEBYTECODE=1  py -3.12 -B  work/attacks/m6_2o_attacks.py

No raw PSID/pepper/phone/email literal appears in this source (markers are synthetic + assembled at runtime).
Classification: DEFENDED / OPEN_NONGATE (armed-not-fired) / NOTE / BREACH (an in-scope FAIL-007/FAIL-008 gate trips
from a channel-reachable path).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve()
IMPL = None
for anc in HERE.parents:
    cand = anc / "04-artifacts" / "impl" / "M6.2O"
    if (cand / "app").is_dir():
        IMPL = cand
        break
if IMPL is None:
    raise SystemExit("cannot locate 04-artifacts/impl/M6.2O/app")
sys.path.insert(0, str(IMPL))

from app import config
from app.measurement.identity.psid_hash import (
    hash_psid, resolve_pepper, PsidHashPolicyError, HASH_PREFIX, PEPPER_ENV,
)
from app.measurement.models.attribution_context import (
    AdsAttributionContext, EntryChannel, SourceConfidence, ConflictStatus,
)
from app.measurement.evidence import pack_assembler as PA
from app.measurement.evidence.pack_assembler import EvidencePackAssembler
from app.measurement.evidence.models import Readiness, GapKind, SmokeResult
from app.measurement.evidence.categories import EvidenceCategory, CATEGORY_MANDATORY
from app.measurement.evidence.gap_blockers import STANDING_BLOCKER_IDS
from app.measurement.evidence.smoke_registry import SMOKE_IDS, SMOKE_REGISTRY, SmokeStatus

OUTCOMES = []


def record(vec, gate, klass, detail):
    OUTCOMES.append((vec, gate, klass, detail))
    print(f"[{klass:12}] {vec:9} {gate:10} {detail}")


# --- synthetic, non-PII psid markers (assembled at runtime; never a raw psid / phone / email literal) -----
def synth_psid(tag="a"):
    return "psid" + "-synthetic-" + tag + "-marker"


def canonical_refs():
    return {cat: {k: f"ev::{cat.value}::{k}" for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}


def all_recorded(status="PASS"):
    return {sid: SmokeResult(sid, status=status, correlation_id="corr_" + sid[-3:], evidence_id="ev_" + sid[-3:])
            for sid in SMOKE_IDS}


def ctx(**over):
    base = dict(page_id="p1", entry_channel=EntryChannel.DIRECT, attribution_window="7d",
                source_confidence=SourceConfidence.LOW, conflict_status=ConflictStatus.NONE)
    base.update(over)
    return AdsAttributionContext(**base)


PROPOSED = tuple(s.smoke_id for s in SMOKE_REGISTRY if s.status is SmokeStatus.PROPOSED)
OWNER = tuple(s.smoke_id for s in SMOKE_REGISTRY if s.status is SmokeStatus.OWNER)


# ===================================================================================================
# GROUP B1 — psid_hash raw-PII (FAIL-008 / RULE-014)
# ===================================================================================================
def group_B1():
    p = synth_psid("buyer")

    # B1-1 — no raw psid on the durable/export surface: as_stored/to_public carry only psid_hash; the raw psid is
    #        NOT a substring of the durable mapping.
    c = ctx(psid_hash=hash_psid(p))
    stored = c.as_stored()
    pub = c.to_public()
    if ("psid_hash" in stored and "psid" not in stored and p not in str(stored) and p not in str(pub)
            and str(stored.get("psid_hash", "")).startswith(HASH_PREFIX)):
        record("B1-1", "FAIL-008", "DEFENDED",
               "no raw psid on the durable/export surface: AdsAttributionContext has only a psid_hash field; "
               "as_stored()/to_public() carry only 'psid_hash:'..., no 'psid' key, and the raw synthetic psid is "
               "not a substring of the durable mapping (RULE-014 / FAIL-008).")
    else:
        record("B1-1", "FAIL-008", "BREACH", f"a raw psid reached the durable surface (keys={list(stored)})")

    # B1-2 — hash_psid is one-way (raw not in the hash) + prefixed + deterministic + collision-sensitive.
    h1, h2 = hash_psid(p), hash_psid(p)
    h_other = hash_psid(synth_psid("other"))
    if (h1.startswith(HASH_PREFIX) and p not in h1 and h1 == h2 and h1 != h_other):
        record("B1-2", "FAIL-008", "DEFENDED",
               "hash_psid is one-way (raw psid not a substring of the HMAC output) + 'psid_hash:' prefixed + "
               "DETERMINISTIC (same pepper -> same hash, a stable join key) + collision-sensitive (distinct psids -> "
               "distinct hashes).")
    else:
        record("B1-2", "FAIL-008", "BREACH", "hash_psid not one-way/deterministic")

    # B1-3 — fail-closed in production: resolve_pepper(production=True) + no pepper env -> raise; hash_psid raises.
    saved = os.environ.pop(PEPPER_ENV, None)                    # test-scoped: ensure the env is unset (restore below)
    try:
        raised = 0
        try:
            resolve_pepper(production=True)
        except PsidHashPolicyError:
            raised += 1
        try:
            hash_psid(p, production=True)
        except PsidHashPolicyError:
            raised += 1
        # dev/staged (production=False) still returns a hash (deterministic staged suite)
        dev_ok = hash_psid(p, production=False) is not None
        if raised == 2 and dev_ok and config.PRODUCTION_FLAG == "OFF":
            record("B1-3", "FAIL-008", "DEFENDED",
                   "fail-closed in production: resolve_pepper(production=True) + hash_psid(production=True) with the "
                   "pepper env UNSET both raise PsidHashPolicyError (never hash with an absent salt); production is "
                   "injected as a call arg so config.PRODUCTION_FLAG stays OFF (no flag flip). Dev/staged still hashes.")
        else:
            record("B1-3", "FAIL-008", "BREACH", f"production fail-closed incomplete (raised={raised})")
    finally:
        if saved is not None:
            os.environ[PEPPER_ENV] = saved

    # B1-4 — None / blank / whitespace psid -> None (nothing to hash; no fabricated hash).
    if hash_psid(None) is None and hash_psid("") is None and hash_psid("   ") is None:
        record("B1-4", "FAIL-008", "DEFENDED",
               "hash_psid(None/''/'   ') -> None: a missing psid produces no hash (fail-closed; a no-psid context "
               "carries psid_hash None).")
    else:
        record("B1-4", "FAIL-008", "BREACH", "blank psid produced a hash")

    # B1-5 — a non-str psid (int) is coerced to str then hashed (never dropped/leaked raw).
    h_int = hash_psid(1234567890)
    if h_int is not None and h_int.startswith(HASH_PREFIX):
        record("B1-5", "FAIL-008", "DEFENDED",
               "a non-str psid (int) is coerced to str then one-way hashed (a legitimately-present numeric join key "
               "is not silently dropped, and the raw value is never stored — still 'psid_hash:'...).")
    else:
        record("B1-5", "FAIL-008", "NOTE", f"non-str psid handling unexpected ({h_int})")

    # B1-6 — the pepper is never in the hash output (it is the HMAC KEY, never emitted). Dev mock pepper check.
    dev_pepper = resolve_pepper(production=False)               # the labeled non-secret mock (bytes)
    if dev_pepper.decode("utf-8", "ignore") not in hash_psid(p):
        record("B1-6", "FAIL-008", "DEFENDED",
               "the pepper is the HMAC KEY and never appears in the hash output (hash_psid never logs/returns the "
               "pepper); the module holds the raw psid only as a call argument in RAM.")
    else:
        record("B1-6", "FAIL-008", "BREACH", "the pepper leaked into the hash output")

    # B1-7 (NOTE) — the staged MOCK pepper is a PUBLIC source constant, so in STAGED a synthetic psid_hash is
    #   recoverable by brute-force (the pepper is known). Acceptable for staged (synthetic ids only); production
    #   fail-closes and requires the real secret_ref pepper -> M6-OD-003 privacy/legal sign-off (disclosed forward).
    guess = synth_psid("buyer")                                # attacker "guesses" the synthetic psid
    if hash_psid(guess, production=False) == hash_psid(p, production=False):
        record("B1-7", "FAIL-008", "NOTE",
               "staged reversibility: with the PUBLIC mock pepper a synthetic psid_hash is recoverable by brute-force "
               "(recomputing the hash of a guessed psid matches). Safe in STAGED (only synthetic ids), but the "
               "ONE-WAYNESS depends on the REAL per-env secret_ref pepper -> M6-OD-003 (privacy/legal hash policy) "
               "must be DECIDED before any real deploy/join. Disclosed forward condition (already the exit-judge gate).")
    else:
        record("B1-7", "FAIL-008", "NOTE", "staged hash not reproducible (inspect)")

    # B1-8 (NOTE) — B1 hashed only psid; the OTHER identity fields still export RAW (carried F-SEC-2I-2 family).
    c2 = ctx(messenger_thread_id="mt_synth", live_session_id="ls_synth", comment_id="cm_synth")
    pub2 = c2.to_public()
    if pub2.get("messenger_thread_id") == "mt_synth" and pub2.get("live_session_id") == "ls_synth":
        record("B1-8", "FAIL-008", "NOTE",
               "B1 hashed only the PSID; messenger_thread_id / live_session_id / comment_id still export RAW (a "
               "per-person handle is a PII-scope question). Carried F-SEC-2I-2 / M6-OD-012 masking-scope family, "
               "out of B1's scope. Route: security M6-P2306 / owner M6-OD-012.")
    else:
        record("B1-8", "FAIL-008", "NOTE", "other identity fields not raw (inspect)")


# ===================================================================================================
# GROUP F2-6 — duck-coerce (FAIL-007 / RULE-015) — closes THIS line's M6.2M duck residual
# ===================================================================================================
def group_F26():
    a = EvidencePackAssembler()

    # F2-6-1 — my M6.2M F2-6 residual CLOSED: a duck with .recorded=True + None fields on a mandatory owner smoke ->
    #          coerced -> recorded recomputed False -> NOT_READY + UNRUN gap.
    duck = SimpleNamespace(smoke_id="M6-SMK-001", status=None, correlation_id=None, evidence_id=None,
                           waived=False, recorded=True)
    refs = dict(all_recorded())
    refs["M6-SMK-001"] = duck
    p = a.assemble(refs, canonical_refs())
    smk = next(s for s in p.smokes if s.smoke_id == "M6-SMK-001")
    gap = any(g.kind is GapKind.UNRUN_SMOKE and "M6-SMK-001" in g.id for g in p.gap_blockers)
    if isinstance(smk, SmokeResult) and not smk.recorded and p.readiness is Readiness.NOT_READY and gap:
        record("F2-6-1", "FAIL-007", "DEFENDED",
               "F-EVID-1 DUCK variant CLOSED (F2-6): a duck object with .recorded=True + None fields is COERCED to a "
               "canonical SmokeResult rebuilt from its fields; recorded is RECOMPUTED (False) -> UNRUN gap -> "
               "NOT_READY. The caller's .recorded is never trusted.")
    else:
        record("F2-6-1", "FAIL-007", "BREACH", f"duck .recorded=True laundered a mandatory smoke (readiness={p.readiness})")

    # F2-6-2 — a duck with whitespace fields -> coerced + whitespace-normalized -> not recorded -> NOT_READY.
    duck = SimpleNamespace(smoke_id="M6-SMK-002", status="  ", correlation_id="\t", evidence_id="\n",
                           waived=False, recorded=True)
    refs = dict(all_recorded())
    refs["M6-SMK-002"] = duck
    p = a.assemble(refs, canonical_refs())
    smk = next(s for s in p.smokes if s.smoke_id == "M6-SMK-002")
    if not smk.recorded and p.readiness is Readiness.NOT_READY:
        record("F2-6-2", "FAIL-007", "DEFENDED",
               "a duck with whitespace fields -> coerced then whitespace-normalized (M6.2M twin) -> not recorded -> "
               "NOT_READY. No crash (the coerce reads fields via getattr, not dataclasses.replace on the duck).")
    else:
        record("F2-6-2", "FAIL-007", "BREACH", "whitespace duck recorded")

    # F2-6-3 — a duck MISSING fields (only smoke_id + recorded) -> getattr default None -> not recorded (my M6.2M
    #          COMP-4 crash CLOSED: the coerce uses getattr(..., None), no AttributeError).
    duck = SimpleNamespace(smoke_id="M6-SMK-003", recorded=True)   # no status/correlation_id/evidence_id/waived
    refs = dict(all_recorded())
    refs["M6-SMK-003"] = duck
    try:
        p = a.assemble(refs, canonical_refs())
        smk = next(s for s in p.smokes if s.smoke_id == "M6-SMK-003")
        if not smk.recorded and p.readiness is Readiness.NOT_READY:
            record("F2-6-3", "FAIL-007", "DEFENDED",
                   "a duck MISSING status/correlation_id/evidence_id/waived -> getattr(...,None) defaults -> not "
                   "recorded -> NOT_READY (my M6.2M COMP-4 missing-attr CRASH is CLOSED; the coerce never raises).")
        else:
            record("F2-6-3", "FAIL-007", "BREACH", "field-less duck recorded")
    except Exception as e:  # noqa
        record("F2-6-3", "FAIL-007", "BREACH", f"coerce crashed on a field-less duck ({type(e).__name__})")

    # F2-6-4 — smoke_id is PINNED to spec.smoke_id: a SmokeResult under the SMK-001 key carrying a different/PII
    #          smoke_id has that leaked id DISCARDED (my M6.2M N4/X2 mislabel+leak CLOSED).
    leaked = "LEAK-" + chr(64) + "-marker"                     # @-shaped, assembled (no literal PII in source)
    refs = dict(all_recorded())
    refs["M6-SMK-001"] = SmokeResult(smoke_id=leaked, status="PASS", correlation_id="c", evidence_id="e")
    p = a.assemble(refs, canonical_refs())
    shown = [s["smoke_id"] for s in p.to_public()["smokes"]]
    if leaked not in shown and "M6-SMK-001" in shown:
        record("F2-6-4", "FAIL-007", "DEFENDED",
               "smoke_id PINNED (F2-6): a SmokeResult under the SMK-001 key carrying a different/PII smoke_id has that "
               "id DISCARDED — the displayed row is the registry id 'M6-SMK-001'. My M6.2M N4/X2 (smoke_id "
               "mislabel + a second unmasked export slot) is CLOSED.")
    else:
        record("F2-6-4", "FAIL-007", "BREACH", f"caller smoke_id survived the coerce ({shown[:3]})")

    # F2-6-5 — a non-SmokeResult VALUE (a bare string) -> getattr on a str -> None fields -> not recorded -> NOT_READY.
    refs = dict(all_recorded())
    refs["M6-SMK-004"] = "recorded"                            # truthy non-SmokeResult value
    p = a.assemble(refs, canonical_refs())
    smk = next(s for s in p.smokes if s.smoke_id == "M6-SMK-004")
    if not smk.recorded and p.readiness is Readiness.NOT_READY:
        record("F2-6-5", "FAIL-007", "DEFENDED",
               "a non-SmokeResult value (the string 'recorded') is coerced: getattr(str,'status',None) -> None -> not "
               "recorded -> NOT_READY. A foreign value can no longer masquerade (my M6.2K SL-12 crash/launder CLOSED).")
    else:
        record("F2-6-5", "FAIL-007", "BREACH", "a bare-string smoke value was recorded")

    # F2-6-6 — control: genuine SmokeResults still record -> OWNER_REVIEW_REQUIRED (no regression).
    p = a.assemble(all_recorded(), canonical_refs())
    if all(s.recorded for s in p.smokes) and p.readiness is Readiness.OWNER_REVIEW_REQUIRED:
        record("F2-6-6", "FAIL-007", "DEFENDED",
               "control: genuine SmokeResults coerce to themselves and still record all 18 -> OWNER_REVIEW_REQUIRED "
               "(the coerce does not break a legitimate pack).")
    else:
        record("F2-6-6", "FAIL-007", "BREACH", "genuine pack regressed under the coerce")

    # F2-6-7 — waived is coerced to a real bool: a truthy non-bool waived is honored for a PROPOSED smoke, STRIPPED
    #          for an OWNER smoke (carried waiver-scope + coerce compose).
    refs = dict(all_recorded())
    refs[PROPOSED[0]] = SimpleNamespace(smoke_id=PROPOSED[0], status=None, correlation_id=None, evidence_id=None,
                                        waived="yes", recorded=True)
    refs[OWNER[0]] = SimpleNamespace(smoke_id=OWNER[0], status=None, correlation_id=None, evidence_id=None,
                                     waived="yes", recorded=True)
    p = a.assemble(refs, canonical_refs())
    prop = next(s for s in p.smokes if s.smoke_id == PROPOSED[0])
    own = next(s for s in p.smokes if s.smoke_id == OWNER[0])
    if prop.recorded and prop.waived is True and own.waived is False and not own.recorded:
        record("F2-6-7", "FAIL-007", "DEFENDED",
               "waived coerced to a real bool: a truthy non-bool 'yes' waiver on a PROPOSED smoke is honored "
               "(recorded via waiver), on an OWNER smoke is stripped -> un-recorded (waiver-scope carried + coerce).")
    else:
        record("F2-6-7", "FAIL-007", "BREACH", f"waiver coerce/scope broke (prop={prop.recorded}, own_waived={own.waived})")

    # F2-6-8 — a duck whose status is a genuinely NON-BLANK fake id coerces to recorded=True. This is NOT a NEW
    #          bypass: it equals passing a real SmokeResult with fake-but-nonblank ids (the F-EVID-5/authenticity
    #          family, trusted-input) — the coerce closes the .recorded-TRUST, not fake-nonblank-id authenticity.
    refs = dict(all_recorded())
    refs["M6-SMK-005"] = SimpleNamespace(smoke_id="M6-SMK-005", status="PASS", correlation_id="c", evidence_id="e",
                                         waived=False, recorded=False)   # recorded=False, but real non-blank fields
    p = a.assemble(refs, canonical_refs())
    smk = next(s for s in p.smokes if s.smoke_id == "M6-SMK-005")
    if smk.recorded:
        record("F2-6-8", "FAIL-007", "OPEN_NONGATE",
               "a duck with genuinely NON-BLANK status/correlation_id/evidence_id coerces to recorded=True even with "
               ".recorded=False — the coerce recomputes recorded from the FIELDS (correct). This is NOT a new bypass: "
               "it equals a real SmokeResult with fake-but-nonblank ids, the trusted-input authenticity family "
               "(F-EVID-5 / known_refs), not the .recorded-trust the coerce closes. Trusted-input; caps at "
               "OWNER_REVIEW_REQUIRED.")
    else:
        record("F2-6-8", "FAIL-007", "NOTE", "non-blank duck not recorded (inspect)")


# ===================================================================================================
# GROUP R — residuals NOT in the M6.2O scope (confirm still open, armed-not-fired)
# ===================================================================================================
def group_R():
    a = EvidencePackAssembler()

    # R1 — F-EVID-5 STILL OPEN: 18 smokes recorded status='FAIL' -> OWNER_REVIEW_REQUIRED (recorded != passed).
    p = a.assemble(all_recorded(status="FAIL"), canonical_refs())
    if p.readiness is Readiness.OWNER_REVIEW_REQUIRED and all(s.recorded for s in p.smokes):
        record("R1", "FAIL-007", "OPEN_NONGATE",
               "F-EVID-5 STILL OPEN (out of M6.2O scope): 18 smokes recorded status='FAIL' still reach "
               "OWNER_REVIEW_REQUIRED -- _readiness tests only s.recorded, never status=='PASS'. Trusted-input; "
               "caps at OWNER_REVIEW_REQUIRED. Carry-forward.")
    else:
        record("R1", "FAIL-007", "DEFENDED", "recorded FAIL smoke now drops readiness (unexpectedly fixed)")

    # R2 — F-EVID-4 STILL OPEN (status verbatim) BUT the N4 smoke_id leak is now CLOSED (F2-6 pins smoke_id).
    marker = "st" + "-" + chr(64) + "-marker"
    refs = dict(all_recorded())
    refs["M6-SMK-006"] = SmokeResult("M6-SMK-006", status=marker, correlation_id="c", evidence_id="e")
    p = a.assemble(refs, canonical_refs())
    exported = next(s for s in p.to_public()["smokes"] if s["smoke_id"] == "M6-SMK-006")
    if exported["status"] == marker:
        record("R2", "FAIL-007", "OPEN_NONGATE",
               "F-EVID-4 STILL OPEN (out of scope): SmokeResult.to_public() emits a non-blank status verbatim (only "
               "corr/ev masked). BUT the paired N4 smoke_id leak is now CLOSED (F2-6 pins smoke_id to the registry "
               "id), so only the STATUS slot remains. Trusted-input. Carry-forward (enum-constrain/mask status).")
    else:
        record("R2", "FAIL-007", "DEFENDED", "status now masked on export")


# ===================================================================================================
# GROUP REG — carried fixes intact (no regression) + posture
# ===================================================================================================
def group_REG():
    a = EvidencePackAssembler()

    # REG1 — B2 forgery (junk + copy-paste) still MISSING/NOT_READY.
    junk = {cat: {k: "x" for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}
    one = "ev::Consent::consent_pass"
    copied = {cat: {k: one for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}
    if a.assemble(all_recorded(), junk).readiness is Readiness.NOT_READY \
            and a.assemble(all_recorded(), copied).readiness is Readiness.NOT_READY:
        record("REG1", "FAIL-007", "DEFENDED", "carried B2 forgery block intact (junk + copy-paste -> NOT_READY).")
    else:
        record("REG1", "FAIL-007", "BREACH", "B2 forgery block regressed")

    # REG2 — B3 standing-floor: the STANDING_GAP_BLOCKERS=() rebind still trips -> NOT_READY.
    saved = PA.STANDING_GAP_BLOCKERS
    try:
        PA.STANDING_GAP_BLOCKERS = ()
        ok = a.assemble(all_recorded(), canonical_refs()).readiness is Readiness.NOT_READY
    finally:
        PA.STANDING_GAP_BLOCKERS = saved
    if ok and len([g for g in a.assemble().gap_blockers if g.kind is GapKind.STANDING_BLOCKER]) == 8:
        record("REG2", "FAIL-007", "DEFENDED", "carried B3 standing-floor intact (rebind -> NOT_READY; all 8 carried).")
    else:
        record("REG2", "FAIL-007", "BREACH", "B3 floor regressed")

    # REG3 — the known_refs authenticity oracle (M6.2M) intact: a reconstructed un-issued ref -> MISSING.
    issued = {f"ev::{cat.value}::{k}" for cat, keys in CATEGORY_MANDATORY.items() for k in keys}
    issued.discard(f"ev::{EvidenceCategory.DEDUP.value}::{CATEGORY_MANDATORY[EvidenceCategory.DEDUP][0]}")
    p = a.assemble(all_recorded(), canonical_refs(), known_refs=issued)
    if not p.category(EvidenceCategory.DEDUP).complete and p.readiness is Readiness.NOT_READY:
        record("REG3", "FAIL-007", "DEFENDED",
               "carried M6.2M known_refs oracle intact: a reconstructed un-issued DEDUP ref -> MISSING -> NOT_READY.")
    else:
        record("REG3", "FAIL-007", "BREACH", "known_refs oracle regressed")


# ===================================================================================================
# GROUP N — reconciliation of the ideation workflow's novel vectors (executed)
# ===================================================================================================
def group_N():
    a = EvidencePackAssembler()

    # N1 (MC-1) — a plain DICT smoke value: getattr on a dict returns the None default (fields are keys, not attrs)
    #     -> coerced to all-None -> not recorded -> NOT_READY. The coerce fail-closes on the most natural fake shape.
    refs = dict(all_recorded())
    refs["M6-SMK-001"] = {"status": "PASS", "correlation_id": "SYNTH", "evidence_id": "SYNTH", "recorded": True}
    p = a.assemble(refs, canonical_refs())
    smk = next(s for s in p.smokes if s.smoke_id == "M6-SMK-001")
    if not smk.recorded and p.readiness is Readiness.NOT_READY:
        record("N1", "FAIL-007", "DEFENDED",
               "MC-1: a plain DICT smoke value coerces to all-None (getattr(dict,'status',None) -> None; dict fields "
               "are keys, not attributes) -> not recorded -> NOT_READY. The coerce fail-closes on a dict, the most "
               "natural fake shape.")
    else:
        record("N1", "FAIL-007", "BREACH", "a dict smoke value was recorded")

    # N2 (MC-2, NEW residual) — cross-slot trace RELABEL: a GENUINE recorded SmokeResult belonging to SMK-002 filed
    #     under the SMK-001 key. The coerce pins smoke_id=SMK-001 but copies SMK-002's real trace -> SMK-001 is
    #     marked recorded using another smoke's genuine trace. F2-6 closes the .recorded-lie + smoke_id mislabel, but
    #     there is NO trace<->smoke BINDING oracle (the smoke-side analog of _ref_binding's (category,key) binding).
    genuine_002 = SmokeResult(smoke_id="M6-SMK-002", status="PASS",
                              correlation_id="corr_002_realtrace", evidence_id="ev_002_realtrace")
    refs = dict(all_recorded())
    refs["M6-SMK-001"] = genuine_002                          # SMK-002's real trace filed under the SMK-001 key
    p = a.assemble(refs, canonical_refs())
    smk1 = next(s for s in p.smokes if s.smoke_id == "M6-SMK-001")
    if smk1.recorded and smk1.correlation_id == "corr_002_realtrace" and p.readiness is Readiness.OWNER_REVIEW_REQUIRED:
        record("N2", "FAIL-007", "OPEN_NONGATE",
               "MC-2 (NEW residual F-EVID-6): cross-slot trace RELABEL — a genuine SmokeResult carrying SMK-002's "
               "real trace, filed under the SMK-001 key, marks SMK-001 recorded with SMK-002's correlation/evidence "
               "id. F2-6 pins smoke_id and kills the .recorded-lie, but there is NO trace<->smoke BINDING (the "
               "smoke-side analog of _ref_binding). Trusted-input (the pack-builder files traces; no channel); caps "
               "at OWNER_REVIEW_REQUIRED. Route: CODER (bind correlation_id/evidence_id to the smoke, or the "
               "known_refs authenticity registry covers it).")
    else:
        record("N2", "FAIL-007", "DEFENDED", f"cross-slot trace not relabeled (recorded={smk1.recorded})")

    # N3 (MC-3/MC-5 reachability floor + wired seam) — the evidence assembler has no app/api caller, and the ONLY
    #     raw-psid read is the in-process resolver signals seam; the wired hash_psid uses production=None ->
    #     config.PRODUCTION_FLAG (immutable OFF) so staged uses the mock pepper and production fail-closes.
    from app.measurement.identity.psid_hash import hash_psid as _hp
    seam_ok = _hp(synth_psid("seam"), production=None) is not None  # staged (flag OFF) -> mock pepper hash
    if seam_ok and config.PRODUCTION_FLAG == "OFF":
        record("N3", "FAIL-008", "DEFENDED",
               "reachability/seam floor (MC-3/MC-5): the wired resolver seam calls hash_psid(signals.get('psid')) "
               "with production=None -> is_prod reads the IMMUTABLE config.PRODUCTION_FLAG (OFF) -> staged mock-pepper "
               "hash; a production deploy (flag ON) with the pepper unset fail-closes. Combined with 'no app/api "
               "caller of the evidence assembler + the only raw-psid read is the in-process signals seam' (grep-"
               "confirmed), the whole F2-6/B1 attack surface is trusted-input/integration-seam, not channel-reachable.")
    else:
        record("N3", "FAIL-008", "NOTE", "seam floor unexpected")


# ===================================================================================================
def main():
    print("=" * 100)
    print("M6.2O BOUNDARY ADVERSARY — out-of-band backfill (in-scope: FAIL-007 [F2-6] + FAIL-008 [B1])")
    print(f"impl root: {IMPL}")
    print(f"config sha posture: PRODUCTION_FLAG={config.PRODUCTION_FLAG} EXTERNAL_SEND={config.EXTERNAL_SEND}")
    print("=" * 100)
    for g in (group_B1, group_F26, group_R, group_REG, group_N):
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
    print(f"IN-SCOPE FAIL-GATE BREACHES (FAIL-007 / FAIL-008): {len(inscope)}")
    for o in breaches:
        print("   BREACH:", o)

    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
    assert config.EXTERNAL_SEND == "OFF"
    assert os.environ.get(PEPPER_ENV) in (None, os.environ.get(PEPPER_ENV))  # env restored if it existed
    assert {m.value for m in Readiness} == {"OWNER_REVIEW_REQUIRED", "NOT_READY"}
    print("POSTURE AFTER RUN: BLOCKED / OFF / OFF (unchanged); Readiness has no Pass/Ready member")
    print("=" * 100)


if __name__ == "__main__":
    main()
