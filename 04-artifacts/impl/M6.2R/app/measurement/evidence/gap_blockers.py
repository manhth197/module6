"""The canonical STANDING gap/blocker list (RULE-015 / FAIL-007 — the honesty payload).

These are the standing conditions the owner-review package MUST disclose (never drop): the standing BLOCKED judge
verdicts + every M6.2G/H/I/J before-real-scale/send/auto-publish/CRM-send/surfacing forward condition + M6-OD-011/012.
They are ALWAYS included in the assembled pack; per §4.4 they are DISCLOSED but do NOT by themselves gate readiness
(production stays BLOCKED regardless — reviewing them is the owner's job). Encoded here so the assembler cannot emit
a pack that omits them. Governance refs only — no PII.
"""
from __future__ import annotations

from typing import Iterable, Tuple

from app.measurement.evidence.models import GapBlocker, GapKind

_SB = GapKind.STANDING_BLOCKER

STANDING_GAP_BLOCKERS: Tuple[GapBlocker, ...] = (
    GapBlocker("M6-P1000", _SB, "M6.2A entry judge verdict BLOCKED (not converted)", "owner/judge"),
    GapBlocker("M6-P1309", _SB, "M6.2D exit judge verdict BLOCKED (not converted)", "owner/judge"),
    GapBlocker(
        "M6.2G-SCALE", _SB,
        "Scale-Gate forward conditions before any real scale: ENTRY-001/003 real-scale conditions, the four "
        "M6-P1600 attestation true-ups, ENTRY-004 M5 DEBT-1..4 + the adversarial P4 re-gate, scale ACCESS-1/"
        "F-SCALE-*, and M6-OD-002/003/004/005",
        "owner",
    ),
    GapBlocker(
        "M6.2H-LEARN", _SB,
        "Learning forward conditions before any real content/auto-publish: M6-OD-006 (safe range), M6-OD-007 "
        "(content fill), F-LEARN-*",
        "owner",
    ),
    GapBlocker(
        "M6.2I-FUNNEL", _SB,
        "Funnel forward conditions before surfacing: F-FUNNEL-4 (single-subject trace bind), F-SEC-2I-2",
        "owner",
    ),
    GapBlocker(
        "M6.2J-GROWTH", _SB,
        "Growth forward conditions: F-GROWTH-1 (CRM subject-bind), F-GROWTH-3 (verified_rows ORDER_VERIFIED "
        "choke), F-SEC-2J-*",
        "owner",
    ),
    GapBlocker("M6-OD-011", _SB, "Admin-endpoint authN/authZ (owner-controlled integration step)", "owner"),
    GapBlocker("M6-OD-012", _SB, "PII masking scope decision (OPEN)", "owner"),
)

STANDING_BLOCKER_IDS: Tuple[str, ...] = tuple(g.id for g in STANDING_GAP_BLOCKERS)

# The canonical identity of each standing blocker (id -> (kind, description)) — the floor's reference. A gap that
# reuses a canonical id with different content is a SHADOW; a canonical id appearing twice is a DUPLICATE.
_CANONICAL: dict = {g.id: (g.kind, g.description) for g in STANDING_GAP_BLOCKERS}


def standing_floor_ok(gaps: Iterable[GapBlocker]) -> bool:
    """B3 / M6-OD-014 — the membership-count floor (NOT a set-subset). PASS iff EACH canonical standing-blocker id
    appears EXACTLY ONCE in `gaps` AND with its canonical (kind, description). A duplicated id (count != 1) or a
    shadowing id (same id, different kind/description) or a missing id FAILs the floor — so a forged/tampered pack
    that duplicates or shadows M6-P1000 / M6-P1309 cannot slip past a naive subset check (FAIL-007). Governance refs
    only; no PII is read."""
    seen: dict = {}
    for g in gaps:
        gid = getattr(g, "id", None)
        if gid in _CANONICAL:
            seen.setdefault(gid, []).append((getattr(g, "kind", None), getattr(g, "description", None)))
    for sid, canonical in _CANONICAL.items():
        occurrences = seen.get(sid, [])
        if len(occurrences) != 1:          # missing (0) or duplicated (>1)
            return False
        if occurrences[0] != canonical:    # shadow: same id, different content
            return False
    return True
