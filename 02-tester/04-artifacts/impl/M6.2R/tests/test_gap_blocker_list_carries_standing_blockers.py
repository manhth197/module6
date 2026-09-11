"""M6.2K leg L1 / M6-RULE-015 / M6-FAIL-007: the pack ALWAYS carries the canonical standing gap/blocker list
(M6-P1000 + M6-P1309 BLOCKED, the G/H/I/J forward conditions, M6-OD-011/012). Per §4.4 those standing blockers are
DISCLOSED but do NOT by themselves gate readiness — a fully-complete pack still discloses them at
OWNER_REVIEW_REQUIRED.
"""
from __future__ import annotations

from app.measurement.evidence.gap_blockers import STANDING_BLOCKER_IDS, STANDING_GAP_BLOCKERS
from app.measurement.evidence.models import GapKind, Readiness


def test_pack_always_carries_standing_blockers(evidence_assembler):
    pack = evidence_assembler.assemble()              # even an empty pack carries them
    ids = {g.id for g in pack.gap_blockers if g.kind is GapKind.STANDING_BLOCKER}
    assert set(STANDING_BLOCKER_IDS) <= ids
    assert {"M6-P1000", "M6-P1309", "M6-OD-011", "M6-OD-012"} <= ids


def test_standing_blockers_present_but_do_not_gate_readiness(evidence_assembler, full_evidence_refs, all_smokes_recorded):
    pack = evidence_assembler.assemble(all_smokes_recorded, full_evidence_refs)
    # complete pack -> OWNER_REVIEW_REQUIRED, yet the standing blockers are STILL disclosed (they don't force NOT_READY)
    assert pack.readiness is Readiness.OWNER_REVIEW_REQUIRED
    assert pack.has_standing_blockers()
    ids = {g.id for g in pack.gap_blockers if g.kind is GapKind.STANDING_BLOCKER}
    assert set(STANDING_BLOCKER_IDS) <= ids


def test_standing_blocker_list_covers_all_slice_forward_conditions():
    ids = {g.id for g in STANDING_GAP_BLOCKERS}
    assert {"M6.2G-SCALE", "M6.2H-LEARN", "M6.2I-FUNNEL", "M6.2J-GROWTH"} <= ids
    assert len(STANDING_GAP_BLOCKERS) == 8
