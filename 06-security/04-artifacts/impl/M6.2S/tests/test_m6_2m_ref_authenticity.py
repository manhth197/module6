"""M6.2M leg 1 / M6-SMK-024 / M6-OD-013 (ref-side) / RULE-015 / FAIL-007: with a staged known-refs allowlist, a ref
that is shape-valid + correctly (category,key)-bound + unique but was NEVER issued (not in the allowlist) is
REJECTED (category MISSING) — authenticity beyond slot-correctness, defeating canonical-string reconstruction. With
NO allowlist the M6.2L slot-correctness bar still holds (no regression). The real issued-refs registry is
owner-populated; here the allowlist is a staged set built inline from the genuine issued refs.
"""
from __future__ import annotations

from app.measurement.evidence.categories import CATEGORY_MANDATORY, EvidenceCategory
from app.measurement.evidence.models import Readiness


def test_reconstructed_canonical_ref_not_issued_is_missing(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    target_cat = EvidenceCategory.DEDUP
    target_key = CATEGORY_MANDATORY[target_cat][0]
    # staged issued-refs allowlist = every genuine ref EXCEPT the target slot's (i.e. that ref was never issued)
    allow = {v for cat, keys in full_evidence_refs.items() for k, v in keys.items()
             if not (cat is target_cat and k == target_key)}
    # the pack still carries the correctly-reconstructed canonical ref for the target slot (shape-valid + bound + unique)
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs, known_refs=allow)
    assert pack.category(target_cat).complete is False                      # not issued -> authenticity rejects it
    assert all(c.complete for c in pack.categories if c.category is not target_cat)   # issued refs still complete
    assert pack.readiness is Readiness.NOT_READY


def test_no_allowlist_keeps_slot_correctness_no_regression(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs)      # no oracle -> M6.2L behaviour
    assert all(c.complete for c in pack.categories)
    assert pack.readiness is Readiness.OWNER_REVIEW_REQUIRED


def test_fully_issued_allowlist_is_all_complete(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    allow = {v for keys in full_evidence_refs.values() for v in keys.values()}       # every ref genuinely issued
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs, known_refs=allow)
    assert all(c.complete for c in pack.categories)                                  # non-vacuous control
    assert pack.readiness is Readiness.OWNER_REVIEW_REQUIRED
