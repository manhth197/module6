"""M6.2L leg 3 / M6-SMK-021 / M6-OD-013 / RULE-015 / FAIL-007: pack_assembler category-completeness validates
evidence-ref EXISTENCE + UNIQUENESS + CATEGORY-BINDING, not raw truthiness. A fake-but-nonblank ref, or one valid
ref copy-pasted across all mandatory keys of all 10 categories, leaves categories MISSING (never COMPLETE) and the
pack NOT_READY. A genuine unique + category-bound ref set is still all-COMPLETE (non-vacuous control).
"""
from __future__ import annotations

from app.measurement.evidence.categories import CATEGORY_MANDATORY, EvidenceCategory
from app.measurement.evidence.models import Readiness


def test_fake_but_nonblank_ref_leaves_category_missing_not_ready(
    evidence_assembler, full_evidence_refs, all_smokes_recorded
):
    refs = {cat: dict(keys) for cat, keys in full_evidence_refs.items()}
    cat = EvidenceCategory.EVENT_REGISTRY
    refs[cat] = {k: "x" for k in refs[cat]}          # fake-but-nonblank junk (passes raw truthiness, fails existence)
    pack = evidence_assembler.assemble(all_smokes_recorded, refs)
    ev = pack.category(cat)
    assert ev.complete is False and set(ev.missing) == set(CATEGORY_MANDATORY[cat])
    assert pack.readiness is Readiness.NOT_READY


def test_one_valid_ref_copy_pasted_across_all_categories_is_all_missing(evidence_assembler, all_smokes_recorded):
    one = "ev::Event Registry::screenshot_api_db_record"   # a single VALID-looking ref, reused for EVERY key
    refs = {cat: {k: one for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}
    pack = evidence_assembler.assemble(all_smokes_recorded, refs)
    # uniqueness (reused > once) AND category-binding (bound only to Event Registry) both reject it everywhere
    assert all(not c.complete for c in pack.categories)
    assert pack.readiness is Readiness.NOT_READY


def test_genuine_unique_bound_refs_are_all_complete(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs)
    assert all(c.complete for c in pack.categories)       # non-vacuous: the honest ref set still completes
    assert pack.readiness is Readiness.OWNER_REVIEW_REQUIRED


def test_wrong_category_binding_alone_is_missing(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    # a ref that EXISTS + is UNIQUE but is bound to the WRONG category (Consent ref placed in Dedup) is rejected
    refs = {cat: dict(keys) for cat, keys in full_evidence_refs.items()}
    dedup = EvidenceCategory.DEDUP
    only_key = CATEGORY_MANDATORY[dedup][0]
    refs[dedup] = {only_key: "ev::Consent::consent_pass_UNIQUE"}   # unique, well-formed, but bound to Consent
    pack = evidence_assembler.assemble(all_smokes_recorded, refs)
    assert pack.category(dedup).complete is False
    assert pack.readiness is Readiness.NOT_READY


def test_convention_shaped_wrong_key_forgery_is_missing(evidence_assembler, all_smokes_recorded):
    # A distinct, unique, right-CATEGORY but WRONG-KEY convention-shaped ref (ev::{category}::FORGED) must NOT
    # complete a category: binding is (category, key), not category alone (defeats the convention-aware forgery).
    from app.measurement.evidence.categories import CATEGORY_MANDATORY as CM
    forged = {cat: {k: f"ev::{cat.value}::FORGED_{i}_{j}" for j, k in enumerate(keys)}
              for i, (cat, keys) in enumerate(CM.items())}
    pack = evidence_assembler.assemble(all_smokes_recorded, forged)
    assert all(not c.complete for c in pack.categories)   # right category, wrong key -> unbound -> MISSING
    assert pack.readiness is Readiness.NOT_READY


def test_known_refs_authenticity_oracle_tightens_existence(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    # Forward seam (M6-OD-013): when an issued-refs authenticity oracle IS supplied, a well-formed + correctly-bound
    # ref that is NOT in the oracle fails existence -> category MISSING (default path accepts it as slot-correct).
    refs = {cat: dict(keys) for cat, keys in full_evidence_refs.items()}
    empty_oracle: set = set()                              # no ref is 'issued' -> nothing authenticates
    pack = evidence_assembler.assemble(all_smokes_recorded, refs, known_refs=empty_oracle)
    assert all(not c.complete for c in pack.categories)
    assert pack.readiness is Readiness.NOT_READY
