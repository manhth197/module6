"""M6.2K leg L1 / M6-FAIL-007: the 10 doc §22 evidence categories are assembled; a category missing its mandatory
content is INCOMPLETE (fail-closed) and forces the pack to NOT_READY. The pack never marks an evidence-less
category complete.
"""
from __future__ import annotations

from app.measurement.evidence.categories import CATEGORY_MANDATORY, EvidenceCategory
from app.measurement.evidence.models import Readiness


def test_all_ten_categories_present(evidence_assembler):
    pack = evidence_assembler.assemble()
    assert len(pack.categories) == 10
    assert {c.category for c in pack.categories} == set(EvidenceCategory)


def test_complete_evidence_marks_categories_complete(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs)
    assert all(c.complete for c in pack.categories)
    assert not pack.incomplete_categories()


def test_missing_content_is_incomplete_and_not_ready(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    # drop one mandatory key from Event Registry -> that category INCOMPLETE -> pack NOT_READY (FAIL-007)
    refs = {cat: dict(keys) for cat, keys in full_evidence_refs.items()}
    dropped = CATEGORY_MANDATORY[EvidenceCategory.EVENT_REGISTRY][0]     # "screenshot_api_db_record"
    del refs[EvidenceCategory.EVENT_REGISTRY][dropped]
    pack = evidence_assembler.assemble(all_smokes_recorded, refs)
    ev = pack.category(EvidenceCategory.EVENT_REGISTRY)
    assert ev.complete is False and dropped in ev.missing
    assert pack.readiness is Readiness.NOT_READY


def test_empty_pack_is_all_incomplete_and_not_ready(evidence_assembler):
    pack = evidence_assembler.assemble()          # no evidence, no smoke results
    assert all(not c.complete for c in pack.categories)   # fail-closed: nothing is complete without evidence
    assert pack.readiness is Readiness.NOT_READY


def test_category_1_keeps_screenshot_api_db_proof_form():
    assert "screenshot_api_db_record" in CATEGORY_MANDATORY[EvidenceCategory.EVENT_REGISTRY]
