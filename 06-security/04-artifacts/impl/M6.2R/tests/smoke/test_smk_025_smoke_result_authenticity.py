"""Official smoke — slice M6.2M — M6-SMK-025 (proposed — HARDENING, owner review).

Authored by TESTER in M6-P2203 (mode=build, "do not yet run"); EXECUTED and its result recorded in M6-P2204
(TESTER_RUN -> 04-artifacts/test-reports/M6.2M/SMOKE_RESULTS.md). Closes the M6-OD-013 smoke-side authenticity twin
(doc B2 Ghi chú "vá cả hai một lượt"). Governance is immutable here: global_gateway_state=BLOCKED,
production_flag=OFF, external_send=OFF — nothing below flips a flag; the pack self-certifies nothing (RULE-015).

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (proposed additions row M6-SMK-025):

    Scenario (verbatim):   "SmokeResult for a mandatory owner smoke carries whitespace / fake-but-nonblank
                           status/correlation_id/evidence_id"
    Expected (verbatim):   "recorded() is False (stripped-non-blank required, not raw truthiness); the mandatory smoke
                           stays un-recorded → pack NOT_READY"

The ref-side twin (SMK-024) hardens evidence refs; this is its smoke-side pair. `SmokeResult.recorded` now requires
STRIPPED-non-blank status + correlation_id + evidence_id — `bool("  ")` is True but a whitespace field is not a real
recorded value. A whitespace / fake-but-nonblank SmokeResult for a MANDATORY owner smoke stays un-recorded ->
UNRUN_SMOKE gap -> pack NOT_READY (fail-closed, FAIL-007); the assembler's `_smokes` also normalizes whitespace-only
fields to None so nothing masquerades on export. Reuses the coder's M6.2M smoke-authenticity leg pattern + the shared
conftest fixtures (evidence_assembler, full_evidence_refs, all_smokes_recorded).
"""
from __future__ import annotations

from app.measurement.evidence.models import GapKind, Readiness, SmokeResult
from app.measurement.evidence.smoke_registry import SmokeStatus, get_spec

_SMK = "M6-SMK-001"   # a MANDATORY owner smoke (doc §21 P0)


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_025_whitespace_mandatory_smoke_is_unrecorded_and_not_ready(
    evidence_assembler, full_evidence_refs, all_smokes_recorded
):
    """M6-SMK-025 "SmokeResult for a mandatory owner smoke carries whitespace / fake-but-nonblank
    status/correlation_id/evidence_id" -> "recorded() is False (stripped-non-blank required, not raw truthiness); the
    mandatory smoke stays un-recorded → pack NOT_READY".

    A fake-but-nonblank (whitespace) SmokeResult replaces a mandatory owner smoke's genuine result. recorded() is
    False; in the assembled pack the smoke stays un-recorded, an UNRUN_SMOKE gap carries its id, and readiness is
    NOT_READY.
    """
    assert get_spec(_SMK).status is SmokeStatus.OWNER
    refs = dict(all_smokes_recorded)
    refs[_SMK] = SmokeResult(smoke_id=_SMK, status="   ", correlation_id="  ", evidence_id="\n")   # fake-but-nonblank
    assert refs[_SMK].recorded is False                                    # stripped-non-blank required
    pack = evidence_assembler.assemble(refs, full_evidence_refs)
    smk = next(s for s in pack.smokes if s.smoke_id == _SMK)
    assert smk.recorded is False
    assert pack.readiness is Readiness.NOT_READY
    assert any(g.kind is GapKind.UNRUN_SMOKE and _SMK in g.id for g in pack.gap_blockers)


# --- negative / property: stripped-non-blank required, not raw truthiness (discriminating) --------
def test_smk_025_neg_recorded_requires_stripped_non_blank_not_raw_truthiness():
    """The `recorded` property: whitespace fields (each individually truthy — bool("  ") is True) do NOT count, but a
    genuine stripped-non-blank trace DOES — so the bar is authenticity, not raw truthiness."""
    blank = SmokeResult(smoke_id=_SMK, status="   ", correlation_id="\t", evidence_id="  ")
    assert blank.recorded is False
    genuine = SmokeResult(smoke_id=_SMK, status="PASS", correlation_id="corr_1", evidence_id="ev_1")
    assert genuine.recorded is True


# --- negative / defense-in-depth: _smokes normalizes whitespace fields to None (no masquerade) ----
def test_smk_025_neg_assembler_normalizes_whitespace_fields_to_none(
    evidence_assembler, full_evidence_refs, all_smokes_recorded
):
    """The assembler's `_smokes` normalizes whitespace-only status/correlation_id/evidence_id to None, so a
    fake-but-nonblank field cannot masquerade as data on export (to_public shows None + recorded False)."""
    refs = dict(all_smokes_recorded)
    refs[_SMK] = SmokeResult(smoke_id=_SMK, status="  ", correlation_id="  ", evidence_id="  ")
    pack = evidence_assembler.assemble(refs, full_evidence_refs)
    smk = next(s for s in pack.smokes if s.smoke_id == _SMK)
    assert smk.status is None and smk.correlation_id is None and smk.evidence_id is None
    pub = smk.to_public()
    assert pub["status"] is None and pub["recorded"] is False


# --- positive control: genuine recorded results still record (non-vacuous) ------------------------
def test_smk_025_control_genuine_recorded_smokes_all_record(
    evidence_assembler, full_evidence_refs, all_smokes_recorded
):
    """Non-vacuity control: the honest all_smokes_recorded set (real stripped-non-blank traces) still records every
    smoke and reaches OWNER_REVIEW_REQUIRED — the tightening rejects blanks, not legitimate results."""
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs)
    assert all(s.recorded for s in pack.smokes)
    assert pack.readiness is Readiness.OWNER_REVIEW_REQUIRED
