"""Official smoke — slice M6.2K (full P0 re-run → owner evidence pack) — M6-SMK-017 (proposed — HARDENING, owner review).

Authored by TESTER in M6-P2003 (mode=build, "do not yet run"); EXECUTED and its recorded result
(correlation_id + evidence_id), OR an explicit owner waiver, captured in M6-P2004 (TESTER_RUN →
04-artifacts/test-reports/M6.2K/SMOKE_RESULTS.md).

This M6.2K leg proves the *evidence-recording* half of exit-gate leg 18 ("Proposed smoke M6-SMK-017 executed OR
explicitly waived by owner decision note"): the smoke's re-run result (or waiver) flows into the doc §22 owner
review package correctly. The *behavioral* half is the carried leg test_smk_017_hash_policy_no_raw_pii.py, re-run
as-is in the same staged suite. Governance is immutable: global_gateway_state=BLOCKED, production_flag=OFF,
external_send=OFF — nothing below flips a flag, and the pack NEVER declares ROAS Pass / Scale Ready and NEVER
self-certifies (M6-RULE-015; doc §23).

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (proposed additions row;
derivation doc §12 line 248, §22 line 429, M6.2D done gate line 388):

    Scenario (verbatim):   "External payload (CAPI/Offline) built from an event containing raw PII"
    Expected (verbatim):   "Hash policy applied per M6-OD-003; no raw phone/email/user-id in the outbound payload or
                           platform result log"

This M6.2K leg records the smoke's RESULT into the owner pack; it handles no raw identity itself (the behavioral
hash-policy proof is the carried M6.2D leg). Reuses the coder-provided M6.2K evidence-pack fixtures
(evidence_assembler, make_smoke_result, full_evidence_refs, all_smokes_recorded). All ids are synthetic;
correlation_id/evidence_id are masked on export (M6-RULE-014 / H02). M6-RULE-015 / M6-FAIL-007; exit-gate leg L1
(evidence pack ready) + the per-smoke recorded-result leg.
"""
from __future__ import annotations

from app.measurement.evidence.models import GapKind, Readiness
from app.measurement.evidence.smoke_registry import SmokeStatus, get_spec

_SMK = "M6-SMK-017"


# --- primary: the re-run result is recorded in the owner pack (scenario verbatim) -----------------
def test_smk_017_recorded_result_is_in_owner_pack(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    """M6-SMK-017 "External payload (CAPI/Offline) built from an event containing raw PII" -> "Hash policy applied
    per M6-OD-003; no raw phone/email/user-id in the outbound payload or platform result log".

    When M6-SMK-017 is re-run and its result recorded (status=PASS + correlation_id + evidence_id), the assembled
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


# --- negative / fail-closed: an un-run AND un-waived smoke can never be "recorded" ----------------
def test_smk_017_neg_unrun_and_unwaived_is_failclosed_not_ready(
    evidence_assembler, full_evidence_refs, all_smokes_recorded, make_smoke_result
):
    """Fail-closed (M6-FAIL-007): if M6-SMK-017 is neither run (no correlation_id + evidence_id) NOR owner-waived,
    it is NOT recorded, the pack raises an UNRUN gap for it, and readiness drops to NOT_READY — a proposed smoke
    cannot silently pass without either a result or a recorded waiver."""
    partial = dict(all_smokes_recorded)
    partial[_SMK] = make_smoke_result(_SMK, status=None, correlation_id=None, evidence_id=None, waived=False)
    pack = evidence_assembler.assemble(partial, full_evidence_refs)
    smk = next(s for s in pack.smokes if s.smoke_id == _SMK)
    assert smk.recorded is False
    assert pack.readiness is Readiness.NOT_READY
    assert any(g.kind is GapKind.UNRUN_SMOKE and _SMK in g.id for g in pack.gap_blockers)


# --- proposed-smoke waiver: executed OR explicitly owner-waived (M6.2K exit gate) -----------------
def test_smk_017_proposed_may_be_owner_waived(
    evidence_assembler, full_evidence_refs, all_smokes_recorded, make_smoke_result
):
    """M6-SMK-017 is `proposed — HARDENING (owner review)` — per the M6.2K exit gate it is executed OR explicitly
    owner-waived. A recorded owner waiver counts as recorded (still disclosed as `waived`), and readiness stays
    OWNER_REVIEW_REQUIRED — the proposed smoke is not forced un-run by an explicit owner waiver."""
    assert get_spec(_SMK).status is SmokeStatus.PROPOSED
    refs = dict(all_smokes_recorded)
    refs[_SMK] = make_smoke_result(_SMK, status=None, correlation_id=None, evidence_id=None, waived=True)
    pack = evidence_assembler.assemble(refs, full_evidence_refs)
    smk = next(s for s in pack.smokes if s.smoke_id == _SMK)
    assert smk.waived is True and smk.recorded is True           # a valid proposed-smoke waiver
    assert pack.readiness is Readiness.OWNER_REVIEW_REQUIRED


# --- PII-safe: the recorded ids are masked on export (M6-RULE-014 / H02) --------------------------
def test_smk_017_recorded_ids_masked_on_export(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    """The recorded correlation_id/evidence_id are masked on export — no raw id leaks into the pack's public view."""
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs)
    smk = next(s for s in pack.smokes if s.smoke_id == _SMK)
    pub = smk.to_public()
    assert pub["correlation_id"] != smk.correlation_id           # masked, not raw
    assert pub["evidence_id"] != smk.evidence_id
    assert smk.correlation_id not in str(pub) and smk.evidence_id not in str(pub)
