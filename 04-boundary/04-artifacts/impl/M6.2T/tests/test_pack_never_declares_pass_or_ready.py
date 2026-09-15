"""M6.2K leg L1 / M6-RULE-015 / doc §23: the pack NEVER declares ROAS Pass / Scale Ready and NEVER self-certifies.
The readiness enum has no PASS/READY member; readiness tops out at OWNER_REVIEW_REQUIRED (per §4.4); the assembler
exposes no pass/ready/certify/sign_off/approve/enable/flag-flip method.
"""
from __future__ import annotations

from app.measurement.evidence.models import Readiness

_FORBIDDEN = (
    "pass", "ready", "roas_pass", "scale_ready", "certify", "self_certify", "sign_off", "signoff",
    "approve", "enable", "flip", "set_flag", "set_production_flag", "declare_ready", "mark_pass",
)


def test_readiness_enum_has_no_pass_or_ready_member():
    members = {m.value for m in Readiness}
    assert members == {"OWNER_REVIEW_REQUIRED", "NOT_READY"}
    assert not any(x in members for x in ("PASS", "READY", "ROAS_PASS", "SCALE_READY"))


def test_complete_pack_reaches_owner_review_required(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs)
    assert pack.readiness is Readiness.OWNER_REVIEW_REQUIRED   # the terminal state — never Pass/Ready


def test_incomplete_or_unrun_forces_not_ready(evidence_assembler, full_evidence_refs, all_smokes_recorded, make_smoke_result):
    # one smoke un-run (no correlation/evidence) -> NOT_READY
    partial = dict(all_smokes_recorded)
    partial["M6-SMK-006"] = make_smoke_result("M6-SMK-006", status=None, correlation_id=None, evidence_id=None)
    pack = evidence_assembler.assemble(partial, full_evidence_refs)
    assert pack.readiness is Readiness.NOT_READY
    assert any(s.smoke_id == "M6-SMK-006" and not s.recorded for s in pack.smokes)


def test_proposed_smoke_may_be_owner_waived(evidence_assembler, full_evidence_refs, all_smokes_recorded, make_smoke_result):
    # a proposed smoke waived by the owner counts as recorded (executed OR waived) -> still OWNER_REVIEW_REQUIRED
    refs = dict(all_smokes_recorded)
    refs["M6-SMK-017"] = make_smoke_result("M6-SMK-017", status=None, correlation_id=None, evidence_id=None, waived=True)
    pack = evidence_assembler.assemble(refs, full_evidence_refs)
    assert pack.readiness is Readiness.OWNER_REVIEW_REQUIRED
    assert next(s for s in pack.smokes if s.smoke_id == "M6-SMK-017").recorded


def test_owner_smoke_waiver_is_invalid_and_stays_not_ready(evidence_assembler, full_evidence_refs, all_smokes_recorded, make_smoke_result):
    """Defense-in-depth (adversarial review): a waiver is valid ONLY for a proposed smoke. Waiving a MANDATORY
    owner smoke (SMK-001, doc §21 P0) un-run must NOT count as recorded — it stays un-run → UNRUN_SMOKE gap +
    NOT_READY (fail-closed, FAIL-007). A mandatory smoke can never vanish from the honest gap list via a waiver."""
    from app.measurement.evidence.models import GapKind
    refs = dict(all_smokes_recorded)
    refs["M6-SMK-001"] = make_smoke_result("M6-SMK-001", status=None, correlation_id=None, evidence_id=None, waived=True)
    pack = evidence_assembler.assemble(refs, full_evidence_refs)
    smk = next(s for s in pack.smokes if s.smoke_id == "M6-SMK-001")
    assert smk.waived is False and smk.recorded is False           # the invalid owner waiver is stripped
    assert pack.readiness is Readiness.NOT_READY
    assert any(g.kind is GapKind.UNRUN_SMOKE and "M6-SMK-001" in g.id for g in pack.gap_blockers)


def test_assembler_exposes_no_self_cert_or_flag_flip_method(evidence_assembler):
    for verb in _FORBIDDEN:
        assert not hasattr(evidence_assembler, verb), f"assembler exposes forbidden verb {verb!r} (RULE-015; doc §23)"
    assert callable(getattr(evidence_assembler, "assemble"))
