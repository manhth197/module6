"""Official smoke — slice M6.2K (full P0 re-run → owner evidence pack) — M6-SMK-009 (doc ADS-P0-009).

Authored by TESTER in M6-P2003 (mode=build, "do not yet run"); EXECUTED and its recorded result
(correlation_id + evidence_id) captured in M6-P2004 (TESTER_RUN → 04-artifacts/test-reports/M6.2K/SMOKE_RESULTS.md).

This M6.2K leg proves the *evidence-recording* half of exit-gate leg 10 ("Smoke M6-SMK-009 executed with recorded
result and evidence ref"): the smoke's re-run result flows into the doc §22 owner review package correctly. The
*behavioral* half is the carried leg test_smk_009_recall_sale_lock_scale_fail.py, re-run as-is in the same staged
suite. Governance is immutable: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below
flips a flag, and the pack NEVER declares ROAS Pass / Scale Ready and NEVER self-certifies (M6-RULE-015; doc §23).

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 409):

    Kịch bản (verbatim):          "Recall/Sale Lock active"
    Kết quả phải đạt (verbatim):  "Scale Gate FAIL/HOLD"

Reuses the coder-provided M6.2K evidence-pack fixtures (evidence_assembler, make_smoke_result, full_evidence_refs,
all_smokes_recorded). All ids are synthetic; correlation_id/evidence_id are masked on export (M6-RULE-014 / H02).
M6-RULE-015 / M6-FAIL-007; exit-gate leg L1 (evidence pack ready) + the per-smoke recorded-result leg.
"""
from __future__ import annotations

from app.measurement.evidence.models import GapKind, Readiness
from app.measurement.evidence.smoke_registry import SmokeStatus, get_spec

_SMK = "M6-SMK-009"


# --- primary: the re-run result is recorded in the owner pack (scenario verbatim) -----------------
def test_smk_009_recorded_result_is_in_owner_pack(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    """M6-SMK-009 "Recall/Sale Lock active" -> "Scale Gate FAIL/HOLD".

    When M6-SMK-009 is re-run and its result recorded (status=PASS + correlation_id + evidence_id), the assembled
    owner review package lists it as `recorded`; with the full P0 matrix recorded and all 10 doc §22 categories
    complete, readiness reaches the terminal OWNER_REVIEW_REQUIRED (never Pass/Ready), while still disclosing every
    standing blocker. That recorded result IS the per-smoke evidence ref the exit gate requires.
    """
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs)
    smk = next(s for s in pack.smokes if s.smoke_id == _SMK)
    assert smk.recorded is True
    assert smk.status == "PASS" and smk.correlation_id and smk.evidence_id   # a real run trace, not a bare flag
    assert pack.readiness is Readiness.OWNER_REVIEW_REQUIRED                  # terminal — never Pass/Ready
    assert pack.has_standing_blockers()                                      # honest hand-off still discloses them


# --- negative / fail-closed: an un-run smoke can never be "recorded" ------------------------------
def test_smk_009_neg_unrun_is_failclosed_not_ready(
    evidence_assembler, full_evidence_refs, all_smokes_recorded, make_smoke_result
):
    """Fail-closed (M6-FAIL-007): if M6-SMK-009 is un-run (no correlation_id + evidence_id), it is NOT recorded, the
    pack raises an UNRUN gap for it, and readiness drops to NOT_READY — the smoke cannot silently pass."""
    partial = dict(all_smokes_recorded)
    partial[_SMK] = make_smoke_result(_SMK, status=None, correlation_id=None, evidence_id=None)
    pack = evidence_assembler.assemble(partial, full_evidence_refs)
    smk = next(s for s in pack.smokes if s.smoke_id == _SMK)
    assert smk.recorded is False
    assert pack.readiness is Readiness.NOT_READY
    assert any(g.kind is GapKind.UNRUN_SMOKE and _SMK in g.id for g in pack.gap_blockers)


# --- negative / fail-closed: a mandatory owner smoke can never be owner-waived un-run -------------
def test_smk_009_neg_owner_smoke_waiver_is_stripped(
    evidence_assembler, full_evidence_refs, all_smokes_recorded, make_smoke_result
):
    """M6-SMK-009 is an OWNER smoke (doc §21 P0), not `proposed` — an owner waiver is INVALID and is stripped by the
    assembler, so an un-run owner smoke can never vanish from the honest gap list via a waiver (FAIL-007 defense-in-
    depth). It stays un-run → NOT_READY."""
    assert get_spec(_SMK).status is SmokeStatus.OWNER
    refs = dict(all_smokes_recorded)
    refs[_SMK] = make_smoke_result(_SMK, status=None, correlation_id=None, evidence_id=None, waived=True)
    pack = evidence_assembler.assemble(refs, full_evidence_refs)
    smk = next(s for s in pack.smokes if s.smoke_id == _SMK)
    assert smk.waived is False and smk.recorded is False         # the invalid owner waiver is stripped
    assert pack.readiness is Readiness.NOT_READY


# --- PII-safe: the recorded ids are masked on export (M6-RULE-014 / H02) --------------------------
def test_smk_009_recorded_ids_masked_on_export(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    """The recorded correlation_id/evidence_id are masked on export — no raw id leaks into the pack's public view."""
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs)
    smk = next(s for s in pack.smokes if s.smoke_id == _SMK)
    pub = smk.to_public()
    assert pub["correlation_id"] != smk.correlation_id           # masked, not raw
    assert pub["evidence_id"] != smk.evidence_id
    assert smk.correlation_id not in str(pub) and smk.evidence_id not in str(pub)
