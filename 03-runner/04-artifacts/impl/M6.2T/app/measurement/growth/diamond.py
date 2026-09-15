"""M6.2J Diamond referral measurement — records attribution + verified revenue; commission MEASURED-not-computed.

Doc §9 / RULE-019: *Diamond referral phải gắn link hợp lệ, buyer identity, order verified và commission eligibility
từ Core/Finance; Module 6 chỉ đo nguồn và hiệu quả.* So this layer:
  * records referral attribution (referral_link_id + buyer identity + DIAMOND_REFERRAL_ORDER_VERIFIED),
  * measures Diamond Revenue (verified-only) and Diamond lead rate,
  * measures **commission-ready revenue** = the verified revenue that is commission-ELIGIBLE (a CONSUMED Core/Finance
    flag) — a REVENUE figure, NOT a commission.
It exposes NO method that computes a commission amount / rate / payout — Finance owns commission (SMK-014). Buyer
identity is PII — masked on export (RULE-014 / H02).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from app.measurement.growth.reads import (
    _safe_div,
    attribution_value,
    event_count,
    has_referral_attribution,
    verified_rows,
)
from app.measurement.growth.signals import (
    DIAMOND_LEAD_CREATED,
    DIAMOND_REFERRAL_ORDER_VERIFIED,
)
from app.measurement.masking import mask


@dataclass(frozen=True)
class DiamondConsumed:
    """CONSUMED Diamond facts (Core/Finance owned). `commission_eligible_orders`: order_code -> commission
    eligibility pass (Finance decides eligibility; M6 only records it). Fail-closed: absent ⇒ not eligible."""

    commission_eligible_orders: Mapping[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class ReferralAttribution:
    """One recorded Diamond referral attribution (measure-only). `buyer_ref` is PII — masked on export."""

    order_code: Optional[str]
    referral_link_id: Optional[str]
    diamond_id: Optional[str]
    buyer_ref: Optional[str]                      # PII (customer/guest id) — masked in to_public
    verified_revenue: float                       # verified-only (RULE-003)

    def to_public(self) -> Dict[str, Any]:
        return {
            "order_code": self.order_code,
            "referral_link_id": self.referral_link_id,
            "diamond_id": self.diamond_id,
            "buyer_ref": mask(self.buyer_ref),
            "verified_revenue": self.verified_revenue,
        }


class DiamondReferralMeasurement:
    """Read-only Diamond referral measurement over the measurement store + consumed commission-eligibility."""

    def __init__(self, measurement_store: Any, consumed: Optional[DiamondConsumed] = None) -> None:
        self._store = measurement_store
        self._c = consumed or DiamondConsumed()

    def referral_rows(self) -> List[Any]:
        """Verified rows carrying Diamond referral attribution (referral_link_id / diamond_id)."""
        return [r for r in verified_rows(self._store) if has_referral_attribution(r)]

    def referral_attributions(self) -> List[ReferralAttribution]:
        """Record referral attribution for each verified Diamond order (measure-only; buyer identity masked)."""
        out: List[ReferralAttribution] = []
        for r in self.referral_rows():
            buyer = getattr(r, "customer_id", None) or getattr(r, "guest_id", None)
            out.append(ReferralAttribution(
                order_code=getattr(r, "order_code", None),
                referral_link_id=attribution_value(r, "referral_link_id"),
                diamond_id=attribution_value(r, "diamond_id"),
                buyer_ref=buyer,
                verified_revenue=float(r.revenue_value),
            ))
        return out

    def diamond_revenue(self) -> float:
        """Diamond Revenue — verified-only (RULE-003), no consent gate (doc §9)."""
        return float(sum(r.revenue_value for r in self.referral_rows()))

    def commission_ready_revenue(self) -> float:
        """Commission-READY revenue = verified referral revenue that is commission-ELIGIBLE (CONSUMED flag,
        fail-closed). This is a REVENUE figure Finance may act on; Module 6 computes NO commission (RULE-019)."""
        return float(sum(
            r.revenue_value for r in self.referral_rows()
            if self._c.commission_eligible_orders.get(getattr(r, "order_code", None)) is True
        ))

    def diamond_lead_rate(self) -> Optional[float]:
        """Diamond lead rate = DIAMOND_REFERRAL_ORDER_VERIFIED / DIAMOND_LEAD_CREATED (fail-closed)."""
        return _safe_div(
            event_count(self._store, DIAMOND_REFERRAL_ORDER_VERIFIED),
            event_count(self._store, DIAMOND_LEAD_CREATED),
        )
