"""Official smoke — slice M6.2L — M6-SMK-021 (proposed — HARDENING, owner review).

Authored by TESTER in M6-P2103 (mode=build, "do not yet run"); EXECUTED and its result recorded in M6-P2104
(TESTER_RUN -> 04-artifacts/test-reports/M6.2L/SMOKE_RESULTS.md). Closes audit item B2 / M6-OD-013 (FIX_M6
2026-09-03). Governance is immutable here: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF —
nothing below flips a flag; the pack still declares no Pass/Ready and self-certifies nothing (RULE-015).

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (proposed additions row M6-SMK-021):

    Scenario (verbatim):   "Evidence pack assembled with a fake-but-nonblank ref, or one valid ref copy-pasted across
                           all mandatory keys of all 10 categories"
    Expected (verbatim):   "categories read MISSING (never COMPLETE); ref existence + uniqueness + category-binding
                           enforced, not raw truthiness"

The pack_assembler no longer accepts raw truthiness: a mandatory key is satisfied ONLY by a ref that EXISTS
(well-formed `ev::{category}::{key}`, or a member of an injected known_refs oracle), is UNIQUE pack-wide, and is
BOUND to THIS (category, key). Fail-closed on any forgery -> categories MISSING -> pack NOT_READY (FAIL-007). Reuses
the coder's B2 leg pattern + the shared conftest fixtures (evidence_assembler, full_evidence_refs, all_smokes_recorded).
"""
from __future__ import annotations

from app.measurement.evidence.categories import CATEGORY_MANDATORY, EvidenceCategory
from app.measurement.evidence.models import Readiness


# --- primary smoke (forgery 1): a fake-but-nonblank ref leaves its category MISSING ---------------
def test_smk_021_fake_but_nonblank_ref_leaves_category_missing(
    evidence_assembler, full_evidence_refs, all_smokes_recorded
):
    """M6-SMK-021 (part 1) "Evidence pack assembled with a fake-but-nonblank ref" -> "categories read MISSING (never
    COMPLETE); ref existence + uniqueness + category-binding enforced, not raw truthiness".

    A fake-but-nonblank junk ref ("x") passes raw truthiness but fails existence/binding -> its category is MISSING
    (never COMPLETE) and the pack is NOT_READY.
    """
    refs = {cat: dict(keys) for cat, keys in full_evidence_refs.items()}
    cat = EvidenceCategory.EVENT_REGISTRY
    refs[cat] = {k: "x" for k in refs[cat]}
    pack = evidence_assembler.assemble(all_smokes_recorded, refs)
    ev = pack.category(cat)
    assert ev.complete is False and set(ev.missing) == set(CATEGORY_MANDATORY[cat])
    assert pack.readiness is Readiness.NOT_READY


# --- primary smoke (forgery 2): one valid ref copy-pasted across every slot is all-MISSING --------
def test_smk_021_one_valid_ref_copy_pasted_everywhere_is_all_missing(evidence_assembler, all_smokes_recorded):
    """M6-SMK-021 (part 2) "or one valid ref copy-pasted across all mandatory keys of all 10 categories" -> all
    categories MISSING: uniqueness (a ref used more than once) AND category-binding (bound only to Event Registry)
    both reject the copy-pasted ref everywhere; the pack is NOT_READY."""
    one = "ev::Event Registry::screenshot_api_db_record"
    refs = {cat: {k: one for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}
    pack = evidence_assembler.assemble(all_smokes_recorded, refs)
    assert all(not c.complete for c in pack.categories)
    assert pack.readiness is Readiness.NOT_READY


# --- negative / fail-closed: a unique well-formed ref bound to the WRONG category is MISSING -------
def test_smk_021_neg_wrong_category_binding_is_missing(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    """A ref that EXISTS + is UNIQUE but is bound to the WRONG category (a Consent-bound ref placed in Dedup) does not
    satisfy the Dedup slot -> Dedup MISSING, pack NOT_READY (binding is (category, key), not truthiness)."""
    refs = {cat: dict(keys) for cat, keys in full_evidence_refs.items()}
    dedup = EvidenceCategory.DEDUP
    only_key = CATEGORY_MANDATORY[dedup][0]
    refs[dedup] = {only_key: "ev::Consent::consent_pass_UNIQUE"}
    pack = evidence_assembler.assemble(all_smokes_recorded, refs)
    assert pack.category(dedup).complete is False
    assert pack.readiness is Readiness.NOT_READY


# --- positive control: a genuine unique + category-bound ref set is still all-COMPLETE ------------
def test_smk_021_control_genuine_unique_bound_refs_all_complete(
    evidence_assembler, full_evidence_refs, all_smokes_recorded
):
    """Non-vacuity control: the honest, unique, correctly-bound full ref set still completes every category and
    reaches the terminal OWNER_REVIEW_REQUIRED (the hardening rejects forgeries, not legitimate evidence)."""
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs)
    assert all(c.complete for c in pack.categories)
    assert pack.readiness is Readiness.OWNER_REVIEW_REQUIRED
