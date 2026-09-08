"""Official smoke — slice M6.2O — M6-SMK-027 (proposed — HARDENING, owner review): F2-6 duck-coerce
(evidence-pack: caller `.recorded` is never trusted).

Authored by TESTER, now formalized on the ledger (M6-P2303 build / M6-P2304 run). F2-6 landed out-of-band in
impl/M6.2O; slice M6.2O retro-certifies the shipped code. EXECUTED + recorded in M6-P2304
(-> 04-artifacts/test-reports/M6.2O/SMOKE_RESULTS.md).

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (proposed additions row M6-SMK-027):

    Scenario (verbatim):   "A duck smoke object with a fake .recorded=True + blank status/correlation_id/evidence_id
                           for a mandatory owner smoke (F2-6)"
    Expected (verbatim):   "_smokes coerces it to a canonical SmokeResult, recomputes recorded=False → UNRUN_SMOKE gap
                           → pack NOT_READY (caller .recorded never trusted)"

Governance is immutable
here: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag; the pack
self-certifies nothing (RULE-015).

F2-6 is the code-exec-only twin of the M6.2M authenticity work (NOT channel-reachable): `EvidencePackAssembler._smokes`
now COERCES every provided smoke object into a canonical frozen `SmokeResult` rebuilt from its FIELDS, so `recorded`
is recomputed by `SmokeResult.recorded` (fail-closed) — a duck object with a fake `.recorded=True` + blank fields can
no longer mark a MANDATORY owner smoke recorded. It stays un-recorded -> UNRUN_SMOKE gap -> pack NOT_READY (FAIL-007).

Covers: the lying duck for a mandatory owner smoke (recorded recomputed False; UNRUN:M6-SMK-001; NOT_READY) + a
non-vacuous isolation (every OTHER smoke genuinely recorded, only M6-SMK-001 ducked -> readiness still flips to
NOT_READY) + a non-vacuity control (genuine results still record). Reuses the coder's F2-6 duck pattern + the shared
conftest fixtures (evidence_assembler, full_evidence_refs, all_smokes_recorded). All ids are synthetic governance refs.
"""
from __future__ import annotations

import types

from app.measurement.evidence.models import GapKind, Readiness, SmokeResult

_SMK = "M6-SMK-001"   # a MANDATORY owner smoke (doc §21 P0)


def _duck(smoke_id=_SMK, **over):
    """A lying duck: claims `.recorded=True` while its status/correlation_id/evidence_id are all None."""
    base = dict(smoke_id=smoke_id, status=None, correlation_id=None, evidence_id=None, waived=False, recorded=True)
    base.update(over)
    return types.SimpleNamespace(**base)


# --- primary smoke: a lying duck's .recorded is NOT trusted; the mandatory smoke stays un-recorded ---
def test_f2_6_duck_recorded_is_not_trusted_mandatory_smoke_unrecorded(evidence_assembler, full_evidence_refs):
    """A duck SimpleNamespace(recorded=True, status/correlation_id/evidence_id=None) for the MANDATORY owner smoke
    M6-SMK-001 is coerced to a canonical SmokeResult whose `recorded` is RECOMPUTED from its (blank) fields -> False;
    the assembled pack raises an UNRUN:M6-SMK-001 gap and readiness is NOT_READY (the fake .recorded is ignored)."""
    duck = _duck(_SMK)
    pack = evidence_assembler.assemble(smoke_results={_SMK: duck}, evidence_refs=full_evidence_refs)
    smk = next(s for s in pack.smokes if s.smoke_id == _SMK)
    assert isinstance(smk, SmokeResult)                         # coerced to the canonical frozen type
    assert smk.recorded is False                                # recomputed from fields; the duck's fake .recorded ignored
    assert pack.readiness is Readiness.NOT_READY
    assert any(g.kind is GapKind.UNRUN_SMOKE and _SMK in g.id for g in pack.gap_blockers)


# --- negative / non-vacuous isolation: only the duck flips readiness ------------------------------
def test_f2_6_duck_alone_flips_readiness_when_all_others_recorded(
    evidence_assembler, full_evidence_refs, all_smokes_recorded
):
    """Isolation (non-vacuous): every OTHER of the 18 smokes is genuinely recorded; ONLY M6-SMK-001 is a lying duck.
    Readiness still drops to NOT_READY — proving the duck is what flips it (without the F2-6 coercion the trusted
    fake .recorded=True would have left the pack OWNER_REVIEW_REQUIRED)."""
    refs = dict(all_smokes_recorded)
    refs[_SMK] = _duck(_SMK)
    pack = evidence_assembler.assemble(refs, full_evidence_refs)
    assert next(s for s in pack.smokes if s.smoke_id == _SMK).recorded is False
    assert pack.readiness is Readiness.NOT_READY


# --- positive control: genuine SmokeResults still record (the coercion does not over-reject) ------
def test_f2_6_control_genuine_smoke_results_still_record(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    """Non-vacuity control: with the honest all_smokes_recorded set (real frozen SmokeResults) every smoke still
    records and the pack reaches OWNER_REVIEW_REQUIRED — the coercion rejects lying ducks, not legitimate results."""
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs)
    assert all(s.recorded for s in pack.smokes)
    assert pack.readiness is Readiness.OWNER_REVIEW_REQUIRED
