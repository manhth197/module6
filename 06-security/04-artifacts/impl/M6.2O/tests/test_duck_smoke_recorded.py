"""F2-6 (code-exec-only hardening; NOT channel-reachable) / M6-FAIL-007 / RULE-015: the assembler must never trust a
caller-supplied `.recorded`. `_smokes` coerces every provided object to a canonical SmokeResult rebuilt from its
FIELDS, so a duck object with `.recorded=True` + blank fields cannot mark a mandatory smoke recorded — its
recorded-ness is recomputed (fail-closed), it stays un-recorded → UNRUN_SMOKE gap → pack NOT_READY.
"""
from __future__ import annotations

import types

from app.measurement.evidence.models import GapKind, Readiness, SmokeResult


def _duck(smoke_id="M6-SMK-001", **over):
    base = dict(smoke_id=smoke_id, status=None, correlation_id=None, evidence_id=None, waived=False, recorded=True)
    base.update(over)
    return types.SimpleNamespace(**base)


def test_duck_recorded_is_not_trusted(evidence_assembler, full_evidence_refs):
    # a lying duck (blank fields but .recorded=True) for a MANDATORY owner smoke must NOT count as recorded
    duck = _duck("M6-SMK-001")
    pack = evidence_assembler.assemble(smoke_results={"M6-SMK-001": duck}, evidence_refs=full_evidence_refs)
    smk = next(s for s in pack.smokes if s.smoke_id == "M6-SMK-001")
    assert isinstance(smk, SmokeResult)                     # coerced to the canonical frozen type
    assert smk.recorded is False                            # recomputed from fields; the duck's fake .recorded ignored
    assert pack.readiness is Readiness.NOT_READY
    assert any(g.kind is GapKind.UNRUN_SMOKE and "M6-SMK-001" in g.id for g in pack.gap_blockers)


def test_duck_flips_readiness_when_all_others_recorded(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    # isolate: every OTHER smoke genuinely recorded; only M6-SMK-001 is a lying duck -> readiness must drop to
    # NOT_READY (without the fix, the trusted duck .recorded=True would leave it OWNER_REVIEW_REQUIRED).
    refs = dict(all_smokes_recorded)
    refs["M6-SMK-001"] = _duck("M6-SMK-001")
    pack = evidence_assembler.assemble(refs, full_evidence_refs)
    assert pack.readiness is Readiness.NOT_READY
    assert next(s for s in pack.smokes if s.smoke_id == "M6-SMK-001").recorded is False


def test_real_smoke_result_still_records(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    # non-vacuity: genuine SmokeResults (real trace) still record -> the coercion does not over-reject
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs)
    assert all(s.recorded for s in pack.smokes)
    assert pack.readiness is Readiness.OWNER_REVIEW_REQUIRED
