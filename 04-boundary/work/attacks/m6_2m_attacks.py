"""M6.2M boundary-adversary harness (READ-ONLY analysis; prompt M6-P2205).

Attacks the staged M6.2M "Evidence Authenticity (M6-OD-013)" slice — the twin fixes that close the M6-OD-013
authenticity residual THIS boundary line raised at M6.2L: FIX-1 (ref-side known_refs oracle) + FIX-2 (smoke-side
stripped-non-blank SmokeResult.recorded). In-scope fail gate: M6-FAIL-007 (no-evidence / overstated readiness);
in-scope rule RULE-015. The harness DRIVES the real staged code and EXECUTES every claimed breach before recording.

    PYTHONDONTWRITEBYTECODE=1  py -3.12 -B  work/attacks/m6_2m_attacks.py

Classification: DEFENDED / OPEN_NONGATE (armed-not-fired) / NOTE / BREACH (an in-scope FAIL-007 gate trips from a
channel-reachable path).
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve()
IMPL = None
for anc in HERE.parents:
    cand = anc / "04-artifacts" / "impl" / "M6.2M"
    if (cand / "app").is_dir():
        IMPL = cand
        break
if IMPL is None:
    raise SystemExit("cannot locate 04-artifacts/impl/M6.2M/app")
sys.path.insert(0, str(IMPL))

from datetime import datetime, timezone

from app import config
from app.measurement.evidence import pack_assembler as PA
from app.measurement.evidence.pack_assembler import EvidencePackAssembler
from app.measurement.evidence.models import Readiness, GapKind, SmokeResult, _nonblank
from app.measurement.evidence.categories import EvidenceCategory, CATEGORY_MANDATORY
from app.measurement.evidence.gap_blockers import STANDING_BLOCKER_IDS
from app.measurement.evidence.smoke_registry import SMOKE_IDS, SMOKE_REGISTRY, SmokeStatus

FIXED_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
OUTCOMES = []


def record(vec, gate, klass, detail):
    OUTCOMES.append((vec, gate, klass, detail))
    print(f"[{klass:12}] {vec:8} {gate:10} {detail}")


def canonical_refs():
    return {cat: {k: f"ev::{cat.value}::{k}" for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}


def all_issued():
    out = set()
    for cat, keys in CATEGORY_MANDATORY.items():
        for k in keys:
            out.add(f"ev::{cat.value}::{k}")
    return out


def all_recorded(status="PASS"):
    return {sid: SmokeResult(sid, status=status, correlation_id="corr_" + sid[-3:], evidence_id="ev_" + sid[-3:])
            for sid in SMOKE_IDS}


PROPOSED = tuple(s.smoke_id for s in SMOKE_REGISTRY if s.status is SmokeStatus.PROPOSED)
OWNER = tuple(s.smoke_id for s in SMOKE_REGISTRY if s.status is SmokeStatus.OWNER)


# ===================================================================================================
# GROUP F1 — ref-side authenticity (FAIL-007 / M6-OD-013): the known_refs oracle
# ===================================================================================================
def group_F1():
    a = EvidencePackAssembler()

    # F1-1 — control: a fully-ISSUED allowlist -> all COMPLETE -> OWNER_REVIEW_REQUIRED (discriminating, non-vacuous).
    p = a.assemble(all_recorded(), canonical_refs(), known_refs=all_issued())
    if all(c.complete for c in p.categories) and p.readiness is Readiness.OWNER_REVIEW_REQUIRED:
        record("F1-1", "FAIL-007", "DEFENDED",
               "control: a fully-issued known_refs allowlist -> every category COMPLETE -> OWNER_REVIEW_REQUIRED "
               "(the oracle is discriminating, not vacuous).")
    else:
        record("F1-1", "FAIL-007", "BREACH", "issued allowlist did not complete the pack")

    # F1-2 — M6-OD-013 CLOSED (oracle wired): a reconstructed canonical ref NOT in the allowlist -> MISSING.
    issued = all_issued()
    dedup_ref = f"ev::{EvidenceCategory.DEDUP.value}::{CATEGORY_MANDATORY[EvidenceCategory.DEDUP][0]}"
    issued.discard(dedup_ref)                                   # omit the DEDUP slot's ref from the registry
    p = a.assemble(all_recorded(), canonical_refs(), known_refs=issued)
    dedup = p.category(EvidenceCategory.DEDUP)
    others_ok = all(c.complete for c in p.categories if c.category is not EvidenceCategory.DEDUP)
    if not dedup.complete and others_ok and p.readiness is Readiness.NOT_READY:
        record("F1-2", "FAIL-007", "DEFENDED",
               "M6-OD-013 CLOSED (oracle wired): a correctly-RECONSTRUCTED canonical DEDUP ref that was never issued "
               "(not in the allowlist) is REJECTED -> DEDUP MISSING -> NOT_READY, while every issued-ref category is "
               "COMPLETE. Canonical-string reconstruction can no longer forge COMPLETE when the allowlist is passed.")
    else:
        record("F1-2", "FAIL-007", "BREACH", f"an un-issued reconstructed ref completed DEDUP (readiness={p.readiness})")

    # F1-3 — the honest REMAINING residual: with NO allowlist, canonical reconstruction still passes (slot-correctness
    #        only). Authenticity requires the owner to POPULATE + PASS the real issued-refs registry (integration).
    p = a.assemble(all_recorded(), canonical_refs())            # no known_refs
    if all(c.complete for c in p.categories) and p.readiness is Readiness.OWNER_REVIEW_REQUIRED:
        record("F1-3", "FAIL-007", "OPEN_NONGATE",
               "default path (no allowlist): a canonical reconstruction still passes (M6.2L slot-correctness bar). "
               "The AUTHENTICITY MECHANISM is proven (F1-2), but proving it in production needs the owner to populate "
               "the real issued-refs registry AND pass it as known_refs -- the disclosed owner-integration seam "
               "(M6-OD-013). Trusted-input (PM authors refs); the pack still caps at OWNER_REVIEW_REQUIRED, no Pass.")
    else:
        record("F1-3", "FAIL-007", "DEFENDED", "default-path reconstruction did not complete the pack")

    # F1-4 — hostile allowlist whose __contains__ returns True for everything -> the oracle is defeated by a bad
    #        registry. Trusted-input / code-exec only (the owner supplies known_refs).
    class _AllIn:
        def __contains__(self, x):
            return True
    p = a.assemble(all_recorded(), canonical_refs(), known_refs=_AllIn())
    if all(c.complete for c in p.categories):
        record("F1-4", "FAIL-007", "OPEN_NONGATE",
               "a hostile known_refs whose __contains__ returns True defeats the oracle (any convention-shaped ref "
               "passes). Trusted-input / code-exec only: known_refs is the owner-supplied registry, not channel input. "
               "Route: owner integration must pass a real set/frozenset of issued refs (carried B2-7).")
    else:
        record("F1-4", "FAIL-007", "DEFENDED", "hostile allowlist did not universally pass")

    # F1-5 — an EMPTY allowlist rejects everything -> all MISSING -> NOT_READY (fail-closed).
    p = a.assemble(all_recorded(), canonical_refs(), known_refs=set())
    if all(not c.complete for c in p.categories) and p.readiness is Readiness.NOT_READY:
        record("F1-5", "FAIL-007", "DEFENDED",
               "an empty allowlist rejects every ref (nothing issued) -> all categories MISSING -> NOT_READY "
               "(fail-closed; the oracle never fails OPEN).")
    else:
        record("F1-5", "FAIL-007", "BREACH", "empty allowlist did not fail closed")

    # F1-6 — allowlist entries are compared against the STRIPPED provided ref (r=ref.strip()); a WHITESPACE-PADDED
    #        allowlist entry does NOT match a clean canonical ref -> MISSING (fail-closed, conservative). Note only.
    issued_padded = {f"  {r}  " for r in all_issued()}         # padded registry entries
    p = a.assemble(all_recorded(), canonical_refs(), known_refs=issued_padded)
    if all(not c.complete for c in p.categories):
        record("F1-6", "FAIL-007", "NOTE",
               "the oracle strips the PROVIDED ref (r=ref.strip()) but not the ALLOWLIST entries, so a "
               "whitespace-padded registry entry fails to match a clean canonical ref -> MISSING (fail-closed, "
               "conservative). The owner registry must store canonical un-padded refs; a padded entry only "
               "under-states readiness, never over-states. Not a breach.")
    else:
        record("F1-6", "FAIL-007", "NOTE", "padded allowlist unexpectedly matched (inspect)")


# ===================================================================================================
# GROUP F2 — smoke-side authenticity (FAIL-007): stripped-non-blank recorded (closes F-EVID-1 whitespace)
# ===================================================================================================
def group_F2():
    a = EvidencePackAssembler()

    # F2-1 — F-EVID-1 WHITESPACE CLOSED: a whitespace status/corr/ev on a mandatory smoke -> recorded False ->
    #        NOT_READY + UNRUN gap.
    refs = dict(all_recorded())
    refs["M6-SMK-001"] = SmokeResult("M6-SMK-001", status="  ", correlation_id="\t", evidence_id="\n")
    p = a.assemble(refs, canonical_refs())
    smk = next(s for s in p.smokes if s.smoke_id == "M6-SMK-001")
    gap = any(g.kind is GapKind.UNRUN_SMOKE and "M6-SMK-001" in g.id for g in p.gap_blockers)
    if not smk.recorded and p.readiness is Readiness.NOT_READY and gap:
        record("F2-1", "FAIL-007", "DEFENDED",
               "F-EVID-1 WHITESPACE CLOSED: a SmokeResult with whitespace/tab/newline status/correlation_id/"
               "evidence_id is NOT recorded (_nonblank: stripped-non-blank required, not bool() truthiness) -> "
               "UNRUN:M6-SMK-001 gap -> NOT_READY.")
    else:
        record("F2-1", "FAIL-007", "BREACH", f"whitespace smoke recorded (recorded={smk.recorded})")

    # F2-2 — a PARTIAL blank (one whitespace field of three) -> recorded False.
    refs = dict(all_recorded())
    refs["M6-SMK-002"] = SmokeResult("M6-SMK-002", status="PASS", correlation_id="  ", evidence_id="e")
    p = a.assemble(refs, canonical_refs())
    smk = next(s for s in p.smokes if s.smoke_id == "M6-SMK-002")
    if not smk.recorded and p.readiness is Readiness.NOT_READY:
        record("F2-2", "FAIL-007", "DEFENDED",
               "a partial blank (one whitespace field of three) -> recorded False -> NOT_READY (all three fields "
               "must be stripped-non-blank).")
    else:
        record("F2-2", "FAIL-007", "BREACH", "partial-blank smoke recorded")

    # F2-3 — non-string fields (int / None / object) -> recorded False (_nonblank isinstance check).
    bad = 0
    for s, c, e in ((123, "c", "e"), ("PASS", None, "e"), ("PASS", "c", object())):
        refs = dict(all_recorded())
        refs["M6-SMK-003"] = SmokeResult("M6-SMK-003", status=s, correlation_id=c, evidence_id=e)
        smk = next(x for x in a.assemble(refs, canonical_refs()).smokes if x.smoke_id == "M6-SMK-003")
        if not smk.recorded:
            bad += 1
    if bad == 3:
        record("F2-3", "FAIL-007", "DEFENDED",
               "non-string status/correlation_id/evidence_id (int / None / object) -> recorded False (_nonblank "
               "requires isinstance(str)); a non-string field cannot masquerade as a run trace.")
    else:
        record("F2-3", "FAIL-007", "BREACH", f"a non-string field was recorded ({3 - bad} leaked)")

    # F2-4 — _smokes NORMALIZES whitespace fields to None (nothing masquerades on export).
    refs = dict(all_recorded())
    refs["M6-SMK-004"] = SmokeResult("M6-SMK-004", status="   ", correlation_id="c", evidence_id="e")
    p = a.assemble(refs, canonical_refs())
    exported = next(s for s in p.to_public()["smokes"] if s["smoke_id"] == "M6-SMK-004")
    if exported["status"] is None and exported["recorded"] is False:
        record("F2-4", "FAIL-007", "DEFENDED",
               "_smokes normalizes a whitespace-only status to None -> to_public shows status None + recorded False; "
               "a fake-but-blank field cannot masquerade downstream.")
    else:
        record("F2-4", "FAIL-007", "NOTE", f"whitespace-normalize unexpected (status={exported['status']!r})")

    # F2-5 — control: genuine non-blank ids still record (no regression).
    p = a.assemble(all_recorded(), canonical_refs())
    if all(s.recorded for s in p.smokes) and p.readiness is Readiness.OWNER_REVIEW_REQUIRED:
        record("F2-5", "FAIL-007", "DEFENDED",
               "control: genuine non-blank status/correlation_id/evidence_id still record all 18 smokes -> "
               "OWNER_REVIEW_REQUIRED (the tightening does not break a legitimate pack).")
    else:
        record("F2-5", "FAIL-007", "BREACH", "genuine recorded pack regressed")

    # F2-6 — DUCK-TYPED object with recorded=True (no real ids) on a mandatory slot: does _smokes still trust it?
    duck = SimpleNamespace(smoke_id="M6-SMK-005", status=None, correlation_id=None, evidence_id=None,
                           waived=False, recorded=True)
    refs = dict(all_recorded())
    refs["M6-SMK-005"] = duck
    try:
        p = a.assemble(refs, canonical_refs())
        smk = next(s for s in p.smokes if getattr(s, "smoke_id", None) == "M6-SMK-005")
        if getattr(smk, "recorded", False) and p.readiness is Readiness.OWNER_REVIEW_REQUIRED:
            record("F2-6", "FAIL-007", "OPEN_NONGATE",
                   "F-EVID-1 DUCK variant STILL OPEN (out of M6.2M scope): a duck-typed object (SimpleNamespace) "
                   "with recorded=True, waived=False and None string fields is trusted -- _smokes reads result."
                   "recorded and only normalizes whitespace STRING fields (None fields are skipped), so it launders "
                   "SMK-005 as recorded. Trusted-input only (smoke_results is TESTER-built SmokeResults; no channel "
                   "supplies objects). M6.2M closed the WHITESPACE-field twin, not the duck-TYPE variant. Route: "
                   "CODER (type-check the value is a real SmokeResult / reconstruct via SmokeResult(**fields)).")
        else:
            record("F2-6", "FAIL-007", "DEFENDED", "duck-typed recorded=True object not honored")
    except Exception as e:  # noqa
        record("F2-6", "FAIL-007", "DEFENDED", f"duck-typed object rejected ({type(e).__name__}) -> fail-closed")

    # F2-7 — a duck WITH a whitespace string field triggers _smokes' replace() on a non-dataclass -> crash =
    #        fail-closed (no pack emitted, nothing overstated).
    duck2 = SimpleNamespace(smoke_id="M6-SMK-006", status="  ", correlation_id="c", evidence_id="e",
                            waived=False, recorded=True)
    refs = dict(all_recorded())
    refs["M6-SMK-006"] = duck2
    try:
        a.assemble(refs, canonical_refs())
        record("F2-7", "FAIL-007", "NOTE", "duck with whitespace field did not crash (inspect)")
    except Exception as e:  # noqa
        record("F2-7", "FAIL-007", "OPEN_NONGATE",
               f"a duck-typed object WITH a whitespace field makes _smokes call dataclasses.replace() on a "
               f"non-dataclass -> {type(e).__name__} (fail-closed-by-crash; no overstated pack). Trusted-input; "
               "robustness gap (coerce/validate the value).")

    # F2-8 — the proposed-smoke waiver still records (no regression); an owner-smoke waiver is still STRIPPED.
    refs = dict(all_recorded())
    refs[PROPOSED[0]] = SmokeResult(PROPOSED[0], status=None, correlation_id=None, evidence_id=None, waived=True)
    refs[OWNER[0]] = SmokeResult(OWNER[0], status=None, correlation_id=None, evidence_id=None, waived=True)
    p = a.assemble(refs, canonical_refs())
    prop = next(s for s in p.smokes if s.smoke_id == PROPOSED[0])
    own = next(s for s in p.smokes if s.smoke_id == OWNER[0])
    if prop.recorded and prop.waived and (own.waived is False and own.recorded is False) \
            and p.readiness is Readiness.NOT_READY:
        record("F2-8", "FAIL-007", "DEFENDED",
               "carried waiver rules intact: a PROPOSED smoke waiver still records (no ids needed); an OWNER-smoke "
               "waiver is still STRIPPED -> un-recorded -> NOT_READY (M6.2K fix carried unchanged).")
    else:
        record("F2-8", "FAIL-007", "BREACH", f"waiver rules regressed (prop={prop.recorded}, own_waived={own.waived})")


# ===================================================================================================
# GROUP R — residuals NOT in the M6.2M scope (confirm still open, armed-not-fired) + the compound
# ===================================================================================================
def group_R():
    a = EvidencePackAssembler()

    # R1 — F-EVID-5 STILL OPEN: 18 smokes recorded status='FAIL' (genuine non-blank ids) -> OWNER_REVIEW_REQUIRED.
    p = a.assemble(all_recorded(status="FAIL"), canonical_refs())
    if p.readiness is Readiness.OWNER_REVIEW_REQUIRED and all(s.recorded for s in p.smokes):
        record("R1", "FAIL-007", "OPEN_NONGATE",
               "F-EVID-5 STILL OPEN (out of M6.2M scope): 18 smokes recorded status='FAIL' (genuine non-blank ids) "
               "still reach OWNER_REVIEW_REQUIRED -- _readiness tests only s.recorded, never status=='PASS'. "
               "Trusted-input; caps at OWNER_REVIEW_REQUIRED. Carry-forward (add a status=='PASS' gate).")
    else:
        record("R1", "FAIL-007", "DEFENDED", "recorded FAIL smoke now drops readiness (unexpectedly fixed)")

    # R2 — F-EVID-4 STILL OPEN: a genuine non-blank status carrying a PII marker is exported verbatim (only corr/ev
    #      masked). _smokes normalizes only WHITESPACE, so a non-blank PII status survives.
    marker = "st" + "-" + chr(64) + "-marker"                  # @-shaped, assembled (no literal PII in source)
    refs = dict(all_recorded())
    refs["M6-SMK-007"] = SmokeResult("M6-SMK-007", status=marker, correlation_id="c", evidence_id="e")
    p = a.assemble(refs, canonical_refs())
    exported = next(s for s in p.to_public()["smokes"] if s["smoke_id"] == "M6-SMK-007")
    if exported["status"] == marker:
        record("R2", "FAIL-007", "OPEN_NONGATE",
               "F-EVID-4 STILL OPEN (out of scope): SmokeResult.to_public() emits a genuine non-blank status "
               "verbatim (only correlation/evidence ids masked); _smokes normalizes only WHITESPACE, so a non-blank "
               "PII status survives. Trusted-input (TESTER sets PASS/FAIL). Carry-forward (enum-constrain/mask status).")
    else:
        record("R2", "FAIL-007", "DEFENDED", "status now masked/constrained on export")

    # R3 — the COMPOUND: default-path canonical reconstruction (all COMPLETE) + 18 genuine-non-blank FAIL smokes ->
    #      OWNER_REVIEW_REQUIRED on a fully-forged base. Closure needs BOTH the owner allowlist AND a status==PASS gate.
    p = a.assemble(all_recorded(status="FAIL"), canonical_refs())
    standing = {g.id for g in p.gap_blockers if g.kind is GapKind.STANDING_BLOCKER}
    if p.readiness is Readiness.OWNER_REVIEW_REQUIRED and standing == set(STANDING_BLOCKER_IDS) \
            and p.posture["production_flag"] == "OFF":
        record("R3", "FAIL-007", "OPEN_NONGATE",
               "compound (carried from M6.2L N3): default-path canonical-reconstructed refs (M6-OD-013 owner-seam) + "
               "18 genuine-non-blank FAIL smokes (F-EVID-5) -> OWNER_REVIEW_REQUIRED on a forged base. STILL caps at "
               "OWNER_REVIEW_REQUIRED (no Pass), discloses all 8 standing blockers + BLOCKED posture. Closure needs "
               "BOTH the owner-populated allowlist (F1-2 proves the mechanism) AND a status=='PASS' gate (F-EVID-5). "
               "Trusted-input; not channel-reachable. Route: owner (M6-OD-013) + CODER (F-EVID-5).")
    else:
        record("R3", "FAIL-007", "DEFENDED", f"compound did not reach OWNER_REVIEW_REQUIRED ({p.readiness})")


# ===================================================================================================
# GROUP REG — carried M6.2L/M6.2K fixes unchanged (no regression)
# ===================================================================================================
def group_REG():
    a = EvidencePackAssembler()

    # REG1 — B2 named forgeries still defeated (junk ref; one ref copy-pasted across all slots).
    junk = {cat: {k: "x" for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}
    one = "ev::Consent::consent_pass"
    copied = {cat: {k: one for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}
    p_junk = a.assemble(all_recorded(), junk)
    p_copy = a.assemble(all_recorded(), copied)
    if p_junk.readiness is Readiness.NOT_READY and p_copy.readiness is Readiness.NOT_READY \
            and all(not c.complete for c in p_junk.categories) and all(not c.complete for c in p_copy.categories):
        record("REG1", "FAIL-007", "DEFENDED",
               "carried B2 (M6.2L) intact: a junk 'x' ref and one ref copy-pasted across all slots both -> all "
               "categories MISSING -> NOT_READY (no regression from the M6.2M twins).")
    else:
        record("REG1", "FAIL-007", "BREACH", "B2 forgery block regressed")

    # REG2 — B3 standing-floor still catches the emptied-payload rebind -> NOT_READY.
    saved = PA.STANDING_GAP_BLOCKERS
    try:
        PA.STANDING_GAP_BLOCKERS = ()
        p = a.assemble(all_recorded(), canonical_refs())
        ok = p.readiness is Readiness.NOT_READY
    finally:
        PA.STANDING_GAP_BLOCKERS = saved
    if ok and len([g for g in a.assemble().gap_blockers if g.kind is GapKind.STANDING_BLOCKER]) == 8:
        record("REG2", "FAIL-007", "DEFENDED",
               "carried B3 (M6.2L) intact: rebinding STANDING_GAP_BLOCKERS=() still trips the defensive "
               "standing_floor_ok -> NOT_READY; the canonical list still carries all 8 standing blockers.")
    else:
        record("REG2", "FAIL-007", "BREACH", "B3 floor regressed")

    # REG3 — B4 revenue-lock still holds (mispair -> 0) — FAIL-001, carried unchanged; light confirmation.
    from app.measurement.store.measurement_event_store import MeasurementEventStore
    from app.measurement.attribution.resolver import AttributionResolver
    from app.measurement.attribution.materializer import AttributionMaterializer
    from app.measurement.audit import AuditLog
    from app.measurement.models.measurement_event import AdsMeasurementEvent
    from app.measurement.models.conversion_event import ConversionEvent
    from app.measurement.dashboard.data_mart import DataMart
    store = MeasurementEventStore()
    q = AdsMeasurementEvent(event_id="q", event_code="QUOTE_SENT", event_ts=FIXED_TS, idempotency_key="idem_q",
                            correlation_id="c", ingested_at=FIXED_TS)
    store.insert(q)
    mat = AttributionMaterializer(store, AttributionResolver(), AuditLog())
    conv = ConversionEvent(conversion_id="cv", event_code="ORDER_VERIFIED", source_event_id="q", correlation_id="c",
                           customer_or_guest_key="g", consent_snapshot_id="cs", occurred_at=FIXED_TS,
                           idempotency_key="idem2", revenue_value=500000.0, currency="VND", order_code="o")
    mat.materialize(q, conv)
    if store.get_by_event_id("q").revenue_value is None and DataMart(store).revenue_verified() == 0.0:
        record("REG3", "FAIL-001", "DEFENDED",
               "carried B4 (M6.2L) intact: the QUOTE_SENT+ORDER_VERIFIED mispair still drops revenue at the store "
               "and reads 0 at the dashboard (revenue-lock unchanged by M6.2M).")
    else:
        record("REG3", "FAIL-001", "BREACH", "B4 revenue-lock regressed")


# ===================================================================================================
# GROUP N — reconciliation of the ideation workflow's novel vectors (executed)
# ===================================================================================================
def group_N():
    a = EvidencePackAssembler()

    # N1 (RA-2) — known_refs is `Any` with no type guard: a STRING allowlist degrades `r not in known_refs` from
    #     exact-set-membership to SUBSTRING containment. A forged ref that is a substring of the blob passes.
    blob = " ".join(sorted(all_issued()))                      # a joined/serialized registry (mis-built as a str)
    p = a.assemble(all_recorded(), canonical_refs(), known_refs=blob)
    if all(c.complete for c in p.categories):
        record("N1", "FAIL-007", "OPEN_NONGATE",
               "RA-2: `known_refs` is untyped (Any); a STRING allowlist makes `r not in known_refs` a SUBSTRING "
               "test, so any canonical ref that is a substring of the blob passes -> all categories COMPLETE. "
               "Trusted-input only (owner tooling builds the registry). Robustness gap: add "
               "isinstance(known_refs,(set,frozenset,dict)) so a mis-built str/iterable cannot degrade the oracle.")
    else:
        record("N1", "FAIL-007", "DEFENDED", "string allowlist did not universally pass")

    # N2 (COMP-1/COMP-2) — `_categories` evaluates `_ref_valid` TWICE per key (present= AND missing= comprehensions),
    #     so a one-shot GENERATOR known_refs is EXHAUSTED mid-pass -> an HONEST fully-issued pack is FALSE-REJECTED.
    gen = (x for x in all_issued())
    p = a.assemble(all_recorded(), canonical_refs(), known_refs=gen)
    if p.readiness is Readiness.NOT_READY and not all(c.complete for c in p.categories):
        record("N2", "FAIL-007", "OPEN_NONGATE",
               "COMP-1/COMP-2: `_categories` calls `_ref_valid` TWICE per key (present= and missing= comprehensions), "
               "so a GENERATOR known_refs of the genuinely-issued refs is CONSUMED mid-pass -> an honest fully-issued "
               "pack is FALSE-REJECTED (NOT_READY). Fail-closed direction (under-states, never over-states -> not a "
               "FAIL-007 breach), but a real robustness regression: materialize known_refs once + evaluate _ref_valid "
               "once per key. Trusted-input.")
    else:
        record("N2", "FAIL-007", "NOTE", f"generator known_refs behaved unexpectedly (readiness={p.readiness})")

    # N3 (COMP-3) — a non-Mapping evidence_refs category value (a list) -> `provided.get(k)` on a list -> crash =
    #     fail-closed (no pack emitted, nothing over-stated). Pre-existing since M6.2L.
    refs = canonical_refs()
    refs[EvidenceCategory.DEDUP] = ["ev::Dedup::x"]             # truthy non-Mapping value
    try:
        a.assemble(all_recorded(), refs)
        record("N3", "FAIL-007", "NOTE", "non-Mapping evidence_refs value did not crash (inspect)")
    except Exception as e:  # noqa
        record("N3", "FAIL-007", "OPEN_NONGATE",
               f"COMP-3: a non-Mapping evidence_refs category value (list) makes `provided.get(k)` raise "
               f"{type(e).__name__} -> assemble aborts (fail-closed-by-crash; no overstated pack). Trusted-input; "
               "robustness gap (guard `provided` is a Mapping -> INCOMPLETE instead of crash). Pre-existing.")

    # N4 (COMP-5 / carried X2) — `_smokes` appends the caller's result VERBATIM (not pinned to spec.smoke_id) and
    #     `to_public` exports smoke_id UNMASKED: a result stored under the SMK-001 key but carrying a different/PII
    #     smoke_id is displayed with that leaked id (mislabel + a SECOND unmasked export slot besides status).
    leaked = "LEAK-" + chr(64) + "-marker"                     # @-shaped, assembled (no literal PII in source)
    refs = dict(all_recorded())
    refs["M6-SMK-001"] = SmokeResult(smoke_id=leaked, status="PASS", correlation_id="c", evidence_id="e")
    p = a.assemble(refs, canonical_refs())
    shown_ids = [s["smoke_id"] for s in p.to_public()["smokes"]]
    if leaked in shown_ids:
        record("N4", "FAIL-007", "OPEN_NONGATE",
               "COMP-5 + carried X2 (out of scope): `_smokes` appends the caller's SmokeResult verbatim (row NOT "
               "pinned to spec.smoke_id) and `to_public` exports smoke_id UNMASKED -> a result under the SMK-001 key "
               "carrying a different/PII smoke_id is DISPLAYED with that leaked id (a mislabel + a SECOND unmasked "
               "export slot besides status, widening F-EVID-4). Trusted-input (TESTER builds SmokeResults). Route: "
               "CODER (pin the row to spec.smoke_id) + security M6-P2206 (mask/constrain smoke_id + status, M6-OD-012).")
    else:
        record("N4", "FAIL-007", "DEFENDED", "smoke_id pinned/masked on export")

    # N5 (COMP-6) — reachability floor: no app/api endpoint constructs or calls the assembler (grep-confirmed
    #     separately), and Readiness has no Pass member, so EVERY residual is trusted-input/code-exec, caps at
    #     OWNER_REVIEW_REQUIRED, and is armed-not-fired.
    members = {m.value for m in Readiness}
    if members == {"OWNER_REVIEW_REQUIRED", "NOT_READY"}:
        record("N5", "FAIL-007", "DEFENDED",
               "reachability floor (COMP-6): the evidence assembler has NO app/api caller (grep-confirmed: the "
               "evidence module is imported only by evidence internals + tests) and Readiness has no Pass/Ready "
               "member -> every M6.2M residual is trusted-input/code-exec, caps at OWNER_REVIEW_REQUIRED (never a "
               "Pass), and is armed-not-fired. This is the load-bearing classification floor.")
    else:
        record("N5", "FAIL-007", "BREACH", f"Readiness gained a member: {members}")


# ===================================================================================================
def main():
    print("=" * 100)
    print("M6.2M BOUNDARY ADVERSARY — evidence-authenticity twin (in-scope: FAIL-007 / M6-OD-013)")
    print(f"impl root: {IMPL}")
    print(f"_nonblank sanity: '  '->{_nonblank('  ')}  'x'->{_nonblank('x')}  None->{_nonblank(None)}")
    print("=" * 100)
    for g in (group_F1, group_F2, group_R, group_REG, group_N):
        print(f"\n----- {g.__name__} -----")
        g()

    print("\n" + "=" * 100)
    tally = {}
    for _, _, k, _ in OUTCOMES:
        tally[k] = tally.get(k, 0) + 1
    breaches = [o for o in OUTCOMES if o[2] == "BREACH"]
    inscope = [o for o in breaches if o[1] == "FAIL-007"]
    print(f"SUMMARY: {tally}")
    print(f"TOTAL RECORDED OUTCOMES: {len(OUTCOMES)}")
    print(f"IN-SCOPE FAIL-GATE BREACHES (FAIL-007): {len(inscope)}")
    for o in breaches:
        print("   BREACH:", o)

    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
    assert config.EXTERNAL_SEND == "OFF"
    assert {m.value for m in Readiness} == {"OWNER_REVIEW_REQUIRED", "NOT_READY"}
    print("POSTURE AFTER RUN: BLOCKED / OFF / OFF (unchanged); Readiness has no Pass/Ready member")
    print("=" * 100)


if __name__ == "__main__":
    main()
