"""M6.2J CRM repeat/reorder measurement — CRM Revenue verified-only AND consent/eligibility/suppression gated.

Doc §9: *CRM revenue phải xuất phát từ CRM eligibility, suppression pass và order verified; không dùng click/chat
làm revenue.* (RULE-002 / RULE-003 / FAIL-002.) A verified CRM order contributes to CRM Revenue ONLY when the
CONSUMED CRM-eligibility flag passes AND suppression passes AND consent is VALID for the CRM scope (reuse
`ConsentGate`). Anything missing ⇒ excluded (fail-closed). Opt-out ⇒ excluded (SMK-008). A CRM_REORDER_SENT /
click / chat is never revenue (only the set-once ORDER_VERIFIED revenue_value is). This layer NEVER sends CRM
(CRM Messaging owns; `external_send=OFF`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Mapping, Optional

from app.measurement.growth.reads import (
    _safe_div,
    event_count,
    is_crm_attributed,
    verified_rows,
)
from app.measurement.growth.signals import (
    CRM_REORDER_ORDER_CREATED,
    CRM_REORDER_SENT,
)
from app.measurement.models.consumed import ConsentScope, ConsentSnapshot


@dataclass(frozen=True)
class CrmConsumed:
    """CONSUMED CRM-lifecycle facts (CRM/Member + Consent owned; M6 READS, never decides). Keyed by order_code.
    All fail-closed: an order absent from a map is treated as NOT-passing that gate."""

    crm_eligible_orders: Mapping[str, bool] = field(default_factory=dict)      # order_code -> CRM eligibility pass
    suppression_pass_orders: Mapping[str, bool] = field(default_factory=dict)  # order_code -> suppression cleared
    consent_by_order: Mapping[str, ConsentSnapshot] = field(default_factory=dict)  # order_code -> CRM-scope consent


class CrmReorderMeasurement:
    """Read-only CRM repeat/reorder measurement over the measurement store + a ConsentGate + consumed CRM facts."""

    def __init__(self, measurement_store: Any, consent_gate: Any, consumed: Optional[CrmConsumed] = None) -> None:
        self._store = measurement_store
        self._gate = consent_gate
        self._c = consumed or CrmConsumed()

    def _crm_gate_passes(self, order_code: Optional[str]) -> bool:
        """RULE-002 fail-closed: an order's CRM revenue is countable ONLY when eligibility + suppression + consent
        all pass. Missing order_code, or any missing/failing consumed flag, ⇒ False."""
        if not order_code:
            return False
        if self._c.crm_eligible_orders.get(order_code) is not True:
            return False
        if self._c.suppression_pass_orders.get(order_code) is not True:
            return False
        snapshot = self._c.consent_by_order.get(order_code)
        return self._gate.evaluate(snapshot, ConsentScope.CRM)   # absent/opt-out/expired ⇒ False (fail-closed)

    def crm_revenue_rows(self) -> List[Any]:
        """Verified, CRM-attributed rows whose CRM eligibility + suppression + consent all pass."""
        return [
            r for r in verified_rows(self._store)
            if is_crm_attributed(r) and self._crm_gate_passes(getattr(r, "order_code", None))
        ]

    def crm_revenue(self) -> float:
        """CRM Revenue — verified-only, gated (RULE-002/003). A click/chat / CRM_REORDER_SENT contributes 0."""
        return float(sum(r.revenue_value for r in self.crm_revenue_rows()))

    def repeat_rate(self) -> Optional[float]:
        """Repeat rate = CRM_REORDER_ORDER_CREATED / CRM_REORDER_SENT (fail-closed; 0 denominator → None)."""
        return _safe_div(
            event_count(self._store, CRM_REORDER_ORDER_CREATED),
            event_count(self._store, CRM_REORDER_SENT),
        )
