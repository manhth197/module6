"""M6.2J dormant / reactivation measurement — gated on consent + CRM eligibility (fail-closed, measure-only).

Doc §9 Dormant/Reactivation valid signals: *Dormant segment, consent pass, CRM eligibility pass, order verified.*
A dormant-segment member is reactivation-ELIGIBLE only when consent is VALID (reuse `ConsentGate`, CRM scope) AND
the CONSUMED CRM-eligibility flag passes — opt-out / expired / ineligible / absent ⇒ excluded (RULE-002 / FAIL-002).
This layer NEVER sends CRM (CRM Messaging owns; `external_send=OFF`); it MEASURES reactivation rate + CPA only.
`member_key` is PII — never emitted raw (aggregate counts only).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, FrozenSet, List, Mapping, Optional

from app.measurement.growth.reads import _safe_div
from app.measurement.models.consumed import ConsentScope


@dataclass(frozen=True)
class ReactivationConsumed:
    """CONSUMED reactivation facts. `crm_eligible_members`: member_key -> CRM eligibility pass (CRM/Member owned).
    `reactivated_member_keys`: members who placed a VERIFIED order (order-verified signal, consumed).
    `reactivation_spend`: approved reactivation ad spend (for CPA). All fail-closed."""

    crm_eligible_members: Mapping[str, bool] = field(default_factory=dict)
    reactivated_member_keys: FrozenSet[str] = field(default_factory=frozenset)
    reactivation_spend: Optional[float] = None


class ReactivationMeasurement:
    """Read-only dormant/reactivation measurement over the CONSUMED segment reader + a ConsentGate."""

    def __init__(
        self,
        segment_reader: Any,
        consent_reader: Any,
        consent_gate: Any,
        consumed: Optional[ReactivationConsumed] = None,
    ) -> None:
        self._segments = segment_reader
        self._consent_reader = consent_reader
        self._gate = consent_gate
        self._c = consumed or ReactivationConsumed()

    def _member_eligible(self, member: Any) -> bool:
        """RULE-002 fail-closed: consent VALID (CRM scope) AND CONSUMED CRM-eligibility pass."""
        snapshot = self._consent_reader.get(getattr(member, "consent_snapshot_id", None))
        if not self._gate.evaluate(snapshot, ConsentScope.CRM):          # absent/opt-out/expired ⇒ False
            return False
        return self._c.crm_eligible_members.get(getattr(member, "member_key", None)) is True

    def eligible_members(self, dormant_segment_id: str) -> List[Any]:
        return [m for m in self._segments.members(dormant_segment_id) if self._member_eligible(m)]

    def reactivated_count(self, dormant_segment_id: str) -> int:
        """Eligible members who reactivated (placed a verified order, consumed signal)."""
        return sum(
            1 for m in self.eligible_members(dormant_segment_id)
            if getattr(m, "member_key", None) in self._c.reactivated_member_keys
        )

    def reactivation_rate(self, dormant_segment_id: str) -> Optional[float]:
        """Reactivation rate = reactivated / eligible (fail-closed; 0 eligible → None)."""
        return _safe_div(self.reactivated_count(dormant_segment_id), len(self.eligible_members(dormant_segment_id)))

    def cpa_reactivation(self, dormant_segment_id: str) -> Optional[float]:
        """CPA reactivation = reactivation spend / reactivated (fail-closed; absent spend / 0 reactivated → None)."""
        return _safe_div(self._c.reactivation_spend, self.reactivated_count(dormant_segment_id))
