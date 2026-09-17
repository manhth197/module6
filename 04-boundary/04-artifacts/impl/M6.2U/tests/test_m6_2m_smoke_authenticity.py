"""M6.2M leg 2 / M6-SMK-025 / M6-OD-013 (smoke-side twin) / RULE-015 / FAIL-007: SmokeResult.recorded (+ _smokes)
require STRIPPED-non-blank status/correlation_id/evidence_id, not raw truthiness. A whitespace / fake-but-nonblank
SmokeResult for a MANDATORY owner smoke is NOT recorded -> it stays un-recorded -> UNRUN_SMOKE gap -> pack NOT_READY.
A genuinely-recorded result still records (non-vacuous control); _smokes normalizes whitespace-only fields to None.
"""
from __future__ import annotations

from app.measurement.evidence.models import GapKind, Readiness, SmokeResult
from app.measurement.evidence.smoke_registry import SmokeStatus, get_spec

_SMK = "M6-SMK-001"   # a MANDATORY owner smoke (doc §21 P0)


def test_whitespace_fields_are_not_recorded_property():
    assert get_spec(_SMK).status is SmokeStatus.OWNER
    r = SmokeResult(smoke_id=_SMK, status="   ", correlation_id="\t", evidence_id="  ")
    assert r.recorded is False          # stripped-non-blank required (bool("  ") is True but must not count)
    # a genuine result IS recorded (discriminating)
    assert SmokeResult(smoke_id=_SMK, status="PASS", correlation_id="corr_1", evidence_id="ev_1").recorded is True


def test_whitespace_mandatory_smoke_forces_not_ready(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    refs = dict(all_smokes_recorded)
    refs[_SMK] = SmokeResult(smoke_id=_SMK, status="   ", correlation_id="  ", evidence_id="\n")   # fake-but-nonblank
    pack = evidence_assembler.assemble(refs, full_evidence_refs)
    smk = next(s for s in pack.smokes if s.smoke_id == _SMK)
    assert smk.recorded is False
    assert pack.readiness is Readiness.NOT_READY
    assert any(g.kind is GapKind.UNRUN_SMOKE and _SMK in g.id for g in pack.gap_blockers)


def test_smokes_normalizes_whitespace_fields_to_none(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    refs = dict(all_smokes_recorded)
    refs[_SMK] = SmokeResult(smoke_id=_SMK, status="  ", correlation_id="  ", evidence_id="  ")
    pack = evidence_assembler.assemble(refs, full_evidence_refs)
    smk = next(s for s in pack.smokes if s.smoke_id == _SMK)
    assert smk.status is None and smk.correlation_id is None and smk.evidence_id is None   # normalized, not masqueraded
    pub = smk.to_public()
    assert pub["status"] is None and pub["recorded"] is False


def test_genuine_recorded_smokes_all_record(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs)
    assert all(s.recorded for s in pack.smokes)                # non-vacuous: real traces still record
    assert pack.readiness is Readiness.OWNER_REVIEW_REQUIRED
