"""Official smoke — slice M6.2M — M6-SMK-024 (proposed — HARDENING, owner review).

Authored by TESTER in M6-P2203 (mode=build, "do not yet run"); EXECUTED and its result recorded in M6-P2204
(TESTER_RUN -> 04-artifacts/test-reports/M6.2M/SMOKE_RESULTS.md). Closes the M6-OD-013 ref-side authenticity residual
disclosed at the M6.2L re-judge (2026-09-03). Governance is immutable here: global_gateway_state=BLOCKED,
production_flag=OFF, external_send=OFF — nothing below flips a flag; the pack self-certifies nothing (RULE-015).

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (proposed additions row M6-SMK-024):

    Scenario (verbatim):   "Evidence pack assembled with a known-refs allowlist + a ref that is shape-valid, uniquely
                           used, correctly (category,key)-bound, but NOT in the allowlist (canonical-string
                           reconstruction)"
    Expected (verbatim):   "that category reads MISSING (authenticity, not just slot-correctness); with no allowlist
                           the M6.2L slot-correctness bar still holds (no regression)"

M6.2L closed the shape-only forgeries (junk / copy-paste / wrong-binding), but a forger reconstructing the exact
canonical `ev::{category}::{key}` string would still pass in the default (no-oracle) path. M6.2M proves the forward
seam: when a `known_refs` allowlist IS supplied, a shape-valid + correctly-bound + unique ref that was never issued
(not in the allowlist) is REJECTED -> category MISSING -> pack NOT_READY (authenticity, FAIL-007). The staged
allowlist is a set built inline from the genuine issued refs; the real issued-refs registry stays owner-populated
(out of scope). Reuses the coder's M6.2M ref-authenticity leg pattern + the shared conftest fixtures
(evidence_assembler, full_evidence_refs, all_smokes_recorded).
"""
from __future__ import annotations

from app.measurement.evidence.categories import CATEGORY_MANDATORY, EvidenceCategory
from app.measurement.evidence.models import Readiness


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_024_reconstructed_canonical_ref_not_issued_is_missing(
    evidence_assembler, full_evidence_refs, all_smokes_recorded
):
    """M6-SMK-024 "Evidence pack assembled with a known-refs allowlist + a ref that is shape-valid, uniquely used,
    correctly (category,key)-bound, but NOT in the allowlist (canonical-string reconstruction)" -> "that category
    reads MISSING (authenticity, not just slot-correctness) ...".

    The pack still carries the correctly-reconstructed canonical ref for the target slot (shape-valid + (category,key)
    bound + unique) — everything M6.2L checked. But the staged issued-refs allowlist OMITS that one ref (it was never
    issued), so authenticity rejects it: the target category is MISSING while every issued-ref category stays
    COMPLETE, and the pack is NOT_READY.
    """
    target_cat = EvidenceCategory.DEDUP
    target_key = CATEGORY_MANDATORY[target_cat][0]
    allow = {v for cat, keys in full_evidence_refs.items() for k, v in keys.items()
             if not (cat is target_cat and k == target_key)}   # every genuine ref EXCEPT the target slot's
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs, known_refs=allow)
    assert pack.category(target_cat).complete is False                                  # not issued -> rejected
    assert all(c.complete for c in pack.categories if c.category is not target_cat)     # issued refs still complete
    assert pack.readiness is Readiness.NOT_READY


# --- negative / no-regression: with NO allowlist the M6.2L slot-correctness bar still holds -------
def test_smk_024_neg_no_allowlist_keeps_slot_correctness_no_regression(
    evidence_assembler, full_evidence_refs, all_smokes_recorded
):
    """"... with no allowlist the M6.2L slot-correctness bar still holds (no regression)": without an oracle the
    genuine, unique, correctly-bound ref set still completes every category and reaches OWNER_REVIEW_REQUIRED — the
    authenticity check is opt-in and does not tighten the default path."""
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs)
    assert all(c.complete for c in pack.categories)
    assert pack.readiness is Readiness.OWNER_REVIEW_REQUIRED


# --- positive control: a fully-issued allowlist is all-COMPLETE (discriminating, non-vacuous) -----
def test_smk_024_control_fully_issued_allowlist_all_complete(
    evidence_assembler, full_evidence_refs, all_smokes_recorded
):
    """Non-vacuity / discriminating control: when EVERY ref is genuinely issued (in the allowlist), all categories
    complete and the pack reaches OWNER_REVIEW_REQUIRED — so a category is COMPLETE iff its ref is issued (the
    rejection above is authenticity-caused, not the oracle rejecting everything)."""
    allow = {v for keys in full_evidence_refs.values() for v in keys.values()}
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs, known_refs=allow)
    assert all(c.complete for c in pack.categories)
    assert pack.readiness is Readiness.OWNER_REVIEW_REQUIRED
