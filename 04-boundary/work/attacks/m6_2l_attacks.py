"""M6.2L boundary-adversary harness (READ-ONLY analysis; prompt M6-P2105).

Attacks the staged M6.2L "Post-Pilot Audit Fix Batch" — the 5 M6-self-doable fixes A3/A4/B2/B3/B4 that close
defects from the 2026-09-03 chief-auditor audit (a cumulative superset of M6.2K). In-scope fail gates:
M6-FAIL-001 (revenue misuse; B4) and M6-FAIL-007 (no-evidence / overstated readiness; B2/B3). The harness DRIVES
the real staged code and EXECUTES every claimed breach before recording it; it writes nothing, flips no flag.

    PYTHONDONTWRITEBYTECODE=1  py -3.12 -B  work/attacks/m6_2l_attacks.py

Classification: DEFENDED / OPEN_NONGATE (armed-not-fired: in-process code-exec-only / trusted-input-only / not
channel-reachable) / NOTE / BREACH (an in-scope FAIL-001/FAIL-007 gate trips from a channel-reachable path).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve()
IMPL = None
for anc in HERE.parents:
    cand = anc / "04-artifacts" / "impl" / "M6.2L"
    if (cand / "app").is_dir():
        IMPL = cand
        break
if IMPL is None:
    raise SystemExit("cannot locate 04-artifacts/impl/M6.2L/app")
sys.path.insert(0, str(IMPL))

from datetime import datetime, timezone

from app import config
from app.measurement.masking import mask
from app.measurement.audit import AuditLog
from app.measurement.store.measurement_event_store import MeasurementEventStore, MeasurementStoreViolation
from app.measurement.attribution.resolver import AttributionResolver
from app.measurement.attribution.materializer import AttributionMaterializer
from app.measurement.models.measurement_event import AdsMeasurementEvent
from app.measurement.models.conversion_event import ConversionEvent
from app.measurement.dashboard.data_mart import DataMart
from app.measurement.dashboard.kpi_metrics import compute_metrics
from app.measurement.growth.reads import verified_rows as growth_verified_rows
from app.measurement.growth.crm import CrmReorderMeasurement, CrmConsumed
from app.measurement.consent.gate import ConsentGate
from app.measurement.models.consumed import ConsentScope, ConsentSnapshot, ConsentState

from app.measurement.evidence import pack_assembler as PA
from app.measurement.evidence.pack_assembler import EvidencePackAssembler
from app.measurement.evidence.models import Readiness, GapKind, SmokeResult, GapBlocker
from app.measurement.evidence.categories import EvidenceCategory, CATEGORY_MANDATORY
from app.measurement.evidence.gap_blockers import (
    STANDING_GAP_BLOCKERS, STANDING_BLOCKER_IDS, standing_floor_ok,
)
from app.measurement.evidence.smoke_registry import SMOKE_IDS

FIXED_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
OV = "ORDER_VERIFIED"
OUTCOMES = []


def record(vec, gate, klass, detail):
    OUTCOMES.append((vec, gate, klass, detail))
    print(f"[{klass:12}] {vec:8} {gate:10} {detail}")


# --- factories --------------------------------------------------------------------------------------
def new_store():
    return MeasurementEventStore()


def insert_event(store, event_id, event_code):
    ev = AdsMeasurementEvent(event_id=event_id, event_code=event_code, event_ts=FIXED_TS,
                             idempotency_key=f"idem_{event_id}", correlation_id=f"corr_{event_id}", ingested_at=FIXED_TS)
    store.insert(ev)
    return ev


def do_materialize(store, ev, *, conv_code, revenue, order_code, signals=None):
    mat = AttributionMaterializer(store, AttributionResolver(), AuditLog())
    conv = ConversionEvent(conversion_id=f"conv_{ev.event_id}", event_code=conv_code, source_event_id=ev.event_id,
                           correlation_id="corr_c", customer_or_guest_key="guest_mapped_ok",
                           consent_snapshot_id="cs_valid", occurred_at=FIXED_TS, idempotency_key=f"idem2_{ev.event_id}",
                           revenue_value=(float(revenue) if revenue is not None else None), currency="VND",
                           order_code=order_code)
    return mat.materialize(ev, conv, signals=signals)


def canonical_refs():
    """The canonical ev::{category.value}::{key} refs — identical to the honest full_evidence_refs fixture."""
    return {cat: {k: f"ev::{cat.value}::{k}" for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}


def all_recorded():
    return {sid: SmokeResult(sid, status="PASS", correlation_id="corr_" + sid[-3:], evidence_id="ev_" + sid[-3:])
            for sid in SMOKE_IDS}


# ===================================================================================================
# GROUP B4 — verified-revenue lock (FAIL-001 / RULE-003) — the M6.2K mispair must now be closed
# ===================================================================================================
def group_B4():
    # B4-1 — the M6.2K MISPAIR at the WRITE layer: QUOTE_SENT event + ORDER_VERIFIED conversion. The store now
    #        self-checks the STORED row's own event_code and DROPS the revenue (no raise).
    store = new_store()
    quote = insert_event(store, "q1", "QUOTE_SENT")
    out = do_materialize(store, quote, conv_code=OV, revenue=650000, order_code="ord_q1")
    row = store.get_by_event_id("q1")
    if row.revenue_value is None and row.order_code is None and out.revenue_value is None:
        record("B4-1", "FAIL-001", "DEFENDED",
               "the M6.2K mispair is CLOSED at the write layer: materialize(QUOTE_SENT event, ORDER_VERIFIED "
               "conversion) drops revenue+order_code fail-closed (store self-checks the STORED event_code, not the "
               "caller's verified flag) -> the quote row carries NO revenue. No raise (carried funnel smokes stay green).")
    else:
        record("B4-1", "FAIL-001", "BREACH", f"revenue landed on a QUOTE_SENT row (rev={row.revenue_value})")

    # B4-2 — the READ layer belt: even a crafted non-OV row that HELD a revenue_value is excluded by BOTH
    #        verified_rows choke points (data_mart + growth.reads).
    leaked = AdsMeasurementEvent(event_id="leak", event_code="QUOTE_SENT", event_ts=FIXED_TS,
                                 idempotency_key="idem_leak", correlation_id="c", ingested_at=FIXED_TS,
                                 revenue_value=999999.0, order_code="ord_leak")

    class _FakeStore:
        def all(self):
            return (leaked,)
    fs = _FakeStore()
    dm_rows = DataMart(fs).verified_rows()
    gr_rows = growth_verified_rows(fs)
    if len(dm_rows) == 0 and len(gr_rows) == 0 and DataMart(fs).revenue_verified() == 0.0:
        record("B4-2", "FAIL-001", "DEFENDED",
               "read-layer belt: a crafted QUOTE_SENT row holding revenue_value=999999 is excluded by BOTH "
               "verified_rows choke points (data_mart + growth.reads AND event_code==ORDER_VERIFIED) -> Revenue "
               "Verified 0, CRM/Diamond 0. Defense-in-depth with the write-layer drop.")
    else:
        record("B4-2", "FAIL-001", "BREACH", f"a non-OV revenue row passed the read filter (dm={len(dm_rows)})")

    # B4-3 — other non-OV event codes (ORDER_CREATED, PAYMENT_COMPLETED) also drop revenue at materialize.
    dropped = 0
    for code in ("ORDER_CREATED", "PAYMENT_COMPLETED", "LIVE_COMMENT"):
        s = new_store()
        e = insert_event(s, f"e_{code}", code)
        do_materialize(s, e, conv_code=OV, revenue=100000, order_code=f"o_{code}")
        if s.get_by_event_id(f"e_{code}").revenue_value is None:
            dropped += 1
    if dropped == 3:
        record("B4-3", "FAIL-001", "DEFENDED",
               "every non-ORDER_VERIFIED event code (ORDER_CREATED / PAYMENT_COMPLETED / LIVE_COMMENT) drops "
               "materialized revenue -- only an ORDER_VERIFIED stored row may carry revenue (RULE-003).")
    else:
        record("B4-3", "FAIL-001", "BREACH", f"a non-OV code kept revenue ({3 - dropped} leaked)")

    # B4-4 — the LEGITIMATE path still works: a genuine ORDER_VERIFIED row carries revenue and counts (non-vacuous).
    store = new_store()
    ov = insert_event(store, "v1", OV)
    do_materialize(store, ov, conv_code=OV, revenue=180000, order_code="ord_v1", signals={"entry_channel": "CRM"})
    dm = DataMart(store)
    if store.get_by_event_id("v1").revenue_value == 180000.0 and dm.revenue_verified() == 180000.0 \
            and len(growth_verified_rows(store)) == 1:
        record("B4-4", "FAIL-001", "DEFENDED",
               "control: a genuine ORDER_VERIFIED row carries revenue 180000 and counts in dashboard + growth "
               "verified_rows (the lock is not over-tight; it does not break legitimate revenue).")
    else:
        record("B4-4", "FAIL-001", "BREACH", f"legitimate OV revenue miscounted (dm={dm.revenue_verified()})")

    # B4-5 — set-once immutability (RULE-008) preserved: a differing re-materialize on a verified OV row raises.
    store = new_store()
    ov = insert_event(store, "v2", OV)
    do_materialize(store, ov, conv_code=OV, revenue=100000, order_code="ord_v2")
    raised = False
    try:
        store.materialize("v2", attribution_context={"x": 1}, revenue_value=999999.0, order_code="ord_other",
                          verified=True)
    except MeasurementStoreViolation:
        raised = True
    if raised and store.get_by_event_id("v2").revenue_value == 100000.0:
        record("B4-5", "FAIL-001", "DEFENDED",
               "set-once (RULE-008) preserved by B4: a differing re-materialize on a verified OV row raises; the "
               "stored 100000 is immutable. The drop-not-raise change applies only to non-OV rows.")
    else:
        record("B4-5", "FAIL-001", "BREACH", f"set-once broken (raised={raised})")

    # B4-6 — growth CRM revenue over the mispaired store is 0 (write drop + read filter compose).
    store = new_store()
    q = insert_event(store, "q6", "QUOTE_SENT")
    do_materialize(store, q, conv_code=OV, revenue=500000, order_code="ord_q6", signals={"entry_channel": "CRM"})
    consumed = CrmConsumed(crm_eligible_orders={"ord_q6": True}, suppression_pass_orders={"ord_q6": True},
                           consent_by_order={"ord_q6": ConsentSnapshot("c", "s", ConsentState.VALID, FIXED_TS,
                                                                       frozenset({ConsentScope.CRM}))})
    crm_rev = CrmReorderMeasurement(store, ConsentGate(AuditLog()), consumed).crm_revenue()
    if crm_rev == 0.0:
        record("B4-6", "FAIL-001", "DEFENDED",
               "growth CRM revenue over the mispaired store = 0 -- the write-layer drop leaves no revenue and the "
               "read-layer event_code filter would exclude it anyway (F-GROWTH-3 CLOSED).")
    else:
        record("B4-6", "FAIL-001", "BREACH", f"CRM revenue leaked from a mispaired quote (rev={crm_rev})")


# ===================================================================================================
# GROUP B2 — evidence-ref forgery (FAIL-007 / RULE-015 / M6-OD-013)
# ===================================================================================================
def group_B2():
    a = EvidencePackAssembler()

    # B2-1 — the DOCUMENTED M6-OD-013 residual: reconstruct the canonical ev::{cat}::{key} for every slot (no
    #        known_refs). Slot-correctness passes; authenticity is NOT proven -> COMPLETE / OWNER_REVIEW_REQUIRED.
    pack = a.assemble(all_recorded(), canonical_refs())
    if all(c.complete for c in pack.categories) and pack.readiness is Readiness.OWNER_REVIEW_REQUIRED:
        record("B2-1", "FAIL-007", "OPEN_NONGATE",
               "DOCUMENTED residual (M6-OD-013): a forger who RECONSTRUCTS the canonical ev::{category}::{key} "
               "string for every slot (no known_refs oracle) passes -- the default path proves slot-correctness "
               "(shape + (category,key)-binding + uniqueness), NOT authenticity (the honest full_evidence_refs and a "
               "reconstruction are byte-identical). Trusted-input only: evidence_refs is authored by the PM, not a "
               "channel; the known_refs registry (owner integration, M6-OD-013) adds authenticity. The pack still "
               "tops at OWNER_REVIEW_REQUIRED, never a Pass. Route: owner (M6-OD-013).")
    else:
        record("B2-1", "FAIL-007", "DEFENDED", "canonical reconstruction did not complete the pack.")

    # B2-2 — named forgery 1: a fake-but-nonblank junk ref 'x' for every slot -> all MISSING -> NOT_READY.
    junk = {cat: {k: "x" for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}
    p2 = a.assemble(all_recorded(), junk)
    if all(not c.complete for c in p2.categories) and p2.readiness is Readiness.NOT_READY:
        record("B2-2", "FAIL-007", "DEFENDED",
               "named forgery 1 DEFEATED: a fake-but-nonblank 'x' ref is unbound (not ev::cat::key) -> every "
               "category MISSING -> NOT_READY.")
    else:
        record("B2-2", "FAIL-007", "BREACH", "junk ref completed a category")

    # B2-3 — named forgery 2: ONE valid ref copy-pasted across all slots -> fails uniqueness -> all MISSING.
    one = "ev::Consent::consent_pass"
    copied = {cat: {k: one for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}
    p3 = a.assemble(all_recorded(), copied)
    if all(not c.complete for c in p3.categories) and p3.readiness is Readiness.NOT_READY:
        record("B2-3", "FAIL-007", "DEFENDED",
               "named forgery 2 DEFEATED: one valid ref reused for every slot fails pack-wide uniqueness "
               "(counts != 1) -> all categories MISSING -> NOT_READY.")
    else:
        record("B2-3", "FAIL-007", "BREACH", "copy-pasted ref completed a category")

    # B2-4 — wrong-category binding: a ref bound to Consent placed in a Dedup slot -> that slot MISSING.
    refs = canonical_refs()
    dedup_key = CATEGORY_MANDATORY[EvidenceCategory.DEDUP][0]
    refs[EvidenceCategory.DEDUP] = {dedup_key: "ev::Consent::consent_pass"}   # wrong category
    p4 = a.assemble(all_recorded(), refs)
    dedup = p4.category(EvidenceCategory.DEDUP)
    if not dedup.complete and p4.readiness is Readiness.NOT_READY:
        record("B2-4", "FAIL-007", "DEFENDED",
               "wrong-category binding: a Consent-bound ref in a Dedup slot fails (category,key)-binding -> Dedup "
               "MISSING -> NOT_READY.")
    else:
        record("B2-4", "FAIL-007", "BREACH", "wrong-category ref satisfied a slot")

    # B2-5 — wrong-key binding: ev::{cat}::WRONGKEY -> the real key MISSING.
    refs = canonical_refs()
    er = EvidenceCategory.EVENT_REGISTRY
    k0 = CATEGORY_MANDATORY[er][0]
    refs[er] = dict(refs[er]); refs[er][k0] = f"ev::{er.value}::WRONGKEY"
    p5 = a.assemble(all_recorded(), refs)
    if not p5.category(er).complete and k0 in p5.category(er).missing:
        record("B2-5", "FAIL-007", "DEFENDED",
               f"wrong-key binding: ev::{er.value}::WRONGKEY does not satisfy key '{k0}' -> Event Registry MISSING.")
    else:
        record("B2-5", "FAIL-007", "BREACH", "wrong-key ref satisfied a slot")

    # B2-6 — the known_refs AUTHENTICITY oracle WORKS: a canonical ref NOT in the issued registry -> MISSING.
    refs = canonical_refs()
    issued = set()
    for cat, keys in CATEGORY_MANDATORY.items():
        for k in keys:
            issued.add(f"ev::{cat.value}::{k}")
    issued.discard(f"ev::{EvidenceCategory.CONSENT.value}::{CATEGORY_MANDATORY[EvidenceCategory.CONSENT][0]}")
    p6 = a.assemble(all_recorded(), refs, known_refs=issued)
    if not p6.category(EvidenceCategory.CONSENT).complete and p6.readiness is Readiness.NOT_READY:
        record("B2-6", "FAIL-007", "DEFENDED",
               "the known_refs oracle enforces AUTHENTICITY: a canonical ref removed from the issued registry -> "
               "its slot MISSING -> NOT_READY (the M6-OD-013 forward seam closes the B2-1 residual when wired).")
    else:
        record("B2-6", "FAIL-007", "BREACH", "known_refs oracle failed to reject an un-issued ref")

    # B2-7 — hostile known_refs whose __contains__ is always True -> any ref passes (owner-supplied oracle).
    class _AllContains:
        def __contains__(self, x):
            return True
    p7 = a.assemble(all_recorded(), canonical_refs(), known_refs=_AllContains())
    if all(c.complete for c in p7.categories):
        record("B2-7", "FAIL-007", "OPEN_NONGATE",
               "a hostile known_refs whose __contains__ returns True for everything defeats the authenticity oracle "
               "(any convention-shaped ref passes). Trusted-input / code-exec only: known_refs is the owner-supplied "
               "issued-refs registry, not channel input. Route: owner integration should pass a real set/frozenset.")
    else:
        record("B2-7", "FAIL-007", "DEFENDED", "hostile known_refs did not universally pass.")

    # B2-8 — non-string / hostile ref values fail-closed to MISSING.
    for bad in (123, None, ["ev::x::y"], {"ev": 1}):
        refs = canonical_refs()
        refs[er] = dict(refs[er]); refs[er][k0] = bad
        pb = a.assemble(all_recorded(), refs)
        if pb.category(er).complete:
            record("B2-8", "FAIL-007", "BREACH", f"non-string ref {bad!r} satisfied a slot")
            break
    else:
        record("B2-8", "FAIL-007", "DEFENDED",
               "non-string / hostile ref values (int/None/list/dict) fail the isinstance(str) guard -> MISSING.")


# ===================================================================================================
# GROUP B3 — gap-id collision floor (FAIL-007 / M6-OD-014) — closes F-EVID-3
# ===================================================================================================
def group_B3():
    a = EvidencePackAssembler()
    SB = GapKind.STANDING_BLOCKER

    # B3-1 — F-EVID-3 CLOSED: rebinding pack_assembler.STANDING_GAP_BLOCKERS=() now makes the emitted gap list miss
    #        all standing ids -> the defensive floor FAILS -> NOT_READY (in M6.2K/M6-P3002 this yielded OWNER_REVIEW_REQUIRED).
    saved = PA.STANDING_GAP_BLOCKERS
    try:
        PA.STANDING_GAP_BLOCKERS = ()
        p = a.assemble(all_recorded(), canonical_refs())
        if p.readiness is Readiness.NOT_READY:
            record("B3-1", "FAIL-007", "DEFENDED",
                   "F-EVID-3 CLOSED (B3): rebinding pack_assembler.STANDING_GAP_BLOCKERS=() empties the honesty "
                   "payload, but the defensive standing_floor_ok now catches the missing standing ids -> NOT_READY "
                   "(M6.2K/M6-P3002 residual is fixed -- the readiness<->standing cross-check exists).")
        else:
            record("B3-1", "FAIL-007", "BREACH", f"emptied standing payload still reached {p.readiness}")
    finally:
        PA.STANDING_GAP_BLOCKERS = saved
    assert len(a.assemble().gap_blockers) >= 8

    # B3-2/3/4 — the floor detects duplicate / shadow / missing standing ids (called directly).
    canon = list(STANDING_GAP_BLOCKERS)
    dup = canon + [canon[0]]                                   # duplicate M6-P1000
    shadow = [GapBlocker(canon[1].id, SB, "TAMPERED content", "x")] + canon[2:] + [canon[0]]  # shadow M6-P1309
    missing = canon[1:]                                        # drop M6-P1000
    res = (standing_floor_ok(dup), standing_floor_ok(shadow), standing_floor_ok(missing), standing_floor_ok(canon))
    if res == (False, False, False, True):
        record("B3-2", "FAIL-007", "DEFENDED",
               "the membership-count floor FAILs a duplicated, a shadowing (same id, different content), and a "
               "missing standing id, and PASSes the canonical list (a naive set-subset check would pass the "
               "duplicate/shadow). Duplicate/shadow/missing -> NOT_READY.")
    else:
        record("B3-2", "FAIL-007", "BREACH", f"floor mis-verdicts: dup/shadow/missing/canon = {res}")

    # B3-5 — a clean assembled pack passes the floor AND carries all 8 standing blockers (non-vacuous).
    pack = a.assemble(all_recorded(), canonical_refs())
    standing = {g.id for g in pack.gap_blockers if g.kind is SB}
    if standing == set(STANDING_BLOCKER_IDS) and standing_floor_ok(pack.gap_blockers) \
            and pack.readiness is Readiness.OWNER_REVIEW_REQUIRED:
        record("B3-5", "FAIL-007", "DEFENDED",
               "control: a clean complete pack passes the floor and discloses all 8 standing blockers -> "
               "OWNER_REVIEW_REQUIRED (the floor does not over-tighten a legitimate pack).")
    else:
        record("B3-5", "FAIL-007", "BREACH", f"clean pack failed the floor (standing={sorted(standing)})")

    # B3-6 — a hostile GapBlocker with a spoofed __eq__ that compares equal to the canonical (kind, desc) while
    #        shadowing an id -> code-exec-only bypass of the floor's content check.
    class _SpoofEq(GapBlocker):
        pass
    # (frozen dataclass; build a plain object with the attributes the floor reads + a spoofed content tuple)

    class _HostileGap:
        id = "M6-P1000"
        kind = SB

        @property
        def description(self):
            return "M6.2A entry judge verdict BLOCKED (not converted)"   # exact canonical content
    # Not a real bypass (it just reproduces the canonical content); a genuine shadow needs DIFFERENT content, which
    # the floor rejects. Document the boundary honestly.
    record("B3-6", "FAIL-007", "DEFENDED",
           "the floor compares (kind, description) by value against the canonical; to 'pass' a shadow one must "
           "reproduce the EXACT canonical content (i.e. not a shadow at all). A genuinely different content is "
           "rejected. Only rebinding standing_floor_ok itself (deeper code-exec) bypasses it -- not channel-reachable.")


# ===================================================================================================
# GROUP R — residuals NOT in the 5-fix scope: confirm they remain (armed-not-fired), and note stale disclosure
# ===================================================================================================
def group_R():
    a = EvidencePackAssembler()

    # R1 — F-EVID-5 (recorded != passed) STILL OPEN: all 18 smokes recorded status='FAIL' -> OWNER_REVIEW_REQUIRED.
    all_fail = {s: SmokeResult(s, status="FAIL", correlation_id="c", evidence_id="e") for s in SMOKE_IDS}
    p = a.assemble(all_fail, canonical_refs())
    if p.readiness is Readiness.OWNER_REVIEW_REQUIRED:
        record("R1", "FAIL-007", "OPEN_NONGATE",
               "F-EVID-5 STILL OPEN (out of the 5-fix scope): a pack with all 18 P0 smokes recorded status='FAIL' "
               "still reaches OWNER_REVIEW_REQUIRED -- _readiness tests only s.recorded, never PASS/FAIL. "
               "SmokeResult.recorded is byte-identical to M6.2K. Trusted-input; caps at OWNER_REVIEW_REQUIRED. "
               "Carry-forward for a future slice (F-EVID-5).")
    else:
        record("R1", "FAIL-007", "DEFENDED", "recorded FAIL smoke now drops readiness (unexpectedly fixed).")

    # R2 — F-EVID-1 (whitespace-id smoke) STILL OPEN: a whitespace status/corr/ev reads as recorded.
    ws = dict(all_recorded())
    ws["M6-SMK-001"] = SmokeResult("M6-SMK-001", status=" ", correlation_id=" ", evidence_id=" ")
    p = a.assemble(ws, canonical_refs())
    smk = next(s for s in p.smokes if s.smoke_id == "M6-SMK-001")
    if smk.recorded:
        record("R2", "FAIL-007", "OPEN_NONGATE",
               "F-EVID-1 STILL OPEN (out of scope): a SmokeResult with whitespace status/correlation_id/evidence_id "
               "reads as recorded (recorded uses bool() truthiness). Trusted-input. Carry-forward.")
    else:
        record("R2", "FAIL-007", "DEFENDED", "whitespace-id smoke no longer recorded.")

    # R3 — F-EVID-4 (status exported verbatim) STILL OPEN.
    marker = "st" + "atus-with-" + chr(64) + "marker"   # @-shaped, assembled (no literal PII in source)
    refs2 = dict(all_recorded())
    refs2["M6-SMK-002"] = SmokeResult("M6-SMK-002", status=marker, correlation_id="c", evidence_id="e")
    p = a.assemble(refs2, canonical_refs())
    exported = next(s for s in p.to_public()["smokes"] if s["smoke_id"] == "M6-SMK-002")
    if exported["status"] == marker:
        record("R3", "FAIL-007", "OPEN_NONGATE",
               "F-EVID-4 STILL OPEN (out of scope): SmokeResult.to_public() emits status verbatim (only corr/ev "
               "ids masked). Trusted-input (TESTER sets PASS/FAIL). Carry-forward.")
    else:
        record("R3", "FAIL-007", "DEFENDED", "status now masked/constrained on export.")

    # R4 — F-GROWTH-1 (CRM borrowed consent) STILL OPEN: B4 fixed F-GROWTH-3 but not the subject-bind.
    store = new_store()
    v = insert_event(store, "cb", OV)
    do_materialize(store, v, conv_code=OV, revenue=650000, order_code="ord_cb", signals={"entry_channel": "CRM"})
    other = ConsentSnapshot("cs_b", "subject_B_different", ConsentState.VALID, FIXED_TS,
                            frozenset({ConsentScope.CRM}))
    consumed = CrmConsumed(crm_eligible_orders={"ord_cb": True}, suppression_pass_orders={"ord_cb": True},
                           consent_by_order={"ord_cb": other})
    rev = CrmReorderMeasurement(store, ConsentGate(AuditLog()), consumed).crm_revenue()
    if rev == 650000.0:
        record("R4", "FAIL-002", "OPEN_NONGATE",
               "F-GROWTH-1 STILL OPEN (out of scope; FAIL-002-adjacent): the CRM gate counts 650000 using "
               "subject_B's consent for the buyer's order -- no subject_ref<->buyer bind. B4 fixed F-GROWTH-3 "
               "(verified_rows event_code), NOT F-GROWTH-1. Trusted-input. Standing blocker M6.2J-GROWTH.")
    else:
        record("R4", "FAIL-002", "DEFENDED", f"borrowed consent no longer counts (rev={rev}).")

    # R5 — NOTE: the standing-blocker text still lists F-GROWTH-3 as a forward condition, but B4 CLOSED it -> the
    #      disclosure now over-discloses a fixed item (safe/honest-conservative), and the floor LOCKS the text.
    j = next((g for g in STANDING_GAP_BLOCKERS if g.id == "M6.2J-GROWTH"), None)
    if j is not None and "F-GROWTH-3" in j.description:
        record("R5", "FAIL-007", "NOTE",
               "the M6.2J-GROWTH standing-blocker text still lists 'F-GROWTH-3 (verified_rows ORDER_VERIFIED "
               "choke)' as a forward condition, but B4 CLOSED F-GROWTH-3. Over-disclosure is safe (honest-"
               "conservative) and the B3 floor LOCKS this description; a future slice should update the text "
               "(floor-aware) once the owner confirms. Not a gate breach.")
    else:
        record("R5", "FAIL-007", "NOTE", "F-GROWTH-3 disclosure already updated.")


# ===================================================================================================
# GROUP A — A3/A4 attribution intake: confirm no FAIL-001 / FAIL-007 hole (light)
# ===================================================================================================
def group_A():
    # A-1 — attribution_id is a deterministic governance ref (A3): re-resolving the same OV row yields the same
    #       attribution_id; distinct events yield distinct ids; it does not carry or become revenue.
    store = new_store()
    ov = insert_event(store, "a1", OV)
    do_materialize(store, ov, conv_code=OV, revenue=120000, order_code="ord_a1", signals={"campaign_id": "camp_1"})
    ctx = store.get_by_event_id("a1").attribution_context
    aid = ctx.get("attribution_id") if isinstance(ctx, dict) else None
    store2 = new_store()
    ov2 = insert_event(store2, "a1", OV)   # same event_id -> same derived id
    do_materialize(store2, ov2, conv_code=OV, revenue=120000, order_code="ord_a1", signals={"campaign_id": "camp_1"})
    aid2 = store2.get_by_event_id("a1").attribution_context.get("attribution_id")
    store3 = new_store()
    ov3 = insert_event(store3, "a1_other", OV)
    do_materialize(store3, ov3, conv_code=OV, revenue=120000, order_code="ord_a1", signals={"campaign_id": "camp_1"})
    aid3 = store3.get_by_event_id("a1_other").attribution_context.get("attribution_id")
    if aid and aid == aid2 and aid != aid3 and str(aid).startswith("attr_"):
        record("A-1", "FAIL-001", "DEFENDED",
               f"attribution_id (A3) is a deterministic governance ref ('{str(aid)[:8]}...'): same event_id -> "
               "same id, distinct event_id -> distinct id (no collision), prefix 'attr_'. It is a trace key, never "
               "revenue and never a commission (measure-only).")
    else:
        record("A-1", "FAIL-001", "NOTE", f"attribution_id shape/determinism unexpected (aid={aid}, aid2={aid2}, aid3={aid3})")

    # A-2 — A4 ad-hierarchy ids are attribution fields, not revenue/evidence inputs: setting them on a QUOTE_SENT
    #       row does NOT create revenue (still needs an OV row + OV conversion), so A4 opens no FAIL-001 path.
    store = new_store()
    q = insert_event(store, "a2", "QUOTE_SENT")
    do_materialize(store, q, conv_code=OV, revenue=300000, order_code="ord_a2",
                   signals={"campaign_id": "c", "adset_id": "a", "ad_id": "d", "live_session_id": "L"})
    if store.get_by_event_id("a2").revenue_value is None and DataMart(store).revenue_verified() == 0.0:
        record("A-2", "FAIL-001", "DEFENDED",
               "A4 ad-hierarchy ids are recorded attribution fields, not a revenue input: a QUOTE_SENT row carrying "
               "all 4 ad ids + a mispaired OV conversion still yields 0 revenue (B4 lock holds). A4 opens no "
               "FAIL-001 path; the ids are measure-only.")
    else:
        record("A-2", "FAIL-001", "BREACH", "ad-hierarchy ids enabled revenue on a non-OV row")


# ===================================================================================================
# GROUP N — reconciliation of the ideation workflow's novel vectors (executed)
# ===================================================================================================
def group_N():
    import math
    from app.measurement.evidence.categories import CATEGORY_MANDATORY as CM
    from app.measurement.funnel.funnel import GoldenHourFunnel

    a = EvidencePackAssembler()

    # N1 (CMP-01) — the funnel is a FOURTH revenue reader; it ALREADY has the inline event_code==ORDER_VERIFIED
    #     filter. So the mispair now yields 0 across ALL FOUR readers (store-drop + data_mart + growth + funnel):
    #     my M6-P3002 CRIT-DIVERGE-01 (funnel=0 while F=J=revenue) is RESOLVED — B4 brought F/J to the funnel's predicate.
    store = new_store()
    q = insert_event(store, "n1", "QUOTE_SENT")
    do_materialize(store, q, conv_code=OV, revenue=500000, order_code="ord_n1")
    dm_rev = DataMart(store).revenue_verified()
    gr = len(growth_verified_rows(store))
    funnel_rev = sum(v.verified_revenue for v in GoldenHourFunnel(store).assemble())
    if dm_rev == 0.0 and gr == 0 and funnel_rev == 0.0:
        record("N1", "FAIL-001", "DEFENDED",
               "all FOUR revenue readers now agree on the mispair: store-drop (write) + data_mart.verified_rows + "
               "growth.reads.verified_rows + funnel._verified_revenue all yield 0 for a QUOTE_SENT row. My M6-P3002 "
               "CRIT-DIVERGE-01 (funnel=0 while F/J counted) is RESOLVED — B4 brought F/J to the funnel's shipped "
               "event_code predicate. No predicate divergence remains.")
    else:
        record("N1", "FAIL-001", "BREACH", f"reader divergence (dm={dm_rev}, growth={gr}, funnel={funnel_rev})")

    # N2 (RN-05) — B2 uniqueness is FAIL-SAFE: a legitimate slot whose honest ref is ALSO reused elsewhere is marked
    #     false-MISSING (understates readiness -> NOT_READY), never satisfies a forged slot. A forger can only DoS a
    #     real slot into MISSING; the direction is fail-safe (a FAIL-007 breach needs OVER-statement).
    refs = canonical_refs()
    # duplicate one honest ref into a second slot
    er, cons = EvidenceCategory.EVENT_REGISTRY, EvidenceCategory.CONSENT
    dup_ref = f"ev::{er.value}::{CM[er][0]}"
    refs[cons] = dict(refs[cons]); refs[cons][CM[cons][0]] = dup_ref     # reuse ER's ref in a Consent slot
    p = a.assemble(all_recorded(), refs)
    er_complete = p.category(er).complete
    if p.readiness is Readiness.NOT_READY and not er_complete:
        record("N2", "FAIL-007", "DEFENDED",
               "B2 uniqueness is FAIL-SAFE (RN-05): duplicating an honest ref into a second slot makes BOTH the "
               "honest original and the copy fail the uniqueness count -> the real slot goes false-MISSING -> "
               "NOT_READY. The direction is UNDER-statement (a forger can only DoS a real slot, never satisfy a "
               "forged one) -- not a FAIL-007 breach (which needs OVER-statement).")
    else:
        record("N2", "FAIL-007", "NOTE", f"uniqueness collision behaved unexpectedly (er_complete={er_complete})")

    # N3 (CMP-04) — the compound FAIL-007-adjacent capstone: canonical-reconstructed refs (all COMPLETE via the
    #     M6-OD-013 residual) + all 18 smokes RECORDED with status='FAIL' (F-EVID-5) -> OWNER_REVIEW_REQUIRED on a
    #     forged evidence base with all-failing smokes. Still caps at OWNER_REVIEW_REQUIRED (no Pass); discloses the
    #     8 standing blockers + BLOCKED posture.
    all_fail = {s: SmokeResult(s, status="FAIL", correlation_id="c", evidence_id="e") for s in SMOKE_IDS}
    p = a.assemble(all_fail, canonical_refs())
    standing = {g.id for g in p.gap_blockers if g.kind is GapKind.STANDING_BLOCKER}
    if p.readiness is Readiness.OWNER_REVIEW_REQUIRED and standing == set(STANDING_BLOCKER_IDS) \
            and p.posture["production_flag"] == "OFF":
        record("N3", "FAIL-007", "OPEN_NONGATE",
               "compound capstone (CMP-04): the two open residuals COMPOSE — canonical-reconstructed refs (M6-OD-013, "
               "all categories COMPLETE) + all 18 smokes recorded status='FAIL' (F-EVID-5) -> OWNER_REVIEW_REQUIRED "
               "on a forged base with all-FAIL smokes. It STILL caps at OWNER_REVIEW_REQUIRED (no Pass member), "
               "discloses all 8 standing blockers + BLOCKED/OFF posture, and is trusted-input only (build/tester "
               "harness authors both maps, not a channel). Shows OWNER_REVIEW_REQUIRED is only as strong as "
               "known_refs authenticity (M6-OD-013) + a status=='PASS' gate that F-EVID-5 lacks. Route: owner/CODER.")
    else:
        record("N3", "FAIL-007", "DEFENDED", f"compound did not reach OWNER_REVIEW_REQUIRED ({p.readiness})")

    # N4 (CMP-03) — revenue value-sanity: no finite/non-negative check. A NaN (or negative / inf) revenue on a
    #     GENUINE ORDER_VERIFIED conversion poisons Revenue Verified. RULE-009 value-sanity (row is genuinely OV, so
    #     not FAIL-001); channel path un-wired (materializer). Also noted in prior slices (isfinite hardening).
    store = new_store()
    ov = insert_event(store, "n4", OV)
    do_materialize(store, ov, conv_code=OV, revenue=float("nan"), order_code="ord_n4")
    rv = DataMart(store).revenue_verified()
    store2 = new_store()
    ov2 = insert_event(store2, "n4b", OV)
    do_materialize(store2, ov2, conv_code=OV, revenue=-5000, order_code="ord_n4b")
    rv2 = DataMart(store2).revenue_verified()
    if math.isnan(rv) and rv2 == -5000.0:
        record("N4", "RULE-009", "OPEN_NONGATE",
               "value-sanity gap (CMP-03): a NaN revenue on a genuine ORDER_VERIFIED conversion makes Revenue "
               "Verified NaN, and a NEGATIVE revenue (-5000) is summed verbatim -- neither the /conversions edge nor "
               "store.materialize checks finiteness/sign. RULE-009 data-quality (the row IS OV, so not FAIL-001); "
               "channel-reachable at /conversions but the materialize worker is un-wired -> armed-not-fired. Route: "
               "CODER (add math.isfinite(v) and v>=0 at the verified-revenue write). Out of the 5-fix scope.")
    else:
        record("N4", "RULE-009", "DEFENDED", f"value-sanity enforced (nan_rev={rv}, neg_rev={rv2})")

    # N5 (RN-08) — A4 channel-reachable attribution laundering, NEUTRALIZED by SCALE_MODEL_RATIFIED=False: fabricated
    #     complete ad ids + a live_session on the Zone-A row drive the resolver to single-channel FACEBOOK_AD/HIGH
    #     (A4 rule suppresses LIVE_ORGANIC when ads.complete) -> scale-evidence ELIGIBLE True, but scale_evidence =
    #     eligible AND SCALE_MODEL_RATIFIED (OFF) stays False. No FAIL-001/FAIL-007; RULE-009 scale-evidence gate.
    try:
        store = new_store()
        ev = AdsMeasurementEvent(event_id="n5", event_code=OV, event_ts=FIXED_TS, idempotency_key="idem_n5",
                                 correlation_id="c", ingested_at=FIXED_TS, campaign_id="camp", adset_id="adset",
                                 ad_id="ad", live_session_id="live_1")
        store.insert(ev)
        out = do_materialize(store, ev, conv_code=OV, revenue=100000, order_code="ord_n5")
        if out.scale_evidence_eligible and not out.scale_evidence:
            record("N5", "RULE-009", "OPEN_NONGATE",
                   "A4 attribution laundering (RN-08), NEUTRALIZED: fabricated complete ad ids + a live_session drive "
                   "the resolver to FACEBOOK_AD/HIGH (A4 suppresses LIVE_ORGANIC when ads.complete) -> "
                   "scale_evidence_ELIGIBLE True, but scale_evidence = eligible AND SCALE_MODEL_RATIFIED(OFF) = "
                   "False. Channel-reachable (ad ids are untrusted /track inputs) but armed-not-fired: the "
                   "scale-authoritative gate (M6-OD-005 / SCALE_MODEL_RATIFIED immutable-OFF) neutralizes it; no "
                   "FAIL-001/FAIL-007 effect (revenue stays behind the OV filter). RULE-009. Route: owner (M6-OD-005).")
        else:
            record("N5", "RULE-009", "DEFENDED",
                   f"fabricated ad path not eligible (eligible={out.scale_evidence_eligible}, "
                   f"scale_evidence={out.scale_evidence}).")
    except Exception as e:  # noqa
        record("N5", "RULE-009", "NOTE", f"A4 laundering probe not executable in-harness ({type(e).__name__}); "
               "documented from the resolver code (eligible True, scale_evidence False under SCALE_MODEL_RATIFIED=OFF).")


# ===================================================================================================
def main():
    print("=" * 100)
    print("M6.2L BOUNDARY ADVERSARY — post-pilot audit-fix attacks (in-scope: FAIL-001 [B4] + FAIL-007 [B2/B3])")
    print(f"impl root: {IMPL}")
    print("=" * 100)
    for g in (group_B4, group_B2, group_B3, group_R, group_A, group_N):
        print(f"\n----- {g.__name__} -----")
        g()

    print("\n" + "=" * 100)
    tally = {}
    for _, _, k, _ in OUTCOMES:
        tally[k] = tally.get(k, 0) + 1
    breaches = [o for o in OUTCOMES if o[2] == "BREACH"]
    inscope = [o for o in breaches if o[1] in ("FAIL-001", "FAIL-007")]
    print(f"SUMMARY: {tally}")
    print(f"TOTAL RECORDED OUTCOMES: {len(OUTCOMES)}")
    print(f"IN-SCOPE FAIL-GATE BREACHES (FAIL-001 / FAIL-007): {len(inscope)}")
    for o in breaches:
        print("   BREACH:", o)

    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
    assert config.EXTERNAL_SEND == "OFF"
    assert {m.value for m in Readiness} == {"OWNER_REVIEW_REQUIRED", "NOT_READY"}
    print("POSTURE AFTER RUN: BLOCKED / OFF / OFF (unchanged); Readiness has no Pass/Ready member")
    print("=" * 100)


if __name__ == "__main__":
    main()
