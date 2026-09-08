"""M6.2L leg 4 / M6-SMK-022 / M6-OD-014 / RULE-015 / FAIL-007: the standing-blocker floor pins/de-dups gap ids and
counts MEMBERSHIP (not a set-subset). A duplicated or shadowing standing-blocker id (M6-P1000 / M6-P1309), or a
missing one, FAILs the floor — so a forged/tampered pack cannot slip past a naive subset check. The canonical list
passes, and a fully-assembled honest pack still carries all 8 standing blockers.
"""
from __future__ import annotations

from app.measurement.evidence.gap_blockers import (
    STANDING_BLOCKER_IDS,
    STANDING_GAP_BLOCKERS,
    standing_floor_ok,
)
from app.measurement.evidence.models import GapBlocker, GapKind


def test_canonical_list_passes_the_floor():
    assert standing_floor_ok(STANDING_GAP_BLOCKERS) is True


def test_duplicated_standing_id_fails_floor():
    canonical = next(g for g in STANDING_GAP_BLOCKERS if g.id == "M6-P1000")
    # a byte-identical DUPLICATE of M6-P1000 -> the id now appears twice (a set-subset check would still "contain" it)
    duped = list(STANDING_GAP_BLOCKERS) + [
        GapBlocker(canonical.id, canonical.kind, canonical.description, canonical.owner)
    ]
    assert set(STANDING_BLOCKER_IDS) <= {g.id for g in duped}   # the naive subset check is fooled ...
    assert standing_floor_ok(duped) is False                    # ... but the membership-count floor FAILs


def test_shadowing_standing_id_fails_floor():
    # same id (M6-P1309), DIFFERENT content -> a shadow the subset check cannot see
    shadowed = [g for g in STANDING_GAP_BLOCKERS if g.id != "M6-P1309"] + [
        GapBlocker("M6-P1309", GapKind.STANDING_BLOCKER, "TAMPERED description", "owner/judge")
    ]
    assert set(STANDING_BLOCKER_IDS) <= {g.id for g in shadowed}
    assert standing_floor_ok(shadowed) is False


def test_missing_standing_id_fails_floor():
    dropped = [g for g in STANDING_GAP_BLOCKERS if g.id != "M6-P1000"]
    assert standing_floor_ok(dropped) is False


def test_assembled_pack_passes_floor_and_carries_all_standing_blockers(evidence_assembler):
    pack = evidence_assembler.assemble()
    assert standing_floor_ok(pack.gap_blockers) is True
    ids = {g.id for g in pack.gap_blockers if g.kind is GapKind.STANDING_BLOCKER}
    assert set(STANDING_BLOCKER_IDS) <= ids
