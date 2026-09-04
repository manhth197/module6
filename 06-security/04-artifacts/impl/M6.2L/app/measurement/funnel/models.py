"""Golden Hour funnel result models — frozen, read-only, export-masked (RULE-014 / H02).

A `GoldenHourFunnelView` is one live-session's measured funnel: per-stage counts (total + per Golden-Hour-state),
the doc §14 funnel rates, the verified-only revenue (RULE-003), the RULE-021 order-capture flag (consumed), and the
live/comment/messenger trace (SMK-013). `to_public()` masks `psid` — the raw value never reaches an export surface.
No field carries anything but ORDER_VERIFIED revenue (RULE-003); there is no write/trigger handle (RULE-012).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

from app.measurement.funnel.flow import CHAIN, FlowStage
from app.measurement.funnel.golden_hour import GoldenHourState
from app.measurement.masking import mask


@dataclass(frozen=True)
class FunnelRate:
    """One doc §14 funnel rate, fail-closed (value None when the denominator is 0 / absent — never fabricated)."""

    name: str
    formula: str                    # doc §14 formula verbatim
    value: Optional[float]
    numerator: int
    denominator: int


@dataclass(frozen=True)
class FunnelTrace:
    """The live/comment/messenger trace (SMK-013). `psid` is PII — masked on export (RULE-014 / H02)."""

    live_session_id: Optional[str] = None
    comment_id: Optional[str] = None
    messenger_thread_id: Optional[str] = None
    psid: Optional[str] = None      # PII — masked in to_public

    def to_public(self) -> Dict[str, Any]:
        return {
            "live_session_id": self.live_session_id,
            "comment_id": self.comment_id,
            "messenger_thread_id": self.messenger_thread_id,
            "psid": mask(self.psid),
        }


@dataclass(frozen=True)
class GoldenHourFunnelView:
    """One live-session funnel view (measured; read-only)."""

    live_session_id: Optional[str]
    golden_hour_states: Tuple[GoldenHourState, ...]          # the states observed in this session
    stage_counts: Mapping[FlowStage, int]                    # total per stage (ADS_TO_LIVE = identity presence 0/1)
    state_breakdown: Mapping[GoldenHourState, Mapping[FlowStage, int]]  # per Golden-Hour-state stage counts
    rates: Tuple[FunnelRate, ...]                            # the doc §14 funnel rates
    verified_revenue: float                                 # RULE-003: ORDER_VERIFIED revenue only (0.0 if none)
    capture_gate_passed: bool                               # RULE-021: consumed Commerce-gate flag (absent → False)
    trace: FunnelTrace = field(default_factory=FunnelTrace)

    def stage_count(self, stage: FlowStage) -> int:
        return int(self.stage_counts.get(stage, 0))

    def rate(self, name: str) -> Optional[FunnelRate]:
        for r in self.rates:
            if r.name == name:
                return r
        return None

    def to_public(self) -> Dict[str, Any]:
        """Export-safe mapping (dashboard / evidence). psid masked (via FunnelTrace.to_public); enums → tokens.
        Only verified revenue is present (RULE-003); no write/trigger field exists (RULE-012)."""
        return {
            "live_session_id": self.live_session_id,
            "golden_hour_states": [s.value for s in self.golden_hour_states],
            "stage_counts": {stage.value: int(self.stage_counts.get(stage, 0)) for stage in CHAIN},
            "state_breakdown": {
                state.value: {stage.value: int(counts.get(stage, 0)) for stage in CHAIN}
                for state, counts in self.state_breakdown.items()
            },
            "rates": [
                {"name": r.name, "formula": r.formula, "value": r.value,
                 "numerator": r.numerator, "denominator": r.denominator}
                for r in self.rates
            ],
            "verified_revenue": self.verified_revenue,
            "capture_gate_passed": self.capture_gate_passed,
            "trace": self.trace.to_public(),
        }
