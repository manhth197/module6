"""Staged in-memory ConsentReader adapter (M6.2B).

The "real ConsentReader adapter" the M6.2B entry gate names — kept STAGED (in-memory, seeded). It reads issued
consent snapshots by id (M6-CTR-006, consume-only, RULE-018) and exposes the send-time `current_state` the
future dispatcher will use; it has NO write path (M6 cannot mutate the consent system). The DB-backed adapter
binds at the owner integration step (M6-OD-011).

The consent gate is hardened at its DECISION POINT (F2, see consent/gate.py: consent_scope coerced/asserted),
so even a hostile adapter that returned a malformed/subclass snapshot cannot make the gate fail OPEN.
"""
from __future__ import annotations

from typing import Dict, Optional

from app.measurement.models.consumed import ConsentSnapshot, ConsentState


class InMemoryConsentReader:
    """Read-only; satisfies the ConsentReader port (`get` + `current_state`)."""

    def __init__(
        self,
        snapshots: Optional[Dict[str, ConsentSnapshot]] = None,
        current: Optional[Dict[str, ConsentState]] = None,
    ) -> None:
        self._snapshots: Dict[str, ConsentSnapshot] = dict(snapshots or {})
        self._current: Dict[str, ConsentState] = dict(current or {})

    def get(self, consent_snapshot_id: str) -> Optional[ConsentSnapshot]:
        return self._snapshots.get(consent_snapshot_id)

    def current_state(self, subject_ref: str) -> ConsentState:
        # Unknown subject -> fail-closed (MISSING), never an inferred/upgraded consent.
        return self._current.get(subject_ref, ConsentState.MISSING)
