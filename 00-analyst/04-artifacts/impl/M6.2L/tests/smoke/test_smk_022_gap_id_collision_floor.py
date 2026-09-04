"""Official smoke — slice M6.2L — M6-SMK-022 (proposed — HARDENING, owner review).

Authored by TESTER in M6-P2103 (mode=build, "do not yet run"); EXECUTED and its result recorded in M6-P2104
(TESTER_RUN -> 04-artifacts/test-reports/M6.2L/SMOKE_RESULTS.md). Closes audit item B3 / M6-OD-014 (FIX_M6
2026-09-03). Governance is immutable here: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF —
nothing below flips a flag; the pack self-certifies nothing (RULE-015).

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (proposed additions row M6-SMK-022):

    Scenario (verbatim):   "Gap-blocker list carries a duplicated/shadowing standing-blocker id (M6-P1000/M6-P1309)"
    Expected (verbatim):   "the floor detects the duplicate and FAILs (membership count, not set-subset)"

standing_floor_ok() PASSes only when EACH canonical standing-blocker id appears EXACTLY ONCE with its canonical
(kind, description). A duplicated id (count != 1), a shadowing id (same id, different content), or a missing id FAILs
the floor — so a forged/tampered gap list that a naive set-subset check would still "contain" cannot slip past
(FAIL-007). The assembler calls the floor defensively and degrades to NOT_READY on failure. Reuses the coder's B3
leg pattern + the shared conftest fixture (evidence_assembler).
"""
from __future__ import annotations

from app.measurement.evidence.gap_blockers import (
    STANDING_BLOCKER_IDS,
    STANDING_GAP_BLOCKERS,
    standing_floor_ok,
)
from app.measurement.evidence.models import GapBlocker, GapKind


# --- primary smoke: scenario verbatim -- a duplicated standing id FAILs the membership-count floor -
def test_smk_022_duplicated_standing_id_fails_floor(evidence_assembler):
    """M6-SMK-022 "Gap-blocker list carries a duplicated/shadowing standing-blocker id (M6-P1000/M6-P1309)" -> "the
    floor detects the duplicate and FAILs (membership count, not set-subset)".

    A byte-identical DUPLICATE of M6-P1000 makes its id appear twice. A naive set-subset check is still satisfied
    (the id is "contained"), but the membership-count floor FAILs — and an assembled pack whose gap list is
    duplicate/shadow-free still passes and carries all 8 standing blockers (non-vacuous).
    """
    canonical = next(g for g in STANDING_GAP_BLOCKERS if g.id == "M6-P1000")
    duped = list(STANDING_GAP_BLOCKERS) + [
        GapBlocker(canonical.id, canonical.kind, canonical.description, canonical.owner)
    ]
    assert set(STANDING_BLOCKER_IDS) <= {g.id for g in duped}     # the naive subset check is fooled ...
    assert standing_floor_ok(duped) is False                      # ... but the membership-count floor FAILs

    pack = evidence_assembler.assemble()
    assert standing_floor_ok(pack.gap_blockers) is True           # a clean assembled pack passes the floor
    ids = {g.id for g in pack.gap_blockers if g.kind is GapKind.STANDING_BLOCKER}
    assert set(STANDING_BLOCKER_IDS) <= ids                       # and carries all 8 standing blockers


# --- negative / fail-closed: a shadowing id (same id, different content) FAILs the floor ----------
def test_smk_022_neg_shadowing_standing_id_fails_floor():
    """A SHADOW — the same id (M6-P1309) with TAMPERED content — is invisible to a set-subset check but FAILs the
    floor (canonical (kind, description) must match)."""
    shadowed = [g for g in STANDING_GAP_BLOCKERS if g.id != "M6-P1309"] + [
        GapBlocker("M6-P1309", GapKind.STANDING_BLOCKER, "TAMPERED description", "owner/judge")
    ]
    assert set(STANDING_BLOCKER_IDS) <= {g.id for g in shadowed}
    assert standing_floor_ok(shadowed) is False


# --- negative / fail-closed: a missing standing id FAILs the floor --------------------------------
def test_smk_022_neg_missing_standing_id_fails_floor():
    """A DROPPED standing blocker (M6-P1000 removed) FAILs the floor — the honesty payload cannot be silently
    thinned out (FAIL-007)."""
    dropped = [g for g in STANDING_GAP_BLOCKERS if g.id != "M6-P1000"]
    assert standing_floor_ok(dropped) is False


# --- positive control: the canonical list passes the floor ----------------------------------------
def test_smk_022_control_canonical_list_passes_floor():
    """Non-vacuity control: the canonical STANDING_GAP_BLOCKERS list passes the floor (the floor rejects tampering,
    not the honest list)."""
    assert standing_floor_ok(STANDING_GAP_BLOCKERS) is True
